import type { SavedConversation, StreamEvent } from "../types";
import { request } from "./client";

export class StreamInterruptedError extends Error {}

export async function loadConversation(
  id: string,
  signal: AbortSignal,
): Promise<SavedConversation> {
  return (
    await request(`/conversations/${encodeURIComponent(id)}`, { signal })
  ).json();
}

/** Decode complete SSE frames, preserving UTF-8 and frame fragments between reads. */
export async function readChatStream(
  response: Response,
  requestId: string,
  onEvent: (event: StreamEvent) => void,
) {
  if (
    !response.headers.get("content-type")?.includes("text/event-stream") ||
    !response.body
  ) {
    throw new Error(
      "The server did not return an answer stream. Please try again.",
    );
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      let result: ReadableStreamReadResult<Uint8Array>;
      try {
        result = await reader.read();
      } catch {
        throw new StreamInterruptedError(
          "The connection was lost before the answer completed.",
        );
      }
      buffer += decoder.decode(result.value, { stream: !result.done });
      let separator: RegExpExecArray | null;
      while ((separator = /\r?\n\r?\n/.exec(buffer))) {
        const frame = buffer.slice(0, separator.index);
        buffer = buffer.slice(separator.index + separator[0].length);
        let eventName = "";
        const data: string[] = [];
        for (const line of frame.split(/\r?\n/)) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          if (line.startsWith("data:"))
            data.push(line.slice(5).replace(/^ /, ""));
        }
        if (!data.length) continue;
        const event = {
          ...JSON.parse(data.join("\n")),
          event: eventName,
        } as StreamEvent;
        if (event.request_id !== requestId) continue;
        if (event.event === "error") throw new Error(event.message);
        onEvent(event);
        if (event.event === "complete") return;
      }
      if (result.done)
        throw new StreamInterruptedError(
          "The stream ended before the answer completed.",
        );
    }
  } finally {
    // Cancel after a terminal event too, so an open response cannot keep reading.
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

export async function streamAnswer(
  question: string,
  conversationId: string | null,
  requestId: string,
  signal: AbortSignal,
  onEvent: (event: StreamEvent) => void,
  retrievalMode: "single" | "planned" = "single",
) {
  const response = await request("/chat/stream", {
    method: "POST",
    signal,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      request_id: requestId,
      retrieval_mode: retrievalMode,
      ...(conversationId ? { conversation_id: conversationId } : {}),
    }),
  });
  await readChatStream(response, requestId, onEvent);
}
