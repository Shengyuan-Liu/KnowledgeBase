import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useChat, CONVERSATION_KEY } from "./useChat";
import {
  loadConversation,
  streamAnswer,
  StreamInterruptedError,
} from "../api/chat";
import { completed } from "../test/chatFixtures";

vi.mock("../api/chat", () => ({
  loadConversation: vi.fn(),
  streamAnswer: vi.fn(),
  StreamInterruptedError: class extends Error {},
}));
const saved = {
  conversation_id: "conversation-1",
  messages: [
    {
      message_id: 1,
      role: "user" as const,
      content: completed.question,
      sources: null,
      citation_check: null,
      retrieval_question: null,
    },
    {
      message_id: 2,
      role: "assistant" as const,
      content: completed.answer,
      sources: completed.sources,
      citation_check: completed.citation_check,
      retrieval_question: completed.retrieval_question,
    },
  ],
};

beforeEach(() => {
  vi.mocked(loadConversation).mockReset();
  vi.mocked(streamAnswer).mockReset();
});

describe("chat state and recovery", () => {
  it("reconciles partial text with complete, saves only the ID, and clears the draft", async () => {
    vi.mocked(streamAnswer).mockImplementation(
      async (_q, _c, id, _signal, event) => {
        event({ event: "answer_delta", request_id: "stale", delta: "Wrong" });
        event({ event: "answer_delta", request_id: id, delta: "Temporary" });
        event({ event: "complete", request_id: id, ...completed });
      },
    );
    const { result } = renderHook(useChat);
    await act(async () => {
      await result.current.send("When?");
    });
    expect(result.current.messages.at(-1)).toMatchObject({
      text: completed.answer,
      status: "complete",
      messageId: 2,
    });
    expect(result.current.draft).toBe("");
    expect(localStorage.getItem(CONVERSATION_KEY)).toBe("conversation-1");
    expect(localStorage.length).toBe(1);
  });
  it("restores a saved conversation and preserves missing legacy evidence", async () => {
    localStorage.setItem(CONVERSATION_KEY, "conversation-1");
    vi.mocked(loadConversation).mockResolvedValue({
      ...saved,
      messages: [{ ...saved.messages[1], sources: null, citation_check: null }],
    });
    const { result } = renderHook(useChat);
    await waitFor(() => expect(result.current.restoring).toBe(false));
    expect(result.current.messages[0]).toMatchObject({
      text: completed.answer,
      sources: null,
    });
    expect(streamAnswer).not.toHaveBeenCalled();
  });
  it("requires an explicit action after restoration fails", async () => {
    localStorage.setItem(CONVERSATION_KEY, "missing");
    vi.mocked(loadConversation).mockRejectedValue(
      new Error("Conversation not found."),
    );
    const { result } = renderHook(useChat);
    await waitFor(() =>
      expect(result.current.restoreError).toBe("Conversation not found."),
    );
    await act(async () => {
      await result.current.send("Hello");
    });
    expect(streamAnswer).not.toHaveBeenCalled();
    act(() => result.current.reset());
    expect(result.current.restoreError).toBe("");
    expect(localStorage.getItem(CONVERSATION_KEY)).toBeNull();
  });
  it("stops generation, retains partial text and draft, and ignores late completion", async () => {
    let deliver!: Parameters<typeof streamAnswer>[4];
    let signal!: AbortSignal;
    let finish!: () => void;
    vi.mocked(streamAnswer).mockImplementation(
      async (_q, _c, id, abort, event) => {
        deliver = event;
        signal = abort;
        event({ event: "answer_delta", request_id: id, delta: "Partial" });
        await new Promise<void>((resolve) => {
          finish = resolve;
        });
        event({ event: "complete", request_id: id, ...completed });
      },
    );
    const { result } = renderHook(useChat);
    let task!: Promise<void>;
    act(() => {
      task = result.current.send("When?");
    });
    act(() => result.current.stop());
    expect(signal.aborted).toBe(true);
    expect(result.current.messages.at(-1)).toMatchObject({
      text: "Partial",
      status: "interrupted",
    });
    expect(result.current.draft).toBe("When?");
    await act(async () => {
      finish();
      await task;
    });
    expect(deliver).toBeDefined();
    expect(localStorage.getItem(CONVERSATION_KEY)).toBeNull();
    expect(result.current.messages.at(-1)?.status).toBe("interrupted");
  });
  it("checks a known conversation before retrying and recovers a lost completion without reposting", async () => {
    localStorage.setItem(CONVERSATION_KEY, "conversation-1");
    vi.mocked(loadConversation).mockResolvedValue(saved);
    vi.mocked(streamAnswer).mockRejectedValue(
      new StreamInterruptedError("Lost completion"),
    );
    const { result } = renderHook(useChat);
    await waitFor(() => expect(result.current.restoring).toBe(false));
    await act(async () => {
      await result.current.send("Next?");
    });
    vi.mocked(loadConversation).mockResolvedValue({
      ...saved,
      messages: [
        ...saved.messages,
        { ...saved.messages[0], message_id: 3 },
        { ...saved.messages[1], message_id: 4, content: "Saved second answer" },
      ],
    });
    await act(async () => {
      await result.current.send("Next?");
    });
    expect(streamAnswer).toHaveBeenCalledTimes(1);
    expect(result.current.messages.at(-1)?.text).toBe("Saved second answer");
    expect(result.current.notice).toContain("Recovered");
  });
  it("retries explicitly after checking that no new turn was saved", async () => {
    localStorage.setItem(CONVERSATION_KEY, "conversation-1");
    vi.mocked(loadConversation).mockResolvedValue(saved);
    vi.mocked(streamAnswer).mockRejectedValueOnce(
      new StreamInterruptedError("Lost connection"),
    );
    const { result } = renderHook(useChat);
    await waitFor(() => expect(result.current.restoring).toBe(false));
    await act(async () => {
      await result.current.send("Next?");
    });
    vi.mocked(streamAnswer).mockImplementationOnce(
      async (_q, _c, id, _signal, event) => {
        event({
          event: "complete",
          request_id: id,
          ...completed,
          message_id: 4,
        });
      },
    );
    await act(async () => {
      await result.current.send("Next?");
    });
    expect(loadConversation).toHaveBeenCalledTimes(2);
    expect(streamAnswer).toHaveBeenCalledTimes(2);
    expect(result.current.messages).toHaveLength(4);
  });
  it("aborts on unmount and does not save late events", async () => {
    let signal!: AbortSignal;
    vi.mocked(streamAnswer).mockImplementation(async (_q, _c, _id, abort) => {
      signal = abort;
      await new Promise(() => {});
    });
    const { result, unmount } = renderHook(useChat);
    act(() => {
      void result.current.send("When?");
    });
    unmount();
    expect(signal.aborted).toBe(true);
  });
});
