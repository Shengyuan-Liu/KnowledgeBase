"""Enforce downward dependencies, including local and type-only imports."""

import ast
from graphlib import CycleError, TopologicalSorter
from importlib.util import resolve_name
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# A layer can use its own modules and these lower layers. Peer adapters stay separate.
ALLOWED = {
    "knowledgebase": set(),
    "defaults": set(),
    "schemas": {"defaults"},
    "providers": {"defaults", "schemas"},
    "storage": {"defaults", "schemas"},
    "rag": {"defaults", "schemas", "providers", "storage"},
    "services": {"defaults", "schemas", "providers", "storage", "rag"},
    "config": {"defaults", "schemas"},
    "bootstrap": {
        "defaults",
        "schemas",
        "providers",
        "storage",
        "rag",
        "services",
        "config",
    },
    "api": {
        "defaults",
        "schemas",
        "providers",
        "storage",
        "rag",
        "services",
        "config",
        "bootstrap",
    },
    "cli": {
        "defaults",
        "schemas",
        "providers",
        "storage",
        "rag",
        "services",
        "config",
        "bootstrap",
    },
    "main": {"cli"},
    "evals": {
        "defaults",
        "schemas",
        "providers",
        "storage",
        "rag",
        "services",
        "config",
        "bootstrap",
        "api",
        "cli",
    },
}


def module_name(path):
    parts = path.with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def dependencies(sources):
    """Resolve explicit first-party edges without importing the application."""
    modules = {module_name(path): path for path in sources}
    graph = {module: set() for module in modules}
    for module, path in modules.items():
        package = module if path.name == "__init__.py" else module.rpartition(".")[0]
        tree = ast.parse(sources[path], filename=str(path))
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = resolve_name("." * node.level + (node.module or ""), package)
                targets = [base, *(f"{base}.{alias.name}" for alias in node.names)]
            elif isinstance(node, ast.Call):
                name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else getattr(node.func, "attr", "")
                )
                if name in {"import_module", "__import__"}:
                    assert node.args and isinstance(node.args[0], ast.Constant), (
                        f"{path}:{node.lineno}: computed imports need an explicit architecture audit"
                    )
                    target = node.args[0].value
                    assert isinstance(target, str) and not target.startswith("."), (
                        f"{path}:{node.lineno}: use an absolute literal dynamic import"
                    )
                    targets = [target]
            for target in targets:
                if target in modules:
                    graph[module].add(target)
    return graph


def layer(module):
    if module.startswith("knowledgebase."):
        return module.split(".")[1]
    return module.split(".")[0]


@pytest.fixture
def import_graph():
    paths = [
        *ROOT.joinpath("knowledgebase").rglob("*.py"),
        ROOT / "main.py",
        *ROOT.joinpath("evals").glob("*.py"),
    ]
    return dependencies({path.relative_to(ROOT): path.read_text() for path in paths})


def test_python_module_graph_is_acyclic(import_graph):
    # Local imports and TYPE_CHECKING imports still represent architectural dependencies.
    TopologicalSorter(import_graph).prepare()


def test_layers_only_depend_downward(import_graph):
    violations = []
    for source, targets in import_graph.items():
        source_layer = layer(source)
        assert source_layer in ALLOWED, (
            f"Assign new module {source} to a documented layer"
        )
        for target in targets:
            target_layer = layer(target)
            if (
                target_layer
                not in {source_layer, "knowledgebase"} | ALLOWED[source_layer]
            ):
                violations.append(f"{source} -> {target}")
    assert not violations, "Forbidden dependencies:\n" + "\n".join(sorted(violations))


def test_http_routes_use_services_and_contracts(import_graph):
    # app owns startup; dependencies exposes the assembled resources to request handlers.
    for source, targets in import_graph.items():
        if source.startswith("knowledgebase.api.") and source not in {
            "knowledgebase.api.app",
            "knowledgebase.api.dependencies",
        }:
            assert {layer(target) for target in targets} <= {
                "api",
                "services",
                "schemas",
            }, source


def test_scanner_includes_relative_local_type_only_and_dynamic_imports():
    sources = {
        Path(
            "knowledgebase/rag/chunking.py"
        ): "def split():\n    from . import semantic_chunking\n",
        Path("knowledgebase/rag/semantic_chunking.py"): "from .chunking import split\n",
        Path("knowledgebase/rag/client.py"): (
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n    from ..services import chat\n"
            "import importlib\nimportlib.import_module('knowledgebase.api.app')\n"
        ),
        Path("knowledgebase/services/chat.py"): "",
        Path("knowledgebase/api/app.py"): "",
    }
    graph = dependencies(sources)
    assert graph["knowledgebase.rag.client"] == {
        "knowledgebase.services.chat",
        "knowledgebase.api.app",
    }
    with pytest.raises(CycleError):
        TopologicalSorter(graph).prepare()
