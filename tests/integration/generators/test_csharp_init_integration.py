"""Integration tests for ``sgsg init --language csharp`` (#370).

Runs the full init flow once via the Typer CliRunner and asserts the
generated C# project tree, the SDK-style csproj manifest, and the
quality-tooling artifacts. The AI orchestrator is patched to ``None``
so no real Anthropic API calls are made (Issue #196); the null keyring
backend is enforced globally by ``tests/conftest.py``.

These tests are structural only — they never invoke the dotnet CLI —
so they pass on CI runners without a .NET SDK, mirroring
``test_java_init_integration.py`` (#367).

With #370 the quality toolchain (pre-commit config, quality scripts,
the .editorconfig/CodeMetricsConfig.txt analyzer companions,
architecture rules) is generated for csharp alongside the foundation
scaffold and its CI workflow, so this suite locks in the presence of
every pipeline artifact.
"""

from pathlib import Path
from unittest.mock import patch

from defusedxml import ElementTree as DefusedElementTree
import pytest
from typer.testing import CliRunner
import yaml

from start_green_stay_green.cli import app
from start_green_stay_green.utils.csharp import csharp_namespace

# Project name chosen to exercise the hyphen sanitization path:
# wrist-ledger -> package wrist_ledger -> namespace WristLedger.
_PROJECT_NAME = "wrist-ledger"
_NAMESPACE = csharp_namespace("wrist_ledger")


@pytest.fixture(scope="module")
def csharp_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run ``sgsg init --language csharp`` once and return the project root.

    Args:
        tmp_path_factory: Pytest factory for a module-scoped temp directory.

    Returns:
        Path to the generated project directory.
    """
    output_dir = tmp_path_factory.mktemp("csharp-init")
    runner = CliRunner()
    with patch(
        "start_green_stay_green.cli._initialize_orchestrator", return_value=None
    ):
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                _PROJECT_NAME,
                "--language",
                "csharp",
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
        )
    assert result.exit_code == 0, f"sgsg init failed for csharp: {result.output}"
    return output_dir / _PROJECT_NAME


class TestCsharpInitTree:
    """Assert the generated C# project tree."""

    def test_project_directory_created(self, csharp_project: Path) -> None:
        """Init creates the project directory."""
        assert csharp_project.is_dir()

    @pytest.mark.parametrize(
        "relative_path",
        [
            f"{_PROJECT_NAME}.csproj",
            "src/Program.cs",
            "tests/MainTests.cs",
            "README.md",
            # The CI workflow is real: ci.py has a csharp config and
            # reference/ci/csharp.yml backs it.
            ".github/workflows/ci.yml",
        ],
    )
    def test_expected_file_generated(
        self, csharp_project: Path, relative_path: str
    ) -> None:
        """Every expected csharp project file exists and is non-empty."""
        file_path = csharp_project / relative_path
        assert file_path.is_file(), f"Missing {relative_path}"
        assert file_path.read_text(), f"Empty {relative_path}"

    @pytest.mark.parametrize(
        "relative_path",
        [
            # Quality tooling (#370) is now generated alongside the
            # foundation scaffold.
            ".pre-commit-config.yaml",
            ".editorconfig",
            "CodeMetricsConfig.txt",
            "scripts/check-all.sh",
            "scripts/format.sh",
            "scripts/lint.sh",
            "scripts/test.sh",
            "scripts/security.sh",
            "plans/architecture/ArchitectureTest.cs",
            "plans/architecture/run-check.sh",
        ],
    )
    def test_quality_tooling_artifact_generated(
        self, csharp_project: Path, relative_path: str
    ) -> None:
        """#370 quality-tooling artifacts exist and are non-empty."""
        file_path = csharp_project / relative_path
        assert file_path.is_file(), f"Missing {relative_path}"
        assert file_path.read_text(), f"Empty {relative_path}"

    @pytest.mark.parametrize(
        "relative_path",
        [
            # The metrics dashboard is opt-in (--enable-live-dashboard).
            "docs/metrics.json",
            # No solution file is generated (single-project layout).
            f"{_PROJECT_NAME}.sln",
        ],
    )
    def test_out_of_scope_artifact_not_generated(
        self, csharp_project: Path, relative_path: str
    ) -> None:
        """The scaffold must not emit opt-in or unadvertised artifacts."""
        assert not (csharp_project / relative_path).exists()


