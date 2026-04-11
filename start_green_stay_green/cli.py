"""Main CLI entry point for Start Green Stay Green.

Implements the command-line interface using Typer with rich output formatting.
"""

from __future__ import annotations

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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Sequence

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
from start_green_stay_green.generators.subagents import SubagentsGenerator
from start_green_stay_green.generators.tests_gen import TestsConfig
from start_green_stay_green.generators.tests_gen import TestsGenerator
from start_green_stay_green.utils.async_bridge import run_async
from start_green_stay_green.utils.credentials import get_api_key_from_keyring
from start_green_stay_green.utils.credentials import store_api_key_in_keyring
from start_green_stay_green.utils.file_writer import FileWriter
from start_green_stay_green.utils.yaml_merge import merge_precommit_configs

# Version information
__version__ = "1.0.0"

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
) -> Generator[tuple[str | None, str], None, None]:
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


def _generate_structure_step(
    project_path: Path,
    project_name: str,
    language: str,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate source code structure."""
    with console.status("Generating source structure..."):
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
    with console.status("Generating dependencies..."):
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
    with console.status("Generating tests..."):
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
    with console.status("Generating README..."):
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

    with console.status(f"Generating {language} scripts..."):
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
    with console.status("Generating pre-commit config..."):
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
    with console.status("Generating skills..."):
        skills_dir = project_path / ".claude" / "skills"
        _copy_reference_skills(skills_dir, file_writer=file_writer)
    console.print("[green]✓[/green] Generated skills")


def _generate_ci_step(
    project_path: Path,
    language: str,
    orchestrator: AIOrchestrator | None,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate CI pipeline or skip if no orchestrator."""
    if orchestrator:
        with console.status("Generating CI pipeline..."):
            ci_generator = CIGenerator(orchestrator, language)
            workflow = ci_generator.generate_workflow()
            workflows_dir = project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            ci_file = workflows_dir / "ci.yml"
            if file_writer is not None:
                file_writer.write_file(ci_file, workflow.content)
            else:
                ci_file.write_text(workflow.content)
        console.print("[green]✓[/green] Generated CI pipeline")
    else:
        console.print("[yellow]⊘[/yellow] Skipped CI (no API key)")


def _generate_review_step(
    project_path: Path,
    orchestrator: AIOrchestrator | None,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate GitHub Actions code review or skip if no orchestrator."""
    if orchestrator:
        with console.status("Generating GitHub Actions review..."):
            review_generator = GitHubActionsReviewGenerator(orchestrator)
            review_result = review_generator.generate()
            workflows_dir = project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            workflow_file = workflows_dir / "code-review.yml"
            if file_writer is not None:
                file_writer.write_file(workflow_file, review_result["workflow_content"])
            else:
                workflow_file.write_text(review_result["workflow_content"])
        console.print("[green]✓[/green] Generated GitHub Actions review")
    else:
        console.print("[yellow]⊘[/yellow] Skipped code review (no API key)")


def _generate_claude_md_step(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate CLAUDE.md or skip if no orchestrator."""
    if orchestrator:
        with console.status("Generating CLAUDE.md..."):
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
                claude_md_file.write_text(claude_md_result.content)
        console.print("[green]✓[/green] Generated CLAUDE.md")
    else:
        console.print("[yellow]⊘[/yellow] Skipped CLAUDE.md (no API key)")


def _generate_architecture_step(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate architecture rules or skip if no orchestrator."""
    if not orchestrator:
        console.print("[yellow]⊘[/yellow] Skipped architecture rules (no API key)")
        return

    arch_dir = project_path / "plans" / "architecture"
    # ArchitectureEnforcementGenerator writes files internally;
    # skip the entire step if the output directory already has content.
    if file_writer is not None and file_writer.skip_existing_dir(arch_dir):
        console.print("[green]✓[/green] Architecture rules (preserved existing)")
        return

    with console.status("Generating architecture rules..."):
        arch_generator = ArchitectureEnforcementGenerator(
            orchestrator,
            output_dir=arch_dir,
        )
        arch_generator.generate(language=language, project_name=project_name)
    console.print("[green]✓[/green] Generated architecture rules")


def _generate_subagents_step(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate subagents or skip if no orchestrator."""
    if orchestrator:
        with console.status("Generating subagents..."):
            subagents_generator = SubagentsGenerator(orchestrator)
            project_config_for_agents = (
                f"Project: {project_name}, "
                f"Language: {language}, "
                f"Type: quality-control-tool"
            )
            results = run_async(
                subagents_generator.generate_all_agents(project_config_for_agents)
            )
            subagents_output_dir = project_path / ".claude" / "agents"
            subagents_output_dir.mkdir(parents=True, exist_ok=True)
            for agent_name, result in results.items():
                agent_file = subagents_output_dir / f"{agent_name}.md"
                if file_writer is not None:
                    file_writer.write_file(agent_file, result.content)
                else:
                    agent_file.write_text(result.content)
        console.print("[green]✓[/green] Generated subagents")
    else:
        console.print("[yellow]⊘[/yellow] Skipped subagents (no API key)")


def _generate_metrics_dashboard_step(
    project_path: Path,
    project_name: str,
    language: str,
) -> None:
    """Generate live metrics dashboard and workflow."""
    with console.status("Generating metrics dashboard..."):
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
        initial_metrics_path.write_text(json.dumps(initial_metrics, indent=2))

        workflows_dir = project_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        sgsg_root = Path(__file__).parent.parent
        sgsg_workflow = sgsg_root / ".github" / "workflows" / "metrics.yml"
        missing_workflow = False
        missing_script = False
        if sgsg_workflow.exists():
            target_workflow = workflows_dir / "metrics.yml"
            shutil.copy(sgsg_workflow, target_workflow)
            workflow_content = target_workflow.read_text()
            workflow_content = workflow_content.replace(
                "start-green-stay-green", project_name
            )
            target_workflow.write_text(workflow_content)
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


def _generate_with_orchestrator(
    project_path: Path,
    project_name: str,
    language: str,
    orchestrator: AIOrchestrator | None,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate AI-powered artifacts (CI, CLAUDE.md, etc.) with progress indicators."""
    _generate_ci_step(project_path, language, orchestrator, file_writer)
    _generate_review_step(project_path, orchestrator, file_writer)
    _generate_claude_md_step(
        project_path, project_name, language, orchestrator, file_writer
    )
    _generate_architecture_step(
        project_path, project_name, language, orchestrator, file_writer
    )
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

        # AI-powered features use primary language
        try:
            _generate_with_orchestrator(
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
    for lang in languages:
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
    enable_live_dashboard: Annotated[
        bool,
        typer.Option(
            "--enable-live-dashboard",
            help="Generate live metrics dashboard with auto-updating workflow.",
        ),
    ] = False,
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
        enable_live_dashboard: Generate live metrics dashboard with workflow.
        config: Configuration file path.

    Raises:
        typer.Exit: If validation fails or generation errors occur.
    """
    _validate_conflict_flags(force, interactive)

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

    # Create FileWriter with the chosen conflict resolution mode
    file_writer = FileWriter(
        project_root=project_path,
        force=force,
        interactive=interactive,
        console=console,
    )

    # Generate all project files (handles errors internally)
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


def cli_main() -> None:
    """Entry point for the CLI when installed as a package."""
    app()


if __name__ == "__main__":
    cli_main()
