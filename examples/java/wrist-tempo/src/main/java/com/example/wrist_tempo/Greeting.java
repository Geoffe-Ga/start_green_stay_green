package com.example.wrist_tempo;

/**
 * Assembles the greeting shown on the watch face.
 *
 * <p>Pure logic with no Android imports: the Maven build (pom.xml)
 * compiles and unit-tests this class on any host without the Android
 * SDK. The Wear OS app module under app/ consumes it too — see the
 * README section "The two builds".</p>
 */
public final class Greeting {

    private Greeting() {
        // Static utility class: not instantiable.
    }

    /**
     * Returns the greeting assembled from the project name.
     *
     * @param projectName the name to greet from
     * @return the assembled greeting, e.g. {@code "Hello from wear!"}
     */
    public static String greet(final String projectName) {
        return "Hello from " + projectName + "!";
    }
}
