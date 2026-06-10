"""Java/Android naming helpers and Maven toolchain versions (#366).

Provides a single source of truth for the Android package derived from a
project's package name, shared by the Java and Kotlin Wear OS scaffolds:
the structure, dependencies, and tests generators all derive source
``package`` declarations, the manifest application ID, and the on-disk
source paths from :func:`android_package`, so they can never drift apart.
The Android package sanitization rules are Java's package rules (Kotlin
packages compile to Java packages), which is why the canonical
implementation lives here.

The pinned Maven toolchain versions for the generated Java ``pom.xml``
live here for the same reason. The pom deliberately covers only the
PURE-LOGIC half of the legacy Android Wear scaffold (``src/main/java`` +
``src/test/java``): the watch-app module under ``app/`` needs the Android
SDK and the androidx.wear AAR, which plain Maven cannot consume (the
android-maven-plugin is unmaintained), so the APK build belongs to
Android tooling (Android Studio / Gradle) that the generator does not
scaffold — the same two-builds split as the C/C++ Tizen scaffold (#361).
"""

from __future__ import annotations

import re

# Pinned toolchain versions for the generated Maven (pom.xml) manifest.
# JUnit 4 (not 5) matches the Android ecosystem convention shared with
# the Kotlin Wear OS scaffold (#356).
JUNIT4_VERSION = "4.13.2"
MAVEN_COMPILER_PLUGIN_VERSION = "3.13.0"
SUREFIRE_VERSION = "3.5.2"
JACOCO_VERSION = "0.8.12"
CHECKSTYLE_PLUGIN_VERSION = "3.6.0"
PMD_PLUGIN_VERSION = "3.26.0"
SPOTBUGS_PLUGIN_VERSION = "4.8.6.6"
# ArchUnit backs the generated architecture test (#367); test-scoped in
# the pom so the plans/architecture template compiles once copied into
# src/test/java (the Konsist manifest-touch precedent from #357).
ARCHUNIT_VERSION = "1.4.1"
# OWASP dependency-check Maven plugin (#367); declared in the pom so
# `mvn dependency-check:check` resolves without the org.owasp group
# being in Maven's default plugin-prefix search path.
DEPENDENCY_CHECK_PLUGIN_VERSION = "12.1.3"
# Java release the pure-logic build targets; within the generated CI
# workflow's JDK matrix (reference/ci/java.yml runs 17 and 21).
JAVA_RELEASE = "17"
# androidx.wear (Wearable Support Library successor) for the legacy
# Android Wear app module. Referenced in documentation only: the AAR is
# consumed by the Android (Gradle) build, never by the pom.
ANDROIDX_WEAR_VERSION = "1.3.0"

# Characters invalid in a lowercase Java package segment.
_INVALID_SEGMENT_CHARS = re.compile(r"[^a-z0-9_]")

# Java language keywords (plus literals) that cannot be used as a package
# segment.
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
    namespace (users typically change the application ID before
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
    """Return the source-directory path for the Android package.

    Args:
        package_name: The project's package identifier.

    Returns:
        The slash-separated form of :func:`android_package`, e.g.
        ``com/example/wrist_timer``, for building Java
        (``src/{main,test}/java/``, ``app/src/main/java/``) and Kotlin
        (``app/src/{main,test}/kotlin/``) source paths.
    """
    return android_package(package_name).replace(".", "/")
