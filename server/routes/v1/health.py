from __future__ import annotations

from datetime import datetime

from flask import jsonify

from . import bp


@bp.get("/health")
def health_check():
    return jsonify({"status": "healthy", "version": "1.0.0", "timestamp": datetime.utcnow().isoformat()})
