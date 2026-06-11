"""Security gate — Bandit + pip-audit (port of ``scripts/security.sh``).

Preserves the #380 pragmatic-resilience behavior verbatim: pip-audit
queries osv.dev (PyPI's JSON API caused repeated 503 CI failures), skips
the local editable package, honors the ``.pip-audit-known-vulnerabilities``
ignore file, and retries exactly once after a 10s delay — a retried audit
is still a full audit, so the gate is not weakened.
"""

from __future__ import annotations

import json
import sys
import time
from time import sleep
from typing import TYPE_CHECKING

from start_green_stay_green.gates import common

if TYPE_CHECKING:
    import argparse

#: Seconds to wait before the single pip-audit retry (security.sh parity).
RETRY_DELAY_SECONDS = 10

#: Repo-relative file listing pip-audit vulnerability IDs to ignore, one
#: per line with optional ``#`` comments. Each entry must have a
#: corresponding tracking issue.
IGNORE_FILE = ".pip-audit-known-vulnerabilities"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse security gate arguments (parity with security.sh).

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        Parsed namespace.
    """
    parser = common.gate_parser(
        "security", "Run security checks using Bandit and pip-audit."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run comprehensive security scan",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Output machine-readable JSON metrics to stdout",
    )
    return parser.parse_args(argv)


def _parse_bandit_issues(payload: str) -> int | None:
    """Extract the issue count from bandit JSON output.

    Args:
        payload: Raw ``bandit -f json`` stdout.

    Returns:
        Number of results, or None when the payload is unparseable
        (the script's "unknown" state).
    """
    try:
        data = json.loads(payload)
        issues = len(data.get("results", []))
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None
    return issues


def _bandit_metrics_payload() -> str:
    """Fetch bandit's JSON report for metrics mode.

    Returns:
        Raw bandit JSON output, or empty when bandit is unavailable.
    """
    bandit = common.resolve_tool("bandit")
    if bandit is None:
        return ""
    result = common.run_tool(
        [bandit, "-r", "start_green_stay_green/", "-ll", "-f", "json"],
        stdout=common.PIPE,
        stderr=common.DEVNULL,
    )
    return result.stdout or ""


def _metrics() -> int:
    """Emit machine-readable security metrics (security.sh --metrics).

    Returns:
        Always 0, matching the script's unconditional ``exit 0``.
    """
    payload = _bandit_metrics_payload()
    if not payload.strip():
        print('{"bandit_issues": null, "status": "unknown"}')
        return 0
    issues = _parse_bandit_issues(payload)
    if issues is None:
        print('{"bandit_issues": null, "status": "unknown"}')
        return 0
    status = "pass" if issues == 0 else "fail"
    print(json.dumps({"bandit_issues": issues, "status": status}))
    return 0


def _run_bandit(bandit: str, *, verbose: bool) -> bool:
    """Run the Bandit source scan.

    Args:
        bandit: Absolute path to the bandit executable.
        verbose: Whether to print progress detail.

    Returns:
        True when bandit found no issues.
    """
    print("=== Security Checks (Bandit) ===")
    if verbose:
        print("Running Bandit security scanner...")
    result = common.run_tool([bandit, "-r", "start_green_stay_green/"])
    if result.returncode != 0:
        print("✗ Bandit found issues", file=sys.stderr)
        return False
    return True


def load_ignore_args() -> list[str]:
    """Build ``--ignore-vuln`` flags from the known-vulnerabilities file.

    Strips inline ``#`` comments and whitespace and skips empty lines,
    mirroring security.sh's parsing.

    Returns:
        Flat list of ``--ignore-vuln <id>`` argument pairs.
    """
    path = common.project_root() / IGNORE_FILE
    if not path.is_file():
        return []
    flags: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        vuln_id = line.split("#", 1)[0].strip()
        if vuln_id:
            flags.extend(["--ignore-vuln", vuln_id])
    return flags


def _run_pip_audit(pip_audit: str, *, verbose: bool) -> bool:
    """Run pip-audit with the osv service, ignore file, and one retry.

    Args:
        pip_audit: Absolute path to the pip-audit executable.
        verbose: Whether to print progress detail.

    Returns:
        True when the audit (or its single retry) passed.
    """
    print("=== Security Checks (pip-audit) ===")
    if verbose:
        print("Running pip-audit dependency checker...")
    cmd = [
        pip_audit,
        "--vulnerability-service",
        "osv",
        "--skip-editable",
        *load_ignore_args(),
    ]
    result = common.run_tool(cmd)
    if result.returncode == 0:
        return True
    _surface_audit_stderr(
        "⚠ pip-audit failed once; retrying in 10s (stderr below)",
        result.stderr,
    )
    sleep(RETRY_DELAY_SECONDS)
    retry = common.run_tool(cmd)
    if retry.returncode == 0:
        return True
    # Surface the captured stderr: without it a transient OSV
    # ServiceError is indistinguishable from a real vulnerability
    # finding in CI logs.
    _surface_audit_stderr("✗ pip-audit failed; stderr follows:", retry.stderr)
    return False


def _surface_audit_stderr(message: str, stderr: str | None) -> None:
    """Print an audit failure message followed by the captured stderr.

    Args:
        message: Failure headline.
        stderr: Captured pip-audit stderr (may be None).
    """
    print(message, file=sys.stderr)
    print(stderr or "", file=sys.stderr, end="")


def _run_detect_secrets(*, verbose: bool) -> None:
    """Run the optional detect-secrets scan (``--full`` mode, warn-first).

    Failures are deliberately non-fatal, matching the script's
    ``detect-secrets scan . || true``.

    Args:
        verbose: Whether to print progress detail.
    """
    print("=== Comprehensive Security Scan ===")
    detect_secrets = common.resolve_tool("detect-secrets")
    if detect_secrets is None:
        return
    if verbose:
        print("Running detect-secrets scan...")
    common.run_tool([detect_secrets, "scan", "."])


def main(argv: list[str] | None = None) -> int:
    """Entry point for the security gate.

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        0 on success, 1 on findings, 2 on runner errors.
    """
    args = _parse_args(argv)
    start = time.monotonic()
    common.enter_project_root()
    if args.metrics:
        return _metrics()
    bandit = common.resolve_tool("bandit")
    pip_audit = common.resolve_tool("pip-audit")
    if bandit is None or pip_audit is None:
        print("Error: bandit/pip-audit are not installed", file=sys.stderr)
        return 2
    return _run_checks(bandit, pip_audit, args, start)


def _run_checks(
    bandit: str, pip_audit: str, args: argparse.Namespace, start: float
) -> int:
    """Run the bandit, pip-audit, and optional detect-secrets checks.

    Args:
        bandit: Absolute path to the bandit executable.
        pip_audit: Absolute path to the pip-audit executable.
        args: Parsed gate arguments.
        start: Monotonic timestamp of gate start.

    Returns:
        0 on success, 1 on findings.
    """
    sec_start = time.monotonic()
    if not _run_bandit(bandit, verbose=args.verbose):
        return 1
    if not _run_pip_audit(pip_audit, verbose=args.verbose):
        return 1
    if args.full:
        _run_detect_secrets(verbose=args.verbose)
    print("✓ Security checks passed")
    if args.verbose:
        print(
            f"Security check execution time: "
            f"{common.elapsed_seconds(sec_start)} seconds"
        )
        print(f"Total execution time: {common.elapsed_seconds(start)} seconds")
    return 0