class TestCsharpInitQualityTooling:
    """Assert the generated quality-tooling configs are valid (#370)."""

    def test_precommit_config_parses_and_includes_csharp_hooks(
        self, csharp_project: Path
    ) -> None:
        """.pre-commit-config.yaml parses and wires the C# toolchain."""
        content = (csharp_project / ".pre-commit-config.yaml").read_text()
        parsed = yaml.safe_load(
            "\n".join(line for line in content.split("\n") if not line.startswith("#"))
        )
        local_repo = next(
            repo for repo in parsed["repos"] if repo.get("repo") == "local"
        )
        hook_ids = {hook["id"] for hook in local_repo["hooks"]}
        assert {"dotnet-format", "roslyn-analyzers"} <= hook_ids

    def test_precommit_formatter_hook_is_check_mode(self, csharp_project: Path) -> None:
        """The dotnet-format hook can actually fail on unformatted code."""
        content = (csharp_project / ".pre-commit-config.yaml").read_text()
        assert "dotnet format --verify-no-changes" in content

    def test_code_metrics_config_carries_the_complexity_bound(
        self, csharp_project: Path
    ) -> None:
        """CodeMetricsConfig.txt is the single home of the <=10 bound."""
        content = (csharp_project / "CodeMetricsConfig.txt").read_text()
        assert "CA1502: 10" in content

    def test_editorconfig_enables_the_complexity_rule(
        self, csharp_project: Path
    ) -> None:
        """.editorconfig switches the otherwise-off CA1502 rule on."""
        content = (csharp_project / ".editorconfig").read_text()
        assert "dotnet_diagnostic.CA1502.severity = error" in content

    def test_check_all_script_runs_the_csharp_toolchain(
        self, csharp_project: Path
    ) -> None:
        """check-all.sh chains format, lint, coverage-gated tests, security."""
        content = (csharp_project / "scripts" / "check-all.sh").read_text()
        assert 'run_check "Tests" "test.sh" --coverage' in content

    def test_architecture_test_defines_the_layer_matrix(
        self, csharp_project: Path
    ) -> None:
        """The NetArchTest template derives its layers from the project name."""
        source = (
            csharp_project / "plans" / "architecture" / "ArchitectureTest.cs"
        ).read_text()
        assert f"namespace {_NAMESPACE}.Architecture" in source
        assert f'BaseNamespace = "{_NAMESPACE}"' in source
        assert ".HaveDependencyOnAny(" in source


class TestCsharpInitManifest:
    """Assert the csproj manifest and the CI workflow."""

    def test_csproj_is_well_formed_sdk_project(self, csharp_project: Path) -> None:
        """The csproj parses as XML rooted at an SDK-style Project."""
        content = (csharp_project / f"{_PROJECT_NAME}.csproj").read_text()
        root = DefusedElementTree.fromstring(content)
        assert root.tag == "Project"
        assert root.get("Sdk") == "Microsoft.NET.Sdk"

    def test_csproj_owns_the_quality_gates(self, csharp_project: Path) -> None:
        """The csproj pins the coverage bound and the analyzer policy."""
        content = (csharp_project / f"{_PROJECT_NAME}.csproj").read_text()
        assert "<Threshold>90</Threshold>" in content
        assert "<TreatWarningsAsErrors>true</TreatWarningsAsErrors>" in content
        assert '<AdditionalFiles Include="CodeMetricsConfig.txt" />' in content
        assert 'Include="coverlet.msbuild"' in content
        assert 'Include="NetArchTest.Rules"' in content
        assert 'Include="SecurityCodeScan.VS2019"' in content

    def test_ci_workflow_parses_and_gates_via_the_manifest(
        self, csharp_project: Path
    ) -> None:
        """ci.yml parses as YAML and never restates the coverage bound.

        The >=90% number lives in the csproj (single home), so the CI
        coverage step passes only /p:CollectCoverage=true.
        """
        content = (csharp_project / ".github" / "workflows" / "ci.yml").read_text()
        parsed = yaml.safe_load(content)
        assert parsed["name"] == "C# Quality Checks"
        assert "/p:CollectCoverage=true" in content
        assert "/p:Threshold=" not in content

    def test_ci_matrix_can_build_the_target_framework(
        self, csharp_project: Path
    ) -> None:
        """The SDK matrix has no entry older than the net8.0 target.

        An SDK 7 runner cannot build a net8.0 project, so its matrix
        leg would be red on every push.
        """
        content = (csharp_project / ".github" / "workflows" / "ci.yml").read_text()
        parsed = yaml.safe_load(content)
        matrix = parsed["jobs"]["quality"]["strategy"]["matrix"]["dotnet-version"]
        assert "7.0" not in matrix
        assert any(str(version).startswith("8") for version in matrix)

    def test_ci_codecov_upload_cannot_fail_a_fresh_project(
        self, csharp_project: Path
    ) -> None:
        """The Codecov upload is best-effort in generated projects.

        A fresh `green init` project ships no CODECOV_TOKEN secret, so
        `fail_ci_if_error: true` would start the project red; the real
        coverage gate is the csproj-backed Coverlet run (#368 lesson).
        """
        content = (csharp_project / ".github" / "workflows" / "ci.yml").read_text()
        parsed = yaml.safe_load(content)
        codecov_steps = [
            step
            for job in parsed["jobs"].values()
            for step in job["steps"]
            if "codecov" in step.get("uses", "")
        ]
        assert codecov_steps, "CI must still upload coverage to Codecov"
        for step in codecov_steps:
            assert step["with"]["fail_ci_if_error"] is False


