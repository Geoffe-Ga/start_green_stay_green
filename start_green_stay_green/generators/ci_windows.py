"""Opt-in Windows CI leg for generated workflows (#388, windows-compat #378).

The single source of truth for the ``quality-windows`` job that
``green init --windows-ci`` appends to the generated
``.github/workflows/ci.yml``. The job mirrors the pattern Start Green
Stay Green's own Windows CI leg (#380) established and invokes the
quality gates the way ``scripts/README.md`` documents for Windows
(#386): ``bash scripts/<gate>.sh`` through Git Bash, which ships with
Git for Windows and is preinstalled on the ``windows-latest`` runner
image.

Design notes:

* **Default off.** Nothing here runs unless the user opts in, so the
  default generated CI is byte-for-byte unchanged and no one pays for
  Windows runner minutes by surprise.
* **One job shape, parameterized per language (DRY).** Every language
  shares the same scaffold — LF-safe checkout, toolchain setup,
  dependency install, then gate invocations through Git Bash — and only
  the toolchain setup fragment and gate list vary, exactly where the
  per-language Linux templates already vary.
* **No invented versions.** Every action the leg references reuses a
  pin that already appears in the language's ``reference/ci/*.yml``
  template, so version bumps stay single-sourced in the templates.
* **A smoke leg, not a second matrix.** The leg runs once on the newest
  toolchain version from the Linux quality matrix; languages keep their
  multi-version coverage on Linux.

Supported languages and the honest reasons for each exclusion:

* ``swift`` is excluded: the scaffolded gates run SwiftLint and
  swift-format, which have no Windows distribution, and the reference
  workflow targets macOS/Linux toolchains.
* ``cpp`` is excluded: the reference workflow provisions the toolchain
  with ``apt-get`` (Linux-only); no equivalent Windows provisioning is
  scaffolded.
* ``kotlin`` is excluded: the gate scripts call ``./gradlew``, but the
  Gradle wrapper jar is a binary ``green init`` never writes — the
  language's own CI deliberately runs ``gradle`` directly for the same
  reason — so the Git Bash gate path cannot run on a fresh checkout.
* ``go`` runs only its test gate: the lint gate needs golangci-lint,
  which the Linux quality job provisions through a Linux-specific
  action; ``go test`` needs nothing beyond the Go toolchain.
"""

from __future__ import annotations

import io

import yaml

#: Job id of the opt-in Windows leg inside the generated workflow.
WINDOWS_JOB_ID = "quality-windows"

#: Languages whose generated projects support the opt-in Windows leg.
#: Kept in the CLI's canonical language order. See the module docstring
#: for why swift, cpp, and kotlin are excluded.
WINDOWS_CI_LANGUAGES: tuple[str, ...] = (
    "python",
    "typescript",
    "go",
    "rust",
    "java",
    "csharp",
    "ruby",
)

#: Gate scripts the Windows leg invokes per language, in execution
#: order. Each entry is a script the scripts generator emits for that
#: language; the leg runs them as ``bash scripts/<gate>`` (the #386
#: Windows invocation). lint + test mirrors the smoke-leg scope of this
#: repository's own Windows CI job; go drops lint (module docstring).
WINDOWS_GATES: dict[str, tuple[str, ...]] = {
    "python": ("lint.sh", "test.sh"),
    "typescript": ("lint.sh", "test.sh"),
    "go": ("test.sh",),
    "rust": ("lint.sh", "test.sh"),
    "java": ("lint.sh", "test.sh"),
    "csharp": ("lint.sh", "test.sh"),
    "ruby": ("lint.sh", "test.sh"),
}

#: Job-level env blocks (4-space indented YAML lines), per language.
#: Only python needs one: Windows Python defaults text I/O to the
#: legacy ANSI code page (cp1252) while the gates and generated content
#: are UTF-8, so the leg enables Python's UTF-8 mode (PEP 540) for the
#: gate processes it spawns — the same fix this repository's own
#: Windows CI leg applies.
_JOB_ENV: dict[str, str] = {
    "python": """\
    env:
      # Windows Python defaults text I/O to the legacy ANSI code page
      # (cp1252); the gates and project content are UTF-8, so enable
      # Python's UTF-8 mode (PEP 540) for every gate process.
      PYTHONUTF8: "1"
""",
}

#: Toolchain setup + dependency install steps per language (6-space
#: indented YAML list items). Single-version: the newest entry from the
#: language's Linux quality matrix — this is a smoke leg, not a second
#: matrix. Action pins are reused from ``reference/ci/<language>.yml``.
_SETUP_STEPS: dict[str, str] = {
    "python": """\
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt
""",
    "typescript": """\
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20.x"
          cache: 'npm'

      # Like the Linux quality job, `npm ci` expects the lockfile the
      # first local `npm install` commits.
      - name: Install dependencies
        run: npm ci
""",
    "go": """\
      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: "1.22"
          cache: true

      - name: Download dependencies
        run: go mod download
""",
    "rust": """\
      - name: Set up Rust
        uses: dtolnay/rust-toolchain@master
        with:
          toolchain: stable
          components: rustfmt, clippy
""",
    "java": """\
      - name: Set up JDK
        uses: actions/setup-java@v4
        with:
          java-version: "21"
          distribution: 'temurin'
          cache: 'maven'
""",
    "csharp": """\
      - name: Set up .NET
        uses: actions/setup-dotnet@v4
        with:
          dotnet-version: "8.0"

      - name: Restore dependencies
        run: dotnet restore
""",
    "ruby": """\
      - name: Set up Ruby
        uses: ruby/setup-ruby@v1
        with:
          ruby-version: "3.4"
          # bundler-cache runs `bundle install` and caches the gems.
          bundler-cache: true
""",
}

