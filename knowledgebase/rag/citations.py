"""Check the bracketed source numbers requested by the answer prompt."""

import re

from knowledgebase.schemas import AnswerSource, CitationCheck


def validate_citations(answer: str, sources: list[AnswerSource]) -> CitationCheck:
    """Match [n] references against this answer's actual source IDs.

    Return unique IDs in order of first appearance. Only the requested [n]
    syntax is recognized; grouped references such as [1, 2] are not expanded.
    Keep the original answer unchanged. No citations is an observation, not
    necessarily an error (for example, an insufficient-evidence response).
    """
    cited_ids = list(dict.fromkeys(int(number) for number in re.findall(r"\[([0-9]+)\]", answer)))
    source_ids = {source.source_id for source in sources}
    return CitationCheck(
        valid_source_ids=[number for number in cited_ids if number in source_ids],
        invalid_source_ids=[number for number in cited_ids if number not in source_ids],
        no_citations=not cited_ids,
    )
