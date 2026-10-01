"""Compare actual generation SDK source text with the reviewed evidence objects."""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import tiktoken

from knowledgebase.rag.context import build_context
from knowledgebase.schemas import RetrievedEvidence
from analyze import ROOT, DIRECTORY, evidence_diagnostics, final_result, read, records, write


def main():
    helper = Path("evals/check-runs/20260927-table-context-scope/analyze_comparison.py")
    spec = importlib.util.spec_from_file_location("offline_context_audit", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    observations = records()
    frozen = read(ROOT / "frozen-cases.json")
    encoding = tiktoken.get_encoding("cl100k_base")
    rows = []
    for case in frozen["cases"]:
        for arm in ["single", "planned"]:
            identity = case["id"] + "-" + arm
            result = final_result(observations, identity)
            raw_evidence = result["evidence"] if "trace" in result else result
            evidence = RetrievedEvidence.model_validate(raw_evidence)
            expected = build_context(evidence.chunks)
            starts = [(index, row) for index, row in enumerate(observations, 1)
                      if row["kind"] == "sdk_start" and row["request"] == identity
                      and row["api"] == "responses" and row["input"].get("stream")]
            assert len(starts) == 1, (identity, len(starts))
            line, start = starts[0]
            user = next(message["content"] for message in start["input"]["input"] if message["role"] == "user")
            actual = user.split("\n\nSources:\n", 1)[1]
            assert actual == expected
            checks = module.audit_serialized_context(raw_evidence, actual)
            token_count = len(encoding.encode_ordinary(actual))
            assert token_count == evidence.diagnostics.evidence_tokens <= evidence.diagnostics.max_tokens
            output_path = DIRECTORY / (identity + "-actual-context.txt")
            with output_path.open("x") as output:
                output.write(actual)
            rows.append(dict(identity=identity, sdk_observation_line=line, sdk_call_id=start["call_id"],
                actual_context_artifact=output_path.name, actual_context_sha256=sha256(actual.encode()).hexdigest(),
                actual_context_equals_packed_evidence=True, actual_context_tokens=token_count,
                maximum_context_tokens=evidence.diagnostics.max_tokens, source_checks=checks))
    write("actual-context-audit.json", dict(
        method="Read each actual streamed-generation SDK user message. Compare its entire Sources section byte-for-byte with build_context of the final recorded production retrieval evidence. Independently decode serialized table metadata and check original body, page, offsets and separately located supplement text.",
        reviewer="Codex agent /root/context_replay; programmatic audit, not a human reviewer",
        rows=rows, generation_calls=len(rows), provider_calls_during_audit=0,
        limitation="Confirms actual supplied evidence serialization. Semantic answer and citation judgments remain the independent review's responsibility."))
    print(f"Verified all {len(rows)} actual generation contexts against packed source objects, including exact table coordinates and header supplements.")


if __name__ == "__main__":
    main()
