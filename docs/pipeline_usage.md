# Extraction Pipeline Usage Guide

> Current pipeline schema version: **0.3.0**

## Overview

The extraction pipeline orchestrates all document extraction modules to:
1. Extract metadata (from JSON + filename)
2. Optionally detect document family (in-memory grouping)
3. Extract document content (text/tables)
4. Extract features using LLM (ESG, performance, countries, etc.)
5. Aggregate results in-memory for the session

## Quick Start

### Basic Usage

```python
from src.extractors.pipeline import process_document

# Process a document
result = process_document(
    file_path="dataset/example_1/document.pptx",
    metadata_json_path="dataset/example_1/metadata.json",  # Optional
    uploaded_by="user123",  # Optional
    use_llm=True  # Set to False to skip LLM feature extraction
)

# Check results
print(f"Status: {result['status']}")
print(f"Document ID: {result.get('document_id')}")
print(f"Steps completed: {result.get('steps_completed')}")
```

### Using the Pipeline Class

```python
from src.extractors.pipeline import ExtractionPipeline

# Create pipeline
pipeline = ExtractionPipeline(use_llm=True)

# Process document
result = pipeline.process_document(
    file_path="path/to/document.pptx",
    metadata_json_path="path/to/metadata.json",
    uploaded_by="user123"
)

# Access results
if result['status'] == 'success':
    document_id = result['document_id']
    extraction_id = result['extraction_id']
    features = result.get('features', {})
    
    print(f"✅ Document processed successfully!")
    print(f"   ESG mentions: {features.get('esg_mentions', 0)}")
    print(f"   Performance data: {features.get('performance_data', 0)}")
    print(f"   Country mentions: {features.get('country_mentions', 0)}")
else:
    print(f"❌ Processing failed:")
    for error in result.get('errors', []):
        print(f"   - {error}")
```

## Command Line Usage

```bash
# Process a single document
python -m src.extractors.pipeline "path/to/document.pptx" "path/to/metadata.json"

# Process without LLM (faster, no feature extraction)
python -m src.extractors.pipeline "path/to/document.pptx" --no-llm
```

## Pipeline Steps

The pipeline executes these steps in order:

1. **Metadata Extraction** - Extracts metadata from JSON file and filename
2. **Family Detection (In-Memory)** - Attempts to group documents during the session (skipped by default)
3. **Document Record Creation** - Generates an in-memory identifier for the processed document
4. **Content Extraction** - Extracts text and tables from the document
5. **Feature Extraction** - Uses LLM to extract compliance features (if enabled)
6. **Finalization** - Returns the aggregated results to the caller

## Result Structure

```python
{
    'document_id': 'uuid-string',
    'extraction_id': 'uuid-string',
    'family_id': 'uuid-string',
    'status': 'success' | 'error',
    'steps_completed': ['metadata_extraction', 'family_detection', ...],
    'errors': [],  # List of errors
    'warnings': [],  # List of warnings
    'metadata': {...},  # Extracted metadata
    'extraction_result': {...},  # Document content
    'features': {  # If LLM enabled
        'esg_mentions': 5,
        'performance_data': 3,
        'country_mentions': 8,
        'company_mentions': 12,
        'financial_terms': 2
    }
}
```

## Error Handling

The pipeline handles errors gracefully:
- **Errors**: Critical failures that stop processing (e.g., unreadable source file)
- **Warnings**: Non-critical issues (e.g., LLM feature extraction failed, but document extracted)

```python
result = process_document("document.pptx")

if result['status'] == 'error':
    print("Critical errors:")
    for error in result['errors']:
        print(f"  ❌ {error}")

if result.get('warnings'):
    print("Warnings:")
    for warning in result['warnings']:
        print(f"  ⚠️  {warning}")
```

## Processing Multiple Documents

```python
from src.extractors.pipeline import ExtractionPipeline
from pathlib import Path

pipeline = ExtractionPipeline(use_llm=True)

# Process all documents in a directory
documents_dir = Path("dataset")
for doc_file in documents_dir.rglob("*.pptx"):
    metadata_file = doc_file.parent / "metadata.json"
    
    print(f"\nProcessing: {doc_file.name}")
    result = pipeline.process_document(
        file_path=str(doc_file),
        metadata_json_path=str(metadata_file) if metadata_file.exists() else None
    )
    
    if result['status'] == 'success':
        print(f"  ✅ Success: {result['document_id']}")
    else:
        print(f"  ❌ Failed: {result.get('errors', [])}")
```

## Configuration

### Environment Variables

Make sure your `.env` file exposes the LLM credentials needed for feature extraction:

```env
# Hugging Face or Token Factory credentials (example)
HUGGINGFACE_API_KEY=hf_your_key_here
LLM_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
TOKEN_FACTORY_API_KEY=your_token_factory_key
TOKEN_FACTORY_BASE_URL=https://tokenfactory.esprit.tn/api
```

All extracted data is written to JSON artifacts; no database configuration is required.

### Output Structure

Each processed document is saved under `outputs/<document_id>/` (override with `PIPELINE_OUTPUT_DIR`). The folder contains:

- `metadata.json` – Full metadata inferred from filename/JSON
- `extraction.json` – OCR/text/tables plus structural metadata (`slide_summaries`, `performance_sections`, `table_sources`, etc.)
- `features.json` – Present only when LLM feature extraction is enabled
- `manifest.json` – Summary with timestamps, counts, and relative paths
- `executive_summary` – Included in the manifest and index to highlight key stats and warnings
- `file_checksum` – SHA-256 fingerprint of the source document to guarantee deterministic reprocessing

A global index at `outputs/index.jsonl` maintains one JSON object per document, enabling quick queries in DuckDB/pandas by loading the JSONL file.

