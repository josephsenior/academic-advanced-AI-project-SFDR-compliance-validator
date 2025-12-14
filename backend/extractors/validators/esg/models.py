"""
ESG Compliance Agent Models

Pydantic models for ESG compliance validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime


class ESGLevel(BaseModel):
    level: Literal["engaging", "reduced", "limited", "none"]
    exclusion_percentage: Optional[float] = None
    portfolio_coverage: Optional[float] = None
    sfdr_article: Optional[Literal[6, 8, 9]] = None
    description: str


class ESGMentions(BaseModel):
    total_text_length: int
    esg_text_length: int
    esg_percentage: float
    esg_keywords_found: List[str]
    esg_keywords_by_slide: Dict[str, List[int]] = {}  # keyword -> [slide numbers]
    esg_sentences: List[str]
    mandatory_regulatory_mentions: int
    commercial_esg_mentions: int


class ImageAnalysisResult(BaseModel):
    image_path: str
    slide_number: int
    slide_title: str
    extracted_text_ocr: str
    llm_visual_description: str
    title_image_coherence: str
    esg_keywords_in_image: List[str]
    compliance_issues: List[str]


class ESGViolation(BaseModel):
    violation_type: str
    severity: Literal["critical", "high", "medium", "low"]
    description: str
    location: Optional[str] = None
    recommendation: str


class ESGComplianceOutput(BaseModel):
    document_id: str
    file_name: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    fund_name: str
    client_type: Literal["retail", "professional"]
    document_type: str
    esg_level: ESGLevel
    esg_mentions: ESGMentions
    is_compliant: bool
    violations: List[ESGViolation] = []
    overall_confidence: float
    requires_human_review: bool
    image_analysis_results: List[ImageAnalysisResult] = []

