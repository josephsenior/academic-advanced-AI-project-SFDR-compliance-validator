"""
Anglicism Detector

Detects undefined English words in French/German retail documents.
Only flags for non-professional clients who may not understand technical English terms.

Checks against glossary_disclaimers.json to determine if English words are approved,
otherwise suggests either adding to glossary or replacing with native language equivalent.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass
from backend.extractors.rules.models import ComplianceIssue
from backend.extractors.rules.enums import ComplianceIssueType
from .base import BaseValidator

logger = logging.getLogger(__name__)


@dataclass
class AnglicismFinding:
    """A detected undefined English word in non-English document"""
    word: str
    language: str
    context: str
    location: str
    suggestion: str


class AnglicismDetector(BaseValidator):
    """
    Detects and flags undefined English words in French/German documents.
    
    Only applies to retail (non-professional) clients per Oddo BHF rules.
    Checks against glossary to determine if English terms are pre-approved.
    """
    
    # Common financial/technical terms approved in English across languages
    STANDARD_ENGLISH_TERMS = {
        # Financial terms commonly used in EN/FR/DE
        'etf', 'nav', 'isin', 'isin code', 'cusip', 'bid-ask', 'libor', 'euribor',
        'esg', 'srri', 'var', 'sharpe', 'alpha', 'beta', 'aum', 'ocf',
        'brexit', 'sec', 'esma', 'eba', 'ecb', 'fed', 'fed funds',
        'holdings', 'benchmark', 'backtesting', 'performance', 'volatility',
        'leverage', 'derivative', 'hedge', 'short', 'long', 'overweight',
        'underweight', 'yield', 'duration', 'convexity', 'spread',
        'credit', 'default', 'rating', 'covenant', 'dividend',
        'buyback', 'ipo', 'ipo', 'cap', 'float', 'liquidity', 'spread',
        'tracking error', 'underperformance', 'outperformance',
        # Technology/modern terms
        'bitcoin', 'cryptocurrency', 'blockchain', 'ai', 'ml', 'data',
        'cloud', 'saas', 'api', 'mobile', 'digital', 'online',
        # Brand names and proper nouns handled separately
    }
    
    def __init__(self, glossary_path: Optional[str] = None):
        """
        Initialize Anglicism Detector.
        
        Args:
            glossary_path: Path to glossary_disclaimers.json. 
                          If None, looks in dataset directory.
        """
        self.approved_english_words: Set[str] = set(self.STANDARD_ENGLISH_TERMS)
        self.glossary_data = {}
        
        # Load glossary if available
        self._load_glossary(glossary_path)
    
    def _load_glossary(self, glossary_path: Optional[str]) -> None:
        """Load approved English terms from glossary file."""
        if glossary_path:
            path = Path(glossary_path)
        else:
            # Look in common locations
            path = Path(__file__).parent.parent.parent.parent / "dataset" / "glossary_disclaimers.json"
        
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.glossary_data = json.load(f)
                
                # Extract English terms that are approved
                if isinstance(self.glossary_data, dict):
                    for key, value in self.glossary_data.items():
                        if isinstance(value, dict) and 'en' in value:
                            self.approved_english_words.add(key.lower())
                            self.approved_english_words.add(value['en'].lower())
                
                logger.info(f"Loaded glossary with {len(self.approved_english_words)} approved terms")
            except Exception as e:
                logger.warning(f"Failed to load glossary: {e}")
    
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """
        Validate for undefined Anglicisms.
        
        Only applies to retail (non-professional) clients.
        Returns ComplianceIssue for each undefined English term found.
        """
        issues: List[ComplianceIssue] = []
        
        # Only check for non-professional clients
        if client_type and str(client_type).lower() == 'professional':
            return issues
        
        # Determine document language
        doc_language = self._detect_language(extraction_result, metadata)
        
        # Only check FR and DE documents
        if doc_language not in ['FR', 'DE']:
            return issues
        
        # Extract text
        all_text = self._extract_text(extraction_result)
        
        if not all_text:
            return issues
        
        # Find anglicisms
        findings = self._find_anglicisms(all_text, doc_language)
        
        # Create issues for each finding
        for finding in findings:
            issue = ComplianceIssue(
                issue_type=ComplianceIssueType.ANGLICISM_UNDEFINED,
                issue_category='compliance',
                severity='warning',
                rule_reference="Retail Communication - Language Clarity (Oddo BHF)",
                location=finding.location,
                message=(
                    f"Undefined English term '{finding.word}' used in {doc_language} document "
                    f"for retail clients"
                ),
                context=finding.context[:150],
                suggestion=finding.suggestion,
                auto_fixable=False
            )
            issues.append(issue)
        
        return issues
    
    def _detect_language(self, extraction_result: Dict[str, Any], metadata: Optional[Dict[str, Any]]) -> str:
        """
        Detect document language.
        
        Returns: 'FR', 'EN', 'DE', or 'UNKNOWN'
        """
        # Check metadata first
        if metadata:
            if 'language_code' in metadata:
                lang = metadata['language_code'].upper()
                if lang in ['FR', 'EN', 'DE']:
                    return lang
            
            if 'language' in metadata:
                lang = metadata['language'].upper()[:2]
                if lang in ['FR', 'EN', 'DE']:
                    return lang
        
        # Infer from text
        text = self._extract_text(extraction_result).lower()
        
        # French indicators
        fr_words = ['est', 'pour', 'dans', 'avec', 'sans', 'très', 'français']
        fr_count = sum(1 for w in fr_words if f' {w} ' in f' {text} ')
        
        # German indicators
        de_words = ['ist', 'für', 'mit', 'wird', 'deutsch', 'deutschland']
        de_count = sum(1 for w in de_words if f' {w} ' in f' {text} ')
        
        if fr_count > de_count and fr_count > 5:
            return 'FR'
        elif de_count > fr_count and de_count > 5:
            return 'DE'
        
        # Check for file name hints
        if 'extraction_result' in extraction_result:
            filename = extraction_result.get('extraction_result', {}).get('filename', '').upper()
        else:
            filename = extraction_result.get('filename', '').upper()
        
        if '-FR' in filename or 'FRANCAIS' in filename:
            return 'FR'
        if '-DE' in filename or 'DEUTSCH' in filename:
            return 'DE'
        
        return 'UNKNOWN'
    
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
    
    def _find_anglicisms(self, text: str, language: str) -> List[AnglicismFinding]:
        """
        Find undefined English words in non-English text.
        
        Returns list of AnglicismFinding objects.
        """
        findings = []
        
        # Extract words that look English
        # English words typically: all lowercase, no diacritics, English morphology
        english_patterns = self._get_english_patterns(language)
        
        # Find potential English words
        words = re.findall(r'\b[a-z]+\b', text.lower())
        seen = set()
        
        for word in words:
            if word in seen or len(word) < 3:
                continue
            seen.add(word)
            
            # Check if it looks like an English word in FR/DE text
            if self._is_likely_english(word, language):
                # Check if it's approved
                if word not in self.approved_english_words:
                    # Find context
                    context = self._find_context(text, word, 50)
                    location = self._find_location(text, word)
                    
                    # Suggest replacement
                    suggestion = self._suggest_replacement(word, language)
                    
                    findings.append(AnglicismFinding(
                        word=word,
                        language=language,
                        context=context,
                        location=location,
                        suggestion=suggestion
                    ))
        
        # Sort by frequency (most common first)
        findings = sorted(findings, key=lambda f: text.count(f.word), reverse=True)
        
        # Return top 10
        return findings[:10]
    
    def _get_english_patterns(self, language: str) -> List[str]:
        """Get patterns that indicate English words in specific language."""
        if language == 'FR':
            # French: -tion, -ment, -eur, accent marks
            # English lacks these patterns
            return []
        elif language == 'DE':
            # German: -heit, -keit, -ung, ß, ü, ö, ä
            # English lacks these
            return []
        return []
    
    def _is_likely_english(self, word: str, context_language: str) -> bool:
        """
        Check if word is likely English based on morphology and context.
        """
        # Check common English endings
        english_endings = (
            '-ing', '-tion', '-ness', '-ment', '-able', '-ible',
            '-ity', '-ly', '-er', '-or', '-ist', '-ism'
        )
        
        if any(word.endswith(suffix[1:]) for suffix in english_endings):
            return True
        
        # Check for common English letter patterns
        # English often has vowel-consonant patterns like 'th', 'ch'
        if re.search(r'th[aeiou]|ch[aeiou]|sh[aeiou]', word):
            return True
        
        # No diacritics or umlauts (unlike FR/DE)
        if not re.search(r'[àâäéèêëïîôöùûüœæç]', word):
            # And contains mostly common English letters
            if len(word) >= 4 and word not in ['test', 'code', 'data']:
                return True
        
        return False
    
    def _find_context(self, text: str, word: str, context_len: int = 50) -> str:
        """Find word in context."""
        pattern = r'.{0,' + str(context_len) + r'}' + re.escape(word) + r'.{0,' + str(context_len) + r'}'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group().strip()
        return word
    
    def _find_location(self, text: str, word: str) -> str:
        """Find approximate location in document."""
        # Find which paragraph/section
        paragraphs = text.split('\n\n')
        for i, para in enumerate(paragraphs):
            if word.lower() in para.lower():
                return f"Paragraph {i+1}"
        return "Document body"
    
    def _suggest_replacement(self, english_word: str, target_language: str) -> str:
        """
        Suggest native language equivalent or glossary entry.
        """
        replacements = {
            'FR': {
                'dashboard': 'tableau de bord',
                'performance': 'rendement',
                'holdings': 'portefeuille',
                'benchmark': 'indice de référence',
                'backtest': 'test rétrospectif',
                'alert': 'alerte',
                'tracking': 'suivi',
                'leverage': 'effet de levier',
                'hedge': 'couverture',
                'hedging': 'couverture',
            },
            'DE': {
                'dashboard': 'Übersicht',
                'performance': 'Rendite',
                'holdings': 'Bestände',
                'benchmark': 'Referenzindex',
                'backtest': 'Rückwärts-Test',
                'alert': 'Warnung',
                'tracking': 'Verfolgung',
                'leverage': 'Hebelwirkung',
                'hedge': 'Absicherung',
                'hedging': 'Absicherung',
            }
        }
        
        if target_language in replacements and english_word.lower() in replacements[target_language]:
            suggestion = replacements[target_language][english_word.lower()]
            return f"Consider using '{suggestion}' instead of English term '{english_word}', or add to approved glossary"
        
        return f"Either add '{english_word}' to approved glossary or replace with {target_language} equivalent for clarity to retail clients"
