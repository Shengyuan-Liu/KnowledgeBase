import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Workspace } from "./Workspace";
import "./tokens.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Workspace />
  </StrictMode>,
);
