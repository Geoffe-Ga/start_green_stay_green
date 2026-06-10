import SwiftUI

// watchOS entry point: shows "Hello from wrist-timer!"
// @main only applies on watchOS: the macOS host build that `swift test`
// performs links SwiftPM's test runner executable, and a second entry
// point would collide with the runner's own `main` symbol.
#if os(watchOS)
@main
#endif
struct WristTimerApp: App {
    @SceneBuilder var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
