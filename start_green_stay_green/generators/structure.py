"""Project structure generator.

Generates source code directory structure for target projects (source directory,
__init__.py, Hello World starter code).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

from start_green_stay_green.generators.base import BaseGenerator
from start_green_stay_green.generators.base import GenerationError
from start_green_stay_green.generators.base import validate_language
from start_green_stay_green.utils.cpp import TIZEN_API_VERSION
from start_green_stay_green.utils.cpp import cpp_identifier
from start_green_stay_green.utils.cpp import tizen_app_id
from start_green_stay_green.utils.kotlin import android_package
from start_green_stay_green.utils.kotlin import android_package_path
from start_green_stay_green.utils.naming import pascal_case
from start_green_stay_green.utils.swift import package_swift

if TYPE_CHECKING:
    from start_green_stay_green.utils.file_writer import FileWriter


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

    All 10 supported languages (python, typescript, go, rust, java, csharp,
    ruby, swift, kotlin, cpp) are available at the generator level. Note that
    the full CLI pipeline (``sgsg init``) skips its quality-tooling steps
    (pre-commit, scripts, CI, architecture, metrics) for java, csharp, ruby,
    and cpp; C/C++ tooling arrives with #362/#363.

    Attributes:
        output_dir: Directory where structure will be created
        config: Configuration for structure generation
    """

    def __init__(
        self,
        output_dir: Path,
        config: StructureConfig,
        *,
        file_writer: FileWriter | None = None,
    ) -> None:
        """Initialize the Structure Generator.

        Args:
            output_dir: Directory where structure will be created
            config: StructureConfig with project settings
            file_writer: Optional FileWriter for additive behavior.
                If provided, existing files are skipped instead of overwritten.

        Raises:
            ValueError: If output_dir is invalid or language is unsupported
        """
        self.output_dir = Path(output_dir)
        self.config = config
        self._file_writer = file_writer
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
            "swift": self._generate_swift_structure,
            "kotlin": self._generate_kotlin_structure,
            "cpp": self._generate_cpp_structure,
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

        If a FileWriter is configured, delegates to it for existence checking.
        Otherwise, writes directly (original behavior).

        Args:
            file_path: Path where file will be written
            content: Content to write to the file

        Returns:
            Path to the written file

        Raises:
            GenerationError: If file cannot be written
        """
        if self._file_writer is not None:
            self._file_writer.write_file(file_path, content)
            return file_path

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

        # Generate .eslintrc.js
        eslintrc_key = ".eslintrc.js"
        files[eslintrc_key] = self._write_file(
            self.output_dir / ".eslintrc.js",
            self._typescript_eslintrc_js(),
        )

        # Generate .prettierrc
        prettierrc_key = ".prettierrc"
        files[prettierrc_key] = self._write_file(
            self.output_dir / ".prettierrc",
            self._typescript_prettierrc(),
        )

        # Generate jest.config.js
        jest_config_key = "jest.config.js"
        files[jest_config_key] = self._write_file(
            self.output_dir / "jest.config.js",
            self._typescript_jest_config_js(),
        )

        # Generate .prettierignore
        prettierignore_key = ".prettierignore"
        files[prettierignore_key] = self._write_file(
            self.output_dir / ".prettierignore",
            self._typescript_prettierignore(),
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

    def _typescript_eslintrc_js(self) -> str:
        """Generate TypeScript .eslintrc.js content.

        Returns:
            Content for .eslintrc.js with TypeScript parser and recommended rules
        """
        return """module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: "module",
  },
  plugins: ["@typescript-eslint"],
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
  ],
  env: {
    node: true,
    jest: true,
  },
  ignorePatterns: ["dist", "node_modules"],
};
"""

    def _typescript_prettierignore(self) -> str:
        """Generate TypeScript .prettierignore content.

        Returns:
            Content for .prettierignore to exclude non-source files
        """
        return """dist
