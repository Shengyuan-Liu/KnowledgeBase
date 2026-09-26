import { useCallback, useEffect, useRef, useState } from "react";
import * as api from "../api/files";
import type { FileInfo } from "../types";

export function useLibrary() {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const currentLoad = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    currentLoad.current?.abort();
    const controller = new AbortController();
    currentLoad.current = controller;
    try {
      const result = await api.listFiles(controller.signal);
      if (!controller.signal.aborted) {
        setFiles(result);
        setListError("");
      }
    } catch (error) {
      if (!controller.signal.aborted) setListError((error as Error).message);
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
    return () => currentLoad.current?.abort();
  }, [refresh]);

  useEffect(() => {
    if (listError || !files.some((file) => file.status === "processing"))
      return;
    const timer = window.setTimeout(() => void refresh(), 2000);
    return () => window.clearTimeout(timer);
  }, [files, listError, refresh]);

  async function upload(file: File) {
    setActionError("");
    setNotice("");
    if (!/\.(txt|md|pdf)$/i.test(file.name)) {
      setActionError(
        "Only .txt, .md and .pdf files are supported. Text files must use UTF-8.",
      );
      return;
    }
    setBusy(true);
    setNotice(`Uploading and indexing ${file.name}…`);
    try {
      const saved = await api.uploadFile(file);
      setFiles((previous) => [
        saved,
        ...previous.filter((item) => item.file_id !== saved.file_id),
      ]);
      setNotice(`${saved.file_name} is ready.`);
    } catch (error) {
      setNotice("");
      setActionError((error as Error).message);
    } finally {
      await refresh();
      setBusy(false);
    }
  }

  async function remove(id: string): Promise<void> {
    setBusy(true);
    setNotice("");
    try {
      await api.deleteFile(id);
      setFiles((previous) => previous.filter((file) => file.file_id !== id));
      setNotice("File and indexed content deleted.");
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  return {
    files,
    loading,
    listError,
    actionError,
    notice,
    busy,
    refresh,
    upload,
    remove,
  };
}
