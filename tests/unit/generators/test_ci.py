"""Unit tests for CI Generator (Issue #10).

Comprehensive tests for CI pipeline generation covering:
- Initialization and validation
- Workflow generation for all supported languages
- YAML validation and structure checking
- Error handling and edge cases
- Language-specific configurations
- Static utility methods
"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

from jinja2 import UndefinedError
import pytest
import yaml

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError
from start_green_stay_green.ai.orchestrator import GenerationResult
from start_green_stay_green.ai.orchestrator import ModelConfig
from start_green_stay_green.ai.orchestrator import TokenUsage
from start_green_stay_green.generators.ci import CIGenerator
from start_green_stay_green.generators.ci import CIWorkflow
from start_green_stay_green.generators.ci import LANGUAGE_CONFIGS
from start_green_stay_green.utils.kotlin import GRADLE_WRAPPER_VERSION


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
        assert workflow.is_valid
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
        assert not workflow.is_valid
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

        for variant in ("PYTHON", "Python", "PyThOn"):
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

        assert languages
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
        for variant in ("PYTHON", "Python", "PyThOn"):
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

        context = generator._build_generation_context(LANGUAGE_CONFIGS["python"])

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

        context = generator._build_generation_context(LANGUAGE_CONFIGS["python"])

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

        context = generator._build_generation_context(LANGUAGE_CONFIGS["python"])

        assert "Django" in context

    def test_build_generation_context_omits_framework_when_not_provided(
        self,
    ) -> None:
        """Test context omits framework section when not provided."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        context = generator._build_generation_context(LANGUAGE_CONFIGS["python"])

        # Check Framework: line doesn't appear
        # (avoid false positive from "Test Framework:")
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

        workflow = generator._validate_and_parse(self._create_minimal_valid_workflow())

        assert workflow.is_valid
        assert workflow.error_message is None
        assert workflow.name == "Test CI"
        assert workflow.language == "python"

    def test_validate_invalid_yaml_raises_error(self) -> None:
        """Test validation fails for invalid YAML."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        with pytest.raises(ValueError, match="Invalid YAML"):
            generator._validate_and_parse("not: valid: yaml: [syntax")

    def test_validate_not_dict_raises_error(self) -> None:
        """Test validation fails when YAML is not a dictionary."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        with pytest.raises(ValueError, match="YAML dictionary"):
            generator._validate_and_parse("- item1\n- item2")

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
            generator._validate_and_parse(workflow_yaml)

    def test_validate_missing_jobs_raises_error(self) -> None:
        """Test validation fails when 'jobs' field is missing."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        workflow_yaml = "name: Test CI\non: push"

        with pytest.raises(ValueError, match="'jobs' field"):
            generator._validate_and_parse(workflow_yaml)

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
            generator._validate_and_parse(workflow_yaml)

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
            generator._validate_and_parse(workflow_yaml)

    def test_validate_workflow_with_quality_job_only(self) -> None:
        """Test validation accepts workflow with only quality job.

        This matches the pattern in reference/ci/python.yml where tests
        are run within the quality job, not as a separate job.

        Fixes Issue #165: AI-generated workflows follow reference pattern.
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        # Workflow with only quality job (like reference/ci/python.yml)
        workflow_yaml = """name: Python Quality Checks
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Run tests
        run: pytest --cov=src
  complexity:
    runs-on: ubuntu-latest
    steps:
      - name: Check complexity
        run: radon cc src/
"""
        # Should NOT raise - quality job is present with test steps
        workflow = generator._validate_and_parse(workflow_yaml)
        assert workflow.is_valid
        assert workflow.name == "Python Quality Checks"

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
            generator._validate_and_parse(workflow_yaml)

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
            generator._validate_and_parse(workflow_yaml)

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
            generator._validate_and_parse(workflow_yaml)


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

        assert workflow.is_valid
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
            "swift",
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

        assert workflow.is_valid
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
        assert workflow.is_valid
        assert workflow.is_valid

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

        Updated for Issue #165: Only 'quality' job is required now.
        Tests can be run within the quality job (like reference workflows).
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
        workflow = generator._validate_and_parse(valid_yaml)
        assert workflow.is_valid

        # Should also accept workflow with only quality (test is optional)
        quality_only = """name: CI
on: push
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - run: test
"""
        workflow = generator._validate_and_parse(quality_only)
        assert workflow.is_valid

        # Should reject workflow with neither quality nor test
        no_required_jobs = """name: CI
on: push
jobs:
  other:
    runs-on: ubuntu-latest
    steps:
      - run: test
"""
        with pytest.raises(ValueError, match="missing required jobs"):
            generator._validate_and_parse(no_required_jobs)

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
        workflow = generator._validate_and_parse(valid_yaml)

        assert workflow.is_valid
        assert workflow.is_valid
        assert workflow.is_valid

    def test_parse_yaml_safe_load_used(self) -> None:
        """Test yaml.safe_load is used (not unsafe load).

        Kills mutations: safe_load → load
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = CIGenerator(mock_orchestrator, "python")

        # safe_load prevents code injection
        with pytest.raises(ValueError, match="Invalid YAML"):
            generator._validate_and_parse("!!python/object/new:os.system ['id']")

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

        workflow = generator._validate_and_parse(original_content)

        assert workflow.content == original_content
        # Should have exact whitespace preservation
        assert workflow.content.count("\n") == original_content.count("\n")

    # LANGUAGE_CONFIGS Exact Value Tests - Python
    def test_python_test_framework_exact(self) -> None:
        """Test Python test_framework is exactly pytest."""
        assert LANGUAGE_CONFIGS["python"]["test_framework"] == "pytest"

    def test_python_linters_exact(self) -> None:
        """Test Python linters list is exact."""
        assert LANGUAGE_CONFIGS["python"]["linters"] == ["ruff", "pylint", "mypy"]

    def test_python_formatters_exact(self) -> None:
        """Test Python formatters list is exact."""
        assert LANGUAGE_CONFIGS["python"]["formatters"] == ["black", "ruff"]

    def test_python_security_tools_exact(self) -> None:
        """Test Python security_tools list is exact."""
        assert LANGUAGE_CONFIGS["python"]["security_tools"] == ["bandit", "pip-audit"]

    def test_python_supported_versions_exact(self) -> None:
        """Test Python supported_versions list is exact."""
        expected = ["3.11", "3.12", "3.13"]
        assert LANGUAGE_CONFIGS["python"]["supported_versions"] == expected

    def test_python_package_manager_exact(self) -> None:
        """Test Python package_manager is exactly pip."""
        assert LANGUAGE_CONFIGS["python"]["package_manager"] == "pip"

    # LANGUAGE_CONFIGS Exact Value Tests - TypeScript
    def test_typescript_test_framework_exact(self) -> None:
        """Test TypeScript test_framework is exactly jest."""
        assert LANGUAGE_CONFIGS["typescript"]["test_framework"] == "jest"

    def test_typescript_linters_exact(self) -> None:
        """Test TypeScript linters list is exact."""
        assert LANGUAGE_CONFIGS["typescript"]["linters"] == ["eslint", "tsc"]

    def test_typescript_formatters_exact(self) -> None:
        """Test TypeScript formatters list is exact."""
        assert LANGUAGE_CONFIGS["typescript"]["formatters"] == ["prettier", "eslint"]

    def test_typescript_security_tools_exact(self) -> None:
        """Test TypeScript security_tools list is exact."""
        assert LANGUAGE_CONFIGS["typescript"]["security_tools"] == ["npm_audit", "snyk"]

    def test_typescript_supported_versions_exact(self) -> None:
        """Test TypeScript supported_versions list is exact."""
        assert LANGUAGE_CONFIGS["typescript"]["supported_versions"] == ["18", "20"]

    def test_typescript_package_manager_exact(self) -> None:
        """Test TypeScript package_manager is exactly npm."""
        assert LANGUAGE_CONFIGS["typescript"]["package_manager"] == "npm"

    # LANGUAGE_CONFIGS Exact Value Tests - Go
    def test_go_test_framework_exact(self) -> None:
        """Test Go test_framework is exactly go_test."""
        assert LANGUAGE_CONFIGS["go"]["test_framework"] == "go_test"

    def test_go_linters_exact(self) -> None:
        """Test Go linters list is exact."""
        assert LANGUAGE_CONFIGS["go"]["linters"] == ["golangci-lint"]

    def test_go_formatters_exact(self) -> None:
        """Test Go formatters list is exact."""
        assert LANGUAGE_CONFIGS["go"]["formatters"] == ["gofmt"]

    def test_go_security_tools_exact(self) -> None:
        """Test Go security_tools list is exact."""
        assert LANGUAGE_CONFIGS["go"]["security_tools"] == ["gosec"]

    def test_go_supported_versions_exact(self) -> None:
        """Test Go supported_versions list is exact."""
        assert LANGUAGE_CONFIGS["go"]["supported_versions"] == ["1.21", "1.22"]

    def test_go_package_manager_exact(self) -> None:
        """Test Go package_manager is exactly go_modules."""
        assert LANGUAGE_CONFIGS["go"]["package_manager"] == "go_modules"

    # LANGUAGE_CONFIGS Exact Value Tests - Rust
    def test_rust_test_framework_exact(self) -> None:
        """Test Rust test_framework is exactly cargo_test."""
        assert LANGUAGE_CONFIGS["rust"]["test_framework"] == "cargo_test"

    def test_rust_linters_exact(self) -> None:
        """Test Rust linters list is exact."""
        assert LANGUAGE_CONFIGS["rust"]["linters"] == ["clippy"]

    def test_rust_formatters_exact(self) -> None:
        """Test Rust formatters list is exact."""
        assert LANGUAGE_CONFIGS["rust"]["formatters"] == ["rustfmt"]

    def test_rust_security_tools_exact(self) -> None:
        """Test Rust security_tools list is exact."""
        assert LANGUAGE_CONFIGS["rust"]["security_tools"] == ["cargo_audit"]

    def test_rust_supported_versions_exact(self) -> None:
        """Test Rust supported_versions list is exact."""
        assert LANGUAGE_CONFIGS["rust"]["supported_versions"] == ["1.70", "1.75"]

    def test_rust_package_manager_exact(self) -> None:
        """Test Rust package_manager is exactly cargo."""
        assert LANGUAGE_CONFIGS["rust"]["package_manager"] == "cargo"

    # LANGUAGE_CONFIGS Exact Value Tests - Java
    def test_java_test_framework_exact(self) -> None:
        """Test Java test_framework is exactly junit."""
        assert LANGUAGE_CONFIGS["java"]["test_framework"] == "junit"

    def test_java_linters_exact(self) -> None:
        """Test Java linters list is exact."""
        assert LANGUAGE_CONFIGS["java"]["linters"] == ["checkstyle"]

    def test_java_formatters_exact(self) -> None:
        """Test Java formatters list is exact."""
        assert LANGUAGE_CONFIGS["java"]["formatters"] == ["google-java-format"]

    def test_java_security_tools_exact(self) -> None:
        """Test Java security_tools list is exact."""
        assert LANGUAGE_CONFIGS["java"]["security_tools"] == ["spotbugs"]

    def test_java_supported_versions_exact(self) -> None:
        """Test Java supported_versions list is exact."""
        assert LANGUAGE_CONFIGS["java"]["supported_versions"] == ["11", "17", "21"]

    def test_java_package_manager_exact(self) -> None:
        """Test Java package_manager is exactly maven."""
        assert LANGUAGE_CONFIGS["java"]["package_manager"] == "maven"

    # LANGUAGE_CONFIGS Exact Value Tests - C#
    def test_csharp_test_framework_exact(self) -> None:
        """Test C# test_framework is exactly xunit."""
        assert LANGUAGE_CONFIGS["csharp"]["test_framework"] == "xunit"

    def test_csharp_linters_exact(self) -> None:
        """Test C# linters list is exact."""
        assert LANGUAGE_CONFIGS["csharp"]["linters"] == ["roslyn"]

    def test_csharp_formatters_exact(self) -> None:
        """Test C# formatters list is exact."""
        assert LANGUAGE_CONFIGS["csharp"]["formatters"] == ["dotnet_format"]

    def test_csharp_security_tools_exact(self) -> None:
        """Test C# security_tools list is exact."""
        assert LANGUAGE_CONFIGS["csharp"]["security_tools"] == ["security_code_scan"]

    def test_csharp_supported_versions_exact(self) -> None:
        """Test C# supported_versions list is exact."""
        assert LANGUAGE_CONFIGS["csharp"]["supported_versions"] == ["6.0", "8.0"]

    def test_csharp_package_manager_exact(self) -> None:
        """Test C# package_manager is exactly nuget."""
        assert LANGUAGE_CONFIGS["csharp"]["package_manager"] == "nuget"

    # LANGUAGE_CONFIGS Exact Value Tests - Ruby
    def test_ruby_test_framework_exact(self) -> None:
        """Test Ruby test_framework is exactly rspec."""
        assert LANGUAGE_CONFIGS["ruby"]["test_framework"] == "rspec"

    def test_ruby_linters_exact(self) -> None:
        """Test Ruby linters list is exact."""
        assert LANGUAGE_CONFIGS["ruby"]["linters"] == ["rubocop"]

    def test_ruby_formatters_exact(self) -> None:
        """Test Ruby formatters list is exact."""
        assert LANGUAGE_CONFIGS["ruby"]["formatters"] == ["rubocop"]

    def test_ruby_security_tools_exact(self) -> None:
        """Test Ruby security_tools list is exact.

        bundler-audit owns the generated security gate (#373); Brakeman
        is Rails-specific and errors on the plain-Ruby scaffold, so it
        must not be advertised as wired tooling.
        """
        assert LANGUAGE_CONFIGS["ruby"]["security_tools"] == ["bundler-audit"]

    def test_ruby_supported_versions_exact(self) -> None:
        """Test Ruby supported_versions list is exact.

        3.1 and 3.2 reached upstream EOL; 3.3/3.4 are the maintained
        lines (verified against ruby-lang.org, 2026-06).
        """
        assert LANGUAGE_CONFIGS["ruby"]["supported_versions"] == ["3.3", "3.4"]

    def test_ruby_package_manager_exact(self) -> None:
        """Test Ruby package_manager is exactly bundler."""
        assert LANGUAGE_CONFIGS["ruby"]["package_manager"] == "bundler"

    # LANGUAGE_CONFIGS Exact Value Tests - Swift
    def test_swift_test_framework_exact(self) -> None:
        """Test Swift test_framework is exactly xctest."""
        assert LANGUAGE_CONFIGS["swift"]["test_framework"] == "xctest"

    def test_swift_linters_exact(self) -> None:
        """Test Swift linters list is exact."""
        assert LANGUAGE_CONFIGS["swift"]["linters"] == ["swiftlint"]

    def test_swift_formatters_exact(self) -> None:
        """Test Swift formatters list is exact."""
        assert LANGUAGE_CONFIGS["swift"]["formatters"] == ["swift-format"]

    def test_swift_security_tools_exact(self) -> None:
        """Test Swift security_tools list is exact.

        SwiftLint serves security duty too but is listed only under
        linters so tool-install consumers don't double-install it.
        """
        expected = ["gitleaks", "periphery"]
        assert LANGUAGE_CONFIGS["swift"]["security_tools"] == expected

    def test_swift_supported_versions_exact(self) -> None:
        """Test Swift supported_versions list is exact."""
        assert LANGUAGE_CONFIGS["swift"]["supported_versions"] == ["5.9", "5.10", "6.0"]

    def test_swift_package_manager_exact(self) -> None:
        """Test Swift package_manager is exactly spm."""
        assert LANGUAGE_CONFIGS["swift"]["package_manager"] == "spm"

    # LANGUAGE_CONFIGS Exact Value Tests - Kotlin
    def test_kotlin_test_framework_exact(self) -> None:
        """Test Kotlin test_framework is exactly junit."""
        assert LANGUAGE_CONFIGS["kotlin"]["test_framework"] == "junit"

    def test_kotlin_linters_exact(self) -> None:
        """Test Kotlin linters list is exact."""
        assert LANGUAGE_CONFIGS["kotlin"]["linters"] == ["ktlint", "detekt"]

    def test_kotlin_formatters_exact(self) -> None:
        """Test Kotlin formatters list is exact.

        ktlint genuinely is both a linter and a formatter (like ruff,
        eslint, and rubocop in the other configs), so it appears in both
        lists; that is established precedent, unlike double-listing a
        tool under security_tools (the Swift PR #414 lesson).
        """
        assert LANGUAGE_CONFIGS["kotlin"]["formatters"] == ["ktlint"]

    def test_kotlin_security_tools_exact(self) -> None:
        """Test Kotlin security_tools list is exact.

        detekt's potential-bugs rules serve security duty too but it is
        listed only under linters so tool-install consumers don't
        double-install it (the Swift PR #414 review lesson).
        """
        expected = ["gitleaks", "dependency-check"]
        assert LANGUAGE_CONFIGS["kotlin"]["security_tools"] == expected

    def test_kotlin_supported_versions_exact(self) -> None:
        """Test Kotlin supported_versions are the JDK LTS releases.

        The Kotlin version (2.0.21) is pinned by the generated root
        build.gradle.kts — a project decision, not a CI input — so the
        meaningful matrix axis is the JVM running Gradle/AGP.
        """
        assert LANGUAGE_CONFIGS["kotlin"]["supported_versions"] == ["17", "21"]

    def test_kotlin_package_manager_exact(self) -> None:
        """Test Kotlin package_manager is exactly gradle."""
        assert LANGUAGE_CONFIGS["kotlin"]["package_manager"] == "gradle"

    # LANGUAGE_CONFIGS Exact Value Tests - C/C++
    def test_cpp_test_framework_exact(self) -> None:
        """Test cpp test_framework is exactly catch2.

        The epic text named GoogleTest, but the #361 foundation chose
        Catch2 (conanfile.txt pins catch2/3.x and the scaffolded tests
        use Catch2 macros), so CI stays consistent with what the
        generated project actually builds.
        """
        assert LANGUAGE_CONFIGS["cpp"]["test_framework"] == "catch2"

    def test_cpp_linters_exact(self) -> None:
        """Test cpp linters list is exact."""
        assert LANGUAGE_CONFIGS["cpp"]["linters"] == ["clang-tidy", "cppcheck"]

    def test_cpp_formatters_exact(self) -> None:
        """Test cpp formatters list is exact."""
        assert LANGUAGE_CONFIGS["cpp"]["formatters"] == ["clang-format"]

    def test_cpp_security_tools_exact(self) -> None:
        """Test cpp security_tools list is exact.

        cppcheck and clang-tidy's clang-analyzer-*/cert-* checks serve
        security duty too but are listed only under linters so
        tool-install consumers don't double-install them (the Swift
        PR #414 lesson).
        """
        assert LANGUAGE_CONFIGS["cpp"]["security_tools"] == [
            "gitleaks",
            "flawfinder",
        ]

    def test_cpp_supported_versions_exact(self) -> None:
        """Test cpp supported_versions are the matrix compilers.

        The generated CMakeLists.txt pins CMAKE_CXX_STANDARD to 17
        (utils.cpp.CPP_STANDARD — a project decision, not a CI input),
        so the honest matrix axis is the compiler building that pinned
        standard, not a language-standard matrix CI could never vary.
        """
        assert LANGUAGE_CONFIGS["cpp"]["supported_versions"] == ["gcc", "clang"]

    def test_cpp_package_manager_exact(self) -> None:
        """Test cpp package_manager is exactly cmake-conan."""
        assert LANGUAGE_CONFIGS["cpp"]["package_manager"] == "cmake-conan"

    # Config Keys Exact Tests
    def test_language_configs_has_exactly_10_languages(self) -> None:
        """Test LANGUAGE_CONFIGS has exactly 10 supported languages."""
        assert len(LANGUAGE_CONFIGS) == 10

    def test_language_configs_contains_python(self) -> None:
        """Test LANGUAGE_CONFIGS contains python key."""
        assert "python" in LANGUAGE_CONFIGS

    def test_language_configs_contains_typescript(self) -> None:
        """Test LANGUAGE_CONFIGS contains typescript key."""
        assert "typescript" in LANGUAGE_CONFIGS

    def test_language_configs_contains_go(self) -> None:
        """Test LANGUAGE_CONFIGS contains go key."""
        assert "go" in LANGUAGE_CONFIGS

    def test_language_configs_contains_rust(self) -> None:
        """Test LANGUAGE_CONFIGS contains rust key."""
        assert "rust" in LANGUAGE_CONFIGS

    def test_language_configs_contains_java(self) -> None:
        """Test LANGUAGE_CONFIGS contains java key."""
        assert "java" in LANGUAGE_CONFIGS

    def test_language_configs_contains_csharp(self) -> None:
        """Test LANGUAGE_CONFIGS contains csharp key."""
        assert "csharp" in LANGUAGE_CONFIGS

    def test_language_configs_contains_ruby(self) -> None:
        """Test LANGUAGE_CONFIGS contains ruby key."""
        assert "ruby" in LANGUAGE_CONFIGS

    def test_language_configs_contains_swift(self) -> None:
        """Test LANGUAGE_CONFIGS contains swift key."""
        assert "swift" in LANGUAGE_CONFIGS

    def test_language_configs_contains_kotlin(self) -> None:
        """Test LANGUAGE_CONFIGS contains kotlin key."""
        assert "kotlin" in LANGUAGE_CONFIGS

    def test_language_configs_contains_cpp(self) -> None:
        """Test LANGUAGE_CONFIGS contains cpp key."""
        assert "cpp" in LANGUAGE_CONFIGS

    def test_all_configs_have_test_framework_key(self) -> None:
        """Test all language configs have test_framework key."""
        for lang, config in LANGUAGE_CONFIGS.items():
            assert "test_framework" in config, f"{lang} missing test_framework"

    def test_all_configs_have_linters_key(self) -> None:
        """Test all language configs have linters key."""
        for lang, config in LANGUAGE_CONFIGS.items():
            assert "linters" in config, f"{lang} missing linters"

    def test_all_configs_have_formatters_key(self) -> None:
        """Test all language configs have formatters key."""
        for lang, config in LANGUAGE_CONFIGS.items():
            assert "formatters" in config, f"{lang} missing formatters"

    def test_all_configs_have_security_tools_key(self) -> None:
        """Test all language configs have security_tools key."""
        for lang, config in LANGUAGE_CONFIGS.items():
            assert "security_tools" in config, f"{lang} missing security_tools"

    def test_all_configs_have_supported_versions_key(self) -> None:
        """Test all language configs have supported_versions key."""
        for lang, config in LANGUAGE_CONFIGS.items():
            assert "supported_versions" in config, f"{lang} missing supported_versions"

    def test_all_configs_have_package_manager_key(self) -> None:
        """Test all language configs have package_manager key."""
        for lang, config in LANGUAGE_CONFIGS.items():
            assert "package_manager" in config, f"{lang} missing package_manager"

    def test_all_linters_are_non_empty_lists(self) -> None:
        """Test all linters are non-empty lists."""
        for lang, config in LANGUAGE_CONFIGS.items():
            linters = config["linters"]
            assert isinstance(linters, list), f"{lang} linters not a list"
            assert len(linters) > 0, f"{lang} linters is empty"

    def test_all_formatters_are_non_empty_lists(self) -> None:
        """Test all formatters are non-empty lists."""
        for lang, config in LANGUAGE_CONFIGS.items():
            formatters = config["formatters"]
            assert isinstance(formatters, list), f"{lang} formatters not a list"
            assert len(formatters) > 0, f"{lang} formatters is empty"

    def test_all_security_tools_are_non_empty_lists(self) -> None:
        """Test all security_tools are non-empty lists."""
        for lang, config in LANGUAGE_CONFIGS.items():
            security_tools = config["security_tools"]
            assert isinstance(security_tools, list), f"{lang} security_tools not a list"
            assert len(security_tools) > 0, f"{lang} security_tools is empty"

    def test_all_supported_versions_are_non_empty_lists(self) -> None:
        """Test all supported_versions are non-empty lists."""
        for lang, config in LANGUAGE_CONFIGS.items():
            versions = config["supported_versions"]
            assert isinstance(versions, list), f"{lang} versions not a list"
            assert len(versions) > 0, f"{lang} versions is empty"


