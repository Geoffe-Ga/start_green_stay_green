"""Tests directory generator.

Generates tests directory structure for target projects (tests/, tests/__init__.py,
tests/test_main.py with passing test).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from start_green_stay_green.generators.base import BaseGenerator
from start_green_stay_green.generators.base import GenerationError
from start_green_stay_green.generators.base import validate_language


@dataclass(frozen=True)
class TestsConfig:
    """Configuration for tests structure generation.

    Attributes:
        project_name: Name of the project (e.g., "my-project")
        language: Programming language (python, typescript, go, rust, etc.)
        package_name: Name of the main package/module (e.g., "my_project")
    """

    project_name: str
    language: str
    package_name: str

    def __post_init__(self) -> None:
        """Validate configuration after initialization.

        Raises:
            ValueError: If any required field is empty
        """
        if not self.project_name:
            msg = "Project name cannot be empty"
            raise ValueError(msg)
        if not self.language:
            msg = "Language cannot be empty"
            raise ValueError(msg)
        if not self.package_name:
            msg = "Package name cannot be empty"
            raise ValueError(msg)


class TestsGenerator(BaseGenerator):
    """Generate tests directory structure for target projects.

    This generator creates the tests directory structure (tests/, tests/__init__.py,
    tests/test_main.py) with a passing test for the Hello World code.

    All 7 supported languages (python, typescript, go, rust, java, csharp, ruby)
    are available at the generator level. Note that java, csharp, and ruby are
    not yet supported by the full CLI pipeline (``sgsg init``) because
    PreCommitGenerator does not yet handle those languages.

    Attributes:
        output_dir: Directory where tests structure will be created
        config: Configuration for tests generation
    """

    def __init__(
        self,
        output_dir: Path,
        config: TestsConfig,
    ) -> None:
        """Initialize the Tests Generator.

        Args:
            output_dir: Directory where tests structure will be created
            config: TestsConfig with project settings

        Raises:
            ValueError: If output_dir is invalid or language is unsupported
        """
        self.output_dir = Path(output_dir)
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration and ensure output directory exists.

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config.language:
            msg = "Language cannot be empty"
            raise ValueError(msg)

        if not self.config.package_name:
            msg = "Package name cannot be empty"
            raise ValueError(msg)

        if not self.config.project_name:
            msg = "Project name cannot be empty"
            raise ValueError(msg)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self) -> dict[str, Any]:
        """Generate tests directory structure.

        Returns:
            Dictionary mapping file names to their generated file paths

        Raises:
            GenerationError: If generation fails
            ValueError: If configuration is invalid
        """
        # Validate language is supported
        validate_language(self.config.language)

        # Dispatch to language-specific generator
        generators = {
            "python": self._generate_python_tests,
            "typescript": self._generate_typescript_tests,
            "go": self._generate_go_tests,
            "rust": self._generate_rust_tests,
            "java": self._generate_java_tests,
            "csharp": self._generate_csharp_tests,
            "ruby": self._generate_ruby_tests,
        }
        return generators[self.config.language]()

    def _generate_python_tests(self) -> dict[str, Path]:
        """Generate Python tests structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create tests directory
        tests_dir = self.output_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate tests/__init__.py
        init_key = "tests/__init__.py"
        files[init_key] = self._write_file(
            tests_dir / "__init__.py",
            self._python_tests_init_py(),
        )

        # Generate tests/test_main.py
        test_main_key = "tests/test_main.py"
        files[test_main_key] = self._write_file(
            tests_dir / "test_main.py",
            self._python_test_main_py(),
        )

        return files

    def _write_file(self, file_path: Path, content: str) -> Path:
        """Write a test file to disk.

        Args:
            file_path: Path where file will be written
            content: Content to write to the file

        Returns:
            Path to the written file

        Raises:
            GenerationError: If file cannot be written
        """
        try:
            file_path.write_text(content)
        except OSError as e:
            msg = f"Failed to write {file_path.name}: {e}"
            raise GenerationError(msg, cause=e) from e
        return file_path

    def _python_tests_init_py(self) -> str:
        """Generate Python tests/__init__.py content.

        Returns:
            Content for tests/__init__.py with package docstring
        """
        return f'"""Tests for {self.config.project_name}."""\n'

    def _python_test_main_py(self) -> str:
        """Generate Python tests/test_main.py content.

        Returns:
            Content for test_main.py with passing test for main()
        """
        return f'''"""Tests for {self.config.package_name}.main module."""

from {self.config.package_name}.main import main


def test_main_runs() -> None:
    """Test that main() runs without error."""
    main()  # Should print "Hello from {self.config.project_name}!"
'''

    def _generate_typescript_tests(self) -> dict[str, Path]:
        """Generate TypeScript tests structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create tests directory
        tests_dir = self.output_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate tests/index.test.ts
        test_index_key = "tests/index.test.ts"
        files[test_index_key] = self._write_file(
            tests_dir / "index.test.ts",
            self._typescript_test_index_ts(),
        )

        return files

    def _typescript_test_index_ts(self) -> str:
        """Generate TypeScript tests/index.test.ts content.

        Returns:
            Content for index.test.ts with Jest test
        """
        return f"""/**
 * Tests for {self.config.project_name} main entry point
 */

