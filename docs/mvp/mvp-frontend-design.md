# Personal Knowledge Base MVP Frontend Design and Technical Plan

## Purpose and Reference Review

This document defines the frontend with TypeScript, React, Vite, and CSS Modules. It supplements the [MVP product design](mvp-product-design.md) and [MVP technical plan](mvp-technical-plan.md). It remains the target design; the [frontend guide](../frontend.md) records the implemented responsive shell, file management, streaming chat, evidence navigation, and restoration, including remaining presentation limits.

Two user-selected Chrome tabs were reviewed on September 6, 2026:

| Reference | What was observed | How it informs this MVP |
| --- | --- | --- |
| [Vellum preview](https://id-preview--277c5715-92dc-494e-9128-58a2ff99566d.lovable.app/) | A pale blue workspace with Library, chat, and Evidence columns; rounded surfaces; inline numbered citations; a bottom composer | Primary reference for visual hierarchy, layout, and evidence navigation |
| [Knowledge Hub in Lovable](https://lovable.dev/projects/277c5715-92dc-494e-9128-58a2ff99566d?view=codeEditor) | The same project's code editor, with a React/TypeScript file tree and separate knowledge and UI component folders | Supports organizing product components separately from reusable UI; the editor itself is not a second product screen |

Clicking citation 1 in the preview visibly moved the blue evidence highlight from the third passage to the first. This interaction was inspected; upload, generation, deletion, mobile behavior, and backend persistence were not verified. The preview's example answers and source numbering are demonstration content, not verified evidence mappings.

Use the reference's spatial design rather than its sample legal content, branding, account avatar, or supported file formats. The MVP remains a single-user TXT knowledge base. Use the working product name `Knowledge Base`; all application text is English. The dimensions and color values below are proposed implementation values, not extracted CSS measurements.

## Page Layout

Provide a single workspace at `/`, with a compact header and three panels on wide screens. Chat receives the most space. No dashboard, marketing page, authentication screen, or code editor is required.

```text
+-----------------------------------------------------------------------+
| Knowledge Base                         Answers from your documents    |
+------------------+-----------------------------+----------------------+
| Library          | Chat                        | Evidence             |
| 4 files          | Grounded in your library    | Selected answer      |
| Search files     +-----------------------------+----------------------+
|                  |              User question  | 1  campus-rules.txt  |
| TXT notes.txt    |                             | Lines 12-18          |
| Ready            | Answer with citations [1]   | Exact source excerpt |
|                  | Sources (1)                 |                      |
| TXT calendar.txt | [Expandable excerpts]       | 2  calendar.txt      |
| Processing       | [Debug details]             | Lines 40-46          |
|                  |                             | Exact source excerpt |
|                  +-----------------------------+                      |
| Upload TXT files | Ask about your documents... |                      |
|                  |                       Send  |                      |
+------------------+-----------------------------+----------------------+
```

At desktop widths, use a centered shell with a maximum width of about 1600 px, 24 px outer spacing, and 16 px panel gaps. Target a 260-300 px library, a flexible chat column of at least 480 px, and a 300-340 px evidence panel. Use CSS Grid with `minmax(0, 1fr)` for the chat column and `min-width: 0` on grid children.

The shell fills the available viewport height using `100dvh`. Panel headers and the composer remain visible while each panel's content scrolls independently. Use `min-height: 0` on the appropriate grid and flex children. Long filenames, URLs, and excerpts must wrap without expanding the page horizontally.

## Visual System

Aim for a quiet reading workspace: a subtle blue-gray background, near-white surfaces, dark readable text, and restrained blue accents. Keep elevation light. Avoid excessive blur, low-contrast body text, or decorative animation.

| Token or element | Proposed value or treatment |
| --- | --- |
| Page background | `#EEF3FA`, with an optional subtle pale-blue corner gradient |
| Main surface | `#FFFFFF` |
| Secondary surface | `#F7F9FD` |
| Main text | `#1E293B` |
| Secondary text | `#526174` |
| Divider | `#D8E1EE`; stronger outlines for inputs and interactive boundaries |
| Primary accent | `#3159CC`, with white button text |
| Selected surface | `#E8EEFF`, with a visible blue border |
| Success / warning / error | `#166534` / `#92400E` / `#B91C1C`, always paired with text |
| Panel / card / control radius | 20 px / 14 px / 10 px |
| Spacing scale | 4, 8, 12, 16, 24, and 32 px |
| Body and controls | System sans-serif, 15-16 px body text, around 1.6 line height |
| Product and panel headings | Georgia or a system serif fallback, 18-22 px |
| User message | Right-aligned, pale blue bubble, up to 85% of chat width |
| Assistant message | Left-aligned, near-white answer card with a small label and source count |
| Evidence card | Filename and location above a blockquote with a thin left rule |
| Selected evidence | Blue outline and soft background tint; no layout shift |

Define global CSS custom properties in `tokens.css` and use CSS Modules for component styling. Verify actual rendered contrast during implementation, including borders and focus indicators. Source passages use readable upright text; italic styling is optional for short excerpts only.

## Component Behavior

### Library

Show the file count, a local filename search field, the file list, and a persistent `Upload TXT files` button. Search only filters the displayed file list; it does not alter retrieval scope. Display a `TXT` badge, filename, upload date, and processing status for each item. Upload dates are metadata, not effective dates for the source content.

Use a native file input accepting `.txt`. Client checks provide immediate feedback; the backend validates format, encoding, content, and configured size limits. Do not hard-code a different limit in the frontend. Show `Uploading...` without a fabricated percentage when transfer progress is unavailable, then display the backend's `Processing`, `Ready`, or `Failed` state. Stop polling once no file requires status updates.

Failed items show a short reason and a `Re-upload` action. Selecting a file highlights its row and exposes its metadata and delete action; it does not restrict the chat to that file or repurpose the Evidence panel as a full document editor. Empty searches show `No matching files` without replacing the underlying library state.

Deletion uses a compact confirmation dialog naming the file: `Delete this file and its indexed content?`. Keep the row pending until the backend confirms cleanup. On failure, show the error and a retry action. After success, refresh file state and mark retained references to that file as `Source deleted`; historical excerpts must not become evidence for future answers.

### Chat and Composer

Use `Chat` as the default title and `Grounded in your library` as supporting text. Avoid adding a separate title-generation model call. Render the user's message immediately on submission and show a distinct pending assistant state before text arrives.

The composer supports multiple lines. Enter sends, Shift+Enter inserts a newline, and Enter during input-method composition must not submit. Disable sending whitespace-only input and prevent concurrent submissions while an answer is active. Keep the draft on request failure. If no documents are ready, explain the reason near the composer and direct the user to upload or wait for processing.

Keep the composer anchored within the chat panel. Automatically follow the stream only while the user is near the bottom; otherwise preserve their reading position and offer `Jump to latest`. An error or dropped connection leaves the partial answer visible with an `Interrupted` or `Failed` label and a deliberate `Retry` action. Do not silently resend a question.

Support ordinary answer formatting such as paragraphs, lists, emphasis, and code blocks. Treat model text as untrusted content: no raw HTML execution, no unsafe link schemes, and no citations inferred from arbitrary bracketed numbers. Use a narrowly configured Markdown renderer if rich Markdown is implemented.

### Sources and Evidence

Keep expandable `Sources` beneath every completed answer, as required by the product design. The right-hand Evidence panel is a synchronized reading view of those same source records, not a separate collection of facts. Default to the latest completed answer; clicking an older answer's citation selects that answer and its source.

Citation activation must select by `(messageId, sourceId)`, open the Evidence panel if collapsed, scroll the corresponding card into view, and visibly highlight it. Use stable identifiers rather than array positions or filename matching. Display numbers are local to an answer and may repeat across answers. Counts refer to cited passages; label them `passages` to distinguish them from unique files.

Each source shows the actual filename, exact excerpt, and a backend-provided location. For TXT, prefer line ranges computed from source offsets; otherwise show a chunk label. Do not invent page numbers or copy PDF locations from the reference. Preserve explicit academic year or semester text. Citation correctness and answer support remain backend and evaluation responsibilities.

The reference demonstrates the desired highlighting, but its sample numbered links must not be reused as citation fixtures. The MVP's fixtures must pair each claim with the correct passage and exercise repeated citation numbers across multiple answers.

### Debug Details

Place a collapsed `Debug details` disclosure beneath each answer. Show the resolved retrieval question, retrieved chunks, metric name, raw scores with their ordering meaning, and processing time. Separate all retrieved candidates from the passages actually cited. Debug data is associated with its answer and does not change when another answer streams. Do not expose credentials, private reasoning, or full internal prompts.

## Empty, Loading, and Error States

| Condition | Expected presentation |
| --- | --- |
| First visit, no files | `Upload your first TXT file` in Library; brief chat guidance; `Sources will appear here` in Evidence |
| Library ready, no conversation | `Ask a question about your documents` with the enabled composer |
| File processing | Visible status beside that file; use other ready files if available |
| Upload or processing failed | File-specific reason and recovery action; no successful-looking ready badge |
| Request pending | Assistant placeholder labeled `Searching your documents...` |
| Answer streaming | Incremental text with `Answering...`; no completed badge before the completion event |
| Insufficient evidence | Clear explanation in the answer; show only actual sources, including an empty source list when appropriate |
| Conflicting sources | Explain the differing passages and applicable contexts; keep clarification in chat |
| Stream interrupted | Preserve partial text, label the failure, and offer explicit retry |
| Library request failed | Error and retry in Library; do not present failure as an empty knowledge base |
| Source unavailable or deleted | Named unavailable state; never redirect to a different source with the same display number |

Use honest state labels. `Completed` describes request completion, not factual correctness; insufficient evidence can still be a successfully completed response.

## Responsive and Accessible Behavior

| Width | Layout |
| --- | --- |
| 1200 px and above | Library, chat, and Evidence visible together |
| 768-1199 px | Library plus chat; Evidence opens as a dismissible side drawer |
| Below 768 px | Chat fills the page; `Library` and `Evidence` buttons open separate drawers |

On small screens, citation activation opens the Evidence drawer to the selected passage. Keep the composer visible above the virtual keyboard and account for safe-area insets. Allow full-screen drawers on narrow devices; avoid compressing three columns into unreadable widths.

Use semantic navigation, main, complementary, heading, button, and form elements. Give icon controls and citation buttons explicit accessible names, such as `View source 2: calendar.txt`. Provide visible keyboard focus, adequate text contrast, and touch targets of at least 44 px for primary mobile controls. Announce status changes politely without announcing every streamed token. Do not rely on color alone.

Dialogs and modal drawers must support Escape, contain keyboard focus while open, and restore focus to their triggering control when closed. Honor reduced-motion preferences for scrolling and highlighting. Use disclosures with expanded state exposed to assistive technology.

## Frontend Technical Structure

Keep the agreed stack: TypeScript, React, Vite, CSS Modules, React state/reducers, and `fetch` with SSE. The Lovable project's generated routing, server files, and broad UI catalog are not implementation requirements. One route is sufficient for the MVP.

| Module | Responsibility |
| --- | --- |
| `WorkspacePage` / `WorkspaceLayout` | Compose panels and responsive drawers |
| `LibraryPanel` / `FileItem` / `UploadButton` | Display server file state and initiate upload, refresh, and delete operations |
| `ChatPanel` / `MessageList` / `AnswerCard` / `Composer` | Render conversation state, compose questions, and show incremental output |
| `CitationButton` / `SourceList` / `EvidencePanel` | Share source records and synchronize active evidence |
| `DebugDetails` | Render answer-specific retrieval diagnostics |
| `useLibrary` | Load files, poll processing state, and handle file-operation results |
| `useChat` with a reducer | Track messages and pending, streaming, completed, failed, or interrupted requests |
| `api/client.ts` / `api/chatStream.ts` | Centralize HTTP errors, typed payloads, and incremental SSE parsing |
| `types.ts` / `tokens.css` | Define shared data contracts and visual tokens |

Keep file state, conversation state, and presentation state distinct. `activeMessageId`, `activeSourceId`, open drawers, search text, and expanded disclosures are presentation state. Source records remain attached to their owning message. The browser does not embed documents, query Chroma, or call model providers directly.

### API and Stream Contract

The following backend endpoints are implemented. The frontend integrates file
management, streaming chat, and conversation restoration;
see the [streaming guide](../chat-streaming.md) for the current event payloads.

| Operation | Contract |
| --- | --- |
| Load library / poll state | `GET /api/files` |
| Upload one file | `POST /api/files` with multipart form data; wait for indexing and return a ready file with status 201 |
| Delete a file | `DELETE /api/files/{fileId}`; report success only after cleanup |
| Load a known conversation | `GET /api/conversations/{conversationId}` |
| Submit a question | `POST /api/chat/stream` with question, optional conversation ID, and a required client request ID; return SSE |
| Submit a question without streaming | `POST /api/chat` with question and optional conversation ID; return complete JSON |

Use the client request ID to identify temporary messages during streaming. The backend returns the existing conversation ID, or null for a new conversation, in `start`; persistent conversation and assistant message IDs arrive in `complete` after the exchange is saved. A saved conversation ID may be retained locally to restore the current conversation after refresh; the backend remains authoritative for messages and sources. If restoration fails, show retry or an explicit option to start fresh. A conversation-management sidebar is outside this MVP.

Define a discriminated union for `start`, `answer_delta`, `sources`, `debug`, `complete`, and `error` events. Every event carries `request_id`; discard events that do not belong to the active request. Bind the temporary message to its persisted message ID at completion. A source record includes source ID, file ID, chunk ID, filename, exact excerpt, and cosine distance. Keep source records available before activating any inline citation that refers to them; unresolved references remain noninteractive until validated.

`complete` provides the finalized answer and validated source mappings. Reconcile streamed text with that final result. Treat EOF without completion as interruption. Use a streaming UTF-8 decoder and buffer incomplete SSE frames, including multiple events in one network read. Cancel obsolete requests with AbortController on unmount or conversation changes, and discard late events. Surface non-SSE HTTP errors separately from errors received during a stream. Do not automatically retry the streamed POST.

Interrupted partial text remains local UI state and is not saved. A completed database commit can precede a lost completion event; reload a known conversation before a deliberate retry. Request IDs are correlation values, not idempotency keys.

## Verification and Acceptance

Use Vitest and React Testing Library for components, reducers, and stream parsing with deterministic fixtures. Add an end-to-end browser check of the actual React/FastAPI integration when implemented. Evaluate the following scenarios:

| Scenario | Acceptance requirement |
| --- | --- |
| Desktop reference fidelity | Clear three-panel hierarchy, readable central conversation, restrained blue selection, and anchored upload/composer controls |
| Upload and processing | Valid TXT reaches Ready; invalid files and failed processing provide usable feedback |
| Citation navigation | Clicking a citation in either an old or new answer selects exactly its passage and preserves message identity |
| Source association | Two answers may both contain citation 1 without sharing the wrong passage; sources under answers and in Evidence agree |
| Realistic content | Long filenames, multiline excerpts, source years, and long answers fit without horizontal page overflow |
| Stream handling | Split UTF-8, split SSE frames, combined events, stale events, HTTP errors, and early EOF produce the correct state |
| Evidence boundaries | Missing evidence and conflicting years remain explicit; no fabricated source cards or correctness percentages |
| Deletion | Successful cleanup updates Library; retained citations show unavailable state; subsequent answers exclude deleted content |
| Responsive layout | Check approximately 1440, 1024, and 390 px widths; citation drawers and the composer remain usable |
| Accessibility | Keyboard-only upload, send, source navigation, disclosures, and dialogs work with visible focus and correct focus restoration |

For documentation-only changes, review the content, verify local links, and check formatting with `git diff --check`; automated documentation tests are not required. Once the frontend exists, require TypeScript checking, frontend tests, the production build, and browser verification of the acceptance scenarios. Do not present this reference review as proof that those implementation checks have passed.
