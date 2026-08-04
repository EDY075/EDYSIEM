"""API v1 do EDY SIEM (FastAPI).

Endpoints:
- GET /api/v1/health
- GET /api/v1/version
- GET /api/v1/metrics
- POST /api/v1/pipeline/run
- POST /api/v1/alerts
- POST /api/v1/incidents
- POST /api/v1/cases

OpenAPI/Swagger em /docs e /redoc.
"""

from .app import create_app

__all__ = ["create_app"]
