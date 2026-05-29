## Context

Part of the **language-support parity initiative**. Go is wired into precommit/scripts/metrics/ci, but is **missing from `architecture.py`** (`supported_languages = {python, typescript}` at architecture.py:94). Architecture enforcement is the only parity gap.

Go is otherwise fully wired (precommit, scripts, metrics, ci),
so this is a single focused parity issue rather than a full epic.

## Goal

Add Go dependency/layer enforcement to `architecture.py` so
generated Go projects get the same architecture gate as
python/typescript.

## Scope — files to touch

- `start_green_stay_green/generators/architecture.py` — add `go` to
  `supported_languages` (`architecture.py:94`) and a generation branch using
  **go-arch-lint (or depguard via golangci-lint)** (parallel to import-linter/dependency-cruiser)
- `tests/unit/generators/` — tests for the new branch
- `tests/unit/test_multi_language.py` — ensure `go` exercises architecture
- docs: note Go architecture enforcement where relevant

## Acceptance Criteria

- [ ] `green init -l go` emits an architecture-enforcement config
      (go-arch-lint (or depguard via golangci-lint))
- [ ] Architecture parity row for Go is ✅
- [ ] Repo coverage stays ≥90%

## Quality Gates (non-negotiable)

- [ ] `pre-commit run --all-files` passes (all hooks)
- [ ] Repo coverage stays ≥90%, every function complexity ≤10, pylint ≥9.0
- [ ] Docstring coverage ≥95% on new/changed code
- [ ] No new `# noqa` / `type: ignore` without an issue reference
- [ ] CI green (Gate 2) and review LGTM (Gate 3)

## References

- `start_green_stay_green/generators/architecture.py:94`
- `tests/unit/test_multi_language.py`
