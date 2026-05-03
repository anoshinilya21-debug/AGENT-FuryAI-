from pathlib import Path


class MemoryManager:
    """Manages agent memory via USER.md and MEMORY.md files.

    Key idea: hard length limits force the model to compress information.
    Source: Pattern inspired by Hermes Agent
    - https://github.com/OpenRouterTeam/spawn
    """

    MAX_USER_MD_CHARS = 2000
    MAX_MEMORY_MD_CHARS = 5000

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.user_file = workspace / "USER.md"
        self.memory_file = workspace / "MEMORY.md"
        self._ensure_files_exist()

    def _ensure_files_exist(self) -> None:
        if not self.user_file.exists():
            self.user_file.write_text(
                "# User Profile\n\n"
                "## Preferences\n"
                "- Language: \n"
                "- Code style: \n"
                "- Project: \n\n"
                "## Constraints\n"
                "- \n",
                encoding="utf-8",
            )

        if not self.memory_file.exists():
            self.memory_file.write_text(
                "# Agent Memory\n\n"
                "## Project Context\n\n"
                "## Recent Actions\n\n"
                "## Recent Decisions\n\n"
                "## Lessons Learned\n",
                encoding="utf-8",
            )
        else:
            # Ensure new sections exist for older workspaces
            current = self.memory_file.read_text(encoding="utf-8")
            if "## Recent Actions" not in current:
                # Insert after Project Context if possible, otherwise append
                if "## Project Context" in current:
                    current = current.replace(
                        "## Project Context\n\n",
                        "## Project Context\n\n## Recent Actions\n\n",
                        1,
                    )
                else:
                    current = current.rstrip() + "\n\n## Recent Actions\n\n"
                self.memory_file.write_text(current, encoding="utf-8")

    def get_context(self) -> str:
        user_content = self._read_file_with_limit(
            self.user_file, self.MAX_USER_MD_CHARS
        )
        memory_content = self._read_file_with_limit(
            self.memory_file, self.MAX_MEMORY_MD_CHARS
        )

        return (
            f"<user_profile>\n{user_content}\n</user_profile>\n\n"
            f"<agent_memory>\n{memory_content}\n</agent_memory>"
        )

    def update_memory(self, new_content: str, section: str = "## Recent Decisions") -> None:
        current = self.memory_file.read_text(encoding="utf-8")

        if section not in current:
            current = current.rstrip() + f"\n\n{section}\n\n"

        updated = self._append_to_section(current, section, new_content)

        if len(updated) > self.MAX_MEMORY_MD_CHARS:
            updated = self._truncate_old_entries(updated)

        self.memory_file.write_text(updated, encoding="utf-8")

    def update_user(self, new_content: str, section: str = "## Preferences") -> None:
        current = self.user_file.read_text(encoding="utf-8")
        if section not in current:
            current = current.rstrip() + f"\n\n{section}\n\n"

        updated = self._append_to_section(current, section, new_content)

        if len(updated) > self.MAX_USER_MD_CHARS:
            updated = updated[: self.MAX_USER_MD_CHARS]

        self.user_file.write_text(updated, encoding="utf-8")

    def _append_to_section(self, doc: str, section: str, new_content: str) -> str:
        """Append content under a markdown section, preserving other sections."""
        lines = doc.splitlines()
        try:
            idx = next(i for i, l in enumerate(lines) if l.strip() == section.strip())
        except StopIteration:
            # Fallback: append section at end
            return doc.rstrip() + f"\n\n{section}\n{new_content.rstrip()}\n"

        insert_at = idx + 1
        # Skip a single blank line after header
        if insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1

        payload = [l for l in new_content.rstrip().splitlines()]
        if payload:
            payload.append("")  # ensure separation

        new_lines = lines[:insert_at] + payload + lines[insert_at:]
        return "\n".join(new_lines).rstrip() + "\n"

    def _read_file_with_limit(self, filepath: Path, limit: int) -> str:
        content = filepath.read_text(encoding="utf-8")
        return content[:limit]

    def _truncate_old_entries(self, content: str) -> str:
        lines = content.split("\n")
        if len(lines) > 100:
            header = "\n".join(lines[:10])
            recent = "\n".join(lines[-80:])
            return f"{header}\n... (older entries truncated) ...\n{recent}"
        return content
