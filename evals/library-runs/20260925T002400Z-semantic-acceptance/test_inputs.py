"""Offline validation of frozen comparison inputs and source annotations."""
import json
from pathlib import Path
import runpy

from evals.automatic import load_benchmark
from knowledgebase.config import Settings

DIRECTORY = Path(__file__).parent


def test_frozen_inputs_match_corpus_and_protocol():
    module = runpy.run_path(str(DIRECTORY / "run_pair.py"))
    plan, cases, manifest, documents = module["load_inputs"]()
    assert len(cases) == 24 and len(manifest) == 17
    assert len({c["id"] for c in cases}) == len(cases)
    for case in cases:
        assert case["expected_answer_points"]
        assert bool(case["evidence"]) == case["answerable"]
        for span in case["evidence"] + case.get("context_evidence", []):
            text = documents[span["file"]][span["start_offset"]:span["end_offset"]]
            assert text and ("quote" not in span or text == span["quote"])


def test_only_chunking_strategy_changes_and_library_is_isolated():
    plan = json.loads((DIRECTORY / "plan.json").read_text())
    configurations = [Settings(**{**plan["base_config"], "chunking_strategy": strategy}).model_dump(
        exclude={"openai_api_key", "openai_base_url"}) for strategy in plan["order"]]
    assert {key for key in configurations[0] if configurations[0][key] != configurations[1][key]} == {"chunking_strategy"}
    assert configurations[0]["data_dir"] == Path("data/evals/20260925T002400Z-semantic-acceptance")


def test_stable_blocks_are_identical_source_slices():
    _, _, documents = load_benchmark()
    blocks = json.loads((DIRECTORY / "blocks.json").read_text())
    assert len({b["unit_id"] for b in blocks}) == len(blocks)
    for block in blocks:
        assert block["text"] == documents[block["file_name"]][block["start_offset"]:block["end_offset"]]


def test_block_metrics_deduplicate_children_and_score_misses():
    score = runpy.run_path(str(DIRECTORY / "analyze.py"))["fixed_block_ranking"]
    blocks = [{"unit_id": "a", "file_name": "x", "start_offset": 0, "end_offset": 10},
              {"unit_id": "b", "file_name": "x", "start_offset": 10, "end_offset": 20}]
    case = {"answerable": True, "evidence": [{"file": "x", "start_offset": 12, "end_offset": 18}]}
    hits = [{"file_name": "x", "start_offset": 0, "end_offset": 4},
            {"file_name": "x", "start_offset": 4, "end_offset": 8},
            {"file_name": "x", "start_offset": 12, "end_offset": 18}]
    result = score(case, hits, blocks, k=5)
    assert result["ranked_units"] == ["a", "b"]
    assert result["recall_at_k"] == result["hit_rate_at_k"] == 1
    assert result["precision_at_k"] == .2 and result["mrr_at_k"] == .5
    assert score(case, [], blocks)["ndcg_at_k"] == 0
    assert score({"answerable": False}, hits, blocks) is None
