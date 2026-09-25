# Document scope verification

Offline checks use actual local storage and mocked providers. Each JSON/log pair
records command, code hashes, elapsed time, counts, failures and the complete
metric inventory. Mocked answers verify contracts, not semantic compliance.

- `scoped-1`: 73 passed, source selection and service/API regressions.
- `backend-1`: 585 passed, one intentional opt-in live-provider skip; existing
  Starlette/AnyIO deprecation warning.
- `frontend-1`: 42 passed, including saved scope display and clarification.
- `build-1`: TypeScript and production build passed.

The browser cancellation fixture was updated to inspect the current user-message
position; it previously looked at the developer message after the earlier ordering
change. This preserves the intended cancellation test rather than accepting an
answer that merely completes quickly.

- `final-backend-1`: 585 passed, 1 intentionally skipped after final formatting and
  cancellation-fixture correction.
- `browser-1`: 11 passed, 1 failed. The new clarification locator matched both the
  answer and a hidden diagnostic paragraph; raw error context/trace/screenshots
  are retained in `browser-1-artifacts/`. Product clarification worked.
- `browser-2`: both scoped browser scenarios passed after narrowing that locator
  to the answer body. The ten existing scenarios passed in `browser-1`; no product
  change was made between browser runs.
- `preflight-1`: 2 passed, 1 pre-collection skip. All frozen references resolve on
  the actual corpus, including both FAQs, the Anthropic guide and two clarifications.

The retained scope screenshot was visually reviewed: the scoped answer/source are
readable alongside both library files, without layout overlap. Browser timings use
mocked provider fixtures and are not live answer-quality or production metrics.
