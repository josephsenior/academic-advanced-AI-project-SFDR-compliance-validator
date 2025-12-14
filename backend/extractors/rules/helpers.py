"""
Compliance Rules Helper Functions

Utility functions for compliance validation.
"""

from .disclaimer import DisclaimerRules
from .constants import RETAIL_SHARE_CLASSES


def get_performance_disclaimer(language: str = "en") -> str:
    """Get the mandatory performance disclaimer in specified language"""
    disclaimers = {
        "fr": DisclaimerRules.PAST_PERFORMANCE_DISCLAIMER_FR,
        "en": DisclaimerRules.PAST_PERFORMANCE_DISCLAIMER_EN,
        "de": DisclaimerRules.PAST_PERFORMANCE_DISCLAIMER_DE
    }
    return disclaimers.get(language.lower(), disclaimers["en"])


def get_backtest_disclaimer(language: str = "en") -> str:
    """Get the backtest disclaimer in specified language"""
    disclaimers = {
        "fr": DisclaimerRules.BACKTEST_DISCLAIMER_FR,
        "en": DisclaimerRules.BACKTEST_DISCLAIMER_EN
    }
    return disclaimers.get(language.lower(), disclaimers["en"])


def get_simulation_disclaimer(language: str = "en", multiple_scenarios: bool = False) -> str:
    """Get the simulation disclaimer in specified language"""
    base = {
        "fr": DisclaimerRules.FUTURE_SIMULATION_DISCLAIMER_FR,
        "en": DisclaimerRules.FUTURE_SIMULATION_DISCLAIMER_EN
    }
    scenarios = {
        "fr": DisclaimerRules.MULTIPLE_SCENARIOS_DISCLAIMER_FR,
        "en": DisclaimerRules.MULTIPLE_SCENARIOS_DISCLAIMER_EN
    }
    
    disclaimer = base.get(language.lower(), base["en"])
    if multiple_scenarios:
        disclaimer += "\n" + scenarios.get(language.lower(), scenarios["en"])
    return disclaimer


def is_retail_share_class(share_class: str) -> bool:
    """Check if a share class is a retail share class"""
    return share_class.upper() in RETAIL_SHARE_CLASSES


def detect_language(text: str) -> str:
    """Simple language detection based on common words"""
    text_lower = text.lower()
    
    # French indicators
    fr_words = ["le", "la", "les", "de", "du", "des", "fonds", "gestion", "risque", "investissement"]
    fr_count = sum(1 for w in fr_words if f" {w} " in f" {text_lower} ")
    
    # German indicators
    de_words = ["der", "die", "das", "und", "ist", "fonds", "anlage", "risiko"]
    de_count = sum(1 for w in de_words if f" {w} " in f" {text_lower} ")
    
    # English indicators
    en_words = ["the", "and", "is", "fund", "investment", "risk", "performance"]
    en_count = sum(1 for w in en_words if f" {w} " in f" {text_lower} ")
    
    if fr_count > de_count and fr_count > en_count:
        return "fr"
    elif de_count > en_count:
        return "de"
    else:
        return "en"