class TestCIGeneratorTemplatePath:
    """Tests for the deterministic, no-API template path (Phase 1)."""

    @pytest.mark.parametrize(
        "language",
        ["python", "typescript", "go", "rust", "swift", "kotlin", "cpp", "java"],
    )
    def test_generate_from_template_for_supported_language(self, language: str) -> None:
        """Each canonical language renders without an orchestrator."""
        generator = CIGenerator(language=language)

        workflow = generator.generate_workflow_from_template()

        assert workflow.is_valid
        assert workflow.language == language
        assert workflow.content
        # Reference templates ship a 'quality' job; validation should pass.
        assert "quality" in workflow.content

    def test_generate_workflow_uses_template_when_no_orchestrator(self) -> None:
        """Calling generate_workflow() with no orchestrator picks the template path."""
        generator = CIGenerator(language="python")

        workflow = generator.generate_workflow()

        assert workflow.is_valid
        # Output should match what generate_workflow_from_template returns.
        from_template = generator.generate_workflow_from_template()
        assert workflow.content == from_template.content

    def test_generate_workflow_falls_back_to_ai_when_orchestrator_provided(
        self,
    ) -> None:
        """When an orchestrator is supplied the legacy AI path is taken."""
        # Build a minimal valid workflow YAML for the AI mock to return.
        valid_yaml = (
            "name: Test\n"
            "on: [push]\n"
            "jobs:\n"
            "  quality:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: echo hi\n"
        )
        mock_orchestrator = Mock(spec=AIOrchestrator)
        mock_orchestrator.generate.return_value = GenerationResult(
            content=valid_yaml,
            format="yaml",
            token_usage=TokenUsage(input_tokens=10, output_tokens=20),
            model=ModelConfig.SONNET,
            message_id="msg_test",
        )

        generator = CIGenerator(mock_orchestrator, "python")
        workflow = generator.generate_workflow()

        assert workflow.is_valid
        mock_orchestrator.generate.assert_called_once()

    def test_generate_from_template_raises_for_missing_template(
        self, tmp_path: Path
    ) -> None:
        """Missing reference template raises FileNotFoundError."""
        # Point reference_dir at an empty directory.
        generator = CIGenerator(
            language="python",
            reference_dir=tmp_path,
        )

        with pytest.raises(FileNotFoundError, match="reference CI template"):
            generator.generate_workflow_from_template()

    def test_project_name_substituted_into_template(self, tmp_path: Path) -> None:
        """A ``<<% project_name %>>`` placeholder renders with the real value."""
        # Build a synthetic reference template that *does* use the
        # placeholder. The real reference YAMLs do not yet (intentional —
        # the API is forward-looking); this fixture proves the wiring
        # works the moment a maintainer adds it.
        reference_dir = tmp_path / "ref"
        reference_dir.mkdir()
        (reference_dir / "python.yml").write_text(
            "name: CI for <<% project_name %>>\n"
            "on: [push]\n"
            "jobs:\n"
            "  quality:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: echo <<% project_name %>>\n",
            encoding="utf-8",
        )

        generator = CIGenerator(
            language="python",
            reference_dir=reference_dir,
            project_name="my-cool-app",
        )
        workflow = generator.generate_workflow()

        assert workflow.is_valid
        assert "name: CI for my-cool-app" in workflow.content
        assert "echo my-cool-app" in workflow.content
        # The placeholder must be fully substituted.
        assert "<<% project_name %>>" not in workflow.content

    def test_project_name_none_renders_empty_string(self, tmp_path: Path) -> None:
        """``project_name=None`` coerces to ``""`` rather than the string "None"."""
        reference_dir = tmp_path / "ref"
        reference_dir.mkdir()
        (reference_dir / "python.yml").write_text(
            "name: CI<<% project_name %>>\n"
            "on: [push]\n"
            "jobs:\n"
            "  quality:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: echo hi\n",
            encoding="utf-8",
        )

        generator = CIGenerator(
            language="python",
            reference_dir=reference_dir,
        )
        workflow = generator.generate_workflow_from_template()

        assert workflow.is_valid
        # ``None`` would have produced "name: CINone" — that's the bug
        # the StrictUndefined+coercion change fixed.
        assert "None" not in workflow.content
        assert "name: CI\n" in workflow.content

    def test_undeclared_placeholder_raises_strict_undefined(
        self, tmp_path: Path
    ) -> None:
        """Adding a new placeholder without wiring it raises at render time."""
        reference_dir = tmp_path / "ref"
        reference_dir.mkdir()
        (reference_dir / "python.yml").write_text(
            "name: CI <<% missing_var %>>\n"
            "jobs:\n  quality:\n    runs-on: ubuntu-latest\n"
            "    steps:\n      - run: echo hi\n",
            encoding="utf-8",
        )

        generator = CIGenerator(language="python", reference_dir=reference_dir)
        with pytest.raises(UndefinedError):
            generator.generate_workflow_from_template()


