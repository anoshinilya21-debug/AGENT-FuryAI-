"""CLI interface with 80s-90s hacking aesthetic."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.styles import Style

from src.config import Config
from src.core.agent import CodingAgent

if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

VERSION = "0.1.0"

BANNER = r"""
 ██╗  ██╗ █████╗ ███╗   ██╗██████╗ ██╗     ███████╗
 ██║  ██║██╔══██╗████╗  ██║██╔══██╗██║     ██╔════╝
 ███████║███████║██╔██╗ ██║██████╔╝██║     █████╗  
 ██╔══██║██╔══██║██║╚██╗██║██╔══██╗██║     ██╔══╝  
 ██║  ██║██║  ██║██║ ╚████║██║  ██║███████╗███████╗
 ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚══════╝
                       (dev anoshin)
                 autonomous agent v{version}
""".format(version=VERSION)

FURY_STYLE = Style.from_dict(
    {
        "prompt": "bold #00ff41",
        "error": "#ff0000",
        "success": "#00ff41",
        "info": "#888888",
        "warning": "#ffff00",
        "banner": "#00ffff",
        "cyan": "#00ffff",
    }
)


def _print(text: str, style: str = "") -> None:
    tokens: list[tuple[str, str]] = []
    if style:
        tokens.append((f"class:{style}", text))
    else:
        tokens.append(("", text))
    print_formatted_text(FormattedText(tokens), end="\n")


def print_banner() -> None:
    _print(BANNER, "banner")


def print_ok(text: str) -> None:
    _print(f"  [+] {text}", "success")


def print_error(text: str) -> None:
    _print(f"  [-] {text}", "error")


def print_info(text: str) -> None:
    _print(f"  {text}", "info")


def print_warn(text: str) -> None:
    _print(f"  {text}", "warning")


def print_fury(text: str) -> None:
    _print(f"  Fury >> {text}")


def input_fury(message: str, default: str = "") -> str:
    try:
        pfx = f"  >> {message}"
        if default:
            pfx += f" [{default}]"
        pfx += ": "

        result = prompt(
            pfx,
            style=FURY_STYLE,
            default=default,
        )
        return result.strip() or default
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


class OnboardingWizard:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    def run(self) -> Config:
        print_banner()
        _print("  Welcome to FuryAI. Let's set things up.", "success")
        print()

        api_key = self._step_api_key()
        model = self._step_model()
        level = self._step_fury_level()
        workspace = self._step_workspace()

        self._save_config(api_key, model, level, workspace)

        print()
        print_ok(f"Configuration saved to {self.config_path}")
        print_ok(f"Workspace created at {workspace}")
        print()
        print_info("FuryAI is ready. Try:")
        print_info("  fury run \"Optimize my React app\"")
        print_info("  fury chat  # Interactive mode")
        print_info("  fury status # Show agent state")
        print()

        return Config(
            api_key=api_key,
            workspace=Path(workspace),
            model=model,
            max_iterations=int(level),
        )

    def _step_api_key(self) -> str:
        _print("  Step 1/4: API Key", "warning")
        print()
        _print("  Authenticate with OpenRouter to get your API key", "cyan")
        print()
        _print("  1) Browser login (recommended) — press Enter to continue", "success")
        _print("  2) Manual API key entry", "success")
        print()

        choice = input_fury("Choose", "1")

        if choice == "1":
            try:
                from src.auth import authenticate

                api_key = authenticate()
                print()
                print_ok("Authentication successful!")
                print()
                return api_key
            except Exception as e:
                print_error(str(e))
                print_info("Falling back to manual entry...")
                return self._manual_api_key()
        else:
            return self._manual_api_key()

    def _manual_api_key(self) -> str:
        print()
        print_info("Create a key at: https://openrouter.ai/keys")
        print()

        key = input_fury("OpenRouter API Key")
        if not key:
            print_error("API key is required")
            return self._manual_api_key()

        print()
        print_ok("API key saved!")
        print()
        return key

    def _step_model(self) -> str:
        _print("  Step 2/4: Default Model", "warning")
        print()
        _print("  1) openai/gpt-oss-20b:free (recommended)", "success")
        _print("  2) nvidia/nemotron-3-super-120b-a12b:free", "success")
        _print("  3) Custom model ID", "success")
        print()

        choice = input_fury("Choose", "1")

        models = {
            "1": "openai/gpt-oss-20b:free",
            "2": "nvidia/nemotron-3-super-120b-a12b:free",
        }

        model = models.get(choice)
        if not model:
            model = choice

        print()
        print_ok(f"Model set to: {model}")
        print()
        return model

    def _step_fury_level(self) -> str:
        _print("  Step 3/4: Fury Level", "warning")
        print()
        _print("  How autonomous should FuryAI be?")
        print()
        _print("  1  - Ask before every action (safe)", "success")
        _print("  5  - Plan then execute (recommended)", "success")
        _print("  10 - Full autonomy (for experts)", "success")
        print()

        level = input_fury("Level", "5")

        try:
            level_int = int(level)
            if level_int < 1 or level_int > 10:
                raise ValueError
        except ValueError:
            print_error("Level must be 1-10")
            return self._step_fury_level()

        print()
        print_ok(f"Fury level set to {level_int}/10")
        print()
        return level

    def _step_workspace(self) -> str:
        _print("  Step 4/4: Workspace", "warning")
        print()
        print_info("Where should FuryAI work?")
        print()

        workspace = input_fury("Path", "./fury-workspace")
        print()
        print_ok(f"Workspace set to: {workspace}")
        print()
        return workspace

    def _save_config(
        self, api_key: str, model: str, level: str, workspace: str
    ) -> None:
        self.config_path.write_text(
            f"OPENROUTER_API_KEY={api_key}\n"
            f"FURY_MODEL={model}\n"
            f"FURY_LEVEL={level}\n"
            f"FURY_WORKSPACE={workspace}\n"
        )


class ChatInterface:
    def __init__(self, agent: CodingAgent, max_iterations: int = 5) -> None:
        self.agent = agent
        self.max_iterations = max_iterations
        self.session_tokens = 0
        self.skills: list[str] = []

    def run(self) -> None:
        print_banner()

        model_display = self.agent.llm.model.split("/")[-1]
        ws = self.agent.workspace.name

        _print(f"  [=] FuryAI v{VERSION} | model: {model_display} | level: {self.max_iterations}/10 [=]", "cyan")
        _print(f"  [=] workspace: {ws} | skills: {len(self.skills)} [=]", "cyan")
        _print("  [=] Type /help for commands, /exit to quit [=]", "cyan")
        print()

        self._load_skills()

        while True:
            try:
                user_input = prompt(
                    "  You >> ",
                    style=FURY_STYLE,
                )
            except (EOFError, KeyboardInterrupt):
                print()
                self._save_skills()
                print_info("Session saved. See you later.")
                break

            if not user_input.strip():
                continue

            if user_input.startswith("/"):
                self._handle_command(user_input.strip())
                continue

            self._process_task(user_input.strip())

    def _handle_command(self, cmd: str) -> None:
        parts = cmd.split()
        command = parts[0].lower()

        if command == "/exit" or command == "/quit":
            self._save_skills()
            print_info("Session saved. See you later.")
            sys.exit(0)

        elif command == "/help":
            self._show_help()

        elif command == "/memory":
            self._show_memory()

        elif command == "/skills":
            self._show_skills()

        elif command == "/status":
            self._show_status()

        elif command == "/clear":
            os.system("cls" if os.name == "nt" else "clear")
            print_banner()

        else:
            print_error(f"Unknown command: {command}")
            print_info("Type /help for available commands")

    def _show_help(self) -> None:
        print()
        _print("  Available commands:", "bold")
        _print("    /help     - Show this help", "success")
        _print("    /memory   - Show agent memory", "success")
        _print("    /skills   - Show learned skills", "success")
        _print("    /status   - Show agent status", "success")
        _print("    /clear    - Clear screen", "success")
        _print("    /exit     - Quit FuryAI", "success")
        print()

    def _show_memory(self) -> None:
        memory_file = self.agent.workspace / "MEMORY.md"
        user_file = self.agent.workspace / "USER.md"

        memory = memory_file.read_text() if memory_file.exists() else "(empty)"
        user = user_file.read_text() if user_file.exists() else "(empty)"

        print()
        border = "-" * 55
        top = "+" + "-" * 55 + "+"
        bottom = "+" + "-" * 55 + "+"

        _print(f"  {top}", "cyan")
        _print(f"  | FuryAI Memory {' ' * 39}|", "cyan")
        _print(f"  {border}", "cyan")

        lines = user.strip().split("\n")[:5]
        for line in lines:
            cleaned = line.replace("#", "").replace("*", "").strip()
            if cleaned:
                _print(f"  | User: {cleaned[:48]}", "cyan")

        _print(f"  {border}", "cyan")

        lines = memory.strip().split("\n")[:5]
        for line in lines:
            cleaned = line.replace("#", "").replace("*", "").strip()
            if cleaned:
                _print(f"  | {cleaned[:48]}", "cyan")

        _print(f"  {border}", "cyan")
        _print(f"  | Tokens used this session: {self.session_tokens}", "cyan")
        _print(f"  {bottom}", "cyan")
        print()

    def _show_skills(self) -> None:
        if not self.skills:
            print_info("No skills learned yet.")
            return

        print()
        _print("  Learned skills:", "bold")
        for skill in self.skills:
            _print(f"    > {skill}", "success")
        print()

    def _show_status(self) -> None:
        ws = self.agent.workspace
        files = list(ws.glob("*"))
        ws_files = [f.name for f in files if f.name not in ("sandbox", "MEMORY.md", "USER.md")]

        print()
        _print("  Agent Status:", "bold")
        _print(f"    Model:     {self.agent.llm.model}")
        _print(f"    Workspace: {ws}")
        _print(f"    Files:     {len(ws_files)}")
        for f in ws_files:
            _print(f"      > {f}", "success")
        _print(f"    Skills:    {len(self.skills)}")
        print()

    def _process_task(self, task: str) -> None:
        print()
        print_fury("Analyzing task...")
        start = time.time()

        try:
            result = self.agent.run(task, max_iterations=self.max_iterations)
            duration = time.time() - start

            filled = int(20 * min(duration / 3.0, 1.0))
            bar = "\u2588" * filled + "\u2591" * (20 - filled)
            _print(f"  Processing [{bar}] {duration:.1f}s", "info")
            print()

            print_fury(result)
            print()

            if len(task) > 30:
                skill_name = task[:30].lower().replace(" ", "-")
                if skill_name not in self.skills:
                    self.skills.append(skill_name)
                    print_info(f"Skill saved: \"{skill_name}\"")

        except Exception as e:
            print_error(f"Error: {e}")
            print()

    def _load_skills(self) -> None:
        skills_file = self.agent.workspace / "SKILLS.json"
        if skills_file.exists():
            try:
                self.skills = json.loads(skills_file.read_text())
            except (json.JSONDecodeError, ValueError):
                self.skills = []

    def _save_skills(self) -> None:
        skills_file = self.agent.workspace / "SKILLS.json"
        skills_file.write_text(json.dumps(self.skills, indent=2))


def run_onboarding() -> Config:
    wizard = OnboardingWizard(Path(".env"))
    return wizard.run()


def run_interactive(config: Config) -> None:
    agent = CodingAgent(
        api_key=config.api_key,
        workspace=config.workspace,
        model=config.model,
    )
    chat = ChatInterface(agent, max_iterations=config.max_iterations)
    chat.run()


def run_task(config: Config, task: str) -> None:
    agent = CodingAgent(
        api_key=config.api_key,
        workspace=config.workspace,
        model=config.model,
    )

    print_banner()
    print_fury(f"Processing: {task}")
    print()

    start = time.time()
    result = agent.run(task, max_iterations=config.max_iterations)
    duration = time.time() - start

    filled = int(20 * min(duration / 3.0, 1.0))
    bar = "\u2588" * filled + "\u2591" * (20 - filled)
    _print(f"  Processing [{bar}] {duration:.1f}s", "info")
    print()
    print_fury(result)


def show_status(config: Config) -> None:
    ws = config.workspace
    _print("  FuryAI Status:", "bold")
    _print(f"    Model:     {config.model}")
    _print(f"    Workspace: {ws}")
    _print(f"    Level:     {config.max_iterations}/10")

    if ws.exists():
        files = list(ws.glob("*"))
        _print(f"    Files:     {len(files)}")
    else:
        print_info("  Workspace not yet created")

    print()


def list_models(config: Config) -> None:
    import requests

    _print("  Available free models on OpenRouter:", "bold")
    print()

    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=15,
        )
        models = [m for m in resp.json()["data"] if ":free" in m["id"]]
        for m in sorted(models, key=lambda x: x["id"])[:30]:
            ctx = m.get("context_length", "?")
            _print(f"    > {m['id']} (ctx: {ctx})", "success")
    except Exception as e:
        print_error(f"Failed to fetch models: {e}")

    print()


def cli() -> None:
    parser = argparse.ArgumentParser(
        description=f"FuryAI v{VERSION} - Autonomous Coding Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  run TASK     Execute a task
  chat         Start interactive chat
  setup        Run setup wizard
  config       Show current configuration
  status       Show agent status
  models       List available models
  feedback     Print feedback info

Examples:
  fury run "Create a Flask hello world app"
  fury chat
  fury setup
  fury status
        """,
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=["run", "chat", "setup", "config", "status", "models", "feedback"],
        help="Command to execute",
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="Task description (for 'run' command)",
    )
    parser.add_argument(
        "--workspace", "-w",
        help="Override workspace directory",
    )
    parser.add_argument(
        "--model", "-m",
        help="Override model",
    )

    args = parser.parse_args()

    if args.command == "setup":
        run_onboarding()
        return

    env_path = Path(".env")
    if env_path.exists():
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        model = os.environ.get("FURY_MODEL", "openai/gpt-oss-20b:free")
        level = int(os.environ.get("FURY_LEVEL", "5"))
        workspace = os.environ.get("FURY_WORKSPACE", "./fury-workspace")

        if not api_key:
            print_info("API key not configured. Running setup...")
            print()
            config = run_onboarding()
        else:
            config = Config(
                api_key=api_key,
                workspace=Path(args.workspace or workspace),
                model=args.model or model,
                max_iterations=level,
            )
    else:
        print_info("No configuration found. Running setup...")
        print()
        config = run_onboarding()

    if args.command == "run":
        if not args.task:
            print_error("Task is required for 'run' command")
            print_info("Usage: fury run \"your task here\"")
            sys.exit(1)
        run_task(config, args.task)

    elif args.command == "chat":
        run_interactive(config)

    elif args.command == "config":
        _print("  Current configuration:", "bold")
        _print(f"    Model:     {config.model}")
        _print(f"    Workspace: {config.workspace}")
        _print(f"    Level:     {config.max_iterations}/10")
        _print(f"    API Key:   {config.api_key[:8]}...{config.api_key[-4:]}")
        print()

    elif args.command == "status":
        show_status(config)

    elif args.command == "models":
        list_models(config)

    elif args.command == "feedback":
        _print("  Feedback:", "bold")
        print_info("    GitHub: https://github.com/anoshinilya21-debug/AGENT-FuryAI-")
        print_info("    Issues: https://github.com/anoshinilya21-debug/AGENT-FuryAI-/issues")
        print()
