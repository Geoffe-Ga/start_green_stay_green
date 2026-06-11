"""Tests for the mutation gate (port of scripts/mutation.sh)."""

import json
from pathlib import Path
import sqlite3

import pytest

from start_green_stay_green.gates import common
from start_green_stay_green.gates import mutation
from tests.unit.gates.conftest import FakeRunner
from tests.unit.gates.conftest import completed

PROGRESS_OUTPUT = "200/200  🎉 180  ⏰ 5  🤔 3  🙁 12  🔇 0\n"


def write_cache(directory: Path, statuses: list[str]) -> None:
    """Create a mutmut-style SQLite cache with the given status rows."""
    path = directory / mutation.CACHE_FILE
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE Mutant (status TEXT)")
    connection.executemany(
        "INSERT INTO Mutant (status) VALUES (?)",
        [(status,) for status in statuses],
    )
    connection.commit()
    connection.close()


@pytest.fixture
def fake_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the gate at a throwaway project root."""
    monkeypatch.setattr(common, "project_root", lambda: tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.usefixtures("fake_tools")
class TestFilterPaths:
    def test_keeps_existing_package_sources(self) -> None:
        assert mutation.filter_paths(["start_green_stay_green/cli.py"]) == [
            "start_green_stay_green/cli.py"
        ]

    def test_drops_test_files_and_non_python(self) -> None:
        assert not mutation.filter_paths(
            [
                "tests/unit/test_cli.py",
                "README.md",
                "start_green_stay_green/missing-file.py",
            ]
        )

    def test_keeps_nested_package_sources(self) -> None:
        nested = "start_green_stay_green/gates/common.py"
        assert mutation.filter_paths([nested]) == [nested]


@pytest.mark.usefixtures("fake_tools")
class TestCacheQuery:
    def test_counts_by_status(self, fake_root: Path) -> None:
        write_cache(
            fake_root,
            ["ok_killed"] * 8 + ["bad_survived"] * 2 + ["bad_timeout"],
        )
        assert mutation.query_cache() == {
            "killed": 8,
            "survived": 2,
            "suspicious": 0,
            "timeout": 1,
            "untested": 0,
        }

    @pytest.mark.usefixtures("fake_root")
    def test_missing_cache_returns_none(self) -> None:
        assert mutation.query_cache() is None

    def test_unreadable_cache_returns_none(self, fake_root: Path) -> None:
        cache = fake_root / mutation.CACHE_FILE
        cache.write_text("not a database")
        assert mutation.query_cache() is None


@pytest.mark.usefixtures("fake_tools")
class TestProgressFallback:
    def test_parses_emoji_progress_line(self) -> None:
        counts = mutation.parse_progress_fallback(PROGRESS_OUTPUT)
        assert counts == {
            "killed": 180,
            "survived": 12,
            "suspicious": 3,
            "timeout": 5,
            "untested": 0,
        }

    def test_no_progress_line_returns_none(self) -> None:
        assert mutation.parse_progress_fallback("nothing useful") is None


@pytest.mark.usefixtures("fake_tools")
class TestMutationGate:
    def test_passing_score(
        self,
        fake_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        write_cache(fake_root, ["ok_killed"] * 9 + ["bad_survived"])
        monkeypatch.setattr(common, "stream_tool", lambda _cmd: (0, ""))
        assert mutation.main([]) == 0
        out = capsys.readouterr().out
        assert "=== Running Mutation Tests ===" in out
        assert "Minimum required score: 80%" in out
        assert "Mutation Score: 90.0% (of tested mutants)" in out
        assert "✓ Mutation score meets minimum threshold" in out
        assert "Note: 1 mutants survived" in out

    def test_failing_score_shows_first_survivor(
        self,
        fake_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        write_cache(fake_root, ["ok_killed"] + ["bad_survived"] * 9)
        monkeypatch.setattr(common, "stream_tool", lambda _cmd: (1, ""))
        show_output = "\n".join(f"line {i}" for i in range(30))
        runner = FakeRunner(completed(0, stdout=show_output))
        monkeypatch.setattr(common, "run_tool", runner)
        assert mutation.main([]) == 1
        captured = capsys.readouterr()
        assert "✗ Mutation score below minimum threshold" in captured.err
        assert "Your test suite killed 10.0% of mutants" in captured.err
        assert "Surviving mutants:" in captured.err
        assert "line 19" in captured.err
        assert "line 20" not in captured.err
        assert runner.calls == [["/fake/mutmut", "show", "1"]]

    def test_min_score_override(
        self,
        fake_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        write_cache(fake_root, ["ok_killed", "bad_survived"])
        monkeypatch.setattr(common, "stream_tool", lambda _cmd: (1, ""))
        assert mutation.main(["--min-score", "40"]) == 0
        assert "Required:       40%" in capsys.readouterr().out

    def test_no_mutants_generated_skips_validation(
        self,
        fake_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        write_cache(fake_root, [])
        monkeypatch.setattr(common, "stream_tool", lambda _cmd: (0, ""))
        assert mutation.main([]) == 0
        captured = capsys.readouterr()
        assert "Warning: No mutants were generated" in captured.err
        assert "Skipping mutation score validation" in captured.out

    def test_all_untested_skips_validation(
        self,
        fake_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        write_cache(fake_root, ["untested"] * 5)
        monkeypatch.setattr(common, "stream_tool", lambda _cmd: (0, ""))
        assert mutation.main([]) == 0
        captured = capsys.readouterr()
        assert "Warning: No mutants were tested" in captured.err
        assert "All 5 mutants are untested" in captured.out

    def test_progress_fallback_when_cache_unreadable(
        self,
        fake_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (fake_root / mutation.CACHE_FILE).write_text("not a database")
        monkeypatch.setattr(common, "stream_tool", lambda _cmd: (1, PROGRESS_OUTPUT))
        assert mutation.main([]) == 0
        captured = capsys.readouterr()
        assert "Warning: Could not query cache" in captured.err
        assert "Mutation Score: 90.0% (of tested mutants)" in captured.out

    @pytest.mark.usefixtures("fake_root")
    def test_unparseable_results_exit_2(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "stream_tool", lambda _cmd: (1, "no data"))
        assert mutation.main([]) == 2
        assert "Could not parse mutation results" in capsys.readouterr().err

    @pytest.mark.usefixtures("fake_root")
    def test_missing_mutmut_exits_2(
        self, fake_tools: dict[str, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_tools["mutmut"] = ""
        assert mutation.main([]) == 2
        err = capsys.readouterr().err
        assert "mutmut is not installed" in err
        assert "pip install mutmut" in err

    @pytest.mark.usefixtures("fake_root")
    def test_paths_filtered_to_nothing_skips(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert mutation.main(["--paths-to-mutate", "README.md"]) == 0
        out = capsys.readouterr().out
        assert "No Python source files to mutate" in out
        assert "Skipping mutation testing" in out

    def test_paths_passed_to_mutmut(
        self,
        fake_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        target = fake_root / "start_green_stay_green" / "mod.py"
        target.parent.mkdir(parents=True)
        target.write_text("x = 1\n")
        write_cache(fake_root, ["ok_killed"])
        commands: list[list[str]] = []

        def fake_stream(cmd: list[str]) -> tuple[int, str]:
            commands.append(cmd)
            return (0, "")

        monkeypatch.setattr(common, "stream_tool", fake_stream)
        rel = "start_green_stay_green/mod.py"
        assert mutation.main(["--paths-to-mutate", rel]) == 0
        assert commands == [["/fake/mutmut", "run", f"--paths-to-mutate={rel}"]]
        assert f"Mutating specific files: {rel}" in capsys.readouterr().out

    def test_interrupt_cleans_cache(
        self, fake_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_cache(fake_root, ["ok_killed"])

        def interrupted(_cmd: list[str]) -> tuple[int, str]:
            raise KeyboardInterrupt

        monkeypatch.setattr(common, "stream_tool", interrupted)
        with pytest.raises(KeyboardInterrupt):
            mutation.main([])
        assert not (fake_root / mutation.CACHE_FILE).exists()


@pytest.mark.usefixtures("fake_tools")
class TestMutationMetrics:
    @pytest.mark.usefixtures("fake_root")
    def test_metrics_without_cache(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert mutation.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload == {
            "killed": None,
            "survived": None,
            "timeout": None,
            "score": None,
        }

    def test_metrics_from_cache(
        self, fake_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write_cache(
            fake_root,
            ["ok_killed"] * 8 + ["bad_survived"] + ["bad_timeout"],
        )
        assert mutation.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload == {
            "killed": 8,
            "survived": 1,
            "timeout": 1,
            "score": 80.0,
        }
