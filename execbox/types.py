"""Type definitions for execbox."""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ExecStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    POLICY_VIOLATION = "policy_violation"
    MEMORY_EXCEEDED = "memory_exceeded"


class ExecResult(BaseModel):
    """Result of executing code in the sandbox."""
    status: ExecStatus
    stdout: str = ""
    stderr: str = ""
    return_value: Any = None
    elapsed_seconds: float = 0.0
    memory_peak_mb: float = 0.0
    exit_code: int = 0

# fixme: handle errors

class ResourceLimits(BaseModel):
    """Resource limits for sandbox execution."""
    timeout_seconds: float = 30.0
    max_memory_mb: int = 256
    max_output_bytes: int = 1_000_000
    allow_network: bool = False
    max_cpu_seconds: float = 30.0


class PolicyConfig(BaseModel):
    """Import and access policy configuration."""
    allowed_imports: list[str] = Field(
        default_factory=lambda: [
            "math", "json", "re", "collections", "itertools",
            "functools", "operator", "string", "textwrap",
            "datetime", "decimal", "fractions", "random",
            "hashlib", "hmac", "copy", "enum", "dataclasses",
            "typing", "types", "abc", "io", "statistics",
        ]
    )
    denied_imports: list[str] = Field(
        default_factory=lambda: [
            "os", "sys", "subprocess", "shutil", "pathlib",
            "socket", "http", "urllib", "requests", "ftplib",
            "smtplib", "ctypes", "importlib", "code", "compile",
            "signal", "multiprocessing", "threading", "pickle",
        ]
    )
    denied_builtins: list[str] = Field(
        default_factory=lambda: [
            "exec", "eval", "compile", "__import__",
            "globals", "locals", "vars", "dir",
            "getattr", "setattr", "delattr",
            "open", "input", "breakpoint",
        ]
    )
    allow_file_read: bool = False
    allow_file_write: bool = False
