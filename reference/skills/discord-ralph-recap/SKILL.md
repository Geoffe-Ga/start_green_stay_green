---
name: discord-ralph-recap
description: >-
  Post a beautifully formatted recap of a Ralph tick-loop's progress to a
  Discord channel every time a pull request is merged, using the
  DISCORD_BOT_TOKEN and RALPH_CHANNEL_ID environment variables. Use when the
  user says "recap my Ralph loop", "post merge stats to Discord", "summarize
  the tick loop", "set up a Ralph progress bot", or wants merge-rate, review-
  iteration, ETA, and a ten-word "what this unlocked" headline pushed to
  Discord on each merge. Covers the GitHub Actions trigger, the stats engine,
  and the Discord embed. Do NOT use for iterating on a single PR's review
  feedback (use address-feedback skill), waiting on a verdict (use
  await-claude-review skill), debugging CI failures (use ci-debugging skill),
  or general GitHub backlog cleanup (use backlog-grooming skill).
metadata:
  author: Geoff
  version: 1.0.0
---

# Discord Ralph Recap

Whenever a PR merges, summarize how the Ralph tick loop is doing and post it to a Discord channel as a clean embed: PRs merged, merge rate, average review iterations before LGTM, estimated time remaining, and a ten-word headline for what the latest merge unlocked.

A "Ralph tick loop" is an autonomous agent grinding a backlog one issue at a time — each tick opens a PR, iterates against the Claude reviewer's verdict until LGTM, merges, and moves on. This skill turns that merge history into a recap.

## What You Need

- `DISCORD_BOT_TOKEN` — a Discord bot token. The bot must be in the server and have **View Channel** + **Send Messages** on the target channel.
- `RALPH_CHANNEL_ID` — the target channel's numeric ID (Developer Mode → right-click channel → Copy Channel ID).
- A GitHub token. In GitHub Actions the built-in `GITHUB_TOKEN` is enough (it needs `contents: read`, `pull-requests: read`, `issues: read`).
- Optional `ANTHROPIC_API_KEY` — enables the Claude-written ten-word headline. Without it, the headline falls back to a cleaned PR title, and nothing else changes.

## Files

```
discord-ralph-recap/
├── SKILL.md
├── scripts/
│   ├── recap.py      # I/O shell: fetch GitHub data, generate headline, post embed
│   └── stats.py      # pure, unit-tested statistics math
├── assets/
│   └── ralph-recap.yml  # GitHub Actions workflow: fires on every merged PR
└── references/
    └── metrics.md    # exactly how each number is computed, and how to tune it
```

## Instructions

### Step 1: Confirm the trigger model

The recap should "fire every time a PR is merged". The robust way to do that is a GitHub Actions workflow keyed on `pull_request` with `types: [closed]`, gated to merged PRs:

```yaml
on:
  pull_request:
    types: [closed]
jobs:
  recap:
    if: github.event.pull_request.merged == true
```

`closed` fires on both merge and plain close; the `merged == true` guard keeps it to actual merges. Do not use `push: branches: [main]` — squash-merges land as one commit but a non-merge push (a hotfix, a revert) would also trip it.

### Step 2: Install the workflow

Copy the bundled workflow into the repo and confirm the secrets are wired:

```bash
mkdir -p .github/workflows
cp .claude/skills/discord-ralph-recap/assets/ralph-recap.yml .github/workflows/ralph-recap.yml
```

Then add the repository secret `DISCORD_BOT_TOKEN` and the repository variable (or secret) `RALPH_CHANNEL_ID`. Add `ANTHROPIC_API_KEY` as a secret if you want the Claude headline. The workflow reads them as env vars of the same name — no code change needed.

### Step 3: Dry-run locally before trusting the trigger

Verify the embed renders before it ever posts. `--dry-run` prints the payload instead of sending it:

```bash
DISCORD_BOT_TOKEN=unused RALPH_CHANNEL_ID=unused \
GITHUB_TOKEN="$(gh auth token)" \
python .claude/skills/discord-ralph-recap/scripts/recap.py \
    --repo your-org/your-repo --dry-run
```

Inspect the JSON. If the numbers look right, drop `--dry-run` (and set the real `DISCORD_BOT_TOKEN` / `RALPH_CHANNEL_ID`) to post once manually.

### Step 4: Tune the metrics if needed

The defaults work out of the box, but the backlog ETA and the iteration count make assumptions worth checking — see `references/metrics.md`. The two most common adjustments:

- **Backlog size**: ETA divides open GitHub issues (PRs excluded) by the merge rate. If the loop's backlog lives somewhere else (a `git-issues/` directory, a project board), point the count at that instead.
- **Verdict detection**: iteration counting keys on Claude review comments containing a `Verdict` line, matching the `iteration-trigger.yml` convention. If the reviewer phrases verdicts differently, adjust `normalize_verdict` in `stats.py`.

### Step 5: Let it run

After the first real merge, the recap posts automatically. Each post is self-contained — no state is stored between runs; every recap is recomputed from the live merge history.

## Examples

### Example 1: Stand it up on an existing Ralph repo

```bash
cp .claude/skills/discord-ralph-recap/assets/ralph-recap.yml .github/workflows/ralph-recap.yml
gh secret set DISCORD_BOT_TOKEN
gh variable set RALPH_CHANNEL_ID --body "123456789012345678"
gh secret set ANTHROPIC_API_KEY      # optional, for the headline
git add .github/workflows/ralph-recap.yml
git commit -m "Add Discord Ralph recap on merge"
```

The next merged PR triggers the first recap.

### Example 2: Post a one-off recap from the terminal

```bash
DISCORD_BOT_TOKEN="$BOT_TOKEN" RALPH_CHANNEL_ID="$CHANNEL_ID" \
GITHUB_TOKEN="$(gh auth token)" ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
python .claude/skills/discord-ralph-recap/scripts/recap.py --repo your-org/your-repo
```

Useful for backfilling a recap after enabling the bot mid-campaign.

## Troubleshooting

### Error: Discord API request failed: 401 Unauthorized
The bot token is wrong or revoked. Confirm `DISCORD_BOT_TOKEN` is the **bot** token (from the Bot tab), not the application/client secret, and that it is not prefixed with `Bot ` — the script adds that prefix itself.

### Error: Discord API request failed: 403 Forbidden
The bot is not in the server, or lacks **View Channel** / **Send Messages** on `RALPH_CHANNEL_ID`. Invite the bot with the `bot` scope and grant the two permissions on that channel.

### Error: Discord API request failed: 404 Not Found
`RALPH_CHANNEL_ID` is wrong. Enable Developer Mode in Discord, right-click the channel, Copy Channel ID — it is an all-digits snowflake, not the channel name.

### The headline is just the PR title
`ANTHROPIC_API_KEY` is unset or the SDK isn't installed, so the heuristic fallback is used. Add the key and `pip install anthropic` (the bundled workflow already installs it) to get the Claude-written headline.

### Iteration count says "no LGTM verdicts found yet"
No merged PR has a Claude review comment containing a `Verdict` line. Either the reviewer isn't running, or it phrases verdicts differently — see Step 4 and `references/metrics.md`.

### Backlog ETA is "unknown (loop is stalled)"
The merge rate computed to zero — there are no merges in the window, so no rate to extrapolate. This resolves itself once merges resume.

## See Also

- `references/metrics.md` — precise definition and tuning for every number in the recap
- `.claude/skills/address-feedback/` — the per-PR feedback loop this recap aggregates over
- `.claude/skills/await-claude-review/` — how the `Verdict` comments the iteration count reads get produced
