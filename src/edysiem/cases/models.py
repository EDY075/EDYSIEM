"""Modelos do Case Engine (Investigation Workspace).

Define o modelo ``Case``, o ciclo de vida, prioridade, evidencia,
tarefa, comentario, anexo, owner, timeline, playbook e metricas.
Todos imutaveis (frozen=True, slots=True) seguindo o padrao do projeto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .._utils import new_id as _new_id
from .._utils import utcnow as _utcnow
from ..domain import RiskScore


class CaseSeverity(Enum):
    """Severidade operacional de um case."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        return {
            CaseSeverity.INFO: 0,
            CaseSeverity.LOW: 1,
            CaseSeverity.MEDIUM: 2,
            CaseSeverity.HIGH: 3,
            CaseSeverity.CRITICAL: 4,
        }[self]


class CasePriority(Enum):
    """Prioridade de resposta de um case."""

    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    P4 = "p4"
    P5 = "p5"

    @property
    def rank(self) -> int:
        return {
            CasePriority.P1: 0,
            CasePriority.P2: 1,
            CasePriority.P3: 2,
            CasePriority.P4: 3,
            CasePriority.P5: 4,
        }[self]


# Transicoes validas do ciclo de vida (nivel de modulo).
_CASE_TRANSITIONS: dict[str, frozenset[str]] = {
    "open": frozenset({"in_progress", "resolved", "closed"}),
    "in_progress": frozenset({"on_hold", "resolved", "closed"}),
    "on_hold": frozenset({"in_progress", "resolved", "closed"}),
    "resolved": frozenset({"closed", "reopened"}),
    "closed": frozenset({"reopened"}),
    "reopened": frozenset({"in_progress", "on_hold"}),
}


class CaseStatus(Enum):
    """Estado do ciclo de vida de um case de investigacao."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"

    def can_transition_to(self, target: CaseStatus) -> bool:
        """Verifica se a transicao para ``target`` e valida."""
        allowed = _CASE_TRANSITIONS.get(self.value, frozenset())
        return target.value in allowed


class CaseTaskStatus(Enum):
    """Estado de uma tarefa de investigacao."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REOPENED = "reopened"


class CaseEvidenceKind(Enum):
    """Tipo de evidencia anexada a um case."""

    LOG = "log"
    HASH = "hash"
    IP = "ip"
    DOMAIN = "domain"
    FILE = "file"
    SCREENSHOT = "screenshot"
    JSON = "json"
    IOC = "ioc"
    LINK = "link"


@dataclass(frozen=True, slots=True)
class CaseTimelineEntry:
    """Entrada imutavel na timeline de um case.

    Attributes:
        action: Acao registrada (ex.: "created", "status_change").
        detail: Detalhe da acao.
        actor: Ator responsavel.
        created_at: Carimbo (UTC).
    """

    action: str
    detail: str = ""
    actor: str = "system"
    created_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class CaseEvidence:
    """Evidencia anexada a um case.

    Attributes:
        kind: Tipo de evidencia (log/hash/ip/domain/file/screenshot/json/ioc/link).
        value: Valor da evidencia (ex.: hash, IP, texto de log).
        label: Rotulo legivel.
        source: Origem da evidencia (ex.: "incident", "analyst").
        created_at: Carimbo (UTC).
    """

    kind: CaseEvidenceKind
    value: str
    label: str = ""
    source: str = "analyst"
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("value nao pode ser vazio")


@dataclass(frozen=True, slots=True)
class CaseComment:
    """Comentario/nota markdown em um case.

    Attributes:
        body: Conteudo (Markdown).
        author: Autor da nota.
        created_at: Carimbo (UTC).
    """

    body: str
    author: str
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.body or not self.body.strip():
            raise ValueError("body nao pode ser vazio")
        if not self.author or not self.author.strip():
            raise ValueError("author nao pode ser vazio")


@dataclass(frozen=True, slots=True)
class CaseTask:
    """Tarefa de investigacao.

    Attributes:
        title: Titulo da tarefa.
        status: Estado da tarefa.
        priority: Prioridade da tarefa.
        assignee: Responsavel pela tarefa.
        due_at: Prazo (UTC), se houver.
        created_by: Quem criou.
        id: Identificador unico (auto-gerado).
        created_at: Carimbo (UTC).
    """

    title: str
    status: CaseTaskStatus = CaseTaskStatus.PENDING
    priority: CasePriority = CasePriority.P3
    assignee: str | None = None
    due_at: datetime | None = None
    created_by: str = "system"
    id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("title nao pode ser vazio")


