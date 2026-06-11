// Root Gradle build: pins plugin versions for all modules.
// The Compose compiler plugin version must match the Kotlin version.
plugins {
    id("com.android.application") version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
    // Kover: Kotlin-native code coverage (run: scripts/test.sh --coverage).
    id("org.jetbrains.kotlinx.kover") version "0.9.8" apply false
}
