"""Integration tests for ``sgsg init --language ruby`` (#373).

Runs the full init flow once via the Typer CliRunner and asserts the
generated Ruby project tree, the Gemfile manifest, and the
quality-tooling artifacts. The AI orchestrator is patched to ``None``
so no real Anthropic API calls are made (Issue #196); the null keyring
backend is enforced globally by ``tests/conftest.py``.

These tests are structural only — they never invoke the Ruby
toolchain — so they pass on CI runners without a Ruby install,
mirroring ``test_csharp_init_integration.py`` (#370).

With #373 the quality toolchain (pre-commit config, quality scripts,
the .rubocop.yml policy companion, the Packwerk architecture configs)
is generated for ruby alongside the foundation scaffold and its CI
workflow, so this suite locks in the presence of every pipeline
artifact.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner
import yaml

from start_green_stay_green.cli import app
from start_green_stay_green.utils.ruby import ruby_module_name

# Project name chosen to exercise the hyphen sanitization path:
# wrist-ledger -> package wrist_ledger -> module WristLedger.
_PROJECT_NAME = "wrist-ledger"
_MODULE_NAME = ruby_module_name("wrist_ledger")


@pytest.fixture(scope="module")
def ruby_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run ``sgsg init --language ruby`` once and return the project root.

    Args:
        tmp_path_factory: Pytest factory for a module-scoped temp directory.

    Returns:
        Path to the generated project directory.
    """
    output_dir = tmp_path_factory.mktemp("ruby-init")
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
                "ruby",
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
        )
    assert result.exit_code == 0, f"sgsg init failed for ruby: {result.output}"
    return output_dir / _PROJECT_NAME


class TestRubyInitTree:
    """Assert the generated Ruby project tree."""

    def test_project_directory_created(self, ruby_project: Path) -> None:
        """Init creates the project directory."""
        assert ruby_project.is_dir()

    @pytest.mark.parametrize(
        "relative_path",
        [
            "Gemfile",
            "lib/wrist_ledger.rb",
            "spec/wrist_ledger_spec.rb",
            "spec/spec_helper.rb",
            "README.md",
            # The CI workflow is real: ci.py has a ruby config and
            # reference/ci/ruby.yml backs it.
            ".github/workflows/ci.yml",
        ],
    )
    def test_expected_file_generated(
        self, ruby_project: Path, relative_path: str
    ) -> None:
        """Every expected ruby project file exists and is non-empty."""
        file_path = ruby_project / relative_path
        assert file_path.is_file(), f"Missing {relative_path}"
        assert file_path.read_text(), f"Empty {relative_path}"

    @pytest.mark.parametrize(
        "relative_path",
        [
            # Quality tooling (#373) is now generated alongside the
            # foundation scaffold.
            ".pre-commit-config.yaml",
            ".rubocop.yml",
            "scripts/check-all.sh",
            "scripts/format.sh",
            "scripts/lint.sh",
            "scripts/test.sh",
            "scripts/security.sh",
            "plans/architecture/packwerk.yml",
            "plans/architecture/package.yml",
            "plans/architecture/run-check.sh",
        ],
    )
    def test_quality_tooling_artifact_generated(
        self, ruby_project: Path, relative_path: str
    ) -> None:
        """#373 quality-tooling artifacts exist and are non-empty."""
        file_path = ruby_project / relative_path
        assert file_path.is_file(), f"Missing {relative_path}"
        assert file_path.read_text(), f"Empty {relative_path}"

    @pytest.mark.parametrize(
        "relative_path",
        [
            # The metrics dashboard is opt-in (--enable-live-dashboard).
            "docs/metrics.json",
            # No lockfile or gemspec is generated (plain-Ruby scaffold;
            # the lockfile materializes on the user's first
            # `bundle install`).
            "Gemfile.lock",
            f"{_PROJECT_NAME}.gemspec",
        ],
    )
    def test_out_of_scope_artifact_not_generated(
        self, ruby_project: Path, relative_path: str
    ) -> None:
        """The scaffold must not emit opt-in or unadvertised artifacts."""
        assert not (ruby_project / relative_path).exists()


