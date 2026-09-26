"""Freeze new functional acceptance questions and exact existing corpus spans."""
import json
from pathlib import Path
from evals.automatic import load_benchmark
from evals.evaluate import digest,git_state,timestamp,write_json
from knowledgebase.rag.generation import ANSWER_INSTRUCTIONS
DIR=Path(__file__).parent
_,manifest,documents=load_benchmark()
FAQ='masters-in-data-science-faq-general.txt'
API='anthropic_api.md'
IND='masters-in-data-science-industry-concentration.txt'


def span(file,quote,points):
    text=documents[file];assert text.count(quote)==1
    start=text.index(quote);end=start+len(quote)
    return {'file':file,'quote':quote,'start_offset':start,'end_offset':end,
            'line':text[:start].count('\n')+1,'end_line':text[:end].count('\n')+1,'supports_answer_points':points}


def case(identity,question,points,evidence,answerable=True):
    return {'id':identity,'question':question,'answerable':answerable,'category':'frozen-functional-acceptance',
        'expected_answer_points':points,'evidence':evidence if answerable else [],
        'context_evidence':[] if answerable else evidence,'split':'new-frozen-functional-acceptance'}


cases=[
case('accept-load-hours','According to the saved general FAQ, what credit load distinguishes full-time from part-time CDS students, and what weekly effort should a student with the prerequisites plan for each data science course?',[
'Full-time students register for 9 credits; part-time students register for less than 9 credits.',
'Plan 10–15 hours per week per data science course, assuming all prerequisites are met.'],[
span(FAQ,'Full-time CDS students register for 9 credits. Part-time students register for less than 9 credits.',[1]),
span(FAQ,'Students should plan on spending 10-15 hours per week per data science course, assuming they have all the prerequisites.',[2])]),
case('accept-independent-passfail','According to the saved general FAQ, how many DS-GA 1010 credits can count toward the MSDS, and which courses can be counted pass/fail? Include the exclusion and the Industry Concentration allowance.',[
'Up to 6 credits of independent study, DS-GA 1010, can count.',
'Only one elective, excluding the One Data Science Elective requirement, and DS-GA 1009 may count pass/fail.',
'Industry Concentration students can use the one-elective allowance for an Industry Concentration elective.',
'Required degree courses cannot be taken pass/fail.'],[
span(FAQ,'MSDS students can apply up to 6 credits of independent study (DS-GA 1010) to the MSDS degree.',[1]),
span(FAQ,'Only 1 elective (this does not include the “One Data Science Elective” requirement) and DS-GA 1009 can be taken as pass/fail and count towards the MSDS degree. Students in the Industry Concentration can use their 1 elective allowance for an Industry Concentration elective. Required courses for the degree cannot be taken as pass/fail.',[2,3,4])]),
case('accept-course-two-areas','In the saved Industry Concentration page, is DS-GA 1012 listed under Big Data, Natural Language Processing, or both, and what current course title is given?',[
'DS-GA 1012 appears in both the Big Data and Natural Language Processing lists.',
'The title is Large Language Models: Evaluation and Applications.'],[
span(IND,documents[IND][documents[IND].index('Big Data\n\nThe courses below'):documents[IND].index('\n\nReferenced links')],[1,2])]),
case('accept-awards-jobs','According to the saved general FAQ, how are applicants considered for tuition scholarships, how are recipients notified, and is an on-campus research or teaching position guaranteed?',[
'A limited number of tuition scholarships are competitive; all admission applicants are considered.',
'Recipients are notified in their admit letter.',
'On-campus positions are not guaranteed for any individual, are competitive, and typically posted semester by semester.'],[
span(FAQ,'CDS offers a limited number of tuition scholarships for our students. All applicants for admission are considered for these awards on a competitive basis. Scholarship recipients will be notified in their admit letter.',[1,2]),
span(FAQ,'On-campus positions are available at CDS and NYU, but we do not guarantee such opportunities for any given student. Positions are competitive, and are typically posted on a semester-by-semester basis.',[3])]),
case('accept-beta-header-scope','In the saved DeepSeek Anthropic guide, does anthropic-beta have the same behavior for /messages and Files API endpoints? What happens to anthropic-version?',[
'anthropic-beta is ignored for /messages but required for Files API endpoints with files-api-2025-04-14.',
'anthropic-version is ignored.'],[
span(API,'| anthropic-beta | Ignored for `/messages`; required (`files-api-2025-04-14`) for Files API endpoints — see [Files API](https://api-docs.deepseek.com/guides/files_api#anthropic-compatible-files-api) |',[1]),
span(API,'| anthropic-version | Ignored |',[2])]),
case('accept-message-subfields','According to the saved DeepSeek Anthropic compatibility table, what are the support statuses of text content citations, tool_use id, and tool_result is_error? Keep the nested fields distinct.',[
'Text content citations are ignored.',
'The id field of tool_use content is fully supported.',
'The is_error field of tool_result content is ignored.'],[
span(API,r'| content | array, type="text" | citations | Ignored |',[1]),
span(API,r'| content | array, type = "tool\_use" | id | Fully Supported |',[2]),
span(API,r'| content | array, type = "tool\_result" | is\_error | Ignored |',[3])]),
case('accept-unspecified-api-error','What exact HTTP status code and JSON error body does the saved DeepSeek Anthropic guide promise when a request contains a search_result content block?',[
'The saved guide does not specify the exact HTTP status code or JSON error body; do not invent either.'],[
span(API,r'| content | array, type = "search\_result" |  | Not Supported |',[1])],False),
case('accept-personal-study-approval','Has my own DS-GA 1010 independent-study proposal already been approved, and who is my assigned supervisor?',[
'The provided public documents do not establish the user’s proposal approval status or assigned supervisor; explicitly acknowledge the missing personal information without inventing it.'],[],False),
]

if __name__=='__main__':
    assert not (DIR/'freeze.json').exists()
    prior=json.loads((DIR.parent/'20260925T002400Z-semantic-acceptance/cases.json').read_text())
    assert not {c['question'] for c in cases}&{c['question'] for c in prior}
    write_json(DIR/'cases.json',cases);write_json(DIR/'corpus.json',manifest)
    write_json(DIR/'freeze.json',{'frozen_at':timestamp(),'git':git_state(),'cases_sha256':digest((DIR/'cases.json').read_bytes()),
        'corpus_sha256':digest((DIR/'corpus.json').read_bytes()),'prompt_sha256':digest(ANSWER_INSTRUCTIONS.encode()),
        'reviewer':'Codex, same agent that authored the cases; not independent human review.',
        'scope':'Eight new questions on an already familiar frozen corpus. Never call this an independent held-out accuracy estimate.',
        'config':{'chunking_strategy':'parent_child','chunk_max_tokens':512,'parent_max_tokens':1536,'chunk_tokenizer':'cl100k_base',
                  'retrieval_strategy':'hybrid','retrieval_candidate_limit':20,'retrieval_top_k':5,'bm25_k1':1.2,'bm25_b':0.75,'rrf_k':60,
                  'rerank_enabled':False,'rerank_unit':'child','evidence_max_tokens':4096,'evidence_packing_strategy':'parent_then_child',
                  'answer_model':'gpt-4.1','embedding_model':'text-embedding-3-small','eval_timeout_seconds':60,'eval_max_retries':0,
                  'data_dir':'data/evals/20260925-v1-codex-acceptance'}})
    print('Frozen 8 questions: 6 answerable, 2 unanswerable; all source quotes validated.')
