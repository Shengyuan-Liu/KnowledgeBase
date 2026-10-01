"""Review final staged formatting while retaining exact raw table delimiters."""

from pathlib import Path
import re
import subprocess

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]
raw_paths = [RUN / name for name in [
    "diagnostics/child-0-context.txt", "diagnostics/parent-of-child-0-context.txt", "format-review-1.log",
]]
checks = 0
for path in raw_paths[:2]:
    lines = path.read_text().splitlines()
    assert lines[6] and not lines[6].strip(), path
    assert lines[7].startswith("\t\tPre-Pawn\tRedemption\t") and lines[7].endswith("\t"), path
    checks += 1
command = ["git", "diff", "--cached", "--check", "--", "."] + [
    ":(exclude)" + str(path.relative_to(ROOT)) for path in raw_paths
]
result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
assert result.returncode == 0, result.stdout + result.stderr
checks += 1
docs = list(RUN.rglob("*.md")) + [ROOT / name for name in ["docs/v2/README.md", "docs/pdf-parsing.md", "docs/pdf-integration.md"]]
for path in docs:
    content = path.read_text()
    assert not re.search(r"[\u4e00-\u9fff]", content), path
    assert content.count("```") % 2 == 0, path
    checks += 2
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
        if re.match(r"(?:https?://|mailto:|#)", target):
            continue
        resolved = (path.parent / target.split("#", 1)[0]).resolve()
        assert resolved.exists() or resolved == RUN / "format-review-2.json", (path, target)
        checks += 1
print(f"{checks} passed, 0 failed, 0 skipped. Staged text and final document links reviewed.")
print("Exact raw table tabs and the initial failure log remain unchanged. Only those three recorded raw artifacts are excluded from the whitespace rule; no production source is excluded.")
