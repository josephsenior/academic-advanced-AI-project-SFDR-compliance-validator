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
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pptx.presentation import Presentation as PresentationType
else:
    PresentationType = Any

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE_TYPE, MSO_SHAPE
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
        try:
            self._apply_source_date_fixes(prs, validation_result, result)
        except Exception as e:
            logger.error(f"Error in _apply_source_date_fixes: {e}", exc_info=True)
            result.fixes_failed.append({"issue": "all_source_date", "reason": f"Internal error: {str(e)}"})
        
        # Apply disclaimer fixes if enabled
        if auto_fix_disclaimers and disclaimer_result:
            try:
                self._apply_disclaimer_fixes(prs, disclaimer_result, result)
            except Exception as e:
                logger.error(f"Error in _apply_disclaimer_fixes: {e}", exc_info=True)
                result.fixes_failed.append({"issue": "all_disclaimers", "reason": f"Internal error: {str(e)}"})
        
        # Highlight all issues in the document
        try:
            self._highlight_issues(prs, validation_result, result)
        except Exception as e:
            logger.error(f"Error in _highlight_issues: {e}", exc_info=True)
            result.fixes_failed.append({"issue": "all_highlights", "reason": f"Internal error: {str(e)}"})

        # Flag numerical issues for manual review
        self._flag_numerical_issues(validation_result, result)
        
        # Flag cross-reference issues for manual review
        self._flag_cross_reference_issues(validation_result, result)
        
        # Save corrected presentation
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # EMERGENCY DEBUG LOG
            DEBUG_FILE = r"C:\Users\GIGABYTE\Desktop\Advanced Ai Project\debug_fix_abs.log"
            try:
                import os
                with open(DEBUG_FILE, "a") as f:
                    f.write(f"Saving to: {output_path}\n")
            except:
                pass
                
            logger.info(f"Saving corrected presentation to {output_path}")
            prs.save(str(output_path))
            
            # EMERGENCY DEBUG LOG
            DEBUG_FILE = r"C:\Users\GIGABYTE\Desktop\Advanced Ai Project\debug_fix_abs.log"
            try:
                import os
                with open(DEBUG_FILE, "a") as f:
                    f.write(f"Save successful. File exists: {os.path.exists(output_path)}\n")
            except:
                pass
                
            logger.info("Successfully saved corrected presentation")
        except Exception as e:
            # EMERGENCY DEBUG LOG
            DEBUG_FILE = r"C:\Users\GIGABYTE\Desktop\Advanced Ai Project\debug_fix_abs.log"
            try:
                with open(DEBUG_FILE, "a") as f:
                    f.write(f"SAVE FAILED: {str(e)}\n")
            except:
                pass
            logger.error(f"Failed to save corrected presentation: {e}", exc_info=True)
            raise e
        
        # Clean up
        self._current_prs = None

    def _get_issues_from_result(self, result: Any, field_name: str) -> List[Any]:
        """Helper to get issues from validation_result regardless of if it's a dict or model."""
        if isinstance(result, dict):
            # Sometimes nested in 'validation_result'
            inner = result.get("validation_result", result)
            
            # If the direct field exists, use it
            if field_name in inner and inner[field_name]:
                return inner[field_name]
                
            # Otherwise look in the categorized issues (common for formatted results)
            categorized = inner.get("issues_by_category", {})
            
            # Map legacy field names to category keys
            mapping = {
                "source_date_issues": "source_date",
                "numerical_inconsistencies": "numerical",
                "cross_reference_issues": "cross_reference",
                "compliance_issues": None # Already checked at top level
            }
            
            if field_name in mapping and mapping[field_name]:
                cat_key = mapping[field_name]
                return categorized.get(cat_key, [])
            
            # Final fallback: look for the field name directly in inner
            return inner.get(field_name, [])
            
        return getattr(result, field_name, [])

    def _get_val(self, obj: Any, field: str, default: Any = None) -> Any:
        """Helper to get value from object or dict."""
        if isinstance(obj, dict):
            return obj.get(field, default)
        return getattr(obj, field, default)
    
    def _apply_source_date_fixes(
        self,
        prs: PresentationType,
        validation_result: DataConsistencyResult,
        result: CorrectionResult
    ) -> None:
        """Apply source/date fixes to slides"""
        source_date_issues = self._get_issues_from_result(validation_result, "source_date_issues")
        logger.info(f"Found {len(source_date_issues)} source/date issues to fix")
        
        for issue in source_date_issues:
            severity = self._get_val(issue, "severity", "warning").lower()
            if severity not in ["error", "critical", "high", "warning"]:
                logger.info(f"Skipping source/date fix for severity: {severity}")
                continue  # Only fix higher severity issues
            
            slide_num = self._get_val(issue, "slide_number")
            location = self._get_val(issue, "location")
            issue_type = self._get_val(issue, "issue_type")
            
            if slide_num is None or slide_num < 1:
                result.fixes_failed.append({
                    "issue": issue_type,
                    "location": location,
                    "reason": "Invalid slide number"
                })
                continue
            
            try:
                # Get slide (0-indexed)
                if slide_num > len(prs.slides):
                    result.fixes_failed.append({
                        "issue": issue_type,
                        "location": location,
                        "reason": f"Slide {slide_num} does not exist (presentation has {len(prs.slides)} slides)"
                    })
                    continue
                
                slide = prs.slides[slide_num - 1]
                
                # Determine what needs to be added
                needs_source = issue_type in ["missing_source", "both_missing", "missing_source_date"]
                needs_date = issue_type in ["missing_date", "both_missing", "missing_source_date", "missing_date_info"]
                
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
                
                self._add_note_to_slide(slide, note_text, self._get_val(issue, "table_index"))
                
                change_info = {
                    "type": "source_date",
                    "issue_type": issue_type,
                    "location": location,
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
                    "issue": issue_type,
                    "location": location,
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
        paragraph.font.bold = True  # Make it bold as requested
        
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
                # Use _get_val to be safe for both models and dicts
                disclaimer_text = self._format_disclaimer(disclaimer)
                self._add_disclaimer_to_slide(last_slide, disclaimer_text)
                
                result.fixes_applied.append({
                    "type": "disclaimer",
                    "disclaimer_type": self._get_val(disclaimer, "disclaimer_type", "Unknown"),
                    "fix": f"Added disclaimer: {disclaimer_text[:50]}..."
                })
    
    def _format_disclaimer(self, disclaimer: Any) -> str:
        """Format disclaimer text"""
        # Use helper for dictionary safety
        expected = self._get_val(disclaimer, 'expected_text')
        text = self._get_val(disclaimer, 'text')
        
        if expected:
            return expected
        elif text:
            return text
        else:
            # Fallback: create a placeholder based on disclaimer type
            disclaimer_type = self._get_val(disclaimer, 'disclaimer_type', 'Unknown')
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
        numerical_inconsistencies = self._get_issues_from_result(validation_result, "numerical_inconsistencies")
        
        for inc in numerical_inconsistencies:
            result.manual_review_required.append({
                "type": "numerical_inconsistency",
                "location": self._get_val(inc, "location"),
                "issue": self._get_val(inc, "message"),
                "document_value": self._get_val(inc, "document_value"),
                "reference_value": self._get_val(inc, "reference_value"),
                "action": "Review and correct manually"
            })
    
    def _flag_cross_reference_issues(
        self,
        validation_result: DataConsistencyResult,
        result: CorrectionResult
    ) -> None:
        """Flag cross-reference issues for manual review (don't auto-fix)"""
        cross_reference_issues = self._get_issues_from_result(validation_result, "cross_reference_issues")
        
        for issue in cross_reference_issues:
            result.manual_review_required.append({
                "type": "cross_reference",
                "location": self._get_val(issue, "location"),
                "issue": self._get_val(issue, "message"),
                "value1": self._get_val(issue, "value1"),
                "value2": self._get_val(issue, "value2"),
                "action": "Review and correct manually"
            })

    def _highlight_issues(
        self,
        prs: PresentationType,
        validation_result: DataConsistencyResult,
        result: CorrectionResult
    ) -> None:
        """Add visual markers/notes for all issues to slides"""
        
        # Prefer unified compliance_issues if available, else use legacy fields
        all_issues = []
        compliance_issues = self._get_issues_from_result(validation_result, "compliance_issues")
        if compliance_issues:
            all_issues = compliance_issues
        else:
            # Aggregate from legacy fields
            all_issues.extend(self._get_issues_from_result(validation_result, "source_date_issues"))
            all_issues.extend(self._get_issues_from_result(validation_result, "numerical_inconsistencies"))
            all_issues.extend(self._get_issues_from_result(validation_result, "cross_reference_issues"))

        issues_by_slide: Dict[int, List[Any]] = {}
        for issue in all_issues:
            # Handle both Pydantic models and dicts
            issue_dict = issue if isinstance(issue, dict) else (issue.model_dump() if hasattr(issue, 'model_dump') else {})
            slide_num = issue_dict.get('slide_number')
            
            if slide_num and slide_num >= 1:
                if slide_num not in issues_by_slide:
                    issues_by_slide[slide_num] = []
                issues_by_slide[slide_num].append(issue_dict)

        for slide_num, issues in issues_by_slide.items():
            if slide_num > len(prs.slides):
                continue
            
            slide = prs.slides[slide_num - 1]
            
            # Add a banner or collective note at top of slide
            severity_colors = {
                "critical": RGBColor(255, 0, 0),    # Red
                "error": RGBColor(200, 0, 0),       # Dark Red
                "high": RGBColor(255, 100, 0),     # Orange
                "medium": RGBColor(200, 150, 0),   # Yellow/Gold
                "low": RGBColor(100, 100, 100)     # Gray
            }

            # Strategy: Add a small warning icon/text box at top right
            left = prs.slide_width - Inches(3.2)
            top = Inches(0.1)
            width = Inches(3.0)
            height = Inches(0.3) * len(issues)
            
            # Cap height
            height = min(height, Inches(2.0))
            
            textbox = slide.shapes.add_textbox(left, top, width, height)
            text_frame = textbox.text_frame
            text_frame.word_wrap = True
            
            p = text_frame.paragraphs[0]
            p.text = f"⚠️ {len(issues)} Issue(s) detected:"
            p.font.bold = True
            p.font.size = Pt(10)
            p.font.color.rgb = RGBColor(255, 0, 0)
            
            for i, issue in enumerate(issues[:5]): # Show max 5 in the banner
                severity = issue.get('severity', 'low').lower()
                msg = issue.get('message', issue.get('issue', 'Unknown issue'))
                
                # Truncate long messages
                if len(msg) > 60:
                    msg = msg[:57] + "..."
                
                p = text_frame.add_paragraph()
                p.text = f"• [{severity.upper()}] {msg}"
                p.font.size = Pt(8)
                p.font.color.rgb = severity_colors.get(severity, RGBColor(0, 0, 0))

            if len(issues) > 5:
                p = text_frame.add_paragraph()
                p.text = f"...and {len(issues) - 5} more issues. See report."
                p.font.size = Pt(8)
                p.font.italic = True

            # --- ELEMENT-LEVEL HIGHLIGHTING ---
            for issue in issues:
                target_shape = None
                
                # Try to find the specific table or chart
                if issue.get('table_index') is not None:
                    target_shape = self._find_shape_by_index(slide, MSO_SHAPE_TYPE.TABLE, issue.get('table_index'))
                elif issue.get('chart_index') is not None:
                    # Charts are often in GRAPHIC_FRAME (14)
                    target_shape = self._find_shape_by_index(slide, MSO_SHAPE_TYPE.CHART, issue.get('chart_index'))
                    if not target_shape:
                        GRAPHIC_FRAME = getattr(MSO_SHAPE_TYPE, 'GRAPHIC_FRAME', 14)
                        target_shape = self._find_shape_by_index(slide, GRAPHIC_FRAME, issue.get('chart_index'))
                
                if target_shape:
                    self._add_visual_highlight(slide, target_shape, issue)

    def _find_shape_by_index(self, slide: Any, shape_type: Any, index: int) -> Optional[Any]:
        """Find a shape of a specific type by its index on the slide."""
        count = 0
        for shape in slide.shapes:
            # For tables, check has_table attribute
            if shape_type == MSO_SHAPE_TYPE.TABLE and hasattr(shape, "has_table") and shape.has_table:
                if count == index:
                    return shape
                count += 1
            # For charts, check has_chart or shape_type
            elif shape_type in [MSO_SHAPE_TYPE.CHART, getattr(MSO_SHAPE_TYPE, 'GRAPHIC_FRAME', 14)]:
                if (hasattr(shape, "has_chart") and shape.has_chart) or shape.shape_type == MSO_SHAPE_TYPE.CHART:
                    if count == index:
                        return shape
                    count += 1
            elif shape.shape_type == shape_type:
                if count == index:
                    return shape
                count += 1
        return None

    def _add_visual_highlight(self, slide: Any, shape: Any, issue: Dict[str, Any]) -> None:
        """Add a red border around a shape and a green suggestion box nearby."""
        try:
            # 1. Add Red Border (Rectangle behind or around)
            # Shapes like Tables/Charts sometimes don't allow' line' property directly on the frame
            # We add a transparent rectangle with a red border exactly over the shape
            border = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                shape.left - Pt(2),
                shape.top - Pt(2),
                shape.width + Pt(4),
                shape.height + Pt(4)
            )
            border.fill.background() # Transparent fill
            border.line.color.rgb = RGBColor(255, 0, 0) # Red
            border.line.width = Pt(3)
            
            # 2. Add Green Suggestion Box
            suggestion = issue.get('suggestion', 'Review required')
            
            # Position box at the top right of the element
            box_width = min(shape.width, Inches(3))
            box_left = shape.left + shape.width - box_width
            box_top = shape.top - Inches(0.4) # Slightly above the shape
            
            # Ensure it doesn't go off-slide
            if box_top < Inches(0.1):
                box_top = shape.top + shape.height + Inches(0.1) # Move below instead
            
            callout = slide.shapes.add_textbox(box_left, box_top, box_width, Inches(0.4))
            callout.fill.solid()
            callout.fill.fore_color.rgb = RGBColor(220, 255, 220) # Very light green
            callout.line.color.rgb = RGBColor(0, 150, 0) # Dark green border
            callout.line.width = Pt(1)
            
            tf = callout.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = f"💡 Suggested: {suggestion}"
            p.font.size = Pt(9)
            p.font.color.rgb = RGBColor(0, 100, 0) # Dark green text
            p.font.bold = True
            
        except Exception as e:
            logger.warning(f"Failed to add visual highlight for issue: {e}")

