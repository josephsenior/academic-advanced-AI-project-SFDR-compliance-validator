"""
Chart and Graph Analyzer using LLM

Uses LLM (Llama) to analyze charts, graphs, and visualizations in documents.
Extracts numerical data, metadata, and validates chart content for data consistency.
"""

import base64
import os
import sys
# Apply Pydantic v1 patch for Python 3.12 compatibility
try:
    from src.utils import pydantic_v1_patch
except ImportError:
    # Fallback if running as script
    pass

from typing import Dict, List, Any, Optional
from io import BytesIO
from pydantic import BaseModel, Field

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    from langchain_core.prompts import ChatPromptTemplate
    try:
        from langchain.output_parsers import PydanticOutputParser
    except ImportError:
        from langchain_core.output_parsers import PydanticOutputParser
except ImportError:
    ChatOpenAI = None
    HumanMessage = None
    ChatPromptTemplate = None
    PydanticOutputParser = None

from .llm_config import get_vision_model_config

# Import performance utilities
try:
    from src.utils.llm_cache import get_llm_cache
    from src.utils.metrics import get_metrics_collector
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


class ChartDataPoint(BaseModel):
    """A single data point extracted from a chart"""
    label: str = Field(description="Label or category name")
    value: Optional[float] = Field(None, description="Numerical value")
    x_value: Optional[float] = Field(None, description="X-axis value if applicable")
    y_value: Optional[float] = Field(None, description="Y-axis value if applicable")
    series: Optional[str] = Field(None, description="Series name if multiple series")
    period: Optional[str] = Field(None, description="Time period if applicable (e.g., '1Y', '2024')")


class ChartMetadata(BaseModel):
    """Metadata extracted from a chart"""
    chart_type: str = Field(description="Type of chart: 'bar', 'line', 'pie', 'scatter', 'table', 'other'")
    title: Optional[str] = Field(None, description="Chart title")
    x_axis_label: Optional[str] = Field(None, description="X-axis label")
    y_axis_label: Optional[str] = Field(None, description="Y-axis label")
    has_source: bool = Field(default=False, description="Whether source is visible in chart")
    has_date: bool = Field(default=False, description="Whether date is visible in chart")
    source_text: Optional[str] = Field(None, description="Source text if visible")
    date_text: Optional[str] = Field(None, description="Date text if visible")
    units: Optional[str] = Field(None, description="Units (e.g., '%', 'EUR', 'USD')")
    currency: Optional[str] = Field(None, description="Currency if applicable")


class ChartAnalysis(BaseModel):
    """Complete analysis of a chart/graph"""
    is_chart: bool = Field(description="Whether this image is a chart/graph/visualization")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence that this is a chart (0-1)")
    metadata: Optional[ChartMetadata] = Field(None, description="Chart metadata")
    data_points: List[ChartDataPoint] = Field(default_factory=list, description="Extracted data points")
    performance_values: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Performance-related values extracted (period, value, basis)"
    )
    notes: Optional[str] = Field(None, description="Additional notes or observations")


