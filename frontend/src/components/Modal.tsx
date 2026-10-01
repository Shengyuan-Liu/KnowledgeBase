import { useLayoutEffect, useRef, type ReactNode } from "react";
import styles from "../Workspace.module.css";

export function Modal({
  titleId,
  children,
  onClose,
  drawer = false,
  wide = false,
}: {
  titleId: string;
  children: ReactNode;
  onClose: () => void;
  drawer?: boolean;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useLayoutEffect(() => {
    const dialog = ref.current!;
    const trigger = document.activeElement as HTMLElement | null;
    dialog.showModal();
    dialog.querySelector<HTMLElement>("[data-autofocus]")?.focus();
    return () => {
      dialog.close();
      trigger?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      className={drawer ? styles.drawer : styles.modal}
      style={wide ? { width: "min(960px, calc(100vw - 32px))", maxHeight: "90vh", overflow: "auto" } : undefined}
      onCancel={(event) => {
        event.preventDefault();
        event.stopPropagation();
        onClose();
      }}
    >
      {children}
    </dialog>
  );
}
