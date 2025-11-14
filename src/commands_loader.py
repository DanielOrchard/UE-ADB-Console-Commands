"""Load Unreal Engine console commands from the generated Help HTML file.

Parses the JavaScript array `var cvars = [...]` (emitted by UE's `Help`
command) and extracts `{name, help, type}` tuples.

Designed to avoid needing a manual export copy; just point to the latest
`ConsoleHelp.html` file. If the file can't be found or parsed, returns an
empty list.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import List, Optional

# Relative default path (from src directory) to the Saved export.
DEFAULT_HTML_RELATIVE = Path("..") / ".." / ".." / "Saved" / "ConsoleHelp.html"


@dataclass
class UnrealCommand:
    name: str
    help: str
    type: str  # e.g. Cmd / Exec / others


_JS_ARRAY_START = re.compile(r"var\s+cvars\s*=\s*\[", re.IGNORECASE)
_JS_ENTRY_REGEX = re.compile(
    r"\{\s*name\s*:\s*\"(?P<name>(?:\\.|[^\"])*)\"\s*,\s*help\s*:\s*\"(?P<help>(?:\\.|[^\"])*)\"\s*,\s*type\s*:\s*\"(?P<type>(?:\\.|[^\"])*)\"\s*\}",
    re.DOTALL,
)

_DEF_END_REGEX = re.compile(r"\];")


def _decode_js_string(text: str) -> str:
    try:
        # Use unicode_escape to unescape sequences such as \n, \", \' etc.
        return bytes(text, "utf-8").decode("unicode_escape")
    except Exception:
        return text


def _sanitize_help(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_commands(html_path: Optional[Path] = None) -> List[UnrealCommand]:
    path = html_path or DEFAULT_HTML_RELATIVE
    path = path if path.is_absolute() else (Path(__file__).parent / path).resolve()
    if not path.exists():
        return []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    # Locate the array block
    start_match = _JS_ARRAY_START.search(content)
    if not start_match:
        return []
    start_idx = start_match.end()
    end_match = _DEF_END_REGEX.search(content, start_idx)
    if not end_match:
        return []
    array_block = content[start_idx:end_match.start()]

    commands: List[UnrealCommand] = []
    for m in _JS_ENTRY_REGEX.finditer(array_block):
        name = _decode_js_string(m.group("name"))
        help_raw = _decode_js_string(m.group("help"))
        ctype = _decode_js_string(m.group("type"))
        help_text = _sanitize_help(help_raw)
        commands.append(UnrealCommand(name=name, help=help_text, type=ctype))
    return commands


def load_command_names(html_path: Optional[Path] = None) -> List[str]:
    return [c.name for c in load_commands(html_path)]


__all__ = ["UnrealCommand", "load_commands", "load_command_names"]
