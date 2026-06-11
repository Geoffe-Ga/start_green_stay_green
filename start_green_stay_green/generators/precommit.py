"""Pre-commit hook configuration generator.

Generates customized .pre-commit-config.yaml files for target projects
with language-appropriate hooks for formatting, linting, security, and quality.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import TYPE_CHECKING
from typing import cast

import yaml

from start_green_stay_green.generators.base import BaseGenerator

if TYPE_CHECKING:
    from start_green_stay_green.ai.orchestrator import AIOrchestrator


@dataclass
class GenerationConfig:
    """Configuration for generating pre-commit hooks.

    Attributes:
        project_name: Name of the project.
        language: Programming language (python, typescript, go, rust,
            swift, kotlin, cpp, java, csharp, ruby).
        language_config: Additional language-specific configuration.
    """

    project_name: str
    language: str
    language_config: dict[str, Any]


# Language-specific pre-commit hook configurations
LANGUAGE_CONFIGS: dict[str, dict[str, Any]] = {
    "python": {
        "hooks": [
            {
                "repo": "https://github.com/pre-commit/pre-commit-hooks",
                "rev": "v4.5.0",
                "hooks": [
                    {"id": "trailing-whitespace"},
                    {"id": "end-of-file-fixer"},
                    {"id": "check-yaml"},
                    {"id": "check-toml"},
                    {"id": "check-json"},
                    {"id": "check-added-large-files", "args": ["--maxkb=500"]},
                    {"id": "check-case-conflict"},
                    {"id": "check-merge-conflict"},
                    {"id": "check-symlinks"},
                    {"id": "check-ast"},
                    {"id": "debug-statements"},
                    {"id": "check-docstring-first"},
                    {"id": "detect-private-key"},
                    {"id": "fix-byte-order-marker"},
                    {"id": "mixed-line-ending", "args": ["--fix=lf"]},
                    {"id": "no-commit-to-branch", "args": ["--branch", "main"]},
                ],
            },
            {
                "repo": "https://github.com/astral-sh/ruff-pre-commit",
                "rev": "v0.2.0",
                "hooks": [
                    {"id": "ruff", "args": ["--fix"]},
                    {"id": "ruff-format"},
                ],
            },
            {
                "repo": "https://github.com/psf/black",
                "rev": "24.1.0",
                "hooks": [
                    {"id": "black", "language_version": "python3.11"},
                ],
            },
            {
                "repo": "https://github.com/PyCQA/isort",
                "rev": "5.13.0",
                "hooks": [
                    {"id": "isort"},
                ],
            },
            {
                "repo": "https://github.com/pre-commit/mirrors-mypy",
                "rev": "v1.8.0",
                "hooks": [
                    {
                        "id": "mypy",
                        "additional_dependencies": ["types-all"],
                        "args": ["--strict"],
                    },
                ],
            },
            {
                "repo": "https://github.com/PyCQA/bandit",
                "rev": "1.7.7",
                "hooks": [
                    {
                        "id": "bandit",
                        "args": ["-c", "pyproject.toml"],
                        "additional_dependencies": ["bandit[toml]"],
                    },
                ],
            },
            {
                "repo": "https://github.com/pypa/pip-audit",
                "rev": "v2.7.3",
                "hooks": [
                    {"id": "pip-audit"},
                ],
            },
            {
                "repo": "https://github.com/compilerla/conventional-pre-commit",
                "rev": "v3.0.0",
                "hooks": [
                    {
                        "id": "conventional-pre-commit",
                        "stages": ["commit-msg"],
                    },
                ],
            },
            {
                "repo": "https://github.com/shellcheck-py/shellcheck-py",
                "rev": "v0.9.0.6",
                "hooks": [
                    {"id": "shellcheck"},
                ],
            },
            {
                "repo": "https://github.com/asottile/pyupgrade",
                "rev": "v3.21.2",
                "hooks": [
                    {"id": "pyupgrade", "args": ["--py311-plus"]},
                ],
            },
            {
                "repo": "https://github.com/PyCQA/autoflake",
                "rev": "v2.2.1",
                "hooks": [
                    {
                        "id": "autoflake",
                        "args": [
                            "--in-place",
                            "--remove-all-unused-imports",
                            "--remove-unused-variables",
                            "--remove-duplicate-keys",
                            "--ignore-init-module-imports",
                        ],
                    },
                ],
            },
            {
                "repo": "https://github.com/guilatrova/tryceratops",
                "rev": "v2.3.2",
                "hooks": [
                    {"id": "tryceratops"},
                ],
            },
            {
                "repo": "https://github.com/dosisod/refurb",
                "rev": "v2.3.1",
                "hooks": [
                    {"id": "refurb"},
                ],
            },
            {
                "repo": "https://github.com/jendrikseipp/vulture",
                "rev": "v2.10",
                "hooks": [
                    {
                        "id": "vulture",
                        "args": ["start_green_stay_green/", "--min-confidence", "80"],
                    },
                ],
            },
            {
                "repo": "https://github.com/Yelp/detect-secrets",
                "rev": "v1.4.0",
                "hooks": [
                    {
                        "id": "detect-secrets",
                        "args": ["--baseline", ".secrets.baseline"],
                    },
                ],
            },
        ],
        "default_language_version": {
            "python": "python3.11",
        },
    },
    "typescript": {
        "hooks": [
            {
                "repo": "https://github.com/pre-commit/pre-commit-hooks",
                "rev": "v4.5.0",
                "hooks": [
                    {"id": "trailing-whitespace"},
                    {"id": "end-of-file-fixer"},
                    {"id": "check-yaml"},
                    {"id": "check-json"},
                    {"id": "check-added-large-files", "args": ["--maxkb=500"]},
                    {"id": "check-case-conflict"},
                    {"id": "check-merge-conflict"},
                    {"id": "check-symlinks"},
                    {"id": "detect-private-key"},
                    {"id": "fix-byte-order-marker"},
                    {"id": "mixed-line-ending", "args": ["--fix=lf"]},
                    {"id": "no-commit-to-branch", "args": ["--branch", "main"]},
                ],
            },
            {
                "repo": "https://github.com/pre-commit/mirrors-prettier",
                "rev": "v4.0.0-alpha.8",
                "hooks": [
                    {
                        "id": "prettier",
                        "types_or": ["typescript", "tsx", "javascript", "json"],
                    },
                ],
            },
            {
                "repo": "https://github.com/shellcheck-py/shellcheck-py",
                "rev": "v0.9.0.6",
                "hooks": [
                    {"id": "shellcheck"},
                ],
            },
            {
                "repo": "https://github.com/Yelp/detect-secrets",
                "rev": "v1.4.0",
                "hooks": [
                    {
                        "id": "detect-secrets",
                        "args": ["--baseline", ".secrets.baseline"],
                    },
                ],
            },
        ],
        "default_language_version": {},
    },
    "go": {
        "hooks": [
            {
                "repo": "https://github.com/pre-commit/pre-commit-hooks",
                "rev": "v4.5.0",
                "hooks": [
                    {"id": "trailing-whitespace"},
                    {"id": "end-of-file-fixer"},
                    {"id": "check-yaml"},
                    {"id": "check-json"},
                    {"id": "check-added-large-files", "args": ["--maxkb=500"]},
                    {"id": "check-case-conflict"},
                    {"id": "check-merge-conflict"},
                    {"id": "check-symlinks"},
                    {"id": "detect-private-key"},
                    {"id": "fix-byte-order-marker"},
                    {"id": "mixed-line-ending", "args": ["--fix=lf"]},
                    {"id": "no-commit-to-branch", "args": ["--branch", "main"]},
                ],
            },
            {
                "repo": "https://github.com/golangci/golangci-lint",
                "rev": "v1.55.2",
                "hooks": [
                    {"id": "golangci-lint"},
                ],
            },
            {
                "repo": "https://github.com/shellcheck-py/shellcheck-py",
                "rev": "v0.9.0.6",
                "hooks": [
                    {"id": "shellcheck"},
                ],
            },
            {
                "repo": "https://github.com/Yelp/detect-secrets",
                "rev": "v1.4.0",
                "hooks": [
                    {
                        "id": "detect-secrets",
                        "args": ["--baseline", ".secrets.baseline"],
                    },
                ],
            },
        ],
        "default_language_version": {},
    },
    "rust": {
        "hooks": [
            {
                "repo": "https://github.com/pre-commit/pre-commit-hooks",
                "rev": "v4.5.0",
                "hooks": [
                    {"id": "trailing-whitespace"},
                    {"id": "end-of-file-fixer"},
                    {"id": "check-yaml"},
                    {"id": "check-toml"},
                    {"id": "check-json"},
                    {"id": "check-added-large-files", "args": ["--maxkb=500"]},
                    {"id": "check-case-conflict"},
                    {"id": "check-merge-conflict"},
                    {"id": "check-symlinks"},
                    {"id": "detect-private-key"},
                    {"id": "fix-byte-order-marker"},
                    {"id": "mixed-line-ending", "args": ["--fix=lf"]},
                    {"id": "no-commit-to-branch", "args": ["--branch", "main"]},
                ],
            },
            {
                "repo": "https://github.com/doublify/pre-commit-rust",
                "rev": "v1.0",
                "hooks": [
                    {
                        "id": "fmt",
                        "name": "Rustfmt",
                        "entry": "cargo fmt --",
                        "language": "system",
                        "types": ["rust"],
                        "pass_filenames": True,  # nosec B105  # Boolean config, not password
                    },
                    {
                        "id": "clippy",
                        "name": "Clippy",
                        "entry": "cargo clippy -- -D warnings",
                        "language": "system",
                        "types": ["rust"],
                        "pass_filenames": False,  # nosec B105  # Boolean config, not password
                    },
                ],
            },
            {
                "repo": "https://github.com/shellcheck-py/shellcheck-py",
                "rev": "v0.9.0.6",
                "hooks": [
                    {"id": "shellcheck"},
                ],
            },
            {
                "repo": "https://github.com/Yelp/detect-secrets",
                "rev": "v1.4.0",
                "hooks": [
                    {
                        "id": "detect-secrets",
                        "args": ["--baseline", ".secrets.baseline"],
                    },
                ],
            },
        ],
        "default_language_version": {},
    },
    "swift": {
        "hooks": [
            {
                "repo": "https://github.com/pre-commit/pre-commit-hooks",
                "rev": "v4.5.0",
                "hooks": [
                    {"id": "trailing-whitespace"},
                    {"id": "end-of-file-fixer"},
                    {"id": "check-yaml"},
                    {"id": "check-json"},
                    {"id": "check-added-large-files", "args": ["--maxkb=500"]},
                    {"id": "check-case-conflict"},
                    {"id": "check-merge-conflict"},
                    {"id": "check-symlinks"},
                    {"id": "detect-private-key"},
                    {"id": "fix-byte-order-marker"},
                    {"id": "mixed-line-ending", "args": ["--fix=lf"]},
                    {"id": "no-commit-to-branch", "args": ["--branch", "main"]},
                ],
            },
            # swift-format and SwiftLint run as `repo: local` system hooks
            # (mirroring how the Rust hooks invoke the cargo toolchain):
            # apple/swift-format ships no .pre-commit-hooks.yaml, and
            # realm/SwiftLint's remote hook builds SwiftLint from source via
            # SPM on first run (a multi-minute build). Install both with:
            # `brew install swift-format swiftlint`.
            {
                "repo": "local",
                "hooks": [
                    {
                        "id": "swift-format",
                        "name": "swift-format",
                        "entry": "swift-format format --in-place",
                        "language": "system",
                        "types": ["swift"],
                    },
                    {
                        "id": "swiftlint",
                        "name": "SwiftLint",
                        # --strict promotes warnings to errors; reads the
                        # generated .swiftlint.yml (cyclomatic_complexity
                        # <=10 plus the crash-safety/security opt-in rules).
                        "entry": "swiftlint lint --strict",
                        "language": "system",
                        "types": ["swift"],
                        "pass_filenames": False,  # nosec B105  # Boolean config, not password
                    },
                ],
            },
            {
                "repo": "https://github.com/gitleaks/gitleaks",
                "rev": "v8.18.4",
                "hooks": [
                    {"id": "gitleaks"},
                ],
            },
            {
                "repo": "https://github.com/shellcheck-py/shellcheck-py",
                "rev": "v0.9.0.6",
                "hooks": [
                    {"id": "shellcheck"},
                ],
            },
            {
                "repo": "https://github.com/Yelp/detect-secrets",
                "rev": "v1.4.0",
                "hooks": [
                    {
                        "id": "detect-secrets",
                        "args": ["--baseline", ".secrets.baseline"],
                    },
                ],
            },
        ],
        "default_language_version": {},
    },
    "kotlin": {
        "hooks": [
            {
                "repo": "https://github.com/pre-commit/pre-commit-hooks",
                "rev": "v4.5.0",
                "hooks": [
                    {"id": "trailing-whitespace"},
                    {"id": "end-of-file-fixer"},
                    {"id": "check-yaml"},
                    {"id": "check-json"},
                    {"id": "check-added-large-files", "args": ["--maxkb=500"]},
                    {"id": "check-case-conflict"},
                    {"id": "check-merge-conflict"},
                    {"id": "check-symlinks"},
                    {"id": "detect-private-key"},
                    {"id": "fix-byte-order-marker"},
                    {"id": "mixed-line-ending", "args": ["--fix=lf"]},
                    {"id": "no-commit-to-branch", "args": ["--branch", "main"]},
                ],
            },
            # ktlint and detekt run as `repo: local` system hooks
            # (mirroring the Swift swift-format/SwiftLint hooks): neither
            # pinterest/ktlint nor detekt/detekt ships an official
            # .pre-commit-hooks.yaml manifest, so a remote hook repo would
            # have to point at an unofficial mirror. Install both with:
            # `brew install ktlint detekt`.
            {
                "repo": "local",
                "hooks": [
                    {
                        "id": "ktlint",
                        "name": "ktlint",
                        # --format fixes what it can and still fails on
                        # the violations it cannot fix.
                        "entry": "ktlint --format",
                        "language": "system",
                        "types": ["kotlin"],
                    },
                    {
                        "id": "detekt",
                        "name": "detekt",
                        # Reads the generated detekt.yml (complexity <=10
                        # gate + potential-bugs rules) on top of detekt's
                        # default config, the same file lint.sh uses.
                        "entry": (
                            "detekt --config detekt.yml "
                            "--build-upon-default-config "
                            "--excludes **/build/**"
                        ),
                        "language": "system",
                        "types": ["kotlin"],
                        "pass_filenames": False,  # nosec B105  # Boolean config, not password
                    },
                ],
            },
            {
                "repo": "https://github.com/gitleaks/gitleaks",
                "rev": "v8.18.4",
                "hooks": [
                    {"id": "gitleaks"},
                ],
            },
            {
                "repo": "https://github.com/shellcheck-py/shellcheck-py",
                "rev": "v0.9.0.6",
                "hooks": [
                    {"id": "shellcheck"},
                ],
            },
            {
                "repo": "https://github.com/Yelp/detect-secrets",
                "rev": "v1.4.0",
                "hooks": [
                    {
                        "id": "detect-secrets",
                        "args": ["--baseline", ".secrets.baseline"],
                    },
                ],
            },
        ],
        "default_language_version": {},
    },
    "java": {
        "hooks": [
            {
                "repo": "https://github.com/pre-commit/pre-commit-hooks",
                "rev": "v4.5.0",
                "hooks": [
                    {"id": "trailing-whitespace"},
                    {"id": "end-of-file-fixer"},
                    {"id": "check-yaml"},
                    {"id": "check-json"},
                    # AndroidManifest.xml and the res/layout XML are the
                    # scaffold's Android surface, so XML well-formedness
                    # is gated here (the tizen-manifest.xml precedent).
                    {"id": "check-xml"},
                    {"id": "check-added-large-files", "args": ["--maxkb=500"]},
                    {"id": "check-case-conflict"},
                    {"id": "check-merge-conflict"},
                    {"id": "check-symlinks"},
                    {"id": "detect-private-key"},
                    {"id": "fix-byte-order-marker"},
                    {"id": "mixed-line-ending", "args": ["--fix=lf"]},
                    {"id": "no-commit-to-branch", "args": ["--branch", "main"]},
                ],
            },
            # google-java-format runs as a `repo: local` system hook
            # (the Swift/Kotlin precedent): unlike clang-format there is
            # no official pre-commit mirror — the only hook repos are
            # unofficial wrappers that download release jars at runtime.
            # Install with: `brew install google-java-format` (macOS) or
            # grab the all-deps release jar from
            # https://github.com/google/google-java-format/releases and
            # wrap it in a `google-java-format` launcher script.
            #
            # checkstyle/pmd/spotbugs invoke the Maven goals the #366 pom
            # already pins and configures (google_checks, the
            # pmd-ruleset.xml CCN companion, SpotBugs). Maven-goal hooks
            # are slower than native binaries but zero-install and
            # cannot version-drift from the build: pom.xml is the single
            # source of tool truth, locally, in pre-commit, and in CI.
            {
                "repo": "local",
                "hooks": [
                    {
                        "id": "google-java-format",
                        "name": "google-java-format",
                        # Check-mode: --replace exits 0 whether or not it
                        # changed files, so it can never fail a commit.
                        # --dry-run --set-exit-if-changed fails the hook
                        # on unformatted files; scripts/format.sh keeps
                        # --replace for the fixing path.
                        "entry": (
                            "google-java-format --dry-run" " --set-exit-if-changed"
                        ),
                        "language": "system",
                        "types": ["java"],
                    },
                    {
                        "id": "checkstyle",
                        "name": "Checkstyle (mvn)",
                        # Reads the google_checks configLocation pinned
                        # in pom.xml.
                        "entry": "mvn -q checkstyle:check",
                        "language": "system",
                        "types": ["java"],
                        "pass_filenames": False,  # nosec B105  # Boolean config, not password
                    },
                    {
                        "id": "pmd",
                        "name": "PMD (mvn)",
                        # Reads the pom's rulesets: the maven-pmd-plugin
                        # defaults plus the pmd-ruleset.xml companion
                        # (cyclomatic complexity <=10 gate) that
                        # scripts/lint.sh shares.
                        "entry": "mvn -q pmd:check",
                        "language": "system",
                        "types": ["java"],
                        "pass_filenames": False,  # nosec B105  # Boolean config, not password
                    },
                    {
                        "id": "spotbugs",
                        "name": "SpotBugs (mvn)",
                        # SpotBugs reads bytecode and `mvn spotbugs:check`
                        # silently skips when target/classes is empty, so
                        # the compile phase runs first or the gate would
                        # be a no-op.
                        "entry": "mvn -q compile spotbugs:check",
                        "language": "system",
                        "types": ["java"],
                        "pass_filenames": False,  # nosec B105  # Boolean config, not password
                    },
                ],
            },
            {
                "repo": "https://github.com/gitleaks/gitleaks",
                "rev": "v8.18.4",
                "hooks": [
                    {"id": "gitleaks"},
                ],
            },
            {
                "repo": "https://github.com/shellcheck-py/shellcheck-py",
                "rev": "v0.9.0.6",
                "hooks": [
                    {"id": "shellcheck"},
                ],
            },
            {
                "repo": "https://github.com/Yelp/detect-secrets",
                "rev": "v1.4.0",
                "hooks": [
                    {
                        "id": "detect-secrets",
                        "args": ["--baseline", ".secrets.baseline"],
                    },
                ],
            },
        ],
        "default_language_version": {},
    },
    "csharp": {
        "hooks": [
            {
                "repo": "https://github.com/pre-commit/pre-commit-hooks",
                "rev": "v4.5.0",
                "hooks": [
                    {"id": "trailing-whitespace"},
                    {"id": "end-of-file-fixer"},
                    {"id": "check-yaml"},
                    {"id": "check-json"},
                    # identify tags .csproj files as xml, so the stock
                    # check-xml hook gates the manifest's
                    # well-formedness (the AndroidManifest.xml /
                    # tizen-manifest.xml precedent).
                    {"id": "check-xml"},
                    {"id": "check-added-large-files", "args": ["--maxkb=500"]},
                    {"id": "check-case-conflict"},
                    {"id": "check-merge-conflict"},
                    {"id": "check-symlinks"},
                    {"id": "detect-private-key"},
                    {"id": "fix-byte-order-marker"},
                    {"id": "mixed-line-ending", "args": ["--fix=lf"]},
                    {"id": "no-commit-to-branch", "args": ["--branch", "main"]},
                ],
            },
            # Both C# hooks run the dotnet CLI as `repo: local` system
            # hooks (the Swift/Kotlin/Java precedent: no official
            # pre-commit mirror exists for the .NET toolchain). Install
            # the .NET 8 SDK with: `brew install dotnet-sdk` (macOS) or
            # `apt-get install dotnet-sdk-8.0` (Debian/Ubuntu) — both
            # `dotnet format` and the Roslyn analyzers ship inside it,
            # so there is nothing else to install.
            #
            # dotnet operates on the project (not a file list), so both
            # hooks set pass_filenames: false and use the c# type
            # filter only to decide WHETHER to run.
            {
                "repo": "local",
                "hooks": [
                    {
                        "id": "dotnet-format",
                        "name": "dotnet format (check mode)",
                        # Check-mode: a bare `dotnet format` rewrites
                        # files and exits 0 either way, so it could
                        # never fail a commit. --verify-no-changes
                        # exits non-zero on unformatted code;
                        # scripts/format.sh keeps the fixing path.
                        "entry": "dotnet format --verify-no-changes",
                        "language": "system",
                        "types": ["c#"],
                        "pass_filenames": False,  # nosec B105  # Boolean config, not password
                    },
                    {
                        "id": "roslyn-analyzers",
                        "name": "Roslyn analyzers (dotnet build)",
                        # The csproj is the single home of the lint
                        # policy. It enables the SDK analyzers (with
                        # the CA1502 <=10 complexity ceiling switched
                        # on via .editorconfig and bounded by
                        # CodeMetricsConfig.txt, plus the
                        # SecurityCodeScan analyzer) and treats
                        # warnings as errors, so this plain build
                        # fails on findings — no -warnaserror restated
                        # here.
                        "entry": "dotnet build --nologo",
                        "language": "system",
                        "types": ["c#"],
                        "pass_filenames": False,  # nosec B105  # Boolean config, not password
                    },
                ],
            },
            {
                "repo": "https://github.com/gitleaks/gitleaks",
                "rev": "v8.18.4",
                "hooks": [
                    {"id": "gitleaks"},
                ],
            },
            {
                "repo": "https://github.com/shellcheck-py/shellcheck-py",
                "rev": "v0.9.0.6",
                "hooks": [
                    {"id": "shellcheck"},
                ],
            },
            {
                "repo": "https://github.com/Yelp/detect-secrets",
                "rev": "v1.4.0",
                "hooks": [
                    {
                        "id": "detect-secrets",
                        "args": ["--baseline", ".secrets.baseline"],
                    },
                ],
            },
        ],
        "default_language_version": {},
    },
    "ruby": {
        "hooks": [
            {
                "repo": "https://github.com/pre-commit/pre-commit-hooks",
                "rev": "v4.5.0",
                "hooks": [
                    {"id": "trailing-whitespace"},
                    {"id": "end-of-file-fixer"},
                    {"id": "check-yaml"},
                    {"id": "check-json"},
                    {"id": "check-added-large-files", "args": ["--maxkb=500"]},
                    {"id": "check-case-conflict"},
                    {"id": "check-merge-conflict"},
                    {"id": "check-symlinks"},
                    {"id": "detect-private-key"},
                    {"id": "fix-byte-order-marker"},
                    {"id": "mixed-line-ending", "args": ["--fix=lf"]},
                    {"id": "no-commit-to-branch", "args": ["--branch", "main"]},
                ],
            },
            # RuboCop is the one official-hook language in the matrix:
            # rubocop/rubocop ships a .pre-commit-hooks.yaml at its repo
            # root (verified at the pinned tag), so no `repo: local`
            # system hook is needed. `language: ruby` means pre-commit
            # builds an isolated gem environment from the pinned tag —
            # a Ruby runtime must be on PATH, but the RuboCop version
            # can never drift from this rev.
            #
            # The manifest's DEFAULT args include --autocorrect, which
            # rewrites correctable offenses and would let them through
            # (the #430 formatter lesson: a fixing-mode hook can fail
            # only via pre-commit's file-modified detection, and silently
            # passes once files are clean-but-unchecked-in). Overriding
            # args to --force-exclusion alone makes the hook check-mode:
            # plain `rubocop` exits non-zero on ANY offense.
            # scripts/format.sh keeps the --autocorrect fixing path.
            #
            # One hook covers format (Layout cops), lint (Lint/Style),
            # complexity (Metrics/CyclomaticComplexity <=10), and the
            # source-level Security cops — .rubocop.yml at the project
            # root is the single home of that policy, shared with
            # scripts/lint.sh and CI; no flag here restates any of it.
            {
                "repo": "https://github.com/rubocop/rubocop",
                "rev": "v1.87.0",
                "hooks": [
                    {
                        "id": "rubocop",
                        "args": ["--force-exclusion"],
                    },
                ],
            },
            {
                "repo": "https://github.com/gitleaks/gitleaks",
                "rev": "v8.18.4",
                "hooks": [
                    {"id": "gitleaks"},
                ],
            },
            {
                "repo": "https://github.com/shellcheck-py/shellcheck-py",
                "rev": "v0.9.0.6",
                "hooks": [
                    {"id": "shellcheck"},
                ],
            },
            {
                "repo": "https://github.com/Yelp/detect-secrets",
                "rev": "v1.4.0",
                "hooks": [
                    {
                        "id": "detect-secrets",
                        "args": ["--baseline", ".secrets.baseline"],
                    },
                ],
            },
        ],
        "default_language_version": {},
    },
    "cpp": {
        "hooks": [
            {
                "repo": "https://github.com/pre-commit/pre-commit-hooks",
                "rev": "v4.5.0",
                "hooks": [
                    {"id": "trailing-whitespace"},
                    {"id": "end-of-file-fixer"},
                    {"id": "check-yaml"},
                    {"id": "check-json"},
                    # tizen-manifest.xml is the scaffold's central
                    # manifest, so XML well-formedness is gated here.
                    {"id": "check-xml"},
                    {"id": "check-added-large-files", "args": ["--maxkb=500"]},
                    {"id": "check-case-conflict"},
                    {"id": "check-merge-conflict"},
                    {"id": "check-symlinks"},
                    {"id": "detect-private-key"},
                    {"id": "fix-byte-order-marker"},
                    {"id": "mixed-line-ending", "args": ["--fix=lf"]},
                    {"id": "no-commit-to-branch", "args": ["--branch", "main"]},
                ],
            },
            # clang-format runs from its official pre-commit mirror
            # (pre-commit/mirrors-clang-format), which installs a pinned
            # clang-format wheel from PyPI — no local LLVM install needed
            # for formatting. It reads the .clang-format companion config
            # at the project root (args: -style=file is the mirror's
            # default), the same file scripts/format.sh uses. The rev pins
            # LLVM 18 to match current distro toolchains (Ubuntu 24.04
            # ships clang-format-18); bump it together with your local
            # clang-format so the hook and format.sh agree byte-for-byte.
            {
                "repo": "https://github.com/pre-commit/mirrors-clang-format",
                "rev": "v18.1.8",
                "hooks": [
                    {"id": "clang-format", "types_or": ["c", "c++"]},
                ],
            },
            # clang-tidy and cppcheck run as `repo: local` system hooks
            # (mirroring the Swift/Kotlin lint hooks): neither ships an
            # official .pre-commit-hooks.yaml manifest. Install with:
            # `brew install llvm cppcheck` (macOS) or
            # `apt-get install clang-tidy cppcheck` (Debian/Ubuntu).
            {
                "repo": "local",
                "hooks": [
                    {
                        "id": "clang-tidy",
                        "name": "clang-tidy",
                        # Reads the generated .clang-tidy companion config
                        # (bugprone/cert/clang-analyzer/... checks promoted
                        # to errors), the same file lint.sh uses. Requires
                        # build/compile_commands.json, exported by the
                        # documented cmake configure step
                        # (CMAKE_EXPORT_COMPILE_COMMANDS is ON in the
                        # generated CMakeLists.txt). Runs on .cpp files
                        # only: headers have no compile command of their
                        # own and are covered via HeaderFilterRegex, and
                        # pure-C sources are deliberately left to
                        # cppcheck below (types_or covers c and c++) —
                        # clang-tidy's check set here is C++-oriented and
                        # would need a separate -std=cNN profile to add
                        # value for C. The -p path assumes the documented
                        # `cmake -B build` configure step; a different
                        # build dir must be mirrored here and in lint.sh
                        # or clang-tidy silently runs without compile
                        # commands.
                        "entry": "clang-tidy -p build",
                        "language": "system",
                        "types": ["c++"],
                    },
                    {
                        "id": "cppcheck",
                        "name": "cppcheck",
                        # warning/performance/portability only: style and
                        # readability are clang-tidy's job, so the two
                        # linters do not double-report the same findings.
                        "entry": (
                            "cppcheck --enable=warning,performance,portability "
                            "--error-exitcode=1 --inline-suppr "
                            "--suppress=missingIncludeSystem"
                        ),
                        "language": "system",
                        "types_or": ["c", "c++"],
                    },
                ],
            },
            {
                "repo": "https://github.com/gitleaks/gitleaks",
                "rev": "v8.18.4",
                "hooks": [
                    {"id": "gitleaks"},
                ],
            },
            {
                "repo": "https://github.com/shellcheck-py/shellcheck-py",
                "rev": "v0.9.0.6",
                "hooks": [
                    {"id": "shellcheck"},
                ],
            },
            {
                "repo": "https://github.com/Yelp/detect-secrets",
                "rev": "v1.4.0",
                "hooks": [
                    {
                        "id": "detect-secrets",
                        "args": ["--baseline", ".secrets.baseline"],
                    },
                ],
            },
        ],
        "default_language_version": {},
    },
}


class PreCommitGenerator(BaseGenerator):
    """Generates .pre-commit-config.yaml for target projects.

    Customizes pre-commit hooks based on project language and requirements.
    Includes formatting, linting, security, and general file quality checks.

    Supports: Python, TypeScript, Go, Rust, Swift, Kotlin, C/C++ (cpp),
    Java, C# (csharp), Ruby, and other languages.

    Attributes:
        orchestrator: Optional AI orchestrator for enhanced generation.
            If None, generator uses pure configuration-based generation.

    Example:
        >>> from start_green_stay_green.generators.precommit import GenerationConfig
        >>> generator = PreCommitGenerator()
        >>> config = GenerationConfig(
        ...     project_name="my-project",
        ...     language="python",
        ...     language_config={},
        ... )
        >>> result = generator.generate(config)
        >>> print(result["content"][:100])
        # Pre-commit configuration for my-project
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator | None = None,
        *,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize pre-commit generator.

        Args:
            orchestrator: Optional AI orchestrator for enhanced generation.
                If None, uses pure configuration-based generation.
            config: Optional additional configuration dictionary.
                Reserved for future use in AI-enhanced generation.
        """
        self.orchestrator = orchestrator
        self.config = config or {}

    def _validate_language_supported(self, language: str) -> None:
        """Validate that language is supported.

        Args:
            language: Language identifier to validate.

        Raises:
            ValueError: If language is not supported.
        """
        if language not in LANGUAGE_CONFIGS:
            msg = (
                f"Unsupported language: {language}. "
                f"Supported languages: {', '.join(LANGUAGE_CONFIGS.keys())}"
            )
            raise ValueError(msg)

    def _build_config_dict(self, language: str) -> dict[str, Any]:
        """Build pre-commit configuration dictionary.

        Args:
            language: Language identifier.

        Returns:
            Configuration dictionary with repos, CI settings, and language versions.
        """
        language_config = LANGUAGE_CONFIGS[language]
        return {
            "default_language_version": language_config["default_language_version"],
            "repos": language_config["hooks"],
            "ci": {
                "autofix_commit_msg": "style: auto-fix by pre-commit hooks",
                "autoupdate_commit_msg": "chore: update pre-commit hooks",
                "skip": [],
            },
        }

    def _generate_header(self, project_name: str) -> str:
        """Generate YAML header comment with instructions.

        Args:
            project_name: Name of the project.

        Returns:
            Header comment string.
        """
        return (
            f"# Pre-commit hooks configuration for {project_name}\n"
            "# Install: pre-commit install\n"
            "# Run manually: pre-commit run --all-files\n\n"
        )

    def generate(
        self,
        config: GenerationConfig | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> dict[str, Any]:
        """Generate .pre-commit-config.yaml content.

        Produces a complete pre-commit configuration file customized for the
        target language with appropriate hooks for code quality, formatting,
        linting, and security scanning.

        Args:
            config: Generation configuration with project name and language.
                Can be passed as positional or keyword argument.
            **kwargs: Alternative way to pass config as keyword arguments
                (project_name, language, language_config).

        Returns:
            Dictionary with keys:
                - content: YAML-formatted pre-commit configuration
                - repos: List of repository configurations
                - languages: List of supported languages

        Raises:
            ValueError: If language is not supported.
            TypeError: If config not provided or has wrong type.
        """
        # Handle flexible input - config positional or via kwargs
        if config is None:
            if "project_name" in kwargs and "language" in kwargs:
                config = GenerationConfig(
                    project_name=kwargs["project_name"],
                    language=kwargs["language"],
                    language_config=kwargs.get("language_config", {}),
                )
            else:
                msg = (
                    "generate() requires GenerationConfig or "
                    "(project_name, language) keyword arguments"
                )
                raise TypeError(msg)

        self._validate_language_supported(config.language)
        config_dict = self._build_config_dict(config.language)

        # Convert to YAML
        yaml_content = yaml.dump(
            config_dict,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        header = self._generate_header(config.project_name)
        content = header + yaml_content

        return {
            "content": content,
            "repos": config_dict["repos"],
            "languages": list(LANGUAGE_CONFIGS.keys()),
        }

    def generate_yaml(self, config: GenerationConfig) -> str:
        """Legacy method for backward compatibility.

        This method wraps generate() and returns only the YAML content string.

        Args:
            config: Generation configuration with project name and language.

        Returns:
            YAML-formatted pre-commit configuration content as string.

        Raises:
            ValueError: If language is not supported.

        Deprecated:
            Use generate() instead. This method will be removed in v2.0.
        """
        result = self.generate(config)
        content: str = result["content"]
        return content

    def validate_language(self, language: str) -> bool:
        """Check if language is supported.

        Args:
            language: Language identifier to validate.

        Returns:
            True if language is supported, False otherwise.

        Example:
            >>> generator = PreCommitGenerator()
            >>> generator.validate_language("python")
            True
            >>> generator.validate_language("cobol")
            False
        """
        return language in LANGUAGE_CONFIGS

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages.

        Returns:
            List of language identifiers that can be configured.

        Example:
            >>> generator = PreCommitGenerator()
            >>> langs = generator.get_supported_languages()
            >>> "python" in langs
            True
        """
        return list(LANGUAGE_CONFIGS.keys())

    def get_language_hooks(self, language: str) -> list[dict[str, Any]]:
        """Get hooks configured for a specific language.

        Args:
            language: Language identifier.

        Returns:
            List of hook configurations for the language.

        Raises:
            ValueError: If language is not supported.

        Example:
            >>> generator = PreCommitGenerator()
            >>> hooks = generator.get_language_hooks("python")
            >>> len(hooks) > 0
            True
        """
        self._validate_language_supported(language)
        # Cast to satisfy mypy strict mode - dict access returns Any
        return cast("list[dict[str, Any]]", LANGUAGE_CONFIGS[language]["hooks"])

    def _sum_hooks_in_repos(self, repos_config: list[dict[str, Any]]) -> int:
        """Sum total hooks across all repository configurations.

        Args:
            repos_config: List of repository configurations.

        Returns:
            Total count of hooks across all repositories.
        """
        return sum(len(repo.get("hooks", [])) for repo in repos_config)

    def count_hooks_for_language(self, language: str) -> int:
        """Count total number of hooks configured for a language.

        Args:
            language: Language identifier.

        Returns:
            Total number of individual hooks configured.

        Raises:
            ValueError: If language is not supported.

        Example:
            >>> generator = PreCommitGenerator()
            >>> count = generator.count_hooks_for_language("python")
            >>> count > 20
            True
        """
        self._validate_language_supported(language)

        hooks_config = LANGUAGE_CONFIGS[language]["hooks"]
        return self._sum_hooks_in_repos(hooks_config)
