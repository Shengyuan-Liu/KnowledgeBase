import { useEffect, useRef, useState } from "react";
import type { ChatMessage, Source } from "../types";
import type { useChat } from "../hooks/useChat";
import { AnswerText } from "./AnswerText";
import { Icon } from "./Icon";
import common from "../Workspace.module.css";
import styles from "../Chat.module.css";

export function ChatPanel({
  chat,
  messages,
  ready,
  libraryLoading,
  libraryError,
  onSource,
  onAnswer,
}: {
  chat: ReturnType<typeof useChat>;
  messages: ChatMessage[];
  ready: boolean;
  libraryLoading: boolean;
  libraryError: boolean;
  onSource: (key: string, source: Source) => void;
  onAnswer: (key: string) => void;
}) {
  const scroll = useRef<HTMLDivElement>(null);
  const nearBottom = useRef(true);
  const [showJump, setShowJump] = useState(false);
  const latest = messages.at(-1);
  const busy = !!chat.activeId || chat.restoring;
  const canSend =
    ready &&
    !libraryLoading &&
    !libraryError &&
    !busy &&
    !chat.restoreError &&
    !!chat.draft.trim();
  function jump() {
    const element = scroll.current;
    if (element) element.scrollTop = element.scrollHeight;
    nearBottom.current = true;
    setShowJump(false);
  }
  useEffect(() => {
    if (nearBottom.current) jump();
    else setShowJump(true);
  }, [latest?.text, messages.length, latest?.status]);

  return (
    <>
      <header className={common.panelHeader}>
        <div>
          <h1>Chat</h1>
          <p>Grounded in your library</p>
        </div>
        <button className={common.secondaryButton} onClick={chat.reset}>
          New chat
        </button>
      </header>
      {chat.restoring && (
        <p className={styles.banner} role="status">
          Restoring saved conversation…
        </p>
      )}
      {chat.restoreError && (
        <div className={common.error} role="alert">
          <strong>Could not restore the conversation</strong>
          <p>{chat.restoreError}</p>
          <button
            className={common.textButton}
            onClick={() => void chat.restore(chat.conversationId!)}
          >
            Retry restoration
          </button>
          {" · "}
          <button className={common.textButton} onClick={chat.reset}>
            Start fresh
          </button>
        </div>
      )}
      {chat.notice && (
        <p className={styles.banner} role="status">
          {chat.notice}
        </p>
      )}
      <div
        ref={scroll}
        className={styles.messages}
        onScroll={() => {
          const element = scroll.current!;
          nearBottom.current =
            element.scrollHeight - element.scrollTop - element.clientHeight <
            80;
          setShowJump(!nearBottom.current);
        }}
      >
        {!messages.length && !chat.restoring && !chat.restoreError && (
          <div className={common.chatEmpty}>
            <div className={common.heroIllustration}>
              <Icon name="book" size={38} />
            </div>
            <span className={common.eyebrow}>YOUR KNOWLEDGE, CONNECTED</span>
            <h2>
              Make room for
              <br />a clearer answer.
            </h2>
            <p>
              {ready
                ? "Ask about your documents. Follow the citations back to the original passages."
                : "Upload your first TXT or Markdown file in Library, then ask a question about it."}
            </p>
          </div>
        )}
        {messages.map((message) =>
          message.role === "user" ? (
            <div key={message.key} className={styles.userMessage}>
              {message.text}
            </div>
          ) : (
            <article
              key={message.key}
              className={styles.answer}
              aria-label="Assistant answer"
            >
              <div className={styles.answerHeading}>
                <span>
                  <Icon name="book" size={16} />
                  Knowledge Base
                </span>
                <span role="status">
                  {message.status === "pending"
                    ? "Searching your documents…"
                    : message.status === "streaming"
                      ? "Answering…"
                      : message.status === "complete"
                        ? "Completed"
                        : message.status === "interrupted"
                          ? "Interrupted"
                          : "Failed"}
                </span>
              </div>
              <AnswerText
                message={message}
                onSource={(source) => onSource(message.key, source)}
              />
              {message.error && (
                <div className={styles.answerError}>
                  <p role="alert">{message.error}</p>
                  {!chat.conversationId && message.status === "interrupted" && (
                    <p>
                      A new conversation cannot be recovered if its completion
                      was lost.
                    </p>
                  )}
                  {message.key === latest?.key && (
                    <button
                      className={common.textButton}
                      disabled={busy || !ready || !!chat.restoreError}
                      onClick={() => void chat.send(message.question)}
                    >
                      Retry answer
                    </button>
                  )}
                </div>
              )}
              {message.sources !== null && (
                <details className={styles.disclosure}>
                  <summary>
                    Sources ({message.sources.length} retrieved passages)
                  </summary>
                  {message.sources.length === 0 ? (
                    <p>No sources were retrieved.</p>
                  ) : (
                    message.sources.map((source) => (
                      <div
                        className={styles.inlineSource}
                        key={source.source_id}
                      >
                        <button
                          className={styles.sourceLink}
                          onClick={() => onSource(message.key, source)}
                        >
                          [{source.source_id}] {source.file_name}
                        </button>
                        {source.file_deleted && (
                          <span className={styles.deleted}>Source deleted</span>
                        )}
                        <blockquote>{source.text}</blockquote>
                      </div>
                    ))
                  )}
                </details>
              )}
              {message.status === "complete" && (
                <button
                  className={styles.inspectButton}
                  onClick={() => onAnswer(message.key)}
                >
                  View evidence
                </button>
              )}
              {message.status === "complete" && message.sources === null && (
                <p className={styles.sourceNote}>
                  No evidence snapshot was recorded for this message.
                </p>
              )}
              {(message.retrievalQuestion || message.debug) && (
                <details className={styles.disclosure}>
                  <summary>Debug details</summary>
                  <p>
                    <strong>Retrieval question:</strong>{" "}
                    {message.retrievalQuestion}
                  </p>
                  {message.debug && (
                    <p>
                      Generation time:{" "}
                      {message.debug.elapsed_seconds.toFixed(2)} s (before
                      saving).
                    </p>
                  )}
                  <p>
                    Cosine distance: smaller is nearer, not a correctness
                    probability.
                  </p>
                  <ul>
                    {message.sources?.map((source) => (
                      <li key={source.source_id}>
                        [{source.source_id}] {source.chunk_id}:{" "}
                        {source.distance.toFixed(4)}
                      </li>
                    ))}
                  </ul>
                  {message.citationCheck && (
                    <p>
                      {message.citationCheck.no_citations
                        ? "No numbered citations."
                        : `Matched citation IDs: ${message.citationCheck.valid_source_ids.join(", ") || "none"}.`}
                      {message.citationCheck.invalid_source_ids.length > 0 &&
                        ` Unmatched IDs: ${message.citationCheck.invalid_source_ids.join(", ")}.`}
                    </p>
                  )}
                </details>
              )}
            </article>
          ),
        )}
      </div>
      {showJump && (
        <button className={styles.jumpButton} onClick={jump}>
          Jump to latest
        </button>
      )}
      <form
        className={common.composerArea}
        onSubmit={(event) => {
          event.preventDefault();
          if (canSend) {
            jump();
            void chat.send();
          }
        }}
      >
        <div className={common.composer}>
          <textarea
            aria-label="Ask about your documents"
            placeholder="Ask about your documents…"
            rows={2}
            disabled={
              busy ||
              !ready ||
              !!chat.restoreError ||
              libraryLoading ||
              libraryError
            }
            value={chat.draft}
            onChange={(event) => chat.setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing
              ) {
                event.preventDefault();
                if (canSend) {
                  jump();
                  void chat.send();
                }
              }
            }}
          />
          {chat.activeId ? (
            <button
              type="button"
              className={styles.stopButton}
              onClick={chat.stop}
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              aria-label="Send question"
              disabled={!canSend}
              className={common.sendButton}
            >
              <Icon name="arrow" size={20} />
            </button>
          )}
        </div>
        <p>
          {libraryLoading
            ? "Checking your library…"
            : libraryError
              ? "Restore your library connection before sending."
              : !ready
                ? "Upload a TXT or Markdown file or wait for processing to finish."
                : "Enter to send · Shift+Enter for a new line · Check the sources."}
        </p>
      </form>
    </>
  );
}
