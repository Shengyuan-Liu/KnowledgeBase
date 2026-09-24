"""Verify the running app without uploading or deleting any library content."""

import json
import sqlite3
from pathlib import Path

import httpx


def run():
    report = Path(__file__).parent
    cases = json.loads((report / "cases.json").read_text())
    question = next(c["question"] for c in cases if c["id"] == "msds-admissions-prerequisites")
    with sqlite3.connect("file:data/knowledgebase.db?mode=ro", uri=True) as db:
        previous_ids = [row[0] for row in db.execute("select conversation_id from conversations")]
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=120) as client:
        before = client.get("/api/files")
        before.raise_for_status()
        history_checks = []
        for conversation_id in previous_ids:
            response = client.get(f"/api/conversations/{conversation_id}")
            response.raise_for_status()
            history_checks.append({"conversation_id": conversation_id, "messages": len(response.json()["messages"])})
        response = client.post("/api/chat/stream", json={
            "question": question, "request_id": "bge-live-acceptance",
        })
        response.raise_for_status()
        events = [{"event": frame.split("\n")[0].removeprefix("event: "),
                   "data": json.loads(frame.split("\ndata: ")[1])}
                  for frame in response.text.strip().split("\n\n")]
        assert events[-1]["event"] == "complete"
        complete = events[-1]["data"]
        assert complete["retrieval"]["options"]["rerank_enabled"]
        assert complete["sources"][0]["file_name"] == "admissions-requirements.txt"
        assert complete["sources"][0]["rerank"]["rerank_rank"] == 1
        conversation_id = complete["conversation_id"]
        response = client.post("/api/chat", json={
            "question": "Does that mean a specific programming language is mandatory?",
            "conversation_id": conversation_id,
        })
        response.raise_for_status()
        followup = response.json()
        assert followup["retrieval"]["rerank"]["question"] == followup["retrieval_question"]
        history = client.get(f"/api/conversations/{conversation_id}").json()
        assert len(history["messages"]) == 4
        for answer, saved in zip([complete, followup], history["messages"][1::2]):
            assert saved["retrieval"] == answer["retrieval"]
            assert saved["sources"] == [{**s, "file_deleted": False} for s in answer["sources"]]
        assert client.get("/api/files").json() == before.json()
        assert client.get("/").status_code == 200
    with (report / "app-smoke.json").open("x") as output:
        json.dump({"file_count": len(before.json()), "previous_history_checks": history_checks,
                   "events": events, "followup": followup, "saved_history_matches": True,
                   "library_unchanged": True, "frontend_served": True}, output, indent=2)
    print({"file_count": len(before.json()), "old_conversations_readable": len(history_checks),
           "new_conversation": conversation_id, "source": complete["sources"][0]["file_name"],
           "resolved_followup": followup["retrieval_question"], "history_matches": True})


if __name__ == "__main__":
    run()
