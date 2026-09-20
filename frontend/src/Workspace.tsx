import { useState } from "react";
import { Icon } from "./components/Icon";
import { LibraryPanel } from "./components/LibraryPanel";
import { Modal } from "./components/Modal";
import { useLibrary } from "./hooks/useLibrary";
import { useMediaQuery } from "./hooks/useMediaQuery";
import styles from "./Workspace.module.css";

function EvidencePanel({ onClose }: { onClose?: () => void }) {
  return (
    <>
      <header className={styles.panelHeader}>
        <div>
          <h2 id="evidence-title">Evidence</h2>
          <p>The passages behind an answer</p>
        </div>
        {onClose && (
          <button
            className={styles.iconButton}
            onClick={onClose}
            aria-label="Close evidence"
          >
            <Icon name="close" />
          </button>
        )}
      </header>
      <div className={styles.evidenceEmpty}>
        <span className={styles.smallIllustration}>
          <Icon name="quote" size={25} />
        </span>
        <h3>Sources will appear here</h3>
        <p>
          When chat is connected, explore the original passages behind each
          answer.
        </p>
        <div className={styles.evidenceNote}>
          <Icon name="file" size={17} />
          <span>Grounded in your documents</span>
        </div>
      </div>
    </>
  );
}

export function Workspace() {
  const library = useLibrary();
  const mobile = useMediaQuery("(max-width: 767px)");
  const compact = useMediaQuery("(max-width: 1199px)");
  const [drawer, setDrawer] = useState<"library" | "evidence" | null>(null);
  const readyCount = library.files.filter(
    (file) => file.status === "ready",
  ).length;

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
          <aside
            className={styles.panel}
            aria-labelledby="library-title"
          >
            <LibraryPanel library={library} />
          </aside>
        )}
        <main className={`${styles.panel} ${styles.chat}`}>
          <header className={styles.panelHeader}>
            <div>
              <h1>Chat</h1>
              <p>Grounded in your library</p>
            </div>
            <span className={styles.stageBadge}>Workspace preview</span>
          </header>
          <div className={styles.chatEmpty}>
            <div className={styles.heroIllustration}>
              <Icon name="book" size={38} />
              <span className={styles.quoteAccent}>
                <Icon name="quote" size={16} />
              </span>
            </div>
            <span className={styles.eyebrow}>YOUR KNOWLEDGE, CONNECTED</span>
            <h2>
              Make room for
              <br />a clearer answer.
            </h2>
            <p>
              Bring your notes, ideas, and reference material together. Your
              documents are the starting point.
            </p>
            <div className={styles.stepCard}>
              <span className={styles.stepNumber}>01</span>
              <div>
                <strong>Start with your library</strong>
                <p>
                  {readyCount
                    ? `${readyCount} ${readyCount === 1 ? "document is" : "documents are"} ready. Add more or manage your files in Library.`
                    : "Upload a TXT file using the Library panel."}
                </p>
              </div>
              <Icon name="file" size={21} />
            </div>
          </div>
          <div className={styles.composerArea}>
            <div className={styles.composer}>
              <textarea
                aria-label="Ask about your documents"
                placeholder="Ask about your documents…"
                disabled
                rows={2}
              />
              <button
                aria-label="Send question"
                disabled
                className={styles.sendButton}
              >
                <Icon name="arrow" size={20} />
              </button>
            </div>
            <p>
              File management is ready. Chat will be connected in the next step.
            </p>
          </div>
        </main>
        {!compact && (
          <aside
            className={styles.panel}
            aria-labelledby="evidence-title"
          >
            <EvidencePanel />
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
          <EvidencePanel onClose={() => setDrawer(null)} />
        </Modal>
      )}
      <footer className={styles.pageFooter}>
        <span>Keep your sources close.</span>
        <span>TXT knowledge base</span>
      </footer>
    </div>
  );
}
