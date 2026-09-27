"""Replay frozen production packing inputs without retrieval or provider calls."""

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter

import tiktoken

from knowledgebase.rag.context import build_context
from knowledgebase.rag.packing import pack_evidence
from knowledgebase.rag.pdf_evidence import pdf_evidence
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.rag.scope import document_references, identity_labels, resolve_document_scope
from knowledgebase.schemas import ChildChunk, RetrievedChunk, RetrievalDiagnostics, ScopeFile, StructuredChunk


ROOT = Path(__file__).parent
FROZEN = Path("evals/library-runs/20260927-dense-table-acceptance")
ENCODING = tiktoken.get_encoding("cl100k_base")
PRODUCT_FILES = ["knowledgebase/rag/context.py", "knowledgebase/rag/packing.py",
                 "knowledgebase/rag/pdf_evidence.py", "knowledgebase/rag/scope.py"]


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as output:
        output.write(value if isinstance(value, str) else json.dumps(value, indent=2) + "\n")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tokens(text):
    return len(ENCODING.encode_ordinary(text))


def hashes():
    return {name: sha256(Path(name).read_bytes()).hexdigest() for name in PRODUCT_FILES}


def source(row, number):
    return dict(source_id=number, file_id=row.chunk.file_id, file_name=row.file_name,
                chunk_id=row.chunk.chunk_id, text=row.chunk.text,
                start_offset=row.chunk.start_offset, end_offset=row.chunk.end_offset,
                pdf=row.pdf.model_dump(mode="json") if row.pdf else None)


def make_inputs(frozen, snapshot, observations):
    document = snapshot["files"][0]
    info = document["file"]
    extraction = PdfExtraction.model_validate(document["extraction"])
    children = {row["chunk_id"]: ChildChunk.model_validate(row) for row in document["chunks"]}
    parents = {row["parent_id"]: row for row in document["parents"]}
    labels = identity_labels(info["file_name"], extraction.text)
    results = []
    for case in frozen["cases"]:
        for arm in ["single", "planned"]:
            identity = f"{case['id']}-{arm}"
            stages = [dict(row, observation_line=index) for index, row in enumerate(observations, 1)
                      if row["kind"] == "stage" and row["request"] == identity and "result" in row]
            observed = stages[-1]
            result = observed["result"]
            actual = result["evidence"] if "trace" in result else result
            diagnostic = actual["diagnostics"]
            selected = []
            expanded = {}
            for candidate in diagnostic["candidates"]:
                chunk = children[candidate["chunk_id"]]
                assert all(getattr(chunk, key) == candidate[key]
                           for key in ["file_id", "parent_id", "text", "start_offset", "end_offset"])
                provenance = {key: candidate[key] for key in ["distance", "fusion", "rerank"]}
                hit = RetrievedChunk(chunk=chunk, file_name=info["file_name"], **provenance,
                    document_labels=labels, parent_id=chunk.parent_id,
                    matched_child_ids=[chunk.chunk_id] if chunk.parent_id else [])
                selected.append(hit)
                if hit.parent_id:
                    if hit.parent_id in expanded:
                        expanded[hit.parent_id].matched_child_ids.append(chunk.chunk_id)
                        continue
                    parent = parents[hit.parent_id]
                    excerpt = StructuredChunk(chunk_id=parent["parent_id"],
                        **{key: value for key, value in parent.items() if key != "parent_id"})
                    expanded[hit.parent_id] = hit.model_copy(update={"chunk": excerpt,
                        "matched_child_ids": [chunk.chunk_id]})
                else:
                    expanded[chunk.chunk_id] = hit.model_copy()
            for row in [*selected, *expanded.values()]:
                row.pdf = pdf_evidence(extraction, row.chunk.start_offset, row.chunk.end_offset)
            request = read(FROZEN / f"{identity}.json")["request"]
            results.append(dict(identity=identity, case=case, arm=arm, request=request,
                stage_observation_line=observed["observation_line"], stage_count=len(stages),
                chosen_stage="Last observed production retrieval result before the original answer/refusal",
                selected=[row.model_dump(mode="json") for row in selected],
                expanded=[row.model_dump(mode="json") for row in expanded.values()],
                diagnostics=diagnostic, original_evidence=actual,
                original_query_runs=result.get("trace", {}).get("runs", []),
                original_trace=result.get("trace")))
    return dict(catalog=[dict(file_id=info["file_id"], file_name=info["file_name"], labels=labels)],
                cases=results)


