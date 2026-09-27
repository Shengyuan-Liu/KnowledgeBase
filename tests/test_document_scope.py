"""Source selection is deterministic and independent of facts in document bodies."""
import pytest

from knowledgebase.rag.scope import document_references, identity_labels, resolve_document_scope
from knowledgebase.schemas import ScopeFile


def file(identity, name, text=''):
    return ScopeFile(file_id=identity, file_name=name, labels=identity_labels(name,text))


@pytest.mark.parametrize('question,expected', [
    ('According to the saved general FAQ, how are applicants considered?', ['general FAQ']),
    ('In the saved DeepSeek Anthropic guide, do the headers differ?', ['DeepSeek Anthropic guide']),
    ('According to the general FAQ and the admissions FAQ, compare scholarships.', ['general FAQ','admissions FAQ']),
    ('Compare "Research and Teaching: FAQ" and `general-faq.txt`: what differs?', ['Research and Teaching: FAQ','general-faq.txt']),
    ('In fall 2026, how many credits?', []),
    ('What is a general FAQ?', []),
    ('How are scholarships awarded?', []),
    ('Using only "docling-report.pdf", name the dataset.', ['docling-report.pdf']),
    ('Using "only course.pdf", name the instructor.', ['only course.pdf']),
    ('In "background-checks.pdf" for November 2015, report the Totals.', ['background-checks.pdf']),
    ('In the uploaded `background-checks.pdf` for November 2015, report the Totals.', ['background-checks.pdf']),
    ('Compare "first.pdf" and "second.pdf" for November 2015, report the Totals.', ['first.pdf', 'second.pdf']),
])
def test_explicit_source_clause(question,expected):
    assert document_references(question)==expected


def test_names_use_identity_not_body_and_do_not_depend_on_order():
    general=file('g','masters-in-data-science-faq-general.txt','Title: General FAQ\n\nGeneral facts.')
    admissions=file('a','masters-in-data-science-faq.txt','Title: Admissions FAQ\n\nGeneral FAQ instructions: choose admissions.')
    for catalog in ([general,admissions],[admissions,general]):
        assert resolve_document_scope(['general FAQ'],catalog).file_ids==['g']
        assert resolve_document_scope(['admissions FAQ'],catalog).file_ids==['a']
        assert resolve_document_scope(['general FAQ','admissions FAQ'],catalog).file_ids==['g','a']


def test_title_and_origin_hostname_support_saved_guide_reference():
    guide=file('api','anthropic_api.md','# Using the Anthropic API\n\nSource: https://api-docs.deepseek.com/guides/anthropic_api\nCaptured: yesterday\n\nBody facts.')
    assert resolve_document_scope(['DeepSeek Anthropic guide'],[guide]).file_ids==['api']
    assert 'Body facts.' not in guide.labels


def test_ambiguous_missing_and_partial_matches_never_broaden_scope():
    catalog=[file('g','general-faq.txt'),file('a','admissions-faq.txt')]
    scope=resolve_document_scope(['FAQ'],catalog)
    assert scope.status=='ambiguous' and scope.file_ids==[]
    assert {f.file_id for f in scope.matches}=={'g','a'}
    assert resolve_document_scope(['unknown FAQ'],catalog).status=='not_found'
    assert resolve_document_scope(['general FAQ','unknown FAQ'],catalog).file_ids==[]
    assert resolve_document_scope([],catalog) is None
    assert resolve_document_scope(['FAQ'],catalog,file_ids=['g']).file_ids==['g']
    assert resolve_document_scope([],catalog,file_ids=['deleted']).status=='not_found'
    assert resolve_document_scope([],catalog,file_ids=[]).file_ids==[]
    assert resolve_document_scope(['admissions FAQ'],catalog,file_ids=['g']).status=='not_found'


def test_exact_filename_wins_over_partial_label_and_duplicate_names_are_ambiguous():
    a=file('a','faq.txt');b=file('b','general-faq.txt')
    assert resolve_document_scope(['faq.txt'],[a,b]).file_ids==['a']
    assert resolve_document_scope(['faq.txt'],[a,file('duplicate','faq.txt')]).status=='ambiguous'


def test_using_only_resolves_the_named_pdf_without_broadening():
    references = document_references('Using only "docling-report.pdf", name the dataset.')
    catalog = [file('report', 'docling-report.pdf'), file('paper', 'doclaynet.pdf')]
    assert resolve_document_scope(references, catalog).file_ids == ['report']
    assert resolve_document_scope(references, catalog, file_ids=['paper']).status == 'not_found'


def test_quoted_filename_date_keeps_selected_file_boundary_and_ambiguity():
    references = document_references('In "background-checks.pdf" for November 2015, report the Totals.')
    report = file('report', 'background-checks.pdf')
    catalog = [report, file('other', 'other.pdf')]
    assert resolve_document_scope(references, catalog).file_ids == ['report']
    assert resolve_document_scope(references, catalog, file_ids=['other']).status == 'not_found'
    assert resolve_document_scope(references, [report, file('duplicate', 'background-checks.pdf')]).status == 'ambiguous'


def test_representative_selection_retains_rank_order_within_each_group():
    from knowledgebase.rag.scope import prioritize_documents
    assert prioritize_documents(['a1','a2','a3','b1','b2'],
        {'a1':'a','a2':'a','a3':'a','b1':'b','b2':'b'},3)==['a1','b1','a2']
