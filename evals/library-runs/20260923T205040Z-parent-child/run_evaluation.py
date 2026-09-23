"""One-run library evaluation; credentials stay in Settings, results are append-only."""
import json, sys, time, statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from knowledgebase.config import Settings
from knowledgebase.storage.runtime import open_storage
from knowledgebase.storage.operations import get_files, get_chunks, get_parents, get_document_source
from knowledgebase.services.chat import answer_question
from knowledgebase.providers.embeddings import EmbeddingClient
from knowledgebase.providers.llm import LLMClient
from evals.evaluate import retrieval_metrics

import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("report",type=Path,help="Directory containing frozen cases.json")
parser.add_argument("stage",help="New artifact prefix; existing outputs are not overwritten")
parser.add_argument("--data-dir",type=Path,required=True)
args=parser.parse_args()
report=args.report;stage=args.stage;settings=Settings(data_dir=args.data_dir);rows=[]
cases_path=report/"cases.json"
cases=json.loads(cases_path.read_text()); out=report/f'{stage}-answers.jsonl'
assert not out.exists()
with open_storage(settings.data_dir) as (sessions,store):
 with sessions() as s:
  snapshots=[]
  for file in get_files(s):
   chunks=get_chunks(s,file.file_id); parents=get_parents(s,file.file_id)
   snapshots.append({'file':file.model_dump(mode='json'),'chunks':[c.model_dump() for c in chunks],'parents':[p.model_dump() for p in parents]})
  (report/f'{stage}-chunks.json').write_text(json.dumps(snapshots,indent=2)+'\n')
 with OpenAI(api_key=settings.openai_api_key,base_url=settings.openai_base_url,timeout=90,max_retries=1) as sdk:
  embeddings=EmbeddingClient(sdk,model=settings.embedding_model); llm=LLMClient(sdk,model=settings.answer_model)
  def run(case):
   started=time.perf_counter()
   result=answer_question(case['question'],sessions,embeddings,store,llm,top_k=settings.retrieval_top_k,evidence_max_tokens=settings.evidence_max_tokens,encoding_name=settings.chunk_tokenizer)
   answer=result.model_dump()
   normalized=json.loads(json.dumps(case))
   for span in normalized['evidence']:span['file']=Path(span['file']).name
   return {'case_id':case['id'],'question':case['question'],'seconds':time.perf_counter()-started,'answer':answer,'coverage':retrieval_metrics(normalized,answer['sources'])}
  with ThreadPoolExecutor(max_workers=3) as pool:
   jobs={pool.submit(run,c):c for c in cases}
   with out.open('x') as f:
    for job in as_completed(jobs):
     row=job.result(); rows.append(row); f.write(json.dumps(row)+'\n'); f.flush()
     print(stage,row['case_id'],round(row['seconds'],2),len(row['answer']['sources']),flush=True)
 metrics={key:statistics.mean(r['coverage'][key] for r in rows if r['coverage'][key] is not None) for key in ('annotated_char_recall','full_evidence_recall')}
 metadata={'stage':stage,'cases':len(rows),'answer_model':settings.answer_model,'embedding_model':settings.embedding_model,'top_k':settings.retrieval_top_k,'child_limit':settings.chunk_max_tokens,'parent_limit':settings.parent_max_tokens,'evidence_limit':settings.evidence_max_tokens,'tokenizer':settings.chunk_tokenizer,'coverage':metrics,'mean_seconds':statistics.mean(r['seconds'] for r in rows),'note':'Three concurrent independent questions. Corpus-grounded review is separate from automatic span coverage.'}
 (report/f'{stage}-summary.json').write_text(json.dumps(metadata,indent=2)+'\n'); print(json.dumps(metadata),flush=True)
