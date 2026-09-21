"""Translate file-management HTTP requests into existing service calls."""

from fastapi import APIRouter, HTTPException, Response, UploadFile

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
    400: {"description": "Invalid TXT upload"},
    500: {"description": "File processing failed"},
})
def upload_file(file: UploadFile, resources: Resources):
    """Wait for indexing to finish before returning the ready file record."""
    try:
        file_id = ingest_file(
            file.filename or "", file.file.read(), resources.sessions,
            resources.embeddings, resources.store,
            chunk_size=resources.settings.chunk_size, overlap=resources.settings.chunk_overlap,
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
        delete_file(file_id, resources.sessions, resources.store)
    except FileRecordNotFoundError as error:
        raise HTTPException(status_code=404, detail="File not found.") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="File deletion failed. Retry deletion to finish cleanup.") from error
    return Response(status_code=204)
