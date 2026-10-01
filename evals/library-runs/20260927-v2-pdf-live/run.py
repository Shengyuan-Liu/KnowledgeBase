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
FROZEN=json.loads((ROOT/'effective-cases.json').read_text())


def write(name, value):
    target=ROOT/name
    assert not target.exists(), f'Append-only: {name} exists.'
    target.write_text(json.dumps(value,indent=2)+'\n')


def ingest(client):
    results=[]
    for document in FROZEN['corpus']:
        name=document['file']
        data=(Path('evals/materials/pdf-v2')/name).read_bytes()
        started=perf_counter()
        try:
            response=client.post(BASE+'/api/files', files={'file':(name,data,'application/pdf')}, headers={'x-eval-id':'ingest-'+name})
            row=dict(file=name,http_status=response.status_code,seconds=perf_counter()-started,result=response.json())
            if response.status_code==201:
                original=client.get(BASE+f"/api/files/{row['result']['file_id']}/original")
                row['original_sha256']=sha256(original.content).hexdigest()
                row['original_matches']=row['original_sha256']==document['sha256']
                partial=client.get(BASE+f"/api/files/{row['result']['file_id']}/original",headers={'Range':'bytes=0-31'})
                row['range_matches']=partial.status_code==206 and partial.content==data[:32]
        except Exception as error:
            row=dict(file=name,seconds=perf_counter()-started,error_type=type(error).__name__)
        write('ingest-'+name+'.json',row)
        results.append(row)
        print(name, row.get('http_status'), round(row['seconds'],2),flush=True)
    snapshot=client.get(BASE+'/__eval__/snapshot').json()
    write('index-snapshot.json',snapshot)
    write('ingestion-summary.json',dict(results=results,index_bytes=snapshot.get('index_bytes')))
    assert all(r.get('http_status')==201 and r.get('original_matches') and r.get('range_matches') for r in results)


def answers(client):
    snapshot=json.loads((ROOT/'index-snapshot.json').read_text())
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


def lifecycle(client):
    snapshot=json.loads((ROOT/'index-snapshot.json').read_text())
    file=next(d['file'] for d in snapshot['files'] if d['file']['file_name']=='apple-fy24.pdf')
    answer=json.loads((ROOT/'apple-sales-planned.json').read_text())
    started=perf_counter()
    result=client.delete(BASE+'/api/files/'+file['file_id'],headers={'x-eval-id':'delete-apple'})
    history=client.get(BASE+'/api/conversations/'+answer['answer']['conversation_id']).json()
    sources=history['messages'][-1]['sources']
    original=client.get(BASE+'/api/files/'+file['file_id']+'/original')
    after=client.get(BASE+'/__eval__/snapshot').json()
    row=dict(delete_status=result.status_code,seconds=perf_counter()-started,original_status=original.status_code,
             historical_sources=sources,history_retrieval=history['messages'][-1]['retrieval'],
             history_retrieval_matches=history['messages'][-1]['retrieval']==answer['answer']['retrieval'],
             remaining_files=[d['file']['file_name'] for d in after['files']],index_bytes_after=after['index_bytes'],
             update_behavior={'status':'not_applicable','reason':'No in-place file update endpoint; this run exercises upload and deletion.'})
    write('lifecycle.json',row)
    assert result.status_code==204 and original.status_code==404
    assert row['history_retrieval_matches'] and all(s['file_deleted'] for s in sources if s['file_id']==file['file_id'])
    assert 'apple-fy24.pdf' not in row['remaining_files']
    print('Original byte ranges, historical evidence, deletion and original unavailability verified.')


if __name__=='__main__':
    with httpx.Client(timeout=240,trust_env=False) as client:
        {'ingest':ingest,'answers':answers,'lifecycle':lifecycle}[sys.argv[1]](client)
