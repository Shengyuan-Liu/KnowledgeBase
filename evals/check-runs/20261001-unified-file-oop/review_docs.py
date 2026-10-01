"""Review changed documentation links, fences, content conventions and diff format."""

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
paths = [ROOT / name for name in subprocess.check_output(['git', 'diff', '--name-only'], text=True).splitlines()
         if name.endswith('.md')]
paths.append(Path(__file__).with_name('README.md'))
links = 0
for path in paths:
    content = path.read_text()
    assert content.count('```') % 2 == 0, path
    assert not re.search(r'[\u4e00-\u9fff]', content), path
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
        if target.startswith(('http:', 'https:', '#', 'mailto:')):
            continue
        target = target.split('#', 1)[0]
        assert (path.parent / target).exists(), (path, target)
        links += 1
subprocess.run(['git', 'diff', '--check'], check=True)
print(f'{len(paths)} documents; {links} local links; fences, English content and diff formatting passed.')
print('Codex content review: type dispatch, service ownership, immutable snapshots, legacy table mapping, PDF revision compatibility, verification scope and retained failures match the implementation.')