@dataclass(frozen=True, slots=True)
class CaseAttachment:
    """Anexo a um case (arquivo/URL/metadados).

    Attributes:
        name: Nome do anexo.
        content_type: Tipo MIME (se aplicavel).
        size: Tamanho em bytes (se aplicavel).
        url: URL do anexo (se armazenado externo).
        added_by: Quem anexou.
        created_at: Carimbo (UTC).
    """

    name: str
    content_type: str = ""
    size: int = 0
    url: str = ""
    added_by: str = "system"
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("name nao pode ser vazio")


@dataclass(frozen=True, slots=True)
class CaseOwner:
    """Registro de ownership (responsavel) de um case.

    Attributes:
        owner: Responsavel atual.
        previous: Responsavel anterior (None se inicial).
        assigned_by: Quem transferiu.
        created_at: Carimbo (UTC).
    """

    owner: str
    previous: str | None = None
    assigned_by: str = "system"
    created_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True, slots=True)
class PlaybookStep:
    """Passo de um playbook (estrutura - ainda sem automacao).

    Attributes:
        order: Ordem do passo.
        title: Titulo do passo.
        description: Descricao/acao esperada.
    """

    order: int
    title: str
    description: str = ""

    def __post_init__(self) -> None:
        if self.order < 1:
            raise ValueError(f"order deve ser >= 1; recebido {self.order}")
        if not self.title or not self.title.strip():
            raise ValueError("title nao pode ser vazio")


@dataclass(frozen=True, slots=True)
class Playbook:
    """Estrutura de um playbook de resposta (sem automacao ainda).

    Attributes:
        name: Nome do playbook.
        steps: Passos ordenados do playbook.
        description: Descricao.
    """

    name: str
    steps: tuple[PlaybookStep, ...] = ()
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("name nao pode ser vazio")


@dataclass(frozen=True, slots=True)
class Case:
    """Case de investigacao (workspace do analista SOC).

    Attributes:
        title: Titulo do case.
        description: Descricao.
        owner: Responsavel pelo case.
        status: Estado do ciclo de vida.
        severity: Severidade.
        priority: Prioridade.
        risk_score: Pontuacao de risco (0-100).
        incident_id: Incidente de origem.
        alerts: IDs de alertas relacionados.
        assets: Ativos envolvidos.
        users: Usuarios envolvidos.
        iocs: IOCs envolvidos.
        mitre: Referencias MITRE.
        timeline: Historico imutavel de acoes.
        comments: Notas markdown.
        attachments: Anexos.
        tasks: Tarefas.
        evidences: Evidencias.
        playbook: Playbook de resposta (estrutura).
        resolution: Descricao da resolucao.
        id: Identificador unico (auto-gerado).
        created_at: Carimbo de criacao (UTC).
        updated_at: Carimbo de ultima atualizacao (UTC).
        closed_at: Data de fechamento (UTC).
    """

    title: str
    description: str = ""
    owner: str | None = None
    status: CaseStatus = CaseStatus.OPEN
    severity: CaseSeverity = CaseSeverity.MEDIUM
    priority: CasePriority = CasePriority.P3
    risk_score: RiskScore = RiskScore(50)  # noqa: RUF009
    incident_id: str | None = None
    alerts: tuple[str, ...] = ()
    assets: frozenset[str] = frozenset()
    users: frozenset[str] = frozenset()
    iocs: frozenset[str] = frozenset()
    mitre: frozenset[str] = frozenset()
    timeline: tuple[CaseTimelineEntry, ...] = ()
    comments: tuple[CaseComment, ...] = ()
    attachments: tuple[CaseAttachment, ...] = ()
    tasks: tuple[CaseTask, ...] = ()
    evidences: tuple[CaseEvidence, ...] = ()
    playbook: Playbook | None = None
    resolution: str = ""
    id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
    closed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("title nao pode ser vazio")


@dataclass(slots=True)
class CaseMetrics:
    """Metricas agregadas do Case Engine (mutavel, nao frozen)."""

    total_created: int = 0
    total_transitions: int = 0
    total_comments: int = 0
    total_evidences: int = 0
    total_tasks_created: int = 0
    total_tasks_completed: int = 0
    total_owner_changes: int = 0
    last_updated: datetime = field(default_factory=_utcnow)


__all__ = [
    "Case",
    "CaseAttachment",
    "CaseComment",
    "CaseEvidence",
    "CaseEvidenceKind",
    "CaseMetrics",
    "CaseOwner",
    "CasePriority",
    "CaseSeverity",
    "CaseStatus",
    "CaseTask",
    "CaseTaskStatus",
    "CaseTimelineEntry",
    "Playbook",
    "PlaybookStep",
]
