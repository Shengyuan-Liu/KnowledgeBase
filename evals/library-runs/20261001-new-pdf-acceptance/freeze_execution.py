"""Seal canonical labels and execution code after ingestion, before answer calls."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from prepare import ROOT, MATERIAL, write
runtime=json.loads((ROOT/'resolved-runtime-2.json').read_text())
assert runtime['settings']['answer_model']=='gpt-4.1'
assert runtime['settings']['embedding_model']=='text-embedding-3-small'
assert runtime['settings']['evidence_max_tokens']==4096
assert runtime['settings']['planning']['max_input_tokens']==8192
assert runtime['settings']['planning']['answer_max_input_tokens']==16384
assert runtime['reranker']['revision']=='953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e'
assert runtime['reranker']['device']=='mps'
observations=[json.loads(line) for line in (ROOT/'server-observations.jsonl').read_text().splitlines()]
starts=[o for o in observations if o['kind']=='sdk_start']
assert all(o['request'].startswith('ingest-') and o['api']=='embeddings' for o in starts)
paths=[ROOT/n for n in ['index-snapshot.json','frozen-labels.json','frozen-cases.json','mapping-freeze.json','resolved-runtime-2.json']]+list(ROOT.glob('*.py'))+[MATERIAL/'questions.json',MATERIAL/'references.json']
write('execution-freeze.json',dict(at=datetime.now(timezone.utc).isoformat(),hashes={str(p):sha256(p.read_bytes()).hexdigest() for p in paths},answer_calls=0,ingestion_sdk_calls=len(starts),configuration_matches_protocol=True,failed_infrastructure_attempts=['server-start-check.json','reference-mapping-check.json','reference-mapping-check-2.json'],mapping_review='Twelve original-page facts matched by whitespace-only normalization before answers; exact original source refs and offsets retained. Repeated same-page unit notes are equivalent.'))
print('1 passed: runtime matches protocol; all prior provider calls are ingestion embeddings; labels sealed.')
