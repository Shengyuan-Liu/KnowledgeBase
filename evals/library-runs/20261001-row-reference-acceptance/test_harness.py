"""Check score denominators and page/scope mapping without provider requests."""
from labels import covered, locations, scores


def test_rank_metrics_include_misses_and_unretrieved_relevant_children():
    chunks = {str(i): dict(file_id='a', start_offset=i*10, end_offset=i*10+9) for i in range(4)}
    labels = {'one': dict(anchors=[dict(spans=[dict(file_id='a', start=11, end=13)])]),
              'two': dict(anchors=[dict(spans=[dict(file_id='a', start=31, end=33)])])}
    result = scores(['0', '1'], ['one', 'two'], chunks, labels)
    assert result['Recall@K'] == .5
    assert result['Precision@K'] == .2
    assert result['MRR'] == .5
    assert result['fact_anchor_recall'] == .5
    assert result['NDCG@K'] < .4
    assert scores(['0'], ['one', 'two'], chunks, labels)['MRR'] == 0
    assert scores(['1'], [], chunks, labels) is None


def test_mapping_uses_annotated_page_and_requires_complete_anchor():
    facts = {'value': dict(file='a.pdf', physical_pages=[2], anchors=['42'])}
    documents = [dict(file=dict(file_name='a.pdf', file_id='a'), extraction=dict(blocks=[
        dict(text='42', start_offset=0, regions=[dict(page_index=0)]),
        dict(text='42', start_offset=10, regions=[dict(page_index=1)])]))]
    label = locations(facts, documents)['value']
    assert label['anchors'][0]['spans'] == [dict(file_id='a', start=10, end=12)]
    assert not covered([dict(file_id='b', start_offset=10, end_offset=12)], label)
    assert not covered([dict(file_id='a', start_offset=10, end_offset=11)], label)
    assert covered([dict(file_id='a', start_offset=10, end_offset=12)], label)
