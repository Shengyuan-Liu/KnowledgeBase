"""Preserve the second reviewer's independent first pass before reconciliation."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
assert not (ROOT/'root-review.json').exists()
cases=json.loads((ROOT/'frozen-cases.json').read_text())
rows=[]
for case in cases['cases']:
    for arm in ['single','planned']:
        path=ROOT/(case['id']+'-'+arm+'.json')
        raw=json.loads(path.read_text());answer=raw['answer']
        expected=case['expected_fact_ids']
        points=[dict(fact_id=f,reference_correctness=int(f=='checks_not_sales' and case['id']=='dense-table'),
                     completeness=int(f=='checks_not_sales' and case['id']=='dense-table'),
                     supplied_evidence_coverage=int(f=='checks_not_sales' and case['id']=='dense-table')) for f in expected]
        if case['id']=='dense-table':
            note='Only disclaimer/notes are supplied. The checks-not-sales point is correct and explicitly supported by source 1, page 1 offsets 4907:5738. Four count omissions accurately describe the supplied excerpt, but fail original-page completeness. They are missing-information reviews, not uncited invented source facts.'
            claims=[dict(kind='disclaimer',faithfulness=1,citation_support=1,citation_coverage=1,source_ids=[1])]
            abstention=False;relevance=1
        elif case['id']=='state-totals' and arm=='single':
            note='The answer invents 29,801 for Alabama, 5,733 for Alaska, and 32,667 for Arizona. Source 1 contains only disclaimer/notes and supports none of these. Original gold is 71,137 / 7,095 / 27,087. Three separate bullets have syntactically valid but unsupported [1] citations. Introductory framing is not a separate claim.'
            claims=[dict(kind=label,observed=value,faithfulness=0,citation_support=0,citation_coverage=0,source_ids=[1]) for label,value in [('Alabama','29,801'),('Alaska','5,733'),('Arizona','32,667')]]
            abstention=False;relevance=1
        elif case['id']=='state-totals':
            note='No final sources supplied; the application returns an insufficient-information refusal. Faithful to its empty context, but the original question is answerable and all three counts are omitted. No source-fact or citation claim denominator.'
            claims=[];abstention=True;relevance=0.5
        else:
            note='Scope resolution reads background-checks.pdf" for November 2015 as the filename, despite an explicit ready file ID. No retrieval or model answer is attempted. The clarification/refusal is an incorrect product outcome for an answerable scoped question. Blanks and grouped values are untested by generation; all four requested points are absent.'
            claims=[];abstention=True;relevance=0.5
        history=raw['saved_message']['sources']
        normalized=[{k:v for k,v in s.items() if k!='file_deleted'} for s in history]
        rows.append(dict(case_id=case['id'],arm=arm,raw_sha256=sha256(path.read_bytes()).hexdigest(),answer_text=answer['answer'],
            points=points,claim_groups=claims,incorrect_full_abstention=abstention,answer_relevance=relevance,review_note=note,
            raw_history_sources_match=raw['history_sources_match'],history_common_source_fields_match=normalized==answer['sources'],
            history_difference='Saved history adds file_deleted=false; all source contract fields match.' if history else 'No sources in either payload.'))
result=dict(reviewer='Root Codex model reviewer; independent of the primary reviewer; not human',reviewed_at=datetime.now(timezone.utc).isoformat(),
    method='Read all six raw answers, all supplied source bodies, current extraction/gold and request diagnostics. Inspect source/schema differences separately. Primary reviewer quality verdicts were withheld before this first pass.',
    expected_points=24,correct_complete_points=sum(p['reference_correctness'] for r in rows for p in r['points']),
    claims_supported=sum(c['faithfulness'] for r in rows for c in r['claim_groups']),claim_count=sum(len(r['claim_groups']) for r in rows),rows=rows)
(ROOT/'root-review.json').write_text(json.dumps(result,indent=2)+'\n')
print('Preserved independent root review: all six answers, exact raw hashes, point and claim judgments, and history schema normalization.')
