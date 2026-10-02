"""Record exact equality of the retained, already-normalized offline observations."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess


DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    before_path = DIRECTORY / "behavior-before-v2.json"
    after_path = DIRECTORY / "behavior-after.json"
    before = json.loads(before_path.read_text())
    after = json.loads(after_path.read_text())
    groups = {
        name: {"equal": before.get(name) == after.get(name)}
        for name in sorted(before.keys() | after.keys())
    }
    code_paths = subprocess.check_output(
        ["git", "ls-files", "knowledgebase", "tests", "evals/automatic.py", "evals/evaluate.py"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    record = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "baseline_production_commit": "bbd0a8d",
        "final_code_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "scope": "One frozen offline TXT corpus; exact normalized contract equality.",
        "reviewer": "Codex, automated equality comparison and code/document review",
        "before": {"artifact": before_path.name, "sha256": digest(before_path)},
        "after": {"artifact": after_path.name, "sha256": digest(after_path)},
        "equal": before == after,
        "groups": groups,
        "schema_count": len(before["schemas"]),
        "schema_names": sorted(before["schemas"]),
        "code_file_hashes": {name: digest(ROOT / name) for name in code_paths},
        "limits": [
            "Generated identities and wall-clock fields are normalized by the frozen test.",
            "Provider responses are mocked; this is not a live quality or performance benchmark.",
            "Other PDF and reranking behavior is covered by the offline suite, not this snapshot.",
        ],
    }
    with (DIRECTORY / "comparison.json").open("x") as output:
        json.dump(record, output, indent=2)
        output.write("\n")
    assert record["equal"], "Frozen observations differ; see comparison.json"
    print(f"1 passed: {len(groups)} groups and {record['schema_count']} schemas match.")


if __name__ == "__main__":
    main()
