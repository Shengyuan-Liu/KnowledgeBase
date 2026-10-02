"""Read Git snapshots with AST; never import or initialize application modules."""

import ast
from hashlib import sha256
import json
from pathlib import Path
import subprocess

DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def module_name(path):
    parts = Path(path).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def layer(module):
    if module == "main" or module.startswith("evals.") or module == "knowledgebase.cli":
        return "entry"
    return module.split(".")[1] if "." in module else module


def strongly_connected(nodes, edges):
    graph = {node: set() for node in nodes}
    for edge in edges:
        graph[edge["source"]].add(edge["target"])
    index, indices, low, stack, active, components = 0, {}, {}, [], set(), []

    def visit(node):
        nonlocal index
        indices[node] = low[node] = index
        index += 1
        stack.append(node)
        active.add(node)
        for target in sorted(graph[node]):
            if target not in indices:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in active:
                low[node] = min(low[node], indices[target])
        if low[node] == indices[node]:
            component = []
            while True:
                target = stack.pop()
                active.remove(target)
                component.append(target)
                if target == node:
                    break
            if len(component) > 1 or node in graph[node]:
                components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indices:
            visit(node)
    return sorted(components)


def audit(revision):
    paths = [p for p in git("ls-tree", "-r", "--name-only", revision).splitlines()
             if p.endswith(".py") and (p.startswith("knowledgebase/") or p == "main.py"
                 or p.startswith("evals/") and p.count("/") == 1)]
    modules = {module_name(path): path for path in paths}
    edges, dynamic, external, hashes = [], [], [], {}

    for module, path in sorted(modules.items()):
        source = git("show", f"{revision}:{path}")
        hashes[path] = sha256(source.encode()).hexdigest()
        package = module if path.endswith("/__init__.py") else module.rpartition(".")[0]

        class Imports(ast.NodeVisitor):
            deferred = 0
            type_only = 0

            def emit(self, target, node, imported):
                row = {"source": module, "target": target, "file": path, "line": node.lineno,
                       "deferred": bool(self.deferred), "type_only": bool(self.type_only),
                       "imported": imported}
                if target in modules:
                    edges.append(row)
                else:
                    external.append(row)

            def visit_Import(self, node):
                for alias in node.names:
                    self.emit(alias.name, node, alias.name)

            def visit_ImportFrom(self, node):
                parts = package.split(".") if package else []
                if node.level:
                    base = ".".join(parts[:len(parts) - node.level + 1])
                    target = ".".join(filter(None, [base, node.module]))
                else:
                    target = node.module or ""
                self.emit(target, node, [alias.name for alias in node.names])
                for alias in node.names:
                    child = f"{target}.{alias.name}"
                    if child in modules:
                        self.emit(child, node, alias.name)

            def visit_FunctionDef(self, node):
                self.deferred += 1
                self.generic_visit(node)
                self.deferred -= 1

            visit_AsyncFunctionDef = visit_FunctionDef

            def visit_If(self, node):
                checking = (isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING"
                            or isinstance(node.test, ast.Attribute) and node.test.attr == "TYPE_CHECKING")
                self.visit(node.test)
                self.type_only += int(checking)
                for statement in node.body:
                    self.visit(statement)
                self.type_only -= int(checking)
                for statement in node.orelse:
                    self.visit(statement)

            def visit_Call(self, node):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                if name in {"import_module", "__import__"}:
                    literal = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) else None
                    dynamic.append({"file": path, "line": node.lineno, "target": literal})
                    if isinstance(literal, str):
                        self.emit(literal, node, "dynamic literal")
                self.generic_visit(node)

        Imports().visit(ast.parse(source, filename=path))

    forbidden = {
        "config": {"schemas", "providers", "storage", "rag", "services", "bootstrap", "api", "entry"},
        "schemas": {"providers", "storage", "rag", "services", "bootstrap", "api", "entry"},
        "providers": {"storage", "rag", "services", "bootstrap", "api", "entry"},
        "storage": {"providers", "rag", "services", "bootstrap", "api", "entry"},
        "rag": {"services", "bootstrap", "api", "entry"},
        "services": {"bootstrap", "api", "entry"},
        "bootstrap": {"api", "entry"},
    }
    violations = [edge for edge in edges if layer(edge["target"]) in forbidden.get(layer(edge["source"]), set())]
    package_edges = sorted({(layer(edge["source"]), layer(edge["target"])) for edge in edges if layer(edge["source"]) != layer(edge["target"])})
    cycles = strongly_connected(modules, edges)
    eager_cycles = strongly_connected(modules, [e for e in edges if not e["deferred"] and not e["type_only"]])
    return {"revision": git("rev-parse", revision).strip(), "module_count": len(modules),
            "application_module_count": sum(p.startswith("knowledgebase/") for p in paths),
            "modules": modules, "source_hashes": hashes, "edges": edges,
            "external_imports": external, "dynamic_imports": dynamic,
            "full_cycles": cycles, "eager_runtime_cycles": eager_cycles,
            "cycle_edges": [e for e in edges if any(e["source"] in cycle and e["target"] in cycle for cycle in cycles)],
            "package_edges": package_edges, "forbidden_package_edges": violations,
            "rules": forbidden}


before, after = audit("bbd0a8d"), audit("c87bf76")
record = {"scope": "All knowledgebase Python modules, root main.py and active top-level evals Python modules; archived runs, tests, dependencies and runtime data excluded.",
          "method": "Python AST, absolute/relative and literal dynamic imports, deferred and type-only imports retained, Tarjan SCC. No application module is executed.",
          "limits": "Static imports only; computed/reflection imports are reported but cannot be resolved. Third-party package internals and implicit package-initialization edges are not treated as source dependencies. Package order allows config as a shared foundation; its mixed Settings/options role is reviewed separately.",
          "before": before, "after": after}
with (DIRECTORY / "python-dependencies.json").open("x") as output:
    json.dump(record, output, indent=2)
    output.write("\n")
for label, report in [("before", before), ("after", after)]:
    print(label, report["module_count"], "modules; full cycles:", report["full_cycles"])
    print(label, "eager cycles:", report["eager_runtime_cycles"], "package violations:", len(report["forbidden_package_edges"]))
print("Cycle imports:", after["cycle_edges"])
print("Package graph:", after["package_edges"])
if after["full_cycles"] or after["forbidden_package_edges"]:
    print("1 failed: strict acyclic architecture check.")
    raise SystemExit(1)
print("1 passed: strict acyclic architecture check.")
