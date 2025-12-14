import pytest

from backend.extractors.core.document_extractor import DocumentExtractor


@pytest.fixture(scope="module")
def extractor():
    return DocumentExtractor()


def test_extract_title_fields(extractor):
    text = """ODDO BHF Algo Trend
Promotional document – Retail clients
Currency EUR
31/08/2025
ODDO BHF Asset Management SAS"""

    info = extractor._extract_title_fields(text)

    assert info['fund_name'] == "ODDO BHF Algo Trend"
    assert info['currency'] == "EUR"
    assert info['client_type'] == "retail"
    assert info['document_date'] == "31/08/2025"
    assert "Asset Management" in info['management_company']


def test_extract_identifiers(extractor):
    sample = "Share class CR-EUR with ISIN FR0012345678 available"
    identifiers = extractor._extract_identifiers(sample, {'slide_number': 2})
    isin = next(item for item in identifiers if item['type'] == 'isin')
    share = next(item for item in identifiers if item['type'] == 'share_class')

    assert isin['value'] == "FR0012345678"
    assert isin['slide_number'] == 2
    assert share['value'] == "CR-EUR"


def test_categorize_disclaimer(extractor):
    text = "Past performance disclaimer: performances passées ne préjugent pas des résultats futurs"
    categories = extractor._categorize_disclaimer(text)
    assert 'performance' in categories


def test_analyze_performance_sentence(extractor):
    sentence = "Net of fees, fund performance YTD is 12.5% vs benchmark EuroStoxx"
    data = extractor._analyze_performance_sentence(sentence)
    assert data['basis'] == 'net'
    assert data['period'] == 'ytd'
    assert data['benchmark'].lower().startswith('eurostoxx')
    assert data['value'] == pytest.approx(12.5)


def test_extract_issuer_mentions(extractor):
    text = "Top holdings:\n• Apple Inc\n• Microsoft Corp\n• Alphabet"
    mentions = extractor._extract_issuer_mentions(text, {'slide_number': 3})
    names = {m['issuer_name'] for m in mentions}
    assert {"Apple Inc", "Microsoft Corp", "Alphabet"}.issubset(names)


def test_country_entries(extractor):
    countries = ["France", "Germany"]
    entries = extractor._country_entries(countries, "Distribution", "Distribution: France, Germany", {'slide_number': 5})
    assert len(entries) == 2
    assert entries[0]['heading'] == "Distribution"
    assert entries[0]['slide_number'] == 5


def test_detect_legal_notice(extractor):
    text = "ODDO BHF Asset Management SAS est une société de gestion régulée"
    assert extractor._detect_legal_notice(text) is True
