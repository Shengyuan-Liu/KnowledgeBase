"""Check the restored app, exact retained child evidence, and saved history."""

import json
from pathlib import Path
import sqlite3
from time import perf_counter

import httpx


def run():
    root = Path(__file__).parent
    case = next(c for c in json.loads((root / 'cases.json').read_text())
                if c['id'] == 'msds-cpt-source-context')
    with sqlite3.connect('file:data/knowledgebase.db?mode=ro', uri=True) as db:
        previous = [row[0] for row in db.execute('select conversation_id from conversations')]
    with httpx.Client(base_url='http://127.0.0.1:8000', timeout=120) as client:
        before = client.get('/api/files').json()
        for identity in previous:
            client.get(f'/api/conversations/{identity}').raise_for_status()
        events, first_delta = [], None
        started = perf_counter()
        with client.stream('POST', '/api/chat/stream', json={
            'question': case['question'], 'request_id': 'source-metadata-live-smoke',
        }) as response:
            response.raise_for_status()
            event = None
            for line in response.iter_lines():
                if line.startswith('event: '):
                    event = line[7:]
                elif line.startswith('data: '):
                    data = json.loads(line[6:])
                    elapsed = perf_counter() - started
                    events.append({'event': event, 'seconds': elapsed, 'data': data})
                    if event == 'answer_delta' and data['delta'] and first_delta is None:
                        first_delta = elapsed
        total = perf_counter() - started
        assert events[-1]['event'] == 'complete'
        answer = events[-1]['data']
        assert answer['retrieval']['options']['packing_strategy'] == 'parent_then_child'
        assert answer['retrieval']['context_format'] == 'source-metadata-v1'
        from knowledgebase.rag.context import build_context
        from knowledgebase.schemas import StructuredChunk, RetrievedChunk
        import tiktoken
        evidence = [RetrievedChunk(chunk=StructuredChunk.model_validate({**s, 'index': 0}),
                                   file_name=s['file_name'], distance=s['distance']) for s in answer['sources']]
        actual_tokens = len(tiktoken.get_encoding('cl100k_base').encode_ordinary(build_context(evidence)))
        assert actual_tokens == answer['retrieval']['evidence_tokens'] <= 4096
        assert any(s['chunk_id'] != s['parent_id'] and 'after the first year' in s['text']
                   for s in answer['sources'])
        history = client.get(f"/api/conversations/{answer['conversation_id']}").json()
        saved = history['messages'][-1]
        assert saved['retrieval'] == answer['retrieval']
        assert saved['sources'] == [{**s, 'file_deleted': False} for s in answer['sources']]
        assert client.get('/api/files').json() == before
        assert client.get('/').status_code == 200
    with (root / 'app-smoke.json').open('x') as output:
        json.dump({'file_count': len(before), 'previous_readable_conversations': previous,
                   'events': events, 'first_delta_seconds': first_delta, 'total_seconds': total,
                   'saved_history_matches': True, 'library_unchanged': True,
                   'frontend_served': True}, output, indent=2)
    print({'files': len(before), 'old_conversations_readable': len(previous),
           'first_delta_seconds': first_delta, 'total_seconds': total,
           'conversation_id': answer['conversation_id']})


if __name__ == '__main__':
    run()
