"""Tests for the C# naming helper and NuGet version pins (#370).

The :func:`csharp_namespace` helper is the single source of truth for
the PascalCase root namespace shared by the structure, tests,
dependencies, and architecture generators, so the scaffolded sources,
the xUnit tests, and the NetArchTest template can never drift apart.
"""

from __future__ import annotations

import pytest

from start_green_stay_green.utils import csharp


class TestCsharpNamespace:
    """Tests for csharp_namespace sanitization rules."""

    @pytest.mark.parametrize(
        ("package_name", "expected"),
        [
            ("wrist_ledger", "WristLedger"),
            ("test_project", "TestProject"),
            ("myapp", "Myapp"),
            ("my-app", "MyApp"),
            ("My_App", "MyApp"),
        ],
    )
    def test_pascal_case_namespace(self, package_name: str, expected: str) -> None:
        """Snake/kebab-case package names become PascalCase namespaces."""
        assert csharp.csharp_namespace(package_name) == expected

    def test_leading_digit_gets_app_prefix(self) -> None:
        """A namespace cannot start with a digit (C# identifier rules)."""
        result = csharp.csharp_namespace("2048_game")
        assert not result[0].isdigit()
        assert result == "App2048Game"

    def test_empty_input_falls_back_to_app(self) -> None:
        """A name with no usable characters falls back to ``App``."""
        assert csharp.csharp_namespace("---") == "App"

    def test_invalid_characters_are_dropped(self) -> None:
        """Characters invalid in a C# identifier are treated as separators."""
        result = csharp.csharp_namespace("my.app!name")
        assert result == "MyAppName"


class TestNuGetVersionPins:
    """The pinned NuGet versions exist and follow SemVer-ish shapes."""

    @pytest.mark.parametrize(
        "constant",
        [
            "XUNIT_VERSION",
            "XUNIT_RUNNER_VERSION",
            "TEST_SDK_VERSION",
            "COVERLET_MSBUILD_VERSION",
            "NETARCHTEST_RULES_VERSION",
            "SECURITY_CODE_SCAN_VERSION",
        ],
    )
    def test_pin_is_a_dotted_version_string(self, constant: str) -> None:
        """Every pin is a non-empty dotted version string."""
        value = getattr(csharp, constant)
        assert isinstance(value, str)
        parts = value.split(".")
        assert len(parts) >= 2
        assert all(part.isdigit() for part in parts)

    def test_coverlet_msbuild_pin_matches_net8_line(self) -> None:
        """coverlet.msbuild stays on the 8.x line that matches net8.0.

        Verified live on nuget.org (2026-06): 8.0.1 is the newest 8.x
        release; the 10.x line tracks the .NET 10 SDK the scaffold does
        not target yet.
        """
        assert csharp.COVERLET_MSBUILD_VERSION == "8.0.1"

    def test_netarchtest_rules_pin_is_latest_stable(self) -> None:
        """NetArchTest.Rules pins the latest stable (live-verified)."""
        assert csharp.NETARCHTEST_RULES_VERSION == "1.3.2"

    def test_security_code_scan_pin_is_latest_stable(self) -> None:
        """SecurityCodeScan.VS2019 pins the latest stable (live-verified)."""
        assert csharp.SECURITY_CODE_SCAN_VERSION == "5.6.7"
