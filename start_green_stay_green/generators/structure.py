"""Project structure generator.

Generates source code directory structure for target projects (source directory,
__init__.py, Hello World starter code).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from start_green_stay_green.generators.base import BaseGenerator
from start_green_stay_green.generators.base import GenerationError
from start_green_stay_green.generators.base import validate_language


@dataclass(frozen=True)
class StructureConfig:
    """Configuration for project structure generation.

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


class StructureGenerator(BaseGenerator):
    """Generate project source code structure for target projects.

    This generator creates the source code directory structure (package directory,
    __init__.py, Hello World starter code) for the target project's language.

    All 7 supported languages (python, typescript, go, rust, java, csharp, ruby)
    are available at the generator level. Note that java, csharp, and ruby are
    not yet supported by the full CLI pipeline (``sgsg init``) because
    PreCommitGenerator does not yet handle those languages.

    Attributes:
        output_dir: Directory where structure will be created
        config: Configuration for structure generation
    """

    def __init__(
        self,
        output_dir: Path,
        config: StructureConfig,
    ) -> None:
        """Initialize the Structure Generator.

        Args:
            output_dir: Directory where structure will be created
            config: StructureConfig with project settings

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
        """Generate project source code structure.

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
            "python": self._generate_python_structure,
            "typescript": self._generate_typescript_structure,
            "go": self._generate_go_structure,
            "rust": self._generate_rust_structure,
            "java": self._generate_java_structure,
            "csharp": self._generate_csharp_structure,
            "ruby": self._generate_ruby_structure,
        }
        return generators[self.config.language]()

    def _generate_python_structure(self) -> dict[str, Path]:
        """Generate Python project structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create package directory
        package_dir = self.output_dir / self.config.package_name
        package_dir.mkdir(parents=True, exist_ok=True)

        # Generate __init__.py
        init_key = f"{self.config.package_name}/__init__.py"
        files[init_key] = self._write_file(
            package_dir / "__init__.py",
            self._python_init_py(),
        )

        # Generate main.py
        main_key = f"{self.config.package_name}/main.py"
        files[main_key] = self._write_file(
            package_dir / "main.py",
            self._python_main_py(),
        )

        return files

    def _write_file(self, file_path: Path, content: str) -> Path:
        """Write a source file to disk.

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

    def _python_init_py(self) -> str:
        """Generate Python __init__.py content.

        Returns:
            Content for __init__.py with package docstring and version
        """
        # Convert package name to title case for display
        display_name = self.config.project_name.replace("-", " ").title()

        return f'''"""{display_name} package."""

__version__ = "0.1.0"
'''

    def _python_main_py(self) -> str:
        """Generate Python main.py content.

        Returns:
            Content for main.py with Hello World function
        """
        return f'''"""Main entry point for {self.config.project_name}."""


def main() -> None:
    """Run the main application."""
    print("Hello from {self.config.project_name}!")


if __name__ == "__main__":
    main()
'''

    def _generate_typescript_structure(self) -> dict[str, Path]:
        """Generate TypeScript project structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create src directory
        src_dir = self.output_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        # Generate index.ts
        index_key = "src/index.ts"
        files[index_key] = self._write_file(
            src_dir / "index.ts",
            self._typescript_index_ts(),
        )

        # Generate tsconfig.json
        tsconfig_key = "tsconfig.json"
        files[tsconfig_key] = self._write_file(
            self.output_dir / "tsconfig.json",
            self._typescript_tsconfig_json(),
        )

        return files

    def _typescript_index_ts(self) -> str:
        """Generate TypeScript index.ts content.

        Returns:
            Content for index.ts with Hello World function
        """
        return f"""/**
 * Main entry point for {self.config.project_name}
 */

function main(): void {{
    console.log("Hello from {self.config.project_name}!");
}}

