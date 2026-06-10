"""C/C++ (Tizen) naming helpers and toolchain versions for the watch scaffold.

Provides a single source of truth for the Tizen application ID and the C++
namespace derived from a project's package name, shared by the structure,
dependencies, and tests generators so the ``tizen-manifest.xml`` app ID, the
CMake project name, the C++ ``namespace`` declarations, and the generated
test includes can never drift apart. The pinned toolchain versions used
across the generated CMake/Conan manifests live here for the same reason.

The scaffold deliberately does NOT generate any ``.tpk`` packaging artifacts
or icon binaries: ``.tpk`` packaging requires the Tizen Studio CLI (which
cannot be generated or installed by a text generator) and icons are binary
artifacts. Generated projects document both gaps instead, mirroring the
Gradle-wrapper (#356) and Bun precedents.
"""

from __future__ import annotations

import re

# Pinned toolchain versions for the generated CMake/Conan manifests.
# CMake 3.20 is a pragmatic minimum: it predates every current LTS distro's
# packaged CMake, fully supports C++17, and provides the modern
# find_package/CMakeToolchain flow Conan 2 generates for. Catch2 v3 ships
# the Catch2WithMain link target and catch_discover_tests CMake helper, so
# the unit-test scaffold needs no hand-written main() — and unlike
# GoogleTest it is a single Conan package (no separate gmock).
CMAKE_MINIMUM_VERSION = "3.20"
CPP_STANDARD = "17"
CATCH2_VERSION = "3.8.0"
# Tizen 5.5 is the last wearable Tizen release with native watch-app
# support (Galaxy Watch / Galaxy Watch 3 / Watch Active2); later Samsung
# watches run Wear OS, which the Kotlin scaffold (#356) targets.
TIZEN_API_VERSION = "5.5"

# Characters invalid in a conservative Tizen app-ID segment. Tizen app IDs
# are reverse-DNS strings; alphanumeric-only segments are accepted by every
# Tizen Studio validation path, so anything else is dropped outright.
_INVALID_APP_ID_CHARS = re.compile(r"[^a-z0-9]")

# Characters invalid in a lowercase C++ identifier segment.
_INVALID_IDENTIFIER_CHARS = re.compile(r"[^a-z0-9_]")

# C++ keywords (through C++20, plus the alternative operator tokens) that
# cannot be used as an identifier, e.g. for the generated namespace.
_CPP_KEYWORDS = frozenset(
    {
        "alignas",
        "alignof",
        "and",
        "and_eq",
        "asm",
        "auto",
        "bitand",
        "bitor",
        "bool",
        "break",
        "case",
        "catch",
        "char",
        "char8_t",
        "char16_t",
        "char32_t",
        "class",
        "compl",
        "concept",
        "const",
        "consteval",
        "constexpr",
        "constinit",
        "const_cast",
        "continue",
        "co_await",
        "co_return",
        "co_yield",
        "decltype",
        "default",
        "delete",
        "do",
        "double",
        "dynamic_cast",
        "else",
        "enum",
        "explicit",
        "export",
        "extern",
        "false",
        "float",
        "for",
        "friend",
        "goto",
        "if",
        "inline",
        "int",
        "long",
        "mutable",
        "namespace",
        "new",
        "noexcept",
        "not",
        "not_eq",
        "nullptr",
        "operator",
        "or",
        "or_eq",
        "private",
        "protected",
        "public",
        "register",
        "reinterpret_cast",
        "requires",
        "return",
        "short",
        "signed",
        "sizeof",
        "static",
        "static_assert",
        "static_cast",
        "struct",
        "switch",
        "template",
        "this",
        "thread_local",
        "throw",
        "true",
        "try",
        "typedef",
        "typeid",
        "typename",
        "union",
        "unsigned",
        "using",
        "virtual",
        "void",
        "volatile",
        "wchar_t",
        "while",
        "xor",
        "xor_eq",
    }
)


def tizen_app_id(package_name: str) -> str:
    """Derive a valid Tizen application ID from a package name.

    The result lives under the conventional ``org.example`` placeholder
    namespace (users typically change the ID before publishing). The final
    segment is sanitized conservatively to lowercase alphanumerics — Tizen
    app IDs are reverse-DNS strings and alphanumeric-only segments pass
    every Tizen Studio validation path — and prefixed with ``app`` when it
    would start with a digit. A name with no usable characters falls back
    to ``app``.

    Args:
        package_name: The project's package identifier (e.g.
            ``watch_timer`` or ``watch-timer``).

    Returns:
        A dotted Tizen application ID such as ``org.example.watchtimer``.
    """
    segment = _INVALID_APP_ID_CHARS.sub("", package_name.lower())
    if not segment:
        segment = "app"
    elif segment[0].isdigit():
        segment = f"app{segment}"
    return f"org.example.{segment}"


def cpp_identifier(package_name: str) -> str:
    """Derive a valid lowercase C++ identifier from a package name.

    Used for the generated C++ ``namespace``, the CMake project name, and
    the native ``exec`` name in ``tizen-manifest.xml``. The name is
    lowercased, hyphens and other invalid characters are replaced with
    underscores, and the result is prefixed with ``app_`` when it would
    start with a digit or collide with a C++ keyword. A name with no
    usable characters falls back to ``app``.

    Args:
        package_name: The project's package identifier (e.g.
            ``watch_timer`` or ``watch-timer``).

    Returns:
        A valid C++ identifier such as ``watch_timer``.
    """
    identifier = _INVALID_IDENTIFIER_CHARS.sub(
        "_", package_name.lower().replace("-", "_")
    )
    if not identifier or identifier.strip("_") == "":
        identifier = "app"
    elif identifier[0].isdigit() or identifier in _CPP_KEYWORDS:
        identifier = f"app_{identifier}"
    return identifier
