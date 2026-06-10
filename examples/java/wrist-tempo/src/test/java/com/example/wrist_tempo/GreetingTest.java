package com.example.wrist_tempo;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

/**
 * Verifies the greeting assembly logic in {@link Greeting}.
 *
 * <p>Plain JVM JUnit 4 run by Maven Surefire ({@code mvn test}) -
 * no Android SDK, emulator, or Robolectric needed.</p>
 */
public class GreetingTest {

    @Test
    public void greetingIsAssembledFromProjectName() {
        // Greeting.greet() concatenates its argument, so this verifies
        // real logic rather than comparing two identical literals.
        assertEquals(
                "Hello from wrist-tempo!",
                Greeting.greet("wrist-tempo"));
    }

    @Test
    public void greetingReflectsAnArbitraryName() {
        assertEquals("Hello from wear!", Greeting.greet("wear"));
    }
}