#: Shared job preamble. ``needs: quality`` gates the leg behind the
#: Linux quality job (present in every reference template and enforced
#: by the CI generator's validation) so a red Linux run never burns
#: Windows minutes.
_JOB_HEADER = f"""\
  # Opt-in Windows leg (`green init --windows-ci`). Runs the quality
  # gates on windows-latest through Git Bash — the documented Windows
  # invocation (`bash scripts/<gate>.sh`, see scripts/README.md) —
  # mirroring the Windows CI pattern of the generator's own pipeline.
  {WINDOWS_JOB_ID}:
    name: Quality Gates (Windows)
    runs-on: windows-latest
    needs: quality
    # Cap a hung Windows runner well above a healthy gate runtime.
    timeout-minutes: 30
"""

#: Shared first steps: force-LF checkout. Windows git defaults to
#: ``core.autocrlf=true``, which would check the repo out with CRLF
#: endings — bash cannot execute CRLF scripts. The generated
#: ``.gitattributes`` already pins ``*.sh`` to LF; configuring git
#: before checkout keeps the leg green even where that file has been
#: customised (belt and suspenders, same as the reference pattern).
_CHECKOUT_STEPS = """\
    steps:
      - name: Force LF line endings on checkout
        run: |
          git config --global core.autocrlf false
          git config --global core.eol lf

      - name: Checkout code
        uses: actions/checkout@v4

"""


def _unsupported_language_message(language: str) -> str:
    """Build the fail-fast message for an unsupported language.

    Args:
        language: The rejected language identifier.

    Returns:
        An actionable message naming every supported language.
    """
    supported = ", ".join(WINDOWS_CI_LANGUAGES)
    return (
        f"the opt-in windows-latest CI leg does not support {language!r} "
        f"(supported: {supported}); see generators/ci_windows.py for the "
        "per-language rationale"
    )


def _gate_steps(language: str) -> str:
    """Render the gate-invocation steps for ``language``.

    Each gate runs as ``bash scripts/<gate>`` with ``shell: bash`` so
    the step uses Git Bash regardless of the runner's default shell
    (PowerShell on windows-latest).

    Args:
        language: A key of :data:`WINDOWS_GATES`.

    Returns:
        YAML list items (6-space indented), one step per gate.
    """
    steps = []
    for gate in WINDOWS_GATES[language]:
        stem = gate.removesuffix(".sh")
        steps.append(f"""\
      - name: Run {stem} gate (Git Bash)
        shell: bash
        run: bash scripts/{gate}
""")
    return "\n".join(steps)


def render_windows_job(language: str) -> str:
    """Render the ``quality-windows`` job block for ``language``.

    The block is indented two spaces so it nests directly under a
    workflow's top-level ``jobs:`` mapping. Rendering is pure string
    assembly from module constants — deterministic and LF-only.

    Args:
        language: Generated project's language; must be in
            :data:`WINDOWS_CI_LANGUAGES`.

    Returns:
        The YAML job block, ending with a single trailing newline.

    Raises:
        ValueError: If the language has no supported Windows leg.
    """
    if language not in WINDOWS_CI_LANGUAGES:
        raise ValueError(_unsupported_language_message(language))

    parts = [_JOB_HEADER]
    env_block = _JOB_ENV.get(language)
    if env_block is not None:
        parts.append(env_block)
    parts.extend((_CHECKOUT_STEPS, _SETUP_STEPS[language], "\n", _gate_steps(language)))
    return "".join(parts)


def append_windows_job(workflow_yaml: str, language: str) -> str:
    """Append the Windows leg to a rendered workflow's jobs mapping.

    Relies on ``jobs`` being the final top-level key of the workflow —
    true for every reference template — and verifies the result by
    re-parsing, so a workflow with a different layout fails loudly
    instead of silently emitting a job outside ``jobs``.

    Args:
        workflow_yaml: Complete rendered workflow YAML.
        language: Generated project's language; must be in
            :data:`WINDOWS_CI_LANGUAGES`.

    Returns:
        The workflow YAML with the ``quality-windows`` job appended.

    Raises:
        ValueError: If the language is unsupported, or the appended job
            did not attach under the ``jobs`` mapping.
    """
    job_block = render_windows_job(language)
    merged = workflow_yaml.rstrip("\n") + "\n\n" + job_block

    try:
        with io.StringIO(merged) as stream:
            parsed = yaml.safe_load(stream)
    except yaml.YAMLError as e:
        msg = f"appending the Windows CI leg produced invalid YAML: {e}"
        raise ValueError(msg) from e
    jobs = parsed.get("jobs") if isinstance(parsed, dict) else None
    if not isinstance(jobs, dict) or WINDOWS_JOB_ID not in jobs:
        msg = (
            "could not attach the Windows CI leg under the workflow's "
            "'jobs' mapping; 'jobs' must be the final top-level key"
        )
        raise ValueError(msg)
    return merged
