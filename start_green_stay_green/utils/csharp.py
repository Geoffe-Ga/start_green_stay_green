"""C# naming helpers and NuGet toolchain versions (#370).

Provides a single source of truth for the PascalCase root namespace
derived from a project's package name, shared by the C# scaffold's
structure, tests, dependencies, and architecture generators: source
``namespace`` declarations, the xUnit test namespace, and the
NetArchTest layer matrix all derive from :func:`csharp_namespace`, so
they can never drift apart. Unlike Java packages, C# namespaces carry
no directory-matching requirement, so the helper has no path
counterpart (the inverse of ``utils.java.android_package_path``).

The pinned NuGet package versions for the generated ``.csproj`` live
here for the same reason (the ``utils.java`` Maven-pin precedent). All
pins were verified against the live nuget.org flat-container index
before being recorded.
"""

from __future__ import annotations

import re

from start_green_stay_green.utils.naming import pascal_case

# Pinned NuGet package versions for the generated .csproj manifest.
# xUnit test stack (foundation scaffold).
XUNIT_VERSION = "2.6.0"
XUNIT_RUNNER_VERSION = "2.5.3"
TEST_SDK_VERSION = "17.8.0"
# coverlet.msbuild backs the >=90% coverage gate (#370). The 8.x line
# matches the scaffold's net8.0 TargetFramework; the 10.x line tracks
# the .NET 10 SDK the scaffold does not target yet. Live-verified.
COVERLET_MSBUILD_VERSION = "8.0.1"
# NetArchTest.Rules backs the generated architecture test (#370); a
# plain PackageReference in the single-project csproj (the ArchUnit/
# Konsist manifest-touch precedent). Live-verified latest stable.
NETARCHTEST_RULES_VERSION = "1.3.2"
# SecurityCodeScan runs as a Roslyn analyzer during every build (#370).
# Live-verified latest stable; the VS2019 suffix is the package's
# naming convention, not a Visual Studio requirement — it is a
# netstandard2.0 analyzer that the .NET 8 SDK loads fine.
SECURITY_CODE_SCAN_VERSION = "5.6.7"

# Characters that split a package name into namespace words.
_SEPARATORS = re.compile(r"[^a-zA-Z0-9]+")


def csharp_namespace(package_name: str) -> str:
    """Derive a valid PascalCase C# root namespace from a package name.

    Separator characters (hyphens, dots, anything not alphanumeric) are
    normalized to underscores and the result runs through the shared
    :func:`~start_green_stay_green.utils.naming.pascal_case` helper
    (``wrist_ledger`` -> ``WristLedger``). On top of that, C#'s
    identifier rules apply: a namespace that would start with a digit
    gains an ``App`` prefix, and a name with no usable characters falls
    back to ``App``.

    Args:
        package_name: The project's package identifier (e.g.
            ``wrist_ledger`` or ``wrist-ledger``).

    Returns:
        A PascalCase namespace such as ``WristLedger``.
    """
    namespace = pascal_case(_SEPARATORS.sub("_", package_name))
    if not namespace:
        return "App"
    if namespace[0].isdigit():
        return f"App{namespace}"
    return namespace
