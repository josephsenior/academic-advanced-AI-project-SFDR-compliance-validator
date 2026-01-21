from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from flask import current_app, jsonify, request

from ...constants import ValidationStatus
from ...store import validation_jobs

from . import bp
from .utils import standardize_results
from backend.extractors.agents.data_consistency_agent import DataConsistencyResult

logger = logging.getLogger(__name__)


@bp.post("/fix/<document_id>")
def fix_document(document_id: str):
    try:
        if document_id not in validation_jobs:
            return jsonify({"error": "Document not found"}), 404

        job = validation_jobs[document_id]

        # Allow force override for testing/debugging using query param ?force=true
        force = request.args.get("force", "false").lower() == "true"
        if job["status"] != ValidationStatus.COMPLETED and not force:
            return jsonify({"error": "Validation must be completed first"}), 400

        data = request.get_json(silent=True) or {}
        fix_types = data.get("fix_types", ["all"])

        # Lazy import to avoid heavy deps at startup
        from backend.extractors.document_corrector import DocumentCorrector

        corrector = DocumentCorrector()

        original_path = job["file_path"]
        # Ensure path is absolute
        if not os.path.isabs(original_path):
            project_root = Path(current_app.root_path).parent
            original_path = str(project_root / original_path)
            
        output_path = Path(current_app.config["CORRECTED_FOLDER"]) / f"{document_id}_corrected.pptx"

        # EMERGENCY DEBUG LOG
        DEBUG_FILE = "debug_fix_abs.log"
        try:
            with open(DEBUG_FILE, "a") as f:
                f.write(f"\n--- {datetime.now()} ---\n")
                f.write(f"ID: {document_id}\n")
                f.write(f"Input: {original_path}\n")
                f.write(f"Output: {output_path}\n")
                f.write(f"Input exists: {os.path.exists(original_path)}\n")
            print(f"DEBUG_LOG: Wrote to {DEBUG_FILE}")
        except Exception as e:
            print(f"DEBUG_LOG_ERROR: {str(e)}")

        logger.info(f"Applying fixes to {document_id}")
        logger.info(f"Input path: {original_path}")
        logger.info(f"Output path: {output_path}")


        validation_result = job.get("validation_result")
        
        # NEW: Lazy validation if results are missing
        if not validation_result:
            logger.info(f"Validation result missing for {document_id}. Triggering lazy validation...")
            try:
                from ...services.validation_service import run_validation
                # We use empty options for lazy validation
                validation_result = run_validation(document_id, job, {})
                # Update the local job reference as well
                job["validation_result"] = validation_result
                logger.info(f"Lazy validation successful for {document_id}")
            except Exception as e:
                logger.error(f"Lazy validation failed for {document_id}: {str(e)}")
                return jsonify({"error": f"Could not perform lazy validation: {str(e)}"}), 500

        # DEBUG: Log issue count
        if not validation_result:
             return jsonify({"error": "Validation result is empty after lazy validation"}), 500
             
        validation_result = standardize_results(validation_result)
        issues_to_process = validation_result.get("compliance_issues", [])
        print(f"DEBUG: fix_document processing {len(issues_to_process)} issues for document {document_id}")
        
        logger.info(f"Applying fixes for document {document_id}. Fix types: {fix_types}")
        
        auto_fix_disclaimers = "all" in fix_types or "disclaimers" in fix_types
        
        # Prepare disclaimer_result from validation_result if present so the corrector
        # can auto-fix disclaimers. Some validation outputs store disclaimers under
        # issues_by_category -> 'disclaimer'.
        disclaimer_result = None
        try:
            from types import SimpleNamespace

            if isinstance(validation_result, dict):
                missing = validation_result.get("issues_by_category", {}).get("disclaimer", [])
                # Wrap into an object with attribute `missing_disclaimers` expected by the corrector
                disclaimer_result = SimpleNamespace(missing_disclaimers=missing)
            else:
                # Pass through if it's already a model/object
                disclaimer_result = getattr(validation_result, "disclaimer_result", None) or validation_result
        except Exception:
            disclaimer_result = None

        result = corrector.correct(
            original_path,
            DataConsistencyResult(**validation_result) if isinstance(validation_result, dict) else validation_result,
            disclaimer_result=disclaimer_result,
            output_path=str(output_path),
            auto_fix_disclaimers=auto_fix_disclaimers,
        )
        
        if not result.success:
            logger.error(f"Correction failed for {document_id}: {result.error_message}")
            return jsonify({"error": f"Correction failed: {result.error_message}"}), 500

        fixes_applied = len(result.fixes_applied)
        logger.info(f"Successfully applied {fixes_applied} fixes for {document_id}. Path: {output_path}")

        return jsonify(
            {
                "document_id": document_id,
                "corrected_file_path": str(output_path),
                "fixes_applied": fixes_applied,
                "message": f"Document corrected successfully. {fixes_applied} fixes applied.",
                "details": {
                    "applied": result.fixes_applied,
                    "failed": result.fixes_failed
                }
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error in fix_document for {document_id}: {str(e)}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
