"""
Enhanced Text Matching Module

Multi-level text matching algorithm extracted from teammate's work.
Provides robust disclaimer detection with fallback matching strategies.
"""

import re
import unicodedata
from typing import Tuple, Set, Dict, Any
from difflib import SequenceMatcher


class TextNormalizer:
    """Normalizes text for improved matching accuracy"""
    
    @staticmethod
    def normalize(text: str) -> str:
        """
        Complete text normalization for matching.
        
        Steps:
        1. Convert to lowercase
        2. Remove accents/diacritics
        3. Remove excessive punctuation
        4. Normalize whitespace
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text string
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove accents using Unicode normalization
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('utf-8')
        
        # Remove punctuation (keep alphanumeric and spaces)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 4) -> Set[str]:
        """
        Extract significant keywords from text.
        
        Args:
            text: Text to extract keywords from
            min_length: Minimum word length to consider
            
        Returns:
            Set of keyword strings
        """
        normalized = TextNormalizer.normalize(text)
        words = normalized.split()
        
        # Filter words by minimum length
        keywords = {w for w in words if len(w) >= min_length}
        
        # Remove common stop words (French and English)
        stop_words = {
            # French
            'dans', 'avec', 'pour', 'cette', 'sont', 'plus', 'peut', 'tout', 'tous',
            'cette', 'sans', 'être', 'avoir', 'faire', 'dire', 'elle', 'nous', 'vous',
            'leur', 'leurs', 'comme', 'mais', 'donc', 'très', 'aussi', 'autre',
            # English
            'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'will',
            'their', 'they', 'been', 'were', 'which', 'when', 'where', 'what',
            'there', 'would', 'could', 'should', 'about', 'into', 'through', 'after'
        }
        keywords = keywords - stop_words
        
        return keywords


class EnhancedTextMatcher:
    """
    Multi-level text matching with confidence scoring.
    
    Matching Levels:
    1. Exact Match (100% confidence)
    2. High Similarity (85%+ via SequenceMatcher)
    3. Key Sentences (60%+ sentence fragments matched)
    4. Keywords (50%+ common keywords)
    5. No Match
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize enhanced text matcher.
        
        Args:
            debug: Enable detailed matching logs
        """
        self.debug = debug
    
    def match(
        self,
        required_text: str,
        target_text: str,
        strict_mode: bool = False
    ) -> Tuple[bool, float, str]:
        """
        Multi-level text matching with fallback strategies.
        
        Args:
            required_text: Text that should be present (e.g., expected disclaimer)
            target_text: Text to search in (e.g., document content)
            strict_mode: If True, only accept matches with >85% confidence
            
        Returns:
            Tuple of (is_match, confidence_score, match_method)
            - is_match: Boolean indicating if match found
            - confidence_score: Float 0.0-1.0
            - match_method: String describing which level matched
        """
        # Normalize both texts
        normalized_required = TextNormalizer.normalize(required_text)
        normalized_target = TextNormalizer.normalize(target_text)
        
        if self.debug:
            print(f"    [SEARCH] Matching text (length: {len(required_text)} chars)")
        
        # LEVEL 1: Exact Match (100% confidence)
        if normalized_required in normalized_target:
            if self.debug:
                print("       [OK] EXACT MATCH (100%)")
            return True, 1.0, "exact_match"
        
        # LEVEL 2: High Similarity via SequenceMatcher (85%+)
        similarity = SequenceMatcher(None, normalized_required, normalized_target).ratio()
        if similarity > 0.85:
            if self.debug:
                print(f"       [OK] HIGH SIMILARITY ({similarity:.1%})")
            return True, similarity, "high_similarity"
        
        # LEVEL 3: Key Sentences Match (60%+ sentences present)
        sentence_ratio = self._match_key_sentences(normalized_required, normalized_target)
        if sentence_ratio >= 0.6:
            if self.debug:
                print(f"       [OK] KEY SENTENCES ({sentence_ratio:.1%})")
            return True, sentence_ratio, "key_sentences"
        
        # LEVEL 4: Keywords Match (50%+ keywords present)
        required_keywords = TextNormalizer.extract_keywords(required_text)
        target_keywords = TextNormalizer.extract_keywords(target_text)
        
        keyword_ratio = 0
        if required_keywords:
            common_keywords = required_keywords & target_keywords
            keyword_ratio = len(common_keywords) / len(required_keywords)
            
            if keyword_ratio >= 0.5:
                if self.debug:
                    print(f"       [OK] KEYWORDS MATCH ({keyword_ratio:.1%})")
                    print(f"          Common words: {list(common_keywords)[:5]}")
                return True, keyword_ratio, "keywords_match"
        
        # LEVEL 5: No significant match
        max_score = max(similarity, sentence_ratio, keyword_ratio)
        if self.debug:
            print(f"       [FAIL] NO MATCH (best score: {max_score:.1%})")
        
        # In strict mode, require >85% confidence
        if strict_mode:
            return False, max_score, "no_match"
        
        return False, max_score, "no_match"
    
    def _match_key_sentences(self, required: str, target: str) -> float:
        """
        Match key sentence fragments.
        
        Args:
            required: Normalized required text
            target: Normalized target text
            
        Returns:
            Ratio of matched sentences (0.0-1.0)
        """
        # Split into sentences (by period)
        required_sentences = [
            s.strip() 
            for s in required.split('.') 
            if len(s.strip()) > 30  # Only meaningful sentences
        ]
        
        if not required_sentences:
            return 0.0
        
        matched_sentences = 0
        
        for sentence in required_sentences:
            words = sentence.split()
            if len(words) >= 5:
                # Take 70% of the sentence words
                sample_size = max(5, int(len(words) * 0.7))
                fragment = ' '.join(words[:sample_size])
                
                # Check if fragment is present
                if fragment in target:
                    matched_sentences += 1
        
        return matched_sentences / len(required_sentences)
    
    def match_with_preprocessed(
        self,
        normalized_required: str,
        required_keywords: Set[str],
        target_text: str,
        strict_mode: bool = False
    ) -> Tuple[bool, float, str]:
        """
        Optimized matching with pre-normalized/pre-extracted data.
        
        Useful when matching the same required text against multiple targets.
        
        Args:
            normalized_required: Pre-normalized required text
            required_keywords: Pre-extracted required text keywords
            target_text: Target text to search in
            strict_mode: If True, only accept matches with >85% confidence
            
        Returns:
            Tuple of (is_match, confidence_score, match_method)
        """
        normalized_target = TextNormalizer.normalize(target_text)
        
        # LEVEL 1: Exact Match
        if normalized_required in normalized_target:
            return True, 1.0, "exact_match"
        
        # LEVEL 2: High Similarity
        similarity = SequenceMatcher(None, normalized_required, normalized_target).ratio()
        if similarity > 0.85:
            return True, similarity, "high_similarity"
        
        # LEVEL 3: Key Sentences
        sentence_ratio = self._match_key_sentences(normalized_required, normalized_target)
        if sentence_ratio >= 0.6:
            return True, sentence_ratio, "key_sentences"
        
        # LEVEL 4: Keywords
        target_keywords = TextNormalizer.extract_keywords(target_text)
        keyword_ratio = 0
        
        if required_keywords:
            common_keywords = required_keywords & target_keywords
            keyword_ratio = len(common_keywords) / len(required_keywords)
            
            if keyword_ratio >= 0.5:
                return True, keyword_ratio, "keywords_match"
        
        # LEVEL 5: No Match
        max_score = max(similarity, sentence_ratio, keyword_ratio)
        
        if strict_mode:
            return False, max_score, "no_match"
        
        return False, max_score, "no_match"


class DisclaimerTextMatcher:
    """
    Specialized matcher for disclaimer validation with intelligent fallbacks.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize disclaimer matcher.
        
        Args:
            debug: Enable detailed logs
        """
        self.matcher = EnhancedTextMatcher(debug=debug)
        self.debug = debug
        self._preprocessed_cache: Dict[str, Dict[str, Any]] = {}
    
    def preprocess_disclaimer(self, disclaimer_id: str, disclaimer_text: str) -> None:
        """
        Preprocess and cache a disclaimer for faster matching.
        
        Args:
            disclaimer_id: Unique identifier for the disclaimer
            disclaimer_text: Full disclaimer text
        """
        self._preprocessed_cache[disclaimer_id] = {
            'normalized': TextNormalizer.normalize(disclaimer_text),
            'keywords': TextNormalizer.extract_keywords(disclaimer_text),
            'original': disclaimer_text
        }
    
    def match_disclaimer(
        self,
        disclaimer_id: str,
        disclaimer_text: str,
        document_text: str,
        strict: bool = False
    ) -> Tuple[bool, float, str]:
        """
        Match a disclaimer against document text.
        
        Args:
            disclaimer_id: Disclaimer identifier (for caching)
            disclaimer_text: Expected disclaimer text
            document_text: Document text to search
            strict: Use strict matching threshold
            
        Returns:
            Tuple of (found, confidence, method)
        """
        # Use cached preprocessed data if available
        if disclaimer_id in self._preprocessed_cache:
            cached = self._preprocessed_cache[disclaimer_id]
            return self.matcher.match_with_preprocessed(
                cached['normalized'],
                cached['keywords'],
                document_text,
                strict_mode=strict
            )
        else:
            # Preprocess and cache for future use
            self.preprocess_disclaimer(disclaimer_id, disclaimer_text)
            return self.match_disclaimer(disclaimer_id, disclaimer_text, document_text, strict)
    
    def clear_cache(self) -> None:
        """Clear the preprocessing cache."""
        self._preprocessed_cache.clear()
