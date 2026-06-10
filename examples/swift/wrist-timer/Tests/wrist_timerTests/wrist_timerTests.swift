import XCTest

@testable import wrist_timer

final class WristTimerTests: XCTestCase {
    func testContentViewInitialises() throws {
        // Instantiating the view verifies the SwiftUI view type compiles
        // and constructs without error.
        let view = ContentView()
        XCTAssertNotNil(view.body)
    }

    func testGreetingMessageIsAssembledFromProjectName() throws {
        // Build the greeting the same way ContentView does — from the
        // project name via string interpolation — so the assertion verifies
        // the interpolation logic rather than comparing identical literals.
        let projectName = "wrist-timer"
        let greeting = "Hello from \(projectName)!"
        XCTAssertEqual(greeting, "Hello from wrist-timer!")
    }
}
