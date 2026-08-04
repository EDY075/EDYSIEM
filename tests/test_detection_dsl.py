"""Testes da DSL de regras de deteccao."""

from __future__ import annotations

import pytest

from edysiem.detection import (
    RuleCondition,
    RuleExpression,
    RuleLogicalOp,
    RuleOperator,
    evaluate_expression,
    parse_rule_text,
)


def test_rule_operator_enum() -> None:
    assert RuleOperator.EQ.value == "=="
    assert RuleOperator.GTE.value == ">="
    assert RuleOperator.CONTAINS.value == "contains"


def test_rule_operator_from_token() -> None:
    assert RuleOperator.from_token("==") is RuleOperator.EQ
    assert RuleOperator.from_token(">=") is RuleOperator.GTE
    assert RuleOperator.from_token("contains") is RuleOperator.CONTAINS
    assert RuleOperator.from_token("MATCHES") is RuleOperator.MATCHES
    with pytest.raises(ValueError, match="operador nao reconhecido"):
        RuleOperator.from_token("~=")


def test_rule_condition_eq() -> None:
    cond = RuleCondition(field="event_category", operator=RuleOperator.EQ, value="auth")
    assert cond.evaluate("auth") is True
    assert cond.evaluate("network") is False


def test_rule_condition_gte() -> None:
    cond = RuleCondition(field="severity", operator=RuleOperator.GTE, value=3)
    assert cond.evaluate(3) is True
    assert cond.evaluate(4) is True
    assert cond.evaluate(2) is False
    assert cond.evaluate(None) is False


def test_rule_condition_contains() -> None:
    cond = RuleCondition(field="process", operator=RuleOperator.CONTAINS, value="powershell")
    assert cond.evaluate("powershell.exe -enc") is True
    assert cond.evaluate("cmd.exe") is False
    assert cond.evaluate(["powershell", "cmd"]) is True  # valor na lista


def test_rule_condition_in() -> None:
    cond = RuleCondition(field="event_action", operator=RuleOperator.IN, value=("reject", "failed"))
    assert cond.evaluate("reject") is True
    assert cond.evaluate("accept") is False


def test_rule_condition_matches() -> None:
    cond = RuleCondition(field="user", operator=RuleOperator.MATCHES, value=r"^admin")
    assert cond.evaluate("admin01") is True
    assert cond.evaluate("user02") is False


def test_rule_condition_requires_field() -> None:
    with pytest.raises(ValueError, match="field nao pode ser vazio"):
        RuleCondition(field="", operator=RuleOperator.EQ, value=1)


def test_rule_expression_single_condition() -> None:
    expr = RuleExpression(
        condition=RuleCondition(field="category", operator=RuleOperator.EQ, value="auth")
    )
    assert expr.evaluate({"category": "auth"}) is True
    assert expr.evaluate({"category": "net"}) is False


def test_rule_expression_and() -> None:
    expr = RuleExpression(
        logical=RuleLogicalOp.AND,
        operands=(
            RuleCondition("category", RuleOperator.EQ, "auth"),
            RuleCondition("severity", RuleOperator.GTE, 3),
        ),
    )
    assert expr.evaluate({"category": "auth", "severity": 3}) is True
    assert expr.evaluate({"category": "auth", "severity": 2}) is False
    assert expr.evaluate({"category": "net", "severity": 4}) is False


def test_rule_expression_or() -> None:
    expr = RuleExpression(
        logical=RuleLogicalOp.OR,
        operands=(
            RuleCondition("category", RuleOperator.EQ, "auth"),
            RuleCondition("category", RuleOperator.EQ, "network"),
        ),
    )
    assert expr.evaluate({"category": "auth"}) is True
    assert expr.evaluate({"category": "network"}) is True
    assert expr.evaluate({"category": "file"}) is False


def test_rule_expression_not() -> None:
    expr = RuleExpression(
        logical=RuleLogicalOp.NOT,
        operands=(RuleCondition("category", RuleOperator.EQ, "auth"),),
    )
    assert expr.evaluate({"category": "net"}) is True
    assert expr.evaluate({"category": "auth"}) is False


def test_rule_expression_empty() -> None:
    expr = RuleExpression()
    assert expr.evaluate({}) is False


def test_parse_rule_text_simple() -> None:
    expr = parse_rule_text("WHEN event.category == authentication THEN raise_alert()")
    assert expr.condition is not None
    assert expr.condition.field == "category"
    assert expr.condition.value == "authentication"


def test_parse_rule_text_and() -> None:
    expr = parse_rule_text(
        "WHEN event.category == authentication AND event.severity >= HIGH THEN raise_alert()"
    )
    assert expr.logical is RuleLogicalOp.AND
    assert len(expr.operands) == 2

    values = {"category": "authentication", "severity": "HIGH"}
    assert evaluate_expression(expr, values) is True

    values2 = {"category": "authentication", "severity": "LOW"}
    assert evaluate_expression(expr, values2) is False


def test_parse_rule_text_number_values() -> None:
    expr = parse_rule_text("WHEN event.risk_score >= 60 THEN raise_alert()")
    assert expr.condition.value == 60


def test_parse_rule_text_not() -> None:
    expr = parse_rule_text("WHEN NOT event.category == authentication THEN raise_alert()")
    # NOT e tratado como operando com NOT logico
    assert expr.logical is not None


def test_parse_rule_text_invalid() -> None:
    with pytest.raises(ValueError, match="condicao nao reconhecida"):
        parse_rule_text("WHEN whatever THEN raise_alert()")


def test_parse_rule_text_empty() -> None:
    with pytest.raises(ValueError, match="expressao vazia"):
        parse_rule_text("WHEN THEN raise_alert()")