node_modules
coverage
.claude
*.md
*.yaml
*.yml
.github/
scripts/
"""

    def _typescript_prettierrc(self) -> str:
        """Generate TypeScript .prettierrc content.

        Returns:
            Content for .prettierrc with standard formatting options
        """
        return """{
  "semi": true,
  "trailingComma": "all",
  "printWidth": 80,
  "tabWidth": 2
}
"""

    def _typescript_jest_config_js(self) -> str:
        """Generate TypeScript jest.config.js content.

        Returns:
            Content for jest.config.js with ts-jest preset and coverage thresholds
        """
        return """module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  roots: ["<rootDir>/src", "<rootDir>/tests"],
  testMatch: ["**/*.test.ts", "**/*.spec.ts"],
  moduleFileExtensions: ["ts", "js", "json"],
  collectCoverageFrom: [
    "src/**/*.ts",
    "!src/**/*.d.ts",
  ],
  coverageThreshold: {
    global: {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },
};
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

    def _generate_swift_structure(self) -> dict[str, Path]:
        """Generate Swift watchOS project structure.

        Creates a Swift Package Manager layout with a SwiftUI + WatchKit
        watchOS app target: an ``@main`` App entry point and a ``ContentView``
        under ``Sources/{package_name}/``, plus the ``Package.swift`` manifest.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create Sources/{package_name} directory for the watchOS app target
        source_dir = self.output_dir / "Sources" / self.config.package_name
        source_dir.mkdir(parents=True, exist_ok=True)

        type_name = pascal_case(self.config.package_name)

        # Generate the SwiftUI @main App entry point
        app_key = f"Sources/{self.config.package_name}/{type_name}App.swift"
        files[app_key] = self._write_file(
            source_dir / f"{type_name}App.swift",
            self._swift_app_swift(type_name),
        )

        # Generate the SwiftUI ContentView
        view_key = f"Sources/{self.config.package_name}/ContentView.swift"
        files[view_key] = self._write_file(
            source_dir / "ContentView.swift",
            self._swift_content_view_swift(),
        )

        # Generate the SPM manifest
        package_key = "Package.swift"
        files[package_key] = self._write_file(
            self.output_dir / "Package.swift",
            self._swift_package_swift(),
        )

        return files

    def _swift_app_swift(self, type_name: str) -> str:
        """Generate the SwiftUI watchOS App entry point.

        Args:
            type_name: PascalCase prefix used for the App struct name.

        Returns:
            Content for the ``@main`` SwiftUI App source file. The
            ``@main`` attribute is gated behind ``#if os(watchOS)``:
            ``swift test`` links the package's test runner *executable*
            on the host platform, and a second entry point in the app
            target collides with the runner's ``main`` symbol (duplicate
            ``_main`` link error). On watchOS the entry point is intact;
            on the macOS test host the type compiles as plain,
            testable code.
        """
        return f"""import SwiftUI

// watchOS entry point: shows "Hello from {self.config.project_name}!"
// @main only applies on watchOS: the macOS host build that `swift test`
// performs links SwiftPM's test runner executable, and a second entry
// point would collide with the runner's own `main` symbol.
#if os(watchOS)
@main
#endif
struct {type_name}App: App {{
    @SceneBuilder var body: some Scene {{
        WindowGroup {{
            ContentView()
        }}
    }}
}}
"""

    def _swift_content_view_swift(self) -> str:
        """Generate the SwiftUI ContentView for the watchOS app.

        Returns:
            Content for the ``ContentView`` SwiftUI source file.
        """
        return f"""import SwiftUI

struct ContentView: View {{
    var body: some View {{
        Text("Hello from {self.config.project_name}!")
            .padding()
    }}
}}

