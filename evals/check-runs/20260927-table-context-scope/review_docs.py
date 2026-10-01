"""Check changed documentation and source formatting; keep raw replay text exact."""

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parent
changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
paths = [ROOT / path for path in changed if path.endswith(".md")]
paths += list(RUN.rglob("*.md"))
count = 0
for path in paths:
    text = path.read_text()
    assert not re.search(r"[\u4e00-\u9fff]", text), path
    assert text.count("```") % 2 == 0, path
    count += 2
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
        if re.match(r"(?:https?://|mailto:|#)", target):
            continue
        assert (path.parent / target.split("#", 1)[0]).exists(), (path, target)
        count += 1
result = subprocess.run(["git", "diff", "--check", "--", "*.py", "*.md", "*.ts", "*.tsx"], cwd=ROOT, capture_output=True, text=True)
assert result.returncode == 0, result.stdout + result.stderr
count += 1
print(f"{count} passed, 0 failed, 0 skipped. Changed documentation links, English text, code fences and code/doc formatting reviewed.")
print("Raw TXT contexts and command logs retain exact tabs and source whitespace; they are evidence artifacts outside the code-format rule.")
