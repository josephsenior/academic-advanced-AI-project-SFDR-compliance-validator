"""
REST API for Document Validation System
Modern API endpoints for frontend integration
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.pipeline import ExtractionPipeline
from src.extractors.data_consistency_agent import DataConsistencyAgent
from src.extractors.document_corrector import DocumentCorrector
from src.extractors.disclaimer_validator import DisclaimerValidator
from src.utils.validation_report_generator import ValidationReportGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['CORRECTED_FOLDER'] = 'corrected_documents'

# Create directories
for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], app.config['CORRECTED_FOLDER']]:
    Path(folder).mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'pptx', 'pdf', 'docx'}

# In-memory storage for validation jobs (use Redis/DB in production)
validation_jobs = {}


# ==================== MODELS ====================

class ValidationStatus:
    PENDING = "pending"
    UPLOADING = "uploading"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


# ==================== HELPER FUNCTIONS ====================

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_type(filename: str) -> str:
    """Get file type from filename"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext


def create_job_record(document_id: str, filename: str, file_path: str) -> Dict[str, Any]:
    """Create a new validation job record"""
    return {
        'document_id': document_id,
        'filename': filename,
        'file_path': file_path,
        'status': ValidationStatus.PENDING,
        'progress': 0,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'extraction_result': None,
        'validation_result': None,
        'metadata': None,
        'error': None
    }


def update_job_status(document_id: str, status: str, progress: int = None, **kwargs):
    """Update job status"""
    if document_id in validation_jobs:
        validation_jobs[document_id]['status'] = status
        validation_jobs[document_id]['updated_at'] = datetime.utcnow().isoformat()
        if progress is not None:
            validation_jobs[document_id]['progress'] = progress
        for key, value in kwargs.items():
            validation_jobs[document_id][key] = value