**Why heuristics instead of ML models?**

The extractor intentionally uses transparent keyword/regex rules to label
slides/paragraphs (disclaimer locations, performance statements, glossary
slides, country mentions).  This keeps runtime low and makes the signals easy to
audit against *Consignes.pdf*.  If a rule produces false positives you can see
the exact text snippet and adjust the keyword list – no need to retrain a model
for every policy tweak.

### Key Metadata Fields

- `slide_summaries` / `page_summaries` / `paragraph_summaries`: flag whether a
  section contains disclaimers, performance data, glossary content, and the
  countries mentioned.  The Disclaimer, ESG, Registration, and Structure agents
  can read these booleans instead of re-parsing raw text.
- `performance_sections`: captures the exact sentences containing percentage
  figures so performance placement rules can reference them with slide numbers.
- `performance_table_entries`: normalized key/value rows extracted from tables
  (label, column, numeric value) to support numeric consistency checks.
- `table_sources`: records snippets containing “source”/“date” near tables to
  accelerate Data Consistency checks.
- `structure`: aggregates high-level cues (title slide, disclaimer slides,
  glossary slides, countries detected) for quick assertions in unit tests or in
  the upcoming document-structure agent.
- `structure.disclaimer_categories`: keyword-based mapping of each section’s
  disclaimer to glossary categories (performance, ESG risk, backtest, etc.),
  enabling deterministic rule checks.
- `language`: detected per section when `langdetect` is available.  Multilingual
  decks are common; storing the language allows later modules to pick the right
  rule set without running detection again.
- `identifiers`: list of ISINs/share-class codes with location context, ready to
  join with the registration Excel sheet.
- `issuer_mentions`: captures holdings/issuers (linked to Glossaire disclaimers)
  so the “Issuers mentioned” rule can run deterministically.
- `country_entries`: each country mention is stored with the surrounding
  heading/sentence, helping distinguish “Distribution list” from casual mention.
- `metadata_flags`: surfaced in the manifest (`is_new_product`, `is_new_strategy`,
  `is_professional_client`, `is_sicav_product`) so downstream modules can apply
  the conditional logic described in Consignes without reopening metadata.json.
- `title_information`: fund name, currency, document date, client type, and risk
  indicator extracted from the opening slide for quick checks.
- `disclaimer_glossary_matches`: each detected disclaimer is linked to the
  reference text in `dataset/GLOSSAIRE DISCLAIMER…xlsx` (via
  `src/extractors/data/disclaimer_glossary.json`) using language and client type
  so the rule engine can check mandatory statements without fuzzy matching.
- `structure.has_glossary` / `structure.has_management_notice`: quick flags to
  confirm that retail presentations end with the required glossary and legal
  notice about the management company.

### Cache & Integrity Behavior

- Before extraction the pipeline computes a SHA-256 hash of the document.  If an
  identical checksum already exists in `index.jsonl`, the previously generated
  manifest is reused and the pipeline warns with `status="skipped"`.  This keeps
  results consistent across runs and avoids unnecessary OCR churn.
- Every manifest entry contains the checksum and relative file paths so audits
  can prove the JSON bundle corresponds to the exact input.

### Automatic Warnings

- `_validate_extraction` now alerts when the output text is very short, when
  table counts disagree, or when potential PII (emails/phone numbers) appears in
  the extracted text.  These are early indicators that human review is required.

### OCR Dependencies

The extractor now relies on Tesseract OCR with `pdf2image` for PDF processing. Install the Tesseract engine separately (for Windows download the official installer) and set the path if it is not on your `PATH`:

```env
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe
TESSERACT_LANG=eng+fra      # optional: list of languages to load
TESSERACT_CONFIG=--psm 6    # optional: override Tesseract OCR config
```

Ensure `poppler` is also installed so `pdf2image` can render PDF pages (on Windows, add the `bin` directory of Poppler to `PATH`).

Optional but recommended:

- Install `langdetect` to populate section-level language codes.  Without it the
  fields remain `null`, but the schema still validates.

### LLM Feature Extraction

- **Enabled by default**: Set `use_llm=True` to extract features (ESG, performance, etc.)
- **Disabled**: Set `use_llm=False` to skip LLM processing (faster, no features)

### Chunking for Large Documents

For large documents, the pipeline automatically chunks text for LLM processing:

```python
pipeline = ExtractionPipeline(use_llm=True)
result = pipeline.process_document(
    file_path="large_document.pdf",
    chunk_size=10000  # Default: 10000 characters per chunk
)
```

## Data Persistence

- **Per-document artifacts** are JSON files as described above.
- **Global manifest** (`outputs/index.jsonl`) aggregates key fields for analytics. Load it via DuckDB:

```sql
CREATE TABLE documents AS
  SELECT * FROM read_json_auto('outputs/index.jsonl');
```

If you need Parquet/CSV for BI tools, load the JSONL into pandas and export.

## Troubleshooting

### LLM Feature Extraction Failed
- Check Hugging Face API key in `.env`
- Verify model name is correct
- Check API quota/limits
- Pipeline will continue without features (warning only)

### Metadata Not Found
- Pipeline will use basic metadata from filename
- Check if `metadata.json` file exists
- Verify JSON file format

## Performance Tips

1. **Disable LLM for bulk processing**: Set `use_llm=False` for faster processing
2. **Process in batches**: Process documents in smaller batches
3. **Chunk size**: Adjust `chunk_size` based on document size and LLM token limits
4. **Index refresh**: Re-run the pipeline on the same document to refresh the JSON bundle and the global index entry.
5. **Version awareness**: Check the `pipeline_version` value in manifests/index entries before comparing runs processed at different times.

