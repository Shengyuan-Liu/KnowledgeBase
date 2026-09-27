"""Reproduce the planned path's second scope resolution, without providers."""

import json
from pathlib import Path

from knowledgebase.rag.scope import resolve_document_scope


directory = Path(__file__).parent
raw = json.loads((directory.parent / "grouped-and-blank-cells-planned.json").read_text())
first_pass = json.loads((directory / "scope-reproduction.json").read_text())[1]
allowed_ids = first_pass["replayed_scope"]["file_ids"]
assert allowed_ids == []
# prepare_planning keeps the empty ready-file list but discards the first scope.
# retrieve_plan then resolves again with that list as allowed_file_ids, so its
# ready-file catalog is empty even though the request still supplies the file ID.
second_pass = resolve_document_scope(first_pass["extracted_references"], [],
                                     file_ids=raw["request"]["file_ids"])
actual = raw["answer"]["retrieval"]["document_scope"]
result = dict(
    method="Pure existing resolve_document_scope with the empty catalog produced by the first failed scope resolution; no planner, embedding, or generation call.",
    first_pass_scope=first_pass["replayed_scope"], propagated_allowed_file_ids=allowed_ids,
    second_pass_scope=second_pass.model_dump(mode="json"), actual_final_scope=actual,
    second_pass_matches_actual=second_pass.model_dump(mode="json") == actual,
    code_path=["knowledgebase/services/planning.py:58", "knowledgebase/services/chat.py:128",
               "knowledgebase/rag/planned_retrieval.py:166", "knowledgebase/rag/retrieval.py:215",
               "knowledgebase/rag/scope.py:104"],
    interpretation="The original malformed filename causes an empty allowed-file set. The planned path's second resolution then replaces the filename-specific error with a generic selected-document-missing error. This does not establish that the ready file was actually missing.",
)
with (directory / "scope-plan-followup.json").open("x") as output:
    output.write(json.dumps(result, indent=2) + "\n")
assert result["second_pass_matches_actual"]
print(json.dumps(result, indent=2))
