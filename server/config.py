from __future__ import annotations

from pathlib import Path
from flask import Flask

from .constants import ApiConfig


def apply_config(app: Flask, cfg: ApiConfig | None = None) -> ApiConfig:
    cfg = cfg or ApiConfig()
    
    # Get the project root (parent of server directory)
    project_root = Path(__file__).resolve().parent.parent
    
    # Make paths absolute
    upload_path = project_root / cfg.upload_folder
    output_path = project_root / cfg.output_folder
    corrected_path = project_root / cfg.corrected_folder

    app.config["MAX_CONTENT_LENGTH"] = cfg.max_content_length_bytes
    app.config["UPLOAD_FOLDER"] = str(upload_path)
    app.config["OUTPUT_FOLDER"] = str(output_path)
    app.config["CORRECTED_FOLDER"] = str(corrected_path)

    # Ensure directories exist
    for folder in [upload_path, output_path, corrected_path]:
        folder.mkdir(parents=True, exist_ok=True)

    return cfg
