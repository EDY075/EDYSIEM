"""Testes de borda da DSL (cobertura)."""

from __future__ import annotations

from edysiem.detection import (
    RuleCondition,
    RuleExpression,
    RuleLogicalOp,
    RuleOperator,
    parse_rule_text,
)


def test_condition_neq() -> None:
    cond = RuleCondition("category", RuleOperator.NEQ, "auth")
    assert cond.evaluate("network") is True
    assert cond.evaluate("auth") is False


def test_condition_gt_lt_lte() -> None:
    assert RuleCondition("n", RuleOperator.GT, 5).evaluate(6) is True
    assert RuleCondition("n", RuleOperator.GT, 5).evaluate(5) is False
    assert RuleCondition("n", RuleOperator.LT, 5).evaluate(4) is True
    assert RuleCondition("n", RuleOperator.LT, 5).evaluate(5) is False
    assert RuleCondition("n", RuleOperator.LTE, 5).evaluate(5) is True


def test_condition_compare_typeerror() -> None:
    # comparar tipos incompativeis nao levanta
    cond = RuleCondition("n", RuleOperator.GT, "abc")
    assert cond.evaluate(5) is False


def test_condition_contains_none_and_int() -> None:
    cond = RuleCondition("p", RuleOperator.CONTAINS, "x")
    assert cond.evaluate(None) is False
    assert cond.evaluate(123) is False


def test_condition_matches_none_and_bad_regex() -> None:
    cond = RuleCondition("u", RuleOperator.MATCHES, r"^admin")
    assert cond.evaluate(None) is False
    bad = RuleCondition("u", RuleOperator.MATCHES, "(")
    assert bad.evaluate("admin") is False


def test_expression_not_with_expression() -> None:
    inner = RuleExpression(condition=RuleCondition("cat", RuleOperator.EQ, "auth"))
    expr = RuleExpression(logical=RuleLogicalOp.NOT, operands=(inner,))
    assert expr.evaluate({"cat": "net"}) is True
    assert expr.evaluate({"cat": "auth"}) is False


def test_expression_and_empty_operands() -> None:
    expr = RuleExpression(logical=RuleLogicalOp.AND, operands=())
    assert expr.evaluate({}) is False


def test_parse_quoted_and_boolean() -> None:
    expr = parse_rule_text('WHEN event.user == "admin" THEN x()')
    assert expr.condition.value == "admin"

    expr2 = parse_rule_text("WHEN event.enabled == true THEN x()")
    assert expr2.condition.value is True


def test_parse_keyword_not_found() -> None:
    expr = parse_rule_text("event.category == auth")  # sem WHEN/THEN
    assert expr.condition is not None
    assert expr.condition.field == "category"


def test_parse_or_root() -> None:
    expr = parse_rule_text("WHEN event.category == auth OR event.category == network THEN x()")
    assert expr.logical is RuleLogicalOp.OR
    assert expr.evaluate({"category": "network"}) is True
    assert expr.evaluate({"category": "file"}) is False


def test_severity_ordering() -> None:
    cond = RuleCondition("severity", RuleOperator.GTE, "high")
    assert cond.evaluate("critical") is True
    assert cond.evaluate("low") is False
    assert cond.evaluate("HIGH") is True
