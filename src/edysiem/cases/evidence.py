"""Evidence Engine do Case Framework.

Permite anexar evidencias a um case: logs, hashes, IPs, dominios,
arquivos, prints, JSON, IOCs e links.
"""

from __future__ import annotations

from dataclasses import replace

from .._utils import utcnow as _utcnow
from .models import Case, CaseEvidence, CaseEvidenceKind
from .timeline import TimelineEngine


class EvidenceEngine:
    """Anexa evidencias a um case e registra na timeline.

    Args:
        timeline: Engine de timeline (para auto-registro).
    """

    def __init__(self, timeline: TimelineEngine | None = None) -> None:
        self._timeline = timeline or TimelineEngine()

    def add(
        self,
        case: Case,
        kind: CaseEvidenceKind,
        value: str,
        *,
        label: str = "",
        source: str = "analyst",
        actor: str = "system",
    ) -> Case:
        """Anexa uma evidencia ao case.

        Returns:
            ``Case`` atualizado com a evidencia e registro na timeline.
        """
        evidence = CaseEvidence(
            kind=kind,
            value=value,
            label=label,
            source=source,
            created_at=_utcnow(),
        )
        updated = replace(case, evidences=(*case.evidences, evidence))
        return self._timeline.record(
            updated, "evidence", f"Evidencia '{label or value[:40]}' anexada", actor
        )

    def add_hash(self, case: Case, value: str, *, label: str = "", actor: str = "system") -> Case:
        """Anexa um hash (ex.: SHA-256)."""
        return self.add(case, CaseEvidenceKind.HASH, value, label=label, actor=actor)

    def add_ip(self, case: Case, value: str, *, label: str = "", actor: str = "system") -> Case:
        """Anexa um endereco IP."""
        return self.add(case, CaseEvidenceKind.IP, value, label=label, actor=actor)

    def add_domain(self, case: Case, value: str, *, label: str = "", actor: str = "system") -> Case:
        """Anexa um dominio."""
        return self.add(case, CaseEvidenceKind.DOMAIN, value, label=label, actor=actor)

    def add_log(self, case: Case, value: str, *, label: str = "", actor: str = "system") -> Case:
        """Anexa um trecho de log."""
        return self.add(case, CaseEvidenceKind.LOG, value, label=label, actor=actor)

    def add_ioc(self, case: Case, value: str, *, label: str = "", actor: str = "system") -> Case:
        """Anexa um IOC."""
        return self.add(case, CaseEvidenceKind.IOC, value, label=label, actor=actor)

    def add_json(self, case: Case, value: str, *, label: str = "", actor: str = "system") -> Case:
        """Anexa um bloco JSON (string)."""
        return self.add(case, CaseEvidenceKind.JSON, value, label=label, actor=actor)

    def add_link(self, case: Case, value: str, *, label: str = "", actor: str = "system") -> Case:
        """Anexa um link/URL."""
        return self.add(case, CaseEvidenceKind.LINK, value, label=label, actor=actor)


__all__ = ["EvidenceEngine"]
