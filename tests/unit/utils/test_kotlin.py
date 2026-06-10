"""Unit tests for the shared Kotlin/Android naming helpers."""

from __future__ import annotations

import pytest

from start_green_stay_green.utils.kotlin import android_package
from start_green_stay_green.utils.kotlin import android_package_path


class TestAndroidPackage:
    """Tests for :func:`android_package`."""

    def test_uses_com_example_placeholder_namespace(self) -> None:
        """Package names live under the conventional com.example prefix."""
        assert android_package("wrist_timer") == "com.example.wrist_timer"

    def test_hyphen_is_replaced_with_underscore(self) -> None:
        """Hyphens are invalid in Java package segments and are replaced."""
        assert android_package("wrist-timer") == "com.example.wrist_timer"

    def test_uppercase_is_lowered(self) -> None:
        """Android package segments are conventionally lowercase."""
        assert android_package("WristTimer") == "com.example.wristtimer"

    def test_invalid_characters_become_underscores(self) -> None:
        """Characters outside [a-z0-9_] are replaced with underscores."""
        assert android_package("wrist.timer!") == "com.example.wrist_timer_"

    def test_leading_digit_gets_app_prefix(self) -> None:
        """Java identifiers cannot start with a digit; ``app_`` is prefixed."""
        assert android_package("4ever") == "com.example.app_4ever"

    def test_empty_name_gets_app_fallback(self) -> None:
        """An empty or fully-invalid name falls back to ``app``."""
        assert android_package("") == "com.example.app"

    @pytest.mark.parametrize("keyword", ["new", "class", "package", "default"])
    def test_java_keyword_gets_app_prefix(self, keyword: str) -> None:
        """Java keywords are invalid package segments; ``app_`` is prefixed."""
        assert android_package(keyword) == f"com.example.app_{keyword}"

    def test_non_keyword_is_not_prefixed(self) -> None:
        """Ordinary names pass through without the ``app_`` prefix."""
        assert android_package("classy") == "com.example.classy"


class TestAndroidPackagePath:
    """Tests for :func:`android_package_path`."""

    def test_returns_slash_separated_source_path(self) -> None:
        """The path form swaps dots for slashes (Kotlin source layout)."""
        assert android_package_path("wrist_timer") == "com/example/wrist_timer"

    def test_matches_android_package_segments(self) -> None:
        """The path is exactly the package with dots replaced by slashes."""
        package = android_package("my-cool-app")
        assert android_package_path("my-cool-app") == package.replace(".", "/")
