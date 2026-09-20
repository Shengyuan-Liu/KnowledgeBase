import type { FileInfo } from "../types";

async function request(path: string, options?: RequestInit): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(`/api/files${path}`, options);
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw error;
    throw new Error(
      "Cannot reach the server. Check your connection and try again.",
    );
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      typeof body?.detail === "string"
        ? body.detail
        : `Request failed (${response.status}). Please try again.`,
    );
  }
  return response;
}

export async function listFiles(signal?: AbortSignal): Promise<FileInfo[]> {
  return (await request("", { signal })).json();
}

export async function uploadFile(file: File): Promise<FileInfo> {
  const body = new FormData();
  body.append("file", file);
  return (await request("", { method: "POST", body })).json();
}

export async function deleteFile(id: string): Promise<void> {
  await request(`/${encodeURIComponent(id)}`, { method: "DELETE" });
}
