"""Scripts directory generator.

Generates quality control scripts adapted to target project languages and structure.
Supports Python, TypeScript, Go, Rust, and other languages with appropriate tooling.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScriptConfig:
    """Configuration for script generation.

    Attributes:
        language: Programming language (python, typescript, go, rust, etc.)
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
    ) -> None:
        """Initialize the Scripts Generator.

        Args:
            output_dir: Directory where scripts will be created
            config: ScriptConfig with language and tool settings

        Raises:
            ValueError: If output_dir is invalid or language is unsupported
        """
        self.output_dir = Path(output_dir)
        self.config = config
        self._validate_config()

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

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self) -> dict[str, Path]:
        """Generate all quality control scripts.

        Returns:
            Dictionary mapping script names to their generated file paths

        Raises:
            OSError: If script files cannot be written
        """
        scripts: dict[str, Path] = {}

        # Generate language-specific scripts
        if self.config.language == "python":
            scripts.update(self._generate_python_scripts())
        elif self.config.language in ("typescript", "ts", "javascript", "js"):
            scripts.update(self._generate_typescript_scripts())
        elif self.config.language == "go":
            scripts.update(self._generate_go_scripts())
        elif self.config.language == "rust":
            scripts.update(self._generate_rust_scripts())
        else:
            # Fallback to Python scripts for unknown languages
            scripts.update(self._generate_python_scripts())

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
        scripts["fix-all.sh"] = self._write_script(
            "fix-all.sh",
            self._python_fix_all_script(),
        )
        scripts["security.sh"] = self._write_script(
            "security.sh",
            self._python_security_script(),
        )
        scripts["complexity.sh"] = self._write_script(
            "complexity.sh",
            self._python_complexity_script(),
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
        return """#!/usr/bin/env bash
# scripts/test.sh - Run tests with Pytest
# Usage: ./scripts/test.sh [--unit|--integration|--e2e|--all] [--coverage] [--mutation] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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
        --cov=start_green_stay_green
        --cov-branch
        --cov-report=term-missing
        --cov-report=html
        --cov-report=xml
        --cov-fail-under=90
    )
fi

# Run tests
if $VERBOSE; then
    echo "Running pytest with args: ${PYTEST_ARGS[*]}"
fi

pytest "${PYTEST_ARGS[@]}" tests/ || { echo "✗ Tests failed" >&2; exit 1; }

echo "✓ Tests passed"

# Run mutation tests if requested
if $MUTATION; then
    echo "=== Running Mutation Tests ==="
    if command -v mutmut &> /dev/null; then
        mutmut run || { echo "✗ Mutation tests failed" >&2; exit 1; }
        echo "✓ Mutation tests passed"
    else
        echo "Warning: mutmut not installed, skipping mutation tests" >&2
    fi
fi

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
bandit -r start_green_stay_green/ || { echo "✗ Bandit found issues" >&2; exit 1; }

echo "=== Security Checks (Safety) ==="

# Run Safety with policy file
if $VERBOSE; then
    echo "Running Safety dependency checker..."
fi
if [ -f "$PROJECT_ROOT/.safety-policy.yml" ]; then
    safety check --policy-file "$PROJECT_ROOT/.safety-policy.yml" || { echo "✗ Safety found issues" >&2; exit 1; }
else
    safety check || { echo "✗ Safety found issues" >&2; exit 1; }
fi

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
"""

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
    radon cc -a start_green_stay_green/ || true

    echo ""
    echo "Maintainability Index (should be >= 20):"
    radon mi -a start_green_stay_green/ || true
else
    echo "Warning: radon not installed, skipping cyclomatic complexity check" >&2
fi

# Check complexity with Xenon
if command -v xenon &> /dev/null; then
    if $VERBOSE; then
        echo "Running Xenon complexity check..."
    fi
    xenon --max-absolute B --max-modules B --max-average B start_green_stay_green/ || \
        { echo "✗ Complexity exceeds thresholds" >&2; exit 1; }
else
    if $VERBOSE; then
        echo "Note: xenon not installed for strict complexity checks"
    fi
fi

echo "✓ Complexity analysis completed"
exit 0
"""

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

if $CHECK; then
    if $VERBOSE; then
        echo "Checking formatting..."
    fi
    npx prettier --check . || { echo "✗ Formatting check failed" >&2; exit 1; }
    echo "✓ Code formatting check passed"
else
    if $VERBOSE; then
        echo "Formatting code..."
    fi
    npx prettier --write . || { echo "✗ Formatting failed" >&2; exit 1; }
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

npx jest "${JEST_ARGS[@]}" || { echo "✗ Tests failed" >&2; exit 1; }

echo "✓ Tests passed"
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
    cargo clippy --all --fix --allow-dirty --allow-staged || { echo "✗ Clippy fix failed" >&2; exit 1; }
else
    cargo clippy --all -- -D warnings || { echo "✗ Clippy check failed" >&2; exit 1; }
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
    CARGO_INCREMENTAL=0 RUSTFLAGS="-Cinstrument-coverage" LLVM_PROFILE_FILE="coverage-%p-%m.profraw" cargo test || { echo "✗ Tests failed" >&2; exit 1; }
else
    cargo test || { echo "✗ Tests failed" >&2; exit 1; }
fi

echo "✓ Tests passed"
exit 0
"""

    def _write_script(self, filename: str, content: str) -> Path:
        """Write a script file and make it executable.

        Args:
            filename: Name of the script file
            content: Script content

        Returns:
            Path to the written script file

        Raises:
            OSError: If script cannot be written or made executable
        """
        script_path = self.output_dir / filename

        # Write script content
        script_path.write_text(content, encoding="utf-8")

        # Make script executable
        script_path.chmod(0o755)

        return script_path
