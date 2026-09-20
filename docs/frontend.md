# Frontend Workspace

## Implemented Scope

The React/TypeScript frontend uses Vite and CSS Modules. Its Library panel calls
the real file API to list, upload, search locally, and delete TXT files. Chat and
Evidence currently show inactive placeholders; streaming chat, citations, and
conversation restoration are the next stage.

The workspace follows the [frontend design](mvp/mvp-frontend-design.md): three
panels on desktop, a library/chat layout with an Evidence drawer on tablets, and
separate Library/Evidence dialogs on phones. Native modal dialogs provide focus
containment, Escape dismissal, and focus restoration.

## Local Development

Install frontend dependencies once from the repository root:

```bash
npm --prefix frontend ci
```

Start the backend and frontend in separate terminals:

```bash
make api
```

```bash
make frontend
```

Open <http://127.0.0.1:5173>. Vite proxies `/api` to the backend at
`http://127.0.0.1:8000`. Uploads use the backend's `.env` credentials and `DATA_DIR`,
so uploaded files also appear in the CLI. No credentials belong in frontend code
or `VITE_*` variables. Real uploads make embedding API calls.

For a different local backend, set `KNOWLEDGEBASE_API_PROXY` when starting Vite.
This is a development-server setting, not a browser credential. A production
host must serve the built `frontend/dist/` assets and route `/api` to FastAPI;
production hosting is not configured by this change.

Run `make stop` before restarting to stop listeners on the development ports
8000/5173, browser-test ports 8001/5174, and Vite preview port 4173. It sends
SIGTERM and waits up to five seconds for the ports to become free. If all ports
are already free, it exits successfully. This command targets listeners by port,
including any other application using one of these ports. It does not delete data.

`make test-stop` verifies shutdown and repeated execution with temporary listeners
on dynamically assigned ports, leaving running development servers untouched.

## File Behavior

- Upload accepts one `.txt` file per request. The backend validates UTF-8 and
  nonempty content. No client-only size limit is invented.
- The upload stays pending until the backend returns the indexed file. Failed
  uploads display the server error and refresh the library to expose failed records.
- Processing records are polled every two seconds. Polling stops when no processing
  records remain or a list request fails; the user can retry a failed list request.
- Search filters filenames locally and does not change retrieval scope.
- Select a row to see its date and delete action. Processing files cannot be deleted.
- Deletion requires confirmation and removes the row only after server success.
  Failed deletion keeps the dialog and file visible with an explicit retry action.
- Re-upload opens the file picker and creates a new record, matching the existing
  backend contract. It does not replace a failed record; that record can be deleted.

## Modules

| Path under `frontend/src/` | Responsibility |
| --- | --- |
| `Workspace.tsx` | Compose the panels, stage placeholders, and responsive drawers |
| `components/LibraryPanel.tsx` | File selection, search, upload control, metadata, and deletion dialog |
| `components/Modal.tsx` | Native modal lifecycle and Escape handling |
| `hooks/useLibrary.ts` | Fetch server metadata, poll processing files, and manage mutations |
| `hooks/useMediaQuery.ts` | Track responsive breakpoints |
| `api/files.ts` | Typed file requests, multipart upload, and readable HTTP/network errors |
| `types.ts` | File response contract |
| `tokens.css` / `Workspace.module.css` | Global defaults and workspace styles |

## Verification

```bash
make test-frontend
```

This runs Vitest/React Testing Library interaction tests, TypeScript checking,
and a production build. Tests cover pending uploads, TXT validation, backend
errors, list retry, filename filtering, confirmed/retryable deletion, and polling.

For browser acceptance tests, install Chromium once:

```bash
cd frontend
npx playwright install chromium
cd ..
make test-browser
```

Playwright starts Vite on port 5174 and `tests/frontend_server.py` on port 8001.
The test server uses the production FastAPI routes, services, SQLite, and Chroma
in a temporary directory. Only provider calls are replaced with offline mocks;
no key or existing library is used. Both ports must be available.

The browser tests exercise upload, persisted reload, search, deletion, invalid
UTF-8/empty content, dialog focus, Escape, and layouts at 1440, 1024, and 390 pixels.
Screenshots are saved under ignored `frontend/test-results/` directories. These
checks establish file-management integration, not live embedding quality or chat
acceptance. See [Vite setup](https://vite.dev/guide/) and
[Vitest setup](https://vitest.dev/guide/) for the underlying development tools.