class TestRubyInitQualityTooling:
    """Assert the generated quality-tooling configs are valid (#373)."""

    def test_precommit_config_parses_and_includes_rubocop_hook(
        self, ruby_project: Path
    ) -> None:
        """.pre-commit-config.yaml parses and wires the Ruby toolchain."""
        content = (ruby_project / ".pre-commit-config.yaml").read_text()
        parsed = yaml.safe_load(
            "\n".join(line for line in content.split("\n") if not line.startswith("#"))
        )
        rubocop_repo = next(
            repo
            for repo in parsed["repos"]
            if "rubocop/rubocop" in repo.get("repo", "")
        )
        hook_ids = {hook["id"] for hook in rubocop_repo["hooks"]}
        assert hook_ids == {"rubocop"}

    def test_precommit_rubocop_hook_is_check_mode(self, ruby_project: Path) -> None:
        """The rubocop hook can actually fail on offenses.

        The upstream manifest defaults to --autocorrect (fixing mode);
        the generated hook must override args to plain check-mode so
        offenses fail the commit (scripts/format.sh keeps the fixing
        path).
        """
        content = (ruby_project / ".pre-commit-config.yaml").read_text()
        parsed = yaml.safe_load(
            "\n".join(line for line in content.split("\n") if not line.startswith("#"))
        )
        rubocop_repo = next(
            repo
            for repo in parsed["repos"]
            if "rubocop/rubocop" in repo.get("repo", "")
        )
        hook = next(h for h in rubocop_repo["hooks"] if h["id"] == "rubocop")
        assert "--autocorrect" not in hook.get("args", [])

    def test_rubocop_config_carries_the_complexity_bound(
        self, ruby_project: Path
    ) -> None:
        """.rubocop.yml is the single home of the <=10 bound."""
        parsed = yaml.safe_load((ruby_project / ".rubocop.yml").read_text())
        assert parsed["Metrics/CyclomaticComplexity"]["Max"] == 10

    def test_spec_helper_carries_the_coverage_bound(self, ruby_project: Path) -> None:
        """spec_helper.rb is the single home of the >=90% coverage bound."""
        content = (ruby_project / "spec" / "spec_helper.rb").read_text()
        assert "minimum_coverage 90" in content
        assert 'if ENV["COVERAGE"]' in content

    def test_check_all_script_runs_the_ruby_toolchain(self, ruby_project: Path) -> None:
        """check-all.sh chains format, lint, coverage-gated tests, security."""
        content = (ruby_project / "scripts" / "check-all.sh").read_text()
        assert 'run_check "Tests" "test.sh" --coverage' in content

    def test_architecture_configs_parse_and_document_limits(
        self, ruby_project: Path
    ) -> None:
        """The Packwerk configs parse as YAML and disclose their limits."""
        packwerk = ruby_project / "plans" / "architecture" / "packwerk.yml"
        package = ruby_project / "plans" / "architecture" / "package.yml"
        packwerk_parsed = yaml.safe_load(packwerk.read_text())
        package_parsed = yaml.safe_load(package.read_text())
        assert packwerk_parsed["package_paths"] == "**/"
        assert package_parsed["enforce_dependencies"] is True
        # Honest enforcement-limit disclosure (no overclaiming).
        assert "Zeitwerk" in packwerk.read_text()
        assert "NOT reject circular requires" in packwerk.read_text()


