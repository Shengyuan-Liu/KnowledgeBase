"""Review edited docs and frozen comparison integrity without provider calls."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
fixture = json.loads((ROOT / "frozen-case.json").read_text())
assert sha256((PROJECT / fixture["source_artifact"]).read_bytes()).hexdigest() == fixture["source_sha256"]
comparison = json.loads((ROOT / "comparison-1/summary.json").read_text())
assert comparison["rows"][0]["context_sha256"] == comparison["rows"][1]["context_sha256"]
assert [row["requirement_count"] for row in comparison["rows"]] == [3, 2]
assert [row["provider_mock_calls"] for row in comparison["rows"]] == [3, 2]
paths = [ROOT / "README.md", PROJECT / "docs/v2/README.md", PROJECT / "docs/planned-retrieval.md",
         PROJECT / "docs/dependent-retrieval.md", PROJECT / "docs/evidence-sufficiency.md"]
links = 0
for path in paths:
    content = path.read_text()
    assert not re.search(r"[\u4e00-\u9fff]", content)
    assert content.count("\n```") % 2 == 0
    assert all(line == line.rstrip() for line in content.splitlines())
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
        if link.startswith("http"):
            continue
        target = (path.parent / link.split("#", 1)[0]).resolve()
        if target == ROOT / "documentation-1.json":
            continue  # Written by the wrapper on completion.
        assert target.exists(), (path, link)
        links += 1
subprocess.run(["git", "diff", "--check", "--", "knowledgebase", "tests", "docs"], check=True)
for path in [*ROOT.glob("*.py"), PROJECT / "tests/test_planner_fact_scope.py"]:
    assert all(line == line.rstrip() for line in path.read_text().splitlines())
print(f"Reviewed five English documents and {links} existing local links; wrapper writes one self-record link. Frozen source and comparison hashes agree.")
print("Content review distinguishes prompt changes, controlled desired outputs and unverified model behavior; historical failures and generic-refusal tradeoff remain visible. No quality or merge claim.")
