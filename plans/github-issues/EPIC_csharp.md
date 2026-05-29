## Context

Part of the **language-support parity initiative**: every supported language
should be wired into every generator so `green init` produces a fully green
project regardless of language. This epic covers **C#**
(general .NET).

**Current state:** C# is registered with `ci.py`/`dependencies.py`/`structure.py`/`readme.py`/`tests_gen.py` entries, but is **missing from `precommit.py`, `scripts.py`, `metrics.py`, and `architecture.py`** — pre-commit generation raises for C#.

No smartwatch platform; this closes parity gaps so C# matches python/typescript as a fully green target.

## Goal

Complete production-grade **C#** support so
`green init -l csharp` generates a project that Starts Green and Stays Green
with the language's native quality tooling — passing all three gates.

## Target toolchain

| Concern | Tooling |
|---|---|
| Test framework | xUnit |
| Linters | Roslyn analyzers |
| Formatters | dotnet format |
| Security | security-code-scan + dotnet list package --vulnerable |
| Coverage | Coverlet (≥90%) |
| Complexity | Roslyn / SonarAnalyzer.CSharp (≤10) |
| Architecture enforcement | NetArchTest (or ArchUnitNET) |
| Package manager | NuGet |
| Versions | .NET 6.0, 8.0 |


## Sub-Issues (gap-driven)

Only the generator cells C# is actually missing are filed:

1. **Quality tooling** — pre-commit, scripts, metrics & architecture
2. **Tests & coverage** — unit / integration / e2e
3. **Documentation** — CLAUDE.md, README, CLI reference, SPEC

## Acceptance Criteria

- [ ] All sub-issues closed
- [ ] `green init -l csharp` produces a project passing
      `pre-commit run --all-files` out of the box
- [ ] `green init -l python -l csharp` (multi-language) works via the
      YAML-aware pre-commit merge
- [ ] Parity matrix row for C# is fully ✅
- [ ] CLAUDE.md / README list C# as fully supported

## Quality Gates (non-negotiable)

- [ ] `pre-commit run --all-files` passes (all hooks)
- [ ] Repo coverage stays ≥90%, every function complexity ≤10, pylint ≥9.0
- [ ] Docstring coverage ≥95% on new/changed code
- [ ] No new `# noqa` / `type: ignore` without an issue reference
- [ ] CI green (Gate 2) and review LGTM (Gate 3)

## References

- `start_green_stay_green/generators/base.py:20` — `SUPPORTED_LANGUAGES`
- `start_green_stay_green/generators/ci.py:40` — `LANGUAGE_CONFIGS`
- `start_green_stay_green/cli.py` — `_resolve_languages`, `_get_setup_instructions`
- `.claude/docs/quality-standards.md`, `reference/workflows/stay-green.md`
