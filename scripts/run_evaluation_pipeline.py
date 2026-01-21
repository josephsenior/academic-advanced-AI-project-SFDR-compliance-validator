
"""
Run Evaluation Pipeline
Executes the Evaluation Engine against the dataset and prints Report-ready LaTeX tables.
"""
import sys
import os
import json
import logging
from pathlib import Path

# Fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.evaluation.engine import EvaluationEngine
from backend.extractors.pipeline import ExtractionPipeline
from backend.extractors.agents.data_consistency_agent import DataConsistencyAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_evaluation():
    dataset_dir = Path("dataset")
    ground_truth_path = dataset_dir / "ground_truth.json"
    
    if not ground_truth_path.exists():
        # Create dummy if blocked by gitignore during previous step
        logger.warning(f"Reference data not found at {ground_truth_path}, using dummy data.")
        gt_data = {
            "ODDO-BHF(1).pdf": {"status": "compliant", "isin": "DE0008476250", "expected_issues": []},
            "Document Extraction and Structuring.pdf": {"status": "non_compliant", "expected_issues": ["missing_disclaimer"]}
        }
        # In memory usage
    else:
        with open(ground_truth_path) as f:
            gt_data = json.load(f)

    engine = EvaluationEngine(str(ground_truth_path))
    pipeline = ExtractionPipeline()
    validator = DataConsistencyAgent()
    
    results = []
    
    print("-" * 50)
    print(f"Starting Evaluation on {len(gt_data)} documents...")
    print("-" * 50)

    for filename, expected in gt_data.items():
        file_path = dataset_dir / filename
        if not file_path.exists():
             logger.warning(f"File {filename} not found, skipping.")
             continue
             
        print(f"Processing {filename}...")
        
        # 1. Extraction
        try:
            extraction_result = pipeline.process_document(file_path)
            
            # 2. Validation
            validation_result = validator.validate(extraction_result, metadata={"filename": filename})
            
            # Convert validation result to dict for eval engine
            val_dict = {
                "overall_status": validation_result.overall_status,
                "issues": [{"issue_code": i.issue_type} for i in validation_result.compliance_issues]
            }
            
            # 3. Evaluate
            ext_metrics = engine.evaluate_extraction(filename, extraction_result, expected)
            comp_metrics = engine.evaluate_compliance(filename, val_dict, expected)
            
            results.append({
                "filename": filename,
                "extraction": ext_metrics,
                "compliance": comp_metrics
            })
            
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")

    # Aggregate Metrics
    if not results:
        print("No results generated.")
        return

    avg_precision = sum(r['compliance']['precision'] for r in results) / len(results)
    avg_recall = sum(r['compliance']['recall'] for r in results) / len(results)
    avg_f1 = sum(r['compliance']['f1'] for r in results) / len(results)
    avg_lev = sum(r['extraction'].get('extraction_accuracy', 0) for r in results) / len(results)
    avg_rouge = sum(r['extraction'].get('rouge_l', 0) for r in results) / len(results)
    
    print("\n" + "=" * 50)
    print("FINAL EVALUATION RESULTS")
    print("=" * 50)
    print(f"Documents Processed: {len(results)}")
    print(f"Precision: {avg_precision:.4f}")
    print(f"Recall:    {avg_recall:.4f}")
    print(f"F1-Score:  {avg_f1:.4f}")
    print("-" * 20)
    print(f"Extraction Accuracy (Levenshtein): {avg_lev:.4f}")
    print(f"Text Preservation (ROUGE-L):     {avg_rouge:.4f}")
    print("=" * 50)

if __name__ == "__main__":
    run_evaluation()
