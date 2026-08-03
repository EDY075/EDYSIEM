"""Controle de backpressure da fila de ingestão.

``BackpressureController`` aplica a estratégia de *high/low water marks* com
histerese: quando o tamanho monitorado atinge (ou ultrapassa) o
``high_water_mark`` o estado passa a ``PAUSED``; quando desce até (ou abaixo
de) o ``low_water_mark`` o estado volta a ``NORMAL``. Entre os dois marcos o
estado permanece inalterado, evitando oscilação (flapping).

O controle é thread-safe: ``report_size``/``pause``/``resume`` podem ser
chamados de qualquer thread. O suporte async (``wait_until_resumed``) exige
que o uso aconteça a partir do loop asyncio que primeiro vinculou o
controller (documentado em ``_ensure_event``).
"""

from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from enum import Enum


class BackpressureState(Enum):
    """Estado operacional do backpressure."""

    NORMAL = "normal"
    PAUSED = "paused"


@dataclass(frozen=True, slots=True)
class BackpressureConfig:
    """Configuração dos water marks.

    Attributes:
        high_water_mark: Tamanho a partir do qual o estado vira ``PAUSED``.
        low_water_mark: Tamanho até o qual o estado volta a ``NORMAL``.
    """

    high_water_mark: int = 8_000
    low_water_mark: int = 2_000

    def __post_init__(self) -> None:
        if self.high_water_mark <= 0:
            raise ValueError("high_water_mark deve ser > 0")
        if self.low_water_mark <= 0:
            raise ValueError("low_water_mark deve ser > 0")
        if self.low_water_mark > self.high_water_mark:
            raise ValueError("low_water_mark deve ser <= high_water_mark")


class BackpressureController:
    """Aplica high/low water marks com histerese e suporte async.

    A transição de estado é protegida por um ``threading.Lock`` e as
    notificações async são entregues por um ``asyncio.Event`` criado de forma
    lazy no primeiro loop que usar ``wait_until_resumed``. Quando o estado
    muda fora da thread do loop, o evento é atualizado via
    ``loop.call_soon_threadsafe`` para manter o async seguro.
    """

    def __init__(self, config: BackpressureConfig | None = None) -> None:
        self._config = config or BackpressureConfig()
        self._state = BackpressureState.NORMAL
        self._lock = threading.Lock()
        self._resume_event: asyncio.Event | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None

    @property
    def state(self) -> BackpressureState:
        """Estado corrente (``NORMAL`` ou ``PAUSED``)."""
        with self._lock:
            return self._state

    def report_size(self, size: int) -> None:
        """Atualiza os water marks a partir do tamanho corrente monitorado.

        Args:
            size: Tamanho corrente (ex.: número de itens na fila).

        Raises:
            ValueError: Se ``size`` for negativo.
        """
        if size < 0:
            raise ValueError(f"size não pode ser negativo; recebido {size}")
        with self._lock:
            if self._state is BackpressureState.NORMAL and size >= self._config.high_water_mark:
                self._state = BackpressureState.PAUSED
                self._clear_event_locked()
            elif self._state is BackpressureState.PAUSED and size <= self._config.low_water_mark:
                self._state = BackpressureState.NORMAL
                self._set_event_locked()

    def pause(self) -> None:
        """Força o estado para ``PAUSED`` (pausa manual)."""
        with self._lock:
            self._state = BackpressureState.PAUSED
            self._clear_event_locked()

    def resume(self) -> None:
        """Força o estado para ``NORMAL`` (retomada manual)."""
        with self._lock:
            self._state = BackpressureState.NORMAL
            self._set_event_locked()

    def is_paused(self) -> bool:
        """Retorna ``True`` quando o estado corrente é ``PAUSED``."""
        return self.state is BackpressureState.PAUSED

    def can_accept(self, size: int) -> bool:
        """Diz se um produtor síncrono pode enfileirar no tamanho ``size``.

        Retorna ``False`` se o backpressure está ``PAUSED`` ou se ``size`` já
        alcançou o ``high_water_mark``; caso contrário ``True``. Útil para
        produtores síncronos que não usam ``put`` async.
        """
        with self._lock:
            return self._state is BackpressureState.NORMAL and size < self._config.high_water_mark

    async def wait_until_resumed(self, timeout: float | None = None) -> bool:
        """Aguarda até o estado voltar a ``NORMAL``.

        Args:
            timeout: Tempo máximo (segundos) de espera; ``None`` aguarda
                indefinidamente.

        Returns:
            ``True`` se retomado; ``False`` se o ``timeout`` expirou.
        """
        event = self._ensure_event()
        if not self.is_paused():
            return True
        if timeout is None:
            await event.wait()
            return True
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except TimeoutError:
            return False
        return True

    def _ensure_event(self) -> asyncio.Event:
        """Obtém (ou cria) o evento async vinculado ao loop corrente.

        Raises:
            RuntimeError: Se um loop diferente do que vinculou o controller
                tentar usar a espera async. O uso async é single-loop.
        """
        loop = asyncio.get_running_loop()
        with self._lock:
            if self._resume_event is None:
                self._loop = loop
                self._loop_thread = threading.current_thread()
                event = asyncio.Event()
                if self._state is BackpressureState.NORMAL:
                    event.set()
                self._resume_event = event
                return event
            if self._loop is not loop:
                raise RuntimeError("BackpressureController já vinculado a outro event loop")
            event = self._resume_event
            if event is None:
                raise RuntimeError("BackpressureController em estado inválido")
            return event

    def _set_event_locked(self) -> None:
        """Seta o evento de retomada (deve segurar o lock)."""
        event = self._resume_event
        loop = self._loop
        if event is None or loop is None or loop.is_closed():
            return
        if threading.current_thread() is self._loop_thread:
            event.set()
        else:
            loop.call_soon_threadsafe(event.set)

    def _clear_event_locked(self) -> None:
        """Limpa o evento de retomada (deve segurar o lock)."""
        event = self._resume_event
        loop = self._loop
        if event is None or loop is None or loop.is_closed():
            return
        if threading.current_thread() is self._loop_thread:
            event.clear()
        else:
            loop.call_soon_threadsafe(event.clear)


__all__ = ["BackpressureConfig", "BackpressureController", "BackpressureState"]
