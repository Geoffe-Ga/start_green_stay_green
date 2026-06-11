#include "greeting.h"

namespace wrist_pulse {

std::string format_greeting(const std::string &project_name) {
    return "Hello from " + project_name + "!";
}

}  // namespace wrist_pulse