def format_validation_result(result: Any, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Format validation result for API response"""
    
    # Calculate compliance score (0-100)
    total_issues = len(result.compliance_issues)
    critical_count = sum(1 for i in result.compliance_issues if i.severity == 'critical')
    high_count = sum(1 for i in result.compliance_issues if i.severity == 'high')
    medium_count = sum(1 for i in result.compliance_issues if i.severity == 'medium')
    low_count = sum(1 for i in result.compliance_issues if i.severity == 'low')
    
    # Score calculation: critical = -10, high = -5, medium = -3, low = -1
    penalty = (critical_count * 10) + (high_count * 5) + (medium_count * 3) + (low_count * 1)
    compliance_score = max(0, min(100, 100 - penalty))
    
    # Group issues by category
    issues_by_category = {}
    for issue in result.compliance_issues:
        category = issue.issue_category or 'general'
        if category not in issues_by_category:
            issues_by_category[category] = []
        issues_by_category[category].append({
            'issue_type': issue.issue_type,
            'severity': issue.severity,
            'category': issue.issue_category,
            'location': issue.location,
            'slide_number': issue.slide_number,
            'message': issue.message,
            'context': issue.context,
            'suggestion': issue.suggestion,
            'auto_fixable': getattr(issue, 'auto_fixable', False),
            'rule_reference': issue.rule_reference,
            'details': issue.details
        })
    
    # Category counts
    category_counts = {
        category: {
            'total': len(issues),
            'critical': sum(1 for i in issues if i['severity'] == 'critical'),
            'high': sum(1 for i in issues if i['severity'] == 'high'),
            'medium': sum(1 for i in issues if i['severity'] == 'medium'),
            'low': sum(1 for i in issues if i['severity'] == 'low'),
        }
        for category, issues in issues_by_category.items()
    }
    
    return {
        'document_id': result.document_id,
        'overall_status': result.overall_status,
        'compliance_score': compliance_score,
        'total_issues': total_issues,
        'issues_by_severity': {
            'critical': critical_count,
            'high': high_count,
            'medium': medium_count,
            'low': low_count
        },
        'issues_by_category': issues_by_category,
        'category_counts': category_counts,
        'statistics': {
            'total_tables_checked': result.total_tables_checked,
            'tables_with_source_date': result.tables_with_source_date,
            'tables_missing_source_date': result.tables_missing_source_date,
            'total_charts_analyzed': result.total_charts_analyzed,
            'charts_with_source_date': result.charts_with_source_date,
            'charts_missing_source_date': result.charts_missing_source_date,
            'total_numerical_values_checked': result.total_numerical_values_checked,
            'values_matching_reference': result.values_matching_reference,
            'values_mismatched': result.values_mismatched
        },
        'metadata': metadata,
        'summary': result.summary
    }


# ==================== API ENDPOINTS ====================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/v1/upload', methods=['POST'])
def upload_document():
    """
    Upload document with optional metadata and prospectus files
    
    Form Data:
        document: Document file (pptx/pdf/docx) - REQUIRED
        metadata: metadata.json file - OPTIONAL (validation will use defaults if missing)
        prospectus: Prospectus reference document - OPTIONAL (enables performance data validation)
        
    Returns:
        {
            'document_id': 'uuid',
            'filename': 'document.pptx',
            'status': 'uploading',
            'message': 'Upload successful',
            'has_metadata': bool,
            'has_prospectus': bool
        }
    """
    try:
        # Validate main document file (required)
        if 'document' not in request.files:
            return jsonify({'error': 'No document file provided. Please upload the main document.'}), 400
        
        document_file = request.files['document']
        if document_file.filename == '':
            return jsonify({'error': 'No document file selected'}), 400
        
        if not allowed_file(document_file.filename):
            return jsonify({
                'error': f'Document file type not supported. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Create document directory
        doc_dir = Path(app.config['UPLOAD_FOLDER']) / document_id
        doc_dir.mkdir(exist_ok=True)
        
        # Save main document file
        filename = secure_filename(document_file.filename)
        file_path = doc_dir / filename
        document_file.save(file_path)
        
        # Handle metadata file (optional)
        metadata = None
        has_metadata = False
        if 'metadata' in request.files:
            metadata_file = request.files['metadata']
            if metadata_file.filename and metadata_file.filename.endswith('.json'):
                try:
                    metadata = json.load(metadata_file)
                    # Save metadata.json to document directory
                    metadata_path = doc_dir / 'metadata.json'
                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    has_metadata = True
                    logger.info(f"Metadata uploaded for {document_id}")
                except Exception as e:
                    logger.warning(f"Failed to parse metadata file: {e}")
        
        # Handle prospectus file (optional - enables performance validation)
        has_prospectus = False
        if 'prospectus' in request.files:
            prospectus_file = request.files['prospectus']
            if prospectus_file.filename:
                prospectus_filename = secure_filename(prospectus_file.filename)
                prospectus_path = doc_dir / f'prospectus_{prospectus_filename}'
                prospectus_file.save(prospectus_path)
                has_prospectus = True
                logger.info(f"Prospectus uploaded for {document_id}: {prospectus_filename}")
        
        # Create job record
        job = create_job_record(document_id, filename, str(file_path))
        job['metadata'] = metadata
        job['has_prospectus'] = has_prospectus
        validation_jobs[document_id] = job
        
        logger.info(f"Upload complete: {document_id} - {filename} (metadata: {has_metadata}, prospectus: {has_prospectus})")
        
        return jsonify({
            'document_id': document_id,
            'filename': filename,
            'status': ValidationStatus.PENDING,
            'message': 'Upload successful. Use /api/v1/validate/{document_id} to start validation.',
            'has_metadata': has_metadata,
            'has_prospectus': has_prospectus,
            'note': 'Prospectus is optional. Without it, performance data validation will be limited.'
        }), 201
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/v1/validate/<document_id>', methods=['POST'])
def validate_document(document_id: str):
    """
    Start validation for uploaded document
    
    JSON Body (optional):
        {
            'options': {
                'enable_llm': bool,
                'enable_esg': bool,
                'enable_disclaimers': bool
            },
            'metadata': {...}
        }
    
    Returns:
        {
            'document_id': 'uuid',
            'status': 'validating',
            'progress': 10,
            'message': 'Validation started'
        }
    """
    try:
        # Check if job exists
        if document_id not in validation_jobs:
            return jsonify({'error': 'Document not found'}), 404
        
        job = validation_jobs[document_id]
        
        # Check if already processing
        if job['status'] in [ValidationStatus.EXTRACTING, ValidationStatus.VALIDATING]:
            return jsonify({
                'document_id': document_id,
                'status': job['status'],
                'progress': job['progress'],
                'message': 'Validation already in progress'
            })
        
        # Parse options
        options = {}
        if request.is_json:
            data = request.get_json()
            options = data.get('options', {})
            if 'metadata' in data:
                job['metadata'] = {**job['metadata'], **data['metadata']} if job['metadata'] else data['metadata']
        
        # Update status
        update_job_status(document_id, ValidationStatus.EXTRACTING, 10)
        
        # STEP 1: Extract document
        logger.info(f"Starting extraction for {document_id}")
        pipeline = ExtractionPipeline(use_llm_extraction=options.get('enable_llm', False))
        
        extraction_result = pipeline.extract(job['file_path'])
        
        # Save extraction result
        output_dir = Path(app.config['OUTPUT_FOLDER']) / document_id
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / 'extraction.json', 'w', encoding='utf-8') as f:
            json.dump(extraction_result, f, indent=2, ensure_ascii=False)
        
        update_job_status(document_id, ValidationStatus.VALIDATING, 50, extraction_result=extraction_result)
        
        # STEP 2: Validate document
        logger.info(f"Starting validation for {document_id}")
        
        # Initialize validators
        disclaimer_validator = None
        if options.get('enable_disclaimers', True):
            try:
                disclaimer_validator = DisclaimerValidator()
            except Exception as e:
                logger.warning(f"Could not initialize disclaimer validator: {e}")
        
        agent = DataConsistencyAgent(
            enable_disclaimer_validation=options.get('enable_disclaimers', True),
            disclaimer_validator=disclaimer_validator,
            enable_esg_validation=options.get('enable_esg', False)
        )
        
        validation_result = agent.validate(extraction_result, job['metadata'], document_id)
        
        # Save validation result
        formatted_result = format_validation_result(validation_result, job['metadata'])
        
        with open(output_dir / 'validation_result.json', 'w', encoding='utf-8') as f:
            json.dump(formatted_result, f, indent=2, ensure_ascii=False)
        
        update_job_status(
            document_id,
            ValidationStatus.COMPLETED,
            100,
            validation_result=formatted_result
        )
        
        logger.info(f"Validation completed for {document_id}: {formatted_result['total_issues']} issues found")
        
        return jsonify({
            'document_id': document_id,
            'status': ValidationStatus.COMPLETED,
            'progress': 100,
            'message': 'Validation completed',
            'results': formatted_result
        })
        
    except Exception as e:
        logger.error(f"Validation error for {document_id}: {str(e)}", exc_info=True)
        update_job_status(document_id, ValidationStatus.FAILED, error=str(e))
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500


@app.route('/api/v1/status/<document_id>', methods=['GET'])
def get_status(document_id: str):
    """
    Get validation status
    
    Returns:
        {
            'document_id': 'uuid',
            'filename': 'document.pptx',
            'status': 'completed',
            'progress': 100,
            'created_at': '2025-12-07T...',
            'updated_at': '2025-12-07T...'
        }
    """
    if document_id not in validation_jobs:
        return jsonify({'error': 'Document not found'}), 404
    
    job = validation_jobs[document_id]
    
    return jsonify({
        'document_id': document_id,
        'filename': job['filename'],
        'status': job['status'],
        'progress': job['progress'],
        'created_at': job['created_at'],
        'updated_at': job['updated_at'],
        'error': job.get('error')
    })


@app.route('/api/v1/results/<document_id>', methods=['GET'])
def get_results(document_id: str):
    """
    Get validation results
    
    Query Parameters:
        category: Filter by category
        severity: Filter by severity (critical/high/medium/low)
        slide: Filter by slide number
    
    Returns:
        Full validation results with filtering applied
    """
    if document_id not in validation_jobs:
        return jsonify({'error': 'Document not found'}), 404
    
    job = validation_jobs[document_id]
    
    if job['status'] != ValidationStatus.COMPLETED:
        return jsonify({
            'error': 'Validation not completed',
            'status': job['status'],
            'progress': job['progress']
        }), 400
    
    results = job['validation_result']
    
    # Apply filters
    category_filter = request.args.get('category')
    severity_filter = request.args.get('severity')
    slide_filter = request.args.get('slide', type=int)
    
    if any([category_filter, severity_filter, slide_filter]):
        filtered_issues = {}
        for category, issues in results['issues_by_category'].items():
            if category_filter and category != category_filter:
                continue
            
            filtered = [
                issue for issue in issues
                if (not severity_filter or issue['severity'] == severity_filter) and
                   (not slide_filter or issue['slide_number'] == slide_filter)
            ]
            
            if filtered:
                filtered_issues[category] = filtered
        
        results = {**results, 'issues_by_category': filtered_issues}
    
    return jsonify(results)


@app.route('/api/v1/fix/<document_id>', methods=['POST'])
def fix_document(document_id: str):
    """
    Apply automatic fixes to document
    
    JSON Body:
        {
            'fix_types': ['disclaimers', 'formatting', 'all'],
            'options': {...}
        }
    
    Returns:
        {
            'document_id': 'uuid',
            'corrected_file_path': 'path/to/corrected.pptx',
            'fixes_applied': 5,
            'message': 'Document corrected'
        }
    """
    try:
        if document_id not in validation_jobs:
            return jsonify({'error': 'Document not found'}), 404
        
        job = validation_jobs[document_id]
        
        if job['status'] != ValidationStatus.COMPLETED:
            return jsonify({'error': 'Validation must be completed first'}), 400
        
        data = request.get_json() or {}
        fix_types = data.get('fix_types', ['all'])
        
        # Initialize corrector
        corrector = DocumentCorrector()
        
        # Apply fixes
        original_path = job['file_path']
        output_path = Path(app.config['CORRECTED_FOLDER']) / f"{document_id}_corrected.pptx"
        
        logger.info(f"Applying fixes to {document_id}")
        
        # Get validation issues
        validation_result = job['validation_result']
        issues_to_fix = []
        
        # Filter fixable issues
        for category, issues in validation_result['issues_by_category'].items():
            for issue in issues:
                if issue.get('auto_fixable', False):
                    if 'all' in fix_types or category in fix_types:
                        issues_to_fix.append(issue)
        
        # Apply corrections (simplified - you'll need to implement based on your corrector)
        corrector_result = corrector.correct_document(
            original_path,
            str(output_path),
            job['extraction_result'],
            job['validation_result'],
            job['metadata']
        )
        
        fixes_applied = len(issues_to_fix)
        
        logger.info(f"Applied {fixes_applied} fixes to {document_id}")
        
        return jsonify({
            'document_id': document_id,
            'corrected_file_path': str(output_path),
            'fixes_applied': fixes_applied,
            'message': f'Document corrected successfully. {fixes_applied} fixes applied.'
        })
        
    except Exception as e:
        logger.error(f"Fix error for {document_id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Fix failed: {str(e)}'}), 500


@app.route('/api/v1/download/<document_id>', methods=['GET'])
def download_document(document_id: str):
    """
    Download corrected document
    
    Query Parameters:
        type: 'original' or 'corrected' (default: corrected)
    """
    try:
        if document_id not in validation_jobs:
            return jsonify({'error': 'Document not found'}), 404
        
        job = validation_jobs[document_id]
        download_type = request.args.get('type', 'corrected')
        
        if download_type == 'original':
            file_path = job['file_path']
        else:
            file_path = Path(app.config['CORRECTED_FOLDER']) / f"{document_id}_corrected.pptx"
            if not file_path.exists():
                return jsonify({'error': 'Corrected document not found. Run /api/v1/fix first'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"{download_type}_{job['filename']}"
        )
        
    except Exception as e:
        logger.error(f"Download error for {document_id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


@app.route('/api/v1/report/<document_id>', methods=['GET'])
def generate_report(document_id: str):
    """
    Generate compliance report
    
    Query Parameters:
        format: 'json', 'pdf', 'html' (default: json)
    """
    try:
        if document_id not in validation_jobs:
            return jsonify({'error': 'Document not found'}), 404
        
        job = validation_jobs[document_id]
        
        if job['status'] != ValidationStatus.COMPLETED:
            return jsonify({'error': 'Validation not completed'}), 400
        
        report_format = request.args.get('format', 'json')
        
        if report_format == 'json':
            return jsonify(job['validation_result'])
        
        # Generate report using ValidationReportGenerator
        generator = ValidationReportGenerator()
        output_dir = Path(app.config['OUTPUT_FOLDER']) / document_id
        
        if report_format == 'html':
            report_path = generator.generate_html_report(
                job['validation_result'],
                str(output_dir / 'report.html')
            )
            return send_file(report_path, mimetype='text/html')
        
        elif report_format == 'pdf':
            # PDF generation (requires additional implementation)
            return jsonify({'error': 'PDF format not yet implemented'}), 501
        
        else:
            return jsonify({'error': f'Unsupported format: {report_format}'}), 400
        
    except Exception as e:
        logger.error(f"Report generation error for {document_id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500


@app.route('/api/v1/list', methods=['GET'])
def list_documents():
    """
    List all validation jobs
    
    Query Parameters:
        status: Filter by status
        limit: Max results (default: 50)
        offset: Pagination offset (default: 0)
    """
    status_filter = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Filter jobs
    filtered_jobs = []
    for job_id, job in validation_jobs.items():
        if status_filter and job['status'] != status_filter:
            continue
        
        filtered_jobs.append({
            'document_id': job_id,
            'filename': job['filename'],
            'status': job['status'],
            'progress': job['progress'],
            'created_at': job['created_at'],
            'updated_at': job['updated_at'],
            'compliance_score': job['validation_result']['compliance_score'] if job.get('validation_result') else None,
            'total_issues': job['validation_result']['total_issues'] if job.get('validation_result') else None
        })
    
    # Sort by created_at (newest first)
    filtered_jobs.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Paginate
    total = len(filtered_jobs)
    paginated = filtered_jobs[offset:offset + limit]
    
    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'documents': paginated
    })


@app.route('/api/v1/delete/<document_id>', methods=['DELETE'])
def delete_document(document_id: str):
    """Delete document and all associated data"""
    try:
        if document_id not in validation_jobs:
            return jsonify({'error': 'Document not found'}), 404
        
        job = validation_jobs[document_id]
        
        # Delete files
        try:
            Path(job['file_path']).unlink(missing_ok=True)
        except:
            pass
        
        try:
            output_dir = Path(app.config['OUTPUT_FOLDER']) / document_id
            if output_dir.exists():
                import shutil
                shutil.rmtree(output_dir)
        except:
            pass
        
        try:
            corrected_path = Path(app.config['CORRECTED_FOLDER']) / f"{document_id}_corrected.pptx"
            corrected_path.unlink(missing_ok=True)
        except:
            pass
        
        # Remove from jobs
        del validation_jobs[document_id]
        
        logger.info(f"Deleted document {document_id}")
        
        return jsonify({
            'message': 'Document deleted successfully',
            'document_id': document_id
        })
        
    except Exception as e:
        logger.error(f"Delete error for {document_id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Delete failed: {str(e)}'}), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("Document Validation API Server")
    print("="*80)
    print("\nAPI Endpoints:")
    print("  GET    /api/v1/health              - Health check")
    print("  POST   /api/v1/upload              - Upload document")
    print("  POST   /api/v1/validate/<id>       - Start validation")
    print("  GET    /api/v1/status/<id>         - Get status")
    print("  GET    /api/v1/results/<id>        - Get results")
    print("  POST   /api/v1/fix/<id>            - Apply fixes")
    print("  GET    /api/v1/download/<id>       - Download document")
    print("  GET    /api/v1/report/<id>         - Generate report")
    print("  GET    /api/v1/list                - List documents")
    print("  DELETE /api/v1/delete/<id>         - Delete document")
    print("\n" + "="*80)
    print("Server running on http://localhost:5000")
    print("="*80 + "\n")
    
    # Use threading to run Flask in background, keep main thread alive
    import threading
    import time
    
    def run_server():
        app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False, threaded=True)
    
    server_thread = threading.Thread(target=run_server, daemon=False)
    server_thread.start()
    
    print("Server thread started. Press Ctrl+C to stop.\n")
    
    try:
        # Keep main thread alive
        while server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

