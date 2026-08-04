"""Exceções do Correlation Engine.

Hierarquia de erros especifica para o framework de correlacao.
"""

from __future__ import annotations

from ..exceptions import EdysiemException


class CorrelationError(EdysiemException):
    """Erro base do Correlation Engine."""


class CorrelationRuleNotFoundError(CorrelationError):
    """Regra de correlacao nao encontrada no registry."""

    def __init__(self, rule_id: str) -> None:
        self.rule_id = rule_id
        super().__init__(f"Regra de correlacao '{rule_id}' nao encontrada")


class CorrelationRuleTimeoutError(CorrelationError):
    """Tempo de execucao da regra excedido."""

    def __init__(self, rule_id: str, timeout_seconds: float) -> None:
        self.rule_id = rule_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Regra '{rule_id}' excedeu timeout de {timeout_seconds}s")


class CorrelationRuleRegistrationError(CorrelationError):
    """Erro ao registrar regra (duplicada, invalida, etc.)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class CorrelationRuleDependencyError(CorrelationError):
    """Dependencia de regra nao satisfeita."""

    def __init__(self, rule_id: str, missing_dependency: str) -> None:
        self.rule_id = rule_id
        self.missing_dependency = missing_dependency
        super().__init__(
            f"Regra '{rule_id}' requer dependencia '{missing_dependency}' nao satisfeita"
        )


class CorrelationContextError(CorrelationError):
    """Erro no contexto de correlacao (estado de janela invalido)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


__all__ = [
    "CorrelationContextError",
    "CorrelationError",
    "CorrelationRuleDependencyError",
    "CorrelationRuleNotFoundError",
    "CorrelationRuleRegistrationError",
    "CorrelationRuleTimeoutError",
]
