from __future__ import annotations

import json
import logging
from pathlib import Path

from flask import current_app, jsonify, request

from ...constants import ValidationStatus
from ...store import validation_jobs

from . import bp

logger = logging.getLogger(__name__)


def _standardize_results(results: dict) -> dict:
    """Standardize severities to frontend-compatible values."""
    if not results:
        return results

    # Map for severity standardization
    severity_map = {
        "error": "critical",
        "warning": "high",
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "low"
    }

    # Fix overall status
    if "overall_status" in results:
        # If score is 100, status must be completed/pass
        if results.get("compliance_score", 0) == 100 and not results.get("has_errors"):
            # Ensure we don't overwrite completed status if that's what we want,
            # but usually frontend expects 'compliant' or 'completed'
            pass

    # Fix compliance_issues list
    if "compliance_issues" in results:
        for issue in results["compliance_issues"]:
            if issue.get("severity") in severity_map:
                issue["severity"] = severity_map[issue["severity"]]

    # Fix issues_by_category list
    if "issues_by_category" in results:
        for category, issues in results["issues_by_category"].items():
            for issue in issues:
                if issue.get("severity") in severity_map:
                    issue["severity"] = severity_map[issue["severity"]]

    # Rebuild issues_by_severity counts
    if "compliance_issues" in results:
        issues = results["compliance_issues"]
        results["issues_by_severity"] = {
            "critical": sum(1 for i in issues if i.get("severity") == "critical"),
            "high": sum(1 for i in issues if i.get("severity") == "high"),
            "medium": sum(1 for i in issues if i.get("severity") == "medium"),
            "low": sum(1 for i in issues if i.get("severity") == "low"),
        }

    # Add descriptive label if missing (legacy results)
    if "compliance_status_label" not in results:
        score = results.get("compliance_score", 100)
        if score == 100:
            results["compliance_status_label"] = "Totally compliant"
        elif score > 0:
            results["compliance_status_label"] = "Partially compliant"
        else:
            results["compliance_status_label"] = "Non-compliant"

    return results


@bp.get("/results/<document_id>")
def get_results(document_id: str):
    if document_id not in validation_jobs:
        output_path = Path(current_app.config["OUTPUT_FOLDER"]) / document_id / "validation_result.json"
        if not output_path.exists():
            return jsonify({"error": "Document not found"}), 404

        try:
            with open(output_path, "r", encoding="utf-8") as f:
                results = json.load(f)
            return jsonify(_standardize_results(results)), 200
        except Exception as e:
            logger.error("Failed to load results from disk: %s", e)
            return jsonify({"error": "Failed to load results"}), 500

    job = validation_jobs[document_id]

    if job["status"] != ValidationStatus.COMPLETED:
        return jsonify({"error": "Validation not completed", "status": job["status"], "progress": job["progress"]}), 400

    results = _standardize_results(job["validation_result"])

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
