"""Risk Engine do Alert Framework.

Calcula o ``risk_score`` de um alerta a partir de multiplos fatores.
Simples na v1, mas preparado para evolucao (asset criticality,
threat intel, contexto de rede, etc.).

Cada ``RiskFactor`` contribui com um peso (0.0-1.0) e um peso relativo.
O score final e a soma ponderada normalizada para 0-100.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..domain import RiskScore
from .models import AlertSeverity


@dataclass(frozen=True, slots=True)
class RiskFactor:
    """Fator de risco com contribuicao.

    Attributes:
        name: Nome do fator.
        score: Contribuicao do fator (0.0-1.0).
        weight: Peso relativo do fator no score final.
    """

    name: str
    score: float
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"score deve estar entre 0.0 e 1.0; recebido {self.score}")
        if self.weight < 0:
            raise ValueError(f"weight nao pode ser negativo; recebido {self.weight}")
        if not self.name or not self.name.strip():
            raise ValueError("name nao pode ser vazio")


class RiskEngine:
    """Calcula o risk_score agregado de um alerta.

    O score e a soma ponderada dos fatores normalizada para 0-100.
    Com nenhum fator, retorna o score base (ex.: 0).
    """

    def __init__(self, base_score: int = 0) -> None:
        if not 0 <= base_score <= 100:
            raise ValueError(f"base_score deve estar entre 0 e 100; recebido {base_score}")
        self._base = base_score

    def evaluate(
        self,
        *,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        confidence: float = 1.0,
        additional_factors: tuple[RiskFactor, ...] = (),
    ) -> RiskScore:
        """Calcula o risco a partir de severidade, confianca e fatores extras.

        Args:
            severity: Severidade do alerta.
            confidence: Confianca da deteccao (0.0-1.0).
            additional_factors: Fatores adicionais (asset criticality, intel, ...).

        Returns:
            ``RiskScore`` (0-100).
        """
        factors = [
            RiskFactor(name="severity", score=_severity_score(severity), weight=3.0),
            RiskFactor(name="confidence", score=confidence, weight=1.0),
            *additional_factors,
        ]

        total_weight = sum(f.weight for f in factors)
        if total_weight <= 0:
            return RiskScore(self._base)

        weighted = sum(f.score * f.weight for f in factors) / total_weight
        score = round(self._base + weighted * (100 - self._base))
        return RiskScore(max(0, min(100, score)))

    def factor_from_asset_criticality(self, criticality: int) -> RiskFactor:
        """Cria um fator de risco a partir da criticalidade de um ativo (0-100)."""
        if not 0 <= criticality <= 100:
            raise ValueError(f"criticality deve estar entre 0 e 100; recebido {criticality}")
        return RiskFactor(name="asset_criticality", score=criticality / 100.0, weight=2.0)

    def factor_from_intel(self, intel_score: float) -> RiskFactor:
        """Cria um fator de risco a partir de intel (0.0-1.0)."""
        if not 0.0 <= intel_score <= 1.0:
            raise ValueError(f"intel_score deve estar entre 0.0 e 1.0; recebido {intel_score}")
        return RiskFactor(name="threat_intel", score=intel_score, weight=2.5)


def _severity_score(severity: AlertSeverity) -> float:
    """Converte severidade em score 0.0-1.0."""
    return severity.rank / 4.0


__all__ = ["RiskEngine", "RiskFactor", "_severity_score"]
