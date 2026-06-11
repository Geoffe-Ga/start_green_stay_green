package com.example.wrist_counter

import org.junit.Assert.assertEquals
import org.junit.Test

/** Verifies the greeting interpolation logic in MainActivity.kt. */
class GreetingTest {
    @Test
    fun greetingIsAssembledFromProjectName() {
        // greeting() interpolates its argument, so this verifies real
        // logic rather than comparing two identical literals.
        assertEquals("Hello from wrist-counter!", greeting("wrist-counter"))
    }

    @Test
    fun greetingReflectsAnArbitraryName() {
        assertEquals("Hello from wear!", greeting("wear"))
    }
}
