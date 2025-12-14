# Fund Type Specific Rules Implementation

**Status**: [OK] **COMPLETED**

---

## Overview

Successfully implemented comprehensive fund type-specific validation rules as part of medium-priority features.

---

## Implemented Features

### 1. [OK] Dated Fund Rules

#### **Active Dated Funds - YTM/YTW Restrictions**
- **Rule**: YTM/YTW should NOT be shown for active management dated funds to retail clients
- **Issue Types**: 
  - `YTM_FOR_ACTIVE_RETAIL`
  - `YTW_FOR_ACTIVE_RETAIL`
- **Severity**: Error
- **Keywords Detected**:
  - YTM: "ytm", "yield to maturity", "rendement à l'échéance"
  - YTW: "ytw", "yield to worst", "rendement au pire"
- **Logic**: Only flags for active dated funds + retail clients (buy-hold dated funds are allowed)

#### **Fund Type Detection**
- Enhanced detection to distinguish between:
  - `DATED_FUND_ACTIVE` - Active management dated funds
  - `DATED_FUND_BUY_HOLD` - Buy and hold dated funds
- Detection based on fund name keywords

---

### 2. [OK] Private Equity Rules

#### **Net IRR Restriction**
- **Rule**: Net IRR should NOT be shown to retail clients
- **Issue Type**: `NET_IRR_FOR_RETAIL`
- **Severity**: Error
- **Keywords Detected**:
  - "net irr", "irr net", "taux de rendement interne net"
  - "internal rate of return", "taux de rendement interne"

#### **Institutional Track Record Restriction**
- **Rule**: Institutional track record should NOT be shown to retail clients
- **Issue Type**: `INSTITUTIONAL_TRACK_FOR_RETAIL`
- **Severity**: Error
- **Keywords Detected**:
  - "institutional track record", "track record institutionnel"
  - "performance institutionnelle", "institutional performance"

#### **Liquidity Disclaimer** (Already implemented, enhanced)
- **Rule**: Private Equity funds require liquidity risk warning
- **Issue Type**: `MISSING_STANDARD_DISCLAIMER`
- **Severity**: Error

---

### 3. [OK] ETF Rules

#### **Liquidity Description Prohibition**
- **Rule**: ETF should NOT be called "liquid"
- **Issue Type**: `ETF_CALLED_LIQUID`
- **Severity**: Error
- **Keywords Detected**:
  - "liquid etf", "etf liquid", "liquid exchange traded"
  - "etf liquide", "fonds négociable liquide"
- **Context-Aware**: Checks if "liquid" appears near "etf" (within 10 words)

---

### 4. [OK] Money Market Fund Rules

#### **Money Market Disclaimer**
- **Rule**: Money Market funds require specific disclaimer
- **Issue Type**: `MISSING_STANDARD_DISCLAIMER`
- **Severity**: Warning
- **Keywords Detected**:
  - "money market fund", "fonds monétaire", "geldmarktfonds"
- **Required Disclaimer Phrases**:
  - "not a guaranteed investment"
  - "different from investment in deposits"

---

### 5. [OK] RAIF Rules

#### **Well-Informed Investor Indication**
- **Rule**: RAIF funds must indicate "Well-informed investors" target audience
- **Issue Type**: `MISSING_TARGET_AUDIENCE`
- **Severity**: Error
- **Keywords Detected**:
  - "well-informed investor", "investisseur bien informé"
  - "well informed investor", "investisseur averti"

#### **RAIF Disclaimer**
- **Rule**: RAIF funds require RAIF-specific disclaimer
- **Issue Type**: `MISSING_STANDARD_DISCLAIMER`
- **Severity**: Warning
- **Keywords Detected**:
  - "raif", "reserved alternative investment fund"
  - "fonds d'investissement alternatif réservé"

---

## Code Implementation

### Method Enhanced
- **Location**: `backend/extractors/agents/data_consistency_agent.py`
- **Method**: `_validate_fund_type_rules()` 
- **Lines Added**: ~200 lines of enhanced validation logic
- **Integration**: Enhanced existing fund type validation section

