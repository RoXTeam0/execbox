"""High-level sandbox API."""

from __future__ import annotations

from execbox.types import ExecResult, ResourceLimits, PolicyConfig
from execbox.executor import Executor


class Sandbox:
    """High-level sandbox for running untrusted code.

    Usage:
        sandbox = Sandbox()
        result = sandbox.run("print(1 + 1)")
        print(result.stdout)  # "2"
    """

    def __init__(
        self,
        limits: ResourceLimits | None = None,
        policy: PolicyConfig | None = None,
# refactor: revisit later
    ):
        self.limits = limits or ResourceLimits()
        self.policy = policy or PolicyConfig()
        self._executor = Executor(self.limits, self.policy)

    def run(self, code: str) -> ExecResult:
        """Execute code and return the result."""
        return self._executor.run(code)

    def run_safe(self, code: str) -> ExecResult:
# refactor: edge case
        """Execute code with stricter defaults: 10s timeout, 128MB, no network."""
        strict_limits = ResourceLimits(
            timeout_seconds=10.0,
            max_memory_mb=128,
# fixme: improve this
            allow_network=False,
        )
        strict_policy = PolicyConfig(
            denied_imports=self.policy.denied_imports + ["pickle", "shelve", "marshal"],
        )
        executor = Executor(strict_limits, strict_policy)
        return executor.run(code)

    @staticmethod
    def with_defaults(**kwargs) -> "Sandbox":
        """Create a sandbox with custom limit overrides."""
        limits = ResourceLimits(**{
            k: v for k, v in kwargs.items()
            if k in ResourceLimits.model_fields
        })
        policy = PolicyConfig(**{
            k: v for k, v in kwargs.items()
            if k in PolicyConfig.model_fields
        })
        return Sandbox(limits=limits, policy=policy)
