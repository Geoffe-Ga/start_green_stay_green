"""Unit tests for Architecture Enforcement Generator."""

import ast
from pathlib import Path
import runpy
import tomllib
from unittest.mock import create_autospec

import pytest
import yaml

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.architecture import (
    ArchitectureEnforcementGenerator,
)
from start_green_stay_green.generators.architecture import _LANGUAGE_TOOLING
from start_green_stay_green.generators.architecture import _LanguageTooling


class TestArchitectureEnforcementGeneratorInit:
    """Test ArchitectureEnforcementGenerator initialization."""

    def test_init_with_orchestrator(self) -> None:
        """Passing an orchestrator still works but emits a DeprecationWarning."""
        orchestrator = create_autospec(AIOrchestrator)
        with pytest.warns(DeprecationWarning, match="'orchestrator' parameter"):
            generator = ArchitectureEnforcementGenerator(orchestrator)

        assert generator.orchestrator is orchestrator

    def test_init_without_orchestrator_is_silent(self) -> None:
        """The default (no orchestrator) does not emit a warning."""
        generator = ArchitectureEnforcementGenerator()
        assert generator.orchestrator is None

    def test_init_with_output_dir(self) -> None:
        """Test initialization with custom output directory."""
        output_dir = Path("/custom/plans/architecture")

        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        assert generator.output_dir == output_dir

    def test_init_with_default_output_dir(self) -> None:
        """Test initialization sets default output directory."""
        generator = ArchitectureEnforcementGenerator()

        assert generator.output_dir == Path("plans/architecture")


class TestArchitectureEnforcementGeneratorGenerate:
    """Test architecture enforcement generation."""

    def test_generate_python_creates_importlinter_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating import-linter config for Python."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="python", project_name="test-project")

        # Should create output directory
        assert output_dir.exists()

        # Should create .importlinter file
        importlinter_file = output_dir / ".importlinter"
        assert importlinter_file.exists()

        # Should create README
        readme_file = output_dir / "README.md"
        assert readme_file.exists()

        # Should create run script
        run_script = output_dir / "run-check.sh"
        assert run_script.exists()

    def test_generate_typescript_creates_dependency_cruiser_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating dependency-cruiser config for TypeScript."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(
            language="typescript",
            project_name="test-project",
        )

        # Should create .dependency-cruiser.js file
        dc_file = output_dir / ".dependency-cruiser.js"
        assert dc_file.exists()

    def test_generate_raises_on_unsupported_language(self) -> None:
        """Test generate raises ValueError for unsupported languages.

        ruby graduated to a real Packwerk config with #373, so the
        probe uses php — a language with no architecture tooling.
        """
        generator = ArchitectureEnforcementGenerator()

        with pytest.raises(ValueError, match="Unsupported language"):
            generator.generate(language="php", project_name="test")

    def test_generate_creates_readme_with_usage_instructions(
        self,
        tmp_path: Path,
    ) -> None:
        """Test README contains usage instructions."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="python", project_name="test-project")

        readme = output_dir / "README.md"
        content = readme.read_text()

        # Should contain usage instructions
        assert "Architecture Enforcement" in content
        assert "import-linter" in content
        assert "run-check.sh" in content

    def test_generate_run_script_is_executable(
        self,
        tmp_path: Path,
    ) -> None:
        """Test run-check.sh is created with executable permissions."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="python", project_name="test-project")

        run_script = output_dir / "run-check.sh"
        # Check file has executable bit
        assert run_script.stat().st_mode & 0o111  # Any execute bit set


