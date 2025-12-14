# Quick Reference: Using Integrated Features

## [FAST] **Important: Enhanced Features Are Always On**

All enhanced features are now the **default and only implementation**. No configuration needed - just use the APIs normally and get better results automatically!

## [TARGET] When to Use What

### Use **Enhanced Text Matcher** when:
- [OK] Detecting disclaimers with variations in wording
- [OK] Need confidence scores for matches
- [OK] Want to reduce false positives
- [OK] Matching across multiple languages

### Use **Medical-Style Reports** when:
- [OK] Presenting results to stakeholders
- [OK] Need prioritized action items
- [OK] Want time/effort estimates
- [OK] Generating executive summaries

### Use **Slide Validation Rules** when:
- [OK] Validating PowerPoint presentations
- [OK] Need position-specific rules
- [OK] Checking structural consistency
- [OK] Enforcing slide-by-slide standards

---

## [START] Quick Start Examples

### Example 1: Validate Document with Enhanced Features

```python
from src.extractors.disclaimer_validator import DisclaimerValidator
from src.extractors.data_consistency_agent import DataConsistencyAgent

# 1. Setup validators (enhanced matching always enabled)
disclaimer_validator = DisclaimerValidator(
    debug_matching=False  # Set True for troubleshooting
)

data_agent = DataConsistencyAgent(
    enable_disclaimer_validation=True,
    disclaimer_validator=disclaimer_validator
)

# 2. Run validation
extraction_result = {...}  # From document_extractor.py
metadata = {...}  # Document metadata

result = data_agent.validate_document(extraction_result, metadata)

# 3. Generate medical-style report
medical_report = data_agent.generate_medical_style_report(
    result, 
    doc_type="fund_presentation"
)

# 4. Access results
print(f"Health: {medical_report['medical_diagnosis']['overall_health']}")
print(f"Severity: {medical_report['medical_diagnosis']['severity_level']}")

# 5. Get prioritized actions
for prescription in medical_report['prescriptions']:
    if prescription['priority'] == 'Critical':
        print(f"URGENT: {prescription['prescription']}")
        print(f"Time needed: {prescription['estimated_time']}")
```

### Example 2: Custom Text Matching

```python
from src.utils.text_matcher import DisclaimerTextMatcher

# Setup
matcher = DisclaimerTextMatcher(debug=False)

# Preprocess for performance (if matching same text multiple times)
matcher.preprocess_disclaimer(
    disclaimer_id="perf_disclaimer",
    disclaimer_text="Past performance is not indicative of future results"
)

# Match against document
is_found, confidence, method = matcher.match_disclaimer(
    disclaimer_id="perf_disclaimer",
    disclaimer_text="Past performance is not indicative of future results",
    document_text="The fund shows past performance...",
    strict=False
)

if is_found:
    print(f"Found with {confidence:.1%} confidence via {method}")
else:
    print(f"Not found (best score: {confidence:.1%})")
```

### Example 3: Validate Slide Structure

```python
from src.extractors.compliance_rules import SlideValidationRules

# Extract slides (from your extraction pipeline)
slides = [
    {'text': 'ODDO BHF Fund\n2024', 'slide_number': 1},
    {'text': 'Objective: Growth...', 'slide_number': 2},
    {'text': 'Performance: 10.5%', 'slide_number': 3},
]

metadata = {
    'document_type': 'fund_presentation',
    'language': 'en'
}

# Validate each slide
all_errors = []
for slide in slides:
    errors = SlideValidationRules.validate_slide_by_position(
        slide_content=slide,
        slide_num=slide['slide_number'],
        total_slides=len(slides),
        metadata=metadata
    )
    all_errors.extend(errors)

# Validate overall structure
structure_errors = SlideValidationRules.validate_structural_consistency(
    all_slides=slides,
    metadata=metadata
)
all_errors.extend(structure_errors)

# Report
print(f"Total structural issues: {len(all_errors)}")
for error in all_errors:
    print(f"- {error}")
```

---

## [FIX] Configuration Options

### DisclaimerValidator Options

```python
validator = DisclaimerValidator(
    # Path to glossary (optional)
    disclaimer_glossary_path="path/to/glossary.xlsx",
    
    # Show matching details in console (for debugging)
    debug_matching=False  # Set True for troubleshooting
)

# That's it! Multi-level matching is always enabled
```

### Text Matcher Thresholds

Edit `backend/utils/text_matcher.py` to adjust:

```python
# In EnhancedTextMatcher.match()
if similarity > 0.85:  # High similarity threshold (adjust as needed)
    return True, similarity, "high_similarity"

if sentence_ratio >= 0.6:  # Key sentences threshold (adjust as needed)
    return True, sentence_ratio, "key_sentences"

if keyword_ratio >= 0.5:  # Keywords threshold (adjust as needed)
    return True, keyword_ratio, "keywords_match"
```

### Medical Report Scoring

Edit `backend/utils/medical_recommendations.py` to adjust:

```python
# In MedicalRecommendationEngine.classify_severity()
if incorrect_count > 0 or score < 50:  # Adjust thresholds
    return ComplianceSeverity.CRITICAL
elif score < 70 or missing_count > 3:
    return ComplianceSeverity.HIGH
```

---

## [CHART] Understanding Match Results

### Match Methods Explained

| Method | Confidence | Description | Use Case |
|--------|-----------|-------------|----------|
| `exact_match` | 100% | Exact text found in document | Best case |
| `high_similarity` | 85-99% | Very similar text via SequenceMatcher | Minor variations |
| `key_sentences` | 60-84% | Most sentence fragments present | Rephrased content |
| `keywords_match` | 50-59% | Many keywords match | Summarized content |
| `no_match` | 0-49% | No significant match | Missing content |

### Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| `Critical` | Regulatory violations, incorrect content | Immediate action |
| `High` | Missing required content, structural errors | Action within 48h |
| `Medium` | Minor missing items, warnings | Action within 1 week |
| `Low` | Recommendations, best practices | Optional improvement |

### Health Status

| Status | Score Range | Description |
|--------|------------|-------------|
| `Excellent` | 95-100 | Fully compliant |
| `Good` | 85-94 | Minor issues only |
| `Moderate` | 70-84 | Some corrections needed |
| `Poor` | 50-69 | Significant issues |
| `Critical` | 0-49 | Major revision required |

---

##  Debugging Tips

### Problem: False Positives (Text Matcher)

**Solution**: Use strict mode
```python
is_match, confidence, method = matcher.match(
    required_text="...",
    target_text="...",
    strict_mode=True  # Requires >85% confidence
)
```

### Problem: False Negatives (Text Matcher)

**Solution**: Enable debug mode to see why it's not matching
```python
matcher = EnhancedTextMatcher(debug=True)
# Will print matching process details
```

### Problem: No Medical Report Generated

**Check**:
1. Is `MEDICAL_RECOMMENDATIONS_AVAILABLE` True?
2. Is `generate_medical_style_report()` returning None?
3. Check imports in `data_consistency_agent.py`

```python
# Test import
try:
    from src.utils.medical_recommendations import MedicalRecommendationEngine
    print("[OK] Medical engine available")
except ImportError as e:
    print(f"[FAIL] Medical engine not available: {e}")
```

### Problem: Slide Validation Too Strict/Lenient

**Adjust thresholds** in `compliance_rules.py`:
```python
class SlideValidationRules:
    # Adjust these as needed
    MIN_TEXT_LENGTH_COVER = 50  # chars
    MIN_TEXT_LENGTH_CONTENT = 100  # chars
    MIN_TEXT_LENGTH_PERFORMANCE = 150  # chars
```

---

## [IDEA] Best Practices

### 1. **Multi-Level Matching Is Always On**
```python
# [OK] Good - Just use it normally
validator = DisclaimerValidator()

# [FAIL] No longer exists
validator = DisclaimerValidator(use_enhanced_matching=True)  # This parameter is gone
```

### 2. **Cache Preprocessed Disclaimers for Performance**
```python
matcher = DisclaimerTextMatcher()

# Preprocess once
for disclaimer_id, text in disclaimers.items():
    matcher.preprocess_disclaimer(disclaimer_id, text)

# Match many times (uses cache)
for document in documents:
    matcher.match_disclaimer(disclaimer_id, text, document)
```

### 3. **Generate Medical Reports for Stakeholders**
```python
# [OK] Good for presentations
medical_report = agent.generate_medical_style_report(result)
present_to_stakeholders(medical_report)

# [FAIL] Too technical for stakeholders
present_to_stakeholders(result.compliance_issues)
```

### 4. **Use Slide Rules Position-Aware**
```python
# [OK] Good - validates based on position
for i, slide in enumerate(slides, 1):
    errors = SlideValidationRules.validate_slide_by_position(
        slide, i, len(slides), metadata
    )

# [FAIL] Less accurate - same rules for all
for slide in slides:
    errors = generic_validation(slide)
```

---

## [UP] Performance Tips

1. **Preprocess disclaimers once**: Use `preprocess_disclaimer()` for repeated matching
2. **Batch validation**: Validate all slides at once instead of one-by-one
3. **Disable debug mode**: Only enable `debug=True` when troubleshooting
4. **Clear cache**: Call `matcher.clear_cache()` after processing many documents

---

##  Related Documentation

- [Full Integration Summary](INTEGRATION_SUMMARY.md) - Detailed overview
- [API Documentation](API_DOCUMENTATION.md) - Complete API reference
- [Test Examples](../tests/test_integrated_features.py) - Working code examples

---

## 🆘 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Import errors | Check Python path includes `backend/` |
| Low match confidence | Adjust thresholds in `text_matcher.py` |
| Too many false positives | Use `strict_mode=True` in custom matching |
| Medical report None | Check imports and dependencies |
| Slide validation errors | Adjust min/max length constants |
| Different results than before | Expected - new matching is more accurate |

---

**Last Updated**: December 8, 2025  
**Integration Version**: 2.0 (Enhanced features only)
