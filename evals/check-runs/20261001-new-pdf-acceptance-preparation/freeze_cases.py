"""Freeze manually reviewed reference facts independently of production extraction."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from acquire import MATERIALS, ROOT

documents = json.loads((ROOT / 'reference-reading-text.json').read_text())['documents']
pages = {d['file']: {p['physical_page']: p['text'] for p in d['pages']} for d in documents}
manifest = json.loads((MATERIALS / 'manifest.json').read_text())
hashes = {d['file']: d['sha256'] for d in manifest['files']}


def span(file, page, phrase, location, occurrence=None):
    text = pages[file][page]
    tokens = list(re.finditer(r'\S+', text))
    normalized = ' '.join(m.group() for m in tokens)
    matches = list(re.finditer(re.escape(phrase), normalized))
    assert occurrence is not None or len(matches) == 1, (file, page, phrase)
    start = matches[occurrence or 0].start()
    first = normalized[:start].count(' ')
    last = first + len(phrase.split()) - 1
    lo, hi = tokens[first].start(), tokens[last].end()
    assert ' '.join(text[lo:hi].split()) == phrase
    return dict(file=file, source_sha256=hashes[file], physical_page=page,
                location=location, normalized_quote=phrase, raw_quote=text[lo:hi],
                match_count_on_page=len(matches), match_occurrence=occurrence or 0,
                reference_text_start=lo, reference_text_end=hi,
                offset_system='Page-local Poppler reading text; NOT production canonical offsets.')


def fact(identity, expected, evidence, **extra):
    return dict(id=identity, expected=expected, evidence=evidence, **extra)


facts = [
    fact('rag_sequence', 'RAG-Sequence uses the same retrieved document for the complete output sequence.',
         [span('rag-paper.pdf', 3, 'The RAG-Sequence model uses the same retrieved document to generate the complete sequence.', 'Section 2.1, first prose sentence')]),
    fact('rag_token', 'RAG-Token can use a different retrieved document for each target token.',
         [span('rag-paper.pdf', 3, 'In the RAG-Token model we can draw a different latent document for each target token', 'Section 2.1, RAG-Token prose')]),
    fact('retriever_bridge', 'A pretrained bi-encoder from DPR initializes the RAG retriever.',
         [span('rag-paper.pdf', 3, 'a pre-trained bi-encoder from DPR to initialize our retriever and to build the document index.', 'Section 2.2, closing paragraph')],
         accepted_target_strings=['DPR'], target_must_be_literal_in_binding_quote=True),
    fact('negative_gold', 'The best DPR model uses gold (positive) passages from the same mini-batch as negatives.',
         [span('dpr-paper.pdf', 3, 'Our best model uses gold passages from the same mini-batch and one BM25 negative passage.', 'Right column, Positive and negative passages')]),
    fact('negative_bm25', 'The best DPR model also uses one BM25 negative passage.',
         [span('dpr-paper.pdf', 3, 'Our best model uses gold passages from the same mini-batch and one BM25 negative passage.', 'Right column, Positive and negative passages')]),
    fact('overfitting_definition', 'Overfitting means fitting noise or attending to irrelevant parts of the data.',
         [span('decision-trees.pdf', 35, 'algorithm fits noise (i.e. pays attention to parts of the data that are irrelevant)', 'Upper slide, printed Slide 69, definition bullet')], printed_label='Slide 69'),
    fact('overfitting_effect', 'An overfitting algorithm may perform less well on test-set data.',
         [span('decision-trees.pdf', 35, 'then it may perform less well on test set data.', 'Upper slide, printed Slide 69, second bullet')], printed_label='Slide 69'),
]

# Table semantics are transcribed from original page renders, not inferred from
# numeric matches. All four values share measure names but differ by group/period.
for identity, page, value, group, period, alternate_pages in [
    ('quarter_gaap', 1, '24,034', 'GAAP', 'Q4 FY25', [4, 8]),
    ('quarter_nongaap', 1, '25,516', 'Non-GAAP', 'Q4 FY25', [8]),
    ('annual_gaap', 2, '81,453', 'GAAP', 'FY25', [4, 8]),
    ('annual_nongaap', 2, '86,789', 'Non-GAAP', 'FY25', [8]),
]:
    facts.append(fact(identity, f'{period} {group} operating income is USD {value} million.',
        [span('nvidia-fy25.pdf', page, '$'+value, f'{group} summary table; Operating income row; {period} column')],
        table=dict(row='Operating income', group=group, period=period,
                   value=value, currency='USD', scale='millions',
                   distractor_rows=['Operating expenses', 'Net income'],
                   alternate_original_pages=alternate_pages,
                   continued_table_header_page=7,
                   alternative_note='Page 4 is the GAAP income statement; page 8 continues the reconciliation table whose units/date headings are on page 7. Alternatives were visually checked; labels are not exhaustive semantic relevance.')))
facts.append(fact('income_units', 'All four operating-income amounts are expressed in millions of dollars.',
    [span('nvidia-fy25.pdf', 1, '($ in millions, except earnings per share)', 'GAAP summary table unit note; repeated in the Non-GAAP table', occurrence=0)],
    table=dict(currency='USD', scale='millions', note='The earnings-per-share exception does not apply to operating income.')))

DEPENDENT_QUESTION = 'Which retriever supplies the pretrained bi-encoder used to initialize RAG, and what combination of negative passages does that retriever\'s best model use during training? Cite the initialization relationship and the training details from the supplied papers.'
questions = [
    dict(id='rag-document-granularity', question='How do RAG-Sequence and RAG-Token differ in whether they can change the retrieved document while generating an answer?', files=['rag-paper.pdf']),
    dict(id='retriever-training-hop', question=DEPENDENT_QUESTION, files=['rag-paper.pdf', 'dpr-paper.pdf']),
    dict(id='retriever-training-restricted', question=DEPENDENT_QUESTION, files=['rag-paper.pdf']),
    dict(id='lecture-overfitting', question='How does the decision-tree lecture define overfitting, and what effect can it have on test-set performance?', files=['decision-trees.pdf']),
    dict(id='income-period-basis', question='What were NVIDIA\'s GAAP and non-GAAP operating income for Q4 FY25 and for the full fiscal year 2025? Give all four amounts, label each accounting basis and period, and state the units.', files=['nvidia-fy25.pdf']),
    dict(id='forecast-is-not-actual', question='What actual revenue did NVIDIA report for the first quarter of fiscal 2026? Answer only from the selected report.', files=['nvidia-fy25.pdf']),
]
references = [
    dict(case_id='rag-document-granularity', answerability='full', fact_ids=['rag_sequence', 'rag_token'], gap_ids=[]),
    dict(case_id='retriever-training-hop', answerability='full', fact_ids=['retriever_bridge', 'negative_gold', 'negative_bm25'], gap_ids=[],
         dependency=dict(seed='RAG retriever initialization', bridge_fact='retriever_bridge', target='DPR',
                         downstream_facts=['negative_gold', 'negative_bm25'], prerequisite_file='rag-paper.pdf',
                         downstream_file='dpr-paper.pdf',
                         gate='Report answer quality and actual dependent execution separately. Require a resolved target from retained prerequisite evidence before the downstream search; a correct answer or two independent searches alone does not pass the dependent-execution gate.')),
    dict(case_id='retriever-training-restricted', answerability='partial', fact_ids=['retriever_bridge'],
         gap_ids=['negative_gold', 'negative_bm25'],
         abstention='Name DPR with support, but disclose that its negative-training recipe is absent from the selected RAG paper. Do not refuse the supported bridge or use DPR paper evidence outside scope.',
         scope_pair='retriever-training-hop'),
    dict(case_id='lecture-overfitting', answerability='full', fact_ids=['overfitting_definition', 'overfitting_effect'], gap_ids=[]),
    dict(case_id='income-period-basis', answerability='full', fact_ids=['quarter_gaap', 'quarter_nongaap', 'annual_gaap', 'annual_nongaap', 'income_units'], gap_ids=[]),
    dict(case_id='forecast-is-not-actual', answerability='none', fact_ids=[], gap_ids=['actual_q1_fy26_revenue'],
         abstention='The selected report has an outlook, not actual Q1 FY26 revenue. Refuse the unavailable actual amount. An optional clearly labeled forecast needs its own source citation.',
         tempting_but_not_answer=span('nvidia-fy25.pdf', 2, 'Revenue is expected to be $43.0 billion, plus or minus 2%.', 'Outlook, first bullet')),
]


def main():
    timestamp = datetime.now(timezone.utc).isoformat()
    assert timestamp > manifest['frozen_at']
    for name, data in [
        ('questions.json', dict(version=1, created_at=timestamp, retrieval_mode='planned', questions=questions,
                               request_boundary='Send only question and resolved allowed file IDs; no gold facts, answerability labels or expected targets in model input.')),
        ('references.json', dict(version=1, created_at=timestamp, reviewer='Codex (model)', human_review=False,
                                facts=facts, cases=references,
                                counting='12 unique positive facts; 13 positive case-fact instances, because the bridge is repeated in the paired scope case. Four fully answerable, one partial and one fully unanswerable question.',
                                production_span_mapping='unavailable until future production ingestion; map frozen references without changing missing facts into zero-length successes.')),
    ]:
        with (MATERIALS/name).open('x') as output:
            json.dump(data, output, indent=2)
            output.write('\n')
    negatives = []
    for filename, pattern, finding in [
        ('rag-paper.pdf', r'negative|mini.batch|BM25', 'All 16 pages searched in reading-order text. Negative mentions concern likelihood; BM25 mentions concern an ablation and references. No best-DPR negative recipe is supplied. RAG page 3 visually confirms the available bridge.'),
        ('nvidia-fy25.pdf', r'2026|43\.0', 'All 10 pages searched. Q1 FY26 appears as outlook or future conference-call timing, not actual reported revenue. Original page 2 visually distinguishes the forecast.'),
    ]:
        hits = []
        for page, raw in pages[filename].items():
            normalized = ' '.join(raw.split())
            for match in re.finditer(pattern, normalized, re.I):
                hits.append(dict(physical_page=page, term=match.group(),
                                 context=normalized[max(0, match.start()-100):match.end()+200]))
        negatives.append(dict(file=filename, pattern=pattern, searched_physical_pages=len(pages[filename]),
                              matches=hits, reviewer_finding=finding,
                              limitation='Digital text and relevant rendered-page review; not exhaustive visual reading of every embedded image.'))
    with (ROOT / 'absence-review.json').open('x') as output:
        json.dump(dict(reviewer='Codex (model)', reviewed_at=timestamp, cases=negatives), output, indent=2)
        output.write('\n')
    print('Frozen six questions and original-page references before product ingestion or answer generation.')


if __name__ == '__main__':
    main()
