// Gradle (Kotlin DSL) settings for the wrist-counter Wear OS project.
//
// NOTE: the Gradle wrapper (gradlew, gradle/wrapper/gradle-wrapper.jar)
// is NOT generated — binary artifacts do not belong in a generator.
// With a local Gradle install, create it once via:
//   gradle wrapper --gradle-version 8.9
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "wrist-counter"
include(":app")
