"""Motor de validação declarativa por regras."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ValidationRule(Generic[T]):
    """Uma regra de validação nomeada.

    Attributes:
        name: Identificador estável da regra.
        predicate: Função que retorna ``True`` quando o valor é válido.
        error_msg: Mensagem de erro exibida quando a regra falha.
    """

    name: str
    predicate: Callable[[T], bool]
    error_msg: str


@dataclass(frozen=True, slots=True)
class ValidationResult(Generic[T]):
    """Resultado de uma validação (nunca ``None``)."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    value: T | None = None

    @property
    def is_valid(self) -> bool:
        return self.valid

    def __bool__(self) -> bool:
        return self.valid


class ValidationEngine:
    """Aplica um conjunto de regras a um valor, com opção de normalização."""

    def __init__(self) -> None:
        pass

    def validate(
        self,
        value: T,
        rules: Sequence[ValidationRule[T]],
        *,
        normalize: Callable[[T], T] | None = None,
    ) -> ValidationResult[T]:
        """Valida ``value`` contra ``rules``.

        Args:
            value: Valor candidato.
            rules: Regras a aplicar em ordem.
            normalize: Transformação aplicada antes de validar (se houver).

        Returns:
            Um ``ValidationResult`` com ``valid`` e a lista de erros.
        """
        if normalize is not None:
            normalized = normalize(value)
        else:
            normalized = value

        errors: list[str] = []
        for rule in rules:
            try:
                ok = rule.predicate(normalized)
            except Exception:
                ok = False
            if not ok:
                errors.append(rule.error_msg)

        return ValidationResult(valid=not errors, errors=errors, value=normalized)


__all__ = ["ValidationEngine", "ValidationResult", "ValidationRule"]