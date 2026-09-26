import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { EvidencePanel } from "./EvidencePanel";
import type { ChatMessage, Source } from "../types";

const source: Source = {
  source_id: 1, file_id: "pdf-1", file_name: "report.pdf", chunk_id: "pdf-1:child:0",
  text: "Revenue 42", distance: null,
  pdf: {
    revision_id: "revision-1", source_hash: "hash", page_count: 3,
    regions: [{ page_index: 1, start_offset: 10, end_offset: 20, bbox: [1, 2, 3, 4], precision: "block" }],
    supplements: [{ role: "column_header", table_id: "table-1", text: "USD millions", start_offset: 0, end_offset: 9,
      regions: [{ page_index: 0, start_offset: 0, end_offset: 9, bbox: [1, 2, 3, 4], precision: "cell" }] }],
    warnings: [{ code: "table_structure_unverified", message: "Table structure needs review.", page_indices: [1] }],
  },
};
const message: ChatMessage = { key: "m", role: "assistant", text: "42 [1]", status: "complete",
  sources: [source], citationCheck: { valid_source_ids: [1], invalid_source_ids: [], no_citations: false }, retrievalQuestion: "Revenue?" };

it("links body and separately located headers to matching original pages", () => {
  render(<EvidencePanel message={message} sourceId={1} />);
  expect(screen.getByRole("link", { name: "Open page 2" })).toHaveAttribute("href", "/api/files/pdf-1/original?revision=revision-1#page=2");
  expect(screen.getByRole("link", { name: "Open page 1" })).toHaveAttribute("href", "/api/files/pdf-1/original?revision=revision-1#page=1");
  expect(screen.getByText("USD millions")).toBeInTheDocument();
  expect(screen.getByText("Table structure needs review.")).toBeInTheDocument();
});

it("keeps historical excerpts and page labels after the original is deleted", () => {
  render(<EvidencePanel message={{ ...message, sources: [{ ...source, file_deleted: true }] }} sourceId={1} />);
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
  expect(screen.getByText("Page 2 (original unavailable)")).toBeInTheDocument();
  expect(screen.getByText("Revenue 42")).toBeInTheDocument();
  expect(screen.getByText("USD millions")).toBeInTheDocument();
});
