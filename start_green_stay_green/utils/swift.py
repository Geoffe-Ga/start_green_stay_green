"""Swift Package Manager manifest helpers.

Provides a single source of truth for the ``Package.swift`` manifest emitted
by the Swift scaffold so the structure and dependency generators cannot drift
apart. The scaffold targets a watchOS SwiftUI *application*, which is not a
distributable library, so the manifest deliberately omits a ``products:``
block (targets-only is the conventional shape for an app scaffold).
"""

from __future__ import annotations

from start_green_stay_green.utils.naming import pascal_case


def package_swift(package_name: str) -> str:
    """Render the ``Package.swift`` manifest for the watchOS app scaffold.

    Args:
        package_name: The snake/kebab package identifier used for the SPM
            target and test target names. The PascalCase form is derived for
            the package's display name.

    Returns:
        The full contents of a ``Package.swift`` manifest declaring a
        watchOS app target and its XCTest test target. No ``products:``
        block is emitted because an app target is not a distributable
        library. Alongside the watchOS deployment target the manifest
        declares ``.macOS(.v14)``: ``swift test`` builds the package for
        the macOS *host*, and without an explicit entry SwiftPM falls
        back to the macOS 10.13 default, which fails SwiftUI
        availability checks (SwiftUI needs 10.15+, the ``App`` protocol
        11+). The macOS minimum is what lets the generated CI and
        ``scripts/test.sh`` run ``swift test --enable-code-coverage``.
    """
    type_name = pascal_case(package_name)
    return f"""// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "{type_name}",
    platforms: [
        .watchOS(.v10),
        // macOS minimum for the host that `swift test` builds for; the
        // SwiftPM default (10.13) predates SwiftUI and fails to compile.
        .macOS(.v14)
    ],
    targets: [
        .target(name: "{package_name}"),
        .testTarget(
            name: "{package_name}Tests",
            dependencies: ["{package_name}"]
        )
    ]
)
"""
