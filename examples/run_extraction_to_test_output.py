"""
Run Full Data Extraction Pipeline and Save Outputs to test_output

This script processes documents from the dataset and saves complete extraction results
including metadata, content extraction, features, and summaries to test_output directory.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.extractors.pipeline import ExtractionPipeline


def main():
    """Run extraction pipeline on example documents and save to test_output"""
    
    print("=" * 80)
    print("DATA EXTRACTION PIPELINE - TEST OUTPUT GENERATOR")
    print("=" * 80)
    print()
    
    # Setup paths
    workspace = Path(__file__).resolve().parent
    dataset_dir = workspace / 'dataset'
    output_dir = workspace / 'test_output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Workspace: {workspace}")
    print(f"Dataset directory: {dataset_dir}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Initialize pipeline with test_output as output directory
    print("Initializing extraction pipeline...")
    pipeline = ExtractionPipeline(
        use_llm=True,  # Enable LLM features
        output_dir=str(output_dir)
    )
    print("[OK] Pipeline initialized")
    print()
    
    # Find all supported documents
    supported_exts = {'.pptx', '.docx', '.pdf'}
    documents = []
    
    for example_dir in dataset_dir.iterdir():
        if example_dir.is_dir():
            for file_path in example_dir.rglob('*'):
                if file_path.suffix.lower() in supported_exts:
                    # Check if metadata.json exists in same directory
                    metadata_json = file_path.parent / 'metadata.json'
                    metadata_path = str(metadata_json) if metadata_json.exists() else None
                    documents.append((file_path, metadata_path))
    
    if not documents:
        print("[WARNING] No documents found in dataset directory")
        return
    
    print(f"Found {len(documents)} document(s) to process")
    print()
    
    # Process each document
    processed = 0
    errors = 0
    
    for idx, (doc_path, metadata_path) in enumerate(documents, 1):
        print("=" * 80)
        print(f"Processing Document {idx}/{len(documents)}")
        print("=" * 80)
        print(f"File: {doc_path.name}")
        print(f"Path: {doc_path}")
        if metadata_path:
            print(f"Metadata JSON: {metadata_path}")
        print()
        
        try:
            # Process document through pipeline
            result = pipeline.process_document(
                file_path=str(doc_path),
                metadata_json_path=metadata_path
            )
            
            if result.get('status') == 'success':
                processed += 1
                print(f"[SUCCESS] Document processed successfully")
                print(f"  Document ID: {result.get('document_id')}")
                print(f"  Output directory: {result.get('output_paths', {}).get('document_dir', 'N/A')}")
                
                # Print summary
                summary = result.get('summary', {})
                if summary:
                    print(f"\n  Summary:")
                    print(f"    - Slides: {summary.get('total_slides', 0)}")
                    print(f"    - Tables: {summary.get('total_tables', 0)}")
                    print(f"    - Charts: {summary.get('total_charts', 0)}")
                    print(f"    - Text length: {summary.get('text_length', 0)} chars")
                    
                    features = summary.get('features', {})
                    if features:
                        print(f"    - ESG mentions: {features.get('esg_mentions', 0)}")
                        print(f"    - Performance data: {features.get('performance_data', 0)}")
                        print(f"    - Countries: {features.get('countries', 0)}")
                        print(f"    - Companies: {features.get('companies', 0)}")
                
                # Print output files
                output_paths = result.get('output_paths', {})
                if output_paths:
                    print(f"\n  Output files:")
                    for key, path in output_paths.items():
                        if path:
                            print(f"    - {key}: {path}")
            else:
                errors += 1
                print(f"[ERROR] Document processing failed")
                error_list = result.get('errors', [])
                for error in error_list:
                    print(f"  - {error}")
        
        except Exception as e:
            errors += 1
            print(f"[ERROR] Exception during processing: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    # Final summary
    print("=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Total documents: {len(documents)}")
    print(f"Successfully processed: {processed}")
    print(f"Errors: {errors}")
    print(f"\nOutput directory: {output_dir}")
    print()
    
    # List all output files
    if output_dir.exists():
        output_files = list(output_dir.rglob('*.json'))
        if output_files:
            print(f"Generated {len(output_files)} output file(s):")
            for file_path in sorted(output_files):
                rel_path = file_path.relative_to(workspace)
                size = file_path.stat().st_size
                print(f"  - {rel_path} ({size:,} bytes)")


if __name__ == '__main__':
    main()

