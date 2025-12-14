from __future__ import annotations

from pathlib import Path
from flask import Flask

from .constants import ApiConfig


def apply_config(app: Flask, cfg: ApiConfig | None = None) -> ApiConfig:
    cfg = cfg or ApiConfig()

    app.config["MAX_CONTENT_LENGTH"] = cfg.max_content_length_bytes
    app.config["UPLOAD_FOLDER"] = cfg.upload_folder
    app.config["OUTPUT_FOLDER"] = cfg.output_folder
    app.config["CORRECTED_FOLDER"] = cfg.corrected_folder

    # Ensure directories exist
    for folder in [cfg.upload_folder, cfg.output_folder, cfg.corrected_folder]:
        Path(folder).mkdir(parents=True, exist_ok=True)

    return cfg
