# Disclaimers Glossary - Overview

## Purpose
Comprehensive glossary of mandatory and conditional disclaimers required for ODDO BHF marketing documents. Contains 31 unique disclaimer types in 3 languages (English, French, German) with variations based on client type, management company, and document content.

## File Information
- **File**: `GLOSSAIRE DISCLAIMERS 20231122 .xlsx`
- **Sheets**: 3 (ENGLISH, FRENCH, GERMAN)
- **Disclaimer Types**: 31 unique types per language
- **Columns**: 
  - Document type / Type Document / Dokument typ
  - Language-specific disclaimer text (ENGLISH LANGUAGE / FRENCH LANGUAGE / GERMAN LANGUAGE)
  - Client type (Professional vs Non-professional)

## Structure

### Multi-Language Support
Each disclaimer exists in 3 languages:
- **ENGLISH** sheet
- **FRENCH** sheet  
- **GERMAN** sheet

### Key Columns
- **Document Type**: Type of document (presentation, commercial doc, strategy doc, video, etc.)
- **Language Column**: Disclaimer text in the respective language
- **Client Type Column**: Differentiates between Professional and Non-professional clients

## Disclaimer Categories

### 1. Mandatory Disclaimers

#### OBAM Presentation
- **Required**: Always required on all presentations
- **Purpose**: Introduces ODDO BHF Asset Management
- **Variations**: Different text for professional vs non-professional clients
- **Language**: Available in EN/FR/DE

#### Commercial Documentation
- **Required**: Based on management company
- **Variants**:
  - OBAM SAS (France)
  - OBAM GmbH (Germany)
  - OBAM Lux (Luxembourg)
- **Document Types**: Different for strategies vs funds
- **Restrictions**: Some combinations marked as "Not allowed" / "Non autorisé" / "nicht erlaubt"

### 2. Content-Specific Disclaimers

#### Opinion
- **Trigger**: When opinions are expressed in the document
- **Purpose**: Disclaims opinions expressed

#### Performance
- **Trigger**: When past performance data is shown
- **Purpose**: Past performance doesn't guarantee future results
- **Variations**: Also applies to back-tested performance

#### ESG Risk
- **Trigger**: When ESG (Environmental, Social, Governance) criteria are mentioned
- **Purpose**: Discloses ESG-related risks
- **Context**: Often related to SFDR regulations

#### Issuers Mentioned
- **Trigger**: When companies/logos are referenced in the document
- **Purpose**: Disclaims responsibility for company-specific information

#### Back-tested Performance
- **Trigger**: When historical simulated performance is shown
- **Purpose**: Similar to Performance disclaimer

#### Simulations of Future Performance
- **Trigger**: When forecasts or future performance projections are provided
- **Purpose**: Disclaims that projections are not guaranteed

#### YtM/YtW Usage
- **Trigger**: When Yield to Maturity (YtM) or Yield to Worst (YtW) terms appear
- **Purpose**: Explains yield calculations and limitations

### 3. Regulatory Disclaimers

#### SFDR Article 6
- **Trigger**: When Article 6 of SFDR (Sustainable Finance Disclosure Regulation) applies
- **Purpose**: Standard disclosure for non-ESG products

#### SFDR Article 8
- **Trigger**: When Article 8 of SFDR applies (products promoting environmental/social characteristics)
- **Purpose**: Enhanced disclosure for ESG-promoting products

#### SFDR Article 9
- **Trigger**: When Article 9 of SFDR applies (products with sustainable investment objective)
- **Purpose**: Highest level of ESG disclosure

#### Money Market Fund
- **Trigger**: Regulatory weekly factsheet for money market funds
- **Purpose**: Specific regulatory requirements

#### SRI (Socially Responsible Investment)
- **Trigger**: Risk mentions in marketing documents/videos
- **Purpose**: SRI-specific risk disclosure

### 4. New Offer Disclaimers

#### New Offer Products (Strategy Only)
- **Trigger**: When document references a new strategy (no fund track record)
- **Purpose**: Disclaims lack of historical performance

