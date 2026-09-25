"""Freeze source-grounded acceptance inputs before any candidate outputs are seen."""
import json
from pathlib import Path

from evals.automatic import load_benchmark
from evals import judge
from evals.evaluate import digest, git_state, timestamp, write_json
from knowledgebase.config import Settings
from knowledgebase.rag.parsing import parse_markdown, parse_txt

DIRECTORY = Path(__file__).parent


def main():
    if (DIRECTORY / "plan.json").exists():
        raise SystemExit("Inputs are already frozen.")
    development, manifest, documents = load_benchmark()
    heldout = []

    def case(identity, question, points, file, quotes, answerable=True):
        spans = []
        for quote in quotes:
            start = documents[file].index(quote)
            spans.append({"file": file, "start_offset": start, "end_offset": start + len(quote), "quote": quote})
        heldout.append({"id": identity, "question": question, "answerable": answerable,
            "expected_answer_points": points, "category": "release-factual" if answerable else "release-unanswerable",
            "evidence": spans if answerable else [], "context_evidence": [] if answerable else spans,
            "split": "new-frozen-acceptance"})

    case("release-temperature", "In the saved DeepSeek Anthropic compatibility guide, what temperature range is supported?",
         ["Temperature is fully supported over the range 0.0 to 2.0."], "anthropic_api.md",
         [r"| temperature | Fully Supported (range \[0.0 ~ 2.0\]) |"])
    case("release-tool-definition", "In the saved DeepSeek Anthropic guide's tools definition table, are name, input_schema, description and cache_control supported?",
         ["Tool name, input_schema and description are fully supported.", "Tool cache_control is ignored."],
         "anthropic_api.md", ["| name | Fully Supported |\n| input\\_schema | Fully Supported |\n| description | Fully Supported |\n| cache\\_control | Ignored |"])
    case("release-research-fair", "According to the saved Summer Research Initiative page, when is the research project fair held, and can a student outside the CDS MS in Data Science program participate?",
         ["The research project fair is held each spring.", "The initiative is not open to students outside the CDS MS in Data Science program; external student participation is not considered."],
         "masters-in-data-science-summer-research-initiative.txt", [
             "To facilitate connections between CDS MS students and researchers, CDS hosts a research project fair each spring, where invited researchers meet and discuss open projects directly with interested CDS MS students. This initiative is not open to students outside the CDS MS in Data Science program, and external student participation is not considered at this time."])
    case("release-capstone-team", "According to the saved capstone page, how many people are typically in a capstone project group?",
         ["Capstone projects are typically run in groups of 2 to 4 people."],
         "masters-in-data-science-capstone.txt", ["Cooperation within teams is another crucial skill built through the Capstone experience as projects are typically run across groups of 2 to 4 people."])
    case("release-elective-approval", "According to the saved MSDS curriculum page, how do students request approval for an elective not on the approved list, and what information does the request require?",
         ["Complete the Elective Request for DS Students Google form to obtain approval.",
          "Provide course information, the syllabus, the course's relevance to the MSDS degree and goals, and the course website if available."],
         "curriculum.txt", ["Students wishing to take elective courses not on the list must obtain approval. For approval, please complete the Elective Request for DS Students Google form. You will be asked for the below information.\n\nCourse information\nCourse syllabus\nThe relevance of course to your MSDS degree and goals\nThe course website (if available)"])
    case("release-personal-capstone", "Which capstone project and team members have I personally been assigned to?",
         ["State that the supplied documents do not contain the user's personal capstone assignment or team roster.",
          "Do not invent the user's project or teammates from example projects or poster authors."],
         "masters-in-data-science-capstone.txt", [], answerable=False)
    for item in development:
        item["split"] = "development-regression"
    all_cases = development + heldout
    assert len({item["id"] for item in all_cases}) == len(all_cases)
    blocks = []
    for name, text in documents.items():
        parsed = parse_markdown(text) if name.endswith(".md") else parse_txt(text)
        blocks.extend({"unit_id": f"{name}:{i}", "file_name": name, **block.model_dump()}
                      for i, block in enumerate(parsed))
    config = Settings(data_dir=Path("data/evals/20260925T002400Z-semantic-acceptance"),
        openai_max_retries=0, eval_max_retries=0).model_dump(mode="json", exclude={"openai_api_key", "openai_base_url"})
    plan = {"frozen_at": timestamp(), "git": git_state(), "base_config": config,
        "intervention": "parent_child versus semantic; similarity threshold 0.5; other settings fixed",
        "order": ["parent_child", "semantic"], "development_cases": 18, "new_acceptance_cases": 6,
        "cases_sha256": digest(json.dumps(all_cases, sort_keys=True).encode()),
        "corpus_sha256": digest(json.dumps(manifest, sort_keys=True).encode()),
        "judge_protocol": judge.PROTOCOL, "judge_protocol_sha256": judge.protocol_hash(),
        "authorship": "New cases and source spans authored by Codex; no independent human annotation. Frozen before new runs; same familiar corpus, not an independent population.",
        "review": "Codex inspect all new-case answers and all paired correctness, faithfulness and evidence-coverage regressions; retain raw judge disagreements.",
        "decision": "Keep structural default. No threshold/prompt/judge tuning within this comparison. User decides acceptance and merge.",
        "timing_scope": "In-process production streamed service to iterator completion, including save; HTTP excluded. Single pass per question, sequential RAG, four judge workers; model loading separate; no warmup; caches/provider load uncontrolled.",
        "ranking": "Primary comparison uses fixed annotated character/span coverage. Also map ordered child hits to deduplicated canonical parser-block units at K=5, source order within each hit; binary gold-span overlap labels are incomplete semantic relevance proxies. Raw child metrics retained but not compared across different boundaries."}
    for name, data in (("plan.json", plan), ("cases.json", all_cases), ("corpus.json", manifest), ("blocks.json", blocks)):
        write_json(DIRECTORY / name, data)
    print(f"Frozen {len(all_cases)} cases, {len(documents)} documents, {len(blocks)} stable blocks.")


if __name__ == "__main__":
    main()
