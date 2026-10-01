# KnowledgeBase v2 Product Design

Status: implemented v2 scope with a completed scoped functional closeout. See the
[release summary](release-summary.md) for delivered behavior, evidence and limits.
OCR, visual figures/charts and formula understanding remain deferred.

## Goal

Let a single user upload PDFs, ask questions spanning sections or documents, and
inspect the evidence behind each answer. When an initial search leaves a required
point unsupported, the application should make a limited, targeted effort to find
it and disclose any remaining gap.

## Feature 1: PDF Ingestion and Page Citations

The core accepts digitally generated English PDFs alongside existing
TXT and Markdown files. Preserve reading order, headings, paragraphs, lists, and
supported table structure. Acceptance must include representative two-column
pages and tables; perfect extraction from arbitrary PDFs is not promised.

An answer citation opens its saved evidence excerpt and lets the user navigate
to the original PDF page while that file remains available. A PDF page number is
the one-based physical position in the file. A printed label such as `iv` or `12`
may be shown separately when available; it must not silently replace that position.

PDF extraction is a transformation. Exact agreement with extracted text does not
prove agreement with the original page. The product must keep those views distinct
and retain enough location information to check extraction and quotations.

| Content type | Proposed v2 treatment |
| --- | --- |
| Digital prose, headings, lists | Core support with original page mapping |
| Multi-column prose | Core acceptance fixtures must verify correct reading order |
| Tables | Preserve headers, row/column associations, units, and relevant notes for supported layouts |
| Scanned or mixed image/text pages | OCR is deferred from v2; disclose unindexed pages/content instead of claiming complete coverage |
| Figures and charts | Visual understanding is deferred; index available captions as text without inferring visual values or relationships |
| Mathematical expressions | Formula understanding is deferred; preserve available extracted content without promising interpretation |
| Password-protected PDFs | Password entry and decryption workflows are outside the core scope |

Retain the original PDF locally to support page navigation. On deletion, remove
it and its live index/source records through the existing exclusion-first
lifecycle. Historical answers retain their saved evidence text and page metadata;
they do not retain a hidden original PDF copy. The original-page action becomes
unavailable after deletion.

## Feature 2: Decomposition and Multi-hop Retrieval

A simple fact question should use a single retrieval round. A compound question
may be split into explicit requirements, such as each document and comparison
dimension. Independent requirements can be searched without a dependency chain.

A dependent question can require another retrieval round after an earlier passage
identifies what to search for. For example: a report names a baseline method, and
another uploaded paper contains that method's assumptions. The second query is
grounded in the first passage rather than an invented intermediate answer.

Preserve the user's original question and requested file scope throughout. A
follow-up resolver already exists in v1; the new capability is decomposing the
resolved task and using retrieved findings for bounded subsequent searches.

Example: `Compare the datasets, reported results, and limitations in Paper A and
Paper B.` The answer should cover both papers and all three dimensions, including
explicit missing-information items when the supplied evidence lacks a dimension.
Different experimental conditions must not be flattened into a claim that one
method is universally better.

## Feature 3: Sufficiency Assessment and Supplementary Retrieval

After packing candidate evidence, assess each required answer point against the
actual supplied excerpts. Distinguish supported, partially supported, missing,
and conflicting evidence. An LLM assessment helps route retrieval; it is not
proof of correctness and must not be displayed as a calibrated confidence score.

When support is missing, search specifically for the missing point if budget
remains. Stop when requirements are supported, no supported next query is
available, no new evidence is found, or a configured limit is reached.

If only part of the question is answerable, return that supported portion and
identify the missing portion. If none is answerable, abstain. Absence from a few
retrieved excerpts does not establish absence from an entire document. Conflicting
sources should be attributed and qualified; the controller must not keep searching
until it finds a preferred answer.

## Preserved User Experience

Keep file management, streaming answers, Stop, continued conversations, refresh
restoration, document scope, and source inspection. Show brief progress while
retrieval is running. A progress event is not an answer token. Do not require the
user to configure retrieval algorithms in the normal question flow.

## Functional Acceptance Scenarios

| Scenario | Required result |
| --- | --- |
| Digital PDF fact question | Answer uses correct extracted evidence; citation opens the correct original page |
| Two-column page | Reading order and page association match the original page on the frozen fixture |
| Supported table question | Value, header, unit, and required note stay associated and are cited |
| Cross-page qualification | Relevant condition from another page is included with its own location |
| Multi-document comparison | Every requested document/dimension is addressed or explicitly marked unsupported |
| Dependent retrieval | Later query records the earlier evidence that identified its target |
| Missing evidence | Bounded supplementary search ends with an honest partial answer or abstention |
| Conflicting evidence | Answer preserves source-specific disagreement and qualifications |
| Scope restriction | Every retrieval round stays within the allowed files |
| Stop during planning/search/generation | Further work stops and an incomplete exchange is not saved |
| Refresh and deletion | Saved evidence remains inspectable; a deleted original PDF is not still served |
| Existing TXT/Markdown workflow | Existing source locations and behavior remain compatible |

These scenarios establish functionality. A quality improvement requires the
controlled comparisons in the [evaluation plan](v2-evaluation-plan.md).
