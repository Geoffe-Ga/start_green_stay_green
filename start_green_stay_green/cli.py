"""Main CLI entry point for Start Green Stay Green.

Implements the command-line interface using Typer with rich output formatting.
"""

from __future__ import annotations

from contextlib import contextmanager
import dataclasses
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import shlex
import shutil
import sys
from typing import Annotated
from typing import Any
from typing import Final
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import assert_never

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Coroutine
    from collections.abc import Generator
    from collections.abc import Mapping
    from collections.abc import Sequence

    from start_green_stay_green.ai.providers.base import ProviderCapabilities
    from start_green_stay_green.generators.agent_context import AgentContextContent
    from start_green_stay_green.utils.enhance_state import EnhanceState

from rich.console import Console
from rich.panel import Panel
import typer

from start_green_stay_green.ai.batch_dispatch import BatchPersistenceContext
from start_green_stay_green.ai.batch_dispatch import BatchWaitConfig
from start_green_stay_green.ai.batch_dispatch import ResumeOutcome
from start_green_stay_green.ai.batch_dispatch import ResumeStatus
from start_green_stay_green.ai.batch_dispatch import resume_subagent_batch
from start_green_stay_green.ai.batch_dispatch import submit_subagent_batch
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError as AIGenerationError
from start_green_stay_green.ai.provider_selection import ProviderSelection
from start_green_stay_green.ai.provider_selection import ProviderUnavailableError
from start_green_stay_green.ai.provider_selection import build_provider
from start_green_stay_green.ai.provider_selection import describe_providers
from start_green_stay_green.ai.provider_selection import resolve_api_key_env_var
from start_green_stay_green.ai.provider_selection import resolve_provider_selection
from start_green_stay_green.generators.agent_context import AGENT_CONTEXT_TARGETS
from start_green_stay_green.generators.agent_context import TARGET_AGENTS_MD
from start_green_stay_green.generators.agent_context import TARGET_AIDER
from start_green_stay_green.generators.agent_context import TARGET_CLAUDE
from start_green_stay_green.generators.agent_context import load_agent_context_content
from start_green_stay_green.generators.agent_context import render_target_files
from start_green_stay_green.generators.architecture import (
    ArchitectureEnforcementGenerator,
)
from start_green_stay_green.generators.base import SUPPORTED_LANGUAGES
from start_green_stay_green.generators.base import validate_language
from start_green_stay_green.generators.ci import CIGenerator
from start_green_stay_green.generators.ci import LANGUAGE_CONFIGS as CI_LANGUAGE_CONFIGS
from start_green_stay_green.generators.ci_windows import WINDOWS_CI_LANGUAGES
from start_green_stay_green.generators.claude_md import ClaudeMdGenerationResult
from start_green_stay_green.generators.claude_md import ClaudeMdGenerator
from start_green_stay_green.generators.dependencies import DependenciesGenerator
from start_green_stay_green.generators.dependencies import DependencyConfig
from start_green_stay_green.generators.github_actions import (
    GitHubActionsReviewGenerator,
)
from start_green_stay_green.generators.metrics import (
    LANGUAGE_TOOLS as METRICS_LANGUAGE_TOOLS,
)
from start_green_stay_green.generators.metrics import MetricsGenerationConfig
from start_green_stay_green.generators.metrics import MetricsGenerator
from start_green_stay_green.generators.metrics import ci_status
from start_green_stay_green.generators.metrics import count_ci_jobs
from start_green_stay_green.generators.metrics import precommit_status
from start_green_stay_green.generators.precommit import (
    LANGUAGE_CONFIGS as PRECOMMIT_LANGUAGE_CONFIGS,
)
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
from start_green_stay_green.utils.fs import is_windows
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

provider_option = Annotated[
    str | None,
    typer.Option(
        "--provider",
        help=(
            "LLM provider for AI features. Precedence: this flag > "
            "GREEN_LLM_PROVIDER env > config file > default (anthropic). "
            "The provider's API key is read from its own env var "
            "(ANTHROPIC_API_KEY for anthropic, OPENAI_API_KEY for openai). "
            "For openai, OPENAI_BASE_URL points at any OpenAI-compatible "
            "local server (a dummy key is fine there)."
        ),
    ),
]