#### New Offer Products (Strategy Mentioning Funds Track Record)
- **Trigger**: When document references a new strategy but mentions related fund track record
- **Purpose**: Distinguishes between strategy and fund performance

### 5. Special Cases

#### Commercial Documentation (Luxembourg Funds-RAIF)
- **Trigger**: Specific to Luxembourg funds (RAIF structure)
- **Purpose**: Luxembourg-specific regulatory requirements

#### Additional Information
Various country/context-specific additional information:
- **FWW-Fundstars Usage**: For FWW-Fundstars platform
- **German Market**: German market specific information
- **German Professional Clients**: Performance information for German professional clients
- **MSCI ESG Information**: When MSCI ESG data is referenced
- **Switzerland Registration**: Various types for funds registered in Switzerland

#### VIDEO
- **Trigger**: For video scripts
- **Purpose**: Video-specific disclaimer requirements

## Selection Logic

### Based on Document Content
- **ESG mentions** → ESG Risk disclaimer
- **Performance data** → Performance disclaimer
- **Company logos** → Issuers mentioned disclaimer
- **New strategy** → New Offer disclaimer
- **SFDR articles** → Corresponding SFDR disclaimer

### Based on Client Type
- **Professional clients**: Professional version of disclaimer
- **Non-professional clients**: Non-professional version of disclaimer
- **Different requirements**: Some disclaimers are mandatory only for retail clients

### Based on Management Company
- **OBAM SAS (France)**: French management company disclaimer
- **OBAM GmbH (Germany)**: German management company disclaimer
- **OBAM Lux (Luxembourg)**: Luxembourg management company disclaimer

### Based on Document Type
- **Presentation**: Standard presentation disclaimers
- **Commercial Documentation**: Commercial document disclaimers
- **Strategy Document**: Strategy-specific disclaimers
- **Video**: Video-specific disclaimers

### Based on Product Status
- **New Strategy**: New Offer disclaimers required
- **Existing Strategy**: No new offer disclaimers needed

## Important Rules

### Always Required
- **OBAM Presentation**: Must appear on all presentations regardless of content

### Conditional Requirements
- **Commercial Documentation**: Required based on management company type
- **Opinion**: Required when opinions are expressed
- **Performance**: Required when past performance is shown

### Prohibited Combinations
- Some disclaimer combinations are marked as "Not allowed" / "Non autorisé" / "nicht erlaubt"
- System must detect and flag these conflicts

### Language Selection
- Must select disclaimer in the same language as the document
- Language detection from filename or content analysis
- English (GB), French (FR), German (DE)

## Usage in Compliance System

### Step 1: Analyze Document Content
Extract:
- ESG mentions (keywords, SFDR articles)
- Performance data (charts, tables, date ranges)
- Company mentions (logos, company names)
- Financial terms (YtM, YtW)
- New strategy/product indicators

### Step 2: Extract Metadata
From `metadata.json`:
- Client type (professional vs non-professional)
- Management company (SAS/GmbH/Lux)
- New product/strategy flags
- Document type

### Step 3: Determine Required Disclaimers
Apply conditional logic:
1. **Always include**: OBAM Presentation disclaimer
2. **Based on management company**: Commercial Documentation disclaimer
3. **Based on content**: Content-specific disclaimers (ESG, Performance, etc.)
4. **Based on client type**: Select professional or non-professional version
5. **Based on language**: Select appropriate language version

### Step 4: Validate Against Document
- Check if required disclaimers are present in the document
- Verify correct language version is used
- Verify correct client type version is used
- Check for prohibited combinations

### Step 5: Flag Missing or Incorrect Disclaimers
- **Missing**: Required disclaimer not found
- **Wrong Language**: Disclaimer in incorrect language
- **Wrong Client Type**: Professional disclaimer used for retail, or vice versa
- **Prohibited Combination**: Conflicting disclaimers detected

## Example Scenarios

