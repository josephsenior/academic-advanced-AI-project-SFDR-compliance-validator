from __future__ import annotations

from datetime import datetime, timezone

from flask import jsonify

from . import bp


@bp.get("/health")
def health_check():
    return jsonify({"status": "healthy", "version": "1.0.0", "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')})
