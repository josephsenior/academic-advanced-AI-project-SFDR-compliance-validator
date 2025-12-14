"""
ESG Compliance Agent Utilities

Utility functions for ESG compliance validation.
"""

import logging
from pathlib import Path
import fitz

logger = logging.getLogger(__name__)


def normalize_esg_level(raw: dict) -> dict:
    """Normalise le niveau ESG retourné par le LLM avant Pydantic."""
    level = str(raw.get("level", "")).strip().lower()
    
    mapping = {
        "article 6": "none",
        "article 8": "reduced",
        "article 9": "engaging",
        "6": "none",
        "8": "reduced",
        "9": "engaging",
    }
    
    if level in mapping:
        raw["level"] = mapping[level]
    elif level not in ["engaging", "reduced", "limited", "none"]:
        art = raw.get("sfdr_article")
        if art == 6:
            raw["level"] = "none"
        elif art == 8:
            raw["level"] = "reduced"
        elif art == 9:
            raw["level"] = "engaging"
        else:
            raw["level"] = "none"
    
    if "sfdr_article" in raw and raw["sfdr_article"]:
        try:
            raw["sfdr_article"] = int(raw["sfdr_article"])
        except (ValueError, TypeError):
            raw["sfdr_article"] = None
    
    if "exclusion_percentage" in raw and raw["exclusion_percentage"]:
        try:
            raw["exclusion_percentage"] = float(raw["exclusion_percentage"])
        except (ValueError, TypeError):
            raw["exclusion_percentage"] = None
    
    if "portfolio_coverage" in raw and raw["portfolio_coverage"]:
        try:
            raw["portfolio_coverage"] = float(raw["portfolio_coverage"])
        except (ValueError, TypeError):
            raw["portfolio_coverage"] = None
    
    return raw


def extract_fund_metadata_from_prospectus(prospectus_path: str) -> dict:
    """Extrait le nom du fonds et l'article SFDR du prospectus."""
    prospectus_path = Path(prospectus_path)
    if not prospectus_path.exists():
        logger.warning(f"Prospectus introuvable: {prospectus_path}")
        return {"fund_name": "Unknown Fund", "sfdr_article": None}
    
    try:
        doc = fitz.open(str(prospectus_path))
        full_text = "\n".join([page.get_text("text") for page in doc])
        doc.close()
        
        import re
        # Extract fund name (simplified - could be enhanced)
        fund_name_match = re.search(r"Fonds?\s+([A-Z][A-Za-z0-9\s&]+)", full_text[:2000])
        fund_name = fund_name_match.group(1).strip() if fund_name_match else "Unknown Fund"
        
        # Extract SFDR article
        article_match = re.search(r"Article\s+([689])\s", full_text, re.IGNORECASE)
        sfdr_article = int(article_match.group(1)) if article_match else None
        
        return {
            "fund_name": fund_name,
            "sfdr_article": sfdr_article
        }
    except Exception as e:
        logger.error(f"Erreur extraction prospectus: {e}")
        return {"fund_name": "Unknown Fund", "sfdr_article": None}

