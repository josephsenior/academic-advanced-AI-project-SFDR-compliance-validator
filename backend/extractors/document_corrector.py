"""
Document Corrector

Applies validation fixes to documents based on validation results.
Currently supports PowerPoint (.pptx) format.

Auto-fixes:
- Missing source/date on tables/charts
- Missing disclaimers (when enabled)

Flags for manual review:
- Numerical inconsistencies
- Cross-reference mismatches
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from pptx.presentation import Presentation as PresentationType
else:
    PresentationType = Any

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
    Presentation = None

from .agents.data_consistency_agent import DataConsistencyResult


class CorrectionResult:
    """Result of document correction operation"""
    
    def __init__(self):
        self.corrected_path: Optional[str] = None
        self.fixes_applied: List[Dict[str, Any]] = []
        self.fixes_failed: List[Dict[str, Any]] = []
        self.manual_review_required: List[Dict[str, Any]] = []
        self.success: bool = False
        self.error_message: Optional[str] = None
        # Visual change tracking
        self.changes_by_slide: Dict[int, List[Dict[str, Any]]] = {}


class DocumentCorrector:
    """
    Apply validation fixes to documents.
    
    Currently supports:
    - PowerPoint (.pptx): Source/date fixes, disclaimer fixes
    """
    
    def __init__(self):
        self.supported_formats = {
            '.pptx': self._correct_pptx,
        }
        self._current_prs = None  # Store current presentation for slide dimension access
        
        if not PPTX_AVAILABLE:
            raise ImportError("python-pptx not installed. Install with: pip install python-pptx")
    
    def correct(
        self,
        original_path: str,
        validation_result: DataConsistencyResult,
        disclaimer_result: Optional[Any] = None,
        output_path: Optional[str] = None,
        auto_fix_disclaimers: bool = False
    ) -> CorrectionResult:
        """
        Apply fixes to document and save corrected version.
        
        Args:
            original_path: Path to original document
            validation_result: DataConsistencyResult from validation
            disclaimer_result: Optional disclaimer validation result
            output_path: Path for corrected document (default: adds _corrected suffix)
            auto_fix_disclaimers: Whether to auto-fix missing disclaimers
            
        Returns:
            CorrectionResult with details of fixes applied
        """
        result = CorrectionResult()
        input_path_obj = Path(original_path)
        
        if not input_path_obj.exists():
            result.error_message = f"File not found: {input_path_obj}"
            return result
        
        # Determine output path
        if output_path is None:
            stem = input_path_obj.stem
            suffix = input_path_obj.suffix
            output_path_obj = input_path_obj.parent / f"{stem}_corrected{suffix}"
        else:
            output_path_obj = Path(output_path)
        
        # Get file extension
        file_ext = input_path_obj.suffix.lower()
        
        if file_ext not in self.supported_formats:
            result.error_message = f"Unsupported format: {file_ext}. Supported: {list(self.supported_formats.keys())}"
            return result
        
        try:
            # Call appropriate corrector
            corrector_func = self.supported_formats[file_ext]
            corrector_func(input_path_obj, output_path_obj, validation_result, disclaimer_result, result, auto_fix_disclaimers)
            
            result.corrected_path = str(output_path_obj)
            result.success = True
            
        except Exception as e:
            result.error_message = f"Correction failed: {str(e)}"
            result.success = False
        
        return result
    
    def _correct_pptx(
        self,
        input_path: Path,
        output_path: Path,
        validation_result: DataConsistencyResult,
        disclaimer_result: Optional[Any],
        result: CorrectionResult,
        auto_fix_disclaimers: bool
    ) -> None:
        """Correct PowerPoint presentation"""
        
        # Load presentation
        prs = Presentation(str(input_path))
        
        # Store prs reference for slide dimension access
        self._current_prs = prs
        
        # Apply source/date fixes
        self._apply_source_date_fixes(prs, validation_result, result)
        
        # Apply disclaimer fixes if enabled
        if auto_fix_disclaimers and disclaimer_result:
            self._apply_disclaimer_fixes(prs, disclaimer_result, result)
        
        # Flag numerical issues for manual review
        self._flag_numerical_issues(validation_result, result)
        
        # Flag cross-reference issues for manual review
        self._flag_cross_reference_issues(validation_result, result)
        
        # Save corrected presentation
        output_path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(output_path))
        
        # Clean up
        self._current_prs = None
    
    def _apply_source_date_fixes(
        self,
        prs: PresentationType,
        validation_result: DataConsistencyResult,
        result: CorrectionResult
    ) -> None:
        """Apply source/date fixes to slides"""
        
        for issue in validation_result.source_date_issues:
            if issue.severity != "error":
                continue  # Only fix errors, not warnings
            
            slide_num = issue.slide_number
            if slide_num is None or slide_num < 1:
                result.fixes_failed.append({
                    "issue": issue.issue_type,
                    "location": issue.location,
                    "reason": "Invalid slide number"
                })
                continue
            
            try:
                # Get slide (0-indexed)
                if slide_num > len(prs.slides):
                    result.fixes_failed.append({
                        "issue": issue.issue_type,
                        "location": issue.location,
                        "reason": f"Slide {slide_num} does not exist (presentation has {len(prs.slides)} slides)"
                    })
                    continue
                
                slide = prs.slides[slide_num - 1]
                
                # Determine what needs to be added
                needs_source = issue.issue_type in ["missing_source", "both_missing"]
                needs_date = issue.issue_type in ["missing_date", "both_missing"]
                
                # Try to extract source/date from existing notes or use defaults
                source_text = "Source: [To be specified]"
                date_text = datetime.now().strftime("%Y-%m-%d")
                
                # Check if we can infer from other slides or use metadata
                # For now, use placeholder values
                
                # Add source/date note
                note_text = self._format_source_date_note(
                    source_text if needs_source else None,
                    date_text if needs_date else None
                )
                
                # Get position where note will be added (bottom of slide)
                if hasattr(self, '_current_prs') and self._current_prs:
                    slide_height = self._current_prs.slide_height
                else:
                    slide_height = Inches(7.5)
                
                note_y = float(slide_height - Inches(0.8)) / float(slide_height)
                
                self._add_note_to_slide(slide, note_text, issue.table_index)
                
                change_info = {
                    "type": "source_date",
                    "issue_type": issue.issue_type,
                    "location": issue.location,
                    "fix": f"Added source/date note: {note_text}",
                    "slide_number": slide_num,
                    "change_type": "added",
                    "position": {"x": 0.5, "y": note_y},
                    "description": f"Added source/date note at bottom of slide {slide_num}"
                }
                
                result.fixes_applied.append(change_info)
                
                # Track change by slide for visual annotation
                if slide_num not in result.changes_by_slide:
                    result.changes_by_slide[slide_num] = []
                result.changes_by_slide[slide_num].append(change_info)
                
            except Exception as e:
                result.fixes_failed.append({
                    "issue": issue.issue_type,
                    "location": issue.location,
                    "reason": str(e)
                })
    
    def _format_source_date_note(
        self,
        source: Optional[str],
        date: Optional[str]
    ) -> str:
        """Format source/date note text"""
        parts = []
        
        if source:
            if not source.startswith("Source:"):
                parts.append(f"Source: {source}")
            else:
                parts.append(source)
        
        if date:
            parts.append(f"Data as of {date}")
        
        return " | ".join(parts) if parts else "Source: [To be specified] | Data as of [To be specified]"
    
    def _add_note_to_slide(
        self,
        slide,
        note_text: str,
        table_index: Optional[int] = None
    ) -> None:
        """
        Add a source/date note to a slide.
        
        Strategy:
        - Add as text box at bottom of slide
        - Use small font, gray color
        - Position near bottom right
        """
        # Get slide dimensions from presentation if available
        if hasattr(self, '_current_prs') and self._current_prs:
            slide_width = self._current_prs.slide_width
            slide_height = self._current_prs.slide_height
        else:
            # Standard PowerPoint slide dimensions (10x7.5 inches)
            slide_width = Inches(10)
            slide_height = Inches(7.5)
        
        # Calculate position (bottom right area)
        left = Inches(0.5)
        top = slide_height - Inches(0.8)  # Near bottom
        width = slide_width - Inches(1.0)  # Most of slide width
        height = Inches(0.4)
        
        # Add text box
        textbox = slide.shapes.add_textbox(left, top, width, height)
        text_frame = textbox.text_frame
        text_frame.text = note_text
        text_frame.word_wrap = True
        
        # Format text
        paragraph = text_frame.paragraphs[0]
        paragraph.alignment = PP_ALIGN.LEFT
        paragraph.font.size = Pt(8)
        paragraph.font.color.rgb = RGBColor(128, 128, 128)  # Gray
        paragraph.font.name = "Calibri"
        
        # Make it non-selectable/editable (optional, for protection)
        # textbox.click_action = None
    
    def _apply_disclaimer_fixes(
        self,
        prs: PresentationType,
        disclaimer_result: Any,
        result: CorrectionResult
    ) -> None:
        """Apply disclaimer fixes to presentation"""
        
        # Check if disclaimer_result has missing disclaimers
        if not hasattr(disclaimer_result, 'missing_disclaimers'):
            return
        
        missing = disclaimer_result.missing_disclaimers
        if not missing:
            return
        
        # Add missing disclaimers to appropriate slide
        # Typically add to last slide or create new slide
        if len(prs.slides) > 0:
            # Add to last slide as footnote/note
            last_slide = prs.slides[-1]
            
            for disclaimer in missing:
                # MissingDisclaimer is a Pydantic model, access attributes directly
                disclaimer_text = self._format_disclaimer(disclaimer)
                self._add_disclaimer_to_slide(last_slide, disclaimer_text)
                
                result.fixes_applied.append({
                    "type": "disclaimer",
                    "disclaimer_type": disclaimer.disclaimer_type,
                    "fix": f"Added disclaimer: {disclaimer_text[:50]}..."
                })
    
    def _format_disclaimer(self, disclaimer: Any) -> str:
        """Format disclaimer text"""
        # MissingDisclaimer is a Pydantic model with attributes
        # Try to get expected_text first, then fall back to disclaimer_type
        if hasattr(disclaimer, 'expected_text') and disclaimer.expected_text:
            return disclaimer.expected_text
        elif hasattr(disclaimer, 'text') and disclaimer.text:
            return disclaimer.text
        else:
            # Fallback: create a placeholder based on disclaimer type
            disclaimer_type = getattr(disclaimer, 'disclaimer_type', 'Unknown')
            return f"[Disclaimer: {disclaimer_type}]"
    
    def _add_disclaimer_to_slide(self, slide, disclaimer_text: str) -> None:
        """Add disclaimer text to slide"""
        # Get slide dimensions from presentation if available
        if hasattr(self, '_current_prs') and self._current_prs:
            slide_width = self._current_prs.slide_width
            slide_height = self._current_prs.slide_height
        else:
            slide_width = Inches(10)
            slide_height = Inches(7.5)
        
        # Add as small text at bottom
        left = Inches(0.5)
        top = slide_height - Inches(0.5)
        width = slide_width - Inches(1.0)
        height = Inches(0.3)
        
        textbox = slide.shapes.add_textbox(left, top, width, height)
        text_frame = textbox.text_frame
        text_frame.text = disclaimer_text
        text_frame.word_wrap = True
        
        paragraph = text_frame.paragraphs[0]
        paragraph.font.size = Pt(7)
        paragraph.font.color.rgb = RGBColor(100, 100, 100)
        paragraph.font.italic = True
    
    def _flag_numerical_issues(
        self,
        validation_result: DataConsistencyResult,
        result: CorrectionResult
    ) -> None:
        """Flag numerical issues for manual review (don't auto-fix)"""
        
        for inc in validation_result.numerical_inconsistencies:
            result.manual_review_required.append({
                "type": "numerical_inconsistency",
                "location": inc.location,
                "issue": inc.message,
                "document_value": inc.document_value,
                "reference_value": inc.reference_value,
                "action": "Review and correct manually"
            })
    
    def _flag_cross_reference_issues(
        self,
        validation_result: DataConsistencyResult,
        result: CorrectionResult
    ) -> None:
        """Flag cross-reference issues for manual review (don't auto-fix)"""
        
        for issue in validation_result.cross_reference_issues:
            result.manual_review_required.append({
                "type": "cross_reference",
                "location": issue.location,
                "issue": issue.message,
                "value1": issue.value1,
                "value2": issue.value2,
                "action": "Review and correct manually"
            })

