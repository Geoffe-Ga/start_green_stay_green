"""Unit tests for BaseGenerator.

Tests the base generator class that all generators inherit from.
"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from start_green_stay_green.generators.base import AIGenerationError
from start_green_stay_green.generators.base import BaseGenerator
from start_green_stay_green.generators.base import GenerationError
from start_green_stay_green.generators.base import TemplateBasedGenerator


class ConcreteGenerator(BaseGenerator):
    """Concrete implementation of BaseGenerator for testing."""

    def __init__(self, orchestrator: Any | None = None) -> None:
        """Initialize concrete generator.

        Args:
            orchestrator: Optional orchestrator for testing.
        """
        self.orchestrator = orchestrator

    def generate(self) -> dict[str, Any]:
        """Concrete implementation of abstract generate method.

        Returns:
            Empty dictionary for testing.
        """
        return {}


class ConcreteTemplateGenerator(TemplateBasedGenerator):
    """Concrete implementation of TemplateBasedGenerator for testing."""

    def generate(self) -> dict[str, Any]:
        """Concrete implementation of abstract generate method.

        Returns:
            Empty dictionary for testing.
        """
        return {}


class TestBaseGeneratorInitialization:
    """Test BaseGenerator initialization."""

    def test_init_stores_orchestrator(self) -> None:
        """Test __init__ stores orchestrator as instance attribute."""
        mock_orchestrator = Mock()
        generator = ConcreteGenerator(mock_orchestrator)

        assert generator.orchestrator is mock_orchestrator

    def test_orchestrator_attribute_exact_reference(self) -> None:
        """Test orchestrator attribute is exactly the provided object."""
        mock_orchestrator_1 = Mock(name="orchestrator_1")
        mock_orchestrator_2 = Mock(name="orchestrator_2")

        generator_1 = ConcreteGenerator(mock_orchestrator_1)
        generator_2 = ConcreteGenerator(mock_orchestrator_2)

        assert generator_1.orchestrator is mock_orchestrator_1
        assert generator_1.orchestrator is not mock_orchestrator_2
        assert generator_2.orchestrator is mock_orchestrator_2
        assert generator_2.orchestrator is not mock_orchestrator_1

    def test_orchestrator_can_be_none(self) -> None:
        """Test orchestrator can be None."""
        generator = ConcreteGenerator(None)
        assert generator.orchestrator is None

    def test_multiple_instances_have_independent_orchestrators(self) -> None:
        """Test multiple generator instances have independent orchestrators."""
        orchestrator_1 = Mock(name="orchestrator_1")
        orchestrator_2 = Mock(name="orchestrator_2")
        orchestrator_3 = Mock(name="orchestrator_3")

        gen1 = ConcreteGenerator(orchestrator_1)
        gen2 = ConcreteGenerator(orchestrator_2)
        gen3 = ConcreteGenerator(orchestrator_3)

        assert gen1.orchestrator is not gen2.orchestrator
        assert gen1.orchestrator is not gen3.orchestrator
        assert gen2.orchestrator is not gen3.orchestrator

        assert gen1.orchestrator is orchestrator_1
        assert gen2.orchestrator is orchestrator_2
        assert gen3.orchestrator is orchestrator_3


class TestBaseGeneratorAbstract:
    """Test BaseGenerator abstract method."""

    def test_cannot_instantiate_base_generator_directly(self) -> None:
        """Test BaseGenerator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseGenerator()  # type: ignore[abstract]

    def test_concrete_implementation_required(self) -> None:
        """Test concrete subclass must implement generate method."""

        class IncompleteGenerator(BaseGenerator):
            """Generator without generate implementation."""

        with pytest.raises(TypeError):
            IncompleteGenerator()  # type: ignore[abstract]

    def test_concrete_implementation_works(self) -> None:
        """Test concrete subclass with generate method works."""
        generator = ConcreteGenerator(Mock())

        result = generator.generate()
        assert isinstance(result, dict)


class TestGenerationError:
    """Test GenerationError exception."""

    def test_generation_error_with_message(self) -> None:
        """Test GenerationError with message."""
        error = GenerationError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.cause is None

    def test_generation_error_with_cause(self) -> None:
        """Test GenerationError with underlying exception."""
        underlying = ValueError("root cause")
        error = GenerationError("Generation failed", cause=underlying)
        assert error.message == "Generation failed"
        assert error.cause is underlying

    def test_generation_error_inheritance(self) -> None:
        """Test GenerationError is Exception subclass."""
        error = GenerationError("test")
        assert isinstance(error, Exception)


class TestAIGenerationError:
    """Test AIGenerationError exception."""

    def test_ai_generation_error_is_generation_error(self) -> None:
        """Test AIGenerationError is GenerationError subclass."""
        error = AIGenerationError("AI failed")
        assert isinstance(error, GenerationError)
        assert isinstance(error, Exception)

    def test_ai_generation_error_with_message(self) -> None:
        """Test AIGenerationError with message."""
        error = AIGenerationError("API timeout")
        assert error.message == "API timeout"

    def test_ai_generation_error_with_cause(self) -> None:
        """Test AIGenerationError with cause."""
        underlying = TimeoutError("connection timeout")
        error = AIGenerationError("API call failed", cause=underlying)
        assert error.cause is underlying


class TestTemplateBasedGenerator:
    """Test TemplateBasedGenerator base class."""

    def test_init_with_orchestrator_and_template_dir(self) -> None:
        """Test TemplateBasedGenerator initialization."""
        mock_orchestrator = Mock()
        template_dir = Path("/templates")

        generator = ConcreteTemplateGenerator(
            orchestrator=mock_orchestrator,
            template_dir=template_dir,
        )

        assert generator.orchestrator is mock_orchestrator
        assert generator.template_dir == template_dir

    def test_init_with_none_values(self) -> None:
        """Test TemplateBasedGenerator with None values."""
        generator = ConcreteTemplateGenerator(orchestrator=None, template_dir=None)
        assert generator.orchestrator is None
        assert generator.template_dir is None

    def test_validate_template_path_missing_raises_error(self) -> None:
        """Test validation raises for missing template."""
        generator = ConcreteTemplateGenerator(template_dir=Path("/nonexistent"))

        with pytest.raises(GenerationError, match="Template not found"):
            generator._validate_template_path("missing.j2")

    def test_validate_template_path_without_template_dir_raises_error(self) -> None:
        """Test validation raises when template_dir not set."""
        generator = ConcreteTemplateGenerator(template_dir=None)

        with pytest.raises(GenerationError, match="Template directory not configured"):
            generator._validate_template_path("template.j2")

    def test_validate_template_path_existing_returns_path(self, tmp_path: Any) -> None:
        """Test validation returns path for existing template."""
        template_file = tmp_path / "template.j2"
        template_file.write_text("test")

        generator = ConcreteTemplateGenerator(template_dir=tmp_path)
        result = generator._validate_template_path("template.j2")

        assert result == template_file
        assert result.exists()

    def test_generation_error_cause_preserved(self) -> None:
        """Test GenerationError preserves underlying cause."""
        underlying = FileNotFoundError("file missing")
        error = GenerationError("Template error", cause=underlying)

        assert error.cause is underlying
        assert isinstance(error.cause, FileNotFoundError)
