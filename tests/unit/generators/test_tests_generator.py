"""Unit tests for Tests Generator."""

import ast
from pathlib import Path
import tempfile

import pytest

from start_green_stay_green.generators.base import SUPPORTED_LANGUAGES
from start_green_stay_green.generators.tests_gen import TestsConfig as Config
from start_green_stay_green.generators.tests_gen import TestsGenerator as Generator

# Expected test file patterns per language
EXPECTED_TEST_FILES: dict[str, list[str]] = {
    "python": ["tests/__init__.py", "tests/test_main.py"],
    "typescript": ["tests/index.test.ts"],
    "go": ["cmd/test_project/main_test.go"],
    "rust": ["tests/integration_test.rs"],
    "java": ["src/test/java/com/example/test_project/GreetingTest.java"],
    "csharp": ["tests/MainTests.cs"],
    "ruby": ["spec/test_project_spec.rb", "spec/spec_helper.rb"],
    "swift": ["Tests/test_projectTests/test_projectTests.swift"],
    "kotlin": ["app/src/test/kotlin/com/example/test_project/GreetingTest.kt"],
    "cpp": ["tests/test_greeting.cpp"],
}


class TestGeneratorInitialization:
    """Test TestsGen initialization and basic instantiation."""

    def test_generator_can_be_instantiated(self) -> None:
        """Test TestsGenerator can be created with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            assert generator is not None
            assert isinstance(generator, Generator)

    def test_generator_has_generate_method(self) -> None:
        """Test generator has generate method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            assert hasattr(generator, "generate")
            assert callable(generator.generate)


class TestGeneration:
    """Test tests directory structure generation."""

    def test_generate_creates_tests_directory(self) -> None:
        """Test generate creates tests directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            generator.generate()

            # Should create tests directory
            tests_dir = Path(tmpdir) / "tests"
            assert tests_dir.exists()
            assert tests_dir.is_dir()

    def test_generate_creates_init_file(self) -> None:
        """Test generate creates __init__.py in tests directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            assert "tests/__init__.py" in files
            init_path = files["tests/__init__.py"]
            assert init_path.exists()
            assert init_path.is_file()

    def test_generate_creates_test_main_file(self) -> None:
        """Test generate creates test_main.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            assert "tests/test_main.py" in files
            test_path = files["tests/test_main.py"]
            assert test_path.exists()
            assert test_path.is_file()

    def test_init_has_docstring(self) -> None:
        """Test tests/__init__.py contains docstring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            init_path = files["tests/__init__.py"]
            content = init_path.read_text()

            # Should have triple-quoted docstring
            assert '"""' in content

    def test_test_main_has_test_function(self) -> None:
        """Test test_main.py contains a test function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            test_path = files["tests/test_main.py"]
            content = test_path.read_text()

            assert "def test_" in content

    def test_test_main_imports_from_package(self) -> None:
        """Test test_main.py imports from the source package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            test_path = files["tests/test_main.py"]
            content = test_path.read_text()

            # Should import from the package
            assert "from test_project" in content or "import test_project" in content
            assert "main" in content

    def test_test_main_calls_main_function(self) -> None:
        """Test test_main.py calls main() function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            test_path = files["tests/test_main.py"]
            content = test_path.read_text()

            # Should call main()
            assert "main()" in content

    def test_generated_files_are_valid_python(self) -> None:
        """Test generated files are syntactically valid Python."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            # Try to compile the generated files
            for file_path in files.values():
                if file_path.suffix == ".py":
                    content = file_path.read_text()
                    # Should compile without SyntaxError
                    ast.parse(content)


class TestConfigValidation:
    """Test TestsGenConfig validation."""

    def test_config_requires_project_name(self) -> None:
        """Test config validates project_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            Config(
                project_name="",  # Empty string
                language="python",
                package_name="test",
            )

    def test_config_requires_language(self) -> None:
        """Test config validates language is provided."""
        with pytest.raises((TypeError, ValueError)):
            Config(
                project_name="test",
                language="",  # Empty string
                package_name="test",
            )

    def test_config_requires_package_name(self) -> None:
        """Test config validates package_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            Config(
                project_name="test",
                language="python",
                package_name="",  # Empty string
            )


