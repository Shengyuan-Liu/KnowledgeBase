import type { RetrievalDiagnostics } from "../types";
import styles from "../Chat.module.css";

export function SearchPlan({ planning }: { planning: NonNullable<RetrievalDiagnostics["planning"]> }) {
  const trace = planning.trace;
  return <details className={`${styles.disclosure} ${styles.searchPlan}`}>
    <summary>Search plan</summary>
    {planning.message && <p>{planning.message}</p>}
    {trace && <>
      <p>{trace.runs.length} {trace.runs.length === 1 ? "search" : "searches"} completed.
        {trace.plan.route === "direct" ? " Used the original retrieval question." : " Searched independent answer points."}</p>
      <ol>{trace.runs.map((run, i) => <li key={i}>{run.text}</li>)}</ol>
      <ul>{trace.plan.requirements.map(requirement => {
        const evidence = trace.requirements.find(item => item.requirement_id === requirement.requirement_id);
        return <li key={requirement.requirement_id}>{requirement.description} · {evidence?.supplied_ids.length
          ? "Passages retained" : "No passage retained"}
          {!!evidence?.budget_excluded_ids.length && " · Some passages did not fit the evidence budget"}</li>;
      })}</ul>
      <p>Retrieved passages still need to support the answer. This plan does not verify correctness.</p>
    </>}
  </details>;
}
