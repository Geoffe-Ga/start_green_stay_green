# Roadmap: Optimize Claude Usage in `green init`

**Created**: 2026-05-03
**Owner**: Performance / AI Orchestration
**Branch**: `claude/optimize-green-init-performance-Lsf7Y`
**Status**: In progress.

Shipped:
- Phases 0 (telemetry), 1 (de-AI generators), 2 (subagent parallelism) — PR #305
  merged onto main as commit `acf4572`.
- Phase 3a (two-pass split foundation: `--offline` / `--no-enhance` flags +
  `_generate_pass2_polish` rename) — branch
  `claude/execute-optimization-roadmap-Fhfnu`, commit `1abea59`.

Remaining: prompt caching + `tool_use` parsing (2c), `green enhance` command
+ `.enhance-state.json` resume (3b), prompt cleanup (4), batch mode (5),
UX/docs (6).

---

## Executive Summary

`green init` currently makes **~10 sequential Claude API calls** per run (~15–30 s of API
time, ~30–40 s wall-clock), and **5 of its core generators are gated entirely on
`ANTHROPIC_API_KEY`** — without a key, init prints `⊘ Skipped` for CI, code review,
CLAUDE.md, architecture rules, and subagents. The result:

- A user without a key gets a **partial scaffold** (no CI, no CLAUDE.md, no agents).
- A user with a key waits **30–40 seconds**, mostly on serial network round-trips.
- Several generators (`PreCommitGenerator`, `MetricsGenerator`, `ArchitectureEnforcementGenerator`,
  `GitHubActionsReviewGenerator`) accept an `orchestrator` parameter but **never call it** —
  the param exists but is dead.
- `CIGenerator` calls Claude to generate YAML that already exists as a static template
  for every supported language in `reference/ci/`.

**Target after this roadmap**:
- **No API key** → complete project, ~3–5 s, all generators produce real output via
  templates.
- **With API key** → same complete project + Claude polish layer, ~6–10 s wall-clock,
  **~9 logical Claude calls dispatched concurrently** (1 CLAUDE.md tune + 8 subagent
  tunes + N opt-in skill tunes), down from ~10 *sequential*. Wall-clock is bounded by
  the slowest single call, not their sum.
- **Zero "skipped" steps**. Claude becomes additive enhancement, never the only path.

### Design principle: many small parallel calls, not one big call

This roadmap **deliberately does not consolidate** subagent or skill tunings into a
single multi-target prompt. Many small parallel calls are preferred because:

1. **Failure isolation** — one bad subagent tune doesn't poison the other seven; the
   failed task can be retried independently.
2. **Surgical resume** — `green enhance` (Phase 3) can re-tune one agent on demand
   without re-paying for the rest.
3. **Better cache locality** — each per-agent prompt has a long, stable
   `SOURCE_AGENT_CONTEXT` prefix that benefits from prompt caching across calls;
   a single mega-prompt has no such repeated prefix to amortize.
4. **Clearer telemetry** — per-agent latency, token usage, and changes are visible,
   not hidden inside one giant tool-use array.
5. **Quality** — small focused prompts produce higher-fidelity output than asking
   one call to reason about 8+ heterogeneous targets at once.

The cost of this choice is that **request count stays roughly flat (~10)**;
the win is purely in latency (parallelism) and resilience.

This roadmap is sequenced so each phase ships independently, lowers risk, and is
readable by Claude Code agents using the 6-component prompt structure
(`Role / Goal / Context / Output Format / Examples / Requirements`).

---

## 1. Current-State Diagnosis (Validated)

### 1.1 Per-generator Claude usage

