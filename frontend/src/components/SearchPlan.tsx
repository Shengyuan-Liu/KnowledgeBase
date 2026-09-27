import type { RetrievalDiagnostics } from "../types";
import styles from "../Chat.module.css";

export function SearchPlan({ planning }: { planning: NonNullable<RetrievalDiagnostics["planning"]> }) {
  const trace = planning.trace;
  return <details className={`${styles.disclosure} ${styles.searchPlan}`}>
    <summary>Search plan</summary>
    {planning.message && <p>{planning.message}</p>}
    {trace && <>
      <p>{trace.runs.length} {trace.runs.length === 1 ? "search" : "searches"} completed.
        {planning.hops ? ` Used ${planning.hops.rounds.length} retrieval ${planning.hops.rounds.length === 1 ? "round" : "rounds"}.`
          : trace.plan.route === "direct" ? " Used the original retrieval question." : " Searched independent answer points."}</p>
      <ol>{trace.runs.map((run, i) => <li key={i}>{run.text}</li>)}</ol>
      {planning.hops && <>
        <p>Search stopped: {planning.hops.stop_reason.replaceAll("_", " ")}.</p>
        {planning.hops.dependencies.map(dependency => <div key={dependency.query_id}>
          <p><strong>{dependency.query || dependency.query_template.replace("{target}", "…")}</strong>
            {" · "}{dependency.status.replaceAll("_", " ")}</p>
          {!!dependency.references.length && <>
            <p>Search target: {dependency.target}. Found in:</p>
            {dependency.references.map((reference, index) => <blockquote key={index}>
              {reference.quote}<br /><cite>{reference.file_name}</cite>
            </blockquote>)}
            {!dependency.references_in_final_context && <p>Target evidence is absent from the final answer context.</p>}
          </>}
        </div>)}
      </>}
      <ul>{trace.plan.requirements.map(requirement => {
        const evidence = trace.requirements.find(item => item.requirement_id === requirement.requirement_id);
        return <li key={requirement.requirement_id}>{requirement.description} · {evidence?.supplied_ids.length
          ? "Passages retained" : "No passage retained"}
          {!!evidence?.budget_excluded_ids.length && " · Some passages did not fit the evidence budget"}</li>;
      })}</ul>
      <p>Retrieved passages still need to support the answer. This plan does not verify correctness.</p>
    </>}
    {planning.assessment && <section aria-label="Evidence assessment">
      <h4>Evidence assessment</h4>
      <p>Model assessment of the final supplied passages. Check the quoted evidence; these labels can be wrong.</p>
      {planning.assessment.requirements.map(requirement => <div key={requirement.requirement_id}>
        <p><strong>{requirement.description}</strong>{" · "}{{supported: "Supported", partial: "Partial support",
          missing: "Missing evidence", conflicting: "Conflicting evidence"}[requirement.status]}</p>
        {requirement.gap && <p>{requirement.gap}</p>}
        {requirement.references.map((reference, index) => <blockquote key={index}>
          {reference.quote}<br /><cite>{reference.file_name}</cite>
        </blockquote>)}
      </div>)}
    </section>}
  </details>;
}
