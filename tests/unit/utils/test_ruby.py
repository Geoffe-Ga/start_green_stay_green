"""Tests for the Ruby naming helper, gem pins, and Gemfile source (#373).

The :func:`ruby_module_name` helper is the single source of truth for
the CamelCase module name shared by the structure and tests
generators, so the scaffolded ``module`` declaration and the constant
the RSpec scaffold describes can never drift apart. The
:func:`ruby_gemfile` helper is likewise the one home of the generated
Gemfile, shared by the structure and dependencies generators.
"""

from __future__ import annotations

import pytest

from start_green_stay_green.utils import ruby


class TestRubyModuleName:
    """Tests for ruby_module_name sanitization rules."""

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
    def test_camel_case_module_name(self, package_name: str, expected: str) -> None:
        """Snake/kebab-case package names become CamelCase module names."""
        assert ruby.ruby_module_name(package_name) == expected

    def test_leading_digit_gets_app_prefix(self) -> None:
        """A Ruby constant cannot start with a digit."""
        result = ruby.ruby_module_name("2048_game")
        assert not result[0].isdigit()
        assert result == "App2048Game"

    def test_empty_input_falls_back_to_app(self) -> None:
        """A name with no usable characters falls back to ``App``."""
        assert ruby.ruby_module_name("---") == "App"

    def test_invalid_characters_are_dropped(self) -> None:
        """Characters invalid in a Ruby constant are treated as separators."""
        assert ruby.ruby_module_name("my.app!name") == "MyAppName"


class TestGemVersionPins:
    """The pinned gem constraints exist and follow version shapes."""

    @pytest.mark.parametrize(
        "constant",
        [
            "RAKE_VERSION",
            "RSPEC_VERSION",
            "SIMPLECOV_VERSION",
            "RUBOCOP_VERSION",
            "BUNDLER_AUDIT_VERSION",
            "PACKWERK_VERSION",
        ],
    )
    def test_pin_is_a_dotted_version_string(self, constant: str) -> None:
        """Every pin is a non-empty dotted version string."""
        value = getattr(ruby, constant)
        assert isinstance(value, str)
        parts = value.split(".")
        assert len(parts) >= 2
        assert all(part.isdigit() for part in parts)

    def test_rubocop_pin_is_current_stable_line(self) -> None:
        """RuboCop pins the live-verified stable line (2026-06: 1.87.0)."""
        assert ruby.RUBOCOP_VERSION == "1.87"

    def test_rspec_pin_is_current_stable_line(self) -> None:
        """RSpec pins the live-verified stable line (2026-06: 3.13.2)."""
        assert ruby.RSPEC_VERSION == "3.13"

    def test_packwerk_pin_is_current_stable_line(self) -> None:
        """Packwerk pins the live-verified stable line (2026-06: 3.3.0)."""
        assert ruby.PACKWERK_VERSION == "3.3"


class TestRubyGemfile:
    """Tests for the canonical Gemfile content."""

    def test_gemfile_sources_rubygems(self) -> None:
        """The Gemfile pulls from rubygems.org with frozen literals."""
        content = ruby.ruby_gemfile()
        assert content.startswith("# frozen_string_literal: true")
        assert 'source "https://rubygems.org"' in content

    @pytest.mark.parametrize(
        ("gem_name", "version"),
        [
            ("rake", ruby.RAKE_VERSION),
            ("rspec", ruby.RSPEC_VERSION),
            ("simplecov", ruby.SIMPLECOV_VERSION),
            ("rubocop", ruby.RUBOCOP_VERSION),
            ("bundler-audit", ruby.BUNDLER_AUDIT_VERSION),
            ("packwerk", ruby.PACKWERK_VERSION),
        ],
    )
    def test_gemfile_pins_quality_toolchain(self, gem_name: str, version: str) -> None:
        """Every quality gem is declared with its pessimistic pin."""
        content = ruby.ruby_gemfile()
        assert f'gem "{gem_name}", "~> {version}"' in content

    def test_gemfile_excludes_rails_only_brakeman(self) -> None:
        """Brakeman is Rails-specific and must not break the scaffold.

        ``brakeman`` exits with an error when pointed at a non-Rails
        project, so wiring it into a plain-Ruby scaffold would emit a
        tool that can never pass; the Gemfile documents it as the
        add-on for when Rails is adopted instead.
        """
        content = ruby.ruby_gemfile()
        assert 'gem "brakeman"' not in content
        assert "Brakeman" in content

    def test_quality_gems_are_development_group_only(self) -> None:
        """Quality tooling lives in the development/test group."""
        content = ruby.ruby_gemfile()
        group_index = content.index("group :development, :test do")
        for gem_name in ("rspec", "rubocop", "simplecov", "bundler-audit"):
            assert content.index(f'gem "{gem_name}"') > group_index
