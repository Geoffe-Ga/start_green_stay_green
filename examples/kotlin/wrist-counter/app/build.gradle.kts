// Android application module for the Wear OS app.
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlinx.kover")
}

android {
    namespace = "com.example.wrist_counter"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.wrist_counter"
        // Wear OS 3 (Galaxy Watch 4+) baseline.
        minSdk = 30
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    buildFeatures {
        compose = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    jvmToolchain(17)
}

// Coverage gate: scripts/test.sh --coverage runs koverVerifyDebug, which
// fails the build when debug-variant line coverage drops below 90%. This
// block is the single source of truth for the bound.
kover {
    reports {
        variant("debug") {
            verify {
                rule {
                    minBound(90)
                }
            }
        }
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2024.10.01"))
    implementation("androidx.activity:activity-compose:1.9.3")

    // Jetpack Compose for Wear OS (androidx.wear.compose).
    implementation("androidx.wear.compose:compose-material:1.4.0")
    implementation("androidx.wear.compose:compose-foundation:1.4.0")

    // JUnit scaffold for the unit tests (run: ./gradlew test).
    testImplementation("junit:junit:4.13.2")

    // Konsist backs the generated architecture test: copy
    // plans/architecture/ArchitectureTest.kt into app/src/test/kotlin/
    // and it compiles with no further dependency edits.
    testImplementation("com.lemonappdev:konsist:0.17.3")
}