class TestArchitectureEnforcementGeneratorPython:
    """Test Python-specific architecture rules."""

    def test_python_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Python config enforces layer separation."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="python", project_name="myapp")

        importlinter = output_dir / ".importlinter"
        content = importlinter.read_text()

        # Should enforce layer separation
        assert "layers" in content.lower() or "contract" in content.lower()

    def test_python_config_prevents_circular_dependencies(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Python config prevents circular dependencies."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="python", project_name="myapp")

        importlinter = output_dir / ".importlinter"
        content = importlinter.read_text()

        # Should check for circular dependencies
        assert "circular" in content.lower() or "cycle" in content.lower()


class TestArchitectureEnforcementGeneratorGo:
    """Test Go-specific architecture rules."""

    def test_generate_go_creates_go_arch_lint_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating go-arch-lint config for Go."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="test-project")

        # Should create the go-arch-lint config file
        config_file = output_dir / ".go-arch-lint.yml"
        assert config_file.exists()

        # Should create README and run script
        assert (output_dir / "README.md").exists()
        assert (output_dir / "run-check.sh").exists()

    def test_go_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Go config enforces layered architecture components."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="myapp")

        config = (output_dir / ".go-arch-lint.yml").read_text()

        # Should define the architecture layers as components
        assert "components" in config.lower()
        assert "domain" in config.lower()
        assert "presentation" in config.lower()

    def test_go_config_enforces_domain_independence(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Go config keeps the domain layer dependency-free."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="myapp")

        config = (output_dir / ".go-arch-lint.yml").read_text()

        # Domain dependency rules must be present (deps section)
        assert "deps" in config.lower()
        assert "infrastructure" in config.lower()

    def test_go_config_common_components_comment_is_accurate(
        self,
        tmp_path: Path,
    ) -> None:
        """commonComponents is documented as a whitelist, not a cycle guard.

        ``commonComponents`` in go-arch-lint v3 is a whitelist: every
        component may import the listed components without an explicit
        ``deps`` entry. It does not detect circular dependencies, so the
        config must not claim that it does.
        """
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="myapp")

        config = (output_dir / ".go-arch-lint.yml").read_text()

        # The misleading cycle-detection claim must be gone.
        assert "circular dependencies between layers" not in config
        # An accurate whitelist description must precede commonComponents.
        assert (
            "# domain is available to all components without an explicit "
            "deps entry." in config
        )

    def test_go_readme_mentions_go_arch_lint(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Go README references the go-arch-lint tooling."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="myapp")

        readme = (output_dir / "README.md").read_text()
        assert "go-arch-lint" in readme

    def test_go_run_script_invokes_go_arch_lint(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Go run-check.sh script invokes go-arch-lint."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="myapp")

        script = (output_dir / "run-check.sh").read_text()
        assert "go-arch-lint" in script

    def test_go_result_reports_go_language(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the result object records the Go language."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        result = generator.generate(language="go", project_name="myapp")

        assert result.language == "go"

    def test_go_run_script_uses_display_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Go run-check.sh announces the 'Go' display name."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="myapp")

        script = (output_dir / "run-check.sh").read_text()
        assert "Checking Go architecture" in script

    def test_go_run_script_prefixes_config_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Go run-check.sh points at the plans/architecture config."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="myapp")

        script = (output_dir / "run-check.sh").read_text()
        assert (
            "go-arch-lint check --arch-file plans/architecture/.go-arch-lint.yml"
            in script
        )


class TestArchitectureEnforcementGeneratorRust:
    """Test Rust-specific architecture rules."""

    def test_generate_rust_creates_cargo_deny_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating cargo-deny config for Rust."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="test-project")

        # Should create the cargo-deny config file
        config_file = output_dir / "deny.toml"
        assert config_file.exists()

        # Should create README and run script
        assert (output_dir / "README.md").exists()
        assert (output_dir / "run-check.sh").exists()

    def test_rust_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Rust config enforces layered architecture via bans."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="myapp")

        config = (output_dir / "deny.toml").read_text()

        # Should define dependency bans expressing the layer rules
        assert "[bans]" in config
        assert "domain" in config.lower()
        assert "presentation" in config.lower()

    def test_rust_config_enforces_domain_independence(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Rust config keeps inner layers free of outer-layer deps."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="myapp")

        config = (output_dir / "deny.toml").read_text()

        # Layer crates are banned outside their wrapper (consumer) crates,
        # which is how cargo-deny expresses "only outer layers may depend
        # on this crate".
        assert "wrappers" in config
        assert "infrastructure" in config.lower()

    def test_rust_config_cycle_comment_is_accurate(
        self,
        tmp_path: Path,
    ) -> None:
        """Cycle prevention is attributed to Cargo, not to cargo-deny.

        cargo-deny does not detect dependency cycles; Cargo itself rejects
        circular dependencies between crates at build time. The generated
        config must say so rather than overclaiming what cargo-deny does.
        """
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="myapp")

        config = (output_dir / "deny.toml").read_text()

        # An accurate statement about Cargo's built-in cycle rejection
        # must be present.
        assert "# Cargo itself rejects circular crate dependencies" in config

    def test_rust_config_is_parseable_toml(
        self,
        tmp_path: Path,
    ) -> None:
        """deny.toml must be syntactically valid TOML."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="myapp")

        config = (output_dir / "deny.toml").read_text()
        tomllib.loads(config)  # raises on parse error

    def test_rust_config_documents_presentation_gap(
        self,
        tmp_path: Path,
    ) -> None:
        """The config documents what cargo-deny cannot enforce.

        cargo-deny cannot restrict what depends on the presentation
        crate without knowing the top-level binary name, so
        ``domain -> presentation`` and ``application -> presentation``
        rely on convention. The generated config must say so rather
        than imply complete enforcement.
        """
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="myapp")

        config = (output_dir / "deny.toml").read_text()
        assert "cargo-deny cannot restrict what depends on" in config
        assert "convention" in config

    def test_rust_config_warns_on_duplicate_versions(
        self,
        tmp_path: Path,
    ) -> None:
        """Duplicate-version policy defaults to warn, not deny.

        Transitive Rust dependency trees routinely contain duplicate
        semver-incompatible versions (windows-*, syn, regex families);
        a hard deny would fail users on their first ``cargo add``.
        """
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="myapp")

        config = (output_dir / "deny.toml").read_text()
        assert 'multiple-versions = "warn"' in config
        assert 'multiple-versions = "deny"' not in config

    def test_rust_readme_mentions_cargo_deny(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Rust README references the cargo-deny tooling."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="myapp")

        readme = (output_dir / "README.md").read_text()
        assert "cargo-deny" in readme

    def test_rust_run_script_invokes_cargo_deny(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Rust run-check.sh script invokes cargo-deny."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="myapp")

        script = (output_dir / "run-check.sh").read_text()
        assert "cargo-deny" in script

    def test_rust_result_reports_rust_language(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the result object records the Rust language."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        result = generator.generate(language="rust", project_name="myapp")

        assert result.language == "rust"

    def test_rust_run_script_uses_display_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Rust run-check.sh announces the 'Rust' display name."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="myapp")

        script = (output_dir / "run-check.sh").read_text()
        assert "Checking Rust architecture" in script

    def test_rust_run_script_prefixes_config_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Rust run-check.sh points at the plans/architecture config."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="myapp")

        script = (output_dir / "run-check.sh").read_text()
        assert "cargo-deny check --config plans/architecture/deny.toml" in script

    def test_rust_run_script_probes_cargo_deny_binary(
        self,
        tmp_path: Path,
    ) -> None:
        """run-check.sh guards on the cargo-deny binary, not bare cargo.

        Probing ``cargo`` would succeed on any Rust toolchain even when the
        cargo-deny subcommand is missing, so the availability guard must
        target the ``cargo-deny`` binary itself.
        """
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="rust", project_name="myapp")

        script = (output_dir / "run-check.sh").read_text()
        assert "command -v cargo-deny" in script


class TestArchitectureEnforcementGeneratorSwift:
    """Test Swift-specific architecture rules (#352)."""

    @staticmethod
    def _generate(tmp_path: Path) -> Path:
        """Generate the Swift architecture config and return its directory."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)
        generator.generate(language="swift", project_name="myapp")
        return output_dir

    def test_generate_swift_creates_swiftlint_architecture_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating SwiftLint custom-rules config for Swift."""
        output_dir = self._generate(tmp_path)

        # Should create the SwiftLint custom-rules config file
        config_file = output_dir / ".swiftlint-architecture.yml"
        assert config_file.exists()

        # Should create README and run script
        assert (output_dir / "README.md").exists()
        assert (output_dir / "run-check.sh").exists()

    def test_swift_config_is_parseable_yaml(
        self,
        tmp_path: Path,
    ) -> None:
        """.swiftlint-architecture.yml must be syntactically valid YAML."""
        output_dir = self._generate(tmp_path)

        config = (output_dir / ".swiftlint-architecture.yml").read_text()
        parsed = yaml.safe_load(config)  # raises on parse error
        assert isinstance(parsed, dict)

    def test_swift_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Swift config expresses layer rules as custom regex rules."""
        output_dir = self._generate(tmp_path)

        config = (output_dir / ".swiftlint-architecture.yml").read_text()
        parsed = yaml.safe_load(config)

        rules = parsed["custom_rules"]
        assert "domain_layer_purity" in rules
        assert "application_layer_boundary" in rules
        assert "infrastructure_layer_boundary" in rules
        assert "presentation_layer_boundary" in rules

    def test_swift_config_keeps_domain_pure(
        self,
        tmp_path: Path,
    ) -> None:
        """The domain rule forbids importing every outer-layer module."""
        output_dir = self._generate(tmp_path)

        config = (output_dir / ".swiftlint-architecture.yml").read_text()
        parsed = yaml.safe_load(config)

        domain_rule = parsed["custom_rules"]["domain_layer_purity"]
        for module in ("Presentation", "Application", "Infrastructure"):
            assert module in domain_rule["regex"]
        assert domain_rule["severity"] == "error"

    def test_swift_config_runs_only_custom_rules(
        self,
        tmp_path: Path,
    ) -> None:
        """The architecture pass stays orthogonal to the general lint pass."""
        output_dir = self._generate(tmp_path)

        config = (output_dir / ".swiftlint-architecture.yml").read_text()
        parsed = yaml.safe_load(config)

        assert parsed["only_rules"] == ["custom_rules"]

    def test_swift_config_documents_regex_limits(
        self,
        tmp_path: Path,
    ) -> None:
        """The config documents what regex custom rules cannot enforce.

        No native Swift layer linter exists; SwiftLint custom rules match
        source text, not a resolved dependency graph. The generated config
        must disclose that limit (mirroring the Rust deny.toml gap note)
        rather than imply complete enforcement.
        """
        output_dir = self._generate(tmp_path)

        config = (output_dir / ".swiftlint-architecture.yml").read_text()
        assert "regex matches over source text" in config
        assert "not a resolved dependency graph" in config

    def test_swift_config_cycle_comment_is_accurate(
        self,
        tmp_path: Path,
    ) -> None:
        """Cycle prevention is attributed to SPM, not to SwiftLint.

        SwiftLint custom rules cannot detect dependency cycles; Swift
        Package Manager itself rejects circular target dependencies at
        build time. The generated config must say so rather than
        overclaiming what SwiftLint does.
        """
        output_dir = self._generate(tmp_path)

        config = (output_dir / ".swiftlint-architecture.yml").read_text()
        assert "Swift Package Manager itself rejects circular" in config

    def test_swift_config_catches_testable_imports(
        self,
        tmp_path: Path,
    ) -> None:
        """Layer rules also match @testable import statements."""
        output_dir = self._generate(tmp_path)

        config = (output_dir / ".swiftlint-architecture.yml").read_text()
        parsed = yaml.safe_load(config)

        domain_rule = parsed["custom_rules"]["domain_layer_purity"]
        assert "@testable" in domain_rule["regex"]

    def test_swift_readme_mentions_swiftlint(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Swift README references the SwiftLint tooling."""
        output_dir = self._generate(tmp_path)

        readme = (output_dir / "README.md").read_text()
        assert "SwiftLint" in readme

    def test_swift_run_script_invokes_swiftlint(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Swift run-check.sh script invokes swiftlint."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "command -v swiftlint" in script

    def test_swift_run_script_prefixes_config_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Swift run-check.sh points at the plans/architecture config."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert (
            "swiftlint lint --config "
            "plans/architecture/.swiftlint-architecture.yml" in script
        )

    def test_swift_run_script_uses_display_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Swift run-check.sh announces the 'Swift' display name."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "Checking Swift architecture" in script

    def test_swift_result_reports_swift_language(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the result object records the Swift language."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        result = generator.generate(language="swift", project_name="myapp")

        assert result.language == "swift"


class TestArchitectureEnforcementGeneratorKotlin:
    """Test Kotlin-specific architecture rules (#357)."""

    @staticmethod
    def _generate(tmp_path: Path, project_name: str = "my-app") -> Path:
        """Generate the Kotlin architecture config and return its directory."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)
        generator.generate(language="kotlin", project_name=project_name)
        return output_dir

    def test_generate_kotlin_creates_konsist_test(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating the Konsist architecture test for Kotlin."""
        output_dir = self._generate(tmp_path)

        # Should create the Konsist test template
        config_file = output_dir / "ArchitectureTest.kt"
        assert config_file.exists()

        # Should create README and run script
        assert (output_dir / "README.md").exists()
        assert (output_dir / "run-check.sh").exists()

    def test_kotlin_config_is_structurally_valid_kotlin(
        self,
        tmp_path: Path,
    ) -> None:
        """ArchitectureTest.kt must be structurally valid Kotlin source.

        There is no Kotlin parser in the test environment, so validity is
        checked structurally: balanced braces/parentheses, a package
        declaration first, imports before the class, and no unrendered
        template placeholders.
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.kt").read_text()
        code_lines = [
            line
            for line in source.splitlines()
            if line.strip() and not line.lstrip().startswith("//")
        ]
        code = "\n".join(code_lines)

        assert code.count("{") == code.count("}")
        assert code.count("(") == code.count(")")
        # The first statement must be the package declaration, followed by
        # the imports, then the class.
        assert code_lines[0].startswith("package ")
        import_lines = [line for line in code_lines if line.startswith("import ")]
        assert import_lines
        assert code.index("package ") < code.index("import ")
        assert code.index("import ") < code.index("class ArchitectureTest")
        assert "class ArchitectureTest" in code
        assert "@Test" in code
        # No unrendered Python format placeholders may survive.
        assert "{namespace}" not in source

    def test_kotlin_config_uses_konsist_api(
        self,
        tmp_path: Path,
    ) -> None:
        """The test drives Konsist's architecture-assertion API."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.kt").read_text()
        assert "import com.lemonappdev.konsist.api.Konsist" in source
        assert (
            "import com.lemonappdev.konsist.api.architecture."
            "KoArchitectureCreator.assertArchitecture" in source
        )
        assert "import com.lemonappdev.konsist.api.architecture.Layer" in source
        assert "Konsist" in source
        assert ".scopeFromProject()" in source
        assert ".assertArchitecture" in source

    def test_kotlin_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Kotlin config defines all four layers with inward deps."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.kt").read_text()
        for layer in ("Domain", "Application", "Presentation", "Infrastructure"):
            assert f'Layer("{layer}"' in source
        assert "domain.dependsOnNothing()" in source
        assert "application.dependsOn(domain)" in source
        assert "presentation.dependsOn(application)" in source
        assert "presentation.dependsOn(domain)" in source
        assert "infrastructure.dependsOn(domain)" in source

    def test_kotlin_config_derives_layer_packages_from_project_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Layer packages come from the shared Android namespace helper.

        A hyphenated project name must produce the sanitized namespace
        (my-app -> com.example.my_app), keeping the architecture test in
        sync with the scaffolded sources.
        """
        output_dir = self._generate(tmp_path, project_name="my-app")

        source = (output_dir / "ArchitectureTest.kt").read_text()
        assert '"com.example.my_app.domain.."' in source
        assert '"com.example.my_app.presentation.."' in source

    def test_kotlin_config_documents_static_analysis_limits(
        self,
        tmp_path: Path,
    ) -> None:
        """The test documents what Konsist cannot enforce.

        Konsist analyzes Kotlin source declarations statically; the
        generated test must disclose that limit (mirroring the Rust
        deny.toml and Swift regex-rule gap notes) rather than imply
        complete enforcement.
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.kt").read_text()
        assert "not a resolved dependency graph" in source
        assert "reflection" in source

    def test_kotlin_config_documents_wiring_requirement(
        self,
        tmp_path: Path,
    ) -> None:
        """The test discloses it only enforces once wired into a source set."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.kt").read_text()
        assert "app/src/test/kotlin" in source

    def test_kotlin_config_documents_non_strict_default(
        self,
        tmp_path: Path,
    ) -> None:
        """The warn-first non-strict default carries a tighten-me note."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.kt").read_text()
        assert "strict = true" in source

    def test_kotlin_config_cycle_comment_is_accurate(
        self,
        tmp_path: Path,
    ) -> None:
        """Cycle prevention is attributed to Gradle, not to Konsist.

        Gradle itself rejects circular project dependencies at build
        time; the generated test must say so rather than overclaiming
        what Konsist does.
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.kt").read_text()
        assert "Gradle itself rejects circular" in source

    def test_kotlin_readme_mentions_konsist(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Kotlin README references the Konsist tooling."""
        output_dir = self._generate(tmp_path)

        readme = (output_dir / "README.md").read_text()
        assert "Konsist" in readme

    def test_kotlin_run_script_probes_gradle_wrapper(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Kotlin run-check.sh probes the Gradle wrapper."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "command -v ./gradlew" in script

    def test_kotlin_run_script_runs_architecture_test(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Kotlin run-check.sh runs the Konsist test via Gradle."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert '--tests "*ArchitectureTest"' in script

    def test_kotlin_run_script_uses_display_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Kotlin run-check.sh announces the 'Kotlin' display name."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "Checking Kotlin architecture" in script

    def test_kotlin_result_reports_kotlin_language(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the result object records the Kotlin language."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        result = generator.generate(language="kotlin", project_name="my-app")

        assert result.language == "kotlin"


class TestArchitectureEnforcementGeneratorCpp:
    """Test C/C++-specific architecture rules (#362)."""

    @staticmethod
    def _generate(tmp_path: Path, project_name: str = "my-app") -> Path:
        """Generate the cpp architecture config and return its directory."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)
        generator.generate(language="cpp", project_name=project_name)
        return output_dir

    @staticmethod
    def _run_checker(script: Path) -> int:
        """Execute the generated checker in-process and return its exit code.

        ``runpy`` runs the script exactly as ``python3 <script>`` would
        (``__name__ == "__main__"``, ``__file__`` set), so the script's
        own project-root resolution from its plans/architecture location
        is exercised for real.

        Args:
            script: Path to the generated check_architecture.py.

        Returns:
            The exit code the script passed to sys.exit().
        """
        try:
            runpy.run_path(str(script), run_name="__main__")
        except SystemExit as exc:
            return int(exc.code) if exc.code is not None else 0
        return 0

    def test_generate_cpp_creates_include_boundary_checker(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating the include-boundary checker for cpp."""
        output_dir = self._generate(tmp_path)

        # Should create the runnable checker script
        config_file = output_dir / "check_architecture.py"
        assert config_file.exists()

        # Should create README and run script
        assert (output_dir / "README.md").exists()
        assert (output_dir / "run-check.sh").exists()

    def test_cpp_config_is_valid_python(
        self,
        tmp_path: Path,
    ) -> None:
        """check_architecture.py must parse as valid Python source."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "check_architecture.py").read_text()
        ast.parse(source)

    def test_cpp_config_defines_the_layer_matrix(
        self,
        tmp_path: Path,
    ) -> None:
        """The editable dependency matrix mirrors the Go config."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "check_architecture.py").read_text()
        assert "ALLOWED_DEPENDENCIES" in source
        for layer in ("presentation", "application", "domain", "infrastructure"):
            assert f'"{layer}"' in source
        assert '"domain": frozenset(),' in source

    def test_cpp_checker_passes_on_a_clean_layer_tree(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A tree honoring the matrix exits 0."""
        output_dir = self._generate(tmp_path)
        app_dir = tmp_path / "src" / "application"
        app_dir.mkdir(parents=True)
        (app_dir / "service.cpp").write_text('#include "domain/clock.h"\n')

        exit_code = self._run_checker(output_dir / "check_architecture.py")

        captured = capsys.readouterr()
        assert exit_code == 0, captured.out
        assert "Architecture OK" in captured.out

    def test_cpp_checker_fails_on_a_boundary_violation(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A domain file including presentation headers exits 1."""
        output_dir = self._generate(tmp_path)
        domain_dir = tmp_path / "src" / "domain"
        domain_dir.mkdir(parents=True)
        (domain_dir / "clock.cpp").write_text('#include "presentation/widget.h"\n')

        exit_code = self._run_checker(output_dir / "check_architecture.py")

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "layer 'domain' must not include from layer 'presentation'" in (
            captured.out
        )

    def test_cpp_checker_rejects_unknown_layer_in_matrix(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A typo'd layer name in the editable matrix fails loudly.

        The whole enforcement rests on ALLOWED_DEPENDENCIES, so an
        allowed-set entry naming no known layer (e.g. "domian") must
        abort with exit 2 instead of silently never matching.
        """
        output_dir = self._generate(tmp_path)
        script = output_dir / "check_architecture.py"
        source = script.read_text()
        source = source.replace(
            '"application": frozenset({"domain"}),',
            '"application": frozenset({"domian"}),',
        )
        script.write_text(source)

        exit_code = self._run_checker(script)

        captured = capsys.readouterr()
        assert exit_code == 2
        assert "unknown layer 'domian'" in captured.out

    def test_cpp_checker_warns_and_passes_without_layer_dirs(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The warn-first default passes when no layer directory exists yet.

        Mirrors the Konsist non-strict default: the #361 scaffold ships a
        flat src/, so the checker must not fail a fresh project. The
        STRICT switch is the documented tighten-me.
        """
        output_dir = self._generate(tmp_path)

        exit_code = self._run_checker(output_dir / "check_architecture.py")

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "warn-first" in captured.out

    def test_cpp_config_documents_textual_scan_limits(
        self,
        tmp_path: Path,
    ) -> None:
        """The checker documents what a textual #include scan cannot see.

        Mirroring the Rust deny.toml and Swift regex-rule gap notes: the
        script must disclose that it is not a resolved dependency graph
        and that the C/C++ toolchain does not reject include cycles.
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "check_architecture.py").read_text()
        assert "not a resolved dependency graph" in source
        assert "does NOT reject include cycles" in source
        assert "STRICT = True" in source

    def test_cpp_config_documents_evaluated_alternatives(
        self,
        tmp_path: Path,
    ) -> None:
        """The checker explains why IWYU/cpp-dependencies were not chosen."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "check_architecture.py").read_text()
        assert "include-what-you-use" in source
        assert "cpp-dependencies" in source

    def test_cpp_readme_mentions_include_boundary_checker(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the cpp README references the include-boundary tooling."""
        output_dir = self._generate(tmp_path)

        readme = (output_dir / "README.md").read_text()
        assert "include-boundary checker" in readme
        assert "check_architecture.py" in readme

    def test_cpp_run_script_invokes_python3(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the cpp run-check.sh probes python3 and runs the checker."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "command -v python3" in script
        assert "python3 plans/architecture/check_architecture.py" in script

    def test_cpp_run_script_uses_display_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the cpp run-check.sh announces the 'C/C++' display name."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "Checking C/C++ architecture" in script

    def test_cpp_result_reports_cpp_language(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the result object records the cpp language."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        result = generator.generate(language="cpp", project_name="my-app")

        assert result.language == "cpp"


class TestArchitectureEnforcementGeneratorJava:
    """Test Java-specific architecture rules (#367)."""

    @staticmethod
    def _generate(tmp_path: Path, project_name: str = "my-app") -> Path:
        """Generate the Java architecture config and return its directory."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)
        generator.generate(language="java", project_name=project_name)
        return output_dir

    def test_generate_java_creates_archunit_test(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating the ArchUnit architecture test for Java."""
        output_dir = self._generate(tmp_path)

        # Should create the ArchUnit test template
        config_file = output_dir / "ArchitectureTest.java"
        assert config_file.exists()

        # Should create README and run script
        assert (output_dir / "README.md").exists()
        assert (output_dir / "run-check.sh").exists()

    def test_java_config_is_structurally_valid_java(
        self,
        tmp_path: Path,
    ) -> None:
        """ArchitectureTest.java must be structurally valid Java source.

        There is no Java parser in the test environment, so validity is
        checked structurally (the Kotlin precedent): balanced braces/
        parentheses, a package declaration first, imports before the
        class, and no unrendered template placeholders.
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.java").read_text()
        code_lines = [
            line
            for line in source.splitlines()
            if line.strip() and not line.lstrip().startswith(("//", "*", "/*"))
        ]
        code = "\n".join(code_lines)

        assert code.count("{") == code.count("}")
        assert code.count("(") == code.count(")")
        # The first statement must be the package declaration, followed by
        # the imports, then the class.
        assert code_lines[0].startswith("package ")
        assert code_lines[0].rstrip().endswith(";")
        import_lines = [line for line in code_lines if line.startswith("import ")]
        assert import_lines
        assert all(line.rstrip().endswith(";") for line in import_lines)
        assert code.index("package ") < code.index("import ")
        assert code.index("import ") < code.index("public class ArchitectureTest")
        assert "@Test" in code
        # No unrendered Python format placeholders may survive.
        assert "{namespace}" not in source

    def test_java_config_uses_archunit_api(
        self,
        tmp_path: Path,
    ) -> None:
        """The test drives ArchUnit's layered-architecture API."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.java").read_text()
        assert "import com.tngtech.archunit.core.domain.JavaClasses;" in source
        assert "import com.tngtech.archunit.core.importer.ClassFileImporter;" in source
        assert "import com.tngtech.archunit.library.Architectures;" in source
        assert "Architectures.layeredArchitecture()" in source
        assert ".consideringOnlyDependenciesInLayers()" in source

    def test_java_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Java config defines all four layers with inward deps."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.java").read_text()
        for layer in ("Domain", "Application", "Presentation", "Infrastructure"):
            assert f'.layer("{layer}")' in source
        assert '.whereLayer("Presentation").mayNotBeAccessedByAnyLayer()' in source
        assert (
            '.whereLayer("Application").mayOnlyBeAccessedByLayers("Presentation")'
            in source
        )
        assert '.whereLayer("Infrastructure").mayNotBeAccessedByAnyLayer()' in source
        assert (
            '"Application", "Presentation", "Infrastructure"' in source
        ), "Domain must be accessible from the three outer layers only"

    def test_java_config_checks_package_cycles(
        self,
        tmp_path: Path,
    ) -> None:
        """The test adds a slices cycle rule — Maven cannot do it.

        Unlike Gradle project graphs or Cargo crate graphs, javac and
        Maven accept circular package dependencies, so cycle prevention
        must be enforced by ArchUnit itself rather than attributed to
        the build system (the inverse of the Kotlin/Rust notes).
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.java").read_text()
        assert ".beFreeOfCycles()" in source
        assert "SlicesRuleDefinition.slices()" in source
        assert "do NOT reject" in source

    def test_java_config_derives_layer_packages_from_project_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Layer packages come from the shared Android namespace helper.

        A hyphenated project name must produce the sanitized namespace
        (my-app -> com.example.my_app), keeping the architecture test in
        sync with the scaffolded sources.
        """
        output_dir = self._generate(tmp_path, project_name="my-app")

        source = (output_dir / "ArchitectureTest.java").read_text()
        assert '"com.example.my_app"' in source
        assert "package com.example.my_app.architecture;" in source

    def test_java_config_documents_bytecode_analysis_limits(
        self,
        tmp_path: Path,
    ) -> None:
        """The test documents what ArchUnit cannot enforce.

        ArchUnit analyzes compiled bytecode; the generated test must
        disclose that reflection/DI wiring is invisible and that the
        classes must be compiled first (mirroring the Konsist, Rust
        deny.toml, and Swift regex-rule gap notes).
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.java").read_text()
        assert "reflection" in source
        assert "bytecode" in source
        assert "target/classes" in source

    def test_java_config_documents_wiring_requirement(
        self,
        tmp_path: Path,
    ) -> None:
        """The test discloses it only enforces once wired into src/test/java."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.java").read_text()
        assert "src/test/java" in source
        assert "cp plans/architecture/ArchitectureTest.java" in source

    def test_java_config_documents_optional_layers_default(
        self,
        tmp_path: Path,
    ) -> None:
        """The warn-first optional-layers default carries a tighten-me note."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.java").read_text()
        assert ".withOptionalLayers(true)" in source
        assert "withOptionalLayers(false)" in source

    def test_java_readme_mentions_archunit(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Java README references the ArchUnit tooling."""
        output_dir = self._generate(tmp_path)

        readme = (output_dir / "README.md").read_text()
        assert "ArchUnit" in readme

    def test_java_run_script_probes_maven(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Java run-check.sh probes the mvn binary."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "command -v mvn" in script

    def test_java_run_script_runs_architecture_test(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Java run-check.sh runs the ArchUnit test via Maven."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "-Dtest=ArchitectureTest" in script

    def test_java_run_script_uses_display_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Java run-check.sh announces the 'Java' display name."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "Checking Java architecture" in script

    def test_java_result_reports_java_language(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the result object records the Java language."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        result = generator.generate(language="java", project_name="my-app")

        assert result.language == "java"


class TestArchitectureEnforcementGeneratorCsharp:
    """Test C#-specific architecture rules (#370)."""

    @staticmethod
    def _generate(tmp_path: Path, project_name: str = "my-app") -> Path:
        """Generate the C# architecture config and return its directory."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)
        generator.generate(language="csharp", project_name=project_name)
        return output_dir

    def test_generate_csharp_creates_netarchtest_test(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating the NetArchTest architecture test for C#."""
        output_dir = self._generate(tmp_path)

        config_file = output_dir / "ArchitectureTest.cs"
        assert config_file.exists()

        # Should create README and run script
        assert (output_dir / "README.md").exists()
        assert (output_dir / "run-check.sh").exists()

    def test_csharp_config_is_structurally_valid_csharp(
        self,
        tmp_path: Path,
    ) -> None:
        """ArchitectureTest.cs must be structurally valid C# source.

        There is no C# parser in the test environment, so validity is
        checked structurally (the Kotlin/Java precedent): balanced
        braces/parentheses, usings before the namespace declaration,
        and no unrendered template placeholders.
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.cs").read_text()
        code_lines = [
            line
            for line in source.splitlines()
            if line.strip() and not line.lstrip().startswith(("//", "*", "/*"))
        ]
        code = "\n".join(code_lines)

        assert code.count("{") == code.count("}")
        assert code.count("(") == code.count(")")
        # Usings come first, then the namespace, then the class.
        assert code_lines[0].startswith("using ")
        using_lines = [line for line in code_lines if line.startswith("using ")]
        assert using_lines
        assert all(line.rstrip().endswith(";") for line in using_lines)
        assert code.index("using ") < code.index("namespace ")
        assert code.index("namespace ") < code.index("public class ArchitectureTest")
        assert "[Fact]" in code
        # No unrendered Python format placeholders may survive.
        assert "{namespace}" not in source

    def test_csharp_config_uses_netarchtest_api(
        self,
        tmp_path: Path,
    ) -> None:
        """The test drives NetArchTest's fluent rules API."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.cs").read_text()
        assert "using NetArchTest.Rules;" in source
        assert "using Xunit;" in source
        assert "Types.InAssembly(" in source
        assert ".GetResult()" in source
        assert ".IsSuccessful" in source

    def test_csharp_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test C# config encodes the four-layer inward-only matrix."""
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.cs").read_text()
        for layer in ("Domain", "Application", "Presentation", "Infrastructure"):
            assert f'"{layer}"' in source or f".{layer}" in source
        # Domain must not reach any outer layer; application must not
        # reach presentation/infrastructure; infrastructure must not
        # reach presentation/application.
        assert ".ShouldNot()" in source
        assert ".HaveDependencyOnAny(" in source

    def test_csharp_config_documents_cycle_rule_gap(
        self,
        tmp_path: Path,
    ) -> None:
        """The test discloses how cycle freedom is (and is not) covered.

        NetArchTest has no slices/cycle rule (ArchUnitNET does — the
        documented alternative): cycle freedom among the four layers
        follows from the acyclic dependency matrix, but arbitrary
        namespace cycles outside it go unchecked, and the C# compiler
        does NOT reject namespace cycles, so the limit must be stated
        rather than attributed to the build system.
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.cs").read_text()
        assert "ArchUnitNET" in source
        assert "does NOT reject" in source
        assert "acyclic" in source

    def test_csharp_config_derives_layer_namespaces_from_project_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Layer namespaces come from the shared csharp_namespace helper.

        A hyphenated project name must produce the PascalCase namespace
        (my-app -> MyApp), keeping the architecture test in sync with
        the scaffolded sources.
        """
        output_dir = self._generate(tmp_path, project_name="my-app")

        source = (output_dir / "ArchitectureTest.cs").read_text()
        assert '"MyApp"' in source
        assert "namespace MyApp.Architecture" in source

    def test_csharp_config_documents_compiled_assembly_limits(
        self,
        tmp_path: Path,
    ) -> None:
        """The test documents what NetArchTest cannot enforce.

        NetArchTest analyzes the compiled assembly (via Mono.Cecil), so
        the generated test must disclose that reflection/DI wiring is
        invisible and that the project must build first.
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.cs").read_text()
        assert "reflection" in source
        assert "compiled" in source

    def test_csharp_config_documents_wiring_requirement(
        self,
        tmp_path: Path,
    ) -> None:
        """The test discloses it only enforces once copied into tests/.

        Unlike javac, C# namespaces carry no directory-matching
        requirement, so the flat copy is correct (and the template says
        so — the inverse of the Java package-path lesson).
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.cs").read_text()
        assert "cp plans/architecture/ArchitectureTest.cs tests/" in source
        assert "directory" in source

    def test_csharp_config_documents_vacuous_pass_default(
        self,
        tmp_path: Path,
    ) -> None:
        """The warn-first empty-namespace default carries a tighten note.

        NetArchTest rules pass vacuously when a layer namespace has no
        types yet (the withOptionalLayers(true) analogue), so the test
        must disclose it and point at the tighten-me path.
        """
        output_dir = self._generate(tmp_path)

        source = (output_dir / "ArchitectureTest.cs").read_text()
        assert "vacuous" in source
        assert "Tighten" in source

    def test_csharp_readme_mentions_netarchtest(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the C# README references the NetArchTest tooling."""
        output_dir = self._generate(tmp_path)

        readme = (output_dir / "README.md").read_text()
        assert "NetArchTest" in readme
        assert "ArchitectureTest.cs" in readme

    def test_csharp_run_script_probes_dotnet(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the C# run-check.sh probes the dotnet binary."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "command -v dotnet" in script

    def test_csharp_run_script_filters_to_architecture_test(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the C# run-check.sh runs only the architecture test."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "--filter" in script
        assert "ArchitectureTest" in script

    def test_csharp_run_script_uses_display_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the C# run-check.sh announces the 'C#' display name."""
        output_dir = self._generate(tmp_path)

        script = (output_dir / "run-check.sh").read_text()
        assert "Checking C# architecture" in script

    def test_csharp_result_reports_csharp_language(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the result object records the csharp language."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        result = generator.generate(language="csharp", project_name="my-app")

        assert result.language == "csharp"


class TestArchitectureEnforcementGeneratorRuby:
    """Test Ruby-specific architecture rules (#373)."""

    @staticmethod
    def _generate(tmp_path: Path, project_name: str = "my-gem") -> Path:
        """Generate the Ruby architecture config and return its directory."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)
        generator.generate(language="ruby", project_name=project_name)
        return output_dir

    def test_generate_ruby_creates_packwerk_configs(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating the Packwerk configuration pair for Ruby."""
        output_dir = self._generate(tmp_path)

        assert (output_dir / "packwerk.yml").exists()
        assert (output_dir / "package.yml").exists()

        # Should create README and run script
        assert (output_dir / "README.md").exists()
        assert (output_dir / "run-check.sh").exists()

    def test_ruby_packwerk_config_parses_as_yaml(
        self,
        tmp_path: Path,
    ) -> None:
        """packwerk.yml must parse as YAML with Packwerk's documented keys.

        Parse-validation guardrail: every generated artifact must be
        loadable by the tool that will read it.
        """
        output_dir = self._generate(tmp_path)

        parsed = yaml.safe_load((output_dir / "packwerk.yml").read_text())
        assert parsed["include"] == ["**/*.{rb,rake,erb}"]
        assert parsed["package_paths"] == "**/"
        assert parsed["parallel"] is True

    def test_ruby_package_config_enforces_dependencies(
        self,
        tmp_path: Path,
    ) -> None:
        """package.yml parses as YAML and switches enforcement on."""
        output_dir = self._generate(tmp_path)

        parsed = yaml.safe_load((output_dir / "package.yml").read_text())
        assert parsed["enforce_dependencies"] is True
        assert parsed["dependencies"] == []

    def test_ruby_config_documents_zeitwerk_limit(
        self,
        tmp_path: Path,
    ) -> None:
        """The config discloses Packwerk's Zeitwerk assumption honestly.

        Packwerk is built for Zeitwerk-style autoloaded codebases; on
        the plain-Ruby scaffold the check passes vacuously until
        packages are defined, and the config must say so (no
        overclaiming) with a tighten-me path.
        """
        output_dir = self._generate(tmp_path)

        content = (output_dir / "packwerk.yml").read_text()
        assert "Zeitwerk" in content
        assert "VACUOUSLY" in content
        assert "Tighten" in content

    def test_ruby_config_documents_static_analysis_limit(
        self,
        tmp_path: Path,
    ) -> None:
        """The config discloses the static-analysis blind spot."""
        output_dir = self._generate(tmp_path)

        content = (output_dir / "packwerk.yml").read_text()
        assert "STATIC" in content
        assert "const_get" in content

    def test_ruby_config_documents_circular_require_hazard(
        self,
        tmp_path: Path,
    ) -> None:
        """The config explains Ruby's load-time behavior accurately.

        Ruby's require does NOT reject circular requires at load time —
        the cycle silently yields a partially-defined module at
        runtime — so the config must document boundary enforcement as
        the only early signal, without overclaiming a compiler-style
        rejection.
        """
        output_dir = self._generate(tmp_path)

        content = (output_dir / "packwerk.yml").read_text()
        assert "NOT reject circular requires" in content
        assert "partially-defined module" in content

    def test_ruby_config_documents_wiring_requirement(
        self,
        tmp_path: Path,
    ) -> None:
        """Both files document the copy-to-root activation step."""
        output_dir = self._generate(tmp_path)

        packwerk = (output_dir / "packwerk.yml").read_text()
        package = (output_dir / "package.yml").read_text()
        assert "cp plans/architecture/packwerk.yml" in packwerk
        assert "bundle exec packwerk check" in packwerk
        assert "project root" in package

    def test_ruby_readme_mentions_packwerk(
        self,
        tmp_path: Path,
    ) -> None:
        """The architecture README names Packwerk and its docs."""
        output_dir = self._generate(tmp_path)

        content = (output_dir / "README.md").read_text()
        assert "Packwerk" in content
        assert "https://github.com/Shopify/packwerk" in content

    def test_ruby_run_script_probes_bundler(
        self,
        tmp_path: Path,
    ) -> None:
        """run-check.sh guards on the bundle binary before running."""
        output_dir = self._generate(tmp_path)

        content = (output_dir / "run-check.sh").read_text()
        assert "command -v bundle" in content
        assert "bundle exec packwerk check" in content

    def test_ruby_result_reports_ruby_language(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the result object records the ruby language."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        result = generator.generate(language="ruby", project_name="my-gem")

        assert result.language == "ruby"
        assert len(result.files_created) == 4


class TestArchitectureEnforcementGeneratorTypeScript:
    """Test TypeScript-specific architecture rules."""

    def test_typescript_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test TypeScript config enforces layer separation."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="typescript", project_name="myapp")

        dc_file = output_dir / ".dependency-cruiser.js"
        content = dc_file.read_text()

        # Should enforce layer rules
        assert "forbidden" in content or "allowed" in content

    def test_typescript_config_prevents_circular_dependencies(
        self,
        tmp_path: Path,
    ) -> None:
        """Test TypeScript config prevents circular dependencies."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="typescript", project_name="myapp")

        dc_file = output_dir / ".dependency-cruiser.js"
        content = dc_file.read_text()

        # Should check for circular dependencies
        assert "circular" in content.lower() or "cycle" in content.lower()


class TestLanguageTooling:
    """Test the shared _LanguageTooling / _LANGUAGE_TOOLING metadata."""

    @pytest.mark.parametrize(
        ("language", "expected_display"),
        [
            ("python", "Python"),
            ("typescript", "TypeScript"),
            ("go", "Go"),
            ("rust", "Rust"),
            ("swift", "Swift"),
            ("kotlin", "Kotlin"),
            ("cpp", "C/C++"),
            ("java", "Java"),
            ("csharp", "C#"),
            ("ruby", "Ruby"),
        ],
    )
    def test_each_tooling_carries_a_display_name(
        self, language: str, expected_display: str
    ) -> None:
        """Display name is a single-source-of-truth field on the dataclass."""
        assert _LANGUAGE_TOOLING[language].display_name == expected_display

    @pytest.mark.parametrize(
        "language", ["python", "typescript", "go", "rust", "swift", "cpp"]
    )
    def test_run_cmd_is_a_config_file_template(self, language: str) -> None:
        """run_cmd holds a {config_file} placeholder, not a literal path."""
        tooling = _LANGUAGE_TOOLING[language]
        assert "{config_file}" in tooling.run_cmd
        # Filling the template reproduces the bare-config invocation.
        filled = tooling.run_cmd.format(config_file=tooling.config_file)
        assert tooling.config_file in filled
        assert "{config_file}" not in filled

    def test_kotlin_install_cmd_carries_the_config_path(self) -> None:
        """Kotlin references its config via install_cmd, not run_cmd.

        Konsist's 'config' is a JUnit test compiled into the project, so
        the Gradle run command takes no config-file flag. The wiring step
        (copying the template into the test source set) lives in
        install_cmd instead, which is what run-check.sh and the README
        surface to users.
        """
        tooling = _LANGUAGE_TOOLING["kotlin"]
        assert "{config_file}" not in tooling.run_cmd
        assert f"plans/architecture/{tooling.config_file}" in tooling.install_cmd

    def test_java_install_cmd_carries_the_config_path(self) -> None:
        """Java references its config via install_cmd, not run_cmd (#367).

        ArchUnit's 'config' is a JUnit test compiled into the project —
        the Konsist precedent — so the Maven run command takes no
        config-file flag and the wiring step (copying the template into
        src/test/java) lives in install_cmd.
        """
        tooling = _LANGUAGE_TOOLING["java"]
        assert "{config_file}" not in tooling.run_cmd
        assert f"plans/architecture/{tooling.config_file}" in tooling.install_cmd

    def test_csharp_install_cmd_carries_the_config_path(self) -> None:
        """C# references its config via install_cmd, not run_cmd (#370).

        NetArchTest's 'config' is an xUnit test compiled into the
        project — the Konsist/ArchUnit precedent — so the dotnet run
        command takes no config-file flag and the wiring step (the flat
        copy into tests/) lives in install_cmd. Unlike javac, C#
        namespaces carry no directory-matching requirement, so the
        flat copy needs no {package_path} resolution.
        """
        tooling = _LANGUAGE_TOOLING["csharp"]
        assert "{config_file}" not in tooling.run_cmd
        assert f"plans/architecture/{tooling.config_file}" in tooling.install_cmd
        assert "{package_path}" not in tooling.install_cmd

    def test_ruby_install_cmd_carries_the_config_path(self) -> None:
        """Ruby references its config via install_cmd, not run_cmd (#373).

        Packwerk reads packwerk.yml from the working directory (no
        config flag exists), so the run command takes no config-file
        placeholder and the wiring step — copying packwerk.yml and the
        root package.yml to the project root — lives in install_cmd,
        the Konsist/ArchUnit/NetArchTest parked-template precedent.
        """
        tooling = _LANGUAGE_TOOLING["ruby"]
        assert "{config_file}" not in tooling.run_cmd
        assert f"plans/architecture/{tooling.config_file}" in tooling.install_cmd
        assert "package.yml" in tooling.install_cmd
        assert "{package_path}" not in tooling.install_cmd

    def test_java_install_cmd_resolves_package_matched_path(self) -> None:
        """Java's install command targets the package-matching directory.

        javac requires ArchitectureTest.java to live in the directory
        matching its declared package; a flat copy into src/test/java/
        is a guaranteed compile error (kotlinc tolerates the flat copy,
        javac does not).
        """
        cmd = ArchitectureEnforcementGenerator._resolved_install_cmd(
            "java", "my-watch-app"
        )
        assert "mkdir -p src/test/java/com/example/my_watch_app/architecture" in cmd
        assert "src/test/java/com/example/my_watch_app/architecture/" in cmd
        assert "{package_path}" not in cmd

    def test_non_java_install_cmds_pass_through_unchanged(self) -> None:
        """Languages without the placeholder return their command as-is."""
        for language in ("python", "kotlin", "cpp"):
            cmd = ArchitectureEnforcementGenerator._resolved_install_cmd(
                language, "my-app"
            )
            assert cmd == _LANGUAGE_TOOLING[language].install_cmd

    def test_build_run_script_uses_display_name_not_a_dict(self) -> None:
        """_build_run_script reads display_name from the dataclass."""
        for language in _LANGUAGE_TOOLING:
            script = ArchitectureEnforcementGenerator._build_run_script(
                language, "my-app"
            )
            assert _LANGUAGE_TOOLING[language].display_name in script

    def test_build_run_script_prefixes_config_via_template(self) -> None:
        """The plans/architecture prefix is inserted via the template."""
        for language, tooling in _LANGUAGE_TOOLING.items():
            script = ArchitectureEnforcementGenerator._build_run_script(
                language, "my-app"
            )
            assert f"plans/architecture/{tooling.config_file}" in script

    def test_template_prefix_immune_to_substring_collision(self) -> None:
        """A config filename that is a prefix of a flag is filled correctly.

        The template approach must not misfire when ``config_file`` happens
        to be a substring of another token in ``run_cmd`` — something the
        old ``str.replace`` approach was vulnerable to.
        """
        tooling = _LanguageTooling(
            tool="phony-lint",
            config_file="arch.yml",
            install_cmd="install phony-lint",
            # 'arch.yml' is also a substring of the '--arch.yml-strict' flag.
            run_cmd="phony-lint --arch.yml-strict check {config_file}",
            docs_url="https://example.com",
            display_name="Phony",
        )
        full_cmd = tooling.run_cmd.format(
            config_file=f"plans/architecture/{tooling.config_file}",
        )
        # Only the {config_file} placeholder is expanded; the look-alike
        # flag token is left untouched.
        assert "--arch.yml-strict" in full_cmd
        assert "plans/architecture/arch.yml" in full_cmd
        assert "plans/architecture/--arch.yml-strict" not in full_cmd

    def test_supported_languages_match_tooling_keys(
        self,
        tmp_path: Path,
    ) -> None:
        """generate() accepts exactly the languages with tooling metadata.

        ``supported_languages`` is derived from ``_LANGUAGE_TOOLING`` so the
        accepted-language set and the tooling map cannot drift apart. Every
        tooling key must generate without raising, and a key-less language
        must be rejected.
        """
        generator = ArchitectureEnforcementGenerator(
            output_dir=tmp_path / "plans" / "architecture"
        )

        for language in _LANGUAGE_TOOLING:
            result = generator.generate(language=language, project_name="myapp")
            assert result.language == language

        assert "php" not in _LANGUAGE_TOOLING
        with pytest.raises(ValueError, match="Unsupported language"):
            generator.generate(language="php", project_name="myapp")
