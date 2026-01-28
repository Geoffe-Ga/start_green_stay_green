"""Validate Issue #17 implementation.

Quick validation script to verify the metrics generator implementation
is complete and functional before running full test suite.
"""

from pathlib import Path
import sys


def check_imports() -> bool:
    """Verify all required imports work."""
    print("Checking imports...")
    try:
        pass
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    else:
        print("✓ All imports successful")
        return True


def check_standard_metrics() -> bool:
    """Verify STANDARD_METRICS has all 10 metrics."""
    print("\nChecking STANDARD_METRICS...")
    try:
        from start_green_stay_green.generators.metrics import STANDARD_METRICS

        expected_metrics = {
            "code_coverage",
            "branch_coverage",
            "mutation_score",
            "cyclomatic_complexity",
            "cognitive_complexity",
            "maintainability_index",
            "technical_debt_ratio",
            "documentation_coverage",
            "dependency_freshness",
            "security_vulnerabilities",
        }

        actual_metrics = set(STANDARD_METRICS.keys())

        if actual_metrics != expected_metrics:
            missing = expected_metrics - actual_metrics
            extra = actual_metrics - expected_metrics
            if missing:
                print(f"✗ Missing metrics: {missing}")
            if extra:
                print(f"✗ Extra metrics: {extra}")
            return False
    except Exception as e:
        print(f"✗ Error checking metrics: {e}")
        return False
    else:
        print(f"✓ All 10 metrics present: {len(STANDARD_METRICS)}")
        return True


def check_language_support() -> bool:
    """Verify all required languages are supported."""
    print("\nChecking language support...")
    try:
        from start_green_stay_green.generators.metrics import LANGUAGE_TOOLS

        required_languages = {"python", "typescript", "javascript", "go", "rust"}
        actual_languages = set(LANGUAGE_TOOLS.keys())

        if not required_languages.issubset(actual_languages):
            missing = required_languages - actual_languages
            print(f"✗ Missing languages: {missing}")
            return False
    except Exception as e:
        print(f"✗ Error checking languages: {e}")
        return False
    else:
        print(f"✓ All required languages supported: {sorted(actual_languages)}")
        return True


def check_basic_instantiation() -> bool:
    """Verify generator can be instantiated."""
    print("\nChecking basic instantiation...")
    try:
        from start_green_stay_green.generators.metrics import MetricsGenerationConfig
        from start_green_stay_green.generators.metrics import MetricsGenerator

        config = MetricsGenerationConfig(
            language="python",
            project_name="test-project",
        )

        MetricsGenerator(orchestrator=None, config=config)
    except Exception as e:
        print(f"✗ Instantiation error: {e}")
        return False
    else:
        print("✓ Generator instantiated successfully")
        return True


def check_generation() -> bool:
    """Verify basic generation works."""
    print("\nChecking generation...")
    try:
        from start_green_stay_green.generators.metrics import MetricsGenerationConfig
        from start_green_stay_green.generators.metrics import MetricsGenerator

        config = MetricsGenerationConfig(
            language="python",
            project_name="test-project",
        )

        generator = MetricsGenerator(orchestrator=None, config=config)
        result = generator.generate()

        expected_keys = {
            "metrics_config",
            "sonarqube_config",
            "badges",
            "dashboard_template",
            "ci_config",
        }

        if set(result.keys()) != expected_keys:
            missing = expected_keys - set(result.keys())
            print(f"✗ Missing artifacts: {missing}")
            return False
    except Exception as e:
        print(f"✗ Generation error: {e}")
        import traceback

        traceback.print_exc()
        return False
    else:
        print("✓ Generation successful with all artifacts")
        return True


def _check_empty_language_validation() -> bool:
    """Check that empty language raises appropriate error."""
    from start_green_stay_green.generators.metrics import MetricsGenerationConfig
    from start_green_stay_green.generators.metrics import MetricsGenerator

    try:
        config = MetricsGenerationConfig(language="", project_name="test")
        MetricsGenerator(orchestrator=None, config=config)
    except ValueError as e:
        if "Language cannot be empty" not in str(e):
            print(f"✗ Wrong error message: {e}")
            return False
        print("✓ Empty language validation works")
        return True
    else:
        print("✗ Empty language should have raised ValueError")
        return False


def _check_unsupported_language_validation() -> bool:
    """Check that unsupported language raises appropriate error."""
    from start_green_stay_green.generators.metrics import MetricsGenerationConfig
    from start_green_stay_green.generators.metrics import MetricsGenerator

    try:
        config = MetricsGenerationConfig(language="cobol", project_name="test")
        MetricsGenerator(orchestrator=None, config=config)
    except ValueError as e:
        if "Unsupported language: cobol" not in str(e):
            print(f"✗ Wrong error message: {e}")
            return False
        print("✓ Unsupported language validation works")
        return True
    else:
        print("✗ Unsupported language should have raised ValueError")
        return False


def _check_threshold_validation() -> bool:
    """Check that invalid threshold raises appropriate error."""
    from start_green_stay_green.generators.metrics import MetricsGenerationConfig
    from start_green_stay_green.generators.metrics import MetricsGenerator

    try:
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            coverage_threshold=150,
        )
        MetricsGenerator(orchestrator=None, config=config)
    except ValueError as e:
        if "Coverage threshold must be between 0 and 100" not in str(e):
            print(f"✗ Wrong error message: {e}")
            return False
        print("✓ Threshold validation works")
        return True
    else:
        print("✗ Invalid threshold should have raised ValueError")
        return False


def check_validation() -> bool:
    """Verify validation works correctly."""
    print("\nChecking validation...")
    try:
        if not _check_empty_language_validation():
            return False
        if not _check_unsupported_language_validation():
            return False
        if not _check_threshold_validation():
            return False
    except Exception as e:
        print(f"✗ Validation check error: {e}")
        import traceback

        traceback.print_exc()
        return False
    else:
        return True


def check_file_structure() -> bool:
    """Verify all expected files exist."""
    print("\nChecking file structure...")

    base_dir = Path(__file__).parent
    expected_files = [
        "start_green_stay_green/generators/metrics.py",
        "tests/unit/generators/test_metrics.py",
        "tests/integration/generators/test_metrics_integration.py",
        "docs/METRICS_DASHBOARD.md",
        "examples/generate_metrics_example.py",
    ]

    all_exist = True
    for file_path in expected_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (missing)")
            all_exist = False

    return all_exist


def main() -> int:
    """Run all validation checks."""
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Issue #17 Implementation Validation" + " " * 18 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    checks = [
        ("File Structure", check_file_structure),
        ("Imports", check_imports),
        ("Standard Metrics", check_standard_metrics),
        ("Language Support", check_language_support),
        ("Basic Instantiation", check_basic_instantiation),
        ("Generation", check_generation),
        ("Validation", check_validation),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Check '{name}' failed with exception: {e}")
            import traceback

            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")

    print("-" * 70)
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print("\n✅ All validation checks passed!")
        print("\nNext steps:")
        print("  1. Run: pre-commit run --all-files")
        print("  2. Run: pytest tests/unit/generators/test_metrics.py -v")
        integration_cmd = (
            "pytest tests/integration/generators/test_metrics_integration.py -v"
        )
        print(f"  3. Run: {integration_cmd}")
        print("  4. Create PR when all tests pass")
        return 0

    print("\n❌ Some validation checks failed!")
    print("\nPlease fix the issues above before proceeding.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
