"""Integration tests for Pre-commit Generator."""

from pathlib import Path
import tempfile

import pytest
import yaml

from start_green_stay_green.generators.base import GenerationConfig
from start_green_stay_green.generators.precommit import PreCommitGenerator


@pytest.mark.integration
class TestPreCommitGeneratorIntegration:
    """Test Pre-commit Generator in integration scenarios."""

    def test_generate_and_write_python_config(self) -> None:
        """Test generating and writing Python pre-commit config."""
        generator = PreCommitGenerator()
        config = GenerationConfig(
            project_name="integration-test",
            language="python",
            output_path=Path(),
            language_config={},
        )
        result = generator.generate(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(result)
            temp_path = Path(f.name)

        try:
            # Verify file was created
            assert temp_path.exists()

            # Verify file can be read and parsed
            with temp_path.open() as f:
                content = f.read()
                yaml_lines = [
                    line for line in content.split("\n") if not line.startswith("#")
                ]
                yaml_content = "\n".join(yaml_lines)
                parsed = yaml.safe_load(yaml_content)

            assert parsed is not None
            assert "repos" in parsed
            assert len(parsed["repos"]) > 0
        finally:
            temp_path.unlink()

    def test_generate_and_write_typescript_config(self) -> None:
        """Test generating and writing TypeScript pre-commit config."""
        generator = PreCommitGenerator()
        config = GenerationConfig(
            project_name="ts-integration-test",
            language="typescript",
            output_path=Path(),
            language_config={},
        )
        result = generator.generate(config)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(result)
            temp_path = Path(f.name)

        try:
            assert temp_path.exists()
            with temp_path.open() as f:
                content = f.read()
                yaml_lines = [
                    line for line in content.split("\n") if not line.startswith("#")
                ]
                yaml_content = "\n".join(yaml_lines)
                parsed = yaml.safe_load(yaml_content)

            assert parsed is not None
            assert "repos" in parsed
        finally:
            temp_path.unlink()

    def test_multiple_languages_workflow(self) -> None:
        """Test generating configs for multiple languages."""
        generator = PreCommitGenerator()
        languages = ["python", "typescript", "go", "rust"]

        for language in languages:
            config = GenerationConfig(
                project_name=f"{language}-project",
                language=language,
                output_path=Path(),
                language_config={},
            )
            result = generator.generate(config)
            assert language in result or f"{language}-project" in result
            assert "repos" in result

    def test_generated_config_has_valid_structure_for_all_languages(self) -> None:
        """Test all language configs have valid YAML structure."""
        generator = PreCommitGenerator()

        for language in generator.get_supported_languages():
            config = GenerationConfig(
                project_name="test",
                language=language,
                output_path=Path(),
                language_config={},
            )
            result = generator.generate(config)

            # Extract YAML content (skip comments)
            yaml_lines = [
                line for line in result.split("\n") if not line.startswith("#")
            ]
            yaml_content = "\n".join(yaml_lines)

            # Parse and validate structure
            parsed = yaml.safe_load(yaml_content)
            assert isinstance(parsed, dict)
            assert "default_language_version" in parsed
            assert "repos" in parsed
            assert "ci" in parsed
            assert isinstance(parsed["repos"], list)
            assert isinstance(parsed["ci"], dict)

    def test_generated_repos_have_required_fields(self) -> None:
        """Test all generated repos have required fields."""
        generator = PreCommitGenerator()
        config = GenerationConfig(
            project_name="test",
            language="python",
            output_path=Path(),
            language_config={},
        )
        result = generator.generate(config)

        yaml_lines = [line for line in result.split("\n") if not line.startswith("#")]
        yaml_content = "\n".join(yaml_lines)
        parsed = yaml.safe_load(yaml_content)

        repos = parsed["repos"]
        for repo in repos:
            # Each repo should have either repo field or hooks
            if "repo" in repo:
                assert isinstance(repo["repo"], str)
                assert len(repo["repo"]) > 0
            assert "hooks" in repo
            assert isinstance(repo["hooks"], list)

    def test_python_config_includes_critical_hooks(self) -> None:
        """Test Python config includes all critical hooks."""
        generator = PreCommitGenerator()
        config = GenerationConfig(
            project_name="test",
            language="python",
            output_path=Path(),
            language_config={},
        )
        result = generator.generate(config)

        yaml_lines = [line for line in result.split("\n") if not line.startswith("#")]
        yaml_content = "\n".join(yaml_lines)
        parsed = yaml.safe_load(yaml_content)

        repos = parsed["repos"]
        repo_urls = [repo.get("repo", "") for repo in repos]

        # Check for critical Python tools
        critical_tools = ["ruff", "black", "mypy", "bandit"]
        for tool in critical_tools:
            assert any(tool in url for url in repo_urls), f"Missing {tool}"

    def test_ci_configuration_present_in_all_languages(self) -> None:
        """Test CI configuration is present for all languages."""
        generator = PreCommitGenerator()

        for language in generator.get_supported_languages():
            config = GenerationConfig(
                project_name="test",
                language=language,
                output_path=Path(),
                language_config={},
            )
            result = generator.generate(config)

            yaml_lines = [
                line for line in result.split("\n") if not line.startswith("#")
            ]
            yaml_content = "\n".join(yaml_lines)
            parsed = yaml.safe_load(yaml_content)

            assert "ci" in parsed
            ci_config = parsed["ci"]
            assert "autofix_commit_msg" in ci_config
            assert "autoupdate_commit_msg" in ci_config
            assert "skip" in ci_config

    def test_project_name_appears_in_output(self) -> None:
        """Test project name appears in generated output."""
        generator = PreCommitGenerator()
        project_names = [
            "my-awesome-project",
            "test_project_123",
            "project-with-dashes",
        ]

        for project_name in project_names:
            config = GenerationConfig(
                project_name=project_name,
                language="python",
                output_path=Path(),
                language_config={},
            )
            result = generator.generate(config)
            assert project_name in result

    def test_yaml_roundtrip_consistency(self) -> None:
        """Test YAML can be parsed, modified, and re-serialized."""
        generator = PreCommitGenerator()
        config = GenerationConfig(
            project_name="roundtrip-test",
            language="python",
            output_path=Path(),
            language_config={},
        )
        original = generator.generate(config)

        # Parse YAML
        yaml_lines = [line for line in original.split("\n") if not line.startswith("#")]
        yaml_content = "\n".join(yaml_lines)
        parsed = yaml.safe_load(yaml_content)

        # Re-serialize
        reserialized = yaml.dump(
            parsed, default_flow_style=False, sort_keys=False, allow_unicode=True
        )

        # Parse again to verify consistency
        reparsed = yaml.safe_load(reserialized)
        assert reparsed == parsed

    def test_language_specific_hooks_for_typescript(self) -> None:
        """Test TypeScript config has prettier (language-specific)."""
        generator = PreCommitGenerator()
        config = GenerationConfig(
            project_name="ts-test",
            language="typescript",
            output_path=Path(),
            language_config={},
        )
        result = generator.generate(config)

        yaml_lines = [line for line in result.split("\n") if not line.startswith("#")]
        yaml_content = "\n".join(yaml_lines)
        parsed = yaml.safe_load(yaml_content)

        repos = parsed["repos"]
        repo_urls = [repo.get("repo", "") for repo in repos]

        # TypeScript should have prettier
        assert any("prettier" in url for url in repo_urls)

    def test_language_specific_hooks_for_go(self) -> None:
        """Test Go config has golangci-lint (language-specific)."""
        generator = PreCommitGenerator()
        config = GenerationConfig(
            project_name="go-test",
            language="go",
            output_path=Path(),
            language_config={},
        )
        result = generator.generate(config)

        yaml_lines = [line for line in result.split("\n") if not line.startswith("#")]
        yaml_content = "\n".join(yaml_lines)
        parsed = yaml.safe_load(yaml_content)

        repos = parsed["repos"]
        repo_urls = [repo.get("repo", "") for repo in repos]

        # Go should have golangci-lint
        assert any("golangci-lint" in url for url in repo_urls)

    def test_language_specific_hooks_for_rust(self) -> None:
        """Test Rust config has clippy and rustfmt (language-specific)."""
        generator = PreCommitGenerator()
        config = GenerationConfig(
            project_name="rust-test",
            language="rust",
            output_path=Path(),
            language_config={},
        )
        result = generator.generate(config)

        yaml_lines = [line for line in result.split("\n") if not line.startswith("#")]
        yaml_content = "\n".join(yaml_lines)
        parsed = yaml.safe_load(yaml_content)

        repos = parsed["repos"]
        rust_repo = next(
            (repo for repo in repos if "pre-commit-rust" in repo.get("repo", "")),
            None,
        )

        assert rust_repo is not None
        hooks = rust_repo.get("hooks", [])
        hook_ids = [hook.get("id", "") for hook in hooks]
        assert "fmt" in hook_ids
        assert "clippy" in hook_ids

    def test_shared_hooks_across_languages(self) -> None:
        """Test common hooks appear in all language configs."""
        generator = PreCommitGenerator()

        # Get hooks for all languages
        all_language_hooks = {
            lang: generator.get_language_hooks(lang)
            for lang in generator.get_supported_languages()
        }

        # All should have pre-commit-hooks basic checks
        for language, hooks in all_language_hooks.items():
            repo_urls = [repo.get("repo", "") for repo in hooks]
            assert any(
                "pre-commit/pre-commit-hooks" in url for url in repo_urls
            ), f"{language} missing basic pre-commit-hooks"

    def test_all_hooks_have_id_or_entry(self) -> None:
        """Test all configured hooks have id or entry field."""
        generator = PreCommitGenerator()
        config = GenerationConfig(
            project_name="test",
            language="python",
            output_path=Path(),
            language_config={},
        )
        result = generator.generate(config)

        yaml_lines = [line for line in result.split("\n") if not line.startswith("#")]
        yaml_content = "\n".join(yaml_lines)
        parsed = yaml.safe_load(yaml_content)

        repos = parsed["repos"]
        for repo in repos:
            hooks = repo.get("hooks", [])
            for hook in hooks:
                # Each hook must have either id or entry
                assert (
                    "id" in hook or "entry" in hook
                ), f"Hook missing id or entry: {hook}"

    def test_generator_performance_multiple_calls(self) -> None:
        """Test generator performs well across multiple calls."""
        generator = PreCommitGenerator()

        for i in range(10):
            config = GenerationConfig(
                project_name=f"perf-test-{i}",
                language="python",
                output_path=Path(),
                language_config={},
            )
            result = generator.generate(config)
            assert len(result) > 0
            assert f"perf-test-{i}" in result
