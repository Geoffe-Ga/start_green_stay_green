"""Kotlin/Android toolchain versions for the Wear OS scaffold.

Holds the pinned toolchain versions used across the generated Gradle
(Kotlin DSL) manifests, so the structure, dependencies, and tests
generators share one source of truth.

The Android package/namespace naming helpers
(:func:`~start_green_stay_green.utils.java.android_package` and
:func:`~start_green_stay_green.utils.java.android_package_path`) live in
``utils/java.py``: the sanitization rules are Java's package rules
(Kotlin packages compile to Java packages), and the Java Wear OS
scaffold (#366) shares them.

The scaffold deliberately does NOT generate the Gradle wrapper (``gradlew``,
``gradle/wrapper/gradle-wrapper.jar``): the wrapper jar is a binary artifact
and binary artifacts do not belong in text generators. Generated projects
document running ``gradle wrapper --gradle-version <version>`` once instead.
"""

from __future__ import annotations

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
