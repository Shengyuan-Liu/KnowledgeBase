import { useEffect, useState } from "react";
import { Icon } from "./components/Icon";
import { LibraryPanel } from "./components/LibraryPanel";
import { Modal } from "./components/Modal";
import { EvidencePanel } from "./components/EvidencePanel";
import { ChatPanel } from "./components/ChatPanel";
import { useLibrary } from "./hooks/useLibrary";
import { useChat } from "./hooks/useChat";
import { useMediaQuery } from "./hooks/useMediaQuery";
import styles from "./Workspace.module.css";

export function Workspace() {
  const library = useLibrary();
  const chat = useChat();
  const mobile = useMediaQuery("(max-width: 767px)");
  const compact = useMediaQuery("(max-width: 1199px)");
  const [drawer, setDrawer] = useState<"library" | "evidence" | null>(null);
  const [selection, setSelection] = useState<{
    key: string;
    sourceId: number | null;
  } | null>(null);
  const currentFileIds = new Set(library.files.map((file) => file.file_id));
  const messages = chat.messages.map((message) => ({
    ...message,
    sources:
      message.sources?.map((source) => ({
        ...source,
        file_deleted:
          source.file_deleted ||
          (!library.loading &&
            !library.listError &&
            !currentFileIds.has(source.file_id)),
      })) ?? null,
  }));
  const latestComplete = messages
    .filter(
      (message) =>
        message.role === "assistant" && message.status === "complete",
    )
    .at(-1);
  useEffect(() => {
    setSelection(
      latestComplete ? { key: latestComplete.key, sourceId: null } : null,
    );
  }, [latestComplete?.key]);
  const selected =
    messages.find((message) => message.key === selection?.key) ??
    latestComplete;
  function selectEvidence(key: string, sourceId: number | null) {
    setSelection({ key, sourceId });
    if (compact) setDrawer("evidence");
  }
  const evidence = (
    <EvidencePanel
      message={selected}
      sourceId={selection?.sourceId ?? null}
      onClose={compact ? () => setDrawer(null) : undefined}
    />
  );

  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <a href="/" className={styles.brand}>
          <span className={styles.logo}>
            <Icon name="book" size={23} />
          </span>
          <span>Knowledge Base</span>
        </a>
        <span className={styles.tagline}>
          A little clarity, from your own documents.
        </span>
        <span className={styles.workspaceLabel}>
          <span className={styles.dot} />
          Personal workspace
        </span>
      </header>
      <div className={styles.mobileToolbar}>
        {mobile && (
          <button
            className={styles.secondaryButton}
            onClick={() => setDrawer("library")}
          >
            <Icon name="book" size={17} />
            Library <span className={styles.count}>{library.files.length}</span>
          </button>
        )}
        {compact && (
          <button
            className={styles.secondaryButton}
            onClick={() => setDrawer("evidence")}
          >
            <Icon name="quote" size={17} />
            Evidence
          </button>
        )}
      </div>
      <div className={styles.grid}>
        {!mobile && (
          <aside className={styles.panel} aria-labelledby="library-title">
            <LibraryPanel library={library} />
          </aside>
        )}
        <main className={`${styles.panel} ${styles.chat}`}>
          <ChatPanel
            chat={chat}
            messages={messages}
            ready={library.files.some((file) => file.status === "ready")}
            libraryLoading={library.loading}
            libraryError={!!library.listError}
            onSource={(key, source) => selectEvidence(key, source.source_id)}
            onAnswer={(key) => selectEvidence(key, null)}
          />
        </main>
        {!compact && (
          <aside className={styles.panel} aria-labelledby="evidence-title">
            {evidence}
          </aside>
        )}
      </div>
      {drawer === "library" && mobile && (
        <Modal drawer titleId="library-title" onClose={() => setDrawer(null)}>
          <LibraryPanel library={library} onClose={() => setDrawer(null)} />
        </Modal>
      )}
      {drawer === "evidence" && compact && (
        <Modal drawer titleId="evidence-title" onClose={() => setDrawer(null)}>
          {evidence}
        </Modal>
      )}
      <footer className={styles.pageFooter}>
        <span>Keep your sources close.</span>
        <span>TXT and Markdown knowledge base</span>
      </footer>
    </div>
  );
}
