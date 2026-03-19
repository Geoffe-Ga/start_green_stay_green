"""Tests for generator integration with FileWriter.

Verifies that generators skip existing files when a FileWriter is provided,
and maintain backward compatibility without one.
"""

from pathlib import Path

import pytest
from rich.console import Console

from start_green_stay_green.generators.dependencies import DependenciesGenerator
from start_green_stay_green.generators.dependencies import DependencyConfig
from start_green_stay_green.generators.readme import ReadmeConfig
from start_green_stay_green.generators.readme import ReadmeGenerator
from start_green_stay_green.generators.scripts import ScriptConfig
from start_green_stay_green.generators.scripts import ScriptsGenerator
from start_green_stay_green.generators.structure import StructureConfig
from start_green_stay_green.generators.structure import StructureGenerator
from start_green_stay_green.generators.tests_gen import (
    TestsGenerator as GenTestsGenerator,
)
from start_green_stay_green.generators.tests_gen import TestsConfig as GenTestsConfig
from start_green_stay_green.utils.file_writer import FileWriter


@pytest.fixture
def quiet_writer(tmp_path: Path) -> FileWriter:
    """Create a FileWriter with quiet console output."""
    return FileWriter(
        project_root=tmp_path,
        console=Console(quiet=True),
    )


@pytest.fixture
def python_structure_config() -> StructureConfig:
    """Create a Python StructureConfig for testing."""
    return StructureConfig(
        project_name="test-project",
        language="python",
        package_name="test_project",
    )


class TestStructureGeneratorWithFileWriter:
    """Test StructureGenerator additive behavior with FileWriter."""

    def test_skips_existing_files(
        self,
        tmp_path: Path,
        quiet_writer: FileWriter,
        python_structure_config: StructureConfig,
    ) -> None:
        """Test StructureGenerator skips files that already exist."""
        # Pre-create one of the files that would be generated
        pkg_dir = tmp_path / "test_project"
        pkg_dir.mkdir()
        init_file = pkg_dir / "__init__.py"
        init_file.write_text("# custom content")

        generator = StructureGenerator(
            tmp_path, python_structure_config, file_writer=quiet_writer
        )
        generator.generate()

        # __init__.py should be preserved
        assert init_file.read_text() == "# custom content"
        # main.py should be created
        assert (pkg_dir / "main.py").exists()
        assert quiet_writer.skipped >= 1
        assert quiet_writer.created >= 1

    def test_backward_compatible_without_file_writer(
        self,
        tmp_path: Path,
        python_structure_config: StructureConfig,
    ) -> None:
        """Test StructureGenerator works without FileWriter (backward compat)."""
        generator = StructureGenerator(tmp_path, python_structure_config)
        result = generator.generate()

        assert result
        assert (tmp_path / "test_project" / "__init__.py").exists()
        assert (tmp_path / "test_project" / "main.py").exists()

    def test_overwrites_when_no_file_writer(
        self,
        tmp_path: Path,
        python_structure_config: StructureConfig,
    ) -> None:
        """Test without FileWriter, existing files are overwritten (old behavior)."""
        pkg_dir = tmp_path / "test_project"
        pkg_dir.mkdir()
        init_file = pkg_dir / "__init__.py"
        init_file.write_text("# custom content")

        generator = StructureGenerator(tmp_path, python_structure_config)
        generator.generate()

        # Without FileWriter, the file should be overwritten
        assert init_file.read_text() != "# custom content"


class TestDependenciesGeneratorWithFileWriter:
    """Test DependenciesGenerator additive behavior with FileWriter."""

    def test_skips_existing_pyproject_toml(
        self,
        tmp_path: Path,
        quiet_writer: FileWriter,
    ) -> None:
        """Test DependenciesGenerator skips existing pyproject.toml."""
        config = DependencyConfig(
            project_name="test-project",
            language="python",
            package_name="test_project",
        )
        (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n# custom config")

        generator = DependenciesGenerator(tmp_path, config, file_writer=quiet_writer)
        generator.generate()

        assert (tmp_path / "pyproject.toml").read_text() == (
            "[tool.ruff]\n# custom config"
        )
        assert quiet_writer.skipped >= 1


class TestTestsGeneratorWithFileWriter:
    """Test TestsGenerator additive behavior with FileWriter."""

    def test_skips_existing_test_file(
        self,
        tmp_path: Path,
        quiet_writer: FileWriter,
    ) -> None:
        """Test TestsGenerator skips existing test files."""
        config = GenTestsConfig(
            project_name="test-project",
            language="python",
            package_name="test_project",
        )
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_main.py"
        test_file.write_text("# my custom tests")

        generator = GenTestsGenerator(tmp_path, config, file_writer=quiet_writer)
        generator.generate()

        assert test_file.read_text() == "# my custom tests"
        assert quiet_writer.skipped >= 1


class TestReadmeGeneratorWithFileWriter:
    """Test ReadmeGenerator additive behavior with FileWriter."""

    def test_skips_existing_readme(
        self,
        tmp_path: Path,
        quiet_writer: FileWriter,
    ) -> None:
        """Test ReadmeGenerator skips existing README.md."""
        config = ReadmeConfig(
            project_name="test-project",
            language="python",
            package_name="test_project",
        )
        (tmp_path / "README.md").write_text("# My Custom README")

        generator = ReadmeGenerator(tmp_path, config, file_writer=quiet_writer)
        generator.generate()

        assert (tmp_path / "README.md").read_text() == "# My Custom README"
        assert quiet_writer.skipped == 1
        assert quiet_writer.created == 0


class TestScriptsGeneratorWithFileWriter:
    """Test ScriptsGenerator additive behavior with FileWriter."""

    def test_skips_existing_scripts(
        self,
        tmp_path: Path,
        quiet_writer: FileWriter,
    ) -> None:
        """Test ScriptsGenerator skips existing script files."""
        config = ScriptConfig(
            language="python",
            package_name="test_project",
        )
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.sh").write_text("#!/bin/bash\n# custom test script")

        generator = ScriptsGenerator(
            output_dir=scripts_dir,
            config=config,
            file_writer=quiet_writer,
        )
        generator.generate()

        # test.sh should be preserved
        assert (scripts_dir / "test.sh").read_text() == (
            "#!/bin/bash\n# custom test script"
        )
        assert quiet_writer.skipped >= 1
        # Other scripts should be created
        assert quiet_writer.created >= 1


class TestMixedScenario:
    """Test mixed scenario: some files exist, some don't."""

    def test_empty_directory_creates_all(
        self,
        tmp_path: Path,
        quiet_writer: FileWriter,
        python_structure_config: StructureConfig,
    ) -> None:
        """Test in empty directory, all files are created."""
        generator = StructureGenerator(
            tmp_path, python_structure_config, file_writer=quiet_writer
        )
        generator.generate()

        assert quiet_writer.created == 2  # __init__.py + main.py
        assert quiet_writer.skipped == 0

    def test_all_files_exist_skips_all(
        self,
        tmp_path: Path,
        quiet_writer: FileWriter,
        python_structure_config: StructureConfig,
    ) -> None:
        """Test when all files exist, everything is skipped."""
        # Pre-create all files
        pkg_dir = tmp_path / "test_project"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("# existing")
        (pkg_dir / "main.py").write_text("# existing")

        generator = StructureGenerator(
            tmp_path, python_structure_config, file_writer=quiet_writer
        )
        generator.generate()

        assert quiet_writer.created == 0
        assert quiet_writer.skipped == 2
