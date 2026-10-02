# Dependency and layering audit

Inspected revision: `c87bf76` on `v2`. Comparison baseline: `bbd0a8d`, before the
OOP migration. This is a static architecture review; no application implementation
was changed and no application module, model or network provider was executed.

**The current code does not satisfy a strictly acyclic dependency requirement.**
The audit found one two-module cycle introduced by moving DocumentChunker into
the same module as the lower-level splitting algorithms.

## Scope and results

| Check | Before OOP | Current |
| --- | --- | --- |
| Python modules scanned | 62 | 64 |
| Python application package modules | 55 | 57 |
| Cycles including function-local imports | 0 | 1 |
| Cycles using eager runtime imports only | 0 | 0 |
| Upward package edges under the recorded layer policy | 1 | 0 |
| Production frontend modules | Not rerun | 19 |
| Frontend cycles including type and dynamic imports | Not rerun | 0 |
| Frontend upward layer edges | Not rerun | 0 |

The Python scope includes `knowledgebase/`, root `main.py`, and six active
top-level evaluation modules. The frontend scope includes production TS/TSX;
tests, CSS/assets, archived run scripts, installed dependencies and runtime data
are excluded. Python imports are extracted with AST and checked by strongly
connected components. The frontend uses the installed TypeScript compiler's
module-resolution trace; both the lazy PDF import and type-only hook imports are
explicitly verified as present in the graph.

Results: [Python graph](python-dependencies-2.json),
[frontend graph](frontend-dependencies.json),
[frontend resolution trace](frontend-resolution.log).

## Finding 1: a new deferred import cycle

```text
rag/chunking.py:331
  DocumentChunker.split -> semantic_chunking.split_semantic
                           |
                           v
rag/semantic_chunking.py:10
  imports _bounded_units, _pack_units, _sentence_boundaries,
  _spans_between, split_parent_child and split_structured from chunking.py
```

The first import executes inside `DocumentChunker.split`; the reverse import is
at module scope. Delaying the first import avoids an eager initialization failure
in the tested workflows, but it does not remove the source dependency cycle.
This is not merely a type annotation or a false positive from a prompt string.

At `bbd0a8d`, DocumentChunker lived in `services/files.py`. Its dependency chain
was `services.files -> rag.semantic_chunking -> rag.chunking`, with no return
edge. Moving it into `rag/chunking.py` created the loop. Functional test success
and frozen-output equality did not establish architectural acyclicity.

Minimal proposed correction, not implemented by this audit:

```text
FileService -> rag/document_chunker.py (DocumentChunker)
                 |-> rag/semantic_chunking.py
                 |       -> rag/chunking.py (pure algorithms)
                 |-> rag/chunking.py
                 |-> rag/pdf_chunking.py
                 |-> rag/pdf_evidence.py
                 `-> embedding dependency
```

Keep shared splitting helpers with the basic algorithms. Move only the configured
dispatcher to its own component module, update consumers, and remove the old
re-export path. Re-exporting DocumentChunker from `rag/chunking.py` would recreate
an indirect loop. A private-helper import can be cleaned up deliberately, but
does not require another class hierarchy or a general plugin framework.

## Finding 2: domain options share a module with environment settings

`schemas/retrieval.py:7` imports `RetrievalOptions` from `config.py`. The same
module defines defaults, `PlanningOptions` and the environment-reading `Settings`
class. Providers, storage and RAG modules also import defaults/options from it.

This is not a current import cycle: config.py has no first-party imports, and
importing it alone does not instantiate Settings or read `.env`. It nevertheless
ties low-level contracts to a module that also owns application configuration.
The package-level audit treats config as a shared foundation, so its zero upward
edge result must not be read as proof of complete architectural decoupling.

Proposed separation:

- Put pure default constants in `defaults.py`, importing no application modules.
- Put `RetrievalOptions` and `PlanningOptions` in a shared options/schema module
  that depends only on defaults and third-party data-model libraries.
- Keep environment/credential loading in `config.py`; it imports those pure types.
- Change lower layers to import pure contracts/defaults directly. Do not add a
  compatibility import from the pure modules back into runtime config.

## Finding 3: service construction still depends on Settings

`services/files.py:60` defines `FileService.from_settings`, and
`bootstrap.py:46` calls it. The method creates the parser and chunker and reads
application configuration. This is not a loop, but assembly responsibilities are
split across the bootstrap module and a business service.

Move this Settings-to-components mapping into bootstrap. FileService should
receive its configured parser, chunker, embeddings, storage and session factory.
It should not need the application Settings class to perform file operations.

## Finding 4: a route knows a storage-layer exception

`api/files.py:13` imports `FileRecordNotFoundError` from `storage/operations.py`.
The arrow still points downward, so this is not a reverse dependency. However,
the route is coupled to the storage implementation's error contract.

For a stricter service boundary, translate the storage exception into a service
exception, or define the application-facing error in a shared contract module.
The route can then translate that service/contract error into HTTP 404.
Opening storage in the API entry point's lifespan is a separate, legitimate
resource-ownership responsibility and should not be confused with route logic.

## What is already one-way

- Storage and provider modules do not import services, API, bootstrap or RAG.
- RAG modules do not import services, API or bootstrap.
- Services do not import API, bootstrap or entry points.
- Bootstrap does not import API or CLI.
- The previous `storage.runtime -> services.files` edge has been removed. Recovery
  is now invoked by bootstrap inside the caller's storage lifetime.
- Frontend components/hooks/API/types have no dependency cycle in the scanned
  graph. Type-only coupling is counted rather than hidden.

## Proposed acceptance rules

The construction boundary (entry points, runtime Settings and bootstrap) may
assemble lower-level services and adapters. Request handling follows:

```text
API / CLI / evaluation callers
            -> application services
            -> RAG components
            -> provider and storage adapters
            -> shared contracts / pure defaults
```

Each upper layer can use lower shared contracts directly. Shared contracts and
defaults must not depend on runtime settings, services, adapters or entry points.
Within RAG, a configured dispatcher may use specialized and basic algorithms;
the basic algorithms must not import the dispatcher.

After an explicitly authorized correction, add an automated architecture gate
that checks both forbidden layer edges and module cycles, including function-local
and type-only imports. Do not make the gate pass by excluding deferred imports.
Run focused chunking/ingestion regressions and the frozen contract comparison;
this structural change does not itself require paid model evaluations.

## Retained checks and limitations

- `python-import-graph.json` / `.log`: the first audit script failed serializing
  a set in its policy metadata. The original script and incomplete
  `python-dependencies.json` are retained; use `python-dependencies-2.json`.
- `python-import-graph-2.json` / `.log`: extraction completed; the strict
  acyclicity check intentionally exits nonzero because the product has one cycle.
- `frontend-import-graph.json` / `.log`: the installed TypeScript 7 package exposes
  version metadata rather than the former compiler AST API. The first inspection
  adapter failed before analyzing application files.
- `frontend-import-graph-2.json` / `.log`: the compiler CLI trace completed and
  the frontend dependency check passed.

Each command record includes code identity, duration, counts/output and all 20
metric categories marked not applicable to static architecture checks. The audit
does not measure runtime RAG quality, cost or performance, and does not inspect
third-party dependency internals. No unresolved Python dynamic-import calls were
found. Arbitrary reflection and implicit interpreter package-initialization edges
are outside the static source graph.

The architecture findings remain open; this audit does not implement their fixes
or authorize a merge into `main`.