class TestRubyInitManifest:
    """Assert the Gemfile manifest and the CI workflow."""

    def test_gemfile_pins_the_quality_toolchain(self, ruby_project: Path) -> None:
        """The Gemfile declares the pinned #373 quality gems."""
        content = (ruby_project / "Gemfile").read_text()
        for gem_name in ("rspec", "simplecov", "rubocop", "bundler-audit", "packwerk"):
            assert f'gem "{gem_name}"' in content

    def test_ci_workflow_parses_and_gates_via_spec_helper(
        self, ruby_project: Path
    ) -> None:
        """ci.yml parses as YAML and never restates the coverage bound.

        The >=90% number lives in spec/spec_helper.rb (single home), so
        the CI coverage step only sets COVERAGE=true.
        """
        content = (ruby_project / ".github" / "workflows" / "ci.yml").read_text()
        parsed = yaml.safe_load(content)
        assert parsed["name"] == "Ruby Quality Checks"
        assert "COVERAGE=true bundle exec rspec" in content
        assert "--minimum-coverage" not in content

    def test_ci_matrix_runs_only_maintained_rubies(self, ruby_project: Path) -> None:
        """The Ruby matrix has no EOL entries.

        3.1 and 3.2 reached upstream EOL (verified against
        ruby-lang.org, 2026-06), so their matrix legs would test
        unsupported runtimes.
        """
        content = (ruby_project / ".github" / "workflows" / "ci.yml").read_text()
        parsed = yaml.safe_load(content)
        matrix = parsed["jobs"]["quality"]["strategy"]["matrix"]["ruby-version"]
        assert "3.1" not in matrix
        assert "3.2" not in matrix
        assert matrix, "matrix must not be empty"

    def test_ci_runs_bundler_audit_not_brakeman(self, ruby_project: Path) -> None:
        """CI gates on bundler-audit; Brakeman would error on plain Ruby.

        brakeman exits with an error when pointed at a non-Rails
        project, so a Brakeman step would be red on every push of the
        generated scaffold.
        """
        content = (ruby_project / ".github" / "workflows" / "ci.yml").read_text()
        assert "bundler-audit check" in content
        assert "bundle exec brakeman" not in content

    def test_ci_codecov_upload_cannot_fail_a_fresh_project(
        self, ruby_project: Path
    ) -> None:
        """The Codecov upload is best-effort in generated projects.

        A fresh `green init` project ships no CODECOV_TOKEN secret, so
        `fail_ci_if_error: true` would start the project red; the real
        coverage gate is the spec_helper-backed SimpleCov run (#368
        lesson). The action is pinned to >=v6 (the #435 note).
        """
        content = (ruby_project / ".github" / "workflows" / "ci.yml").read_text()
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
            action_version = int(step["uses"].rsplit("@v", maxsplit=1)[1])
            assert action_version >= 6


class TestRubyInitSources:
    """Assert the generated Ruby source and spec files."""

    def test_lib_module_name_and_entry_point(self, ruby_project: Path) -> None:
        """lib/wrist_ledger.rb declares the shared module with .hello."""
        source = (ruby_project / "lib" / "wrist_ledger.rb").read_text()
        assert f"module {_MODULE_NAME}" in source
        assert "def self.hello" in source
        assert f'"Hello from {_PROJECT_NAME}!"' in source

    def test_generated_spec_resolves_the_module(self, ruby_project: Path) -> None:
        """The spec describes the module the lib file declares.

        Both sides derive the constant from utils.ruby.ruby_module_name
        (#373) — the pre-#373 spec described a constant that did not
        exist and called a method the lib never defined.
        """
        source = (ruby_project / "spec" / "wrist_ledger_spec.rb").read_text()
        assert f"RSpec.describe {_MODULE_NAME}" in source
        assert "described_class.hello" in source
        assert 'require_relative "../lib/wrist_ledger"' in source


class TestRubyInitReadme:
    """Assert the generated README stays truthful (#373)."""

    def test_readme_advertises_373_tooling_as_real(self, ruby_project: Path) -> None:
        """README advertises the now-generated #373 quality tooling.

        Every artifact the README checkmarks must exist next to it —
        the truthfulness contract.
        """
        readme = (ruby_project / "README.md").read_text()
        assert "./scripts/check-all.sh" in readme
        assert (ruby_project / "scripts" / "check-all.sh").is_file()
        assert "plans/architecture" in readme
        assert (ruby_project / "plans" / "architecture" / "packwerk.yml").is_file()
        assert ".github/workflows/ci.yml" in readme
        assert (ruby_project / ".github" / "workflows" / "ci.yml").is_file()

    def test_readme_structure_block_is_truthful(self, ruby_project: Path) -> None:
        """README never names tools or files the scaffold does not emit."""
        readme = (ruby_project / "README.md").read_text()
        assert "Reek" not in readme
        assert "Sorbet" not in readme
        assert "Gemfile.lock" not in readme
        assert "lib/main.rb" not in readme


class TestRubyInitConsoleOutput:
    """Assert init's console output reflects the #373 wiring."""

    def test_init_skips_no_pipeline_steps(self, tmp_path: Path) -> None:
        """Init prints no skip notice for any ruby pipeline step.

        The pre-commit, scripts, and architecture steps gained ruby
        support with #373 (CI has been real since the foundation), so
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
                    "ruby",
                    "--output-dir",
                    str(tmp_path),
                    "--no-interactive",
                ],
            )
        assert result.exit_code == 0
        assert "Pre-commit config unavailable for ruby" not in result.output
        assert "Quality scripts unavailable for ruby" not in result.output
        assert "Architecture rules unavailable for ruby" not in result.output
        assert "CI pipeline unavailable for ruby" not in result.output
        assert "Generated CI pipeline" in result.output
