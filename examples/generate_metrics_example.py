"""Example: Generate quality metrics dashboard configuration.

Demonstrates how to use the MetricsGenerator to create comprehensive
quality metrics tracking for different project types and languages.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from start_green_stay_green.generators.metrics import MetricsGenerationConfig
from start_green_stay_green.generators.metrics import MetricsGenerator


def example_python_project() -> None:
    """Generate metrics for a Python project with all features."""
    print("=" * 70)
    print("Example 1: Python Project (Full Featured)")
    print("=" * 70)

    config = MetricsGenerationConfig(
        language="python",
        project_name="my-python-app",
        coverage_threshold=90,
        branch_coverage_threshold=85,
        mutation_threshold=80,
        complexity_threshold=10,
        doc_coverage_threshold=95,
        enable_sonarqube=True,
        enable_badges=True,
        enable_dashboard=True,
    )

    generator = MetricsGenerator(orchestrator=None, config=config)

    # Generate all artifacts
    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        artifacts = generator.write_all(output_dir)

        print(f"\nGenerated {len(artifacts)} artifacts:")
        for name, path in artifacts.items():
            print(f"  - {name}: {path.name}")
            print(f"    Size: {path.stat().st_size:,} bytes")

        # Show metrics.yml preview
        print("\nmetrics.yml preview:")
        print("-" * 70)
        metrics_content = artifacts["metrics"].read_text()
        print(metrics_content[:500])
        print("...")


def example_typescript_project() -> None:
    """Generate metrics for a TypeScript project (minimal)."""
    print("\n" + "=" * 70)
    print("Example 2: TypeScript Project (Minimal)")
    print("=" * 70)

    config = MetricsGenerationConfig(
        language="typescript",
        project_name="my-ts-app",
        enable_sonarqube=False,
        enable_badges=False,
        enable_dashboard=False,
    )

    generator = MetricsGenerator(orchestrator=None, config=config)

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        artifacts = generator.write_all(output_dir)

        print(f"\nGenerated {len(artifacts)} artifact(s):")
        for name, path in artifacts.items():
            print(f"  - {name}: {path.name}")


def example_custom_thresholds() -> None:
    """Generate metrics with custom thresholds."""
    print("\n" + "=" * 70)
    print("Example 3: Custom Thresholds")
    print("=" * 70)

    config = MetricsGenerationConfig(
        language="go",
        project_name="go-microservice",
        coverage_threshold=85,  # Lower for legacy code
        branch_coverage_threshold=80,
        mutation_threshold=70,
        complexity_threshold=15,  # Higher for complex domain
        doc_coverage_threshold=90,
    )

    generator = MetricsGenerator(orchestrator=None, config=config)
    result = generator.generate()

    print("\nConfigured thresholds:")
    metrics = result["metrics_config"]["metrics"]
    print(f"  - Code Coverage: {metrics['code_coverage']['threshold']}%")
    print(f"  - Branch Coverage: {metrics['branch_coverage']['threshold']}%")
    print(f"  - Mutation Score: {metrics['mutation_score']['threshold']}%")
    print(f"  - Complexity: {metrics['cyclomatic_complexity']['threshold']}")
    print(f"  - Documentation: {metrics['documentation_coverage']['threshold']}%")


def example_dashboard_generation() -> None:
    """Generate and display dashboard HTML."""
    print("\n" + "=" * 70)
    print("Example 4: Dashboard Generation")
    print("=" * 70)

    config = MetricsGenerationConfig(
        language="rust",
        project_name="rust-cli-tool",
        enable_dashboard=True,
    )

    generator = MetricsGenerator(orchestrator=None, config=config)

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        dashboard_path = generator.write_dashboard(output_dir)

        if dashboard_path:
            print(f"\nDashboard generated: {dashboard_path.name}")
            print(f"Size: {dashboard_path.stat().st_size:,} bytes")

            html_content = dashboard_path.read_text()
            print("\nHTML preview:")
            print("-" * 70)
            # Show first 300 characters
            print(html_content[:300])
            print("...")


def example_badges_generation() -> None:
    """Generate GitHub badges."""
    print("\n" + "=" * 70)
    print("Example 5: GitHub Badges")
    print("=" * 70)

    config = MetricsGenerationConfig(
        language="python",
        project_name="awesome-library",
        enable_badges=True,
    )

    generator = MetricsGenerator(orchestrator=None, config=config)

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        badges_path = generator.write_badges(output_dir)

        print(f"\nBadges generated: {badges_path.name}")
        print("\nBadge markdown:")
        print("-" * 70)
        print(badges_path.read_text())


def example_ci_integration() -> None:
    """Show CI integration configuration."""
    print("\n" + "=" * 70)
    print("Example 6: CI Integration")
    print("=" * 70)

    config = MetricsGenerationConfig(
        language="python",
        project_name="ci-example",
        coverage_threshold=90,
    )

    generator = MetricsGenerator(orchestrator=None, config=config)
    result = generator.generate()

    print("\nGitHub Actions configuration:")
    print("-" * 70)

    ci_config = result["ci_config"]["github_actions"]
    for check_config in ci_config.values():
        print(f"\n{check_config['name']}:")
        print(f"  run: {check_config['run']}")
        if "notes" in check_config:
            print(f"  notes: {check_config['notes']}")


def main() -> None:
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Quality Metrics Generator Examples" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝")

    try:
        example_python_project()
        example_typescript_project()
        example_custom_thresholds()
        example_dashboard_generation()
        example_badges_generation()
        example_ci_integration()

        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Run tests: pytest tests/unit/generators/test_metrics.py")
        print("  2. Generate for your project using the patterns above")
        print("  3. Integrate metrics.yml into your CI/CD pipeline")
        print("  4. Deploy dashboard.html to GitHub Pages")
        print("  5. Add badges.md to your README.md")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
