# Source locations and retrieval-details verification

Scope: offline source-location contracts, saved retrieval diagnostics, responsive
evidence presentation, streaming completion, restoration and deletion. Provider
fixtures are deterministic; no live API calls or paid evaluation ran.

## Checks

- [Initial scoped backend checks](backend-1.json): 101 passed, 5 failed. Three
  new fixtures incorrectly included a blank separator outside the actual parent
  span; the others expected the old source/diagnostic fields. Expectations were
  corrected to the actual source ranges and new recorded fields.
- [Initial full backend checks](backend-2.json): 540 passed, 3 failed, 1 skipped.
  Repeated retrieval comparisons needed to exclude the newly measured timing
  fields, while continuing to compare all rankings and evidence.
- [Final backend checks](backend-3.json): 543 passed, 1 skipped. The optional
  live API test remains skipped; the existing dependency warning remains.
- [Frontend tests](frontend-1.json): 38 passed, including zero versus missing
  values, score separation, source-line/citation labels and restored diagnostics.
- [Production build](build-1.json): TypeScript and Vite succeeded.
- [First browser checks](browser-1.json): 9 passed.
- [Expanded browser checks](browser-2.json): 9 passed, 1 failed. The new tablet
  test incorrectly looked for the phone-only Library toggle. The test now uses
  the tablet's persistent Library panel. Its original
  [failure context](browser-2-artifacts/chat-streams-restores-sele-f27e6-s-deleted-excerpts-at-900px/error-context.md)
  and trace remain preserved.
- [Final browser checks](browser-3.json): 10 passed, including the added tablet
  workflow. Final screenshots are retained in `screenshots-3/`.

All checks retain command, code identity, duration, exit status, counts, raw logs
and the full metric inventory. Production timing, answer quality and provider
cost are not inferred from mocked requests. Build counts are not test counts.
Source-location tests cover LF, CRLF and CR, then restore the same lines and
diagnostics after source deletion. Existing historical snapshots retain null
locations rather than fabricated values.

## Visual review

Codex inspected desktop and phone screenshots in `screenshots-1/`. Evidence line
ranges, citation status, modal controls and the existing layout remain readable.
Candidate tables scroll within their region rather than widening the page.
Browser checks exercise desktop, tablet and phone layouts, completion, follow-ups,
restoration, cancellation, Markdown upload and deleted-source history.

This change does not alter ranking, evidence selection or answer prompts. Added
source lookup and timings are included in the retrieval/source-lookup duration.
Live performance impact and final v1 release quality remain unmeasured. User
acceptance and merge approval remain outstanding.