def main():
    phase = sys.argv[1]
    assert phase in {"baseline", "after"}
    output = ROOT / (sys.argv[2] if len(sys.argv) > 2 else phase)
    assert not output.exists(), f"Append-only phase already exists: {output}"
    output.mkdir()
    frozen = read(FROZEN / "frozen-cases.json")
    snapshot = read(FROZEN / "index-snapshot.json")
    labels = read(FROZEN / "metrics/fact-labels.json")["labels"]
    documents = {row["file"]["file_id"]: row for row in snapshot["files"]}
    old_metrics = load_module(FROZEN / "metrics/analyze.py", "frozen_metrics")
    before = hashes()
    if phase == "baseline":
        for name in PRODUCT_FILES:
            original = subprocess.check_output(["git", "show", f"b792448:{name}"], text=True)
            saved = ROOT / "baseline-code" / Path(name).name
            if saved.exists():
                assert saved.read_text() == original
            else:
                write(saved, original)
            if not name.endswith("scope.py"):
                assert sha256(original.encode()).hexdigest() == before[name], name
        observations = [json.loads(line) for line in (FROZEN / "server-observations.jsonl").read_text().splitlines()]
        inputs = make_inputs(frozen, snapshot, observations)
        if (ROOT / "frozen-inputs.json").exists():
            assert read(ROOT / "frozen-inputs.json") == inputs
        else:
            write(ROOT / "frozen-inputs.json", inputs)
        scope_module = load_module(ROOT / "baseline-code/scope.py", "baseline_scope")
    else:
        inputs = read(ROOT / "frozen-inputs.json")
        scope_module = sys.modules[document_references.__module__]
    catalog = [ScopeFile.model_validate(row) for row in inputs["catalog"]]
    results = []
    for item in inputs["cases"]:
        diagnostic = RetrievalDiagnostics.model_validate(deepcopy(item["diagnostics"]))
        selected = [RetrievedChunk.model_validate(row) for row in item["selected"]]
        expanded = [RetrievedChunk.model_validate(row) for row in item["expanded"]]
        started = perf_counter()
        packed = pack_evidence(selected, expanded, diagnostic)
        elapsed = perf_counter() - started
        context = build_context(packed.chunks)
        scope_started = perf_counter()
        references = scope_module.document_references(item["request"]["question"])
        scope = scope_module.resolve_document_scope(references, catalog,
            file_ids=item["request"]["file_ids"])
        scope_elapsed = perf_counter() - scope_started
        packed_dump = packed.model_dump(mode="json")
        actual = item["original_evidence"]
        matching = dict(chunks=packed_dump["chunks"] == actual["chunks"],
            evidence_tokens=packed.diagnostics.evidence_tokens == actual["diagnostics"]["evidence_tokens"],
            excluded=packed_dump["diagnostics"]["excluded"] == actual["diagnostics"]["excluded"],
            unexpanded_parents=packed_dump["diagnostics"]["unexpanded_parents"] == actual["diagnostics"]["unexpanded_parents"],
            scope=scope.model_dump(mode="json") == actual["diagnostics"]["document_scope"],
            scope_resolution=all(scope.model_dump(mode="json")[key] == actual["diagnostics"]["document_scope"][key]
                                 for key in ["status", "references", "file_ids", "matches"]))
        if phase == "baseline":
            assert all(value for key, value in matching.items() if key != "scope"), (item["identity"], matching)
        sources = [source(row, index) for index, row in enumerate(packed.chunks, 1)]
        coverage = old_metrics.supplied_coverage(sources, item["case"]["expected_fact_ids"], labels, documents)
        inventory = [dict(chunk_id=row.chunk.chunk_id, kind=kind, body_tokens=tokens(row.chunk.text),
                          serialized_context_tokens=tokens(build_context([row])),
                          cells=sum(len(table.cells) for table in row.pdf.tables) if row.pdf else 0,
                          supplements=len(row.pdf.supplements) if row.pdf else 0)
                     for kind, group in [("selected_child", selected), ("expanded_parent", expanded)] for row in group]
        summary = dict(identity=item["identity"], case_id=item["case"]["id"], arm=item["arm"],
            question=item["request"]["question"], original_stage_observation_line=item["stage_observation_line"],
            selected_rank_order=[row.chunk.chunk_id for row in selected],
            expanded_order=[row.chunk.chunk_id for row in expanded],
            packed_order=[row.chunk.chunk_id for row in packed.chunks],
            evidence_tokens=packed.diagnostics.evidence_tokens, serialized_tokens=tokens(context),
            max_tokens=packed.diagnostics.max_tokens, original_live_output_match=matching,
            scope=dict(references=references, result=scope.model_dump(mode="json")),
            scope_message_note="Direct scope replay and planned caller can use different not-found messages; resolution status, references, file IDs and matches are compared separately from the message.",
            final_structural_coverage=coverage,
            inventory=inventory, local_pack_seconds=elapsed, local_scope_seconds=scope_elapsed,
            query_not_rerun=True, answer_not_generated=True,
            scope_only_without_candidates=not bool(selected))
        write(output / f"{item['identity']}-evidence.json", packed_dump)
        write(output / f"{item['identity']}-context.txt", context)
        write(output / f"{item['identity']}-summary.json", summary)
        results.append(summary)
    write(output / "manifest.json", dict(phase=phase,
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        git_status=subprocess.check_output(["git", "status", "--short"], text=True),
        frozen_artifact_hashes={str(path): sha256(path.read_bytes()).hexdigest() for path in
            [FROZEN / "index-snapshot.json", FROZEN / "frozen-cases.json",
             FROZEN / "metrics/fact-labels.json", FROZEN / "server-observations.jsonl", ROOT / "frozen-inputs.json"]},
        source_hashes=before, source_hashes_after=hashes(), device=platform.platform(), python=platform.python_version(),
        tokenizer="cl100k_base", concurrency=1, model_calls=0, results=results,
        method="Reconstruct original production pack_retrieval_candidates inputs from the last observed retrieval stage, candidate provenance, unchanged frozen children/parents, original PDF extraction and labels; freeze those inputs once and call pack_evidence. Ranks, selected IDs, queries, corpus and annotations do not change. Scope is separately replayed from the six original questions. No retrieval, parsing, indexing, model answer, or sufficiency decision is rerun.",
        limitations="Stored planned queries and selected ranks were produced under the old context/sufficiency cycle and remain fixed. The two originally scope-blocked cases have no recorded candidates; a corrected scope cannot demonstrate their retrieval or answer quality. Structural metadata coverage must be checked against actual serialized model text before calling it final model-context coverage. Local pack/scope timings are diagnostics, not production response latency."))
    print(json.dumps(dict(phase=phase, cases=[dict(identity=row["identity"], tokens=row["evidence_tokens"],
        coverage=row["final_structural_coverage"]["value"], scope=row["scope"]["result"]["status"],
        original_match=row["original_live_output_match"]) for row in results]), indent=2))


if __name__ == "__main__":
    main()