| Generator | File | API calls | Verdict | Evidence |
|-----------|------|----------:|---------|----------|
| `CIGenerator` | `generators/ci.py:261` | 1 | **Should not use Claude** — deterministic YAML | `reference/ci/{python,typescript,go,rust,…}.yml` already exist as canonical templates |
| `ClaudeMdGenerator` | `generators/claude_md.py:241` | 1 | **Good fit** — narrative synthesis | Combines reference template + project config into prose |
| `SubagentsGenerator` | `generators/subagents.py:280-282` | **8 (serial)** | **Good fit, bad implementation** — sequential `await` loop with no `asyncio.gather` | `for agent_name in REQUIRED_AGENTS: result = await self.generate_agent(...)` |
| `ArchitectureEnforcementGenerator` | `generators/architecture.py:57` | **0** | **Dead param** — stores `self.orchestrator` but never calls it | `grep "orchestrator\.generate"` returns no matches |
| `GitHubActionsReviewGenerator` | `generators/github_actions.py:56` | **0** | **Dead param** — Jinja2 only | Issue #102 notes "orchestrator reserved for future" |
| `PreCommitGenerator` | `generators/precommit.py:383` | **0** | **Dead param** — hardcoded `LANGUAGE_CONFIGS` | Param accepted, never invoked |
| `MetricsGenerator` | `generators/metrics.py:282` | **0** | **Dead param** — confirmed by `MetricsGenerator(None, config)` at `cli.py:975` | Caller passes `None` |
| `SkillsGenerator` (via `ContentTuner`) | `generators/skills.py` | 0–23 (optional) | **Already optional** — copy fallback works | `_copy_reference_skills` at `cli.py:550-581` |
| `StructureGenerator`, `DependenciesGenerator`, `TestsGenerator`, `ScriptsGenerator`, `ReadmeGenerator` | various | 0 | Pure template logic, no API needed | — |

### 1.2 Skip-on-no-key behaviour

`cli.py:1052-1070` (`_generate_with_orchestrator`) is strictly sequential and each step
short-circuits to `console.print("[yellow]⊘[/yellow] Skipped …")` when `orchestrator
is None`:

- `cli.py:836` — `Skipped CI (no API key)`
- `cli.py:858` — `Skipped code review (no API key)`
- `cli.py:893` — `Skipped CLAUDE.md (no API key)`
- `cli.py:905` — `Skipped architecture rules (no API key)`
- `cli.py:953` — `Skipped subagents (no API key)`

Three of these (review, architecture, CI) have no real Claude dependency in the
generated content — they are skipped purely because the orchestrator is `None`.

### 1.3 Wall-clock breakdown (estimated, with key)

| Stage | Duration | Notes |
|-------|---------:|-------|
| Structure / deps / tests / README | ~2–3 s | No API |
| Scripts (78 KB shell) | ~1 s | No API |
| Pre-commit, metrics | ~1.5 s | No API |
| Skills copy (no tuning) | ~0.2 s | No API |
| **CI generation** | **~4 s** | API |
| **CLAUDE.md** | **~4 s** | API |
| **Subagents (8 serial calls)** | **~10–16 s** | API, **largest single bottleneck** |
| **Architecture, review** | ~0.5 s | No API in practice |
| **Total** | **~30–40 s** | ~80% time in API |

### 1.4 Orchestrator design issues

`ai/orchestrator.py:303` opens a fresh `Anthropic` client per call:
```python
with Anthropic(api_key=self._api_key) as client:
    return self._retry_with_backoff(client, prompt, output_format)
```
This means **no connection reuse, no shared httpx pool, no async support, no
prompt caching, no batch API**. Every call eats fresh TLS + handshake.

The system prompt is also generic — `f"Generate {output_format} output. Follow
the instructions precisely."` — providing no role grounding and no caching
opportunity.

### 1.5 Prompt template state

`ai/prompts/templates/*.jinja2` exists with 5 minimal stub templates (~8 lines
each). They are **not used** by any generator — every generator builds its
prompt inline. The `PromptManager` infrastructure is built but unused.

---

## 2. Target Architecture

### 2.1 Two-pass model

```
green init  →  Pass 1: Deterministic scaffold      (always, ~3–5 s, no API)
                       ├─ structure, deps, tests, scripts, README
                       ├─ pre-commit, metrics, architecture rules
                       ├─ CI workflow (from reference/ci/<lang>.yml + Jinja2)
                       ├─ GitHub Actions code review (Jinja2)
                       ├─ CLAUDE.md (template-rendered baseline)
                       ├─ Skills (copy from reference/)
                       └─ Subagents (copy from reference/)

           →  Pass 2: Optional Claude polish        (if key present, ~3–6 s, parallel)
                       ├─ CLAUDE.md narrative tuning   (1 call)
                       ├─ Subagent body tuning         (1 batch / async-gather, 8 logical calls)
                       └─ Skills body tuning           (opt-in, batched)
```

**Key invariants**:
1. Pass 1 always produces a **complete, working project**. Pass 2 is additive.
2. Pass 2 calls run **in parallel** via `asyncio.gather` or the Anthropic Batches API.
3. No generator is "skipped". If Claude can't help, it ran the deterministic path.
4. `green enhance` becomes a separate command that re-runs only Pass 2 on an
   existing project (resumable, idempotent).

### 2.2 Right-sized Claude usage

