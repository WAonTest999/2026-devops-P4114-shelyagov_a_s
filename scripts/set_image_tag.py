"""Only change the two image tags in the GitOps manifest."""
import re
import sys
from pathlib import Path

tag = sys.argv[1]
if not re.fullmatch(r'[0-9a-f]{40}', tag):
    raise SystemExit('Expected a full 40-character Git commit SHA')
path = Path('deploy/app/kustomization.yaml')
content, count = re.subn(r'(?m)^(    newTag: ).+$', rf'\g<1>{tag}', path.read_text())
if count != 2:
    raise SystemExit('Expected exactly two images')
path.write_text(content, encoding='utf-8')
