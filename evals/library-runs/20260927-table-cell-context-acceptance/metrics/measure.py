"""Aggregate the six recorded requests and single-reviewer assessment without API calls."""

from collections import Counter, defaultdict
import json
import statistics
import sys

from analyze import DIRECTORY, ROOT, digest, distribution, evidence_diagnostics, final_result, query_runs, read, records, selected_ids, write

sys.path.insert(0, str(ROOT))
from record_check import METRICS

DIAGNOSTICS = sys.argv[1] if sys.argv[1:] else "retrieval-diagnostics.json"


def mean(values):
    return statistics.mean(values) if values else None


def measured(value, unit, population, method, n, artifact, aggregation="macro mean"):
    return dict(status="measured", value=value, unit=unit, sample_count=n, population=population,
                method=method, aggregation=aggregation, artifact=artifact)


def absent(status, reason, population, artifact):
    return dict(status=status, value=None, unit=None, sample_count=None, population=population,
                reason=reason, method=reason, aggregation="none", artifact=artifact)


def provider_usage(observations):
    by_model = defaultdict(list)
    missing = []
    for record in observations:
        if record["kind"] == "sdk_complete":
            result = record.get("result")
        elif record["kind"] == "sdk_stream_terminal":
            result = record.get("event", {}).get("response")
        else:
            continue
        if result is None or result.get("usage") is None:
            missing.append(record["call_id"])
            continue
        by_model[result["model"]].append(result["usage"])
    models = {}
    for model, usages in by_model.items():
        output = dict(calls=len(usages), raw_usage=usages)
        for field, getter in [
            ("input_tokens", lambda item: item.get("input_tokens", item.get("prompt_tokens"))),
            ("output_tokens", lambda item: item.get("output_tokens")),
            ("cached_input_tokens", lambda item: (item.get("input_tokens_details") or {}).get("cached_tokens")),
            ("total_tokens", lambda item: item.get("total_tokens")),
        ]:
            values = [getter(item) for item in usages]
            output[field] = sum(values) if all(value is not None for value in values) else None
            if output[field] is None:
                status = "not_applicable" if field == "output_tokens" and model.startswith("text-embedding-") else "unavailable"
                output[field + "_status"] = status
                output[field + "_reason"] = "Embedding calls return vectors, not generated text." if status == "not_applicable" else "At least one actual provider response omits this field."
        models[model] = output
    return dict(by_model=models, sdk_calls_started=sum(row["kind"] == "sdk_start" for row in observations),
                terminal_results_without_usage=missing,
                billed_cost=dict(status="unavailable", value=None, reason="No provider billing statement supplied; no estimated or fabricated bill."),
                local_compute_cost=dict(status="unavailable", value=None, reason="No local energy/hardware cost measurement."))


def stage_stats(observations, identities):
    stages = defaultdict(list)
    starts = {row["call_id"]: row for row in observations if row["kind"] == "sdk_start"}
    for row in observations:
        if row["kind"] == "stage":
            stages[row["stage"]].append(row["seconds"])
            diagnostic = evidence_diagnostics(row.get("result"))
            if diagnostic and diagnostic.get("packing_seconds") is not None:
                stages["packing_observed_call"].append(diagnostic["packing_seconds"])
        if row["kind"] in {"sdk_complete", "sdk_error", "sdk_stream_terminal"}:
            start = starts[row["call_id"]]
            stage = "embedding_sdk" if start["api"] == "embeddings" else (
                "answer_generation_sdk" if start["input"].get("stream") else
                start["input"].get("text", {}).get("format", {}).get("name", "answer_or_rewrite"))
            stages[stage].append(row["seconds"])
    for identity in identities:
        result = final_result(observations, identity)
        for run in query_runs(result):
            for key in ["embedding_seconds", "rerank_seconds"]:
                if run["diagnostics"].get(key) is not None:
                    stages[key].append(run["diagnostics"][key])
        if result and "trace" in result:
            for key in ["scope_seconds", "merge_seconds"]:
                if result["trace"].get(key) is not None:
                    stages[key].append(result["trace"][key])
        elif result and result["diagnostics"].get("scope_seconds") is not None:
            stages["scope_seconds"].append(result["diagnostics"]["scope_seconds"])
    return {key: distribution(values) for key, values in stages.items()}


