"""Main CLI entry point for Start Green Stay Green.

Implements the command-line interface using Typer with rich output formatting.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import sys
from typing import Annotated
from typing import Any
from typing import TYPE_CHECKING
from typing import TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Coroutine
    from collections.abc import Generator
    from collections.abc import Sequence

    from start_green_stay_green.utils.enhance_state import EnhanceState

from rich.console import Console
from rich.panel import Panel
import typer

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError as AIGenerationError
from start_green_stay_green.generators.architecture import (
    ArchitectureEnforcementGenerator,
)
from start_green_stay_green.generators.base import SUPPORTED_LANGUAGES
from start_green_stay_green.generators.base import validate_language
from start_green_stay_green.generators.ci import CIGenerator
from start_green_stay_green.generators.claude_md import ClaudeMdGenerator
from start_green_stay_green.generators.dependencies import DependenciesGenerator
from start_green_stay_green.generators.dependencies import DependencyConfig
from start_green_stay_green.generators.github_actions import (
    GitHubActionsReviewGenerator,
)
from start_green_stay_green.generators.metrics import MetricsGenerationConfig
from start_green_stay_green.generators.metrics import MetricsGenerator
from start_green_stay_green.generators.precommit import GenerationConfig
from start_green_stay_green.generators.precommit import PreCommitGenerator
from start_green_stay_green.generators.readme import ReadmeConfig
from start_green_stay_green.generators.readme import ReadmeGenerator
from start_green_stay_green.generators.scripts import ScriptConfig
from start_green_stay_green.generators.scripts import ScriptsGenerator
from start_green_stay_green.generators.skills import REFERENCE_SKILLS_DIR
from start_green_stay_green.generators.skills import REQUIRED_SKILLS
from start_green_stay_green.generators.structure import StructureConfig
from start_green_stay_green.generators.structure import StructureGenerator
from start_green_stay_green.generators.subagents import REFERENCE_AGENTS_DIR
from start_green_stay_green.generators.subagents import REQUIRED_AGENTS
from start_green_stay_green.generators.subagents import SubagentsGenerator
from start_green_stay_green.generators.tests_gen import TestsConfig
from start_green_stay_green.generators.tests_gen import TestsGenerator
from start_green_stay_green.utils.async_bridge import run_async
from start_green_stay_green.utils.credentials import get_api_key_from_keyring
from start_green_stay_green.utils.credentials import store_api_key_in_keyring
from start_green_stay_green.utils.enhance_state import hash_inputs
from start_green_stay_green.utils.enhance_state import load_state
from start_green_stay_green.utils.enhance_state import save_state
from start_green_stay_green.utils.file_writer import FileWriter
from start_green_stay_green.utils.timing import TimingReport
from start_green_stay_green.utils.timing import set_active_report
from start_green_stay_green.utils.timing import step_timer
from start_green_stay_green.utils.yaml_merge import merge_precommit_configs

# Version information
__version__ = "1.0.0"

# Constants
MAX_PROJECT_NAME_LENGTH = 100

# Generic return type for the orchestrator-close coroutine wrapper.
_R = TypeVar("_R")

# Create Typer app with rich markup enabled
app = typer.Typer(
    name="start-green-stay-green",
    help=(
        "Generate quality-controlled, AI-ready repositories "
        "with enterprise-grade standards."
    ),
    add_completion=False,
    rich_markup_mode="rich",
)

# Rich console for formatted output
console = Console()

# Global options
verbose_option = Annotated[
    bool,
    typer.Option(
        "--verbose",
        "-v",
        help="Enable verbose output with detailed information.",
    ),
]

quiet_option = Annotated[
    bool,
    typer.Option(
        "--quiet",
        "-q",
        help="Suppress non-essential output.",
    ),
]

config_file_option = Annotated[
    Path | None,
    typer.Option(
        "--config",
        "--config-file",
        help="Path to configuration file (YAML or TOML).",
        exists=False,
    ),
]


def get_version() -> str:
    """Get the version string for Start Green Stay Green.

    Returns:
        Version string in semantic versioning format.
    """
    return __version__


def load_config_file(config_path: Path) -> dict[str, str]:
    """Load configuration from YAML or TOML file.

    Args:
        config_path: Path to configuration file.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config file format is invalid.
    """
    if not config_path.exists():
        msg = f"Configuration file not found: {config_path}"
        raise FileNotFoundError(msg)

    # Implementation will be added in Issue 4.2
    return {}


def _validate_options(verbose: bool, quiet: bool) -> None:  # noqa: FBT001
    """Validate that verbose and quiet are mutually exclusive.

    Args:
        verbose: Verbose mode flag.
        quiet: Quiet mode flag.

    Raises:
        typer.Exit: If both verbose and quiet are True.
    """
    if verbose and quiet:
        console.print(
            "[red]Error:[/red] --verbose and --quiet are mutually exclusive.",
            style="bold",
        )
        raise typer.Exit(code=1)


def _load_config_if_specified(
    config: Path | None,
    verbose: bool,  # noqa: FBT001
) -> None:
    """Load configuration file if specified.

    Args:
        config: Path to configuration file (or None).
        verbose: Whether to show verbose output.

    Raises:
        typer.Exit: If config file not found.
    """
    if config:
        try:
            load_config_file(config)
            if verbose:
                console.print(f"[dim]Loaded configuration from {config}[/dim]")
        except FileNotFoundError as e:
            console.print(f"[red]Error:[/red] {e}", style="bold")
            raise typer.Exit(code=1) from e


@app.callback()
def main(
    verbose: verbose_option = False,  # noqa: FBT002
    quiet: quiet_option = False,  # noqa: FBT002
    config: config_file_option = None,
) -> None:
    """Start Green Stay Green - Generate quality-controlled, AI-ready repositories.

    A meta-tool for scaffolding new software projects with enterprise-grade
    quality controls pre-configured.

    Args:
        verbose: Enable verbose output.
        quiet: Suppress non-essential output.
        config: Path to configuration file.
    """
    _validate_options(verbose, quiet)
    _load_config_if_specified(config, verbose)


@app.command()
def version(
    verbose: verbose_option = False,  # noqa: FBT002
) -> None:
    """Display version information.

    Shows the current version of Start Green Stay Green.

    Args:
        verbose: Show additional version details.
    """
    version_str = get_version()

    if verbose:
        # Verbose version output with details
        console.print(
            Panel(
                f"[bold cyan]Start Green Stay Green[/bold cyan]\n"
                f"Version: [bold]{version_str}[/bold]\n"
                f"Python: {sys.version.split()[0]}\n"
                f"Platform: {sys.platform}",
                title="Version Information",
                border_style="cyan",
            )
        )
    else:
        # Simple version output
        console.print(f"[bold cyan]Start Green Stay Green v{version_str}[/bold cyan]")


def _validate_project_name(name: str) -> None:
    """Validate project name format.

    Args:
        name: Project name to validate.

    Raises:
        typer.BadParameter: If project name is invalid.
    """
    # Only allow alphanumeric, hyphens, underscores
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        msg = (
            f"Invalid project name: {name}. "
            "Only letters, numbers, hyphens, and underscores are allowed."
        )
        raise typer.BadParameter(msg)

    if len(name) > MAX_PROJECT_NAME_LENGTH:
        msg = (
            f"Project name too long: {len(name)} characters "
            f"(max {MAX_PROJECT_NAME_LENGTH})"
        )
        raise typer.BadParameter(msg)

    if name.startswith(("-", "_")):
        msg = f"Project name cannot start with '{name[0]}'"
        raise typer.BadParameter(msg)

    # Check Windows reserved names
    reserved_names = {
        "con",
        "prn",
        "aux",
        "nul",
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
    }

    if name.lower() in reserved_names:
        msg = f"Invalid project name: '{name}'. This is a reserved system name."
        raise typer.BadParameter(msg)


def _validate_output_dir(output_dir: Path | None) -> Path:
    """Validate output directory is safe from path traversal.

    Args:
        output_dir: User-provided output directory (or None for CWD).

    Returns:
        Validated and resolved Path.

    Raises:
        typer.BadParameter: If path traversal detected.
    """
    if output_dir is None:
        return Path.cwd()

    # Resolve to absolute path to eliminate any .. sequences
    return output_dir.resolve()


def _load_config_data(config: Path | None) -> dict[str, str]:
    """Load configuration data from file if specified.

    Args:
        config: Configuration file path or None.

    Returns:
        Configuration dictionary (empty if no config file).

    Raises:
        typer.Exit: If config file not found.
    """
    if not config:
        return {}

    try:
        config_data = load_config_file(config)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        raise typer.Exit(code=1) from e
    else:
        console.print(f"[dim]Loaded configuration from {config}[/dim]")
        return config_data


def _validate_and_prepare_paths(
    project_name: str,
    output_dir: Path | None,
) -> tuple[Path, Path]:
    """Validate project name and output directory, return validated paths.

    Args:
        project_name: Name of the project to validate.
        output_dir: User-provided output directory (or None for CWD).

    Returns:
        Tuple of (target_output_dir, project_path).

    Raises:
        typer.Exit: If validation fails.
    """
    # Validate both project name and output directory
    _validate_project_name(project_name)
    target_output_dir = _validate_output_dir(output_dir)

    # Determine project path
    project_path = target_output_dir / project_name

    # Path traversal guard: verify project stays within output directory
    if not str(project_path.resolve()).startswith(str(target_output_dir.resolve())):
        msg = "Project path escapes output directory"
        raise typer.BadParameter(msg)

    return target_output_dir, project_path


def _resolve_parameter(
    param_value: str | None,
    config_data: dict[str, str],
    config_key: str,
    param_name: str,
    *,
    no_interactive: bool,
) -> str:
    """Resolve parameter from args, config, or interactive prompt.

    Args:
        param_value: Parameter value from command line args.
        config_data: Configuration data from file.
        config_key: Key to look up in config_data.
        param_name: Display name for error/prompt messages.
        no_interactive: Whether running in non-interactive mode.

    Returns:
        Resolved parameter value.

    Raises:
        typer.Exit: If parameter missing in non-interactive mode.
    """
    # Try command line argument first
    if param_value:
        return param_value

    # Try config file
    config_value = config_data.get(config_key)
    if config_value:
        return config_value

    # Interactive prompt as fallback
    if no_interactive:
        console.print(
            f"[red]Error:[/red] --{param_name.replace(' ', '-')} "
            "required in non-interactive mode.",
            style="bold",
        )
        raise typer.Exit(code=1)

    return str(typer.prompt(param_name))


def _show_dry_run_preview(
    project_name: str,
    language: str,
    project_path: Path,
) -> None:
    """Display dry-run preview of what would be generated.

    Args:
        project_name: Name of the project.
        language: Programming language.
        project_path: Path where project would be created.
    """
    console.print("[bold yellow]Dry Run Mode[/bold yellow] - Preview only\n")
    console.print(f"Project: [cyan]{project_name}[/cyan]")
    console.print(f"Language: [cyan]{language}[/cyan]")
    console.print(f"Output: [cyan]{project_path}[/cyan]\n")
    console.print("Would generate:")
    console.print("  - CI/CD pipeline")
    console.print("  - Pre-commit hooks")
    console.print("  - Quality scripts")
    console.print("  - Skills")
    console.print("  - Subagent profiles")
    console.print("  - CLAUDE.md")
    console.print("  - GitHub Actions (AI review)")
    console.print("  - Architecture enforcement")


def _prompt_for_api_key() -> str | None:
    """Interactively prompt user for API key and optionally save to keyring.

    Returns:
        API key string if provided, None if user declined.
    """
    console.print("\n[yellow]No API key found.[/yellow]")
    console.print("AI-powered features require a Claude API key.")
    console.print("Get your key at: https://console.anthropic.com/")

    if not typer.confirm("\nWould you like to enter your API key now?"):
        return None

    api_key: str = typer.prompt("API Key", hide_input=True)

    # Offer to save to keyring
    if typer.confirm("Save to OS keyring for future use?"):
        if store_api_key_in_keyring(api_key):
            console.print("[green]✓[/green] API key saved to keyring")
        else:
            console.print(
                "[yellow]![/yellow] Failed to save to keyring "
                "(you'll need to provide it again next time)"
            )

    return api_key


def _warn_if_cli_api_key(source: str) -> None:
    """Warn user if API key was provided via CLI argument."""
    if source == "command line":
        console.print(
            "[yellow]Warning:[/yellow] --api-key is visible in the "
            "process list. Use ANTHROPIC_API_KEY env var or keyring "
            "instead.",
            style="bold",
        )


def _lazy_api_key_sources(
    api_key_arg: str | None,
) -> Generator[tuple[str | None, str]]:
    """Yield API key sources lazily to avoid unnecessary keychain prompts.

    Each source is only evaluated when iterated, so keyring is never
    accessed if an earlier source provides the key.

    Args:
        api_key_arg: API key from command line argument.

    Yields:
        (key_or_none, source_name) tuples.
    """
    yield api_key_arg, "command line"
    yield get_api_key_from_keyring(), "keyring"
    yield os.getenv("ANTHROPIC_API_KEY"), "environment variable"


def _get_api_key_with_source(
    api_key_arg: str | None,
    *,
    no_interactive: bool,
) -> tuple[str, str] | tuple[None, None]:
    """Get API key from the first available source.

    Returns:
        (api_key, source) tuple, or (None, None) if not found.
    """
    for key, source in _lazy_api_key_sources(api_key_arg):
        if key:
            _warn_if_cli_api_key(source)
            return key, source

    if not no_interactive:
        interactive_key = _prompt_for_api_key()
        if interactive_key:
            return interactive_key, "interactive prompt"

    return None, None


def _initialize_orchestrator(
    api_key_arg: str | None = None,
    *,
    no_interactive: bool = False,
) -> AIOrchestrator | None:
    """Initialize AI orchestrator with optional API key.

    Args:
        api_key_arg: API key from CLI argument.
        no_interactive: Disable interactive prompts.

    Returns:
        AIOrchestrator instance if API key found, None otherwise.
    """
    api_key, source = _get_api_key_with_source(
        api_key_arg, no_interactive=no_interactive
    )

    if not api_key:
        return None

    try:
        orchestrator = AIOrchestrator(api_key=api_key)
        console.print(f"[green]✓[/green] AI features enabled (from {source})")
        return orchestrator  # noqa: TRY300  # Happy path return is clearer
    except ValueError as e:
        console.print(f"[red]Error:[/red] Invalid API key: {e}", style="bold")
        return None


def _copy_reference_skills(
    target_dir: Path,
    file_writer: FileWriter | None = None,
) -> None:
    """Copy reference skills to target directory.

    This is a temporary implementation that directly copies reference skills
    without AI-powered tuning. Full AI integration (async + AIOrchestrator)
    will be added in Issue #115.

    Args:
        target_dir: Target directory for skills (.claude/skills/).
        file_writer: Optional FileWriter for additive behavior.

    Raises:
        FileNotFoundError: If reference skills directory not found.
    """
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy each required skill directory
    for skill_name in REQUIRED_SKILLS:
        source_dir = REFERENCE_SKILLS_DIR / skill_name
        if not source_dir.is_dir():
            msg = f"Reference skill not found: {skill_name}"
            raise FileNotFoundError(msg)

        target_skill_dir = target_dir / skill_name
        if file_writer is not None:
            file_writer.copy_tree(source_dir, target_skill_dir)
        else:
            shutil.copytree(source_dir, target_skill_dir, dirs_exist_ok=True)


def _copy_reference_subagents(
    target_dir: Path,
    file_writer: FileWriter | None = None,
) -> None:
    """Copy reference subagent profiles to ``target_dir`` verbatim.

    Used by the no-API path of ``_generate_subagents_step``. Each
    required agent in ``REQUIRED_AGENTS`` is copied from the source
    file declared in the mapping to ``<agent_name>.md`` so the file
    layout matches what the AI-tuned path produces.

    Args:
        target_dir: Destination ``.claude/agents`` directory.
        file_writer: Optional ``FileWriter`` for additive behaviour
            (handles --force / --interactive conflict resolution).

    Raises:
        FileNotFoundError: If a required reference agent is missing.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    for agent_name, source_file in REQUIRED_AGENTS.items():
        source_path = REFERENCE_AGENTS_DIR / source_file
        if not source_path.exists():
            msg = f"Reference subagent not found: {source_file}"
            raise FileNotFoundError(msg)
        target_path = target_dir / f"{agent_name}.md"
        # Pin UTF-8 explicitly: agent prose contains characters
        # (✓, ⊘, em-dashes) that would corrupt under a non-UTF-8 locale
        # default on Windows.
        content = source_path.read_text(encoding="utf-8")
        if file_writer is not None:
            file_writer.write_file(target_path, content)
        else:
            target_path.write_text(content, encoding="utf-8")


