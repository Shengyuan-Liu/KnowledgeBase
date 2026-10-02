# Shared schema and code consolidation

Starting point: merged v2 commit `88a78af`. Changes remain on `v2`; this cleanup
has no merge authorization. No user library or environment configuration is edited.

## Shared contracts

- `knowledgebase.schemas` remains the shared import namespace. Four domain modules
  hold document/PDF, retrieval, planning/assessment, and chat contracts. Component
  modules no longer define their own Pydantic contracts.
- Candidate search and final packing share `RetrievedEvidence.chunks`. New query
  traces use version 2; the result model still accepts the historical `hits` field.
  Saved HTTP answers and extraction schemas are unchanged.
- Parent/child content, ranking provenance, source metadata, planned query fields,
  frontend rerank results and evidence references have one definition each.
- Removed the list-only `retrieve()` forwarding wrapper. Current callers use
  `retrieve_evidence().chunks`; the three chunk lookups now share one SQL join and
  snapshot conversion implementation.
- Distinct required model-output contracts remain distinct: a draft cannot choose
  file IDs, and a target binding must supply a quote while an assessment selects a
  passage ID. Making those fields optional would weaken real validation.

## Verification and retained attempts

Commands, code hashes, durations, counts, outputs and all 20 measurement fields
are in each check's JSON/log pair. These are offline checks; live answer quality,
provider billing and production performance are not exercised.

- `baseline`: 851 passed, 1 opt-in live smoke skipped.
- `schema-contracts`: all 10 before/after schema contracts preserved; the three
  provider-output schemas are exactly equal. API/PDF comparison ignores only
  descriptions and required-field ordering. Frozen input is `schema-before.json`.
- `schemas-and-storage`: retained collection failure from two tests importing
  configuration through an incidental schema-module import. Corrected the imports.
- `schemas-and-storage-2`: 823 passed, 1 skipped, 29 fixture setup errors. An unused
  import cleanup had removed pytest's indirectly registered `hop_api` fixture;
  restored it with an explicit re-export. No product failure was suppressed.
- `sufficiency-fixture-restored`: 35 passed, covering every fixture error and the
  new legacy-result round-trip regression.
- `frontend`: 49 passed. `frontend-build`: type checking and production build passed.
- Initial Ruff unused-code and Vulture (80% confidence) scans found no production
  findings. Route handlers are framework entry points, and storage accessors are
  used by tests/evaluation callers; they are not classified as dead merely because
  one production text search does not find a caller.

Existing Starlette and Docling deprecation warnings remain. Historical evaluation
artifacts are unchanged and must be replayed from their recorded code revision
when they import a removed internal module path.

## BM25 replacement and final verification

The [BM25 comparison](bm25-comparison.md) records the frozen before/after workload
and all applicable quality/performance measurements. BM25S 0.3.11 replaces the
custom scoring loop; all 25 top-20 rankings match, with maximum score roundoff
`7.11e-15`. Local mean scoring time rises from 2.976 ms to 5.150 ms on this small
corpus. This is a maintenance change, not an answer-quality or speed improvement.

- `bm25-unit`: 47 lexical/fusion/hybrid tests passed, including the valid k1=0
  boundary, common terms, no matches, deterministic ties and lifecycle changes.
- `final-backend`: 853 passed, 1 opt-in paid smoke skipped, 0 failures/errors.
- `final-browser`: all 21 controlled browser tests passed, including PDF citations,
  planned/dependent retrieval, Stop, history restoration and source deletion.
- The earlier 49 frontend tests and production build remain valid; only backend
  scoring changed after those checks. No paid model evaluation was run.

No high-confidence unreachable production implementation was identified by the
static audit. The deletions are verified redundant wrappers, duplicated fields,
duplicated SQL assembly and the replaced scoring implementation. RRF provenance,
scope resolution, bounded planning and streaming cancellation remain application
behavior; replacing them with a generic framework would not remove the need for
those rules. Markdown/PDF parsing, token counting, storage and model clients already
use their respective libraries.

Dependency synchronization briefly removed optional notebook packages; the existing
notebook group and prior `dotenv==0.9.9` installation were restored. Existing locked
package versions remain unchanged. The user library and `.env` were not edited.
