import importlib.util
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from evals.evaluate import read_jsonl

spec = importlib.util.spec_from_file_location('supplement', __file__.replace('test_supplement.py', 'supplement.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize('case_id', ['msds-credits', 'msds-industry'])
def test_resume_sends_only_original_failed_assessment_and_preserves_error(case_id):
    prior = next(r for r in read_jsonl(module.ORIGIN / 'reviews.jsonl') if r['case_id'] == case_id)
    answer = next(r for r in read_jsonl(module.ORIGIN / 'answers.jsonl') if r['case_id'] == case_id)
    case = next(c for c in json.loads((module.BASELINE / 'cases.json').read_text()) if c['id'] == case_id)
    original = json.dumps(prior, sort_keys=True)
    sdk = SimpleNamespace(responses=SimpleNamespace(create=Mock(side_effect=TimeoutError)))
    row = module.resume(sdk, prior, case, answer)
    sdk.responses.create.assert_called_once()
    sent = sdk.responses.create.call_args.kwargs
    assert sent['input'] == prior['calls'][-1]['messages']
    assert sent['text']['format']['schema'] == prior['calls'][-1]['schema']
    assert row['inventory'] == prior['inventory'] and row['claims'] == prior['claims']
    assert row['status'] == 'error' and row['error_type'] == 'TimeoutError'
    assert len(row['calls']) == 1
    assert json.dumps(prior, sort_keys=True) == original
