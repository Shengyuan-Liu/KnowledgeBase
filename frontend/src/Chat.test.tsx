import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { Workspace } from "./Workspace";
import { completed, frame, source, sse } from "./test/chatFixtures";
import { CONVERSATION_KEY } from "./hooks/useChat";
import type { SavedConversation } from "./types";

const files = [
  {
    file_id: "file-1",
    file_name: "hours.txt",
    status: "ready",
    error_message: null,
    created_at: "2026-09-20T10:00:00Z",
  },
  {
    file_id: "file-2",
    file_name: "other.txt",
    status: "ready",
    error_message: null,
    created_at: "2026-09-20T10:00:00Z",
  },
];
let fetchMock: ReturnType<typeof vi.fn>;
beforeEach(() => {
  fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
    if (url === "/api/chat/stream") {
      const id = JSON.parse(options?.body as string).request_id;
      return sse(
        frame("sources", { sources: [source] }, id) +
          frame("answer_delta", { delta: "Temporary" }, id) +
          frame("complete", completed, id),
      );
    }
    return new Response(JSON.stringify(files));
  });
  vi.stubGlobal("fetch", fetchMock);
});

it("sends on Enter, renders completion, and opens validated evidence", async () => {
  render(<Workspace />);
  const input = screen.getByRole("textbox", {
    name: "Ask about your documents",
  });
  await waitFor(() => expect(input).toBeEnabled());
  await userEvent.type(input, "When does it close?{enter}");
  expect(await screen.findByText("Completed")).toBeInTheDocument();
  expect(screen.queryByText("Temporary")).not.toBeInTheDocument();
  expect(input).toHaveValue("");
  await userEvent.click(
    screen.getByRole("button", { name: "View source 1: hours.txt" }),
  );
  expect(
    within(screen.getByRole("complementary", { name: "Evidence" })).getByText(
      source.text,
    ),
  ).toBeInTheDocument();
});

it("does not send during IME composition or Shift+Enter", async () => {
  render(<Workspace />);
  const input = screen.getByRole("textbox", {
    name: "Ask about your documents",
  });
  await waitFor(() => expect(input).toBeEnabled());
  fireEvent.change(input, { target: { value: "When?" } });
  fireEvent.keyDown(input, { key: "Enter", isComposing: true });
  fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
  expect(
    fetchMock.mock.calls.filter(([url]) => url === "/api/chat/stream"),
  ).toHaveLength(0);
});

it("keeps repeated citation numbers bound to their answer and marks deleted historical sources", async () => {
  localStorage.setItem(CONVERSATION_KEY, "conversation-1");
  const history: SavedConversation = {
    conversation_id: "conversation-1",
    messages: [
      {
        message_id: 2,
        role: "assistant",
        content: "First answer. [1] [99] <script>bad()</script>",
        sources: [source],
        citation_check: completed.citation_check,
        retrieval_question: "First?",
      },
      {
        message_id: 4,
        role: "assistant",
        content: "Second answer. [1]",
        sources: [
          {
            ...source,
            file_id: "file-2",
            file_name: "other.txt",
            text: "Second original passage",
          },
        ],
        citation_check: completed.citation_check,
        retrieval_question: "Second?",
      },
    ],
  };
  fetchMock.mockImplementation(async (url: string, options?: RequestInit) => {
    if (url.includes("/conversations/"))
      return new Response(JSON.stringify(history));
    if (options?.method === "DELETE")
      return new Response(null, { status: 204 });
    return new Response(
      JSON.stringify(files.filter((file) => file.file_id !== "file-1")),
    );
  });
  render(<Workspace />);
  await screen.findByRole("button", { name: "View source 1: hours.txt" });
  await userEvent.click(
    screen.getByRole("button", { name: "View source 1: other.txt" }),
  );
  const evidence = screen.getByRole("complementary", { name: "Evidence" });
  expect(
    within(evidence).getByText("Second original passage"),
  ).toBeInTheDocument();
  await userEvent.click(
    screen.getByRole("button", { name: "View source 1: hours.txt" }),
  );
  expect(within(evidence).getByText(source.text)).toBeInTheDocument();
  expect(
    within(evidence).getByText("Source deleted · Historical excerpt"),
  ).toBeInTheDocument();
  expect(
    within(evidence).queryByText("Second original passage"),
  ).not.toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: /View source 99/ }),
  ).not.toBeInTheDocument();
  expect(document.querySelector("script")).toBeNull();
});

it("preserves the draft and partial answer after EOF without completion", async () => {
  fetchMock.mockImplementation(async (url: string, options?: RequestInit) =>
    url === "/api/chat/stream"
      ? sse(
          frame(
            "answer_delta",
            { delta: "Partial answer" },
            JSON.parse(options?.body as string).request_id,
          ),
        )
      : new Response(JSON.stringify(files)),
  );
  render(<Workspace />);
  const input = screen.getByRole("textbox", {
    name: "Ask about your documents",
  });
  await waitFor(() => expect(input).toBeEnabled());
  await userEvent.type(input, "When?{enter}");
  await screen.findByText("Interrupted");
  expect(screen.getByText("Partial answer")).toBeInTheDocument();
  expect(input).toHaveValue("When?");
  expect(screen.queryByText("Completed")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Retry answer" })).toBeEnabled();
});
