"""Ruby naming helpers and pinned gem versions (#373).

Provides a single source of truth for the CamelCase Ruby module name
derived from a project's package name, shared by the Ruby scaffold's
structure and tests generators: the ``module`` declaration in
``lib/{package_name}.rb`` and the constant the RSpec scaffold
describes both derive from :func:`ruby_module_name`, so they can
never drift apart (the ``utils.csharp.csharp_namespace`` precedent —
before #373 the spec described ``package_name.capitalize()`` while
the lib file declared a per-word-capitalized module, a guaranteed
``NameError`` in the generated project).

The pinned gem version constraints for the generated ``Gemfile`` live
here for the same reason (the ``utils.java`` / ``utils.csharp``
version-pin precedent), as does the canonical Gemfile content shared
by the structure and dependencies generators. All pins were verified
against the live rubygems.org API before being recorded.
"""

from __future__ import annotations

import re

from start_green_stay_green.utils.naming import pascal_case

# Pinned gem version constraints for the generated Gemfile (pessimistic
# ``~>`` bounds; live-verified latest stable on rubygems.org).
# rake backs the conventional default task runner.
RAKE_VERSION = "13.4"
# RSpec is the test framework; SimpleCov hooks into the suite and owns
# the >=90% coverage bound via spec/spec_helper.rb (#373).
RSPEC_VERSION = "3.13"
SIMPLECOV_VERSION = "0.22"
# RuboCop owns formatting (--autocorrect via scripts/format.sh), lint,
# the Metrics/CyclomaticComplexity <=10 gate, and the Security cops;
# .rubocop.yml is the single home of its policy (#373).
# Patch-precision pessimistic pin: pre-commit runs RuboCop from its own
# pinned environment (rev v1.87.0), so the Gemfile must not float to a
# newer minor and silently diverge from the hook.
RUBOCOP_VERSION = "1.87.0"
# bundler-audit owns dependency CVE scanning (scripts/security.sh).
BUNDLER_AUDIT_VERSION = "0.9"
# Packwerk backs the architecture boundary rules generated into
# plans/architecture (#373). It pulls in activesupport/zeitwerk as
# runtime dependencies; see plans/architecture/packwerk.yml for its
# enforcement limits on a plain-Ruby (non-Zeitwerk) scaffold.
PACKWERK_VERSION = "3.3"

# Characters that split a package name into module-name words.
_SEPARATORS = re.compile(r"[^a-zA-Z0-9]+")


def ruby_module_name(package_name: str) -> str:
    """Derive a valid CamelCase Ruby module name from a package name.

    Separator characters (hyphens, dots, anything not alphanumeric) are
    normalized to underscores and the result runs through the shared
    :func:`~start_green_stay_green.utils.naming.pascal_case` helper
    (``wrist_ledger`` -> ``WristLedger``). On top of that, Ruby's
    constant rules apply: a constant must start with an uppercase
    letter, so a name that would start with a digit gains an ``App``
    prefix, and a name with no usable characters falls back to ``App``.

    Args:
        package_name: The project's package identifier (e.g.
            ``wrist_ledger`` or ``wrist-ledger``).

    Returns:
        A CamelCase module name such as ``WristLedger``.
    """
    module_name = pascal_case(_SEPARATORS.sub("_", package_name))
    if not module_name:
        return "App"
    if module_name[0].isdigit():
        return f"App{module_name}"
    return module_name


def ruby_gemfile() -> str:
    """Return the canonical Gemfile for the generated Ruby scaffold.

    Shared by the structure and dependencies generators so the two
    emit an identical manifest from one source of truth (the
    ``utils.swift.package_swift`` precedent — before #373 they emitted
    two diverging Gemfiles).

    The development/test group wires the full #373 quality toolchain:
    RSpec + SimpleCov (coverage, bound in spec/spec_helper.rb), RuboCop
    (format/lint/complexity/security cops via .rubocop.yml),
    bundler-audit (dependency CVEs), and Packwerk (architecture
    boundaries; see plans/architecture). Brakeman is deliberately NOT
    included: it is a Rails-specific scanner that errors out on a
    plain-Ruby project — add it alongside Rails if the project adopts
    the framework.

    Returns:
        Content for the generated ``Gemfile``.
    """
    return f"""# frozen_string_literal: true

source "https://rubygems.org"

gem "rake", "~> {RAKE_VERSION}"

group :development, :test do
  # Test framework; SimpleCov hooks the suite and enforces the >=90%
  # coverage bound declared in spec/spec_helper.rb (its single home).
  gem "rspec", "~> {RSPEC_VERSION}"
  gem "simplecov", "~> {SIMPLECOV_VERSION}", require: false

  # Formatter, linter, complexity (<=10 via Metrics cops), and
  # source-level security cops in one tool; .rubocop.yml is the single
  # home of the policy shared by pre-commit, scripts, and CI.
  gem "rubocop", "~> {RUBOCOP_VERSION}", require: false

  # Dependency CVE scanning against the ruby-advisory-db
  # (scripts/security.sh). Brakeman is deliberately absent: it is a
  # Rails-specific scanner that errors on plain-Ruby projects — add it
  # here together with Rails if the project adopts the framework.
  gem "bundler-audit", "~> {BUNDLER_AUDIT_VERSION}", require: false

  # Architecture boundary enforcement (plans/architecture). Packwerk
  # targets Zeitwerk-style autoloaded codebases; see the generated
  # packwerk.yml for its enforcement limits on this plain-Ruby layout.
  gem "packwerk", "~> {PACKWERK_VERSION}", require: false
end
"""
