"""
Field Extraction Utilities

Extract structured fields from document text (title, identifiers, performance, etc.).
"""

import re
from typing import Dict, List, Any, Optional
from .text_utils import DATE_PATTERN, ISIN_PATTERN, SHARE_CLASS_PATTERN, PERCENT_PATTERN
from .keywords import ISSUER_SECTION_KEYWORDS


def extract_title_fields(text: str) -> Dict[str, Optional[str]]:
    """Extract key facts from the opening section of a document."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    joined = " ".join(lines)

    # Fund name heuristic: first non-empty line with capital letters that is not purely a date
    fund_name = None
    for line in lines:
        if len(line) < 4:
            continue
        if DATE_PATTERN.search(line):
            continue
        if any(char.isalpha() for char in line):
            fund_name = line
            break

    # Currency: capture tokens like "EUR", "USD", "CHF"
    currency_match = re.search(r"(?:currency|devise)\s*[:\-]?\s*([A-Z]{3})", joined, re.IGNORECASE)
    if not currency_match:
        # Fallback: take an isolated 3-letter token that looks like an ISO currency code
        fallback_match = re.search(r"\b([A-Z]{3})\b", joined)
        if fallback_match and fallback_match.group(1) not in {"ODD", "ODDO", "BHF"}:
            currency_match = fallback_match
    currency = currency_match.group(1) if currency_match else None

    # Document date
    date_match = DATE_PATTERN.search(joined)
    document_date = date_match.group(0) if date_match else None

    # Client type
    client_type = None
    lowered = joined.lower()
    if "professional" in lowered or "professionnel" in lowered:
        client_type = "professional"
    elif "retail" in lowered or "non-professional" in lowered or "grand public" in lowered:
        client_type = "retail"

    # Risk indicator
    risk_indicator = None
    risk_match = re.search(r"srri\s*(\d)", lowered)
    if risk_match:
        risk_indicator = risk_match.group(1)
    elif "risk" in lowered and any(token in lowered for token in ["1/7", "2/7", "3/7", "4/7", "5/7", "6/7", "7/7"]):
        risk_match = re.search(r"([1-7]/7)", lowered)
        if risk_match:
            risk_indicator = risk_match.group(1)

    # Management company
    mgmt_match = re.search(r"ODDO\s+BHF[^\n]*", joined, re.IGNORECASE)
    management_company = mgmt_match.group(0) if mgmt_match else None

    return {
        'fund_name': fund_name,
        'currency': currency,
        'document_date': document_date,
        'client_type': client_type,
        'risk_indicator': risk_indicator,
        'management_company': management_company,
    }


def extract_identifiers(text: str, location: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Harvest ISINs and share-class codes with location metadata."""
    identifiers: List[Dict[str, Any]] = []
    for isin in ISIN_PATTERN.findall(text):
        entry = {
            'type': 'isin',
            'value': isin,
            'context': text.strip()[:120],
        }
        entry.update(location)
        identifiers.append(entry)

    for share in SHARE_CLASS_PATTERN.findall(text):
        entry = {
            'type': 'share_class',
            'value': share,
            'context': text.strip()[:120],
        }
        entry.update(location)
        identifiers.append(entry)

    return identifiers


def extract_issuer_mentions(text: str, location: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract issuer mentions from text."""
    mentions = []
    lowered = text.lower()
    if not any(keyword in lowered for keyword in ISSUER_SECTION_KEYWORDS):
        return mentions

    # Split lines – bullet lists are common
    for line in text.splitlines():
        candidate = line.strip(" •-\t")
        if len(candidate) < 3:
            continue
        if any(char.isdigit() for char in candidate):
            continue
        if candidate.lower() in ISSUER_SECTION_KEYWORDS:
            continue
        entry = {
            'issuer_name': candidate,
            'context': text.strip()[:160],
        }
        entry.update(location)
        mentions.append(entry)
    return mentions


def analyze_performance_sentence(sentence: str) -> Dict[str, Any]:
    """Analyze a performance sentence to extract structured data."""
    lowered = sentence.lower()

    basis = None
    if any(keyword in lowered for keyword in ["net of fees", "net des frais", "net"]):
        basis = "net"
    elif any(keyword in lowered for keyword in ["gross of fees", "brut", "gross"]):
        basis = "gross"
    elif "backtest" in lowered or "back-tested" in lowered or "reconstitu" in lowered:
        basis = "backtest"
    elif "simulation" in lowered or "prospective" in lowered:
        basis = "simulation"

    benchmark_name = None
    benchmark_match = re.search(r"(?:benchmark|indice\s*(?:de\s*référence)?)[:\-]?\s*([^.;\n]+)", sentence, re.IGNORECASE)
    if benchmark_match:
        benchmark_name = benchmark_match.group(1).strip()

    period = None
    period_patterns = ["ytd", "1y", "3y", "5y", "10y", "since inception", "depuis l'origine"]
    for token in period_patterns:
        if token in lowered:
            period = token
            break

    value_float = None
    percent_match = PERCENT_PATTERN.search(sentence)
    if percent_match:
        percent_text = percent_match.group(0).replace('%', '').replace(' ', '').replace(',', '.')
        try:
            value_float = float(percent_text)
        except ValueError:
            value_float = None

    return {
        'sentence': sentence,
        'basis': basis,
        'benchmark': benchmark_name,
        'period': period,
        'value': value_float,
    }


def parse_table_source(note: str) -> Dict[str, Optional[str]]:
    """Extract source name and date from a table source note."""
    date_match = DATE_PATTERN.search(note)
    date_text = date_match.group(0) if date_match else None
    source_candidate = note
    if date_text:
        source_candidate = source_candidate.replace(date_text, "")
    source_candidate = re.sub(r"^[^A-Za-z0-9]+|[^A-Za-z0-9]+$", "", source_candidate).strip()
    return {
        'raw_note': note,
        'source_name': source_candidate or None,
        'source_date': date_text,
    }


def detect_countries(text: str, country_patterns: Dict[str, re.Pattern]) -> List[str]:
    """
    Detect countries using enhanced pattern-based matching with word boundaries.
    
    This replaces the old substring matching which caused false positives
    (e.g., "France" matching "Franchise", "Germany" matching "Germanic").
    """
    matches = []
    text_lower = text.lower()
    
    # Use enhanced patterns with word boundaries
    for country, pattern in country_patterns.items():
        if pattern.search(text_lower):
            matches.append(country)
    
    # Return unique, title-cased country names for consistency
    return sorted({country.title() for country in matches})


def country_entries(
    countries: List[str],
    heading: Optional[str],
    sentence: str,
    location: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Create country entry dictionaries with location metadata."""
    entries = []
    for country in countries:
        entry = {
            'country': country,
            'heading': heading,
            'sentence': sentence.strip()[:160],
        }
        entry.update(location)
        entries.append(entry)
    return entries

