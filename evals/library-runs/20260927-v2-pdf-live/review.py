"""Record Codex's source/answer review; no judge call or inferred truth labels."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / 'effective-cases.json').read_text())

# Reviewed against the original-page facts, all answer text, and supplied sources.
# Unrequested contextual qualifiers (e.g. four homework assignments) are not
# required when the actual question only asks the grade weight.
NOTES = {
 'paper-facts': 'Abstract, introduction and dataset section support 80,863 pages and 11 classes. The label-selection excerpt also supports 11 classes.',
 'paper-paraphrase': 'Introduction supports human versus automatic annotations, scientific repositories and uniform templates. Dataset section supports the extra diversity examples when present.',
 'lecture-logistics': 'Physical page 3 has no required book, readings on the homepage, and the two guest names. The parser joins YaoliangYu; semantic review accepts the restored name spacing.',
 'lecture-grades': 'Physical page 4 supports 40/40/20 percent and three-person teams. The initial merged evidence dropped the locally best grade and team hits.',
 'lecture-followup': 'Physical page 4 specifies forming three-member teams in the first two weeks. A blocked request is an end-to-end failure, not an abstention.',
 'apple-sales': 'The sales child plus header supplements supplies both periods and totals. Its cited excerpt lacks a units label; millions appears in a different supplied income statement. Unit attribution is only partial support in this context.',
 'apple-income': 'Page 4 GAAP reconciliation supports 14,736 and 93,736 million, with explicitly separate non-GAAP amounts. Both planned attempts fabricated a non-contiguous assessor quote and correctly failed strict validation.',
 'technical-table': 'Original page 5 confirms native 177s/1.27 and pypdfium 103s/2.18 for four threads. Extracted paired rows retain enough ordering for these facts, but do not establish general merged-table fidelity. Caption states OCR disabled.',
 'technical-tradeoff': 'Performance section explicitly recommends pypdfium for very low resources and warns of worse table structure recovery.',
 'dependent-dataset': 'The layout-model section names DocLayNet. The separately supplied dataset paper supports size and classes. A decomposed route can answer this case without a dependent hop; inspect actual route, not the case label.',
 'dense-table': 'Original Alabama row: 18,870 / 23,022 / 22,650 / 71,137. All four values are absent from canonical extraction. Single mode instead assigns unrelated 29,905 / 38,487 / 102 / 1,656 to Alabama; citations do not support that association. Repaired planned mode withholds four numbers and answers only the supported background-check caveat.',
 'apparent-conflict': 'Original page 1 establishes quarter versus year. Both single answers are correct against the original but cite the income reconciliation, which does not contain these sales figures. Planned mode abstains after relevant sales candidates are excluded by packing. Correctness and faithfulness differ.',
 'partial-lecture': 'Guest names are supported; exact enrollment is absent. The repaired planned answer states both facts and the missing count. Absence claims are reviewed as missing-point handling, not ordinary factual citations.',
 'forecast-missing': 'No exact 2025 sales forecast in the allowed report. Scope-limited absence is appropriate. An error is not successful abstention.',
 'restricted-dependency': 'The pre-answer correction makes the missing item the double-annotation count, not total pages. Initial leading-only scope parsing failed in both arms. Repair retrieves DocLayNet within the allowed report and withholds the count. The single answer extra note about triple annotations/training is in source 5.',
 'unsupported-screenshot': 'Screenshot navigation is outside native text extraction. Abstention is appropriate; no OCR claim is credited. Initial single answer additionally calls source 2 a course title, but it is only the Class Webpage heading; that extra factual group has partial support.',
}


def normalize(text):
    return re.sub(r'\s+', '', text.casefold())


def factual_lines(answer, case_id):
    result = []
    for raw in answer.splitlines():
        line = re.sub(r'^\s*(?:[-*]|\d+\.)\s*', '', raw).strip()
        if not line or line.endswith(':') or line.endswith('?'):
            continue
        if case_id in {'forecast-missing'}:
            continue
        if any(term in line.lower() for term in ['not enough information', 'could not find a ready',
                'selected document is missing', 'exact number of students', 'number of doclaynet pages with two',
                'provided excerpts do not state how many', 'provided excerpts do not contain an explicit value',
                'provided excerpts from "apple-fy24.pdf" do not include']):
            continue
        if case_id == 'unsupported-screenshot' and 'excerpts mention' not in line:
            continue
        result.append(line)
    return result


rows = []
for pass_name, folder in [('before', ROOT), ('repair', ROOT / 'repair-1')]:
    for case in DATA['cases']:
        for arm in ['single', 'planned']:
            row = json.loads((folder / f"{case['id']}-{arm}.json").read_text())
            answer = row.get('answer', {})
            completed = row['status'] == 'completed'
            identity = case['id']
            error = not completed
            full_abstention = completed and (
                not case['answerable'] or identity == 'apple-sales' and arm == 'single'
                or identity == 'apparent-conflict' and arm == 'planned'
                or identity == 'restricted-dependency' and pass_name == 'before')
            points = []
            for fact in case['expected_fact_ids']:
                correctness = 0 if error or full_abstention else 1
                evidence = 0 if error or full_abstention else 1
                if identity == 'dense-table' and fact.startswith('alabama_'):
                    correctness = evidence = 0
                if identity == 'apparent-conflict':
                    evidence = 0
                if identity == 'apple-sales' and arm == 'planned' and fact == 'apple_units':
                    evidence = .5
                # Completeness gives no credit for a wrong or absent requested value.
                texts = {s['source_id']: s['text'] + '\n' + '\n'.join(x['text'] for x in s['pdf']['supplements'])
                         for s in answer.get('sources', [])}
                anchor_matches = [i for i, t in texts.items() if any(normalize(a) in normalize(t) for a in DATA['facts'][fact]['anchors'])]
                points.append(dict(fact_id=fact, reference_correctness=correctness,
                                   completeness=correctness, supplied_evidence_coverage=evidence,
                                   source_ids_with_matching_anchors=anchor_matches,
                                   evidence_note=NOTES[identity]))
            claims = []
            for line in factual_lines(answer.get('answer', ''), identity):
                cited = [int(x) for x in re.findall(r'\[(\d+)\]', line)]
                support = .5 if identity == 'apple-sales' else 1
                original = 1
                if identity == 'apparent-conflict':
                    support = 0
                if identity == 'dense-table' and arm == 'single' and line.startswith(('Permit:', 'Handgun:', 'Long Gun:', 'Totals:')):
                    support = original = 0
                if identity == 'unsupported-screenshot':
                    support = original = .5
                claims.append(dict(text=line, original_page_correctness=original, context_support=support,
                                   cited_source_ids=cited, citation_support=support if cited else None,
                                   citation_coverage=support if cited else 0,
                                   supporting_evidence_artifact=str((folder / f"{identity}-{arm}.json").relative_to(ROOT)) + '#answer.sources',
                                   note=NOTES[identity]))
            missing = [dict(point=point, correctly_stated=int(completed and not (identity=='restricted-dependency' and pass_name=='before')))
                       for point in case['expected_missing']]
            rows.append(dict(pass_name=pass_name, case_id=identity, arm=arm, answer_status=row['status'],
                source_artifact=str((folder / f"{identity}-{arm}.json").relative_to(ROOT)),
                points=points, factual_claim_groups=claims, missing_point_review=missing,
                relevance=0 if error or identity=='restricted-dependency' and pass_name=='before' else 1,
                full_abstention=full_abstention, appropriate_abstention=int(full_abstention and not case['answerable']),
                incorrect_abstention=int(full_abstention and case['answerable']), note=NOTES[identity]))
path = ROOT / 'reviewed-cases.json'
assert not path.exists()
path.write_text(json.dumps(dict(reviewer='Codex (GPT-6 model), source and answer inspection in this chat; no independent human reviewer, no paid judge call',
 rubric='protocol.md; scalar values 0 / 0.5 / 1. Correctness and completeness are frozen requested-point coverage, including failed cases as zero; contextual details not requested are not required. Citation and faithfulness units are factual claim groups (paragraph/bullet), not token counts. Missing-information claims are scored separately. Compound claim groups receive partial support when a material qualifier is unsupported. Citation support pools the cited passages for one claim; citation coverage requires a supporting inline citation on that claim group. Claim-free answers have no citation/faithfulness denominator; they still affect correctness, abstention and reliability.',
 rows=rows),indent=2)+'\n')