model_option = Annotated[
    str | None,
    typer.Option(
        "--model",
        help=(
            "Model identifier for AI features. Precedence: this flag > "
            "GREEN_LLM_MODEL env > config file > the provider's default "
            "model."
        ),
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


def _version_flag_callback(value: bool) -> None:  # noqa: FBT001
    """Print the version and exit when ``--version`` is passed.

    Eager Typer callback: runs before any command or option validation,
    so ``sgsg --version`` works regardless of other arguments. Output
    matches the ``version`` subcommand's simple form.

    Args:
        value: ``True`` when the flag was supplied on the command line.

    Raises:
        typer.Exit: Always, after printing (exit code 0).
    """
    if value:
        console.print(f"[bold cyan]Start Green Stay Green v{get_version()}[/bold cyan]")
        raise typer.Exit


version_flag_option = Annotated[
    bool,
    typer.Option(
        "--version",
        help="Show the version and exit.",
        callback=_version_flag_callback,
        is_eager=True,
    ),
]


@app.callback()
def main(
    verbose: verbose_option = False,  # noqa: FBT002
    quiet: quiet_option = False,  # noqa: FBT002
    config: config_file_option = None,
    version: version_flag_option = False,  # noqa: FBT002
) -> None:
    """Start Green Stay Green - Generate quality-controlled, AI-ready repositories.

    A meta-tool for scaffolding new software projects with enterprise-grade
    quality controls pre-configured.

    Args:
        verbose: Enable verbose output.
        quiet: Suppress non-essential output.
        config: Path to configuration file.
        version: Print the version and exit (handled eagerly).
    """
    # The eager callback consumed --version before this body runs; the
    # parameter exists only so Typer registers the option.
    del version
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


# Display labels for ProviderCapabilities flag fields whose name alone
# doesn't read well; every other bool field falls back to its field
# name with underscores spaced.
_CAPABILITY_FLAG_LABELS: Final[dict[str, str]] = {"tool_use": "tool-use"}


def _format_capability_flags(capabilities: ProviderCapabilities) -> str:
    """Render one provider's capability flags as a short yes/no line.

    Derives the flag list from the dataclass's own bool fields so a new
    capability added to :class:`ProviderCapabilities` shows up here
    without a second edit point.

    Args:
        capabilities: The provider's frozen advertisement.

    Returns:
        A comma-separated ``flag: yes/no`` summary, e.g.
        ``"batch: yes, tool-use: yes, token accounting: yes"``.
    """
    flags = (
        (
            _CAPABILITY_FLAG_LABELS.get(field.name, field.name.replace("_", " ")),
            getattr(capabilities, field.name),
        )
        for field in dataclasses.fields(capabilities)
        if isinstance(getattr(capabilities, field.name), bool)
    )
    return ", ".join(
        f"{label}: {'yes' if supported else 'no'}" for label, supported in flags
    )


@app.command()
def providers() -> None:
    """List registered LLM providers and their capabilities.

    Shows, for each provider the ``--provider`` flag accepts: the
    default model, the environment variable its API key is read from,
    and which capability groups it implements (batch, tool-use, token
    accounting). The listing is read from each provider's capability
    advertisement — no credentials, network access, or optional vendor
    SDK required.
    """
    for listing in describe_providers():
        flags = _format_capability_flags(listing.capabilities)
        console.print(f"[bold]{listing.name}[/bold]")
        console.print(f"  default model:   {listing.default_model}")
        console.print(f"  API key env var: {listing.api_key_env_var}")
        console.print(f"  capabilities:    {flags}")
    console.print(
        "\n[dim]Select with --provider/--model on `green init` / "
        "`green enhance`, or via GREEN_LLM_PROVIDER / GREEN_LLM_MODEL. "
        "Providers without batch support fall back to sequential API "
        "calls (with a warning) when --batch is requested.[/dim]"
    )


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
    agent_targets: tuple[str, ...] = (TARGET_CLAUDE,),
) -> None:
    """Display dry-run preview of what would be generated.

    Args:
        project_name: Name of the project.
        language: Programming language.
        project_path: Path where project would be created.
        agent_targets: Resolved ``--agent`` context targets; controls
            which agent-context artifacts the preview lists (#387).
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
    if TARGET_CLAUDE in agent_targets:
        console.print("  - Subagent profiles")
        console.print("  - CLAUDE.md (modular: index + .claude/docs/)")
    if TARGET_AGENTS_MD in agent_targets:
        console.print("  - AGENTS.md (open agent-context standard)")
    if TARGET_AIDER in agent_targets:
        console.print("  - CONVENTIONS.md + .aider.conf.yml (aider)")
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
    api_key_env_var: str = "ANTHROPIC_API_KEY",
) -> Generator[tuple[str | None, str]]:
    """Yield API key sources lazily to avoid unnecessary keychain prompts.

    Each source is only evaluated when iterated, so keyring is never
    accessed if an earlier source provides the key.

    Args:
        api_key_arg: API key from command line argument.
        api_key_env_var: Name of the environment variable holding the
            selected provider's key (``ANTHROPIC_API_KEY`` for the
            default Anthropic provider, kept unchanged).

    Yields:
        (key_or_none, source_name) tuples.
    """
    yield api_key_arg, "command line"
    yield get_api_key_from_keyring(), "keyring"
    yield os.getenv(api_key_env_var), "environment variable"


def _get_api_key_with_source(
    api_key_arg: str | None,
    api_key_env_var: str = "ANTHROPIC_API_KEY",
    *,
    no_interactive: bool,
) -> tuple[str, str] | tuple[None, None]:
    """Get API key from the first available source.

    Args:
        api_key_arg: API key from the command line argument.
        api_key_env_var: Environment variable to read the key from.
        no_interactive: Disable the interactive keyring prompt.

    Returns:
        (api_key, source) tuple, or (None, None) if not found.
    """
    for key, source in _lazy_api_key_sources(api_key_arg, api_key_env_var):
        if key:
            _warn_if_cli_api_key(source)
            return key, source

    if not no_interactive:
        interactive_key = _prompt_for_api_key()
        if interactive_key:
            return interactive_key, "interactive prompt"

    return None, None


@dataclass(frozen=True)
class _SelectionInputs:
    """The three provider/model selection inputs threaded from a command.

    Bundles the ``--provider`` / ``--model`` flag values and the parsed
    config-file mapping so the orchestrator-init helpers pass one object
    instead of three loose arguments (keeping them under the project's
    argument-count limit).

    Attributes:
        provider_flag: Value of ``--provider`` (or ``None``).
        model_flag: Value of ``--model`` (or ``None``).
        config_data: Parsed config-file mapping (may be empty).
    """

    provider_flag: str | None = None
    model_flag: str | None = None
    config_data: dict[str, str] | None = None


def _resolve_orchestrator_selection(
    inputs: _SelectionInputs,
) -> ProviderSelection | None:
    """Resolve the provider/model selection, reporting any bad input.

    Args:
        inputs: The bundled ``--provider`` / ``--model`` / config-file
            selection inputs.

    Returns:
        The resolved :class:`ProviderSelection`, or ``None`` when the
        provider name is unknown (an error has already been printed).
    """
    try:
        return resolve_provider_selection(
            provider_flag=inputs.provider_flag,
            model_flag=inputs.model_flag,
            config=inputs.config_data or {},
            env=os.environ,
        )
    except ValueError as e:
        # ``e`` already names the supported set ("Supported providers: …"),
        # so we must not append a second copy here (regression: #383).
        console.print(
            f"[red]Error:[/red] {e}",
            style="bold",
        )
        return None


def _build_orchestrator_from_selection(
    selection: ProviderSelection,
    api_key: str,
    source: str,
) -> AIOrchestrator | None:
    """Build an orchestrator from a resolved selection and key.

    Args:
        selection: Resolved provider/model.
        api_key: Resolved API key for the provider.
        source: Human-readable origin of the key (for the status line).

    Returns:
        The constructed :class:`AIOrchestrator`, or ``None`` if the
        provider's optional extra is missing or the key is rejected
        (an actionable error has already been printed).
    """
    try:
        provider = build_provider(
            selection.provider,
            api_key=api_key,
            model=selection.model,
        )
        orchestrator = AIOrchestrator(
            api_key=api_key,
            model=selection.model,
            provider=provider,
        )
    except ProviderUnavailableError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        return None
    except ValueError as e:
        console.print(f"[red]Error:[/red] Invalid API key: {e}", style="bold")
        return None
    console.print(
        f"[green]✓[/green] AI features enabled "
        f"({selection.provider} {selection.model}, key from {source})"
    )
    return orchestrator


def _initialize_orchestrator(
    api_key_arg: str | None = None,
    *,
    no_interactive: bool = False,
    selection_inputs: _SelectionInputs | None = None,
) -> AIOrchestrator | None:
    """Initialize AI orchestrator with a resolved provider/model + key.

    Provider and model are resolved with the precedence CLI flag > env
    (``GREEN_LLM_PROVIDER`` / ``GREEN_LLM_MODEL``) > config file >
    built-in default (Anthropic + the current model id). The API key is
    then read from the *selected* provider's env var
    (``ANTHROPIC_API_KEY`` for Anthropic), keyring, or CLI argument.

    Args:
        api_key_arg: API key from CLI argument.
        no_interactive: Disable interactive prompts.
        selection_inputs: Bundled ``--provider`` / ``--model`` /
            config-file selection inputs. Defaults to an empty bundle,
            which resolves to the built-in Anthropic default.

    Returns:
        AIOrchestrator instance if a provider and key resolve, else None.
    """
    selection = _resolve_orchestrator_selection(
        selection_inputs or _SelectionInputs(),
    )
    if selection is None:
        return None

    api_key, source = _get_api_key_with_source(
        api_key_arg,
        resolve_api_key_env_var(selection.provider),
        no_interactive=no_interactive,
    )
    if api_key is None or source is None:
        return None

    return _build_orchestrator_from_selection(selection, api_key, source)


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
) -> Generator[None]:
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


# Languages with native quality-script templates in ScriptsGenerator.
# The generator falls back to *Python* scripts for anything else, which
# would be wrong for e.g. a PHP project, so the init pipeline skips
# the step instead. Every base.SUPPORTED_LANGUAGES entry now has native
# templates (ruby joined with #373); the gate remains for typo'd or
# future languages.
_SCRIPTS_STEP_LANGUAGES: frozenset[str] = frozenset(
    {
        "python",
        "typescript",
        "go",
        "rust",
        "swift",
        "kotlin",
        "cpp",
        "java",
        "csharp",
        "ruby",
    }
)


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
    Languages without native script templates (none of the supported
    set since ruby joined with #373) are skipped with an informational
    message instead of receiving the generator's Python fallback.

    Args:
        project_path: Project root directory.
        project_name: Name of the project.
        language: Programming language for scripts.
        file_writer: Optional FileWriter for additive behavior.
        subdirectory: If set, write to scripts/{subdirectory}/ instead
            of scripts/. Used for multi-language projects.
    """
    if language not in _SCRIPTS_STEP_LANGUAGES:
        console.print(
            f"[dim]Quality scripts unavailable for {language} "
            f"(supported: {', '.join(sorted(_SCRIPTS_STEP_LANGUAGES))})[/dim]"
        )
        return

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
            project_root=project_path,
        )
        scripts_generator.generate()
    console.print(f"[green]✓[/green] Generated {language} scripts")


