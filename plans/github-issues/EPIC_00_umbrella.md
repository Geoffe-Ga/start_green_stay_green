## Context

Audit of `start_green_stay_green/generators/*.py` shows uneven language
support: `precommit.py`, `scripts.py`, `metrics.py` cover only
python/typescript/go/rust, and `architecture.py` only python/typescript — yet
`base.py` advertises 7 languages and CLAUDE.md advertises Swift. Several
languages (java, csharp, ruby) **raise** when generating pre-commit config.
Smartwatch platforms additionally require Swift (watchOS), Kotlin/Java
(Wear OS), and C/C++ (Tizen).

## Goal

Reach **full parity**: every supported language wired into every generator so
`green init -l <lang>` produces a fully green project. python/typescript are
the reference; all others are brought up to match.

## Parity gaps (current)

| Language | Parity gaps |
|---|---|
| `python` | ✅✅✅✅✅✅✅✅ (reference) |
| `typescript` | ✅✅✅✅✅✅✅✅ (reference) |
| `go` | missing: architecture |
| `rust` | missing: architecture |
| `java` | missing: precommit, scripts, metrics, architecture (+Wear OS scaffold) |
| `csharp` | missing: precommit, scripts, metrics, architecture |
| `ruby` | missing: precommit, scripts, metrics, architecture |
| `swift` | NEW — all generators |
| `kotlin` | NEW — all generators |
| `cpp` | NEW — all generators |

## Approach

Gap-driven per-language epics (this issue is the umbrella tracker). Each
language epic only files sub-issues for cells it actually lacks; `templates/`
is excluded (vestigial — every language ships only `.gitkeep` yet python works).

## Language Support Contract (new invariant)

To prevent regression, adding a language MUST wire all of: registration
(`base.py` + CLI), scaffolding (`structure`/`dependencies`/`readme`), quality
(`precommit`/`scripts`/`metrics`/`architecture`), `ci`, tests
(incl. `test_multi_language.py`), and docs. Add a test asserting every
`SUPPORTED_LANGUAGES` entry is handled by every generator.

## Child Epics / Issues

Linked as GitHub sub-issues below (swift, kotlin, cpp, java, csharp, ruby
epics; go, rust single architecture issues).

## Acceptance Criteria

- [ ] All child epics/issues closed
- [ ] A guard test fails if any `SUPPORTED_LANGUAGES` entry is unhandled by any generator
- [ ] Parity matrix is fully ✅ for every language
- [ ] CLAUDE.md / README accurately list supported languages

## Quality Gates (non-negotiable)

- [ ] `pre-commit run --all-files` passes (all hooks)
- [ ] Repo coverage stays ≥90%, every function complexity ≤10, pylint ≥9.0
- [ ] Docstring coverage ≥95% on new/changed code
- [ ] No new `# noqa` / `type: ignore` without an issue reference
- [ ] CI green (Gate 2) and review LGTM (Gate 3)

## References

- `start_green_stay_green/generators/base.py:20`
- `start_green_stay_green/generators/{precommit,scripts,metrics,architecture,ci}.py`
- `.claude/docs/quality-standards.md`