def saved_sources_match(answer):
    if answer["status"] != "completed":
        return False
    saved = [{key: value for key, value in source.items() if key != "file_deleted"}
             for source in answer["saved_message"]["sources"]]
    return saved == answer["answer"]["sources"]


def response_path(answer, observations):
    identity = answer["case_id"] + "-" + answer["arm"]
    scope = (answer.get("answer", {}).get("retrieval") or {}).get("document_scope")
    if scope is not None and scope["status"] != "resolved":
        return "scope_rejection"
    if any(row["kind"] == "sdk_start" and row["request"] == identity and row["input"].get("stream") for row in observations):
        return "provider_generated"
    return "programmatic_after_retrieval"


def score_group(answers, reviewed, retrieval, observations, frozen, runtime, command):
    n = len(answers)
    scope = f"{n} original-page-answerable dense-table question/mode pairs"
    inventory = {}
    for key in METRICS[:5]:
        values = [row["scores"][key] for row in retrieval if row["scores"] is not None]
        inventory[key] = measured(mean(values), "ratio", scope,
            "K=5 final selected children. Source-bound cell/fact labels; fact Recall and binary child Precision use different units. Blank labels require complete original row slices. See fact-labels.json and retrieval-diagnostics.json for exact definitions.",
            len(values), DIAGNOSTICS) if values else absent("unavailable", "No recorded retrieval result in this subset.", scope, DIAGNOSTICS)
        stage_values = defaultdict(list)
        for row in retrieval:
            for query in row["per_query"]:
                stage_values[query["stage"]].append(query["scores"][key])
        inventory[key]["per_query_stage_metrics"] = {stage: dict(value=mean(values), query_count=len(values),
            aggregation="macro mean per executed query; planned requests can execute multiple queries") for stage, values in stage_values.items()}
        inventory[key]["requests_without_observed_retrieval"] = sum(row["scores"] is None for row in retrieval)
    points = [point for row in reviewed for point in row["points"]]
    for key, field in [("Final evidence coverage", "supplied_evidence_coverage"), ("Answer correctness", "reference_correctness"), ("Answer completeness", "completeness")]:
        inventory[key] = measured(mean([mean([point[field] for point in row["points"]]) for row in reviewed]), "score 0..1", scope,
            "Frozen 0/0.5/1 protocol; single Codex model review against original-page facts and actual supplied context. Blank contents require explicit row, empty positions, parent and leaf headers. An honest context limitation can be faithful but incomplete.",
            n, "../review/reviewed-cases.json")
        inventory[key].update(point_micro_average=mean([point[field] for point in points]), point_count=len(points))
    inventory["Final evidence coverage"]["structural_diagnostic"] = dict(value=mean([row["final_structural_coverage"]["value"] for row in retrieval]),
        method="Actual source/supplement slices, exact table-cell tuples, row labels, full header paths and report-period cells. Blank targets additionally require a complete supplied original row. A separate audit confirms every actual SDK Sources block equals the packed evidence and preserves canonical excerpts and the derived cell readings; original coordinates are retained in source metadata. Separate from semantic model review.",
        artifact=DIAGNOSTICS, actual_context_audit_artifact="actual-context-audit.json")
    claims = [claim for row in reviewed for claim in row["factual_claim_groups"]]
    for key, field in [("Faithfulness", "context_support"), ("Citation support", "citation_support"), ("Citation coverage", "citation_coverage")]:
        values = [claim[field] for claim in claims if claim[field] is not None]
        inventory[key] = measured(mean(values), "score 0..1", "Factual claim groups in completed answers; errors and claim-free refusals excluded",
            "Frozen paragraph/bullet rubric; actual supplied context and each group's cited sources reviewed. Uncited groups remain in citation coverage but have no citation-support denominator.",
            len(values), "../review/reviewed-cases.json", "micro mean over reviewed claim groups") if values else absent("not_applicable", "No applicable factual claim groups.", scope, "../review/reviewed-cases.json")
    inventory["Answer relevance"] = measured(mean([row["relevance"] for row in reviewed]), "score 0..1", scope,
        "Frozen relevance rubric applied independently from correctness and completeness.", n, "../review/reviewed-cases.json")
    case_map = {case["id"]: case for case in frozen["cases"]}
    unanswerable = [row for row in reviewed if not case_map[row["case_id"]]["answerable"]]
    answerable = [row for row in reviewed if case_map[row["case_id"]]["answerable"]]
    inventory["Abstention"] = measured(dict(
        appropriate=dict(status="measured" if unanswerable else "not_applicable", numerator=sum(row["appropriate_abstention"] for row in unanswerable) if unanswerable else None,
            denominator=len(unanswerable), rate=mean([row["appropriate_abstention"] for row in unanswerable]), reason=None if unanswerable else "No fully unanswerable questions in this workload."),
        incorrect=dict(numerator=sum(row["incorrect_abstention"] for row in answerable), denominator=len(answerable), rate=mean([row["incorrect_abstention"] for row in answerable]))),
        "counts and rates", scope, "Full refusals only. Point-level uncertainty is separately reviewed, and printed blanks are answerable cell contents. Errors are not abstentions.", n, "../review/reviewed-cases.json", "separate denominators")
    for key, field in [("First-answer-delta latency", "first_answer_delta_seconds"), ("Complete-response latency", "complete_response_seconds")]:
        values = [answer[field] for answer in answers if answer["status"] == "completed" and answer.get(field) is not None]
        inventory[key] = measured(distribution(values), "seconds", "Completed SSE requests in this subset",
            "Client perf_counter from HTTP start to first nonempty answer delta / stream closure. Startup excluded; request and provider/network waits included. These boundaries are distinct.",
            len(values), "../case-arm JSON files", "mean/P50/P95; linear interpolation") if values else absent("unavailable", "No completed request exposes this timing.", scope, "../case-arm JSON files")
        failed = [answer for answer in answers if answer["status"] != "completed"]
        inventory[key]["unsuccessful_requests"] = dict(count=len(failed), observed_values=distribution([answer[field] for answer in failed if answer.get(field) is not None]),
            missing_values=sum(answer.get(field) is None for answer in failed), method="Failed/incomplete timings remain separate. Missing first deltas are not replaced by response completion time.")
        inventory[key]["by_response_path"] = {path: distribution([answer[field] for answer in answers
            if answer["status"] == "completed" and answer.get(field) is not None and response_path(answer, observations) == path])
            for path in sorted({response_path(answer, observations) for answer in answers})}
        inventory[key]["response_path_caveat"] = "Scope rejections and programmatic replies can complete without answer generation. Do not interpret the mixed aggregate as normal generation performance."
    identities = {answer["case_id"] + "-" + answer["arm"] for answer in answers}
    observed = [row for row in observations if row["request"] in identities]
    inventory["Stage latency"] = measured(stage_stats(observed, identities), "seconds", "Actual observed stages and SDK calls in this subset",
        "SDK timers include provider/network waiting. Final cumulative traces supply each query once. Stage distributions overlap and must not be summed. Startup excluded; lazy reranker loading may affect the first query.",
        len(observed), "../server-observations.jsonl", "per-stage mean/P50/P95 and sample counts")
    inventory["Stage latency"]["server_startup"] = dict(seconds=runtime["startup_seconds"], sample_count=1, included_in_answer_latency=False, artifact="../resolved-runtime.json")
    inventory["Stage latency"]["unavailable"] = dict(search_fusion_separate="No dedicated wall timer; do not infer by subtraction.",
        provider_queue_separate="Provider queue duration is not exposed.", model_loading_separate="Lazy model loading has no separate timer.")
    inventory["Token usage and cost"] = measured(provider_usage(observed), "provider tokens; actual billing unavailable", scope,
        "Actual SDK terminal usage including planner/assessor calls, summed by provider-resolved model. No token estimates or provider billing estimates.",
        sum(row["kind"] in {"sdk_complete", "sdk_stream_terminal"} for row in observed), "../server-observations.jsonl", "sum by resolved model")
    inventory["Token usage and cost"]["local_evidence_tokens"] = dict(values=[row["evidence_tokens"] for row in retrieval],
        mean=mean([row["evidence_tokens"] for row in retrieval if row["evidence_tokens"] is not None]), budgets=[row["context_budget"] for row in retrieval],
        method="Production cl100k_base context counts, distinct from provider tokens. Failed candidate contexts may not reach generation.")
    statuses = Counter(answer["status"] for answer in answers)
    sdk_errors = [row for row in observed if row["kind"] == "sdk_error"]
    retries = runtime["settings"]["openai_max_retries"]
    reliability = dict(intended_requests=n, submitted_requests=n - statuses["blocked"], completed=statuses["completed"], errors=statuses["error"],
        incomplete=statuses["incomplete"], blocked=statuses["blocked"], success_rate=statuses["completed"] / n, error_rate=statuses["error"] / n,
        observed_sdk_errors=len(sdk_errors), observed_sdk_timeouts=sum("Timeout" in row.get("error_type", "") for row in sdk_errors),
        client_timeouts=sum("Timeout" in answer.get("error_type", "") for answer in answers),
        sdk_stream_failed=sum(row["kind"] == "sdk_stream_terminal" and row.get("event", {}).get("type") == "response.failed" for row in observed),
        sdk_stream_incomplete=sum(row["kind"] == "sdk_stream_terminal" and row.get("event", {}).get("type") == "response.incomplete" for row in observed),
        http_status_counts=dict(Counter(str(answer.get("http_status")) for answer in answers)), sdk_retry_configuration=retries,
        retries=0 if retries == 0 else None, application_replays=0,
        response_path_counts=dict(Counter(response_path(answer, observations) for answer in answers)),
        raw_history_sources_match_counts=dict(Counter(str(answer.get("history_sources_match")) for answer in answers)),
        saved_source_parity=sum(saved_sources_match(answer) for answer in answers),
        saved_answer_and_trace_parity=sum(bool(answer.get("history_matches") and answer.get("history_retrieval_matches")) for answer in answers if answer["status"] == "completed"),
        source_comparison="All source fields compared exactly except the saved-history file_deleted lifecycle flag.")
    inventory["Reliability"] = measured(reliability, "counts and rates", scope, "Actual request terminal statuses, SDK errors and history parity. One request per pair; no automatic retries or reruns.", n, "../case-arm JSON files", "counts and rates over intended requests")
    inventory["Concurrency and throughput"] = measured(dict(concurrency=1, completed=statuses["completed"], workload_wall_seconds=command["duration_seconds"],
        completed_per_workload_second=statuses["completed"] / command["duration_seconds"]), "completed requests/second", "One sequential alternating six-request command",
        "Command wall includes both arms, setup and history/client I/O. Arm contributions use the same denominator and sum to the overall rate; this is not load capacity.", n, "../answers-1.json", "whole command wall-clock rate")
    inventory["Ingestion and index"] = absent("not_applicable", "Answer subset reads a byte-identical isolated copy of the baseline index; no fresh upload, parse, embedding or index update.", scope, "../index-reuse.json")
    assert set(inventory) == set(METRICS)
    return inventory


