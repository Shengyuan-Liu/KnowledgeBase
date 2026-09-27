"""Resolve frozen table facts and score recorded retrieval without provider calls."""

from hashlib import sha256
import json
import math
from pathlib import Path
import re
import statistics
import sys


DIRECTORY = Path(__file__).parent
ROOT = DIRECTORY.parent
K = 5


def read(path):
    return json.loads(path.read_text())


def write(name, value):
    path = DIRECTORY / name
    assert not path.exists(), f"Append-only: {path}"
    path.write_text(json.dumps(value, indent=2) + "\n")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def normalized(text):
    return " ".join((text or "").split())


def distribution(values):
    if not values:
        return None
    values = sorted(values)

    def percentile(fraction):
        position = (len(values) - 1) * fraction
        lower = int(position)
        return values[lower] + (values[min(lower + 1, len(values) - 1)] - values[lower]) * (position - lower)

    return dict(n=len(values), mean=statistics.mean(values), p50=percentile(.5),
                p95=percentile(.95), unit="seconds", percentile_method="linear interpolation")


def records():
    return [json.loads(line) for line in (ROOT / "server-observations.jsonl").read_text().splitlines()]


def final_result(observations, identity):
    stages = [row for row in observations if row["request"] == identity and row["kind"] == "stage" and "result" in row]
    return stages[-1]["result"] if stages else None


def query_runs(result):
    if result is None:
        return []
    if "trace" in result:
        return [dict(index=i, round_index=run["round_index"], query=run["text"], diagnostics=run["result"]["diagnostics"])
                for i, run in enumerate(result["trace"]["runs"])]
    scope = result["diagnostics"].get("document_scope")
    if scope is not None and scope["status"] != "resolved":
        return []
    return [dict(index=0, round_index=1, query=None, diagnostics=result["diagnostics"])]


def evidence_diagnostics(result):
    if result is None:
        return None
    return result["evidence"]["diagnostics"] if "trace" in result else result["diagnostics"]


def selected_ids(result):
    if result is None:
        return []
    if "trace" in result:
        return result["trace"]["selected_ids"]
    return [candidate["chunk_id"] for candidate in result["diagnostics"]["candidates"]]


def cell_tuple(cell):
    return [cell[key] for key in ["row_start", "row_end", "column_start", "column_end", "start_offset", "end_offset"]]


def contains(span, start, end):
    return span["start_offset"] <= start and end <= span["end_offset"]


