"""Fila FIFO thread-safe e async-ready de eventos brutos.

``RawEventQueue`` é o buffer central da ingestão: produtores (collectors)
enfileiram ``RawEvent`` e consumidores (pipeline) retiram. A fila coopera com
o ``BackpressureController`` (bloqueando ``put`` enquanto ``PAUSED``), aplica
a ``DropPolicy`` configurada quando cheia e registra métricas no
``MetricsRegistry``.

Garantias de concorrência
-------------------------
- **Thread-safety síncrono**: todos os acessos ao ``deque`` interno são
  serializados por um ``threading.Lock``. ``put_nowait``/``get_nowait``/
  ``qsize``/``empty``/``full``/``reset`` podem ser chamados de qualquer thread.
- **Async-ready**: ``put``/``get`` usam um ``asyncio.Event`` criado de forma
  lazy no primeiro loop asyncio que usar a fila. Wakeups cross-thread (ex.:
  produtor síncrono notificando um consumidor async) são entregues via
  ``loop.call_soon_threadsafe``. O uso async é **single-loop**: chamar
  ``put``/``get`` de um loop diferente do primeiro levanta ``RuntimeError``.
"""

from __future__ import annotations

import asyncio
import threading
from collections import deque
from dataclasses import dataclass
from enum import Enum

from ..domain import RawEvent
from ..result import Error, ErrorCode, Failure, Result, ok
from .backpressure import BackpressureController
from .dead_letter import DeadLetterQueue
from .metrics import METRIC_DROPS, METRIC_QUEUE_SIZE, MetricsRegistry


class DropPolicy(Enum):
    """Política aplicada quando a fila está cheia."""

    BLOCK = "block"
    DISCARD = "discard"
    DEAD_LETTER = "dead_letter"


@dataclass(frozen=True, slots=True)
class QueueConfig:
    """Configuração da fila.

    Attributes:
        maxsize: Capacidade máxima de eventos.
        drop_policy: Comportamento quando cheia (default: ``BLOCK``).
        put_timeout: Timeout (segundos) do ``put``/``put_nowait``; ``None``
            significa sem timeout (aguarda indefinidamente).
        get_timeout: Timeout (segundos) do ``get``; ``None`` significa sem
            timeout (bloqueia até haver item).
    """

    maxsize: int = 10_000
    drop_policy: DropPolicy = DropPolicy.BLOCK
    put_timeout: float | None = None
    get_timeout: float | None = None

    def __post_init__(self) -> None:
        if self.maxsize <= 0:
            raise ValueError(f"maxsize deve ser > 0; recebido {self.maxsize}")
        if self.put_timeout is not None and self.put_timeout < 0:
            raise ValueError("put_timeout não pode ser negativo")
        if self.get_timeout is not None and self.get_timeout < 0:
            raise ValueError("get_timeout não pode ser negativo")


