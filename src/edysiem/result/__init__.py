"""Resultados tipados e erros do EDY SIEM.

Este pacote fornece o tipo ``Result[T]`` (algebra de soma entre sucesso e
falha) e a hierarquia base de ``Error``/``ErrorCode`` usada em todo o núcleo.
"""

from .errors import Error, ErrorCode
from .result import (
    Failure,
    Result,
    ResultUnwrapError,
    Success,
    and_then,
    err,
    from_exc,
    ok,
)

__all__ = [
    "Error",
    "ErrorCode",
    "Failure",
    "Result",
    "ResultUnwrapError",
    "Success",
    "and_then",
    "err",
    "from_exc",
    "ok",
]