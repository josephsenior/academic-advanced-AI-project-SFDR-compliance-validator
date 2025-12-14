"""
Registration Country Detector

Detects country mentions in text with context awareness.
"""

import re
from typing import List

from .models import CountryMention
from .constants import COUNTRY_PATTERNS, DISTRIBUTION_KEYWORDS, GENERAL_REFERENCE_KEYWORDS


def detect_country_mentions(
    text: str,
    context_window: int = 100,
    enable_context_awareness: bool = True
) -> List[CountryMention]:
    """
    Detect all country mentions in text with context awareness.
    
    Args:
        text: Text to analyze
        context_window: Characters to capture around each match for context
        enable_context_awareness: Whether to classify distribution claims
        
    Returns:
        List of CountryMention objects with context and classification
    """
    mentions = []
    text_lower = text.lower()
    detected_ranges = []  # Track (start, end, country) to avoid overlaps and duplicates
    
    # Helper function to check if range overlaps or is duplicate country
    def should_skip(start, end, country):
        for existing_start, existing_end, existing_country in detected_ranges:
            # Check if ranges overlap
            if not (end <= existing_start or start >= existing_end):
                return True
            # Check if same country mentioned in close proximity (within 20 chars)
            if country == existing_country and abs(start - existing_start) < 20:
                return True
        return False
    
    for country, pattern in COUNTRY_PATTERNS.items():
        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
            start_pos = match.start()
            end_pos = match.end()
            
            # Skip if this overlaps or is a duplicate
            if should_skip(start_pos, end_pos, country):
                continue
            
            # Mark this range as detected
            detected_ranges.append((start_pos, end_pos, country))
            
            # Extract context window
            context_start = max(0, start_pos - context_window)
            context_end = min(len(text), end_pos + context_window)
            context = text[context_start:context_end]
            
            # Determine if this is a distribution claim
            is_distribution_claim = False
            if enable_context_awareness:
                is_distribution_claim = is_distribution_context(context)
            
            # Create mention object
            mention = CountryMention(
                country=country,
                raw_text=text[start_pos:end_pos],
                context=context,
                position=start_pos,
                is_distribution_claim=is_distribution_claim,
                confidence=1.0,  # Pattern-based detection has high confidence
                location=None
            )
            
            mentions.append(mention)
    
    return mentions


def is_distribution_context(context: str) -> bool:
    """
    Determine if context indicates a distribution/availability claim.
    
    Args:
        context: Text context around country mention
        
    Returns:
        True if distribution claim, False if general reference
    """
    context_lower = context.lower()
    
    # Check for distribution keywords
    distribution_score = sum(1 for kw in DISTRIBUTION_KEYWORDS if kw in context_lower)
    
    # Check for general reference keywords (reduces score)
    reference_score = sum(1 for kw in GENERAL_REFERENCE_KEYWORDS if kw in context_lower)
    
    # Decision: distribution if ANY distribution keywords present, unless dominated by reference keywords
    return distribution_score > 0 and distribution_score >= reference_score

