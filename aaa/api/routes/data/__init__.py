"""aaa.api.routes.data — REST endpoints for querying the file-based data store.

These endpoints let the user retrieve what they entered (inputs) and what the
audit produced (results) from the persistent ``data/`` folder.

Endpoints
---------
GET  /api/v1/data/engagements                     — index: all stored engagements
GET  /api/v1/data/engagements/{id}/input          — stored user inputs (engagement + intake + files)
GET  /api/v1/data/engagements/{id}/input/engagement  — engagement creation record
GET  /api/v1/data/engagements/{id}/input/intake      — Stage A/B/C payload
GET  /api/v1/data/engagements/{id}/input/files       — uploaded-file metadata list
GET  /api/v1/data/engagements/{id}/result         — full audit result (verdict + KPIs + artefacts + findings)
GET  /api/v1/data/engagements/{id}/result/summary — verdict + KPIs only
GET  /api/v1/data/engagements/{id}/result/findings   — blocking / positive findings
GET  /api/v1/data/engagements/{id}/result/compliance — compliance matrix
GET  /api/v1/data/results                         — index: only completed engagements"""
from aaa.api.routes.data.get_result import (  # noqa: F401
    get_result,
    get_result_compliance,
    get_result_findings,
    get_result_summary,
)
from aaa.api.routes.data.router import (  # noqa: F401
    get_input,
    get_input_engagement,
    get_input_files,
    get_input_intake,
    list_stored_engagements,
    list_stored_results,
    router,
)

__all__ = [
    'router',
    'list_stored_engagements',
    'list_stored_results',
    'get_input',
    'get_input_engagement',
    'get_input_intake',
    'get_input_files',
    'get_result',
    'get_result_summary',
    'get_result_findings',
    'get_result_compliance',
]
