"""
Utility functions for validators
"""

from typing import Optional, Dict, Any, List


def infer_last_slide(extraction_result: Dict[str, Any]) -> int:
    """
    Infer the last slide number from extraction result.
    
    Used for disclaimers and glossary issues which typically appear on the last slide.
    
    Args:
        extraction_result: Extraction result dictionary
        
    Returns:
        Last slide number (1-indexed)
    """
    if 'slides' in extraction_result:
        return len(extraction_result['slides'])
    if 'pages' in extraction_result:
        return len(extraction_result['pages'])
    return 6  # Default to slide 6 for standard 6-slide presentations


def infer_slide_containing_text(extraction_result: Dict[str, Any], keywords: List[str]) -> Optional[int]:
    """
    Infer which slide contains any of the given keywords.
    
    Args:
        extraction_result: Extraction result dictionary
        keywords: List of keywords to search for
        
    Returns:
        Slide number (1-indexed) or None if not found
    """
    if 'slides' in extraction_result:
        for i, slide in enumerate(extraction_result['slides'], start=1):
            if isinstance(slide, dict):
                content = (slide.get('content', '') or slide.get('text', '')).lower()
            else:
                content = str(slide).lower()
            
            if any(k.lower() in content for k in keywords):
                return i
    return None


def infer_performance_slide(
    extraction_result: Dict[str, Any],
    performance_sections: Optional[List[Dict[str, Any]]] = None
) -> Optional[int]:
    """
    Infer which slide contains performance data.
    
    Performance issues should point to where performance data is actually shown.
    Per compliance rules, performance MUST NOT be on slide 1 (cover page).
    Typically, it also should not be on slide 2 (Risk Profile).
    
    Args:
        extraction_result: Extraction result dictionary
        performance_sections: List of performance sections with slide_number info
        
    Returns:
        Slide number where performance appears, or None if not found
    """
    # 1. Try to get from performance sections, prioritizing slides > 2
    if performance_sections:
        # First pass: look for performance AFTER slide 2 (Risk/Profile)
        # Exclude slides that are explicitly marked as examples or non-recommendations
        for section in performance_sections:
            slide_num = section.get('slide_number')
            if not slide_num or slide_num <= 2:
                continue
                
            # Check slide text for "example" or "illustration" keywords
            if 'slides' in extraction_result and len(extraction_result['slides']) >= slide_num:
                slide_data = extraction_result['slides'][slide_num - 1]
                text = (slide_data.get('content', '') or slide_data.get('text', '') or '').lower()
                
                # Broadened exclusion keywords for example/illustrative slides
                example_keywords = [
                    "example", "exemple", "illustration", "illustrative", 
                    "no investment recommendation", "not an investment recommendation",
                    "historically attractive performance", "world’s largest economy",
                    "market performance", "performance du marché", "historique du marché",
                    "why invest in", "pourquoi investir", "warum in", "market context"
                ]
                
                if any(kw in text for kw in example_keywords):
                    continue
            
            return slide_num
        
        # Second pass: accept slide > 1 if that's the only place we found it
        for section in performance_sections:
            slide_num = section.get('slide_number')
            if slide_num and slide_num > 1:
                return slide_num
    
    # 2. Fallback: search for performance keywords in slide content
    perf_keywords = ['performance', 'rendement', 'ytd', '1y', '3y', '5y', '10y', 'benchmark', 'indice']
    
    # We use infer_slide_containing_text but need to manually handle the priority > 2
    if 'slides' in extraction_result:
        # Check slides > 2 first
        for i, slide in enumerate(extraction_result['slides'], start=1):
            if i <= 2:
                continue
            
            if isinstance(slide, dict):
                content = (slide.get('content', '') or slide.get('text', '') or '').lower()
            else:
                content = str(slide).lower()
                
            # Exclude example slides
            example_keywords = [
                "example", "exemple", "illustration", "illustrative", 
                "no investment recommendation", "not an investment recommendation",
                "historical attractive performance", "world’s largest economy"
            ]
            if any(kw in content for kw in example_keywords):
                continue

            if any(k.lower() in content for k in perf_keywords):
                return i
    
    return None


def infer_glossary_slide(extraction_result: Dict[str, Any]) -> int:
    """
    Infer which slide contains the glossary.
    
    Per compliance rules, glossary typically appears on the last slide for retail documents.
    
    Args:
        extraction_result: Extraction result dictionary
        
    Returns:
        Slide number where glossary appears (defaults to last slide)
    """
    found_slide = infer_slide_containing_text(extraction_result, ['glossaire', 'glossary'])
    
    if found_slide:
        return found_slide
    
    # Default to last slide if not found (per compliance rules)
    return infer_last_slide(extraction_result)
