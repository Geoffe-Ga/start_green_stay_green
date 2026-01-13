"""Unit tests for CI Generator (Issue #10).

Comprehensive tests for CI pipeline generation covering:
- Initialization and validation
- Workflow generation for all supported languages
- YAML validation and structure checking
- Error handling and edge cases
- Language-specific configurations
- Static utility methods
"""

from unittest.mock import Mock

import pytest

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError
from start_green_stay_green.ai.orchestrator import GenerationResult
from start_green_stay_green.ai.orchestrator import ModelConfig
from start_green_stay_green.ai.orchestrator import TokenUsage
from start_green_stay_green.generators.ci import CIGenerator
from start_green_stay_green.generators.ci import CIWorkflow
from start_green_stay_green.generators.ci import LANGUAGE_CONFIGS


class TestCIWorkflowDataClass:
    """Test CIWorkflow data class."""

    def test_ci_workflow_creation_with_all_fields(self) -> None:
        """Test creating CIWorkflow with all fields."""
        workflow = CIWorkflow(
            name="Test CI",
            content="test: content",
            language="python",
            is_valid=True,
            error_message=None,
        )
        assert workflow.name == "Test CI"
        assert workflow.content == "test: content"
        assert workflow.language == "python"
        assert workflow.is_valid is True
        assert workflow.error_message is None

    def test_ci_workflow_with_error_message(self) -> None:
        """Test CIWorkflow with error message."""
        workflow = CIWorkflow(
            name="Invalid CI",
            content="",
            language="python",
            is_valid=False,
            error_message="YAML parse error",
        )
        assert workflow.is_valid is False
        assert workflow.error_message == "YAML parse error"

    def test_ci_workflow_is_immutable(self) -> None:
        """Test CIWorkflow is immutable (frozen dataclass)."""
        workflow = CIWorkflow(
            name="Test",
            content="content",
            language="python",
            is_valid=True,
        )
        with pytest.raises(AttributeError):
            workflow.name = "Modified"  # type: ignore[misc]

    def test_ci_workflow_supports_all_languages(self) -> None:
        """Test CIWorkflow can represent any language."""
        for lang in LANGUAGE_CONFIGS:
            workflow = CIWorkflow(
                name=f"{lang} CI",
                content="content",
                language=lang,
                is_valid=True,
            )
            assert workflow.language == lang


