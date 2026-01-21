"""
Translation Consistency Validator

Validates that translations across multiple languages maintain semantic consistency.
Uses embeddings-based semantic similarity to detect translations that deviate
from the original meaning by more than a threshold (default 15%).

Works for FR/EN/DE language pairs commonly used in financial marketing documents.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType
from .base import BaseValidator

logger = logging.getLogger(__name__)

# Language pair patterns for detecting translations
LANGUAGE_MARKERS = {
    'FR': {
        'keywords': ['français', 'france', 'fr:'],
        'stopwords': ['le', 'la', 'les', 'de', 'des', 'et', 'ou', 'un', 'une']
    },
    'EN': {
        'keywords': ['english', 'uk', 'us', 'en:'],
        'stopwords': ['the', 'a', 'an', 'and', 'or', 'of', 'in', 'is']
    },
    'DE': {
        'keywords': ['deutsch', 'german', 'deutschland', 'de:'],
        'stopwords': ['der', 'die', 'das', 'und', 'oder', 'ein', 'eine']
    }
}


@dataclass
class TranslationComparison:
    """Result of comparing two language versions"""
    source_lang: str
    target_lang: str
    source_text: str
    target_text: str
    similarity_score: float  # 0-1, where 1 = identical meaning
    divergence_percent: float  # 0-100, where 100 = completely different
    is_violation: bool  # True if divergence > threshold
    deviations: List[str]  # Specific deviations found


class TranslationConsistencyValidator(BaseValidator):
    """
    Validates semantic consistency of translations across languages.
    
    Detects when financial documents have multiple language versions
    and checks if the translations maintain semantic equivalence.
    """
    
    def __init__(self, divergence_threshold: float = 15.0, use_embeddings: bool = True):
        """
        Initialize validator.
        
        Args:
            divergence_threshold: Maximum allowed divergence % (default 15%)
            use_embeddings: Use transformer embeddings for similarity (requires transformers)
        """
        self.divergence_threshold = divergence_threshold
        self.use_embeddings = use_embeddings
        self._embeddings_available = False
        
        # Try to load embeddings model
        if use_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                # Multilingual model that handles FR, EN, DE
                self.embeddings_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
                self._embeddings_available = True
                logger.info("Translation Consistency: Embeddings model loaded")
            except ImportError:
                logger.warning("Translation Consistency: sentence-transformers not available, using keyword-based similarity")
                self._embeddings_available = False
            except Exception as e:
                logger.warning(f"Translation Consistency: Failed to load embeddings: {e}, using keyword-based similarity")
                self._embeddings_available = False
    
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate translation consistency.
        
        Returns ComplianceIssue for each translation that diverges beyond threshold.
        """
        issues: List[ComplianceIssue] = []
        
        # Extract all text content
        all_text = self._extract_text(extraction_result)
        
        if not all_text:
            return issues
        
        # Detect language sections/pairs
        language_sections = self._detect_language_sections(all_text)
        
        if len(language_sections) < 2:
            # No multilingual content detected
            return issues
        
        # Compare each pair of languages
        for lang_pair, sections in self._generate_language_pairs(language_sections):
            source_lang, target_lang = lang_pair
            source_text = sections.get(source_lang, '')
            target_text = sections.get(target_lang, '')
            
            if not source_text or not target_text:
                continue
            
            # Compare similarity
            comparison = self._compare_translations(
                source_text, target_text, source_lang, target_lang
            )
            
            if comparison.is_violation:
                # Create issue for significant divergence
                issue = ComplianceIssue(
                    issue_type=ComplianceIssueType.TRANSLATION_INCONSISTENCY,
                    issue_category='compliance',
                    severity='warning',
                    rule_reference="Translation Consistency Check",
                    location=f"Translation: {source_lang} → {target_lang}",
                    message=(
                        f"Translation divergence detected: {comparison.divergence_percent:.1f}% "
                        f"({source_lang} → {target_lang}) exceeds {self.divergence_threshold}% threshold"
                    ),
                    context=f"Source ({source_lang}): {source_text[:100]}...\n"
                            f"Target ({target_lang}): {target_text[:100]}...",
                    suggestion=(
                        f"Review translation for semantic accuracy. "
                        f"Deviations found: {', '.join(comparison.deviations[:3]) if comparison.deviations else 'general meaning shift'}"
                    ),
                    auto_fixable=False
                )
                issues.append(issue)
        
        return issues
    
    def _extract_text(self, extraction_result: Dict[str, Any]) -> str:
        """Extract all text from extraction result."""
        text_parts = []
        
        # From slides
        if 'slides' in extraction_result:
            for slide in extraction_result['slides']:
                if isinstance(slide, dict):
                    text_parts.append(slide.get('content', '') or slide.get('text', ''))
                elif isinstance(slide, str):
                    text_parts.append(slide)
        
        # From pages
        if 'pages' in extraction_result:
            for page in extraction_result['pages']:
                if isinstance(page, dict):
                    text_parts.append(page.get('content', '') or page.get('text', ''))
                elif isinstance(page, str):
                    text_parts.append(page)
        
        # Main text
        if 'text' in extraction_result:
            text_parts.append(extraction_result['text'])
        
        return ' '.join(filter(None, text_parts))
    
    def _detect_language_sections(self, text: str) -> Dict[str, str]:
        """
        Detect language sections in document.
        
        Returns dict mapping language code to detected text.
        """
        sections = {}
        text_lower = text.lower()
        
        # Look for language markers and split sections
        # Simple heuristic: look for explicit language headers
        for lang_code, markers in LANGUAGE_MARKERS.items():
            for keyword in markers['keywords']:
                pattern = rf'{re.escape(keyword)}[:\s]+([^a-z][^\.]*[\.!?]{{1,3}})'
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    sections[lang_code] = ' '.join(matches)
        
        # If no explicit markers, try to infer by word content
        if not sections:
            sections = self._infer_languages(text)
        
        return sections
    
    def _infer_languages(self, text: str) -> Dict[str, str]:
        """
        Infer languages present in document by analyzing word content.
        
        Simple approach: use distinctive words for each language.
        """
        sections = {}
        
        # Language-specific distinctive words
        distinctive_words = {
            'FR': ['est', 'pour', 'dans', 'cela', 'avec', 'sans', 'très'],
            'EN': ['is', 'for', 'with', 'this', 'that', 'about', 'more'],
            'DE': ['ist', 'der', 'für', 'mit', 'einen', 'keine', 'zu']
        }
        
        text_words = text.lower().split()
        lang_scores = {'FR': 0, 'EN': 0, 'DE': 0}
        
        for word in text_words:
            # Remove punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            for lang, keywords in distinctive_words.items():
                if clean_word in keywords:
                    lang_scores[lang] += 1
        
        # If significant text for multiple languages, include them
        total = sum(lang_scores.values())
        if total > 0:
            for lang, score in lang_scores.items():
                if score / total > 0.1:  # At least 10% of distinctive words
                    sections[lang] = text  # Use full text as proxy
        
        return sections
    
    def _generate_language_pairs(
        self, language_sections: Dict[str, str]
    ) -> List[Tuple[Tuple[str, str], Dict[str, str]]]:
        """
        Generate language pairs to compare.
        
        Returns list of (lang_pair, sections) tuples.
        """
        pairs = []
        langs = sorted(language_sections.keys())
        
        # Generate all pairs (typically FR-EN, FR-DE, EN-DE)
        for i, lang1 in enumerate(langs):
            for lang2 in langs[i+1:]:
                pairs.append(((lang1, lang2), language_sections))
        
        return pairs
    
    def _compare_translations(
        self,
        source_text: str,
        target_text: str,
        source_lang: str,
        target_lang: str
    ) -> TranslationComparison:
        """
        Compare semantic similarity of source and target text.
        
        Uses embeddings if available, falls back to keyword/length-based heuristic.
        """
        if self._embeddings_available:
            similarity = self._embeddings_similarity(source_text, target_text)
        else:
            similarity = self._keyword_similarity(source_text, target_text, source_lang, target_lang)
        
        divergence_percent = (1 - similarity) * 100
        is_violation = divergence_percent > self.divergence_threshold
        
        # Find specific deviations
        deviations = self._find_deviations(
            source_text, target_text, source_lang, target_lang
        )
        
        return TranslationComparison(
            source_lang=source_lang,
            target_lang=target_lang,
            source_text=source_text[:200],
            target_text=target_text[:200],
            similarity_score=similarity,
            divergence_percent=divergence_percent,
            is_violation=is_violation,
            deviations=deviations
        )
    
    def _embeddings_similarity(self, source_text: str, target_text: str) -> float:
        """
        Compute semantic similarity using transformer embeddings.
        
        Returns: 0-1 similarity score where 1 = identical meaning
        """
        try:
            # Get embeddings
            embeddings = self.embeddings_model.encode(
                [source_text, target_text],
                convert_to_tensor=False
            )
            
            # Compute cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            similarity = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
            
            # Clamp to 0-1 range
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            logger.warning(f"Embeddings similarity failed: {e}, using fallback")
            return self._keyword_similarity(source_text, target_text, '', '')
    
    def _keyword_similarity(
        self,
        source_text: str,
        target_text: str,
        source_lang: str,
        target_lang: str
    ) -> float:
        """
        Fallback similarity using keyword overlap and length ratio.
        
        Returns: 0-1 similarity score
        """
        # Normalize texts
        source_words = set(self._tokenize(source_text, source_lang))
        target_words = set(self._tokenize(target_text, target_lang))
        
        # Intersection over union
        if not source_words or not target_words:
            return 0.0
        
        intersection = len(source_words & target_words)
        union = len(source_words | target_words)
        
        keyword_similarity = intersection / union if union > 0 else 0.0
        
        # Also consider length ratio (translations shouldn't differ drastically)
        length_ratio = min(len(source_text), len(target_text)) / max(len(source_text), len(target_text))
        
        # Weighted average
        return (keyword_similarity * 0.7) + (length_ratio * 0.3)
    
    def _tokenize(self, text: str, lang: str) -> List[str]:
        """
        Simple tokenization, removing stopwords and punctuation.
        """
        # Remove punctuation and split
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stopwords
        stopwords = LANGUAGE_MARKERS.get(lang, {}).get('stopwords', [])
        filtered = [w for w in words if w not in stopwords and len(w) > 2]
        
        return filtered
    
    def _find_deviations(
        self,
        source_text: str,
        target_text: str,
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """
        Find specific deviations between translations.
        
        Returns list of deviation descriptions.
        """
        deviations = []
        
        # Length-based deviation
        length_ratio = len(target_text) / len(source_text) if source_text else 0
        if length_ratio < 0.7 or length_ratio > 1.3:
            deviations.append(f"Text length differs by {abs(length_ratio - 1) * 100:.0f}%")
        
        # Keyword-based deviations
        source_words = set(self._tokenize(source_text, source_lang))
        target_words = set(self._tokenize(target_text, target_lang))
        
        missing_concepts = source_words - target_words
        extra_concepts = target_words - source_words
        
        if missing_concepts:
            sample = list(missing_concepts)[:2]
            deviations.append(f"Missing concepts: {', '.join(sample)}")
        
        if extra_concepts:
            sample = list(extra_concepts)[:2]
            deviations.append(f"Extra concepts: {', '.join(sample)}")
        
        return deviations[:3]  # Return top 3 deviations
