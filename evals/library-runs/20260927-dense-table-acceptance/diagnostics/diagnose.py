"""Diagnose frozen acceptance inputs with unchanged local production functions.

No provider, parser, index, or server calls. This is not a proposed-fix trial.
"""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import tiktoken

from knowledgebase.rag.context import build_context
from knowledgebase.rag.pdf_evidence import pdf_evidence
from knowledgebase.rag.pdf_models import PdfExtraction
from knowledgebase.rag.scope import document_references, identity_labels, resolve_document_scope
from knowledgebase.schemas import ChildChunk, RetrievedChunk, ScopeFile, StructuredChunk


DIRECTORY = Path(__file__).parent
RUN = DIRECTORY.parent
ENCODING = tiktoken.get_encoding("cl100k_base")


def read(path):
    return json.loads(path.read_text())


def write(name, value):
    path = DIRECTORY / name
    with path.open("x") as output:
        output.write(value if isinstance(value, str) else json.dumps(value, indent=2) + "\n")


def tokens(text):
    return len(ENCODING.encode_ordinary(text))


def production_hashes():
    return {str(path): sha256(path.read_bytes()).hexdigest()
            for path in sorted(Path("knowledgebase").rglob("*.py"))}


def context_sections(context):
    markers = [("source_identity_and_body", 0)]
    for name, marker in [
        ("pdf_page_and_offset_metadata", "\nPDF physical pages:"),
        ("table_cell_coordinates", "\nTable cells ["),
        ("separately_located_context", "\nSeparately located "),
        ("extraction_warnings", "\nExtraction limitations:"),
    ]:
        if marker in context:
            markers.append((name, context.index(marker)))
    markers.sort(key=lambda item: item[1])
    result = []
    previous = 0
    for i, (name, start) in enumerate(markers):
        end = markers[i + 1][1] if i + 1 < len(markers) else len(context)
        cumulative = tokens(context[:end])
        result.append(dict(section=name, characters=end-start,
                           independent_tokens=tokens(context[start:end]),
                           cumulative_tokens=cumulative,
                           incremental_tokens=cumulative-previous))
        previous = cumulative
    return result


