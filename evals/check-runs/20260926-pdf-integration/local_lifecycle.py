"""One local original-byte lifecycle diagnostic; providers are deterministic mocks."""

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from unittest.mock import Mock

from knowledgebase.rag.context import build_context
from knowledgebase.rag.retrieval import retrieve_evidence
from knowledgebase.services.chat import answer_in_conversation
from knowledgebase.services.files import ingest_file, delete_file
from knowledgebase.services.pdf import LocalPdfParser
from knowledgebase.storage.operations import get_pdf_extraction, get_conversation_detail
from knowledgebase.storage.pdf_assets import PdfAssets
from knowledgebase.storage.runtime import open_storage

OUTPUT = Path(__file__).parent / "local-1-details.json"
assert not OUTPUT.exists(), "Results are append-only."
content = Path("evals/materials/pdf-v2/apple-fy24.pdf").read_bytes()
parser = LocalPdfParser(Path("data/pdf-models"))
timings = {}
parse = parser.parse


def timed_parse(content):
    started = perf_counter()
    extraction = parse(content)
    timings["parse_with_initial_model_loading_seconds"] = perf_counter() - started
    return extraction


parser.parse = timed_parse
embeddings = Mock()
embeddings.embed_documents.side_effect = lambda texts: [[1.0, 0.0] for _ in texts]
embeddings.embed_query.return_value = [1.0, 0.0]
llm = Mock()
llm.generate.return_value = "See the selected PDF passage. [1]"
question = "What were total net sales?"
with TemporaryDirectory(prefix="kb-pdf-lifecycle-") as directory:
    data_dir = Path(directory)
    assets = PdfAssets(data_dir)
    with open_storage(data_dir) as (sessions, store):
        started = perf_counter()
        file_id = ingest_file("apple-fy24.pdf", content, sessions, embeddings, store,
                              assets=assets, pdf_parser=parser, embedding_model="offline-constant-2d")
        timings["upload_to_ready_seconds"] = perf_counter() - started
        assert assets.path(file_id).read_bytes() == content
        with sessions() as session:
            extraction = get_pdf_extraction(session, file_id)
            started = perf_counter()
            evidence = retrieve_evidence(question, session, embeddings, store, file_ids=[file_id])
            timings["retrieval_seconds"] = perf_counter() - started
        assert evidence.chunks and all(c.pdf and c.pdf.regions for c in evidence.chunks)
        answer = answer_in_conversation(question, sessions, embeddings, store, llm, file_ids=[file_id])
        snapshot = [s.model_dump(mode="json") for s in answer.sources]
        storage_bytes = sum(p.stat().st_size for p in data_dir.rglob("*") if p.is_file())
    with open_storage(data_dir) as (sessions, store):
        with sessions() as session:
            assert get_pdf_extraction(session, file_id) == extraction
            assert assets.path(file_id).read_bytes() == content
        started = perf_counter()
        delete_file(file_id, sessions, store, assets=assets)
        timings["delete_seconds"] = perf_counter() - started
        assert not assets.path(file_id).exists()
        with sessions() as session:
            history = get_conversation_detail(session, answer.conversation_id)
            retained = history.messages[-1].sources
            assert [s.model_dump(mode="json", exclude={"file_deleted"}) for s in retained] == snapshot
            assert all(s.file_deleted for s in retained)
            assert not retrieve_evidence(question, session, embeddings, store).chunks
    details = {
        "question": question, "source_sha256": sha256(content).hexdigest(),
        "parser": extraction.parser.model_dump(mode="json"), "revision_id": extraction.revision_id,
        "extraction": extraction.model_dump(mode="json"),
        "retrieval": evidence.model_dump(mode="json"), "context": build_context(evidence.chunks),
        "answer": answer.model_dump(mode="json"), "timings": timings,
        "storage_bytes_including_original_sqlite_chroma_and_wal": storage_bytes,
        "pages": extraction.page_count, "concurrency": 1, "samples": 1,
        "parse_cache": "Fresh parser; local weights; model loading included; no queue wait.",
        "checks": ["original bytes", "ready retrieval", "page provenance", "restart", "delete", "historical snapshot"],
        "providers": "Mock embeddings and mock answer; no provider requests or semantic quality claims.",
    }
    OUTPUT.write_text(json.dumps(details, indent=2) + "\n")
    print(json.dumps({"timings": timings, "storage_bytes": storage_bytes, "checks_passed": 6}))
