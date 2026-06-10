"""Kotlin/Android naming helpers and toolchain versions for the Wear OS scaffold.

Provides a single source of truth for the Android namespace derived from a
project's package name, shared by the structure, dependencies, and tests
generators so the Kotlin source ``package`` declarations, the Gradle
``namespace``/``applicationId``, and the on-disk source paths can never
drift apart. The pinned toolchain versions used across the generated Gradle
manifests live here for the same reason.

The scaffold deliberately does NOT generate the Gradle wrapper (``gradlew``,
``gradle/wrapper/gradle-wrapper.jar``): the wrapper jar is a binary artifact
and binary artifacts do not belong in text generators. Generated projects
document running ``gradle wrapper --gradle-version <version>`` once instead.
"""

from __future__ import annotations

import re

# Pinned toolchain versions for the generated Gradle (Kotlin DSL) manifests.
# Chosen as a mutually-compatible stable set: AGP 8.7 requires Gradle 8.9+,
# and the Compose compiler Gradle plugin version tracks the Kotlin version.
AGP_VERSION = "8.7.3"
KOTLIN_VERSION = "2.0.21"
COMPOSE_BOM_VERSION = "2024.10.01"
WEAR_COMPOSE_VERSION = "1.4.0"
ACTIVITY_COMPOSE_VERSION = "1.9.3"
JUNIT_VERSION = "4.13.2"
GRADLE_WRAPPER_VERSION = "8.9"
# Quality-tooling versions (#357). Kover is the Kotlin-native coverage
# plugin (JetBrains); Konsist powers the generated architecture test
# (plans/architecture/ArchitectureTest.kt).
KOVER_VERSION = "0.9.8"
KONSIST_VERSION = "0.17.3"

# Characters invalid in a lowercase Java/Kotlin package segment.
_INVALID_SEGMENT_CHARS = re.compile(r"[^a-z0-9_]")

# Java language keywords (plus literals) that cannot be used as a package
# segment. Kotlin packages compile to Java packages, so the Java rules apply.
_JAVA_KEYWORDS = frozenset(
    {
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
    }
)


def android_package(package_name: str) -> str:
    """Derive a valid Android package/namespace from a package name.

    The result lives under the conventional ``com.example`` placeholder
    namespace (users typically change the ``applicationId`` before
    publishing). The final segment is sanitized to a valid Java package
    segment: lowercased, hyphens and other invalid characters replaced
    with underscores, and prefixed with ``app_`` when it would start with
    a digit or collide with a Java keyword. A name with no usable
    characters falls back to ``app``.

    Args:
        package_name: The project's package identifier (e.g.
            ``wrist_timer`` or ``wrist-timer``).

    Returns:
        A dotted Android package such as ``com.example.wrist_timer``.
    """
    segment = _INVALID_SEGMENT_CHARS.sub("_", package_name.lower().replace("-", "_"))
    if not segment:
        segment = "app"
    elif segment[0].isdigit() or segment in _JAVA_KEYWORDS:
        segment = f"app_{segment}"
    return f"com.example.{segment}"


def android_package_path(package_name: str) -> str:
    """Return the Kotlin source-directory path for the Android package.

    Args:
        package_name: The project's package identifier.

    Returns:
        The slash-separated form of :func:`android_package`, e.g.
        ``com/example/wrist_timer``, for building
        ``app/src/{main,test}/kotlin/`` paths.
    """
    return android_package(package_name).replace(".", "/")
