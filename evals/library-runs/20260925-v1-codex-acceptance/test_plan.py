import importlib.util
from pathlib import Path
from knowledgebase.config import Settings
spec=importlib.util.spec_from_file_location('acceptance_run',Path(__file__).with_name('run.py'))
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


def test_frozen_references_and_defaults():
    frozen,cases,docs=runner.inputs()
    assert len(cases)==8 and sum(c['answerable'] for c in cases)==6 and len(docs)==17
    defaults=Settings(_env_file=None,openai_api_key='offline-test')
    selected=Settings(_env_file=None,openai_api_key='offline-test',**frozen['config'])
    for field in ('chunking_strategy','chunk_max_tokens','parent_max_tokens','retrieval_options','evidence_max_tokens','answer_model','embedding_model'):
        assert getattr(defaults,field)==getattr(selected,field)


def test_unanswerable_cases_do_not_claim_retrievable_personal_or_error_details():
    _,cases,_=runner.inputs()
    missing=[c for c in cases if not c['answerable']]
    assert all(c['evidence']==[] for c in missing)
    assert {c['id'] for c in missing}=={'accept-unspecified-api-error','accept-personal-study-approval'}