def _generate_precommit_step(
    project_path: Path,
    project_name: str,
    language: str,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate pre-commit configuration, merging with existing if present.

    Languages PreCommitGenerator does not support yet (none of the
    supported set since ruby joined with #373) are skipped with an
    informational message instead of aborting the whole init run.
    """
    if language not in PRECOMMIT_LANGUAGE_CONFIGS:
        console.print(
            f"[dim]Pre-commit config unavailable for {language} "
            f"(supported: {', '.join(PRECOMMIT_LANGUAGE_CONFIGS)})[/dim]"
        )
        return

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
    pass2: _Pass2Options | None,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate the CI pipeline.

    Always runs the deterministic template path so a project is never
    missing CI just because the user has no API key.
    ``pass2.orchestrator`` is only used to opt into the legacy AI-tuned
    path for backward compatibility; ``pass2`` as a whole may be
    ``None``, selecting the deterministic defaults. ``project_name`` is
    forwarded to the template renderer so any ``<<% project_name %>>``
    placeholder lands with the real value rather than the empty string.
    ``pass2.windows_ci`` opts into the ``quality-windows`` leg (#388);
    default off leaves the generated workflow unchanged. Languages
    without a CIGenerator config are skipped with an informational
    message instead of aborting init — with kotlin wired in (#358)
    every CLI language has one, so this guard is defensive for future
    additions.
    """
    if language not in CI_LANGUAGE_CONFIGS:
        console.print(
            f"[dim]CI pipeline unavailable for {language} "
            f"(supported: {', '.join(CI_LANGUAGE_CONFIGS)})[/dim]"
        )
        return

    if pass2 is None:
        pass2 = _Pass2Options(orchestrator=None)

    with step_timer("ci"), console.status("Generating CI pipeline..."):
        ci_generator = CIGenerator(
            pass2.orchestrator,
            language,
            project_name=project_name,
        )
        workflow = ci_generator.generate_workflow(windows_ci=pass2.windows_ci)
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


def _write_modular_claude_md(
    generator: ClaudeMdGenerator,
    project_path: Path,
    project_config: dict[str, Any],
    file_writer: FileWriter | None,
) -> ClaudeMdGenerationResult:
    """Render and write the modular ``.claude/`` CLAUDE.md tree (#397).

    Writes the index ``CLAUDE.md`` plus the six ``.claude/docs/*.md`` split
    files. When a ``file_writer`` is supplied, each file goes through its
    conflict-aware path so ``green init`` re-runs preserve user edits.

    Args:
        generator: Configured CLAUDE.md generator.
        project_path: Target project root directory.
        project_config: Project configuration passed to the generator.
        file_writer: Optional conflict-aware writer; direct writes when None.

    Returns:
        The index generation result (carries token usage telemetry).
    """
    index_result, docs = generator.render_modular(project_config)
    index_file = project_path / "CLAUDE.md"
    docs_dir = project_path / ".claude" / "docs"
    if file_writer is not None:
        file_writer.write_file(index_file, index_result.content)
        for name, content in docs.items():
            file_writer.write_file(docs_dir / f"{name}.md", content)
    else:
        index_file.write_text(index_result.content, encoding="utf-8")
        docs_dir.mkdir(parents=True, exist_ok=True)
        for name, content in docs.items():
            (docs_dir / f"{name}.md").write_text(content, encoding="utf-8")
    return index_result


def _claude_context_project_config(
    project_name: str,
    language: str,
) -> dict[str, Any]:
    """Build the project config shared by every agent-context render.

    Single source for the config dict used by the CLAUDE.md init step,
    the ``enhance`` re-tune path, and the non-Claude agent-context
    emitters (#387) — the same canonical content inputs everywhere.

    Args:
        project_name: Name of the target project.
        language: Primary project language.

    Returns:
        Project config with ``project_name``, ``language``, ``scripts``,
        and ``skills`` keys.
    """
    return {
        "project_name": project_name,
        "language": language,
        "scripts": list(_CLAUDE_MD_SCRIPTS),
        "skills": REQUIRED_SKILLS.copy(),
    }


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
        project_config = _claude_context_project_config(project_name, language)
        _write_modular_claude_md(
            claude_md_generator,
            project_path,
            project_config,
            file_writer,
        )
    console.print("[green]✓[/green] Generated CLAUDE.md (modular .claude/docs)")


def _generate_agent_context_step(
    project_path: Path,
    project_name: str,
    language: str,
    agent_targets: tuple[str, ...],
    file_writer: FileWriter | None = None,
) -> None:
    """Emit agent-context files for the non-Claude targets (#387).

    Renders the shared canonical content (the same split docs and
    subagent role descriptions the Claude target uses) into each
    selected non-Claude format: ``AGENTS.md`` for ``agents-md``,
    ``CONVENTIONS.md`` + ``.aider.conf.yml`` for ``aider``. Fully
    deterministic — no orchestrator involved — so it runs identically
    online and offline. When only the ``claude`` target is selected
    this is a no-op, keeping the default output byte-for-byte
    unchanged.
    """
    extra_targets = tuple(t for t in agent_targets if t != TARGET_CLAUDE)
    if not extra_targets:
        return

    with step_timer("agent_context"), console.status("Generating agent context..."):
        content = load_agent_context_content(
            _claude_context_project_config(project_name, language)
        )
        emitted = _emit_agent_context_targets(
            project_path, extra_targets, content, file_writer
        )
    console.print(f"[green]✓[/green] Generated agent context: {', '.join(emitted)}")


def _emit_agent_context_targets(
    project_path: Path,
    targets: tuple[str, ...],
    content: AgentContextContent,
    file_writer: FileWriter | None,
) -> list[str]:
    """Write every file the selected non-Claude targets render.

    Args:
        project_path: Target project root directory.
        targets: Non-Claude agent-context targets to emit.
        content: The loaded shared agent-context content.
        file_writer: Optional conflict-aware writer (additive init);
            direct LF-only writes when ``None``.

    Returns:
        The emitted filenames, in emission order.
    """
    emitted: list[str] = []
    for target in targets:
        for filename, text in render_target_files(target, content).items():
            target_file = project_path / filename
            if file_writer is not None:
                file_writer.write_file(target_file, text)
            else:
                target_file.write_text(text, encoding="utf-8", newline="\n")
            emitted.append(filename)
    return emitted


def _generate_architecture_step(
    project_path: Path,
    project_name: str,
    language: str,
    file_writer: FileWriter | None = None,
) -> None:
    """Generate architecture rules.

    Architecture configuration is fully deterministic (import-linter for
    Python, dependency-cruiser for TypeScript, go-arch-lint for Go,
    cargo-deny for Rust, SwiftLint custom rules for Swift, a Konsist test
    for Kotlin, an include-boundary checker for C/C++, an ArchUnit test
    for Java, a NetArchTest test for C#, a Packwerk package config for
    Ruby). Runs regardless of API key availability; only Python,
    TypeScript, Go, Rust, Swift, Kotlin, C/C++, Java, C#, and Ruby
    projects produce output. The previous ``orchestrator`` argument was
    unused and has been removed from this private helper.
    """
    supported = {
        "python",
        "typescript",
        "go",
        "rust",
        "swift",
        "kotlin",
        "cpp",
        "java",
        "csharp",
        "ruby",
    }
    if language not in supported:
        # The generator only supports these languages; surface a dim info
        # line so users understand why no architecture rules were generated
        # for, e.g., a PHP project rather than seeing silence.
        console.print(
            f"[dim]Architecture rules unavailable for {language} "
            f"(supported: {', '.join(sorted(supported))})[/dim]"
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


def _write_initial_metrics_json(
    docs_dir: Path,
    project_name: str,
    config: MetricsGenerationConfig,
    precommit_hooks_total: int,
    ci_jobs_total: int,
) -> None:
    """Write the initial ``docs/metrics.json`` payload for the dashboard.

    Args:
        docs_dir: The project's ``docs/`` directory (must exist).
        project_name: Name of the project recorded in the payload.
        config: Metrics generation config supplying the thresholds.
        precommit_hooks_total: Number of pre-commit hooks configured.
        ci_jobs_total: Number of CI jobs configured.
    """
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
            "precommit_status": precommit_status(precommit_hooks_total),
            "ci_status": ci_status(ci_jobs_total),
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
    (docs_dir / "metrics.json").write_text(
        json.dumps(initial_metrics, indent=2),
        encoding="utf-8",
    )


def _copy_metrics_assets(project_path: Path, project_name: str) -> tuple[bool, bool]:
    """Copy the metrics workflow and collection script into the project.

    Args:
        project_path: Target project root directory.
        project_name: Project name substituted into the workflow file.

    Returns:
        ``(missing_workflow, missing_script)`` flags — ``True`` when the
        corresponding source asset could not be found in the sgsg install.
    """
    workflows_dir = project_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)

    sgsg_root = Path(__file__).parent.parent
    sgsg_workflow = sgsg_root / ".github" / "workflows" / "metrics.yml"
    missing_workflow = not sgsg_workflow.exists()
    if not missing_workflow:
        target_workflow = workflows_dir / "metrics.yml"
        shutil.copy(sgsg_workflow, target_workflow)
        workflow_content = target_workflow.read_text(encoding="utf-8")
        workflow_content = workflow_content.replace(
            "start-green-stay-green", project_name
        )
        target_workflow.write_text(workflow_content, encoding="utf-8")

    scripts_dir = project_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    sgsg_script = sgsg_root / "scripts" / "collect_metrics.py"
    missing_script = not sgsg_script.exists()
    if not missing_script:
        shutil.copy(sgsg_script, scripts_dir / "collect_metrics.py")

    return missing_workflow, missing_script


def _generate_metrics_dashboard_step(
    project_path: Path,
    project_name: str,
    language: str,
) -> None:
    """Generate live metrics dashboard and workflow.

    Languages MetricsGenerator does not support yet (none of the
    supported set since ruby joined with #373) are skipped with an
    informational message instead of aborting init when
    ``--enable-live-dashboard`` is passed.
    """
    if language not in METRICS_LANGUAGE_TOOLS:
        console.print(
            f"[dim]Metrics dashboard unavailable for {language} "
            f"(supported: {', '.join(METRICS_LANGUAGE_TOOLS)})[/dim]"
        )
        return

    with step_timer("metrics"), console.status("Generating metrics dashboard..."):
        precommit_hooks_total = MetricsGenerator.count_precommit_hooks(
            project_path / ".pre-commit-config.yaml"
        )
        ci_jobs_total = count_ci_jobs(project_path / ".github" / "workflows")
        config = MetricsGenerationConfig(
            language=language,
            project_name=project_name,
            coverage_threshold=90,
            branch_coverage_threshold=85,
            mutation_threshold=80,
            complexity_threshold=10,
            doc_coverage_threshold=95,
            precommit_hooks_total=precommit_hooks_total,
            ci_jobs_total=ci_jobs_total,
            enable_dashboard=True,
            enable_badges=True,
        )

        generator = MetricsGenerator(None, config)

        docs_dir = project_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        generator.write_dashboard(docs_dir)
        _write_initial_metrics_json(
            docs_dir,
            project_name,
            config,
            precommit_hooks_total,
            ci_jobs_total,
        )

        missing_workflow, missing_script = _copy_metrics_assets(
            project_path, project_name
        )

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


@dataclass(frozen=True)
class _Pass2Options:
    """Inputs that select what Pass 2 of init emits and how.

    Bundles the orchestrator (which flips each step between "render
    template" and "AI-tune the template") with the resolved ``--agent``
    context targets (#387). Grouping them keeps
    :func:`_generate_project_files` and :func:`_generate_pass2_polish`
    below the ``PLR0913`` threshold — same pattern as
    :class:`_EnhanceRunOptions`.

    Attributes:
        orchestrator: Optional AI orchestrator; ``None`` selects the
            deterministic baseline path for every step.
        agent_targets: Resolved agent-context targets in canonical
            order. Defaults to Claude only (the backward-compatible
            default).
        windows_ci: Opt-in ``--windows-ci`` flag (#388): append the
            ``quality-windows`` leg to the generated CI workflow.
            Default off keeps the generated CI unchanged.
    """

    orchestrator: AIOrchestrator | None
    agent_targets: tuple[str, ...] = (TARGET_CLAUDE,)
    windows_ci: bool = False


def _generate_pass2_polish(
    project_path: Path,
    project_name: str,
    language: str,
    pass2: _Pass2Options,
    file_writer: FileWriter | None = None,
) -> None:
    """Run Pass 2 of the optimization roadmap's two-pass init model.

    Generates the artifacts whose output is *enhanced* by an
    :class:`AIOrchestrator` when one is available. After Phase 1 every
    one of these has a deterministic baseline path too, so the function
    runs unconditionally; the orchestrator is what flips each step
    between "render template" and "AI-tune the template". When
    ``pass2.orchestrator`` is ``None`` (``--offline`` / ``--no-enhance``
    / no API key), every step still runs and produces a complete project
    via the deterministic path.

    The Claude context artifacts (CLAUDE.md tree + subagent profiles)
    are emitted only when the ``claude`` agent target is selected;
    non-Claude targets are emitted by
    :func:`_generate_agent_context_step` (#387). CI, review workflow,
    and architecture rules are target-independent and always run.

    The roadmap (plans/2026-05-03-claude-init-optimization-roadmap.md)
    calls this Pass 2 to distinguish it from Pass 1's per-language
    scaffold steps.
    """
    orchestrator = pass2.orchestrator
    emit_claude = TARGET_CLAUDE in pass2.agent_targets
    _generate_ci_step(project_path, project_name, language, pass2, file_writer)
    _generate_review_step(project_path, file_writer)
    if emit_claude:
        _generate_claude_md_step(
            project_path, project_name, language, orchestrator, file_writer
        )
    _generate_architecture_step(project_path, project_name, language, file_writer)
    if emit_claude:
        _generate_subagents_step(
            project_path, project_name, language, orchestrator, file_writer
        )
    _generate_agent_context_step(
        project_path, project_name, language, pass2.agent_targets, file_writer
    )


def _generate_project_files(
    project_path: Path,
    project_name: str,
    languages: tuple[str, ...],
    pass2: _Pass2Options,
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
        pass2: Pass 2 options bundling the optional AI orchestrator
            (``None`` indicates fallback to template mode) and the
            resolved agent-context targets (#387).
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
                pass2,
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


# "python" is intentionally absent: its venv activation line depends on the
# user's shell, so its steps are built dynamically in _get_setup_instructions.
_LANG_SETUP_STEPS: dict[str, list[str]] = {
    "typescript": ["npm install"],
    "go": ["go mod download"],
    "rust": ["cargo build"],
    "swift": ["swift package resolve", "swift build"],
    # The Gradle wrapper jar is a binary the generator never writes, so
    # the first step materialises it from a local Gradle install (#356).
    "kotlin": ["gradle wrapper", "./gradlew build"],
    # Plain CMake + Conan builds the pure-logic library and Catch2 tests;
    # .tpk packaging needs Tizen Studio, which init cannot install (#361).
    "cpp": [
        "conan install . --output-folder=build --build=missing",
        (
            "cmake -B build -S . "
            "-DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake "
            "-DCMAKE_BUILD_TYPE=Release"
        ),
        "cmake --build build",
        "ctest --test-dir build",
    ],
    # Plain Maven builds and tests the pure-logic half of the legacy
    # Android Wear scaffold; the watch APK needs Android tooling
    # (Android Studio / Gradle), which init cannot install (#366).
    "java": ["mvn test"],
    # `dotnet test` restores, builds (Roslyn analyzers as errors), and
    # runs the xUnit suite in one invocation — the csproj owns the whole
    # quality policy (#370), so the single command verifies the scaffold.
    "csharp": ["dotnet test"],
    # bundle install provisions the pinned quality gems (rspec,
    # rubocop, simplecov, bundler-audit, packwerk) and `bundle exec
    # rspec` verifies the scaffold (#373) — the csharp #371 lesson:
    # never leave a supported language on the unknown-language default
    # path.
    "ruby": ["bundle install", "bundle exec rspec"],
}


def _venv_activation_command(os_name: str, env: Mapping[str, str]) -> str:
    r"""Return the venv activation command for the user's shell.

    The default ``source .venv/bin/activate`` is bash/zsh syntax and
    silently fails in fish, csh/tcsh, cmd.exe, and PowerShell, so a
    best-effort heuristic detection is applied:

    - Windows (``os_name == "nt"``): a ``PSModulePath`` environment
      variable is treated as a PowerShell indicator (``Activate.ps1``);
      otherwise the cmd.exe form (``.venv\Scripts\activate``) is used.
    - POSIX: the basename of the ``SHELL`` environment variable selects
      ``activate.fish`` for fish and ``activate.csh`` for csh/tcsh.
    - Unknown or missing shells fall back to the bash/zsh form, matching
      the historical default.

    Args:
        os_name: Platform identifier, typically ``os.name`` ("nt" on
            Windows, "posix" elsewhere).
        env: Environment mapping to inspect, typically ``os.environ``.

    Returns:
        Shell command string that activates ``.venv`` in the detected
        shell.
    """
    if os_name == "nt":
        if "PSModulePath" in env:
            return ".venv\\Scripts\\Activate.ps1"
        return ".venv\\Scripts\\activate"
    shell = PurePosixPath(env.get("SHELL", "")).name
    if shell == "fish":
        return "source .venv/bin/activate.fish"
    if shell in {"csh", "tcsh"}:
        return "source .venv/bin/activate.csh"
    return "source .venv/bin/activate"


def _quote_path_for_shell(os_name: str, path: Path) -> str:
    r"""Quote ``path`` for copy-paste into the platform's shell.

    ``shlex.quote`` emits POSIX single-quote syntax, which cmd.exe does
    not understand at all (``cd 'C:\my project'`` fails) and which is
    unnecessary in PowerShell. Both Windows shells accept double
    quotes, and ``"`` cannot appear in Windows file names, so on
    Windows the path is wrapped verbatim with no escaping needed.

    Args:
        os_name: Platform identifier, typically ``os.name`` ("nt" on
            Windows, "posix" elsewhere).
        path: Filesystem path to quote.

    Returns:
        The path quoted for safe copy-paste into the platform's shell.
    """
    if os_name == "nt":
        return f'"{path}"'
    return shlex.quote(str(path))


def _check_all_command(os_name: str) -> str:
    """Return the command that runs a generated project's check-all gate.

    On POSIX the generated ``scripts/check-all.sh`` carries the
    executable bit (see ``utils.fs.make_executable``) and is invoked
    directly. Windows has no executable bit, so the documented
    cross-platform path (#386) is to run the POSIX script through Git
    Bash, which needs no executable bit because bash receives the
    script path as an argument. The generated ``scripts/README.md``
    additionally documents the toolchain-native command each gate
    wraps for environments without bash.

    Args:
        os_name: Platform identifier, typically ``os.name``.

    Returns:
        The shell command that runs all quality checks in the
        generated project.
    """
    if os_name == "nt":
        return "bash scripts/check-all.sh"
    return "./scripts/check-all.sh"


def _get_setup_instructions(
    languages: Sequence[str],
    project_path: Path,
    *,
    os_name: str,
    env: Mapping[str, str],
) -> list[str]:
    """Return language-specific setup commands for a generated project.

    For multi-language projects, language-specific steps are concatenated
    in the order the languages appear. Shared steps (cd, pre-commit
    install, check-all) are not duplicated. Every shell-sensitive line
    is platform-aware via one canonical helper each: cd quoting
    (:func:`_quote_path_for_shell`), venv activation
    (:func:`_venv_activation_command`), and the check-all invocation
    (:func:`_check_all_command`). Shell detection is a heuristic based
    on ``os_name`` and the ``SHELL`` / ``PSModulePath`` environment
    variables, defaulting to the bash/zsh form when the shell cannot
    be identified.

    Args:
        languages: Ordered sequence of programming languages (python,
            typescript, go, rust, etc.). May be empty for a sensible
            default.
        project_path: Path to the generated project directory.
        os_name: Platform identifier, typically ``os.name``. Passed
            explicitly so tests never patch the real ``os.name``,
            which breaks ``pathlib.Path`` construction (#380).
        env: Environment mapping for shell detection, typically
            ``os.environ``.

    Returns:
        Ordered list of shell commands to set up and verify the project.
    """
    cd = f"cd {_quote_path_for_shell(os_name, project_path)}"
    common_tail = ["pre-commit install", _check_all_command(os_name)]

    middle: list[str] = []
    for lang in dict.fromkeys(languages):
        if lang == "python":
            middle.extend(
                [
                    "python -m venv .venv",
                    _venv_activation_command(os_name, env),
                    "pip install -r requirements.txt -r requirements-dev.txt",
                ]
            )
        else:
            middle.extend(_LANG_SETUP_STEPS.get(lang, []))

    return [cd, *middle, *common_tail]


def _print_setup_instructions(languages: Sequence[str], project_path: Path) -> None:
    """Print platform-appropriate setup commands for a generated project.

    The command list comes from :func:`_get_setup_instructions` for the
    live platform. On Windows (via the patchable ``is_windows`` seam,
    #380) a note explains that the generated POSIX scripts run through
    Git Bash and points at the generated ``scripts/README.md``, which
    documents the Windows and toolchain-native invocation for every
    gate (#386).

    Args:
        languages: Ordered sequence of programming languages for the
            project.
        project_path: Path to the generated project directory.
    """
    console.print("\nTo get started, run:")
    for cmd in _get_setup_instructions(
        languages, project_path, os_name=os.name, env=os.environ
    ):
        console.print(f"  {cmd}")
    if is_windows():
        console.print(
            "\nNote: 'bash scripts/check-all.sh' runs the quality gate "
            "through Git Bash (included with Git for Windows). The "
            "generated scripts/README.md documents the Windows "
            "invocation and the toolchain-native cross-platform "
            "command for every gate."
        )
    console.print()


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
    _print_setup_instructions(languages, project_path)
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
    selection_inputs: _SelectionInputs | None = None,
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

    orchestrator = _initialize_orchestrator(
        api_key,
        no_interactive=no_interactive,
        selection_inputs=selection_inputs,
    )

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
        console.print(
            "    2. Set ANTHROPIC_API_KEY env var (or store in keyring "
            "via the next prompt)"
        )
        console.print("    3. Re-run: green enhance  (no need to re-init)\n")
    return orchestrator


def _validate_agent_target(value: str) -> str:
    """Normalize and validate one ``--agent`` value (#387).

    Args:
        value: A single agent-target name from the CLI.

    Returns:
        The lower-cased target name if it is recognised.

    Raises:
        typer.BadParameter: If the target is not in
            :data:`AGENT_CONTEXT_TARGETS`.
    """
    normalized = value.strip().lower()
    if normalized not in AGENT_CONTEXT_TARGETS:
        valid = ", ".join(AGENT_CONTEXT_TARGETS)
        msg = f"unknown agent target {value!r}; choose from: {valid}"
        raise typer.BadParameter(msg)
    return normalized


def _resolve_agent_targets(agent: list[str] | None) -> tuple[str, ...]:
    """Resolve the ``--agent`` flag list into context targets (#387).

    Accepts both repeated flags (``--agent claude --agent agents-md``)
    and comma-separated values (``--agent claude,agents-md``), matching
    the ``-l`` multi-language flag's ergonomics. Omitting the flag
    selects the backward-compatible Claude default.

    Args:
        agent: Raw values from the typer option, or ``None``.

    Returns:
        A deduplicated tuple of target names in the canonical order
        defined by :data:`AGENT_CONTEXT_TARGETS`.

    Raises:
        typer.BadParameter: If any target is unknown, or the flag was
            passed but resolves to no targets.
    """
    if not agent:
        return (TARGET_CLAUDE,)
    resolved = _canonicalize_agent_targets(_split_target_pieces(agent))
    if not resolved:
        msg = "--agent requires at least one target value"
        raise typer.BadParameter(msg)
    return resolved


def _canonicalize_agent_targets(pieces: list[str]) -> tuple[str, ...]:
    """Validate and dedupe agent-target pieces into canonical order.

    Args:
        pieces: Individual target values (already split on commas).

    Returns:
        The recognised targets in :data:`AGENT_CONTEXT_TARGETS` order.

    Raises:
        typer.BadParameter: If any piece is not a known target.
    """
    requested = {_validate_agent_target(piece) for piece in pieces}
    return tuple(t for t in AGENT_CONTEXT_TARGETS if t in requested)


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


def _validate_windows_ci_language(
    *,
    windows_ci: bool,
    primary_language: str,
) -> None:
    """Fail fast when ``--windows-ci`` targets an unsupported language.

    The generated CI workflow follows the project's primary language
    (the first ``-l`` value), so the Windows leg is validated against
    that language. Validation runs before any file is generated — and
    before the ``--dry-run`` preview — so the user learns about the
    unsupported combination immediately.

    Args:
        windows_ci: ``True`` if ``--windows-ci`` was passed.
        primary_language: The resolved primary project language.

    Raises:
        typer.Exit: If the flag was passed for a language without a
            supported Windows CI leg (see
            :data:`~start_green_stay_green.generators.ci_windows.WINDOWS_CI_LANGUAGES`).
    """
    if not windows_ci or primary_language in WINDOWS_CI_LANGUAGES:
        return
    supported = ", ".join(WINDOWS_CI_LANGUAGES)
    console.print(
        f"[red]Error:[/red] --windows-ci is not supported for "
        f"{primary_language!r} (supported: {supported}). The gates for "
        "this language cannot run on a windows-latest runner — see "
        "generators/ci_windows.py for the per-language rationale.",
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
    agent: Annotated[
        list[str] | None,
        typer.Option(
            "--agent",
            help=(
                "Agent-context format(s) to generate. Repeat or "
                "comma-separate for multiple targets: --agent claude "
                "--agent agents-md. Choices: claude (default; CLAUDE.md "
                "+ .claude/), agents-md (AGENTS.md, the open "
                "agent-context convention), aider (CONVENTIONS.md + "
                ".aider.conf.yml). All formats render the same shared "
                "content."
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
            hidden=True,
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
    windows_ci: Annotated[
        bool,
        typer.Option(
            "--windows-ci",
            help=(
                "Add an opt-in windows-latest job to the generated CI "
                "workflow that runs the quality gates through Git Bash "
                "(bash scripts/<gate>.sh). Default off: without this "
                "flag the generated CI is unchanged and uses no Windows "
                "runner minutes. Applies to the primary language's "
                "workflow; not supported for swift, cpp, or kotlin."
            ),
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
    provider: provider_option = None,
    model: model_option = None,
) -> None:
    """Initialize a new project with quality controls.

    Generates a complete project structure with CI/CD, quality checks,
    AI subagents, and documentation pre-configured.

    AI-powered features are optional and require a Claude API key.
    Without a key, the tool generates reference templates instead.

    Args:
        project_name: Name of the project.
        language: Primary programming language.
        agent: Agent-context format(s) to generate (``--agent``).
            Defaults to Claude (``CLAUDE.md`` + ``.claude/``); also
            supports ``agents-md`` and ``aider``, alone or combined.
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
        windows_ci: Opt into a ``quality-windows`` CI job that runs the
            generated project's quality gates on ``windows-latest``
            through Git Bash (#388). Default off leaves the generated
            workflow unchanged.
        timing_json: Optional path to write a timing/telemetry JSON report.
        config: Configuration file path.
        provider: Optional LLM provider override (``--provider``).
        model: Optional model override (``--model``).

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
    resolved_agents = _resolve_agent_targets(agent)
    _validate_windows_ci_language(
        windows_ci=windows_ci,
        primary_language=resolved_languages[0],
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
            resolved_project_name,
            ", ".join(resolved_languages),
            project_path,
            resolved_agents,
        )
        return

    orchestrator = _resolve_pass2_orchestrator(
        api_key=api_key,
        offline=offline,
        no_enhance=no_enhance,
        no_interactive=no_interactive,
        selection_inputs=_SelectionInputs(
            provider_flag=provider,
            model_flag=model,
            config_data=config_data,
        ),
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
            _Pass2Options(
                orchestrator=orchestrator,
                agent_targets=resolved_agents,
                windows_ci=windows_ci,
            ),
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
    # Kotlin DSL manifests before Groovy build.gradle: a Wear OS scaffold
    # (#356) ships settings.gradle.kts / build.gradle.kts only.
    ("settings.gradle.kts", "kotlin"),
    ("build.gradle.kts", "kotlin"),
    ("build.gradle", "java"),
    ("Gemfile", "ruby"),
    ("composer.json", "php"),
    ("Package.swift", "swift"),
    # cpp probes come last: tizen-manifest.xml and conanfile.txt are
    # unambiguous, but CMakeLists.txt also appears in other ecosystems'
    # projects (e.g. Rust or Swift packages vendoring native code), so
    # every more specific manifest above must win first (#361).
    ("tizen-manifest.xml", "cpp"),
    ("conanfile.txt", "cpp"),
    ("CMakeLists.txt", "cpp"),
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
    selection_inputs: _SelectionInputs | None = None,
) -> AIOrchestrator:
    """Resolve an :class:`AIOrchestrator` for the ``enhance`` command.

    Unlike ``init``, ``enhance`` cannot fall back to a deterministic
    path — re-tuning is the entire point. If no API key is available,
    fail fast with an actionable message instead of writing an empty
    "tuning" that silently no-ops.

    Args:
        api_key: Optional CLI-supplied key.
        no_interactive: Skip any keyring prompts.
        selection_inputs: Bundled ``--provider`` / ``--model`` /
            config-file selection inputs.

    Returns:
        A real ``AIOrchestrator`` ready to dispatch.

    Raises:
        typer.Exit: With code 1 if no key could be resolved.
    """
    orchestrator = _initialize_orchestrator(
        api_key,
        no_interactive=no_interactive,
        selection_inputs=selection_inputs,
    )
    if orchestrator is None:
        console.print(
            "[red]Error:[/red] `green enhance` requires an API key for the "
            "selected provider — there is no deterministic fallback for "
            "AI-tuned artifacts.\n  Set ANTHROPIC_API_KEY (or store one in "
            "the keyring on first run).",
            style="bold",
        )
        raise typer.Exit(code=1)
    return orchestrator


# Single source of truth for the script list embedded in the CLAUDE.md prompt.
_CLAUDE_MD_SCRIPTS: tuple[str, ...] = (
    "check-all.sh",
    "test.sh",
    "lint.sh",
    "format.sh",
    "security.sh",
    "mutation.sh",
)


def _read_reference_or_warn(path: Path, label: str) -> str:
    """Read a reference file or print a dim warning and return ``""``.

    The hash helpers must remain crash-free even on a broken install
    (missing submodule, moved file, etc.) — see Phase 3c reviewer
    note. But silent fallback to an empty string would let the empty
    hash get persisted, after which every subsequent re-tune skips
    permanently with no user-visible signal. Print a warning so the
    user can spot the broken install while still preserving the
    no-crash contract.
    """
    if path.is_file():
        return path.read_text(encoding="utf-8")
    console.print(
        f"[yellow]warning:[/yellow] reference file missing — "
        f"{label}: {path}\n"
        f"  This will produce an empty-input hash and may suppress "
        f"future re-tunes. Check your install."
    )
    return ""


def _hash_claude_md_inputs(project_name: str, language: str) -> str:
    """Hash the inputs that drive a ``CLAUDE.md`` re-tune.

    Captures everything that would alter the model's output: the
    reference template content (so updates to the canonical template
    invalidate stale tunes), plus the project metadata (name +
    language + the script and skill lists baked into the prompt).
    """
    project_root = Path(__file__).parent.parent
    reference = project_root / "reference" / "claude" / "CLAUDE.md"
    template_bytes = _read_reference_or_warn(reference, "CLAUDE.md template")
    return hash_inputs(
        [
            "claude-md\x00",
            f"project_name={project_name}\x00",
            f"language={language}\x00",
            # Declaration order is authoritative — same order the prompt sees.
            f"scripts={','.join(_CLAUDE_MD_SCRIPTS)}\x00",
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
        body = _read_reference_or_warn(source_path, f"subagent '{agent_name}'")
        parts.extend((f"agent={agent_name}\x00", body))
    return hash_inputs(parts)


def _compute_target_source_hash(
    target: str,
    project_name: str,
    language: str,
) -> str:
    """Look the target up in the registry and call its hash helper."""
    spec = _ENHANCE_DISPATCH.get(target)
    if spec is None:
        msg = f"unknown target: {target}"
        raise ValueError(msg)
    hash_helper: Callable[[str, str], str] = globals()[spec.hash_helper_name]
    return hash_helper(project_name, language)


@dataclass(frozen=True)
class _EnhanceProjectContext:
    """Project metadata threaded through the enhance dispatchers.

    Bundles the three identifiers that every enhance helper needs to
    know about the project under tune: where it lives, what it's
    called, and what language preset to use. Grouping them keeps the
    enhance pipeline helpers (:func:`_enhance_claude_md`,
    :func:`_enhance_subagents`, :func:`_dispatch_enhance_targets`,
    :func:`_run_enhance_pipeline`, :func:`_run_enhance_batch`, and
    :func:`_submit_subagent_batch_cli`) below the ``PLR0913``
    threshold without splitting concerns. See issues #316 and #326.
    """

    project_path: Path
    project_name: str
    language: str


@dataclass(frozen=True)
class _EnhanceRunOptions:
    """Per-invocation behaviour flags for the enhance pipeline.

    Bundles the three knobs that control *how* a ``green enhance`` run
    writes (or doesn't write) its output: ``dry_run`` skips writes but
    keeps the API calls, ``force`` bypasses the unchanged-source skip,
    and ``file_writer`` carries the conflict-resolution policy.
    Companion to :class:`_EnhanceProjectContext` (which carries *what*
    is being tuned) so :func:`_dispatch_enhance_targets` and
    :func:`_run_enhance_pipeline` stay below the ``PLR0913`` threshold.
    See issue #326.
    """

    dry_run: bool
    force: bool
    file_writer: FileWriter | None


def _enhance_claude_md(
    project: _EnhanceProjectContext,
    orchestrator: AIOrchestrator,
    *,
    dry_run: bool,
    file_writer: FileWriter | None,
) -> None:
    """Re-tune the modular ``CLAUDE.md`` tree against the existing project.

    Mirrors :func:`_generate_claude_md_step`'s tuning path but writes
    to the existing project (``project.project_path``) rather than a
    fresh scaffold. Emits the index ``CLAUDE.md`` plus the six
    ``.claude/docs/*.md`` split files. ``dry_run`` skips the writes but
    still runs the API call so the user sees the full token-usage
    telemetry (and any errors) they'd see for real.
    """
    with step_timer("enhance_claude_md"), console.status("Re-tuning CLAUDE.md..."):
        claude_md_generator = ClaudeMdGenerator(orchestrator)
        project_config = _claude_context_project_config(
            project.project_name,
            project.language,
        )
        if dry_run:
            index_result, _docs = claude_md_generator.render_modular(project_config)
            target = project.project_path / "CLAUDE.md"
            console.print(
                f"[dim]--dry-run: would rewrite {target} and "
                f".claude/docs/ ({len(index_result.content):,} index chars).[/dim]"
            )
            return
        _write_modular_claude_md(
            claude_md_generator,
            project.project_path,
            project_config,
            file_writer,
        )
    console.print("[green]✓[/green] Re-tuned CLAUDE.md (modular .claude/docs)")


def _enhance_subagents(
    project: _EnhanceProjectContext,
    orchestrator: AIOrchestrator,
    *,
    dry_run: bool,
    file_writer: FileWriter | None,
) -> None:
    """Re-tune every subagent against the existing project.

    Same parallel-fan-out path as Pass 2 of init, but writes back to
    ``<project>/.claude/agents`` instead of generating it fresh.
    """
    target_dir = project.project_path / ".claude" / "agents"
    target_dir.mkdir(parents=True, exist_ok=True)

    with step_timer("enhance_subagents"), console.status("Re-tuning subagents..."):
        subagents_generator = SubagentsGenerator(orchestrator)
        target_context = (
            f"Project: {project.project_name}, "
            f"Language: {project.language}, "
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


@dataclass(frozen=True)
class _EnhanceTargetSpec:
    """Per-target wiring for ``green enhance``.

    Single source of truth pairing the skip message, the tune helper,
    and the source-hash helper for one target. Holding all three in
    one record means a new target requires exactly one entry in
    :data:`_ENHANCE_DISPATCH` — there is no separate hash table to
    forget to update. Helpers are stored by *name* (not function
    reference) so test ``patch("cli._enhance_…")`` decorations are
    honoured at call time via ``globals()[name]``.
    """

    skip_message: str
    helper_name: str
    hash_helper_name: str


_ENHANCE_DISPATCH: dict[str, _EnhanceTargetSpec] = {
    "claude-md": _EnhanceTargetSpec(
        skip_message=(
            "[dim]CLAUDE.md unchanged since last successful tune — "
            "skipping (use --force to re-tune anyway).[/dim]"
        ),
        helper_name="_enhance_claude_md",
        hash_helper_name="_hash_claude_md_inputs",
    ),
    "subagents": _EnhanceTargetSpec(
        skip_message=(
            "[dim]Subagents unchanged since last successful tune — "
            "skipping (use --force to re-tune anyway).[/dim]"
        ),
        helper_name="_enhance_subagents",
        hash_helper_name="_hash_subagents_inputs",
    ),
}


def _assert_enhance_dispatch_intact() -> None:
    """Fail at import time if a dispatch entry references a missing helper.

    The registry looks helpers up by *name* (so test ``patch``
    decorators can intercept), which trades static-analysis safety
    for late-binding flexibility. This guard rebuilds the missing
    safety net at import time so a typo in either ``helper_name`` or
    ``hash_helper_name`` is caught as soon as the module loads, not
    at first ``green enhance`` invocation.
    """
    missing: list[str] = [
        name
        for spec in _ENHANCE_DISPATCH.values()
        for name in (spec.helper_name, spec.hash_helper_name)
        if name not in globals()
    ]
    if missing:
        msg = (
            f"_ENHANCE_DISPATCH references undefined helper(s): "
            f"{', '.join(missing)}"
        )
        raise RuntimeError(msg)


_assert_enhance_dispatch_intact()


def _dispatch_enhance_targets(
    targets: tuple[str, ...],
    *,
    project: _EnhanceProjectContext,
    orchestrator: AIOrchestrator,
    state: EnhanceState,
    options: _EnhanceRunOptions,
) -> list[str]:
    """Drive Pass 2 across each selected target with the skip/force logic.

    Each target's source hash is computed here (the hash helpers are
    pure functions of the project name + language) and reused for both
    the skip check and the ``mark_completed`` record.

    Returns the list of target names that were skipped because the
    source hash matched a stored completion. The caller uses that to
    decide whether the state file is worth re-writing.
    """
    skipped: list[str] = []
    for target in targets:
        spec = _ENHANCE_DISPATCH[target]
        target_hash = _compute_target_source_hash(
            target,
            project.project_name,
            project.language,
        )
        if not options.force and state.is_unchanged(target, target_hash):
            console.print(spec.skip_message)
            skipped.append(target)
            continue
        # Late-bound lookup so test ``patch("cli._enhance_claude_md")``
        # decorations are honoured.
        helper: Callable[..., None] = globals()[spec.helper_name]
        helper(
            project,
            orchestrator,
            dry_run=options.dry_run,
            file_writer=options.file_writer,
        )
        if not options.dry_run:
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
    if len(skipped) == len(selected_targets):
        return
    save_state(project_path, state)


def _print_enhance_summary(*, project_name: str, dry_run: bool) -> None:
    """Print the closing one-liner for an ``enhance`` invocation."""
    if dry_run:
        console.print("\n[green]✓[/green] Dry run complete — no files written.")
    else:
        console.print(f"\n[green]✓[/green] Enhancement complete: {project_name}")


def _run_enhance_pipeline(
    *,
    project: _EnhanceProjectContext,
    selected_targets: tuple[str, ...],
    orchestrator: AIOrchestrator,
    options: _EnhanceRunOptions,
) -> None:
    """Execute the full Pass 2 pipeline + persist state on success."""
    console.print(
        f"[dim]Enhancing project: {project.project_name} ({project.language})"
        f"  →  targets: {', '.join(selected_targets)}"
        f"{'  [DRY RUN]' if options.dry_run else ''}[/dim]"
    )
    state = load_state(project.project_path)
    skipped = _dispatch_enhance_targets(
        selected_targets,
        project=project,
        orchestrator=orchestrator,
        state=state,
        options=options,
    )
    _persist_enhance_state(
        project.project_path,
        state,
        skipped=skipped,
        selected_targets=selected_targets,
        dry_run=options.dry_run,
    )
    _print_enhance_summary(
        project_name=project.project_name,
        dry_run=options.dry_run,
    )


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


_BATCH_SUPPORTED_TARGETS: frozenset[str] = frozenset({"subagents"})


def _validate_batch_targets(selected_targets: tuple[str, ...]) -> None:
    """Reject ``--batch`` when targets it cannot handle are selected.

    Phase 5b only batches subagents (every other target uses a free-
    text generation path that the Batches API does not yet wrap).
    Failing fast here — rather than letting the dispatch silently
    skip claude-md — keeps the user model honest: ``--batch`` either
    runs the whole selection through the API once, or it errors.
    """
    unsupported = tuple(
        t for t in selected_targets if t not in _BATCH_SUPPORTED_TARGETS
    )
    if not unsupported:
        return
    supported = ", ".join(sorted(_BATCH_SUPPORTED_TARGETS))
    msg = (
        f"[red]Error:[/red] --batch does not support targets "
        f"{', '.join(unsupported)} (Phase 5a primitives only cover "
        f"tool_use tunings — sync mode handles the rest). Re-run "
        f"with --targets {supported} to use batch mode, or drop "
        f"--batch to keep the sync flow."
    )
    console.print(msg)
    raise typer.Exit(code=1)


def _validate_enhance_flags(
    *,
    batch: bool,
    wait: bool,
    selected_targets: tuple[str, ...],
) -> None:
    """Validate the ``--batch`` / ``--wait`` flag combination up front.

    ``--batch`` only supports the batchable targets (see
    :func:`_validate_batch_targets`), and ``--wait`` is meaningless
    without ``--batch``. Both checks fail fast before any orchestrator
    is constructed or API key resolved.

    Args:
        batch: Value of the ``--batch`` flag.
        wait: Value of the ``--wait`` flag.
        selected_targets: Resolved ``--targets`` selection.

    Raises:
        typer.Exit: With code 1 on an invalid combination.
    """
    if batch:
        _validate_batch_targets(selected_targets)
    if wait and not batch:
        console.print("[red]Error:[/red] --wait only applies in --batch mode.")
        raise typer.Exit(code=1)


def _dispatch_enhance_batch(
    *,
    project: _EnhanceProjectContext,
    orchestrator: AIOrchestrator,
    file_writer: FileWriter,
    dry_run: bool,
    wait: bool,
) -> bool:
    """Run the batch path when the provider advertises batch support.

    Capability negotiation (T5, #389): the decision derives from the
    provider's capability advertisement, never from probing for the
    typed batch decline. Batch-capable providers (Anthropic) take the
    existing batch machinery unchanged; for everyone else this prints
    the loud fallback warning and reports back so the caller runs the
    same targets through the documented sequential pipeline instead —
    no crash, no dropped work.

    Args:
        project: Project metadata for the enhance run.
        orchestrator: Configured orchestrator wrapping the selected
            provider.
        file_writer: Conflict-resolution-aware writer.
        dry_run: Skip API calls and writes (batch path only).
        wait: Block in-process until the batch ends (resume calls).

    Returns:
        ``True`` when the batch path handled the run; ``False`` when
        the provider lacks batch and the caller must fall back to the
        sequential pipeline.
    """
    if not orchestrator.capabilities.batch:
        _warn_batch_capability_fallback(orchestrator.capabilities)
        return False
    _run_enhance_batch(
        project=project,
        orchestrator=orchestrator,
        file_writer=file_writer,
        dry_run=dry_run,
        wait=wait,
    )
    return True


def _warn_batch_capability_fallback(capabilities: ProviderCapabilities) -> None:
    """Print the loud fallback warning for ``--batch`` on a non-batch provider.

    No work is dropped: the same subagent tunings run through the
    documented sequential pipeline (:func:`_run_enhance_pipeline` —
    the exact path the non-batch flow uses), producing the same
    artifacts. What changes is the cost/latency semantics: no Batches
    API discount, no submit/resume two-call flow — the calls run
    in-process now.

    Args:
        capabilities: The selected provider's advertisement (its
            ``batch`` flag is ``False`` when this fires).
    """
    console.print(
        f"[yellow]Warning:[/yellow] provider {capabilities.provider!r} "
        f"does not support batch processing — falling back to "
        f"sequential API calls now (same results; no batch discount, "
        f"no submit/resume flow). Run `green providers` to see "
        f"per-provider capabilities.",
        style="bold",
    )


def _run_enhance_batch(
    *,
    project: _EnhanceProjectContext,
    orchestrator: AIOrchestrator,
    file_writer: FileWriter,
    dry_run: bool,
    wait: bool,
) -> None:
    """Submit-or-resume the subagent batch path.

    Branches on ``state.has_batch()``: if a batch is already
    in flight (recorded by a prior ``--batch`` invocation), this run
    polls / fetches; otherwise it builds the per-agent batch plan and
    submits. ``dry_run`` short-circuits before any API call.
    """
    if dry_run:
        console.print(
            "[dim]--dry-run with --batch: nothing submitted, "
            "no state file written.[/dim]"
        )
        return

    state = load_state(project.project_path)
    try:
        if state.has_batch():
            _resume_subagent_batch_cli(
                project_path=project.project_path,
                orchestrator=orchestrator,
                state=state,
                file_writer=file_writer,
                wait=wait,
            )
            return
        # ``wait`` is meaningful for the resume branch above, but the
        # submit call itself never blocks (see ADR-001's two-call
        # contract). Warn upfront on first-run so users know to pass
        # ``--wait`` again on the resume call. See issue #319.
        if wait:
            console.print(
                "[dim]--wait has no effect on the first --batch call "
                "(submit-only by design — see ADR-001). Re-run with "
                "--wait once the batch is in flight to block until "
                "results land.[/dim]"
            )
        _submit_subagent_batch_cli(
            project=project,
            orchestrator=orchestrator,
            state=state,
        )
    except AIGenerationError as ai_err:
        # Unlike the ``green init`` Pass 2 flow (which downgrades AI
        # failures to warnings + offline scaffold), the user
        # explicitly opted into batch mode here — there is no
        # silent fallback. Surface the API error and exit non-zero
        # so the user can re-run when ready.
        console.print(f"[red]Error:[/red] Batch API call failed: {ai_err}")
        raise typer.Exit(code=1) from ai_err


def _submit_subagent_batch_cli(
    *,
    project: _EnhanceProjectContext,
    orchestrator: AIOrchestrator,
    state: EnhanceState,
) -> None:
    """Build the subagent batch plan, submit, and persist."""
    target_context = (
        f"Project: {project.project_name}, "
        f"Language: {project.language}, "
        f"Type: existing project being re-tuned via `green enhance --batch`"
    )
    generator = SubagentsGenerator(orchestrator)
    outcome = run_async(
        _run_with_orchestrator_close(
            orchestrator,
            submit_subagent_batch(
                orchestrator=orchestrator,
                generator=generator,
                target_context=target_context,
                state=state,
                project_path=project.project_path,
            ),
        )
    )
    console.print(
        f"[green]✓[/green] Submitted batch [bold]"
        f"{outcome.submission.batch_id}[/bold] covering "
        f"{outcome.agent_count} subagent(s). Re-run "
        f"`green enhance --batch` to fetch results, or with "
        f"`--wait` to block in-process."
    )


def _resume_subagent_batch_cli(
    *,
    project_path: Path,
    orchestrator: AIOrchestrator,
    state: EnhanceState,
    file_writer: FileWriter,
    wait: bool,
) -> None:
    """Poll an in-flight batch; on ``ended``, fetch and write."""
    generator = SubagentsGenerator(orchestrator)
    outcome = run_async(
        _run_with_orchestrator_close(
            orchestrator,
            resume_subagent_batch(
                orchestrator=orchestrator,
                generator=generator,
                persistence=BatchPersistenceContext(
                    state=state,
                    project_path=project_path,
                    file_writer=file_writer,
                ),
                wait_config=BatchWaitConfig(wait=wait),
            ),
        )
    )
    _render_batch_resume_outcome(outcome)


# Message contents for the static-message branches of
# :func:`_render_batch_resume_outcome`; IN_PROGRESS and ENDED have their
# own ``case`` branches because their messages weave in dynamic data.
_BATCH_OUTCOME_STATIC: dict[ResumeStatus, str] = {
    ResumeStatus.NO_BATCH: (
        "[yellow]No batch is in flight; nothing to resume.[/yellow]"
    ),
    ResumeStatus.EXPIRED: (
        "[yellow]Previous batch crossed the 24 h SLA and was cleared. "
        "Re-run `green enhance --batch` to submit a fresh batch.[/yellow]"
    ),
    ResumeStatus.TIMED_OUT: (
        "[yellow]--wait timed out before the batch ended. "
        "Re-run `green enhance --batch` to pick up later.[/yellow]"
    ),
}


def _render_batch_resume_outcome(outcome: ResumeOutcome) -> None:
    """Translate a :class:`ResumeOutcome` into a CLI message.

    Static-message statuses (``NO_BATCH``, ``EXPIRED``, ``TIMED_OUT``)
    are rendered from the lookup table above. ``IN_PROGRESS`` and
    ``ENDED`` need ``outcome.poll`` / ``outcome.bundle`` data woven
    in, so they branch into dedicated helpers. The ``case _`` is
    unreachable today — :data:`ResumeStatus` is a closed
    :class:`enum.StrEnum` and every member has a branch above — but
    the :func:`typing.assert_never` keeps mypy honest: adding a new
    member without updating this dispatcher fails type checking
    instead of silently falling through.
    """
    match outcome.status:
        case ResumeStatus.NO_BATCH | ResumeStatus.EXPIRED | ResumeStatus.TIMED_OUT:
            console.print(_BATCH_OUTCOME_STATIC[outcome.status])
        case ResumeStatus.IN_PROGRESS:
            _render_batch_in_progress(outcome)
        case ResumeStatus.ENDED:
            _render_batch_ended(outcome)
        case _:
            assert_never(outcome.status)


def _render_batch_in_progress(outcome: ResumeOutcome) -> None:
    """Render the ``IN_PROGRESS`` status line with poll counts."""
    poll = outcome.poll
    if poll is None:
        return
    console.print(
        f"[dim]Batch {poll.batch_id}: still running "
        f"({poll.processing_count} processing, "
        f"{poll.succeeded_count} succeeded, "
        f"{poll.errored_count} errored). Re-run later, or "
        f"pass --wait to block.[/dim]"
    )


def _render_batch_ended(outcome: ResumeOutcome) -> None:
    """Render the ``ENDED`` summary plus a failed-agents follow-up."""
    console.print(
        f"[green]✓[/green] Batch reconciled: "
        f"{len(outcome.succeeded_agents)} agent(s) written, "
        f"{len(outcome.failed_agents)} failed."
    )
    if outcome.failed_agents:
        joined = ", ".join(outcome.failed_agents)
        console.print(
            f"[red]Failed agents:[/red] {joined}. Re-run "
            f"`green enhance --batch` (the failed entries will be "
            f"included in the next submission)."
        )


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
            hidden=True,
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
    batch: Annotated[
        bool,
        typer.Option(
            "--batch",
            help=(
                "Submit subagent tunings via the Anthropic Message "
                "Batches API (50% cheaper, ≤24 h SLA). Use with "
                "``--targets subagents``. The first run submits and "
                "exits; re-run to fetch results, or pass ``--wait`` "
                "to block until done. See ADR-001 for the rationale. "
                "Providers without batch support (see `green "
                "providers`) fall back to sequential API calls with "
                "a warning."
            ),
        ),
    ] = False,
    wait: Annotated[
        bool,
        typer.Option(
            "--wait",
            help=(
                "When used with ``--batch``: block in-process polling "
                "every 30 s until the batch ends or the timeout is "
                "reached. Default off (two-call submit-then-resume "
                "pattern is friendlier for CI). Has no effect on the "
                "first ``--batch`` invocation (submit-only); pass "
                "``--wait`` on the resume call to block."
            ),
        ),
    ] = False,
    config: config_file_option = None,
    provider: provider_option = None,
    model: model_option = None,
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
        batch: Submit subagent tunings via the Anthropic Message
            Batches API. Submit-then-resume two-call flow; pair
            with ``--wait`` for in-process polling. If the selected
            provider does not advertise batch support, the same
            targets fall back to sequential API calls with a loud
            warning (never a crash, never dropped work).
        wait: Block in-process when ``--batch`` is set; polls every
            30 s until the batch ends or the timeout elapses.
        config: Configuration file path (``--config``, YAML or TOML).
            Loaded through the same loader as ``green init``; its
            ``llm_provider`` / ``llm_model`` keys feed the config-file
            tier of provider/model selection (#396).
        provider: Optional LLM provider override (``--provider``).
        model: Optional model override (``--model``). The case of the
            model id is preserved verbatim (API identifiers are
            case-sensitive).

    Note:
        Provider/model resolve with the same four-tier precedence as
        ``green init``: CLI flag > env (``GREEN_LLM_PROVIDER`` /
        ``GREEN_LLM_MODEL``) > config-file key (``llm_provider`` /
        ``llm_model``, via ``--config``) > built-in default (#396).

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
    _validate_enhance_flags(
        batch=batch,
        wait=wait,
        selected_targets=selected_targets,
    )
    # Same config-file source as ``green init`` (#396): one shared
    # loader, so the ``llm_provider`` / ``llm_model`` keys feed tier 3
    # of the selection precedence identically in both commands.
    config_data = _load_config_data(config)
    orchestrator = _require_enhance_orchestrator(
        api_key,
        no_interactive=no_interactive,
        selection_inputs=_SelectionInputs(
            provider_flag=provider,
            model_flag=model,
            config_data=config_data,
        ),
    )
    file_writer = FileWriter(
        project_root=project_path,
        force=force,
        interactive=False,
        console=console,
    )

    project = _EnhanceProjectContext(
        project_path=project_path,
        project_name=resolved_name,
        language=resolved_language,
    )

    # A False return means the provider lacks batch support and a
    # fallback warning was already printed — fall through to the
    # sequential pipeline below instead of returning.
    if batch and _dispatch_enhance_batch(
        project=project,
        orchestrator=orchestrator,
        file_writer=file_writer,
        dry_run=dry_run,
        wait=wait,
    ):
        return

    _run_enhance_pipeline(
        project=project,
        selected_targets=selected_targets,
        orchestrator=orchestrator,
        options=_EnhanceRunOptions(
            dry_run=dry_run,
            force=force,
            file_writer=file_writer,
        ),
    )


def cli_main() -> None:
    """Entry point for the CLI when installed as a package."""
    app()


if __name__ == "__main__":
    cli_main()
