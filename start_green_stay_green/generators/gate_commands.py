"""Cross-platform gate documentation for generated projects (#386).

The single source of truth mapping each scaffolded language's quality
gate scripts to the toolchain-native cross-platform command they wrap.
The scripts generator renders this table into a ``scripts/README.md``
inside every generated project, so each gate has a documented Windows
invocation without any per-language Windows shims (DRY): the shared
mechanism is "run the POSIX script through Git Bash, or fall back to
the language's own cross-platform toolchain runner".

This mirrors the #382 pattern used by this repository itself, where the
bash scripts are thin delegates and one documented cross-platform entry
point carries the gate logic. Generated projects keep their bash gates
unchanged; the toolchain runners (npm/npx, go, cargo, gradle, swift,
mvn, dotnet, bundle, cmake/ctest) are already cross-platform, so the
documentation layer is all that is needed.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Placeholder substituted with the project's package name. A literal
#: marker (not ``str.format``) because some commands contain shell brace
#: globs like ``*.{ts,tsx}`` that ``format`` would mis-parse.
_PACKAGE_PLACEHOLDER = "__PACKAGE__"

#: Language aliases accepted by the scripts generator's dispatch table.
_LANGUAGE_ALIASES: dict[str, str] = {
    "ts": "typescript",
    "javascript": "typescript",
    "js": "typescript",
}

#: Fallback language, mirroring ``ScriptsGenerator.generate()``'s
#: python-builder fallback for unknown languages.
_FALLBACK_LANGUAGE = "python"


@dataclass(frozen=True)
class GateDoc:
    """Documentation for one quality gate script.

    Attributes:
        native: Toolchain-native cross-platform command the gate wraps
            (empty when no single command honestly captures the gate).
        note: Optional honest qualifier shown alongside the command.
    """

    native: str = ""
    note: str = ""


#: Gate rows shared by every language (language-agnostic scripts).
_SHARED_GATE_DOCS: dict[str, GateDoc] = {
    "check-all.sh": GateDoc(note="runs every other gate in order"),
    "pr-status.sh": GateDoc(note="wraps the GitHub CLI (`gh`); use Git Bash"),
    "fix-all.sh": GateDoc(note="runs the fixing modes of the gates above"),
}

#: Language-specific gate → toolchain-native command. The commands are
#: the core tool invocations each generated script wraps; the scripts
#: remain the source of truth for option sets, ordering, and thresholds.
#: The shared rows are merged in below (single definition, DRY).
_LANGUAGE_GATE_DOCS: dict[str, dict[str, GateDoc]] = {
    "python": {
        "format.sh": GateDoc("isort . && black ."),
        "lint.sh": GateDoc("ruff check ."),
        "test.sh": GateDoc("pytest tests/"),
        "typecheck.sh": GateDoc(f"mypy {_PACKAGE_PLACEHOLDER}/"),
        "coverage.sh": GateDoc(
            f"pytest --cov={_PACKAGE_PLACEHOLDER} --cov-branch"
            " --cov-report=term-missing --cov-fail-under=90 tests/"
        ),
        "security.sh": GateDoc(f"bandit -r {_PACKAGE_PLACEHOLDER}/ && pip-audit"),
        "complexity.sh": GateDoc(
            f"radon cc -a {_PACKAGE_PLACEHOLDER}/ && xenon --max-absolute B"
            f" --max-modules B --max-average B {_PACKAGE_PLACEHOLDER}/"
        ),
        "mutation.sh": GateDoc("mutmut run"),
    },
    "typescript": {
        "format.sh": GateDoc(
            'npx prettier --check "src/**/*.{ts,tsx}"'
            ' "tests/**/*.{ts,tsx}" "*.{js,json}"'
        ),
        "lint.sh": GateDoc("npx eslint ."),
        "test.sh": GateDoc("npx jest"),
        "typecheck.sh": GateDoc("npx tsc --noEmit"),
    },
    "go": {
        "format.sh": GateDoc("go fmt ./..."),
        "lint.sh": GateDoc("golangci-lint run ./..."),
        "test.sh": GateDoc("go test -cover ./..."),
    },
    "rust": {
        "format.sh": GateDoc("cargo fmt --all -- --check"),
        "lint.sh": GateDoc("cargo clippy --all -- -D warnings"),
        "test.sh": GateDoc("cargo test"),
    },
    "swift": {
        "format.sh": GateDoc("swift-format lint --strict --recursive Sources Tests"),
        "lint.sh": GateDoc("swiftlint lint --strict"),
        "test.sh": GateDoc("swift test --enable-code-coverage"),
        "security.sh": GateDoc("periphery scan --strict"),
    },
    "kotlin": {
        "format.sh": GateDoc("ktlint"),
        "lint.sh": GateDoc("detekt --config detekt.yml --build-upon-default-config"),
        "test.sh": GateDoc(
            "./gradlew test",
            note="from cmd.exe/PowerShell use `gradlew.bat test`",
        ),
        "security.sh": GateDoc(
            note="OWASP dependency-check CLI; see the script for arguments"
        ),
    },
    "cpp": {
        "format.sh": GateDoc(
            note="clang-format over src/, inc/, tests/; see the script"
        ),
        "lint.sh": GateDoc(
            note="clang-tidy (-p build), cppcheck, and lizard; see the script"
        ),
        "test.sh": GateDoc(
            "cmake --build build && ctest --test-dir build --output-on-failure"
        ),
        "security.sh": GateDoc("flawfinder --error-level=4 --minlevel=1 src inc tests"),
    },
    "java": {
        "format.sh": GateDoc(
            note="google-java-format over the source tree; see the script"
        ),
        "lint.sh": GateDoc("mvn -q checkstyle:check && mvn -q pmd:check"),
        "test.sh": GateDoc("mvn test"),
        "security.sh": GateDoc("mvn -q compile spotbugs:check"),
    },
    "csharp": {
        "format.sh": GateDoc("dotnet format --verify-no-changes"),
        "lint.sh": GateDoc(
            "dotnet build --nologo",
            note="the csproj promotes analyzer warnings to errors",
        ),
        "test.sh": GateDoc("dotnet test"),
        "security.sh": GateDoc("dotnet list package --vulnerable"),
    },
    "ruby": {
        "format.sh": GateDoc("bundle exec rubocop --only Layout --force-exclusion"),
        "lint.sh": GateDoc("bundle exec rubocop --force-exclusion"),
        "test.sh": GateDoc("bundle exec rspec"),
        "security.sh": GateDoc("bundle exec bundler-audit check"),
    },
}

#: Per-language gate documentation: the shared language-agnostic rows
#: merged with each language's toolchain-specific rows.
GATE_DOCS: dict[str, dict[str, GateDoc]] = {
    language: _SHARED_GATE_DOCS | rows for language, rows in _LANGUAGE_GATE_DOCS.items()
}

#: Optional language-specific preamble for the Windows notes section.
_LANGUAGE_NOTES: dict[str, str] = {
    "python": (
        "The toolchain-native commands assume the project virtualenv is "
        "active (`.venv\\Scripts\\activate` on Windows, "
        "`source .venv/bin/activate` on POSIX)."
    ),
    "kotlin": (
        "`./gradlew` is the Gradle wrapper's POSIX/Git Bash entry point; "
        "from cmd.exe or PowerShell use `gradlew.bat` instead."
    ),
}

_README_HEADER = """\
# Quality Gate Scripts