def preparation_inventory(observations):
    reuse = read(ROOT / "index-reuse.json")
    index = read(ROOT / "index-snapshot.json")
    scope = "Isolated byte-identical copy of the stopped baseline index; no ingestion"
    inventory = {key: absent("not_applicable", "Index-copy preparation has no retrieval, provider, generated answer, upload, parser or embedding workload.", scope, "../index-reuse.json") for key in METRICS}
    inventory["Ingestion and index"] = measured(dict(file_count=len(index["files"]),
        page_count=sum(len(row["extraction"]["pages"]) for row in index["files"]),
        child_count=sum(len(row["chunks"]) for row in index["files"]),
        parent_count=sum(len(row["parents"]) for row in index["files"]),
        snapshot_index_bytes=index["index_bytes"], copied_file_bytes=sum(row["bytes"] for row in reuse["source_file_hashes"].values()),
        byte_identical_copy=reuse["byte_identical_copy"], source_unchanged_after_copy=reuse["source_unchanged_after_copy"],
        source_hashes=[row["extraction"]["source_hash"] for row in index["files"]],
        extraction_revisions=[row["extraction"]["revision_id"] for row in index["files"]],
        snapshot_sha256=digest(ROOT / "index-snapshot.json"),
        upload_parse_index_duration=dict(status="not_applicable", value=None, reason="No ingestion operation; do not reuse historical ingestion timing as a new measurement."),
        update_delete=dict(status="not_applicable", value=None, reason="No update or deletion operation.")),
        "counts and bytes; no ingestion time", scope, "Inspect the preserved baseline copy and read-only API snapshot. Corpus, extracted cells, chunk IDs and embeddings are fixed; conversations from the baseline are preserved but six requests start new conversations.",
        1, "../index-reuse.json; ../index-snapshot.json", "single index inventory")
    return inventory


