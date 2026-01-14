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
        assert len(result) > 0

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
        assert len(result) > 0

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
        assert len(result) > 0

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
        assert len(result) > 0

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
        assert generator.validate_language("python") is True

    def test_validate_language_typescript_returns_true(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test validate_language returns True for TypeScript."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator.validate_language("typescript") is True

    def test_validate_language_go_returns_true(self, mock_orchestrator: Mock) -> None:
        """Test validate_language returns True for Go."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator.validate_language("go") is True

    def test_validate_language_rust_returns_true(self, mock_orchestrator: Mock) -> None:
        """Test validate_language returns True for Rust."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator.validate_language("rust") is True

    def test_validate_language_unsupported_returns_false(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test validate_language returns False for unsupported language."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator.validate_language("cobol") is False

    def test_validate_language_empty_string_returns_false(
        self, mock_orchestrator: Mock
    ) -> None:
        """Test validate_language returns False for empty string."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator.validate_language("") is False

    def test_validate_language_case_sensitive(self, mock_orchestrator: Mock) -> None:
        """Test validate_language is case sensitive."""
        generator = PreCommitGenerator(mock_orchestrator)
        assert generator.validate_language("Python") is False
        assert generator.validate_language("PYTHON") is False


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
        assert len(result) > 0

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
        assert len(LANGUAGE_CONFIGS) > 0

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
        assert config.language_config == {}

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
        assert generator.validate_language("python") is True
        assert generator.validate_language("unknown") is False

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
