from __future__ import annotations
"""ADB client abstraction using adbutils.

This module provides a thin wrapper around adbutils to:
- List connected devices
- Send generic shell commands
- Send Unreal Engine broadcast console commands
"""
from typing import List, Optional, Tuple
import shlex

try:
    from adbutils import adb, AdbDevice
except Exception as e:  # pragma: no cover
    raise RuntimeError("Failed to import adbutils. Ensure it is installed inside the venv.") from e

ADB_BROADCAST_ACTION = "android.intent.action.RUN"
EXTRA_KEY = "cmd"


def list_devices() -> List[AdbDevice]:
    """Return a list of connected ADB devices."""
    return adb.device_list()


def get_default_device() -> Optional[AdbDevice]:
    devices = list_devices()
    return devices[0] if devices else None


def shell(device: Optional[AdbDevice], command: str, timeout: int = 10) -> Tuple[bool, str]:
    """Execute a shell command on the given device (or default).

    Returns (ok, output_or_error)
    """
    dev = device or get_default_device()
    if dev is None:
        return False, "No ADB devices connected."
    try:
        # adbutils shell does not expose timeout directly; rely on underlying implementation.
        out = dev.shell(command)
        return True, out.strip()
    except Exception as e:  # pragma: no cover
        return False, f"Shell command failed: {e}"


def _quote_single(s: str) -> str:
    # Use shlex.quote for robust quoting; Android shell (sh) honors single-quoted strings.
    return shlex.quote(s)


def send_unreal_command(cmd: str, device: Optional[AdbDevice] = None) -> Tuple[bool, str]:
    """Send an Unreal command via broadcast intent.

    Returns (ok, message)
    """
    quoted = _quote_single(cmd)
    broadcast_cmd = f"am broadcast -a {ADB_BROADCAST_ACTION} -e {EXTRA_KEY} {quoted}"
    return shell(device, broadcast_cmd)


def ensure_adb_available() -> Tuple[bool, str]:
    """Check that adb server is responsive by listing devices."""
    try:
        devices = list_devices()
        if devices:
            return True, f"{len(devices)} device(s) detected."
        return False, "ADB reachable but no devices detected."
    except Exception as e:  # pragma: no cover
        return False, f"ADB not available: {e}"

__all__ = [
    "list_devices",
    "get_default_device",
    "shell",
    "send_unreal_command",
    "ensure_adb_available",
    "ADB_BROADCAST_ACTION",
    "EXTRA_KEY",
]
