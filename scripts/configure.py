"""Run once from repository root: python scripts/configure.py --owner NAME --repo REPO --domain example.org --email you@example.org"""
import argparse
import re
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
for name in ('owner', 'repo', 'domain', 'email'):
    p.add_argument('--' + name, required=True)
a = p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_-]+', a.owner) or not re.fullmatch(r'[A-Za-z0-9_.-]+', a.repo):
    p.error('Invalid GitHub owner or repository')
if not re.fullmatch(r'[A-Za-z0-9.-]+\.[A-Za-z]{2,}', a.domain) or not re.fullmatch(r'[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+', a.email):
    p.error('Provide a domain without https:// and a valid email')
replacements = {'CHANGE_ME_OWNER': a.owner, 'CHANGE_ME_REPO': a.repo, 'CHANGE_ME_EMAIL': a.email, 'ghcr.io/CHANGE_ME/': f'ghcr.io/{a.owner.lower()}/', 'CHANGE_ME': a.domain.lower()}
for path in Path('deploy').rglob('*.yaml'):
    content = path.read_text(encoding='utf-8')
    for old, new in replacements.items():
        content = content.replace(old, new)
    path.write_text(content, encoding='utf-8')
print('Deployment placeholders replaced. Review git diff before committing.')
