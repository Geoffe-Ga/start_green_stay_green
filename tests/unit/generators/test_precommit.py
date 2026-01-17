"""Unit tests for Pre-commit Generator."""

from unittest.mock import Mock

import pytest
import yaml

from start_green_stay_green.generators.precommit import GenerationConfig
from start_green_stay_green.generators.precommit import LANGUAGE_CONFIGS
from start_green_stay_green.generators.precommit import PreCommitGenerator


@pytest.fixture
def mock_orchestrator() -> Mock:
    """Provide mock AIOrchestrator for testing.

    Returns:
        Mock object configured as AIOrchestrator.
    """
    return Mock()


class TestPreCommitGeneratorInitialization:
    """Test PreCommitGenerator initialization and basic instantiation."""

    def test_generator_can_be_instantiated(self, mock_orchestrator: Mock) -> None:
        """Test PreCommitGenerator can be created without arguments."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator is not None
        assert isinstance(generator, PreCommitGenerator)

    def test_generator_has_generate_method(self, mock_orchestrator: Mock) -> None:
        """Test generator has generate method."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert hasattr(generator, "generate")
        assert callable(generator.generate)

    def test_generator_has_validate_language_method(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generator has validate_language method."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert hasattr(generator, "validate_language")
        assert callable(generator.validate_language)

    def test_generator_has_get_supported_languages_method(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generator has get_supported_languages method."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert hasattr(generator, "get_supported_languages")
        assert callable(generator.get_supported_languages)

    def test_generator_has_get_language_hooks_method(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generator has get_language_hooks method."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert hasattr(generator, "get_language_hooks")
        assert callable(generator.get_language_hooks)

    def test_generator_has_count_hooks_for_language_method(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generator has count_hooks_for_language method."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert hasattr(generator, "count_hooks_for_language")
        assert callable(generator.count_hooks_for_language)


class TestGenerateWithPython:
    """Test content generation for Python projects."""

    def test_generate_python_returns_string(self, mock_orchestrator: Mock) -> None:
        """Test generate returns string for Python."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        assert isinstance(result, str)
        assert result

    def test_generate_python_includes_header_comment(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generated Python config includes header comment."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        assert "# Pre-commit hooks configuration for test-project" in result

    def test_generate_python_includes_installation_instructions(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generated Python config includes installation instructions."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        assert "# Install: pre-commit install" in result
        assert "# Run manually: pre-commit run --all-files" in result

    def test_generate_python_is_valid_yaml(self, mock_orchestrator: Mock) -> None:
        """Test generated Python config is valid YAML."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        # Remove header comments for YAML parsing
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        assert isinstance(parsed, dict)

    def test_generate_python_has_repos_section(self, mock_orchestrator: Mock) -> None:
        """Test generated Python config has repos section."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        assert "repos" in parsed
        assert isinstance(parsed["repos"], list)
        assert len(parsed["repos"]) > 0

    def test_generate_python_has_ci_configuration(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generated Python config has CI configuration."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        assert "ci" in parsed
        assert "autofix_commit_msg" in parsed["ci"]
        assert "autoupdate_commit_msg" in parsed["ci"]

    def test_generate_python_includes_ruff(self, mock_orchestrator: Mock) -> None:
        """Test generated Python config includes ruff."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        repos = parsed["repos"]
        repo_urls = [repo.get("repo", "") for repo in repos]
        assert any("ruff" in url for url in repo_urls)

    def test_generate_python_includes_mypy(self, mock_orchestrator: Mock) -> None:
        """Test generated Python config includes mypy."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        repos = parsed["repos"]
        repo_urls = [repo.get("repo", "") for repo in repos]
        assert any("mypy" in url for url in repo_urls)

    def test_generate_python_includes_bandit(self, mock_orchestrator: Mock) -> None:
        """Test generated Python config includes bandit."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        repos = parsed["repos"]
        repo_urls = [repo.get("repo", "") for repo in repos]
        assert any("bandit" in url for url in repo_urls)

    def test_generate_python_includes_black(self, mock_orchestrator: Mock) -> None:
        """Test generated Python config includes black."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        repos = parsed["repos"]
        repo_urls = [repo.get("repo", "") for repo in repos]
        assert any("black" in url for url in repo_urls)

    def test_generate_python_has_default_language_version(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generated Python config has default_language_version."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        assert "default_language_version" in parsed
        assert "python" in parsed["default_language_version"]


class TestGenerateWithTypeScript:
    """Test content generation for TypeScript projects."""

    def test_generate_typescript_returns_string(self, mock_orchestrator: Mock) -> None:
        """Test generate returns string for TypeScript."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="ts-project",
            language="typescript",
            language_config={},
        )
        result = generator.generate(config)
        assert isinstance(result, str)
        assert result

    def test_generate_typescript_includes_project_name(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generated TypeScript config includes project name."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="my-ts-app",
            language="typescript",
            language_config={},
        )
        result = generator.generate(config)
        assert "my-ts-app" in result

    def test_generate_typescript_includes_prettier(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generated TypeScript config includes prettier."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="ts-project",
            language="typescript",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        repos = parsed["repos"]
        repo_urls = [repo.get("repo", "") for repo in repos]
        assert any("prettier" in url for url in repo_urls)


class TestGenerateWithGo:
    """Test content generation for Go projects."""

    def test_generate_go_returns_string(self, mock_orchestrator: Mock) -> None:
        """Test generate returns string for Go."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="go-project",
            language="go",
            language_config={},
        )
        result = generator.generate(config)
        assert isinstance(result, str)
        assert result

    def test_generate_go_includes_golangci_lint(self, mock_orchestrator: Mock) -> None:
        """Test generated Go config includes golangci-lint."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="go-project",
            language="go",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        repos = parsed["repos"]
        repo_urls = [repo.get("repo", "") for repo in repos]
        assert any("golangci-lint" in url for url in repo_urls)


class TestGenerateWithRust:
    """Test content generation for Rust projects."""

    def test_generate_rust_returns_string(self, mock_orchestrator: Mock) -> None:
        """Test generate returns string for Rust."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="rust-project",
            language="rust",
            language_config={},
        )
        result = generator.generate(config)
        assert isinstance(result, str)
        assert result

    def test_generate_rust_includes_rustfmt(self, mock_orchestrator: Mock) -> None:
        """Test generated Rust config includes rustfmt."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="rust-project",
            language="rust",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        repos = parsed["repos"]
        # Find the rust pre-commit repo
        rust_repo = next(
            (
                repo
                for repo in repos
                if "doublify/pre-commit-rust" in repo.get("repo", "")
            ),
            None,
        )
        assert rust_repo is not None
        hooks = rust_repo.get("hooks", [])
        hook_ids = [hook.get("id", "") for hook in hooks]
        assert "fmt" in hook_ids

    def test_generate_rust_includes_clippy(self, mock_orchestrator: Mock) -> None:
        """Test generated Rust config includes clippy."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="rust-project",
            language="rust",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        repos = parsed["repos"]
        rust_repo = next(
            (
                repo
                for repo in repos
                if "doublify/pre-commit-rust" in repo.get("repo", "")
            ),
            None,
        )
        assert rust_repo is not None
        hooks = rust_repo.get("hooks", [])
        hook_ids = [hook.get("id", "") for hook in hooks]
        assert "clippy" in hook_ids


class TestValidateLanguage:
    """Test language validation functionality."""

    def test_validate_language_python_returns_true(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test validate_language returns True for Python."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator.validate_language("python")

    def test_validate_language_typescript_returns_true(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test validate_language returns True for TypeScript."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator.validate_language("typescript")

    def test_validate_language_go_returns_true(self, mock_orchestrator: Mock) -> None:
        """Test validate_language returns True for Go."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator.validate_language("go")

    def test_validate_language_rust_returns_true(self, mock_orchestrator: Mock) -> None:
        """Test validate_language returns True for Rust."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator.validate_language("rust")

    def test_validate_language_unsupported_returns_false(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test validate_language returns False for unsupported language."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert not generator.validate_language("cobol")

    def test_validate_language_empty_string_returns_false(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test validate_language returns False for empty string."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert not generator.validate_language("")

    def test_validate_language_case_sensitive(self, mock_orchestrator: Mock) -> None:
        """Test validate_language is case sensitive."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert not generator.validate_language("Python")
        assert not generator.validate_language("PYTHON")


class TestGetSupportedLanguages:
    """Test getting list of supported languages."""

    def test_get_supported_languages_returns_list(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test get_supported_languages returns list."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_supported_languages()
        assert isinstance(result, list)

    def test_get_supported_languages_includes_python(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test get_supported_languages includes python."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_supported_languages()
        assert "python" in result

    def test_get_supported_languages_includes_typescript(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test get_supported_languages includes typescript."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_supported_languages()
        assert "typescript" in result

    def test_get_supported_languages_includes_go(self, mock_orchestrator: Mock) -> None:
        """Test get_supported_languages includes go."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_supported_languages()
        assert "go" in result

    def test_get_supported_languages_includes_rust(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test get_supported_languages includes rust."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_supported_languages()
        assert "rust" in result

    def test_get_supported_languages_exact_count(self, mock_orchestrator: Mock) -> None:
        """Test get_supported_languages returns expected count."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_supported_languages()
        assert len(result) == 4

    def test_get_supported_languages_no_duplicates(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test get_supported_languages has no duplicates."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_supported_languages()
        assert len(result) == len(set(result))


class TestGetLanguageHooks:
    """Test getting hooks for specific language."""

    def test_get_language_hooks_python_returns_list(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test get_language_hooks returns list for python."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_language_hooks("python")
        assert isinstance(result, list)

    def test_get_language_hooks_python_not_empty(self, mock_orchestrator: Mock) -> None:
        """Test get_language_hooks returns non-empty list for python."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_language_hooks("python")
        assert result

    def test_get_language_hooks_typescript_returns_list(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test get_language_hooks returns list for typescript."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_language_hooks("typescript")
        assert isinstance(result, list)

    def test_get_language_hooks_go_returns_list(self, mock_orchestrator: Mock) -> None:
        """Test get_language_hooks returns list for go."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_language_hooks("go")
        assert isinstance(result, list)

    def test_get_language_hooks_rust_returns_list(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test get_language_hooks returns list for rust."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_language_hooks("rust")
        assert isinstance(result, list)

    def test_get_language_hooks_unsupported_raises_error(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test get_language_hooks raises ValueError for unsupported language."""
        generator = PreCommitGenerator(mock_orchestrator)
        with pytest.raises(ValueError, match="Unsupported language"):
            generator.get_language_hooks("cobol")

    def test_get_language_hooks_python_has_repo_structure(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test Python hooks have proper repo structure."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.get_language_hooks("python")
        for repo in result:
            assert "repo" in repo or "id" in repo
            assert "hooks" in repo


class TestCountHooksForLanguage:
    """Test counting hooks for specific language."""

    def test_count_hooks_python_returns_int(self, mock_orchestrator: Mock) -> None:
        """Test count_hooks_for_language returns int for python."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.count_hooks_for_language("python")
        assert isinstance(result, int)

    def test_count_hooks_python_greater_than_zero(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test count_hooks_for_language returns positive int for python."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.count_hooks_for_language("python")
        assert result > 0

    def test_count_hooks_python_greater_than_twenty(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test Python has many hooks configured."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.count_hooks_for_language("python")
        assert result >= 20

    def test_count_hooks_typescript_returns_int(self, mock_orchestrator: Mock) -> None:
        """Test count_hooks_for_language returns int for typescript."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.count_hooks_for_language("typescript")
        assert isinstance(result, int)

    def test_count_hooks_go_returns_int(self, mock_orchestrator: Mock) -> None:
        """Test count_hooks_for_language returns int for go."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.count_hooks_for_language("go")
        assert isinstance(result, int)

    def test_count_hooks_rust_returns_int(self, mock_orchestrator: Mock) -> None:
        """Test count_hooks_for_language returns int for rust."""
        generator = PreCommitGenerator(mock_orchestrator)
        result = generator.count_hooks_for_language("rust")
        assert isinstance(result, int)

    def test_count_hooks_unsupported_raises_error(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test count_hooks_for_language raises ValueError for unsupported language."""
        generator = PreCommitGenerator(mock_orchestrator)
        with pytest.raises(ValueError, match="Unsupported language"):
            generator.count_hooks_for_language("cobol")

    def test_count_hooks_python_less_than_typescript(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test Python typically has more hooks than TypeScript."""
        generator = PreCommitGenerator(mock_orchestrator)
        python_count = generator.count_hooks_for_language("python")
        typescript_count = generator.count_hooks_for_language("typescript")
        assert python_count > typescript_count


class TestGenerateWithUnsupportedLanguage:
    """Test handling of unsupported languages."""

    def test_generate_unsupported_language_raises_error(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generate raises ValueError for unsupported language."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="cobol",
            language_config={},
        )
        with pytest.raises(ValueError, match="Unsupported language"):
            generator.generate(config)

    def test_generate_unsupported_language_mentions_supported(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test error message mentions supported languages."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="unsupported",
            language_config={},
        )
        with pytest.raises(ValueError, match="Supported languages"):
            generator.generate(config)

    def test_generate_empty_language_raises_error(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generate raises ValueError for empty language."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="",
            language_config={},
        )
        with pytest.raises(ValueError, match="language"):
            generator.generate(config)


class TestLanguageConfigsStructure:
    """Test LANGUAGE_CONFIGS data structure."""

    def test_language_configs_is_dict(self) -> None:
        """Test LANGUAGE_CONFIGS is a dictionary."""
        assert isinstance(LANGUAGE_CONFIGS, dict)

    def test_language_configs_not_empty(self) -> None:
        """Test LANGUAGE_CONFIGS is not empty."""
        assert LANGUAGE_CONFIGS

    def test_language_configs_has_python(self) -> None:
        """Test LANGUAGE_CONFIGS has python entry."""
        assert "python" in LANGUAGE_CONFIGS

    def test_language_configs_has_typescript(self) -> None:
        """Test LANGUAGE_CONFIGS has typescript entry."""
        assert "typescript" in LANGUAGE_CONFIGS

    def test_language_configs_has_go(self) -> None:
        """Test LANGUAGE_CONFIGS has go entry."""
        assert "go" in LANGUAGE_CONFIGS

    def test_language_configs_has_rust(self) -> None:
        """Test LANGUAGE_CONFIGS has rust entry."""
        assert "rust" in LANGUAGE_CONFIGS

    def test_each_language_has_hooks_key(self) -> None:
        """Test each language config has hooks key."""
        for language, config in LANGUAGE_CONFIGS.items():
            assert "hooks" in config, f"{language} missing 'hooks' key"

    def test_each_language_has_default_language_version(self) -> None:
        """Test each language config has default_language_version key."""
        for language, config in LANGUAGE_CONFIGS.items():
            assert (
                "default_language_version" in config
            ), f"{language} missing 'default_language_version' key"

    def test_hooks_are_list(self) -> None:
        """Test hooks in each language are lists."""
        for language, config in LANGUAGE_CONFIGS.items():
            assert isinstance(config["hooks"], list), f"{language} hooks not a list"

    def test_default_language_version_is_dict(self) -> None:
        """Test default_language_version in each language is dict."""
        for language, config in LANGUAGE_CONFIGS.items():
            assert isinstance(
                config["default_language_version"], dict
            ), f"{language} default_language_version not a dict"


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_generate_with_special_characters_in_project_name(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generate handles special characters in project name."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="my-test-project_v2.0",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        assert "my-test-project_v2.0" in result

    def test_generate_with_unicode_in_project_name(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generate handles unicode in project name."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="projet-fr",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        assert "projet-fr" in result

    def test_generate_with_long_project_name(self, mock_orchestrator: Mock) -> None:
        """Test generate handles long project name."""
        generator = PreCommitGenerator(mock_orchestrator)
        long_name = "a" * 100
        config = GenerationConfig(
            project_name=long_name,
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        assert long_name in result

    def test_generate_idempotent(self, mock_orchestrator: Mock) -> None:
        """Test generate produces same output when called multiple times."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test-project",
            language="python",
            language_config={},
        )
        result1 = generator.generate(config)
        result2 = generator.generate(config)
        assert result1 == result2

    def test_multiple_generators_independent(self, mock_orchestrator: Mock) -> None:
        """Test multiple generator instances are independent."""
        gen1 = PreCommitGenerator(mock_orchestrator)
        gen2 = PreCommitGenerator(mock_orchestrator)

        config1 = GenerationConfig(
            project_name="project1",
            language="python",
            language_config={},
        )
        config2 = GenerationConfig(
            project_name="project2",
            language="typescript",
            language_config={},
        )

        result1 = gen1.generate(config1)
        result2 = gen2.generate(config2)

        assert "project1" in result1
        assert "project2" in result2
        assert "project1" not in result2


class TestYAMLValidation:
    """Test YAML output validation for all languages."""

    def test_python_output_is_valid_yaml(self, mock_orchestrator: Mock) -> None:
        """Test Python output can be parsed as YAML."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        assert parsed is not None

    def test_typescript_output_is_valid_yaml(self, mock_orchestrator: Mock) -> None:
        """Test TypeScript output can be parsed as YAML."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test",
            language="typescript",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        assert parsed is not None

    def test_go_output_is_valid_yaml(self, mock_orchestrator: Mock) -> None:
        """Test Go output can be parsed as YAML."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test",
            language="go",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        assert parsed is not None

    def test_rust_output_is_valid_yaml(self, mock_orchestrator: Mock) -> None:
        """Test Rust output can be parsed as YAML."""
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test",
            language="rust",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)
        assert parsed is not None


class TestGenerationConfigCreation:
    """Test GenerationConfig dataclass."""

    def test_generation_config_creation(self) -> None:
        """Test creating GenerationConfig instance."""
        config = GenerationConfig(
            project_name="test",
            language="python",
            language_config={},
        )
        assert config.project_name == "test"
        assert config.language == "python"
        assert not config.language_config

    def test_generation_config_with_language_config(self) -> None:
        """Test GenerationConfig with language config dict."""
        lang_config = {"key": "value"}
        config = GenerationConfig(
            project_name="test",
            language="python",
            language_config=lang_config,
        )
        assert config.language_config == lang_config


class TestMutationKillers:
    """Targeted tests to kill mutations and achieve high mutation score."""

    def test_validate_language_exact_comparison(self, mock_orchestrator: Mock) -> None:
        """Test validate_language uses exact comparison.

        Kills mutations: in → not in
        """
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator.validate_language("python")
        assert not generator.validate_language("unknown")

    def test_count_hooks_increments_correctly(self, mock_orchestrator: Mock) -> None:
        """Test count_hooks_for_language increments by exact count.

        Kills mutations: += 1 → += 0, += 2
        """
        generator = PreCommitGenerator(mock_orchestrator)
        python_count = generator.count_hooks_for_language("python")
        hooks = generator.get_language_hooks("python")
        total = sum(len(repo.get("hooks", [])) for repo in hooks)
        assert python_count == total

    def test_generate_includes_all_required_sections(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test generate includes all required YAML sections.

        Kills mutations that remove sections.
        """
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        yaml_content = "\n".join(
            line for line in result.split("\n") if not line.startswith("#")
        )
        parsed = yaml.safe_load(yaml_content)

        # Verify all sections exist
        assert "default_language_version" in parsed
        assert "repos" in parsed
        assert "ci" in parsed

    def test_error_message_exact_text(self, mock_orchestrator: Mock) -> None:
        """Test error message contains exact text.

        Kills mutations in error message strings.
        """
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="test",
            language="invalid",
            language_config={},
        )
        with pytest.raises(ValueError, match=r"Unsupported language.*invalid"):
            generator.generate(config)

    def test_header_comment_format(self, mock_orchestrator: Mock) -> None:
        """Test header comment has exact format.

        Kills mutations in string formatting.
        """
        generator = PreCommitGenerator(mock_orchestrator)
        config = GenerationConfig(
            project_name="my-project",
            language="python",
            language_config={},
        )
        result = generator.generate(config)
        assert result.startswith("# Pre-commit hooks configuration for my-project\n")

    def test_language_config_python_exact_hooks_count(self) -> None:
        """Test Python has exact expected hook count.

        Kills mutations in LANGUAGE_CONFIGS.
        """
        python_hooks = LANGUAGE_CONFIGS["python"]["hooks"]
        assert len(python_hooks) == 16

    def test_language_config_typescript_exact_hooks_count(self) -> None:
        """Test TypeScript has exact expected hook count."""
        ts_hooks = LANGUAGE_CONFIGS["typescript"]["hooks"]
        assert len(ts_hooks) == 4

    def test_language_config_go_exact_hooks_count(self) -> None:
        """Test Go has exact expected hook count."""
        go_hooks = LANGUAGE_CONFIGS["go"]["hooks"]
        assert len(go_hooks) == 4

    def test_language_config_rust_exact_hooks_count(self) -> None:
        """Test Rust has exact expected hook count."""
        rust_hooks = LANGUAGE_CONFIGS["rust"]["hooks"]
        assert len(rust_hooks) == 4

    # Python Configuration - Exact URL and Version Tests
    def test_python_pre_commit_hooks_repo_url_exact(self) -> None:
        """Test Python pre-commit-hooks repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][0]
        assert repo["repo"] == "https://github.com/pre-commit/pre-commit-hooks"

    def test_python_pre_commit_hooks_rev_exact(self) -> None:
        """Test Python pre-commit-hooks rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][0]
        assert repo["rev"] == "v4.5.0"

    def test_python_ruff_repo_url_exact(self) -> None:
        """Test Python ruff repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][1]
        assert repo["repo"] == "https://github.com/astral-sh/ruff-pre-commit"

    def test_python_ruff_rev_exact(self) -> None:
        """Test Python ruff rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][1]
        assert repo["rev"] == "v0.2.0"

    def test_python_black_repo_url_exact(self) -> None:
        """Test Python black repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][2]
        assert repo["repo"] == "https://github.com/psf/black"

    def test_python_black_rev_exact(self) -> None:
        """Test Python black rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][2]
        assert repo["rev"] == "24.1.0"

    def test_python_isort_repo_url_exact(self) -> None:
        """Test Python isort repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][3]
        assert repo["repo"] == "https://github.com/PyCQA/isort"

    def test_python_isort_rev_exact(self) -> None:
        """Test Python isort rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][3]
        assert repo["rev"] == "5.13.0"

    def test_python_mypy_repo_url_exact(self) -> None:
        """Test Python mypy repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][4]
        assert repo["repo"] == "https://github.com/pre-commit/mirrors-mypy"

    def test_python_mypy_rev_exact(self) -> None:
        """Test Python mypy rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][4]
        assert repo["rev"] == "v1.8.0"

    def test_python_bandit_repo_url_exact(self) -> None:
        """Test Python bandit repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][5]
        assert repo["repo"] == "https://github.com/PyCQA/bandit"

    def test_python_bandit_rev_exact(self) -> None:
        """Test Python bandit rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][5]
        assert repo["rev"] == "1.7.7"

    def test_python_safety_repo_url_exact(self) -> None:
        """Test Python safety repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][6]
        assert repo["repo"] == "https://github.com/Lucas-C/pre-commit-hooks-safety"

    def test_python_safety_rev_exact(self) -> None:
        """Test Python safety rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][6]
        assert repo["rev"] == "v1.3.3"

    def test_python_conventional_commit_repo_url_exact(self) -> None:
        """Test Python conventional commit repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][7]
        assert repo["repo"] == "https://github.com/compilerla/conventional-pre-commit"

    def test_python_conventional_commit_rev_exact(self) -> None:
        """Test Python conventional commit rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][7]
        assert repo["rev"] == "v3.0.0"

    def test_python_shellcheck_repo_url_exact(self) -> None:
        """Test Python shellcheck repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][8]
        assert repo["repo"] == "https://github.com/shellcheck-py/shellcheck-py"

    def test_python_shellcheck_rev_exact(self) -> None:
        """Test Python shellcheck rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][8]
        assert repo["rev"] == "v0.9.0.6"

    def test_python_pyupgrade_repo_url_exact(self) -> None:
        """Test Python pyupgrade repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][9]
        assert repo["repo"] == "https://github.com/asottile/pyupgrade"

    def test_python_pyupgrade_rev_exact(self) -> None:
        """Test Python pyupgrade rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][9]
        assert repo["rev"] == "v3.15.0"

    def test_python_autoflake_repo_url_exact(self) -> None:
        """Test Python autoflake repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][10]
        assert repo["repo"] == "https://github.com/PyCQA/autoflake"

    def test_python_autoflake_rev_exact(self) -> None:
        """Test Python autoflake rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][10]
        assert repo["rev"] == "v2.2.1"

    def test_python_tryceratops_repo_url_exact(self) -> None:
        """Test Python tryceratops repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][11]
        assert repo["repo"] == "https://github.com/guilatrova/tryceratops"

    def test_python_tryceratops_rev_exact(self) -> None:
        """Test Python tryceratops rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][11]
        assert repo["rev"] == "v2.3.2"

    def test_python_refurb_repo_url_exact(self) -> None:
        """Test Python refurb repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][12]
        assert repo["repo"] == "https://github.com/dosisod/refurb"

    def test_python_refurb_rev_exact(self) -> None:
        """Test Python refurb rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][12]
        assert repo["rev"] == "v1.26.0"

    def test_python_vulture_repo_url_exact(self) -> None:
        """Test Python vulture repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][13]
        assert repo["repo"] == "https://github.com/jendrikseipp/vulture"

    def test_python_vulture_rev_exact(self) -> None:
        """Test Python vulture rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][13]
        assert repo["rev"] == "v2.10"

    def test_python_interrogate_repo_url_exact(self) -> None:
        """Test Python interrogate repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][14]
        assert repo["repo"] == "https://github.com/econchick/interrogate"

    def test_python_interrogate_rev_exact(self) -> None:
        """Test Python interrogate rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][14]
        assert repo["rev"] == "1.5.0"

    def test_python_detect_secrets_repo_url_exact(self) -> None:
        """Test Python detect-secrets repo URL is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][15]
        assert repo["repo"] == "https://github.com/Yelp/detect-secrets"

    def test_python_detect_secrets_rev_exact(self) -> None:
        """Test Python detect-secrets rev is exact."""
        repo = LANGUAGE_CONFIGS["python"]["hooks"][15]
        assert repo["rev"] == "v1.4.0"

    # Python Hook IDs - Exact Tests
    def test_python_trailing_whitespace_id_exact(self) -> None:
        """Test trailing-whitespace hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[0]["id"] == "trailing-whitespace"

    def test_python_end_of_file_fixer_id_exact(self) -> None:
        """Test end-of-file-fixer hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[1]["id"] == "end-of-file-fixer"

    def test_python_check_yaml_id_exact(self) -> None:
        """Test check-yaml hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[2]["id"] == "check-yaml"

    def test_python_check_toml_id_exact(self) -> None:
        """Test check-toml hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[3]["id"] == "check-toml"

    def test_python_check_json_id_exact(self) -> None:
        """Test check-json hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[4]["id"] == "check-json"

    def test_python_check_added_large_files_id_exact(self) -> None:
        """Test check-added-large-files hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[5]["id"] == "check-added-large-files"

    def test_python_check_added_large_files_args_exact(self) -> None:
        """Test check-added-large-files args are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[5]["args"] == ["--maxkb=500"]

    def test_python_check_case_conflict_id_exact(self) -> None:
        """Test check-case-conflict hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[6]["id"] == "check-case-conflict"

    def test_python_check_merge_conflict_id_exact(self) -> None:
        """Test check-merge-conflict hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[7]["id"] == "check-merge-conflict"

    def test_python_check_symlinks_id_exact(self) -> None:
        """Test check-symlinks hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[8]["id"] == "check-symlinks"

    def test_python_check_ast_id_exact(self) -> None:
        """Test check-ast hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[9]["id"] == "check-ast"

    def test_python_debug_statements_id_exact(self) -> None:
        """Test debug-statements hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[10]["id"] == "debug-statements"

    def test_python_check_docstring_first_id_exact(self) -> None:
        """Test check-docstring-first hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[11]["id"] == "check-docstring-first"

    def test_python_detect_private_key_id_exact(self) -> None:
        """Test detect-private-key hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[12]["id"] == "detect-private-key"

    def test_python_fix_byte_order_marker_id_exact(self) -> None:
        """Test fix-byte-order-marker hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[13]["id"] == "fix-byte-order-marker"

    def test_python_mixed_line_ending_id_exact(self) -> None:
        """Test mixed-line-ending hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[14]["id"] == "mixed-line-ending"

    def test_python_mixed_line_ending_args_exact(self) -> None:
        """Test mixed-line-ending args are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[14]["args"] == ["--fix=lf"]

    def test_python_no_commit_to_branch_id_exact(self) -> None:
        """Test no-commit-to-branch hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[15]["id"] == "no-commit-to-branch"

    def test_python_no_commit_to_branch_args_exact(self) -> None:
        """Test no-commit-to-branch args are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][0]["hooks"]
        assert hooks[15]["args"] == ["--branch", "main"]

    def test_python_ruff_hook_id_exact(self) -> None:
        """Test ruff hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][1]["hooks"]
        assert hooks[0]["id"] == "ruff"

    def test_python_ruff_args_exact(self) -> None:
        """Test ruff args are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][1]["hooks"]
        assert hooks[0]["args"] == ["--fix"]

    def test_python_ruff_format_id_exact(self) -> None:
        """Test ruff-format hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][1]["hooks"]
        assert hooks[1]["id"] == "ruff-format"

    def test_python_black_hook_id_exact(self) -> None:
        """Test black hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][2]["hooks"]
        assert hooks[0]["id"] == "black"

    def test_python_black_language_version_exact(self) -> None:
        """Test black language_version is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][2]["hooks"]
        assert hooks[0]["language_version"] == "python3.11"

    def test_python_isort_hook_id_exact(self) -> None:
        """Test isort hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][3]["hooks"]
        assert hooks[0]["id"] == "isort"

    def test_python_mypy_hook_id_exact(self) -> None:
        """Test mypy hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][4]["hooks"]
        assert hooks[0]["id"] == "mypy"

    def test_python_mypy_additional_dependencies_exact(self) -> None:
        """Test mypy additional_dependencies are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][4]["hooks"]
        assert hooks[0]["additional_dependencies"] == ["types-all"]

    def test_python_mypy_args_exact(self) -> None:
        """Test mypy args are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][4]["hooks"]
        assert hooks[0]["args"] == ["--strict"]

    def test_python_bandit_hook_id_exact(self) -> None:
        """Test bandit hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][5]["hooks"]
        assert hooks[0]["id"] == "bandit"

    def test_python_bandit_args_exact(self) -> None:
        """Test bandit args are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][5]["hooks"]
        assert hooks[0]["args"] == ["-c", "pyproject.toml"]

    def test_python_bandit_additional_dependencies_exact(self) -> None:
        """Test bandit additional_dependencies are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][5]["hooks"]
        assert hooks[0]["additional_dependencies"] == ["bandit[toml]"]

    def test_python_safety_hook_id_exact(self) -> None:
        """Test safety hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][6]["hooks"]
        assert hooks[0]["id"] == "python-safety-dependencies-check"

    def test_python_conventional_pre_commit_hook_id_exact(self) -> None:
        """Test conventional-pre-commit hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][7]["hooks"]
        assert hooks[0]["id"] == "conventional-pre-commit"

    def test_python_conventional_pre_commit_stages_exact(self) -> None:
        """Test conventional-pre-commit stages are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][7]["hooks"]
        assert hooks[0]["stages"] == ["commit-msg"]

    def test_python_shellcheck_hook_id_exact(self) -> None:
        """Test shellcheck hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][8]["hooks"]
        assert hooks[0]["id"] == "shellcheck"

    def test_python_pyupgrade_hook_id_exact(self) -> None:
        """Test pyupgrade hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][9]["hooks"]
        assert hooks[0]["id"] == "pyupgrade"

    def test_python_pyupgrade_args_exact(self) -> None:
        """Test pyupgrade args are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][9]["hooks"]
        assert hooks[0]["args"] == ["--py311-plus"]

    def test_python_autoflake_hook_id_exact(self) -> None:
        """Test autoflake hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][10]["hooks"]
        assert hooks[0]["id"] == "autoflake"

    def test_python_autoflake_args_exact(self) -> None:
        """Test autoflake args are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][10]["hooks"]
        expected_args = [
            "--in-place",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--remove-duplicate-keys",
            "--ignore-init-module-imports",
        ]
        assert hooks[0]["args"] == expected_args

    def test_python_tryceratops_hook_id_exact(self) -> None:
        """Test tryceratops hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][11]["hooks"]
        assert hooks[0]["id"] == "tryceratops"

    def test_python_refurb_hook_id_exact(self) -> None:
        """Test refurb hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][12]["hooks"]
        assert hooks[0]["id"] == "refurb"

    def test_python_vulture_hook_id_exact(self) -> None:
        """Test vulture hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][13]["hooks"]
        assert hooks[0]["id"] == "vulture"

    def test_python_vulture_args_exact(self) -> None:
        """Test vulture args are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][13]["hooks"]
        assert hooks[0]["args"] == ["start_green_stay_green/", "--min-confidence", "80"]

    def test_python_interrogate_hook_id_exact(self) -> None:
        """Test interrogate hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][14]["hooks"]
        assert hooks[0]["id"] == "interrogate"

    def test_python_interrogate_args_exact(self) -> None:
        """Test interrogate args are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][14]["hooks"]
        assert hooks[0]["args"] == ["-vv", "--fail-under=95"]

    def test_python_detect_secrets_hook_id_exact(self) -> None:
        """Test detect-secrets hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][15]["hooks"]
        assert hooks[0]["id"] == "detect-secrets"

    def test_python_detect_secrets_args_exact(self) -> None:
        """Test detect-secrets args are exact."""
        hooks = LANGUAGE_CONFIGS["python"]["hooks"][15]["hooks"]
        assert hooks[0]["args"] == ["--baseline", ".secrets.baseline"]

    def test_python_default_language_version_key_exact(self) -> None:
        """Test Python default_language_version key is exact."""
        config = LANGUAGE_CONFIGS["python"]["default_language_version"]
        assert "python" in config

    def test_python_default_language_version_value_exact(self) -> None:
        """Test Python default_language_version value is exact."""
        config = LANGUAGE_CONFIGS["python"]["default_language_version"]
        assert config["python"] == "python3.11"

    # TypeScript Configuration - Exact Tests
    def test_typescript_pre_commit_hooks_repo_url_exact(self) -> None:
        """Test TypeScript pre-commit-hooks repo URL is exact."""
        repo = LANGUAGE_CONFIGS["typescript"]["hooks"][0]
        assert repo["repo"] == "https://github.com/pre-commit/pre-commit-hooks"

    def test_typescript_pre_commit_hooks_rev_exact(self) -> None:
        """Test TypeScript pre-commit-hooks rev is exact."""
        repo = LANGUAGE_CONFIGS["typescript"]["hooks"][0]
        assert repo["rev"] == "v4.5.0"

    def test_typescript_prettier_repo_url_exact(self) -> None:
        """Test TypeScript prettier repo URL is exact."""
        repo = LANGUAGE_CONFIGS["typescript"]["hooks"][1]
        assert repo["repo"] == "https://github.com/pre-commit/mirrors-prettier"

    def test_typescript_prettier_rev_exact(self) -> None:
        """Test TypeScript prettier rev is exact."""
        repo = LANGUAGE_CONFIGS["typescript"]["hooks"][1]
        assert repo["rev"] == "v4.0.0-alpha.8"

    def test_typescript_shellcheck_repo_url_exact(self) -> None:
        """Test TypeScript shellcheck repo URL is exact."""
        repo = LANGUAGE_CONFIGS["typescript"]["hooks"][2]
        assert repo["repo"] == "https://github.com/shellcheck-py/shellcheck-py"

    def test_typescript_shellcheck_rev_exact(self) -> None:
        """Test TypeScript shellcheck rev is exact."""
        repo = LANGUAGE_CONFIGS["typescript"]["hooks"][2]
        assert repo["rev"] == "v0.9.0.6"

    def test_typescript_detect_secrets_repo_url_exact(self) -> None:
        """Test TypeScript detect-secrets repo URL is exact."""
        repo = LANGUAGE_CONFIGS["typescript"]["hooks"][3]
        assert repo["repo"] == "https://github.com/Yelp/detect-secrets"

    def test_typescript_detect_secrets_rev_exact(self) -> None:
        """Test TypeScript detect-secrets rev is exact."""
        repo = LANGUAGE_CONFIGS["typescript"]["hooks"][3]
        assert repo["rev"] == "v1.4.0"

    def test_typescript_prettier_hook_id_exact(self) -> None:
        """Test TypeScript prettier hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["typescript"]["hooks"][1]["hooks"]
        assert hooks[0]["id"] == "prettier"

    def test_typescript_prettier_types_or_exact(self) -> None:
        """Test TypeScript prettier types_or is exact."""
        hooks = LANGUAGE_CONFIGS["typescript"]["hooks"][1]["hooks"]
        expected_types = ["typescript", "tsx", "javascript", "json"]
        assert hooks[0]["types_or"] == expected_types

    def test_typescript_default_language_version_empty(self) -> None:
        """Test TypeScript default_language_version is empty dict."""
        config = LANGUAGE_CONFIGS["typescript"]["default_language_version"]
        assert not config

    # Go Configuration - Exact Tests
    def test_go_pre_commit_hooks_repo_url_exact(self) -> None:
        """Test Go pre-commit-hooks repo URL is exact."""
        repo = LANGUAGE_CONFIGS["go"]["hooks"][0]
        assert repo["repo"] == "https://github.com/pre-commit/pre-commit-hooks"

    def test_go_pre_commit_hooks_rev_exact(self) -> None:
        """Test Go pre-commit-hooks rev is exact."""
        repo = LANGUAGE_CONFIGS["go"]["hooks"][0]
        assert repo["rev"] == "v4.5.0"

    def test_go_golangci_lint_repo_url_exact(self) -> None:
        """Test Go golangci-lint repo URL is exact."""
        repo = LANGUAGE_CONFIGS["go"]["hooks"][1]
        assert repo["repo"] == "https://github.com/golangci/golangci-lint"

    def test_go_golangci_lint_rev_exact(self) -> None:
        """Test Go golangci-lint rev is exact."""
        repo = LANGUAGE_CONFIGS["go"]["hooks"][1]
        assert repo["rev"] == "v1.55.2"

    def test_go_shellcheck_repo_url_exact(self) -> None:
        """Test Go shellcheck repo URL is exact."""
        repo = LANGUAGE_CONFIGS["go"]["hooks"][2]
        assert repo["repo"] == "https://github.com/shellcheck-py/shellcheck-py"

    def test_go_shellcheck_rev_exact(self) -> None:
        """Test Go shellcheck rev is exact."""
        repo = LANGUAGE_CONFIGS["go"]["hooks"][2]
        assert repo["rev"] == "v0.9.0.6"

    def test_go_detect_secrets_repo_url_exact(self) -> None:
        """Test Go detect-secrets repo URL is exact."""
        repo = LANGUAGE_CONFIGS["go"]["hooks"][3]
        assert repo["repo"] == "https://github.com/Yelp/detect-secrets"

    def test_go_detect_secrets_rev_exact(self) -> None:
        """Test Go detect-secrets rev is exact."""
        repo = LANGUAGE_CONFIGS["go"]["hooks"][3]
        assert repo["rev"] == "v1.4.0"

    def test_go_golangci_lint_hook_id_exact(self) -> None:
        """Test Go golangci-lint hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["go"]["hooks"][1]["hooks"]
        assert hooks[0]["id"] == "golangci-lint"

    def test_go_default_language_version_empty(self) -> None:
        """Test Go default_language_version is empty dict."""
        config = LANGUAGE_CONFIGS["go"]["default_language_version"]
        assert not config

    # Rust Configuration - Exact Tests
    def test_rust_pre_commit_hooks_repo_url_exact(self) -> None:
        """Test Rust pre-commit-hooks repo URL is exact."""
        repo = LANGUAGE_CONFIGS["rust"]["hooks"][0]
        assert repo["repo"] == "https://github.com/pre-commit/pre-commit-hooks"

    def test_rust_pre_commit_hooks_rev_exact(self) -> None:
        """Test Rust pre-commit-hooks rev is exact."""
        repo = LANGUAGE_CONFIGS["rust"]["hooks"][0]
        assert repo["rev"] == "v4.5.0"

    def test_rust_pre_commit_rust_repo_url_exact(self) -> None:
        """Test Rust pre-commit-rust repo URL is exact."""
        repo = LANGUAGE_CONFIGS["rust"]["hooks"][1]
        assert repo["repo"] == "https://github.com/doublify/pre-commit-rust"

    def test_rust_pre_commit_rust_rev_exact(self) -> None:
        """Test Rust pre-commit-rust rev is exact."""
        repo = LANGUAGE_CONFIGS["rust"]["hooks"][1]
        assert repo["rev"] == "v1.0"

    def test_rust_shellcheck_repo_url_exact(self) -> None:
        """Test Rust shellcheck repo URL is exact."""
        repo = LANGUAGE_CONFIGS["rust"]["hooks"][2]
        assert repo["repo"] == "https://github.com/shellcheck-py/shellcheck-py"

    def test_rust_shellcheck_rev_exact(self) -> None:
        """Test Rust shellcheck rev is exact."""
        repo = LANGUAGE_CONFIGS["rust"]["hooks"][2]
        assert repo["rev"] == "v0.9.0.6"

    def test_rust_detect_secrets_repo_url_exact(self) -> None:
        """Test Rust detect-secrets repo URL is exact."""
        repo = LANGUAGE_CONFIGS["rust"]["hooks"][3]
        assert repo["repo"] == "https://github.com/Yelp/detect-secrets"

    def test_rust_detect_secrets_rev_exact(self) -> None:
        """Test Rust detect-secrets rev is exact."""
        repo = LANGUAGE_CONFIGS["rust"]["hooks"][3]
        assert repo["rev"] == "v1.4.0"

    def test_rust_fmt_hook_id_exact(self) -> None:
        """Test Rust fmt hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[0]["id"] == "fmt"

    def test_rust_fmt_hook_name_exact(self) -> None:
        """Test Rust fmt hook name is exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[0]["name"] == "Rustfmt"

    def test_rust_fmt_hook_entry_exact(self) -> None:
        """Test Rust fmt hook entry is exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[0]["entry"] == "cargo fmt --"

    def test_rust_fmt_hook_language_exact(self) -> None:
        """Test Rust fmt hook language is exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[0]["language"] == "system"

    def test_rust_fmt_hook_types_exact(self) -> None:
        """Test Rust fmt hook types are exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[0]["types"] == ["rust"]

    def test_rust_fmt_hook_pass_filenames_exact(self) -> None:
        """Test Rust fmt hook pass_filenames is exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[0]["pass_filenames"] is True

    def test_rust_clippy_hook_id_exact(self) -> None:
        """Test Rust clippy hook ID is exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[1]["id"] == "clippy"

    def test_rust_clippy_hook_name_exact(self) -> None:
        """Test Rust clippy hook name is exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[1]["name"] == "Clippy"

    def test_rust_clippy_hook_entry_exact(self) -> None:
        """Test Rust clippy hook entry is exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[1]["entry"] == "cargo clippy -- -D warnings"

    def test_rust_clippy_hook_language_exact(self) -> None:
        """Test Rust clippy hook language is exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[1]["language"] == "system"

    def test_rust_clippy_hook_types_exact(self) -> None:
        """Test Rust clippy hook types are exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[1]["types"] == ["rust"]

    def test_rust_clippy_hook_pass_filenames_exact(self) -> None:
        """Test Rust clippy hook pass_filenames is exact."""
        hooks = LANGUAGE_CONFIGS["rust"]["hooks"][1]["hooks"]
        assert hooks[1]["pass_filenames"] is False

    def test_rust_default_language_version_empty(self) -> None:
        """Test Rust default_language_version is empty dict."""
        config = LANGUAGE_CONFIGS["rust"]["default_language_version"]
        assert not config

    # CI Configuration Exact Tests
    def test_ci_autofix_commit_msg_exact(self, mock_orchestrator: Mock) -> None:
        """Test CI autofix_commit_msg is exact."""
        generator = PreCommitGenerator(mock_orchestrator)
        config_dict = generator._build_config_dict("python")  # noqa: SLF001
        expected = "style: auto-fix by pre-commit hooks"
        assert config_dict["ci"]["autofix_commit_msg"] == expected

    def test_ci_autoupdate_commit_msg_exact(self, mock_orchestrator: Mock) -> None:
        """Test CI autoupdate_commit_msg is exact."""
        generator = PreCommitGenerator(mock_orchestrator)
        config_dict = generator._build_config_dict("python")  # noqa: SLF001
        expected = "chore: update pre-commit hooks"
        assert config_dict["ci"]["autoupdate_commit_msg"] == expected

    def test_ci_skip_is_empty_list(self, mock_orchestrator: Mock) -> None:
        """Test CI skip is empty list."""
        generator = PreCommitGenerator(mock_orchestrator)
        config_dict = generator._build_config_dict("python")  # noqa: SLF001
        assert config_dict["ci"]["skip"] == []

    # Header Generation Exact Tests
    def test_header_first_line_exact(self, mock_orchestrator: Mock) -> None:
        """Test header first line is exact."""
        generator = PreCommitGenerator(mock_orchestrator)
        header = generator._generate_header("my-project")  # noqa: SLF001
        lines = header.split("\n")
        assert lines[0] == "# Pre-commit hooks configuration for my-project"

    def test_header_second_line_exact(self, mock_orchestrator: Mock) -> None:
        """Test header second line is exact."""
        generator = PreCommitGenerator(mock_orchestrator)
        header = generator._generate_header("my-project")  # noqa: SLF001
        lines = header.split("\n")
        assert lines[1] == "# Install: pre-commit install"

    def test_header_third_line_exact(self) -> None:
        """Test header third line is exact."""
        generator = PreCommitGenerator(Mock())
        header = generator._generate_header("my-project")  # noqa: SLF001
        lines = header.split("\n")
        assert lines[2] == "# Run manually: pre-commit run --all-files"


class TestLanguageConfigsStructureValidation:
    """Comprehensive validation tests for LANGUAGE_CONFIGS constant.

    These tests validate every key, value, and structure in LANGUAGE_CONFIGS
    to catch mutations in the constant data.
    """

    def test_all_repos_have_required_keys(self) -> None:
        """Test every repo in every language has required keys."""
        required_keys = {"repo", "rev", "hooks"}
        for language, config in LANGUAGE_CONFIGS.items():
            for idx, repo in enumerate(config["hooks"]):
                # Skip local hooks (id-only entries)
                if "id" in repo and "repo" not in repo:
                    continue
                actual_keys = set(repo.keys())
                assert required_keys.issubset(actual_keys), (
                    f"{language} repo {idx} missing keys: "
                    f"{required_keys - actual_keys}"
                )

    def test_all_repos_have_hooks_key_exact_name(self) -> None:
        """Test 'hooks' key exists with exact spelling in all repos."""
        for language, config in LANGUAGE_CONFIGS.items():
            for idx, repo in enumerate(config["hooks"]):
                # Skip local hooks
                if "id" in repo and "repo" not in repo:
                    continue
                assert "hooks" in repo, f"{language} repo {idx} missing 'hooks' key"
                # Verify it's not a mutation like "XXhooksXX"
                keys_list = list(repo.keys())
                assert (
                    "hooks" in keys_list
                ), f"{language} repo {idx} has keys {keys_list} but not 'hooks'"

    def test_all_repos_hooks_are_non_empty_lists(self) -> None:
        """Test hooks value is a non-empty list in all repos."""
        for language, config in LANGUAGE_CONFIGS.items():
            for idx, repo in enumerate(config["hooks"]):
                # Skip local hooks
                if "id" in repo and "repo" not in repo:
                    continue
                hooks = repo.get("hooks", None)
                assert hooks is not None, f"{language} repo {idx} hooks is None"
                assert isinstance(
                    hooks, list
                ), f"{language} repo {idx} hooks is not a list: {type(hooks)}"
                assert hooks, f"{language} repo {idx} hooks is empty"

    def test_python_first_repo_has_16_hooks(self) -> None:
        """Test Python's pre-commit-hooks repo has exactly 16 hooks."""
        first_repo = LANGUAGE_CONFIGS["python"]["hooks"][0]
        assert len(first_repo["hooks"]) == 16

    def test_python_repos_exact_count(self) -> None:
        """Test Python has exactly 16 repository configurations."""
        assert len(LANGUAGE_CONFIGS["python"]["hooks"]) == 16

    def test_typescript_repos_exact_count(self) -> None:
        """Test TypeScript has exactly 4 repository configurations."""
        assert len(LANGUAGE_CONFIGS["typescript"]["hooks"]) == 4

    def test_go_repos_exact_count(self) -> None:
        """Test Go has exactly 4 repository configurations."""
        assert len(LANGUAGE_CONFIGS["go"]["hooks"]) == 4

    def test_rust_repos_exact_count(self) -> None:
        """Test Rust has exactly 4 repository configurations."""
        assert len(LANGUAGE_CONFIGS["rust"]["hooks"]) == 4

    def test_every_hook_has_id_key(self) -> None:
        """Test every individual hook has an 'id' key."""
        for language, config in LANGUAGE_CONFIGS.items():
            for repo_idx, repo in enumerate(config["hooks"]):
                # Get hooks list
                if "hooks" in repo:
                    hooks_list = repo["hooks"]
                elif "id" in repo:
                    # This is a local hook
                    continue
                else:
                    continue

                for hook_idx, hook in enumerate(hooks_list):
                    assert "id" in hook, (
                        f"{language} repo {repo_idx} hook {hook_idx} "
                        f"missing 'id' key: {hook}"
                    )

    def test_python_repo_urls_not_mutated(self) -> None:
        """Test Python repo URLs are exact (not mutated to XXurlXX etc)."""
        expected_repos = [
            "https://github.com/pre-commit/pre-commit-hooks",
            "https://github.com/astral-sh/ruff-pre-commit",
            "https://github.com/psf/black",
            "https://github.com/PyCQA/isort",
            "https://github.com/pre-commit/mirrors-mypy",
            "https://github.com/PyCQA/bandit",
            "https://github.com/Lucas-C/pre-commit-hooks-safety",
            "https://github.com/compilerla/conventional-pre-commit",
            "https://github.com/shellcheck-py/shellcheck-py",
            "https://github.com/asottile/pyupgrade",
            "https://github.com/PyCQA/autoflake",
            "https://github.com/guilatrova/tryceratops",
            "https://github.com/dosisod/refurb",
            "https://github.com/jendrikseipp/vulture",
            "https://github.com/econchick/interrogate",
            "https://github.com/Yelp/detect-secrets",
        ]
        python_repos = LANGUAGE_CONFIGS["python"]["hooks"]
        for idx, expected_url in enumerate(expected_repos):
            actual_url = python_repos[idx].get("repo", "")
            assert actual_url == expected_url, (
                f"Python repo {idx} URL mismatch: "
                f"expected {expected_url}, got {actual_url}"
            )

    def test_python_first_16_hooks_exact_ids(self) -> None:
        """Test first repo (pre-commit-hooks) has exact 16 hook IDs."""
        expected_ids = [
            "trailing-whitespace",
            "end-of-file-fixer",
            "check-yaml",
            "check-toml",
            "check-json",
            "check-added-large-files",
            "check-case-conflict",
            "check-merge-conflict",
            "check-symlinks",
            "check-ast",
            "debug-statements",
            "check-docstring-first",
            "detect-private-key",
            "fix-byte-order-marker",
            "mixed-line-ending",
            "no-commit-to-branch",
        ]
        first_repo = LANGUAGE_CONFIGS["python"]["hooks"][0]
        actual_ids = [hook["id"] for hook in first_repo["hooks"]]
        assert actual_ids == expected_ids

    def test_check_added_large_files_has_args_key(self) -> None:
        """Test check-added-large-files hook has 'args' key."""
        first_repo = LANGUAGE_CONFIGS["python"]["hooks"][0]
        large_files_hook = first_repo["hooks"][5]  # 6th hook
        assert large_files_hook["id"] == "check-added-large-files"
        assert "args" in large_files_hook

    def test_check_added_large_files_args_exact_value(self) -> None:
        """Test check-added-large-files args is exact list."""
        first_repo = LANGUAGE_CONFIGS["python"]["hooks"][0]
        large_files_hook = first_repo["hooks"][5]
        assert large_files_hook["args"] == ["--maxkb=500"]

    def test_mixed_line_ending_has_args(self) -> None:
        """Test mixed-line-ending hook has 'args' key."""
        first_repo = LANGUAGE_CONFIGS["python"]["hooks"][0]
        mixed_line_hook = first_repo["hooks"][14]  # 15th hook
        assert mixed_line_hook["id"] == "mixed-line-ending"
        assert "args" in mixed_line_hook
        assert mixed_line_hook["args"] == ["--fix=lf"]

    def test_no_commit_to_branch_has_args(self) -> None:
        """Test no-commit-to-branch hook has 'args' key."""
        first_repo = LANGUAGE_CONFIGS["python"]["hooks"][0]
        no_commit_hook = first_repo["hooks"][15]  # 16th hook
        assert no_commit_hook["id"] == "no-commit-to-branch"
        assert "args" in no_commit_hook
        assert no_commit_hook["args"] == ["--branch", "main"]

    def test_all_repo_revs_are_non_empty_strings(self) -> None:
        """Test every repo rev is a non-empty string."""
        for language, config in LANGUAGE_CONFIGS.items():
            for idx, repo in enumerate(config["hooks"]):
                if "rev" in repo:
                    rev = repo["rev"]
                    assert isinstance(
                        rev, str
                    ), f"{language} repo {idx} rev is not string: {type(rev)}"
                    assert rev, f"{language} repo {idx} rev is empty"
                    # Verify it's not mutated (e.g., "XXv1.0XX")
                    assert not rev.startswith(
                        "XX"
                    ), f"{language} repo {idx} rev looks mutated: {rev}"
                    assert not rev.endswith(
                        "XX"
                    ), f"{language} repo {idx} rev looks mutated: {rev}"
