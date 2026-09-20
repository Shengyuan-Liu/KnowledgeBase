import { describe, expect, it, vi } from "vitest";
import { readChatStream, streamAnswer, StreamInterruptedError } from "./chat";
import { completed, frame, sse } from "../test/chatFixtures";

describe("chat SSE transport", () => {
  it("decodes one-byte UTF-8 chunks, split CRLF frames, and reconciles completion", async () => {
    const data = new TextEncoder().encode(
      (
        frame("answer_delta", { delta: "Café 📚" }) +
        frame("complete", completed)
      ).replaceAll("\n", "\r\n"),
    );
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        for (const byte of data) controller.enqueue(new Uint8Array([byte]));
        controller.close();
      },
    });
    const event = vi.fn();
    await readChatStream(
      new Response(stream, {
        headers: { "Content-Type": "text/event-stream" },
      }),
      "request-1",
      event,
    );
    expect(event.mock.calls[0][0].delta).toBe("Café 📚");
    expect(event.mock.calls[1][0]).toMatchObject({
      event: "complete",
      answer: completed.answer,
    });
  });
  it("handles multiple frames per read and ignores stale request IDs", async () => {
    const event = vi.fn();
    await readChatStream(
      sse(
        frame("complete", completed, "old") +
          frame("start", { conversation_id: null }) +
          frame("complete", completed),
      ),
      "request-1",
      event,
    );
    expect(event.mock.calls.map(([value]) => value.event)).toEqual([
      "start",
      "complete",
    ]);
  });
  it("treats EOF without completion as interruption, preserving delivered text", async () => {
    const event = vi.fn();
    await expect(
      readChatStream(
        sse(frame("answer_delta", { delta: "Partial" })),
        "request-1",
        event,
      ),
    ).rejects.toBeInstanceOf(StreamInterruptedError);
    expect(event).toHaveBeenCalledWith(
      expect.objectContaining({ delta: "Partial" }),
    );
  });
  it("surfaces SSE errors and never reports them as completion", async () => {
    const event = vi.fn();
    await expect(
      readChatStream(
        sse(frame("error", { message: "Answer processing failed." })),
        "request-1",
        event,
      ),
    ).rejects.toThrow("Answer processing failed.");
    expect(event).not.toHaveBeenCalled();
  });
  it("rejects a non-SSE success response", async () => {
    await expect(
      readChatStream(new Response("{}"), "request-1", vi.fn()),
    ).rejects.toThrow("did not return an answer stream");
  });
  it("posts the question, correlation ID, conversation, and abort signal", async () => {
    const fetch = vi.fn().mockResolvedValue(sse(frame("complete", completed)));
    vi.stubGlobal("fetch", fetch);
    const controller = new AbortController();
    await streamAnswer(
      "When?",
      "conversation-1",
      "request-1",
      controller.signal,
      vi.fn(),
    );
    const [url, options] = fetch.mock.calls[0];
    expect(url).toBe("/api/chat/stream");
    expect(JSON.parse(options.body)).toEqual({
      question: "When?",
      conversation_id: "conversation-1",
      request_id: "request-1",
    });
    expect(options.signal).toBe(controller.signal);
  });
  it("surfaces pre-stream HTTP errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ detail: "Conversation not found." }), {
            status: 404,
          }),
        ),
    );
    await expect(
      streamAnswer(
        "When?",
        "missing",
        "request-1",
        new AbortController().signal,
        vi.fn(),
      ),
    ).rejects.toThrow("Conversation not found.");
  });
});
