# Excel Files Analysis Summary

## 1. DISCLAIMERS GLOSSARY (`GLOSSAIRE DISCLAIMERS 20231122 .xlsx`)

### Structure
- **3 sheets**: ENGLISH, FRENCH, GERMAN
- **31 unique disclaimer types** per language
- **Columns**: 
  - Document type / Type Document / Dokument typ
  - Language-specific column (ENGLISH LANGUAGE / FRENCH LANGUAGE / GERMAN LANGUAGE)
  - Unnamed column (typically for Professional vs Non-professional)

### Key Disclaimer Types

#### 1. **OBAM Presentation**
   - **Required on all presentations**
   - Introduces ODDO BHF Asset Management
   - Different text for professional vs non-professional clients

#### 2. **Commercial Documentation**
   - Variants based on management company:
     - OBAM SAS (France)
     - OBAM GmbH (Germany)
     - OBAM Lux (Luxembourg)
   - Different for strategies vs funds
   - Some marked as "Not allowed" / "Non autorisé" / "nicht erlaubt"

#### 3. **Content-Specific Disclaimers**
   - **Opinion**: Disclaims opinions expressed
   - **Performance**: Past performance doesn't guarantee future results
   - **ESG Risk**: When ESG criteria are mentioned
   - **Issuers mentioned**: When companies/logos are referenced
   - **Back-tested performance**: Similar to Performance
   - **Simulations of future performance**: When forecasts are provided
   - **YtM/YtW usage**: When Yield to Maturity or Yield to Worst terms appear

#### 4. **Regulatory Disclaimers**
   - **SFDR ART.6**: Article 6 of SFDR regulation
   - **SFDR ART.8**: Article 8 of SFDR regulation
   - **SFDR ART.9**: Article 9 of SFDR regulation
   - **Money Market Fund**: Regulatory weekly factsheet
   - **SRI**: Risk mentions in marketing documents/videos

#### 5. **New Offer Disclaimers**
   - **New offer products (strategy only)**
   - **New offer products (strategy mentioning funds track record)**
   - Required when document references a new strategy

#### 6. **Special Cases**
   - **Commercial documentation (luxembourg funds-RAIF)**: Specific to Luxembourg funds
   - **Additional Information**: Various country/context-specific additional information:
     - For FWW-Fundstars usage
     - For German market specific information
     - For performance information for German professional clients
     - For MSCI ESG information
     - For funds registered in Switzerland (various types)
   - **VIDEO**: For video scripts

### Important Notes
- **Client Type Matters**: Disclaimers differ for **Professional** vs **Non-professional** clients
- **Language-Specific**: Each language has its own version
- **Management Company**: Different disclaimers based on which entity (SAS/GmbH/Lux)
- **Some combinations are "Not allowed"**: Certain disclaimer combinations are prohibited

---

## 2. FUND REGISTRATION (`Registration abroad of Funds_20251008.xlsx`)

### Structure
- **1 sheet**: Registration
- **560 rows** (including headers)
- **38 columns** (fund info + country registrations)
- **82 unique funds** registered

### Key Columns

#### Fund Identification
- **Unnamed: 0**: Fund name (e.g., "ODDO BHF Active Small Cap")
- **Share**: Share class identifier (e.g., "CR-EUR", "CI-EUR")
- **ISIN**: International Securities Identification Number
- **Date de clôture**: Closing date

#### Registration Status by Country
**21 countries** tracked for registration:
1. Germany (fund)
2. Austria (fund)
3. Belgium (fund)
4. Chile (fund)
5. Spain (unit)
6. France (fund)
7. Italy (fund)
8. Luxembourg (unit)
9. The Netherlands (fund)
10. Peru (unit)
11. Portugal (fund)
12. United Kingdom (fund)
13. Singapore (fund)
14. Sweden (fund)
15. Switzerland (fund)
16. Finland (fund)
17. Denmark (fund)
18. Norway (fund)
19. Ireland (fund)
20. United Arab Emirates (fund)
21. Iceland (fund)

### Registration Codes

| Code | Meaning |
|------|---------|
| **R** | Registered |
| **RX** | Registered (specific type) |
| **Y** | Yes (Tax Transparency) |
| **Institutional** | Institutional only |
| **Retail** | Retail available |
| **NaN/Empty** | Not registered |

### Important Rules

1. **Only for Existing Products**: 
   - Registration file should only be checked if the product is **NOT new**
   - If `"Le document fait-il référence à un nouveau Produit": true`, skip registration check

2. **Commercialization Authorization**: 
   - Documents must only mention countries where the fund is registered
   - Cannot claim availability in countries where registration doesn't exist

3. **Tax Transparency**: 
   - Some countries have "Y" indicating tax transparency status
   - This affects which disclaimers are needed

---

## Key Insights for Compliance Automation

### 1. **Disclaimer Selection Logic**
- Based on document content (mentions of ESG, performance, companies, etc.)
- Based on client type (professional vs non-professional)
- Based on management company (SAS/GmbH/Lux)
- Based on whether document is about a new strategy
- Based on document type (presentation, commercial doc, strategy doc)

### 2. **Registration Check Logic**
- **ONLY check registration if**: `"Le document fait-il référence à un nouveau Produit": false`
- Check all country mentions in the document against registration status
- Flag any claims about countries where fund is not registered

### 3. **Multi-Language Support**
- Same disclaimer types exist in EN/FR/DE
- Must select appropriate language version based on document language

### 4. **Mandatory Disclaimers**
- **OBAM Presentation**: Always required on all presentations
- **Commercial Documentation**: Required based on management company
- **Opinion**: Required when opinions are expressed
- **Performance**: Required when past performance is shown

### 5. **Conditional Disclaimers**
- **ESG Risk**: Only if ESG criteria mentioned
- **Issuers mentioned**: Only if companies/logos appear
- **New Offer**: Only if document references new strategy
- **SFDR**: Only if specific SFDR articles are cited
- **YtM/YtW**: Only if these terms appear

---

## Next Steps for Implementation

1. **Parse Excel files** into structured data (JSON/CSV)
2. **Create lookup dictionaries** for:
   - Disclaimers by type/language/client type
   - Fund registrations by ISIN/Share
3. **Build rule engine** that:
   - Analyzes document content
   - Matches against metadata
   - Selects appropriate disclaimers
   - Validates country mentions
4. **Integrate with document analysis** to extract:
   - Client type from metadata
   - Management company from metadata
   - Content features (ESG, performance, companies, etc.)
   - Country mentions
   - Language detection

