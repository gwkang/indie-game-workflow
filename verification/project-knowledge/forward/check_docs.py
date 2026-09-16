from pathlib import Path
import re
root=Path(__file__).parent
for p in (root/'comet-wiki').glob('*.md'):
    for target in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', p.read_text(encoding='utf-8')):
        assert (p.parent/target).is_file(), (p, target)
print('PASS: local wiki links resolve')
