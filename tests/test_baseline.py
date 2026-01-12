"""Baseline test to verify test infrastructure works.

This test ensures the testing framework is properly configured
and can run tests successfully. It should be replaced with real
tests as features are implemented.
"""

import start_green_stay_green


def test_baseline_infrastructure_works() -> None:
    """Verify test infrastructure is functional.

    This is a minimal test that always passes, ensuring:
    - Pytest can discover and run tests
    - Test collection works correctly
    - Coverage reporting is functional
    """
    assert True, "Test infrastructure is working"


def test_package_imports() -> None:
    """Verify main package can be imported.

    This ensures the package structure is correct and
    basic imports work as expected.
    """
    # Import already at module level for proper linting
    assert start_green_stay_green is not None, "Package imports successfully"
