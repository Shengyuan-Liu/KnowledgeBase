"""Aggregate the six live financial requests and their frozen historical baseline."""

from collections import Counter, defaultdict
from hashlib import sha256
import json
import statistics

from analyze import BASE, FROZEN, ROOT, distribution, evidence_diagnostics, final_result, query_runs, records, write
from record_check import METRICS


def measured(value, unit, population, method, n, artifact, aggregation="macro mean"):
    return dict(status="measured", value=value, unit=unit, sample_count=n,
                population=population, method=method, aggregation=aggregation, artifact=artifact)


def absent(status, reason, population, artifact):
    return dict(status=status, value=None, unit=None, sample_count=None,
                population=population, reason=reason, method=reason, aggregation="none", artifact=artifact)


def mean(values):
    return statistics.mean(values) if values else None


def provider_usage(observations):
    by_model = defaultdict(list)
    missing = 0
    for record in observations:
        result = record.get("result") if record["kind"] == "sdk_complete" else record.get("event", {}).get("response") if record["kind"] == "sdk_stream_terminal" else None
        if result is None:
            continue
        usage = result.get("usage")
        if usage is None:
            missing += 1
            continue
        by_model[result["model"]].append(usage)
    models = {}
    for model, calls in by_model.items():
        output = dict(calls=len(calls))
        for field, getter in [
            ("input_tokens", lambda x: x.get("input_tokens", x.get("prompt_tokens"))),
            ("output_tokens", lambda x: x.get("output_tokens")),
            ("cached_input_tokens", lambda x: (x.get("input_tokens_details") or {}).get("cached_tokens")),
        ]:
            values = [getter(c) for c in calls]
            if all(v is not None for v in values):
                output[field] = sum(values)
            else:
                output[field] = None
                output[field + "_status"] = "not_applicable" if field == "output_tokens" and model.startswith("text-embedding-") else "unavailable"
                output[field + "_reason"] = "Embedding calls produce vectors, not generated text." if output[field + "_status"] == "not_applicable" else "At least one provider response omits this usage field."
        models[model] = output
    return dict(by_model=models, terminal_results_without_usage=missing,
                billed_cost=dict(status="unavailable", value=None, reason="Provider billing statement unavailable; no fabricated or estimated bill."),
                local_compute=dict(device="Apple Silicon; BGE reranker on MPS; resolved-runtime.json records exact configuration.",
                                   cost=None, cost_status="unavailable", reason="No local energy/hardware billing measurement."))


def stage_stats(observations, identities):
    stages = defaultdict(list)
    starts = {r["call_id"]: r for r in observations if r["kind"] == "sdk_start"}
    for row in observations:
        if row["kind"] == "stage":
            stages[row["stage"]].append(row["seconds"])
            diag = evidence_diagnostics(row.get("result"))
            if diag and diag.get("packing_seconds") is not None:
                stages["packing_observed_call"].append(diag["packing_seconds"])
        if row["kind"] in ["sdk_complete", "sdk_error", "sdk_stream_terminal"]:
            start = starts[row["call_id"]]
            if start["api"] == "embeddings":
                stage = "embedding_sdk"
            elif start["input"].get("stream"):
                stage = "answer_generation_sdk"
            else:
                stage = start["input"].get("text", {}).get("format", {}).get("name", "answer_or_rewrite")
            stages[stage].append(row["seconds"])
    # Final cumulative traces contain every query once, including supplementary rounds.
    for identity in identities:
        result = final_result(observations, identity)
        for run in query_runs(result):
            diag = run["diagnostics"]
            for key in ["embedding_seconds", "rerank_seconds"]:
                if diag.get(key) is not None:
                    stages[key].append(diag[key])
        if result and "trace" in result:
            for key in ["scope_seconds", "merge_seconds"]:
                if result["trace"].get(key) is not None:
                    stages[key].append(result["trace"][key])
    return {key: distribution(values) for key, values in stages.items()}


def saved_sources_match(answer):
    if answer["status"] != "completed":
        return False
    saved = [{key: value for key, value in source.items() if key != "file_deleted"} for source in answer["saved_message"]["sources"]]
    return saved == answer["answer"]["sources"]