def resolve_labels(frozen, index):
    labels = {}
    for identity, fact in frozen["facts"].items():
        document = next(item for item in index["files"] if item["file"]["file_name"] == fact["file"])
        extraction = document["extraction"]
        assert extraction["source_hash"] == fact["source_sha256"]
        pages = set(fact["page_indices"])
        blocks = [block for block in extraction["blocks"]
                  if pages & {region["page_index"] for region in block["regions"]}]
        label = dict(fact_id=identity, fact=fact, file_id=document["file"]["file_id"],
                     source_hash=extraction["source_hash"], revision_id=extraction["revision_id"])
        if fact["kind"] in {"table_cell", "blank_cell"}:
            matches = []
            for block in blocks:
                table = block.get("table")
                if table is None:
                    continue
                for row_label in table["cells"]:
                    if row_label["column_start"] != 0 or normalized(row_label["text"]) != fact["row_label"]:
                        continue
                    row = [cell for cell in table["cells"] if cell["row_start"] == row_label["row_start"]]
                    target = [cell for cell in row if cell["column_start"] == fact["column_index"]
                              and cell["column_end"] == fact["column_index"] + 1]
                    if len(target) != 1:
                        continue
                    headers = sorted([cell for cell in table["cells"] if cell["column_header"]
                        and cell["row_start"] < row_label["row_start"]
                        and cell["column_start"] <= fact["column_index"] < cell["column_end"]
                        and cell["column_end"] - cell["column_start"] < table["columns"] and normalized(cell["text"])],
                        key=lambda cell: (cell["row_start"], cell["column_start"]))
                    if [normalized(cell["text"]) for cell in headers] == fact["header_path"]:
                        matches.append((table, row, row_label, target[0], headers))
            assert len(matches) == 1, (identity, "Expected exactly one original-page row/header association", len(matches))
            table, row, row_label, target, headers = matches[0]
            assert normalized(target["text"]) == normalized(fact["exact_value"]), (identity, target["text"])
            period = [cell for cell in table["cells"] if cell["column_header"]
                      and fact["report_month"] in cell["text"] and str(fact["report_year"]) in cell["text"]]
            assert len(period) == 1, (identity, "Expected one explicit report-period cell")
            assert all({region["page_index"] for region in cell["regions"]} == pages
                       for cell in [row_label, target, *headers, *period])
            assert all(extraction["text"][cell["start_offset"]:cell["end_offset"]] == cell["text"]
                       for cell in [row_label, target, *headers, *period])
            label.update(table_id=table["table_id"], target_cell=target, row_label_cell=row_label, header_cells=headers,
                         period_cell=period[0],
                         row_span=dict(start_offset=min(cell["start_offset"] for cell in row),
                                       end_offset=max(cell["end_offset"] for cell in row)))
            label["row_text"] = extraction["text"][label["row_span"]["start_offset"]:label["row_span"]["end_offset"]]
        elif fact["kind"] == "prose":
            phrases = []
            for phrase in fact["required_phrases"]:
                pattern = r"\s+".join(re.escape(word) for word in phrase.split())
                spans = []
                for block in blocks:
                    for match in re.finditer(pattern, block["text"], flags=re.IGNORECASE):
                        spans.append(dict(start_offset=block["start_offset"] + match.start(),
                                          end_offset=block["start_offset"] + match.end(),
                                          text=match.group(), source_ref=block["source_ref"], regions=block["regions"]))
                assert spans, (identity, phrase, "Unmapped original-page phrase")
                phrases.append(dict(phrase=phrase, spans=spans))
            label["phrases"] = phrases
        else:
            raise ValueError(f"Unsupported frozen fact kind: {fact['kind']}")
        labels[identity] = label
    return labels


def candidate_covers(chunk, label):
    if chunk["file_id"] != label["file_id"]:
        return False
    if label["fact"]["kind"] == "blank_cell":
        # The complete row and its delimiters locate the blank; an empty span alone is not proof.
        row = label["row_span"]
        return contains(chunk, row["start_offset"], row["end_offset"])
    if label["fact"]["kind"] == "table_cell":
        cell = label["target_cell"]
        return contains(chunk, cell["start_offset"], cell["end_offset"])
    return any(contains(chunk, span["start_offset"], span["end_offset"])
               for phrase in label["phrases"] for span in phrase["spans"])


def fact_covered(chunks, label):
    if label["fact"]["kind"] != "prose":
        return any(candidate_covers(chunk, label) for chunk in chunks)
    return all(any(chunk["file_id"] == label["file_id"] and contains(chunk, span["start_offset"], span["end_offset"])
                   for chunk in chunks for span in phrase["spans"]) for phrase in label["phrases"])


def retrieval_scores(ids, facts, chunks, labels):
    selected = [chunks[identity] for identity in ids[:K]]
    relevant = lambda chunk: any(candidate_covers(chunk, labels[fact]) for fact in facts)
    binary = [int(relevant(chunk)) for chunk in selected]
    coverage = {fact: fact_covered(selected, labels[fact]) for fact in facts}
    ideal_count = min(K, sum(relevant(chunk) for chunk in chunks.values()))
    ideal = sum(1 / math.log2(i + 2) for i in range(ideal_count))
    return {"Recall@K": sum(coverage.values()) / len(facts), "Precision@K": sum(binary) / K,
            "Hit Rate@K": int(any(binary)), "MRR": next((1 / (i + 1) for i, value in enumerate(binary) if value), 0),
            "NDCG@K": sum(value / math.log2(i + 2) for i, value in enumerate(binary)) / ideal if ideal else 0,
            "fact_coverage": coverage, "selected_ids": ids[:K], "binary_relevance": binary,
            "ideal_relevant_children_at_5": ideal_count}


