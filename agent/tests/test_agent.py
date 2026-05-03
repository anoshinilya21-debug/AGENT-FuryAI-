from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile

from src.core.agent import CodingAgent


def _mock_response(content: str | None = None, tool_calls: list | None = None) -> dict:
    return {"content": content, "tool_calls": tool_calls, "usage": {}}


def test_agent_creates_workspace() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp) / "ws"
        CodingAgent(api_key="fake-key", workspace=workspace)
        assert workspace.exists()


def test_read_file_tool() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        (workspace / "test.txt").write_text("hello world")

        agent = CodingAgent(api_key="fake-key", workspace=workspace)
        result = agent._read_file("test.txt")
        assert "hello world" in result


def test_read_file_not_found() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        agent = CodingAgent(api_key="fake-key", workspace=Path(tmp))
        result = agent._read_file("nonexistent.txt")
        assert "not found" in result.lower()


def test_write_file_tool() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        agent = CodingAgent(api_key="fake-key", workspace=workspace)

        result = agent._write_file("out.txt", "test content")
        assert "wrote" in result.lower()
        assert (workspace / "out.txt").read_text() == "test content"


def test_run_command_tool() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        agent = CodingAgent(api_key="fake-key", workspace=Path(tmp))
        result = agent._run_command("echo test")
        assert "test" in result


@patch("src.core.agent.OpenRouterProvider")
def test_agent_run_completes(mock_provider: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)

        mock_instance = MagicMock()
        mock_instance.chat.return_value = _mock_response(
            content="Task completed."
        )
        mock_provider.return_value = mock_instance

        agent = CodingAgent(api_key="fake-key", workspace=workspace)
        agent.llm = mock_instance

        result = agent.run("Do something")
        assert "Task completed" in result


@patch("src.core.agent.OpenRouterProvider")
def test_agent_runs_tool_calls(mock_provider: MagicMock) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)

        mock_instance = MagicMock()
        # First call: use tool, second call: respond
        mock_instance.chat.side_effect = [
            _mock_response(
                content=None,
                tool_calls=[
                    {
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path": "test.txt"}',
                        }
                    }
                ],
            ),
            _mock_response(content="Done after reading"),
        ]
        mock_provider.return_value = mock_instance

        agent = CodingAgent(api_key="fake-key", workspace=workspace)
        agent.llm = mock_instance

        result = agent.run("Read test.txt")
        assert "Done after reading" in result
        assert mock_instance.chat.call_count == 2
