import type { CompletedAnswer, Source } from "../types";

export const source: Source = {
  source_id: 1,
  file_id: "file-1",
  file_name: "hours.txt",
  chunk_id: "file-1:0",
  text: "The library closes at 5 PM.",
  distance: 0.12,
};
export const completed: CompletedAnswer = {
  conversation_id: "conversation-1",
  message_id: 2,
  question: "When does it close?",
  retrieval_question: "When does it close?",
  answer: "At 5 PM. [1]",
  sources: [source],
  citation_check: {
    valid_source_ids: [1],
    invalid_source_ids: [],
    no_citations: false,
  },
};
export function frame(event: string, data: object, requestId = "request-1") {
  return `event: ${event}\ndata: ${JSON.stringify({ request_id: requestId, ...data })}\n\n`;
}
export function sse(text: string) {
  return new Response(text, {
    headers: { "Content-Type": "text/event-stream" },
  });
}
