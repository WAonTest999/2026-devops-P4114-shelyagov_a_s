"""Update Helm image tags after a successful CI publish."""
import re
import sys
from pathlib import Path

tag = sys.argv[1]
if not re.fullmatch(r'[0-9a-f]{40}', tag):
    raise SystemExit('Expected a full 40-character Git commit SHA')
path = Path('deploy/school/values.yaml')
content, count = re.subn(r'(?m)^  tag: .+$', f'  tag: {tag}', path.read_text(encoding='utf-8'))
if count != 2:
    raise SystemExit(f'Expected exactly two image tags, found {count}')
path.write_text(content, encoding='utf-8')
