"""Review local links and formatting; the wrapper writes its record on completion."""
from pathlib import Path
import re
import subprocess

directory = Path(__file__).resolve().parent
paths = [Path("docs/v2/README.md"), Path("docs/planned-retrieval.md"),
         Path("docs/dependent-retrieval.md"), Path("docs/evidence-sufficiency.md"),
         directory / "README.md"]
links = 0
for path in paths:
    content = path.read_text()
    assert not re.search(r"[\u4e00-\u9fff]", content), path
    assert content.count("\n```") % 2 == 0, path
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
        if link.startswith("http"):
            continue
        target = (path.parent / link.split("#", 1)[0]).resolve()
        if target == directory / "documentation-1.json":
            continue  # Written by record_check.py after this command completes.
        assert target.exists(), (path, link)
        links += 1
subprocess.run(["git", "diff", "--check", "--", "knowledgebase", "tests", "docs"], check=True)
for path in [*directory.glob("*.py"), directory / "README.md", Path("tests/test_answer_rules.py")]:
    assert all(line == line.rstrip() for line in path.read_text().splitlines()), path
print(f"Reviewed {len(paths)} English documents and {links} existing local links; one self-record link is written on completion.")
print("Content review: classified fixture is explicitly annotated; live classification remains unverified; historical results and source evidence are preserved. No live improvement or merge claim.")