def supplied_coverage(sources, facts, labels, documents):
    points = []
    for fact_id in facts:
        label = labels[fact_id]
        rows = []
        for number, source in enumerate(sources, 1):
            pdf = source.get("pdf") or {}
            if source["file_id"] != label["file_id"] or pdf.get("revision_id") != label["revision_id"]:
                continue
            extraction = documents[label["file_id"]]["extraction"]
            spans = [source, *pdf.get("supplements", [])]
            assert all(extraction["text"][span["start_offset"]:span["end_offset"]] == span["text"] for span in spans)
            if label["fact"]["kind"] == "prose":
                covered = [any(contains(span, match["start_offset"], match["end_offset"])
                               for span in spans for match in phrase["spans"]) for phrase in label["phrases"]]
                rows.append(dict(source_id=number, phrases_covered=covered, complete=all(covered)))
                continue
            table = next((table for table in pdf.get("tables", []) if table["table_id"] == label["table_id"]), None)
            tuples = table["cells"] if table else []
            required = [label["row_label_cell"], label["target_cell"], *label["header_cells"], label["period_cell"]]
            cell_checks = [dict(cell=cell_tuple(cell), text=cell["text"], metadata_present=cell_tuple(cell) in tuples,
                               text_supplied=any(contains(span, cell["start_offset"], cell["end_offset"])
                                                 for span in spans) if cell["text"] else None)
                           for cell in required]
            full_row = contains(source, label["row_span"]["start_offset"], label["row_span"]["end_offset"])
            checks_pass = all(cell["metadata_present"] and cell["text_supplied"] is not False for cell in cell_checks)
            if label["fact"]["kind"] == "blank_cell":
                checks_pass = checks_pass and full_row
            rows.append(dict(source_id=number, table_id=label["table_id"], cells=cell_checks,
                             full_original_row_supplied=full_row, complete=checks_pass))
        if label["fact"]["kind"] == "prose":
            complete = all(any(row["phrases_covered"][i] for row in rows) for i in range(len(label["phrases"])))
        else:
            complete = any(row["complete"] for row in rows)
        points.append(dict(fact_id=fact_id, fully_covered=complete, source_checks=rows))
    return dict(value=sum(point["fully_covered"] for point in points) / len(points), facts=points,
                source_count=len(sources))


