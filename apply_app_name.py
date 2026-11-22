#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "src")
res = root / "app" / "src" / "main" / "res"

if not res.is_dir():
    raise SystemExit(f"Resources folder not found: {res}")

updated = []

for path in res.glob("values*/strings.xml"):
    text = path.read_text(encoding="utf-8")

    new = re.sub(
        r'(<string\s+name="app_name"[^>]*>).*?(</string>)',
        r'\1StreamVerse\2',
        text,
        flags=re.DOTALL
    )

    new = re.sub(
        r'(<string\s+name="play_with_app_name"[^>]*>).*?(</string>)',
        r'\1Play with StreamVerse\2',
        new,
        flags=re.DOTALL
    )

    if new != text:
        path.write_text(new, encoding="utf-8")
        updated.append(str(path))

if not updated:
    raise SystemExit("No app_name string found. Check source files.")

print("StreamVerse name updated in:")
for item in updated:
    print(item)
