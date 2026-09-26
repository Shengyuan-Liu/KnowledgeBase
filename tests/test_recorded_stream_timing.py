"""The observed host-sleep gap must remain distinguishable from active time."""
from types import SimpleNamespace

import pytest
from evals import automatic


@pytest.mark.anyio
@pytest.mark.parametrize('fail', [False, True])
async def test_records_wall_clock_gap_and_retains_partial_failed_stream(monkeypatch, fail):
    clock = {'active': 10.0, 'wall': 100.0}
    monkeypatch.setattr(automatic, 'perf_counter', lambda: clock['active'])
    monkeypatch.setattr(automatic, 'time', lambda: clock['wall'])

    class Stream:
        closed = False
        count = 0

        async def __anext__(self):
            self.count += 1
            if self.count == 1:
                clock.update(active=12.0, wall=222.0)
                return SimpleNamespace(type='response.output_text.delta', delta='Partial')
            if fail:
                try:
                    raise TimeoutError('private diagnostic')
                except TimeoutError as cause:
                    raise RuntimeError('private provider diagnostic') from cause
            return SimpleNamespace(type='response.completed', response=SimpleNamespace(model='resolved', usage=None))

        async def close(self):
            self.closed = True

    stream = Stream()
    class Responses:
        async def create(self, **kwargs):
            clock.update(active=11.0, wall=101.0)
            return stream

    calls = []
    recorder = automatic.RecordedResponses(SimpleNamespace(responses=Responses()), calls)
    wrapped = await recorder.create(model='test', input=[], stream=True)
    assert (await anext(wrapped)).delta == 'Partial'
    if fail:
        with pytest.raises(RuntimeError):
            await anext(wrapped)
    else:
        await anext(wrapped)
    await wrapped.close()
    row, = calls
    assert row['stream_open_seconds'] == row['stream_open_wall_seconds'] == 1
    assert row['deltas'] == [{'seconds': 2, 'wall_seconds': 122, 'delta': 'Partial'}]
    assert row['seconds'] == 2 and row['wall_seconds'] == 122
    assert row['status'] == ('error' if fail else 'ok')
    assert row['started_at'] and row['finished_at'] and stream.closed
    if fail:
        assert row['error_cause_type'] == 'TimeoutError'
        assert 'private' not in str(row)


@pytest.mark.anyio
async def test_stream_open_failure_records_both_clocks_without_secret_message(monkeypatch):
    class Responses:
        async def create(self, **kwargs):
            raise TimeoutError('private')
    calls = []
    recorder = automatic.RecordedResponses(SimpleNamespace(responses=Responses()), calls)
    with pytest.raises(TimeoutError):
        await recorder.create(model='test', input=[], stream=True)
    row, = calls
    assert row['status'] == 'error' and row['error_type'] == 'TimeoutError'
    assert row['seconds'] >= 0 and row['wall_seconds'] >= 0
    assert row['finished_at']
    assert 'private' not in str(row)
