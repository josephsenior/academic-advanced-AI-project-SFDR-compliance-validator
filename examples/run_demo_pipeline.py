"""
Run Demo Pipeline on Single Document

Runs the full extraction and consistency pipeline on a selected document
and saves the output to a dedicated folder.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Apply Pydantic v1 patch for Python 3.12 compatibility
try:
    from backend.utils import pydantic_v1_patch
except ImportError:
    pass

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.extractors.pipeline import ExtractionPipeline

def main():
    # Setup paths
    workspace = Path(__file__).resolve().parent
    
    # Create a dedicated output folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = workspace / 'outputs' / f'demo_run_{timestamp}'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Target document
    doc_path = workspace / 'dataset' / 'ODDO-BHF(1).pdf'
    
    print("=" * 80)
    print("DEMO PIPELINE RUN")
    print("=" * 80)
    print(f"Target Document: {doc_path}")
    print(f"Output Directory: {output_dir}")
    print("-" * 80)

    if not doc_path.exists():
        print(f"[ERROR] Document not found: {doc_path}")
        return

    # Initialize pipeline
    print("Initializing pipeline...")
    pipeline = ExtractionPipeline(
        use_llm=True,
        output_dir=str(output_dir)
    )
    
    # Run processing
    print("Running processing (Extraction + Consistency)...")
    try:
        result = pipeline.process_document(file_path=str(doc_path))
        
        if result.get('status') == 'success':
            print("\n[SUCCESS] Processing complete!")
            print(f"Document ID: {result.get('document_id')}")
            
            # Show Consistency Results
            consistency = result.get('consistency_results', {})
            if consistency:
                print("\n--- Data Consistency Report ---")
                status = consistency.get('overall_status', 'unknown').upper()
                print(f"Overall Status: {status}")
                
                issues = consistency.get('compliance_issues', [])
                if issues:
                    print(f"\nFound {len(issues)} Compliance Issues:")
                    for i, issue in enumerate(issues, 1):
                        severity = issue.get('severity', 'info').upper()
                        msg = issue.get('message', '')
                        loc = issue.get('location', 'unknown')
                        print(f"  {i}. [{severity}] {msg} (at {loc})")
                else:
                    print("\nNo compliance issues found.")
            
            # List generated files
            print("\n--- Generated Output Files ---")
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    rel_path = Path(root) / file
                    print(f"- {rel_path.relative_to(workspace)}")
                    
        else:
            print("\n[ERROR] Processing failed.")
            for err in result.get('errors', []):
                print(f"- {err}")
                
    except Exception as e:
        print(f"\n[EXCEPTION] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