@contextmanager
def _maybe_collect_timing(
    timing_json: Path | None,
) -> Generator[None, None, None]:
    """Optionally install a :class:`TimingReport` for the wrapped block.

    When ``timing_json`` is ``None`` the manager is a no-op; otherwise a
    fresh report is installed as the active collector for the duration of
    the block and written to disk on exit (success or failure).
    """
    if timing_json is None:
        yield
        return
    report = TimingReport()
    set_active_report(report)
    try:
        yield
    finally:
        timing_json.parent.mkdir(parents=True, exist_ok=True)
        report.write_json(timing_json)
        set_active_report(None)


async def _run_with_orchestrator_close(
    orchestrator: AIOrchestrator,
    coro: Coroutine[Any, Any, _R],
) -> _R:
    """Await ``coro`` and release the orchestrator's async client on exit.

    ``AIOrchestrator`` lazily allocates an :class:`AsyncAnthropic` (and
    therefore an httpx pool) when ``generate_async`` is first invoked.
    Without an explicit ``aclose`` the pool would leak across calls in
    long-lived contexts. ``aclose`` is idempotent, so this is safe even
    when the async client was never created.
    """
    try:
        return await coro
    finally:
        await orchestrator.aclose()


def _generate_structure_step(
    project_path: Path,
    project_name: str,
    language: str,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate source code structure."""
    with step_timer("structure"), console.status("Generating source structure..."):
        config = StructureConfig(
            project_name=project_name,
            language=language,
            package_name=project_name.replace("-", "_"),
        )
        generator = StructureGenerator(project_path, config, file_writer=file_writer)
        generator.generate()
    console.print("[green]✓[/green] Generated source structure")


def _generate_dependencies_step(
    project_path: Path,
    project_name: str,
    language: str,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate dependencies files."""
    with step_timer("dependencies"), console.status("Generating dependencies..."):
        config = DependencyConfig(
            project_name=project_name,
            language=language,
            package_name=project_name.replace("-", "_"),
        )
        generator = DependenciesGenerator(project_path, config, file_writer=file_writer)
        generator.generate()
    console.print("[green]✓[/green] Generated dependencies")


def _generate_tests_step(
    project_path: Path,
    project_name: str,
    language: str,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate tests directory."""
    with step_timer("tests"), console.status("Generating tests..."):
        config = TestsConfig(
            project_name=project_name,
            language=language,
            package_name=project_name.replace("-", "_"),
        )
        generator = TestsGenerator(project_path, config, file_writer=file_writer)
        generator.generate()
    console.print("[green]✓[/green] Generated tests")


def _generate_readme_step(
    project_path: Path,
    project_name: str,
    language: str,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate README.md."""
    with step_timer("readme"), console.status("Generating README..."):
        config = ReadmeConfig(
            project_name=project_name,
            language=language,
            package_name=project_name.replace("-", "_"),
        )
        generator = ReadmeGenerator(project_path, config, file_writer=file_writer)
        generator.generate()
    console.print("[green]✓[/green] Generated README")


def _scripts_dir_has_other_language(scripts_dir: Path, language: str) -> bool:
    """Check if scripts/ already has scripts from a different language.

    Detects this by checking for known language-specific script content
    in existing test.sh or check-all.sh files.

    Args:
        scripts_dir: Path to scripts/ directory.
        language: Current language being generated.

    Returns:
        True if scripts from a different language are present.
    """
    marker_file = scripts_dir / "test.sh"
    if not marker_file.exists():
        return False

    content = marker_file.read_text(encoding="utf-8")
    language_markers = {
        "python": "pytest",
        "typescript": "jest",
        "go": "go test",
        "rust": "cargo test",
        "java": "mvn test",
        "csharp": "dotnet test",
        "ruby": "rspec",
    }
    current_marker = language_markers.get(language, "")
    return current_marker != "" and current_marker not in content


def _generate_scripts_step(
    project_path: Path,
    project_name: str,
    language: str,
    file_writer: FileWriter | None = None,
    subdirectory: str | None = None,
) -> None:
    """Generate quality scripts.

    If scripts/ already contains scripts from a different language,
    automatically uses scripts/{language}/ subdirectory to avoid conflicts.

    Args:
        project_path: Project root directory.
        project_name: Name of the project.
        language: Programming language for scripts.
        file_writer: Optional FileWriter for additive behavior.
        subdirectory: If set, write to scripts/{subdirectory}/ instead
            of scripts/. Used for multi-language projects.
    """
    scripts_dir = project_path / "scripts"
    if subdirectory:
        scripts_dir = scripts_dir / subdirectory
    elif _scripts_dir_has_other_language(scripts_dir, language):
        scripts_dir = scripts_dir / language

    with step_timer("scripts"), console.status(f"Generating {language} scripts..."):
        scripts_config = ScriptConfig(
            language=language,
            package_name=project_name.replace("-", "_"),
        )
        scripts_generator = ScriptsGenerator(
            output_dir=scripts_dir,
            config=scripts_config,
            file_writer=file_writer,
        )
        scripts_generator.generate()
    console.print(f"[green]✓[/green] Generated {language} scripts")


def _generate_precommit_step(
    project_path: Path,
    project_name: str,
    language: str,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate pre-commit configuration, merging with existing if present."""
    with step_timer("precommit"), console.status("Generating pre-commit config..."):
        precommit_config = GenerationConfig(
            project_name=project_name,
            language=language,
            language_config={},
        )
        precommit_generator = PreCommitGenerator(orchestrator=None)
        precommit_result = precommit_generator.generate(precommit_config)
        precommit_file = project_path / ".pre-commit-config.yaml"
        generated_content = precommit_result["content"]

        _write_precommit_config(precommit_file, generated_content, file_writer)
    console.print("[green]✓[/green] Generated pre-commit config")


def _write_precommit_config(
    precommit_file: Path,
    generated_content: str,
    file_writer: FileWriter | None,
) -> None:
    """Write pre-commit config, merging with existing if appropriate.

    Args:
        precommit_file: Path to .pre-commit-config.yaml.
        generated_content: Generated YAML content.
        file_writer: Optional FileWriter for conflict resolution.
    """
    if file_writer is None:
        precommit_file.write_text(generated_content, encoding="utf-8")
        return

    if not precommit_file.exists() or file_writer.is_force:
        file_writer.write_file(precommit_file, generated_content)
        return

    _merge_and_write_precommit(precommit_file, generated_content, file_writer)


def _merge_and_write_precommit(
    precommit_file: Path,
    generated_content: str,
    file_writer: FileWriter,
) -> None:
    """Merge generated pre-commit config into existing file.

    Args:
        precommit_file: Path to existing .pre-commit-config.yaml.
        generated_content: Generated YAML content to merge.
        file_writer: FileWriter for stats tracking.
    """
    existing_content = precommit_file.read_text(encoding="utf-8")
    try:
        merged, added, kept = merge_precommit_configs(
            existing_content, generated_content
        )
    except (ValueError, TypeError) as e:
        console.print(
            f"  [yellow]WARN[/yellow] Cannot merge .pre-commit-config.yaml: {e}"
        )
        console.print("  [yellow]SKIP[/yellow] .pre-commit-config.yaml (kept existing)")
        file_writer.skipped += 1
        return

    precommit_file.write_text(merged, encoding="utf-8")
    file_writer.overwritten += 1
    console.print(
        f"  [blue]MERGE[/blue] .pre-commit-config.yaml "
        f"(added {added} repos, kept {kept} existing)"
    )


def _generate_skills_step(
    project_path: Path,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate Claude skills."""
    with step_timer("skills"), console.status("Generating skills..."):
        skills_dir = project_path / ".claude" / "skills"
        _copy_reference_skills(skills_dir, file_writer=file_writer)
    console.print("[green]✓[/green] Generated skills")


def _generate_ci_step(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate the CI pipeline.

    Always runs the deterministic template path so a project is never
    missing CI just because the user has no API key. ``orchestrator`` is
    only used to opt into the legacy AI-tuned path for backward
    compatibility. ``project_name`` is forwarded to the template
    renderer so any ``<<% project_name %>>`` placeholder lands with
    the real value rather than the empty string.
    """
    with step_timer("ci"), console.status("Generating CI pipeline..."):
        ci_generator = CIGenerator(
            orchestrator,
            language,
            project_name=project_name,
        )
        workflow = ci_generator.generate_workflow()
        workflows_dir = project_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        ci_file = workflows_dir / "ci.yml"
        if file_writer is not None:
            file_writer.write_file(ci_file, workflow.content)
        else:
            ci_file.write_text(workflow.content, encoding="utf-8")
    console.print("[green]✓[/green] Generated CI pipeline")


def _generate_review_step(
    project_path: Path,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate the GitHub Actions code review workflow.

    The generator is fully template-based — no orchestrator parameter
    needed. (The orchestrator was previously passed but never used; it
    has been dropped from this private helper, so the historical
    ``orchestrator`` argument is gone entirely.)
    """
    with step_timer("review"), console.status("Generating GitHub Actions review..."):
        review_generator = GitHubActionsReviewGenerator()
        review_result = review_generator.generate()
        workflows_dir = project_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        workflow_file = workflows_dir / "code-review.yml"
        if file_writer is not None:
            file_writer.write_file(workflow_file, review_result["workflow_content"])
        else:
            workflow_file.write_text(
                review_result["workflow_content"], encoding="utf-8"
            )
    console.print("[green]✓[/green] Generated GitHub Actions review")


def _generate_claude_md_step(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate CLAUDE.md.

    Always runs: with no orchestrator the deterministic baseline is
    rendered (Phase 1 of the optimization roadmap); with one, the legacy
    AI-tuned generator is used.
    """
    with step_timer("claude_md"), console.status("Generating CLAUDE.md..."):
        claude_md_generator = ClaudeMdGenerator(orchestrator)
        project_config = {
            "project_name": project_name,
            "language": language,
            "scripts": [
                "check-all.sh",
                "test.sh",
                "lint.sh",
                "format.sh",
                "security.sh",
                "mutation.sh",
            ],
            "skills": REQUIRED_SKILLS.copy(),
        }
        claude_md_result = claude_md_generator.generate(project_config)
        claude_md_file = project_path / "CLAUDE.md"
        if file_writer is not None:
            file_writer.write_file(claude_md_file, claude_md_result.content)
        else:
            claude_md_file.write_text(claude_md_result.content, encoding="utf-8")
    console.print("[green]✓[/green] Generated CLAUDE.md")


def _generate_architecture_step(
    project_path: Path,
    project_name: str,
    language: str,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate architecture rules.

    Architecture configuration is fully deterministic (import-linter for
    Python, dependency-cruiser for TypeScript). Runs regardless of API
    key availability; only Python and TypeScript projects produce output.
    The previous ``orchestrator`` argument was unused and has been
    removed from this private helper.
    """
    if language not in {"python", "typescript"}:
        # The generator only supports these two; surface a dim info line
        # so users understand why no architecture rules were generated
        # for, e.g., a Go or Rust project rather than seeing silence.
        console.print(
            f"[dim]Architecture rules unavailable for {language} "
            "(supported: python, typescript)[/dim]"
        )
        return

    arch_dir = project_path / "plans" / "architecture"
    if file_writer is not None and file_writer.skip_existing_dir(arch_dir):
        console.print("[green]✓[/green] Architecture rules (preserved existing)")
        return

    with step_timer("architecture"), console.status("Generating architecture rules..."):
        arch_generator = ArchitectureEnforcementGenerator(output_dir=arch_dir)
        arch_generator.generate(language=language, project_name=project_name)
    console.print("[green]✓[/green] Generated architecture rules")


def _generate_subagents_step(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate subagents.

    With an orchestrator: tunes each reference subagent for the target
    project (currently in parallel, see Phase 2). Without an orchestrator:
    falls back to copying the reference subagents verbatim so a project
    is never missing its agent profiles.
    """
    subagents_output_dir = project_path / ".claude" / "agents"
    subagents_output_dir.mkdir(parents=True, exist_ok=True)

    if orchestrator is None:
        with step_timer("subagents"), console.status("Copying reference subagents..."):
            _copy_reference_subagents(subagents_output_dir, file_writer=file_writer)
        console.print("[green]✓[/green] Copied reference subagents")
        return

    with step_timer("subagents"), console.status("Generating subagents..."):
        subagents_generator = SubagentsGenerator(orchestrator)
        project_config_for_agents = (
            f"Project: {project_name}, "
            f"Language: {language}, "
            f"Type: quality-control-tool"
        )
        # ``_run_with_orchestrator_close`` guarantees the lazily-created
        # ``AsyncAnthropic`` client is released on the way out, even if
        # one of the parallel tunings raises.
        results = run_async(
            _run_with_orchestrator_close(
                orchestrator,
                subagents_generator.generate_all_agents(project_config_for_agents),
            )
        )
        for agent_name, result in results.items():
            agent_file = subagents_output_dir / f"{agent_name}.md"
            if file_writer is not None:
                file_writer.write_file(agent_file, result.content)
            else:
                agent_file.write_text(result.content, encoding="utf-8")
    console.print("[green]✓[/green] Generated subagents")


def _generate_metrics_dashboard_step(
    project_path: Path,
    project_name: str,
    language: str,
) -> None:
    """Generate live metrics dashboard and workflow."""
    with step_timer("metrics"), console.status("Generating metrics dashboard..."):
        config = MetricsGenerationConfig(
            language=language,
            project_name=project_name,
            coverage_threshold=90,
            branch_coverage_threshold=85,
            mutation_threshold=80,
            complexity_threshold=10,
            doc_coverage_threshold=95,
            enable_dashboard=True,
            enable_badges=True,
        )

        generator = MetricsGenerator(None, config)

        docs_dir = project_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        generator.write_dashboard(docs_dir)
        initial_metrics_path = docs_dir / "metrics.json"
        initial_metrics = {
            "timestamp": datetime.now(UTC).isoformat(),
            "project": project_name,
            "thresholds": {
                "coverage": config.coverage_threshold,
                "branch_coverage": config.branch_coverage_threshold,
                "mutation_score": config.mutation_threshold,
                "complexity": config.complexity_threshold,
                "docs_coverage": config.doc_coverage_threshold,
                "security_issues": 0,
            },
            "metrics": {
                "coverage": 0.0,
                "coverage_status": "fail",
                "branch_coverage": 0.0,
                "branch_coverage_status": "fail",
                "mutation_score": 0.0,
                "mutation_status": "fail",
                "complexity_avg": 0.0,
                "complexity_status": "pass",
                "docs_coverage": 0.0,
                "docs_status": "fail",
                "security_issues": 0,
                "security_status": "pass",
            },
        }
        initial_metrics_path.write_text(
            json.dumps(initial_metrics, indent=2),
            encoding="utf-8",
        )

        workflows_dir = project_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        sgsg_root = Path(__file__).parent.parent
        sgsg_workflow = sgsg_root / ".github" / "workflows" / "metrics.yml"
        missing_workflow = False
        missing_script = False
        if sgsg_workflow.exists():
            target_workflow = workflows_dir / "metrics.yml"
            shutil.copy(sgsg_workflow, target_workflow)
            workflow_content = target_workflow.read_text(encoding="utf-8")
            workflow_content = workflow_content.replace(
                "start-green-stay-green", project_name
            )
            target_workflow.write_text(workflow_content, encoding="utf-8")
        else:
            missing_workflow = True

        scripts_dir = project_path / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        sgsg_script = sgsg_root / "scripts" / "collect_metrics.py"
        if sgsg_script.exists():
            shutil.copy(
                sgsg_script,
                scripts_dir / "collect_metrics.py",
            )
        else:
            missing_script = True

    console.print("[green]✓[/green] Generated metrics dashboard")
    if missing_workflow:
        console.print(
            "[yellow]Warning:[/yellow] Metrics workflow template not found. "
            "You'll need to create .github/workflows/metrics.yml manually."
        )
    if missing_script:
        console.print(
            "[yellow]Warning:[/yellow] Metrics collection script not found. "
            "You'll need to create scripts/collect_metrics.py manually."
        )


def _generate_pass2_polish(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    file_writer: FileWriter | None = None,
) -> None:
    """Run Pass 2 of the optimization roadmap's two-pass init model.

    Generates the artifacts whose output is *enhanced* by an
    :class:`AIOrchestrator` when one is available. After Phase 1 every
    one of these has a deterministic baseline path too, so the function
    runs unconditionally; the orchestrator is what flips each step
    between "render template" and "AI-tune the template". When
    ``orchestrator`` is ``None`` (``--offline`` / ``--no-enhance`` /
    no API key), every step still runs and produces a complete project
    via the deterministic path.

    The roadmap (plans/2026-05-03-claude-init-optimization-roadmap.md)
    calls this Pass 2 to distinguish it from Pass 1's per-language
    scaffold steps.
    """
    _generate_ci_step(project_path, project_name, language, orchestrator, file_writer)
    _generate_review_step(project_path, file_writer)
    _generate_claude_md_step(
        project_path, project_name, language, orchestrator, file_writer
    )
    _generate_architecture_step(project_path, project_name, language, file_writer)
    _generate_subagents_step(
        project_path, project_name, language, orchestrator, file_writer
    )


def _generate_project_files(
    project_path: Path,
    project_name: str,
    languages: tuple[str, ...],
    orchestrator: AIOrchestrator | None,
    file_writer: FileWriter,
) -> None:
    """Generate all project files with progress indicators.

    For multi-language projects, per-language generators (structure, deps,
    tests, scripts, precommit) run once per language. Shared generators
    (skills, AI features) run once. Pre-commit configs are merged across
    languages via the YAML merge utility.

    Args:
        project_path: Path where project will be created.
        project_name: Name of the project.
        languages: Tuple of programming languages to generate for.
        orchestrator: Optional AI orchestrator for AI-powered features.
            None indicates fallback to template mode.
        file_writer: FileWriter instance for safe file operations.

    Raises:
        typer.Exit: If generation fails.
    """
    primary_language = languages[0]

    multi_language = len(languages) > 1

    try:
        # Per-language generation
        for language in languages:
            _generate_structure_step(project_path, project_name, language, file_writer)
            _generate_dependencies_step(
                project_path, project_name, language, file_writer
            )
            _generate_tests_step(project_path, project_name, language, file_writer)
            _generate_scripts_step(
                project_path,
                project_name,
                language,
                file_writer,
                subdirectory=language if multi_language else None,
            )
            _generate_precommit_step(project_path, project_name, language, file_writer)

        # Shared steps (run once, using primary language)
        _generate_readme_step(project_path, project_name, primary_language, file_writer)
        _generate_skills_step(project_path, file_writer)

        # Pass 2 of the two-pass init model: AI-tunable artifacts.
        # Uses the primary language for cross-language projects.
        try:
            _generate_pass2_polish(
                project_path,
                project_name,
                primary_language,
                orchestrator,
                file_writer,
            )
        except (AIGenerationError, OSError) as ai_err:
            console.print(
                f"\n[yellow]Warning:[/yellow] AI-powered generation failed: {ai_err}"
            )
            console.print(
                "[yellow]⊘[/yellow] Project generated without AI features "
                "(CI, CLAUDE.md, architecture rules, subagents)."
            )
            console.print(
                "  Re-run with a valid API key to generate these artifacts.\n"
            )

        # Print summary stats
        console.print(f"\n[bold]{file_writer.summary()}[/bold]")
    except Exception as e:
        console.print(
            f"\n[red]Error:[/red] Generation failed: {e}",
            style="bold",
        )
        raise typer.Exit(code=1) from e


_LANG_SETUP_STEPS: dict[str, list[str]] = {
    "python": [
        "python -m venv .venv",
        "source .venv/bin/activate",
        "pip install -r requirements.txt -r requirements-dev.txt",
    ],
    "typescript": ["npm install"],
    "go": ["go mod download"],
    "rust": ["cargo build"],
}


def _get_setup_instructions(languages: Sequence[str], project_path: Path) -> list[str]:
    """Return language-specific setup commands for a generated project.

    For multi-language projects, language-specific steps are concatenated
    in the order the languages appear. Shared steps (cd, pre-commit
    install, check-all) are not duplicated.

    Args:
        languages: Ordered sequence of programming languages (python,
            typescript, go, rust, etc.). May be empty for a sensible
            default.
        project_path: Path to the generated project directory.

    Returns:
        Ordered list of shell commands to set up and verify the project.
    """
    cd = f"cd {shlex.quote(str(project_path))}"
    common_tail = ["pre-commit install", "./scripts/check-all.sh"]

    middle: list[str] = []
    for lang in dict.fromkeys(languages):
        middle.extend(_LANG_SETUP_STEPS.get(lang, []))

    return [cd, *middle, *common_tail]


def _finalize_init(
    project_path: Path,
    project_name: str,
    languages: Sequence[str],
    *,
    enable_live_dashboard: bool = False,
) -> None:
    """Generate optional dashboard and print success message.

    Args:
        project_path: Path to the generated project.
        project_name: Name of the project.
        languages: Ordered sequence of programming languages for the
            project. The first is treated as the primary language for
            features that only support one (e.g. dashboard generation).
        enable_live_dashboard: Whether to generate live metrics dashboard.
    """
    if enable_live_dashboard:
        primary_language = languages[0] if languages else ""
        _generate_metrics_dashboard_step(project_path, project_name, primary_language)

    console.print(
        f"\n[green]✓[/green] Project generated successfully at: {project_path}"
    )
    console.print("\nTo get started, run:")
    for cmd in _get_setup_instructions(languages, project_path):
        console.print(f"  {cmd}")
    console.print()
    if enable_live_dashboard:
        console.print(
            "[green]✓[/green] Live metrics dashboard enabled "
            "- configure GitHub Pages to deploy from /docs"
        )


def _split_language_values(language: list[str]) -> tuple[str, ...]:
    """Split comma-separated language values into individual languages.

    Args:
        language: List of language strings, possibly comma-separated.

    Returns:
        Tuple of individual language strings, stripped of whitespace.
    """
    return tuple(
        lang.strip() for item in language for lang in item.split(",") if lang.strip()
    )


def _resolve_language_param(
    language: list[str] | None,
    config_data: dict[str, str],
    *,
    no_interactive: bool,
) -> tuple[str, ...]:
    """Resolve language parameter from CLI args, config, or prompt.

    Args:
        language: Language list from CLI (None if not provided).
        config_data: Configuration data from file.
        no_interactive: Whether interactive prompts are disabled.

    Returns:
        Validated tuple of language strings.

    Raises:
        typer.Exit: If languages are invalid or missing in non-interactive mode.
    """
    if language:
        raw = _split_language_values(language)
    elif config_data.get("language"):
        raw = (config_data["language"],)
    elif no_interactive:
        console.print(
            "[red]Error:[/red] --language required in non-interactive mode.",
            style="bold",
        )
        raise typer.Exit(code=1)
    else:
        raw = (str(typer.prompt("Primary language")),)

    try:
        return _resolve_languages(raw)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        raise typer.Exit(code=1) from e


def _resolve_languages(languages: tuple[str, ...]) -> tuple[str, ...]:
    """Validate and deduplicate language list.

    Args:
        languages: Tuple of language strings from CLI.

    Returns:
        Deduplicated tuple of validated language strings.

    Raises:
        ValueError: If any language is unsupported or list is empty.
    """
    if not languages:
        msg = "At least one language must be specified"
        raise ValueError(msg)

    seen: set[str] = set()
    unique: list[str] = []
    for lang in languages:
        validate_language(lang)
        if lang not in seen:
            seen.add(lang)
            unique.append(lang)

    return tuple(unique)


def _validate_conflict_flags(
    force: bool,  # noqa: FBT001
    interactive: bool,  # noqa: FBT001
) -> None:
    """Validate that --force and --interactive are mutually exclusive.

    Args:
        force: Whether --force was passed.
        interactive: Whether --interactive was passed.

    Raises:
        typer.Exit: If both flags are set.
    """
    if force and interactive:
        console.print(
            "[red]Error:[/red] --force and --interactive are mutually exclusive.",
            style="bold",
        )
        raise typer.Exit(code=1)


def _resolve_pass2_orchestrator(
    *,
    api_key: str | None,
    offline: bool,
    no_enhance: bool,
    no_interactive: bool,
) -> AIOrchestrator | None:
    """Decide whether Pass 2 should run, and return the orchestrator if so.

    Encapsulates the three flags that interact to control Pass 2 of the
    two-pass init model so the ``init`` command stays at complexity
    grade A. The branches are deliberately mutually-exclusive (the
    validator guarantees this) so each one returns directly:

    * ``--offline`` → never resolve a key, never instantiate an
      orchestrator. Returns ``None`` and prints a dim status line so
      the user sees that Pass 1 alone is running.
    * ``--no-enhance`` → resolve the key (so it lands in the keyring
      / env / etc. for a future ``green enhance``) and then discard
      the orchestrator so Pass 2 is skipped this run.
    * Otherwise → resolve the key normally; if no key is available
      print the legacy "AI features disabled" instructions.
    """
    if offline:
        console.print(
            "[dim]Running in offline mode — Pass 1 only (no API calls).[/dim]"
        )
        return None

    orchestrator = _initialize_orchestrator(api_key, no_interactive=no_interactive)

    if no_enhance:
        # Always print *something* so the user knows --no-enhance had an
        # effect, regardless of whether a key was resolved. The two
        # paths differ in what the user can do next: with a key cached,
        # ``green enhance`` will pick it up; without, they need to set
        # ANTHROPIC_API_KEY first.
        if orchestrator is not None:
            console.print(
                "[dim]--no-enhance: skipping Pass 2; run `green enhance` "
                "later to add AI polish.[/dim]"
            )
        else:
            console.print(
                "[dim]--no-enhance: no API key found; Pass 2 skipped. "
                "Set ANTHROPIC_API_KEY before running `green enhance`.[/dim]"
            )
        return None

    if orchestrator is None:
        console.print("\n[yellow]![/yellow] AI features disabled")
        console.print("  - Skills: Using reference templates (no customization)")
        console.print("  - CI/Subagents/CLAUDE.md: Using default templates")
        console.print("\n  To enable AI features:")
        console.print("    1. Get API key: https://console.anthropic.com/")
        console.print("    2. Run: sgsg init --api-key YOUR_KEY")
        console.print("    3. Or: Set ANTHROPIC_API_KEY environment variable\n")
    return orchestrator


def _validate_pass2_flags(
    *,
    offline: bool,
    no_enhance: bool,
    api_key: str | None,
) -> None:
    """Validate the Pass 2 flag combinations introduced for the two-pass init.

    The flags interact in three ways the user might trip on:

    * ``--offline`` and ``--no-enhance`` are redundant when used together
      (both skip Pass 2). It is an error to combine them — the user
      almost certainly meant one or the other.
    * ``--offline`` with ``--api-key`` is contradictory (the user is
      both supplying a key and asking to never use it). Treated as an
      error to surface the mistake loudly.
    * ``--no-enhance`` with ``--api-key`` is fine — the key gets
      cached / kept available for a future ``green enhance`` (Phase 3b),
      it just is not used during this init.

    Args:
        offline: ``True`` if ``--offline`` was passed.
        no_enhance: ``True`` if ``--no-enhance`` was passed.
        api_key: The string value passed to ``--api-key``, or ``None``
            if the flag was omitted. Truthiness is what matters here:
            an empty string is treated the same as ``None``.

    Raises:
        typer.Exit: If a contradictory combination is detected.
    """
    if offline and no_enhance:
        console.print(
            "[red]Error:[/red] --offline and --no-enhance are redundant; "
            "pass only one.",
            style="bold",
        )
        raise typer.Exit(code=1)
    if offline and api_key:
        console.print(
            "[red]Error:[/red] --offline and --api-key are contradictory; "
            "drop --offline or omit --api-key.",
            style="bold",
        )
        raise typer.Exit(code=1)


@app.command()
def init(  # noqa: PLR0913
    project_name: Annotated[
        str | None,
        typer.Option(
            "--project-name",
            "-n",
            help="Name of the project to generate.",
        ),
    ] = None,
    language: Annotated[
        list[str] | None,
        typer.Option(
            "--language",
            "-l",
            help=(
                "Programming language(s). Repeat for multi-language projects: "
                f"-l python -l typescript. ({', '.join(SUPPORTED_LANGUAGES)})"
            ),
        ),
    ] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            "-o",
            help="Output directory for generated project.",
        ),
    ] = None,
    *,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Preview what would be generated without creating files.",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite all existing files without prompting.",
        ),
    ] = False,
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            help="Prompt per-file when conflicts exist (skip/overwrite/diff).",
        ),
    ] = False,
    no_interactive: Annotated[
        bool,
        typer.Option(
            "--no-interactive",
            help="Run in non-interactive mode (requires all options).",
        ),
    ] = False,
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            help=(
                "[DEPRECATED] API key is visible in process list. "
                "Use ANTHROPIC_API_KEY env var or keyring instead."
            ),
            hide_input=True,
        ),
    ] = None,
    offline: Annotated[
        bool,
        typer.Option(
            "--offline",
            help=(
                "Run only Pass 1 of the two-pass init: produce a complete "
                "project from deterministic templates. No API key is read, "
                "no network is used, no AI tuning is attempted. Equivalent "
                "to ``--no-enhance`` plus suppressing every API-key prompt."
            ),
        ),
    ] = False,
    no_enhance: Annotated[
        bool,
        typer.Option(
            "--no-enhance",
            help=(
                "Skip Pass 2 of the two-pass init (the AI-tuned polish over "
                "CLAUDE.md and subagents). Unlike ``--offline`` the API key "
                "resolution still runs, so a follow-up ``green enhance`` "
                "call (Phase 3b) can pick up where this one left off."
            ),
        ),
    ] = False,
    enable_live_dashboard: Annotated[
        bool,
        typer.Option(
            "--enable-live-dashboard",
            help="Generate live metrics dashboard with auto-updating workflow.",
        ),
    ] = False,
    timing_json: Annotated[
        Path | None,
        typer.Option(
            "--timing-json",
            help=(
                "Write a structured timing/telemetry report to PATH "
                "(JSON). No effect on default output."
            ),
        ),
    ] = None,
    config: config_file_option = None,
) -> None:
    """Initialize a new project with quality controls.

    Generates a complete project structure with CI/CD, quality checks,
    AI subagents, and documentation pre-configured.

    AI-powered features are optional and require a Claude API key.
    Without a key, the tool generates reference templates instead.

    Args:
        project_name: Name of the project.
        language: Primary programming language.
        output_dir: Output directory (defaults to current directory).
        dry_run: Preview mode without file creation.
        force: Overwrite all existing files without prompting.
        interactive: Prompt per-file for conflict resolution.
        no_interactive: Non-interactive mode.
        api_key: Optional Claude API key for AI features.
        offline: Skip API-key resolution and Pass 2 entirely; produces
            a complete project from deterministic templates only.
        no_enhance: Skip Pass 2 (AI tuning) but still resolve the API
            key for a future ``green enhance`` invocation.
        enable_live_dashboard: Generate live metrics dashboard with workflow.
        timing_json: Optional path to write a timing/telemetry JSON report.
        config: Configuration file path.

    Raises:
        typer.Exit: If validation fails or generation errors occur.
    """
    _validate_conflict_flags(force, interactive)
    _validate_pass2_flags(offline=offline, no_enhance=no_enhance, api_key=api_key)

    # Load configuration
    config_data = _load_config_data(config)

    # Resolve parameters from args, config, or interactive prompts
    resolved_project_name = _resolve_parameter(
        project_name,
        config_data,
        "project_name",
        "Project name",
        no_interactive=no_interactive,
    )
    resolved_languages = _resolve_language_param(
        language, config_data, no_interactive=no_interactive
    )

    # Validate project name and paths
    try:
        _target_output_dir, project_path = _validate_and_prepare_paths(
            resolved_project_name,
            output_dir,
        )
    except typer.BadParameter as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        sys.exit(1)

    # Handle dry-run mode (skip orchestrator initialization for preview)
    if dry_run:
        _show_dry_run_preview(
            resolved_project_name, ", ".join(resolved_languages), project_path
        )
        return

    orchestrator = _resolve_pass2_orchestrator(
        api_key=api_key,
        offline=offline,
        no_enhance=no_enhance,
        no_interactive=no_interactive,
    )

    # Create project directory
    project_path.mkdir(parents=True, exist_ok=True)

    # Create FileWriter with the chosen conflict resolution mode
    file_writer = FileWriter(
        project_root=project_path,
        force=force,
        interactive=interactive,
        console=console,
    )

    with _maybe_collect_timing(timing_json):
        _generate_project_files(
            project_path,
            resolved_project_name,
            resolved_languages,
            orchestrator,
            file_writer,
        )
        _finalize_init(
            project_path,
            resolved_project_name,
            resolved_languages,
            enable_live_dashboard=enable_live_dashboard,
        )


_LANGUAGE_PROBES: tuple[tuple[str, str], ...] = (
    # (filename relative to project root, language). The first match wins.
    ("pyproject.toml", "python"),
    ("requirements.txt", "python"),
    ("package.json", "typescript"),
    ("go.mod", "go"),
    ("Cargo.toml", "rust"),
    ("pom.xml", "java"),
    ("build.gradle", "java"),
    ("Gemfile", "ruby"),
    ("composer.json", "php"),
    ("Package.swift", "swift"),
)

# Pattern for the H1 line in a generated CLAUDE.md file.
# ``# Claude Code Project Context: <project-name>``
_CLAUDE_MD_TITLE = re.compile(
    r"^#\s+Claude Code Project Context:\s+(?P<name>.+?)\s*$",
    re.MULTILINE,
)

# Targets the ``green enhance`` command knows how to re-tune. Order
# matches the on-disk layout users expect to see touched.
_ENHANCE_TARGETS: tuple[str, ...] = ("claude-md", "subagents")


def _detect_project_name(project_path: Path) -> str | None:
    """Return the project name parsed out of an existing CLAUDE.md.

    The init-generated CLAUDE.md baseline starts with
    ``# Claude Code Project Context: <name>``. Reading the first line
    matching that pattern is more reliable than guessing from the
    directory name (the user may have renamed the directory) or from
    ``pyproject.toml`` (project may be multi-language).

    Returns ``None`` if CLAUDE.md is missing or doesn't have the
    expected H1 — in which case the caller must require ``-n``.
    """
    claude_md = project_path / "CLAUDE.md"
    if not claude_md.is_file():
        return None
    try:
        content = claude_md.read_text(encoding="utf-8")
    except OSError:
        return None
    match = _CLAUDE_MD_TITLE.search(content)
    if match is None:
        return None
    return match.group("name").strip() or None


def _detect_project_language(project_path: Path) -> str | None:
    """Return the project's primary language by file probing.

    The probes are ordered: the first hit wins. For multi-language
    projects this returns whatever shows up first in the canonical
    list; users can override with ``-l`` if the auto-detected one
    isn't the one they want re-tuned.

    Returns ``None`` if no probe matched, in which case the caller
    must require ``-l``.
    """
    for filename, language in _LANGUAGE_PROBES:
        if (project_path / filename).is_file():
            return language
    return None


def _validate_enhance_target(value: str) -> str:
    """Normalize and validate one ``--targets`` value.

    Args:
        value: A single target name from the CLI.

    Returns:
        The lower-cased target name if it is recognised.

    Raises:
        typer.BadParameter: If the target is not in
            :data:`_ENHANCE_TARGETS`.
    """
    normalized = value.strip().lower()
    if normalized not in _ENHANCE_TARGETS:
        valid = ", ".join(_ENHANCE_TARGETS)
        msg = f"unknown target {value!r}; choose from: {valid}"
        raise typer.BadParameter(msg)
    return normalized


def _split_target_pieces(targets: list[str]) -> list[str]:
    """Flatten ``--targets`` values into individual pieces, dropping empties."""
    return [
        piece.strip() for raw in targets for piece in raw.split(",") if piece.strip()
    ]


def _resolve_enhance_targets(targets: list[str] | None) -> tuple[str, ...]:
    """Resolve the ``--targets`` argument list (possibly comma-separated).

    Accepts both ``--targets claude-md --targets subagents`` and
    ``--targets claude-md,subagents``. ``None`` (no flag passed) means
    "tune every target".

    Args:
        targets: Raw values from the typer option.

    Returns:
        A tuple of resolved target names in the canonical order
        defined by :data:`_ENHANCE_TARGETS`.

    Raises:
        typer.BadParameter: If any target is unknown.
    """
    if not targets:
        return _ENHANCE_TARGETS
    requested = {_validate_enhance_target(p) for p in _split_target_pieces(targets)}
    # Preserve canonical order, deduplicating.
    return tuple(t for t in _ENHANCE_TARGETS if t in requested)


def _require_enhance_orchestrator(
    api_key: str | None,
    *,
    no_interactive: bool,
) -> AIOrchestrator:
    """Resolve an :class:`AIOrchestrator` for the ``enhance`` command.

    Unlike ``init``, ``enhance`` cannot fall back to a deterministic
    path — re-tuning is the entire point. If no API key is available,
    fail fast with an actionable message instead of writing an empty
    "tuning" that silently no-ops.

    Args:
        api_key: Optional CLI-supplied key.
        no_interactive: Skip any keyring prompts.

    Returns:
        A real ``AIOrchestrator`` ready to dispatch.

    Raises:
        typer.Exit: With code 1 if no key could be resolved.
    """
    orchestrator = _initialize_orchestrator(api_key, no_interactive=no_interactive)
    if orchestrator is None:
        console.print(
            "[red]Error:[/red] `green enhance` requires an Anthropic API "
            "key — there is no deterministic fallback for AI-tuned "
            "artifacts.\n  Set ANTHROPIC_API_KEY or pass --api-key.",
            style="bold",
        )
        raise typer.Exit(code=1)
    return orchestrator


def _hash_claude_md_inputs(project_name: str, language: str) -> str:
    """Hash the inputs that drive a ``CLAUDE.md`` re-tune.

    Captures everything that would alter the model's output: the
    reference template content (so updates to the canonical template
    invalidate stale tunes), plus the project metadata (name +
    language + the script and skill lists baked into the prompt).
    """
    project_root = Path(__file__).parent.parent
    reference = project_root / "reference" / "claude" / "CLAUDE.md"
    template_bytes = (
        reference.read_text(encoding="utf-8") if reference.is_file() else ""
    )
    return hash_inputs(
        [
            "claude-md\x00",
            f"project_name={project_name}\x00",
            f"language={language}\x00",
            f"scripts={','.join(sorted(_CLAUDE_MD_SCRIPTS))}\x00",
            f"skills={','.join(sorted(REQUIRED_SKILLS))}\x00",
            "template:\x00",
            template_bytes,
        ]
    )


def _hash_subagents_inputs(project_name: str, language: str) -> str:
    """Hash the inputs that drive a subagents re-tune.

    Captures the union of every required reference subagent's content
    (so a maintainer-side update to any one of them invalidates the
    cached tune) plus the target context (project name + language)
    which flows verbatim into the prompt.
    """
    parts: list[str | bytes] = [
        "subagents\x00",
        f"project_name={project_name}\x00",
        f"language={language}\x00",
    ]
    # Walk REQUIRED_AGENTS in declaration order so the hash is
    # deterministic regardless of dict insertion-order quirks.
    for agent_name, source_file in REQUIRED_AGENTS.items():
        source_path = REFERENCE_AGENTS_DIR / source_file
        body = source_path.read_text(encoding="utf-8") if source_path.is_file() else ""
        parts.append(f"agent={agent_name}\x00")
        parts.append(body)
    return hash_inputs(parts)


# Single source of truth for the script list embedded in the
# CLAUDE.md prompt. Kept here (not duplicated in
# ``_enhance_claude_md``) so the hash stays in sync with the actual
# input.
_CLAUDE_MD_SCRIPTS: tuple[str, ...] = (
    "check-all.sh",
    "test.sh",
    "lint.sh",
    "format.sh",
    "security.sh",
    "mutation.sh",
)


def _compute_target_source_hash(
    target: str,
    project_name: str,
    language: str,
) -> str:
    """Dispatch to the per-target hash function."""
    if target == "claude-md":
        return _hash_claude_md_inputs(project_name, language)
    if target == "subagents":
        return _hash_subagents_inputs(project_name, language)
    msg = f"unknown target: {target}"
    raise ValueError(msg)


def _enhance_claude_md(  # noqa: PLR0913 — Pass 2 helpers mirror init steps
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator,
    *,
    dry_run: bool,
    file_writer: FileWriter | None,
) -> None:
    """Re-tune ``CLAUDE.md`` against the existing project.

    Mirrors :func:`_generate_claude_md_step`'s tuning path but writes
    to the existing project rather than a fresh scaffold. ``dry_run``
    skips the write but still runs the API call so the user sees the
    full token-usage telemetry (and any errors) they'd see for real.
    """
    with step_timer("enhance_claude_md"), console.status("Re-tuning CLAUDE.md..."):
        claude_md_generator = ClaudeMdGenerator(orchestrator)
        result = claude_md_generator.generate(
            {
                "project_name": project_name,
                "language": language,
                "scripts": list(_CLAUDE_MD_SCRIPTS),
                "skills": REQUIRED_SKILLS.copy(),
            }
        )
        target = project_path / "CLAUDE.md"
        if dry_run:
            console.print(
                f"[dim]--dry-run: would rewrite {target} "
                f"({len(result.content):,} chars).[/dim]"
            )
            return
        if file_writer is not None:
            file_writer.write_file(target, result.content)
        else:
            target.write_text(result.content, encoding="utf-8")
    console.print("[green]✓[/green] Re-tuned CLAUDE.md")


def _enhance_subagents(  # noqa: PLR0913 — Pass 2 helpers mirror init steps
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator,
    *,
    dry_run: bool,
    file_writer: FileWriter | None,
) -> None:
    """Re-tune every subagent against the existing project.

    Same parallel-fan-out path as Pass 2 of init, but writes back to
    ``<project>/.claude/agents`` instead of generating it fresh.
    """
    target_dir = project_path / ".claude" / "agents"
    target_dir.mkdir(parents=True, exist_ok=True)

    with step_timer("enhance_subagents"), console.status("Re-tuning subagents..."):
        subagents_generator = SubagentsGenerator(orchestrator)
        target_context = (
            f"Project: {project_name}, "
            f"Language: {language}, "
            f"Type: existing project being re-tuned via `green enhance`"
        )
        results = run_async(
            _run_with_orchestrator_close(
                orchestrator,
                subagents_generator.generate_all_agents(target_context),
            )
        )
        if dry_run:
            console.print(
                f"[dim]--dry-run: would rewrite {len(results)} agent "
                f"file(s) in {target_dir}.[/dim]"
            )
            return
        for agent_name, result in results.items():
            agent_file = target_dir / f"{agent_name}.md"
            if file_writer is not None:
                file_writer.write_file(agent_file, result.content)
            else:
                agent_file.write_text(result.content, encoding="utf-8")
    console.print(f"[green]✓[/green] Re-tuned {len(results)} subagents")


def _resolve_enhance_name(project_path: Path, override: str | None) -> str:
    """Resolve the project name for ``enhance``; exit if neither path works."""
    resolved = override or _detect_project_name(project_path)
    if resolved is None:
        console.print(
            "[red]Error:[/red] could not determine the project name "
            "from CLAUDE.md. Pass --project-name explicitly.",
            style="bold",
        )
        raise typer.Exit(code=1)
    return resolved


def _resolve_enhance_language(project_path: Path, override: str | None) -> str:
    """Resolve the language for ``enhance``; exit if absent or unsupported."""
    resolved = override or _detect_project_language(project_path)
    if resolved is None:
        console.print(
            "[red]Error:[/red] could not detect the project language. "
            "Pass --language explicitly.",
            style="bold",
        )
        raise typer.Exit(code=1)
    try:
        validate_language(resolved)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        raise typer.Exit(code=1) from e
    return resolved


def _resolve_enhance_metadata(
    project_path: Path,
    *,
    project_name: str | None,
    language: str | None,
) -> tuple[str, str]:
    """Resolve project name + language for ``enhance``, exiting on failure.

    Auto-detection from the project layout is the default path; the
    explicit ``--project-name`` and ``--language`` flags win where
    supplied. Either piece missing (no override + no detected value)
    is a fatal error so the caller cannot accidentally tune the wrong
    project metadata into a fresh CLAUDE.md.
    """
    return (
        _resolve_enhance_name(project_path, project_name),
        _resolve_enhance_language(project_path, language),
    )


# Map from target name → (skip-message, name-of-helper-on-this-module).
# Storing the helper *name* (rather than the function reference) lets
# tests patch ``cli._enhance_claude_md`` / ``cli._enhance_subagents``
# at the module attribute level and have the dispatcher pick up the
# patched version at call time. Python's late binding via
# ``globals()[name]`` is the simplest way to achieve that without
# adding a registry layer.
_ENHANCE_DISPATCH: dict[str, tuple[str, str]] = {
    "claude-md": (
        "[dim]CLAUDE.md unchanged since last successful tune — "
        "skipping (use --force to re-tune anyway).[/dim]",
        "_enhance_claude_md",
    ),
    "subagents": (
        "[dim]Subagents unchanged since last successful tune — "
        "skipping (use --force to re-tune anyway).[/dim]",
        "_enhance_subagents",
    ),
}


def _dispatch_enhance_targets(  # noqa: PLR0913 — orchestration glue
    targets: tuple[str, ...],
    *,
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator,
    state: EnhanceState,
    target_hashes: dict[str, str],
    dry_run: bool,
    force: bool,
    file_writer: FileWriter | None,
) -> list[str]:
    """Drive Pass 2 across each selected target with the skip/force logic.

    Returns the list of target names that were skipped because the
    source hash matched a stored completion. The caller uses that to
    decide whether the state file is worth re-writing.
    """
    skipped: list[str] = []
    for target in targets:
        skip_message, helper_name = _ENHANCE_DISPATCH[target]
        target_hash = target_hashes[target]
        if not force and state.is_unchanged(target, target_hash):
            console.print(skip_message)
            skipped.append(target)
            continue
        # Late-bound lookup so test ``patch("cli._enhance_claude_md")``
        # decorations are honoured.
        helper: Callable[..., None] = globals()[helper_name]
        helper(
            project_path,
            project_name,
            language,
            orchestrator,
            dry_run=dry_run,
            file_writer=file_writer,
        )
        if not dry_run:
            state.mark_completed(target, target_hash, orchestrator.model)
    return skipped


def _persist_enhance_state(
    project_path: Path,
    state: EnhanceState,
    *,
    skipped: list[str],
    selected_targets: tuple[str, ...],
    dry_run: bool,
) -> None:
    """Save the state file unless this run wrote nothing.

    A "nothing happened" run is either a ``--dry-run`` (we ran the
    API calls but skipped the writes) or a run where every selected
    target was skipped because its source hash matched. In both
    cases the prior state on disk is still authoritative.
    """
    if dry_run:
        return
    if len(skipped) >= len(selected_targets):
        return
    save_state(project_path, state)


def _print_enhance_summary(*, project_name: str, dry_run: bool) -> None:
    """Print the closing one-liner for an ``enhance`` invocation."""
    if dry_run:
        console.print("\n[green]✓[/green] Dry run complete — no files written.")
    else:
        console.print(f"\n[green]✓[/green] Enhancement complete: {project_name}")


def _run_enhance_pipeline(  # noqa: PLR0913 — orchestration glue
    *,
    project_path: Path,
    project_name: str,
    language: str,
    selected_targets: tuple[str, ...],
    orchestrator: AIOrchestrator,
    file_writer: FileWriter | None,
    dry_run: bool,
    force: bool,
) -> None:
    """Execute the full Pass 2 pipeline + persist state on success."""
    console.print(
        f"[dim]Enhancing project: {project_name} ({language})"
        f"  →  targets: {', '.join(selected_targets)}"
        f"{'  [DRY RUN]' if dry_run else ''}[/dim]"
    )
    state = load_state(project_path)
    target_hashes = {
        target: _compute_target_source_hash(target, project_name, language)
        for target in selected_targets
    }
    skipped = _dispatch_enhance_targets(
        selected_targets,
        project_path=project_path,
        project_name=project_name,
        language=language,
        orchestrator=orchestrator,
        state=state,
        target_hashes=target_hashes,
        dry_run=dry_run,
        force=force,
        file_writer=file_writer,
    )
    _persist_enhance_state(
        project_path,
        state,
        skipped=skipped,
        selected_targets=selected_targets,
        dry_run=dry_run,
    )
    _print_enhance_summary(project_name=project_name, dry_run=dry_run)


def _validate_enhance_path(project_path: Path) -> None:
    """Confirm ``project_path`` looks like a generated green-init project.

    The cheapest reliable signature is the presence of ``CLAUDE.md`` —
    every init flow writes one (Phase 1 added the deterministic
    baseline so even ``--offline`` projects have it). Without that
    file, ``enhance`` has no project to re-tune; fail fast with a
    pointer to ``green init``.

    Args:
        project_path: Directory the user passed as the enhance target.

    Raises:
        typer.Exit: With code 1 if the path is not an enhanceable
            project.
    """
    if not project_path.exists():
        console.print(
            f"[red]Error:[/red] {project_path} does not exist.",
            style="bold",
        )
        raise typer.Exit(code=1)
    if not project_path.is_dir():
        console.print(
            f"[red]Error:[/red] {project_path} is not a directory.",
            style="bold",
        )
        raise typer.Exit(code=1)
    if not (project_path / "CLAUDE.md").is_file():
        console.print(
            f"[red]Error:[/red] {project_path} does not look like a "
            "green-init project (no CLAUDE.md found).\n  Run "
            "`green init` first or pass a different path.",
            style="bold",
        )
        raise typer.Exit(code=1)


@app.command()
def enhance(  # noqa: PLR0913 — top-level CLI command; matches init's pattern
    project_path: Annotated[
        Path,
        typer.Argument(
            help=(
                "Path to an existing green-init project. Defaults to the "
                "current directory. The directory must contain a "
                "``CLAUDE.md`` produced by `green init`."
            ),
            exists=False,
        ),
    ] = Path(),
    project_name: Annotated[
        str | None,
        typer.Option(
            "--project-name",
            "-n",
            help=(
                "Override the auto-detected project name. By default the "
                "name is parsed out of the existing ``CLAUDE.md``'s H1 "
                "title."
            ),
        ),
    ] = None,
    language: Annotated[
        str | None,
        typer.Option(
            "--language",
            "-l",
            help=(
                "Override the auto-detected primary language. By default "
                "the language is probed from canonical project files "
                "(pyproject.toml, package.json, go.mod, Cargo.toml, ...)."
            ),
        ),
    ] = None,
    targets: Annotated[
        list[str] | None,
        typer.Option(
            "--targets",
            "-t",
            help=(
                "Subset of artifacts to re-tune. Repeat the flag or "
                f"comma-separate. Choices: {', '.join(_ENHANCE_TARGETS)}. "
                "Default: re-tune everything."
            ),
        ),
    ] = None,
    *,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help=(
                "Make the API calls but do not write any files. Useful "
                "for previewing token cost / changes before committing "
                "to a re-tune."
            ),
        ),
    ] = False,
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            help=(
                "[DEPRECATED] API key is visible in process list. "
                "Use ANTHROPIC_API_KEY env var or keyring instead."
            ),
            hide_input=True,
        ),
    ] = None,
    no_interactive: Annotated[
        bool,
        typer.Option(
            "--no-interactive",
            help="Run in non-interactive mode (skip keyring prompts).",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite files without prompting. Off by default.",
        ),
    ] = False,
) -> None:
    r"""Re-run Pass 2 (AI tuning) on an existing green-init project.

    Phase 3b of the optimization roadmap: gives users who ran
    ``green init --offline`` (or who have updated their reference
    skills/subagents) a way to add or refresh the AI-tuned artifacts
    without re-scaffolding the whole project.

    Examples:
        \b
        # Re-tune everything in the current directory:
        green enhance
    \b
        # Re-tune only CLAUDE.md in a specific project:
        green enhance ./my-app --targets claude-md
    \b
        # Preview the token cost without writing anything:
        green enhance --dry-run

    Args:
        project_path: Directory of the existing project.
        project_name: Optional override for auto-detection.
        language: Optional override for auto-detection.
        targets: Subset of artifacts to re-tune.
        dry_run: Run the API calls but skip the writes.
        api_key: Optional Claude API key.
        no_interactive: Disable interactive prompts.
        force: Overwrite files without prompting.

    Raises:
        typer.Exit: If the path is invalid, project metadata cannot
            be inferred, an unknown ``--targets`` value is supplied,
            or no API key is available.
    """
    project_path = project_path.resolve()
    _validate_enhance_path(project_path)

    resolved_name, resolved_language = _resolve_enhance_metadata(
        project_path,
        project_name=project_name,
        language=language,
    )

    selected_targets = _resolve_enhance_targets(targets)
    orchestrator = _require_enhance_orchestrator(api_key, no_interactive=no_interactive)
    file_writer = FileWriter(
        project_root=project_path,
        force=force,
        interactive=False,
        console=console,
    )

    _run_enhance_pipeline(
        project_path=project_path,
        project_name=resolved_name,
        language=resolved_language,
        selected_targets=selected_targets,
        orchestrator=orchestrator,
        file_writer=file_writer,
        dry_run=dry_run,
        force=force,
    )


def cli_main() -> None:
    """Entry point for the CLI when installed as a package."""
    app()


if __name__ == "__main__":
    cli_main()