def historical_comparison(frozen, reviewed, answers):
    directory = ROOT.parent / "20260927-table-context-scope-acceptance"
    old = read(directory / "review/reviewed-cases.json")["rows"]
    old_observations = [json.loads(line) for line in (directory / "server-observations.jsonl").read_text().splitlines()]
    current_observations = records()
    assert read(directory / "frozen-cases.json") == frozen
    assert read(directory / "index-snapshot.json")["files"] == read(ROOT / "index-snapshot.json")["files"]
    comparisons = []
    for before in old:
        after = next(row for row in reviewed if row["case_id"] == before["case_id"] and row["arm"] == before["arm"])
        identity = before["case_id"] + "-" + before["arm"]
        previous_answer = read(directory / (identity + ".json"))
        current_answer = next(answer for answer in answers if answer["case_id"] == before["case_id"] and answer["arm"] == before["arm"])
        assert previous_answer["request"]["question"] == current_answer["request"]["question"]
        comparisons.append(dict(case_id=before["case_id"], arm=before["arm"], before_status=before["answer_status"], after_status=after["answer_status"],
            points=[dict(fact_id=point["fact_id"], **{field: dict(before=point[field], after=next(p[field] for p in after["points"] if p["fact_id"] == point["fact_id"]))
                    for field in ["reference_correctness", "completeness", "supplied_evidence_coverage"]}) for point in before["points"]],
            before_selected_ids=selected_ids(final_result(old_observations, identity)),
            before_answer_artifact="../../20260927-table-context-scope-acceptance/" + identity + ".json",
            after_answer_artifact="../" + identity + ".json",
            response_paths=dict(before=response_path(previous_answer, old_observations), after=response_path(current_answer, current_observations)),
            first_answer_delta_seconds=dict(before=previous_answer.get("first_answer_delta_seconds"), after=current_answer.get("first_answer_delta_seconds")),
            complete_response_seconds=dict(before=previous_answer.get("complete_response_seconds"), after=current_answer.get("complete_response_seconds")),
            before_raw_rankings_artifact="../../20260927-table-context-scope-acceptance/server-observations.jsonl",
            after_raw_rankings_artifact="../server-observations.jsonl"))
    return dict(rows=comparisons,
                limitations="Same frozen three questions, two modes, corpus, extraction, embeddings, annotations and runtime; table reading representation changed; parser, scope and packing implementation unchanged. This is one stochastic development-subset pass, not held-out generalization. Plans, sufficiency checks and candidate rankings may change with new context. Before/after latency paths differ when a prior refusal becomes a generated answer; no causal performance claim.",
                method="Baseline requested-point scores retained verbatim, with current single Codex review. Compare all six question/mode pairs on the byte-identical isolated index copy, preserve improvements and regressions per point, and retain both raw answers and actual supplied evidence.")


