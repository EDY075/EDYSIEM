"""DSL de regras de deteccao (arquitetura preparada para evolucao).

Define as estruturas e um parser minimo para condicoes declarativas.
O objetivo aqui e a ARQUITETURA: os blocos construtores (``RuleCondition``,
``RuleExpression``, ``RuleOperator``) sao reais e avaliaveis; o parser
reconhece a sintaxe basica ``WHEN ... AND ... THEN``.

Sintaxe suportada (v1, minima):

    WHEN
      event.category == authentication
    AND
      event.severity >= HIGH
    THEN
      raise_alert()

Em sprints futuras o parser evoluira para suportar Sigma, MITRE e
operadores complexos sem alterar o modelo ``RuleExpression``.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class RuleOperator(Enum):
    """Operadores de comparacao de uma condicao."""

    EQ = "=="
    NEQ = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    CONTAINS = "contains"
    IN = "in"
    MATCHES = "matches"

    @classmethod
    def from_token(cls, token: str) -> RuleOperator:
        """Converte um token textual em operador."""
        normalized = token.strip().lower()
        for op in cls:
            if op.value == token.strip() or op.name.lower() == normalized:
                return op
        raise ValueError(f"operador nao reconhecido: {token!r}")


class RuleLogicalOp(Enum):
    """Operadores logicos entre condicoes/expressoes."""

    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass(frozen=True, slots=True)
class RuleCondition:
    """Condicao atomica: ``field operator value``.

    Attributes:
        field: Campo do evento (ex.: ``"event_category"``).
        operator: Operador de comparacao.
        value: Valor esperado.
    """

    field: str
    operator: RuleOperator
    value: Any

    def __post_init__(self) -> None:
        if not self.field or not self.field.strip():
            raise ValueError("field nao pode ser vazio")

    def evaluate(self, actual: Any) -> bool:
        """Avalia a condicao contra o valor real do campo."""
        if self.operator is RuleOperator.EQ:
            return bool(actual == self.value)
        if self.operator is RuleOperator.NEQ:
            return bool(actual != self.value)
        if self.operator is RuleOperator.GT:
            return _compare(actual, self.value, lambda a, b: a > b)
        if self.operator is RuleOperator.GTE:
            return _compare(actual, self.value, lambda a, b: a >= b)
        if self.operator is RuleOperator.LT:
            return _compare(actual, self.value, lambda a, b: a < b)
        if self.operator is RuleOperator.LTE:
            return _compare(actual, self.value, lambda a, b: a <= b)
        if self.operator is RuleOperator.CONTAINS:
            return _contains(actual, self.value)
        if self.operator is RuleOperator.IN:
            return actual in self.value if isinstance(self.value, (list, tuple, set)) else False
        if self.operator is RuleOperator.MATCHES:
            return _matches(actual, self.value)
        return False


@dataclass(frozen=True, slots=True)
class RuleExpression:
    """Expressao logica composta por condicoes e/ou sub-expressoes.

    Uma folha (``logical=None``) contem exatamente uma ``condition``.
    Um no (``logical`` nao-None) combina ``operands``.

    Attributes:
        condition: Condicao atomica (quando folha).
        logical: Operador logico (quando no).
        operands: Sub-expressoes/condicoes (quando no).
    """

    condition: RuleCondition | None = None
    logical: RuleLogicalOp | None = None
    operands: tuple[RuleCondition | RuleExpression, ...] = ()

    def evaluate(self, values: dict[str, Any]) -> bool:
        """Avalia a expressao contra um mapa field->valor."""
        if self.logical is None and self.condition is not None:
            return self.condition.evaluate(values.get(self.condition.field))

        if not self.operands:
            return False

        if self.logical is RuleLogicalOp.NOT:
            op = self.operands[0]
            if isinstance(op, RuleCondition):
                return not op.evaluate(values.get(op.field))
            return not op.evaluate(values)

        results: list[bool] = []
        for op in self.operands:
            if isinstance(op, RuleCondition):
                results.append(op.evaluate(values.get(op.field)))
            else:
                results.append(op.evaluate(values))

        if self.logical is RuleLogicalOp.AND:
            return all(results)
        if self.logical is RuleLogicalOp.OR:
            return any(results)
        return False


# ---------------------------------------------------------------------------
# Helpers de comparacao
# ---------------------------------------------------------------------------

_SEVERITY_RANK: dict[str, int] = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def _compare(actual: Any, expected: Any, op: Callable[[Any, Any], bool]) -> bool:
    """Compara ``actual`` e ``expected`` com ``op``; ``None`` nunca compara."""
    if actual is None or expected is None:
        return False
    # Ordenacao ordinal para severidades (string -> rank)
    if isinstance(actual, str) and isinstance(expected, str):
        a_rank = _SEVERITY_RANK.get(actual.lower())
        e_rank = _SEVERITY_RANK.get(expected.lower())
        if a_rank is not None and e_rank is not None:
            return op(a_rank, e_rank)
    try:
        return op(actual, expected)
    except TypeError:
        return False


def _contains(actual: Any, expected: Any) -> bool:
    """Verifica se ``actual`` contem ``expected`` (string/lista/set)."""
    if actual is None:
        return False
    if isinstance(actual, (list, tuple, set)):
        return expected in actual
    if isinstance(actual, str):
        return str(expected) in actual
    return False


def _matches(actual: Any, pattern: str) -> bool:
    """Verifica se ``actual`` casa com a regex ``pattern``."""
    if actual is None:
        return False
    try:
        return re.search(pattern, str(actual)) is not None
    except re.error:
        return False


# ---------------------------------------------------------------------------
# Parser minimo
# ---------------------------------------------------------------------------

_CONDITION_RE = re.compile(
    r"^\s*(event\.)?([\w_]+)\s*(==|!=|>=|<=|>|<|contains|in|matches)\s*(.+?)\s*$"
)


def _parse_condition(token: str) -> RuleCondition:
    """Converte um token textual em ``RuleCondition``."""
    match = _CONDITION_RE.match(token)
    if match is None:
        raise ValueError(f"condicao nao reconhecida: {token!r}")

    field = match.group(2)
    operator = RuleOperator.from_token(match.group(3))
    raw_value = match.group(4).strip()

    value: Any = raw_value
    # Normaliza valores: inteiro, float, boolean, entre aspas
    lowered = raw_value.lower()
    if raw_value.startswith('"') and raw_value.endswith('"'):
        value = raw_value[1:-1]
    elif lowered == "true":
        value = True
    elif lowered == "false":
        value = False
    else:
        try:
            value = int(raw_value)
        except ValueError:
            try:
                value = float(raw_value)
            except ValueError:
                value = raw_value

    return RuleCondition(field=field, operator=operator, value=value)


def parse_rule_text(text: str) -> RuleExpression:
    """Parseia a sintaxe basica da DSL em uma ``RuleExpression``.

    Suporta: ``WHEN <cond> [AND|OR <cond>]* THEN <acao>``.
    A acao (``THEN ...``) e ignorada na v1 (apenas arquitetura).

    Raises:
        ValueError: Se a sintaxe nao for reconhecida.
    """
    normalized = text.strip()

    # Remove bloco THEN (acao) - v1 nao executa acoes
    then_idx = _find_keyword(normalized, "THEN")
    if then_idx >= 0:
        normalized = normalized[:then_idx].strip()

    # Remove bloco WHEN (opcional)
    when_idx = _find_keyword(normalized, "WHEN")
    if when_idx >= 0:
        normalized = normalized[when_idx + len("WHEN") :].strip()

    if not normalized:
        raise ValueError("expressao vazia apos remover WHEN/THEN")

    # Separa por AND/OR em nivel raiz
    operands = _split_logical(normalized)
    if len(operands) == 1:
        return _parse_operand(operands[0])

    op = _root_logical(normalized)
    parsed_ops: list[RuleCondition | RuleExpression] = [
        _parse_operand(operand) for operand in operands
    ]

    return RuleExpression(logical=op, operands=tuple(parsed_ops))


def _parse_operand(token: str) -> RuleExpression:
    """Converte um token em expressao (condicao ou NOT)."""
    if token.upper().startswith("NOT "):
        inner = _parse_condition(token[4:].strip())
        return RuleExpression(logical=RuleLogicalOp.NOT, operands=(inner,))
    return RuleExpression(condition=_parse_condition(token))


def evaluate_expression(expression: RuleExpression, values: dict[str, Any]) -> bool:
    """Avalia uma expressao contra um mapa field->valor (conveniencia)."""
    return expression.evaluate(values)


# ---------------------------------------------------------------------------
# Helpers do parser
# ---------------------------------------------------------------------------


def _find_keyword(text: str, keyword: str) -> int:
    """Encontra um keyword isolado (palavra inteira) no texto."""
    for match in re.finditer(rf"\b{keyword}\b", text, flags=re.IGNORECASE):
        return match.start()
    return -1


def _split_logical(text: str) -> list[str]:
    """Divide o texto pelas palavras-chave AND/OR (nivel raiz)."""
    parts = re.split(r"\b(AND|OR)\b", text, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip() and p.upper() not in ("AND", "OR")]


def _root_logical(text: str) -> RuleLogicalOp:
    """Detecta o operador logico raiz (AND/OR)."""
    if re.search(r"\bAND\b", text, flags=re.IGNORECASE):
        return RuleLogicalOp.AND
    if re.search(r"\bOR\b", text, flags=re.IGNORECASE):
        return RuleLogicalOp.OR
    return RuleLogicalOp.AND


__all__ = [
    "RuleCondition",
    "RuleExpression",
    "RuleLogicalOp",
    "RuleOperator",
    "evaluate_expression",
    "parse_rule_text",
]
