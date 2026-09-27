"""Freeze original-page expectations before any provider-backed answers."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

root = Path(__file__).parent
manifest = json.loads(Path('evals/materials/pdf-v2/manifest.json').read_text())
for document in manifest:
    assert hashlib.sha256((Path('evals/materials/pdf-v2') / document['file']).read_bytes()).hexdigest() == document['sha256']

facts = {
 'paper_pages': ('doclaynet.pdf', [1,2], 'DocLayNet contains 80,863 manually annotated document pages.', ['80863']),
 'paper_classes': ('doclaynet.pdf', [1,2], 'DocLayNet has 11 distinct layout classes.', ['11', 'class']),
 'paper_human': ('doclaynet.pdf', [2], 'DocLayNet uses human annotation rather than automated ground-truth generation.', ['Human Annotation']),
 'paper_automatic': ('doclaynet.pdf', [2], 'PubLayNet and DocBank used automation and scientific repositories; their layouts are less diverse.', ['automation', 'scientific']),
 'lecture_book': ('ml-lecture.pdf', [3], 'No textbook is required; reading assignments are on the class homepage.', ['No required book', 'Reading assignments on class homepage']),
 'lecture_yu': ('ml-lecture.pdf', [3], 'Yaoliang Yu is a guest lecturer.', ['Yaoliang Yu']),
 'lecture_wilson': ('ml-lecture.pdf', [3], 'Andrew Wilson is a guest lecturer.', ['Andrew Wilson']),
 'lecture_homework': ('ml-lecture.pdf', [4], 'Four homework assignments account for 40% of the grade.', ['4 homework assignments', '40%']),
 'lecture_project': ('ml-lecture.pdf', [4], 'The final project accounts for 40% of the grade.', ['Final project', '40%']),
 'lecture_exam': ('ml-lecture.pdf', [4], 'One midterm accounts for 20% of the grade.', ['midterm', '20%']),
 'lecture_team': ('ml-lecture.pdf', [4], 'Project teams have three members.', ['3-member team']),
 'lecture_when': ('ml-lecture.pdf', [4], 'Teams should be formed in the first two weeks.', ['first two weeks']),
 'apple_sales_q': ('apple-fy24.pdf', [1], 'Three months ended September 28, 2024 total net sales are 94,930 million dollars.', ['Total net sales', '94,930']),
 'apple_sales_y': ('apple-fy24.pdf', [1], 'Twelve months ended September 28, 2024 total net sales are 391,035 million dollars.', ['Total net sales', '391,035']),
 'apple_units': ('apple-fy24.pdf', [1], 'Sales and income figures are in millions; share counts and per-share amounts have exceptions.', ['In millions']),
 'apple_income_q': ('apple-fy24.pdf', [1], 'Three months ended September 28, 2024 net income is 14,736 million dollars.', ['Net income', '14,736']),
 'apple_income_y': ('apple-fy24.pdf', [1], 'Twelve months ended September 28, 2024 net income is 93,736 million dollars.', ['Net income', '93,736']),
 'technical_native': ('docling-report.pdf', [5], 'Apple M3 Max, four threads, native backend: 177 seconds and 1.27 pages per second.', ['177', '1.27']),
 'technical_pypdfium': ('docling-report.pdf', [5], 'Apple M3 Max, four threads, pypdfium backend: 103 seconds and 2.18 pages per second.', ['103', '2.18']),
 'technical_ocr': ('docling-report.pdf', [5], 'OCR is disabled for the benchmark table.', ['OCR is disabled']),
 'technical_lowresource': ('docling-report.pdf', [4], 'The report recommends pypdfium for very low-resource environments because it is faster and more memory efficient.', ['low-resource', 'pypdfium']),
 'technical_tradeoff': ('docling-report.pdf', [4], 'That backend trades off worse output quality, especially table structure recovery.', ['worse quality', 'table structure recovery']),
 'technical_dataset': ('docling-report.pdf', [3], 'The layout model is derived from RT-DETR and retrained on DocLayNet, among other proprietary datasets.', ['re-trained on DocLayNet']),
 'alabama_permit': ('background-checks.pdf', [1], 'Alabama, November 2015: Permit is 18,870.', ['Alabama', '18,870']),
 'alabama_handgun': ('background-checks.pdf', [1], 'Alabama, November 2015: Handgun is 23,022.', ['Alabama', '23,022']),
 'alabama_longgun': ('background-checks.pdf', [1], 'Alabama, November 2015: Long Gun is 22,650.', ['Alabama', '22,650']),
 'alabama_total': ('background-checks.pdf', [1], 'Alabama, November 2015: Totals is 71,137.', ['Alabama', '71,137']),
 'checks_not_sales': ('background-checks.pdf', [1], 'The figures count background checks, not firearms sold; one-to-one correlation cannot be made.', ['do not represent', 'firearms sold']),
}
cases=[]
def add(id,category,question,scope,points,*,missing=(),followup=None,answerable=True):
 cases.append(dict(id=id,category=category,question=question,files=scope,expected_fact_ids=points,
                   expected_missing=list(missing),followup_of=followup,answerable=answerable))
add('paper-facts','paper_simple','In "doclaynet.pdf", how many manually annotated pages and layout classes does DocLayNet contain?', ['doclaynet.pdf'], ['paper_pages','paper_classes'])
add('paper-paraphrase','paper_paraphrase','In "doclaynet.pdf", how does the way DocLayNet was labeled differ from PubLayNet and DocBank, and what limits the older datasets\' layout variety?', ['doclaynet.pdf'], ['paper_human','paper_automatic'])
add('lecture-logistics','lecture_compound','In "ml-lecture.pdf", is a textbook required, where are readings assigned, and who are the guest lecturers?', ['ml-lecture.pdf'], ['lecture_book','lecture_yu','lecture_wilson'])
add('lecture-grades','lecture_compound','In "ml-lecture.pdf", give the grade weights for homework, the final project and the midterm, and state the project team size.', ['ml-lecture.pdf'], ['lecture_homework','lecture_project','lecture_exam','lecture_team'])
add('lecture-followup','followup','When should those teams be formed?', ['ml-lecture.pdf'], ['lecture_when'], followup='lecture-grades')
add('apple-sales','report_table','In "apple-fy24.pdf", compare total net sales for the three and twelve months ended September 28, 2024, and state the units.', ['apple-fy24.pdf'], ['apple_sales_q','apple_sales_y','apple_units'])
add('apple-income','report_table','In "apple-fy24.pdf", what was net income for the three and twelve months ended September 28, 2024? Include units.', ['apple-fy24.pdf'], ['apple_income_q','apple_income_y','apple_units'])
add('technical-table','merged_table_limit','In "docling-report.pdf", compare TTS and pages per second for the native and pypdfium backends on Apple M3 Max with four threads. Was OCR enabled for that table?', ['docling-report.pdf'], ['technical_native','technical_pypdfium','technical_ocr'])
add('technical-tradeoff','report_prose','In "docling-report.pdf", which PDF backend is recommended for very low-resource environments, and what quality tradeoff is stated?', ['docling-report.pdf'], ['technical_lowresource','technical_tradeoff'])
add('dependent-dataset','cross_document_dependency','Which public dataset was used to retrain the layout model described in "docling-report.pdf", and how many pages and layout classes does that dataset\'s paper, "doclaynet.pdf", report?', ['docling-report.pdf','doclaynet.pdf'], ['technical_dataset','paper_pages','paper_classes'])
add('dense-table','dense_table_limit','In "background-checks.pdf", report Alabama\'s Permit, Handgun, Long Gun and Totals values for November 2015. Do these statistics represent firearms sold?', ['background-checks.pdf'], ['alabama_permit','alabama_handgun','alabama_longgun','alabama_total','checks_not_sales'])
add('apparent-conflict','scope_not_conflict','In "apple-fy24.pdf", are the 2024 total net sales figures 94,930 and 391,035 contradictory? Explain their respective reporting periods.', ['apple-fy24.pdf'], ['apple_sales_q','apple_sales_y'])
add('partial-lecture','partial','In "ml-lecture.pdf", name the guest lecturers and give the exact number of students enrolled in this course.', ['ml-lecture.pdf'], ['lecture_yu','lecture_wilson'], missing=['The exact course enrollment count is not supplied.'])
add('forecast-missing','unanswerable','In "apple-fy24.pdf", what exact total net sales does Apple forecast for the twelve months ending in fiscal 2025?', ['apple-fy24.pdf'], [], missing=['No exact fiscal 2025 net-sales forecast is supplied.'], answerable=False)
add('restricted-dependency','scope_partial','Using only "docling-report.pdf", name the public dataset used to retrain its layout model and give that dataset\'s exact number of annotated pages.', ['docling-report.pdf'], ['technical_dataset'], missing=['The exact number of DocLayNet pages is not supplied in this allowed report.'])
add('unsupported-screenshot','deferred_visual','In "ml-lecture.pdf", transcribe every navigation label visible inside the embedded browser screenshot on physical page 2.', ['ml-lecture.pdf'], [], missing=['Embedded screenshot text is outside this text-only extraction; the surrounding webpage URL is not its navigation content.'], answerable=False)
artifact=dict(frozen_at=datetime.now(timezone.utc).isoformat(),reviewer='Codex (model), original-page visual inspection plus full-document text search; no human reviewer',
 corpus=manifest, facts={k:dict(file=v[0],physical_pages=v[1],expected=v[2],anchors=v[3]) for k,v in facts.items()},cases=cases,
 annotation_scope='Development corpus reused from parser selection. Facts are based on original rendered pages, not extraction output. Anchor spans are retrieval diagnostics, not semantic support judgments. Fully unanswerable labels rely on full-document text search and scope, not exhaustive visual review of every page.')
target=root/'frozen-cases.json'
assert not target.exists()
target.write_text(json.dumps(artifact,indent=2)+'\n')
print(f'Frozen {len(cases)} cases, {len(facts)} facts and {len(manifest)} original PDFs.')
