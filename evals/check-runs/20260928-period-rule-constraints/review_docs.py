"""Review scoped documentation and preserve raw evaluation artifacts."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
paths = [ROOT / "README.md", Path("docs/v2/README.md"), Path("docs/planned-retrieval.md"),
         Path("docs/dependent-retrieval.md"), Path("docs/evidence-sufficiency.md")]
links = 0
for path in paths:
    text = path.read_text()
    assert not re.search(r"[\u4e00-\u9fff]", text)
    assert text.count("\n```") % 2 == 0
    assert all(line == line.rstrip() for line in text.splitlines())
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if link.startswith("http"):
            continue
        target = (path.parent / link.split("#", 1)[0]).resolve()
        if target == ROOT / "documentation-1.json":
            continue  # The wrapper writes this self-record after completion.
        assert target.exists(), (path, link)
        links += 1
subprocess.run(["git", "diff", "--check", "--", "knowledgebase", "tests", "docs"], check=True)
for path in [*ROOT.glob("*.py"), Path("tests/test_period_rule_constraints.py")]:
    assert all(line == line.rstrip() for line in path.read_text().splitlines())
print(f"Reviewed five English documents and {links} existing local links; wrapper writes one self-record link.")
print("Content review preserves prior failures, rejection/error risk, annotated replay limits and unverified live period/column semantics; no quality or merge claim.")
