# Frontend Workspace

## Implemented Scope

The React/TypeScript frontend uses Vite and CSS Modules. Its Library panel calls
the real file API to list, upload, search locally, and delete TXT files. Chat streams
answers from the backend, links validated citations to original excerpts, supports
cancellation, and restores the current saved conversation after a page refresh.

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
or `VITE_*` variables. Real uploads make embedding API calls; questions use the
backend's retrieval, follow-up resolution, and answer generation providers.

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

## Chat, Evidence, and Recovery

- Enter sends a nonblank question; Shift+Enter inserts a newline. Input-method
  composition does not send. Only one request can run at a time, and the composer
  requires at least one ready document and a successfully loaded library.
- The stream parser buffers fragmented SSE frames and decodes UTF-8 incrementally.
  Events must match the active request ID. Completion replaces incremental text
  with the final answer and saved identity; EOF without completion is interrupted.
- Stop aborts the HTTP request and retains the partial answer and draft locally.
  Failed/interrupted responses have explicit labels and an explicit retry action.
  Unmounting or starting a new chat aborts obsolete work and ignores late events.
- Before retrying an interrupted/failed turn in a known conversation, the client
  reloads its saved history. If a newer turn was already committed, it displays that
  history instead of sending again. A new conversation with a lost completion event
  still has no ID recovery endpoint. The UI explains that limit.
- Only the current conversation ID is stored in browser local storage, under
  `knowledgebase.conversationId`. Restoration reads authoritative messages and
  evidence from the backend. Failed restoration offers retry or an explicit fresh
  start. New chat clears the local selection, not the old saved backend conversation.
- Sources belong to each answer. Citation buttons require a source record and the
  backend's completed citation check. Repeated numbers in different answers do not
  share source selection. Clicking a source opens Evidence on narrow screens.
- All retrieved passages appear under Sources; the list can include passages the
  model did not cite. Empty evidence and missing legacy snapshots remain distinct.
  Deleted source files keep their original excerpts with a deletion label, both
  immediately after deletion and after restoration.
- Debug details show the retrieval question, chunk distances, and citation-number
  diagnostics. Stream timing is displayed when received and is not reconstructed
  for restored history. Distances and citation checks are not correctness scores.
- New content follows the scroll only near the bottom. Reading older content keeps
  the current position and exposes Jump to latest.

Answers currently preserve plain text and line breaks with inline citation
controls. Rich Markdown rendering and TXT line-range labels remain presentation
enhancements; source locations use the recorded chunk IDs. No model HTML executes.

## Modules

| Path under `frontend/src/` | Responsibility |
| --- | --- |
| `Workspace.tsx` | Compose panels and drawers, associate evidence with answers, and mark deleted sources |
| `components/LibraryPanel.tsx` | File selection, search, upload control, metadata, and deletion dialog |
| `components/Modal.tsx` | Native modal lifecycle and Escape handling |
| `components/ChatPanel.tsx` | Composer, messages, source disclosures, debug details, and scroll behavior |
| `components/AnswerText.tsx` | Render text safely and activate validated citation numbers |
| `components/EvidencePanel.tsx` | Display and highlight original passages for the selected answer |
| `hooks/useLibrary.ts` | Fetch server metadata, poll processing files, and manage mutations |
| `hooks/useChat.ts` / `hooks/chatState.ts` | Request lifecycle, cancellation, retry reconciliation, restoration, and message state |
| `hooks/useMediaQuery.ts` | Track responsive breakpoints |
| `api/client.ts` | Same-origin requests and readable HTTP/network errors |
| `api/files.ts` / `api/chat.ts` | File operations, saved conversations, and incremental SSE decoding |
| `types.ts` | File, conversation, source, and discriminated stream event contracts |
| `tokens.css` / `Workspace.module.css` / `Chat.module.css` | Global defaults, workspace, and conversation styles |

## Verification

```bash
make test-frontend
```

This runs Vitest/React Testing Library interaction tests, TypeScript checking,
and a production build. Tests cover pending uploads, TXT validation, backend
errors, list retry, filename filtering, confirmed/retryable deletion, and polling.
Chat tests cover UTF-8/frame boundaries, stale events, HTTP/SSE errors, incomplete
EOF, cancellation, recovery before retry, repeated citation numbers, and safe text.

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
Chat browser tests additionally exercise incremental output, cancellation without
partial persistence, completed-history restoration, citation selection on desktop
and mobile, deleted-file excerpts, and missing-conversation recovery. Screenshots
are saved under ignored `frontend/test-results/` directories. These checks establish
local integration, not live model quality or production deployment. See [Vite setup](https://vite.dev/guide/) and
[Vitest setup](https://vitest.dev/guide/) for the underlying development tools.