class TestUnsupportedLanguage:
    """Test error handling for unsupported languages."""

    def test_unsupported_language_raises_error(self) -> None:
        """Test that unsupported language raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="brainfuck",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)

            with pytest.raises(ValueError, match="Unsupported language"):
                generator.generate()


class TestMultiLanguageTests:
    """Test test generation for all supported languages."""

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_generate_creates_test_files(self, lang: str) -> None:
        """Test generate creates test files for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            assert files, f"No test files generated for {lang}"
            for key, path in files.items():
                assert path.exists(), f"Test file {key} missing for {lang}"
                content = path.read_text()
                assert len(content) > 0, f"Test file {key} empty for {lang}"

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_generate_creates_expected_test_files(self, lang: str) -> None:
        """Test generate creates the expected test files for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            expected = EXPECTED_TEST_FILES[lang]
            for expected_file in expected:
                assert expected_file in files, (
                    f"Expected {expected_file} for {lang}, " f"got {list(files.keys())}"
                )

    def test_typescript_test_has_describe_block(self) -> None:
        """Test TypeScript test file has describe/it blocks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            content = files["tests/index.test.ts"].read_text()
            assert "describe" in content or "test" in content

    def test_typescript_test_is_prettier_conformant(self) -> None:
        """Test generated tests/index.test.ts conforms to Prettier defaults.

        Prettier defaults to double quotes when ``singleQuote`` is absent from
        ``.prettierrc``. Single-quoted string literals in the generated test
        file would re-introduce the regression from issue #193 (Prettier
        warnings on freshly scaffolded TS projects). This is a necessary
        (not sufficient) conformance check.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            content = files["tests/index.test.ts"].read_text()
            # Prettier default: double-quoted string literals
            assert "'main'" not in content, (
                "tests/index.test.ts must use double quotes to match "
                "Prettier defaults (singleQuote is not set in .prettierrc)"
            )
            assert "'should run without error'" not in content
            assert "'../src/index'" not in content
            assert '"main"' in content
            assert '"should run without error"' in content
            assert '"../src/index"' in content
            # Must end with newline
            assert content.endswith("\n")

    def test_go_test_has_test_function(self) -> None:
        """Test Go test file has Test function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="go",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            content = files["cmd/test_project/main_test.go"].read_text()
            assert "func Test" in content
            assert "testing" in content

    def test_rust_test_has_test_attribute(self) -> None:
        """Test Rust test file has #[test] attribute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="rust",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            content = files["tests/integration_test.rs"].read_text()
            assert "#[test]" in content

    def test_java_test_has_test_annotation(self) -> None:
        """Test Java test file has the JUnit 4 @Test annotation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="java",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            content = files[
                "src/test/java/com/example/test_project/GreetingTest.java"
            ].read_text()
            assert "@Test" in content
            # JUnit 4 (org.junit), matching the pom — not JUnit 5 (jupiter).
            assert "import org.junit.Test;" in content
            assert "import static org.junit.Assert.assertEquals;" in content
            assert "jupiter" not in content

    def test_java_test_exercises_the_greeting_logic(self) -> None:
        """The Java scaffold test verifies real concatenation logic.

        It must compare ``Greeting.greet()`` output against expected
        literals — for both the project name and an arbitrary name — so
        the assertions are not tautological.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="java",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            content = files[
                "src/test/java/com/example/test_project/GreetingTest.java"
            ].read_text()
            assert "package com.example.test_project;" in content
            assert '"Hello from test-project!"' in content
            assert 'Greeting.greet("test-project")' in content
            assert 'assertEquals("Hello from wear!", Greeting.greet("wear"));' in (
                content
            )

    def test_csharp_test_has_fact_attribute(self) -> None:
        """Test C# test file has [Fact] attribute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="csharp",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            content = files["tests/MainTests.cs"].read_text()
            assert "[Fact]" in content

    def test_csharp_test_namespace_nests_under_program_namespace(self) -> None:
        """The xUnit test namespace derives from the shared helper (#370).

        ``MainTests`` lives in ``<Namespace>.Tests`` so C#'s enclosing-
        namespace lookup resolves ``Program`` (declared in
        ``<Namespace>`` by the structure generator) without a using
        directive — but only when both generators agree on the
        PascalCase namespace.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="csharp",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            content = files["tests/MainTests.cs"].read_text()
            assert "namespace TestProject.Tests" in content
            assert "Program.Main(" in content

    def test_ruby_test_has_describe_block(self) -> None:
        """Test Ruby spec file has describe block."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="ruby",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            content = files["spec/test_project_spec.rb"].read_text()
            assert "describe" in content or "RSpec.describe" in content

    def test_swift_test_has_xctest_case(self) -> None:
        """Test Swift test file uses XCTest with an XCTestCase subclass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="swift",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            test_key = "Tests/test_projectTests/test_projectTests.swift"
            content = files[test_key].read_text()
            assert "import XCTest" in content
            assert "XCTestCase" in content
            assert "func test" in content

    def test_swift_test_has_meaningful_assertions(self) -> None:
        """Swift test exercises behavior, not identical string literals.

        The generated XCTest must instantiate ``ContentView`` and assert the
        greeting is assembled from the project name, rather than comparing two
        identical literals (which would detect no defects).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="swift",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            test_key = "Tests/test_projectTests/test_projectTests.swift"
            content = files[test_key].read_text()

            # ContentView is instantiated and checked for nil — verifies the
            # view type compiles and constructs.
            assert "ContentView()" in content
            assert "XCTAssertNotNil" in content

            # The greeting is built dynamically from the project name via
            # string interpolation, so the assertion verifies real logic
            # rather than comparing two identical literals.
            assert 'let projectName = "test-project"' in content
            assert 'let greeting = "Hello from \\(projectName)!"' in content
            assert 'XCTAssertEqual(greeting, "Hello from test-project!")' in content

    def test_kotlin_test_is_a_junit_class(self) -> None:
        """Kotlin test file uses JUnit 4 with @Test methods (#356)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="kotlin",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            test_key = "app/src/test/kotlin/com/example/test_project/GreetingTest.kt"
            content = files[test_key].read_text()
            assert "package com.example.test_project" in content
            assert "import org.junit.Test" in content
            assert "@Test" in content
            assert "class GreetingTest" in content

    def test_kotlin_test_has_meaningful_assertions(self) -> None:
        """Kotlin test exercises greeting(), not identical string literals.

        The generated JUnit test must call the scaffold's ``greeting``
        function so the assertion verifies the interpolation logic rather
        than comparing two identical literals (which would detect no
        defects) — the same review lesson the Swift scaffold learned in
        PR #392.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="kotlin",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            test_key = "app/src/test/kotlin/com/example/test_project/GreetingTest.kt"
            content = files[test_key].read_text()
            assert 'greeting("test-project")' in content
            assert 'assertEquals("Hello from test-project!", ' in content
            # A second case proves greeting() reflects its argument.
            assert 'greeting("wear")' in content
            assert 'assertEquals("Hello from wear!", ' in content


