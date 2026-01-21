# Features & Validation Rules

This document details the comprehensive compliance validation logic enforced by the system.

## Overview

The system performs **multi-layered validation** across multiple compliance dimensions:
1. **Disclaimer Validation** - Legal disclaimer presence and correctness
2. **Data Consistency** - Cross-reference validation across document elements
3. **Registration Validation** - Country distribution authorization
4. **ESG/SFDR Compliance** - Sustainability disclosure requirements
5. **Content & Formatting** - Visual and content quality checks
6. **Metadata Inference** - Automatic detection of document characteristics

---

## 1. Disclaimer Validation

The system checks for the presence and correctness of **15+ disclaimer types** based on document content, metadata, and regulatory requirements.

### Disclaimer Types

| Disclaimer Type | Trigger Condition | Required For |
|----------------|-------------------|--------------|
| **OBAM Presentation** | PPTX presentations | All marketing presentations |
| **Performance** | Content contains performance data, YTD, percentage tables | Documents with performance claims |
| **ESG Risk** | Content mentions ESG, Sustainability, SFDR | Article 8/9 funds |
| **Simulation** | Content contains "Backtest", "Simulation", "Hypothetical" | Historical/simulated data |
| **Capital Loss** | Financial products | All investment products |
| **Past Performance** | Historical performance data present | Performance presentations |
| **Future Performance** | Forward-looking statements | Projections/forecasts |
| **Currency Risk** | Multi-currency content | International funds |
| **Liquidity Risk** | Fund liquidity information | All funds |
| **Counterparty Risk** | Derivative/swap mentions | Complex products |
| **New Offer** | New strategy/product launch | New fund launches |
| **Professional Investors** | Professional client targeting | Professional-only products |
| **Retail** | Retail client targeting | Retail products |
| **Tax** | Tax-related information | Tax-sensitive content |
| **Regulatory** | Country-specific regulations | Cross-border distribution |

### Glossary Integration

The system loads disclaimer templates from `dataset/GLOSSAIRE DISCLAIMERS.xlsx`:
- **Multi-language Support**: English, French, German templates
- **Client Type Variants**: Distinct wording for Professional vs. Retail clients
- **Context-Aware Matching**: Fuzzy matching against document content
- **Visual Prominence**: Validates disclaimer visibility and formatting

### Validation Checks

- **Presence**: Is the required disclaimer present?
- **Accuracy**: Does the disclaimer text match the glossary template?
- **Location**: Is the disclaimer in an appropriate location (footer, slide)?
- **Visibility**: Is the disclaimer visually prominent enough?
- **Language Consistency**: Are disclaimers in the correct language?

---

## 2. Data Consistency Agent

The `DataConsistencyAgent` performs **cross-reference validation** across all document elements to ensure data accuracy and consistency.

### Core Validation Checks

#### Numerical Accuracy
- **Text vs. Tables**: Validates that numerical values in text match table data
- **Text vs. Charts**: Compares text claims against chart data points
- **Table vs. Charts**: Ensures table and chart data are consistent
- **Tolerance**: Configurable tolerance for floating-point comparisons

#### Date Recency
- **Data Freshness**: Checks if "Data as of" dates are recent (< 3 months)
- **Historical Data**: Validates historical data date ranges
- **Prospectus Dates**: Compares document dates against prospectus dates

#### Source Attribution
- **Chart Sources**: Ensures all charts have source footnotes
- **Table Sources**: Validates table source attribution
- **Data Source Consistency**: Checks source consistency across document

#### Cross-Reference Validation
- **Chart References**: Validates text references to charts exist
- **Table References**: Ensures referenced tables are present
- **Slide References**: Validates cross-slide references

#### Prospectus Comparison
- **Fee Validation**: Compares extracted fees against prospectus
- **Performance Validation**: Validates performance claims against prospectus
- **Strategy Consistency**: Ensures document strategy matches prospectus

### Validation Categories

1. **Numerical Validator**: Checks numerical consistency
2. **Chart Validator**: Validates chart data extraction accuracy
3. **Cross-Reference Validator**: Ensures references are valid
4. **Source Date Validator**: Validates data freshness

---

## 3. Registration Validation

Ensures funds are only marketed in **authorized countries** according to regulatory databases.

### Process

1. **Country Detection**: Identifies country mentions in document (e.g., "Available in Italy", "Distributed in France")
2. **Fund Identification**: Extracts Fund Name, ISIN, or other identifiers
3. **Database Lookup**: Queries `dataset/Registration abroad of Funds.xlsx`
4. **Validation**: Checks if fund-country pair is:
   - **Registered**: Full registration status
   - **Notification**: Notification-only status
   - **Not Registered**: Violation flagged