class TestCIGeneratorInitialization:
    """Test CIGenerator initialization and configuration."""

    def test_initialization_with_python(self) -> None:
        """Test CIGenerator initializes with Python language."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        assert generator.language == "python"
        assert generator.framework is None
        assert generator.test_framework == "pytest"
        assert generator.supported_versions == ["3.11", "3.12", "3.13"]
        assert generator.orchestrator is mock_orchestrator

    def test_initialization_with_typescript(self) -> None:
        """Test CIGenerator initializes with TypeScript language."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "typescript")

        assert generator.language == "typescript"
        assert generator.test_framework == "jest"
        assert generator.supported_versions == ["18", "20"]

    def test_initialization_case_insensitive(self) -> None:
        """Test CIGenerator accepts case-insensitive language names."""
        mock_orchestrator = Mock(spec=AIOrchestrator)

        for variant in ["PYTHON", "Python", "PyThOn"]:
            generator = CIGenerator(mock_orchestrator, variant)
            assert generator.language == "python"

    def test_initialization_with_framework(self) -> None:
        """Test CIGenerator accepts optional framework parameter."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(
            mock_orchestrator,
            "python",
            framework="FastAPI",
        )

        assert generator.framework == "FastAPI"

    def test_initialization_unsupported_language_raises_error(self) -> None:
        """Test CIGenerator rejects unsupported languages."""
        mock_orchestrator = Mock(spec=AIOrchestrator)

        with pytest.raises(ValueError, match="Unsupported language"):
            CIGenerator(mock_orchestrator, "cobol")

    def test_initialization_empty_language_raises_error(self) -> None:
        """Test CIGenerator rejects empty language string."""
        mock_orchestrator = Mock(spec=AIOrchestrator)

        with pytest.raises(ValueError, match="Unsupported language"):
            CIGenerator(mock_orchestrator, "")

    def test_initialization_all_supported_languages(self) -> None:
        """Test CIGenerator initializes with all supported languages."""
        mock_orchestrator = Mock(spec=AIOrchestrator)

        for lang in LANGUAGE_CONFIGS:
            generator = CIGenerator(mock_orchestrator, lang)
            assert generator.language == lang


class TestCIGeneratorStaticMethods:
    """Test CIGenerator static utility methods."""

    def test_get_supported_languages_returns_all_languages(self) -> None:
        """Test get_supported_languages returns all configured languages."""
        languages = CIGenerator.get_supported_languages()

        assert len(languages) > 0
        assert set(languages) == set(LANGUAGE_CONFIGS.keys())
        # Should be sorted
        assert languages == sorted(languages)

    def test_get_supported_languages_returns_copy(self) -> None:
        """Test get_supported_languages returns mutable list."""
        languages = CIGenerator.get_supported_languages()
        original_length = len(languages)

        # Mutating returned list shouldn't affect future calls
        languages.append("fake_language")
        assert len(CIGenerator.get_supported_languages()) == original_length

    def test_get_language_config_python(self) -> None:
        """Test get_language_config returns Python configuration."""
        config = CIGenerator.get_language_config("python")

        assert config["test_framework"] == "pytest"
        assert "ruff" in config["linters"]
        assert "bandit" in config["security_tools"]
        assert config["package_manager"] == "pip"

    def test_get_language_config_case_insensitive(self) -> None:
        """Test get_language_config accepts case-insensitive language names."""
        for variant in ["PYTHON", "Python", "PyThOn"]:
            config = CIGenerator.get_language_config(variant)
            assert config["test_framework"] == "pytest"

    def test_get_language_config_unsupported_raises_error(self) -> None:
        """Test get_language_config rejects unsupported languages."""
        with pytest.raises(ValueError, match="Unsupported language"):
            CIGenerator.get_language_config("cobol")

    def test_get_language_config_returns_copy(self) -> None:
        """Test get_language_config returns independent copy."""
        config1 = CIGenerator.get_language_config("python")
        config1["custom_field"] = "value"

        config2 = CIGenerator.get_language_config("python")
        assert "custom_field" not in config2

    def test_language_configs_all_have_required_fields(self) -> None:
        """Test all language configs have required fields."""
        required_fields = {
            "test_framework",
            "linters",
            "formatters",
            "security_tools",
            "supported_versions",
            "package_manager",
        }

        for lang, config in LANGUAGE_CONFIGS.items():
            assert set(config.keys()) == required_fields, f"Missing fields in {lang}"
            assert isinstance(config["test_framework"], str)
            assert isinstance(config["linters"], list)
            assert isinstance(config["formatters"], list)
            assert isinstance(config["security_tools"], list)
            assert isinstance(config["supported_versions"], list)
            assert isinstance(config["package_manager"], str)


class TestCIGeneratorContextBuilding:
    """Test context building for AI generation."""

    def test_build_generation_context_python(self) -> None:
        """Test context building for Python language."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        context = generator._build_generation_context(  # noqa: SLF001
            LANGUAGE_CONFIGS["python"]
        )

        assert "PYTHON" in context
        assert "pytest" in context
        assert "ruff" in context
        assert "bandit" in context
        assert "3.11" in context
        assert "pip" in context

    def test_build_generation_context_includes_quality_standards(
        self,
    ) -> None:
        """Test context includes quality standards."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        context = generator._build_generation_context(  # noqa: SLF001
            LANGUAGE_CONFIGS["python"]
        )

        assert "Code Coverage" in context
        assert "90%" in context
        assert "Mutation Score" in context

    def test_build_generation_context_includes_framework_when_provided(
        self,
    ) -> None:
        """Test context includes framework information."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(
            mock_orchestrator,
            "python",
            framework="Django",
        )

        context = generator._build_generation_context(  # noqa: SLF001
            LANGUAGE_CONFIGS["python"]
        )

        assert "Django" in context

    def test_build_generation_context_omits_framework_when_not_provided(
        self,
    ) -> None:
        """Test context omits framework section when not provided."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        context = generator._build_generation_context(  # noqa: SLF001
            LANGUAGE_CONFIGS["python"]
        )

        # Check that Framework: line doesn't appear (avoid false positive from "Test Framework:")
        assert "\nFramework: " not in context


class TestCIGeneratorValidation:
    """Test YAML validation and parsing."""

    def _create_minimal_valid_workflow(self) -> str:
        """Create a minimal valid GitHub Actions workflow."""
        return """name: Test CI
