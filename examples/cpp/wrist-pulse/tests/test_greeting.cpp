// Catch2 tests for the pure greeting logic (src/greeting.cpp).
// Builds with plain CMake + Conan — no Tizen Studio required.
#include <catch2/catch_test_macros.hpp>

#include "greeting.h"

TEST_CASE("greeting is assembled from the project name", "[greeting]") {
    // format_greeting() assembles its argument into the message, so this
    // verifies real logic rather than comparing two identical literals.
    REQUIRE(wrist_pulse::format_greeting("wrist-pulse") ==
            "Hello from wrist-pulse!");
}

TEST_CASE("greeting reflects an arbitrary name", "[greeting]") {
    REQUIRE(wrist_pulse::format_greeting("tizen") == "Hello from tizen!");
}