| Use | Justification |
|-----|---------------|
| **CLAUDE.md narrative** | Prose synthesis from heterogeneous inputs (skills list, scripts, language, project name). Genuine LLM value. |
| **Subagent body tuning** | Adapts agent voice/scope from reference (Mojo ML) to target project. Per-agent reasoning useful. |
| **Skill tuning (opt-in)** | Same justification as subagents but at higher cost (23 skills). Default off; flag-gated. |
| **Everything else** | Deterministic templates, hard-coded configs, file copies. No Claude involvement. |

### 2.3 Orchestrator redesign

- `AsyncAnthropic` client, single instance per init, reused across all calls.
- Optional **prompt caching** on the shared system prompt + reference template
  prefix (cuts input tokens ~70 % on subagent batch).
- Optional **Message Batches API** for subagent/skill tuning (50 % cost
  discount, traded against latency — useful for `green enhance --batch` flow).
- Structured output via `tool_use` instead of regex-parsing `CHANGES:` sections
  in `tuner.py:163-181`.

---

## 3. Phased Roadmap

Each phase below uses the 6-component prompt structure so a future
implementation agent can be invoked directly with the phase block as its prompt.

---

### Phase 0 — Measurement & Telemetry (1 day)

**Why first**: every later phase claims a speed-up. We need a baseline that is
not vibes.

#### Role
You are a Python performance engineer instrumenting a CLI for telemetry without
changing user-visible behaviour.

#### Goal
Add per-step timing, API-call counting, and token-usage accounting to
`green init` so every later phase can be measured. Capture baseline numbers
into a checked-in JSON file under `tests/perf/`.

#### Context
- Entry point: `start_green_stay_green/cli.py`, `init` command around line 1100+.
- Step orchestration: `_generate_project_files` (`cli.py:1073-1099`) and
  `_generate_with_orchestrator` (`cli.py:1052-1070`).
- API call site: `AIOrchestrator.generate` (`ai/orchestrator.py:281-304`).
- Existing `console.status("…")` blocks already mark logical steps — wrap them.

#### Output Format
- New module `start_green_stay_green/utils/timing.py` exposing a context
  manager `step_timer(name)` and a module-level `TimingReport` collector.
- `AIOrchestrator` returns / records `(latency_s, retries, input_tokens,
  output_tokens)` per call into the same collector.
- New CLI flag `green init --timing-json PATH` writes a structured report:
  ```json
  {
    "wall_clock_s": 32.4,
    "api_calls": 10,
    "api_seconds": 24.1,
    "steps": [{"name": "subagents", "duration_s": 11.7, "api_calls": 8}, ...],
    "tokens": {"input": 38_412, "output": 11_204}
  }
  ```
- Baseline captured at `tests/perf/baselines/2026-05-03-init-baseline.json`
  for two scenarios: `with_key` and `no_key`.

#### Examples
- Pattern after Python's `time.perf_counter()` deltas inside the `console.status`
  block — see `cli.py:824` style.

#### Requirements
- Zero behaviour change without `--timing-json`. Default output identical.
- No new runtime dependencies.
- Pre-commit (all 31 hooks) must pass.
- Unit test `tests/unit/utils/test_timing.py` covering the collector.

---

### Phase 1 — De-AI the Deterministic Generators (2–3 days)

**Why early**: removes the "skipped without key" cliff and cuts ~4 s + 1 API
call from the happy path. Largest UX win per unit of effort.

#### Role
You are a Python generator-architecture engineer converting forced-API code
paths to deterministic Jinja2 + reference-template paths.

#### Goal
Make the following generators produce real output **without** an
`AIOrchestrator`, and remove `Skipped (no API key)` messages for them:
1. `CIGenerator` — render from `reference/ci/<language>.yml` via Jinja2.
2. `GitHubActionsReviewGenerator` — already Jinja2-based; remove dead
   orchestrator param and skip-when-None branch in caller.
3. `ArchitectureEnforcementGenerator` — already template-based; remove dead
   orchestrator param and skip-when-None branch in caller.
4. `ClaudeMdGenerator` — produce a **template-rendered baseline** when no
   orchestrator is given (so `CLAUDE.md` is always written). The optional
   Claude pass becomes a tuning step in Phase 3.

#### Context
- Reference YAMLs already exist: `reference/ci/{python,typescript,go,rust,
  java,kotlin,csharp,php,ruby,swift}.yml` (10 languages).
