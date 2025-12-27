from __future__ import annotations

import json
import logging
from typing import Optional

from flask import Flask, jsonify
from flask_cors import CORS

from .config import ApiConfig, apply_config
from .routes.v1 import bp as api_v1_bp
from .serialization import DateTimeEncoder


def create_app(cfg: Optional[ApiConfig] = None) -> Flask:
    app = Flask(__name__)

    cfg = cfg or ApiConfig()
    apply_config(app, cfg)

    CORS(app)

    # Load persistent jobs
    from .store import load_jobs
    load_jobs()

    # Ensure JSON can encode datetimes consistently
    json.encoder.JSONEncoder = DateTimeEncoder  # type: ignore[assignment]

    # Register routes
    app.register_blueprint(api_v1_bp)

    # Basic logging
    logging.basicConfig(level=cfg.log_level)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)
