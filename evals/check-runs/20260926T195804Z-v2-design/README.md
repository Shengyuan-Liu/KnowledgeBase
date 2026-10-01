# v2 Design Documentation Review

## Scope

Documentation-only change based on `5f38974f38616f389d051108b85937b42172d2a9`,
prepared on the existing `v1` branch. Adds the six-document
[v2 design set](../../../docs/v2/README.md) and updates the documentation index.
No application implementation, dependency, runtime configuration, or branch merge
is included. No backend/frontend test suite or paid evaluation is required.

## Content Review

Reviewer: Codex, model-assisted documentation review on 2026-09-26, not independent
human review. Reviewed the complete design against the user-confirmed feature
areas, current v1 release/configuration, source contracts, and measurement policy.

| Review area | Result |
| --- | --- |
| Confirmed scope | All three agreed feature areas appear consistently across the six documents |
| Proposal versus delivery | Every document identifies planned work; no v2 implementation or measured improvement is claimed |
| PDF boundaries | Digital PDFs are the proposed core; OCR, figures/formulas, and the user's document population remain explicit decisions |
| Source fidelity and lifecycle | Extracted offsets are distinct from original page positions; original assets are deleted while historical excerpts remain |
| Advanced retrieval | Decomposition, dependent retrieval, and missing-evidence search share finite limits and fixed scope; final assessments use packed evidence |
| Existing behavior | v1 follow-up resolution, hybrid retrieval, parent-child indexing, and optional experiments are treated as existing capabilities |
| Evaluation | Complete metric inventory, stable original-page/fact annotations, controlled comparisons, reviewer identity, and gaps are specified |
| Ownership and workflow | Python implementation is not authorized by the document request; v2 implementation branch remains unselected; no merge is performed |

## Verification Commands and Artifacts

Run from the repository root:

```bash
node evals/check-runs/20260926T195804Z-v2-design/review.mjs
```

The retained script checks local Markdown destinations and heading fragments,
balanced fences, heading spacing, English-only project text, table column counts,
and whitespace errors. Its first execution writes `review-1.json` and
`review-1.log`; retries create new numbered artifacts instead of replacing prior
attempts. Each record contains timestamps, duration, command, base commit, reviewed
file hashes, counts, failures, and all policy metric applicability entries.
Counts are documentation checks, not runtime test results. Final results are in
the corresponding numbered artifacts.

The three external primary references were opened successfully with the web tool
on 2026-09-26. They support technique descriptions, not measured project gains:

- [Docling document model](https://docling-project.github.io/docling/concepts/docling_document/): structure, reading order, and available provenance.
- [IRCoT](https://arxiv.org/abs/2212.10509): dependent retrieval background.
- [CRAG](https://arxiv.org/abs/2401.15884): retrieval assessment background; its web-search scope is not adopted.

Mermaid diagrams received source-level flow review; graphical rendering was not
performed. Runtime quality, performance, cost, retrieval, and lifecycle metrics
are `not_applicable` because this change exercises no runtime behavior. This
record establishes documentation verification only.
