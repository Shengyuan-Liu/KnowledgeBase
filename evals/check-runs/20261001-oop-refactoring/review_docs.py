"""Check changed documentation without executing its examples or provider calls."""

import ast
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote


DIRECTORY = Path(__file__).resolve().parent
ROOT = DIRECTORY.parents[2]


def main():
    names = subprocess.check_output(
        ["git", "diff", "--name-only", "bbd0a8d", "--", "docs"], cwd=ROOT, text=True
    ).splitlines()
    names.append(str((DIRECTORY / "README.md").relative_to(ROOT)))
    results = []
    problems = []
    for name in names:
        path = ROOT / name
        source = path.read_text()
        fences = re.findall(r"^\s*```.*$", source, flags=re.MULTILINE)
        if len(fences) % 2:
            problems.append(f"{name}: unbalanced fenced blocks")
        if re.search(r"[\u3400-\u9fff]", source):
            problems.append(f"{name}: Chinese text in project documentation")
        links = []
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", source):
            target = target.split()[0].strip("<>")
            if re.match(r"[a-zA-Z]+:", target) or target.startswith("#"):
                continue
            target_path = unquote(target.split("#", 1)[0])
            links.append(target)
            if not (path.parent / target_path).exists():
                problems.append(f"{name}: missing relative target {target}")
        snippets = re.findall(r"^```python\n(.*?)^```", source, re.MULTILINE | re.DOTALL)
        for index, snippet in enumerate(snippets, 1):
            try:
                ast.parse(snippet)
            except SyntaxError as error:
                problems.append(f"{name}: Python example {index}: {error}")
        results.append({
            "file": name,
            "sha256": sha256(path.read_bytes()).hexdigest(),
            "relative_links": links,
            "python_examples": len(snippets),
            "fenced_blocks": len(fences) // 2,
        })
    whitespace = subprocess.run(
        ["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True
    )
    if whitespace.returncode:
        problems.append(whitespace.stdout + whitespace.stderr)
    with (DIRECTORY / "documentation-review.json").open("x") as output:
        json.dump({
            "reviewer": "Codex",
            "automated_scope": "Relative file targets, fences, Python syntax, English text and diff whitespace.",
            "manual_scope": "Component ownership, interface examples and removed-function references.",
            "limits": "External URLs and rendered browser layout are not checked; examples are not executed.",
            "files": results,
            "problems": problems,
        }, output, indent=2)
        output.write("\n")
    assert not problems, "\n".join(problems)
    print(f"{len(results)} passed: documentation content, links and formatting reviewed.")


if __name__ == "__main__":
    main()