- `CIGenerator._generate_with_ai` (`generators/ci.py:222-267`) is the only
  Claude call site in the file; `LANGUAGE_CONFIGS` (`ci.py:25-82`) already
  hard-codes everything Claude was supposed to "decide".
- `cli.py:975` literally calls `MetricsGenerator(None, config)` — proof the
  orchestrator param is dead weight in metrics; same pattern should be made
  intentional across the four targeted generators.
- Caller branches to remove:
  `cli.py:835-836`, `857-858`, `904-905` (CI, review, architecture skip
  messages).
- For CLAUDE.md, the baseline template already lives at `reference/claude/`.

#### Output Format
For each of the four generators:
- Remove `orchestrator: AIOrchestrator | None` from `__init__` if unused
  (architecture, review, precommit, metrics) — change the public signature
  and update all callers in one pass.
- For CIGenerator: keep `orchestrator` optional, default `None`. New method
  `generate_workflow_from_template()` returns a `Workflow` populated from
  `reference/ci/<lang>.yml` rendered through Jinja2 with project-name and
  threshold substitutions. Make it the default; reserve Claude path for an
  explicit `enhance=True` flag (used in Phase 3).
- For ClaudeMdGenerator: split into `generate_baseline(project_config)`
  (template-only, sync) and `tune_baseline(baseline, project_config)`
  (Claude-powered, async). Caller decides which to invoke.
- Update `cli.py` `_generate_*_step` helpers: remove "Skipped" branches
  and run unconditionally. Keep the `with console.status(...)` wrapper.

#### Examples
**Before** (`cli.py:822-836`):
```python
def _generate_ci_step(project_path, language, orchestrator, file_writer=None):
    if orchestrator:
        with console.status("Generating CI pipeline..."):
            ci_generator = CIGenerator(orchestrator, language)
            workflow = ci_generator.generate_workflow()
            ...
        console.print("[green]✓[/green] Generated CI pipeline")
    else:
        console.print("[yellow]⊘[/yellow] Skipped CI (no API key)")
```
**After**:
```python
def _generate_ci_step(project_path, language, file_writer=None):
    with console.status("Generating CI pipeline..."):
        ci_generator = CIGenerator(language=language)
        workflow = ci_generator.generate_workflow_from_template()
        ...
    console.print("[green]✓[/green] Generated CI pipeline")
```

#### Requirements
- The generated CI YAML must be byte-equivalent (or strict superset) of
  what Claude produced today for canonical inputs — golden-file tests for
  Python, TypeScript, Go, Rust at minimum.
- Coverage stays ≥90 % overall and on touched files.
- All 31 pre-commit hooks pass.
- Update tests in `tests/unit/generators/` to match new signatures.
- Document the removed `Skipped (no API key)` messages in CHANGELOG.
- No new runtime deps; Jinja2 is already a dep (used by `PromptManager`).

---

### Phase 2 — Async Orchestrator + Parallel Subagent Tuning (2–3 days)

**Why next**: largest single bottleneck (~10–16 s sequential) → ~2–3 s
parallel. Requires Phase 1's baseline numbers to verify.

#### Role
You are an async Python engineer experienced with the Anthropic SDK,
`asyncio.gather`, prompt caching, and structured tool-use outputs.

#### Goal
Convert `AIOrchestrator` to `AsyncAnthropic` with a single shared client per
init run, parallelize `SubagentsGenerator.generate_all_agents`, and add
prompt caching to the system prompt + reference-template prefix used by
`ContentTuner`.

#### Context
- Current sync site: `ai/orchestrator.py:281-304`.
- Per-call client construction: `with Anthropic(api_key=self._api_key)
  as client` — kills connection pooling.
- Serial subagent loop: `generators/subagents.py:280-282`:
  ```python
  for agent_name in REQUIRED_AGENTS:
      result = await self.generate_agent(agent_name, target_context)
      results[agent_name] = result
  ```
- `cli.py:940-942` already uses `run_async(...)` — the async chain reaches
  the CLI; we just need to fan out below.
- Anthropic prompt caching: 5-minute TTL on prefixes ≥1024 tokens, marked
  with `cache_control: {"type": "ephemeral"}`. Subagent tuning sends the
  same `SOURCE_AGENT_CONTEXT` and similar instructions every time —
  prime caching candidate.

#### Output Format
- Refactor `AIOrchestrator`:
  - Hold a long-lived `AsyncAnthropic` client (created lazily, closed in
    `aclose()` / async context manager).
  - Add `async def generate_async(...)` alongside existing sync `generate`.
  - Keep the sync `generate` for non-async callers (it can wrap
    `asyncio.run(self.generate_async(...))` only when no loop is active).
