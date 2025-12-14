# Next Steps According to Plan

**Current Status**: [OK] **ALL MEDIUM PRIORITY FEATURES COMPLETE**  
**Next Phase**: [GREEN] **VERIFICATION & REFINEMENT**

---

## [OK] Completed (High Priority)

1. [OK] **Cover Page Complete Validation** - DONE
2. [OK] **Performance Rules Completion** - DONE
3. [OK] **Prospectus Integration** - DONE
4. [WARNING] **Visual Formatting** - Deferred (requires OCR/vision infrastructure)

---

## [OK] Completed (Medium Priority)

### 5. **Securities Rules Completion** (Priority: MEDIUM)

**Status**: [OK] **Implemented**

**Implemented Validations**:
- [OK] `SECURITY_VALUATION_MENTION` - Validate security valuation mentions
- [OK] `SECURITIES_COMPARISON` - Validate securities comparison rules
- [OK] `MULTIPLE_SECURITY_MENTIONS` - Validate multiple security mentions
- [OK] `SECURITY_PROJECTION` - Validate security projection rules
- [OK] `BUY_SELL_RECOMMENDATION` - Validate buy/sell recommendation rules

---

### 6. **Fund Type Specific Rules** (Priority: MEDIUM)

**Status**: [OK] **Implemented**

**Implemented Validations**:

#### Dated Funds:
- [OK] `YTM_FOR_ACTIVE_RETAIL` - YTM should not be shown for active dated funds to retail
- [OK] `YTW_FOR_ACTIVE_RETAIL` - YTW should not be shown for active dated funds to retail

#### Private Equity:
- [OK] `NET_IRR_FOR_RETAIL` - Net IRR should not be shown to retail clients
- [OK] `INSTITUTIONAL_TRACK_FOR_RETAIL` - Institutional track record should not be shown to retail

#### ETF:
- [OK] `ETF_CALLED_LIQUID` - ETF should not be called "liquid"

#### Money Market:
- [OK] Money Market specific rules (Disclaimer)

#### RAIF:
- [OK] RAIF specific rules (Target Audience & Disclaimer)

---

### 7. **Germany-Specific Rules** (Priority: MEDIUM)

**Status**: [OK] **Implemented**

**Implemented Validations**:
- [OK] `GERMANY_MISSING_SUBSCRIPTION_FEE` / `MISSING_UNKNOWN_NAV_DISCLAIMER` - Fee validation via disclaimer check
- [OK] `NAV_FORMAT_ISSUE` - NAV labeling validation (text-based alternative to graph check)
- [OK] `MISSING_GERMAN_SPECIFIC_DISCLAIMER` - German specific disclaimer validation

---

### 8. **Backtest/Simulation Rules** (Priority: MEDIUM)

**Status**: [OK] **Implemented**

**Implemented Validations**:
- [OK] `BACKTEST_FOR_RETAIL` - Backtest performance should not be shown to retail
- [OK] `BACKTEST_MISSING_DISCLAIMER` - Backtest requires specific disclaimer
- [OK] `SIMULATION_MISSING_DISCLAIMER` - Simulation requires specific disclaimer

---

## [START] Next Steps: Verification & Refinement

All planned features defined in the Medium Priority phase have been implemented. The next logical steps are:

1. **Systematic Testing**: Run the validator against a diverse dataset to tune thresholds and keywords.
2. **False Positive Reduction**: Refine rules based on real-world results.
3. **Frontend Integration**: Ensure all new issue types are correctly displayed in the UI.
