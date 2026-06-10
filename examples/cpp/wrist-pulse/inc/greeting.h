// Pure greeting logic for wrist-pulse: no Tizen
// dependencies, so the unit tests build with plain CMake + Conan.
#pragma once

#include <string>

namespace wrist_pulse {

// Returns the greeting assembled from the project name.
std::string format_greeting(const std::string &project_name);

}  // namespace wrist_pulse
