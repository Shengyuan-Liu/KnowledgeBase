from unittest.mock import Mock

import pytest

from knowledgebase.providers.llm import LLMClient
from knowledgebase.rag.generation import generate_answer, stream_answer
from knowledgebase.schemas import Chunk, RetrievedChunk


def test_empty_retrieval_returns_insufficient_evidence_without_calling_model():
    llm = Mock(spec=LLMClient)

    answer = generate_answer("When does the library close?", [], llm)

    assert answer == (
        "There is not enough information in the provided sources to answer this question."
    )
    llm.generate.assert_not_called()


def test_numbers_sources_in_retrieval_order_and_preserves_question_and_text():
    chunks = [
        RetrievedChunk(
            file_name="notes.txt",
            chunk=Chunk(
                chunk_id="chunk-z",
                file_id="file-b",
                text="  In fall 2026, the café closes at 5 PM.\n",
                index=3,
                start_offset=120,
                end_offset=163,
            ),
            distance=0.1,
        ),
        RetrievedChunk(
            file_name="notes.txt",
            chunk=Chunk(
                chunk_id="chunk-a",
                file_id="file-a",
                text="In spring 2026, the café closes at 4 PM.",
                index=0,
                start_offset=0,
                end_offset=38,
            ),
            distance=0.2,
        ),
    ]
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = "It closes at 5 PM in fall 2026. [1]\n"

    answer = generate_answer("  When does the café close in fall 2026?\n", chunks, llm)

    assert answer == "It closes at 5 PM in fall 2026. [1]\n"
    llm.generate.assert_called_once()
    user_message, instructions = llm.generate.call_args.args[0]
    assert instructions["role"] == "developer"
    assert "using only the provided sources" in instructions["content"]
    assert "Cite supporting source numbers inline" in instructions["content"]
    assert "do not contain enough information" in instructions["content"]
    assert user_message == {
        "role": "user",
        "content": (
            "Question:\n  When does the café close in fall 2026?\n\n\nSources:\n"
            '[1]\nSource metadata: {"file_name": "notes.txt", "heading_path": []}\nExcerpt:\n'
            '  In fall 2026, the café closes at 5 PM.\n\n\n'
            '[2]\nSource metadata: {"file_name": "notes.txt", "heading_path": []}\nExcerpt:\n'
            'In spring 2026, the café closes at 4 PM.'
        ),
    }


@pytest.mark.anyio
async def test_comparison_prompt_is_shared_by_json_and_streaming_with_later_evidence():
    """Guard source identity and later excerpts; live experiments assess semantics."""
    texts = [
        'Title: Industry Concentration\nA mandatory internship is required within the first year. Consult OGS about early CPT.',
        'Title: General FAQ\nThe program connects students with companies.',
        'Title: Admissions FAQ\nCPT allows paid internships for credit after the first year.',
    ]
    chunks = [RetrievedChunk(file_name=f'source-{i}.txt', distance=0.1,
                            chunk=Chunk(chunk_id=str(i), file_id=str(i), text=text,
                                        index=0, start_offset=0, end_offset=len(text)))
              for i, text in enumerate(texts)]
    question = 'Compare internship timing in the admissions FAQ and concentration page.'
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = 'Within the first year [1]; after the first year [3].'
    generate_answer(question, chunks, llm)
    captured = []

    class Stream:
        async def stream(self, messages):
            captured.append(messages)
            yield 'Within the first year [1]; '
            yield 'after the first year [3].'

    answer = ''.join([part async for part in stream_answer(question, chunks, Stream())])
    assert answer == llm.generate.return_value
    assert captured == [llm.generate.call_args.args[0]]
    user, instructions = captured[0]
    assert 'check all provided excerpts for each named' in instructions['content']
    assert 'not interchangeable' in instructions['content']
    assert 'Use one labeled item per named document' in instructions['content']
    assert 'silence is not the opposite policy' in instructions['content']
    assert 'Limit absence claims to the' in instructions['content']
    assert 'source comparisons use the per-document items' in instructions['content']
    assert 'require an explicit statement in the evidence' in instructions['content']
    assert user['content'].endswith('Excerpt:\n' + texts[-1])
    assert '[3]\nSource metadata: {"file_name": "source-2.txt", "heading_path": []}' in user['content']
    assert [user['content'].count(text) for text in texts] == [1, 1, 1]


