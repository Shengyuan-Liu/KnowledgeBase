"""Verify the retained comparison, current code and documentation without providers."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from knowledgebase.providers.limits import input_tokens

DIRECTORY = Path(__file__).parent
manifest = json.loads((DIRECTORY / "frozen-manifest.json").read_text())
before = json.loads((DIRECTORY / "before.json").read_text())
after = json.loads((DIRECTORY / "after.json").read_text())
comparison = json.loads((DIRECTORY / "comparison.json").read_text())
for path, expected in manifest["referenced_artifacts"].items():
    assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
for path, expected in after["code_hashes"].items():
    assert sha256(Path(path).read_bytes()).hexdigest() == expected, path
for source in ["sufficiency", "dependencies", "hops"]:
    production = f"knowledgebase/{'services' if source == 'hops' else 'rag'}/{source}.py"
    assert (DIRECTORY / f"baseline-{source}.py").read_bytes() == subprocess.check_output([
        "git", "show", manifest["baseline_commit"] + ":" + production])
for old, new in zip(before["rows"], after["rows"], strict=True):
    assert old["answer_context_sha256"] == new["answer_context_sha256"]
    assert old["selected_ids"] == new["selected_ids"]
    for row in [old, new]:
        assert input_tokens(row["request"], "cl100k_base") == row["input_token_count"] <= 8192
    old_context = json.loads(old["request"]["messages"][1]["content"])["context"]
    new_payload = json.loads(new["request"]["messages"][1]["content"])
    assert "evidence_catalog" not in new_payload
    assert re.sub(r"\[p\d+\] ", "", new_payload["context"]) == old_context
metrics = comparison["metric_inventory"]
assert len(metrics) == 20
for metric in metrics.values():
    assert metric["status"] in {"measured", "not_applicable", "unavailable"}
    assert (metric["value"] is not None) == (metric["status"] == "measured")
    if metric["status"] != "measured":
        assert metric["reason"]
assert before["historical_failure"]["validated"] is False
for name, passed, skipped in [("backend-tests-2", 745, 1), ("browser-tests-1", 4, 0)]:
    record = json.loads((DIRECTORY / (name + ".json")).read_text())
    assert record["exit_code"] == 0
    assert record["counts"] == {"passed": passed, "failed": 0, "skipped": skipped, "error": 0}
for name in ["pdf-assessment-tests-1", "backend-tests-1"]:
    record = json.loads((DIRECTORY / (name + ".json")).read_text())
    assert record["exit_code"] != 0 and record["counts"]["failed"] == 3
paths = ["README.md", "docs/evidence-sufficiency.md", "docs/pdf-integration.md", "docs/v2/README.md", str(DIRECTORY / "README.md")]
links = 0
for name in paths:
    path = Path(name)
    text = path.read_text()
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if "://" in link or link.startswith("#"):
            continue
        assert (path.parent / link.split("#")[0]).exists(), (name, link)
        links += 1
    assert not any(line.endswith(" ") for line in text.splitlines()), name
subprocess.run(["git", "diff", "--check"], check=True)
print(f"Verified 32 fixed context pairs, 64 exact input-token counts, source hashes, 20 metrics, final test counts, retained failures and {links} local documentation links across {len(paths)} documents.")
