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
bandit -r start_green_stay_green/ || { echo "✗ Bandit found issues" >&2; exit 1; }

echo "=== Security Checks (Safety) ==="

# Run Safety with policy file
if $VERBOSE; then
    echo "Running Safety dependency checker..."
fi
if [ -f "$PROJECT_ROOT/.safety-policy.yml" ]; then
    safety check --policy-file "$PROJECT_ROOT/.safety-policy.yml" || \\
        { echo "✗ Safety found issues" >&2; exit 1; }
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

# ruff: noqa: T201  # print() is intentional for CLI output script
# ruff: noqa: PLR0915  # Many statements acceptable for reporting script

import argparse
from pathlib import Path
import sqlite3
import sys

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
        print(f"Error: Cache file not found: {{cache_path}}", file=sys.stderr)
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
        file_filter_params = (f"%{{filter_file}}",)
        print(f"=== Mutmut Cache Analysis (filtered: {{filter_file}}) ===\\n")
    else:
        print("=== Mutmut Cache Analysis ===\\n")

    # Get total mutants (with optional filter)
    query = f"""  # noqa: S608
        SELECT COUNT(*)
        FROM Mutant m, Line l, SourceFile sf
        WHERE m.line = l.id
          AND l.sourcefile = sf.id
          {{file_filter_sql}}
    """
    cursor.execute(query, file_filter_params)
    total = cursor.fetchone()[0]
    print(f"Total mutants: {{total}}")
    print()

    # Get status counts (with optional filter)
    query = f"""  # noqa: S608
        SELECT m.status, COUNT(*)
        FROM Mutant m, Line l, SourceFile sf
        WHERE m.line = l.id
          AND l.sourcefile = sf.id
          {{file_filter_sql}}
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
        print(f"  {{status}}: {{count}}")
    print()

    # Calculate score
    if total > 0:
        tested_total = total - untested
        if tested_total > 0:
            score = (killed / tested_total) * 100
            print(f"Mutation Score: {{score:.1f}}%")
            print(f"Required: {{MINIMUM_MUTATION_SCORE}}%")
            print()
            print("Breakdown:")
            killed_pct = killed / tested_total * 100
            survived_pct = survived / tested_total * 100
            suspicious_pct = suspicious / tested_total * 100
            timeout_pct = timeout / tested_total * 100
            print(f"  Killed: {{killed}} ({{killed_pct:.1f}}% of tested)")
            print(f"  Survived: {{survived}} ({{survived_pct:.1f}}% of tested)")
            print(f"  Suspicious: {{suspicious}} ({{suspicious_pct:.1f}}%)")
            print(f"  Timeout: {{timeout}} ({{timeout_pct:.1f}}%)")
            print(f"  Untested: {{untested}}")
            print()

            if score < MINIMUM_MUTATION_SCORE:
                gap = int((MINIMUM_MUTATION_SCORE / 100 * tested_total) - killed)
                msg = f"⚠️  Need to kill {{gap}} more mutants"
                msg += f" to reach {{MINIMUM_MUTATION_SCORE}}%"
                print(msg)
                print()

    # Show files with most survived mutants (with optional filter)
    if survived > 0:
        print(f"=== Files with Most Survived Mutants (Top {{top_files}}) ===")
        query = f"""  # noqa: S608
            SELECT sf.filename, COUNT(*) as count
            FROM Mutant m, Line l, SourceFile sf
            WHERE m.line = l.id
              AND l.sourcefile = sf.id
              AND m.status = "bad_survived"
              {{file_filter_sql}}
            GROUP BY sf.filename
            ORDER BY count DESC
            LIMIT ?
        """
        cursor.execute(query, (*file_filter_params, top_files))
        for filename, count in cursor.fetchall():
            percentage = (count / survived) * 100
            print(f"  {{count:3d}} ({{percentage:5.1f}}%): {{filename}}")
        print()

        # Show sample of survived mutants (with optional filter)
        print("Sample of survived mutants (first 10):")
        query = f"""  # noqa: S608
            SELECT m.id, sf.filename, l.line_number
            FROM Mutant m, Line l, SourceFile sf
            WHERE m.line = l.id
              AND l.sourcefile = sf.id
              AND m.status = "bad_survived"
              {{file_filter_sql}}
            ORDER BY sf.filename, l.line_number
            LIMIT 10
        """
        cursor.execute(query, file_filter_params)
        for mutant_id, filename, line_number in cursor.fetchall():
            print(f"  Mutant {{mutant_id}}: {{filename}}:{{line_number}}")
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
