"""Unit tests for Architecture Enforcement Generator."""

from pathlib import Path
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
        """Test generate raises ValueError for unsupported languages."""
        generator = ArchitectureEnforcementGenerator()

        with pytest.raises(ValueError, match="Unsupported language"):
            generator.generate(language="ruby", project_name="test")

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
        ],
    )
    def test_each_tooling_carries_a_display_name(
        self, language: str, expected_display: str
    ) -> None:
        """Display name is a single-source-of-truth field on the dataclass."""
        assert _LANGUAGE_TOOLING[language].display_name == expected_display

    @pytest.mark.parametrize(
        "language", ["python", "typescript", "go", "rust", "swift"]
    )
    def test_run_cmd_is_a_config_file_template(self, language: str) -> None:
        """run_cmd holds a {config_file} placeholder, not a literal path."""
        tooling = _LANGUAGE_TOOLING[language]
        assert "{config_file}" in tooling.run_cmd
        # Filling the template reproduces the bare-config invocation.
        filled = tooling.run_cmd.format(config_file=tooling.config_file)
        assert tooling.config_file in filled
        assert "{config_file}" not in filled

    def test_build_run_script_uses_display_name_not_a_dict(self) -> None:
        """_build_run_script reads display_name from the dataclass."""
        for language in _LANGUAGE_TOOLING:
            script = ArchitectureEnforcementGenerator._build_run_script(language)
            assert _LANGUAGE_TOOLING[language].display_name in script

    def test_build_run_script_prefixes_config_via_template(self) -> None:
        """The plans/architecture prefix is inserted via the template."""
        for language, tooling in _LANGUAGE_TOOLING.items():
            script = ArchitectureEnforcementGenerator._build_run_script(language)
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

        assert "ruby" not in _LANGUAGE_TOOLING
        with pytest.raises(ValueError, match="Unsupported language"):
            generator.generate(language="ruby", project_name="myapp")