def main():
    frozen = read(ROOT / "frozen-cases.json")
    reviewed = read(ROOT / "review/reviewed-cases.json")["rows"]
    answers = [read(ROOT / (case["id"] + "-" + arm + ".json")) for case in frozen["cases"] for arm in ["single", "planned"]]
    retrieval = read(DIRECTORY / DIAGNOSTICS)["rows"]
    observations = records()
    runtime = read(ROOT / "resolved-runtime.json")
    command = read(ROOT / "answers-1.json")
    pairs = {(case["id"], arm) for case in frozen["cases"] for arm in ["single", "planned"]}
    assert len(reviewed) == len(pairs) and {(row["case_id"], row["arm"]) for row in reviewed} == pairs
    for row in reviewed:
        case = next(case for case in frozen["cases"] if case["id"] == row["case_id"])
        assert {point["fact_id"] for point in row["points"]} == set(case["expected_fact_ids"])
    groups = {arm: score_group([a for a in answers if arm == "all" or a["arm"] == arm],
        [row for row in reviewed if arm == "all" or row["arm"] == arm], [row for row in retrieval if arm == "all" or row["arm"] == arm],
        observations, frozen, runtime, command) for arm in ["single", "planned", "all"]}
    points = [point for row in reviewed for point in row["points"]]
    claims = [claim for row in reviewed for claim in row["factual_claim_groups"]]
    grouped = [point for point in points if len(frozen["facts"][point["fact_id"]].get("header_path", [])) > 1]
    def gate(numerator, denominator):
        return dict(passed=denominator > 0 and numerator == denominator, numerator=numerator, denominator=denominator)
    gates = dict(
        six_requests_complete=gate(sum(answer["status"] == "completed" for answer in answers), len(answers)),
        requested_points_correct_and_complete=gate(sum(point["reference_correctness"] == point["completeness"] == 1 for point in points), len(points)),
        factual_claim_groups_supported_and_individually_cited=gate(sum(claim["context_support"] == claim["citation_support"] == claim["citation_coverage"] == 1 for claim in claims), len(claims)),
        grouped_and_blank_distinctions_correct=gate(sum(point["reference_correctness"] == point["completeness"] == 1 for point in grouped), len(grouped)),
        no_incorrect_full_refusals=gate(sum(not row["incorrect_abstention"] for row in reviewed), len(reviewed)),
        no_unsupported_factual_claims=gate(sum(claim["context_support"] == 1 for claim in claims), len(claims)),
        saved_answer_sources_retrieval_match=gate(sum(bool(answer.get("history_matches") and answer.get("history_retrieval_matches") and saved_sources_match(answer)) for answer in answers), len(answers)))
    historical = historical_comparison(frozen, reviewed, answers)
    for comparison in historical["rows"]:
        comparison["after_selected_ids"] = next(row["selected_ids"] for row in retrieval if row["case_id"] == comparison["case_id"] and row["arm"] == comparison["arm"])
    result = dict(scope="Three frozen dense-table questions × two modes on a byte-identical isolated copy of the baseline index; no ingestion, release or merge authorization.",
        reviewer="Single Codex model review under the frozen scoring rubric; no independent second reviewer, human review or paid judge.",
        metric_definition="Complete 20-metric inventory for each arm and all requests, with preparation separately scoped. Candidate retrieval, structural supplied coverage, and semantic answer review remain distinct.",
        groups=groups, scoped_gates=gates, historical_matched_case=historical, shared_preparation=preparation_inventory(observations),
        validity=dict(code_commit=runtime["code_commit"], resolved_runtime_artifact="../resolved-runtime.json", frozen_sha256=digest(ROOT / "frozen-cases.json"),
            index_sha256=digest(ROOT / "index-snapshot.json"), review_sha256=digest(ROOT / "review/reviewed-cases.json"),
            annotation_limit=frozen["annotation_scope"], latency_limit="One stochastic pass with three samples per arm; shared sequential process, provider/network waiting, caching and lazy model loading prevent causal performance attribution.",
            missing_populations=["fully unanswerable questions", "held-out corpus", "unannotated rows", "concurrency above one", "billing statement"],
            historical_records="Read-only comparison; prior questions, scores and artifacts were not changed."),
        evaluator_hashes={path.name: digest(path) for path in [DIRECTORY / "analyze.py", DIRECTORY / "measure.py"]},
        evaluator_attempts=dict(initial_diagnostics="retrieval-diagnostics.json", final_diagnostics=DIAGNOSTICS,
            correction="No semantic score or failed result is repaired. Every analysis attempt uses a new output/record name; any correction must remain explicit in the run report."),
        raw_artifacts=["../server-observations.jsonl", "../resolved-runtime.json", "../index-snapshot.json", "../index-reuse.json", "../answers-1.json", "fact-labels.json", DIAGNOSTICS, "actual-context-audit.json", "../review/reviewed-cases.json"])
    write("measurement.json", result)
    for arm, metrics in groups.items():
        print(arm, "correctness", metrics["Answer correctness"]["value"], "completeness", metrics["Answer completeness"]["value"],
              "first_delta", metrics["First-answer-delta latency"]["value"], "completion", metrics["Complete-response latency"]["value"])


if __name__ == "__main__":
    main()
