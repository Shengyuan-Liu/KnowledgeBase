"""Translate file-management HTTP requests into existing service calls."""

from fastapi import APIRouter, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from knowledgebase.storage.models import PdfSourceRecord

from knowledgebase.api.dependencies import Resources
from knowledgebase.schemas import FileInfo
from knowledgebase.services.files import InvalidUploadError, delete_file, ingest_file
from knowledgebase.storage.operations import FileRecordNotFoundError, get_file, get_files


router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("", response_model=list[FileInfo])
def list_files(resources: Resources):
    with resources.sessions() as session:
        return get_files(session)


@router.post("", response_model=FileInfo, status_code=201, responses={
    400: {"description": "Invalid TXT/Markdown/PDF upload"},
    500: {"description": "File processing failed"},
})
def upload_file(file: UploadFile, resources: Resources):
    """Wait for indexing to finish before returning the ready file record."""
    try:
        file_id = ingest_file(
            file.filename or "", file.file.read(), resources.sessions,
            resources.embeddings, resources.store,
            chunk_size=resources.settings.chunk_size, overlap=resources.settings.chunk_overlap,
            chunking_strategy=resources.settings.chunking_strategy,
            chunk_max_tokens=resources.settings.chunk_max_tokens,
            chunk_tokenizer=resources.settings.chunk_tokenizer,
            parent_max_tokens=resources.settings.parent_max_tokens,
            semantic_similarity_threshold=resources.settings.semantic_similarity_threshold,
            semantic_batch_size=resources.settings.semantic_batch_size,
            embedding_model=resources.settings.embedding_model,
            assets=resources.assets, pdf_parser=resources.pdf_parser,
        )
    except InvalidUploadError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="File processing failed. Check the file list for its status.") from error
    with resources.sessions() as session:
        return get_file(session, file_id)


@router.delete("/{file_id}", status_code=204, responses={
    404: {"description": "File not found"},
    409: {"description": "File is still processing"},
    500: {"description": "File cleanup failed; deletion can be retried"},
})
def remove_file(file_id: str, resources: Resources):
    with resources.sessions() as session:
        file = get_file(session, file_id)
        if file is None:
            raise HTTPException(status_code=404, detail="File not found.")
        if file.status == "processing":
            raise HTTPException(status_code=409, detail="The file is still processing. Wait before deleting it.")
    try:
        delete_file(file_id, resources.sessions, resources.store, assets=resources.assets)
    except FileRecordNotFoundError as error:
        raise HTTPException(status_code=404, detail="File not found.") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="File deletion failed. Retry deletion to finish cleanup.") from error
    return Response(status_code=204)


@router.get("/{file_id}/original", response_class=FileResponse)
def original_pdf(file_id: str, resources: Resources, revision: str | None = None):
    """Read a ready original by identity; historical links must match its extraction."""
    with resources.sessions() as session:
        file = get_file(session, file_id)
        pdf = session.get(PdfSourceRecord, file_id)
        if file is None or file.status != "ready" or pdf is None or resources.assets is None:
            raise HTTPException(status_code=404, detail="Original PDF is unavailable.")
        if revision is not None and revision != pdf.revision_id:
            raise HTTPException(status_code=409, detail="This original does not match the saved extraction.")
        path = resources.assets.path(file_id)
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Original PDF is unavailable.")
        return FileResponse(path, media_type="application/pdf", filename=file.file_name,
                            content_disposition_type="inline", headers={"Cache-Control": "no-store"})
