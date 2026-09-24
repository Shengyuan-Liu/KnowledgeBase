import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types";
import { Icon } from "./Icon";
import common from "../Workspace.module.css";
import styles from "../Chat.module.css";

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
      {message?.sources?.length ? (
        <div className={styles.evidenceList}>
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
              {source.file_deleted && (
                <p className={styles.deleted}>
                  Source deleted · Historical excerpt
                </p>
              )}
              <blockquote>{source.text}</blockquote>
            </div>
          ))}
        </div>
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
    </>
  );
}
