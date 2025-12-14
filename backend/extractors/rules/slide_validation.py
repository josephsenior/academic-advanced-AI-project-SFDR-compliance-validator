"""
Slide-Level Validation Rules

Detailed slide-by-slide validation rules extracted from teammate's work.
"""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class SlideValidationRules:
    """
    Detailed slide-by-slide validation rules.
    
    Extracted from teammate's work - provides granular validation
    for specific slide positions and content types.
    """
    
    # Cover Page (Slide 1) Rules
    COVER_REQUIRED_ELEMENTS = [
        "fund_name",
        "document_type",
        "date",
        "management_company"
    ]
    
    COVER_OPTIONAL_ELEMENTS = [
        "logo",
        "isin",
        "share_class"
    ]
    
    # Slide 2 Typical Rules (Summary/Overview)
    SLIDE_2_REQUIRED_ELEMENTS = [
        "fund_objective",
        "investment_approach"
    ]
    
    SLIDE_2_DISCLAIMERS_REQUIRED = [
        "obam_presentation"  # Must appear by slide 2
    ]
    
    # Performance Section Rules
    PERFORMANCE_SLIDE_REQUIRED_ELEMENTS = [
        "performance_data",
        "date_range",
        "share_class",
        "performance_disclaimer"
    ]
    
    PERFORMANCE_SLIDE_OPTIONAL_ELEMENTS = [
        "benchmark",
        "calendar_year_performance",
        "risk_metrics"
    ]
    
    # Minimum text length by slide type
    MIN_TEXT_LENGTH_COVER = 50  # chars
    MIN_TEXT_LENGTH_CONTENT = 100  # chars
    MIN_TEXT_LENGTH_PERFORMANCE = 150  # chars (more due to disclaimers)
    
    # Maximum reasonable lengths (to detect missing content)
    MAX_TEXT_LENGTH_COVER = 500
    MAX_TEXT_LENGTH_NORMAL = 2000
    
    @staticmethod
    def validate_cover_slide(slide_content: Dict[str, Any]) -> List[str]:
        """
        Validate cover slide (typically slide 1).
        
        Args:
            slide_content: Slide content dictionary
            
        Returns:
            List of error messages
        """
        errors = []
        text = slide_content.get('text', '')
        
        # Check minimum length
        if len(text) < SlideValidationRules.MIN_TEXT_LENGTH_COVER:
            errors.append(
                f"Cover slide too short ({len(text)} chars). "
                f"Expected at least {SlideValidationRules.MIN_TEXT_LENGTH_COVER} chars."
            )
        
        # Check for required elements (basic heuristics)
        text_lower = text.lower()
        
        if not any(word in text_lower for word in ['fund', 'fonds', 'strategy', 'stratégie']):
            errors.append("Cover slide missing fund/strategy name")
        
        if not any(word in text_lower for word in ['20', '19']) or 'date' not in slide_content:
            errors.append("Cover slide missing or unclear date")
        
        if 'oddo' not in text_lower and 'obam' not in text_lower:
            errors.append("Cover slide missing management company branding")
        
        return errors
    
    @staticmethod
    def validate_summary_slide(slide_content: Dict[str, Any], slide_num: int) -> List[str]:
        """
        Validate summary/overview slide (typically slide 2).
        
        Args:
            slide_content: Slide content dictionary
            slide_num: Slide number
            
        Returns:
            List of error messages
        """
        errors = []
        text = slide_content.get('text', '')
        text_lower = text.lower()
        
        # Check minimum length
        if len(text) < SlideValidationRules.MIN_TEXT_LENGTH_CONTENT:
            errors.append(
                f"Slide {slide_num} (summary) too short ({len(text)} chars). "
                f"Expected at least {SlideValidationRules.MIN_TEXT_LENGTH_CONTENT} chars."
            )
        
        # Check for objective/approach
        if not any(word in text_lower for word in ['objective', 'objectif', 'approach', 'approche', 'strategy', 'stratégie']):
            errors.append(f"Slide {slide_num} missing fund objective or investment approach")
        
        return errors
    
    @staticmethod
    def validate_performance_slide(
        slide_content: Dict[str, Any],
        slide_num: int,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """
        Validate performance slide with strict requirements.
        
        Args:
            slide_content: Slide content dictionary
            slide_num: Slide number
            metadata: Document metadata
            
        Returns:
            List of error messages
        """
        errors = []
        text = slide_content.get('text', '')
        text_lower = text.lower()
        
        # Check minimum length (performance slides need disclaimers)
        if len(text) < SlideValidationRules.MIN_TEXT_LENGTH_PERFORMANCE:
            errors.append(
                f"Slide {slide_num} (performance) too short ({len(text)} chars). "
                f"Expected at least {SlideValidationRules.MIN_TEXT_LENGTH_PERFORMANCE} chars "
                f"(including disclaimers)."
            )
        
        # Check for performance disclaimer
        disclaimer_keywords = [
            'past performance', 'performances passées',
            'not indicative', 'ne préjuge pas',
            'not a guarantee', 'ne garantit pas'
        ]
        
        has_disclaimer = any(keyword in text_lower for keyword in disclaimer_keywords)
        if not has_disclaimer:
            errors.append(
                f"Slide {slide_num} (performance) missing required performance disclaimer"
            )
        
        # Check for date information
        if not any(word in text for word in ['20', '19']) and 'as of' not in text_lower:
            errors.append(
                f"Slide {slide_num} (performance) missing date information"
            )
        
        # Check for share class
        if metadata.get('document_type') == 'fund_presentation':
            if not any(word in text for word in ['CR', 'DR', 'CN', 'DN', 'GC', 'share class', 'classe']):
                errors.append(
                    f"Slide {slide_num} (performance) missing share class information"
                )
        
        return errors
    
    @staticmethod
    def validate_structural_consistency(
        all_slides: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> List[str]:
        """
        Validate structural consistency across all slides.
        
        Args:
            all_slides: List of all slide content dictionaries
            metadata: Document metadata
            
        Returns:
            List of error messages
        """
        errors = []
        
        if not all_slides:
            errors.append("No slides found in document")
            return errors
        
        # Check minimum slide count
        if len(all_slides) < 3:
            errors.append(
                f"Document has only {len(all_slides)} slides. "
                f"Expected at least 3 (cover + content)."
            )
        
        # Check if first slide is cover
        first_slide = all_slides[0]
        first_text = first_slide.get('text', '')
        
        if len(first_text) > SlideValidationRules.MAX_TEXT_LENGTH_COVER:
            errors.append(
                f"First slide too long ({len(first_text)} chars). "
                f"May not be a proper cover slide."
            )
        
        # Check for extremely short slides (likely empty)
        for idx, slide in enumerate(all_slides, 1):
            text = slide.get('text', '')
            if len(text) < 20:  # Very short
                errors.append(f"Slide {idx} appears to be empty or nearly empty")
        
        # Check that performance disclaimers appear on performance slides
        performance_slides = [
            i for i, s in enumerate(all_slides, 1)
            if 'performance' in s.get('text', '').lower()
            or any(word in s.get('text', '') for word in ['%', 'return', 'rendement'])
        ]
        
        for perf_slide_num in performance_slides:
            slide = all_slides[perf_slide_num - 1]
            text_lower = slide.get('text', '').lower()
            
            disclaimer_keywords = [
                'past performance', 'performances passées',
                'not indicative', 'ne préjuge pas'
            ]
            
            has_disclaimer = any(keyword in text_lower for keyword in disclaimer_keywords)
            if not has_disclaimer:
                errors.append(
                    f"Slide {perf_slide_num} contains performance data but "
                    f"missing performance disclaimer"
                )
        
        return errors
    
    @staticmethod
    def validate_slide_by_position(
        slide_content: Dict[str, Any],
        slide_num: int,
        total_slides: int,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """
        Validate a slide based on its position in the document.
        
        Args:
            slide_content: Slide content dictionary
            slide_num: Slide number (1-indexed)
            total_slides: Total number of slides
            metadata: Document metadata
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Slide 1: Cover page
        if slide_num == 1:
            errors.extend(SlideValidationRules.validate_cover_slide(slide_content))
        
        # Slide 2: Usually summary/overview
        elif slide_num == 2:
            errors.extend(SlideValidationRules.validate_summary_slide(slide_content, slide_num))
        
        # Performance slides (heuristic detection)
        text_lower = slide_content.get('text', '').lower()
        if 'performance' in text_lower or any(
            word in text_lower for word in ['return', 'rendement', 'ytd', 'annualized']
        ):
            errors.extend(
                SlideValidationRules.validate_performance_slide(
                    slide_content, slide_num, metadata
                )
            )
        
        # General content validation
        else:
            text = slide_content.get('text', '')
            if len(text) < SlideValidationRules.MIN_TEXT_LENGTH_CONTENT:
                errors.append(
                    f"Slide {slide_num} too short ({len(text)} chars). "
                    f"May be missing content."
                )
        
        return errors

