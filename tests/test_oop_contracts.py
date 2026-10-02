"""Frozen HTTP, prompt and storage observations across the OOP migration."""

import json
import os
import re
from pathlib import Path

from test_automatic_planning import planned_api as planned_api
from test_chat_streaming import frames

from knowledgebase import schemas
from knowledgebase.storage.operations import get_chunks, get_document_source

DIRECTORY = Path(__file__).resolve().parents[1] / "evals/check-runs/20261001-oop-refactoring"


def normalize(value):
    """Ignore wall-clock fields and consistently rename generated file/query IDs."""
    identities = {}

    def visit(item):
        if isinstance(item, dict):
            return {
                key: visit(child)
                for key, child in item.items()
                if not key.endswith("_seconds")
                and key not in {"seconds", "created_at", "updated_at"}
            }
        if isinstance(item, list):
            return [visit(child) for child in item]
        if isinstance(item, str):
            return re.sub(
                r"(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])",
                lambda match: identities.setdefault(match[0], f"identity-{len(identities) + 1}"),
                item,
            )
        return item

    return visit(value)


def test_frozen_http_prompts_evidence_and_history(planned_api):
    client, resources, sdk, _, file_id = planned_api
    observed = {}
    with resources.sessions() as session:
        observed["source"] = get_document_source(session, file_id).model_dump(mode="json")
        observed["chunks"] = [
            chunk.model_dump(mode="json") for chunk in get_chunks(session, file_id)
        ]
    for mode in ("single", "planned"):
        response = client.post(
            "/api/chat",
            json={
                "question": "Explain the training method and evaluation result.",
                "retrieval_mode": mode,
            },
        )
        assert response.status_code == 200
        observed[mode] = response.json()
    response = client.post(
        "/api/chat/stream",
        json={
            "question": "Explain the training method and evaluation result.",
            "retrieval_mode": "planned",
            "request_id": "frozen-stream",
        },
    )
    assert response.status_code == 200
    observed["stream"] = frames(response.text)
    complete = observed["stream"][-1][1]
    response = client.post(
        "/api/chat",
        json={
            "question": "What about its result?",
            "conversation_id": complete["conversation_id"],
            "retrieval_mode": "planned",
        },
    )
    assert response.status_code == 200
    observed["followup"] = response.json()
    response = client.post(
        "/api/chat", json={"question": "What is known?", "file_ids": ["missing"]}
    )
    assert response.status_code == 200
    observed["missing_scope"] = response.json()
    assert client.delete(f"/api/files/{file_id}").status_code == 204
    observed["history_after_delete"] = client.get(
        f"/api/conversations/{complete['conversation_id']}"
    ).json()
    observed["empty"] = client.post("/api/chat", json={"question": "What remains?"}).json()
    observed["model_requests"] = [call.kwargs for call in sdk.responses.create.call_args_list]
    observed["schemas"] = {
        name: getattr(schemas, name).model_json_schema()
        for name in (
            "File",
            "Chunk",
            "ChatRequest",
            "ConversationAnswer",
            "ChatStreamEvent",
            "PlannedEvidence",
            "PlanDecision",
            "TargetDecisions",
            "SufficiencyAssessment",
        )
    }
    observed = normalize(json.loads(json.dumps(observed)))
    baseline = DIRECTORY / "behavior-before-v2.json"
    if os.environ.get("OOP_FREEZE") == "1":
        with baseline.open("x") as output:
            json.dump(observed, output, indent=2)
            output.write("\n")
    else:
        assert observed == json.loads(baseline.read_text())
    if os.environ.get("OOP_SNAPSHOT"):
        with Path(os.environ["OOP_SNAPSHOT"]).open("x") as output:
            json.dump(observed, output, indent=2)
            output.write("\n")