class ChartAnalyzer:
    """
    Analyzes charts and graphs using LLM vision capabilities.
    
    Extracts:
    - Chart type and metadata
    - Numerical data points
    - Performance values
    - Source and date information
    """
    
    def __init__(self, use_llm: bool = True, enable_caching: bool = True, enable_metrics: bool = True):
        """
        Initialize Chart Analyzer.
        
        Args:
            use_llm: Whether to use LLM for analysis (default: True)
            enable_caching: Whether to enable LLM response caching (default: True)
            enable_metrics: Whether to enable metrics tracking (default: True)
        """
        self.use_llm = use_llm
        self.llm = None
        self.enable_caching = enable_caching and UTILS_AVAILABLE
        self.enable_metrics = enable_metrics and UTILS_AVAILABLE
        
        # Initialize cache and metrics
        self.cache = get_llm_cache() if self.enable_caching else None
        self.metrics = get_metrics_collector() if self.enable_metrics else None
        
        if use_llm:
            try:
                # Use LLaVA vision model for chart/image analysis
                config = get_vision_model_config()
                # Disable SSL verification for self-signed certificates
                import httpx
                http_client = httpx.Client(verify=False)
                http_async_client = httpx.AsyncClient(verify=False)
                
                self.llm = ChatOpenAI(
                    model=config.get("model_name", "hosted_vllm/llava-1.5-7b-hf"),
                    temperature=0.0,
                    api_key=config.get("api_key"),
                    base_url=config.get("base_url")
                )
                # Manually set clients to bypass validation issues in langchain-openai 0.0.2
                # self.llm.http_client = http_client
                # self.llm.http_async_client = http_async_client
            except Exception as e:
                print(f"Warning: Could not initialize LLM for chart analysis: {e}")
                print("Chart analysis will be limited to basic detection")
                self.use_llm = False
    
    def analyze_chart_image(
        self,
        image_bytes: bytes,
        location: Optional[Dict[str, Any]] = None
    ) -> ChartAnalysis:
        """
        Analyze a chart/graph image using LLM.
        
        Args:
            image_bytes: Image bytes (PNG, JPEG, etc.)
            location: Optional location info (slide_number, page_number, etc.)
            
        Returns:
            ChartAnalysis with extracted data
        """
        if not self.use_llm or not self.llm:
            # Fallback: basic detection
            return ChartAnalysis(
                is_chart=False,
                confidence=0.0,
                notes="LLM not available for chart analysis"
            )
        
        if Image is None:
            return ChartAnalysis(
                is_chart=False,
                confidence=0.0,
                notes="PIL not available for image processing"
            )
        
        try:
            # Convert image to base64 for LLM
            image = Image.open(BytesIO(image_bytes))
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Create prompt for chart analysis
            prompt = self._create_chart_analysis_prompt()
            
            # Check cache first
            cache_key = None
            if self.cache:
                import hashlib
                cache_key = hashlib.sha256(image_bytes).hexdigest()
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    if self.metrics:
                        self.metrics.log_api_usage(
                            api_name="chart_analyzer",
                            tokens_used=0,
                            cost=0.0,
                            cached=True
                        )
                    return cached_result
            
            # Prepare message with image
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}"
                        }
                    }
                ]
            )
            
            # Get response from LLM
            import time
            start_time = time.time()
            response = self.llm.invoke([message])
            duration_ms = (time.time() - start_time) * 1000
            
            # Parse response - LLaVA may return text, so we extract JSON from it
            # Try direct parsing first, then extract JSON from text
            analysis = None
            try:
                # First try: direct JSON parsing (if response is pure JSON)
                parser = PydanticOutputParser(pydantic_object=ChartAnalysis)
                analysis = parser.parse(response.content)
            except Exception:
                # Second try: extract JSON from text response (LLaVA often wraps JSON in text)
                analysis = self._parse_text_response(response.content)
            
            # Cache the result
            if self.cache and cache_key and analysis:
                self.cache.set(cache_key, analysis)
            
            # Log metrics
            if self.metrics:
                # Estimate tokens (rough approximation for vision models)
                estimated_tokens = len(prompt) // 4 + 1000  # prompt tokens + image tokens estimate
                estimated_cost = estimated_tokens * 0.00001  # rough estimate
                self.metrics.log_api_usage(
                    api_name="chart_analyzer",
                    tokens_used=estimated_tokens,
                    cost=estimated_cost,
                    cached=False,
                    duration_ms=duration_ms
                )
            
            return analysis
            
        except Exception as e:
            return ChartAnalysis(
                is_chart=False,
                confidence=0.0,
                notes=f"Error analyzing chart: {str(e)}"
            )
    
    def _create_chart_analysis_prompt(self) -> str:
        """Create prompt for chart analysis - optimized for LLaVA structured output"""
        return """You are a financial document compliance expert analyzing charts and graphs.

**TASK**: Analyze this image and return ONLY valid JSON. No explanations, no markdown, just pure JSON.

**STEP 1: Determine if this is a chart/graph**
- If it's a bar chart, line chart, pie chart, scatter plot, table, or any data visualization → is_chart=true
- If it's a logo, photo, text block, or non-chart image → is_chart=false

**STEP 2: If is_chart=true, extract the following:**

1. **Chart Type**: One of: "bar", "line", "pie", "scatter", "table", "area", "other"

2. **Chart Metadata**:
   - title: Extract the main title (if visible)
   - x_axis_label: Extract X-axis label text
   - y_axis_label: Extract Y-axis label text
   - units: Extract units (%, EUR, USD, etc.) if visible
   - currency: Extract currency if mentioned

3. **Source and Date** (CRITICAL for compliance):
   - Look for text like "Source: Bloomberg", "Source: ...", "As of ...", "Date: ..."
   - has_source: true if source text is visible, false otherwise
   - has_date: true if date text is visible, false otherwise
   - source_text: The exact source text if visible (e.g., "Bloomberg", "Source: Bloomberg 31/08/2025")
   - date_text: The exact date text if visible (e.g., "31/08/2025", "As of August 2025")

4. **Data Points**: Extract ALL numerical values with their labels
   - For each bar/point/slice, extract: label, value, series (if multiple series)
   - Example: If bar chart shows "Fund: 10%", extract label="Fund", value=10.0

5. **Performance Values**: If this shows performance data (returns, percentages with time periods)
   - Extract period: "1Y", "3Y", "5Y", "YTD", "Since inception", etc.
   - Extract value: The percentage number
   - Extract basis: "net", "gross", "backtest", "simulation", or null

**OUTPUT FORMAT - Return ONLY this JSON structure (no markdown, no code blocks):**

{
  "is_chart": true,
  "confidence": 0.9,
  "metadata": {
    "chart_type": "bar",
    "title": "Performance Comparison",
    "x_axis_label": "Period",
    "y_axis_label": "Return %",
    "has_source": true,
    "has_date": true,
    "source_text": "Source: Bloomberg",
    "date_text": "31/08/2025",
    "units": "%",
    "currency": null
  },
  "data_points": [
    {"label": "Fund", "value": 10.5, "period": "1Y", "series": null},
    {"label": "Benchmark", "value": 8.0, "period": "1Y", "series": null}
  ],
  "performance_values": [
    {"period": "1Y", "value": 10.5, "basis": "net"}
  ],
  "notes": null
}

**IMPORTANT RULES:**
- Return ONLY valid JSON, no markdown code blocks, no explanations
- Use null (not "null" string) for missing values
- Extract ALL visible numbers and labels
- If source/date text is visible, extract it exactly as shown
- confidence: 0.0-1.0 based on how clear the chart is (1.0 = very clear, 0.5 = somewhat clear, 0.0 = not a chart)
- If is_chart=false, set confidence=0.0 and return minimal structure

**NOW ANALYZE THE IMAGE AND RETURN ONLY THE JSON:**"""
    
    def _parse_text_response(self, text: str) -> ChartAnalysis:
        """Parse text response from LLM - extracts JSON from various formats"""
        import json
        import re
        
        # Clean the text - remove common prefixes/suffixes
        text = text.strip()
        
        # Try multiple patterns to extract JSON
        json_patterns = [
            # Pattern 1: Markdown JSON code block
            r'```json\s*(\{.*?\})\s*```',
            # Pattern 2: Generic code block
            r'```\s*(\{.*?\})\s*```',
            # Pattern 3: JSON object at start of text
            r'^(\{.*\})',
            # Pattern 4: JSON object anywhere (greedy, but balanced)
            r'(\{(?:[^{}]|(?:\{[^{}]*\}))*\})',
        ]
        
        for pattern in json_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.MULTILINE)
            for match in matches:
                try:
                    json_str = match.group(1).strip()
                    # Fix common issues: escaped underscores, escaped quotes
                    json_str = json_str.replace('\\_', '_')  # Fix escaped underscores
                    json_str = json_str.replace('\\"', '"')  # Fix escaped quotes if needed
                    # Try to parse
                    data = json.loads(json_str)
                    
                    # Validate required fields
                    if 'is_chart' in data:
                        # Convert null strings to None
                        def clean_nulls(obj):
                            if isinstance(obj, dict):
                                return {k: clean_nulls(v) for k, v in obj.items()}
                            elif isinstance(obj, list):
                                return [clean_nulls(item) for item in obj]
                            elif obj == "null" or obj == "None":
                                return None
                            return obj
                        
                        data = clean_nulls(data)
                        
                        # Create ChartAnalysis with validation
                        try:
                            return ChartAnalysis(**data)
                        except Exception as e:
                            # If validation fails, try to fix common issues
                            # Ensure metadata is dict if present
                            if 'metadata' in data and not isinstance(data['metadata'], dict):
                                data['metadata'] = {}
                            # Ensure lists are lists
                            if 'data_points' in data and not isinstance(data['data_points'], list):
                                data['data_points'] = []
                            if 'performance_values' in data and not isinstance(data['performance_values'], list):
                                data['performance_values'] = []
                            
                            try:
                                return ChartAnalysis(**data)
                            except Exception:
                                continue
                except (json.JSONDecodeError, TypeError, ValueError, KeyError) as e:
                    continue
        
        # If no valid JSON found, try to extract information from text
        return self._extract_info_from_text(text)
    
    def _extract_info_from_text(self, text: str) -> ChartAnalysis:
        """Extract chart information from unstructured text response"""
        import re
        
        text_lower = text.lower()
        
        # Determine if it's a chart
        chart_keywords = [
            "bar chart", "line chart", "pie chart", "scatter", "graph", 
            "chart", "visualization", "data visualization", "plot"
        ]
        is_chart = any(keyword in text_lower for keyword in chart_keywords)
        
        # Extract chart type
        chart_type = "other"
        if "bar" in text_lower:
            chart_type = "bar"
        elif "line" in text_lower:
            chart_type = "line"
        elif "pie" in text_lower:
            chart_type = "pie"
        elif "scatter" in text_lower:
            chart_type = "scatter"
        elif "table" in text_lower:
            chart_type = "table"
        
        # Extract source/date information
        has_source = "source" in text_lower
        has_date = any(keyword in text_lower for keyword in ["date", "as of", "as at"])
        
        source_text = None
        date_text = None
        if has_source:
            source_match = re.search(r'source[:\s]+([^,\n]+)', text, re.IGNORECASE)
            if source_match:
                source_text = source_match.group(1).strip()
        if has_date:
            date_match = re.search(r'(?:date|as of|as at)[:\s]+([^,\n]+)', text, re.IGNORECASE)
            if date_match:
                date_text = date_match.group(1).strip()
        
        # Extract performance values (percentages with periods)
        performance_values = []
        # Look for patterns like "10.5%", "1Y: 10%", etc.
        percent_pattern = r'(\d+\.?\d*)\s*%'
        period_pattern = r'(1y|3y|5y|ytd|year to date|since inception)'
        
        # Try to find performance mentions
        if "%" in text:
            percents = re.findall(percent_pattern, text)
            periods = re.findall(period_pattern, text_lower)
            
            for i, percent in enumerate(percents[:5]):  # Limit to first 5
                try:
                    value = float(percent)
                    period = periods[i] if i < len(periods) else None
                    if period:
                        performance_values.append({
                            "period": period,
                            "value": value,
                            "basis": None
                        })
                except ValueError:
                    continue
        
        # Extract data points (try to find label: value patterns)
        data_points = []
        # Look for patterns like "Fund: 10%", "Benchmark: 8%"
        label_value_pattern = r'([A-Za-z\s]+)[:\s]+(\d+\.?\d*)\s*%'
        matches = re.finditer(label_value_pattern, text, re.IGNORECASE)
        for match in matches:
            label = match.group(1).strip()
            value_str = match.group(2)
            try:
                value = float(value_str)
                data_points.append({
                    "label": label,
                    "value": value,
                    "period": None,
                    "series": None
                })
            except ValueError:
                continue
        
        # Build metadata
        metadata = None
        if is_chart:
            metadata = ChartMetadata(
                chart_type=chart_type,
                title=None,
                x_axis_label=None,
                y_axis_label=None,
                has_source=has_source,
                has_date=has_date,
                source_text=source_text,
                date_text=date_text,
                units="%" if "%" in text else None,
                currency=None
            )
        
        confidence = 0.7 if is_chart and (data_points or performance_values) else (0.5 if is_chart else 0.0)
        
        return ChartAnalysis(
            is_chart=is_chart,
            confidence=confidence,
            metadata=metadata,
            data_points=[ChartDataPoint(**dp) for dp in data_points] if data_points else [],
            performance_values=performance_values,
            notes=f"Extracted from unstructured text: {text[:150]}"
        )
    
    def extract_chart_data_from_image(
        self,
        image_bytes: bytes,
        location: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract chart data and return in format compatible with extraction pipeline.
        
        Returns:
            Dict with:
            - is_chart: bool
            - chart_metadata: dict
            - data_points: list
            - performance_values: list (compatible with performance_sections format)
            - source_date_info: dict
        """
        analysis = self.analyze_chart_image(image_bytes, location)
        
        if not analysis.is_chart:
            return {
                'is_chart': False,
                'confidence': analysis.confidence
            }
        
        # Convert to extraction pipeline format
        performance_values = []
        for perf in analysis.performance_values:
            if isinstance(perf, dict):
                performance_values.append(perf)
        
        # Also extract from data_points if they look like performance data
        for point in analysis.data_points:
            if point.value is not None and point.period:
                performance_values.append({
                    'value': point.value,
                    'period': point.period,
                    'basis': None,  # Could be inferred from label
                    'sentence': f"{point.label}: {point.value}% ({point.period})"
                })
        
        source_date_info = {}
        if analysis.metadata:
            source_date_info = {
                'has_source': analysis.metadata.has_source,
                'has_date': analysis.metadata.has_date,
                'source_text': analysis.metadata.source_text,
                'date_text': analysis.metadata.date_text
            }
        
        return {
            'is_chart': True,
            'confidence': analysis.confidence,
            'chart_type': analysis.metadata.chart_type if analysis.metadata else None,
            'chart_title': analysis.metadata.title if analysis.metadata else None,
            'data_points': [
                {
                    'label': point.label,
                    'value': point.value,
                    'period': point.period,
                    'series': point.series
                }
                for point in analysis.data_points
            ],
            'performance_values': performance_values,
            'source_date_info': source_date_info,
            'metadata': analysis.metadata.model_dump() if analysis.metadata else None,
            'notes': analysis.notes
        }


def analyze_chart(image_bytes: bytes, location: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze a chart image.
    
    Args:
        image_bytes: Image bytes
        location: Optional location info
        
    Returns:
        Chart analysis results
    """
    analyzer = ChartAnalyzer(use_llm=True)
    return analyzer.extract_chart_data_from_image(image_bytes, location)

