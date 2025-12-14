from __future__ import annotations

from flask import Blueprint

bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# Register route modules (import side-effects attach handlers to bp)
from . import health as _health  # noqa: F401
from . import upload as _upload  # noqa: F401
from . import validate as _validate  # noqa: F401
from . import status as _status  # noqa: F401
from . import results as _results  # noqa: F401
from . import fix as _fix  # noqa: F401
from . import download as _download  # noqa: F401
from . import report as _report  # noqa: F401
from . import list_delete as _list_delete  # noqa: F401

__all__ = ["bp"]
