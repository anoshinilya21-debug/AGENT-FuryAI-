import pytest
from pathlib import Path

from src.core.memory import MemoryManager


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    return tmp_path


def test_creates_files_on_init(workspace: Path) -> None:
    MemoryManager(workspace)

    assert (workspace / "USER.md").exists()
    assert (workspace / "MEMORY.md").exists()


def test_get_context(workspace: Path) -> None:
    mm = MemoryManager(workspace)
    context = mm.get_context()

    assert "<user_profile>" in context
    assert "</user_profile>" in context
    assert "<agent_memory>" in context
    assert "</agent_memory>" in context


def test_read_file_respects_limit(workspace: Path) -> None:
    mm = MemoryManager(workspace)

    long_content = "x" * 5000
    (workspace / "USER.md").write_text(long_content)

    context = mm.get_context()
    user_section = context.split("<user_profile>")[1].split("</user_profile>")[0]
    assert len(user_section.strip()) <= MemoryManager.MAX_USER_MD_CHARS


def test_update_memory(workspace: Path) -> None:
    mm = MemoryManager(workspace)

    mm.update_memory("Decision: use SQLite", "## Recent Decisions")

    content = (workspace / "MEMORY.md").read_text()
    assert "Decision: use SQLite" in content


def test_update_memory_nonexistent_section(workspace: Path) -> None:
    mm = MemoryManager(workspace)

    mm.update_memory("New section", "## Nonexistent Section")

    content = (workspace / "MEMORY.md").read_text()
    assert "## Nonexistent Section" in content
    assert "New section" in content


def test_truncate_old_entries(workspace: Path) -> None:
    mm = MemoryManager(workspace)

    large_content = "## Recent Decisions\n"
    for i in range(120):
        large_content += f"- Entry {i}\n"

    (workspace / "MEMORY.md").write_text(large_content)
    mm.update_memory("New entry", "## Recent Decisions")

    content = (workspace / "MEMORY.md").read_text()
    assert len(content) <= MemoryManager.MAX_MEMORY_MD_CHARS
