"""Correct the earlier display-escaping interpretation without rewriting it."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
original = json.loads((ROOT / "failure-replay.json").read_text())
queries = [q["text"] for q in original["original_decision"]["queries"]]
queries += [q["query_template"] for q in original["original_decision"]["dependencies"]]
assert all("\\" not in query for query in queries)
with (ROOT / "failure-replay-correction.json").open("x") as file:
    file.write(json.dumps(dict(corrects="failure-replay.json:other_observation", decoded_query_texts=queries,
        literal_backslash_present=False,
        correction="The decoded query strings use ordinary quotes. The earlier note mistook JSON display escaping for literal query characters. There is no observed filename-escaping defect; the two missing {target} validation errors remain confirmed.",
        provider_calls=0), indent=2) + "\n")
print("Corrected filename-escaping interpretation; decoded strings have ordinary quotes. Confirmed dependency-placeholder errors remain unchanged.")
