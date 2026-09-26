import { useRef, useState } from "react";
import type { useLibrary } from "../hooks/useLibrary";
import type { FileInfo } from "../types";
import { Icon } from "./Icon";
import { Modal } from "./Modal";
import styles from "../Workspace.module.css";

const statusLabels = {
  ready: "Ready",
  processing: "Processing",
  failed: "Failed",
};

export function LibraryPanel({
  library,
  onClose,
}: {
  library: ReturnType<typeof useLibrary>;
  onClose?: () => void;
}) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<FileInfo | null>(null);
  const [deleteError, setDeleteError] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const { files, loading, listError, actionError, busy, notice } = library;
  const visible = files.filter((file) =>
    file.file_name.toLowerCase().includes(query.toLowerCase()),
  );

  async function confirmDelete() {
    if (!deleting) return;
    setDeleteError("");
    try {
      await library.remove(deleting.file_id);
      setDeleting(null);
      setSelected(null);
    } catch (error) {
      setDeleteError((error as Error).message);
    }
  }

  return (
    <>
      <header className={styles.panelHeader}>
        <div>
          <h2 id="library-title">
            Library <span className={styles.count}>{files.length}</span>
          </h2>
          <p>Your documents, in one place</p>
        </div>
        {onClose && (
          <button
            className={styles.iconButton}
            onClick={onClose}
            aria-label="Close library"
          >
            <Icon name="close" />
          </button>
        )}
      </header>
      <div className={styles.libraryBody}>
        <label className={styles.search}>
          <Icon name="search" size={17} />
          <input
            aria-label="Search files"
            placeholder="Search files…"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        {listError && (
          <div role="alert" className={styles.error}>
            <strong>Library unavailable</strong>
            <p>{listError}</p>
            <button
              className={styles.textButton}
              onClick={() => void library.refresh()}
            >
              Retry loading
            </button>
          </div>
        )}
        {loading ? (
          <p className={styles.quiet} role="status">
            Loading your library…
          </p>
        ) : !files.length && !listError ? (
          <div className={styles.libraryEmpty}>
            <span className={styles.smallIllustration}>
              <Icon name="file" size={26} />
            </span>
            <h3>A home for your notes</h3>
            <p>
              Upload your first TXT, Markdown or PDF file to start building your knowledge base.
            </p>
          </div>
        ) : (
          <ul className={styles.fileList} aria-label="Files">
            {visible.map((file) => (
              <li
                key={file.file_id}
                className={`${styles.fileItem} ${selected === file.file_id ? styles.selected : ""}`}
              >
                <button
                  className={styles.fileSelect}
                  aria-label={`${file.file_name} ${statusLabels[file.status]}`}
                  aria-pressed={selected === file.file_id}
                  onClick={() =>
                    setSelected(selected === file.file_id ? null : file.file_id)
                  }
                >
                  <span className={styles.fileBadge}>
                    {file.file_name.toLowerCase().endsWith(".pdf") ? "PDF" : file.file_name.toLowerCase().endsWith(".md") ? "MD" : "TXT"}
                  </span>
                  <span className={styles.fileText}>
                    <strong>{file.file_name}</strong>
                    <span className={`${styles.status} ${styles[file.status]}`}>
                      <span className={styles.dot} />
                      {statusLabels[file.status]}{file.page_count != null ? ` · ${file.page_count} pages` : ""}
                      {!!file.extraction_warnings?.length && " · Review extraction"}
                    </span>
                  </span>
                </button>
                {file.status === "failed" && (
                  <div className={styles.fileFailure}>
                    <p>{file.error_message || "Processing failed."}</p>
                    <button
                      className={styles.textButton}
                      disabled={busy}
                      onClick={() => input.current?.click()}
                    >
                      Re-upload
                    </button>
                  </div>
                )}
                {selected === file.file_id && (
                  <div className={styles.fileDetails}>
                    <span>
                      Added{" "}
                      {new Date(file.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </span>
                    <button
                      className={styles.deleteButton}
                      disabled={busy || file.status === "processing"}
                      onClick={() => {
                        setDeleteError("");
                        setDeleting(file);
                      }}
                    >
                      <Icon name="trash" size={15} />
                      Delete
                    </button>
                    {!!file.extraction_warnings?.length && (
                      <details><summary>Extraction limitations</summary>
                        <ul>{[...new Set(file.extraction_warnings.map(w => w.message))].map(message => <li key={message}>{message}</li>)}</ul>
                      </details>
                    )}
                    {file.status === "processing" && (
                      <p>Wait for processing before deleting.</p>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
        {!loading && files.length > 0 && !visible.length && (
          <p className={styles.quiet}>No matching files</p>
        )}
      </div>
      <footer className={styles.libraryFooter}>
        {actionError && (
          <p role="alert" className={styles.error}>
            {actionError}
          </p>
        )}
        <p className={styles.notice} role="status">
          {notice}
        </p>
        <input
          ref={input}
          type="file"
          accept=".txt,.md,.pdf"
          aria-label="Choose TXT, Markdown or PDF file"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.target.value = "";
            if (file) void library.upload(file);
          }}
        />
        <button
          className={styles.primaryButton}
          disabled={busy}
          onClick={() => input.current?.click()}
        >
          <Icon name="upload" size={18} />
          {busy ? "Working…" : "Upload file"}
        </button>
        <p>TXT / Markdown (UTF-8) · PDF (digital text)</p>
      </footer>
      {deleting && (
        <Modal
          titleId="delete-title"
          onClose={() => {
            if (!busy) setDeleting(null);
          }}
        >
          <span className={styles.dangerIllustration}>
            <Icon name="trash" size={24} />
          </span>
          <h2 id="delete-title">Delete this file?</h2>
          <p className={styles.modalCopy}>
            Delete <strong>{deleting.file_name}</strong> and its indexed
            content? It will no longer be available for new answers.
          </p>
          {deleteError && (
            <p className={styles.error} role="alert">
              {deleteError}
            </p>
          )}
          <div className={styles.modalActions}>
            <button
              data-autofocus
              className={styles.secondaryButton}
              disabled={busy}
              onClick={() => setDeleting(null)}
            >
              Cancel
            </button>
            <button
              className={styles.dangerButton}
              disabled={busy}
              onClick={() => void confirmDelete()}
            >
              {busy
                ? "Deleting…"
                : deleteError
                  ? "Retry deletion"
                  : "Delete file"}
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