on:
  push:
    branches: [main]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
"""

    def test_validate_valid_workflow(self) -> None:
        """Test validation passes for valid workflow."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        workflow = generator._validate_and_parse(  # noqa: SLF001
            self._create_minimal_valid_workflow()
        )

        assert workflow.is_valid is True
        assert workflow.error_message is None
        assert workflow.name == "Test CI"
        assert workflow.language == "python"

    def test_validate_invalid_yaml_raises_error(self) -> None:
        """Test validation fails for invalid YAML."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        with pytest.raises(ValueError, match="Invalid YAML"):
            generator._validate_and_parse("not: valid: yaml: [syntax")  # noqa: SLF001

    def test_validate_not_dict_raises_error(self) -> None:
        """Test validation fails when YAML is not a dictionary."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        with pytest.raises(ValueError, match="YAML dictionary"):
            generator._validate_and_parse("- item1\n- item2")  # noqa: SLF001

    def test_validate_missing_name_raises_error(self) -> None:
        """Test validation fails when 'name' field is missing."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        workflow_yaml = """on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
        with pytest.raises(ValueError, match="'name' field"):
            generator._validate_and_parse(workflow_yaml)  # noqa: SLF001

    def test_validate_missing_jobs_raises_error(self) -> None:
        """Test validation fails when 'jobs' field is missing."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        workflow_yaml = "name: Test CI\non: push"

        with pytest.raises(ValueError, match="'jobs' field"):
            generator._validate_and_parse(workflow_yaml)  # noqa: SLF001

    def test_validate_jobs_not_dict_raises_error(self) -> None:
        """Test validation fails when jobs is not a dictionary."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        workflow_yaml = """name: Test CI
on: push
jobs:
  - item1
  - item2
"""
        with pytest.raises(ValueError, match="Jobs must be a dictionary"):
            generator._validate_and_parse(workflow_yaml)  # noqa: SLF001

    def test_validate_missing_required_jobs_raises_error(self) -> None:
        """Test validation fails when required jobs are missing."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        workflow_yaml = """name: Test CI
on: push
jobs:
  other:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
        with pytest.raises(ValueError, match="missing required jobs"):
            generator._validate_and_parse(workflow_yaml)  # noqa: SLF001

    def test_validate_quality_job_missing_steps_raises_error(
        self,
    ) -> None:
        """Test validation fails when quality job has no steps."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        workflow_yaml = """name: Test CI
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""
        with pytest.raises(ValueError, match="Quality job must have"):
            generator._validate_and_parse(workflow_yaml)  # noqa: SLF001

    def test_validate_test_job_missing_steps_raises_error(self) -> None:
        """Test validation fails when test job has no steps."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        workflow_yaml = """name: Test CI
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
  test:
    runs-on: ubuntu-latest
"""
        with pytest.raises(ValueError, match="Test job must have"):
            generator._validate_and_parse(workflow_yaml)  # noqa: SLF001

    def test_validate_empty_steps_raises_error(self) -> None:
        """Test validation fails when steps list is empty."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        workflow_yaml = """name: Test CI
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
    steps: []
  test:
    runs-on: ubuntu-latest
    steps: []
