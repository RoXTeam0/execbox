"""Code execution in isolated subprocess."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

from execbox.types import ExecResult, ExecStatus, ResourceLimits, PolicyConfig
from execbox.policy import PolicyChecker


# Script template that runs inside the subprocess
_WORKER_TEMPLATE = """import sys
import json

def _execbox_run():
    # Apply resource limits
    limits_json = {limits_json!r}
    policy_json = {policy_json!r}
    limits = json.loads(limits_json)
    policy = json.loads(policy_json)

    # Apply OS-level limits (unix)
    try:
        from execbox.limits import apply_limits, block_network
        from execbox.types import ResourceLimits
        rl = ResourceLimits(**limits)
        apply_limits(rl)
        if not rl.allow_network:
            block_network()
    except ImportError:
        pass

    # Build restricted builtins
    denied = set(policy.get("denied_builtins", []))
    import builtins as _b
    safe_builtins = {{k: getattr(_b, k) for k in dir(_b) if not k.startswith("_") and k not in denied}}

    code = {code!r}
    ns = {{"__builtins__": safe_builtins}}

    try:
        exec(compile(code, "<sandbox>", "exec"), ns)
        result = ns.get("result", None)
        out = {{"status": "success", "return_value": repr(result) if result is not None else None}}
    except MemoryError:
        out = {{"status": "memory_exceeded"}}
    except Exception as e:
        out = {{"status": "error", "error": f"{{type(e).__name__}}: {{e}}"}}

    print("---EXECBOX_RESULT---")
    print(json.dumps(out))

_execbox_run()
"""


class Executor:
    """Execute code in an isolated subprocess with policy and resource limits."""

    def __init__(
        self,
        limits: ResourceLimits | None = None,
        policy: PolicyConfig | None = None,
    ):
        self.limits = limits or ResourceLimits()
        self.policy = policy or PolicyConfig()
        self.checker = PolicyChecker(self.policy)

    def run(self, code: str) -> ExecResult:
        """Execute code string and return result."""
        # Static policy check
        violations = self.checker.check(code)
        if violations:
            return ExecResult(
                status=ExecStatus.POLICY_VIOLATION,
                stderr="\n".join(violations),
            )

        # Prepare worker script
        limits_json = self.limits.model_dump_json()
        policy_json = self.policy.model_dump_json()
        script = _WORKER_TEMPLATE.format(
            limits_json=limits_json,
            policy_json=policy_json,
            code=code,
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(script)
            script_path = f.name

        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=self.limits.timeout_seconds,
                env={"PATH": ""},
            )
            elapsed = time.monotonic() - t0

            stdout = proc.stdout
            stderr = proc.stderr

            # Parse result marker
            if "---EXECBOX_RESULT---" in stdout:
                parts = stdout.split("---EXECBOX_RESULT---")
                user_stdout = parts[0]
                try:
                    result_data = json.loads(parts[1].strip())
                except (json.JSONDecodeError, IndexError):
                    result_data = {"status": "error"}
            else:
                user_stdout = stdout
                result_data = {"status": "error"}

            status_map = {
                "success": ExecStatus.SUCCESS,
                "error": ExecStatus.ERROR,
                "memory_exceeded": ExecStatus.MEMORY_EXCEEDED,
            }

            return ExecResult(
                status=status_map.get(result_data.get("status", "error"), ExecStatus.ERROR),
                stdout=user_stdout.rstrip(),
                stderr=stderr.rstrip() + (
                    "\n" + result_data.get("error", "") if result_data.get("error") else ""
                ).rstrip(),
                return_value=result_data.get("return_value"),
                elapsed_seconds=elapsed,
                exit_code=proc.returncode,
            )
# fixme: revisit later

        except subprocess.TimeoutExpired:
            return ExecResult(
                status=ExecStatus.TIMEOUT,
                elapsed_seconds=self.limits.timeout_seconds,
            )
        finally:
            Path(script_path).unlink(missing_ok=True)

