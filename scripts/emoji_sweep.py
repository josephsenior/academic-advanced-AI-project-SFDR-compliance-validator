import os
import re
from pathlib import Path

# Files/dirs to skip
SKIP_DIRS = {'.git', 'node_modules', 'compliance-dashboard/node_modules', 'compliance-dashboard/.next', '.venv', '__pycache__'}
SKIP_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.woff2', '.woff', '.ttf', '.ico', '.bin', '.exe', '.dll', '.so', '.zip', '.tar', '.gz', '.pdf'}

# Emoji replacements mapping
REPLACEMENTS = {
    '[OK]': '[OK]', '[FAIL]': '[FAIL]', '[WARNING]': '[WARNING]', '[WARNING]': '[WARNING]', '[TARGET]': '[TARGET]', '[CHART]': '[CHART]',
    '[SEARCH]': '[SEARCH]', '[NEW]': '[NEW]', '[START]': '[START]', '[IDEA]': '[IDEA]', '[NOTE]': '[NOTE]', '[DESIGN]': '[DESIGN]',
    '[FIX]': '[FIX]', '[TIME]': '[TIME]', '[UP]': '[UP]', '[WIN]': '[WIN]', '[STRONG]': '[STRONG]', '[HOT]': '[HOT]',
    '[GOOD]': '[GOOD]', '[BAD]': '[BAD]', '[STAR]': '[STAR]', '[STAR]': '[STAR]', '[OK]': '[OK]', '[LOVE]': '[LOVE]',
    '[WARN]': '[WARN]', '[TEST]': '[TEST]', '[SUCCESS]': '[SUCCESS]', '[PACKAGE]': '[PACKAGE]', '[LOCKED]': '[LOCKED]', '[UNLOCKED]': '[UNLOCKED]',
    '[FAST]': '[FAST]', '[COLOR]': '[COLOR]', '[MASK]': '[MASK]', '[BUILD]': '[BUILD]', '[TOOL]': '[TOOL]', '[PIN]': '[PIN]',
    '[ACTION]': '[ACTION]', '[LIST]': '[LIST]', '[DOC]': '[DOC]', '[FOLDER]': '[FOLDER]', '[IMAGE]': '[IMAGE]', '[AI]': '[AI]',
    '[GREEN]': '[GREEN]', '[YELLOW]': '[YELLOW]', '[ORANGE]': '[ORANGE]', '[WHITE]': '[WHITE]', '[RED]': '[RED]', '[SAVE]': '[SAVE]',
    '->': '->', '[NO]': '[NO]', '[BOOK]': '[BOOK]', '[RED]': '[RED]'
}

# Broad unicode ranges for many emojis to remove any missed symbols
EMOJI_REGEX = re.compile('[\U0001F300-\U0001F9FF\U00002600-\U000026FF\U00002700-\U000027BF]')

root = Path(__file__).resolve().parents[1]
modified_files = []
total_replacements = 0

for dirpath, dirnames, filenames in os.walk(root):
    # skip directories
    parts = Path(dirpath).parts
    if any(p in SKIP_DIRS for p in parts):
        continue
    for fname in filenames:
        fpath = Path(dirpath) / fname
        if fpath.suffix.lower() in SKIP_EXT:
            continue
        # try reading as text
        try:
            text = fpath.read_text(encoding='utf-8')
        except Exception:
            try:
                text = fpath.read_text(encoding='latin-1')
            except Exception:
                continue
        new_text = text
        # direct replacements
        for em, rep in REPLACEMENTS.items():
            if em in new_text:
                new_text = new_text.replace(em, rep)
        # regex remove other emoji ranges
        new_text, n = EMOJI_REGEX.subn('', new_text)
        if new_text != text:
            try:
                fpath.write_text(new_text, encoding='utf-8')
                modified_files.append(str(fpath.relative_to(root)))
                total_replacements += 1
            except Exception as e:
                print(f"[WARN] Could not write {fpath}: {e}")

print(f"Done. Modified {len(modified_files)} files. (counted replacements: {total_replacements})")
for p in modified_files:
    print(p)
