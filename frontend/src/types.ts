/** File metadata returned by the FastAPI file endpoints. */
export interface FileInfo {
  file_id: string;
  file_name: string;
  status: "processing" | "ready" | "failed";
  error_message: string | null;
  created_at: string;
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
}

export interface CitationCheck {
  valid_source_ids: number[];
  invalid_source_ids: number[];
  no_citations: boolean;
}

export interface CompletedAnswer {
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
  | { event: "sources"; sources: Source[] }
  | { event: "answer_delta"; delta: string }
  | ({ event: "debug" } & AnswerDebug)
  | ({ event: "complete" } & CompletedAnswer)
  | { event: "error"; message: string }
);

export interface SavedConversation {
  conversation_id: string;
  messages: {
    message_id: number;
    role: "user" | "assistant";
    content: string;
    sources: Source[] | null;
    citation_check: CitationCheck | null;
    retrieval_question: string | null;
  }[];
}

export interface ChatMessage {
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
