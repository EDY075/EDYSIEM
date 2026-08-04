"""Attachment Engine do Case Framework.

Permite anexar arquivos/URLs a um case (metadados - o conteudo pode
ser armazenado externamente).
"""

from __future__ import annotations

from dataclasses import replace

from .._utils import utcnow as _utcnow
from .models import Case, CaseAttachment
from .timeline import TimelineEngine


class AttachmentEngine:
    """Gerencia anexos de um case.

    Args:
        timeline: Engine de timeline (para auto-registro).
    """

    def __init__(self, timeline: TimelineEngine | None = None) -> None:
        self._timeline = timeline or TimelineEngine()

    def add(
        self,
        case: Case,
        name: str,
        *,
        content_type: str = "",
        size: int = 0,
        url: str = "",
        added_by: str = "system",
    ) -> Case:
        """Anexa um arquivo/URL ao case.

        Returns:
            ``Case`` atualizado com o anexo e registro na timeline.
        """
        attachment = CaseAttachment(
            name=name,
            content_type=content_type,
            size=size,
            url=url,
            added_by=added_by,
            created_at=_utcnow(),
        )
        updated = replace(case, attachments=(*case.attachments, attachment))
        return self._timeline.record_attachment(updated, name, actor=added_by)


__all__ = ["AttachmentEngine"]