### Fund Type Detection Enhanced
- **Location**: `backend/extractors/agents/data_consistency_agent.py`
- **Method**: `_validate_compliance_rules()` - fund type detection section
- **Enhancement**: Improved detection for dated funds (active vs buy-hold), Money Market, RAIF

### Category Mapping
- **Updated**: `backend/extractors/rules/category_mapper.py` and `server/serialization.py`
- **Change**: Added fund type keywords to category mapping
- **Result**: Fund type issues are categorized as "compliance"

---

## Validation Flow

```
1. Detect fund type from metadata/fund name:
   - Private Equity (FCPR, FPCI)
   - ETF (ETF, exchange traded)
   - Dated Fund Active (dated, échéance, target date)
   - Dated Fund Buy-Hold (dated + buy + hold)
   - Money Market (money market, fonds monétaire)
   - RAIF (raif, reserved alternative)

2. Extract all text content

3. Validate rules based on fund type:
   - Dated Funds: Check YTM/YTW for active + retail
   - Private Equity: Check IRR, track record for retail
   - ETF: Check for "liquid" description
   - Money Market: Check for specific disclaimer
   - RAIF: Check for well-informed investor mention + disclaimer
```

---

## Example Issues Generated

### YTM for Active Retail
```json
{
  "issue_type": "ytm_for_active_retail",
  "severity": "error",
  "message": "YTM (Yield to Maturity) should not be shown for active management dated funds to retail clients.",
  "suggestion": "Remove YTM data or restrict document to professional clients only"
}
```

### Net IRR for Retail
```json
{
  "issue_type": "net_irr_for_retail",
  "severity": "error",
  "message": "Net IRR (Internal Rate of Return) should not be shown to retail clients for Private Equity funds.",
  "suggestion": "Remove Net IRR data or restrict document to professional clients only"
}
```

### ETF Called Liquid
```json
{
  "issue_type": "etf_called_liquid",
  "severity": "error",
  "message": "ETF should not be called 'liquid'. ETFs have liquidity risks and should not be described as liquid.",
  "suggestion": "Remove 'liquid' description from ETF. Use factual language about ETF characteristics instead."
}
```

### RAIF Missing Target Audience
```json
{
  "issue_type": "missing_target_audience",
  "severity": "error",
  "message": "RAIF fund detected, but 'Well-informed investor' target audience indication is missing.",
  "suggestion": "Add target audience indication: 'Well-informed investors' (within the meaning of the RAIF law)"
}
```

---

## Testing Checklist

- [ ] Test active dated fund with YTM (retail) → Should flag YTM_FOR_ACTIVE_RETAIL
- [ ] Test active dated fund with YTM (professional) → Should pass
- [ ] Test buy-hold dated fund with YTM (retail) → Should pass (allowed)
- [ ] Test Private Equity with Net IRR (retail) → Should flag NET_IRR_FOR_RETAIL
- [ ] Test Private Equity with institutional track (retail) → Should flag INSTITUTIONAL_TRACK_FOR_RETAIL
- [ ] Test ETF described as liquid → Should flag ETF_CALLED_LIQUID
- [ ] Test Money Market without disclaimer → Should flag MISSING_STANDARD_DISCLAIMER
- [ ] Test RAIF without well-informed mention → Should flag MISSING_TARGET_AUDIENCE

---

## Integration Status

[OK] **Fully Integrated**
- Enhanced fund type detection
- Enhanced fund type validation
- Category mapping updated
- Type checking passes
- Ready for testing

---

## Next Steps

According to the plan, remaining medium-priority features are:
1. [OK] Backtest/Simulation Rules - **COMPLETE**
2. [OK] Securities Rules Completion - **COMPLETE**
3. [OK] Fund Type Specific Rules - **COMPLETE**
4. **Germany-Specific Rules** - Next (Last medium-priority item)

---

**Status**: [OK] **READY FOR TESTING**

