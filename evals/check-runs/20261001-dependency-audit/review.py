"""Verify the retained audit conclusions and local documentation references."""

import json
from pathlib import Path
import re
import subprocess

directory = Path(__file__).resolve().parent
root = directory.parents[2]
backend = json.loads((directory / "python-dependencies-2.json").read_text())
frontend = json.loads((directory / "frontend-dependencies.json").read_text())
assert backend["before"]["full_cycles"] == []
assert backend["before"]["application_module_count"] == 55
assert backend["after"]["module_count"] == 64
assert backend["after"]["application_module_count"] == 57
assert backend["after"]["full_cycles"] == [[
    "knowledgebase.rag.chunking", "knowledgebase.rag.semantic_chunking"
]]
assert backend["after"]["eager_runtime_cycles"] == []
assert len(backend["before"]["forbidden_package_edges"]) == 1
assert backend["after"]["forbidden_package_edges"] == []
assert frontend["module_count"] == 19
assert frontend["full_cycles"] == []
assert frontend["forbidden_layer_edges"] == []
for edge in backend["after"]["cycle_edges"]:
    source = (root / edge["file"]).read_text().splitlines()
    assert edge["target"] in source[edge["line"] - 1]
for path in [directory / "README.md", root / "docs/v2/oop-refactoring.md"]:
    text = path.read_text()
    assert not re.search(r"[\u3400-\u9fff]", text)
    assert len(re.findall(r"^```", text, flags=re.MULTILINE)) % 2 == 0
    for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
        if re.match(r"[a-z]+:", target) or target.startswith("#"):
            continue
        assert (path.parent / target.split("#", 1)[0]).exists(), target
for name in ["python-import-graph", "python-import-graph-2", "frontend-import-graph", "frontend-import-graph-2"]:
    record = json.loads((directory / f"{name}.json").read_text())
    assert len(record["metric_inventory"]) == 20
assert subprocess.check_output(["git", "diff", "c87bf76", "--", "knowledgebase", "frontend/src"], cwd=root, text=True) == ""
subprocess.run(["git", "diff", "--check"], cwd=root, check=True)
print("1 passed: audit evidence, module counts, known failed gate, source lines, documentation and unchanged application code verified.")