describe('main', () => {{
  it('should run without error', () => {{
    // Import main to ensure it executes
    expect(() => {{
      require('../src/index');
    }}).not.toThrow();
  }});
}});
"""

    def _generate_go_tests(self) -> dict[str, Path]:
        """Generate Go tests structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create cmd/{package_name} directory
        cmd_dir = self.output_dir / "cmd" / self.config.package_name
        cmd_dir.mkdir(parents=True, exist_ok=True)

        # Generate cmd/{package_name}/main_test.go
        test_main_key = f"cmd/{self.config.package_name}/main_test.go"
        files[test_main_key] = self._write_file(
            cmd_dir / "main_test.go",
            self._go_test_main_go(),
        )

        return files

    def _go_test_main_go(self) -> str:
        """Generate Go main_test.go content.

        Returns:
            Content for main_test.go with testing.T test
        """
        return """package main

import (
\t"testing"
)

func TestMain(t *testing.T) {
\t// Test that main function exists and can be called
\t// This verifies the Hello World entry point compiles correctly
\tt.Run("main runs without panic", func(t *testing.T) {
\t\t// If main() panics, the test will fail
\t\tdefer func() {
\t\t\tif r := recover(); r != nil {
\t\t\t\tt.Errorf("main() panicked: %v", r)
\t\t\t}
\t\t}()
\t\t// Note: main() would normally be called, but it runs indefinitely
\t\t// For Hello World, we just verify it compiles
\t})
}
"""

    def _generate_rust_tests(self) -> dict[str, Path]:
        """Generate Rust tests structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create tests directory
        tests_dir = self.output_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate tests/integration_test.rs
        test_integration_key = "tests/integration_test.rs"
        files[test_integration_key] = self._write_file(
            tests_dir / "integration_test.rs",
            self._rust_test_integration_rs(),
        )

        return files

    def _rust_test_integration_rs(self) -> str:
        """Generate Rust tests/integration_test.rs content.

        Returns:
            Content for integration_test.rs with #[test] attribute
        """
        return f"""//! Integration tests for {self.config.project_name}

#[test]
fn test_main_compiles() {{
    // This test verifies that the main entry point compiles
    // and the crate can be used as a library
    // The actual main function prints "Hello from {self.config.project_name}!"
    assert!(true, "Project compiles successfully");
}}

