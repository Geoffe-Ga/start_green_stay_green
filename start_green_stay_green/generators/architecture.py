"""Architecture enforcement generator.

Generates architecture validation configuration for import-linter (Python)
and dependency-cruiser (TypeScript).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from start_green_stay_green.ai.orchestrator import AIOrchestrator


@dataclass(frozen=True)
class ArchitectureResult:
    """Result from architecture enforcement generation.

    Attributes:
        output_dir: Directory containing generated files.
        files_created: List of files created.
        language: Target language (python, typescript).
    """

    output_dir: Path
    files_created: list[Path]
    language: str


class ArchitectureEnforcementGenerator:
    """Generates architecture enforcement configuration.

    Generates import-linter config for Python and dependency-cruiser
    config for TypeScript to enforce layer separation and prevent
    circular dependencies.

    Attributes:
        orchestrator: AI orchestrator for content generation.
        output_dir: Directory for generated files.
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator,
        *,
        output_dir: Path | None = None,
    ) -> None:
        """Initialize Architecture Enforcement Generator.

        Args:
            orchestrator: AI orchestrator for content generation.
            output_dir: Output directory for generated files.
                Defaults to plans/architecture.
        """
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
            language: Target language (python, typescript).
            project_name: Name of the project.

        Returns:
            ArchitectureResult with output directory and files created.

        Raises:
            ValueError: If language is not supported.
        """
        supported_languages = {"python", "typescript"}
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

    def _generate_readme(self, language: str, project_name: str) -> Path:
        """Generate README with usage instructions.

        Args:
            language: Target language.
            project_name: Name of the project.

        Returns:
            Path to generated README file.
        """
        readme_path = self.output_dir / "README.md"

        tool = "import-linter" if language == "python" else "dependency-cruiser"
        install_cmd = (
            "pip install import-linter"
            if language == "python"
            else "npm install -g dependency-cruiser"
        )
        run_cmd = (
            "lint-imports"
            if language == "python"
            else "depcruise --config .dependency-cruiser.js src"
        )

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

See documentation:
- Python: https://import-linter.readthedocs.io/
- TypeScript: https://github.com/sverweij/dependency-cruiser

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

        if language == "python":
            script_content = """#!/usr/bin/env bash
set -euo pipefail

echo "🏛️  Checking Python architecture with import-linter..."

if ! command -v lint-imports &> /dev/null; then
    echo "❌ import-linter not found. Install with: pip install import-linter"
    exit 1
fi

lint-imports --config plans/architecture/.importlinter

echo "✅ Architecture checks passed!"
"""
        else:  # typescript
            script_content = """#!/usr/bin/env bash
set -euo pipefail

echo "🏛️  Checking TypeScript architecture with dependency-cruiser..."

if ! command -v depcruise &> /dev/null; then
    echo "❌ dependency-cruiser not found."
    echo "Install with: npm install -g dependency-cruiser"
    exit 1
fi

depcruise --config plans/architecture/.dependency-cruiser.js src

echo "✅ Architecture checks passed!"
"""

        script_path.write_text(script_content)

        # Make script executable
        script_path.chmod(0o755)

        return script_path
