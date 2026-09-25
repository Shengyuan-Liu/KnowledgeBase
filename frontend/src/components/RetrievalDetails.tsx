import type { RetrievalDiagnostics } from "../types";
import styles from "../Chat.module.css";

const recorded = (value: number | null | undefined, digits = 4) =>
  value == null ? "Not recorded" : value.toFixed(digits);

export function RetrievalDetails({ data }: { data?: RetrievalDiagnostics | null }) {
  if (!data) return <p>Retrieval diagnostics: Not recorded.</p>;
  const selected = new Set(data.candidates.map((candidate) => candidate.chunk_id));
  const reranked = new Map(data.rerank?.matches.map((match) => [match.chunk_id, match]));
  return (
    <section aria-label="Recorded retrieval details">
      <p>
        Strategy: {data.options?.strategy ?? "Not recorded"} · Packing: {data.options?.packing_strategy ?? "Not recorded"}
        {" · "}Selected child limit: {data.top_k ?? "Not recorded"}
      </p>
      <p>Evidence budget: {data.evidence_tokens} / {data.max_tokens} tokens ({data.tokenizer}).</p>
      <p>
        Reranker: {data.rerank?.model ?? (data.options?.rerank_enabled === false ? "Disabled" : "Not recorded")}
        {data.rerank && <> · Scoring unit: {data.options?.rerank_unit ?? "Not recorded"}</>}
        {data.rerank && <> · Revision: {data.rerank.model_revision ?? "Not recorded"} · Device: {data.rerank.device ?? "Not recorded"}</>}
      </p>
      <p>
        Retrieval and source lookup: {recorded(data.retrieval_seconds, 3)} s · Query embedding: {recorded(data.embedding_seconds, 3)} s
        {" · "}Reranking: {recorded(data.rerank_seconds, 3)} s · Packing: {recorded(data.packing_seconds, 3)} s.
        Stage timings are parts of retrieval, not additional response time.
      </p>
      {data.fused_matches.length > 0 && (
        <div className={styles.diagnosticTable} tabIndex={0} role="region" aria-label="Candidate ranking table">
          <table>
            <caption>Candidate rankings. Scores are not correctness probabilities.</caption>
            <thead><tr><th>Child</th><th>BM25 rank / score</th><th>Vector rank / distance</th><th>RRF rank / score</th><th>Rerank rank / score</th><th>Selected</th></tr></thead>
            <tbody>{data.fused_matches.map((match) => {
              const score = reranked.get(match.chunk_id);
              return <tr key={match.chunk_id}>
                <td>{match.chunk_id}</td>
                <td>{match.bm25_rank ?? "No hit"} / {recorded(match.bm25_score)}</td>
                <td>{match.vector_rank ?? "No hit"} / {recorded(match.vector_distance)}</td>
                <td>{match.rank} / {recorded(match.rrf_score, 6)}</td>
                <td>{score ? `${score.rerank_rank} / ${recorded(score.rerank_score)} (${score.score_kind ?? "ordinal_0_3"})` : "Not recorded"}</td>
                <td>{selected.has(match.chunk_id) ? "Yes" : "No"}</td>
              </tr>;
            })}</tbody>
          </table>
        </div>
      )}
      <p><strong>Selected child → parent:</strong></p>
      {data.candidates.length ? <ul>{data.candidates.map((candidate) => (
        <li key={candidate.chunk_id}>{candidate.chunk_id} → {candidate.parent_id ?? "Flat chunk"}</li>
      ))}</ul> : <p>No selected children.</p>}
      <p><strong>Excluded by evidence budget:</strong></p>
      {data.excluded.length ? <ul>{data.excluded.map((region) => (
        <li key={region.chunk_id}>{region.chunk_id} · {region.token_count} source-text tokens · {region.reason}</li>
      ))}</ul> : <p>No budget exclusions recorded.</p>}
      {!!data.unexpanded_parents?.length && <>
        <p><strong>Parents replaced by selected child evidence:</strong></p>
        <ul>{data.unexpanded_parents.map((parent) => <li key={parent.chunk_id}>{parent.chunk_id}</li>)}</ul>
      </>}
    </section>
  );
}
