"""Static enforcement helpers for axiom A1 (no model in the runtime path)."""

from __future__ import annotations

import ast
from collections import deque
import importlib.util
from pathlib import Path


BANNED_CLIENT_ROOTS = frozenset(
    {
        "anthropic",
        "httpx",
        "litellm",
        "llama_cpp",
        "ollama",
        "openai",
        "transformers",
        "vllm",
    }
)


class A1Violation(AssertionError):
    """Raised when runtime source can reach a network/model client import."""


def _module_name(package_root: Path, source: Path) -> tuple[str, bool]:
    relative = source.relative_to(package_root.parent)
    pieces = list(relative.with_suffix("").parts)
    is_package = pieces[-1] == "__init__"
    if is_package:
        pieces.pop()
    return ".".join(pieces), is_package


def _source_imports(module: str, is_package: bool, source: Path) -> set[str]:
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    imported: set[str] = set()
    package = module if is_package else module.rpartition(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                relative = "." * node.level + (node.module or "")
                try:
                    base = importlib.util.resolve_name(relative, package)
                except (ImportError, ValueError):
                    continue
            else:
                base = node.module or ""
            if base:
                imported.add(base)
                imported.update(
                    f"{base}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*"
                )
    return imported


def assert_runtime_dependency_boundary(package_root: str | Path) -> None:
    """Statically reject direct or transitive banned imports from ``fund.runtime``."""

    root = Path(package_root)
    modules: dict[str, tuple[Path, bool]] = {}
    for source in root.rglob("*.py"):
        module, is_package = _module_name(root, source)
        modules[module] = (source, is_package)
    imports = {
        module: _source_imports(module, is_package, source)
        for module, (source, is_package) in modules.items()
    }
    starts = sorted(
        module
        for module in modules
        if module == "fund.runtime" or module.startswith("fund.runtime.")
    )
    queue = deque((module, (module,)) for module in starts)
    visited: set[str] = set()
    while queue:
        module, path = queue.popleft()
        if module in visited:
            continue
        visited.add(module)
        for dependency in imports.get(module, set()):
            root_name = dependency.split(".", 1)[0]
            if root_name in BANNED_CLIENT_ROOTS:
                chain = " -> ".join((*path, dependency))
                raise A1Violation(f"A1 dependency violation: {chain}")
            for local_module in modules:
                if dependency == local_module or dependency.startswith(f"{local_module}."):
                    queue.append((local_module, (*path, local_module)))
