# Backtest/Simulation Rules Implementation

**Status**: [OK] **COMPLETED**

---

## Overview

Successfully implemented comprehensive backtest and simulation validation rules as part of medium-priority features.

---

## Implemented Features

### 1. [OK] Backtest Detection
- Detects backtest keywords in document text
- Keywords: "back-tested", "backtested", "données arrière", "historique reconstruit", "back test", "back-test", "backtest", "performance rétrospective", "simulations des performances passées"

### 2. [OK] Simulation Detection
- Detects simulation keywords in document text
- Keywords: "simulation", "simulé", "forward-looking", "future performance", "projection", "prévision", "simulation de performance future", "simulation of future performance", "projection de performance"

### 3. [OK] Retail Restriction for Backtest
- **Rule**: Backtest performance should NOT be shown to retail clients
- **Issue Type**: `BACKTEST_FOR_RETAIL`
- **Severity**: Error
- **Validation**: Checks if backtest is detected AND client_type is RETAIL

### 4. [OK] Backtest Disclaimer Validation
- **Rule**: Backtest data requires specific disclaimer
- **Issue Type**: `BACKTEST_MISSING_DISCLAIMER`
- **Severity**: Error
- **Validation**: Checks for backtest disclaimer phrases:
  - "simulations of past performances"
  - "simulations des performances passées"
  - "simulations are the result of estimates"
  - "do not in any case constitute a promised return"
  - "only have an indicative value"

### 5. [OK] Simulation Disclaimer Validation
- **Rule**: Future performance simulations require specific disclaimer
- **Issue Type**: `SIMULATION_MISSING_DISCLAIMER`
- **Severity**: Error
- **Validation**: Checks for simulation disclaimer phrases:
  - "simulation presented does not constitute a forecast"
  - "does not constitute a forecast of the future performance"
  - "solely designed to illustrate"
  - "value may deviate upwards or downwards"

---

## Code Implementation

### Method Added
- **Location**: `backend/extractors/agents/data_consistency_agent.py`
- **Method**: `_validate_backtest_simulation_rules()`
- **Lines**: ~120 lines of validation logic
- **Integration**: Added to Phase 3.5 in `_validate_compliance_rules()` pipeline

### Category Mapping
- **Updated**: `backend/extractors/rules/category_mapper.py`
- **Change**: Added 'backtest' and 'simulation' to performance category keywords
- **Result**: Backtest/simulation issues are categorized as "performance"

---

## Validation Flow

```
1. Extract all text from document (pages/slides)
2. Detect backtest keywords → has_backtest
3. Detect simulation keywords → has_simulation
4. Extract disclaimer text from document
5. Validate rules:
   - If backtest + retail → ERROR: BACKTEST_FOR_RETAIL
   - If backtest + no disclaimer → ERROR: BACKTEST_MISSING_DISCLAIMER
   - If simulation + no disclaimer → ERROR: SIMULATION_MISSING_DISCLAIMER
```

---

## Example Issues Generated

### Backtest for Retail
```json
{
  "issue_type": "backtest_for_retail",
  "severity": "error",
  "message": "Backtest performance should not be shown to retail clients. Backtest data is only allowed for professional clients.",
  "suggestion": "Remove backtest performance data or restrict document to professional clients only"
}
```

### Missing Backtest Disclaimer
```json
{
  "issue_type": "backtest_missing_disclaimer",
  "severity": "error",
  "message": "Backtest performance shown but required disclaimer is missing. Backtest data must include a disclaimer stating it is simulated and not a promised return.",
  "suggestion": "Add backtest disclaimer: 'The figures refer to simulations of past performances. These simulations only have an indicative value and do not in any case constitute a promised return.'"
}
```

### Missing Simulation Disclaimer
```json
{
  "issue_type": "simulation_missing_disclaimer",
  "severity": "error",
  "message": "Future performance simulation shown but required disclaimer is missing. Simulations must include a disclaimer stating they do not constitute a forecast.",
  "suggestion": "Add simulation disclaimer: 'The simulation presented does not constitute a forecast of the future performance of your investments. It is solely designed to illustrate the mechanisms of your investment over the investment period. The value of your investment may deviate upwards or downwards from what is displayed.'"
}
```

---

## Testing Checklist

- [ ] Test document with backtest data (retail) → Should flag BACKTEST_FOR_RETAIL
- [ ] Test document with backtest data (professional) → Should flag BACKTEST_MISSING_DISCLAIMER if no disclaimer
- [ ] Test document with backtest + proper disclaimer → Should pass
- [ ] Test document with simulation data → Should flag SIMULATION_MISSING_DISCLAIMER if no disclaimer
- [ ] Test document with simulation + proper disclaimer → Should pass
- [ ] Test document with both backtest and simulation → Should validate both

---

## Integration Status

[OK] **Fully Integrated**
- Method added to validation pipeline
- Category mapping updated
- Type checking passes
- Ready for testing

---

## Next Steps

According to the plan, next medium-priority features are:
1. [OK] Backtest/Simulation Rules - **COMPLETE**
2. **Securities Rules Completion** - Next
3. Fund Type Specific Rules
4. Germany-Specific Rules

---

**Status**: [OK] **READY FOR TESTING**