def score_group(pass_name, arm, answers, reviewed, retrieval, observations):
    n = len(answers)
    scope = f"{n} financial question/mode pairs; all answerable"
    artifact_prefix = "" if pass_name == "current" else "../20260927-financial-acceptance/"
    review_artifact = "reviewed-cases.json" if pass_name == "current" else "../20260927-financial-acceptance/reviewed-cases.json"
    runtime = json.loads(((ROOT if pass_name == "current" else BASE) / "resolved-runtime.json").read_text())
    inventory = {}
    for key in METRICS[:5]:
        inventory[key] = measured(mean([r["scores"][key] for r in retrieval]), "ratio", scope,
                                  "K=5 final selected children, frozen non-exhaustive literal anchor labels. Fact Recall and child Precision are different units; errors retain observed retrieval.",
                                  n, "retrieval-diagnostics.json")
        stage_values = defaultdict(list)
        for row in retrieval:
            for query in row["per_query"]:
                stage_values[query["stage"]].append(query["scores"][key])
        inventory[key]["per_query_stage_metrics"] = {
            stage: dict(value=mean(values), query_count=len(values), aggregation="macro mean per executed query; planned requests can run several queries")
            for stage, values in stage_values.items()
        }
    points = [point for row in reviewed for point in row["points"]]
    for key, field in [("Final evidence coverage", "supplied_evidence_coverage"), ("Answer correctness", "reference_correctness"), ("Answer completeness", "completeness")]:
        inventory[key] = measured(mean([mean([p[field] for p in r["points"]]) for r in reviewed]), "score 0..1", scope,
                                  "Unchanged 0/0.5/1 rubric; Codex model review against frozen original-page facts and actual supplied sources. Errors count zero for requested points.",
                                  n, review_artifact)
        inventory[key].update(point_micro_average=mean([p[field] for p in points]), point_count=len(points))
    inventory["Final evidence coverage"]["literal_anchor_diagnostic"] = dict(
        value=mean([r["final_literal_anchor_coverage"]["value"] for r in retrieval]),
        method="Same original page anchor spans including supplements; equivalent facts elsewhere may miss. This does not replace semantic evidence review.",
        artifact="retrieval-diagnostics.json")
    claims = [claim for row in reviewed for claim in row["factual_claim_groups"]]
    for key, field in [("Faithfulness", "context_support"), ("Citation support", "citation_support"), ("Citation coverage", "citation_coverage")]:
        values = [c[field] for c in claims if c[field] is not None]
        inventory[key] = measured(mean(values), "score 0..1", "Factual claim groups in completed answers; errors and claim-free refusals excluded",
                                  "Unchanged 0/0.5/1 model review of factual paragraphs/bullets against actual context and specifically cited sources; syntactic citation IDs are insufficient.",
                                  len(values), review_artifact, "micro mean over reviewed claim groups") if values else absent(
                                      "not_applicable", "No factual claim groups in this subset.", scope, review_artifact)
    inventory["Answer relevance"] = measured(mean([r["relevance"] for r in reviewed]), "score 0..1", scope,
                                             "1 for addressing the requested topic including relevant refusal; 0 for error/wrong document.", n, review_artifact)
    unanswerable = [c for c in FROZEN["cases"] if not c["answerable"]]
    inventory["Abstention"] = measured(dict(
        appropriate=dict(status="not_applicable" if not unanswerable else "measured", numerator=None if not unanswerable else sum(r["appropriate_abstention"] for r in reviewed),
                         denominator=len(unanswerable), rate=None if not unanswerable else sum(r["appropriate_abstention"] for r in reviewed) / len(unanswerable),
                         reason="No unanswerable questions in this targeted workload." if not unanswerable else None),
        incorrect=dict(numerator=sum(r["incorrect_abstention"] for r in reviewed), denominator=n,
                       rate=sum(r["incorrect_abstention"] for r in reviewed) / n)),
        "counts and rates", scope, "Full refusals only. Failed requests are errors, not abstentions. No unanswerable behavior validated here.", n, review_artifact, "separate denominators")
    for key, field in [("First-answer-delta latency", "first_answer_delta_seconds"), ("Complete-response latency", "complete_response_seconds")]:
        values = [a[field] for a in answers if a["status"] == "completed" and a.get(field) is not None]
        inventory[key] = measured(distribution(values), "seconds", "Completed SSE requests in this subset",
                                  "Client perf_counter from HTTP start to first nonempty answer delta / SSE close. Server startup excluded; request queue/provider waiting included; deterministic replies retained.",
                                  len(values), artifact_prefix + "case-arm JSON files", "mean/P50/P95; linear interpolation")
        unsuccessful = [a for a in answers if a["status"] != "completed"]
        inventory[key]["unsuccessful_requests"] = dict(count=len(unsuccessful), observed_values=distribution([a[field] for a in unsuccessful if a.get(field) is not None]), method="Retain observed failed/incomplete request timing separately from successful latency; absent first deltas are not replaced with completion time.")
    identities = {a["case_id"] + "-" + a["arm"] for a in answers}
    obs = [r for r in observations if r["request"] in identities]
    inventory["Stage latency"] = measured(stage_stats(obs, identities), "seconds", "Observed calls including failed downstream validation",
                                           "SDK boundaries include provider/network waits; retrieval entrypoint and packing diagnostic timers; final traces provide unique per-query rerank/embedding observations. Per-stage sample counts are explicit. Startup excluded; first request may include local lazy loading; no isolated cold/warm attribution.",
                                           len(obs), artifact_prefix + "server-observations.jsonl", "per-stage distributions")
    inventory["Stage latency"]["server_startup"] = dict(seconds=runtime["startup_seconds"], sample_count=1, included_in_answer_latency=False, artifact=artifact_prefix + "resolved-runtime.json")
    inventory["Stage latency"]["unavailable"] = {
        "search_fusion_separate": "No dedicated search/fusion wall timer; not inferred by subtracting unlike boundaries.",
        "provider_queue_separate": "Provider does not expose queue duration.",
        "model_loading_separate": "No separately instrumented lazy model load duration; may be included in first retrieval."}
    inventory["Token usage and cost"] = measured(provider_usage(obs), "provider tokens; billed cost unavailable", "Actual SDK terminal responses for selected requests",
                                                 "Preserved provider usage, including planner/assessor calls that later failed validation; no token estimation. Model identifiers are provider-resolved.",
                                                 sum(r["kind"] in ["sdk_complete", "sdk_stream_terminal"] for r in obs), artifact_prefix + "server-observations.jsonl", "sum by resolved model")
    inventory["Token usage and cost"]["local_evidence_tokens"] = dict(values=[r["evidence_tokens"] for r in retrieval],
                                                                     mean=mean([r["evidence_tokens"] for r in retrieval if r["evidence_tokens"] is not None]),
                                                                     max_budget=4096, method="Production cl100k_base exact context counts; not provider billing. Error final candidate contexts may never reach generation.")
    statuses = Counter(a["status"] for a in answers)
    zero_retry_config = runtime["settings"]["openai_max_retries"] == 0
    sdk_errors = [r for r in obs if r["kind"] == "sdk_error"]
    reliability = dict(intended_requests=n, submitted_requests=n - statuses["blocked"], completed=statuses["completed"],
                       errors=statuses["error"], incomplete=statuses["incomplete"], blocked=statuses["blocked"],
                       success_rate=statuses["completed"] / n, error_rate=statuses["error"] / n,
                       observed_sdk_errors=len(sdk_errors), observed_sdk_timeouts=sum("Timeout" in r.get("error_type", "") for r in sdk_errors),
                       client_timeouts=sum("Timeout" in a.get("error_type", "") for a in answers),
                       sdk_stream_failed=sum(r["kind"] == "sdk_stream_terminal" and r.get("event", {}).get("type") == "response.failed" for r in obs),
                       sdk_stream_incomplete=sum(r["kind"] == "sdk_stream_terminal" and r.get("event", {}).get("type") == "response.incomplete" for r in obs),
                       http_status_counts=dict(Counter(str(a.get("http_status")) for a in answers)),
                       sdk_retry_configuration=runtime["settings"]["openai_max_retries"],
                       application_replays=0, retries=0 if zero_retry_config else None,
                       error_http_close_latency=distribution([a["complete_response_seconds"] for a in answers if a["status"] == "error"]),
                       saved_source_parity=sum(saved_sources_match(a) for a in answers),
                       saved_source_comparison="Exact source payloads, excluding only saved-history file_deleted lifecycle flag.",
                       saved_answer_and_trace_parity=sum(bool(a.get("history_matches") and a.get("history_retrieval_matches")) for a in answers if a["status"] == "completed"))
    inventory["Reliability"] = measured(reliability, "counts and rates", scope,
                                        "Actual SSE terminal status, SDK errors and saved-history equality. SDK retries disabled; one request per pair. Completion alone does not establish correctness.", n, artifact_prefix + "case-arm JSON files", "counts; denominator intended requests")
    run_folder = ROOT if pass_name == "current" else BASE
    run = json.loads((run_folder / "answers-1.json").read_text())
    inventory["Concurrency and throughput"] = measured(dict(concurrency=1, completed=statuses["completed"],
                                                             workload_wall_seconds=run["duration_seconds"], completed_per_workload_second=statuses["completed"] / run["duration_seconds"]),
                                                        "completed requests/second", "One sequential alternating six-request command",
                                                        "Each pass has the same six-request workload. Command wall includes both arms, history/client I/O and setup; arm contributions add to overall throughput. No load-capacity or causal speed claim.", n, artifact_prefix + "answers-1.json", "command wall-clock rate")
    inventory["Ingestion and index"] = absent("not_applicable", "Answer-only pass: no upload/parser/reembedding/update/delete workload. The baseline preparation and current exact clone are documented separately in their preparation artifacts.", scope, artifact_prefix + "preparation.json")
    assert set(inventory) == set(METRICS)
    return inventory


