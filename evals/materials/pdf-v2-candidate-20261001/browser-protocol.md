# PDF citation and saved-history browser protocol

Prepared against the current EvidencePanel and PDF viewer. This document records
planned checks, not browser results. Use the isolated library from the matching
six-request acceptance, its actual saved answers and original uploaded PDFs.
Do not substitute mocked answers or corrected source snapshots. Do not regenerate
answers simply to make a UI case available; report missing prerequisites.

Use a visible browser at 1440-pixel desktop width and 390-pixel mobile width.
Record browser/version, viewport, server/product identity, console/network errors,
timestamps, screenshots and the actual observations. View screenshots as well as
accessible text. A successful original-PDF HTTP request alone is not a rendering
pass. Keep UI interaction timings separate from answer latency.

| Check | Action | Required observation |
| --- | --- | --- |
| B1: Select cited evidence | Open the saved lecture answer; activate its inline citation | Correct filename and original excerpt are shown; source ID matches the saved answer, including after refresh |
| B2: Physical page | Select the lecture source's `Open page 35` link | Viewer shows Page 35 of 51; canvas is visibly rendered and contains the upper Overfitting slide, printed Slide 69. It must not attempt PDF page 69 |
| B3: Navigation | Move from page 35 to 36 and back; close and reopen page 35 | Page indicator and visible page content change together; reopening returns to the cited physical page; controls remain usable at both widths |
| B4: Cross-document sources | Open the full-hop answer and its bridge/detail citations | RAG and DPR are distinct source files; their cited original pages show the initialization relationship and training details. Inspect actual source pages, accepting valid annotated alternatives |
| B5: Financial context | Open each cited operating-income source | Quarter/full-year and GAAP/Non-GAAP groups can be checked in the original: summary pages 1/2, GAAP page 4, or continued table pages 7/8. If page 8 is cited, navigate to page 7 to inspect its period/unit headings |
| B6: History reload | Save conversation IDs, refresh, select another conversation, then reopen lecture and full-hop histories | Answer text, citation IDs, source text/physical pages, dependency target and quote, and final retrieval record match saved API snapshots. Reading history must not make another planning/embedding/generation request |

For B4/B6, a missing dependent trace must remain visible and cannot be called
successful dependency display. The corresponding answer/source UI can still be
reviewed with its own result. Record unavailable/not-exercised checks separately
from passed checks; do not infer success from API-only validation.

Before/after history reads, compare provider observation counts to establish no
new calls; retain corresponding network evidence. Independently compare original
PDF bytes and revision IDs to the frozen manifest, and check downloaded bytes if
the download control is exercised. Use only the isolated evaluation data directory.

This protocol does not delete files, evaluate cancellation, upload performance,
TXT/Markdown regressions or broad accessibility. Those remain separate release
checks. All new screenshots and observations go in the matching acceptance run;
reference renders in preparation are not browser screenshots or evidence of UI
execution. Browser acceptance requires B1-B6 at both widths, with any unavailable
prerequisite or observed defect explicitly reported rather than silently passed.
