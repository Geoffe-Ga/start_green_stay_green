# Quality Control Scripts Reference

This directory contains reference implementations of quality control scripts for different programming languages.

## Purpose
These scripts serve as templates for the Scripts Generator (Issue 3.3) to create customized quality control scripts for target repositories.

## Structure
Each language directory contains:
- `lint.sh` - Run all linters
- `format.sh` - Auto-format code
- `test.sh` - Run test suite with coverage
- `security.sh` - Security scanning
- `complexity.sh` - Complexity analysis
- `build.sh` - Build/compile the project
- `clean.sh` - Clean build artifacts

## Usage
These are reference implementations that will be:
1. Copied to target repositories
2. Customized based on project configuration
3. Tuned by AI to match project specifics

## Languages Supported
- Python
- TypeScript
- Go
- Rust
- Java
- C#
- Swift
- Ruby
- PHP
- Kotlin

## Cross-Platform Usage (Windows)

The reference gates are POSIX shell scripts. They run unchanged on
Windows through Git Bash (bundled with Git for Windows), which needs no
executable bit because bash receives the script path as an argument:

```
bash scripts/test.sh
bash scripts/lint.sh
```

Each script wraps the language's own toolchain runner (`npm`/`npx`,
`go`, `cargo`, `gradle`, `swift`, `mvn`, `dotnet`, `bundle`,
`cmake`/`ctest`), which is cross-platform by design — so where bash is
unavailable, the wrapped toolchain command can be invoked directly.
The scripts remain the source of truth for option sets, ordering, and
threshold enforcement (e.g. minimum coverage).

Generated projects receive a `scripts/README.md` (see
`start_green_stay_green/generators/gate_commands.py`, the single
source of truth) documenting the POSIX, Git Bash, and toolchain-native
invocation for every emitted gate, plus a `.gitattributes` rule pinning
`*.sh` to LF so the gates survive `git clone` on `core.autocrlf=true`
Windows checkouts.
