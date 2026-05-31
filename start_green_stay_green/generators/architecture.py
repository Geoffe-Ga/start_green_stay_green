"""Architecture enforcement generator.

Generates architecture validation configuration for import-linter (Python),
dependency-cruiser (TypeScript), and go-arch-lint (Go).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    from start_green_stay_green.ai.orchestrator import AIOrchestrator


@dataclass(frozen=True)
class ArchitectureResult:
    """Result from architecture enforcement generation.

    Attributes:
        output_dir: Directory containing generated files.
        files_created: List of files created.
        language: Target language (python, typescript, go).
    """

    output_dir: Path
    files_created: list[Path]
    language: str


@dataclass(frozen=True)
class _LanguageTooling:
    """Per-language architecture tooling metadata.

    Attributes:
        tool: Human-readable name of the enforcement tool.
        config_file: Name of the generated configuration file.
        install_cmd: Shell command to install the tool.
        run_cmd: Run-command template with a ``{config_file}`` placeholder
            (e.g. ``"lint-imports --config {config_file}"``). The placeholder
            is filled with the (optionally path-prefixed) config filename at
            the call site, avoiding fragile substring replacement.
        docs_url: URL to the tool's documentation.
        display_name: Capitalized language label for human-readable output
            (e.g. ``"Python"``, ``"TypeScript"``, ``"Go"``).
    """

    tool: str
    config_file: str
    install_cmd: str
    run_cmd: str
    docs_url: str
    display_name: str


# Maps each supported language to its architecture-enforcement tooling.
# Keeping the metadata in one place lets the README and run-script
# generators stay tool-agnostic and avoids per-language branching.
_LANGUAGE_TOOLING: dict[str, _LanguageTooling] = {
    "python": _LanguageTooling(
        tool="import-linter",
        config_file=".importlinter",
        install_cmd="pip install import-linter",
        run_cmd="lint-imports --config {config_file}",
        docs_url="https://import-linter.readthedocs.io/",
        display_name="Python",
    ),
    "typescript": _LanguageTooling(
        tool="dependency-cruiser",
        config_file=".dependency-cruiser.js",
        install_cmd="npm install -g dependency-cruiser",
        run_cmd="depcruise --config {config_file} src",
        docs_url="https://github.com/sverweij/dependency-cruiser",
        display_name="TypeScript",
    ),
    "go": _LanguageTooling(
        tool="go-arch-lint",
        config_file=".go-arch-lint.yml",
        install_cmd=("go install github.com/fe3dback/go-arch-lint@latest"),
        run_cmd="go-arch-lint check --arch-file {config_file}",
        docs_url="https://github.com/fe3dback/go-arch-lint",
        display_name="Go",
    ),
}


class ArchitectureEnforcementGenerator:
    """Generates architecture enforcement configuration.

    Generates import-linter config for Python, dependency-cruiser
    config for TypeScript, and go-arch-lint config for Go to enforce
    layer separation and prevent circular dependencies.

    Attributes:
        orchestrator: AI orchestrator for content generation.
        output_dir: Directory for generated files.
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator | None = None,
        *,
        output_dir: Path | None = None,
    ) -> None:
        """Initialize Architecture Enforcement Generator.

        Args:
            orchestrator: Deprecated. The architecture generator is fully
                deterministic; this parameter is retained for source
                compatibility and ignored. New code should omit it.
                Passing a non-``None`` value emits a
                :class:`DeprecationWarning` so callers can find the
                stale wiring before the parameter is removed in the
                Phase 3 cleanup of the optimization roadmap.
            output_dir: Output directory for generated files.
                Defaults to plans/architecture.
        """
        if orchestrator is not None:
            warnings.warn(
                "ArchitectureEnforcementGenerator's 'orchestrator' parameter "
                "is deprecated and will be removed in Phase 3 of the "
                "optimization roadmap. The generator is fully "
                "deterministic; pass nothing instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        self.orchestrator = orchestrator
        self.output_dir = output_dir or Path("plans/architecture")

    def generate(
        self,
        *,
        language: str,
        project_name: str,
    ) -> ArchitectureResult:
        """Generate architecture enforcement configuration.

        Args:
            language: Target language (python, typescript, go).
            project_name: Name of the project.

        Returns:
            ArchitectureResult with output directory and files created.

        Raises:
            ValueError: If language is not supported.
        """
        supported_languages = frozenset(_LANGUAGE_TOOLING)
        if language not in supported_languages:
            msg = f"Unsupported language: {language}"
            raise ValueError(msg)

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        files_created = []

        if language == "python":
            files_created.extend(self._generate_python_config(project_name))
        elif language == "typescript":
            files_created.extend(self._generate_typescript_config(project_name))
        elif language == "go":
            files_created.extend(self._generate_go_config(project_name))

        # Generate README and run script
        files_created.extend(
            [
                self._generate_readme(language, project_name),
                self._generate_run_script(language, project_name),
            ]
        )

        return ArchitectureResult(
            output_dir=self.output_dir,
            files_created=files_created,
            language=language,
        )

    def _generate_python_config(self, project_name: str) -> list[Path]:
        """Generate import-linter configuration for Python.

        Args:
            project_name: Name of the project.

        Returns:
            List of files created.
        """
        importlinter_path = self.output_dir / ".importlinter"

        # Generate import-linter configuration
        config_content = f"""[importlinter]
root_package = {project_name.replace('-', '_')}

[importlinter:contract:layers]
name = Enforce layered architecture
type = layers
layers =
    presentation
    application
    domain
    infrastructure

[importlinter:contract:independence]
name = Domain layer independence
type = forbidden
source_modules =
    {project_name.replace('-', '_')}.domain
forbidden_modules =
    {project_name.replace('-', '_')}.presentation
    {project_name.replace('-', '_')}.application
    {project_name.replace('-', '_')}.infrastructure

[importlinter:contract:no-cycles]
name = Prevent circular dependencies
type = independence
modules =
    {project_name.replace('-', '_')}
"""

        importlinter_path.write_text(config_content)
        return [importlinter_path]

    def _generate_typescript_config(
        self, project_name: str  # noqa: ARG002
    ) -> list[Path]:
        """Generate dependency-cruiser configuration for TypeScript.

        Args:
            project_name: Name of the project.

        Returns:
            List of files created.
        """
        dc_path = self.output_dir / ".dependency-cruiser.js"

        # Generate dependency-cruiser configuration
        config_content = """/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: 'no-circular',
      severity: 'error',
      comment: 'Circular dependencies create tight coupling and maintenance issues',
      from: {},
      to: {
        circular: true,
      },
    },
    {
      name: 'no-orphans',
      severity: 'warn',
      comment: 'Orphaned modules may indicate dead code',
      from: {
        orphan: true,
        pathNot: ['\\\\.(test|spec)\\\\.[jt]sx?$', '\\\\.(stories)\\\\.[jt]sx?$'],
      },
      to: {},
    },
    {
      name: 'enforce-layers',
      severity: 'error',
      comment: 'Enforce layered architecture: presentation -> application -> domain',
      from: {
        path: '^src/domain',
      },
      to: {
        path: '^src/(presentation|application|infrastructure)',
      },
    },
    {
      name: 'domain-independence',
      severity: 'error',
      comment: 'Domain layer should not depend on infrastructure concerns',
      from: {
        path: '^src/domain',
      },
      to: {
        path: '^src/infrastructure',
      },
    },
  ],
  options: {
    doNotFollow: {
      path: 'node_modules',
    },
    tsPreCompilationDeps: true,
    tsConfig: {
      fileName: 'tsconfig.json',
    },
    enhancedResolveOptions: {
      exportsFields: ['exports'],
      conditionNames: ['import', 'require', 'node', 'default'],
    },
    reporterOptions: {
      dot: {
        collapsePattern: 'node_modules/[^/]+',
      },
      archi: {
        collapsePattern: '^(node_modules|packages/[^/]+/src)/[^/]+',
      },
    },
  },
};
"""

        dc_path.write_text(config_content)
        return [dc_path]

    # ARG002: project_name is unused but kept for API parity with
    # _generate_python_config / _generate_typescript_config so the
    # generate() dispatch can call every _generate_*_config uniformly.
    def _generate_go_config(self, project_name: str) -> list[Path]:  # noqa: ARG002
        """Generate go-arch-lint configuration for Go.

        go-arch-lint enforces a component map and dependency rules over Go
        packages, providing the same layer-separation and domain-independence
        guarantees as import-linter (Python) and dependency-cruiser
        (TypeScript).

        Args:
            project_name: Name of the project.

        Returns:
            List of files created.
        """
        config_path = self.output_dir / ".go-arch-lint.yml"

        # Generate go-arch-lint configuration. Components map onto package
        # globs; the deps section forbids the domain layer from importing
        # the application, presentation, and infrastructure layers, keeping
        # business logic pure and dependency-free.
        config_content = """version: 3
workdir: .

components:
  presentation:
    in: presentation/**
  application:
    in: application/**
  domain:
    in: domain/**
  infrastructure:
    in: infrastructure/**

# Enforce layered architecture:
#   presentation -> application -> domain
# and keep the domain layer independent of outer layers.
deps:
  presentation:
    mayDependOn:
      - application
      - domain
  application:
    mayDependOn:
      - domain
  domain:
    # Domain layer must remain pure: no dependency on application,
    # presentation, or infrastructure concerns.
    mayDependOn: []
  infrastructure:
    mayDependOn:
      - domain

# domain is available to all components without an explicit deps entry.
commonComponents:
  - domain
"""

        config_path.write_text(config_content)
        return [config_path]

    def _generate_readme(self, language: str, project_name: str) -> Path:
        """Generate README with usage instructions.

        Args:
            language: Target language.
            project_name: Name of the project.

        Returns:
            Path to generated README file.
        """
        readme_path = self.output_dir / "README.md"

        tooling = _LANGUAGE_TOOLING[language]
        tool = tooling.tool
        install_cmd = tooling.install_cmd
        # Manual invocation runs from the config directory, so the bare
        # config filename is correct here (no plans/architecture/ prefix).
        run_cmd = tooling.run_cmd.format(config_file=tooling.config_file)

        readme_content = f"""# Architecture Enforcement

This directory contains architecture enforcement rules for **{project_name}**.

## Purpose

Architecture rules ensure:
- **Layer Separation**: Higher layers depend on lower layers only
- **No Circular Dependencies**: Prevent tight coupling
- **Domain Independence**: Domain logic remains pure and testable

## Tool: {tool}

### Installation

```bash
{install_cmd}
```

### Usage

Run the architecture checks:

```bash
./run-check.sh
```

Or manually:

```bash
{run_cmd}
```


## Rules Enforced

### Layer Separation

- **Presentation** → Application → Domain → Infrastructure
- Domain layer cannot depend on infrastructure or presentation
- Each layer can only depend on layers below it

### Circular Dependencies

All circular dependencies are forbidden. They create:
- Tight coupling
- Difficult testing
- Complex refactoring
- Hidden dependencies

### Domain Independence

The domain layer must remain pure:
- No framework dependencies
- No database dependencies
- No UI dependencies
- Only business logic

## Customization

Edit the configuration file:
- Python: `.importlinter`
- TypeScript: `.dependency-cruiser.js`
- Go: `.go-arch-lint.yml`

See documentation:
- Python: https://import-linter.readthedocs.io/
- TypeScript: https://github.com/sverweij/dependency-cruiser
- Go: https://github.com/fe3dback/go-arch-lint

## Integration

Add to CI pipeline:

```yaml
- name: Check Architecture
  run: ./plans/architecture/run-check.sh
```

## References

- Clean Architecture (Robert C. Martin)
- Hexagonal Architecture (Alistair Cockburn)
- Domain-Driven Design (Eric Evans)
"""

        readme_path.write_text(readme_content)
        return readme_path

    def _generate_run_script(
        self, language: str, project_name: str  # noqa: ARG002
    ) -> Path:
        """Generate executable run-check.sh script.

        Args:
            language: Target language.
            project_name: Name of the project.

        Returns:
            Path to generated run script.
        """
        script_path = self.output_dir / "run-check.sh"

        script_content = self._build_run_script(language)

        script_path.write_text(script_content)

        # Make script executable
        script_path.chmod(0o755)

        return script_path

    @staticmethod
    def _build_run_script(language: str) -> str:
        """Build the run-check.sh contents for a language.

        Derives the command and the binary-availability guard from the
        shared :data:`_LANGUAGE_TOOLING` metadata so adding a language
        requires no changes here.

        Args:
            language: Target language.

        Returns:
            The shell script source for run-check.sh.
        """
        tooling = _LANGUAGE_TOOLING[language]
        # The first token of run_cmd is the binary to probe with command -v.
        binary = tooling.run_cmd.split()[0]
        # Fill the {config_file} placeholder with the path-prefixed config so
        # the script works when invoked from the project root. Using the
        # template (rather than substring replacement) keeps the substitution
        # immune to accidental collisions with other tokens in run_cmd.
        full_cmd = tooling.run_cmd.format(
            config_file=f"plans/architecture/{tooling.config_file}",
        )
        return f"""#!/usr/bin/env bash
set -euo pipefail

echo "🏛️  Checking {tooling.display_name} architecture with {tooling.tool}..."

if ! command -v {binary} &> /dev/null; then
    echo "❌ {tooling.tool} not found. Install with: {tooling.install_cmd}"
    exit 1
fi

{full_cmd}

echo "✅ Architecture checks passed!"
"""
