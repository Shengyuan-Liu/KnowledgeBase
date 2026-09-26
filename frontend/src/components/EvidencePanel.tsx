import { lazy, Suspense, useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../types";
import { originalPdfUrl } from "../api/files";
import { Icon } from "./Icon";
import { SearchPlan } from "./SearchPlan";
import common from "../Workspace.module.css";
import styles from "../Chat.module.css";

const PdfViewer = lazy(() => import("./PdfViewer"));

export function EvidencePanel({
  message,
  sourceId,
  onClose,
}: {
  message?: ChatMessage;
  sourceId: number | null;
  onClose?: () => void;
}) {
  const active = useRef<HTMLDivElement>(null);
  const [pdfView, setPdfView] = useState<{ fileId: string; revision: string; fileName: string; initialPage: number } | null>(null);
  useEffect(() => {
    active.current?.scrollIntoView({ block: "nearest", behavior: "instant" });
  }, [message?.key, sourceId]);
  return (
    <>
      <header className={common.panelHeader}>
        <div>
          <h2 id="evidence-title">Evidence</h2>
          <p>
            {message
              ? "Sources for the selected answer"
              : "The passages behind an answer"}
          </p>
        </div>
        {onClose && (
          <button
            className={common.iconButton}
            onClick={onClose}
            aria-label="Close evidence"
          >
            <Icon name="close" />
          </button>
        )}
      </header>
      <div className={styles.evidenceList}>
      {message?.retrieval?.planning && <SearchPlan planning={message.retrieval.planning} />}
      {message?.sources?.length ? (
        <>
          <p className={styles.sourceNote}>
            Original excerpts supplied to this answer. A citation does not
            guarantee support.
          </p>
          {message.sources.map((source) => (
            <div
              key={source.source_id}
              ref={source.source_id === sourceId ? active : undefined}
              className={`${styles.evidenceCard} ${source.source_id === sourceId ? styles.activeSource : ""}`}
              data-source-id={source.source_id}
            >
              <div className={styles.sourceHeading}>
                <span className={styles.sourceNumber}>{source.source_id}</span>
                <strong>{source.file_name}</strong>
              </div>
              <p className={styles.chunkLabel}>
                {source.parent_id === source.chunk_id ? "Parent passage" : "Chunk"} {source.chunk_id}
              </p>
              {!!source.heading_path?.length && (
                <p className={styles.chunkLabel}>{source.heading_path.join(" › ")}</p>
              )}
              <p className={styles.chunkLabel}>
                {source.pdf ? "PDF original pages" : source.start_line != null && source.end_line != null
                  ? `Lines ${source.start_line}–${source.end_line}` : "Source location: Not recorded"}
                {" · "}{message.citationCheck
                  ? message.citationCheck.valid_source_ids.includes(source.source_id)
                    ? "Cited in this answer" : "Additional supplied evidence"
                  : "Citation status: Not recorded"}
              </p>
              {source.file_deleted && (
                <p className={styles.deleted}>
                  Source deleted · Historical excerpt
                </p>
              )}
              {source.pdf && (
                <div className={styles.pdfPages} aria-label="Original PDF pages">
                  {[...new Set([...source.pdf.regions, ...source.pdf.supplements.flatMap(s => s.regions)]
                    .map(r => r.page_index + 1))].sort((a, b) => a - b).map(page =>
                      source.file_deleted ? <span key={page}>Page {page} (original unavailable)</span> :
                        <a key={page} href={originalPdfUrl(source.file_id, source.pdf!.revision_id, page)}
                          onClick={event => {
                            event.preventDefault();
                            setPdfView({ fileId: source.file_id, revision: source.pdf!.revision_id,
                              fileName: source.file_name, initialPage: page });
                          }}>Open page {page}</a>
                    )}
                </div>
              )}
              <blockquote>{source.text}</blockquote>
              {source.pdf?.supplements.map((extra, index) => (
                <div key={index}>
                  <p className={styles.chunkLabel}>Separately located table {extra.role.replaceAll("_", " ")}</p>
                  <blockquote>{extra.text}</blockquote>
                </div>
              ))}
              {!!source.pdf?.warnings.length && (
                <details className={styles.pdfWarnings}>
                  <summary>Extraction limitations</summary>
                  <ul>{[...new Set(source.pdf.warnings.map(w => w.message))].map(message => <li key={message}>{message}</li>)}</ul>
                </details>
              )}
            </div>
          ))}
        </>
      ) : (
        <div className={common.evidenceEmpty}>
          <span className={common.smallIllustration}>
            <Icon name="quote" size={25} />
          </span>
          <h3>
            {!message
              ? "Sources will appear here"
              : message.sources === null
                ? "No recorded evidence"
                : "No sources retrieved"}
          </h3>
          <p>
            {!message
              ? "Ask a question, then select a citation to read its original passage."
              : message.sources === null
                ? "This message has no saved source snapshot."
                : "This answer has no retrieved passages to display."}
          </p>
        </div>
      )}
      </div>
      {pdfView && <Suspense fallback={<p role="status">Opening PDF viewer…</p>}>
        <PdfViewer {...pdfView} onClose={() => setPdfView(null)} />
      </Suspense>}
    </>
  );
}
