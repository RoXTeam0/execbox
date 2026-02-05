"""Resource limit enforcement using OS-level controls."""

from __future__ import annotations

import os
import platform
import resource as _resource
import signal

from execbox.types import ResourceLimits


def apply_limits(limits: ResourceLimits) -> None:
    """Apply resource limits to the current process. Unix only."""
    if platform.system() == "Windows":
        # resource module not available on Windows; timeout handled by parent
        return

    # Memory limit
    mem_bytes = limits.max_memory_mb * 1024 * 1024
    try:
        _resource.setrlimit(_resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except (ValueError, OSError):
        pass

    # CPU time limit
    cpu_secs = int(limits.max_cpu_seconds)
    try:
        _resource.setrlimit(_resource.RLIMIT_CPU, (cpu_secs, cpu_secs + 1))
    except (ValueError, OSError):
        pass

    # Prevent fork
    try:
        _resource.setrlimit(_resource.RLIMIT_NPROC, (0, 0))
    except (ValueError, OSError, AttributeError):
        pass


def block_network() -> None:
    """Attempt to block network access for this process. Best effort."""
    if platform.system() == "Windows":
        return
    try:
        import socket
        # Monkey-patch socket to prevent connections
        _orig_socket = socket.socket

        class BlockedSocket(_orig_socket):
            def connect(self, *args, **kwargs):
                raise OSError("network access denied by execbox policy")
            def connect_ex(self, *args, **kwargs):
                raise OSError("network access denied by execbox policy")
            def bind(self, *args, **kwargs):
                raise OSError("network access denied by execbox policy")

        socket.socket = BlockedSocket
    except Exception:
        pass
