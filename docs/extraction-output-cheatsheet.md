# Extraction Output Cheat Sheet

All fields below are emitted by `ExtractionPipeline` and saved under `outputs/<document_id>/metadata.json`, `extraction.json`, and the manifest/index. This doc maps each feature to downstream compliance modules so teammates know why the signal exists.

## Title & Document Facts

| Field | Description | Downstream Usage |
|-------|-------------|------------------|
| `metadata.title_information` | Fund name, currency, client type, document date, SRRI, management company from the title slide. | Document Structure agent confirms required items; Disclaimer module picks base legal text; Registration module links to fund records. |
| `metadata.is_new_product`, `is_new_strategy`, `is_professional_client`, `is_sicav_product` | Flags propagated from `metadata.json`. | Registration agent skips new products; Disclaimer engine selects professional vs retail wording; ESG/Structure modules apply conditional rules. |

## Identifiers & Issuers

| Field | Description | Usage |
|-------|-------------|-------|
| `metadata.identifiers` | ISINs/share classes with slide/page references. | Registration module cross-references the Excel registration sheet. |
| `metadata.issuer_mentions` | Extracted company names (e.g., top holdings) with context. | Disclaimer engine enforces “Issuers mentioned” text; ESG agent audits issuer references. |

## Disclaimers

| Field | Description | Usage |
|-------|-------------|-------|
| `slide/paragraph/page_summaries[].disclaimer_categories` | Keyword-driven tags: performance, ESG risk, backtest, simulation, etc. | Unified compliance engine knows which rules apply per section. |
| `metadata.disclaimer_glossary_matches` | Each detected disclaimer resolved to official text (language + client type) from `backend/extractors/data/disclaimer_glossary.json`. | Rule engine simply checks mandatory entry presence, no fuzzy matching. |

## Performance Insight

| Field | Description | Usage |
|-------|-------------|-------|
| `performance_sections[].entries` | For each sentence: basis (net/gross/backtest), period (1Y, YTD), benchmark, numeric value. | Data Consistency comparisons; performance disclaimer triggers. |
| `performance_table_entries` | Normalized rows from tables (label, column, numeric value, location). | Numerical checks against prospectus/KID data without re-parsing tables. |

## Countries & Registration

| Field | Description | Usage |
|-------|-------------|-------|
| `country_entries` | Each country mention with heading (“Distribution”, “Registered in…”) and snippet. | Registration agent verifies availability claims vs registration spreadsheet. |

## Document Structure Flags

| Field | Description | Usage |
|-------|-------------|-------|
| `structure.title_slide` | Slide/page index considered the title. | Document Structure agent enforces front-matter rules. |
| `structure.disclaimer_slides`, `performance_slides`, `glossary_slides` | Slide indices grouped by content type. | Ensures performance isn’t on slide 1, glossary/legal notices appear where required. |
| `structure.has_glossary`, `structure.has_management_notice`, `structure.legal_notice_slide` | Boolean + location for mandatory closing sections. | Retail presentations must end with legal notice; quickly verifiable. |

## Table Sources

| Field | Description | Usage |
|-------|-------------|-------|
| `table_sources` | Snippets containing “Source/Date” (parsed into `source_name`/`source_date`). | Data Consistency agent verifies every chart/table cites source + date. |

## Language & OCR

| Field | Description | Usage |
|-------|-------------|-------|
| `slide/page/paragraph_summaries[].language` | Section-level language when `langdetect` is available. | Selects correct disclaimer language and rule set. |
| Validation warnings (short text, table mismatch, PII) | Raised during `_validate_extraction`. | Alerts reviewers that OCR or content may require manual attention. |

## Integrity & Cache

| Field | Description | Usage |
|-------|-------------|-------|
| `metadata.file_checksum`, `manifest.file_checksum` | SHA-256 fingerprint for deterministic reprocessing. | Prevents drift and redundant OCR runs. |
| Cache reuse (`status: "skipped"`) | Pipeline reuses existing output if checksum already indexed. | Saves time/cost and guarantees consistency. |

## Golden Regression Fixtures

- Located in `tests/golden/` with `tests/test_pipeline_golden.py`.
- Simulates a document to guarantee pipeline outputs stay stable when heuristics change.
- Update fixtures deliberately if the schema evolves; they act as a safety net before compliance agents rely on new signals.

---

If a new compliance rule needs additional signals, add a helper in `DocumentExtractor`, document the rationale, and extend the regression tests. This keeps the extraction layer deterministic, auditable, and ready for the downstream modules outlined in Consignes.
