"""Translate file-management HTTP requests into existing service calls."""

from fastapi import APIRouter, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse

from knowledgebase.api.dependencies import Resources
from knowledgebase.schemas import File
from knowledgebase.services.files import (
    InvalidUploadError,
    OriginalRevisionError,
    OriginalUnavailableError,
)
from knowledgebase.storage.operations import FileRecordNotFoundError

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("", response_model=list[File], response_model_exclude_unset=True)
def list_files(resources: Resources):
    return resources.files.list_files()


@router.post(
    "",
    response_model=File,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {"description": "Invalid TXT/Markdown/PDF upload"},
        500: {"description": "File processing failed"},
    },
)
def upload_file(file: UploadFile, resources: Resources):
    """Wait for indexing to finish before returning the ready file record."""
    try:
        file_id = resources.files.ingest(file.filename or "", file.file.read())
    except InvalidUploadError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500, detail="File processing failed. Check the file list for its status."
        ) from error
    return resources.files.get_file(file_id)


@router.delete(
    "/{file_id}",
    status_code=204,
    responses={
        404: {"description": "File not found"},
        409: {"description": "File is still processing"},
        500: {"description": "File cleanup failed; deletion can be retried"},
    },
)
def remove_file(file_id: str, resources: Resources):
    file = resources.files.get_file(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found.")
    if file.status == "processing":
        raise HTTPException(
            status_code=409, detail="File is still processing. Wait before deleting it."
        )
    try:
        resources.files.delete(file_id)
    except FileRecordNotFoundError as error:
        raise HTTPException(status_code=404, detail="File not found.") from error
    except Exception as error:
        raise HTTPException(
            status_code=500, detail="File deletion failed. Retry deletion to finish cleanup."
        ) from error
    return Response(status_code=204)


@router.get("/{file_id}/original", response_class=FileResponse)
def original_pdf(file_id: str, resources: Resources, revision: str | None = None):
    """Read a ready original by identity; historical links must match its extraction."""
    try:
        file, path = resources.files.get_original(file_id, revision)
    except OriginalUnavailableError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except OriginalRevisionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=file.file_name,
        content_disposition_type="inline",
        headers={"Cache-Control": "no-store"},
    )
