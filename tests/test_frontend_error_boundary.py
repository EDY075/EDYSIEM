"""Regression guard for the user-safe React Router error surface."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_router_uses_safe_error_boundary_without_raw_router_copy() -> None:
    routes = (ROOT / "frontend" / "src" / "routing" / "routes.tsx").read_text(encoding="utf-8")
    boundary = (ROOT / "frontend" / "src" / "routing" / "RouteErrorBoundary.tsx").read_text(
        encoding="utf-8"
    )

    assert "errorElement: <RouteErrorBoundary />" in routes
    assert "Unexpected Application Error!" not in boundary
    assert "Tentar novamente" in boundary
    assert "Voltar ao Overview" in boundary
    assert "Nenhum dado operacional foi alterado" in boundary
