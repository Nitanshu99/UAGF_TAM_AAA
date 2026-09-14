"""aaa.api.routes.engagements — Engagement CRUD endpoints.

Endpoints
---------
GET  /api/v1/engagements          — list all engagements
POST /api/v1/engagements          — create a new engagement
GET  /api/v1/engagements/{id}     — get engagement by ID"""
from aaa.api.routes.engagements.get_engagement import get_engagement  # noqa: F401
from aaa.api.routes.engagements.router import (  # noqa: F401
    create_engagement,
    list_engagements,
    router,
)

__all__ = [
    'router',
    'list_engagements',
    'create_engagement',
    'get_engagement',
]
