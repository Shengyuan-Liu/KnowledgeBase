# KnowledgeBase v1 System Design

Status: planned architecture. These diagrams describe the target v1 pipeline,
not implemented components or measured results. The existing
[MVP system map](../mvp/mvp-system-design.md) remains the implementation reference.

## Ingestion

```mermaid
flowchart TD
    Upload["TXT or Markdown upload"] --> Validate["Validate and create processing file"]
    Validate --> Source["Canonical decoded source and structural spans"]
    Source --> Parents["Bounded parent regions"]
    Parents --> Strategy{"Child chunking strategy"}
    Strategy --> Structural["Structure and sentence boundaries: default"]
    Strategy --> Semantic["Embedding-based boundaries: experiment"]
    Structural --> Children["Children with parent IDs and source offsets"]
    Semantic --> Children
    Children --> SQLite["SQLite: source, parents, children, metadata"]
    SQLite --> BM25["BM25 index of child search text"]
    SQLite --> Embed["Child embeddings"]
    Embed --> Chroma["Chroma: child vectors and file IDs"]
    BM25 --> Ready["Mark Ready after both indexes are usable"]
    Chroma --> Ready
```

Canonical source text and exact spans live in SQLite. Derived index text and
embeddings aid search without replacing evidence. Parsing and chunking are backend
modules, not separate deployed services. Ingestion failure keeps the file ineligible
and triggers cleanup of both indexes and partial chunk records.

## Retrieval and Answering

```mermaid
flowchart TD
    Question["Original question"] --> Resolve["Resolve follow-up references"]
    History["Recent history: reference context only"] --> Resolve
    Resolve --> Query["Retrieval question"]
    Eligible["Ready file IDs from SQLite"] --> Lexical["BM25 child candidates"]
    Eligible --> Vector["Vector child candidates"]
    Query --> Lexical
    Query --> Vector
    Lexical --> RRF["RRF fusion by child ID"]
    Vector --> RRF
    RRF --> Rerank["Rerank fused children against retrieval question"]
    Query --> Rerank
    Rerank --> Select["Select children and load parents"]
    Select --> Pack["Deduplicate parents and apply evidence budget"]
    Pack --> Evidence["Numbered exact parent excerpts"]
    Evidence --> Generate["Grounded answer generation"]
    Question --> Generate
    Generate --> Stream["Stream answer to React workspace"]
    Generate --> Save["Check citation IDs and save completed exchange"]
    Evidence --> Save
    Save --> Complete["Emit completion with saved identities"]
```

If no evidence survives selection, return the existing insufficient-evidence result
without answer generation. Stream cancellation and interruptions keep partial text
out of persisted conversation history. A committed answer can survive a lost
completion event, as in the MVP.

## Boundaries and Ownership

| Component | Owns |
| --- | --- |
| React workspace | Uploads, chat state, stream handling, evidence navigation, optional diagnostics |
| FastAPI and services | Request translation, file lifecycle, query orchestration, completed-answer persistence |
| RAG steps | Chunk boundaries, lexical/vector candidate coordination, RRF, parent selection, context packing |
| Provider adapters | Embeddings, relevance reranking, generation, and follow-up resolution |
| SQLite | Canonical source, parent/child relations, eligibility, conversations, evidence snapshots |
| Search indexes | Lexical postings/statistics and child embeddings derived from canonical records |
| Evaluation runner | Isolated indexes, labeled configurations, stage traces, saved outputs, comparisons |

Model placement depends on the selected provider; a reranker need not be remote.
Credentials remain on the backend. Deletion excludes a file first, then removes
both indexes and canonical records while retaining saved answer snapshots.

For record contracts and implementation sequence, see the
[technical plan](v1-technical-plan.md). For quality claims and release evidence,
see the [evaluation plan](v1-evaluation-plan.md).
