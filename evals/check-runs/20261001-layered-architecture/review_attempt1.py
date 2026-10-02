"""Retain before/after dependency graphs, contract equality and documentation review."""

from graphlib import CycleError, TopologicalSorter
import json
from pathlib import Path
import re
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[3]
DIRECTORY = Path(__file__).resolve().parent
helpers = runpy.run_path(str(ROOT / "tests/test_architecture.py"))
layer, allowed = helpers["layer"], helpers["ALLOWED"]
paths = [*ROOT.joinpath("knowledgebase").rglob("*.py"), ROOT / "main.py", *ROOT.joinpath("evals").glob("*.py")]
after_sources = {path.relative_to(ROOT): path.read_text() for path in paths}
before_paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "3d7d7dd"], text=True).splitlines()
before_sources = {
    Path(path): subprocess.check_output(["git", "show", f"3d7d7dd:{path}"], text=True)
    for path in before_paths
    if path.endswith(".py") and (path.startswith("knowledgebase/") or path == "main.py"
        or path.startswith("evals/") and path.count("/") == 1)
}


def audit(sources):
    graph = helpers["dependencies"](sources)
    try:
        TopologicalSorter(graph).prepare()
        cycle = []
    except CycleError as error:
        cycle = error.args[1]
    violations = sorted(
        (source, target) for source, targets in graph.items() for target in targets
        if layer(target) not in {layer(source), "knowledgebase"} | allowed[layer(source)]
    )
    return {
        "modules": len(graph), "first_party_edges": sum(map(len, graph.values())),
        "cycle_witness": cycle, "layer_violations": violations,
        "graph": {source: sorted(targets) for source, targets in sorted(graph.items())},
    }


before, after = audit(before_sources), audit(after_sources)
assert before["cycle_witness"]
assert not after["cycle_witness"] and not after["layer_violations"]
with (DIRECTORY / "dependency-comparison.json").open("x") as output:
    json.dump({"before_revision": "3d7d7dd", "rules": {key: sorted(value) for key, value in allowed.items()},
               "before": before, "after": after}, output, indent=2)
    output.write("\n")
print(f"Dependency graph: {before['modules']} -> {after['modules']} modules; "
      f"{len(before['layer_violations'])} -> 0 forbidden edges; zero cycles after.")

baseline = json.loads((DIRECTORY / "behavior-before.json").read_text())
observed = json.loads((DIRECTORY / "behavior-after.json").read_text())
assert baseline == observed
print(f"Frozen behavior matches in {len(observed)} groups and {len(observed['schemas'])} schemas.")
assert not subprocess.check_output(["git", "diff", "3d7d7dd", "--", "frontend"], text=True)
print("Frontend source is unchanged from its previously recorded acyclic dependency graph.")

documents = [ROOT / "docs/v2/layered-architecture.md", ROOT / "docs/v2/oop-refactoring.md",
             ROOT / "docs/v2/README.md", DIRECTORY / "README.md"]
for path in documents:
    text = path.read_text()
    assert not re.search(r"[\u4e00-\u9fff]", text), path
    assert sum(line.startswith("```") for line in text.splitlines()) % 2 == 0, path
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if target.startswith(("https://", "http://", "#")):
            continue
        assert (path.parent / target.split("#")[0]).exists(), (path, target)
example = re.search(r"```python\n(.*?)\n```", documents[0].read_text(), re.S)[1]
exec(compile(example, str(documents[0]), "exec"), {})
print("Reviewed English content, module/API names, relative links, fences and runnable chunking example.")
print("1 passed: graph, frozen contracts, frontend scope and documentation review.")
