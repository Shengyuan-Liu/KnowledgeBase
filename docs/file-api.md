# File Management API

The FastAPI application exposes the existing TXT ingestion, listing, and deletion
services. This is the local, single-user file API; chat routes and streaming are
separate implementation steps.

## Start the server

Run from the repository root with `OPENAI_API_KEY` in `.env`:

```bash
uv sync --locked
make api
```

The default address is `http://127.0.0.1:8000`. Interactive API documentation is at
`http://127.0.0.1:8000/docs`, and the schema is at `/openapi.json`. Stop the server
with Ctrl+C. The equivalent startup command is:

```bash
uv run --locked uvicorn knowledgebase.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

`DATA_DIR` in `.env` defaults to `data`. The API and CLI use the same SQLite file,
Chroma directory, collection name, and embedding model. `--data-dir` still overrides
the CLI setting. Paths are relative to the process working directory. A Python
caller can override the API directory with `create_app(data_dir=Path(...))`.
Keep one server process for this local storage setup. No authentication or remote
deployment configuration is included.

## Routes

| Method and path | Success | Body |
| --- | --- | --- |
| `POST /api/files` | `201 Created` after indexing finishes | One `FileInfo` object |
| `GET /api/files` | `200 OK` | Array of `FileInfo`, newest first |
| `DELETE /api/files/{file_id}` | `204 No Content` after cleanup | Empty |

`FileInfo` contains `file_id`, `file_name`, `status`, `error_message`, and `created_at`.
The list includes processing, ready, and failed files. An empty library returns `[]`.
Only ready files participate in retrieval. Timestamps retain the existing naive UTC
storage convention. Names need not be unique; operations use file IDs.

### Upload

Send one multipart file under the field name `file`:

```bash
curl -F 'file=@notes.txt' http://127.0.0.1:8000/api/files
```

The route calls `ingest_file` and waits for the result. It returns a ready record
only after indexing completes; this initial API does not acknowledge a background
job with `202`. Other requests can observe `processing` through the file list while
the upload is running. Uploading the same filename again creates another file ID.
The service checks the `.txt` suffix, UTF-8 decoding, and nonempty text; it does not
rely on the client's MIME type. The full file is read for the existing ingestion
service, so this endpoint is intended for the MVP's small TXT materials.

Successful uploads make real embedding API calls. Listing and deletion do not
call a model. Validation failures create no file records. Processing failures
retain the service's failed record and its error details for the file list.

### List and delete

```bash
curl http://127.0.0.1:8000/api/files
curl -i -X DELETE http://127.0.0.1:8000/api/files/FILE_ID
```

Deletion uses the existing service's non-ready transition, vector cleanup, and
transactional chunk/file cleanup. A processing file returns `409` because an active
ingestion must finish before deletion. Failed cleanup returns `500`; the file stays
ineligible for retrieval and deletion can be retried with the same ID. Repeating a
successful deletion returns `404`. See [file deletion](file-deletion.md).

## Error responses

Application errors use `{"detail": "English explanation"}`. Missing multipart
input uses FastAPI's standard `422` validation details.

| Status | Situation |
| --- | --- |
| `400` | Unsupported extension, invalid UTF-8, empty or whitespace-only text |
| `404` | Requested deletion ID does not exist |
| `409` | File is still processing and cannot yet be deleted |
| `422` | Required multipart file field is missing or is not a file |
| `500` | Ingestion or deletion could not complete |

`InvalidUploadError`, a `ValueError` subclass, identifies service input failures.
This distinguishes invalid uploads from a provider's own `ValueError`, which must
remain a server failure. HTTP processing/cleanup errors use a stable explanation;
the file list retains the existing service's recorded error details.

## Structure and lifecycle

- `knowledgebase/api/app.py` creates the application. Its lifespan uses the same
  `storage.runtime.open_storage` helper as the CLI to open SQLite,
  initializes tables, opens the persistent Chroma collection, and creates the
  shared OpenAI embedding client. It closes the SDK client and disposes the SQL
  engine on shutdown. Importing the module does not initialize storage or read keys.
- `knowledgebase/api/files.py` defines the three routes and their dependency on
  shared `AppResources` from `api/dependencies.py`. All routes use the same
  session factory, embeddings, and vector store.
  Routes use synchronous handlers for the existing blocking services; each request
  owns its read sessions, while mutation transactions remain service-owned.

The [chat API](chat-api.md) shares these storage and embedding resources and adds
an LLM client. Uploads wait for indexing, the UI is integrated, and startup recovers interrupted
processing records. Recovery first marks them failed, then cleans partial vectors
and chunks. Failed cleanup remains visible and can be retried through deletion.
A process lock allows one API or CLI owner per data directory. [Streaming chat](chat-streaming.md) is available
through a separate endpoint. Do not delete a file currently being indexed
through another entry point while the API is running.

The implementation follows FastAPI's official [lifespan](https://fastapi.tiangolo.com/advanced/events/),
[file upload](https://fastapi.tiangolo.com/tutorial/request-files/), and
[lifespan testing](https://fastapi.tiangolo.com/advanced/testing-events/) guidance.

## Verification

```bash
uv run --locked python -m pytest tests/test_file_api.py
make test
```

Tests exercise HTTP multipart requests, error codes, upload/list/retrieve/delete,
same-name file isolation, observable processing state, failed-cleanup retry,
application restart, and OpenAPI contracts. They use real temporary SQLite/Chroma
stores and offline embedding doubles; no live embedding charges are incurred.
