"""Replay immutable source contexts and model decisions without provider calls."""

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
from types import SimpleNamespace

from knowledgebase.providers.limits import input_tokens
from knowledgebase.rag import generation, pdf_evidence, sufficiency
from knowledgebase.rag.context import build_context
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.rag.planning import AnswerRequirement
from knowledgebase.schemas import RetrievedChunk, StructuredChunk
from record_check import METRICS

ROOT = Path(__file__).parent
LIVE = Path("evals/library-runs/20260927-financial-acceptance")
PACKED_PATH = Path("evals/check-runs/20260927-pdf-evidence-packing/after-2.json")
INDEX_PATH = Path("evals/library-runs/20260927-v2-pdf-live/index-snapshot.json")
MANIFEST = json.loads((ROOT / "frozen-manifest.json").read_text())
INDEX = json.loads(INDEX_PATH.read_text())
FILES = {doc["file"]["file_id"]: doc for doc in INDEX["files"]}
PDFS = {identity: PdfExtraction.model_validate(doc["extraction"]) for identity, doc in FILES.items()}
CHUNKS = {chunk["chunk_id"]: chunk for doc in INDEX["files"] for chunk in doc["chunks"]}
CHUNKS.update({p["parent_id"]: {"chunk_id": p["parent_id"], **{k: v for k, v in p.items() if k != "parent_id"}}
               for doc in INDEX["files"] for p in doc["parents"]})
