"""Grouping do Incident Engine.

Define os criterios configuraveis de agrupamento de alertas e o
algoritmo de agrupamento. Nada hardcoded: todos os criterios, a
janela temporal e a pontuacao minima sao configuraveis via
``GroupingConfig``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..alerts import Alert
from .models import IncidentFingerprint


class GroupingCriterion(Enum):
    """Criterios de agrupamento de alertas em um incidente."""

    ASSET = "asset"
    USER = "user"
    IOC = "ioc"
    RULE = "rule"
    FINGERPRINT = "fingerprint"
    TIME_WINDOW = "time_window"
    MITRE = "mitre"

    @property
    def weight(self) -> int:
        """Peso do criterio na pontuacao."""
        return {
            GroupingCriterion.ASSET: 20,
            GroupingCriterion.USER: 20,
            GroupingCriterion.IOC: 25,
            GroupingCriterion.RULE: 20,
            GroupingCriterion.FINGERPRINT: 30,
            GroupingCriterion.TIME_WINDOW: 10,
            GroupingCriterion.MITRE: 20,
        }[self]


@dataclass(frozen=True, slots=True)
class GroupingConfig:
    """Configuracao do agrupamento de alertas.

    Attributes:
        enabled_criteria: Criterios ativos. Vazio = todos.
        time_window_seconds: Janela temporal para considerar alertas
            relacionados.
        min_score: Pontuacao minima para agrupar (0-100).
        group_by: Chave de agrupamento (ex.: ``"rule"``) para o fingerprint
            do incidente.
    """

    enabled_criteria: frozenset[GroupingCriterion] = frozenset()
    time_window_seconds: float = 3600.0
    min_score: int = 40
    group_by: str = "rule"

    def __post_init__(self) -> None:
        if self.time_window_seconds <= 0:
            raise ValueError(
                f"time_window_seconds deve ser > 0; recebido {self.time_window_seconds}"
            )
        if not 0 <= self.min_score <= 100:
            raise ValueError(f"min_score deve estar entre 0 e 100; recebido {self.min_score}")

    def active(self, criterion: GroupingCriterion) -> bool:
        """Verifica se um criterio esta ativo."""
        if not self.enabled_criteria:
            return True  # vazio = todos ativos
        return criterion in self.enabled_criteria


@dataclass(frozen=True, slots=True)
class IncidentGroup:
    """Grupo de alertas que formam um incidente.

    Attributes:
        alerts: Alertas agrupados.
        matched_criteria: Criterios que coincidiram.
        score: Pontuacao de agrupamento (0-100).
        fingerprint: Fingerprint do incidente (deterministico).
    """

    alerts: tuple[Alert, ...]
    matched_criteria: frozenset[GroupingCriterion]
    score: int
    fingerprint: IncidentFingerprint

    def __post_init__(self) -> None:
        if not self.alerts:
            raise ValueError("grupo vazio de alertas")


class GroupingEngine:
    """Agrupa alertas em um ``IncidentGroup`` com base na configuracao.

    O agrupamento usa uma chave principal (``group_by``) e verifica os
    criterios ativos. A pontuacao e a soma dos pesos dos criterios que
    coincidiram, normalizada.
    """

    def __init__(self, config: GroupingConfig | None = None) -> None:
        self._config = config or GroupingConfig()

    @property
    def config(self) -> GroupingConfig:
        """Configuracao de agrupamento."""
        return self._config

    def group(self, alerts: list[Alert]) -> IncidentGroup | None:
        """Agrupa a lista de alertas em um incidente.

        Args:
            alerts: Alertas candidatos.

        Returns:
            ``IncidentGroup`` se a pontuacao >= min_score; ``None`` se nao.
        """
        if len(alerts) < 2:
            return None

        matched = self._match_criteria(alerts)
        score = self._compute_score(matched)
        if score < self._config.min_score:
            return None

        fingerprint = self._compute_fingerprint(alerts)

        return IncidentGroup(
            alerts=tuple(alerts),
            matched_criteria=matched,
            score=score,
            fingerprint=fingerprint,
        )

    def _match_criteria(self, alerts: list[Alert]) -> frozenset[GroupingCriterion]:
        """Verifica quais criterios coincidem entre todos os alertas."""
        matched: set[GroupingCriterion] = set()
        cfg = self._config

        if cfg.active(GroupingCriterion.RULE):
            rules = {a.rule_id for a in alerts}
            if len(rules) == 1:
                matched.add(GroupingCriterion.RULE)

        if cfg.active(GroupingCriterion.ASSET):
            assets = {a.asset_id for a in alerts if a.asset_id}
            if len(assets) == 1:
                matched.add(GroupingCriterion.ASSET)

        if cfg.active(GroupingCriterion.USER):
            users = {a.user for a in alerts if a.user}
            if len(users) == 1:
                matched.add(GroupingCriterion.USER)

        if cfg.active(GroupingCriterion.IOC):
            iocs = {ioc for a in alerts for ioc in a.ioc_ids}
            if iocs and len(iocs) >= 1:
                matched.add(GroupingCriterion.IOC)

        if cfg.active(GroupingCriterion.MITRE):
            mitres = {m for a in alerts for m in a.mitre}
            if mitres and len(mitres) >= 1:
                matched.add(GroupingCriterion.MITRE)

        if cfg.active(GroupingCriterion.FINGERPRINT):
            fps = {a.fingerprint.hash for a in alerts if a.fingerprint}
            if len(fps) == 1:
                matched.add(GroupingCriterion.FINGERPRINT)

        if cfg.active(GroupingCriterion.TIME_WINDOW):
            if self._within_time_window(alerts):
                matched.add(GroupingCriterion.TIME_WINDOW)

        return frozenset(matched)

    def _within_time_window(self, alerts: list[Alert]) -> bool:
        """Verifica se os alertas estao dentro da janela temporal."""
        if len(alerts) < 2:
            return False
        first = min(a.first_seen for a in alerts)
        last = max(a.last_seen for a in alerts)
        return (last - first).total_seconds() <= self._config.time_window_seconds

    def _compute_score(self, matched: frozenset[GroupingCriterion]) -> int:
        """Pontuacao ponderada dos criterios coincidentes (0-100)."""
        total_weight = sum(c.weight for c in GroupingCriterion)
        matched_weight = sum(c.weight for c in matched)
        return round(matched_weight / total_weight * 100)

    def _compute_fingerprint(self, alerts: list[Alert]) -> IncidentFingerprint:
        """Fingerprint deterministico baseado na chave de agrupamento."""
        import hashlib
        import json

        key = self._config.group_by
        values: dict[str, Any] = {}
        if key == "rule":
            values["rule"] = alerts[0].rule_id
        elif key == "asset":
            values["asset"] = alerts[0].asset_id
        elif key == "user":
            values["user"] = alerts[0].user
        else:
            values["key"] = key

        payload = json.dumps(values, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

        return IncidentFingerprint(hash=digest, key=key)


__all__ = ["GroupingConfig", "GroupingCriterion", "GroupingEngine", "IncidentGroup"]
