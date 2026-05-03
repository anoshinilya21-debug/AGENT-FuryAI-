"""File operation tools for the agent."""

from pathlib import Path
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.agent import CodingAgent


def register_file_tools(agent: "CodingAgent") -> None:
    """Register file operation tools on the agent's tool registry."""

    agent.tools.register(
        name="list_files",
        description="List files in a directory",
        parameters={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to workspace (default: root). You can also use 'Desktop' or 'Рабочий стол' to list the user's real Desktop.",
                }
            },
            "required": [],
        },
        handler=lambda path="": _list_files(agent.workspace, path),
    )

    agent.tools.register(
        name="delete_file",
        description="Delete a file",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to workspace"}
            },
            "required": ["path"],
        },
        handler=lambda path: _delete_file(agent.workspace, path),
    )


def _list_files(workspace: Path, path: str = "") -> str:
    target = _resolve_list_target(workspace, path)
    if not target.is_dir():
        return f"Error: Not a directory: {path}"

    entries = []
    for entry in sorted(target.iterdir()):
        prefix = "D" if entry.is_dir() else "F"
        try:
            entries.append(f"{prefix} {entry.relative_to(workspace)}")
        except Exception:
            entries.append(f"{prefix} {entry}")

    return "\n".join(entries) if entries else "Directory is empty"


def _delete_file(workspace: Path, path: str) -> str:
    filepath = _resolve_delete_target(workspace, path)
    if not filepath.exists():
        return f"Error: File not found: {path}"

    try:
        filepath.unlink()
        return f"Deleted: {path}"
    except Exception as e:
        return f"Error deleting file: {e}"


def _resolve_list_target(workspace: Path, path: str) -> Path:
    raw = (path or "").strip()
    if not raw:
        return workspace

    expanded = os.path.expanduser(os.path.expandvars(raw))
    if os.path.isabs(expanded):
        return Path(expanded)

    parts = Path(expanded).parts
    if parts:
        first = parts[0].strip().lower()
        if first in {"desktop", "рабочий стол", "рабочий_стол", "рабочий-стол", "рабочийстол"}:
            desktop_root = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
            return desktop_root.joinpath(*parts[1:]) if len(parts) > 1 else desktop_root

    return workspace / expanded


def _resolve_delete_target(workspace: Path, path: str) -> Path:
    # Keep delete conservative: only allow workspace-relative, absolute, or Desktop alias.
    return _resolve_list_target(workspace, path)