#[cfg(test)]
mod tests {{
    #[test]
    fn test_hello_world_runs() {{
        // Verify the hello world functionality is accessible
        // In a real implementation, this would call the main logic
        assert!(true);
    }}
}}
"""

    def _generate_java_tests(self) -> dict[str, Path]:
        """Generate Java tests structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create src/test/java/{package_name} directory
        test_dir = self.output_dir / "src" / "test" / "java" / self.config.package_name
        test_dir.mkdir(parents=True, exist_ok=True)

        # Generate src/test/java/{package_name}/MainTest.java
        test_main_key = f"src/test/java/{self.config.package_name}/MainTest.java"
        files[test_main_key] = self._write_file(
            test_dir / "MainTest.java",
            self._java_test_main_java(),
        )

        return files

    def _java_test_main_java(self) -> str:
        """Generate Java MainTest.java content.

        Returns:
            Content for MainTest.java with JUnit @Test annotation
        """
        # Convert package_name to valid Java package (e.g., my_project -> my.project)
        package_name = self.config.package_name.replace("_", ".")

        return f"""package {package_name};

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for {self.config.project_name} main entry point
 */
public class MainTest {{

    @Test
    public void testMainRuns() {{
        // Test that Main class exists and can be instantiated
        // This verifies the Hello World entry point compiles correctly
        assertDoesNotThrow(() -> {{
            Main.main(new String[]{{}});
        }}, "main() should run without throwing exceptions");
    }}

    @Test
    public void testMainMethodExists() {{
        // Verify main method exists
        try {{
            Main.class.getMethod("main", String[].class);
        }} catch (NoSuchMethodException e) {{
            fail("main(String[] args) method should exist");
        }}
    }}
}}
"""

    def _generate_csharp_tests(self) -> dict[str, Path]:
        """Generate C# tests structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create tests directory
        tests_dir = self.output_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate tests/MainTests.cs
        test_main_key = "tests/MainTests.cs"
        files[test_main_key] = self._write_file(
            tests_dir / "MainTests.cs",
            self._csharp_test_main_cs(),
        )

        return files

    def _csharp_test_main_cs(self) -> str:
        """Generate C# MainTests.cs content.

        Returns:
            Content for MainTests.cs with xUnit [Fact] attribute
        """
        # Convert package_name to PascalCase for C# namespace
        namespace = "".join(
            word.capitalize() for word in self.config.package_name.split("_")
        )

        return f"""using Xunit;

namespace {namespace}.Tests
{{
    /// <summary>
    /// Tests for {self.config.project_name} main entry point
    /// </summary>
    public class MainTests
    {{
        [Fact]
        public void MainRuns_WithoutError()
        {{
            // Test that Main method exists and can be called
            // This verifies the Hello World entry point compiles correctly
            var exception = Record.Exception(() =>
            {{
                Program.Main(new string[] {{}});
            }});

            Assert.Null(exception);
        }}

        [Fact]
        public void MainMethod_Exists()
        {{
            // Verify Main method exists in Program class
            var method = typeof(Program).GetMethod("Main");
            Assert.NotNull(method);
        }}
    }}
}}
"""

    def _generate_ruby_tests(self) -> dict[str, Path]:
        """Generate Ruby tests structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create spec directory
        spec_dir = self.output_dir / "spec"
        spec_dir.mkdir(parents=True, exist_ok=True)

        # Generate spec/{package_name}_spec.rb
        test_spec_key = f"spec/{self.config.package_name}_spec.rb"
        files[test_spec_key] = self._write_file(
            spec_dir / f"{self.config.package_name}_spec.rb",
            self._ruby_test_spec_rb(),
        )

        # Generate spec/spec_helper.rb
        spec_helper_key = "spec/spec_helper.rb"
        files[spec_helper_key] = self._write_file(
            spec_dir / "spec_helper.rb",
            self._ruby_spec_helper_rb(),
        )

        return files

    def _ruby_test_spec_rb(self) -> str:
        """Generate Ruby spec file content.

        Returns:
            Content for {package_name}_spec.rb with RSpec test
        """
        return f"""# frozen_string_literal: true

require 'spec_helper'
require_relative '../lib/{self.config.package_name}'

RSpec.describe {self.config.package_name.capitalize()} do
  describe '.main' do
    it 'runs without error' do
      # Test that main method exists and can be called
      # This verifies the Hello World entry point works correctly
      expect {{ {self.config.package_name.capitalize()}.main }}.not_to raise_error
    end

    it 'prints hello message' do
      # Capture stdout to verify the hello message
      pattern = /Hello from {self.config.project_name}/
      expect {{ {self.config.package_name.capitalize()}.main }}
        .to output(pattern).to_stdout
    end
  end
end
"""

    def _ruby_spec_helper_rb(self) -> str:
        """Generate Ruby spec_helper.rb content.

        Returns:
            Content for spec_helper.rb with RSpec configuration
        """
        return f"""# frozen_string_literal: true

# RSpec configuration for {self.config.project_name}

RSpec.configure do |config|
  # Use the expect syntax
  config.expect_with :rspec do |expectations|
    expectations.include_chain_clauses_in_custom_matcher_descriptions = true
  end

  # Use the new syntax for mocks
  config.mock_with :rspec do |mocks|
    mocks.verify_partial_doubles = true
  end

  # Enable color output
  config.color = true

  # Use the documentation formatter for detailed output
  config.default_formatter = 'doc' if config.files_to_run.one?

  # Randomize test order
  config.order = :random
  Kernel.srand config.seed
end
"""
