export interface PdfRegion {
  page_index: number;
  start_offset: number;
  end_offset: number;
  bbox: [number, number, number, number];
  precision: "block" | "cell" | "table";
}

export interface PdfWarning { code: string; message: string; page_indices: number[]; }
export interface PdfEvidence {
  revision_id: string;
  source_hash: string;
  page_count: number;
  regions: PdfRegion[];
  warnings: PdfWarning[];
  supplements: { role: string; table_id: string; text: string; start_offset: number; end_offset: number; regions: PdfRegion[] }[];
}

/** File metadata returned by the FastAPI file endpoints. */
export interface FileInfo {
  file_id: string;
  file_name: string;
  status: "processing" | "ready" | "failed";
  error_message: string | null;
  created_at: string;
  page_count?: number | null;
  extraction_warnings?: PdfWarning[];
}

export interface FusedMatch {
  chunk_id: string;
  rrf_score: number;
  rank: number;
  bm25_score: number | null;
  bm25_rank: number | null;
  vector_distance: number | null;
  vector_rank: number | null;
}

export interface Source {
  pdf?: PdfEvidence | null;
  document_labels?: string[];
  source_id: number;
  file_id: string;
  file_name: string;
  chunk_id: string;
  text: string;
  distance: number | null;
  fusion?: FusedMatch | null;
  rerank?: (FusedMatch & { rerank_score: number; rerank_rank: number; score_kind?: string }) | null;
  file_deleted?: boolean;
  parent_id?: string | null;
  matched_child_ids?: string[];
  heading_path?: string[];
  start_offset?: number | null;
  end_offset?: number | null;
  start_line?: number | null;
  end_line?: number | null;
}

export interface RetrievalDiagnostics {
  planning?: {
    version: number;
    message: string | null;
    planner: { route: string; model: string; seconds: number } | null;
    trace: {
      plan: { route: string; requirements: { requirement_id: string; description: string }[] };
      runs: { query_ids: string[]; text: string }[];
      requirements: { requirement_id: string; supplied_ids: string[]; budget_excluded_ids: string[] }[];
      stop_reason: string;
    } | null;
  } | null;
  document_scope?: {
    status: "resolved" | "ambiguous" | "not_found";
    references: string[];
    file_ids: string[];
    matches: { file_id: string; file_name: string; labels: string[] }[];
    message: string | null;
  } | null;
  scope_seconds?: number | null;
  options?: { strategy: string; packing_strategy?: string | null; rerank_enabled: boolean; rerank_unit?: "child" | "parent" } | null;
  top_k?: number | null;
  evidence_tokens: number;
  max_tokens: number;
  tokenizer: string;
  retrieval_seconds?: number | null;
  embedding_seconds?: number | null;
  rerank_seconds?: number | null;
  packing_seconds?: number | null;
  fused_matches: FusedMatch[];
  candidates: { chunk_id: string; parent_id?: string | null }[];
  excluded: { chunk_id: string; token_count: number; reason: string }[];
  unexpanded_parents?: { chunk_id: string; token_count: number }[];
  rerank?: {
    model: string;
    model_revision?: string | null;
    device?: string | null;
    matches: (FusedMatch & { rerank_score: number; rerank_rank: number; score_kind?: string })[];
  } | null;
}

export interface CitationCheck {
  valid_source_ids: number[];
  invalid_source_ids: number[];
  no_citations: boolean;
}

export interface CompletedAnswer {
  retrieval?: RetrievalDiagnostics | null;
  conversation_id: string;
  message_id: number;
  question: string;
  retrieval_question: string;
  answer: string;
  sources: Source[];
  citation_check: CitationCheck;
}

export interface AnswerDebug {
  retrieval_question: string;
  distance_metric: string;
  elapsed_seconds: number;
}

export type StreamEvent = { request_id: string } & (
  | { event: "start"; conversation_id: string | null }
  | { event: "progress"; stage: "planning" | "retrieving"; message: string }
  | { event: "sources"; sources: Source[]; retrieval?: RetrievalDiagnostics }
  | { event: "answer_delta"; delta: string }
  | ({ event: "debug" } & AnswerDebug)
  | ({ event: "complete" } & CompletedAnswer)
  | { event: "error"; message: string }
);

export interface SavedConversation {
  conversation_id: string;
  messages: {
    retrieval?: RetrievalDiagnostics | null;
    message_id: number;
    role: "user" | "assistant";
    content: string;
    sources: Source[] | null;
    citation_check: CitationCheck | null;
    retrieval_question: string | null;
  }[];
}

export interface ChatMessage {
  progress?: string;
  retrieval?: RetrievalDiagnostics | null;
  key: string;
  messageId?: number;
  role: "user" | "assistant";
  text: string;
  status: "pending" | "streaming" | "complete" | "failed" | "interrupted";
  sources: Source[] | null;
  citationCheck: CitationCheck | null;
  retrievalQuestion: string | null;
  debug?: AnswerDebug;
  question?: string;
  error?: string;
}
