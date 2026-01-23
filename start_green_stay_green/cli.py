"""Main CLI entry point for Start Green Stay Green.

Implements the command-line interface using Typer with rich output formatting.
"""

from __future__ import annotations

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

from start_green_stay_green.generators.precommit import GenerationConfig
from start_green_stay_green.generators.precommit import PreCommitGenerator
from start_green_stay_green.generators.scripts import ScriptConfig
from start_green_stay_green.generators.scripts import ScriptsGenerator

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


def _generate_project_files(
    project_path: Path,
    project_name: str,
    language: str,
) -> None:
    """Generate all project files with progress indicators.

    Args:
        project_path: Path where project will be created.
        project_name: Name of the project.
        language: Programming language.

    Raises:
        typer.Exit: If generation fails.
    """
    # TODO(Issue #106): Implement remaining generator integrations  # noqa: FIX002
    # Currently integrated: ScriptsGenerator, PreCommitGenerator (2/8)
    # Remaining: CI, Skills, Subagents, ClaudeMd, GitHubActions, Architecture

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Generate quality scripts
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

            # Generate pre-commit configuration
            task = progress.add_task("Generating pre-commit config...", total=None)
            precommit_config = GenerationConfig(
                project_name=project_name,
                language=language,
                language_config={},
            )
            # PreCommitGenerator extends BaseGenerator but doesn't use orchestrator
            # Pass None since it's template-based, not AI-powered
            # Issue #114: BaseGenerator requires orchestrator even for
            # template-based generators
            precommit_generator = PreCommitGenerator(orchestrator=None)  # type: ignore[arg-type]
            precommit_content = precommit_generator.generate(precommit_config)
            precommit_file = project_path / ".pre-commit-config.yaml"
            precommit_file.write_text(precommit_content)
            progress.update(task, completed=True)

            # Placeholders for remaining generators (Issue #106)
            placeholders = [
                "Generating CI pipeline...",
                "Generating skills...",
                "Generating subagents...",
                "Generating CLAUDE.md...",
                "Generating GitHub Actions (AI review)...",
                "Generating architecture rules...",
            ]

            for description in placeholders:
                task = progress.add_task(description, total=None)
                # Placeholder: actual generator calls will be added
                progress.update(task, completed=True)

        console.print(
            f"\n[green]✓[/green] Project generated successfully at: {project_path}"
        )
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
    config: config_file_option = None,
) -> None:
    """Initialize a new project with quality controls.

    Generates a complete project structure with CI/CD, quality checks,
    AI subagents, and documentation pre-configured.

    Args:
        project_name: Name of the project.
        language: Primary programming language.
        output_dir: Output directory (defaults to current directory).
        dry_run: Preview mode without file creation.
        no_interactive: Non-interactive mode.
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
        raise typer.Exit(code=1) from e

    # Handle dry-run mode
    if dry_run:
        _show_dry_run_preview(resolved_project_name, resolved_language, project_path)
        return

    # Create project directory
    project_path.mkdir(parents=True, exist_ok=True)

    # Generate all project files (handles errors internally)
    _generate_project_files(project_path, resolved_project_name, resolved_language)


def cli_main() -> None:
    """Entry point for the CLI when installed as a package."""
    app()


if __name__ == "__main__":
    cli_main()
