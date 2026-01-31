"""Main CLI entry point for Start Green Stay Green.

Implements the command-line interface using Typer with rich output formatting.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import sys
from typing import Annotated

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
import typer

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.architecture import (
    ArchitectureEnforcementGenerator,
)
from start_green_stay_green.generators.ci import CIGenerator
from start_green_stay_green.generators.claude_md import ClaudeMdGenerator
from start_green_stay_green.generators.github_actions import (
    GitHubActionsReviewGenerator,
)
from start_green_stay_green.generators.precommit import GenerationConfig
from start_green_stay_green.generators.precommit import PreCommitGenerator
from start_green_stay_green.generators.scripts import ScriptConfig
from start_green_stay_green.generators.scripts import ScriptsGenerator
from start_green_stay_green.generators.skills import REFERENCE_SKILLS_DIR
from start_green_stay_green.generators.skills import REQUIRED_SKILLS
from start_green_stay_green.generators.subagents import SubagentsGenerator
from start_green_stay_green.utils.async_bridge import run_async
from start_green_stay_green.utils.credentials import get_api_key_from_keyring
from start_green_stay_green.utils.credentials import store_api_key_in_keyring

# Version information
__version__ = "2.0.0"

# Constants
MAX_PROJECT_NAME_LENGTH = 100

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
        console.print(f"[bold cyan]Start Green Stay Green[/bold cyan] v{version_str}")


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
    resolved = output_dir.resolve()

    # Double-check no traversal remains after resolution
    if ".." in resolved.parts:
        msg = "Output directory cannot contain '..' components"
        raise typer.BadParameter(msg)

    return resolved


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

    # Verify no escape after joining paths
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


def _get_api_key_with_source(
    api_key_arg: str | None,
    *,
    no_interactive: bool,
) -> tuple[str, str] | tuple[None, None]:
    """Get API key and its source.

    Returns:
        (api_key, source) tuple, or (None, None) if not found.
    """
    sources = [
        (api_key_arg, "command line"),
        (get_api_key_from_keyring(), "keyring"),
        (os.getenv("ANTHROPIC_API_KEY"), "environment variable"),
    ]

    for key, source in sources:
        if key:
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


def _copy_reference_skills(target_dir: Path) -> None:
    """Copy reference skills to target directory.

    This is a temporary implementation that directly copies reference skills
    without AI-powered tuning. Full AI integration (async + AIOrchestrator)
    will be added in Issue #115.

    Args:
        target_dir: Target directory for skills (.claude/skills/).

    Raises:
        FileNotFoundError: If reference skills directory not found.
    """
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy each required skill
    for skill_name in REQUIRED_SKILLS:
        source_file = REFERENCE_SKILLS_DIR / skill_name
        if not source_file.exists():
            msg = f"Reference skill not found: {skill_name}"
            raise FileNotFoundError(msg)

        target_file = target_dir / skill_name
        target_file.write_text(source_file.read_text())


def _generate_scripts_step(
    project_path: Path, project_name: str, language: str, progress: Progress
) -> None:
    """Generate quality scripts with progress indicator."""
    task = progress.add_task("Generating scripts...", total=None)
    scripts_config = ScriptConfig(
        language=language,
        package_name=project_name.replace("-", "_"),
    )
    scripts_generator = ScriptsGenerator(
        output_dir=project_path / "scripts",
        config=scripts_config,
    )
    scripts_generator.generate()
    progress.update(task, completed=True)


def _generate_precommit_step(
    project_path: Path, project_name: str, language: str, progress: Progress
) -> None:
    """Generate pre-commit configuration with progress indicator."""
    task = progress.add_task("Generating pre-commit config...", total=None)
    precommit_config = GenerationConfig(
        project_name=project_name,
        language=language,
        language_config={},
    )
    precommit_generator = PreCommitGenerator(orchestrator=None)
    precommit_content = precommit_generator.generate(precommit_config)
    precommit_file = project_path / ".pre-commit-config.yaml"
    precommit_file.write_text(precommit_content)
    progress.update(task, completed=True)


def _generate_skills_step(project_path: Path, progress: Progress) -> None:
    """Generate Claude skills with progress indicator."""
    task = progress.add_task("Generating skills...", total=None)
    skills_dir = project_path / ".claude" / "skills"
    _copy_reference_skills(skills_dir)
    progress.update(task, completed=True)


def _generate_ci_step(
    project_path: Path,
    language: str,
    orchestrator: AIOrchestrator | None,
    progress: Progress,
) -> None:
    """Generate CI pipeline or skip if no orchestrator."""
    if orchestrator:
        task = progress.add_task("Generating CI pipeline...", total=None)
        ci_generator = CIGenerator(orchestrator, language)
        workflow = ci_generator.generate_workflow()
        workflows_dir = project_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "ci.yml").write_text(workflow.content)
        progress.update(task, completed=True)
    else:
        task = progress.add_task("Skipping CI (no API key)...", total=None)
        progress.update(task, completed=True)


def _generate_review_step(
    project_path: Path, orchestrator: AIOrchestrator | None, progress: Progress
) -> None:
    """Generate GitHub Actions code review or skip if no orchestrator."""
    if orchestrator:
        task = progress.add_task("Generating GitHub Actions review...", total=None)
        review_generator = GitHubActionsReviewGenerator(orchestrator)
        review_result = review_generator.generate()
        workflows_dir = project_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        (workflows_dir / "code-review.yml").write_text(review_result.workflow_content)
        progress.update(task, completed=True)
    else:
        task = progress.add_task("Skipping code review (no API key)...", total=None)
        progress.update(task, completed=True)


def _generate_claude_md_step(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    progress: Progress,
) -> None:
    """Generate CLAUDE.md or skip if no orchestrator."""
    if orchestrator:
        task = progress.add_task("Generating CLAUDE.md...", total=None)
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
        (project_path / "CLAUDE.md").write_text(claude_md_result.content)
        progress.update(task, completed=True)
    else:
        task = progress.add_task("Skipping CLAUDE.md (no API key)...", total=None)
        progress.update(task, completed=True)


def _generate_architecture_step(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    progress: Progress,
) -> None:
    """Generate architecture rules or skip if no orchestrator."""
    if orchestrator:
        task = progress.add_task("Generating architecture rules...", total=None)
        arch_generator = ArchitectureEnforcementGenerator(
            orchestrator,
            output_dir=project_path / "plans" / "architecture",
        )
        arch_generator.generate(language=language, project_name=project_name)
        progress.update(task, completed=True)
    else:
        task = progress.add_task(
            "Skipping architecture rules (no API key)...", total=None
        )
        progress.update(task, completed=True)


def _generate_subagents_step(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    progress: Progress,
) -> None:
    """Generate subagents or skip if no orchestrator."""
    if orchestrator:
        task = progress.add_task("Generating subagents...", total=None)
        subagents_dir = project_path / ".claude" / "agents"
        subagents_generator = SubagentsGenerator(
            orchestrator, reference_dir=subagents_dir
        )
        project_config_for_agents = (
            f"Project: {project_name}, "
            f"Language: {language}, "
            f"Type: quality-control-tool"
        )
        results = run_async(
            subagents_generator.generate_all_agents(project_config_for_agents)
        )
        subagents_dir.mkdir(parents=True, exist_ok=True)
        for agent_name, result in results.items():
            (subagents_dir / f"{agent_name}.md").write_text(result.content)
        progress.update(task, completed=True)
    else:
        task = progress.add_task("Skipping subagents (no API key)...", total=None)
        progress.update(task, completed=True)


def _generate_with_orchestrator(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    progress: Progress,
) -> None:
    """Generate AI-powered artifacts (CI, CLAUDE.md, etc.) with progress indicators."""
    _generate_ci_step(project_path, language, orchestrator, progress)
    _generate_review_step(project_path, orchestrator, progress)
    _generate_claude_md_step(
        project_path, project_name, language, orchestrator, progress
    )
    _generate_architecture_step(
        project_path, project_name, language, orchestrator, progress
    )
    _generate_subagents_step(
        project_path, project_name, language, orchestrator, progress
    )


def _generate_project_files(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
) -> None:
    """Generate all project files with progress indicators.

    Args:
        project_path: Path where project will be created.
        project_name: Name of the project.
        language: Programming language.
        orchestrator: Optional AI orchestrator for AI-powered features.
            None indicates fallback to template mode.

    Raises:
        typer.Exit: If generation fails.
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            _generate_scripts_step(project_path, project_name, language, progress)
            _generate_precommit_step(project_path, project_name, language, progress)
            _generate_skills_step(project_path, progress)
            _generate_with_orchestrator(
                project_path, project_name, language, orchestrator, progress
            )

        console.print(
            f"\n[green]✓[/green] Project generated successfully at: {project_path}"
        )
        console.print("\nTo get started, run:")
        console.print(f"  cd {project_path}")
        console.print("  pre-commit install")
        console.print("  ./scripts/check-all.sh\n")
    except Exception as e:
        console.print(f"\n[red]Error:[/red] Generation failed: {e}", style="bold")
        raise typer.Exit(code=1) from e


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
        str | None,
        typer.Option(
            "--language",
            "-l",
            help="Primary programming language (python, typescript, go, rust).",
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
            help="Claude API key for AI-powered features (optional).",
            hide_input=True,
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
        no_interactive: Non-interactive mode.
        api_key: Optional Claude API key for AI features.
        config: Configuration file path.

    Raises:
        typer.Exit: If validation fails or generation errors occur.
    """
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
    resolved_language = _resolve_parameter(
        language,
        config_data,
        "language",
        "Primary language",
        no_interactive=no_interactive,
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
        _show_dry_run_preview(resolved_project_name, resolved_language, project_path)
        return

    # Initialize optional AI orchestrator (after dry-run check)
    orchestrator = _initialize_orchestrator(api_key, no_interactive=no_interactive)

    if orchestrator is None:
        console.print("\n[yellow]![/yellow] AI features disabled")
        console.print("  - Skills: Using reference templates (no customization)")
        console.print("  - CI/Subagents/CLAUDE.md: Using default templates")
        console.print("\n  To enable AI features:")
        console.print("    1. Get API key: https://console.anthropic.com/")
        console.print("    2. Run: sgsg init --api-key YOUR_KEY")
        console.print("    3. Or: Set ANTHROPIC_API_KEY environment variable\n")

    # Create project directory
    project_path.mkdir(parents=True, exist_ok=True)

    # Generate all project files (handles errors internally)
    _generate_project_files(
        project_path, resolved_project_name, resolved_language, orchestrator
    )


def cli_main() -> None:
    """Entry point for the CLI when installed as a package."""
    app()


if __name__ == "__main__":
    cli_main()
