import { render, screen, within } from "@testing-library/react";
import { expect, it } from "vitest";
import { RetrievalDetails } from "./RetrievalDetails";
import { EvidencePanel } from "./EvidencePanel";
import { chatReducer, initialChat, savedMessages } from "../hooks/chatState";
import { completed, source } from "../test/chatFixtures";
import type { RetrievalDiagnostics } from "../types";

const match = { chunk_id: "child-a", rank: 1, rrf_score: 0.02,
  bm25_rank: 1, bm25_score: 0, vector_rank: null, vector_distance: null };
const details: RetrievalDiagnostics = {
  options: { strategy: "hybrid", packing_strategy: "parent_then_child", rerank_enabled: true },
  top_k: 5, max_tokens: 100, evidence_tokens: 80, tokenizer: "cl100k_base",
  retrieval_seconds: 1, embedding_seconds: 0, packing_seconds: 0,
  fused_matches: [match], candidates: [{ chunk_id: "child-a", parent_id: "parent-a" }],
  excluded: [{ chunk_id: "child-b", token_count: 40, reason: "context_budget" }],
  unexpanded_parents: [{ chunk_id: "parent-b", token_count: 90 }],
  rerank: { model: "test-model", model_revision: "rev-1", device: "cpu",
    matches: [{ ...match, rerank_rank: 1, rerank_score: -0.25, score_kind: "logit" }] },
};

it("shows separate scores, zero values, missing timings, and budget exclusions", () => {
  render(<RetrievalDetails data={details} />);
  const table = screen.getByRole("table");
  expect(within(table).getByText("1 / 0.0000")).toBeInTheDocument();
  expect(within(table).getByText("No hit / Not recorded")).toBeInTheDocument();
  expect(within(table).getByText("1 / -0.2500 (logit)")).toBeInTheDocument();
  expect(screen.getByText(/Query embedding: 0.000 s/)).toBeInTheDocument();
  expect(screen.getByText(/Reranking: Not recorded/)).toBeInTheDocument();
  expect(screen.getByText(/child-a → parent-a/)).toBeInTheDocument();
  expect(screen.getByText(/child-b · 40 source-text tokens/)).toBeInTheDocument();
  expect(screen.queryByText(/Attempted full context:/)).not.toBeInTheDocument();
});

it("shows recorded full packing attempts separately from source-text token counts", () => {
  render(<RetrievalDetails data={{ ...details,
    excluded: [{ ...details.excluded[0], trial_context_tokens: 110 }],
    unexpanded_parents: [{ ...details.unexpanded_parents![0], trial_context_tokens: 200 }],
  }} />);
  expect(screen.getByText(/child-b · 40 source-text tokens/))
    .toHaveTextContent("Attempted full context: 110 / 100 tokens");
  expect(screen.getByText(/parent-b · Attempted full context: 200 \/ 100 tokens/)).toBeInTheDocument();
});

it("preserves completed diagnostics through streaming reconciliation and history restoration", () => {
  const state = chatReducer(initialChat(), { type: "begin", id: "request", question: "Q?", messages: [] });
  const next = chatReducer(state, { type: "event", event: { event: "complete", request_id: "request", ...completed, retrieval: details } });
  expect(next.messages[1].retrieval).toEqual(details);
  const history = savedMessages({ conversation_id: "one", messages: [{ message_id: 2, role: "assistant",
    content: completed.answer, sources: [source], citation_check: completed.citation_check,
    retrieval_question: "Q?", retrieval: details }] });
  expect(history[0].retrieval).toEqual(details);
});

it("labels line ranges and distinguishes citations from additional supplied evidence", () => {
  render(<EvidencePanel sourceId={1} message={{ key: "answer", role: "assistant", status: "complete",
    text: completed.answer, sources: [{ ...source, start_line: 3, end_line: 8 }, { ...source, source_id: 2 }],
    retrievalQuestion: "Q?", citationCheck: completed.citation_check }} />);
  expect(screen.getByText("Lines 3–8 · Cited in this answer")).toBeInTheDocument();
  expect(screen.getByText("Source location: Not recorded · Additional supplied evidence")).toBeInTheDocument();
});

it("does not invent diagnostics for historical answers", () => {
  render(<RetrievalDetails />);
  expect(screen.getByText("Retrieval diagnostics: Not recorded.")).toBeInTheDocument();
});

it.each(["child", "parent"] as const)("identifies the recorded %s scoring unit", (unit) => {
  render(<RetrievalDetails data={{ ...details, options: { ...details.options!, rerank_unit: unit } }} />);
  expect(screen.getByText(new RegExp(`Scoring unit: ${unit}`))).toBeInTheDocument();
});

it("shows saved document scope separately from retrieved evidence", () => {
  render(<RetrievalDetails data={{ ...details, scope_seconds: 0,
    document_scope: { status: "resolved", references: ["general FAQ"], file_ids: ["general"],
      matches: [{ file_id: "general", file_name: "general-faq.txt", labels: ["General FAQ"] }], message: null } }} />);
  const scope = screen.getByLabelText("Document scope");
  expect(within(scope).getByText("Searched documents: general-faq.txt")).toBeInTheDocument();
  expect(within(scope).getByText("Document selection: 0.000 s.")).toBeInTheDocument();
});

it("shows clarification without claiming that matching documents were searched", () => {
  render(<RetrievalDetails data={{ ...details,
    document_scope: { status: "ambiguous", references: ["FAQ"], file_ids: [],
      matches: [], message: "Please specify the exact filename." } }} />);
  expect(screen.getByLabelText("Document scope")).toHaveTextContent("Please specify the exact filename.");
  expect(screen.queryByText(/Searched documents:/)).not.toBeInTheDocument();
});