- Refactor `SubagentsGenerator.generate_all_agents`:
  ```python
  tasks = [
      self.generate_agent(name, target_context)
      for name in REQUIRED_AGENTS
  ]
  results_list = await asyncio.gather(*tasks)
  return dict(zip(REQUIRED_AGENTS, results_list))
  ```
  Add bounded concurrency (`asyncio.Semaphore(8)`) so we don't hammer the
  Anthropic rate limit on slow networks.
- Add cache control to `ContentTuner._build_tuning_prompt` so the system
  prompt + source-agent prefix is sent with `cache_control: ephemeral`.
- Replace the regex-based `CHANGES:` parser (`tuner.py:163-181`) with a
  `tool_use` schema:
  ```python
  tools = [{
      "name": "report_tuning",
      "input_schema": {
          "type": "object",
          "properties": {
              "tuned_content": {"type": "string"},
              "changes":       {"type": "array", "items": {"type": "string"}}
          },
          "required": ["tuned_content", "changes"],
      }
  }]
  ```
  This eliminates the `len(parts) == _CHANGES_SECTION_PARTS` fragility.

#### Examples
- Reference for `asyncio.gather` with semaphore: standard Python idiom; see
  `https://docs.python.org/3/library/asyncio-task.html#asyncio.gather`.
- Reference for Anthropic prompt caching: prepend a system block with
  `cache_control={"type": "ephemeral"}`.

#### Requirements
- No more than 8 concurrent in-flight Anthropic requests by default.
- Sync `generate` API stays backward compatible (callers in non-async
  contexts still work).
- Phase 0 telemetry shows ≥4× speed-up on the subagents step (target:
  ~10–16 s → ≤4 s).
- Unit tests use `pytest-asyncio` and a mocked `AsyncAnthropic` to assert
  parallelism (e.g. all 8 calls dispatched before any awaits resolve).
- All 31 pre-commit hooks pass.
- No regression in cost: parallelism does not increase total tokens.
- Cache-control hits visible in telemetry (`response.usage
  .cache_read_input_tokens`).

---

### Phase 3 — Two-Pass Init + `green enhance` Command (3–4 days)

**Why now**: with deterministic generators (Phase 1) and fast async (Phase 2),
the architectural split becomes natural and risk-free.

#### Role
You are a CLI architect designing a clear separation between
"always-runs-fast scaffold" and "optional AI polish", with resumable state.

#### Goal
Restructure `green init` into Pass 1 (scaffold, no API needed) and Pass 2
(Claude polish), and expose Pass 2 as a separate idempotent command
`green enhance`. Add a status file so partial enhancements can resume.

#### Context
- Current sequential orchestration: `_generate_with_orchestrator`
  (`cli.py:1052-1070`) and `_generate_project_files` (`cli.py:1073+`).
- `CLAUDE.md` baseline template lives at `reference/claude/`.
- Skills tuning currently lives only behind the `--tune-skills` opt-in
  (verify exact flag name in `cli.py`).
- Anthropic SDK supports `messages.batches.create` for asynchronous
  fire-and-forget jobs — useful for `green enhance --batch`.

#### Output Format
- New flags on `init`:
  - `--offline` → skip Pass 2 entirely; never read API key (no prompts).
  - `--enhance` (default if key available) → run Pass 2 inline after Pass 1.
  - `--no-enhance` → run only Pass 1 even if a key is present.
- New command:
  ```
  green enhance [PATH]
      [--targets claude-md,subagents,skills]
      [--batch]                 # use Anthropic Batches API
      [--dry-run]               # report intended changes only
  ```
- New status file: `<project>/.claude/.enhance-state.json`
  ```json
  {
    "version": 1,
    "last_run": "2026-05-03T12:34:56Z",
    "scaffold_hash": "sha256:…",
    "completed": {
      "claude_md":  {"hash": "sha256:…", "model": "claude-sonnet-4-…"},
      "subagents":  {"hash": "sha256:…", "agents": ["chief-architect", …]}
    }
  }
  ```
  `green enhance` skips items whose source hash hasn't changed since
  the last successful tune.
- New section in README explaining the two-pass model.

#### Examples
- Default flow:
  ```
  $ green init my-app -l python
  ✓ Scaffolded project (3.4 s)
  ✓ Enhancing with Claude... (CLAUDE.md, 8 subagents in parallel) (4.1 s)
  ✓ Done. Run `green enhance` later to refresh AI-generated artifacts.
  ```
