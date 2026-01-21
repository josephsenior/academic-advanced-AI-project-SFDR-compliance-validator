"""
Re-validate a document to update slide numbers with the latest validator logic.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server.store import validation_jobs, update_job_status
from backend.extractors.validator_pipeline import ValidationPipeline

def revalidate_document(document_id: str):
    """Re-run validation for a document."""
    if document_id not in validation_jobs:
        print(f"❌ Document ID {document_id} not found in job store!")
        return False
    
    job = validation_jobs[document_id]
    extraction_result = job.get("extraction_result")
    
    if not extraction_result:
        print(f"❌ No extraction result found for document {document_id}")
        return False
    
    print(f"🔄 Re-validating document {document_id}...")
    print(f"   Filename: {job.get('filename')}")
    
    # Run validation pipeline
    pipeline = ValidationPipeline()
    validation_result = pipeline.validate(extraction_result)
    
    # Count issues with slide numbers
    total_issues = 0
    issues_with_slide = 0
    
    for category, issues in validation_result.get("issues_by_category", {}).items():
        total_issues += len(issues)
        for issue in issues:
            if issue.get("slide_number") is not None:
                issues_with_slide += 1
    
    print("✅ Validation complete!")
    print(f"   Total issues: {total_issues}")
    print(f"   Issues with slide numbers: {issues_with_slide}/{total_issues}")
    
    # Update job with new validation result
    update_job_status(
        document_id,
        status="completed",
        validation_result=validation_result
    )
    
    print("💾 Updated job store with new validation results")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python revalidate_document.py <document_id>")
        sys.exit(1)
    
    doc_id = sys.argv[1]
    success = revalidate_document(doc_id)
    sys.exit(0 if success else 1)