def main():
    reviewed_current = json.loads((ROOT / "reviewed-cases.json").read_text())["rows"]
    reviewed_before = [r for r in json.loads((BASE / "reviewed-cases.json").read_text())["rows"] if r["case_id"] in {c["id"] for c in FROZEN["cases"]}]
    expected_pairs = {(case["id"], arm) for case in FROZEN["cases"] for arm in ["single", "planned"]}
    for rows in [reviewed_before, reviewed_current]:
        assert len(rows) == len(expected_pairs) and {(r["case_id"], r["arm"]) for r in rows} == expected_pairs
    retrieval = json.loads((ROOT / "retrieval-diagnostics.json").read_text())
    groups = {}
    answers_by_pass = {}
    for pass_name, folder, review in [("baseline", BASE, reviewed_before), ("current", ROOT, reviewed_current)]:
        answers = [json.loads((folder / (case["id"] + "-" + arm + ".json")).read_text()) for case in FROZEN["cases"] for arm in ["single", "planned"]]
        answers_by_pass[pass_name] = answers
        observations = records(folder)
        for arm in ["single", "planned", "all"]:
            groups[pass_name + "-" + arm] = score_group(pass_name, arm,
                [a for a in answers if arm == "all" or a["arm"] == arm],
                [r for r in review if arm == "all" or r["arm"] == arm],
                [r for r in retrieval["rows"] if r["pass_name"] == pass_name and (arm == "all" or r["arm"] == arm)], observations)
    comparisons = []
    for before in reviewed_before:
        after = next(r for r in reviewed_current if r["case_id"] == before["case_id"] and r["arm"] == before["arm"])
        row = dict(case_id=before["case_id"], arm=before["arm"], before_status=before["answer_status"], after_status=after["answer_status"], points=[])
        for old_point in before["points"]:
            new_point = next(p for p in after["points"] if p["fact_id"] == old_point["fact_id"])
            row["points"].append(dict(fact_id=old_point["fact_id"], **{
                field: dict(before=old_point[field], after=new_point[field], delta=new_point[field] - old_point[field])
                for field in ["reference_correctness", "completeness", "supplied_evidence_coverage"]}))
        row["claim_group_comparison"] = dict(before_count=len(before["factual_claim_groups"]), after_count=len(after["factual_claim_groups"]),
            **{field: dict(before=mean([claim[field] for claim in before["factual_claim_groups"] if claim[field] is not None]),
                           after=mean([claim[field] for claim in after["factual_claim_groups"] if claim[field] is not None]))
               for field in ["context_support", "citation_support", "citation_coverage"]})
        row["claim_group_comparison"]["method"] = "Same frozen paragraph/bullet rubric, separately counted actual claims in each answer; wording and group counts can change."
        row["incorrect_abstention"] = dict(before=before["incorrect_abstention"], after=after["incorrect_abstention"])
        row["before_note"] = before["note"]
        row["after_note"] = after["note"]
        comparisons.append(row)
    old_runtime = json.loads((BASE / "resolved-runtime.json").read_text())
    new_runtime = json.loads((ROOT / "resolved-runtime.json").read_text())
    settings_diff = {key: dict(before=old_runtime["settings"].get(key), after=new_runtime["settings"].get(key)) for key in set(old_runtime["settings"]) | set(new_runtime["settings"]) if old_runtime["settings"].get(key) != new_runtime["settings"].get(key)}
    preparation_obs = [r for r in records(ROOT) if r["request"] not in {a["case_id"] + "-" + a["arm"] for a in answers_by_pass["current"]}]
    preparation = json.loads((ROOT / "preparation.json").read_text())
    assert preparation["copy_byte_identical"] and preparation["source_unchanged"]
    assert preparation["source_file_hashes"] == preparation["cloned_file_hashes_before_open"]
    assert preparation["provider_calls"] == preparation["regenerated_vectors"] == 0
    preparation_inventory = {key: absent("not_applicable", "Index copy and verification exercise no model, retrieval, generation or ingestion workload.", "Disposable byte-identical index clone", "preparation.json") for key in METRICS}
    preparation_inventory["Token usage and cost"] = absent("not_applicable", "No provider call during index cloning; existing vectors copied unchanged.", "preparation", "preparation.json")
    preparation_attempts = [{"artifact": path.name, "exit_code": json.loads(path.read_text())["exit_code"], "duration_seconds": json.loads(path.read_text())["duration_seconds"]} for path in sorted(ROOT.glob("prepare-[0-9]*.json"))]
    preparation_inventory["Reliability"] = measured(dict(final_verification=preparation, command_attempts=preparation_attempts, failed_commands=sum(attempt["exit_code"] != 0 for attempt in preparation_attempts)), "counts and source/clone hashes", "Preparation copy and verification attempts", "Final source/index parity verified before live calls; failed attempts remain explicit and did not invoke providers.", len(preparation_attempts), "preparation.json; prepare-1.json; prepare-2.json", "verification facts and command attempts, not production request reliability")
    preparation_inventory["Ingestion and index"] = absent("not_applicable", "No new upload, parsing, embedding, update or deletion; the existing exact index clone and its hash/size verification are preparation details.", "preparation", "preparation.json")
    assert not [r for r in preparation_obs if r["kind"] == "sdk_start"], "Preparation must not invoke providers."
    gates = {}
    for pass_name, rows in [("baseline", reviewed_before), ("current", reviewed_current)]:
        answers = answers_by_pass[pass_name]
        points = [p for row in rows for p in row["points"]]
        claims = [c for row in rows for c in row["factual_claim_groups"]]
        gates[pass_name] = {
            "six_requests_complete": dict(passed=all(a["status"] == "completed" for a in answers), numerator=sum(a["status"] == "completed" for a in answers), denominator=len(answers)),
            "requested_facts_correct_and_complete": dict(passed=all(p["reference_correctness"] == 1 and p["completeness"] == 1 for p in points), numerator=sum(p["reference_correctness"] == 1 and p["completeness"] == 1 for p in points), denominator=len(points)),
            "all_claim_groups_have_supporting_inline_citations": dict(passed=bool(claims) and all(c["citation_coverage"] == 1 and c["context_support"] == 1 for c in claims), numerator=sum(c["citation_coverage"] == 1 and c["context_support"] == 1 for c in claims), denominator=len(claims)),
            "no_incorrect_abstentions": dict(passed=not any(row["incorrect_abstention"] for row in rows), count=sum(row["incorrect_abstention"] for row in rows), denominator=len(rows)),
            "no_unsupported_cited_claims": dict(passed=not any(c["citation_support"] is not None and c["citation_support"] < 1 for c in claims), count=sum(c["citation_support"] is not None and c["citation_support"] < 1 for c in claims), denominator=sum(c["citation_support"] is not None for c in claims)),
            "saved_answer_sources_and_retrieval_match": dict(passed=all(a.get("history_matches") and a.get("history_retrieval_matches") and saved_sources_match(a) for a in answers), numerator=sum(bool(a.get("history_matches") and a.get("history_retrieval_matches") and saved_sources_match(a)) for a in answers), denominator=len(answers), source_comparison="Only history file_deleted lifecycle flag excluded; all source content and provenance compared exactly."),
        }
    result = dict(scope="Targeted citation repair acceptance only; three frozen questions x two retrieval modes. No release or merge authorization.",
                  reviewer="Codex model review; no independent human review or paid LLM judge",
                  metric_definition="20 required metrics per arm and overall; candidate retrieval and final supplied evidence are distinct. Quality results are model assessments under the unchanged retained rubric.",
                  baseline="../20260927-financial-acceptance", current=".",
                  frozen_sha256=sha256((ROOT / "frozen-cases.json").read_bytes()).hexdigest(),
                  groups=groups, per_case_comparison=comparisons, scoped_gates=gates,
                  validity=dict(same_questions_facts_and_original_pdf=True,
                                exact_index_clone="Immediate previous financial-acceptance index cloned, including stored embedding vectors; no reembedding. Preparation parity records are authoritative. Actual live query generation and retrieved rankings can still differ.",
                                preparation_artifact="preparation.json",
                                settings_diff=settings_diff, before_code_commit=old_runtime["code_commit"], after_code_commit=new_runtime["code_commit"],
                                source_hash_differences=[key for key in set(old_runtime["source_hashes"]) | set(new_runtime["source_hashes"]) if old_runtime["source_hashes"].get(key) != new_runtime["source_hashes"].get(key)],
                                latency_limit="One stochastic six-request pass per version; process state, lazy model loading, provider/network wait and cache conditions can differ. Descriptive timing does not isolate the effect of prompts or attachment changes.",
                                missing_populations=["unanswerable questions", "genuine contradictory sources", "dense table extraction repair", "held-out corpus", "concurrency above one", "billing statement"],
                                baseline_review_note="Immediate baseline reviewed-cases.json and its scores are retained verbatim; no rescoring or edits to historical records.",
                                review_scope_caveat="The unchanged baseline grouping rules allow fiscal-Q4/full-fiscal-year wording as reasonable inference from the same-ending three/twelve-month periods. Scores under that frozen allowance do not establish literal support for every added period label. A separate strict-source qualifier audit is retained by the reviewer without changing comparison scores."),
                  preparation_provider_usage=dict(provider_calls=preparation["provider_calls"], regenerated_vectors=preparation["regenerated_vectors"], provider_cost=dict(status="not_applicable", value=None, reason="No provider call during cloning.")),
                  shared_preparation=preparation_inventory,
                  raw_artifacts=["server-observations.jsonl", "resolved-runtime.json", "retrieval-diagnostics.json", "reviewed-cases.json", "answers-1.json", "preparation.json"])
    write("measurement.json", result)
    for label, group in groups.items():
        print(label, "completed", group["Reliability"]["value"]["completed"], "correctness", group["Answer correctness"]["value"],
              "evidence", group["Final evidence coverage"]["value"], "complete_latency", group["Complete-response latency"]["value"])


if __name__ == "__main__":
    main()
