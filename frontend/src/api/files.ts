import type { FileInfo } from "../types";
import { request } from "./client";

export async function listFiles(signal?: AbortSignal): Promise<FileInfo[]> {
  return (await request("/files", { signal })).json();
}

export async function uploadFile(file: File): Promise<FileInfo> {
  const body = new FormData();
  body.append("file", file);
  return (await request("/files", { method: "POST", body })).json();
}

export async function deleteFile(id: string): Promise<void> {
  await request(`/files/${encodeURIComponent(id)}`, { method: "DELETE" });
}
