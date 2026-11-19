#!/usr/bin/env python3
r"""Verify that every symbol a scan finding cites exists at the scan SHA.

Scan agents paraphrase. Given a file and a line range, a model will happily
cite ``_unique_filename`` when the code says ``_generate_filename``, or
``verify_chain`` when it says ``verify``. Coverage scans are the worst case:
``--cov-report=term-missing`` prints line numbers and no names, so there is
nothing to copy and the gap gets filled by invention. A prompt sentence asking
the model to be careful does not fix that; refusing the citation does.

Input: newline-delimited JSON findings on stdin, one object per line::

    {"file": "pkg/mod.py", "symbol": "name", "lines": "10-20"}

``symbol`` may be absent (not every finding names one), a string, or a list
(``symbols`` is accepted too). A dotted name is checked on its last segment.

For each cited symbol the blob is read **at the scan SHA** (``git show
SHA:path``), never the working tree: a citation is a claim about a specific
revision.

Verdicts:

* definition-shaped match for the name in the blob -> OK
* the name appears only as a bare word (e.g. a call site) -> WARNING; the
  definition probably lives in another file, so re-check the citation
* the name appears nowhere in the blob -> PHANTOM (fails the run)
* the blob is unreadable (unknown SHA, path absent at that SHA) -> fails the
  run; an unreadable citation is exactly what a stale one looks like, so
  failing open there would make the gate decorative
* a line that is not a JSON object -> fails the run (a broken producer must
  not look like "no symbols declared")

Exit status: 0 when every cited symbol resolves, 1 otherwise.

Usage::

    printf '%s\n' "$FINDINGS_NDJSON" \
      | SCAN_SHA="$(git rev-parse HEAD)" \
        python3 .claude/skills/scan-issue-writer/scripts/verify_scan_citations.py

This check is language-agnostic and deliberately cheap: it proves a name
exists in the cited file, not that the citation is semantically right. A repo
that ships a stronger, AST-based verifier should run that one instead.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

_METHOD_MODIFIERS = "public|private|protected|static|async|readonly|override|get|set"
_DEF_KEYWORDS = (
    r"def|class|function|interface|type|enum|const|let|var|fn|func|struct|"
    r"trait|impl|module|macro_rules!"
)

# A cited line range: "120" or "120-164".
_RANGE_RE = re.compile(r"^\s*(\d+)(?:\s*-\s*(\d+))?\s*$")


def _emit(message: str) -> None:
    """Write one line of output (GitHub Actions annotations included)."""
    sys.stdout.write(f"{message}\n")


def _definition_re(name: str) -> re.Pattern[str]:
    """Build a regex matching a definition-shaped occurrence of *name*.

    Args:
        name: The bare (undotted) symbol name.

    Returns:
        A multiline regex covering common Python / TS / JS / Go / Rust forms:
        keyword definitions, Go methods, class-body methods, and assignments.
    """
    n = re.escape(name)
    patterns = [
        rf"\b(?:async\s+)?(?:{_DEF_KEYWORDS})\s*\*?\s+{n}\b",  # def name / fn name
        rf"\bfunc\s*\([^)]*\)\s*{n}\b",  # Go method
        # class-body method
        rf"^\s*(?:(?:{_METHOD_MODIFIERS})\s+)*{n}\s*[(<][^;\n]*\)[^;\n(]*\{{",
        rf"^\s*(?:export\s+)?{n}\s*[:=]",  # NAME = ... / key: ...
    ]
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.MULTILINE)


def _git() -> str:
    """Return the absolute path of the git executable.

    Raises:
        FileNotFoundError: If git is not on PATH.
    """
    git = shutil.which("git")
    if git is None:
        msg = "git is required to read files at the scan SHA"
        raise FileNotFoundError(msg)
    return git


def _blob_at(sha: str, path: str) -> str | None:
    """Return *path* as of *sha*, or None when it cannot be read."""
    result = subprocess.run(
        [_git(), "show", f"{sha}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _citations(line: str) -> list[tuple[str, str, str]]:
    """Return ``(file, symbol, lines)`` triples from one findings line.

    Raises:
        ValueError: If the line is not valid JSON.
        TypeError: If the line is JSON but not an object.
    """
    finding = json.loads(line)
    if not isinstance(finding, dict):
        msg = f"finding is {type(finding).__name__}, expected an object"
        raise TypeError(msg)
    symbols = finding.get("symbol") or finding.get("symbols") or []
    if isinstance(symbols, str):
        symbols = [symbols]
    path = str(finding.get("file", ""))
    lines = str(finding.get("lines", ""))
    return [(path, str(name), lines) for name in symbols if str(name)]


def _range_hint(blob: str, lines: str) -> str:
    """Return the cited lines' first definition, to suggest the real name."""
    match = _RANGE_RE.match(lines)
    if not match:
        return ""
    text = blob.splitlines()
    start = int(match.group(1))
    # Walk back from the cited line to the nearest definition-looking line.
    for idx in range(min(start, len(text)) - 1, -1, -1):
        stripped = text[idx].strip()
        if re.match(rf"(?:async\s+)?(?:{_DEF_KEYWORDS})\b", stripped):
            return f"; the nearest definition above line {start} is: {stripped[:100]!r}"
    return ""


def _check(sha: str, path: str, symbol: str, lines: str) -> tuple[str, str]:
    """Check one citation and return ``(verdict, message)``."""
    if not path:
        return "ERROR", f"symbol {symbol!r} cites no file"
    blob = _blob_at(sha, path)
    if blob is None:
        return "ERROR", (
            f"cannot read {path!r} at {sha[:12]}; a citation that cannot "
            "be checked must not be reported as verified"
        )
    leaf = symbol.rsplit(".", 1)[-1].rstrip("()")
    if _definition_re(leaf).search(blob):
        return "OK", f"{symbol} defined in {path} at {sha[:12]}"
    if re.search(rf"\b{re.escape(leaf)}\b", blob):
        return "WARN", (
            f"{symbol!r} appears in {path} at {sha[:12]} but not as a "
            "definition; it may be defined elsewhere, so check the citation "
            "points where it claims"
        )
    return "PHANTOM", (
        f"{symbol!r} does not appear in {path} at {sha[:12]}{_range_hint(blob, lines)}"
    )


def main() -> int:
    """Verify every citation on stdin; return the process exit status."""
    sha = (
        os.environ.get("SCAN_SHA")
        or subprocess.run(
            [_git(), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    failures = checked = read = 0
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        read += 1
        try:
            triples = _citations(line)
        except (ValueError, TypeError) as exc:  # JSONDecodeError is a ValueError
            _emit(f"::error::malformed finding JSON: {exc}")
            failures += 1
            continue
        for path, symbol, lines in triples:
            checked += 1
            verdict, message = _check(sha, path, symbol, lines)
            if verdict in {"ERROR", "PHANTOM"}:
                _emit(f"::error::{verdict} {message}")
                failures += 1
            elif verdict == "WARN":
                _emit(f"::warning::{message}")
    if failures:
        _emit(
            f"::error::{failures} unverifiable or phantom citation(s) at "
            f"{sha[:12]}; refusing to file. Re-resolve each against the scan "
            "SHA and cite the real name, or drop the symbol."
        )
        return 1
    if read and not checked:
        # A gate that checked nothing must not read like a clean pass.
        _emit(
            f"::warning::read {read} finding(s) but checked 0 symbols. Any "
            "finding that names a function, class or method MUST declare a "
            "symbol field."
        )
    _emit(f"verify-scan-citations: {checked} symbol citation(s) verified at {sha[:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
