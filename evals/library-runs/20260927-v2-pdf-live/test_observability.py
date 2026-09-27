"""Offline checks for transparent evaluation observers, no provider calls."""
import json
from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock

import pytest
import observability as obs


def test_sync_preserves_response_options_and_does_not_record_key(tmp_path, monkeypatch):
    monkeypatch.setattr(obs, 'ROOT', tmp_path)
    result=SimpleNamespace(model_dump=lambda **_: {'id':'response', 'usage':{'input_tokens':3}})
    sdk=Mock()
    sdk.with_options.return_value=sdk
    sdk.responses.create.return_value=result
    observer=obs.SyncObserver(sdk).with_options(timeout=4, max_retries=0)
    assert observer.responses.create(model='offline', input=[]) is result
    sdk.responses.create.assert_called_once_with(model='offline', input=[])
    records=[json.loads(line) for line in (tmp_path/'server-observations.jsonl').read_text().splitlines()]
    assert records[-1]['result']['usage']['input_tokens']==3
    assert 'api_key' not in json.dumps(records)


@pytest.mark.anyio
async def test_stream_passes_deltas_usage_and_close(tmp_path, monkeypatch):
    monkeypatch.setattr(obs, 'ROOT', tmp_path)
    terminal=SimpleNamespace(type='response.completed', model_dump=lambda **_: {'type':'response.completed','response':{'usage':{'output_tokens':7}}})
    events=[SimpleNamespace(type='response.output_text.delta',delta='Hello'),terminal]
    async def iterator():
        for event in events:
            yield event
    raw=Mock()
    raw.__aiter__=lambda _:iterator()
    raw.close=AsyncMock()
    sdk=Mock()
    sdk.responses.create=AsyncMock(return_value=raw)
    wrapped=await obs.AsyncObserver(sdk).responses.create(model='offline',input=[],stream=True)
    assert [event async for event in wrapped]==events
    await wrapped.close()
    raw.close.assert_awaited_once()
    records=[json.loads(line) for line in (tmp_path/'server-observations.jsonl').read_text().splitlines()]
    assert records[-2]['event']['response']['usage']['output_tokens']==7
    assert sum(r['kind']=='sdk_first_delta' for r in records)==1


@pytest.fixture
def anyio_backend():
    return 'asyncio'
