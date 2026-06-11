# CMake build for the wrist-pulse Tizen watch app.
#
# Scope: ONLY the pure-logic library and its Catch2 unit tests. The Tizen
# watch-app entry point (src/main.cpp) needs the Tizen native SDK headers
# and the .tpk package is produced by the Tizen Studio CLI
# (tizen build-native / tizen package), which cannot be generated or
# installed by this scaffold — see the README. This split keeps the unit
# tests buildable on any host with CMake + Conan, no Tizen Studio needed:
#
#   conan install . --output-folder=build --build=missing
#   cmake -B build -S . \
#       -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake \
#       -DCMAKE_BUILD_TYPE=Release
#   cmake --build build
#   ctest --test-dir build
cmake_minimum_required(VERSION 3.20)
project(wrist_pulse VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export build/compile_commands.json for clang-tidy: scripts/lint.sh and
# the pre-commit clang-tidy hook both read it (-p build).
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Coverage instrumentation for scripts/test.sh --coverage (the >=90%
# line-coverage gate lives in that script). OFF by default so plain
# builds stay uninstrumented.
option(ENABLE_COVERAGE "Instrument the build for gcov/lcov coverage" OFF)

# Pure greeting logic: no Tizen dependencies (src/greeting.cpp + inc/).
# Renaming the source file requires updating both 'greeting' references
# below (and the target_link_libraries in the test target).
add_library(greeting src/greeting.cpp)
target_include_directories(greeting PUBLIC inc)

if(ENABLE_COVERAGE)
    # --coverage = -fprofile-arcs -ftest-coverage on both gcc and clang.
    # PUBLIC so consumers (greeting_tests) also compile and link with the
    # gcov runtime; .gcda data then lands under build/ for lcov.
    target_compile_options(greeting PUBLIC --coverage -O0 -g)
    target_link_options(greeting PUBLIC --coverage)
endif()

# Catch2 unit tests (dependency managed by Conan, see conanfile.txt).
include(CTest)
if(BUILD_TESTING)
    find_package(Catch2 3 REQUIRED)
    add_executable(greeting_tests tests/test_greeting.cpp)
    target_link_libraries(greeting_tests PRIVATE greeting Catch2::Catch2WithMain)
    include(Catch)
    catch_discover_tests(greeting_tests)
endif()