class TestCsharpInitSources:
    """Assert the generated C# source and test files."""

    def test_program_namespace_and_visibility(self, csharp_project: Path) -> None:
        """Program.cs uses the shared namespace and a public Main."""
        source = (csharp_project / "src" / "Program.cs").read_text()
        assert f"namespace {_NAMESPACE}" in source
        assert "public static void Main" in source
        assert f'"Hello from {_PROJECT_NAME}!"' in source

    def test_generated_test_resolves_program(self, csharp_project: Path) -> None:
        """MainTests.cs nests under the Program namespace and calls Main."""
        source = (csharp_project / "tests" / "MainTests.cs").read_text()
        assert f"namespace {_NAMESPACE}.Tests" in source
        assert "Program.Main(" in source
        assert "[Fact]" in source


class TestCsharpInitReadme:
    """Assert the generated README stays truthful (#370)."""

    def test_readme_advertises_370_tooling_as_real(self, csharp_project: Path) -> None:
        """README advertises the now-generated #370 quality tooling.

        Every artifact the README checkmarks must exist next to it —
        the truthfulness contract.
        """
        readme = (csharp_project / "README.md").read_text()
        assert "./scripts/check-all.sh" in readme
        assert (csharp_project / "scripts" / "check-all.sh").is_file()
        assert "plans/architecture" in readme
        assert (
            csharp_project / "plans" / "architecture" / "ArchitectureTest.cs"
        ).is_file()
        assert ".github/workflows/ci.yml" in readme
        assert (csharp_project / ".github" / "workflows" / "ci.yml").is_file()

    def test_readme_structure_block_is_truthful(self, csharp_project: Path) -> None:
        """README never names a solution file the scaffold does not emit."""
        readme = (csharp_project / "README.md").read_text()
        assert ".sln" not in readme


class TestCsharpInitConsoleOutput:
    """Assert init's console output reflects the #370 wiring."""

    def test_init_skips_no_pipeline_steps(self, tmp_path: Path) -> None:
        """Init prints no skip notice for any csharp pipeline step.

        The pre-commit, scripts, and architecture steps gained csharp
        support with #370 (CI has been real since the foundation), so
        every "unavailable" notice must be gone.
        """
        runner = CliRunner()
        with patch(
            "start_green_stay_green.cli._initialize_orchestrator",
            return_value=None,
        ):
            result = runner.invoke(
                app,
                [
                    "init",
                    "--project-name",
                    "skip-check",
                    "--language",
                    "csharp",
                    "--output-dir",
                    str(tmp_path),
                    "--no-interactive",
                ],
            )
        assert result.exit_code == 0
        assert "Pre-commit config unavailable for csharp" not in result.output
        assert "Quality scripts unavailable for csharp" not in result.output
        assert "Architecture rules unavailable for csharp" not in result.output
        assert "CI pipeline unavailable for csharp" not in result.output
        assert "Generated CI pipeline" in result.output
