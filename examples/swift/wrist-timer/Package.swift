// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "WristTimer",
    platforms: [
        .watchOS(.v10),
        // macOS minimum for the host that `swift test` builds for; the
        // SwiftPM default (10.13) predates SwiftUI and fails to compile.
        .macOS(.v14)
    ],
    targets: [
        .target(name: "wrist_timer"),
        .testTarget(
            name: "wrist_timerTests",
            dependencies: ["wrist_timer"]
        )
    ]
)
