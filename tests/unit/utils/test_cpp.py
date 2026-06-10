"""Unit tests for the shared C/C++ (Tizen) naming helpers."""

from __future__ import annotations

import pytest

from start_green_stay_green.utils.cpp import CATCH2_VERSION
from start_green_stay_green.utils.cpp import CMAKE_MINIMUM_VERSION
from start_green_stay_green.utils.cpp import CPP_STANDARD
from start_green_stay_green.utils.cpp import TIZEN_API_VERSION
from start_green_stay_green.utils.cpp import cpp_identifier
from start_green_stay_green.utils.cpp import tizen_app_id


class TestTizenAppId:
    """Tests for :func:`tizen_app_id`."""

    def test_uses_org_example_placeholder_namespace(self) -> None:
        """App IDs live under the conventional org.example prefix."""
        assert tizen_app_id("watchtimer") == "org.example.watchtimer"

    def test_hyphen_is_dropped(self) -> None:
        """Hyphens are stripped: Tizen app-ID segments stay alphanumeric."""
        assert tizen_app_id("watch-timer") == "org.example.watchtimer"

    def test_underscore_is_dropped(self) -> None:
        """Underscores are stripped (conservative Tizen app-ID charset)."""
        assert tizen_app_id("watch_timer") == "org.example.watchtimer"

    def test_uppercase_is_lowered(self) -> None:
        """App-ID segments are conventionally lowercase."""
        assert tizen_app_id("WatchTimer") == "org.example.watchtimer"

    def test_invalid_characters_are_dropped(self) -> None:
        """Characters outside [a-z0-9] are removed, not replaced."""
        assert tizen_app_id("watch.timer!") == "org.example.watchtimer"

    def test_leading_digit_gets_app_prefix(self) -> None:
        """A digit-leading segment is prefixed with ``app`` for safety."""
        assert tizen_app_id("4ever") == "org.example.app4ever"

    def test_empty_name_gets_app_fallback(self) -> None:
        """An empty or fully-invalid name falls back to ``app``."""
        assert tizen_app_id("") == "org.example.app"

    def test_fully_invalid_name_gets_app_fallback(self) -> None:
        """A name with no usable characters falls back to ``app``."""
        assert tizen_app_id("___") == "org.example.app"


class TestCppIdentifier:
    """Tests for :func:`cpp_identifier`."""

    def test_passes_through_a_valid_identifier(self) -> None:
        """Ordinary snake_case names pass through unchanged."""
        assert cpp_identifier("watch_timer") == "watch_timer"

    def test_hyphen_becomes_underscore(self) -> None:
        """Hyphens are invalid in C++ identifiers and become underscores."""
        assert cpp_identifier("watch-timer") == "watch_timer"

    def test_uppercase_is_lowered(self) -> None:
        """Identifiers are lowercased for a consistent namespace style."""
        assert cpp_identifier("WatchTimer") == "watchtimer"

    def test_invalid_characters_become_underscores(self) -> None:
        """Characters outside [a-z0-9_] are replaced with underscores."""
        assert cpp_identifier("watch.timer!") == "watch_timer_"

    def test_leading_digit_gets_app_prefix(self) -> None:
        """C++ identifiers cannot start with a digit; ``app_`` is prefixed."""
        assert cpp_identifier("4ever") == "app_4ever"

    def test_empty_name_gets_app_fallback(self) -> None:
        """An empty or fully-invalid name falls back to ``app``."""
        assert cpp_identifier("") == "app"

    @pytest.mark.parametrize("keyword", ["new", "class", "default", "int", "namespace"])
    def test_cpp_keyword_gets_app_prefix(self, keyword: str) -> None:
        """C++ keywords are invalid identifiers; ``app_`` is prefixed."""
        assert cpp_identifier(keyword) == f"app_{keyword}"

    def test_non_keyword_is_not_prefixed(self) -> None:
        """Ordinary names pass through without the ``app_`` prefix."""
        assert cpp_identifier("classy") == "classy"


class TestPinnedVersions:
    """The pinned toolchain versions are the single source of truth."""

    def test_cmake_minimum_is_pinned(self) -> None:
        """CMake minimum supports C++17 and modern find_package flows."""
        assert CMAKE_MINIMUM_VERSION == "3.20"

    def test_cpp_standard_is_17(self) -> None:
        """The scaffold targets C++17 (Tizen Studio's GCC supports it)."""
        assert CPP_STANDARD == "17"

    def test_catch2_version_is_pinned(self) -> None:
        """Catch2 v3 is pinned for the Conan-managed test framework."""
        assert CATCH2_VERSION == "3.8.0"

    def test_tizen_api_version_is_pinned(self) -> None:
        """Tizen 5.5 is the last wearable Tizen with native watch apps."""
        assert TIZEN_API_VERSION == "5.5"
