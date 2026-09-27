"""Drive the production HTTP routes against an isolated five-PDF index."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter

import httpx

ROOT=Path(__file__).parent
BASE='http://127.0.0.1:8785'
FROZEN=json.loads((ROOT/'frozen-cases.json').read_text())


def write(name, value):
    target=ROOT/name
    assert not target.exists(), f'Append-only: {name} exists.'
    target.write_text(json.dumps(value,indent=2)+'\n')


def answers(client):
    snapshot=json.loads((ROOT.parent/'20260927-v2-pdf-live/index-snapshot.json').read_text())
    identities={d['file']['file_name']:d['file']['file_id'] for d in snapshot['files']}
    conversations={}
    for i,case in enumerate(FROZEN['cases']):
        for arm in (['single','planned'] if i%2==0 else ['planned','single']):
            identity=case['id']+'-'+arm
            target=ROOT/(identity+'.json')
            assert not target.exists(), 'Do not overwrite an earlier request.'
            request=dict(question=case['question'],file_ids=[identities[f] for f in case['files']],request_id=identity,retrieval_mode=arm)
            if case['followup_of']:
                parent=conversations.get((case['followup_of'],arm))
                if parent is None:
                    write(identity+'.json',dict(case_id=case['id'],arm=arm,request=request,status='blocked',reason='Preceding conversation failed.'))
                    continue
                request['conversation_id']=parent
            started=perf_counter()
            events=[]
            row=dict(case_id=case['id'],arm=arm,request=request,at=datetime.now(timezone.utc).isoformat(),
                     first_answer_delta_seconds=None,complete_response_seconds=None,status='running')
            try:
                with client.stream('POST',BASE+'/api/chat/stream',json=request,headers={'x-eval-id':identity}) as response:
                    row['http_status']=response.status_code
                    kind=None
                    for line in response.iter_lines():
                        if line.startswith('event: '): kind=line[7:]
                        if not line.startswith('data: '): continue
                        payload=json.loads(line[6:]); payload['event']=kind or payload.get('event')
                        elapsed=perf_counter()-started
                        events.append(dict(seconds=elapsed,data=payload))
                        if payload['event']=='answer_delta' and payload.get('delta') and row['first_answer_delta_seconds'] is None:
                            row['first_answer_delta_seconds']=elapsed
                        if payload['event']=='complete':
                            row['answer']=payload
                            row['status']='completed'
                            conversations[(case['id'],arm)]=payload['conversation_id']
                        if payload['event']=='error':
                            row['status']='error'; row['error']=payload
                row['complete_response_seconds']=perf_counter()-started
                if row['status']=='running': row['status']='incomplete'
            except Exception as error:
                row.update(status='error',error_type=type(error).__name__,complete_response_seconds=perf_counter()-started)
            row['events']=events
            if 'answer' in row:
                history=client.get(BASE+'/api/conversations/'+row['answer']['conversation_id']).json()
                latest=history['messages'][-1]
                row['history_matches']=latest['answer'] == row['answer']['answer'] if 'answer' in latest else latest.get('content') == row['answer']['answer']
                row['history_retrieval_matches']=latest['retrieval']==row['answer']['retrieval']
                row['saved_message']=latest
            write(identity+'.json',row)
            print(identity,row['status'],round(row.get('complete_response_seconds') or 0,2),flush=True)


if __name__=='__main__':
    with httpx.Client(timeout=240,trust_env=False) as client:
        answers(client)