if __name__ == "__main__":
    before = production_hashes()
    snapshot = read(RUN / "index-snapshot.json")
    frozen = read(RUN / "frozen-cases.json")
    file = snapshot["files"][0]
    info = file["file"]
    extraction = PdfExtraction.model_validate(file["extraction"])
    labels = identity_labels(info["file_name"], extraction.text)
    entries = {}
    for raw in file["chunks"]:
        chunk = ChildChunk.model_validate(raw)
        entries[chunk.chunk_id] = RetrievedChunk(
            chunk=chunk, file_name=info["file_name"], distance=None,
            parent_id=chunk.parent_id, document_labels=labels,
            pdf=pdf_evidence(extraction, chunk.start_offset, chunk.end_offset),
        )
    for raw in file["parents"]:
        chunk = StructuredChunk(chunk_id=raw["parent_id"],
                                **{key: value for key, value in raw.items() if key != "parent_id"})
        entries[chunk.chunk_id] = RetrievedChunk(
            chunk=chunk, file_name=info["file_name"], distance=None,
            parent_id=raw["parent_id"], document_labels=labels,
            pdf=pdf_evidence(extraction, chunk.start_offset, chunk.end_offset),
        )

    inventory = []
    child_zero = entries[f'{info["file_id"]}:child:0']
    for identity, item in entries.items():
        context = build_context([item])
        header_spans = {tuple(span) for table in item.pdf.tables for span in table.column_header_spans}
        counts = Counter(supplement.role for supplement in item.pdf.supplements)
        inventory.append(dict(
            chunk_id=identity, parent_id=item.parent_id,
            start_offset=item.chunk.start_offset, end_offset=item.chunk.end_offset,
            stored_body_tokens=item.chunk.token_count, measured_body_tokens=tokens(item.chunk.text),
            full_serialized_context_tokens=tokens(context), fits_empty_4096_budget=tokens(context) <= 4096,
            cell_tuple_count=sum(len(table.cells) for table in item.pdf.tables),
            declared_column_header_span_count=len(header_spans),
            included_header_tuple_count=sum(tuple(cell[-2:]) in header_spans
                                            for table in item.pdf.tables for cell in table.cells),
            supplement_counts=dict(counts), sections=context_sections(context),
        ))
        if identity in {child_zero.chunk.chunk_id, child_zero.parent_id}:
            name = "child-0" if identity == child_zero.chunk.chunk_id else "parent-of-child-0"
            write(f"{name}-context.txt", context)
            write(f"{name}-evidence.json", item.model_dump(mode="json"))
    write("context-inventory.json", inventory)

    rows = {}
    table = next(block.table for block in extraction.blocks if block.table is not None)
    for state in ["Alabama", "Alaska", "Arizona"]:
        label = next(cell for cell in table.cells if cell.column_start == 0 and cell.text == state)
        row = sorted((cell for cell in table.cells if cell.row_start == label.row_start),
                     key=lambda cell: cell.column_start)
        rows[state] = dict(row_index=label.row_start, values=[cell.text for cell in row],
                          all_cells_inside_child_0=all(child_zero.chunk.start_offset <= cell.start_offset
                                                     and cell.end_offset <= child_zero.chunk.end_offset for cell in row),
                          cells=[cell.model_dump(mode="json") for cell in row])
    write("three-state-rows.json", rows)

    observations = [dict(json.loads(line), observation_line=index)
                    for index, line in enumerate((RUN / "server-observations.jsonl").read_text().splitlines(), 1)]
    streams = [row for row in observations if row["kind"] == "sdk_start"
               and row["api"] == "responses" and row["input"].get("stream")]
    scope_results = []
    generation_results = []
    actual_retrieval = []
    wrong_totals = {"Alabama": "29,801", "Alaska": "5,733", "Arizona": "32,667"}
    correct_totals = {"Alabama": "71,137", "Alaska": "7,095", "Arizona": "27,087"}
    for case_id in ["dense-table", "state-totals", "grouped-and-blank-cells"]:
        for arm in ["single", "planned"]:
            identity = f"{case_id}-{arm}"
            raw = read(RUN / f"{identity}.json")
            answer = raw["answer"]
            diagnostics = answer["retrieval"]
            observed_stages = [row for row in observations if row["request"] == identity and row["kind"] == "stage"]
            actual_retrieval.append(dict(
                request=identity, reported_evidence_tokens=diagnostics["evidence_tokens"],
                max_tokens=diagnostics["max_tokens"],
                candidates=diagnostics["candidates"], excluded=diagnostics["excluded"],
                sources=[{key: source[key] for key in ["source_id", "chunk_id", "start_offset", "end_offset", "text"]}
                         for source in answer["sources"]],
                stage_observation_lines=[row["observation_line"] for row in observed_stages],
            ))
            if case_id == "grouped-and-blank-cells":
                references = document_references(raw["request"]["question"])
                result = resolve_document_scope(references, [ScopeFile(
                    file_id=info["file_id"], file_name=info["file_name"], labels=labels,
                )], file_ids=raw["request"]["file_ids"])
                starts = [row for row in observations if row["request"] == identity and row["kind"] == "sdk_start"]
                scope_results.append(dict(
                    request=identity, question=raw["request"]["question"], explicit_file_ids=raw["request"]["file_ids"],
                    catalog_file=info, catalog_labels=labels, extracted_references=references,
                    replayed_scope=result.model_dump(mode="json"), actual_scope=diagnostics["document_scope"],
                    replay_matches_actual=result.model_dump(mode="json") == diagnostics["document_scope"],
                    sdk_start_count=len(starts), answer=answer["answer"],
                ))
            matched_streams = [row for row in streams if row["request"] == identity]
            generation = dict(request=identity, answer=answer["answer"], generation_stream_count=len(matched_streams))
            if matched_streams:
                assert len(matched_streams) == 1
                observed = matched_streams[0]
                messages = observed["input"]["input"]
                user = next(message["content"] for message in messages if message["role"] == "user")
                source_context = user.split("\n\nSources:\n", 1)[1]
                all_text = "\n".join(message["content"] for message in messages)
                write(f"{identity}-actual-generation-input.json", observed)
                write(f"{identity}-actual-sources.txt", source_context)
                generation.update(
                    call_id=observed["call_id"], sdk_observation_line=observed["observation_line"],
                    source_context_tokens=tokens(source_context),
                    source_context_sha256=sha256(source_context.encode()).hexdigest(),
                    source_count=len(answer["sources"]),
                    supplied_table_span_count=sum(len(source["pdf"]["tables"]) for source in answer["sources"]),
                    source_state_names_present={state: state in source_context for state in correct_totals},
                    correct_total_occurrences={state: dict(value=value, in_source_context=value in source_context,
                                                         in_all_messages=value in all_text) for state, value in correct_totals.items()},
                    wrong_total_occurrences={state: dict(value=value, in_source_context=value in source_context,
                                                       in_all_messages=value in all_text, in_answer=value in answer["answer"])
                                             for state, value in wrong_totals.items()},
                    source_body_offsets=[[source["start_offset"], source["end_offset"]] for source in answer["sources"]],
                )
            generation_results.append(generation)
    write("scope-reproduction.json", scope_results)
    write("actual-retrieval.json", actual_retrieval)
    write("generation-input-audit.json", generation_results)
    after = production_hashes()
    assert before == after
    zero_metrics = next(row for row in inventory if row["chunk_id"] == child_zero.chunk.chunk_id)
    findings = dict(
        method="Offline replay of pdf_evidence/build_context/document_references/resolve_document_scope on frozen accepted-input artifacts; original production functions unchanged; no provider, parser, index, server, or proposed-fix execution.",
        reviewer="Codex assistant /root/citation_design_review; not a human reviewer",
        commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        tokenizer="cl100k_base", budget=4096,
        source_hash=extraction.source_hash, revision_id=extraction.revision_id,
        source_artifact_hashes={name: sha256((RUN / name).read_bytes()).hexdigest()
                                for name in ["index-snapshot.json", "frozen-cases.json", "server-observations.jsonl"]},
        production_hashes_before=before, production_hashes_after=after, production_unchanged=before == after,
        child_zero=zero_metrics,
        original_annotated_states_fully_in_child_zero={state: row["all_cells_inside_child_0"] for state, row in rows.items()},
        scope_replay_matches=[row["replay_matches_actual"] for row in scope_results],
        scope_requests_sdk_start_counts=[row["sdk_start_count"] for row in scope_results],
        generation_inputs=generation_results,
        limits="Local tokenizer counts are serialized source-context diagnostics, not provider billing. No fix efficacy, live rerun, model determinism, or unannotated-row accuracy is established.",
    )
    write("findings.json", findings)
    print(json.dumps(dict(child_zero=zero_metrics,
                          scopes=[{key: row[key] for key in ["request", "extracted_references", "replay_matches_actual", "sdk_start_count"]} for row in scope_results],
                          generation_inputs=generation_results, production_unchanged=before == after), indent=2))
