"""Unit tests for BaseGenerator.

Tests the base generator class that all generators inherit from.
"""

from typing import Any
from unittest.mock import Mock

import pytest

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.base import BaseGenerator


class ConcreteGenerator(BaseGenerator):
    """Concrete implementation of BaseGenerator for testing."""

    def generate(self) -> dict[str, Any]:
        """Concrete implementation of abstract generate method.

        Returns:
            Empty dictionary for testing.
        """
        return {}


class TestBaseGeneratorInitialization:
    """Test BaseGenerator initialization."""

    def test_init_stores_orchestrator(self) -> None:
        """Test __init__ stores orchestrator as instance attribute.

        Kills mutations: orchestrator assignment
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = ConcreteGenerator(mock_orchestrator)

        assert generator.orchestrator is mock_orchestrator
        assert generator.orchestrator == mock_orchestrator
        assert generator.orchestrator is not None

    def test_orchestrator_attribute_exact_reference(self) -> None:
        """Test orchestrator attribute is exactly the provided object.

        Kills mutations: self.orchestrator = orchestrator
        """
        mock_orchestrator_1 = Mock(spec=AIOrchestrator)
        mock_orchestrator_2 = Mock(spec=AIOrchestrator)

        generator_1 = ConcreteGenerator(mock_orchestrator_1)
        generator_2 = ConcreteGenerator(mock_orchestrator_2)

        # Each generator should have its own orchestrator
        assert generator_1.orchestrator is mock_orchestrator_1
        assert generator_1.orchestrator is not mock_orchestrator_2
        assert generator_2.orchestrator is mock_orchestrator_2
        assert generator_2.orchestrator is not mock_orchestrator_1

    def test_orchestrator_not_none(self) -> None:
        """Test orchestrator attribute is not None after init.

        Kills mutations: None assignment
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = ConcreteGenerator(mock_orchestrator)

        assert generator.orchestrator is not None
        assert hasattr(generator, "orchestrator")

    def test_multiple_instances_have_independent_orchestrators(self) -> None:
        """Test multiple generator instances have independent orchestrators.

        Kills mutations: shared state mutations
        """
        orchestrator_1 = Mock(spec=AIOrchestrator, name="orchestrator_1")
        orchestrator_2 = Mock(spec=AIOrchestrator, name="orchestrator_2")
        orchestrator_3 = Mock(spec=AIOrchestrator, name="orchestrator_3")

        gen1 = ConcreteGenerator(orchestrator_1)
        gen2 = ConcreteGenerator(orchestrator_2)
        gen3 = ConcreteGenerator(orchestrator_3)

        # All should be different
        assert gen1.orchestrator is not gen2.orchestrator
        assert gen1.orchestrator is not gen3.orchestrator
        assert gen2.orchestrator is not gen3.orchestrator

        # Each should match its original
        assert gen1.orchestrator is orchestrator_1
        assert gen2.orchestrator is orchestrator_2
        assert gen3.orchestrator is orchestrator_3


class TestBaseGeneratorAbstract:
    """Test BaseGenerator abstract method."""

    def test_cannot_instantiate_base_generator_directly(self) -> None:
        """Test BaseGenerator cannot be instantiated directly.

        Kills mutations: abstract class enforcement
        """
        mock_orchestrator = Mock(spec=AIOrchestrator)

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseGenerator(mock_orchestrator)  # type: ignore[abstract]

    def test_concrete_implementation_required(self) -> None:
        """Test concrete subclass must implement generate method."""

        class IncompleteGenerator(BaseGenerator):
            """Generator without generate implementation."""

        mock_orchestrator = Mock(spec=AIOrchestrator)

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteGenerator(mock_orchestrator)  # type: ignore[abstract]

    def test_concrete_implementation_works(self) -> None:
        """Test concrete subclass with generate method works."""
        mock_orchestrator = Mock(spec=AIOrchestrator)
        generator = ConcreteGenerator(mock_orchestrator)

        # Should be able to call generate
        generator.generate()  # Should not raise
