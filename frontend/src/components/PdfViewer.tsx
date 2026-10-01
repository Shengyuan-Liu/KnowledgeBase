import { useEffect, useRef, useState } from "react";
import { getDocument, GlobalWorkerOptions, type PDFDocumentProxy, type RenderTask } from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { originalPdfUrl } from "../api/files";
import { Modal } from "./Modal";
import styles from "../Chat.module.css";
import common from "../Workspace.module.css";

GlobalWorkerOptions.workerSrc = workerUrl;

export default function PdfViewer({ fileId, revision, fileName, initialPage, onClose }: {
  fileId: string; revision: string; fileName: string; initialPage: number; onClose: () => void;
}) {
  const [document, setDocument] = useState<PDFDocumentProxy | null>(null);
  const [page, setPage] = useState(initialPage);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const canvas = useRef<HTMLCanvasElement>(null);
  const url = originalPdfUrl(fileId, revision, page).split("#")[0];
  useEffect(() => {
    let active = true;
    const loading = getDocument({ url });
    loading.promise.then(pdf => { if (active) setDocument(pdf); })
      .catch(() => { if (active) setError("The original PDF could not be opened. It may have been deleted."); });
    return () => { active = false; void loading.destroy(); };
  }, [url]);
  useEffect(() => {
    if (!document) return;
    let active = true;
    let rendering: RenderTask | undefined;
    setReady(false);
    setError("");
    document.getPage(page).then(async pdfPage => {
      if (!active || !canvas.current) return;
      const viewport = pdfPage.getViewport({ scale: 1.5 });
      canvas.current.width = viewport.width;
      canvas.current.height = viewport.height;
      rendering = pdfPage.render({ canvas: canvas.current, viewport });
      await rendering.promise;
      if (active) setReady(true);
    }).catch(() => { if (active) setError("This PDF page could not be rendered. Download the original to inspect it."); });
    return () => { active = false; rendering?.cancel(); };
  }, [document, page]);
  return <Modal titleId="pdf-title" onClose={onClose} wide>
    <div className={styles.pdfToolbar}>
      <h2 id="pdf-title">{fileName}</h2>
      <button className={common.secondaryButton} onClick={onClose} data-autofocus aria-label="Close PDF">Close</button>
    </div>
    <div className={styles.pdfToolbar}>
      <button className={common.secondaryButton} disabled={!document || page <= 1} onClick={() => setPage(page - 1)}>Previous page</button>
      <span>Page {page}{document ? ` of ${document.numPages}` : ""}</span>
      <button className={common.secondaryButton} disabled={!document || page >= document.numPages} onClick={() => setPage(page + 1)}>Next page</button>
      <a href={url} download={fileName}>Download original</a>
    </div>
    {error ? <p role="alert">{error}</p> : !ready && <p role="status">Loading page…</p>}
    <canvas ref={canvas} className={styles.pdfCanvas} aria-label={`Original PDF page ${page}`}
      data-rendered={ready} hidden={!ready} />
  </Modal>;
}