### Validation Rules

- **Mentioned but Not Registered**: Critical violation
- **Registered but Not Mentioned**: Informational (optional)
- **Multiple Countries**: Validates each country individually
- **Language Variants**: Handles country name variations

---

## 4. ESG & SFDR Compliance

Validates **sustainability disclosures** and **SFDR Article 8/9** compliance.

### Article Classification

- **Article 8**: "Light green" funds promoting environmental/social characteristics
- **Article 9**: "Dark green" funds with sustainable investment objectives
- **Article 6**: Standard funds (no ESG claims)

### Validation Checks

#### Article 8 Requirements
- **Disclosure Presence**: Required SFDR disclosures present
- **Sustainable Investment %**: Validates minimum thresholds (typically 10%+)
- **Principal Adverse Impacts**: Checks for PAI disclosure
- **ESG Risk Disclosure**: Validates ESG risk disclaimer

#### Article 9 Requirements
- **Sustainable Investment Objective**: Clear objective statement
- **Minimum Sustainable Investment %**: Higher thresholds (typically 90%+)
- **Compliance Monitoring**: Ongoing compliance verification

#### ESG Content Validation
- **ESG Claims**: Validates ESG-related claims are supported
- **Greenwashing Detection**: Flags unsupported sustainability claims
- **Volume Analysis**: Ensures adequate ESG content volume
- **Terminology Consistency**: Validates ESG terminology usage

### ESG Analyzer

Uses LLM-based analysis to:
- Extract ESG mentions and claims
- Classify ESG level (Article 6/8/9)
- Validate claim support
- Generate compliance reports

---

## 5. Content & Formatting Validation

### Visual Formatting

- **Font Size**: Validates minimum font sizes for disclaimers
- **Color Contrast**: Checks text-background contrast ratios
- **Bold/Italic**: Ensures required emphasis is applied
- **Positioning**: Validates disclaimer placement

### Visual Prominence

- **Disclaimer Visibility**: Ensures disclaimers are prominent
- **Slide Position**: Validates footer/header placement
- **Size Requirements**: Checks minimum size requirements

### Content Quality

- **Anglicism Detection**: Flags inappropriate English terms in non-English documents
- **Translation Consistency**: Ensures consistent translations across languages
- **Terminology**: Validates financial terminology usage

---

## 6. Metadata Inference

The system automatically infers document metadata to drive validation rules.

### Detected Metadata

- **Client Type**: Professional vs. Retail
  - Detected via phrases like "For Professional Investors Only"
  - Affects disclaimer requirements
  
- **Language**: Document language (EN, FR, DE, etc.)
  - Detected via content analysis
  - Affects glossary template selection
  
- **Fund Type**: Article 6/8/9 classification
  - Detected via ESG content analysis
  - Affects ESG validation requirements
  
- **Strategy Type**: New vs. Existing
  - Detected via content analysis
  - Affects "New Offer" disclaimer requirements
  
- **Document Family**: Presentation, Prospectus, Fact Sheet
  - Detected via structure analysis
  - Affects validation rule selection

### Metadata Sources

1. **Filename Parsing**: Extracts metadata from structured filenames
2. **Content Analysis**: LLM-based content analysis
3. **Structure Analysis**: Document structure patterns
4. **User Input**: API-provided metadata (optional)

---

## Issue Severity Levels

Issues are classified by severity:

- **CRITICAL**: Blocking compliance violations
  - Unregistered country distribution
  - Missing required disclaimers
  - Article 8/9 misclassification
  
- **HIGH**: Major data inconsistencies
  - Text vs. table mismatches (>5% difference)
  - Missing source attribution
  - Significant date recency issues
  
- **MEDIUM**: Formatting or moderate issues
  - Visual formatting problems
  - Minor data inconsistencies
  - Content quality issues
  
- **LOW**: Suggestions or minor warnings
  - Style improvements
  - Optional enhancements
  - Informational notes

---

## Compliance Score Calculation

The system calculates an overall **compliance score** (0-100):

- **Base Score**: 100 points
- **Critical Issues**: -20 points each
- **High Issues**: -10 points each
- **Medium Issues**: -5 points each
- **Low Issues**: -1 point each
- **Minimum Score**: 0 (cannot go negative)

The score provides a quick assessment of overall document compliance.
