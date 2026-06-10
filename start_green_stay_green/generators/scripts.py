"""Scripts directory generator.

Generates quality control scripts adapted to target project languages and structure.
Supports Python, TypeScript, Go, Rust, Swift, Kotlin, and other languages
with appropriate tooling.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from start_green_stay_green.utils.file_writer import FileWriter


@dataclass(frozen=True)
class ScriptConfig:
    """Configuration for script generation.

    Attributes:
        language: Programming language (python, typescript, go, rust,
            swift, kotlin, etc.)
        package_name: Name of the main package/module
        supports_pytest: Whether project uses pytest for testing
        supports_coverage: Whether project uses coverage reporting
        supports_mutation: Whether project uses mutation testing
        supports_complexity: Whether project uses complexity analysis
        supports_security: Whether project uses security scanning
    """

    language: str
    package_name: str
    supports_pytest: bool = True
    supports_coverage: bool = True
    supports_mutation: bool = True
    supports_complexity: bool = True
    supports_security: bool = True


class ScriptsGenerator:
    """Generate quality control scripts for target projects.

    This generator creates executable shell scripts for running quality checks,
    linting, formatting, testing, and other development tasks. Scripts are
    customized for the target project's language and tooling.

    Attributes:
        output_dir: Directory where scripts will be written
        config: Configuration for script generation
    """

    def __init__(
        self,
        output_dir: Path,
        config: ScriptConfig,
        *,
        file_writer: FileWriter | None = None,
        project_root: Path | None = None,
    ) -> None:
        """Initialize the Scripts Generator.

        Args:
            output_dir: Directory where scripts will be created
            config: ScriptConfig with language and tool settings
            file_writer: Optional FileWriter for additive behavior.
                If provided, existing files are skipped instead of overwritten.
            project_root: Optional project root directory. Used to write
                project-level companion files (such as
                ``.pip-audit-known-vulnerabilities``) outside the scripts
                directory. Defaults to ``output_dir`` so that test
                invocations stay self-contained within their temporary
                directory.

        Raises:
            ValueError: If output_dir is invalid or language is unsupported
        """
        self.output_dir = Path(output_dir)
        self.config = config
        self._file_writer = file_writer
        self.project_root = (
            Path(project_root) if project_root is not None else self.output_dir
        )
        self._validate_config()

    _SAFE_PACKAGE_NAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")

    def _validate_config(self) -> None:
        """Validate configuration and ensure output directory exists.

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config.language:
            msg = "Language cannot be empty"
            raise ValueError(msg)

        if not self.config.package_name:
            msg = "Package name cannot be empty"
            raise ValueError(msg)

        if not self._SAFE_PACKAGE_NAME_RE.match(self.config.package_name):
            msg = "Package name must contain only letters, digits, and underscores"
            raise ValueError(msg)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self) -> dict[str, Path]:
        """Generate all quality control scripts.

        Returns:
            Dictionary mapping script names to their generated file paths

        Raises:
            OSError: If script files cannot be written
        """
        # Dispatch table keeps generate() flat as languages are added:
        # each entry is a zero-argument builder returning the scripts dict.
        builders: dict[str, Callable[[], dict[str, Path]]] = {
            "python": self._generate_python_scripts,
            "typescript": self._generate_typescript_scripts,
            "ts": self._generate_typescript_scripts,
            "javascript": self._generate_typescript_scripts,
            "js": self._generate_typescript_scripts,
            "go": self._generate_go_scripts,
            "rust": self._generate_rust_scripts,
            "swift": self._generate_swift_scripts,
            "kotlin": self._generate_kotlin_scripts,
        }
        # Fallback to Python scripts for unknown languages.
        builder = builders.get(self.config.language, self._generate_python_scripts)
        scripts: dict[str, Path] = builder()

        # Language-agnostic scripts
        scripts["pr-status.sh"] = self._write_script(
            "pr-status.sh",
            self._pr_status_script(),
        )

        return scripts

    def _generate_python_scripts(self) -> dict[str, Path]:
        """Generate Python-specific quality control scripts.

        Returns:
            Dictionary mapping script names to file paths
        """
        scripts: dict[str, Path] = {}

        scripts["check-all.sh"] = self._write_script(
            "check-all.sh",
            self._python_check_all_script(),
        )
        scripts["format.sh"] = self._write_script(
            "format.sh",
            self._python_format_script(),
        )
        scripts["lint.sh"] = self._write_script(
            "lint.sh",
            self._python_lint_script(),
        )
        scripts["test.sh"] = self._write_script(
            "test.sh",
            self._python_test_script(),
        )
        scripts["typecheck.sh"] = self._write_script(
            "typecheck.sh",
            self._python_typecheck_script(),
        )
        scripts["coverage.sh"] = self._write_script(
            "coverage.sh",
            self._python_coverage_script(),
        )
        scripts["fix-all.sh"] = self._write_script(
            "fix-all.sh",
            self._python_fix_all_script(),
        )
        scripts["security.sh"] = self._write_script(
            "security.sh",
            self._python_security_script(),
        )
        # Companion data file for pip-audit suppressions — written at the
        # project root, not added to the scripts dict (it isn't an executable).
        self._write_pip_audit_known_vulns_template()
        scripts["complexity.sh"] = self._write_script(
            "complexity.sh",
            self._python_complexity_script(),
        )
        scripts["mutation.sh"] = self._write_script(
            "mutation.sh",
            self._python_mutation_script(),
        )
        scripts["analyze_mutations.py"] = self._write_python_file(
            "analyze_mutations.py",
            self._python_analyze_mutations_script(),
        )

        return scripts

    def _generate_typescript_scripts(self) -> dict[str, Path]:
        """Generate TypeScript-specific quality control scripts.

        Returns:
            Dictionary mapping script names to file paths
        """
        scripts: dict[str, Path] = {}

        scripts["check-all.sh"] = self._write_script(
            "check-all.sh",
            self._typescript_check_all_script(),
        )
        scripts["format.sh"] = self._write_script(
            "format.sh",
            self._typescript_format_script(),
        )
        scripts["lint.sh"] = self._write_script(
            "lint.sh",
            self._typescript_lint_script(),
        )
        scripts["test.sh"] = self._write_script(
            "test.sh",
            self._typescript_test_script(),
        )
        scripts["typecheck.sh"] = self._write_script(
            "typecheck.sh",
            self._typescript_typecheck_script(),
        )
        scripts["fix-all.sh"] = self._write_script(
            "fix-all.sh",
            self._typescript_fix_all_script(),
        )

        return scripts

    def _generate_go_scripts(self) -> dict[str, Path]:
        """Generate Go-specific quality control scripts.

        Returns:
            Dictionary mapping script names to file paths
        """
        scripts: dict[str, Path] = {}

        scripts["check-all.sh"] = self._write_script(
            "check-all.sh",
            self._go_check_all_script(),
        )
        scripts["format.sh"] = self._write_script(
            "format.sh",
            self._go_format_script(),
        )
        scripts["lint.sh"] = self._write_script(
            "lint.sh",
            self._go_lint_script(),
        )
        scripts["test.sh"] = self._write_script(
            "test.sh",
            self._go_test_script(),
        )

        return scripts

    def _generate_rust_scripts(self) -> dict[str, Path]:
        """Generate Rust-specific quality control scripts.

        Returns:
            Dictionary mapping script names to file paths
        """
        scripts: dict[str, Path] = {}

        scripts["check-all.sh"] = self._write_script(
            "check-all.sh",
            self._rust_check_all_script(),
        )
        scripts["format.sh"] = self._write_script(
            "format.sh",
            self._rust_format_script(),
        )
        scripts["lint.sh"] = self._write_script(
            "lint.sh",
            self._rust_lint_script(),
        )
        scripts["test.sh"] = self._write_script(
            "test.sh",
            self._rust_test_script(),
        )

        return scripts

    def _generate_swift_scripts(self) -> dict[str, Path]:
        """Generate Swift-specific quality control scripts.

        Emits check/format/lint/test/security scripts plus a companion
        ``.swiftlint.yml`` at the project root (complexity gate and
        crash-safety/security opt-in rules) so the lint script and the
        pre-commit SwiftLint hook share one configuration.

        Returns:
            Dictionary mapping script names to file paths
        """
        scripts: dict[str, Path] = {}

        scripts["check-all.sh"] = self._write_script(
            "check-all.sh",
            self._swift_check_all_script(),
        )
        scripts["format.sh"] = self._write_script(
            "format.sh",
            self._swift_format_script(),
        )
        scripts["lint.sh"] = self._write_script(
            "lint.sh",
            self._swift_lint_script(),
        )
        scripts["test.sh"] = self._write_script(
            "test.sh",
            self._swift_test_script(),
        )
        scripts["security.sh"] = self._write_script(
            "security.sh",
            self._swift_security_script(),
        )
        # Companion SwiftLint config — written at the project root, not
        # added to the scripts dict (it isn't an executable).
        self._write_swiftlint_config_template()

        return scripts

    def _generate_kotlin_scripts(self) -> dict[str, Path]:
        """Generate Kotlin-specific quality control scripts (#357).

        Emits check/format/lint/test/security scripts plus a companion
        ``detekt.yml`` at the project root (complexity gate and
        potential-bugs rules) so the lint script and the pre-commit
        detekt hook share one configuration.

        Returns:
            Dictionary mapping script names to file paths
        """
        scripts: dict[str, Path] = {}

        scripts["check-all.sh"] = self._write_script(
            "check-all.sh",
            self._kotlin_check_all_script(),
        )
        scripts["format.sh"] = self._write_script(
            "format.sh",
            self._kotlin_format_script(),
        )
        scripts["lint.sh"] = self._write_script(
            "lint.sh",
            self._kotlin_lint_script(),
        )
        scripts["test.sh"] = self._write_script(
            "test.sh",
            self._kotlin_test_script(),
        )
        scripts["security.sh"] = self._write_script(
            "security.sh",
            self._kotlin_security_script(),
        )
        # Companion detekt config — written at the project root, not
        # added to the scripts dict (it isn't an executable).
        self._write_detekt_config_template()

        return scripts

    # Python script generators

    def _python_check_all_script(self) -> str:
        """Generate Python check-all.sh script."""
        return """#!/usr/bin/env bash
# scripts/check-all.sh - Run all quality checks
# Usage: ./scripts/check-all.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run all quality checks in sequence.

Runs:
  1. Linting (Ruff)
  2. Formatting (Black + isort)
  3. Type checking (MyPy)
  4. Security checks (Bandit + Safety)
  5. Complexity analysis (Radon)
  6. Unit tests
  7. Coverage report

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           One or more checks failed
    2           Error running checks

EXAMPLES:
    $(basename "$0")          # Run all checks
    $(basename "$0") --verbose # Show detailed output
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Set verbosity
VERBOSE_FLAG=""
if $VERBOSE; then
    VERBOSE_FLAG="--verbose"
fi

echo "=== Running All Quality Checks ==="
echo ""

FAILED_CHECKS=()
PASSED_CHECKS=()

# Helper function to run a check
run_check() {
    local check_name=$1
    local script=$2
    shift 2
    local args=("$@")

    echo "Running: $check_name"
    if "$SCRIPT_DIR/$script" "${args[@]+"${args[@]}"}\" $VERBOSE_FLAG; then
        PASSED_CHECKS+=("$check_name")
        echo "✓ $check_name passed"
    else
        FAILED_CHECKS+=("$check_name")
        echo "✗ $check_name failed" >&2
    fi
    echo ""
}

# Run all checks
run_check "Linting" "lint.sh" --check
run_check "Formatting" "format.sh" --check
run_check "Type checking" "typecheck.sh"
run_check "Security checks" "security.sh"
run_check "Complexity analysis" "complexity.sh"
run_check "Unit tests" "test.sh" --unit
run_check "Coverage report" "coverage.sh"

echo "=== Quality Checks Summary ==="
echo "Passed: ${#PASSED_CHECKS[@]}"
echo "Failed: ${#FAILED_CHECKS[@]}"

if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    echo ""
    echo "Failed checks:"
    for check in "${FAILED_CHECKS[@]}"; do
        echo "  ✗ $check"
    done
    exit 1
else
    echo ""
    echo "✓ All quality checks passed!"
    exit 0
fi
"""

    def _python_format_script(self) -> str:
        """Generate Python format.sh script."""
        return """#!/usr/bin/env bash
# scripts/format.sh - Format code with Black and isort
# Usage: ./scripts/format.sh [--fix] [--check] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
CHECK=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --check)
            CHECK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Format code using Black and isort.

OPTIONS:
    --fix       Apply formatting changes (default)
    --check     Check only, fail if changes needed
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Code is properly formatted
    1           Formatting issues found
    2           Error running checks

EXAMPLES:
    $(basename "$0") --fix         # Apply formatting
    $(basename "$0") --check       # Check only
    $(basename "$0") --verbose     # Show detailed output
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Set verbosity
if $VERBOSE; then
    set -x
fi

echo "=== Formatting (Black + isort) ==="

# Determine mode
if $CHECK; then
    MODE="--check"
else
    MODE=""
fi

# Run isort
if $VERBOSE; then
    echo "Running isort..."
fi
isort $MODE . || { echo "✗ isort failed" >&2; exit 1; }

# Run Black
if $VERBOSE; then
    echo "Running Black..."
fi
black $MODE . || { echo "✗ Black failed" >&2; exit 1; }

if [ -n "$MODE" ]; then
    echo "✓ Code formatting check passed"
else
    echo "✓ Code formatted successfully"
fi
exit 0
"""

    def _python_lint_script(self) -> str:
        """Generate Python lint.sh script."""
        return """#!/usr/bin/env bash
# scripts/lint.sh - Run linting checks with Ruff
# Usage: ./scripts/lint.sh [--fix] [--check] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
CHECK=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --check)
            CHECK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run linting checks on the project using Ruff.

OPTIONS:
    --fix       Auto-fix linting issues where possible
    --check     Check only, fail if issues found (default mode)
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           Linting issues found
    2           Error running checks

EXAMPLES:
    $(basename "$0")              # Run checks in check mode
    $(basename "$0") --fix         # Auto-fix issues
    $(basename "$0") --verbose     # Show detailed output
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Set verbosity
if $VERBOSE; then
    set -x
fi

echo "=== Linting (Ruff) ==="

if $FIX; then
    if $VERBOSE; then
        echo "Fixing linting issues..."
    fi
    ruff check . --fix
    EXIT_CODE=$?
else
    if $VERBOSE; then
        echo "Checking for linting issues..."
    fi
    ruff check .
    EXIT_CODE=$?
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Linting checks passed"
    exit 0
else
    echo "✗ Linting checks failed" >&2
    exit 1
fi
"""

    def _python_test_script(self) -> str:
        """Generate Python test.sh script."""
        return f"""#!/usr/bin/env bash
# scripts/test.sh - Run tests with Pytest
# Usage: ./scripts/test.sh [--unit|--integration|--e2e|--all] [--coverage]
#                          [--mutation] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

TEST_TYPE="unit"
COVERAGE=false
MUTATION=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --e2e)
            TEST_TYPE="e2e"
            shift
            ;;
        --all)
            TEST_TYPE="all"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --mutation)
            MUTATION=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run tests using Pytest.

OPTIONS:
    --unit          Run unit tests only (default)
    --integration   Run integration tests only
    --e2e           Run end-to-end tests only
    --all           Run all test types
    --coverage      Generate coverage report
    --mutation      Run mutation tests
    --verbose       Show detailed output
    --help          Display this help message

EXIT CODES:
    0               All tests passed
    1               Test failures
    2               Error running tests

EXAMPLES:
    $(basename "$0")                     # Run unit tests
    $(basename "$0") --all               # Run all tests
    $(basename "$0") --unit --coverage   # Unit tests with coverage
    $(basename "$0") --mutation          # Run mutation tests
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Set verbosity
if $VERBOSE; then
    set -x
fi

# Build pytest arguments
PYTEST_ARGS=(-v)

case "$TEST_TYPE" in
    unit)
        echo "=== Running Unit Tests ==="
        PYTEST_ARGS+=(-m "not integration and not e2e")
        ;;
    integration)
        echo "=== Running Integration Tests ==="
        PYTEST_ARGS+=(-m "integration")
        ;;
    e2e)
        echo "=== Running End-to-End Tests ==="
        PYTEST_ARGS+=(-m "e2e")
        ;;
    all)
        echo "=== Running All Tests ==="
        ;;
esac

# Add coverage if requested
if $COVERAGE; then
    echo "Coverage enabled"
    PYTEST_ARGS+=(
        --cov={self.config.package_name}
        --cov-branch
        --cov-report=term-missing
        --cov-report=html
        --cov-report=xml
        --cov-fail-under=90
    )
fi

# Run tests
if $VERBOSE; then
    echo "Running pytest with args: ${{PYTEST_ARGS[*]}}"
fi

pytest "${{PYTEST_ARGS[@]}}" tests/ || {{ echo "✗ Tests failed" >&2; exit 1; }}

echo "✓ Tests passed"

# Run mutation tests if requested
if $MUTATION; then
    echo "=== Running Mutation Tests ==="
    if command -v mutmut &> /dev/null; then
        mutmut run || {{ echo "✗ Mutation tests failed" >&2; exit 1; }}
        echo "✓ Mutation tests passed"
    else
        echo "Warning: mutmut not installed, skipping mutation tests" >&2
    fi
fi

exit 0
"""

    def _python_typecheck_script(self) -> str:
        """Generate Python typecheck.sh script."""
        return f"""#!/usr/bin/env bash
# scripts/typecheck.sh - Run type checking with MyPy
# Usage: ./scripts/typecheck.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run type checking on the project using MyPy.

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All type checks passed
    1           Type errors found
    2           Error running type checker

EXAMPLES:
    $(basename "$0")          # Run type checking
    $(basename "$0") --verbose # Show detailed output
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Set verbosity
if $VERBOSE; then
    set -x
fi

echo "=== Type Checking (MyPy) ==="

if command -v mypy &> /dev/null; then
    mypy {self.config.package_name}/ || {{
        echo "✗ Type checking failed" >&2
        exit 1
    }}
    echo "✓ Type checking passed"
else
    echo "Warning: mypy not installed, skipping type checking" >&2
    echo "Install with: pip install mypy" >&2
    exit 0
fi

exit 0
"""

    def _python_coverage_script(self) -> str:
        """Generate Python coverage.sh script."""
        return f"""#!/usr/bin/env bash
# scripts/coverage.sh - Run tests with coverage report
# Usage: ./scripts/coverage.sh [--html] [--xml] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

HTML_REPORT=false
XML_REPORT=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --html)
            HTML_REPORT=true
            shift
            ;;
        --xml)
            XML_REPORT=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run tests with coverage report.

OPTIONS:
    --html      Generate HTML coverage report
    --xml       Generate XML coverage report (for CI)
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Coverage threshold met
    1           Coverage below threshold
    2           Error running coverage

EXAMPLES:
    $(basename "$0")          # Run coverage with terminal report
    $(basename "$0") --html   # Generate HTML report
    $(basename "$0") --xml    # Generate XML report for CI
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Set verbosity
if $VERBOSE; then
    set -x
fi

echo "=== Coverage Report ==="

# Build pytest arguments
PYTEST_ARGS=(
    -v
    --cov={self.config.package_name}
    --cov-branch
    --cov-report=term-missing
    --cov-fail-under=90
)

# Add HTML report if requested
if $HTML_REPORT; then
    PYTEST_ARGS+=(--cov-report=html)
    echo "HTML report will be generated in htmlcov/"
fi

# Add XML report if requested
if $XML_REPORT; then
    PYTEST_ARGS+=(--cov-report=xml)
    echo "XML report will be generated as coverage.xml"
fi

# Run tests with coverage
pytest "${{PYTEST_ARGS[@]}}" tests/ || {{
    echo "✗ Coverage below threshold" >&2
    exit 1
}}

echo "✓ Coverage threshold met"

exit 0
"""

    def _python_fix_all_script(self) -> str:
        """Generate Python fix-all.sh script."""
        return """#!/usr/bin/env bash
# scripts/fix-all.sh - Auto-fix all issues
# Usage: ./scripts/fix-all.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Auto-fix all auto-fixable issues in sequence.

Fixes:
  1. Linting issues (Ruff)
  2. Formatting (Black + isort)

Note: Some issues may require manual intervention.
Check the output and review changes before committing.

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Fixes applied successfully
    1           Some fixes failed
    2           Error during fixes

EXAMPLES:
    $(basename "$0")          # Apply all auto-fixes
    $(basename "$0") --verbose # Show detailed output
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Set verbosity
VERBOSE_FLAG=""
if $VERBOSE; then
    VERBOSE_FLAG="--verbose"
fi

echo "=== Auto-fixing Issues ==="
echo ""

FAILED_FIXES=()

# Helper function to run a fix
run_fix() {
    local fix_name=$1
    local script=$2
    shift 2
    local args=("$@")

    echo "Running: $fix_name"
    if "$SCRIPT_DIR/$script" --fix "${args[@]}" $VERBOSE_FLAG; then
        echo "✓ $fix_name completed"
    else
        FAILED_FIXES+=("$fix_name")
        echo "✗ $fix_name failed" >&2
    fi
    echo ""
}

# Run all fixes
run_fix "Linting" "lint.sh"
run_fix "Formatting" "format.sh"

echo "=== Auto-fix Summary ==="
if [ ${#FAILED_FIXES[@]} -gt 0 ]; then
    echo "Failed fixes: ${#FAILED_FIXES[@]}"
    echo ""
    for fix in "${FAILED_FIXES[@]}"; do
        echo "  ✗ $fix"
    done
    exit 1
else
    echo "✓ All auto-fixes completed successfully!"
    echo ""
    echo "Review the changes with: git diff"
    echo "Stage changes with: git add ."
    exit 0
fi
"""

    def _python_security_script(self) -> str:
        """Generate Python security.sh script."""
        return """#!/usr/bin/env bash
# scripts/security.sh - Run security checks with Bandit and Safety
# Usage: ./scripts/security.sh [--full] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FULL=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run security checks using Bandit and Safety.

OPTIONS:
    --full      Run comprehensive security scan
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           No security issues found
    1           Security issues found
    2           Error running checks

EXAMPLES:
    $(basename "$0")             # Run basic security checks
    $(basename "$0") --full      # Run comprehensive scan
    $(basename "$0") --verbose   # Show detailed output
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Set verbosity
if $VERBOSE; then
    set -x
fi

echo "=== Security Checks (Bandit) ==="

# Run Bandit
if $VERBOSE; then
    echo "Running Bandit security scanner..."
fi
bandit -r __PACKAGE_NAME__/ || { echo "✗ Bandit found issues" >&2; exit 1; }

echo "=== Security Checks (pip-audit) ==="

# Run pip-audit for dependency vulnerability scanning
if $VERBOSE; then
    echo "Running pip-audit dependency checker..."
fi

# Build ignore flags for known transitive dependency vulnerabilities
# that cannot be fixed (no fix available or deprecated transitive deps).
# Each entry should have a corresponding tracking issue.
PIP_AUDIT_ARGS=()
if [ -f "$PROJECT_ROOT/.pip-audit-known-vulnerabilities" ]; then
    while IFS= read -r line; do
        # Strip inline comments and trim whitespace
        vuln_id="${line%%#*}"
        vuln_id="${vuln_id%"${vuln_id##*[![:space:]]}"}"
        # Skip empty lines
        [[ -z "$vuln_id" ]] && continue
        PIP_AUDIT_ARGS+=(--ignore-vuln "$vuln_id")
    done < "$PROJECT_ROOT/.pip-audit-known-vulnerabilities"
fi

pip-audit "${PIP_AUDIT_ARGS[@]}" || { echo "✗ pip-audit found issues" >&2; exit 1; }

if $FULL; then
    echo "=== Comprehensive Security Scan ==="

    # Check for hardcoded secrets
    if command -v detect-secrets &> /dev/null; then
        if $VERBOSE; then
            echo "Running detect-secrets scan..."
        fi
        detect-secrets scan . || true
    fi
fi

echo "✓ Security checks passed"
exit 0
""".replace("__PACKAGE_NAME__", self.config.package_name)

    def _python_complexity_script(self) -> str:
        """Generate Python complexity.sh script."""
        return """#!/usr/bin/env bash
# scripts/complexity.sh - Code complexity analysis
# Usage: ./scripts/complexity.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Analyze code complexity using Radon and Xenon.

Metrics:
  - Cyclomatic complexity (should be <= 10)
  - Maintainability index (should be >= 20)
  - Cognitive complexity

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Complexity acceptable
    1           Complexity exceeds thresholds
    2           Error during analysis

EXAMPLES:
    $(basename "$0")          # Analyze complexity
    $(basename "$0") --verbose # Show detailed output
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Set verbosity
if $VERBOSE; then
    set -x
fi

echo "=== Code Complexity Analysis ==="

# Check Cyclomatic Complexity with Radon
if command -v radon &> /dev/null; then
    echo ""
    echo "Cyclomatic Complexity (should be <= 10):"
    radon cc -a __PACKAGE_NAME__/ || true

    echo ""
    echo "Maintainability Index (should be >= 20):"
    radon mi -a __PACKAGE_NAME__/ || true
else
    echo "Warning: radon not installed, skipping cyclomatic complexity check" >&2
fi

# Check complexity with Xenon
if command -v xenon &> /dev/null; then
    if $VERBOSE; then
        echo "Running Xenon complexity check..."
    fi
    xenon --max-absolute B --max-modules B --max-average B __PACKAGE_NAME__/ || \
        { echo "✗ Complexity exceeds thresholds" >&2; exit 1; }
else
    if $VERBOSE; then
        echo "Note: xenon not installed for strict complexity checks"
    fi
fi

echo "✓ Complexity analysis completed"
exit 0
""".replace("__PACKAGE_NAME__", self.config.package_name)

    def _python_mutation_script(self) -> str:
        """Generate Python mutation.sh script."""
        package_name = self.config.package_name
        return f"""#!/usr/bin/env bash
# scripts/mutation.sh - Run mutation tests with score validation
# Usage: ./scripts/mutation.sh [--min-score SCORE] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MIN_SCORE=80  # MAXIMUM QUALITY: 80% mutation score minimum
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --min-score)
            MIN_SCORE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run mutation tests and validate minimum score threshold.

Mutation testing introduces small changes (mutations) to your code
to verify that your test suite catches them. A high mutation score
indicates effective tests.

OPTIONS:
    --min-score SCORE   Minimum mutation score (default: 80)
    --verbose           Show detailed output
    --help              Display this help message

EXIT CODES:
    0                   Mutation score meets or exceeds minimum
    1                   Mutation score below minimum threshold
    2                   Error running mutation tests

QUALITY STANDARDS:
    MAXIMUM QUALITY:    80% minimum mutation score
    Good:               70-79%
    Acceptable:         60-69%
    Poor:               <60%

EXAMPLES:
    $(basename "$0")                    # Run with 80% minimum
    $(basename "$0") --min-score 70     # Run with 70% minimum
    $(basename "$0") --verbose          # Show detailed output
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Set verbosity
if $VERBOSE; then
    set -x
fi

# Check if mutmut is installed
if ! command -v mutmut &> /dev/null; then
    echo "Error: mutmut is not installed" >&2
    echo "Install with: pip install mutmut" >&2
    exit 2
fi

echo "=== Running Mutation Tests ==="
echo "Minimum required score: ${{MIN_SCORE}}%"
echo ""

# Run mutation tests (allow failure, we'll check score)
echo "Running mutmut (this may take several minutes)..."
if mutmut run 2>&1; then
    echo "✓ Mutmut run completed"
else
    # mutmut returns non-zero if there are surviving mutants, which is expected
    echo "Info: Mutmut run completed (some mutants may have survived)"
fi

echo ""
echo "=== Mutation Test Results ==="

# Get results as JSON
if ! mutmut junitxml > /dev/null 2>&1; then
    echo "Warning: Could not generate JUnit XML (may be empty results)" >&2
fi

# Parse mutmut results
RESULTS=$(mutmut results)
echo "$RESULTS"
echo ""

# Extract counts from results
KILLED=$(echo "$RESULTS" | grep -o 'Killed: [0-9]*' | \\
    grep -o '[0-9]*$' || echo "0")
SURVIVED=$(echo "$RESULTS" | grep -o 'Survived: [0-9]*' | \\
    grep -o '[0-9]*$' || echo "0")
SUSPICIOUS=$(echo "$RESULTS" | grep -o 'Suspicious: [0-9]*' | \\
    grep -o '[0-9]*$' || echo "0")
TIMEOUT=$(echo "$RESULTS" | grep -o 'Timeout: [0-9]*' | \\
    grep -o '[0-9]*$' || echo "0")

# Calculate total and score
TOTAL=$((KILLED + SURVIVED + SUSPICIOUS + TIMEOUT))

if [ "$TOTAL" -eq 0 ]; then
    echo "Warning: No mutants were generated" >&2
    echo "This might indicate:"
    echo "  - No code to mutate in {package_name}/"
    echo "  - Configuration issue with mutmut"
    echo ""
    echo "Skipping mutation score validation"
    exit 0
fi

# Calculate mutation score (killed / total * 100)
SCORE=$(awk "BEGIN {{printf \\"%.1f\\", ($KILLED / $TOTAL) * 100}}")

echo "=== Mutation Score ==="
echo "Killed:      $KILLED"
echo "Survived:    $SURVIVED"
echo "Suspicious:  $SUSPICIOUS"
echo "Timeout:     $TIMEOUT"
echo "Total:       $TOTAL"
echo ""
echo "Mutation Score: ${{SCORE}}%"
echo "Required:       ${{MIN_SCORE}}%"
echo ""

# Compare score to threshold
if awk "BEGIN {{exit !($SCORE >= $MIN_SCORE)}}"; then
    echo "✓ Mutation score meets minimum threshold"
    echo ""

    if [ "$SURVIVED" -gt 0 ]; then
        echo "Note: $SURVIVED mutants survived. To view them:"
        echo "  mutmut show <id>"
        echo "  mutmut html  # Generate HTML report"
    fi

    exit 0
else
    echo "✗ Mutation score below minimum threshold" >&2
    echo "" >&2
    echo "Your test suite killed ${{SCORE}}% of mutants" >&2
    echo "Minimum required: ${{MIN_SCORE}}%" >&2
    echo "" >&2
    echo "To improve mutation score:" >&2
    echo "  1. View surviving mutants: mutmut show <id>" >&2
    echo "  2. Add tests to catch these mutations" >&2
    echo "  3. Generate HTML report: mutmut html" >&2
    echo "" >&2

    if [ "$SURVIVED" -gt 0 ]; then
        echo "Surviving mutants:" >&2
        mutmut show 1 2>&1 | head -20 || true
    fi

    exit 1
fi
"""

    def _python_analyze_mutations_script(self) -> str:
        """Generate Python analyze_mutations.py script."""
        return '''#!/usr/bin/env python3
"""Analyze mutmut cache database for mutation testing insights.

This script provides detailed analysis of mutation testing results including:
- Overall mutation score and statistics
- Files with the most surviving mutants
- Sample of specific surviving mutants for debugging

Usage:
    ./scripts/analyze_mutations.py
    python scripts/analyze_mutations.py --top 10
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Quality thresholds
MINIMUM_MUTATION_SCORE = 80


def analyze_cache(
    cache_path: Path, top_files: int = 20, filter_file: str | None = None
) -> None:
    """Analyze mutmut cache and print detailed statistics.

    Args:
        cache_path: Path to .mutmut-cache file.
        top_files: Number of top files to show (default: 20).
        filter_file: Optional filename to filter results (e.g., "cli.py").
    """
    if not cache_path.exists():
        print(f"Error: Cache file not found: {cache_path}", file=sys.stderr)
        print("Run mutation tests first: ./scripts/mutation.sh", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(cache_path)
    cursor = conn.cursor()

    # Build file filter condition
    file_filter_sql = ""
    file_filter_params: tuple[str, ...] = ()
    if filter_file:
        # Match any path ending with the specified file
        file_filter_sql = """
            AND sf.filename LIKE ?
        """
        file_filter_params = (f"%{filter_file}",)
        print(f"=== Mutmut Cache Analysis (filtered: {filter_file}) ===\\n")
    else:
        print("=== Mutmut Cache Analysis ===\\n")

    # Get total mutants (with optional filter)
    query = f"""
        SELECT COUNT(*)
        FROM Mutant m, Line l, SourceFile sf
        WHERE m.line = l.id
          AND l.sourcefile = sf.id
          {file_filter_sql}
    """
    cursor.execute(query, file_filter_params)
    total = cursor.fetchone()[0]
    print(f"Total mutants: {total}")
    print()

    # Get status counts (with optional filter)
    query = f"""
        SELECT m.status, COUNT(*)
        FROM Mutant m, Line l, SourceFile sf
        WHERE m.line = l.id
          AND l.sourcefile = sf.id
          {file_filter_sql}
        GROUP BY m.status
    """
    cursor.execute(query, file_filter_params)
    status_counts = dict(cursor.fetchall())
    killed = status_counts.get("ok_killed", 0)
    survived = status_counts.get("bad_survived", 0)
    suspicious = status_counts.get("ok_suspicious", 0)
    timeout = status_counts.get("bad_timeout", 0)
    untested = status_counts.get("untested", 0)

    print("Status counts:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    print()

    # Calculate score
    if total > 0:
        tested_total = total - untested
        if tested_total > 0:
            score = (killed / tested_total) * 100
            print(f"Mutation Score: {score:.1f}%")
            print(f"Required: {MINIMUM_MUTATION_SCORE}%")
            print()
            print("Breakdown:")
            killed_pct = killed / tested_total * 100
            survived_pct = survived / tested_total * 100
            suspicious_pct = suspicious / tested_total * 100
            timeout_pct = timeout / tested_total * 100
            print(f"  Killed: {killed} ({killed_pct:.1f}% of tested)")
            print(f"  Survived: {survived} ({survived_pct:.1f}% of tested)")
            print(f"  Suspicious: {suspicious} ({suspicious_pct:.1f}%)")
            print(f"  Timeout: {timeout} ({timeout_pct:.1f}%)")
            print(f"  Untested: {untested}")
            print()

            if score < MINIMUM_MUTATION_SCORE:
                gap = int((MINIMUM_MUTATION_SCORE / 100 * tested_total) - killed)
                msg = f"⚠️  Need to kill {gap} more mutants"
                msg += f" to reach {MINIMUM_MUTATION_SCORE}%"
                print(msg)
                print()

    # Show files with most survived mutants (with optional filter)
    if survived > 0:
        print(f"=== Files with Most Survived Mutants (Top {top_files}) ===")
        query = f"""
            SELECT sf.filename, COUNT(*) as count
            FROM Mutant m, Line l, SourceFile sf
            WHERE m.line = l.id
              AND l.sourcefile = sf.id
              AND m.status = "bad_survived"
              {file_filter_sql}
            GROUP BY sf.filename
            ORDER BY count DESC
            LIMIT ?
        """
        cursor.execute(query, (*file_filter_params, top_files))
        for filename, count in cursor.fetchall():
            percentage = (count / survived) * 100
            print(f"  {count:3d} ({percentage:5.1f}%): {filename}")
        print()

        # Show sample of survived mutants (with optional filter)
        print("Sample of survived mutants (first 10):")
        query = f"""
            SELECT m.id, sf.filename, l.line_number
            FROM Mutant m, Line l, SourceFile sf
            WHERE m.line = l.id
              AND l.sourcefile = sf.id
              AND m.status = "bad_survived"
              {file_filter_sql}
            ORDER BY sf.filename, l.line_number
            LIMIT 10
        """
        cursor.execute(query, file_filter_params)
        for mutant_id, filename, line_number in cursor.fetchall():
            print(f"  Mutant {mutant_id}: {filename}:{line_number}")
        print()
        print("To view a specific mutant: mutmut show <id>")
        print("To generate HTML report: mutmut html")

    conn.close()


def main() -> None:
    """Parse arguments and run cache analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze mutation testing results from .mutmut-cache",
        epilog="Examples:\\n"
        "  %(prog)s                  # Analyze all files\\n"
        "  %(prog)s cli.py           # Analyze only cli.py\\n"
        "  %(prog)s --cache .cache   # Use custom cache file\\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "filename",
        nargs="?",
        help="Optional filename to filter results (e.g., 'cli.py')",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(".mutmut-cache"),
        help="Path to mutmut cache file (default: .mutmut-cache)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top files to show (default: 20)",
    )

    args = parser.parse_args()
    analyze_cache(args.cache, args.top, args.filename)


if __name__ == "__main__":
    main()
'''

    # TypeScript script generators

    def _typescript_check_all_script(self) -> str:
        """Generate TypeScript check-all.sh script."""
        return """#!/usr/bin/env bash
# scripts/check-all.sh - Run all quality checks
# Usage: ./scripts/check-all.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run all quality checks in sequence.

Runs:
  1. Linting (ESLint)
  2. Formatting (Prettier)
  3. Type checking (TypeScript)
  4. Tests (Jest)

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           One or more checks failed
    2           Error running checks
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

VERBOSE_FLAG=""
if $VERBOSE; then
    VERBOSE_FLAG="--verbose"
fi

echo "=== Running All Quality Checks ==="
echo ""

FAILED_CHECKS=()
PASSED_CHECKS=()

run_check() {
    local check_name=$1
    local script=$2
    shift 2
    local args=("$@")

    echo "Running: $check_name"
    if "$SCRIPT_DIR/$script" "${args[@]+"${args[@]}"}" $VERBOSE_FLAG; then
        PASSED_CHECKS+=("$check_name")
        echo "✓ $check_name passed"
    else
        FAILED_CHECKS+=("$check_name")
        echo "✗ $check_name failed" >&2
    fi
    echo ""
}

run_check "Linting" "lint.sh" --check
run_check "Formatting" "format.sh" --check
run_check "Type checking" "typecheck.sh"
run_check "Tests" "test.sh"

echo "=== Quality Checks Summary ==="
echo "Passed: ${#PASSED_CHECKS[@]}"
echo "Failed: ${#FAILED_CHECKS[@]}"

if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    echo ""
    for check in "${FAILED_CHECKS[@]}"; do
        echo "  ✗ $check"
    done
    exit 1
else
    echo ""
    echo "✓ All quality checks passed!"
    exit 0
fi
"""

    def _typescript_format_script(self) -> str:
        """Generate TypeScript format.sh script."""
        return """#!/usr/bin/env bash
# scripts/format.sh - Format code with Prettier
# Usage: ./scripts/format.sh [--fix] [--check] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
CHECK=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --check)
            CHECK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Format code using Prettier.

OPTIONS:
    --fix       Apply formatting changes (default)
    --check     Check only, fail if changes needed
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Code is properly formatted
    1           Formatting issues found
    2           Error running checks
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Formatting (Prettier) ==="

PRETTIER_GLOBS=(
    "src/**/*.{ts,tsx}"
    "tests/**/*.{ts,tsx}"
    "*.{js,json}"
)

if $CHECK; then
    if $VERBOSE; then
        echo "Checking formatting..."
    fi
    npx prettier --check "${PRETTIER_GLOBS[@]}" || {
        echo "✗ Formatting check failed" >&2; exit 1;
    }
    echo "✓ Code formatting check passed"
else
    if $VERBOSE; then
        echo "Formatting code..."
    fi
    npx prettier --write "${PRETTIER_GLOBS[@]}" || {
        echo "✗ Formatting failed" >&2; exit 1;
    }
    echo "✓ Code formatted successfully"
fi
exit 0
"""

    def _typescript_lint_script(self) -> str:
        """Generate TypeScript lint.sh script."""
        return """#!/usr/bin/env bash
# scripts/lint.sh - Run linting checks with ESLint
# Usage: ./scripts/lint.sh [--fix] [--check] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
CHECK=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --check)
            CHECK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run linting checks using ESLint.

OPTIONS:
    --fix       Auto-fix linting issues where possible
    --check     Check only, fail if issues found
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           Linting issues found
    2           Error running checks
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Linting (ESLint) ==="

if $FIX; then
    if $VERBOSE; then
        echo "Fixing linting issues..."
    fi
    npx eslint . --fix || { echo "✗ ESLint fix failed" >&2; exit 1; }
else
    if $VERBOSE; then
        echo "Checking for linting issues..."
    fi
    npx eslint . || { echo "✗ ESLint check failed" >&2; exit 1; }
fi

echo "✓ Linting checks passed"
exit 0
"""

    def _typescript_test_script(self) -> str:
        """Generate TypeScript test.sh script."""
        return """#!/usr/bin/env bash
# scripts/test.sh - Run tests with Jest
# Usage: ./scripts/test.sh [--coverage] [--watch] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

COVERAGE=false
WATCH=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --watch)
            WATCH=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run tests using Jest.

OPTIONS:
    --coverage  Generate coverage report
    --watch     Watch mode (rerun on file changes)
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All tests passed
    1           Test failures
    2           Error running tests
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Running Tests (Jest) ==="

JEST_ARGS=()

if $COVERAGE; then
    JEST_ARGS+=(--coverage)
fi

if $WATCH; then
    JEST_ARGS+=(--watch)
fi

npx jest ${JEST_ARGS[@]+"${JEST_ARGS[@]}"} || { echo "✗ Tests failed" >&2; exit 1; }

echo "✓ Tests passed"
exit 0
"""

    def _typescript_typecheck_script(self) -> str:
        """Generate TypeScript typecheck.sh script."""
        return """#!/usr/bin/env bash
# scripts/typecheck.sh - Run type checking with TypeScript compiler
# Usage: ./scripts/typecheck.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run type checking using the TypeScript compiler.

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All type checks passed
    1           Type errors found
    2           Error running type checker
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Type Checking (TypeScript) ==="

npx tsc --noEmit || { echo "✗ Type checking failed" >&2; exit 1; }

echo "✓ Type checking passed"
exit 0
"""

    def _typescript_fix_all_script(self) -> str:
        """Generate TypeScript fix-all.sh script."""
        return """#!/usr/bin/env bash
# scripts/fix-all.sh - Auto-fix all issues
# Usage: ./scripts/fix-all.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Auto-fix all auto-fixable issues in sequence.

Fixes:
  1. Linting issues (ESLint)
  2. Formatting (Prettier)

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Fixes applied successfully
    1           Some fixes failed
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

VERBOSE_FLAG=""
if $VERBOSE; then
    VERBOSE_FLAG="--verbose"
fi

echo "=== Auto-fixing Issues ==="
echo ""

FAILED_FIXES=()

run_fix() {
    local fix_name=$1
    local script=$2
    shift 2

    echo "Running: $fix_name"
    if "$SCRIPT_DIR/$script" --fix $VERBOSE_FLAG; then
        echo "✓ $fix_name completed"
    else
        FAILED_FIXES+=("$fix_name")
        echo "✗ $fix_name failed" >&2
    fi
    echo ""
}

run_fix "Linting" "lint.sh"
run_fix "Formatting" "format.sh"

echo "=== Auto-fix Summary ==="
if [ ${#FAILED_FIXES[@]} -gt 0 ]; then
    echo "Failed fixes: ${#FAILED_FIXES[@]}"
    exit 1
else
    echo "✓ All auto-fixes completed successfully!"
    exit 0
fi
"""

    # Go script generators

    def _go_check_all_script(self) -> str:
        """Generate Go check-all.sh script."""
        return """#!/usr/bin/env bash
# scripts/check-all.sh - Run all quality checks
# Usage: ./scripts/check-all.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run all quality checks in sequence.

Runs:
  1. Format check (gofmt)
  2. Linting (golangci-lint)
  3. Tests (go test)

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           One or more checks failed
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

VERBOSE_FLAG=""
if $VERBOSE; then
    VERBOSE_FLAG="--verbose"
fi

echo "=== Running All Quality Checks ==="
echo ""

FAILED_CHECKS=()
PASSED_CHECKS=()

run_check() {
    local check_name=$1
    local script=$2
    shift 2

    echo "Running: $check_name"
    if "$SCRIPT_DIR/$script" "${@}" $VERBOSE_FLAG; then
        PASSED_CHECKS+=("$check_name")
        echo "✓ $check_name passed"
    else
        FAILED_CHECKS+=("$check_name")
        echo "✗ $check_name failed" >&2
    fi
    echo ""
}

run_check "Format" "format.sh"
run_check "Linting" "lint.sh"
run_check "Tests" "test.sh"

echo "=== Quality Checks Summary ==="
echo "Passed: ${#PASSED_CHECKS[@]}"
echo "Failed: ${#FAILED_CHECKS[@]}"

if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    exit 1
else
    echo "✓ All quality checks passed!"
    exit 0
fi
"""

    def _go_format_script(self) -> str:
        """Generate Go format.sh script."""
        return """#!/usr/bin/env bash
# scripts/format.sh - Format Go code
# Usage: ./scripts/format.sh [--fix] [--check] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
CHECK=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --check)
            CHECK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Format Go code using gofmt and goimports.

OPTIONS:
    --fix       Apply formatting (default, writes in place)
    --check     Check only, fail if formatting needed
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Code is properly formatted
    1           Formatting issues found
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Formatting (gofmt + goimports) ==="

if $CHECK; then
    if gofmt -l . | grep -q .; then
        echo "✗ Formatting check failed" >&2
        exit 1
    fi
else
    go fmt ./... || { echo "✗ gofmt failed" >&2; exit 1; }
    goimports -w . || { echo "✗ goimports failed" >&2; exit 1; }
fi

echo "✓ Code formatted successfully"
exit 0
"""

    def _go_lint_script(self) -> str:
        """Generate Go lint.sh script."""
        return """#!/usr/bin/env bash
# scripts/lint.sh - Run linting with golangci-lint
# Usage: ./scripts/lint.sh [--fix] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run linting using golangci-lint.

OPTIONS:
    --fix       Auto-fix linting issues where possible
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           Linting issues found
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Linting (golangci-lint) ==="

if $FIX; then
    golangci-lint run ./... --fix || { echo "✗ Linting failed" >&2; exit 1; }
else
    golangci-lint run ./... || { echo "✗ Linting failed" >&2; exit 1; }
fi

echo "✓ Linting checks passed"
exit 0
"""

    def _go_test_script(self) -> str:
        """Generate Go test.sh script."""
        return """#!/usr/bin/env bash
# scripts/test.sh - Run Go tests
# Usage: ./scripts/test.sh [--coverage] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

COVERAGE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run Go tests.

OPTIONS:
    --coverage  Generate coverage report
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All tests passed
    1           Test failures
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Running Tests (go test) ==="

if $COVERAGE; then
    go test -v -cover ./... || { echo "✗ Tests failed" >&2; exit 1; }
else
    go test -v ./... || { echo "✗ Tests failed" >&2; exit 1; }
fi

echo "✓ Tests passed"
exit 0
"""

    # Rust script generators

    def _rust_check_all_script(self) -> str:
        """Generate Rust check-all.sh script."""
        return """#!/usr/bin/env bash
# scripts/check-all.sh - Run all quality checks
# Usage: ./scripts/check-all.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run all quality checks in sequence.

Runs:
  1. Format check (rustfmt)
  2. Linting (clippy)
  3. Tests (cargo test)

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           One or more checks failed
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

VERBOSE_FLAG=""
if $VERBOSE; then
    VERBOSE_FLAG="--verbose"
fi

echo "=== Running All Quality Checks ==="
echo ""

FAILED_CHECKS=()
PASSED_CHECKS=()

run_check() {
    local check_name=$1
    local script=$2
    shift 2

    echo "Running: $check_name"
    if "$SCRIPT_DIR/$script" "${@}" $VERBOSE_FLAG; then
        PASSED_CHECKS+=("$check_name")
        echo "✓ $check_name passed"
    else
        FAILED_CHECKS+=("$check_name")
        echo "✗ $check_name failed" >&2
    fi
    echo ""
}

run_check "Format" "format.sh"
run_check "Linting" "lint.sh"
run_check "Tests" "test.sh"

echo "=== Quality Checks Summary ==="
echo "Passed: ${#PASSED_CHECKS[@]}"
echo "Failed: ${#FAILED_CHECKS[@]}"

if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    exit 1
else
    echo "✓ All quality checks passed!"
    exit 0
fi
"""

    def _rust_format_script(self) -> str:
        """Generate Rust format.sh script."""
        return """#!/usr/bin/env bash
# scripts/format.sh - Format Rust code
# Usage: ./scripts/format.sh [--fix] [--check] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
CHECK=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --check)
            CHECK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Format Rust code using rustfmt.

OPTIONS:
    --fix       Apply formatting
    --check     Check only, fail if formatting needed
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Code is properly formatted
    1           Formatting issues found
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Formatting (rustfmt) ==="

if $CHECK; then
    cargo fmt --all -- --check || { echo "✗ Format check failed" >&2; exit 1; }
    echo "✓ Code formatting check passed"
else
    cargo fmt --all || { echo "✗ Formatting failed" >&2; exit 1; }
    echo "✓ Code formatted successfully"
fi
exit 0
"""

    def _rust_lint_script(self) -> str:
        """Generate Rust lint.sh script."""
        return """#!/usr/bin/env bash
# scripts/lint.sh - Run linting with clippy
# Usage: ./scripts/lint.sh [--fix] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run linting using clippy.

OPTIONS:
    --fix       Auto-fix linting issues where possible
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           Linting issues found
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Linting (clippy) ==="

if $FIX; then
    cargo clippy --all --fix --allow-dirty --allow-staged || \\
        { echo "✗ Clippy fix failed" >&2; exit 1; }
else
    cargo clippy --all -- -D warnings || \\
        { echo "✗ Clippy check failed" >&2; exit 1; }
fi

echo "✓ Linting checks passed"
exit 0
"""

    def _rust_test_script(self) -> str:
        """Generate Rust test.sh script."""
        return """#!/usr/bin/env bash
# scripts/test.sh - Run Rust tests
# Usage: ./scripts/test.sh [--coverage] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

COVERAGE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run Rust tests.

OPTIONS:
    --coverage  Generate coverage report
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All tests passed
    1           Test failures
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Running Tests (cargo test) ==="

if $COVERAGE; then
    CARGO_INCREMENTAL=0 RUSTFLAGS="-Cinstrument-coverage" \\
        LLVM_PROFILE_FILE="coverage-%p-%m.profraw" cargo test || \\
        { echo "✗ Tests failed" >&2; exit 1; }
else
    cargo test || { echo "✗ Tests failed" >&2; exit 1; }
fi

echo "✓ Tests passed"
exit 0
"""

    # Swift script generators

    def _swift_check_all_script(self) -> str:
        """Generate Swift check-all.sh script."""
        return """#!/usr/bin/env bash
# scripts/check-all.sh - Run all quality checks
# Usage: ./scripts/check-all.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run all quality checks in sequence.

Runs:
  1. Format check (swift-format)
  2. Linting + complexity <=10 (SwiftLint)
  3. Tests + coverage >=90% (swift test + llvm-cov)
  4. Security & dead code (Periphery)

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           One or more checks failed
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

VERBOSE_FLAG=""
if $VERBOSE; then
    VERBOSE_FLAG="--verbose"
fi

echo "=== Running All Quality Checks ==="
echo ""

FAILED_CHECKS=()
PASSED_CHECKS=()

run_check() {
    local check_name=$1
    local script=$2
    shift 2

    echo "Running: $check_name"
    if "$SCRIPT_DIR/$script" "${@}" $VERBOSE_FLAG; then
        PASSED_CHECKS+=("$check_name")
        echo "✓ $check_name passed"
    else
        FAILED_CHECKS+=("$check_name")
        echo "✗ $check_name failed" >&2
    fi
    echo ""
}

run_check "Format" "format.sh"
run_check "Linting" "lint.sh"
run_check "Tests" "test.sh" --coverage
run_check "Security" "security.sh"

echo "=== Quality Checks Summary ==="
echo "Passed: ${#PASSED_CHECKS[@]}"
echo "Failed: ${#FAILED_CHECKS[@]}"

if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    exit 1
else
    echo "✓ All quality checks passed!"
    exit 0
fi
"""

    def _swift_format_script(self) -> str:
        """Generate Swift format.sh script."""
        return """#!/usr/bin/env bash
# scripts/format.sh - Format Swift code
# Usage: ./scripts/format.sh [--fix] [--check] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
CHECK=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --check)
            CHECK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Format Swift code using swift-format (install: brew install swift-format).

OPTIONS:
    --fix       Apply formatting (default, writes in place)
    --check     Check only, fail if formatting needed
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Code is properly formatted
    1           Formatting issues found
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Formatting (swift-format) ==="

if $CHECK; then
    swift-format lint --strict --recursive Sources Tests || \\
        { echo "✗ Format check failed" >&2; exit 1; }
    echo "✓ Code formatting check passed"
else
    swift-format format --in-place --recursive Sources Tests || \\
        { echo "✗ Formatting failed" >&2; exit 1; }
    echo "✓ Code formatted successfully"
fi
exit 0
"""

    def _swift_lint_script(self) -> str:
        """Generate Swift lint.sh script."""
        return """#!/usr/bin/env bash
# scripts/lint.sh - Run linting with SwiftLint
# Usage: ./scripts/lint.sh [--fix] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run linting using SwiftLint (install: brew install swiftlint).

Reads .swiftlint.yml at the project root, which enforces
cyclomatic_complexity <= 10 and the crash-safety/security opt-in rules.

OPTIONS:
    --fix       Auto-fix linting issues where possible
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           Linting issues found
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Linting (SwiftLint) ==="

if $FIX; then
    swiftlint lint --fix || { echo "✗ SwiftLint fix failed" >&2; exit 1; }
else
    swiftlint lint --strict || { echo "✗ Linting failed" >&2; exit 1; }
fi

echo "✓ Linting checks passed"
exit 0
"""

    def _swift_test_script(self) -> str:
        """Generate Swift test.sh script."""
        return """#!/usr/bin/env bash
# scripts/test.sh - Run Swift tests
# Usage: ./scripts/test.sh [--coverage] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

COVERAGE=false
VERBOSE=false
THRESHOLD=90

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run Swift tests (XCTest via swift test).

OPTIONS:
    --coverage  Enforce >=${THRESHOLD}% line coverage via llvm-cov data
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All tests passed (and coverage met, with --coverage)
    1           Test failures or coverage below threshold
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Running Tests (swift test) ==="

swift test --enable-code-coverage || { echo "✗ Tests failed" >&2; exit 1; }

if $COVERAGE; then
    # swift test emits llvm-cov export JSON; --show-codecov-path points
    # at it without re-running the suite.
    CODECOV_JSON="$(swift test --show-codecov-path)"
    python3 - "$CODECOV_JSON" "$THRESHOLD" << 'PYEOF' || exit 1
import json
import sys

path, threshold = sys.argv[1], float(sys.argv[2])
with open(path, encoding="utf-8") as handle:
    percent = json.load(handle)["data"][0]["totals"]["lines"]["percent"]
print(f"Line coverage: {percent:.2f}% (threshold: {threshold:.0f}%)")
sys.exit(0 if percent >= threshold else 1)
PYEOF
fi

echo "✓ Tests passed"
exit 0
"""

    def _swift_security_script(self) -> str:
        """Generate Swift security.sh script."""
        return """#!/usr/bin/env bash
# scripts/security.sh - Security & dead-code checks for Swift
# Usage: ./scripts/security.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run security and dead-code checks.

Division of labor:
  - Secret scanning (gitleaks + detect-secrets) runs in pre-commit.
  - SwiftLint's crash-safety/security rules run in lint.sh.
  - This script adds Periphery dead-code detection
    (install: brew install periphery).

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           No issues found (or Periphery not installed; see below)
    1           Unused/dead code detected
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Security & Dead Code (Periphery) ==="

# Pragmatic default: a missing Periphery binary warns instead of failing
# so a fresh clone passes check-all.sh out of the box. Tighten by
# replacing the warning block with `exit 1` once Periphery is installed
# everywhere (including CI).
if ! command -v periphery &> /dev/null; then
    echo "⚠ periphery not found - skipping dead-code scan" >&2
    echo "⚠ Install with: brew install periphery" >&2
    exit 0
fi

periphery scan --strict || { echo "✗ Periphery found unused code" >&2; exit 1; }

echo "✓ Security checks passed"
exit 0
"""

    # SwiftLint companion configuration template. Shared by lint.sh and the
    # pre-commit SwiftLint hook. cyclomatic_complexity mirrors the <=10 gate
    # used by radon (Python), eslint (TypeScript), gocyclo (Go), and clippy
    # (Rust). SwiftLint has no dedicated security ruleset, so the security
    # posture is documented explicitly: crash-safety/randomness rules here,
    # secret scanning in pre-commit (gitleaks + detect-secrets), dead-code
    # analysis in security.sh (Periphery).
    _SWIFTLINT_CONFIG_TEMPLATE = """\
# SwiftLint configuration generated by Start Green Stay Green.
#
# Complexity gate: cyclomatic_complexity <= 10 (error) mirrors the
# radon/eslint/gocyclo/clippy thresholds enforced for other languages.
#
# Security posture (documented, not implied): SwiftLint has no dedicated
# security ruleset. The opt-in rules below catch crash-prone force
# operations and insecure randomness; secret scanning is handled by the
# gitleaks and detect-secrets pre-commit hooks, and dead-code analysis by
# Periphery (scripts/security.sh).

included:
  - Sources
  - Tests

opt_in_rules:
  # Crash safety: forbid force unwraps/casts/tries outside tests.
  - force_unwrapping
  # Insecure randomness: arc4random/rand are not CSPRNGs.
  - legacy_random
  # Memory safety: capturing unowned references invites use-after-free.
  - unowned_variable_capture
  # Diagnostics: fatalError without a message hides crash causes.
  - fatal_error_message

cyclomatic_complexity:
  warning: 10
  error: 10
"""

    def _write_swiftlint_config_template(self) -> Path | None:
        """Write the companion ``.swiftlint.yml`` at the project root.

        The config lives at ``$PROJECT_ROOT`` so both ``lint.sh`` and the
        pre-commit SwiftLint hook resolve it implicitly. An existing file
        is preserved (user customisations win).

        Returns:
            Path to the written config, or ``None`` if a file already
            exists at the destination.
        """
        config_path = self.project_root / ".swiftlint.yml"
        if config_path.exists():
            return None

        config_path.parent.mkdir(parents=True, exist_ok=True)
        if self._file_writer is not None:
            self._file_writer.write_file(config_path, self._SWIFTLINT_CONFIG_TEMPLATE)
        else:
            config_path.write_text(self._SWIFTLINT_CONFIG_TEMPLATE, encoding="utf-8")
        return config_path

    # Kotlin script generators

    def _kotlin_check_all_script(self) -> str:
        """Generate Kotlin check-all.sh script."""
        return """#!/usr/bin/env bash
# scripts/check-all.sh - Run all quality checks
# Usage: ./scripts/check-all.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run all quality checks in sequence.

Runs:
  1. Format check (ktlint)
  2. Static analysis + complexity <=10 (detekt)
  3. Tests + coverage >=90% (./gradlew test + Kover)
  4. Security (OWASP dependency-check)

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           One or more checks failed
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

VERBOSE_FLAG=""
if $VERBOSE; then
    VERBOSE_FLAG="--verbose"
fi

echo "=== Running All Quality Checks ==="
echo ""

FAILED_CHECKS=()
PASSED_CHECKS=()

run_check() {
    local check_name=$1
    local script=$2
    shift 2

    echo "Running: $check_name"
    if "$SCRIPT_DIR/$script" "${@}" $VERBOSE_FLAG; then
        PASSED_CHECKS+=("$check_name")
        echo "✓ $check_name passed"
    else
        FAILED_CHECKS+=("$check_name")
        echo "✗ $check_name failed" >&2
    fi
    echo ""
}

run_check "Format" "format.sh"
run_check "Linting" "lint.sh"
run_check "Tests" "test.sh" --coverage
run_check "Security" "security.sh"

echo "=== Quality Checks Summary ==="
echo "Passed: ${#PASSED_CHECKS[@]}"
echo "Failed: ${#FAILED_CHECKS[@]}"

if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    exit 1
else
    echo "✓ All quality checks passed!"
    exit 0
fi
"""

    def _kotlin_format_script(self) -> str:
        """Generate Kotlin format.sh script."""
        return """#!/usr/bin/env bash
# scripts/format.sh - Format Kotlin code
# Usage: ./scripts/format.sh [--fix] [--check] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
CHECK=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --check)
            CHECK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Format Kotlin code using ktlint (install: brew install ktlint).

OPTIONS:
    --fix       Apply formatting (default, writes in place)
    --check     Check only, fail if formatting needed
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Code is properly formatted
    1           Formatting issues found
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Formatting (ktlint) ==="

if $CHECK; then
    ktlint || { echo "✗ Format check failed" >&2; exit 1; }
    echo "✓ Code formatting check passed"
else
    # --format fixes what it can and still fails on the rest.
    ktlint --format || { echo "✗ Formatting failed" >&2; exit 1; }
    echo "✓ Code formatted successfully"
fi
exit 0
"""

    def _kotlin_lint_script(self) -> str:
        """Generate Kotlin lint.sh script."""
        return """#!/usr/bin/env bash
# scripts/lint.sh - Run static analysis with detekt
# Usage: ./scripts/lint.sh [--fix] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run static analysis using detekt (install: brew install detekt).

Reads detekt.yml at the project root on top of detekt's default config.
detekt.yml enforces CyclomaticComplexMethod <= 10 and keeps the
potential-bugs ruleset active.

OPTIONS:
    --fix       Auto-correct formatting issues where possible
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           Static-analysis issues found
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Static Analysis (detekt) ==="

DETEKT_ARGS=(--config detekt.yml --build-upon-default-config)
DETEKT_ARGS+=(--excludes '**/build/**')
if $FIX; then
    DETEKT_ARGS+=(--auto-correct)
fi

detekt "${DETEKT_ARGS[@]}" || { echo "✗ Linting failed" >&2; exit 1; }

echo "✓ Linting checks passed"
exit 0
"""

    def _kotlin_test_script(self) -> str:
        """Generate Kotlin test.sh script."""
        return """#!/usr/bin/env bash
# scripts/test.sh - Run Kotlin tests via Gradle
# Usage: ./scripts/test.sh [--coverage] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

COVERAGE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run JVM unit tests (JUnit via ./gradlew test).

OPTIONS:
    --coverage  Enforce >=90% line coverage via Kover
                (the bound lives in app/build.gradle.kts: kover block)
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           All tests passed (and coverage met, with --coverage)
    1           Test failures or coverage below threshold
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

# The Gradle wrapper jar is a binary artifact the generator never
# writes; materialise it once from a local Gradle install (this is the
# first step in the README's Installation section).
if [ ! -x ./gradlew ]; then
    echo "✗ ./gradlew not found - run 'gradle wrapper' once to create it" >&2
    exit 1
fi

echo "=== Running Tests (./gradlew) ==="

if $COVERAGE; then
    # koverVerifyDebug runs the debug unit tests and fails when line
    # coverage drops below the minBound(90) configured in
    # app/build.gradle.kts; koverXmlReportDebug emits the report the
    # metrics dashboard reads.
    ./gradlew koverXmlReportDebug koverVerifyDebug || \\
        { echo "✗ Tests or coverage gate failed" >&2; exit 1; }
else
    ./gradlew test || { echo "✗ Tests failed" >&2; exit 1; }
fi

echo "✓ Tests passed"
exit 0
"""

    def _kotlin_security_script(self) -> str:
        """Generate Kotlin security.sh script."""
        return """#!/usr/bin/env bash
# scripts/security.sh - Security checks for Kotlin
# Usage: ./scripts/security.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run security checks.

Division of labor:
  - Secret scanning (gitleaks + detect-secrets) runs in pre-commit.
  - detekt's potential-bugs rules run in lint.sh.
  - This script adds OWASP dependency-check CVE scanning of the
    dependency tree (install: brew install dependency-check).

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           No issues found (or dependency-check not installed)
    1           Vulnerable dependencies detected (CVSS >= 7)
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

echo "=== Security (OWASP dependency-check) ==="

# Pragmatic default: a missing dependency-check binary warns instead of
# failing so a fresh clone passes check-all.sh out of the box. Tighten by
# replacing the warning block with `exit 1` once dependency-check is
# installed everywhere (including CI).
if ! command -v dependency-check &> /dev/null; then
    echo "⚠ dependency-check not found - skipping dependency CVE scan" >&2
    echo "⚠ Install with: brew install dependency-check" >&2
    exit 0
fi

dependency-check \\
    --project "$(basename "$PROJECT_ROOT")" \\
    --scan . \\
    --out build/reports/dependency-check \\
    --failOnCVSS 7 || \\
    { echo "✗ dependency-check found vulnerable dependencies" >&2; exit 1; }

echo "✓ Security checks passed"
exit 0
"""

    # detekt companion configuration template. Shared by lint.sh and the
    # pre-commit detekt hook, applied on top of detekt's default config
    # via --build-upon-default-config. CyclomaticComplexMethod mirrors the
    # <=10 gate used by radon (Python), eslint (TypeScript), gocyclo (Go),
    # clippy (Rust), and SwiftLint (Swift). detekt has no dedicated
    # security ruleset, so the security posture is documented explicitly:
    # potential-bugs rules here, secret scanning in pre-commit (gitleaks +
    # detect-secrets), dependency CVE scanning in security.sh (OWASP
    # dependency-check).
    _DETEKT_CONFIG_TEMPLATE = """\
# detekt configuration generated by Start Green Stay Green.
#
# Applied on top of detekt's default config (the lint script and the
# pre-commit hook both pass --build-upon-default-config), so only the
# overrides below differ from the defaults.
#
# Complexity gate: detekt 1.23.x reports methods whose McCabe complexity
# is >= the configured threshold, so threshold: 11 reports 11+ and
# enforces the <=10 ceiling that radon/eslint/gocyclo/clippy/SwiftLint
# apply for the other supported languages.
#
# Security posture (documented, not implied): detekt has no dedicated
# security ruleset. The potential-bugs rules below catch crash-prone and
# incorrect constructs; secret scanning is handled by the gitleaks and
# detect-secrets pre-commit hooks, and dependency CVE scanning by OWASP
# dependency-check (scripts/security.sh).

build:
  # Fail on any reported issue (detekt's default); kept explicit so the
  # gate is visible at a glance.
  maxIssues: 0

complexity:
  CyclomaticComplexMethod:
    active: true
    # Reports at complexity >= 11, i.e. every function must stay <= 10.
    threshold: 11

potential-bugs:
  active: true
"""

    def _write_detekt_config_template(self) -> Path | None:
        """Write the companion ``detekt.yml`` at the project root.

        The config lives at ``$PROJECT_ROOT`` so both ``lint.sh`` and the
        pre-commit detekt hook reference it with the same relative path.
        An existing file is preserved (user customisations win).

        Returns:
            Path to the written config, or ``None`` if a file already
            exists at the destination.
        """
        config_path = self.project_root / "detekt.yml"
        if config_path.exists():
            return None

        config_path.parent.mkdir(parents=True, exist_ok=True)
        if self._file_writer is not None:
            self._file_writer.write_file(config_path, self._DETEKT_CONFIG_TEMPLATE)
        else:
            config_path.write_text(self._DETEKT_CONFIG_TEMPLATE, encoding="utf-8")
        return config_path

    # Language-agnostic script generators

    def _pr_status_script(self) -> str:
        """Generate pr-status.sh script for PR merge-readiness monitoring.

        Returns:
            Shell script content for the pr-status.sh CLI tool.
        """
        return f"""#!/usr/bin/env bash
# scripts/pr-status.sh - GitHub Actions workflow monitor for PRs
# Usage: ./scripts/pr-status.sh <subcommand> [OPTIONS]

set -euo pipefail

VERSION="1.0.0"
VERBOSE=false

# Auto-detect repo
get_repo() {{
    gh repo view --json nameWithOwner --jq '.nameWithOwner'
}}

# Print usage
usage() {{
    cat << EOF
Usage: $(basename "$0") <subcommand> [OPTIONS]

GitHub Actions workflow monitor for PRs ({self.config.package_name}).

SUBCOMMANDS:
    list [--branch NAME] [--limit N]    List recent CI workflow runs
    view ID [ID...]                      View workflow run conclusions
    watch ID [ID...]                     Watch runs until complete
    checks PR_NUMBER                     Show PR check status
    status PR_NUMBER [--workflow FILE]   Full PR verdict (CI + Claude review)

OPTIONS:
    --verbose   Show detailed output
    --version   Show version and exit
    --help      Display this help message

STATUS OPTIONS:
    --workflow FILE   CI workflow filename (default: ci.yml)

EXIT CODES:
    0           Success / ready to merge
    1           Failure / not ready to merge
    2           Usage error

EXAMPLES:
    $(basename "$0") list                    # List recent CI runs
    $(basename "$0") list --branch feat/foo  # Filter by branch
    $(basename "$0") view 12345              # View run #12345
    $(basename "$0") watch 12345 12346       # Watch two runs
    $(basename "$0") checks 74               # Show PR #74 checks
    $(basename "$0") status 74               # Full PR #74 verdict
EOF
}}

# === list subcommand ===
cmd_list() {{
    local branch=""
    local limit=10

    while [[ $# -gt 0 ]]; do
        case $1 in
            --branch)
                branch="$2"
                shift 2
                ;;
            --limit)
                if ! [[ "$2" =~ ^[0-9]+$ ]]; then
                    echo "Error: --limit requires a numeric value, got '$2'" >&2
                    exit 2
                fi
                limit="$2"
                shift 2
                ;;
            *)
                echo "Error: Unknown option for list: $1" >&2
                exit 2
                ;;
        esac
    done

    local repo
    repo="$(get_repo)"

    echo "=== Recent CI Workflow Runs ==="
    echo ""

    local args=(run list --repo "$repo" --limit "$limit")
    if [[ -n "$branch" ]]; then
        args+=(--branch "$branch")
    fi
    args+=(--json "databaseId,headBranch,workflowName,status,conclusion,createdAt")
    local jqexpr='.[] | [(.databaseId|tostring),'
    jqexpr+=' .headBranch, .workflowName, .status,'
    jqexpr+=' (.conclusion // "—"), .createdAt] | @tsv'
    args+=(--jq "$jqexpr")

    if $VERBOSE; then
        echo "Running: gh ${{args[*]}}"
    fi

    local fmt="%-12s %-30s %-20s %-12s %-18s %s\\n"
    printf "$fmt" "ID" "BRANCH" "WORKFLOW" \\
        "STATUS" "CONCLUSION" "CREATED"
    printf "$fmt" "----" "------" "--------" \\
        "------" "----------" "-------"

    gh "${{args[@]}}" | while IFS=$'\\t' \\
        read -r id branch_name workflow status conclusion created; do
        printf "$fmt" "$id" "$branch_name" \\
            "$workflow" "$status" "$conclusion" "$created"
    done
}}

# === view subcommand ===
cmd_view() {{
    if [[ $# -eq 0 ]]; then
        echo "Error: view requires at least one run ID" >&2
        exit 2
    fi

    local repo
    repo="$(get_repo)"
    local any_failed=false

    for run_id in "$@"; do
        echo "=== Run #${{run_id}} ==="
        echo ""

        local run_json
        local fields="status,conclusion,workflowName"
        fields+=",headBranch,jobs"
        run_json="$(gh run view "$run_id" \\
            --repo "$repo" --json "$fields")"

        if $VERBOSE; then
            echo "Fetched run data for #${{run_id}}"
        fi

        local status conclusion workflow branch
        local jq_tsv='[.workflowName, .headBranch,'
        jq_tsv+=' .status, (.conclusion // "—")] | @tsv'
        read -r workflow branch status conclusion < <(
            echo "$run_json" | jq -r "$jq_tsv"
        )

        echo "Workflow:   $workflow"
        echo "Branch:     $branch"
        echo "Status:     $status"
        echo "Conclusion: $conclusion"
        echo ""

        echo "Jobs:"
        local jq_jobs='.jobs[] | "  '
        jq_jobs+='\\(if .conclusion == "success" then "✓"'
        jq_jobs+=' elif .conclusion == "failure" then "✗"'
        jq_jobs+=' elif .conclusion == "skipped" then "—"'
        jq_jobs+=' else "●" end)'
        jq_jobs+=' \\(.name): \\(.conclusion // .status)"'
        echo "$run_json" | jq -r "$jq_jobs"
        echo ""

        if [[ "$conclusion" == "failure" ]]; then
            any_failed=true
        fi
    done

    if $any_failed; then
        exit 1
    fi
}}

# === watch subcommand ===
cmd_watch() {{
    if [[ $# -eq 0 ]]; then
        echo "Error: watch requires at least one run ID" >&2
        exit 2
    fi

    local repo
    repo="$(get_repo)"
    local any_failed=false

    for run_id in "$@"; do
        echo "=== Watching Run #${{run_id}} ==="
        echo ""

        if $VERBOSE; then
            echo "Watching run #${{run_id}} in repo $repo"
        fi

        if ! gh run watch "$run_id" --repo "$repo" --exit-status; then
            any_failed=true
            echo "✗ Run #${{run_id}} failed" >&2
        else
            echo "✓ Run #${{run_id}} passed"
        fi
        echo ""
    done

    if $any_failed; then
        exit 1
    fi
}}

# === checks subcommand ===
cmd_checks() {{
    if [[ $# -eq 0 ]]; then
        echo "Error: checks requires a PR number" >&2
        exit 2
    fi

    local pr_number="$1"
    local repo
    repo="$(get_repo)"

    echo "=== PR #${{pr_number}} Checks ==="
    echo ""

    if $VERBOSE; then
        echo "Fetching checks for PR #${{pr_number}} in repo $repo"
    fi

    gh pr checks "$pr_number" --repo "$repo"
}}

# === status subcommand ===
cmd_status() {{
    if [[ $# -eq 0 ]]; then
        echo "Error: status requires a PR number" >&2
        exit 2
    fi

    local pr_number="$1"
    shift
    local workflow="ci.yml"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --workflow)
                workflow="$2"
                shift 2
                ;;
            *)
                echo "Error: Unknown option for status: $1" >&2
                exit 2
                ;;
        esac
    done

    local repo
    repo="$(get_repo)"

    # Get PR info
    local pr_json
    pr_json="$(gh pr view "$pr_number" \\
        --repo "$repo" \\
        --json "title,headRefName,comments")"

    local pr_title pr_branch
    pr_title="$(echo "$pr_json" | jq -r '.title')"
    pr_branch="$(echo "$pr_json" | jq -r '.headRefName')"

    echo "=== PR #${{pr_number}}: ${{pr_title}} ==="
    echo ""

    # --- CI Status ---
    local ci_status="UNKNOWN"
    local ci_detail=""
    local ci_pass=false

    local run_json
    if $VERBOSE; then
        echo "Looking for workflow: $workflow on branch: $pr_branch"
    fi

    run_json="$(gh run list --repo "$repo" \\
        --branch "$pr_branch" \\
        --workflow "$workflow" --limit 1 \\
        --json "databaseId,conclusion,status" \\
        2>/dev/null || echo "[]")"

    local run_count
    run_count="$(echo "$run_json" | jq 'length')"

    if [[ "$run_count" -eq 0 ]]; then
        ci_status="NO RUNS"
        ci_detail="No CI runs found for branch $pr_branch"
        echo "Warning: No runs found for workflow" \\
            "'$workflow' on branch '$pr_branch'." >&2
        echo "  Check workflow filename or" \\
            "use --workflow <file> to specify." >&2
    else
        local run_id run_conclusion run_status
        run_id="$(echo "$run_json" | jq -r '.[0].databaseId')"
        run_conclusion="$(echo "$run_json" | jq -r '.[0].conclusion // ""')"
        run_status="$(echo "$run_json" | jq -r '.[0].status')"

        if [[ "$run_status" != "completed" ]]; then
            ci_status="IN PROGRESS"
            ci_detail="Run #${{run_id}} is ${{run_status}}"
        else
            local jobs_json
            jobs_json="$(gh run view "$run_id" --repo "$repo" --json jobs)"

            local total_jobs passed_jobs failed_jobs
            total_jobs="$(echo "$jobs_json" | jq '.jobs | length')"
            passed_jobs="$(echo "$jobs_json" | \\
                jq '[.jobs[] | select(.conclusion == "success")] | length')"
            failed_jobs="$(echo "$jobs_json" | \\
                jq '[.jobs[] | select(.conclusion == "failure")] | length')"

            if [[ "$run_conclusion" == "success" ]]; then
                ci_status="PASS"
                ci_detail="${{passed_jobs}}/${{total_jobs}} jobs green"
                ci_pass=true
            else
                ci_status="FAIL"
                ci_detail="${{passed_jobs}}/${{total_jobs}} jobs green,"
                ci_detail="${{ci_detail}} ${{failed_jobs}} failed"

                # Show failed jobs
                local failed_names
                failed_names="$(echo "$jobs_json" | \\
                    jq -r '.jobs[] | select(.conclusion == "failure") | .name')"
                if [[ -n "$failed_names" ]]; then
                    ci_detail="${{ci_detail}}"$'\\n'"Failed jobs:"
                    while IFS= read -r name; do
                        ci_detail="${{ci_detail}}"$'\\n'"  ✗ ${{name}}"
                    done <<< "$failed_names"
                fi
            fi
        fi
    fi

    # --- Claude Review Status ---
    local review_status="NO REVIEW"
    local review_issues=""
    local review_pass=false

    # Scan comments for Claude review verdicts (latest wins)
    local comments_count
    comments_count="$(echo "$pr_json" | jq '.comments | length')"

    if [[ "$comments_count" -gt 0 ]]; then
        # Search from latest comment backwards for a verdict
        local i
        for ((i = comments_count - 1; i >= 0; i--)); do
            local body
            body="$(echo "$pr_json" | jq -r ".comments[$i].body")"

            # Check for verdict patterns
            if echo "$body" | grep -qE '✅\\s*LGTM|Verdict:.*LGTM'; then
                review_status="LGTM"
                review_pass=true
                break
            elif echo "$body" | \\
                grep -qE '🔄\\s*CHANGES_REQUESTED|Verdict:.*CHANGES_REQUESTED'; then
                review_status="CHANGES_REQUESTED"

                # Extract problems section
                review_issues="$(echo "$body" | \\
                    sed -n '/^## Problems/,/^## [^P]/p' | sed '$d')"
                if [[ -z "$review_issues" ]]; then
                    # Try alternate format: lines starting with 🔴
                    review_issues="$(echo "$body" | grep '🔴' || true)"
                fi
                break
            elif echo "$body" | grep -qE '💬\\s*COMMENTS|Verdict:.*COMMENTS'; then
                review_status="COMMENTS"
                review_pass=true
                break
            fi
        done
    fi

    # --- Output ---
    if $ci_pass; then
        echo "CI Status:     ✓ ${{ci_status}}  (${{ci_detail}})"
    else
        echo "CI Status:     ✗ ${{ci_status}}  (${{ci_detail}})"
    fi

    if $review_pass; then
        echo "Claude Review: ✓ ${{review_status}}"
    else
        echo "Claude Review: ✗ ${{review_status}}"
    fi

    if [[ -n "$review_issues" ]]; then
        echo ""
        echo "Review Issues:"
        echo "$review_issues" | while IFS= read -r line; do
            # Indent if not already indented
            if [[ "$line" == "  "* ]]; then
                echo "$line"
            else
                echo "  $line"
            fi
        done
    fi

    echo ""

    # --- Verdict ---
    if $ci_pass && $review_pass; then
        echo "Verdict: READY TO MERGE"
        exit 0
    else
        echo "Verdict: NOT READY TO MERGE"
        exit 1
    fi
}}

# === Main argument parsing ===

# Handle no arguments
if [[ $# -eq 0 ]]; then
    usage
    exit 2
fi

# Extract global flags first, collect remaining args
REMAINING_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --version)
            echo "$(basename "$0") version $VERSION"
            exit 0
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            REMAINING_ARGS+=("$1")
            shift
            ;;
    esac
done

# Restore positional args
set -- "${{REMAINING_ARGS[@]+"${{REMAINING_ARGS[@]}}"}}"

if [[ $# -eq 0 ]]; then
    usage
    exit 2
fi

SUBCOMMAND="$1"
shift

case "$SUBCOMMAND" in
    list)
        cmd_list "$@"
        ;;
    view)
        cmd_view "$@"
        ;;
    watch)
        cmd_watch "$@"
        ;;
    checks)
        cmd_checks "$@"
        ;;
    status)
        cmd_status "$@"
        ;;
    *)
        echo "Error: Unknown subcommand: $SUBCOMMAND" >&2
        echo "Run '$(basename "$0") --help' for usage." >&2
        exit 2
        ;;
esac
"""

    _PIP_AUDIT_KNOWN_VULNS_TEMPLATE = """\
# Known vulnerabilities in transitive dependencies that cannot be fixed.
# Each line is a vulnerability ID to ignore via pip-audit --ignore-vuln.
# Format: VULN_ID  # package - reason - tracking issue
#
# Review periodically and remove entries when fixes become available.
#
# Example (uncomment and edit):
# CVE-2025-00000    # example-package - no fix yet - tracking #123
"""

    def _write_pip_audit_known_vulns_template(self) -> Path | None:
        """Write a documented empty ``.pip-audit-known-vulnerabilities`` template.

        The template lives next to ``security.sh``'s ``$PROJECT_ROOT`` (the
        project root in normal CLI usage) so the generated script can locate
        it via ``$PROJECT_ROOT/.pip-audit-known-vulnerabilities``.

        Returns:
            Path to the written template, or ``None`` if a file already
            exists at the destination (preserves user customisations).
        """
        template_path = self.project_root / ".pip-audit-known-vulnerabilities"
        if template_path.exists():
            return None

        template_path.parent.mkdir(parents=True, exist_ok=True)
        if self._file_writer is not None:
            self._file_writer.write_file(
                template_path, self._PIP_AUDIT_KNOWN_VULNS_TEMPLATE
            )
        else:
            template_path.write_text(
                self._PIP_AUDIT_KNOWN_VULNS_TEMPLATE, encoding="utf-8"
            )
        return template_path

    def _write_script(self, filename: str, content: str) -> Path:
        """Write a script file and make it executable.

        If a FileWriter is configured, delegates to it for existence checking.
        Otherwise, writes directly (original behavior).

        Args:
            filename: Name of the script file
            content: Script content

        Returns:
            Path to the written script file

        Raises:
            OSError: If script cannot be written or made executable
        """
        script_path = self.output_dir / filename

        if self._file_writer is not None:
            self._file_writer.write_script(script_path, content)
            return script_path

        # Write script content
        script_path.write_text(content, encoding="utf-8")

        # Make script executable
        script_path.chmod(0o755)

        return script_path

    def _write_python_file(self, filename: str, content: str) -> Path:
        """Write a Python file and make it executable.

        Args:
            filename: Name of the Python file
            content: Python file content

        Returns:
            Path to the written Python file

        Raises:
            OSError: If file cannot be written or made executable
        """
        file_path = self.output_dir / filename

        # Write file content
        file_path.write_text(content, encoding="utf-8")

        # Make executable
        file_path.chmod(0o755)

        return file_path
