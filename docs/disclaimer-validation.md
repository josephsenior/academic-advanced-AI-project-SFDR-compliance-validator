# Disclaimer Validation Module

## Overview

The Disclaimer Validation module ensures that marketing documents contain all required disclaimers based on:
- Document content (ESG mentions, performance data, etc.)
- Metadata (client type, management company, new product/strategy)
- Disclaimer glossary (Excel file)

## Features

### [OK] Complete Disclaimer Type Support

All 15+ disclaimer types are now supported:

1. **OBAM Presentation** - Always required for presentations
2. **Commercial Documentation** - Based on management company (SAS/GmbH/Lux)
3. **Commercial Documentation (RAIF)** - For Luxembourg funds
4. **Performance** - When past performance is shown
5. **ESG Risk** - When ESG criteria are mentioned
6. **Issuers** - When companies/logos are referenced
7. **Backtest** - When back-tested performance is shown
8. **Simulation** - When future performance simulations are provided
9. **YtM/YtW** - When yield terms are mentioned
10. **Opinion** - When opinions are expressed
11. **Additional Information** - Various additional info disclaimers
12. **SFDR Article 6/8/9** - Based on SFDR classification
13. **Money Market Fund** - For MMF regulatory factsheets
14. **SRI** - Summary Risk Indicator mentions
15. **New Offer** - When document references new strategy

### [OK] Excel Integration

- **Disclaimer Glossary**: Loads from `GLOSSAIRE DISCLAIMERS 20231122 .xlsx`
  - Supports 3 languages (English, French, German)
  - Differentiates professional vs non-professional clients
  - 31+ disclaimer types per language

- **Registration of Funds**: Loads from `Registration abroad of Funds_20251008.xlsx`
  - Validates country mentions against registration status
  - Supports 21 countries
  - Checks fund/share class/ISIN combinations

## Usage

### Basic Disclaimer Validation

```python
from src.extractors.disclaimer_validator import DisclaimerValidator
from src.extractors.pipeline import ExtractionPipeline

# Initialize validator
validator = DisclaimerValidator()

# Extract document
pipeline = ExtractionPipeline(use_llm=False)
result = pipeline.process_document("document.pptx")

# Validate disclaimers
disclaimer_result = validator.validate(
    result['extraction_result'],
    result['metadata'],
    result.get('document_id')
)

# Check results
print(f"Required: {disclaimer_result.total_required}")
print(f"Present: {disclaimer_result.total_present}")
print(f"Missing: {disclaimer_result.total_missing}")

for missing in disclaimer_result.missing_disclaimers:
    print(f"Missing: {missing.disclaimer_type} - {missing.reason}")
```

### Country Registration Validation

```python
from src.extractors.registration_parser import RegistrationParser

# Initialize parser
parser = RegistrationParser()

# Validate country mentions
mentioned_countries = ["France", "Germany", "Spain"]
validation = parser.validate_country_mentions(
    mentioned_countries,
    fund_name="ODDO BHF Algo Trend US",
    share_class="CR-EUR"
)

for country, is_registered in validation.items():
    if not is_registered:
        print(f"ERROR: {country} is not registered for this fund")
```

### Integrated with Data Consistency Agent

```python
from src.extractors.data_consistency_agent import DataConsistencyAgent
from src.extractors.disclaimer_validator import DisclaimerValidator

# Initialize validator
disclaimer_validator = DisclaimerValidator()

# Create agent with disclaimer validation enabled
agent = DataConsistencyAgent(
    enable_disclaimer_validation=True,
    disclaimer_validator=disclaimer_validator
)

# Validate (includes disclaimer validation)
result = agent.validate(
    extraction_result,
    metadata,
    document_id
)

# Check disclaimer results
if result.disclaimer_validation:
    disc_val = result.disclaimer_validation
    print(f"Missing disclaimers: {disc_val['total_missing']}")
```

## How It Works

### 1. Disclaimer Detection

The system detects disclaimers in two ways:

**Content-Based Detection**:
- Analyzes document text for keywords
- Checks for ESG mentions, performance data, company logos, etc.
- Uses `DISCLAIMER_CATEGORIES` for pattern matching

**Metadata-Based Requirements**:
- OBAM Presentation: Always required for presentations
- Commercial Documentation: Based on management company
- New Offer: Based on `is_new_strategy` metadata

### 2. Disclaimer Requirement Determination

The validator determines required disclaimers based on:

1. **Document Type**: Presentation vs Commercial Doc
2. **Content Analysis**: What's mentioned in the document
3. **Metadata**: Client type, management company, new product/strategy
4. **Language**: Selects appropriate language version from glossary

### 3. Validation

Compares:
- **Required disclaimers** (determined from content + metadata)
- **Present disclaimers** (detected in document)

Reports:
- Missing disclaimers with expected text
- Present disclaimers
- Overall compliance status

## Configuration

### Disclaimer Glossary Path

Default: `dataset/GLOSSAIRE DISCLAIMERS 20231122 .xlsx`

```python
validator = DisclaimerValidator(
    disclaimer_glossary_path="path/to/glossary.xlsx"
)
```

### Registration File Path

Default: `dataset/Registration abroad of Funds_20251008.xlsx`

```python
parser = RegistrationParser(
    registration_file_path="path/to/registration.xlsx"
)
```

## Integration Points

### With Document Extraction

Disclaimers are detected during document extraction via:
- `DISCLAIMER_CATEGORIES` in `document_extractor.py`
- `_categorize_disclaimer()` method
- Stored in `structure.disclaimer_categories`

### With Data Consistency Agent

Disclaimer validation is integrated as an optional step:
- Enable with `enable_disclaimer_validation=True`
- Results included in `DataConsistencyResult.disclaimer_validation`
- Affects overall `has_errors` and `has_warnings` flags

## Example Output

```json
{
  "required_disclaimers": [
    {
      "disclaimer_type": "obam_presentation",
      "reason": "Mandatory for all presentations",
      "location": "All slides",
      "text": "ODDO BHF Asset Management...",
      "language": "ENGLISH",
      "client_type": "non_professional"
    },
    {
      "disclaimer_type": "performance",
      "reason": "Performance data is present in the document",
      "location": "Near performance data",
      "text": "Past performance is not..."
    }
  ],
  "present_disclaimers": ["obam_presentation"],
  "missing_disclaimers": [
    {
      "disclaimer_type": "performance",
      "reason": "Performance data is present in the document",
      "severity": "error",
      "expected_text": "Past performance is not..."
    }
  ],
  "total_required": 2,
  "total_present": 1,
  "total_missing": 1,
  "has_errors": true
}
```

## Next Steps

1. **Enhanced Detection**: Improve detection accuracy for all disclaimer types
2. **Location Suggestions**: Suggest where to add missing disclaimers
3. **Text Matching**: Fuzzy matching to detect disclaimers even if wording differs slightly
4. **Multi-language**: Better support for mixed-language documents