def main():
    frozen = read(ROOT / "frozen-cases.json")
    index = read(ROOT / "index-snapshot.json")
    documents = {document["file"]["file_id"]: document for document in index["files"]}
    chunks = {chunk["chunk_id"]: chunk for document in index["files"] for chunk in document["chunks"]}
    labels = resolve_labels(frozen, index)
    binding = dict(frozen_sha256=digest(ROOT / "frozen-cases.json"), index_sha256=digest(ROOT / "index-snapshot.json"), labels=labels,
                   children={identity: dict(file_id=chunk["file_id"], start_offset=chunk["start_offset"], end_offset=chunk["end_offset"],
                                            relevant_fact_ids=[fact for fact, label in labels.items() if candidate_covers(chunk, label)])
                             for identity, chunk in chunks.items()})
    baseline_binding = read(ROOT / "frozen-fact-labels.json")
    assert binding["labels"] == baseline_binding["labels"]
    assert binding["children"] == baseline_binding["children"]
    assert binding["frozen_sha256"] == baseline_binding["frozen_sha256"]
    # Freeze the annotation binding before reading any rankings or generated answers.
    if (DIRECTORY / "fact-labels.json").exists():
        assert read(DIRECTORY / "fact-labels.json") == binding
    else:
        write("fact-labels.json", binding)
    if sys.argv[1:] == ["labels"]:
        print(f"Frozen {len(labels)} source-bound facts across {len(chunks)} children before answer review.")
        return
    observations = records()
    rows = []
    for case in frozen["cases"]:
        facts = case["expected_fact_ids"]
        for arm in ["single", "planned"]:
            identity = case["id"] + "-" + arm
            answer = read(ROOT / (identity + ".json"))
            result = final_result(observations, identity)
            per_query = []
            for run in query_runs(result):
                diagnostic = run["diagnostics"]
                for stage in ["vector_matches", "bm25_matches", "fused_matches", "reranked"]:
                    matches = (diagnostic.get("rerank") or {}).get("matches") if stage == "reranked" else diagnostic.get(stage)
                    if matches is None:
                        continue
                    ids = [match["chunk_id"] for match in matches]
                    per_query.append(dict(query_index=run["index"], round_index=run["round_index"], query=run["query"],
                                          stage=stage, candidate_count=len(ids), matches=matches,
                                          ranking_fact_labels=[dict(chunk_id=chunk_id, relevant_fact_ids=[fact for fact in facts if candidate_covers(chunks[chunk_id], labels[fact])]) for chunk_id in ids],
                                          scores=retrieval_scores(ids, facts, chunks, labels)))
            ids = selected_ids(result)
            diagnostic = evidence_diagnostics(result)
            rows.append(dict(case_id=case["id"], arm=arm, status=answer["status"], artifact="../" + identity + ".json",
                             selected_ids=ids, retrieval_observed=result is not None,
                             queries_executed=len(query_runs(result)),
                             document_scope=(answer.get("answer", {}).get("retrieval") or {}).get("document_scope"),
                             scores=retrieval_scores(ids, facts, chunks, labels) if result is not None else None,
                             per_query=per_query, final_structural_coverage=supplied_coverage(answer.get("answer", {}).get("sources", []), facts, labels, documents),
                             evidence_tokens=diagnostic.get("evidence_tokens") if diagnostic else None,
                             context_budget=diagnostic.get("max_tokens") if diagnostic else None,
                             budget_exclusions=diagnostic.get("excluded") if diagnostic else [],
                             unexpanded_parents=diagnostic.get("unexpanded_parents") if diagnostic else [],
                             final_sources_available=answer["status"] == "completed"))
    output_name = sys.argv[1] if sys.argv[1:] else "retrieval-diagnostics.json"
    write(output_name, dict(K=K, label_artifact="fact-labels.json", rows=rows,
        frozen_sha256=digest(ROOT / "frozen-cases.json"), index_sha256=digest(ROOT / "index-snapshot.json"),
        method="Fact Recall: complete target cell or all required prose phrases in the top five child slices. Cell labels are bound to verified original-page state rows and complete header paths, not value substrings. Blank facts require the whole row slice. Binary child relevance requires one complete target cell or required prose phrase; generic header-only chunks are irrelevant. Precision denominator is five even with fewer candidates; MRR cutoff five; binary NDCG uses all frozen one-file children for IDCG. Candidate metrics exclude expansion/header supplements. Final structural coverage separately checks actual supplied exact text, cell tuples, row and header context; blank proof additionally requires the entire original row. Independent semantic review remains authoritative for answer/evidence quality.",
        comparison="Compare with the exact six-request baseline in 20260927-dense-table-acceptance. Questions, fact bindings, indexed extraction and embeddings are fixed; production context/packing/scope changes can alter new generated plans, queries and rankings. See index-reuse.json for the byte-identical pre-run index copy."))
    print(f"Retained {len(labels)} resolved facts and {len(rows)} retrieval/supplied-evidence rows.")


if __name__ == "__main__":
    main()
