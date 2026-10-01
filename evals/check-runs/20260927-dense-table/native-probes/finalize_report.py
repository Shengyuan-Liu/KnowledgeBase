"""Collect retained native probe measurements and verify this report's local links."""
from hashlib import sha256
import json
from pathlib import Path
import re

DIRECTORY = Path(__file__).resolve().parent
target = DIRECTORY / "measurement.json"
if target.exists():
    raise SystemExit("This final measurement already exists.")
initial = json.loads((DIRECTORY / "initial-1.json").read_text())
review = json.loads((DIRECTORY / "review-1-result.json").read_text())
summaries = [json.loads((DIRECTORY / run / "summary.json").read_text()) for run in ["initial-1", "extended-1"]]
metrics = {name: {"status": "not_applicable", "value": None, "unit": None,
    "reason": "Native parser exploration only; no retrieval, generated answers, provider calls, ingestion, index or load workload.",
    "sample_count": None, "population": "eight offline native extraction variants",
    "method": "not exercised", "aggregation": "none", "artifact": "review-1-result.json"}
    for name in initial["metric_inventory"]}
metrics["Stage latency"].update(status="measured", value=review["latency"], unit="seconds", reason=None,
    sample_count=8, method="perf_counter around native page parsing and table variants; includes artifact serialization where timed",
    aggregation="mean, P50, P95 with linear interpolation; heterogeneous workloads reported separately")
metrics["Reliability"].update(status="measured", value=review["reliability"], unit="variant attempts", reason=None,
    sample_count=8, method="Retained parser variant completion records; success is not extraction correctness", aggregation="counts")
wall = sum(summary["duration_seconds"] for summary in summaries)
metrics["Concurrency and throughput"].update(status="measured",
    value={"concurrency": 1, "completed_variants": 8, "measured_probe_wall_seconds": wall, "variants_per_second": 8 / wall},
    unit="variants/second", reason="Heterogeneous sequential parser probes, not production load capacity.",
    sample_count=8, method="Total completed variants divided by retained probe wall time", aggregation="pooled")
report = (DIRECTORY / "README.md").read_text()
links = re.findall(r"\]\(([^)]+)\)", report)
missing = [link for link in links if DIRECTORY / link != target and not (DIRECTORY / link).exists()]
if missing:
    raise RuntimeError(f"Missing local report links: {missing}")
measurement = {
    "scope": "Eight local native extraction variants across five frozen PDF pages; a subsequent deterministic gold comparison.",
    "baseline_code_version": initial["code_commit"], "measurement_policy": "../../../measurement-policy.md",
    "resolved_parser_versions": summaries[0]["versions"], "provider_calls": 0,
    "metric_inventory": metrics,
    "additional_parser_quality_metrics": {"status": "measured", "value": review["comparison"],
        "sample_count": 3, "population": "Three previously observed development rows, 75 explicitly annotated cells",
        "method": review["method"], "aggregation": "Separate counts for numeric values, blanks, labels, header paths, merged groups and exact rows",
        "artifact": "review-1-result.json", "gold_sha256": review["gold_sha256"]},
    "canonical_span_integration": {"status": "unavailable", "value": None,
        "reason": "Probe outputs native geometry and text only. Production PdfExtraction offsets and downstream indexing are not implemented here."},
    "failed_verification_attempts": [{"artifact": "report-review-1.json",
        "reason": "The report link checker incorrectly required its own not-yet-written measurement.json target. Retained failure; checker now treats that output as the current creation target."}],
    "report_review": {"reviewer": "Codex model reviewer", "method": "Original-page visual inspection plus raw candidate/gold comparison; local link and formatting inspection",
        "links_checked": len(links), "missing_links": missing, "english_only_project_text": True,
        "readme_sha256": sha256(report.encode()).hexdigest(), "result": "pass"},
}
target.write_text(json.dumps(measurement, indent=2) + "\n")
print(json.dumps({"metric_count": len(metrics), "links_checked": len(links),
                  "candidate_quality": review["comparison"]["candidate"]}, indent=2))
