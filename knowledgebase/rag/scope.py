"""Resolve explicit document references against file identity, never source facts."""

from collections.abc import Sequence
from pathlib import Path
import re
from urllib.parse import urlparse

from knowledgebase.rag.bm25 import tokenize
from knowledgebase.schemas import DocumentScope, ScopeFile

_DESCRIPTOR_WORDS = {
    'the', 'a', 'an', 'saved', 'uploaded', 'document', 'documents',
    'file', 'files', 'guide', 'guides', 'page', 'pages',
}


def prioritize_documents(chunk_ids: list[str], files_by_chunk: dict[str, str], limit: int) -> list[str]:
    """Keep the best available hit per document before additional same-file hits.

    Input order is the current ranking. Both groups preserve that order; scores
    are unchanged. The caller applies this only to an explicit multi-file scope.
    """
    representatives, remaining, seen = [], [], set()
    for identity in chunk_ids:
        file_id = files_by_chunk[identity]
        if file_id in seen:
            remaining.append(identity)
        else:
            seen.add(file_id)
            representatives.append(identity)
    return (representatives + remaining)[:limit]


def document_references(question: str) -> list[str]:
    """Read a leading source clause, allowing quoted names and an 'and' list.

    This is bounded syntax, not a general intent classifier. Quotes protect
    punctuation and 'and' inside a title. Other questions remain unrestricted
    unless the caller supplies explicit file IDs.
    """
    prefix = re.match(r'^\s*(?:according to|in|from|using|compare)\s+', question, re.I)
    if not prefix:
        return []
    rest = question[prefix.end():]
    quote = None
    stop = None
    for i, char in enumerate(rest):
        if char in {'"', '`'}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
        elif quote is None and (char in {',', '?'} or (char == ':' and rest[i+1:i+2].isspace())):
            stop = i
            break
    if stop is None:
        return []
    clause = rest[:stop]
    if not re.search(r'\b(?:faqs?|guides?|documents?|files?|pages?)\b|\.(?:md|txt)\b|["`]', clause, re.I):
        return []
    parts = re.split(r'\s+and\s+(?=(?:[^"`]*["`][^"`]*["`])*[^"`]*$)', clause, flags=re.I)
    return [re.sub(r'^(?:(?:the|saved|uploaded)\s+)+', '', part.strip(), flags=re.I).strip('"` ')
            for part in parts]


def identity_labels(file_name: str, source_text: str) -> list[str]:
    """Read filename, opening title/heading and opening Source URL hostname.

    Body text and linked-page content do not participate in name resolution.
    Legacy files without a canonical title still have their filename identity.
    """
    labels = [Path(file_name).stem]
    lines = source_text.lstrip().splitlines()
    if not lines:
        return labels
    first = lines[0]
    if first.startswith('Title:'):
        labels.append(first.removeprefix('Title:').strip())
    elif re.match(r'^#\s+', first):
        labels.append(re.sub(r'^#\s+', '', first))
    else:
        return labels
    for line in lines[1:]:
        if not line.strip():
            continue
        if line.startswith('Source:'):
            labels.append(urlparse(line.removeprefix('Source:').strip()).hostname or '')
        elif not line.startswith(('Captured:', 'Retrieved at', 'Language:')):
            break
    return labels


def resolve_document_scope(
    references: Sequence[str], files: Sequence[ScopeFile], *, file_ids: list[str] | None = None,
) -> DocumentScope | None:
    """Resolve every reference uniquely or return a clarification without evidence.

    Explicit file IDs narrow the catalog first. A missing ID or any unresolved
    reference stops the entire request; no partial selection or global fallback.
    """
    if not references and file_ids is None:
        return None
    catalog = list(files)
    if file_ids is not None:
        ready_ids = {f.file_id for f in files}
        if any(identity not in ready_ids for identity in file_ids):
            return DocumentScope(
                status='not_found', references=list(references),
                message='The selected document is missing or not ready. Please choose a ready document.',
            )
        catalog = [f for f in files if f.file_id in file_ids]
    selected = []
    for reference in references:
        exact = [f for f in catalog if reference.casefold() == f.file_name.casefold()
                 or any(reference.casefold() == label.casefold() for label in f.labels)]
        terms = set(tokenize(reference)) - _DESCRIPTOR_WORDS
        matches = exact or [f for f in catalog if terms and terms <= set(tokenize(' '.join(f.labels)))]
        if len(matches) != 1:
            status = 'ambiguous' if matches else 'not_found'
            names = ', '.join(f.file_name for f in matches)
            message = (
                f'The document reference "{reference}" matches more than one file: {names}. '
                'Please specify the exact filename or select a file.'
                if matches else
                f'I could not find a ready document matching "{reference}". '
                'Please specify its exact filename or upload it.'
            )
            return DocumentScope(status=status, references=list(references), matches=matches, message=message)
        if matches[0] not in selected:
            selected.append(matches[0])
    selected = selected if references else catalog
    return DocumentScope(
        status='resolved', references=list(references),
        file_ids=[f.file_id for f in selected], matches=selected,
    )
