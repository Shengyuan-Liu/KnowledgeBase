"""Run a frozen question batch with the existing append-only SSE recorder."""
import json,shutil,sys
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parent
BASE='http://127.0.0.1:8787'

def execute(directory,cases,arms,index):
    directory.mkdir()
    (directory/'index-snapshot.json').write_text(json.dumps(index)+'\n')
    (directory/'frozen-labels.json').write_text(json.dumps({'note':'References frozen in material protocols before calls; source mapping retained separately.'})+'\n')
    source=(ROOT/'run.py').read_text().replace("assert len(FROZEN['cases']) == 6", "assert len(FROZEN['cases']) > 0")
    source=source.replace("for arm in ['planned']:","for arm in ARMS:").replace("case['id']+'-'+arm","case['id']+'--'+arm")
    source=source.replace('retrieval_mode=arm','retrieval_mode=("single" if arm == "A" else "planned")')
    scope={'__name__':'batch_recorder','__file__':str(directory/'run.py'),'ARMS':arms}
    exec(compile(source,str(directory/'run.py'),'exec'),scope)
    scope['FROZEN']={'cases':[{**c,'followup_of':None} for c in cases]}
    with httpx.Client(timeout=240,trust_env=False) as client:scope['answers'](client)

if __name__=='__main__':
    mode=sys.argv[1]
    with httpx.Client(timeout=240,trust_env=False) as c:index=c.get(BASE+'/__eval__/snapshot').json()
    if mode=='dependency':
        cases=json.loads(Path('evals/materials/pdf-v2-closeout-dependency/protocol.json').read_text())['questions']
        execute(ROOT/'dependency',cases,['D'],index)
    elif mode=='ablation':
        protocol=json.loads((ROOT/'ablation-protocol.json').read_text())
        execute(ROOT/'ablation',protocol['questions'],['A','B','C'],index)
        for case in protocol['questions']:
            source=(ROOT/'dependency'/f"{case['id']}--D.json") if case['id']=='unknown-laboratory' else ROOT/f"{case['id']}-planned.json"
            shutil.copy2(source,ROOT/'ablation'/f"{case['id']}--D.json")
        with httpx.Client(timeout=240,trust_env=False) as c:
            for case in protocol['questions']:
                identity=case['id']+'--C'
                r=c.post(BASE+'/__eval__/shadow/'+identity,headers={'x-eval-id':identity+'--shadow'})
                with (ROOT/'ablation'/f'{identity}--shadow.json').open('x') as out:json.dump({'http_status':r.status_code,'result':r.json()},out,indent=2)
                print(identity,'shadow',r.status_code,flush=True)
    elif mode=='heldout':
        cases=json.loads(Path('evals/materials/pdf-v2-closeout-heldout/protocol.json').read_text())['questions']
        execute(ROOT/'heldout',cases,['D'],index)