#Preview {{
    ContentView()
}}
"""

    def _swift_package_swift(self) -> str:
        """Generate the Swift Package Manager manifest for watchOS.

        Delegates to the shared :func:`~start_green_stay_green.utils.swift.\
package_swift` helper so the structure and dependency generators emit an
        identical manifest from one source of truth.

        Returns:
            Content for ``Package.swift`` declaring a watchOS app target.
        """
        return package_swift(self.config.package_name)

    def _generate_kotlin_structure(self) -> dict[str, Path]:
        """Generate the Kotlin Wear OS project structure (#356).

        Creates the Android app module source tree: an ``AndroidManifest.xml``
        declaring the ``wear`` device profile (watch hardware feature plus the
        standalone-app metadata) and a ``MainActivity`` built with Jetpack
        Compose for Wear OS under ``app/src/main/kotlin/``. The Gradle
        (Kotlin DSL) manifests are owned by
        :class:`~start_green_stay_green.generators.dependencies.DependenciesGenerator`.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        package_path = android_package_path(self.config.package_name)

        # Create app/src/main/kotlin/<package>/ for the Wear OS app module
        main_dir = self.output_dir / "app" / "src" / "main"
        source_dir = main_dir / "kotlin" / package_path
        source_dir.mkdir(parents=True, exist_ok=True)

        # Generate the Wear OS AndroidManifest.xml
        manifest_key = "app/src/main/AndroidManifest.xml"
        files[manifest_key] = self._write_file(
            main_dir / "AndroidManifest.xml",
            self._kotlin_android_manifest(),
        )

        # Generate the Compose-for-Wear-OS MainActivity
        activity_key = f"app/src/main/kotlin/{package_path}/MainActivity.kt"
        files[activity_key] = self._write_file(
            source_dir / "MainActivity.kt",
            self._kotlin_main_activity(),
        )

        return files

    def _kotlin_android_manifest(self) -> str:
        """Generate the Wear OS ``AndroidManifest.xml``.

        Returns:
            Manifest content declaring the watch hardware feature (the
            ``wear`` device profile), the wearable shared library, the
            standalone-app metadata (installable without a phone
            companion), and the launcher ``MainActivity``. The package
            namespace is declared in ``app/build.gradle.kts`` (AGP 8+
            convention), not here.
        """
        return f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <!-- Wear device profile: this app installs only on watches. -->
    <uses-feature android:name="android.hardware.type.watch" />

    <application
        android:label="{self.config.project_name}"
        android:theme="@android:style/Theme.DeviceDefault">

        <uses-library
            android:name="com.google.android.wearable"
            android:required="true" />

        <!-- Standalone Wear OS app: installable without a phone companion. -->
        <meta-data
            android:name="com.google.android.wearable.standalone"
            android:value="true" />

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:theme="@android:style/Theme.DeviceDefault">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

    def _kotlin_main_activity(self) -> str:
        """Generate the Compose-for-Wear-OS ``MainActivity.kt``.

        The greeting is assembled by a top-level ``greeting`` function so
        the generated JUnit scaffold can exercise real interpolation logic
        on the JVM without Robolectric or an emulator.

        Returns:
            Content for the Wear OS entry-point activity source file.
        """
        package = android_package(self.config.package_name)
        return f"""package {package}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.wear.compose.material.MaterialTheme
import androidx.wear.compose.material.Text

/** Returns the greeting assembled from the project name. */
fun greeting(projectName: String): String = "Hello from $projectName!"

/** Wear OS entry point hosting the Compose UI. */
class MainActivity : ComponentActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContent {{ WearApp() }}
    }}
}}

/** Root composable: centers the greeting on the round watch face. */
@Composable
fun WearApp() {{
    MaterialTheme {{
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center,
        ) {{
            Text(text = greeting("{self.config.project_name}"))
        }}
    }}
}}
"""

    def _generate_cpp_structure(self) -> dict[str, Path]:
        """Generate the C/C++ Tizen native watch-app structure (#361).

        Creates the Tizen native source tree: a watch-app entry point
        (``src/main.cpp``, appcore ``watch_app`` lifecycle + EFL UI), a
        pure-logic translation unit (``src/greeting.cpp`` with its header
        ``inc/greeting.h``) that the Catch2 scaffold unit-tests without
        Tizen Studio, the ``tizen-manifest.xml`` watch-application
        manifest (wearable profile), and resource-placeholder notes under
        ``res/`` and ``shared/res/``. The CMake/Conan build manifests are
        owned by
        :class:`~start_green_stay_green.generators.dependencies.DependenciesGenerator`.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        src_dir = self.output_dir / "src"
        inc_dir = self.output_dir / "inc"
        src_dir.mkdir(parents=True, exist_ok=True)
        inc_dir.mkdir(parents=True, exist_ok=True)

        files["src/main.cpp"] = self._write_file(
            src_dir / "main.cpp", self._cpp_main_cpp()
        )
        files["src/greeting.cpp"] = self._write_file(
            src_dir / "greeting.cpp", self._cpp_greeting_cpp()
        )
        files["inc/greeting.h"] = self._write_file(
            inc_dir / "greeting.h", self._cpp_greeting_h()
        )
        files["tizen-manifest.xml"] = self._write_file(
            self.output_dir / "tizen-manifest.xml", self._cpp_tizen_manifest()
        )

        # Resource placeholders: the directories matter to Tizen Studio's
        # project layout, but icons are binary artifacts the generator
        # never writes, so a note documents them instead.
        res_dir = self.output_dir / "res"
        shared_res_dir = self.output_dir / "shared" / "res"
        res_dir.mkdir(parents=True, exist_ok=True)
        shared_res_dir.mkdir(parents=True, exist_ok=True)
        files["res/README.md"] = self._write_file(
            res_dir / "README.md", self._cpp_res_note()
        )
        files["shared/res/README.md"] = self._write_file(
            shared_res_dir / "README.md", self._cpp_shared_res_note()
        )

        return files

    def _cpp_main_cpp(self) -> str:
        """Generate the Tizen native watch-app entry point ``src/main.cpp``.

        The greeting text is assembled by ``format_greeting()`` in its own
        translation unit (``src/greeting.cpp``) so the generated Catch2
        scaffold can exercise real logic with plain CMake + Conan, without
        the Tizen SDK headers this file needs.

        Returns:
            Content for the watch-app (appcore) + EFL entry-point source.
        """
        namespace = cpp_identifier(self.config.package_name)
        return f"""// Tizen native watch-app entry point for {self.config.project_name}.
//
// NOTE: this file needs the Tizen native SDK headers (watch_app.h, EFL)
// and is built by Tizen Studio, NOT by the plain CMake build — see
// CMakeLists.txt and the README for the build split.
#include <watch_app.h>
#include <watch_app_efl.h>
#include <Elementary.h>

#include <cstdio>

#include "greeting.h"

namespace {{

struct appdata_s {{
    Evas_Object *win = nullptr;
    Evas_Object *conform = nullptr;
    Evas_Object *label = nullptr;
}};

// Renders the greeting and the current time onto the watch face label.
void update_watch_label(appdata_s *ad, watch_time_h watch_time) {{
    if (ad->label == nullptr || watch_time == nullptr) {{
        return;
    }}

    int hour24 = 0;
    int minute = 0;
    watch_time_get_hour24(watch_time, &hour24);
    watch_time_get_minute(watch_time, &minute);

    const std::string greeting =
        {namespace}::format_greeting("{self.config.project_name}");
    char text[256];
    std::snprintf(text, sizeof(text),
                  "<align=center>%s<br/>%02d:%02d</align>",
                  greeting.c_str(), hour24, minute);
    elm_object_text_set(ad->label, text);
}}

// Builds the base EFL UI: window, conformant, and the greeting label.
void create_base_gui(appdata_s *ad, int width, int height) {{
    watch_app_get_elm_win(&ad->win);
    evas_object_resize(ad->win, width, height);

    ad->conform = elm_conformant_add(ad->win);
    evas_object_size_hint_weight_set(ad->conform, EVAS_HINT_EXPAND,
                                     EVAS_HINT_EXPAND);
    elm_win_resize_object_add(ad->win, ad->conform);
    evas_object_show(ad->conform);

    ad->label = elm_label_add(ad->conform);
    evas_object_resize(ad->label, width, height / 3);
    evas_object_move(ad->label, 0, height / 3);
    evas_object_show(ad->label);

    evas_object_show(ad->win);
}}

bool app_create(int width, int height, void *data) {{
    auto *ad = static_cast<appdata_s *>(data);
    create_base_gui(ad, width, height);
    return true;
}}

void app_terminate(void * /*data*/) {{
    // Release any resources acquired in app_create here.
}}

void app_time_tick(watch_time_h watch_time, void *data) {{
    auto *ad = static_cast<appdata_s *>(data);
    update_watch_label(ad, watch_time);
}}

}}  // namespace

int main(int argc, char *argv[]) {{
    appdata_s ad;
    watch_app_lifecycle_callback_s callbacks = {{}};
    callbacks.create = app_create;
    callbacks.terminate = app_terminate;
    callbacks.time_tick = app_time_tick;

    return watch_app_main(argc, argv, &callbacks, &ad);
}}
"""

    def _cpp_greeting_h(self) -> str:
        """Generate the pure-logic header ``inc/greeting.h``.

        Returns:
            Header declaring ``format_greeting`` in the project namespace.
            This translation unit has no Tizen dependencies, which is what
            lets the Catch2 scaffold build with plain CMake + Conan.
        """
        namespace = cpp_identifier(self.config.package_name)
        return f"""// Pure greeting logic for {self.config.project_name}: no Tizen
// dependencies, so the unit tests build with plain CMake + Conan.
#pragma once

#include <string>

namespace {namespace} {{

// Returns the greeting assembled from the project name.
std::string format_greeting(const std::string &project_name);

}}  // namespace {namespace}
"""

    def _cpp_greeting_cpp(self) -> str:
        """Generate the pure-logic translation unit ``src/greeting.cpp``.

        Returns:
            Implementation of ``format_greeting`` (string assembly the
            Catch2 scaffold exercises).
        """
        namespace = cpp_identifier(self.config.package_name)
        return f"""#include "greeting.h"

namespace {namespace} {{

std::string format_greeting(const std::string &project_name) {{
    return "Hello from " + project_name + "!";
}}

}}  // namespace {namespace}
"""

    def _cpp_tizen_manifest(self) -> str:
        """Generate the Tizen watch-application ``tizen-manifest.xml``.

        Returns:
            Well-formed manifest XML declaring the wearable profile, the
            ``watch-application`` element (app ID from the shared
            :func:`~start_green_stay_green.utils.cpp.tizen_app_id`
            helper), and the ``watch_app`` feature. The icon PNG is a
            binary artifact the generator never writes; an XML comment
            and ``shared/res/README.md`` document adding it via Tizen
            Studio.
        """
        app_id = tizen_app_id(self.config.package_name)
        exec_name = cpp_identifier(self.config.package_name)
        return f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns="http://tizen.org/ns/packages" api-version="{TIZEN_API_VERSION}" \
package="{app_id}" version="0.1.0">
    <profile name="wearable" />
    <watch-application appid="{app_id}" exec="{exec_name}" ambient-support="false">
        <label>{self.config.project_name}</label>
        <!-- The icon PNG is a binary artifact and is NOT generated; add
             shared/res/{exec_name}.png via Tizen Studio before packaging
             (see shared/res/README.md). -->
        <icon>{exec_name}.png</icon>
    </watch-application>
    <feature name="http://tizen.org/feature/watch_app">true</feature>
</manifest>
"""

    def _cpp_res_note(self) -> str:
        """Generate the ``res/README.md`` resource-placeholder note.

        Returns:
            Note explaining what belongs in ``res/`` and why it starts
            empty (binary assets are never generated).
        """
        return f"""# res/

Private resources for the {self.config.project_name} Tizen watch app
(EDC layouts, images, sounds). The directory starts empty because the
scaffold never generates binary assets; add resources here via Tizen
Studio as the app grows.
"""

    def _cpp_shared_res_note(self) -> str:
        """Generate the ``shared/res/README.md`` icon-placeholder note.

        Returns:
            Note explaining that the launcher icon referenced by
            ``tizen-manifest.xml`` is a binary the user must supply.
        """
        exec_name = cpp_identifier(self.config.package_name)
        return f"""# shared/res/

Shared resources for the {self.config.project_name} Tizen watch app.

`tizen-manifest.xml` references the launcher icon `{exec_name}.png`,
which must live in this directory. Icons are binary artifacts and are
NOT generated by the scaffold — add one via Tizen Studio (or copy a
512x512 PNG here) before packaging the `.tpk`.
"""