CASE_IDS = ["apple-sales", "apple-income", "apparent-conflict"]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load_baseline(name, repository_file):
    path = ROOT / ("baseline-" + name + ".py")
    original = subprocess.check_output(["git", "show", MANIFEST["baseline_commit"] + ":" + repository_file])
    assert path.read_bytes() == original, path
    spec = importlib.util.spec_from_file_location("baseline_" + name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def restore_hit(raw, module):
    identity = raw["chunk"]["chunk_id"] if "chunk" in raw else raw["chunk_id"]
    chunk = StructuredChunk.model_validate(CHUNKS[identity])
    body = raw["chunk"] if "chunk" in raw else raw
    for field in ["text", "start_offset", "end_offset", "file_id"]:
        assert body[field] == getattr(chunk, field), (identity, field)
    evidence = module.pdf_evidence(PDFS[chunk.file_id], chunk.start_offset, chunk.end_offset)
    return RetrievedChunk(chunk=chunk, pdf=evidence, file_name=raw["file_name"], distance=raw.get("distance"),
                          document_labels=raw["document_labels"], fusion=raw.get("fusion"), rerank=raw.get("rerank"),
                          parent_id=raw.get("parent_id"), matched_child_ids=raw.get("matched_child_ids", []))


def result(chunks):
    return SimpleNamespace(evidence=SimpleNamespace(chunks=chunks))


def canonical_catalog(catalog):
    return [{key: value for key, value in row.items() if key != "table_context"} for row in catalog]


def verify_spans(chunks, catalog):
    checked = 0
    for hit in chunks:
        extraction = PDFS[hit.chunk.file_id]
        spans = [(hit.chunk.start_offset, hit.chunk.end_offset, hit.chunk.text, hit.pdf.regions)]
        spans.extend((s.start_offset, s.end_offset, s.text, s.regions) for s in hit.pdf.supplements)
        for start, end, text, regions in spans:
            assert extraction.text[start:end] == text
            assert all(0 <= region.page_index < extraction.page_count for region in regions)
            checked += 1
    for row in catalog:
        extraction = PDFS[row["file_id"]]
        assert extraction.text[row["start_offset"]:row["end_offset"]] == row["text"]
        matching = [hit for hit in chunks if hit.chunk.file_id == row["file_id"]]
        regions = [region for hit in matching for region in [*hit.pdf.regions, *(r for s in hit.pdf.supplements for r in s.regions)]]
        pages = sorted({r.page_index for r in regions if r.start_offset < row["end_offset"] and row["start_offset"] < r.end_offset})
        assert row["page_indices"] == pages
        checked += 1
    return checked


def absent(reason, population="Offline component replay", status="not_applicable"):
    return dict(status=status, value=None, unit=None, sample_count=None, reason=reason,
                population=population, method=reason, aggregation="none", artifact="comparison.json")


def measured(value, unit, count, population, method, aggregation="counts"):
    return dict(status="measured", value=value, unit=unit, sample_count=count, population=population,
                method=method, aggregation=aggregation, artifact="comparison.json")


def main():
    assert not (ROOT / "comparison.json").exists(), "Append-only: choose another output for a rerun."
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == MANIFEST["baseline_commit"]
    for path, expected in MANIFEST["inputs"].items():
        assert digest(path) == expected, path
    old_pdf = load_baseline("pdf-evidence", "knowledgebase/rag/pdf_evidence.py")
    old_sufficiency = load_baseline("sufficiency", "knowledgebase/rag/sufficiency.py")
    old_generation = load_baseline("generation", "knowledgebase/rag/generation.py")
    packed_rows = []
    span_checks = 0
    for row in json.loads(PACKED_PATH.read_text())["rows"]:
        before = [restore_hit(hit, old_pdf) for hit in row["result"]["chunks"]]
        after = [restore_hit(hit, pdf_evidence) for hit in row["result"]["chunks"]]
        before_context, after_context = build_context(before), build_context(after)
        assert before_context == after_context == row["context"]
        before_catalog = old_sufficiency.assessment_excerpts(result(before))
        after_catalog = sufficiency.assessment_excerpts(result(after))
        assert before_catalog == canonical_catalog(after_catalog)
        before_annotated = old_sufficiency.assessment_context(result(before), before_catalog)
        after_annotated = sufficiency.assessment_context(result(after), after_catalog)
        assert before_annotated == after_annotated
        checked = verify_spans(after, after_catalog)
        span_checks += checked
        packed_rows.append(dict(case_id=row["case_id"], arm=row["arm"], selected_ids=row["selected_ids"],
                                source_ids=[hit.chunk.chunk_id for hit in after],
                                context_unchanged=True, assessment_context_unchanged=True, passage_catalog_unchanged=True,
                                exact_span_checks=checked, context_sha256=sha256(after_context.encode()).hexdigest(),
                                source_artifact=str(PACKED_PATH),
                                before_context_serialized_tokens=input_tokens(before_context, "cl100k_base"),
                                after_context_serialized_tokens=input_tokens(after_context, "cl100k_base"),
                                before_annotated_serialized_tokens=input_tokens(before_annotated, "cl100k_base"),
                                after_annotated_serialized_tokens=input_tokens(after_annotated, "cl100k_base"),
                                new_catalog=after_catalog))
    observations_path = LIVE / "server-observations.jsonl"
    observations = [json.loads(line) for line in observations_path.read_text().splitlines()]
    replayed = []
    assessments = {}
    raw_inputs = {str(path): digest(path) for path in [PACKED_PATH, INDEX_PATH, observations_path]}
    for case_id in CASE_IDS:
        identity = case_id + "-planned"
        path = LIVE / (identity + ".json")
        raw_inputs[str(path)] = digest(path)
        answer = json.loads(path.read_text())["answer"]
        planning = answer["retrieval"]["planning"]
        before = [restore_hit(source, old_pdf) for source in answer["sources"]]
        after = [restore_hit(source, pdf_evidence) for source in answer["sources"]]
        assert build_context(after) == planning["assessment"]["context"]
        starts = [obs for obs in observations if obs["kind"] == "sdk_start" and obs["request"] == identity
                  and obs["input"].get("text", {}).get("format", {}).get("name") == "evidence_assessment"]
        assert len(starts) == 1, "This frozen workload contains one actual assessment per planned request."
        start = starts[0]
        completion = next(obs for obs in observations if obs["kind"] == "sdk_complete" and obs["call_id"] == start["call_id"])
        raw = "".join(content["text"] for message in completion["result"]["output"] for content in message.get("content", []) if content["type"] == "output_text")
        before_catalog = old_sufficiency.assessment_excerpts(result(before))
        after_catalog = sufficiency.assessment_excerpts(result(after))
        assert before_catalog == canonical_catalog(after_catalog)
        payload = json.loads(start["input"]["input"][1]["content"])
        assert old_sufficiency.assessment_context(result(before), before_catalog) == payload["context"]
        assert sufficiency.assessment_context(result(after), after_catalog) == payload["context"]
        requirements = [AnswerRequirement.model_validate(r) for r in payload["requirements"]]
        old_normalized, old_queries = old_sufficiency.validate_assessment(old_sufficiency.SufficiencyAssessment.model_validate_json(raw), requirements, before_catalog)
        new_normalized, new_queries = sufficiency.validate_assessment(sufficiency.SufficiencyAssessment.model_validate_json(raw), requirements, after_catalog)
        assert old_queries == new_queries
        normalized_without_new_metadata = [{**{k: v for k, v in r.items() if k not in {"table_context", "references"}},
                                            "references": [{k: v for k, v in ref.items() if k != "source_number"} for ref in r["references"]]}
                                           for r in new_normalized]
        assert old_normalized == normalized_without_new_metadata
        for requirement in new_normalized:
            selected_ids = {ref["evidence_id"] for ref in requirement["references"]}
            for ref in requirement["table_context"]:
                assert ref["evidence_id"] not in selected_ids
                assert PDFS[ref["file_id"]].text[ref["start_offset"]:ref["end_offset"]] == ref["quote"]
                assert any(e["evidence_id"] == ref["evidence_id"] and e["page_indices"] == ref["page_indices"] for e in after_catalog)
                assert set(ref["for_evidence_ids"]) <= selected_ids
        assessments[case_id] = dict(requirements=new_normalized, queries=new_queries)
        replayed.append(dict(case_id=case_id, request=identity, historical_call_id=start["call_id"],
                             source_artifact=str(path), observations_artifact=str(observations_path), raw_model_output=raw,
                             raw_decision=json.loads(raw), model_selections_and_statuses_unchanged=True,
                             queries_unchanged=True, assessment_payload_unchanged=True,
                             reference_metadata_change="source_number is retained as an explicit navigation field; original selected IDs, quotes, offsets and pages are unchanged.",
                             before_requirements=old_normalized, after_requirements=new_normalized,
                             before_queries=old_queries, after_queries=new_queries,
                             selected_passage_ids_by_requirement={r["requirement_id"]: [ref["evidence_id"] for ref in r["references"]] for r in new_normalized},
                             attached_context_count=sum(len(r["table_context"]) for r in new_normalized)))
    messages = []
    for case_id in CASE_IDS:
        for arm in ["single", "planned"]:
            path = LIVE / (case_id + "-" + arm + ".json")
            raw_inputs[str(path)] = digest(path)
            answer = json.loads(path.read_text())["answer"]
            before = [restore_hit(source, old_pdf) for source in answer["sources"]]
            after = [restore_hit(source, pdf_evidence) for source in answer["sources"]]
            old_assessment = answer["retrieval"]["planning"]["assessment"] if arm == "planned" else None
            new_assessment = assessments[case_id] if arm == "planned" else None
            question = answer["question"]
            interpretation = answer["retrieval_question"]
            old_messages = old_generation._answer_messages(question, before, interpretation, old_assessment)
            new_messages = generation._answer_messages(question, after, interpretation, new_assessment)
            assert build_context(before) == build_context(after)
            starts = [obs for obs in observations if obs["kind"] == "sdk_start" and obs["request"] == case_id + "-" + arm and obs["input"].get("stream")]
            assert len(starts) == 1
            assert old_messages == starts[0]["input"]["input"], "Baseline input must reproduce the exact observed generation request."
            old_count, new_count = input_tokens(old_messages, "cl100k_base"), input_tokens(new_messages, "cl100k_base")
            assert new_count <= 16384
            hints = [{"requirement_id": r["requirement_id"], "source_ids": generation._assessment_source_ids(r, after)} for r in new_assessment["requirements"]] if new_assessment else []
            messages.append(dict(case_id=case_id, arm=arm, source_artifact=str(path), original_generation_call_id=starts[0]["call_id"],
                                 original_generation_messages_reproduced=True, sources_unchanged=True,
                                 before_messages=old_messages, after_messages=new_messages, source_hints=hints,
                                 before_input_tokens=old_count, after_input_tokens=new_count, delta_tokens=new_count - old_count,
                                 planned_answer_budget=16384, within_budget=True))
    inventory = {metric: absent("No retrieval, model answer, provider, latency/load or ingestion workload is executed; existing decisions and sources are replayed offline.") for metric in METRICS}
    inventory["Final evidence coverage"] = measured(dict(before_contexts=len(packed_rows), after_contexts=len(packed_rows),
                                                         identical_source_contexts=sum(r["context_unchanged"] for r in packed_rows),
                                                         source_span_and_page_checks=span_checks, annotated_contexts_identical=sum(r["assessment_context_unchanged"] for r in packed_rows)),
                                                    "contexts and exact span checks", len(packed_rows), "32 frozen packed question/mode contexts",
                                                    "Byte-identical source text/metadata and exact source/supplement spans; new table links add provenance without supplying extra answer evidence. No semantic answer score inferred.")
    inventory["Token usage and cost"] = measured(dict(provider_calls=0, billed_cost=dict(status="not_applicable", value=None, reason="No provider called."),
                                                       encoding="cl100k_base", before_generation_counts=[r["before_input_tokens"] for r in messages],
                                                       after_generation_counts=[r["after_input_tokens"] for r in messages],
                                                       before_mean=statistics.mean(r["before_input_tokens"] for r in messages),
                                                       after_mean=statistics.mean(r["after_input_tokens"] for r in messages),
                                                       planned_input_budget=16384, all_within_budget=all(r["within_budget"] for r in messages)),
                                                 "local serialized input tokens", len(messages), "Six frozen actual answer requests",
                                                 "Production input_tokens on exact before/after message arrays; local budget counts are not provider usage or billing.", "per-case counts and arithmetic means")
    inventory["Reliability"] = measured(dict(frozen_context_replays=len(packed_rows), saved_assessment_replays=len(replayed),
                                              generation_payload_comparisons=len(messages), failed_assertions=0,
                                              unchanged_raw_assessment_decisions=sum(r["model_selections_and_statuses_unchanged"] for r in replayed)),
                                        "offline comparison counts", len(packed_rows) + len(replayed) + len(messages), "Offline structural comparisons only",
                                        "Every assertion must pass before this append-only result is written; no statement about production completion/error rates.")
    result_record = dict(scope="Offline component before/after comparison; no provider calls, no new answers and no live acceptance claim.",
                         baseline_commit=MANIFEST["baseline_commit"], frozen_inputs=raw_inputs,
                         baseline_files={p.name: digest(p) for p in ROOT.glob("baseline-*.py")},
                         current_code_hashes={str(p): digest(p) for p in Path("knowledgebase").rglob("*.py")},
                         fixture_manifest_sha256=digest(ROOT / "frozen-manifest.json"),
                         metric_inventory=inventory, packed_contexts=packed_rows, replayed_assessments=replayed, generation_payloads=messages,
                         retained_attempts={"comparison-1": "Initial harness expected normalized references to have identical metadata. New explicit source_number changes that shape; the corrected invariant compares original fields and preserves new fields in the full result. Raw failed command record retained."},
                         interpretation="Table context is application-attached structural provenance, explicitly separate from the unchanged model-selected references and statuses. Generation source IDs are navigation hints. Prompt changes have not been judged on new live outputs; historical citation failure remains evidence of the earlier version.")
    (ROOT / "comparison.json").write_text(json.dumps(result_record, indent=2) + "\n")
    print(f"Verified {len(packed_rows)} unchanged packed contexts, {span_checks} exact span/page checks, {len(replayed)} unchanged saved model decisions and {len(messages)} generation payload comparisons.")
    for row in replayed:
        print(row["case_id"], "attached context entries", row["attached_context_count"])
    for row in messages:
        print(row["case_id"], row["arm"], "tokens", row["before_input_tokens"], "->", row["after_input_tokens"])


if __name__ == "__main__":
    main()
