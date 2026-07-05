# Recap Metrics — Definitions and Tuning

Every number in the Discord embed, exactly how it is computed in `stats.py`, and how to change it. All math is pure and unit-tested; all I/O is in `recap.py`.

## PRs merged

- **total** — count of closed PRs with a non-null `merged_at`, capped at `--max-prs` (default 200). The cap bounds the per-PR comment fetches; raise it for very long campaigns.
- **last 7 days** — merges whose `merged_at` falls within the trailing 7 days of `now`.

Source: `GET /repos/{repo}/pulls?state=closed`, filtered to merged. The list endpoint is paginated 100 at a time.

## Merge rate

`per_day = total_merges / span_days`, where `span_days` runs from the **first** merge to **now** — not to the last merge. This is deliberate: anchoring the denominator to `now` makes a stalled loop show a *decaying* rate instead of a frozen one, which is the honest signal. A loop that merged 50 PRs in its first week but nothing since should not keep reporting "7/day".

To report rate over the active window only, change `merge_rate` in `stats.py` to use `max(merged_at)` instead of `now` as the right edge.

## Review iterations before LGTM

For each merged PR, `recap.py` fetches issue comments oldest-first and runs `normalize_verdict` on each body. A comment counts as a verdict only if it contains the word `VERDICT` (case-insensitive), matching the `iteration-trigger.yml` convention. The verdict is then:

- `CHANGES_REQUESTED` if the body mentions changes requested,
- `LGTM` if it mentions LGTM,
- `COMMENTS` otherwise.

`iterations_before_lgtm` returns the number of non-LGTM verdicts that preceded the **first** LGTM — i.e. how many feedback rounds the loop took. PRs that never reached an LGTM verdict return `None` and are excluded from the average (they were merged on human judgment or only got COMMENTS).

The embed shows:

- **avg rounds to LGTM** — mean of the per-PR iteration counts.
- **first-try clean %** — share of LGTM PRs that landed with zero feedback rounds.
- **worst** — the maximum rounds any single PR needed.
- **n** — how many PRs contributed (the LGTM sample size).

**Tuning:** if your reviewer phrases verdicts differently (no `Verdict:` line, or different keywords), edit `normalize_verdict`. If LGTM detection is too loose — e.g. a comment saying "not LGTM yet" — note the function already prefers `CHANGES_REQUESTED` over a bare LGTM mention to avoid that trap.

## Time to merge

Per PR, `merged_at - created_at` in hours. The embed shows median (robust to one slow outlier), fastest, and slowest. `_fmt_hours` renders sub-hour as minutes, up to two days as hours, and beyond that as days.

## Backlog remaining and ETA

`open_items` is the count of **open issues with the `pull_request` key absent** (open PRs are excluded so they don't inflate the backlog) **minus any issue bearing one of the Ralph picker's exclude labels** — epics, `blocked`, `needs-spec`, `do-not-auto-merge`, etc. — so the ETA reflects what `scripts/ralph/pick-next.sh` would actually pick up next, not every open card. The exclude set defaults to the same list as the picker and honors the same `RALPH_EXCLUDE_LABELS` env var; set it (space-separated) to override, or to an empty string to count every open issue. ETA is `open_items / per_day`, expressed as days and an absolute date.

When `per_day` is zero (no merges in window), the ETA is reported as `unknown (stalled)` rather than infinity. When the backlog is empty, it reads `backlog clear`.

**Tuning — this is the metric most worth checking.** If the Ralph backlog is not "open GitHub issues" (for example it's a `git-issues/` directory of unfiled prompts, or a project board column), replace `count_open_backlog` in `recap.py` with a count of the real source. The pure `estimate_remaining` math does not change.

## Busiest day

The calendar day (UTC) with the most merges, and that count. Computed by bucketing `merged_at` by `date()`.

## This PR's footprint

Additions, deletions, and changed-file count for the **most recently merged** PR only (fetched via the single-PR detail endpoint, since the list endpoint omits diff stats). To total churn across the whole campaign instead, fetch detail for every PR and pass all tuples to `churn_totals` — note that is one extra API call per PR.

## The ten-word headline

`generate_headline` asks `claude-opus-4-8` (effort `low`) for a single headline of at most ten words describing what merging the latest PR unlocked, with explicit instructions to avoid buzzwords and jargon. It degrades gracefully: with no `ANTHROPIC_API_KEY` or no SDK, it returns the cleaned PR title clipped to ten words, and any API error falls back the same way — the recap never fails on the headline.
