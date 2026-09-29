"""Evaluation-only SDK observers. Forward original inputs/results without repair."""
from contextvars import ContextVar
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Lock
from time import perf_counter
from types import SimpleNamespace
from uuid import uuid4

REQUEST = ContextVar('evaluation_request', default='startup')
LOCK = Lock()
ROOT = Path(__file__).parent


def log(kind, **data):
    record = dict(kind=kind, request=REQUEST.get(), at=datetime.now(timezone.utc).isoformat(), **data)
    with LOCK, (ROOT / 'server-observations.jsonl').open('a') as file:
        file.write(json.dumps(record, ensure_ascii=False) + '\n')


def result_record(result, kind):
    if kind == 'embeddings':
        return dict(model=result.model, usage=result.usage.model_dump(mode='json'),
                    vector_count=len(result.data), dimensions=len(result.data[0].embedding) if result.data else None)
    return result.model_dump(mode='json')


class SyncObserver:
    def __init__(self, sdk):
        self.sdk = sdk
        self.responses = SimpleNamespace(create=lambda **kwargs: self.call('responses', kwargs))
        self.embeddings = SimpleNamespace(create=lambda **kwargs: self.call('embeddings', kwargs))

    def __enter__(self):
        self.sdk.__enter__()
        return self

    def __exit__(self, *args):
        return self.sdk.__exit__(*args)

    def with_options(self, **kwargs):
        return SyncObserver(self.sdk.with_options(**kwargs))

    def call(self, kind, kwargs):
        call_id, started = uuid4().hex, perf_counter()
        log('sdk_start', call_id=call_id, api=kind, input=kwargs)
        try:
            result = getattr(self.sdk, kind).create(**kwargs)
            log('sdk_complete', call_id=call_id, seconds=perf_counter()-started, result=result_record(result, kind))
            return result
        except Exception as error:
            log('sdk_error', call_id=call_id, seconds=perf_counter()-started,
                error_type=type(error).__name__, status_code=getattr(error, 'status_code', None))
            raise


class ObservedStream:
    def __init__(self, stream, call_id, started):
        self.stream, self.call_id, self.started = stream, call_id, started
        self.iterator = stream.__aiter__()
        self.first = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        event = await anext(self.iterator)
        if event.type == 'response.output_text.delta' and event.delta and self.first:
            self.first = False
            log('sdk_first_delta', call_id=self.call_id, seconds=perf_counter()-self.started)
        if event.type in {'response.completed', 'response.failed', 'response.incomplete', 'error'}:
            log('sdk_stream_terminal', call_id=self.call_id, seconds=perf_counter()-self.started, event=event.model_dump(mode='json'))
        return event

    async def close(self):
        await self.stream.close()
        log('sdk_stream_closed', call_id=self.call_id, seconds=perf_counter()-self.started)


class AsyncObserver:
    def __init__(self, sdk):
        self.sdk = sdk
        self.responses = SimpleNamespace(create=self.call)

    async def __aenter__(self):
        await self.sdk.__aenter__()
        return self

    async def __aexit__(self, *args):
        return await self.sdk.__aexit__(*args)

    def with_options(self, **kwargs):
        return AsyncObserver(self.sdk.with_options(**kwargs))

    async def call(self, **kwargs):
        call_id, started = uuid4().hex, perf_counter()
        log('sdk_start', call_id=call_id, api='responses', input=kwargs)
        try:
            result = await self.sdk.responses.create(**kwargs)
            if kwargs.get('stream'):
                return ObservedStream(result, call_id, started)
            log('sdk_complete', call_id=call_id, seconds=perf_counter()-started, result=result.model_dump(mode='json'))
            return result
        except Exception as error:
            log('sdk_error', call_id=call_id, seconds=perf_counter()-started,
                error_type=type(error).__name__, status_code=getattr(error, 'status_code', None))
            raise
