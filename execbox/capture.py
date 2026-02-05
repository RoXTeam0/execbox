"""Stdout/stderr capture with size limits."""

from __future__ import annotations

import io
import sys
from typing import Generator
from contextlib import contextmanager


class LimitedWriter(io.StringIO):
    """StringIO that enforces a max byte size."""

    def __init__(self, max_bytes: int = 1_000_000):
        super().__init__()
        self.max_bytes = max_bytes
        self._bytes_written = 0

    def write(self, s: str) -> int:
        encoded_len = len(s.encode("utf-8", errors="replace"))
        if self._bytes_written + encoded_len > self.max_bytes:
            remaining = self.max_bytes - self._bytes_written
            if remaining <= 0:
                return 0
            # Truncate to fit
            s = s[:remaining]
            encoded_len = remaining
        self._bytes_written += encoded_len
        return super().write(s)

    @property
    def truncated(self) -> bool:
        return self._bytes_written >= self.max_bytes


@contextmanager
def capture_output(max_bytes: int = 1_000_000) -> Generator[tuple[LimitedWriter, LimitedWriter], None, None]:
    """Context manager to capture stdout and stderr."""
    out = LimitedWriter(max_bytes)
    err = LimitedWriter(max_bytes)
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        yield out, err
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr

