import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SearchPlan } from "./SearchPlan";
import type { RetrievalDiagnostics } from "../types";

describe("evidence assessment", () => {
  it("shows each status, missing details and exact source quotes", () => {
    const planning: NonNullable<RetrievalDiagnostics["planning"]> = {
      version: 3, message: null, planner: null, trace: null,
      assessment: { round_index: 1, requirements: [
        { requirement_id: "a", description: "Closing hours", status: "supported", gap: "",
          references: [{ evidence_id: "file@0:20", quote: "Closes at 5 PM.", file_name: "hours.txt" }] },
        { requirement_id: "b", description: "Access rules", status: "partial", gap: "Weekend access is unspecified.", references: [] },
        { requirement_id: "c", description: "Fees", status: "missing", gap: "No fee is stated.", references: [] },
        { requirement_id: "d", description: "Opening hours", status: "conflicting", gap: "Sources give different hours.", references: [] },
      ] },
    };
    render(<SearchPlan planning={planning} />);
    expect(screen.getByText("Closes at 5 PM.")).toBeInTheDocument();
    expect(screen.getByText("hours.txt")).toBeInTheDocument();
    for (const status of ["Supported", "Partial support", "Missing evidence", "Conflicting evidence"])
      expect(screen.getByText(new RegExp(status))).toBeInTheDocument();
    expect(screen.getByText("Weekend access is unspecified.")).toBeInTheDocument();
    expect(screen.getByText(/these labels can be wrong/)).toBeInTheDocument();
  });

  it("keeps old saved plans readable without assessment fields", () => {
    render(<SearchPlan planning={{ version: 1, message: null, planner: null, trace: null }} />);
    expect(screen.getByText("Search plan")).toBeInTheDocument();
    expect(screen.queryByText("Evidence assessment")).not.toBeInTheDocument();
  });
});
