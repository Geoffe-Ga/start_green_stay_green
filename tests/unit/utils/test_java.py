"""Unit tests for the shared Java/Android naming helpers.

The Android package sanitization rules are Java's package rules, so the
canonical implementation lives in ``utils/java.py`` (#366) and is shared
by the Java and Kotlin Wear OS scaffolds. These tests moved here from
``test_kotlin.py`` together with the implementation.
"""

from __future__ import annotations

import pytest

from start_green_stay_green.utils import java
from start_green_stay_green.utils.java import android_package
from start_green_stay_green.utils.java import android_package_path

# Every Java keyword/literal that must trigger the ``app_`` prefix.
_ALL_JAVA_KEYWORDS = (
    "abstract",
    "assert",
    "boolean",
    "break",
    "byte",
    "case",
    "catch",
    "char",
    "class",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "extends",
    "false",
    "final",
    "finally",
    "float",
    "for",
    "goto",
    "if",
    "implements",
    "import",
    "instanceof",
    "int",
    "interface",
    "long",
    "native",
    "new",
    "null",
    "package",
    "private",
    "protected",
    "public",
    "return",
    "short",
    "static",
    "strictfp",
    "super",
    "switch",
    "synchronized",
    "this",
    "throw",
    "throws",
    "transient",
    "true",
    "try",
    "void",
    "volatile",
    "while",
)


class TestToolchainVersions:
    """Pinned Maven toolchain version constants are exact (#366)."""

    def test_junit4_version(self) -> None:
        """JUnit 4 version matches the Android ecosystem convention."""
        assert java.JUNIT4_VERSION == "4.13.2"

    def test_maven_compiler_plugin_version(self) -> None:
        """Maven compiler plugin version is pinned exactly."""
        assert java.MAVEN_COMPILER_PLUGIN_VERSION == "3.13.0"

    def test_surefire_version(self) -> None:
        """Surefire version is pinned exactly."""
        assert java.SUREFIRE_VERSION == "3.5.2"

    def test_jacoco_version(self) -> None:
        """JaCoCo version is pinned exactly."""
        assert java.JACOCO_VERSION == "0.8.12"

    def test_checkstyle_plugin_version(self) -> None:
        """Checkstyle plugin version is pinned exactly."""
        assert java.CHECKSTYLE_PLUGIN_VERSION == "3.6.0"

    def test_pmd_plugin_version(self) -> None:
        """PMD plugin version is pinned exactly."""
        assert java.PMD_PLUGIN_VERSION == "3.26.0"

    def test_spotbugs_plugin_version(self) -> None:
        """SpotBugs plugin version is pinned exactly."""
        assert java.SPOTBUGS_PLUGIN_VERSION == "4.8.6.6"

    def test_archunit_version(self) -> None:
        """ArchUnit version is pinned exactly (#367)."""
        assert java.ARCHUNIT_VERSION == "1.4.1"

    def test_dependency_check_plugin_version(self) -> None:
        """OWASP dependency-check plugin version is pinned exactly (#367)."""
        assert java.DEPENDENCY_CHECK_PLUGIN_VERSION == "12.1.3"

    def test_java_release(self) -> None:
        """Java release target is pinned exactly."""
        assert java.JAVA_RELEASE == "17"

    def test_androidx_wear_version(self) -> None:
        """androidx.wear version is pinned exactly."""
        assert java.ANDROIDX_WEAR_VERSION == "1.3.0"


class TestJavaKeywords:
    """The keyword set drives the ``app_`` prefix in :func:`android_package`."""

    def test_keyword_set_is_exact(self) -> None:
        """The frozenset contains exactly the Java keywords and literals."""
        assert set(java._JAVA_KEYWORDS) == set(_ALL_JAVA_KEYWORDS)


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

    @pytest.mark.parametrize("keyword", _ALL_JAVA_KEYWORDS)
    def test_java_keyword_gets_app_prefix(self, keyword: str) -> None:
        """Java keywords are invalid package segments; ``app_`` is prefixed."""
        assert android_package(keyword) == f"com.example.app_{keyword}"

    def test_non_keyword_is_not_prefixed(self) -> None:
        """Ordinary names pass through without the ``app_`` prefix."""
        assert android_package("classy") == "com.example.classy"


class TestAndroidPackagePath:
    """Tests for :func:`android_package_path`."""

    def test_returns_slash_separated_source_path(self) -> None:
        """The path form swaps dots for slashes (Java source layout)."""
        assert android_package_path("wrist_timer") == "com/example/wrist_timer"

    def test_matches_android_package_segments(self) -> None:
        """The path is exactly the package with dots replaced by slashes."""
        package = android_package("my-cool-app")
        assert android_package_path("my-cool-app") == package.replace(".", "/")
