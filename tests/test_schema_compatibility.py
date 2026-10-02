"""Read earlier query traces after consolidating the retrieval result models."""

from knowledgebase.schemas import QueryRun, RetrievedEvidence


def test_saved_candidate_hits_load_and_serialize_with_the_shared_result_contract():
    saved = {
        "query_ids": ["q1"], "requirement_ids": ["r1"], "text": "calibration",
        "requested_file_ids": ["manual"], "seconds": 0.1,
        "result": {
            "hits": [{
                "chunk": {"chunk_id": "c1", "file_id": "manual", "text": "17 days",
                          "index": 0, "start_offset": 10, "end_offset": 17},
                "file_name": "manual.pdf", "distance": 0.2,
                "parent_id": "p1", "matched_child_ids": ["c1"],
            }],
            "diagnostics": {"max_tokens": 4096, "tokenizer": "cl100k_base"},
        },
    }
    run = QueryRun.model_validate(saved)
    assert isinstance(run.result, RetrievedEvidence)
    hit = run.result.chunks[0]
    assert (hit.chunk.text, hit.chunk.start_offset, hit.chunk.end_offset) == ("17 days", 10, 17)
    assert (hit.parent_id, hit.matched_child_ids, hit.distance) == ("p1", ["c1"], 0.2)
    serialized = run.model_dump(mode="json")
    assert "hits" not in serialized["result"]
    assert serialized["result"]["chunks"][0]["chunk"]["chunk_id"] == "c1"
    assert QueryRun.model_validate(serialized) == run
    assert "hits" in saved["result"]
