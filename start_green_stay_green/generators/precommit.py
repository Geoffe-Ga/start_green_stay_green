"""Pre-commit hook configuration generator.

Generates customized .pre-commit-config.yaml files for target projects
with language-appropriate hooks for formatting, linting, security, and quality.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import cast

import yaml

from start_green_stay_green.generators.base import BaseGenerator


@dataclass
class GenerationConfig:
    """Configuration for generating pre-commit hooks.

    Attributes:
        project_name: Name of the project.
        language: Programming language (python, typescript, go, rust).
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
                "repo": "https://github.com/Lucas-C/pre-commit-hooks-safety",
                "rev": "v1.3.3",
                "hooks": [
                    {"id": "python-safety-dependencies-check"},
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
                "rev": "v3.15.0",
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
                "rev": "v1.26.0",
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
                "repo": "https://github.com/econchick/interrogate",
                "rev": "1.5.0",
                "hooks": [
                    {
                        "id": "interrogate",
                        "args": ["-vv", "--fail-under=95"],
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
}


class PreCommitGenerator(BaseGenerator):
    """Generates .pre-commit-config.yaml for target projects.

    Customizes pre-commit hooks based on project language and requirements.
    Includes formatting, linting, security, and general file quality checks.

    Supports: Python, TypeScript, Go, Rust, and other languages.

    Example:
        >>> from pathlib import Path
        >>> from start_green_stay_green.generators.base import GenerationConfig
        >>> generator = PreCommitGenerator()
        >>> config = GenerationConfig(
        ...     project_name="my-project",
        ...     language="python",
        ...     output_path=Path("."),
        ...     language_config={},
        ... )
        >>> content = generator.generate(config)
        >>> print(content[:100])
        # Pre-commit configuration for my-project
    """

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

    def generate(self, config: GenerationConfig) -> str:  # type: ignore[override]
        """Generate .pre-commit-config.yaml content.

        Produces a complete pre-commit configuration file customized for the
        target language with appropriate hooks for code quality, formatting,
        linting, and security scanning.

        Args:
            config: Generation configuration with project name and language.

        Returns:
            YAML-formatted pre-commit configuration content.

        Raises:
            ValueError: If language is not supported.
        """
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
        return header + yaml_content

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
        if language not in LANGUAGE_CONFIGS:
            msg = (
                f"Unsupported language: {language}. "
                f"Supported languages: {', '.join(LANGUAGE_CONFIGS.keys())}"
            )
            raise ValueError(msg)
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
        if language not in LANGUAGE_CONFIGS:
            msg = (
                f"Unsupported language: {language}. "
                f"Supported languages: {', '.join(LANGUAGE_CONFIGS.keys())}"
            )
            raise ValueError(msg)

        hooks_config = LANGUAGE_CONFIGS[language]["hooks"]
        return self._sum_hooks_in_repos(hooks_config)
