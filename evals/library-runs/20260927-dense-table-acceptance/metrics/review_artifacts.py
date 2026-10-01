"""Check existing metric artifact references and observed SDK completion only."""

import json
from pathlib import Path
import re

from analyze import DIRECTORY, ROOT, digest, read


def artifact_references(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if (key == "artifact" or key.endswith("_artifact") or key in {"initial_diagnostics", "final_diagnostics"}) and isinstance(item, str):
                yield item
            elif key == "raw_artifacts":
                yield from item
            else:
                yield from artifact_references(item)
    elif isinstance(value, list):
        for item in value:
            yield from artifact_references(item)


if __name__ == "__main__":
    paths = set()
    descriptive = set()
    for name in ["measurement.json", "retrieval-diagnostics.json", "retrieval-diagnostics-2.json", "fact-labels.json"]:
        for reference in artifact_references(read(DIRECTORY / name)):
            for part in reference.split(";"):
                part = part.strip()
                if part.endswith("case-arm JSON files"):
                    descriptive.add(part)
                else:
                    paths.add(part)
    missing = [path for path in sorted(paths) if not (DIRECTORY / path).is_file()]
    assert not missing, missing
    # The wrapper writes this review's JSON after this command returns.
    for target in re.findall(r"\]\(([^)]+)\)", (DIRECTORY / "README.md").read_text()):
        if target != "artifact-review-1.json":
            assert (DIRECTORY / target).is_file(), target
    measurement = read(DIRECTORY / "measurement.json")
    assert measurement["validity"]["review_sha256"] == digest(ROOT / "review/reviewed-cases.json")
    reconciliation = read(ROOT / "review/reconciliation.json")
    assert reconciliation["resolution"]["primary_relevance_mean"] == measurement["groups"]["all"]["Answer relevance"]["value"]
    observations = [json.loads(line) for line in (ROOT / "server-observations.jsonl").read_text().splitlines()]
    starts = [row for row in observations if row["kind"] == "sdk_start"]
    complete = [row for row in observations if row["kind"] == "sdk_complete"]
    streams = [row for row in observations if row["kind"] == "sdk_stream_terminal"]
    assert all(row["event"]["type"] == "response.completed" for row in streams)
    assert {row["call_id"] for row in starts} == {row["call_id"] for row in [*complete, *streams]}
    assert len(starts) == len(complete) + len(streams)
    assert not any(row["kind"] == "sdk_error" for row in observations)
    assert read(ROOT / "resolved-runtime.json")["settings"]["openai_max_retries"] == 0
    print(json.dumps(dict(concrete_metric_artifact_paths=len(paths), missing=missing,
        descriptive_references=sorted(descriptive), sdk_started=len(starts), sdk_sync_complete=len(complete),
        sdk_stream_complete=len(streams), sdk_errors=0, configured_retries=0,
        review_sha256=measurement["validity"]["review_sha256"],
        primary_relevance=reconciliation["resolution"]["primary_relevance_mean"],
        secondary_relevance=reconciliation["resolution"]["secondary_relevance_mean"]), indent=2))
    print("1 passed")