### ✅ Valid Document - Professional Client
```
Document: Presentation about existing ESG fund
Client Type: Professional
Management Company: OBAM SAS
Language: French
Content: ESG criteria, past performance, company logos

Required Disclaimers:
1. OBAM Presentation (FR, Professional) ✅
2. Commercial Documentation OBAM SAS (FR, Professional) ✅
3. ESG Risk (FR, Professional) ✅
4. Performance (FR, Professional) ✅
5. Issuers Mentioned (FR, Professional) ✅
```

### ✅ Valid Document - Retail Client
```
Document: Presentation about new strategy
Client Type: Non-professional
Management Company: OBAM GmbH
Language: English
Content: New strategy description, performance projections

Required Disclaimers:
1. OBAM Presentation (EN, Non-professional) ✅
2. Commercial Documentation OBAM GmbH (EN, Non-professional) ✅
3. New Offer Products (Strategy Only) (EN, Non-professional) ✅
4. Simulations of Future Performance (EN, Non-professional) ✅
```

### ❌ Invalid Document - Missing Disclaimer
```
Document: Presentation with ESG content
Required: ESG Risk disclaimer
Found: Not present
Result: ❌ Violation - Missing ESG Risk disclaimer
```

### ❌ Invalid Document - Wrong Language
```
Document: French presentation
Required: OBAM Presentation (FR)
Found: OBAM Presentation (EN)
Result: ❌ Violation - Wrong language disclaimer
```

### ❌ Invalid Document - Wrong Client Type
```
Document: Retail client presentation
Required: OBAM Presentation (Non-professional)
Found: OBAM Presentation (Professional)
Result: ❌ Violation - Professional disclaimer used for retail client
```

## Integration Requirements

### Database Schema
```sql
Table: Disclaimers
- disclaimer_id (INT, PRIMARY KEY)
- disclaimer_type (VARCHAR) -- e.g., 'OBAM_Presentation', 'ESG_Risk'
- language (VARCHAR) -- 'EN', 'FR', 'DE'
- client_type (VARCHAR) -- 'Professional', 'Non-professional', 'Both'
- management_company (VARCHAR) -- 'SAS', 'GmbH', 'Lux', 'All'
- document_type (VARCHAR) -- 'Presentation', 'Commercial', 'Strategy', 'Video'
- disclaimer_text (TEXT)
- is_mandatory (BOOLEAN)
- trigger_conditions (JSON) -- Conditions that require this disclaimer
- prohibited_with (JSON) -- Disclaimers that cannot be combined with this one
```

### Selection Logic
```python
def select_required_disclaimers(document_content, metadata, language):
    disclaimers = []
    
    # Always required
    disclaimers.append(get_disclaimer(
        type='OBAM_Presentation',
        language=language,
        client_type=metadata['client_type']
    ))
    
    # Management company specific
    disclaimers.append(get_disclaimer(
        type='Commercial_Documentation',
        language=language,
        client_type=metadata['client_type'],
        management_company=metadata['management_company']
    ))
    
    # Content-based
    if has_esg_content(document_content):
        disclaimers.append(get_disclaimer(
            type='ESG_Risk',
            language=language,
            client_type=metadata['client_type']
        ))
    
    if has_performance_data(document_content):
        disclaimers.append(get_disclaimer(
            type='Performance',
            language=language,
            client_type=metadata['client_type']
        ))
    
    # Check for prohibited combinations
    validate_disclaimer_combinations(disclaimers)
    
    return disclaimers
```

## Key Takeaways

- **31 Disclaimer Types**: Comprehensive coverage of all regulatory requirements
- **3 Languages**: EN/FR/DE versions for all disclaimers
- **Client Type Matters**: Different text for professional vs non-professional clients
- **Content-Driven**: Many disclaimers triggered by document content analysis
- **Management Company**: Different disclaimers based on SAS/GmbH/Lux
- **Always Required**: OBAM Presentation disclaimer on all presentations
- **Prohibited Combinations**: Some disclaimers cannot be combined
- **Language Matching**: Disclaimers must match document language

