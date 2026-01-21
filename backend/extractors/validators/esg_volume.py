"""
ESG Volume Validator - Rule 4.1

Validates that ESG content volume complies with Oddo BHF rules:
- Engageante (Article 9): No limit on ESG communication
- Réduite (Article 8): ESG content must not exceed 10% of document volume
- Limitée au prospectus (Article 6): ESG content only in prospectus, not in marketing materials
- Other funds: Only OBAM common exclusions allowed

References:
- Rule 4.1 - ESG Communication Limits
- SFDR Article 8: Réduite approach (10% limit)
- SFDR Article 9: Engageante approach (no limit, but with engagement criteria)
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..rules.models import ComplianceIssue, ComplianceIssueType
from ..rules.enums import ClientType
from ..rules.esg import ESGRules
from .base import BaseValidator


@dataclass
class ESGVolumeMeasurement:
    """Result of ESG volume measurement"""
    total_text_length: int
    esg_character_count: int
    esg_percentage: float
    esg_keywords_found: List[str]
    esg_sentences: List[str]


class ESGVolumeValidator(BaseValidator):
    """Validator for ESG communication volume limits (Rule 4.1)"""
    
    def __init__(self):
        super().__init__()
        self.esg_rules = ESGRules()
        # Expand ESG keywords with more comprehensive list
        self.esg_keywords = list(self.esg_rules.ESG_KEYWORDS)
        
        # Add more granular keywords for better detection
        self.esg_keywords.extend([
            "exclusion", "exclusions", "exclusives",
            "engagement", "engagement policy",
            "sustainable", "sustainability",
            "ESG criteria", "ESG integration",
            "ESG approach", "ESG framework",
            "sustainability risks", "sustainable investment",
            "environmental", "social governance",
            "ethical", "responsible",
            "divestment", "divested",
            "investment grade", "ESG rating",
            "SFDR", "Article 8", "Article 9",
            "Article 6", "sustainability criteria",
            "ecological transition", "transition écologique",
            "sustainable objective", "objectif d'investissement durable"
        ])
    
    def _normalize_client_type(self, client_type_str: Optional[str]) -> Optional[ClientType]:
        """
        Convert metadata client_type string to ComplianceIssue enum
        
        Args:
            client_type_str: Client type from metadata ('Professional', 'Non-professional', 'retail', 'professional', etc.)
            
        Returns:
            ClientType enum or None
        """
        if not client_type_str:
            return None
        
        client_lower = client_type_str.lower()
        
        # Map various formats to enum values
        if 'professional' in client_lower and 'non' not in client_lower:
            return ClientType.PROFESSIONAL
        elif 'non' in client_lower or 'retail' in client_lower:
            return ClientType.RETAIL
        elif 'informed' in client_lower:
            return ClientType.WELL_INFORMED
        
        return None
    
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[ComplianceIssue]:
        """
        Validate ESG volume against Rule 4.1 limits
        
        Args:
            extraction_result: Extracted document content
            metadata: Document metadata including esg_approach
            
        Returns:
            List of compliance issues (empty if compliant)
        """
        issues = []
        
        if not metadata:
            return issues
        
        # Get ESG approach from metadata
        esg_approach = metadata.get('esg_approach')
        if not esg_approach:
            # Cannot validate without knowing ESG approach
            return issues
        
        # Only validate for non-professional clients (retail funds)
        is_professional = metadata.get('is_professional_client', False)
        if is_professional:
            # Professional funds are exempt from ESG volume limits
            return issues
        
        # Normalize client_type for ComplianceIssue enum
        client_type_enum = self._normalize_client_type(metadata.get('client_type'))
        
        # Measure ESG volume
        measurement = self._measure_esg_volume(extraction_result)
        
        # Check compliance based on ESG approach
        if esg_approach == 'Réduite':
            # Article 8: ESG content must not exceed 10% of document
            if measurement.esg_percentage > self.esg_rules.REDUITE_MAX_VOLUME_PCT:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.ESG_OVERMENTIONED_ARTICLE8,
                    rule_reference="Rule 4.1 - ESG Communication Limits (Article 8 - Réduite)",
                    location="Slides 1-3 - ESG claims and messaging sections",
                    slide_number=1,
                    severity="high",
                    message=f"ESG communication volume exceeds 10% limit ({measurement.esg_percentage:.1f}% of document)",
                    context=(
                        f"Detected {measurement.esg_character_count} ESG characters "
                        f"out of {measurement.total_text_length} total characters. "
                        f"ESG approach: {esg_approach} (Article 8)"
                    ),
                    suggestion=(
                        f"Reduce ESG content from {measurement.esg_percentage:.1f}% to below 10%. "
                        f"Target: remove at least {int(measurement.esg_character_count * (measurement.esg_percentage - 10) / measurement.esg_percentage)} characters. "
                        f"Prioritize legally required ESG statements over promotional ESG messaging."
                    ),
                    client_type=client_type_enum,
                    fund_type=None,
                    details={
                        "esg_percentage": measurement.esg_percentage,
                        "esg_characters": measurement.esg_character_count,
                        "total_characters": measurement.total_text_length,
                        "limit": self.esg_rules.REDUITE_MAX_VOLUME_PCT,
                        "esg_keywords_found": measurement.esg_keywords_found[:10]  # Top 10
                    }
                ))
        
        elif esg_approach == 'Limitée au prospectus':
            # Article 6: ESG content only allowed in prospectus, not in marketing materials
            # This is a 6-page or presentation document (marketing material)
            if measurement.esg_percentage > 0.5:  # Allow minimal mentions (< 0.5%)
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.ESG_NOT_ALLOWED_FOR_APPROACH,
                    rule_reference="Rule 4.1 - ESG Communication Limits (Article 6 - Limitée au prospectus)",
                    location="Throughout document",
                    slide_number=1,
                    severity="critical",
                    message=f"ESG content not allowed in marketing materials for Article 6 funds ({measurement.esg_percentage:.1f}% detected)",
                    context=(
                        f"Fund uses 'Limitée au prospectus' approach (Article 6). "
                        f"ESG mentions are only allowed in the prospectus, not in 6-page presentations or marketing documents. "
                        f"Found {measurement.esg_character_count} ESG-related characters."
                    ),
                    suggestion=(
                        "Remove all ESG content from this marketing document. "
                        "ESG information should only appear in the official prospectus. "
                        "Consider using OBAM common exclusions only."
                    ),
                    client_type=client_type_enum,
                    fund_type=None,
                    details={
                        "esg_percentage": measurement.esg_percentage,
                        "esg_characters": measurement.esg_character_count,
                        "total_characters": measurement.total_text_length,
                        "esg_keywords_found": measurement.esg_keywords_found[:10]
                    }
                ))
        
        elif esg_approach not in ['Engageante', 'Réduite', 'Limitée au prospectus']:
            # Unknown ESG approach - flag for review
            if measurement.esg_percentage > 0:
                issues.append(ComplianceIssue(
                    issue_type=ComplianceIssueType.ESG_LEVEL_MISMATCH,
                    rule_reference="Rule 4.1 - ESG Approach Clarification",
                    location="Throughout document",
                    slide_number=1,
                    severity="medium",
                    message=f"Unknown ESG approach '{esg_approach}' - unable to validate volume limits",
                    context=(
                        f"ESG approach in metadata: '{esg_approach}'. "
                        f"Must be one of: 'Engageante', 'Réduite', 'Limitée au prospectus'. "
                        f"Document contains {measurement.esg_percentage:.1f}% ESG content."
                    ),
                    suggestion=(
                        "Verify ESG approach in metadata. "
                        "Select correct approach: Engageante (Article 9), Réduite (Article 8), or Limitée au prospectus (Article 6)"
                    ),
                    client_type=client_type_enum,
                    fund_type=None
                ))
        
        return issues
    
    def _measure_esg_volume(self, extraction_result: Dict[str, Any]) -> ESGVolumeMeasurement:
        """
        Measure ESG content volume in document
        
        Args:
            extraction_result: Extracted document content
            
        Returns:
            ESGVolumeMeasurement with volume statistics
        """
        # Get full text from extraction result
        full_text = extraction_result.get('full_text', '') or extraction_result.get('text', '')
        
        if not full_text:
            return ESGVolumeMeasurement(
                total_text_length=0,
                esg_character_count=0,
                esg_percentage=0.0,
                esg_keywords_found=[],
                esg_sentences=[]
            )
        
        total_length = len(full_text)
        text_lower = full_text.lower()
        
        # Find ESG keywords and count characters
        esg_char_count = 0
        keywords_found = {}
        sentences_with_esg = []
        
        # Split into sentences for context
        sentences = self._split_sentences(full_text)
        
        for keyword in self.esg_keywords:
            keyword_lower = keyword.lower()
            count = 0
            
            # Count occurrences of this keyword
            for match in re.finditer(r'\b' + re.escape(keyword_lower) + r'\b', text_lower):
                count += 1
                # Add surrounding context
                start = max(0, match.start() - 50)
                end = min(len(full_text), match.end() + 50)
                context_sentence = full_text[start:end].strip()
                
                if context_sentence not in sentences_with_esg:
                    sentences_with_esg.append(context_sentence)
            
            if count > 0:
                keywords_found[keyword] = count
                # Estimate character count for this keyword (keyword + context)
                # Simple approach: assume 50 characters of context per match
                esg_char_count += count * (len(keyword) + 100)
        
        # Normalize ESG character count to avoid over-counting
        esg_char_count = min(esg_char_count, total_length)  # Cap at total length
        
        # Calculate percentage
        esg_percentage = (esg_char_count / total_length * 100) if total_length > 0 else 0.0
        
        # Sort keywords by frequency
        sorted_keywords = sorted(keywords_found.items(), key=lambda x: x[1], reverse=True)
        keywords_list = [f"{kw} (×{count})" for kw, count in sorted_keywords]
        
        return ESGVolumeMeasurement(
            total_text_length=total_length,
            esg_character_count=esg_char_count,
            esg_percentage=esg_percentage,
            esg_keywords_found=keywords_list,
            esg_sentences=sentences_with_esg[:5]  # Top 5 sentences with ESG content
        )
    
    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """
        Split text into sentences
        
        Args:
            text: Full text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting on . ! ? and newlines
        # This is basic but sufficient for identifying ESG-related sentences
        patterns = [
            r'[.!?]\s+(?=[A-Z])',  # Period/exclamation/question followed by capital
            r'\n+',  # Newlines
            r'[.!?]$'  # End of text
        ]
        
        pattern = '|'.join(patterns)
        sentences = re.split(pattern, text)
        
        # Clean up and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
        
        return sentences[:100]  # Limit to first 100 sentences for performance
