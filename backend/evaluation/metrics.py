
"""
Evaluation Metrics Module
Implements statistical and NLP metrics without heavy external dependencies.
"""
from typing import List, Set, Dict

def calculate_precision_recall_f1(predicted_set: Set[str], reference_set: Set[str]) -> Dict[str, float]:
    """
    Calculate Classification Metrics for a set of labels.
    """
    if not predicted_set and not reference_set:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    
    true_positives = len(predicted_set.intersection(reference_set))
    false_positives = len(predicted_set - reference_set)
    false_negatives = len(reference_set - predicted_set)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    
    f1 = 0.0
    if (precision + recall) > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
        
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

def levenshtein_distance(s1: str, s2: str) -> int:
    """Standard Edit Distance"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def calculate_rouge_l(candidate: str, reference: str) -> float:
    """
    Calculate ROUGE-L (Longest Common Subsequence) Score.
    This is a simplified character-based or word-based implementation.
    We use word-based here for relevance to document extraction.
    """
    def get_lcs_length(x: List[str], y: List[str]) -> int:
        m = len(x)
        n = len(y)
        L = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                if x[i] == y[j]:
                    L[i+1][j+1] = L[i][j] + 1
                else:
                    L[i+1][j+1] = max(L[i+1][j], L[i][j+1])
        return L[m][n]

    cand_tokens = candidate.split()
    ref_tokens = reference.split()
    
    if not cand_tokens or not ref_tokens:
        return 0.0
        
    lcs = get_lcs_length(cand_tokens, ref_tokens)
    
    precision = lcs / len(cand_tokens) if cand_tokens else 0.0
    recall = lcs / len(ref_tokens) if ref_tokens else 0.0
    
    if (precision + recall) == 0:
        return 0.0
        
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1