- Offline flow:
  ```
  $ green init my-app -l python --offline
  ✓ Scaffolded project (3.4 s)
  ℹ Run `green enhance` after setting ANTHROPIC_API_KEY to add AI polish.
  ```

#### Requirements
- `green init --offline` works on a machine with no network and no key —
  end-to-end test required.
- `green enhance` is idempotent: running it twice with no source changes
  makes zero API calls.
- Status file is **gitignored by default** in generated projects.
- `--batch` defers polling to a background-friendly poll loop with a
  visible progress indicator and a reasonable timeout (default 5 minutes).
- Cohesive UX: same console formatting as existing init steps.
- All 31 pre-commit hooks pass; mutation testing of the resume-skip logic
  ≥80 %.

---

### Phase 4 — Prompt-Engineering Cleanup (2 days)

**Why**: the `PromptManager` infrastructure exists but is unused; inline
prompts in generators duplicate boilerplate; the system prompt is generic.

(Phase 2's "test-only branch in `_await_or_offload`" follow-up was
resolved in PR #305 itself: the affected `ContentTuner` tests were
migrated from `create_autospec(AIOrchestrator)` to
`MagicMock(spec=AIOrchestrator)` and the branch was deleted. Issue
#306 is closed.)

#### Role
You are a prompt engineer applying the 6-component framework
(`Role / Goal / Context / Format / Examples / Requirements`) to all
generator-side prompts.

#### Goal
Move every generator-side Claude prompt into versioned Jinja2 templates
under `start_green_stay_green/ai/prompts/templates/`, give each a strong
role-grounded system prompt, and make the `PromptManager` the single
prompt-loading path.

#### Context
- Existing inline prompts:
  - `ClaudeMdGenerator._build_generation_prompt` (`generators/claude_md.py:119-166`).
  - `CIGenerator._generate_with_ai` (`generators/ci.py:222-267`) — kept
    only as the optional Phase 3 enhancement path after Phase 1.
  - `ContentTuner._build_tuning_prompt` (`ai/tuner.py:99-151`).
- Current system prompt: `f"Generate {output_format} output. Follow the
  instructions precisely."` — no role, no domain grounding.
- `ai/prompts/templates/` already has 5 stub Jinja2 files that nobody uses.

#### Output Format
- New prompt files (one per use case), each a Jinja2 template producing a
  full message-array body conforming to the 6-component structure:
  - `claude_md_baseline.jinja2`  (template-only render of CLAUDE.md)
  - `claude_md_tune.jinja2`      (Claude polish over baseline)
  - `subagent_tune.jinja2`       (per-agent tuning)
  - `skill_tune.jinja2`          (per-skill tuning)
  - `ci_enhance.jinja2`          (optional Claude polish over template CI)
- New role-grounded system prompts per use case, e.g. for subagent tuning:
  > You are a senior agent designer adapting reusable subagent profiles
  > from a Mojo ML research context to a target software project. Preserve
  > YAML frontmatter, role identity, and section structure. Update only
  > examples, terminology, and references.
- All generators import their prompt via `PromptManager.render(name, ctx)`;
  no f-string prompts remain in generator files.
- A unit test for each template asserts the rendered prompt contains all
  6 components by name.

#### Examples
- See `.claude/skills/prompt-engineering/SKILL.md` (in this repo) for the
  6-component framework structure and example transformations.

#### Requirements
- Every generator prompt is one Jinja2 template, not an inline f-string.
- Each template's rendered output begins with `## Role`, `## Goal`,
  `## Context`, `## Output Format`, `## Examples`, `## Requirements`
  sections (or equivalent JSON structure if used inside `tool_use`).
- Templates are validated by `PromptManager.validate_template` in CI.
- Token-count delta vs Phase 3 baseline is reported in PR description
  (acceptable: ±15 % for better outputs; >15 % requires justification).
- All 31 pre-commit hooks pass.

---

### Phase 5 — Cost & Throughput Optimization (1–2 days, optional)

**Why**: enables low-cost bulk runs (CI, demo environments, batch enhance)
and is straight upside once Phases 1–4 land.

**Note**: This phase preserves the *many small parallel calls* design
principle. The Batches API submits N independent requests inside one
submission; per-request results, failures, and token accounting are still
returned per-request. We are not consolidating multiple subagents into a
single multi-target prompt.

#### Role
You are a cost-aware AI infra engineer using the Anthropic Message Batches
API and aggressive prompt caching for predictable bulk workloads.

#### Goal
Add a `--batch` mode to `green enhance` that submits subagent + skill
tunings via `messages.batches.create` (50 % discount, async polling),
and harden prompt caching so a back-to-back `green init` + `green enhance`
on the same project hits the cache reliably.

#### Context
- Anthropic Message Batches API: submit up to 100k requests per batch,
  results within 24 h, 50 % cheaper than sync. SDK method:
  `client.messages.batches.create(requests=[…])`.
- Phase 2 added cache_control to the prefix; Phase 5 should add a
  per-project cache key so a developer iterating with multiple
  `green enhance` invocations gets cache hits across the 5-minute TTL.

#### Output Format
- `green enhance --batch` submits one batch containing all subagent +
  optional skill tunings, polls every 30 s, writes results when complete.
- Telemetry reports `cache_read_input_tokens / total_input_tokens` ratio
  per run; target ≥0.5 on the second consecutive `green enhance`.
- Documentation in README and a short ADR under
  `plans/architecture/ADR-001-batch-enhance.md`.

#### Requirements
- Batch mode is opt-in; sync mode remains the default (lower latency).
- Idempotent: an interrupted batch can be resumed via the
  `.enhance-state.json` file from Phase 3 (store the batch id).
- All 31 pre-commit hooks pass.

---

### Phase 6 — UX, Docs, Release (1 day)

#### Role
You are a developer-experience writer and release manager finalizing a
performance-and-architecture release.

#### Goal
Update README, CLAUDE.md, CHANGELOG, and the `green init` `--help` output
to reflect the new two-pass model, the `enhance` command, the `--offline`
mode, and the new performance numbers.

#### Context
- Current README is 17.7 KB; AI section needs a rewrite.
- `green init --help` currently surfaces `--api-key` (deprecated) — clean
  this up.
- Performance numbers come from Phase 0 telemetry baseline + post-roadmap
  measurement run on the same hardware.

#### Output Format
- README: new "AI Enhancement" section with a side-by-side table:
  | Mode | Wall-clock | API calls | Notes |
  | `green init --offline` | ~3 s | 0 | Complete project, no AI |
  | `green init` (default) | ~6–10 s | ≤3 | Scaffold + parallel polish |
  | `green init --no-enhance` | ~3 s | 0 | Same as `--offline` if no key |
  | `green enhance` | ~3–6 s | ≤3 | Re-tune AI artifacts |
  | `green enhance --batch` | minutes / hours | ≤3 | 50 % cost discount |
- CHANGELOG entry calling out the removal of "Skipped (no API key)"
  steps as a behaviour change.
- `green init --help` lists new flags with one-line descriptions.

#### Requirements
- All numbers in the docs are sourced from a checked-in telemetry JSON,
  not invented.
- All 31 pre-commit hooks pass.

---

## 4. Sequencing & Dependencies

```
Phase 0 (telemetry)  ──────────────────────────────────┐
                                                        ▼
Phase 1 (de-AI generators)  ──┐                     measurement
                              ▼                      gates each
Phase 2 (async + parallel)  ──┤                     subsequent
                              ▼                      phase
Phase 3 (two-pass + enhance) ─┤
                              ▼
Phase 4 (prompt cleanup)  ────┤
                              ▼
Phase 5 (batch / cache)  ─────┤   (optional)
                              ▼
Phase 6 (UX / docs / release)
```

- **Phase 0 must land first.** Without baseline numbers, every later phase's
  claims are unverifiable.
- **Phases 1 and 2 are independent** — could run in parallel PRs, but
  reviewing them sequentially is safer.
- **Phases 3 onwards depend on Phases 1 + 2.**

---

## 5. Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| CI YAML drift between Claude output and template output | Medium | Medium | Golden-file tests across 4+ languages in Phase 1; review one-off Claude diffs against template baseline before merging. |
| Async refactor breaks sync callers | Medium | High | Keep sync `generate` API as a thin wrapper; comprehensive unit tests; mutation testing on the wrapper. |
| `asyncio.gather` rate-limits against Anthropic | Low | Medium | `asyncio.Semaphore(8)` cap; exponential backoff already exists in orchestrator. |
| Prompt caching invalidates unexpectedly (5-min TTL) | Low | Low | Telemetry surfaces hit ratio; cache miss is a perf regression, not a correctness issue. |
| `green enhance --batch` results lag user expectation | Medium | Low | Document expected latency; default remains sync. |
| Removing "Skipped" messages confuses existing users | Low | Low | CHANGELOG callout; release notes. |

---

## 6. Out of Scope

- Adding new languages to `templates/` or `reference/ci/`.
- Replacing `Anthropic` with another model provider.
- Rewriting the generator base classes beyond what each phase requires.
- Local LLM fallback (e.g. Ollama) — could be a follow-up roadmap once
  the two-pass split lands.
- Subagent / skill **content** improvements — this roadmap is about how
  Claude is *deployed*, not what reference content it tunes.

---

## 7. Open Questions for Reviewer

1. **Default behaviour with no key**: should `green init` (no flags, no key)
   silently produce a scaffold (offline-equivalent), or should it print a
   one-line nudge ("Run `green enhance` after setting ANTHROPIC_API_KEY")?
   This roadmap assumes the latter.
2. **Skills tuning by default**: today it's an opt-in `--tune-skills` flag
   (verify in `cli.py`). After Phase 3, should `green enhance` default to
   tuning skills, or remain opt-in? (Cost: 23 calls × ~2 s ≈ 46 s sync,
   ~6 s parallel.)
3. **`green enhance` on dirty trees**: if a user has hand-edited
   `.claude/agents/chief-architect.md`, should `green enhance` overwrite,
   diff, or skip with a warning? Suggested default: skip with a warning
   plus `--force` to override.
4. **Telemetry sharing**: should `--timing-json` ever be sent anywhere
   (opt-in metric reporting), or always stay local? This roadmap assumes
   always local.

---

## 8. Acceptance Criteria for the Whole Roadmap

A reviewer can mark this roadmap "shipped" when **all** of the following hold,
verified by checked-in telemetry from Phase 0's tooling on the same
hardware as the baseline:

- [ ] `green init --offline` produces a complete, ready-to-use project on a
      machine with no network access and no `ANTHROPIC_API_KEY` set —
      no `Skipped` messages, no warnings about missing AI artifacts.
- [ ] Default `green init` wall-clock with key is **≤10 s** (down from
      ~30–40 s) on the baseline machine.
- [ ] Default `green init` dispatches its Claude calls **concurrently** via
      `asyncio.gather` (bounded by `Semaphore(8)`); request count stays
      ~9–10 by design (see *Design principle: many small parallel calls*),
      but **wall-clock API time is bounded by the single slowest call**,
      not their sum. Telemetry must show concurrent dispatch (all calls
      in-flight before the first response returns).
- [ ] All five `console.print("[yellow]⊘[/yellow] Skipped … (no API key)")`
      messages are gone from `cli.py`.
- [ ] `MetricsGenerator`, `PreCommitGenerator`,
      `ArchitectureEnforcementGenerator`, and
      `GitHubActionsReviewGenerator` no longer accept an `orchestrator`
      parameter (or any other dead Claude wiring).
- [ ] `green enhance` exists, is idempotent, and supports `--batch`.
- [ ] Every Claude-bound prompt is loaded via `PromptManager` from a
      versioned Jinja2 template using the 6-component structure.
- [ ] All 31 pre-commit hooks pass; coverage ≥90 %; mutation score ≥80 %
      on touched modules.
- [ ] CHANGELOG, README, and `--help` reflect the new model.

---

## 9. References

- `start_green_stay_green/ai/orchestrator.py` — current sync orchestrator
- `start_green_stay_green/ai/tuner.py` — `ContentTuner` (regex-parsed CHANGES)
- `start_green_stay_green/ai/prompts/manager.py` — unused `PromptManager`
- `start_green_stay_green/cli.py:497-548` — API key resolution
- `start_green_stay_green/cli.py:816-953` — per-step skip-on-no-key branches
- `start_green_stay_green/cli.py:1052-1070` — sequential AI orchestration
- `start_green_stay_green/generators/subagents.py:267-283` — serial async loop
- `start_green_stay_green/generators/ci.py:222-267` — Claude call for deterministic YAML
- `start_green_stay_green/generators/architecture.py:57` — dead orchestrator param
- `start_green_stay_green/generators/metrics.py` — dead orchestrator param (proven by `cli.py:975`)
- `reference/ci/*.yml` — 10 ready-to-use CI templates
- `reference/claude/` — CLAUDE.md baseline
- `.claude/skills/prompt-engineering/SKILL.md` — 6-component framework
- Anthropic SDK: `messages.batches.create`, `cache_control`, `tool_use`
