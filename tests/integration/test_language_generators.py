"""Integration tests for multi-language generator coordination.

Tests that all 4 generators (Structure, Dependencies, Tests, README) work
together for each supported language without errors, and that outputs are
internally consistent.
"""

from pathlib import Path
import tempfile

import pytest

from start_green_stay_green.generators.base import SUPPORTED_LANGUAGES
from start_green_stay_green.generators.dependencies import DependenciesGenerator
from start_green_stay_green.generators.dependencies import DependencyConfig
from start_green_stay_green.generators.readme import ReadmeConfig
from start_green_stay_green.generators.readme import ReadmeGenerator
from start_green_stay_green.generators.structure import StructureConfig
from start_green_stay_green.generators.structure import StructureGenerator
from start_green_stay_green.generators.tests_gen import TestsConfig as TConfig
from start_green_stay_green.generators.tests_gen import TestsGenerator as TGenerator


class TestAllGeneratorsMultiLanguage:
    """Test all 4 generators produce output for each supported language."""

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_all_generators_produce_output_for_language(self, lang: str) -> None:
        """Test all 4 generators work for each language without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Run StructureGenerator
            struct_config = StructureConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            struct_gen = StructureGenerator(output_dir, struct_config)
            struct_files = struct_gen.generate()
            assert struct_files, f"StructureGenerator produced no files for {lang}"

            # Run DependenciesGenerator
            dep_config = DependencyConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            dep_gen = DependenciesGenerator(output_dir, dep_config)
            dep_files = dep_gen.generate()
            assert dep_files, f"DependenciesGenerator produced no files for {lang}"

            # Run TestsGenerator
            tests_config = TConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            tests_gen = TGenerator(output_dir, tests_config)
            tests_files = tests_gen.generate()
            assert tests_files, f"TestsGenerator produced no files for {lang}"

            # Run ReadmeGenerator
            readme_config = ReadmeConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            readme_gen = ReadmeGenerator(output_dir, readme_config)
            readme_files = readme_gen.generate()
            assert readme_files, f"ReadmeGenerator produced no files for {lang}"

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_generated_files_are_consistent(self, lang: str) -> None:
        """Test generated files reference consistent package/project names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Run all 4 generators
            struct_config = StructureConfig(
                project_name="my-app",
                language=lang,
                package_name="my_app",
            )
            StructureGenerator(output_dir, struct_config).generate()

            dep_config = DependencyConfig(
                project_name="my-app",
                language=lang,
                package_name="my_app",
            )
            DependenciesGenerator(output_dir, dep_config).generate()

            tests_config = TConfig(
                project_name="my-app",
                language=lang,
                package_name="my_app",
            )
            TGenerator(output_dir, tests_config).generate()

            readme_config = ReadmeConfig(
                project_name="my-app",
                language=lang,
                package_name="my_app",
            )
            readme_files = ReadmeGenerator(output_dir, readme_config).generate()

            # README should reference the project name
            readme_content = readme_files["README.md"].read_text()
            assert (
                "my-app" in readme_content
            ), f"README missing project name 'my-app' for {lang}"

    def test_all_generators_reject_unsupported_language(self) -> None:
        """Test all 4 generators raise ValueError for unsupported language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # StructureGenerator
            struct_config = StructureConfig(
                project_name="test",
                language="brainfuck",
                package_name="test",
            )
            with pytest.raises(ValueError, match="Unsupported language"):
                StructureGenerator(output_dir, struct_config).generate()

            # DependenciesGenerator
            dep_config = DependencyConfig(
                project_name="test",
                language="brainfuck",
                package_name="test",
            )
            with pytest.raises(ValueError, match="Unsupported language"):
                DependenciesGenerator(output_dir, dep_config).generate()

            # TestsGenerator
            tests_config = TConfig(
                project_name="test",
                language="brainfuck",
                package_name="test",
            )
            with pytest.raises(ValueError, match="Unsupported language"):
                TGenerator(output_dir, tests_config).generate()

            # ReadmeGenerator
            readme_config = ReadmeConfig(
                project_name="test",
                language="brainfuck",
                package_name="test",
            )
            with pytest.raises(ValueError, match="Unsupported language"):
                ReadmeGenerator(output_dir, readme_config).generate()

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_all_generated_files_exist_on_disk(self, lang: str) -> None:
        """Test every file returned by generators actually exists on disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            all_files: dict[str, Path] = {}
            generators = [
                (
                    StructureGenerator,
                    StructureConfig(
                        project_name="test-project",
                        language=lang,
                        package_name="test_project",
                    ),
                ),
                (
                    DependenciesGenerator,
                    DependencyConfig(
                        project_name="test-project",
                        language=lang,
                        package_name="test_project",
                    ),
                ),
                (
                    TGenerator,
                    TConfig(
                        project_name="test-project",
                        language=lang,
                        package_name="test_project",
                    ),
                ),
                (
                    ReadmeGenerator,
                    ReadmeConfig(
                        project_name="test-project",
                        language=lang,
                        package_name="test_project",
                    ),
                ),
            ]

            for gen_cls, config in generators:
                gen = gen_cls(output_dir, config)
                files = gen.generate()
                all_files.update(files)

            for key, path in all_files.items():
                assert path.exists(), f"File {key} missing on disk for {lang}"
                content = path.read_text()
                assert content, f"File {key} is empty for {lang}"
