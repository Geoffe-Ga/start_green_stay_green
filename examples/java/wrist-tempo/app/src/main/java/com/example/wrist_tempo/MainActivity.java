package com.example.wrist_tempo;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;

/**
 * Wear OS entry point for wrist-tempo (legacy Android Wear).
 *
 * <p>Renders res/layout/activity_main.xml, whose root is an
 * androidx.wear.widget.BoxInsetLayout — the maintained view-based
 * layout for round watch faces (WearableActivity is deprecated).</p>
 *
 * <p>THE TWO BUILDS: this file needs the Android SDK and the
 * androidx.wear AAR, so it is built with Android tooling
 * (Android Studio / Gradle) — NOT by the Maven build, which covers
 * only the pure logic in src/main/java/. When assembling the Android
 * build, add src/main/java/ as a source root so this activity can
 * resolve {@link Greeting}. See the README section "The two builds".</p>
 */
public class MainActivity extends Activity {

    @Override
    protected void onCreate(final Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        final TextView greetingView = findViewById(R.id.greeting);
        greetingView.setText(Greeting.greet("wrist-tempo"));
    }
}
