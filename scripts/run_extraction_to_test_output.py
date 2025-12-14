import os
import json
from pathlib import Path

from backend.extractors.core.document_extractor import DocumentExtractor


def main():
    workspace = Path(__file__).resolve().parent.parent
    dataset_dir = workspace / 'dataset'
    output_dir = workspace / 'test_output'
    output_dir.mkdir(parents=True, exist_ok=True)

    extractor = DocumentExtractor()

    # Walk example directories
    example_dirs = [d for d in (dataset_dir).iterdir() if d.is_dir()]

    supported_exts = {'.pptx', '.docx', '.pdf'}

    processed = 0
    errors = 0

    for ex in example_dirs:
        for file in ex.glob('**/*'):
            if file.suffix.lower() in supported_exts:
                print(f"Processing {file}...")
                try:
                    result = extractor.extract(str(file))
                except Exception as e:
                    errors += 1
                    result = {'error': str(e)}

                out_path = output_dir / (file.stem + '.json')
                # Ensure JSON serializable: convert Paths
                def make_serializable(obj):
                    if isinstance(obj, Path):
                        return str(obj)
                    return obj

                try:
                    with open(out_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, default=make_serializable, ensure_ascii=False, indent=2)
                    processed += 1
                except Exception as e:
                    print(f"Failed to write output for {file}: {e}")
                    errors += 1

    print('\nDone.')
    print(f'Processed: {processed}, Errors: {errors}')


if __name__ == '__main__':
    main()
