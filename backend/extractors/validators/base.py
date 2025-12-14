"""
Base Validator
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from backend.extractors.rules.models import ComplianceIssue

class BaseValidator(ABC):
    """Abstract base class for all validators."""
    
    @abstractmethod
    def validate(
        self,
        extraction_result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        client_type: Optional[Any] = None,
        fund_type: Optional[Any] = None
    ) -> List[ComplianceIssue]:
        """Validate rules and return actionable issues."""
        pass