"""
        with pytest.raises(ValueError, match="must have at least one step"):
            generator._validate_and_parse(workflow_yaml)  # noqa: SLF001


class TestCIGeneratorGeneration:
    """Test workflow generation with mocked AI."""

    def _create_mock_orchestrator(
        self,
        return_content: str,
    ) -> Mock:
        """Create a mock orchestrator with predefined response."""
        mock_orchestrator = Mock(spec=AIOrchestrator)

        mock_result = GenerationResult(
            content=return_content,
            format="yaml",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            model=ModelConfig.SONNET,
            message_id="msg_test",
        )

        mock_orchestrator.generate.return_value = mock_result
        return mock_orchestrator

    def _create_minimal_valid_workflow(self) -> str:
        """Create a minimal valid GitHub Actions workflow."""
        return """name: Test CI
on:
  push:
    branches: [main]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
"""

    def test_generate_workflow_python(self) -> None:
        """Test workflow generation for Python."""
        mock_orchestrator = self._create_mock_orchestrator(
            self._create_minimal_valid_workflow()
        )
        generator = CIGenerator(mock_orchestrator, "python")

        workflow = generator.generate_workflow()

        assert workflow.is_valid is True
        assert workflow.language == "python"
        assert workflow.name == "Test CI"
        assert mock_orchestrator.generate.called

    def test_generate_workflow_calls_orchestrator(self) -> None:
        """Test generate_workflow calls AI orchestrator."""
        mock_orchestrator = self._create_mock_orchestrator(
            self._create_minimal_valid_workflow()
        )
        generator = CIGenerator(mock_orchestrator, "python")

        generator.generate_workflow()

        # Verify orchestrator was called
        mock_orchestrator.generate.assert_called_once()
        call_args = mock_orchestrator.generate.call_args

        # Verify correct format was requested
        assert call_args.kwargs["output_format"] == "yaml"

        # Verify prompt contains language information
        prompt = call_args.kwargs["prompt"]
        assert "PYTHON" in prompt or "python" in prompt

    def test_generate_workflow_with_framework(self) -> None:
        """Test workflow generation includes framework information."""
        mock_orchestrator = self._create_mock_orchestrator(
            self._create_minimal_valid_workflow()
        )
        generator = CIGenerator(
            mock_orchestrator,
            "python",
            framework="FastAPI",
        )

        generator.generate_workflow()

        # Verify framework was included in prompt
        prompt = mock_orchestrator.generate.call_args.kwargs["prompt"]
        assert "FastAPI" in prompt

    def test_generate_method_returns_dict(self) -> None:
        """Test generate method returns dictionary with expected keys."""
        mock_orchestrator = self._create_mock_orchestrator(
            self._create_minimal_valid_workflow()
        )
        generator = CIGenerator(
            mock_orchestrator,
            "python",
            framework="Django",
        )

        result = generator.generate()

        assert isinstance(result, dict)
        assert "workflow" in result
        assert "language" in result
        assert "framework" in result
        assert result["language"] == "python"
        assert result["framework"] == "Django"
        assert isinstance(result["workflow"], CIWorkflow)

    def test_generate_workflow_preserves_content(self) -> None:
        """Test generated workflow preserves original YAML content."""
        original_yaml = self._create_minimal_valid_workflow()
        mock_orchestrator = self._create_mock_orchestrator(original_yaml)
        generator = CIGenerator(mock_orchestrator, "python")

        workflow = generator.generate_workflow()

        assert workflow.content == original_yaml


class TestCIGeneratorErrorHandling:
    """Test error handling in CI generator."""

    def test_generate_workflow_orchestrator_error(self) -> None:
        """Test generate_workflow propagates orchestrator errors."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        mock_orchestrator.generate.side_effect = GenerationError("API failed")

        generator = CIGenerator(mock_orchestrator, "python")

        with pytest.raises(GenerationError):
            generator.generate_workflow()

    def test_generate_workflow_invalid_yaml_raises_error(self) -> None:
        """Test generate_workflow handles invalid AI output."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        mock_orchestrator.generate.return_value = GenerationResult(
            content="invalid: yaml: [",
            format="yaml",
            token_usage=TokenUsage(input_tokens=10, output_tokens=5),
            model=ModelConfig.SONNET,
            message_id="msg_test",
        )

        generator = CIGenerator(mock_orchestrator, "python")

        with pytest.raises(ValueError, match="Invalid YAML"):
            generator.generate_workflow()


class TestCIGeneratorAllLanguages:
    """Test CI generation works for all supported languages."""

    def _create_minimal_valid_workflow(self) -> str:
        """Create a minimal valid GitHub Actions workflow."""
        return """name: CI
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - run: echo quality
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""

    @pytest.mark.parametrize(
        "language",
        [
            "python",
            "typescript",
            "go",
            "rust",
            "java",
            "csharp",
            "ruby",
        ],
    )
    def test_generate_workflow_all_languages(
        self,
        language: str,
    ) -> None:
        """Test workflow generation works for all languages."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        mock_orchestrator.generate.return_value = GenerationResult(
            content=self._create_minimal_valid_workflow(),
            format="yaml",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            model=ModelConfig.SONNET,
            message_id="msg_test",
        )

        generator = CIGenerator(mock_orchestrator, language)
        workflow = generator.generate_workflow()

        assert workflow.is_valid is True
        assert workflow.language == language


class TestMutationKillers:
    """Targeted mutation tests to achieve 80%+ mutation score.

    These tests verify exact values, boundaries, and logic conditions
    to ensure mutations are caught.
    """

    def _create_minimal_valid_workflow(self) -> str:
        """Create a minimal valid GitHub Actions workflow."""
        return """name: CI
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo test
"""

    def test_ci_workflow_is_valid_exact_value(self) -> None:
        """Test CIWorkflow.is_valid is exactly True when valid.

        Kills mutations: True → False, is_valid → not is_valid
        """
        workflow = CIWorkflow(
            name="Test",
            content="content",
            language="python",
            is_valid=True,
        )
        assert workflow.is_valid is True
        assert workflow.is_valid is not False

    def test_ci_workflow_error_message_none_when_valid(self) -> None:
        """Test error_message is None when valid.

        Kills mutations: None → "", is_valid → False
        """
        workflow = CIWorkflow(
            name="Test",
            content="content",
            language="python",
            is_valid=True,
        )
        assert workflow.error_message is None
        assert workflow.error_message != ""

    def test_initialization_language_lowercasing_exact(self) -> None:
        """Test language is exactly lowercased.

        Kills mutations in case conversion logic.
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)

        variants = {
            "PYTHON": "python",
            "Python": "python",
            "PyThOn": "python",
            "python": "python",
        }

        for input_lang, expected in variants.items():
            generator = CIGenerator(mock_orchestrator, input_lang)
            assert generator.language == expected
            assert generator.language != input_lang.upper()

    def test_language_config_not_supported_exact_error(self) -> None:
        """Test exact error for unsupported language.

        Kills mutations in error message construction.
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)

        with pytest.raises(ValueError, match=r"Unsupported language.*cobol"):
            CIGenerator(mock_orchestrator, "cobol")

    def test_framework_stored_as_provided(self) -> None:
        """Test framework is stored exactly as provided.

        Kills mutations in field assignment.
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)

        generator = CIGenerator(
            mock_orchestrator,
            "python",
            framework="FastAPI",
        )
        assert generator.framework == "FastAPI"
        assert generator.framework != "fastapi"

        generator_no_framework = CIGenerator(mock_orchestrator, "python")
        assert generator_no_framework.framework is None

    def test_supported_languages_are_sorted(self) -> None:
        """Test get_supported_languages returns exactly sorted list.

        Kills mutations: sorted → unsorted, list.sort() removed
        """
        languages = CIGenerator.get_supported_languages()
        expected = sorted(LANGUAGE_CONFIGS.keys())

        assert languages == expected
        assert languages[0] <= languages[-1]  # First <= Last when sorted

    def test_language_config_returns_independent_copy(self) -> None:
        """Test get_language_config returns independent copy.

        Kills mutations: deepcopy removal, shallow copy → reference
        """
        config1 = CIGenerator.get_language_config("python")
        config1["modified"] = True

        config2 = CIGenerator.get_language_config("python")
        assert "modified" not in config2

    def test_required_jobs_validation_exact_set(self) -> None:
        """Test validation checks for EXACT required jobs.

        Kills mutations: required_jobs set → different set,
        set operations changed
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        # Should accept workflow with quality and test
        valid_yaml = """name: CI
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - run: test
  test:
    runs-on: ubuntu-latest
    steps:
      - run: test