class TestCppTestGeneration:
    """Test C/C++ Catch2 scaffold generation (#361)."""

    @staticmethod
    def _generate(tmpdir: str) -> dict[str, Path]:
        """Run the tests generator for a cpp test project.

        Args:
            tmpdir: Directory to generate into.

        Returns:
            Mapping of generated relative keys to file paths.
        """
        config = Config(
            project_name="test-project",
            language="cpp",
            package_name="test_project",
        )
        return Generator(Path(tmpdir), config).generate()

    def test_cpp_test_uses_catch2(self) -> None:
        """The scaffold test includes Catch2 v3 and uses TEST_CASE."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["tests/test_greeting.cpp"].read_text()
            assert "#include <catch2/catch_test_macros.hpp>" in content
            assert "TEST_CASE(" in content

    def test_cpp_test_exercises_format_greeting_logic(self) -> None:
        """The test calls format_greeting with project and arbitrary names.

        Exercising the assembly logic with two inputs (rather than
        comparing identical literals) is the PR #392 review lesson.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["tests/test_greeting.cpp"].read_text()
            assert 'test_project::format_greeting("test-project")' in content
            assert '"Hello from test-project!"' in content
            assert 'test_project::format_greeting("tizen")' in content

    def test_cpp_test_has_no_tizen_dependencies(self) -> None:
        """The Catch2 scaffold must build without the Tizen SDK."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["tests/test_greeting.cpp"].read_text()
            assert "watch_app" not in content
            assert "Elementary.h" not in content
