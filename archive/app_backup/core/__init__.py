"""Núcleo do EDY SIEM — domínio puro, sem I/O (Clean Architecture)."""

from app.core.result import ErrorCode, Failure, Result, fail, success

__all__ = ["ErrorCode", "Failure", "Result", "success", "fail"]