class RawEventQueue:
    """Fila FIFO de ``RawEvent`` com drop policy, backpressure e métricas.

    Args:
        config: Configuração da fila.
        backpressure: Controller opcional; quando ``PAUSED``, ``put`` aguarda
            retomada antes de enfileirar.
        dead_letter: Fila de eventos mortos; **obrigatória** quando
            ``drop_policy`` é ``DEAD_LETTER``.
        metrics: Registry opcional; exposto via ``metrics``.
    """

    def __init__(
        self,
        config: QueueConfig | None = None,
        *,
        backpressure: BackpressureController | None = None,
        dead_letter: DeadLetterQueue | None = None,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        cfg = config or QueueConfig()
        if cfg.drop_policy is DropPolicy.DEAD_LETTER and dead_letter is None:
            raise ValueError("drop_policy=DEAD_LETTER exige um DeadLetterQueue")
        self._config = cfg
        self._backpressure = backpressure
        self._dead_letter = dead_letter
        self._metrics = metrics or MetricsRegistry()
        self._items: deque[RawEvent] = deque()
        self._lock = threading.Lock()
        self._notify: asyncio.Event | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def put(self, event: RawEvent) -> Result[None]:
        """Enfileira ``event`` respeitando backpressure, política e timeout.

        Returns:
            ``Success(None)`` quando enfileirado (ou aplicada a drop policy);
            ``Failure`` com ``ErrorCode.TIMEOUT`` se o backpressure não retomar
            dentro do ``put_timeout``, ou ``ErrorCode.QUEUE_FULL`` se o espaço
            não abrir dentro do ``put_timeout`` na política ``BLOCK``.
        """
        notify = self._get_notify()
        deadline = self._deadline(self._config.put_timeout)

        if self._backpressure is not None and self._backpressure.is_paused():
            timeout = self._remaining(deadline)
            resumed = await self._backpressure.wait_until_resumed(timeout=timeout)
            if not resumed:
                return Failure[None](
                    Error(ErrorCode.TIMEOUT, "backpressure ainda PAUSED no put_timeout")
                )

        while True:
            with self._lock:
                if len(self._items) < self._config.maxsize:
                    self._items.append(event)
                    break
                if self._config.drop_policy is DropPolicy.DISCARD:
                    self._metrics.increment(METRIC_DROPS)
                    return ok(None)
                if self._config.drop_policy is DropPolicy.DEAD_LETTER:
                    self._submit_dead_letter(event, "fila cheia (DEAD_LETTER)")
                    return ok(None)
                # BLOCK: aguarda espaço
            if not await self._wait_notify(notify, deadline):
                with self._lock:
                    if len(self._items) < self._config.maxsize:
                        self._items.append(event)
                        break
                return Failure[None](
                    Error(
                        ErrorCode.QUEUE_FULL,
                        "put aguardou espaço e expirou o put_timeout",
                    )
                )
        self._set_gauge()
        self._wake()
        return ok(None)

    def put_nowait(self, event: RawEvent) -> Result[None]:
        """Tenta enfileirar sem aguardar, aplicando a drop policy.

        Returns:
            ``Success(None)`` se enfileirado ou drop aplicado; ``Failure`` com
            ``ErrorCode.QUEUE_FULL`` na política ``BLOCK`` quando cheia. Não
            consulta backpressure (produtores síncronos podem usar
            ``BackpressureController.can_accept`` antes).
        """
        with self._lock:
            if len(self._items) < self._config.maxsize:
                self._items.append(event)
                self._set_gauge_locked()
                self._wake_locked()
                return ok(None)
            if self._config.drop_policy is DropPolicy.DISCARD:
                self._metrics.increment(METRIC_DROPS)
                return ok(None)
            if self._config.drop_policy is DropPolicy.DEAD_LETTER:
                self._submit_dead_letter(event, "fila cheia (DEAD_LETTER)")
                return ok(None)
        return Failure[None](Error(ErrorCode.QUEUE_FULL, "fila cheia e drop_policy=BLOCK"))

    async def get(self) -> RawEvent:
        """Retira o evento mais antigo, aguardando até haver item (ou timeout).

        Raises:
            asyncio.TimeoutError: Se ``get_timeout`` expirar sem item.
        """
        notify = self._get_notify()
        deadline = self._deadline(self._config.get_timeout)
        while True:
            with self._lock:
                if self._items:
                    item = self._items.popleft()
                    self._set_gauge_locked()
                    self._wake_locked()
                    return item
            if not await self._wait_notify(notify, deadline):
                with self._lock:
                    if self._items:
                        continue
                raise TimeoutError("get expirou o get_timeout sem item disponível")

    def get_nowait(self) -> RawEvent:
        """Retira o evento mais antigo sem aguardar.

        Raises:
            asyncio.QueueEmpty: Se a fila está vazia.
        """
        with self._lock:
            if not self._items:
                raise asyncio.QueueEmpty("fila vazia")
            item = self._items.popleft()
            self._set_gauge_locked()
            self._wake_locked()
            return item

    def qsize(self) -> int:
        """Número corrente de eventos na fila."""
        with self._lock:
            return len(self._items)

    def empty(self) -> bool:
        """Retorna ``True`` quando a fila está vazia."""
        with self._lock:
            return not self._items

    def full(self) -> bool:
        """Retorna ``True`` quando a fila atingiu ``maxsize``."""
        with self._lock:
            return len(self._items) >= self._config.maxsize

    @property
    def metrics(self) -> MetricsRegistry:
        """Registry de métricas usado pela fila."""
        return self._metrics

    def reset(self) -> None:
        """Esvazia a fila e zera o gauge de tamanho."""
        with self._lock:
            self._items.clear()
            self._set_gauge_locked()
            self._wake_locked()

    # -- internals ---------------------------------------------------------

    def _get_notify(self) -> asyncio.Event:
        """Obtém (ou cria) o evento async vinculado ao loop corrente.

        Raises:
            RuntimeError: Se um loop diferente do que vinculou a fila tentar
                usar o async. O uso async é single-loop.
        """
        loop = asyncio.get_running_loop()
        with self._lock:
            if self._notify is None:
                self._notify = asyncio.Event()
                self._loop = loop
                return self._notify
            if self._loop is not loop:
                raise RuntimeError("RawEventQueue já vinculada a outro event loop")
            notify = self._notify
            if notify is None:
                raise RuntimeError("RawEventQueue em estado inválido")
            return notify

    @staticmethod
    def _deadline(timeout: float | None) -> float | None:
        """Instante absoluto (loop time) do prazo, ou ``None`` sem timeout."""
        if timeout is None:
            return None
        return asyncio.get_running_loop().time() + timeout

    @staticmethod
    def _remaining(deadline: float | None) -> float | None:
        """Tempo restante até o prazo, ou ``None`` sem timeout."""
        if deadline is None:
            return None
        return max(0.0, deadline - asyncio.get_running_loop().time())

    async def _wait_notify(self, notify: asyncio.Event, deadline: float | None) -> bool:
        """Aguarda notificação de mudança; retorna ``False`` se o prazo expirou.

        O evento é limpo após cada despertar para evitar re-checks em cascata
        (busy-loop) quando o evento ficou setado de uma notificação anterior.
        A correção de wake-up perdido vem do padrão: todo produtor seta o
        evento *após* mutar a fila e o consumidor sempre re-verifica o
        predicado sob o lock depois de ``wait``.
        """
        if deadline is None:
            await notify.wait()
        else:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                return False
            try:
                await asyncio.wait_for(notify.wait(), timeout=remaining)
            except TimeoutError:
                return False
        notify.clear()
        return True

    def _submit_dead_letter(self, event: RawEvent, reason: str) -> None:
        """Registra um evento na DeadLetterQueue (métrica incrementada lá)."""
        if self._dead_letter is not None:
            self._dead_letter.submit(event, error=reason)

    def _set_gauge(self) -> None:
        """Atualiza o gauge ``queue_size`` (chamado fora do lock)."""
        with self._lock:
            self._set_gauge_locked()

    def _set_gauge_locked(self) -> None:
        """Atualiza o gauge ``queue_size`` (deve segurar o lock)."""
        self._metrics.set_gauge(METRIC_QUEUE_SIZE, len(self._items))

    def _wake(self) -> None:
        """Notifica waiters async (chamado fora do lock)."""
        with self._lock:
            self._wake_locked()

    def _wake_locked(self) -> None:
        """Notifica waiters async (deve segurar o lock; seguro cross-thread)."""
        loop = self._loop
        notify = self._notify
        if loop is None or notify is None or loop.is_closed():
            return
        try:
            loop.call_soon_threadsafe(notify.set)
        except RuntimeError:
            # Loop em encerramento; waiters async já não existem.
            pass


__all__ = ["DropPolicy", "QueueConfig", "RawEventQueue"]