main();
"""

    def _typescript_tsconfig_json(self) -> str:
        """Generate TypeScript tsconfig.json content.

        Returns:
            Content for tsconfig.json
        """
        return """{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
"""

    def _generate_go_structure(self) -> dict[str, Path]:
        """Generate Go project structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create cmd/{package_name} directory
        cmd_dir = self.output_dir / "cmd" / self.config.package_name
        cmd_dir.mkdir(parents=True, exist_ok=True)

        # Create internal directory
        internal_dir = self.output_dir / "internal"
        internal_dir.mkdir(parents=True, exist_ok=True)

        # Generate main.go
        main_key = f"cmd/{self.config.package_name}/main.go"
        files[main_key] = self._write_file(
            cmd_dir / "main.go",
            self._go_main_go(),
        )

        # Generate go.mod
        gomod_key = "go.mod"
        files[gomod_key] = self._write_file(
            self.output_dir / "go.mod",
            self._go_mod(),
        )

        return files

    def _go_main_go(self) -> str:
        """Generate Go main.go content.

        Returns:
            Content for main.go with Hello World
        """
        return f"""package main

import "fmt"

func main() {{
\tfmt.Println("Hello from {self.config.project_name}!")
}}
"""

    def _go_mod(self) -> str:
        """Generate Go go.mod content.

        Returns:
            Content for go.mod
        """
        return f"""module {self.config.package_name}

go 1.21
"""

    def _generate_rust_structure(self) -> dict[str, Path]:
        """Generate Rust project structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create src directory
        src_dir = self.output_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        # Generate main.rs
        main_key = "src/main.rs"
        files[main_key] = self._write_file(
            src_dir / "main.rs",
            self._rust_main_rs(),
        )

        # Generate lib.rs
        lib_key = "src/lib.rs"
        files[lib_key] = self._write_file(
            src_dir / "lib.rs",
            self._rust_lib_rs(),
        )

        # Generate Cargo.toml
        cargo_key = "Cargo.toml"
        files[cargo_key] = self._write_file(
            self.output_dir / "Cargo.toml",
            self._rust_cargo_toml(),
        )

        return files

    def _rust_main_rs(self) -> str:
        """Generate Rust main.rs content.

        Returns:
            Content for main.rs with Hello World
        """
        return f"""fn main() {{
    println!("Hello from {self.config.project_name}!");
}}
"""

    def _rust_lib_rs(self) -> str:
        """Generate Rust lib.rs content.

        Returns:
            Content for lib.rs
        """
        return f"""//! {self.config.project_name} library

#[cfg(test)]
mod tests {{
    #[test]
    fn it_works() {{
        assert_eq!(2 + 2, 4);
    }}
}}
"""

    def _rust_cargo_toml(self) -> str:
        """Generate Rust Cargo.toml content.

        Returns:
            Content for Cargo.toml
        """
        return f"""[package]
name = "{self.config.project_name}"
version = "0.1.0"
edition = "2021"

[dependencies]
"""

    def _generate_java_structure(self) -> dict[str, Path]:
        """Generate Java project structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create src/main/java/{package_name} directory
        java_dir = self.output_dir / "src" / "main" / "java" / self.config.package_name
        java_dir.mkdir(parents=True, exist_ok=True)

        # Generate Main.java
        main_key = f"src/main/java/{self.config.package_name}/Main.java"
        files[main_key] = self._write_file(
            java_dir / "Main.java",
            self._java_main_java(),
        )

        # Generate pom.xml
        pom_key = "pom.xml"
        files[pom_key] = self._write_file(
            self.output_dir / "pom.xml",
            self._java_pom_xml(),
        )

        return files

    def _java_main_java(self) -> str:
        """Generate Java Main.java content.

        Returns:
            Content for Main.java with Hello World
        """
        return f"""package {self.config.package_name};

public class Main {{
    public static void main(String[] args) {{
        System.out.println("Hello from {self.config.project_name}!");
    }}
}}
"""

    def _java_pom_xml(self) -> str:
        """Generate Java pom.xml content.

        Returns:
            Content for pom.xml
        """
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
                             http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>{self.config.package_name}</groupId>
    <artifactId>{self.config.package_name}</artifactId>
    <version>0.1.0</version>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
</project>
"""

    def _generate_csharp_structure(self) -> dict[str, Path]:
        """Generate C# project structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create src directory
        src_dir = self.output_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        # Generate Program.cs
        program_key = "src/Program.cs"
        files[program_key] = self._write_file(
            src_dir / "Program.cs",
            self._csharp_program_cs(),
        )

        return files

    def _csharp_program_cs(self) -> str:
        """Generate C# Program.cs content.

        Returns:
            Content for Program.cs with Hello World
        """
        return f"""using System;

namespace {self.config.package_name}
{{
    class Program
    {{
        static void Main(string[] args)
        {{
            Console.WriteLine("Hello from {self.config.project_name}!");
        }}
    }}
}}
"""

    def _generate_ruby_structure(self) -> dict[str, Path]:
        """Generate Ruby project structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create lib directory
        lib_dir = self.output_dir / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)

        # Generate main library file
        lib_key = f"lib/{self.config.package_name}.rb"
        files[lib_key] = self._write_file(
            lib_dir / f"{self.config.package_name}.rb",
            self._ruby_lib_rb(),
        )

        # Generate Gemfile
        gemfile_key = "Gemfile"
        files[gemfile_key] = self._write_file(
            self.output_dir / "Gemfile",
            self._ruby_gemfile(),
        )

        return files

    def _ruby_lib_rb(self) -> str:
        """Generate Ruby library file content.

        Returns:
            Content for main Ruby library file
        """
        # Convert package_name to module name (capitalize each part)
        module_name = "".join(
            word.capitalize() for word in self.config.package_name.split("_")
        )

        return f"""# frozen_string_literal: true

module {module_name}
  VERSION = "0.1.0"

  def self.hello
    puts "Hello from {self.config.project_name}!"
  end
end

# Run hello if this file is executed directly
{module_name}.hello if __FILE__ == $PROGRAM_NAME
"""

    def _ruby_gemfile(self) -> str:
        """Generate Ruby Gemfile content.

        Returns:
            Content for Gemfile
        """
        return """# frozen_string_literal: true

source "https://rubygems.org"

gem "rake", "~> 13.0"
gem "rspec", "~> 3.0"
gem "rubocop", "~> 1.0"
"""
