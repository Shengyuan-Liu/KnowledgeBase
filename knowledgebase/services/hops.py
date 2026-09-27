"""Run a bounded dependency graph with fresh read sessions between model calls."""
from time import perf_counter

from knowledgebase.rag.context import build_context
from knowledgebase.rag.dependencies import (
    BINDING_INSTRUCTIONS, TargetDecisions, adds_source_text, context_spans,
    dependency_evidence, validate_binding,
)
from knowledgebase.rag.planning import PlannedQuery
from knowledgebase.rag.planned_retrieval import retrieve_plan
from knowledgebase.rag.retrieval import resolve_ready_scope


class HopController:
    def __init__(self, prepared, sessions, embeddings, store, planner, control, **retrieval):
        self.prepared, self.sessions, self.embeddings, self.store = prepared, sessions, embeddings, store
        self.planner, self.control, self.retrieval = planner, control, retrieval
        self.result = None
        self.round_index = 0
        self.finished = False
        self.seen = {}
        self.retrieval_seconds = 0.0
        self.states = {q.query_id: {"query_id": q.query_id, "depends_on": q.depends_on,
            "query_template": q.query_template, "requirement_ids": q.requirement_ids,
            "status": "pending", "target": None, "query": None, "references": []}
            for q in prepared.plan.dependencies}
        self.trace = {"version": 1, "rounds": [], "bindings": [], "dependencies": [], "stop_reason": None}

    def retrieve(self, queries):
        started = perf_counter()
        with self.sessions() as session:
            result = retrieve_plan(self.prepared.plan, session, self.embeddings, self.store,
                **self.retrieval, allowed_file_ids=self.prepared.allowed_file_ids,
                checkpoint=self.control.before_answer, queries=queries,
                previous_runs=self.result.trace.runs if self.result else None,
                round_index=self.round_index)
        self.retrieval_seconds += perf_counter() - started
        return result

    def finish(self, reason):
        self.finished = True
        self.trace["stop_reason"] = reason
        for state in self.states.values():
            if state["status"] == "pending":
                state["status"] = ("blocked" if any(parent in self.states and self.states[parent]["status"] != "executed"
                                                    for parent in state["depends_on"]) else reason)
        final_spans = context_spans(self.result)
        for state in self.states.values():
            state["references_in_final_context"] = bool(state["references"]) and all(
                not adds_source_text({r["file_id"]: [(r["start_offset"], r["end_offset"])]}, final_spans)
                for r in state["references"])
        self.trace["dependencies"] = list(self.states.values())

    def step(self):
        """Advance once; callers can publish progress before each bounded step."""
        self.control.before_answer()
        plan = self.prepared.plan
        if self.result is None:
            queries = plan.queries
        else:
            # Repack only still-eligible evidence before exposing it to the binding model.
            self.result = self.retrieve([])
            complete = {q.query_id for q in plan.queries}
            complete.update(identity for identity, state in self.states.items() if state["status"] == "executed")
            ready = []
            for dependency in plan.dependencies:
                state = self.states[dependency.query_id]
                if state["status"] != "pending":
                    continue
                if any(parent in self.states and self.states[parent]["status"] not in {"pending", "executed"}
                       for parent in dependency.depends_on):
                    state["status"] = "blocked"
                elif set(dependency.depends_on) <= complete:
                    by_parent = [dependency_evidence(self.result, [parent]) for parent in dependency.depends_on]
                    excerpts = list({e["evidence_id"]: e for group in by_parent for e in group}.values())
                    if all(by_parent):
                        ready.append({**dependency.model_dump(), "evidence": excerpts})
                    else:
                        state["status"] = "missing"
            if not ready:
                self.finish("dependency_unresolved")
                return
            decisions, record = self.planner.structured(TargetDecisions, "dependency_targets", BINDING_INSTRUCTIONS,
                {"original_question": plan.original_question, "resolved_question": plan.resolved_question,
                 "pending_queries": ready}, self.control.before_answer, prompt_version="dependency-targets-v1")
            by_id = {item["query_id"]: item for item in ready}
            if len(decisions.decisions) != len(by_id) or {d.query_id for d in decisions.decisions} != by_id.keys():
                raise ValueError("Dependency decisions must cover the exact pending batch once.")
            self.trace["bindings"].append({"before_round": self.round_index + 1, "record": record})
            queries = []
            # Validate the full response before executing any resulting query.
            for decision in decisions.decisions:
                item = by_id[decision.query_id]
                references = validate_binding(decision, item["evidence"])
                state = self.states[decision.query_id]
                state.update(status=decision.status, target=decision.target or None, references=references)
                if decision.status == "resolved":
                    text = item["query_template"].replace("{target}", decision.target)
                    state["query"] = text
                    queries.append(PlannedQuery(query_id=decision.query_id, text=text, requirement_ids=item["requirement_ids"]))
            # A source deleted while the model was running cannot authorize the next search.
            with self.sessions() as session:
                eligible, _ = resolve_ready_scope(plan.resolved_question, session,
                    file_ids=self.retrieval.get("file_ids"), scope_question=plan.original_question,
                    allowed_file_ids=self.prepared.allowed_file_ids)
            for query in queries:
                if any(ref["file_id"] not in eligible for ref in self.states[query.query_id]["references"]):
                    self.states[query.query_id]["status"] = "evidence_unavailable"
            queries = [q for q in queries if self.states[q.query_id]["status"] == "resolved"]
            if not queries:
                self.result = self.retrieve([])
                self.finish("dependency_unresolved")
                return
        self.round_index += 1
        self.result = self.retrieve(queries)
        for query in queries:
            if query.query_id in self.states:
                run = next(run for run in self.result.trace.runs if query.query_id in run.query_ids)
                scope = run.result.diagnostics.document_scope
                self.states[query.query_id]["status"] = "scope_unresolved" if scope and scope.status != "resolved" else "executed"
        spans = context_spans(self.result)
        progressed = adds_source_text(spans, self.seen)
        for identity, intervals in spans.items():
            self.seen.setdefault(identity, []).extend(intervals)
        self.trace["rounds"].append({"round_index": self.round_index,
            "trace": self.result.trace.model_dump(mode="json"),
            "evidence": self.result.evidence.model_dump(mode="json"),
            "context": build_context(self.result.evidence.chunks), "new_source_text": progressed})
        if not any(state["status"] == "pending" for state in self.states.values()):
            self.finish("dependencies_complete" if all(s["status"] == "executed" for s in self.states.values()) else "dependency_unresolved")
        elif self.round_index >= self.control.options.max_rounds:
            self.finish("round_limit")
        elif not progressed:
            self.finish("no_new_evidence")
