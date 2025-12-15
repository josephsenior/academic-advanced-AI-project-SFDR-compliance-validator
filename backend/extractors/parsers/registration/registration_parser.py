"""
Registration Parser

Main class for parsing and validating fund registrations.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

from .models import FundRegistration, CountryMention
from .file_utils import find_latest_registration_file
from .parser import load_registrations
from .detector import detect_country_mentions
from .validator import (
    is_registered,
    get_registered_countries,
    validate_country_mentions,
    validate_temporal,
    validate_document,
)


class RegistrationParser:
    """
    Enhanced Registration Parser with context awareness and temporal validation.
    
    Features:
    - Auto-discovers latest registration file
    - Context-aware country detection (distribution vs. reference)
    - Temporal validation (registration dates/expiry)
    - Expanded country coverage (60+ countries)
    - Word boundary matching to avoid false positives
    """
    
    def __init__(
        self,
        registration_file_path: Optional[str] = None,
        dataset_dir: str = "dataset",
        enable_context_awareness: bool = True,
        enable_temporal_validation: bool = True
    ):
        """
        Initialize enhanced registration parser.
        
        Args:
            registration_file_path: Explicit path to registration Excel file (optional)
            dataset_dir: Directory to search for registration files
            enable_context_awareness: Enable distribution vs. reference distinction
            enable_temporal_validation: Enable date-based validation
        """
        self.enable_context_awareness = enable_context_awareness
        self.enable_temporal_validation = enable_temporal_validation
        self.dataset_dir = Path(dataset_dir)
        
        # Auto-discover latest registration file if not specified
        if registration_file_path:
            self.registration_path = Path(registration_file_path)
        else:
            self.registration_path = find_latest_registration_file(self.dataset_dir)
        
        self.registrations: Dict[str, FundRegistration] = {}
        self.file_version: Optional[str] = None
        self.file_date: Optional[datetime] = None
        
        self._load_registrations()
    
    def _load_registrations(self) -> None:
        """Load fund registrations from Excel file."""
        self.file_version, self.file_date = load_registrations(
            self.registration_path,
            self.registrations,
            self.file_version,
            self.file_date
        )
    
    def detect_country_mentions(
        self,
        text: str,
        context_window: int = 100
    ) -> List[CountryMention]:
        """
        Detect all country mentions in text with context awareness.
        
        Args:
            text: Text to analyze
            context_window: Characters to capture around each match for context
            
        Returns:
            List of CountryMention objects with context and classification
        """
        return detect_country_mentions(
            text,
            context_window,
            self.enable_context_awareness
        )
    
    def is_registered(
        self,
        fund_name: str,
        country: str,
        share_class: Optional[str] = None,
        isin: Optional[str] = None
    ) -> bool:
        """
        Check if a fund is registered in a specific country.
        
        Args:
            fund_name: Name of the fund
            country: Country name to check
            share_class: Optional share class identifier
            isin: Optional ISIN code
        
        Returns:
            True if registered, False otherwise
        """
        return is_registered(
            fund_name,
            country,
            self.registrations,
            share_class,
            isin
        )
    
    def get_registered_countries(
        self,
        fund_name: str,
        share_class: Optional[str] = None,
        isin: Optional[str] = None
    ) -> Set[str]:
        """
        Get all countries where a fund is registered.
        
        Args:
            fund_name: Name of the fund
            share_class: Optional share class identifier
            isin: Optional ISIN code
        
        Returns:
            Set of registered country names
        """
        return get_registered_countries(
            fund_name,
            self.registrations,
            share_class,
            isin
        )
    
    def validate_country_mentions(
        self,
        mentioned_countries: List[str],
        fund_name: str,
        share_class: Optional[str] = None,
        isin: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Validate that mentioned countries are registered.
        
        Args:
            mentioned_countries: List of country names mentioned in document
            fund_name: Name of the fund
            share_class: Optional share class identifier
            isin: Optional ISIN code
        
        Returns:
            Dictionary mapping country names to registration status (True/False)
        """
        return validate_country_mentions(
            mentioned_countries,
            fund_name,
            self.registrations,
            share_class,
            isin
        )
    
    def validate_temporal(
        self,
        fund_name: str,
        country: str,
        validation_date: Optional[datetime] = None
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Validate registration temporal constraints.
        
        Args:
            fund_name: Fund name to check
            country: Country to validate
            validation_date: Date to validate against (defaults to today)
            
        Returns:
            Tuple of (is_valid, severity, message)
        """
        return validate_temporal(
            fund_name,
            country,
            self.registrations,
            validation_date,
            self.enable_temporal_validation
        )
    
    def validate_document(
        self,
        document_text: str,
        fund_name: str,
        share_class: Optional[str] = None,
        isin: Optional[str] = None,
        document_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive document validation with context awareness and temporal checks.
        
        Args:
            document_text: Full document text to analyze
            fund_name: Fund name
            share_class: Optional share class
            isin: Optional ISIN
            document_date: Document date for temporal validation
            
        Returns:
            Dictionary with validation results, issues, and recommendations
        """
        return validate_document(
            document_text,
            fund_name,
            self.registrations,
            share_class,
            isin,
            document_date,
            self.enable_context_awareness,
            self.enable_temporal_validation
        )
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded registration file.
        
        Returns:
            Dictionary with file information
        """
        return {
            "file_path": str(self.registration_path),
            "file_version": self.file_version,
            "file_date": self.file_date.isoformat() if self.file_date else None,
            "total_funds": len(self.registrations),
            "total_registrations": sum(len(reg.registered_countries) for reg in self.registrations.values()),
            "countries_covered": len(set(
                country for reg in self.registrations.values()
                for country in reg.registered_countries
            )),
            # Backwards-compatible flags expected by older callers/tests
            "context_awareness_enabled": bool(self.enable_context_awareness),
            "temporal_validation_enabled": bool(self.enable_temporal_validation),
        }

    # Backwards-compatible helper to extract file version from filename
    def _extract_file_version(self) -> tuple[Optional[str], Optional[datetime]]:
        # reuse file_utils.extract_file_version logic
        try:
            from .file_utils import extract_file_version
            return extract_file_version(self.registration_path)
        except Exception:
            return (self.file_version, self.file_date)

