from __future__ import annotations

import json
import logging
from pathlib import Path

from flask import current_app, jsonify, request

from ...constants import ValidationStatus
from ...store import validation_jobs

from . import bp

from .utils import standardize_results

logger = logging.getLogger(__name__)


@bp.get("/results/<document_id>")
def get_results(document_id: str):
    if document_id not in validation_jobs:
        output_path = Path(current_app.config["OUTPUT_FOLDER"]) / document_id / "validation_result.json"
        if not output_path.exists():
            return jsonify({"error": "Document not found"}), 404

        try:
            with open(output_path, "r", encoding="utf-8") as f:
                results = json.load(f)
            return jsonify(standardize_results(results)), 200
        except Exception as e:
            logger.error("Failed to load results from disk: %s", e)
            return jsonify({"error": "Failed to load results"}), 500

    job = validation_jobs[document_id]

    if job["status"] != ValidationStatus.COMPLETED:
        return jsonify({"error": "Validation not completed", "status": job["status"], "progress": job["progress"]}), 400

    results = standardize_results(job["validation_result"])

    category_filter = request.args.get("category")
    severity_filter = request.args.get("severity")
    slide_filter = request.args.get("slide", type=int)

    if any([category_filter, severity_filter, slide_filter]):
        filtered_issues = {}
        for category, issues in results["issues_by_category"].items():
            if category_filter and category != category_filter:
                continue

            filtered = [
                issue
                for issue in issues
                if (not severity_filter or issue["severity"] == severity_filter)
                and (not slide_filter or issue.get("slide_number") == slide_filter)
            ]

            if filtered:
                filtered_issues[category] = filtered

        results = {**results, "issues_by_category": filtered_issues}

    return jsonify(results)
