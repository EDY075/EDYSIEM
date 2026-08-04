"""Case Engine (Investigation Workspace) do EDY SIEM.

Camada operacional utilizada por um Analista SOC para investigar
incidentes: timeline, evidencias, notas, tarefas, ownership, anexos
e playbooks (estrutura - sem automacao ainda).

Fluxo:
    Incident -> CaseBuilder -> Case
    -> Timeline/Evidence/Notes/Tasks/Owners/Attachments -> Resolution
"""

from .attachments import AttachmentEngine
from .base import CaseProcessor
from .builder import CaseBuilder
from .context import CaseContext
from .engine import CaseEngine, CaseResult, CaseResultKind
from .evidence import EvidenceEngine
from .exceptions import (
    CaseBuilderError,
    CaseError,
    CaseInvalidStateTransition,
    CaseNotFoundError,
    CaseRegistrationError,
    CaseTaskNotFoundError,
)
from .models import (
    Case,
    CaseAttachment,
    CaseComment,
    CaseEvidence,
    CaseEvidenceKind,
    CaseMetrics,
    CaseOwner,
    CasePriority,
    CaseSeverity,
    CaseStatus,
    CaseTask,
    CaseTaskStatus,
    CaseTimelineEntry,
    Playbook,
    PlaybookStep,
)
from .notes import CommentEngine
from .owners import OwnerEngine
from .registry import CaseRegistry
from .tasks import TaskEngine
from .timeline import TimelineEngine

__all__ = [
    "AttachmentEngine",
    "Case",
    "CaseAttachment",
    "CaseBuilder",
    "CaseBuilderError",
    "CaseComment",
    "CaseContext",
    "CaseEngine",
    "CaseError",
    "CaseEvidence",
    "CaseEvidenceKind",
    "CaseInvalidStateTransition",
    "CaseMetrics",
    "CaseNotFoundError",
    "CaseOwner",
    "CasePriority",
    "CaseProcessor",
    "CaseRegistrationError",
    "CaseRegistry",
    "CaseResult",
    "CaseResultKind",
    "CaseSeverity",
    "CaseStatus",
    "CaseTask",
    "CaseTaskNotFoundError",
    "CaseTaskStatus",
    "CaseTimelineEntry",
    "CommentEngine",
    "EvidenceEngine",
    "OwnerEngine",
    "Playbook",
    "PlaybookStep",
    "TaskEngine",
    "TimelineEngine",
]
