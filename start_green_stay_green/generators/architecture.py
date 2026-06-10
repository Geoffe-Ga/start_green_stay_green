"""Architecture enforcement generator.

Generates architecture validation configuration for import-linter (Python),
dependency-cruiser (TypeScript), go-arch-lint (Go), cargo-deny (Rust),
SwiftLint custom rules (Swift), Konsist (Kotlin), and a stdlib-Python
include-boundary checker (C/C++).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING
import warnings

from start_green_stay_green.utils.kotlin import android_package

if TYPE_CHECKING:
    from collections.abc import Callable

    from start_green_stay_green.ai.orchestrator import AIOrchestrator


@dataclass(frozen=True)
class ArchitectureResult:
    """Result from architecture enforcement generation.

    Attributes:
        output_dir: Directory containing generated files.
        files_created: List of files created.
        language: Target language (python, typescript, go, rust, swift,
            kotlin, cpp).
    """

    output_dir: Path
    files_created: list[Path]
    language: str


@dataclass(frozen=True)
class _LanguageTooling:
    """Per-language architecture tooling metadata.

    Attributes:
        tool: Human-readable name of the enforcement tool.
        config_file: Name of the generated configuration file.
        install_cmd: Shell command to install the tool.
        run_cmd: Run-command template with a ``{config_file}`` placeholder
            (e.g. ``"lint-imports --config {config_file}"``). The placeholder
            is filled with the (optionally path-prefixed) config filename at
            the call site, avoiding fragile substring replacement.
        docs_url: URL to the tool's documentation.
        display_name: Capitalized language label for human-readable output
            (e.g. ``"Python"``, ``"TypeScript"``, ``"Go"``).
    """

    tool: str
    config_file: str
    install_cmd: str
    run_cmd: str
    docs_url: str
    display_name: str


# Maps each supported language to its architecture-enforcement tooling.
# Keeping the metadata in one place lets the README and run-script
# generators stay tool-agnostic and avoids per-language branching.
_LANGUAGE_TOOLING: dict[str, _LanguageTooling] = {
    "python": _LanguageTooling(
        tool="import-linter",
        config_file=".importlinter",
        install_cmd="pip install import-linter",
        run_cmd="lint-imports --config {config_file}",
        docs_url="https://import-linter.readthedocs.io/",
        display_name="Python",
    ),
    "typescript": _LanguageTooling(
        tool="dependency-cruiser",
        config_file=".dependency-cruiser.js",
        install_cmd="npm install -g dependency-cruiser",
        run_cmd="depcruise --config {config_file} src",
        docs_url="https://github.com/sverweij/dependency-cruiser",
        display_name="TypeScript",
    ),
    "go": _LanguageTooling(
        tool="go-arch-lint",
        config_file=".go-arch-lint.yml",
        install_cmd=("go install github.com/fe3dback/go-arch-lint@latest"),
        run_cmd="go-arch-lint check --arch-file {config_file}",
        docs_url="https://github.com/fe3dback/go-arch-lint",
        display_name="Go",
    ),
    "rust": _LanguageTooling(
        tool="cargo-deny",
        config_file="deny.toml",
        install_cmd="cargo install cargo-deny",
        # Invoke the cargo-deny binary directly (not `cargo deny`) so the
        # run script's `command -v` guard probes the actual tool rather
        # than the always-present cargo wrapper.
        run_cmd="cargo-deny check --config {config_file}",
        docs_url="https://embarkstudios.github.io/cargo-deny/",
        display_name="Rust",
    ),
    "swift": _LanguageTooling(
        # No native Swift layer linter exists (unlike import-linter or
        # go-arch-lint), so layer rules are expressed as SwiftLint custom
        # regex rules; the generated config documents that gap.
        tool="SwiftLint custom rules",
        config_file=".swiftlint-architecture.yml",
        install_cmd="brew install swiftlint",
        run_cmd="swiftlint lint --config {config_file}",
        docs_url="https://realm.github.io/SwiftLint/custom_rules.html",
        display_name="Swift",
    ),
    "kotlin": _LanguageTooling(
        # No standalone Kotlin layer linter exists either; layer rules are
        # expressed as a Konsist JUnit test over Kotlin sources. Konsist's
        # 'config' is therefore a test file compiled into the project: the
        # Gradle run command takes no config-file flag (run_cmd carries no
        # {config_file} placeholder), and the one-time wiring step — copy
        # the template into the test source set — lives in install_cmd.
        # The konsist dependency is already declared in the generated
        # app/build.gradle.kts.
        tool="Konsist",
        config_file="ArchitectureTest.kt",
        install_cmd=(
            "gradle wrapper && "
            "cp plans/architecture/ArchitectureTest.kt app/src/test/kotlin/"
        ),
        run_cmd='./gradlew testDebugUnitTest --tests "*ArchitectureTest"',
        docs_url="https://docs.konsist.lemonappdev.com/",
        display_name="Kotlin",
    ),
    "cpp": _LanguageTooling(
        # No config-driven C/C++ layer linter exists either:
        # include-what-you-use is about include hygiene (its .imp mapping
        # files cannot express layer rules) and cpp-dependencies reports
        # directory-level dependency stats without a layer-matrix config.
        # Layer rules are therefore expressed as a runnable, stdlib-only
        # Python script whose dependency matrix sits at the top of the
        # file as the editable config — the same "config the user can
        # run" shape as the Kotlin Konsist test. The generated script
        # documents its enforcement limits explicitly.
        tool="include-boundary checker (stdlib Python script)",
        config_file="check_architecture.py",
        # python3 ships on every supported dev platform and the checker
        # is stdlib-only, so there is nothing else to install.
        install_cmd="python3 --version  # stdlib-only checker, no install needed",
        run_cmd="python3 {config_file}",
        # The checker is generated by this project (no external tool
        # docs exist), so the project repository is the canonical
        # documentation URL.
        docs_url="https://github.com/Geoffe-Ga/start_green_stay_green",
        display_name="C/C++",
    ),
}


class ArchitectureEnforcementGenerator:
    """Generates architecture enforcement configuration.

    Generates import-linter config for Python, dependency-cruiser
    config for TypeScript, go-arch-lint config for Go, cargo-deny
    config for Rust, SwiftLint custom rules for Swift, a Konsist
    test for Kotlin, and a runnable include-boundary checker for C/C++
    to enforce layer separation and prevent circular dependencies.

    Attributes:
        orchestrator: AI orchestrator for content generation.
        output_dir: Directory for generated files.
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator | None = None,
        *,
        output_dir: Path | None = None,
    ) -> None:
        """Initialize Architecture Enforcement Generator.

        Args:
            orchestrator: Deprecated. The architecture generator is fully
                deterministic; this parameter is retained for source
                compatibility and ignored. New code should omit it.
                Passing a non-``None`` value emits a
                :class:`DeprecationWarning` so callers can find the
                stale wiring before the parameter is removed in the
                Phase 3 cleanup of the optimization roadmap.
            output_dir: Output directory for generated files.
                Defaults to plans/architecture.
        """
        if orchestrator is not None:
            warnings.warn(
                "ArchitectureEnforcementGenerator's 'orchestrator' parameter "
                "is deprecated and will be removed in Phase 3 of the "
                "optimization roadmap. The generator is fully "
                "deterministic; pass nothing instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        self.orchestrator = orchestrator
        self.output_dir = output_dir or Path("plans/architecture")

    def generate(
        self,
        *,
        language: str,
        project_name: str,
    ) -> ArchitectureResult:
        """Generate architecture enforcement configuration.

        Args:
            language: Target language (python, typescript, go, rust,
                swift, kotlin, cpp).
            project_name: Name of the project.

        Returns:
            ArchitectureResult with output directory and files created.

        Raises:
            ValueError: If language is not supported.
        """
        supported_languages = frozenset(_LANGUAGE_TOOLING)
        if language not in supported_languages:
            msg = f"Unsupported language: {language}"
            raise ValueError(msg)

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Dispatch table keeps generate() flat as languages are added:
        # each entry is a zero-argument builder returning the config files.
        config_builders: dict[str, Callable[[], list[Path]]] = {
            "python": partial(self._generate_python_config, project_name),
            "typescript": partial(self._generate_typescript_config, project_name),
            "go": partial(self._generate_go_config, project_name),
            "rust": self._generate_rust_config,
            "swift": self._generate_swift_config,
            "kotlin": partial(self._generate_kotlin_config, project_name),
            "cpp": self._generate_cpp_config,
        }
        files_created = config_builders[language]()

        # Generate README and run script
        files_created.extend(
            [
                self._generate_readme(language, project_name),
                self._generate_run_script(language, project_name),
            ]
        )

        return ArchitectureResult(
            output_dir=self.output_dir,
            files_created=files_created,
            language=language,
        )

    def _generate_python_config(self, project_name: str) -> list[Path]:
        """Generate import-linter configuration for Python.

        Args:
            project_name: Name of the project.

        Returns:
            List of files created.
        """
        importlinter_path = self.output_dir / ".importlinter"

        # Generate import-linter configuration
        config_content = f"""[importlinter]
root_package = {project_name.replace('-', '_')}

[importlinter:contract:layers]
name = Enforce layered architecture
type = layers
layers =
    presentation
    application
    domain
    infrastructure

[importlinter:contract:independence]
name = Domain layer independence
type = forbidden
source_modules =
    {project_name.replace('-', '_')}.domain
forbidden_modules =
    {project_name.replace('-', '_')}.presentation
    {project_name.replace('-', '_')}.application
    {project_name.replace('-', '_')}.infrastructure

[importlinter:contract:no-cycles]
name = Prevent circular dependencies
type = independence
modules =
    {project_name.replace('-', '_')}
"""

        importlinter_path.write_text(config_content)
        return [importlinter_path]

    def _generate_typescript_config(
        self, project_name: str  # noqa: ARG002
    ) -> list[Path]:
        """Generate dependency-cruiser configuration for TypeScript.

        Args:
            project_name: Name of the project.

        Returns:
            List of files created.
        """
        dc_path = self.output_dir / ".dependency-cruiser.js"

        # Generate dependency-cruiser configuration
        config_content = """/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: 'no-circular',
      severity: 'error',
      comment: 'Circular dependencies create tight coupling and maintenance issues',
      from: {},
      to: {
        circular: true,
      },
    },
    {
      name: 'no-orphans',
      severity: 'warn',
      comment: 'Orphaned modules may indicate dead code',
      from: {
        orphan: true,
        pathNot: ['\\\\.(test|spec)\\\\.[jt]sx?$', '\\\\.(stories)\\\\.[jt]sx?$'],
      },
      to: {},
    },
    {
      name: 'enforce-layers',
      severity: 'error',
      comment: 'Enforce layered architecture: presentation -> application -> domain',
      from: {
        path: '^src/domain',
      },
      to: {
        path: '^src/(presentation|application|infrastructure)',
      },
    },
    {
      name: 'domain-independence',
      severity: 'error',
      comment: 'Domain layer should not depend on infrastructure concerns',
      from: {
        path: '^src/domain',
      },
      to: {
        path: '^src/infrastructure',
      },
    },
  ],
  options: {
    doNotFollow: {
      path: 'node_modules',
    },
    tsPreCompilationDeps: true,
    tsConfig: {
      fileName: 'tsconfig.json',
    },
    enhancedResolveOptions: {
      exportsFields: ['exports'],
      conditionNames: ['import', 'require', 'node', 'default'],
    },
    reporterOptions: {
      dot: {
        collapsePattern: 'node_modules/[^/]+',
      },
      archi: {
        collapsePattern: '^(node_modules|packages/[^/]+/src)/[^/]+',
      },
    },
  },
};
"""

        dc_path.write_text(config_content)
        return [dc_path]

    # ARG002: project_name is unused but kept for API parity with
    # _generate_python_config / _generate_typescript_config so the
    # generate() dispatch can call every _generate_*_config uniformly.
    def _generate_go_config(self, project_name: str) -> list[Path]:  # noqa: ARG002
        """Generate go-arch-lint configuration for Go.

        go-arch-lint enforces a component map and dependency rules over Go
        packages, providing the same layer-separation and domain-independence
        guarantees as import-linter (Python) and dependency-cruiser
        (TypeScript).

        Args:
            project_name: Name of the project.

        Returns:
            List of files created.
        """
        config_path = self.output_dir / ".go-arch-lint.yml"

        # Generate go-arch-lint configuration. Components map onto package
        # globs; the deps section forbids the domain layer from importing
        # the application, presentation, and infrastructure layers, keeping
        # business logic pure and dependency-free.
        config_content = """version: 3
workdir: .

components:
  presentation:
    in: presentation/**
  application:
    in: application/**
  domain:
    in: domain/**
  infrastructure:
    in: infrastructure/**

# Enforce layered architecture:
#   presentation -> application -> domain
# and keep the domain layer independent of outer layers.
deps:
  presentation:
    mayDependOn:
      - application
      - domain
  application:
    mayDependOn:
      - domain
  domain:
    # Domain layer must remain pure: no dependency on application,
    # presentation, or infrastructure concerns.
    mayDependOn: []
  infrastructure:
    mayDependOn:
      - domain

# domain is available to all components without an explicit deps entry.
commonComponents:
  - domain
"""

        config_path.write_text(config_content)
        return [config_path]

    # Unlike the Python config, the Rust config is project-name agnostic:
    # cargo-deny bans reference the per-layer workspace crate names, which
    # are fixed by the generated structure, so no project_name parameter
    # is needed here.
    def _generate_rust_config(self) -> list[Path]:
        """Generate cargo-deny configuration for Rust.

        cargo-deny enforces dependency rules over the Cargo crate graph.
        Layered architecture in Rust is modeled as one workspace crate per
        layer; the ``[bans]`` wrappers below restrict which crates may
        consume each layer, providing the same layer-separation and
        domain-independence guarantees as import-linter (Python),
        dependency-cruiser (TypeScript), and go-arch-lint (Go). Cycle
        prevention needs no rule at all: Cargo rejects circular crate
        dependencies at build time.

        Returns:
            List of files created.
        """
        config_path = self.output_dir / "deny.toml"

        # Generate cargo-deny configuration. The bans section expresses the
        # layer rules: a layer crate is "banned" everywhere except inside
        # its wrapper (consumer) crates, so only outer layers may depend on
        # inner machinery. The remaining sections add dependency hygiene
        # (duplicate versions, licenses, advisories, sources).
        config_content = """\
# cargo-deny configuration enforcing layered architecture and
# dependency hygiene.
#
# Layered architecture in Rust is modeled as one workspace crate per
# layer (presentation, application, domain, infrastructure).
# Cargo itself rejects circular crate dependencies at build time, so
# no cycle rule is needed here; the bans below enforce the remaining
# layer rules: outer layers depend inward, never the reverse.

[graph]
all-features = true

[advisories]
version = 2
yanked = "deny"

[licenses]
version = 2
# Allow only widely compatible licenses; extend as needed.
allow = [
    "MIT",
    "Apache-2.0",
    "Apache-2.0 WITH LLVM-exception",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "Unicode-3.0",
]

[bans]
# Duplicate crate versions create the same hidden coupling and bloat
# that tangled imports do in other ecosystems. "warn" rather than
# "deny": transitive Rust dependency trees routinely contain duplicate
# semver-incompatible versions (windows-*, syn, regex families), and a
# hard deny fails on the first cargo add. Tighten to "deny" if your
# crate deliberately pins its dependency tree.
multiple-versions = "warn"
wildcards = "deny"
# Enforce layered architecture:
#   presentation -> application -> domain
# A layer crate may only be consumed by the layers listed as wrappers,
# and the domain crate (unrestricted below) must itself stay pure: it
# may not depend on application, presentation, or infrastructure.
#
# Note: cargo-deny cannot restrict what depends on the presentation
# crate without knowing the top-level binary name, so the
# domain -> presentation and application -> presentation directions
# are enforced by convention / code review rather than by this config.
deny = [
    # Only the presentation layer may drive the application layer.
    { crate = "application", wrappers = ["presentation"] },
    # Infrastructure is wired in by the outer layers, never by domain.
    { crate = "infrastructure", wrappers = ["application", "presentation"] },
]

[sources]
unknown-registry = "deny"
unknown-git = "deny"
"""

        config_path.write_text(config_content)
        return [config_path]

    # Like the Rust config, the Swift config is project-name agnostic: the
    # custom rules reference the per-layer SPM module names, which are fixed
    # by convention, so no project_name parameter is needed here.
    def _generate_swift_config(self) -> list[Path]:
        """Generate SwiftLint custom-rules configuration for Swift.

        No native Swift architecture linter exists (unlike import-linter,
        dependency-cruiser, go-arch-lint, or cargo-deny), so layer rules
        are expressed as SwiftLint custom regex rules over ``import``
        statements. The generated config documents that enforcement gap
        explicitly, mirroring how the Rust ``deny.toml`` documents what
        cargo-deny cannot restrict. The dependency matrix mirrors the Go
        config: presentation -> application -> domain, with infrastructure
        allowed to depend on domain only.

        Returns:
            List of files created.
        """
        config_path = self.output_dir / ".swiftlint-architecture.yml"

        # Raw string: the regexes below must reach the YAML file with their
        # backslashes intact (single-quoted YAML scalars keep them literal).
        config_content = r"""# SwiftLint custom rules enforcing layered architecture.
#
# No native Swift layer linter exists (unlike import-linter for Python,
# dependency-cruiser for TypeScript, go-arch-lint for Go, or cargo-deny
# for Rust), so layer rules are expressed as SwiftLint custom regex rules
# over `import` statements.
#
# Enforcement limits (documented, not hidden):
#   - Custom rules are regex matches over source text,
#     not a resolved dependency graph. They only catch explicit `import`
#     statements of layer modules; they cannot see transitive dependencies.
#   - Layers must be modeled as separate SPM targets/modules named
#     Presentation, Application, Domain, and Infrastructure. References
#     within a single module never need an `import` and are NOT caught.
#   - No cycle rule is needed here:
#     Swift Package Manager itself rejects circular target dependencies
#     at build time.
#
# Dependency matrix (mirrors the Go go-arch-lint config):
#   presentation -> application, domain
#   application  -> domain
#   infrastructure -> domain
#   domain       -> (nothing)
#
# Run with:
#   swiftlint lint --config .swiftlint-architecture.yml

# Run only the custom architecture rules from this config so this check
# stays orthogonal to the general lint pass (.swiftlint.yml).
only_rules:
  - custom_rules

included:
  - Sources

custom_rules:
  domain_layer_purity:
    name: 'Domain layer purity'
    included: 'Sources/Domain/.*\.swift'
    regex: '^\s*(@testable\s+)?import\s+(Presentation|Application|Infrastructure)\b'
    message: 'Domain must not import Presentation, Application, or Infrastructure.'
    severity: error
  application_layer_boundary:
    name: 'Application layer boundary'
    included: 'Sources/Application/.*\.swift'
    regex: '^\s*(@testable\s+)?import\s+(Presentation|Infrastructure)\b'
    message: 'Application may only depend on Domain, never on outer layers.'
    severity: error
  infrastructure_layer_boundary:
    name: 'Infrastructure layer boundary'
    included: 'Sources/Infrastructure/.*\.swift'
    regex: '^\s*(@testable\s+)?import\s+(Presentation|Application)\b'
    message: 'Infrastructure may only depend on Domain.'
    severity: error
  presentation_layer_boundary:
    name: 'Presentation layer boundary'
    included: 'Sources/Presentation/.*\.swift'
    regex: '^\s*(@testable\s+)?import\s+Infrastructure\b'
    message: 'Presentation may depend on Application and Domain only.'
    severity: error
"""

        config_path.write_text(config_content)
        return [config_path]

    def _generate_kotlin_config(self, project_name: str) -> list[Path]:
        """Generate the Konsist architecture test for Kotlin.

        No standalone Kotlin layer linter exists (unlike import-linter,
        dependency-cruiser, go-arch-lint, or cargo-deny), so layer rules
        are expressed as a Konsist (architecture-testing library) JUnit
        test over Kotlin sources. The emitted file is a template parked in
        ``plans/architecture``: it only enforces once copied into the
        ``app/src/test/kotlin`` source set (the konsist dependency is
        already declared in the generated ``app/build.gradle.kts``). The
        test documents that wiring step and Konsist's enforcement limits
        explicitly, mirroring how the Rust ``deny.toml`` and Swift custom
        rules document their gaps. The dependency matrix mirrors the Go
        config: presentation -> application -> domain, with infrastructure
        allowed to depend on domain only.

        Args:
            project_name: Name of the project; layer packages derive from
                its sanitized Android namespace so the test stays in sync
                with the scaffolded sources.

        Returns:
            List of files created.
        """
        config_path = self.output_dir / "ArchitectureTest.kt"

        namespace = android_package(project_name)
        config_content = f"""\
// Konsist architecture test enforcing layered architecture.
//
// No standalone Kotlin layer linter exists (unlike import-linter for
// Python, dependency-cruiser for TypeScript, go-arch-lint for Go, or
// cargo-deny for Rust), so layer rules are expressed as a Konsist
// (https://docs.konsist.lemonappdev.com/) JUnit test over Kotlin sources.
//
// Wiring (one-time): this file is a template parked in plans/architecture;
// it only enforces once it lives in a test source set. Copy it in and run:
//   cp plans/architecture/ArchitectureTest.kt app/src/test/kotlin/
//   ./gradlew testDebugUnitTest --tests "*ArchitectureTest"
// The konsist dependency is already declared in app/build.gradle.kts.
//
// Enforcement limits (documented, not hidden):
//   - Konsist analyzes Kotlin source declarations statically,
//     not a resolved dependency graph: dependencies created via
//     reflection, dependency-injection wiring, or generated/Java sources
//     are invisible to it.
//   - Layers are defined by the package convention below
//     ({namespace}.<layer>..); code outside those packages is unchecked.
//   - dependsOn checks are non-strict by default (pragmatic warn-first
//     default): a layer whose package does not exist yet passes. Tighten
//     by passing strict = true once every layer package exists.
//   - No cycle rule is needed here: Gradle itself rejects circular
//     project dependencies at build time.
//
// Dependency matrix (mirrors the Go go-arch-lint config):
//   presentation -> application, domain
//   application  -> domain
//   infrastructure -> domain
//   domain       -> (nothing)
package {namespace}.architecture

import com.lemonappdev.konsist.api.Konsist
import com.lemonappdev.konsist.api.architecture.KoArchitectureCreator.assertArchitecture
import com.lemonappdev.konsist.api.architecture.Layer
import org.junit.Test

class ArchitectureTest {{
    @Test
    fun `layers depend only inward`() {{
        Konsist
            .scopeFromProject()
            .assertArchitecture {{
                val domain = Layer("Domain", "{namespace}.domain..")
                val application = Layer("Application", "{namespace}.application..")
                val presentation = Layer("Presentation", "{namespace}.presentation..")
                val infrastructure =
                    Layer("Infrastructure", "{namespace}.infrastructure..")

                domain.dependsOnNothing()
                application.dependsOn(domain)
                presentation.dependsOn(application)
                presentation.dependsOn(domain)
                infrastructure.dependsOn(domain)
            }}
    }}
}}
"""

        config_path.write_text(config_content)
        return [config_path]

    # Like the Rust and Swift configs, the C/C++ checker is project-name
    # agnostic: layers are defined by the src/<layer> and inc/<layer>
    # directory convention, which is fixed by convention rather than
    # derived from the project name.
    def _generate_cpp_config(self) -> list[Path]:
        """Generate the include-boundary checker for C/C++.

        No config-driven C/C++ layer linter exists (unlike import-linter,
        dependency-cruiser, go-arch-lint, or cargo-deny):
        include-what-you-use targets include *hygiene* — its ``.imp``
        mapping files cannot express layer rules — and cpp-dependencies
        reports directory-level dependency statistics without a
        layer-matrix config. Layer rules are therefore expressed as a
        runnable, stdlib-only Python script whose dependency matrix sits
        at the top of the file as the editable configuration — the same
        "config the user can run" shape as the Kotlin Konsist test. The
        script documents its enforcement limits explicitly, mirroring the
        Rust ``deny.toml`` and Swift custom-rule gap notes, and runs
        warn-first (missing layer directories pass) with a documented
        ``STRICT`` tighten-me switch. The dependency matrix mirrors the
        Go config: presentation -> application -> domain, with
        infrastructure allowed to depend on domain only.

        Returns:
            List of files created.
        """
        config_path = self.output_dir / "check_architecture.py"

        config_content = '''#!/usr/bin/env python3
"""Include-boundary architecture check for C/C++ layered projects.

Generated by Start Green Stay Green. Stdlib-only: any Python 3.10+
interpreter runs it, no install step required.

Why a script and not a tool config: no config-driven C/C++ layer linter
exists (unlike import-linter for Python, dependency-cruiser for
TypeScript, go-arch-lint for Go, or cargo-deny for Rust).
include-what-you-use targets include *hygiene* (its .imp mapping files
cannot express layer rules) and cpp-dependencies reports directory-level
dependency statistics without a layer-matrix config. This script IS the
config: edit ALLOWED_DEPENDENCIES below to change the matrix.

Enforcement limits (documented, not hidden):
  - This is a textual scan of #include directives,
    not a resolved dependency graph: transitive includes, forward
    declarations, and link-time dependencies are invisible to it.
  - Layers are defined by the src/<layer>/ and inc/<layer>/ directory
    convention; code outside those directories is unchecked, and an
    include only counts when its path starts with a layer name
    (#include "domain/clock.h"). Bare includes of sibling headers are
    NOT attributed to a layer.
  - Unlike SPM, Cargo, or Gradle, the C/C++ toolchain
    does NOT reject include cycles on its own (include guards merely
    mask them), so no cycle prevention can be attributed to the build
    system here. The layer matrix below forbids the back-edges between
    layers; intra-layer cycles remain out of scope.
  - Warn-first default: a layer directory that does not exist yet passes
    with a notice. Tighten by setting STRICT = True once every layer
    directory exists.

Dependency matrix (mirrors the Go go-arch-lint config):
  presentation -> application, domain
  application  -> domain
  infrastructure -> domain
  domain       -> (nothing)

Run from the project root (or via plans/architecture/run-check.sh):
  python3 plans/architecture/check_architecture.py
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

# --- Configuration (edit to fit your project) ---------------------------

# Which layers may include headers from which other layers.
ALLOWED_DEPENDENCIES: dict[str, frozenset[str]] = {
    "presentation": frozenset({"application", "domain"}),
    "application": frozenset({"domain"}),
    "infrastructure": frozenset({"domain"}),
    "domain": frozenset(),
}

# Directory roots scanned for the src/<layer> and inc/<layer> convention.
SOURCE_ROOTS = ("src", "inc")

SOURCE_SUFFIXES = frozenset({".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp"})

# Tighten-me: set True to fail when a layer directory is missing instead
# of passing with a notice (warn-first default while layers grow in).
STRICT = False

# -------------------------------------------------------------------------

# Matches #include "<layer>/..." and #include <<layer>/...>.
# Path-traversal includes (#include "../../other.h") are ignored by
# design: they do not name a layer, and banning them outright is a
# style decision left to clang-tidy.
_INCLUDE_RE = re.compile(r'^\\s*#\\s*include\\s+["<]([A-Za-z0-9_]+)/')


def _validate_matrix() -> list[str]:
    """Reject allowed-set entries that name no known layer (typo guard)."""
    errors: list[str] = []
    for layer, allowed in ALLOWED_DEPENDENCIES.items():
        for target in sorted(allowed):
            if target not in ALLOWED_DEPENDENCIES:
                errors.append(
                    f"ALLOWED_DEPENDENCIES['{layer}'] allows unknown "
                    f"layer '{target}' — typo?"
                )
    return errors


def _project_root() -> Path:
    """Resolve the project root whether parked or copied.

    The script ships in plans/architecture/; when run from there (or via
    run-check.sh at the project root) the project root is two levels up.
    If the user copies the script elsewhere, the working directory is
    assumed to be the project root.
    """
    script_dir = Path(__file__).resolve().parent
    if script_dir.name == "architecture" and script_dir.parent.name == "plans":
        return script_dir.parent.parent
    return Path.cwd()


def _layer_violations(layer_dir: Path, layer: str) -> list[str]:
    """Collect forbidden cross-layer includes inside one layer directory."""
    allowed = ALLOWED_DEPENDENCIES[layer]
    violations: list[str] = []
    for source in sorted(layer_dir.rglob("*")):
        if source.suffix not in SOURCE_SUFFIXES or not source.is_file():
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = _INCLUDE_RE.match(line)
            if match is None:
                continue
            target = match.group(1)
            if target in ALLOWED_DEPENDENCIES and target != layer:
                if target not in allowed:
                    violations.append(
                        f"{source}:{line_number}: layer '{layer}' must not "
                        f"include from layer '{target}' ({line.strip()})"
                    )
    return violations


def main() -> int:
    """Scan every layer directory and report boundary violations."""
    matrix_errors = _validate_matrix()
    if matrix_errors:
        print("Invalid ALLOWED_DEPENDENCIES matrix:")
        for error in matrix_errors:
            print(f"  {error}")
        return 2

    root = _project_root()
    violations: list[str] = []
    layers_found = 0
    for source_root in SOURCE_ROOTS:
        for layer in ALLOWED_DEPENDENCIES:
            layer_dir = root / source_root / layer
            if not layer_dir.is_dir():
                continue
            layers_found += 1
            violations.extend(_layer_violations(layer_dir, layer))

    if layers_found == 0:
        print(
            "No layer directories found under "
            f"{'/'.join(SOURCE_ROOTS)} (expected e.g. src/domain/). "
            "Passing (warn-first default; set STRICT = True to fail)."
        )
        return 1 if STRICT else 0

    if violations:
        print(f"Found {len(violations)} layer-boundary violation(s):")
        for violation in violations:
            print(f"  {violation}")
        return 1

    print(f"Architecture OK: {layers_found} layer director(y/ies) checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

        config_path.write_text(config_content)
        return [config_path]

    def _generate_readme(self, language: str, project_name: str) -> Path:
        """Generate README with usage instructions.

        Args:
            language: Target language.
            project_name: Name of the project.

        Returns:
            Path to generated README file.
        """
        readme_path = self.output_dir / "README.md"

        tooling = _LANGUAGE_TOOLING[language]
        tool = tooling.tool
        install_cmd = tooling.install_cmd
        # Manual invocation runs from the config directory, so the bare
        # config filename is correct here (no plans/architecture/ prefix).
        run_cmd = tooling.run_cmd.format(config_file=tooling.config_file)

        readme_content = f"""# Architecture Enforcement

This directory contains architecture enforcement rules for **{project_name}**.

## Purpose

Architecture rules ensure:
- **Layer Separation**: Higher layers depend on lower layers only
- **No Circular Dependencies**: Prevent tight coupling
- **Domain Independence**: Domain logic remains pure and testable

## Tool: {tool}

### Installation

```bash
{install_cmd}
```

### Usage

Run the architecture checks:

```bash
./run-check.sh
```

Or manually:

```bash
{run_cmd}
```


## Rules Enforced

### Layer Separation

- **Presentation** → Application → Domain → Infrastructure
- Domain layer cannot depend on infrastructure or presentation
- Each layer can only depend on layers below it

### Circular Dependencies

All circular dependencies are forbidden. They create:
- Tight coupling
- Difficult testing
- Complex refactoring
- Hidden dependencies

### Domain Independence

The domain layer must remain pure:
- No framework dependencies
- No database dependencies
- No UI dependencies
- Only business logic

## Customization

Edit the configuration file:
- Python: `.importlinter`
- TypeScript: `.dependency-cruiser.js`
- Go: `.go-arch-lint.yml`
- Rust: `deny.toml`
- Swift: `.swiftlint-architecture.yml`
- Kotlin: `ArchitectureTest.kt`
- C/C++: `check_architecture.py` (the ALLOWED_DEPENDENCIES matrix at the top)

See documentation:
- Python: https://import-linter.readthedocs.io/
- TypeScript: https://github.com/sverweij/dependency-cruiser
- Go: https://github.com/fe3dback/go-arch-lint
- Rust: https://embarkstudios.github.io/cargo-deny/
- Swift: https://realm.github.io/SwiftLint/custom_rules.html
- Kotlin: https://docs.konsist.lemonappdev.com/
- C/C++: the header comment in check_architecture.py (self-documented)

## Integration

Add to CI pipeline:

```yaml
- name: Check Architecture
  run: ./plans/architecture/run-check.sh
```

## References

- Clean Architecture (Robert C. Martin)
- Hexagonal Architecture (Alistair Cockburn)
- Domain-Driven Design (Eric Evans)
"""

        readme_path.write_text(readme_content)
        return readme_path

    def _generate_run_script(
        self, language: str, project_name: str  # noqa: ARG002
    ) -> Path:
        """Generate executable run-check.sh script.

        Args:
            language: Target language.
            project_name: Name of the project.

        Returns:
            Path to generated run script.
        """
        script_path = self.output_dir / "run-check.sh"

        script_content = self._build_run_script(language)

        script_path.write_text(script_content)

        # Make script executable
        script_path.chmod(0o755)

        return script_path

    @staticmethod
    def _build_run_script(language: str) -> str:
        """Build the run-check.sh contents for a language.

        Derives the command and the binary-availability guard from the
        shared :data:`_LANGUAGE_TOOLING` metadata so adding a language
        requires no changes here.

        Args:
            language: Target language.

        Returns:
            The shell script source for run-check.sh.
        """
        tooling = _LANGUAGE_TOOLING[language]
        # The first token of run_cmd is the binary to probe with command -v.
        binary = tooling.run_cmd.split()[0]
        # Fill the {config_file} placeholder with the path-prefixed config so
        # the script works when invoked from the project root. Using the
        # template (rather than substring replacement) keeps the substitution
        # immune to accidental collisions with other tokens in run_cmd.
        full_cmd = tooling.run_cmd.format(
            config_file=f"plans/architecture/{tooling.config_file}",
        )
        return f"""#!/usr/bin/env bash
set -euo pipefail

echo "🏛️  Checking {tooling.display_name} architecture with {tooling.tool}..."

if ! command -v {binary} &> /dev/null; then
    echo "❌ {tooling.tool} not found. Install with: {tooling.install_cmd}"
    exit 1
fi

{full_cmd}

echo "✅ Architecture checks passed!"
"""
