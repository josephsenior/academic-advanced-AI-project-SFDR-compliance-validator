# Registration Abroad of Funds - Overview

## Purpose
Registry of ODDO BHF funds authorized for sale across 21 countries. Used for compliance validation to ensure marketing documents only mention countries where funds are legally registered.

## File Information
- **File**: `Registration abroad of Funds_20251008.xlsx`
- **Sheet**: Registration
- **Rows**: 560 (fund share classes)
- **Columns**: 38 (4 fund identification + 21 country registrations)
- **Unique Funds**: 82

## Structure

### Fund Identification (4 columns)
- **Fund Name**: e.g., "ODDO BHF Active Small Cap"
- **Share Class**: e.g., "CR-EUR", "CI-EUR"
- **ISIN**: International Securities Identification Number
- **Date de clôture**: Closing date

### Country Registrations (21 countries)
Germany, Austria, Belgium, Chile, Spain, France, Italy, Luxembourg, Netherlands, Peru, Portugal, United Kingdom, Singapore, Sweden, Switzerland, Finland, Denmark, Norway, Ireland, United Arab Emirates, Iceland

## Registration Codes

| Code | Meaning | Compliance Implication |
|------|---------|------------------------|
| **R** | Registered | [OK] Fund can be marketed in this country |
| **RX** | Registered (specific type) | [OK] Registered but with specific conditions |
| **Y** | Tax Transparency | [OK] Registered + Tax transparency status |
| **Institutional** | Institutional only | [WARNING] Can only be marketed to professional clients |
| **Retail** | Retail available | [OK] Can be marketed to both retail and institutional |
| **NaN/Empty** | Not registered | [FAIL] Cannot be mentioned in marketing documents |

## Compliance Rules

### Rule 1: Only for Existing Products
- Registration file should only be checked if the product is **NOT new**
- If `"Le document fait-il référence à un nouveau Produit": true`, skip registration check entirely

### Rule 2: Country Validation
- Documents must only mention countries where the fund is registered
- Cannot claim availability in countries where registration doesn't exist

### Rule 3: Client Type Distinction
- If registration code = "Institutional":
  - [OK] Valid if document targets professional clients (`"Le client est-il un professionnel": true`)
  - [FAIL] Invalid if targeting retail clients

### Rule 4: Multiple Share Classes
- Each fund can have multiple share classes (different fee structures, currency, investor types)
- Each share class can have different country registrations
- Must match the correct share class being promoted

## Usage in Compliance System

### Step 1: Extract Fund Information
- Extract fund name or ISIN from the marketing presentation
- Identify which share class is being promoted

### Step 2: Look Up Registration Status
- Find the row(s) matching the fund/ISIN/share class
- Read the registration status for each country column

### Step 3: Extract Country Mentions
- Parse document text for country mentions
- Check for phrases like "Available in Germany", country flags/icons, country-specific contact information

### Step 4: Validate Country Claims
For each country mentioned in the document:
- [OK] **If code = R, RX, Y, Institutional, or Retail**: Claim is valid (subject to client type check)
- [FAIL] **If code = NaN/Empty**: Violation - fund is not registered there

## Example Scenarios

### [OK] Valid Document
```
Fund: ODDO BHF Active Small Cap
Share: CR-EUR
Document mentions: "Available in France, Germany, Switzerland"
Registration status:
- France: R [OK]
- Germany: R [OK]
- Switzerland: R [OK]
Result: [OK] All claims valid
```

### [FAIL] Invalid Document - Unregistered Country
```
Fund: ODDO BHF Active Small Cap
Share: CR-EUR
Document mentions: "Available in France, Italy, Japan"
Registration status:
- France: R [OK]
- Italy: NaN [FAIL]
- Japan: (not in list) [FAIL]
Result: [FAIL] Violation - Cannot mention Italy or Japan
```

### [FAIL] Invalid Document - Institutional Only
```
Fund: ODDO BHF Active Small Cap
Share: CI-EUR
Document metadata: "Le client est-il un professionnel": false (retail)
Registration status:
- Germany: Institutional [WARNING]
Result: [FAIL] Violation - Document targets retail but fund is institutional-only in Germany
```

### ⏭️ New Product - Skip Check
```
Document metadata: "Le document fait-il référence à un nouveau Produit": true
Result: ⏭️ Skip registration check (new products exempt)
```

## Integration Requirements

### Database Schema
```sql
Table: FundRegistrations
- fund_name (VARCHAR)
- share_class (VARCHAR)
- isin (VARCHAR)
- country (VARCHAR)
- registration_code (VARCHAR)
- registration_type (VARCHAR) -- 'fund' or 'unit'
- tax_transparency (BOOLEAN) -- true if code = 'Y'
```

### Validation Logic
```python
def validate_country_registration(fund_isin, share_class, country, client_type):
    registration = lookup_registration(fund_isin, share_class, country)
    
    if registration is None or registration == "NaN":
        return "VIOLATION: Fund not registered in {country}"
    
    if registration == "Institutional" and client_type != "professional":
        return "VIOLATION: Institutional-only fund targeting retail clients"
    
    return "VALID"
```

## Key Takeaways

- **Purpose**: Compliance validation to prevent unauthorized country claims
- **Scale**: 82 funds × multiple share classes × 21 countries = 560 registration entries
- **Critical Rule**: Only check existing products (skip if new product flag = true)
- **Complexity**: Must handle institutional vs retail distinction, multiple share classes, and tax transparency status

