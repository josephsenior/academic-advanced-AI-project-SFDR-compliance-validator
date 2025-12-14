from typing import Optional, Dict
from pydantic import BaseModel, Field

class ReferenceData(BaseModel):
    """Reference data from official documents (Prospectus, KID, SFDR)"""
    fund_name: Optional[str] = None
    isin: Optional[str] = None
    
    # Performance data by period and basis
    performance_data: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Nested dict: {period: {basis: value}}, e.g., {'1Y': {'net': 10.5}}"
    )
    
    # Table data (keyed by label/description)
    table_data: Dict[str, float] = Field(
        default_factory=dict,
        description="Key-value pairs of table entries from reference documents"
    )
    
    # Metadata
    reference_date: Optional[str] = None
    source_document: Optional[str] = Field(None, description="e.g., 'Prospectus', 'KID', 'SFDR Annex'")

def create_reference_data_from_dict(data: Dict) -> ReferenceData:
    """Helper to create ReferenceData from dictionary"""
    return ReferenceData(**data)