@pytest.mark.anyio
@pytest.mark.parametrize('text,question', [
    ('| name | Fully Supported |\n| cache_control | Ignored |',
     'Which tool fields are supported?'),
    ('Only effort is supported in output_config.',
     'How is output_config supported?'),
    ('| anthropic-beta | Ignored for /messages; required for Files API endpoints |\n'
     '| anthropic-version | Ignored |',
     'Do these headers have the same behavior across endpoints?'),
    ('Capstone projects typically have two to four people.',
     'Which project have I personally been assigned to?'),
])
async def test_citation_and_fidelity_instructions_reach_both_generation_paths(text, question):
    """Observed table, behavior-inference and personal-advice regressions share one prompt.

    Mocked calls verify prompt delivery and evidence fidelity, not model compliance.
    """
    from knowledgebase.rag.generation import ANSWER_INSTRUCTIONS

    chunks = [RetrievedChunk(file_name='source.txt', distance=0.1,
        chunk=Chunk(chunk_id='one', file_id='file', text=text, index=0,
                    start_offset=0, end_offset=len(text)))]
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = 'Recorded output [1].'
    generate_answer(question, chunks, llm)
    captured = []

    class Stream:
        async def stream(self, messages):
            captured.append(messages)
            yield 'Recorded output [1].'

    assert ''.join([part async for part in stream_answer(question, chunks, Stream())]) == llm.generate.return_value
    messages = llm.generate.call_args.args[0]
    assert captured == [messages]
    assert messages[1] == {'role': 'developer', 'content': ANSWER_INSTRUCTIONS}
    assert 'Cite every factual list item separately' in messages[1]['content']
    assert 'does not establish whether it is ignored, rejected' in messages[1]['content']
    assert 'Do not add unsupported advice' in messages[1]['content']
    assert 'Keep each claim\'s scope no broader or narrower than its source' in messages[1]['content']
    assert 'Retain explicit source restrictions and exceptions' in messages[1]['content']
    assert 'For a table lookup, quote the relevant status cell' in messages[1]['content']
    assert 'one sentence or list item per requested' in messages[1]['content']
    assert 'Use English for all explanatory text' in messages[1]['content']
    assert 'do not repeat the answer' in messages[1]['content']
    assert messages[0]['content'].startswith(f'Question:\n{question}\n\nSources:\n[1]\n')
    assert messages[0]['content'].endswith('Excerpt:\n' + text)


@pytest.mark.anyio
@pytest.mark.parametrize('reverse', [False, True])
async def test_named_document_identity_survives_similar_excerpts_and_reordering(reverse):
    """Guard the actual prompt/evidence contract, not mocked semantic compliance."""
    entries = [
        ('admissions-faq.txt', 'All applicants are considered. No separate application is needed.'),
        ('general-faq.txt', 'All applicants are considered. Awards are competitive.'),
    ]
    if reverse:
        entries.reverse()
    chunks = [RetrievedChunk(file_name=name, distance=0.1,
        chunk=Chunk(chunk_id=name, file_id=name, text=text, index=0,
                    start_offset=0, end_offset=len(text))) for name, text in entries]
    question = 'According to the general FAQ, how are applicants considered?'
    llm = Mock(spec=LLMClient)
    llm.generate.return_value = 'Unmodified provider output.'
    assert generate_answer(question, chunks, llm) == llm.generate.return_value
    captured = []

    class Stream:
        async def stream(self, messages):
            captured.append(messages)
            yield llm.generate.return_value

    assert ''.join([delta async for delta in stream_answer(question, chunks, Stream())]) == llm.generate.return_value
    messages = llm.generate.call_args.args[0]
    assert captured == [messages]
    assert 'A fact found only in another document must not be attributed to the named one' in messages[1]['content']
    assert 'Match each claim to its actual supporting excerpt' in messages[1]['content']
    assert question in messages[0]['content']
    for i, (name, text) in enumerate(entries, 1):
        assert f'[{i}]\nSource metadata: {{"file_name": "{name}", "heading_path": []}}\nExcerpt:\n{text}' in messages[0]['content']
