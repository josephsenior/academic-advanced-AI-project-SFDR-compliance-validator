
"""
Evaluation Engine Core
Orchestrates the comparison between System Output and Ground Truth.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any
from .metrics import calculate_precision_recall_f1, levenshtein_distance, calculate_rouge_l

logger = logging.getLogger(__name__)

class EvaluationEngine:
    def __init__(self, ground_truth_path: str):
        self.ground_truth_path = Path(ground_truth_path)
        self.results = []
        
    def load_ground_truth(self) -> Dict[str, Any]:
        if not self.ground_truth_path.exists():
            return {}
        with open(self.ground_truth_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def evaluate_extraction(self, doc_id: str, extracted_data: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate extraction quality (Levenshtein & ROUGE)"""
        metrics = {}
        
        # 1. Structured Fields (Levenshtein based)
        fields_to_check = ['isin', 'management_company', 'fund_name', 'launch_date']
        total_dist = 0
        checks = 0
        
        for field in fields_to_check:
            sys_val = str(extracted_data.get(field, "")).strip().lower()
            gt_val = str(ground_truth.get(field, "")).strip().lower()
            if gt_val:
                dist = levenshtein_distance(sys_val, gt_val)
                # Normalize distance 0-1
                max_len = max(len(sys_val), len(gt_val))
                score = 1.0 - (dist / max_len) if max_len > 0 else 1.0
                total_dist += score
                checks += 1
                
        metrics['extraction_accuracy'] = total_dist / checks if checks > 0 else 1.0
        
        # 2. Content ROUGE-L (Disclaimer Text, specific paragraphs)
        sys_text = extracted_data.get('full_text', "")
        gt_text = ground_truth.get('full_text', "")
        
        if gt_text:
            metrics['rouge_l'] = calculate_rouge_l(sys_text, gt_text)
            
        return metrics

    def evaluate_compliance(self, doc_id: str, validation_result: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate classification quality (Precision, Recall)"""
        
        # 1. Document Level Status
        sys_status = validation_result.get('overall_status', 'compliant')
        gt_status = ground_truth.get('status', 'compliant')
        
        # Binary: Is it Non-Compliant?
        sys_flag = 1 if sys_status != 'compliant' else 0
        gt_flag = 1 if gt_status != 'compliant' else 0
        
        # 2. Issue Level
        sys_issues = set(i.get('issue_code') for i in validation_result.get('issues', []))
        gt_issues = set(ground_truth.get('expected_issues', []))
        
        metrics = calculate_precision_recall_f1(sys_issues, gt_issues)
        metrics['status_match'] = 1.0 if sys_flag == gt_flag else 0.0
        
        return metrics

    def run_batch(self, outputs_dir: str):
        """Run eval on a directory of outputs"""
        # Placeholder for batch logic
        pass
