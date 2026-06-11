"""Unit tests for the shared Swift Package.swift manifest helper."""

from __future__ import annotations

from start_green_stay_green.utils.swift import package_swift


class TestPackageSwift:
    """Tests for :func:`package_swift`."""

    def test_renders_spm_manifest_header(self) -> None:
        """Manifest declares the SPM tools version and PackageDescription."""
        content = package_swift("test_project")
        assert content.startswith("// swift-tools-version:5.9")
        assert "import PackageDescription" in content

    def test_uses_pascal_case_package_name(self) -> None:
        """Package name is the PascalCase form of the identifier."""
        content = package_swift("my-cool-app")
        assert 'name: "MyCoolApp"' in content

    def test_targets_watchos_platform(self) -> None:
        """Scaffold targets the watchOS platform."""
        content = package_swift("test_project")
        assert ".watchOS(.v10)" in content

    def test_declares_macos_minimum_for_test_host(self) -> None:
        """Manifest declares a macOS minimum so `swift test` can compile.

        `swift test` builds the package for the macOS host. Without an
        explicit macOS platform entry SwiftPM falls back to the 10.13
        default, and the SwiftUI scaffold fails availability checks
        (SwiftUI needs 10.15+, the App protocol 11+). Verified
        empirically for Issue #353: the CI coverage gate can only pass
        with this minimum declared.
        """
        content = package_swift("test_project")
        assert ".macOS(.v14)" in content

    def test_declares_app_and_test_targets(self) -> None:
        """Both the app target and its test target are declared."""
        content = package_swift("test_project")
        assert '.target(name: "test_project")' in content
        assert 'name: "test_projectTests"' in content
        assert 'dependencies: ["test_project"]' in content

    def test_omits_library_product(self) -> None:
        """A watchOS app is not a distributable library: no products block."""
        content = package_swift("test_project")
        assert ".library" not in content
        assert "products:" not in content