Generated by Start Green Stay Green. Each script is one quality gate;
`check-all.sh` runs the full set. Every script supports `--help`.

## Running the gates

| Gate | Linux / macOS | Windows (Git Bash) | Toolchain-native command |
| --- | --- | --- | --- |
"""

_WINDOWS_SECTION = """\

## Windows

The gate scripts are POSIX shell. On Windows, run them through Git Bash
(bundled with Git for Windows) — no executable bit is needed because
bash receives the script path as an argument:

    bash scripts/check-all.sh

The generated `.gitattributes` pins `*.sh` to LF line endings so the
scripts survive `git clone` on checkouts where `core.autocrlf=true`
(bash cannot execute CRLF scripts). Keep that rule if you customise the
file.

Where bash is unavailable, the toolchain-native column above shows the
cross-platform command each gate wraps — the language's own runner
works on Windows natively. Honest limitation: the bare commands do not
reproduce everything the scripts enforce (option sets, gate ordering,
and threshold checks such as minimum coverage), so the scripts remain
the source of truth; prefer Git Bash when possible.
"""


def canonical_language(language: str) -> str:
    """Resolve a language identifier to its canonical documented name.

    Mirrors ``ScriptsGenerator.generate()``: aliases (``ts``, ``js``,
    ``javascript``) collapse to ``typescript``, and unknown languages
    fall back to ``python`` because that is the builder generate() uses
    for them.

    Args:
        language: Language identifier as configured by the user.

    Returns:
        A key of :data:`GATE_DOCS`.
    """
    resolved = _LANGUAGE_ALIASES.get(language, language)
    if resolved not in GATE_DOCS:
        return _FALLBACK_LANGUAGE
    return resolved


def _native_cell(doc: GateDoc, package_name: str) -> str:
    """Render the toolchain-native column for one gate row.

    Args:
        doc: Documentation entry for the gate.
        package_name: Package name substituted into python commands.

    Returns:
        Markdown cell text: the backticked command, the note, or an
        em-dash when neither exists.
    """
    command = doc.native.replace(_PACKAGE_PLACEHOLDER, package_name)
    if command and doc.note:
        return f"`{command}` ({doc.note})"
    if command:
        return f"`{command}`"
    if doc.note:
        return f"— ({doc.note})"
    return "—"


def render_scripts_readme(
    language: str,
    script_names: list[str],
    *,
    package_name: str,
) -> str:
    """Render the ``scripts/README.md`` content for a generated project.

    Documents three invocations per emitted gate: the POSIX path
    (``./scripts/<gate>``), the Windows path (``bash scripts/<gate>``
    via Git Bash), and the toolchain-native cross-platform command the
    gate wraps. Only ``.sh`` scripts get rows; helper files (for
    example ``analyze_mutations.py``) are internal to their gates.

    Args:
        language: Language identifier (aliases and unknown values are
            resolved via :func:`canonical_language`).
        script_names: Names of the scripts actually emitted, so the
            table can never drift from the generated output.
        package_name: Package name substituted into python commands.

    Returns:
        Deterministic markdown content using LF line endings only.
    """
    resolved = canonical_language(language)
    docs = GATE_DOCS[resolved]

    gates = sorted(
        (name for name in script_names if name.endswith(".sh")),
        key=lambda name: (name != "check-all.sh", name),
    )
    rows = []
    for name in gates:
        native = _native_cell(docs.get(name, GateDoc()), package_name)
        rows.append(
            f"| `{name}` | `./scripts/{name}` | `bash scripts/{name}` " f"| {native} |"
        )

    sections = [_README_HEADER + "\n".join(rows) + "\n", _WINDOWS_SECTION]
    note = _LANGUAGE_NOTES.get(resolved)
    if note is not None:
        sections.append(f"\n{note}\n")
    return "".join(sections)
