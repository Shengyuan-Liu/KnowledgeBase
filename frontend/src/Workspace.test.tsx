import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Workspace } from "./Workspace";
import type { FileInfo } from "./types";

const ready: FileInfo = {
  file_id: "file-1",
  file_name: "campus-notes.txt",
  status: "ready",
  error_message: null,
  created_at: "2026-09-20T10:00:00Z",
};
let records: FileInfo[];
let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  records = [];
  fetchMock = vi.fn(async (_url: string, options?: RequestInit) => {
    if (options?.method === "POST") {
      const file = (options.body as FormData).get("file") as File;
      records = [{ ...ready, file_name: file.name }];
      return new Response(JSON.stringify(records[0]), { status: 201 });
    }
    if (options?.method === "DELETE") {
      records = [];
      return new Response(null, { status: 204 });
    }
    return new Response(JSON.stringify(records));
  });
  vi.stubGlobal("fetch", fetchMock);
});

async function openLibrary() {
  render(<Workspace />);
  await waitFor(() =>
    expect(screen.queryByText("Loading your library…")).not.toBeInTheDocument(),
  );
}

function upload(name = "notes.txt") {
  fireEvent.change(screen.getByLabelText("Choose TXT or Markdown file"), {
    target: {
      files: [new File(["Example notes"], name, { type: "text/plain" })],
    },
  });
}

describe("library workspace", () => {
  it("shows an honest empty library and inactive chat", async () => {
    await openLibrary();
    expect(screen.getByText("A home for your notes")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Send question" }),
    ).toBeDisabled();
    expect(screen.getByText("Sources will appear here")).toBeInTheDocument();
  });

  it("uploads multipart TXT and shows the returned ready file", async () => {
    await openLibrary();
    upload();
    expect(await screen.findByText("notes.txt is ready.")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /notes.txt Ready/ }),
    ).toBeInTheDocument();
    const request = fetchMock.mock.calls.find(
      ([, options]) => options?.method === "POST",
    );
    expect(request?.[0]).toBe("/api/files");
    expect(request?.[1].body.get("file").name).toBe("notes.txt");
  });

  it("accepts Markdown and displays its file type", async () => {
    await openLibrary();
    const input = screen.getByLabelText("Choose TXT or Markdown file");
    expect(input).toHaveAttribute("accept", ".txt,.md");
    upload("Guide.MD");
    await screen.findByText("Guide.MD is ready.");
    expect(within(screen.getByRole("button", { name: "Guide.MD Ready" })).getByText("MD"))
      .toBeInTheDocument();
    const request = fetchMock.mock.calls.find(([, options]) => options?.method === "POST");
    expect(request?.[1].body.get("file").name).toBe("Guide.MD");
  });

  it("keeps uploading pending until the server finishes indexing", async () => {
    await openLibrary();
    let finish!: (response: Response) => void;
    fetchMock.mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    );
    upload();
    expect(
      screen.getByText("Uploading and indexing notes.txt…"),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Working…" })).toBeDisabled();
    expect(screen.queryByText("Ready")).not.toBeInTheDocument();
    await act(async () => {
      finish(new Response(JSON.stringify(ready), { status: 201 }));
    });
    await screen.findByText("campus-notes.txt is ready.");
  });

  it("rejects unsupported file selection without posting to the server", async () => {
    await openLibrary();
    upload("notes.pdf");
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Only .txt and .md files",
    );
    expect(
      fetchMock.mock.calls.some(([, options]) => options?.method === "POST"),
    ).toBe(false);
  });

  it("keeps backend validation errors visible and allows another upload", async () => {
    await openLibrary();
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ detail: "The file must be UTF-8 encoded." }),
        { status: 400 },
      ),
    );
    upload();
    expect(await screen.findByRole("alert")).toHaveTextContent("UTF-8");
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Upload file" }),
      ).toBeEnabled(),
    );
    upload();
    await screen.findByText("notes.txt is ready.");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("distinguishes an unavailable library from an empty one and retries", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await openLibrary();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Cannot reach the server",
    );
    expect(screen.queryByText("A home for your notes")).not.toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Retry loading" }),
    );
    await screen.findByText("A home for your notes");
  });

  it("filters locally while retaining the complete library", async () => {
    records = [ready];
    await openLibrary();
    const calls = fetchMock.mock.calls.length;
    await userEvent.type(
      screen.getByRole("textbox", { name: "Search files" }),
      "missing",
    );
    expect(screen.getByText("No matching files")).toBeInTheDocument();
    await userEvent.clear(
      screen.getByRole("textbox", { name: "Search files" }),
    );
    expect(screen.getByText(ready.file_name)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(calls);
  });

  it("requires confirmation, preserves failed deletion, and permits retry", async () => {
    records = [ready];
    await openLibrary();
    await userEvent.click(
      screen.getByRole("button", { name: /campus-notes.txt Ready/ }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(
      fetchMock.mock.calls.some(([, options]) => options?.method === "DELETE"),
    ).toBe(false);
    const dialog = screen.getByRole("dialog");
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ detail: "File cleanup failed; retry deletion." }),
        { status: 500 },
      ),
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Delete file" }),
    );
    expect(await within(dialog).findByRole("alert")).toHaveTextContent(
      "File cleanup failed",
    );
    expect(
      screen.getByRole("button", { name: /campus-notes.txt Ready/ }),
    ).toBeInTheDocument();
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Retry deletion" }),
    );
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(screen.queryByText(ready.file_name)).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/files/file-1", {
      method: "DELETE",
    });
  });

  it("cancels deletion without sending a request", async () => {
    records = [ready];
    await openLibrary();
    await userEvent.click(
      screen.getByRole("button", { name: /campus-notes.txt Ready/ }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Delete" }));
    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([, options]) => options?.method === "DELETE"),
    ).toBe(false);
  });

  it("polls processing records to ready and then stops", async () => {
    vi.useFakeTimers();
    try {
      records = [{ ...ready, status: "processing" }];
      render(<Workspace />);
      await act(async () => {});
      fireEvent.click(
        screen.getByRole("button", { name: /campus-notes.txt Processing/ }),
      );
      expect(screen.getByRole("button", { name: "Delete" })).toBeDisabled();
      records = [ready];
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });
      expect(
        screen.getByRole("button", { name: /campus-notes.txt Ready/ }),
      ).toBeInTheDocument();
      const calls = fetchMock.mock.calls.length;
      await act(async () => {
        await vi.advanceTimersByTimeAsync(6000);
      });
      expect(fetchMock).toHaveBeenCalledTimes(calls);
    } finally {
      vi.useRealTimers();
    }
  });

  it("shows failed server records with a re-upload action", async () => {
    records = [
      {
        ...ready,
        status: "failed",
        error_message: "Embedding service unavailable.",
      },
    ];
    await openLibrary();
    expect(
      screen.getByText("Embedding service unavailable."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Re-upload" })).toBeEnabled();
  });
});
