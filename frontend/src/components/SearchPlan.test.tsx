import { render, screen, within } from "@testing-library/react";
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
    expect(screen.queryByText("Table context")).not.toBeInTheDocument();
    expect(screen.queryByText("Selected passages")).not.toBeInTheDocument();
  });

  it("separates application-added table context from the model's selected passages", () => {
    const selected = "Total net sales (1)\t94,930\t89,498\t391,035\t383,285\n";
    const periods = "Three Months Ended\tTwelve Months Ended\n";
    const dates = "September 28, 2024\tSeptember 30, 2023\tSeptember 28, 2024\tSeptember 30, 2023\n";
    const planning: NonNullable<RetrievalDiagnostics["planning"]> = {
      version: 3, message: null, planner: null, trace: null,
      assessment: { round_index: 1, requirements: [
        { requirement_id: "sales", description: "Quarterly and annual sales", status: "supported", gap: "",
          references: [{ evidence_id: "p6", quote: selected, file_name: "apple-fy24.pdf" }],
          table_context: [
            { evidence_id: "p1", quote: periods, file_name: "apple-fy24.pdf" },
            { evidence_id: "p2", quote: dates, file_name: "apple-fy24.pdf" },
          ] },
      ] },
    };
    const { container } = render(<SearchPlan planning={planning} />);
    const context = screen.getByRole("group", { name: "Table context", hidden: true });
    expect(screen.getByText("Selected passages")).toBeInTheDocument();
    expect(within(context).getByText(/Added by the application from the selected table/)).toBeInTheDocument();
    const quotes = [...container.querySelectorAll("blockquote")];
    expect(quotes.map(quote => quote.firstChild?.textContent)).toEqual([selected, periods, dates]);
    expect(context.contains(quotes[0])).toBe(false);
    expect(context.contains(quotes[1])).toBe(true);
    expect(context.contains(quotes[2])).toBe(true);
    expect(screen.getAllByText("apple-fy24.pdf")).toHaveLength(3);
    expect(screen.queryByText("p6")).not.toBeInTheDocument();
    expect(screen.queryByText("p1")).not.toBeInTheDocument();
    expect(screen.getByText(/these labels can be wrong/)).toBeInTheDocument();
  });

  it("omits the table context section when no context passages were added", () => {
    render(<SearchPlan planning={{
      version: 3, message: null, planner: null, trace: null,
      assessment: { round_index: 1, requirements: [
        { requirement_id: "hours", description: "Closing hours", status: "supported", gap: "",
          references: [{ evidence_id: "p1", quote: "Closes at 5 PM.", file_name: "hours.txt" }], table_context: [] },
      ] },
    }} />);
    expect(screen.getByText("Closes at 5 PM.")).toBeInTheDocument();
    expect(screen.queryByText("Table context")).not.toBeInTheDocument();
    expect(screen.queryByText("Selected passages")).not.toBeInTheDocument();
  });

  it("keeps old saved plans readable without assessment fields", () => {
    render(<SearchPlan planning={{ version: 1, message: null, planner: null, trace: null }} />);
    expect(screen.getByText("Search plan")).toBeInTheDocument();
    expect(screen.queryByText("Evidence assessment")).not.toBeInTheDocument();
  });
});
