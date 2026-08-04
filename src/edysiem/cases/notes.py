"""Notes/Comment Engine do Case Framework.

Permite adicionar notas markdown com autor e data. O historico de
comentarios e imutavel (append-only).
"""

from __future__ import annotations

from dataclasses import replace

from .._utils import utcnow as _utcnow
from .models import Case, CaseComment
from .timeline import TimelineEngine


class CommentEngine:
    """Gerencia comentarios/notas markdown de um case.

    Args:
        timeline: Engine de timeline (para auto-registro).
    """

    def __init__(self, timeline: TimelineEngine | None = None) -> None:
        self._timeline = timeline or TimelineEngine()

    def add(self, case: Case, body: str, author: str) -> Case:
        """Adiciona uma nota markdown ao case.

        Returns:
            ``Case`` atualizado com o comentario e registro na timeline.
        """
        comment = CaseComment(body=body, author=author, created_at=_utcnow())
        updated = replace(case, comments=(*case.comments, comment))
        return self._timeline.record_comment(updated, author, snippet=body)

    def history(self, case: Case) -> tuple[CaseComment, ...]:
        """Retorna o historico de comentarios (mais recentes primeiro)."""
        return tuple(reversed(case.comments))


__all__ = ["CommentEngine"]