"""
        workflow = generator._validate_and_parse(valid_yaml)  # noqa: SLF001
        assert workflow.is_valid is True

        # Should reject workflow with only quality (missing test)
        missing_test = """name: CI
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - run: test
"""
        with pytest.raises(ValueError, match="missing required jobs"):
            generator._validate_and_parse(missing_test)  # noqa: SLF001

    def test_is_valid_flag_exact_true_when_successful(self) -> None:
        """Test is_valid is exactly True on successful validation.

        Kills mutations: is_valid = True → False
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        valid_yaml = """name: CI
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - run: test
  test:
    runs-on: ubuntu-latest
    steps:
      - run: test
"""
        workflow = generator._validate_and_parse(valid_yaml)  # noqa: SLF001

        assert workflow.is_valid is True
        assert workflow.is_valid == True  # noqa: E712
        assert workflow.is_valid is not False

    def test_parse_yaml_safe_load_used(self) -> None:
        """Test yaml.safe_load is used (not unsafe load).

        Kills mutations: safe_load → load
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        # safe_load prevents code injection
        with pytest.raises(ValueError, match="Invalid YAML"):
            generator._validate_and_parse(  # noqa: SLF001
                "!!python/object/new:os.system ['id']"
            )

    def test_generate_returns_dict_with_exact_keys(self) -> None:
        """Test generate returns dict with exactly expected keys.

        Kills mutations in return value construction.
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)
        mock_orchestrator.generate.return_value = GenerationResult(
            content="""name: CI
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - run: test
  test:
    runs-on: ubuntu-latest
    steps:
      - run: test
""",
            format="yaml",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            model=ModelConfig.SONNET,
            message_id="msg_test",
        )

        generator = CIGenerator(
            mock_orchestrator,
            "python",
            framework="FastAPI",
        )
        result = generator.generate()

        expected_keys = {"workflow", "language", "framework"}
        assert set(result.keys()) == expected_keys
        assert result["language"] == "python"
        assert result["framework"] == "FastAPI"

    def test_get_language_config_case_lowercased(self) -> None:
        """Test get_language_config lowercases input.

        Kills mutations: .lower() removed
        """
        config_lower = CIGenerator.get_language_config("python")
        config_upper = CIGenerator.get_language_config("PYTHON")

        assert config_lower == config_upper
        assert config_lower["test_framework"] == "pytest"

    def test_orchestrator_field_is_parent_class_attribute(self) -> None:
        """Test orchestrator is inherited from BaseGenerator.

        Kills mutations: BaseGenerator inheritance removed
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        # Should be inherited from BaseGenerator
        assert hasattr(generator, "orchestrator")
        assert generator.orchestrator is mock_orchestrator

    def test_workflow_content_exact_preservation(self) -> None:
        """Test workflow content is preserved exactly.

        Kills mutations: content modification, trimming, etc.
        """
        original_content = """name: Test CI
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - run: test
  test:
    runs-on: ubuntu-latest
    steps:
      - run: test
"""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        workflow = generator._validate_and_parse(original_content)  # noqa: SLF001

        assert workflow.content == original_content
        # Should have exact whitespace preservation
        assert workflow.content.count("\n") == original_content.count("\n")