class TestSwiftReferenceTemplate:
    """Tests for the Swift reference CI workflow (Issue #353).

    The Swift scaffold is a SwiftUI + WatchKit watchOS app package, so
    every assertion here reflects what can actually run: SwiftUI only
    ships in Apple SDKs (macOS runners), `swift test` covers the SPM
    path, and xcodebuild covers the watchOS-simulator path.
    """

    @pytest.fixture
    def swift_workflow(self) -> CIWorkflow:
        """Render the deterministic Swift reference workflow."""
        return CIGenerator(language="swift").generate_workflow_from_template()

    def test_workflow_is_valid_yaml(self, swift_workflow: CIWorkflow) -> None:
        """Rendered workflow parses with yaml.safe_load and validates."""
        parsed = yaml.safe_load(swift_workflow.content)
        assert swift_workflow.is_valid
        assert isinstance(parsed, dict)
        assert parsed["name"] == "Swift Quality Checks"

    def test_workflow_has_quality_test_and_watchos_jobs(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """Workflow declares the quality, test, and watchos jobs."""
        parsed = yaml.safe_load(swift_workflow.content)
        assert set(parsed["jobs"]) == {"quality", "test", "watchos"}

    def test_all_jobs_run_on_macos(self, swift_workflow: CIWorkflow) -> None:
        """Every job runs on macOS: SwiftUI cannot compile on Linux."""
        parsed = yaml.safe_load(swift_workflow.content)
        for name, job in parsed["jobs"].items():
            assert job["runs-on"] == "macos-latest", f"{name} must run on macOS"

    def test_watchos_job_guards_against_null_discovery(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """Scheme/UDID discovery fails loudly instead of passing null on.

        jq emits the string "null" when no Apple Watch simulator (or no
        scheme) matches; without guards that value reaches
        ``xcodebuild -destination id=null`` as a cryptic late failure,
        and unvalidated writes to GITHUB_ENV are the documented Actions
        env-injection vector. The UDID must look like a simulator UUID.
        """
        content = swift_workflow.content
        assert "No Apple Watch simulator found" in content
        assert "No xcodebuild scheme found" in content
        assert "^[0-9A-Fa-f-]{36}$" in content
        # The scheme is character-class validated like the UDID...
        assert "^[A-Za-z0-9._ -]+$" in content
        # ...and discovery accepts both xcodebuild -list -json shapes
        # (.workspace for app packages, .project for plain projects).
        assert ".workspace.schemes // .project.schemes" in content

    def test_coverage_gate_does_not_rerun_swift_test(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """The coverage gate locates the codecov JSON without re-testing.

        ``swift test --show-codecov-path`` re-runs the entire suite (it
        is not a pure query), doubling CI time and decoupling measured
        coverage from the displayed test results, so the gate must find
        the export JSON from the single coverage run instead.
        """
        content = swift_workflow.content
        assert "--show-codecov-path" not in content
        assert "find .build" in content
        assert "*/codecov/*" in content

    def test_version_matrix_does_not_fail_fast(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """Matrix legs run to completion so every failing version is seen."""
        parsed = yaml.safe_load(swift_workflow.content)
        assert parsed["jobs"]["test"]["strategy"]["fail-fast"] is False

    def test_version_matrix_covers_swift_59_510_60(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """The test job matrixes over Swift 5.9, 5.10, and 6.0."""
        parsed = yaml.safe_load(swift_workflow.content)
        matrix = parsed["jobs"]["test"]["strategy"]["matrix"]
        assert matrix["swift-version"] == ["5.9", "5.10", "6.0"]

    def test_version_matrix_uses_pinned_setup_swift_action(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """setup-swift is pinned to a major version like other setup actions."""
        assert "swift-actions/setup-swift@v2" in swift_workflow.content

    def test_quality_job_enforces_coverage_threshold(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """Coverage gate parses the same llvm-cov JSON as scripts/test.sh."""
        assert "swift test --enable-code-coverage" in swift_workflow.content
        # Same data source as the generated scripts/test.sh --coverage
        # (the export JSON from the single coverage run)...
        assert "*/codecov/*" in swift_workflow.content
        # ...and the same 90% line-coverage threshold.
        assert '["data"][0]["totals"]["lines"]["percent"]' in swift_workflow.content
        assert 'python3 - "$CODECOV_JSON" 90' in swift_workflow.content

    def test_quality_job_mirrors_precommit_lint_and_format_hooks(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """CI runs the same SwiftLint/swift-format checks as pre-commit."""
        # Check-mode counterpart of the `swift-format format --in-place`
        # pre-commit hook (identical to scripts/format.sh --check).
        assert "swift-format lint --strict --recursive Sources Tests" in (
            swift_workflow.content
        )
        # Same invocation as the SwiftLint pre-commit hook; reads the
        # generated .swiftlint.yml (complexity <= 10 + security rules).
        assert "swiftlint lint --strict" in swift_workflow.content

    def test_quality_job_runs_gitleaks_secret_scan(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """CI runs the gitleaks secret scan listed in security_tools."""
        assert "gitleaks detect" in swift_workflow.content

    def test_watchos_job_builds_for_watchos_simulator(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """The watchos job builds via xcodebuild for the watchOS simulator."""
        assert "generic/platform=watchOS Simulator" in swift_workflow.content

    def test_watchos_job_runs_tests_on_watchos_simulator(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """The watchos job runs XCTest on a concrete simulator device."""
        assert "xcodebuild test" in swift_workflow.content
        # Devices are matched by UDID (simctl discovery): name/OS matching
        # breaks when the runner image's runtimes drift from the Xcode SDK.
        assert "xcrun simctl list devices available --json" in swift_workflow.content
        assert "id=$UDID" in swift_workflow.content

    def test_watchos_job_discovers_scheme_dynamically(
        self, swift_workflow: CIWorkflow
    ) -> None:
        """The xcodebuild scheme is discovered, not hardcoded."""
        assert "xcodebuild -list -json" in swift_workflow.content
        # The old stub hardcoded a placeholder scheme that could never exist.
        assert "YourScheme" not in swift_workflow.content


def _all_run_commands(parsed_workflow: dict[str, Any]) -> list[str]:
    """Collect every step ``run`` command across all workflow jobs.

    Parsing (instead of scanning raw content) lets assertions target the
    commands that actually execute while YAML comments stay free to
    document decisions honestly — the PR #414 review noted raw string
    assertions are brittle exactly because they cannot tell the two
    apart.

    Args:
        parsed_workflow: ``yaml.safe_load`` result for a workflow.

    Returns:
        Every non-empty ``run`` value, in job/step order.
    """
    return [
        step["run"]
        for job in parsed_workflow["jobs"].values()
        for step in job["steps"]
        if step.get("run")
    ]


class TestKotlinReferenceTemplate:
    """Tests for the Kotlin reference CI workflow (Issue #358).

    The Kotlin scaffold is a Jetpack Compose for Wear OS Android app
    built with Gradle (Kotlin DSL), so every assertion reflects what can
    actually run: Android/JVM builds work on GitHub's ubuntu runners
    (Android SDK and Temurin JDKs preinstalled, no macOS needed unlike
    Swift), the scaffold deliberately ships no Gradle wrapper binary,
    and the >=90% coverage bound lives in the generated
    app/build.gradle.kts Kover block — not in the workflow.
    """

    @pytest.fixture
    def kotlin_workflow(self) -> CIWorkflow:
        """Render the deterministic Kotlin reference workflow."""
        return CIGenerator(language="kotlin").generate_workflow_from_template()

    def test_workflow_is_valid_yaml(self, kotlin_workflow: CIWorkflow) -> None:
        """Rendered workflow parses with yaml.safe_load and validates."""
        parsed = yaml.safe_load(kotlin_workflow.content)
        assert kotlin_workflow.is_valid
        assert isinstance(parsed, dict)
        assert parsed["name"] == "Kotlin Quality Checks"

    def test_workflow_has_quality_test_and_wear_jobs(
        self, kotlin_workflow: CIWorkflow
    ) -> None:
        """Workflow declares the quality, test, and wear jobs."""
        parsed = yaml.safe_load(kotlin_workflow.content)
        assert set(parsed["jobs"]) == {"quality", "test", "wear"}

    def test_all_jobs_run_on_ubuntu(self, kotlin_workflow: CIWorkflow) -> None:
        """Every job runs on ubuntu: Android/JVM builds need no macOS."""
        parsed = yaml.safe_load(kotlin_workflow.content)
        for name, job in parsed["jobs"].items():
            assert job["runs-on"] == "ubuntu-latest", f"{name} must run on ubuntu"

    def test_jdk_matrix_does_not_fail_fast(self, kotlin_workflow: CIWorkflow) -> None:
        """Matrix legs run to completion so every failing JDK is seen."""
        parsed = yaml.safe_load(kotlin_workflow.content)
        assert parsed["jobs"]["test"]["strategy"]["fail-fast"] is False

    def test_jdk_matrix_matches_language_config_versions(
        self, kotlin_workflow: CIWorkflow
    ) -> None:
        """The test job matrixes over the LANGUAGE_CONFIGS JDK versions."""
        parsed = yaml.safe_load(kotlin_workflow.content)
        matrix = parsed["jobs"]["test"]["strategy"]["matrix"]
        assert matrix["java-version"] == (
            LANGUAGE_CONFIGS["kotlin"]["supported_versions"]
        )

    def test_setup_actions_are_pinned_to_majors(
        self, kotlin_workflow: CIWorkflow
    ) -> None:
        """checkout, setup-java, and setup-gradle are pinned majors."""
        content = kotlin_workflow.content
        assert "actions/checkout@v4" in content
        assert "actions/setup-java@v4" in content
        assert "gradle/actions/setup-gradle@v4" in content

    def test_workflow_provisions_gradle_instead_of_missing_wrapper(
        self, kotlin_workflow: CIWorkflow
    ) -> None:
        """CI never invokes the wrapper the scaffold deliberately omits.

        The generator never writes binary artifacts, so gradlew and
        gradle-wrapper.jar do not exist in a fresh project; any
        ``./gradlew`` (or ``chmod +x gradlew``) step would fail on the
        first run. setup-gradle provisions a pinned Gradle matching
        utils/kotlin.GRADLE_WRAPPER_VERSION (the version the scaffold
        README tells users to materialise) and steps call ``gradle``.
        Assertions parse the workflow so YAML comments may still
        document the wrapper situation honestly.
        """
        parsed = yaml.safe_load(kotlin_workflow.content)
        run_commands = _all_run_commands(parsed)
        # Covers both `./gradlew ...` invocations and the old stub's
        # `chmod +x gradlew` step.
        assert not any("gradlew" in cmd for cmd in run_commands)
        assert parsed["env"]["GRADLE_VERSION"] == GRADLE_WRAPPER_VERSION
        gradle_setups = [
            step
            for job in parsed["jobs"].values()
            for step in job["steps"]
            if "setup-gradle" in step.get("uses", "")
        ]
        assert gradle_setups
        for step in gradle_setups:
            assert step["with"]["gradle-version"] == "${{ env.GRADLE_VERSION }}"

    def test_coverage_gate_runs_kover_once_without_duplicating_bound(
        self, kotlin_workflow: CIWorkflow
    ) -> None:
        """One Gradle invocation gates coverage; the bound stays in Gradle.

        koverXmlReportDebug and koverVerifyDebug share a single
        testDebugUnitTest execution inside one task graph (the Swift
        PR #414 no-double-test-run lesson), and the >=90% bound lives
        only in app/build.gradle.kts (kover { ... minBound(90) }) so the
        threshold can never drift between the manifest and the workflow.
        Run commands are parsed so comments may reference the bound.
        """
        parsed = yaml.safe_load(kotlin_workflow.content)
        run_commands = _all_run_commands(parsed)
        assert any(
            cmd.strip() == "gradle koverXmlReportDebug koverVerifyDebug"
            for cmd in run_commands
        )
        assert not any("minBound" in cmd for cmd in run_commands)
        assert not any("90" in cmd for cmd in run_commands)

    def test_quality_job_does_not_rerun_the_test_suite(
        self, kotlin_workflow: CIWorkflow
    ) -> None:
        """No standalone test step duplicates the Kover coverage run."""
        parsed = yaml.safe_load(kotlin_workflow.content)
        run_commands = [
            step.get("run", "") for step in parsed["jobs"]["quality"]["steps"]
        ]
        kover_runs = [cmd for cmd in run_commands if "koverVerifyDebug" in cmd]
        assert len(kover_runs) == 1
        assert not any(cmd.strip() == "gradle test" for cmd in run_commands)

    def test_quality_job_mirrors_precommit_lint_and_format_hooks(
        self, kotlin_workflow: CIWorkflow
    ) -> None:
        """CI runs the same ktlint/detekt checks as pre-commit."""
        parsed = yaml.safe_load(kotlin_workflow.content)
        run_commands = [
            step.get("run", "") for step in parsed["jobs"]["quality"]["steps"]
        ]
        # Check-mode counterpart of the `ktlint --format` pre-commit hook
        # (identical to scripts/format.sh without --fix).
        assert any(cmd.strip() == "ktlint" for cmd in run_commands)
        # Same invocation as the detekt pre-commit hook and scripts/lint.sh:
        # the shared detekt.yml on top of detekt's default config.
        assert (
            "detekt --config detekt.yml --build-upon-default-config"
            in kotlin_workflow.content
        )
        assert "--excludes '**/build/**'" in kotlin_workflow.content

    def test_quality_job_runs_gitleaks_secret_scan(
        self, kotlin_workflow: CIWorkflow
    ) -> None:
        """CI runs gitleaks at the same version pre-commit pins."""
        content = kotlin_workflow.content
        assert "gitleaks detect" in content
        # Parity with the rev pinned in the generated .pre-commit-config
        # (https://github.com/gitleaks/gitleaks rev v8.18.4).
        assert 'GITLEAKS_VERSION: "8.18.4"' in content

    def test_quality_tools_are_version_pinned_downloads(
        self, kotlin_workflow: CIWorkflow
    ) -> None:
        """ktlint/detekt come from pinned GitHub release downloads.

        Homebrew (the documented local install path) was removed from
        GitHub's Ubuntu runner images, so the workflow fetches pinned
        release binaries instead — deterministically, never "latest".
        """
        content = kotlin_workflow.content
        assert "KTLINT_VERSION" in content
        assert "DETEKT_VERSION" in content
        assert "releases/download" in content
        assert "releases/latest" not in content
        assert "brew install" not in content

    def test_wear_job_assembles_debug_apk_without_emulator(
        self, kotlin_workflow: CIWorkflow
    ) -> None:
        """The wear job builds the Wear OS APK; no emulator steps exist.

        The scaffold generates no androidTest source set, so an emulator
        job would have nothing to execute; assembleDebug is the honest
        deterministic proof the Wear OS target builds. The emulator
        stance is documented in YAML comments, not dead steps.
        """
        parsed = yaml.safe_load(kotlin_workflow.content)
        wear_commands = [
            step.get("run", "") for step in parsed["jobs"]["wear"]["steps"]
        ]
        assert any("gradle assembleDebug" in cmd for cmd in wear_commands)
        uses = [
            step.get("uses", "")
            for job in parsed["jobs"].values()
            for step in job["steps"]
        ]
        assert not any("emulator" in action for action in uses)

    def test_workflow_writes_nothing_to_github_env(
        self, kotlin_workflow: CIWorkflow
    ) -> None:
        """Nothing discovered at runtime is exported to GITHUB_ENV.

        The Swift PR #414 review flagged unvalidated GITHUB_ENV writes
        as the documented Actions env-injection vector. The Kotlin
        workflow sidesteps the vector entirely: every value (versions,
        tasks, paths) is a static literal, so there is no dynamic
        discovery and no GITHUB_ENV/GITHUB_PATH write to guard. Run
        commands are parsed so comments may explain that decision.
        """
        parsed = yaml.safe_load(kotlin_workflow.content)
        run_commands = _all_run_commands(parsed)
        assert not any("GITHUB_ENV" in cmd for cmd in run_commands)
        assert not any("GITHUB_PATH" in cmd for cmd in run_commands)


class TestCppReferenceTemplate:
    """Tests for the C/C++ reference CI workflow (Issue #363).

    The cpp scaffold is a Tizen native watch app whose CMake/Conan build
    deliberately covers ONLY the pure-logic library and its Catch2 tests
    (the #361 two-build split): src/main.cpp needs the Tizen native SDK
    and .tpk packaging is the Tizen Studio CLI's job — a manual,
    login-gated GUI installer no GitHub-hosted runner can provision.
    Every assertion therefore reflects what can actually run on a plain
    ubuntu runner, and the packaging gap is documented in YAML comments
    rather than emitted as steps that can never pass (the Kotlin
    no-emulator / Swift Periphery precedent).
    """

    @pytest.fixture
    def cpp_workflow(self) -> CIWorkflow:
        """Render the deterministic C/C++ reference workflow."""
        return CIGenerator(language="cpp").generate_workflow_from_template()

    def test_workflow_is_valid_yaml(self, cpp_workflow: CIWorkflow) -> None:
        """Rendered workflow parses with yaml.safe_load and validates."""
        parsed = yaml.safe_load(cpp_workflow.content)
        assert cpp_workflow.is_valid
        assert isinstance(parsed, dict)
        assert parsed["name"] == "C/C++ Quality Checks"

    def test_workflow_has_quality_and_test_jobs(self, cpp_workflow: CIWorkflow) -> None:
        """Workflow declares exactly the quality and test jobs."""
        parsed = yaml.safe_load(cpp_workflow.content)
        assert set(parsed["jobs"]) == {"quality", "test"}

    def test_all_jobs_run_on_pinned_ubuntu(self, cpp_workflow: CIWorkflow) -> None:
        """Every job pins ubuntu-24.04, not ubuntu-latest.

        Noble's default apt clang tooling is LLVM 18, matching the
        mirrors-clang-format v18.1.8 rev pinned in the generated
        .pre-commit-config.yaml — a floating ubuntu-latest could silently
        change the clang-format/clang-tidy major and break that parity.
        """
        parsed = yaml.safe_load(cpp_workflow.content)
        for name, job in parsed["jobs"].items():
            assert job["runs-on"] == "ubuntu-24.04", f"{name} must pin ubuntu-24.04"

    def test_compiler_matrix_does_not_fail_fast(self, cpp_workflow: CIWorkflow) -> None:
        """Matrix legs run to completion so every failing compiler is seen."""
        parsed = yaml.safe_load(cpp_workflow.content)
        assert parsed["jobs"]["test"]["strategy"]["fail-fast"] is False

    def test_compiler_matrix_matches_language_config_versions(
        self, cpp_workflow: CIWorkflow
    ) -> None:
        """The test job matrixes over the LANGUAGE_CONFIGS compilers."""
        parsed = yaml.safe_load(cpp_workflow.content)
        matrix = parsed["jobs"]["test"]["strategy"]["matrix"]
        assert matrix["compiler"] == LANGUAGE_CONFIGS["cpp"]["supported_versions"]

    def test_compiler_matrix_maps_cc_and_cxx_pairs(
        self, cpp_workflow: CIWorkflow
    ) -> None:
        """Each matrix leg carries a consistent CC/CXX toolchain pair.

        Both Conan (profile detect honors $CC/$CXX) and CMake read these,
        so the whole leg — dependency build included — really uses the
        matrix compiler instead of silently falling back to the default.
        """
        parsed = yaml.safe_load(cpp_workflow.content)
        include = parsed["jobs"]["test"]["strategy"]["matrix"]["include"]
        pairs = {entry["compiler"]: (entry["cc"], entry["cxx"]) for entry in include}
        assert pairs == {"gcc": ("gcc", "g++"), "clang": ("clang", "clang++")}
        env = parsed["jobs"]["test"]["env"]
        assert env["CC"] == "${{ matrix.cc }}"
        assert env["CXX"] == "${{ matrix.cxx }}"

    def test_checkout_action_is_pinned_to_major(self, cpp_workflow: CIWorkflow) -> None:
        """actions/checkout is pinned to a major version."""
        assert "actions/checkout@v4" in cpp_workflow.content

    def test_quality_job_runs_generated_scripts_for_parity(
        self, cpp_workflow: CIWorkflow
    ) -> None:
        """CI runs the generated scripts instead of reimplementing them.

        format.sh --check, lint.sh, test.sh --coverage, and security.sh
        are the same gates check-all.sh chains locally — one source of
        truth, so CI can never drift from the pre-commit/scripts parity
        the #362 review demanded.
        """
        parsed = yaml.safe_load(cpp_workflow.content)
        quality_commands = [
            step.get("run", "") for step in parsed["jobs"]["quality"]["steps"]
        ]
        assert any(
            cmd.strip() == "./scripts/format.sh --check" for cmd in quality_commands
        )
        assert any(cmd.strip() == "./scripts/lint.sh" for cmd in quality_commands)
        assert any(cmd.strip() == "./scripts/security.sh" for cmd in quality_commands)

    def test_coverage_gate_delegates_to_test_script_once(
        self, cpp_workflow: CIWorkflow
    ) -> None:
        """One test.sh --coverage run gates coverage; the bound stays there.

        scripts/test.sh is the single home of the >=90% line bound (CMake
        has no canonical manifest slot for a coverage threshold), and it
        runs ctest exactly once with instrumentation — no second
        uninstrumented test step duplicates the suite in the quality job
        (the Swift PR #414 no-double-test-run lesson). Run commands are
        parsed so comments may reference the bound.
        """
        parsed = yaml.safe_load(cpp_workflow.content)
        run_commands = _all_run_commands(parsed)
        coverage_runs = [
            cmd for cmd in run_commands if "./scripts/test.sh --coverage" in cmd
        ]
        assert len(coverage_runs) == 1
        quality_commands = [
            step.get("run", "") for step in parsed["jobs"]["quality"]["steps"]
        ]
        assert not any("ctest" in cmd for cmd in quality_commands)
        assert not any("90" in cmd for cmd in run_commands)

    def test_quality_job_runs_gitleaks_at_precommit_pin(
        self, cpp_workflow: CIWorkflow
    ) -> None:
        """CI runs gitleaks at the same version pre-commit pins."""
        content = cpp_workflow.content
        assert "gitleaks detect" in content
        # Parity with the rev pinned in the generated .pre-commit-config
        # (https://github.com/gitleaks/gitleaks rev v8.18.4).
        assert 'GITLEAKS_VERSION: "8.18.4"' in content

    def test_quality_tools_are_version_pinned(self, cpp_workflow: CIWorkflow) -> None:
        """conan/lizard/flawfinder/gitleaks are pinned, never floating.

        Homebrew was removed from GitHub's Ubuntu runner images (the
        Kotlin #421 lesson), so Python CLI tools install via pipx at
        pinned versions and gitleaks comes from a pinned GitHub release
        artifact — deterministically, never "latest".
        """
        content = cpp_workflow.content
        assert "CONAN_VERSION" in content
        assert "LIZARD_VERSION" in content
        assert "FLAWFINDER_VERSION" in content
        assert "releases/download" in content
        assert "releases/latest" not in content
        assert "brew install" not in content

    def test_test_job_builds_and_runs_ctest_without_coverage(
        self, cpp_workflow: CIWorkflow
    ) -> None:
        """Matrix legs build and run plain ctest; coverage stays in quality.

        The test job's axis is compiler compatibility — rerunning the
        instrumented suite here would just duplicate the quality job's
        single coverage measurement.
        """
        parsed = yaml.safe_load(cpp_workflow.content)
        test_commands = [
            step.get("run", "") for step in parsed["jobs"]["test"]["steps"]
        ]
        assert any("cmake --build build" in cmd for cmd in test_commands)
        assert any(
            "ctest --test-dir build --output-on-failure" in cmd for cmd in test_commands
        )
        assert not any("--coverage" in cmd for cmd in test_commands)
        assert not any("lcov" in cmd for cmd in test_commands)

    def test_configure_uses_documented_build_dir_convention(
        self, cpp_workflow: CIWorkflow
    ) -> None:
        """Both jobs configure with the scaffold-wide `cmake -B build` flow.

        The build/ directory name is load-bearing: the clang-tidy
        pre-commit hook, scripts/lint.sh (-p build), and scripts/test.sh
        all assume it, and the CMakeLists.txt header documents the exact
        conan install + cmake configure invocation CI replays here.
        """
        parsed = yaml.safe_load(cpp_workflow.content)
        for job_name in ("quality", "test"):
            commands = [
                step.get("run", "") for step in parsed["jobs"][job_name]["steps"]
            ]
            configure = [cmd for cmd in commands if "conan install" in cmd]
            assert len(configure) == 1, f"{job_name} must configure exactly once"
            assert "conan profile detect --force" in configure[0]
            assert "conan install . --output-folder=build --build=missing" in (
                configure[0]
            )
            assert "cmake -B build -S ." in configure[0]
            assert "-DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake" in configure[0]

    def test_tizen_packaging_documented_not_stubbed(
        self, cpp_workflow: CIWorkflow
    ) -> None:
        """The .tpk packaging gap is YAML comments, not dead steps.

        Tizen Studio is a manual, login-gated GUI installer with no
        headless install path, so no runner can provision it — the
        workflow documents that honestly instead of emitting `tizen
        build-native` steps that can never pass.
        """
        content = cpp_workflow.content
        assert "Tizen Studio" in content
        parsed = yaml.safe_load(content)
        run_commands = _all_run_commands(parsed)
        assert not any("tizen" in cmd for cmd in run_commands)
        assert not any(".tpk" in cmd for cmd in run_commands)

    def test_workflow_writes_nothing_to_github_env(
        self, cpp_workflow: CIWorkflow
    ) -> None:
        """Nothing discovered at runtime is exported to GITHUB_ENV.

        The Swift PR #414 review flagged unvalidated GITHUB_ENV writes as
        the documented Actions env-injection vector; like the Kotlin
        workflow, this one sidesteps the vector entirely — every value is
        a static literal, so there is no dynamic discovery and no
        GITHUB_ENV/GITHUB_PATH write to guard.
        """
        parsed = yaml.safe_load(cpp_workflow.content)
        run_commands = _all_run_commands(parsed)
        assert not any("GITHUB_ENV" in cmd for cmd in run_commands)
        assert not any("GITHUB_PATH" in cmd for cmd in run_commands)


class TestJavaReferenceTemplate:
    """Tests for the Java reference CI workflow (#366/#368).

    The java scaffold is a legacy Android Wear app whose Maven build
    deliberately covers ONLY the pure-logic library and its JUnit 4
    tests (the #366 two-builds split): the APK is Android tooling's job,
    so every assertion reflects what `mvn` can actually run on a plain
    ubuntu runner. The quality gates are the pom-backed Maven goals the
    integration suite cross-checks against the generated pom.
    """

    @pytest.fixture
    def java_workflow(self) -> CIWorkflow:
        """Render the deterministic Java reference workflow."""
        return CIGenerator(language="java").generate_workflow_from_template()

    def test_workflow_is_valid_yaml(self, java_workflow: CIWorkflow) -> None:
        """Rendered workflow parses with yaml.safe_load and validates."""
        parsed = yaml.safe_load(java_workflow.content)
        assert java_workflow.is_valid
        assert isinstance(parsed, dict)
        assert parsed["name"] == "Java Quality Checks"

    def test_workflow_has_quality_and_build_jobs(
        self, java_workflow: CIWorkflow
    ) -> None:
        """Workflow declares exactly the quality and build jobs."""
        parsed = yaml.safe_load(java_workflow.content)
        assert set(parsed["jobs"]) == {"quality", "build"}

    def test_all_jobs_run_on_ubuntu(self, java_workflow: CIWorkflow) -> None:
        """Every job runs on ubuntu: Maven/JVM builds need no macOS."""
        parsed = yaml.safe_load(java_workflow.content)
        for name, job in parsed["jobs"].items():
            assert job["runs-on"] == "ubuntu-latest", f"{name} must run on ubuntu"

    def test_jdk_matrix_covers_the_lts_releases_above_the_pom_target(
        self, java_workflow: CIWorkflow
    ) -> None:
        """The quality job matrixes over JDK 17 and 21.

        utils/java.JAVA_RELEASE pins the pom's --release to 17, so the
        matrix runs the LTS JDKs that can build it (11 from
        LANGUAGE_CONFIGS predates the target and is deliberately
        absent).
        """
        parsed = yaml.safe_load(java_workflow.content)
        matrix = parsed["jobs"]["quality"]["strategy"]["matrix"]
        assert matrix["java-version"] == ["17", "21"]

    def test_setup_actions_are_pinned_to_majors(
        self, java_workflow: CIWorkflow
    ) -> None:
        """checkout and setup-java are pinned majors with Maven caching."""
        content = java_workflow.content
        assert "actions/checkout@v4" in content
        assert "actions/setup-java@v4" in content
        assert "cache: 'maven'" in content

    def test_quality_job_runs_every_pom_backed_gate(
        self, java_workflow: CIWorkflow
    ) -> None:
        """CI runs the checkstyle/pmd/spotbugs/jacoco goals the pom backs.

        The generated pom declares each plugin precisely so these goals
        resolve (test_java_init_integration cross-checks the pom side).
        """
        parsed = yaml.safe_load(java_workflow.content)
        quality_commands = [
            cmd.strip()
            for step in parsed["jobs"]["quality"]["steps"]
            if (cmd := step.get("run"))
        ]
        assert "mvn checkstyle:check" in quality_commands
        assert "mvn pmd:check" in quality_commands
        assert "mvn clean test jacoco:report" in quality_commands
        assert "mvn jacoco:check" in quality_commands

    def test_spotbugs_compiles_before_checking(self, java_workflow: CIWorkflow) -> None:
        """The SpotBugs step compiles first so the scan is not a no-op.

        SpotBugs reads bytecode: a bare `mvn spotbugs:check` silently
        passes when target/classes is empty (the #367 report's gap, the
        PR #430 review's carry-over). The compile must precede the check
        within one invocation, matching the generated pre-commit hook
        and scripts/security.sh.
        """
        parsed = yaml.safe_load(java_workflow.content)
        run_commands = _all_run_commands(parsed)
        spotbugs_runs = [cmd for cmd in run_commands if "spotbugs:check" in cmd]
        assert len(spotbugs_runs) == 1
        command = spotbugs_runs[0]
        assert "compile" in command
        assert command.index("compile") < command.index("spotbugs:check")

    def test_codecov_upload_cannot_fail_ci(self, java_workflow: CIWorkflow) -> None:
        """The tokenless Codecov upload is best-effort, never a gate.

        A fresh project has no CODECOV_TOKEN secret and tokenless
        uploads are rate-limited, so `fail_ci_if_error: true` would make
        generated projects start red (the #366 report's gap). The
        enforced coverage gate is the pom-backed `mvn jacoco:check`
        step instead.
        """
        parsed = yaml.safe_load(java_workflow.content)
        codecov_steps = [
            step
            for job in parsed["jobs"].values()
            for step in job["steps"]
            if "codecov" in step.get("uses", "")
        ]
        assert len(codecov_steps) == 1
        assert codecov_steps[0]["with"]["fail_ci_if_error"] is False

    def test_build_job_packages_without_rerunning_tests(
        self, java_workflow: CIWorkflow
    ) -> None:
        """The build job packages the JAR; the suite ran once in quality.

        -DskipTests keeps the single coverage-gated test execution in
        the quality job (the Swift PR #414 no-double-test-run lesson),
        and a single `mvn clean verify` invocation both builds and
        verifies — verify runs the lifecycle through package, so a
        separate package step would just build twice.
        """
        parsed = yaml.safe_load(java_workflow.content)
        build_commands = [
            step.get("run", "") for step in parsed["jobs"]["build"]["steps"]
        ]
        assert any("mvn clean verify -DskipTests" in cmd for cmd in build_commands)
        assert not any("mvn clean package -DskipTests" in cmd for cmd in build_commands)

    def test_android_packaging_documented_not_stubbed(
        self, java_workflow: CIWorkflow
    ) -> None:
        """No step pretends to build the APK Maven cannot produce."""
        parsed = yaml.safe_load(java_workflow.content)
        run_commands = _all_run_commands(parsed)
        assert not any("gradle" in cmd for cmd in run_commands)
        assert not any("apk" in cmd.lower() for cmd in run_commands)

    def test_workflow_writes_nothing_to_github_env(
        self, java_workflow: CIWorkflow
    ) -> None:
        """Nothing discovered at runtime is exported to GITHUB_ENV.

        The Swift PR #414 review flagged unvalidated GITHUB_ENV writes
        as the documented Actions env-injection vector; like the Kotlin
        and cpp workflows, every value here is a static literal, so
        there is no dynamic discovery and no GITHUB_ENV/GITHUB_PATH
        write to guard.
        """
        parsed = yaml.safe_load(java_workflow.content)
        run_commands = _all_run_commands(parsed)
        assert not any("GITHUB_ENV" in cmd for cmd in run_commands)
        assert not any("GITHUB_PATH" in cmd for cmd in run_commands)


class TestCsharpReferenceTemplate:
    """Tests for the C# reference CI workflow (#370/#371).

    The csharp scaffold is a single-project net8.0 console app whose
    csproj is the single home of the quality policy: Roslyn analyzers
    as errors, the Coverlet >=90% line-coverage bound, and the CA1502
    complexity ceiling. Every assertion here checks that the workflow
    runs thin dotnet invocations against that policy and restates none
    of it — the same manifest-owned shape the Kotlin/Java workflows
    follow.
    """

    @pytest.fixture
    def csharp_workflow(self) -> CIWorkflow:
        """Render the deterministic C# reference workflow."""
        return CIGenerator(language="csharp").generate_workflow_from_template()

    def test_workflow_is_valid_yaml(self, csharp_workflow: CIWorkflow) -> None:
        """Rendered workflow parses with yaml.safe_load and validates."""
        parsed = yaml.safe_load(csharp_workflow.content)
        assert csharp_workflow.is_valid
        assert isinstance(parsed, dict)
        assert parsed["name"] == "C# Quality Checks"

    def test_workflow_has_quality_and_build_jobs(
        self, csharp_workflow: CIWorkflow
    ) -> None:
        """Workflow declares exactly the quality and build jobs."""
        parsed = yaml.safe_load(csharp_workflow.content)
        assert set(parsed["jobs"]) == {"quality", "build"}

    def test_all_jobs_run_on_ubuntu(self, csharp_workflow: CIWorkflow) -> None:
        """Every job runs on ubuntu: the .NET SDK needs no macOS."""
        parsed = yaml.safe_load(csharp_workflow.content)
        for name, job in parsed["jobs"].items():
            assert job["runs-on"] == "ubuntu-latest", f"{name} must run on ubuntu"

    def test_sdk_matrix_pins_the_line_that_builds_net8(
        self, csharp_workflow: CIWorkflow
    ) -> None:
        """The quality job matrixes over exactly the 8.0 SDK line.

        The generated csproj targets net8.0, which older SDKs cannot
        build (the 7.0 matrix entry was dropped for that reason); the
        matrix extends together with the TargetFramework.
        """
        parsed = yaml.safe_load(csharp_workflow.content)
        matrix = parsed["jobs"]["quality"]["strategy"]["matrix"]
        assert matrix["dotnet-version"] == ["8.0"]

    def test_setup_actions_are_pinned_to_majors(
        self, csharp_workflow: CIWorkflow
    ) -> None:
        """checkout and setup-dotnet are pinned to major versions."""
        content = csharp_workflow.content
        assert "actions/checkout@v4" in content
        assert "actions/setup-dotnet@v4" in content

    def test_quality_job_runs_every_csproj_backed_gate(
        self, csharp_workflow: CIWorkflow
    ) -> None:
        """CI runs the restore/build/format/test gates the csproj backs.

        The plain build doubles as the lint gate (the csproj treats
        analyzer warnings as errors), and the coverage-collecting test
        run reuses its output via --no-build so the suite executes
        exactly once (the Swift no-double-test-run lesson).
        """
        parsed = yaml.safe_load(csharp_workflow.content)
        quality_commands = [
            cmd.strip()
            for step in parsed["jobs"]["quality"]["steps"]
            if (cmd := step.get("run"))
        ]
        assert "dotnet restore" in quality_commands
        assert "dotnet build --no-restore" in quality_commands
        assert "dotnet format --verify-no-changes" in quality_commands
        test_runs = [c for c in quality_commands if c.startswith("dotnet test")]
        assert len(test_runs) == 1
        assert "--no-build" in test_runs[0]
        assert "/p:CollectCoverage=true" in test_runs[0]

    def test_coverage_step_defers_the_bound_to_the_csproj(
        self, csharp_workflow: CIWorkflow
    ) -> None:
        """No run command restates the Coverlet coverage threshold.

        The >=90% bound lives in the csproj
        (Threshold/ThresholdType/ThresholdStat — its single home);
        /p:CollectCoverage=true activates the gate without duplicating
        the number, so the workflow cannot drift from the manifest.
        """
        parsed = yaml.safe_load(csharp_workflow.content)
        run_commands = _all_run_commands(parsed)
        assert not any("Threshold" in cmd for cmd in run_commands)

    def test_codecov_upload_cannot_fail_ci(self, csharp_workflow: CIWorkflow) -> None:
        """The tokenless Codecov upload is best-effort, never a gate.

        A fresh project has no CODECOV_TOKEN secret, so a failing
        upload must not start the project red; the enforced coverage
        gate is the csproj-backed Coverlet run in the test step.
        """
        parsed = yaml.safe_load(csharp_workflow.content)
        codecov_steps = [
            step
            for job in parsed["jobs"].values()
            for step in job["steps"]
            if "codecov" in step.get("uses", "")
        ]
        assert len(codecov_steps) == 1
        assert codecov_steps[0]["with"]["fail_ci_if_error"] is False

    def test_build_job_packages_without_rerunning_tests(
        self, csharp_workflow: CIWorkflow
    ) -> None:
        """The build job publishes the app; the suite ran once in quality.

        The Release build feeds dotnet publish via --no-build, and no
        dotnet test invocation appears — the single coverage-gated test
        execution lives in the quality job.
        """
        parsed = yaml.safe_load(csharp_workflow.content)
        build_commands = [
            step.get("run", "") for step in parsed["jobs"]["build"]["steps"]
        ]
        publish_runs = [c for c in build_commands if "dotnet publish" in c]
        assert len(publish_runs) == 1
        assert "--no-build" in publish_runs[0]
        assert not any("dotnet test" in c for c in build_commands)

    def test_workflow_writes_nothing_to_github_env(
        self, csharp_workflow: CIWorkflow
    ) -> None:
        """Nothing discovered at runtime is exported to GITHUB_ENV.

        The Swift PR #414 review flagged unvalidated GITHUB_ENV writes
        as the documented Actions env-injection vector; like the
        Kotlin, cpp, and java workflows, every value here is a static
        literal, so there is no dynamic discovery and no
        GITHUB_ENV/GITHUB_PATH write to guard.
        """
        parsed = yaml.safe_load(csharp_workflow.content)
        run_commands = _all_run_commands(parsed)
        assert not any("GITHUB_ENV" in cmd for cmd in run_commands)
        assert not any("GITHUB_PATH" in cmd for cmd in run_commands)
