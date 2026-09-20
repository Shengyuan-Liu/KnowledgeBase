import type { ChatMessage, Source } from "../types";
import styles from "../Chat.module.css";

/** Render model text as text. Only validated, present source IDs become controls. */
export function AnswerText({
  message,
  onSource,
}: {
  message: ChatMessage;
  onSource: (source: Source) => void;
}) {
  const parts = message.text.split(/(\[\d+\])/g);
  return (
    <div className={styles.answerText}>
      {parts.map((part, index) => {
        const id = /^\[(\d+)\]$/.exec(part)?.[1];
        const source =
          id &&
          message.status === "complete" &&
          message.citationCheck?.valid_source_ids.includes(Number(id))
            ? message.sources?.find((source) => source.source_id === Number(id))
            : undefined;
        return source ? (
          <button
            key={index}
            className={styles.citation}
            onClick={() => onSource(source)}
            aria-label={`View source ${source.source_id}: ${source.file_name}`}
          >
            {part}
          </button>
        ) : (
          part
        );
      })}
    </div>
  );
}
