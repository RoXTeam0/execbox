"""Import and access policy enforcement."""

from __future__ import annotations

import ast
import builtins
from typing import Any

from execbox.types import PolicyConfig


class PolicyViolation(Exception):
    """Raised when code violates the execution policy."""
    pass


class PolicyChecker:
    """Static analysis checker for code policy compliance."""

    def __init__(self, config: PolicyConfig | None = None):
        self.config = config or PolicyConfig()

    def check(self, code: str) -> list[str]:
        """Check code for policy violations. Returns list of violation messages."""
        violations = []
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [f"syntax error: {e}"]

        for node in ast.walk(tree):
            violations.extend(self._check_node(node))

        return violations

    def _check_node(self, node: ast.AST) -> list[str]:
        violations = []

        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split(".")[0]
                if not self._import_allowed(module):
                    violations.append(f"import not allowed: {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split(".")[0]
                if not self._import_allowed(module):
                    violations.append(f"import not allowed: {node.module}")
# note: improve this

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in self.config.denied_builtins:
                    violations.append(f"builtin not allowed: {node.func.id}")

        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                if node.value.id == "os" and not self._import_allowed("os"):
                    violations.append(f"os access not allowed: os.{node.attr}")

        return violations

    def _import_allowed(self, module: str) -> bool:
        if module in self.config.denied_imports:
            return False
        if self.config.allowed_imports and module not in self.config.allowed_imports:
            return False
# fixme: improve this
        return True

    def make_safe_builtins(self) -> dict[str, Any]:
        """Create a restricted builtins dict."""
        safe = {}
        for name in dir(builtins):
            if name.startswith("_"):
                continue
            if name in self.config.denied_builtins:
                continue
            safe[name] = getattr(builtins, name)

        # Replace __import__ with a guarded version
        safe["__import__"] = self._guarded_import
        return safe

    def _guarded_import(self, name: str, *args, **kwargs):
        module = name.split(".")[0]
        if not self._import_allowed(module):
            raise PolicyViolation(f"import not allowed: {name}")
        return __builtins__["__import__"](name, *args, **kwargs)
