---
name: graph
description: >-
  Query a repo's graphify knowledge graph to orient before reading code: what
  connects two modules, the impact of changing a symbol, a plain-language
  explanation of a node, or the graph's freshness/status. Use when the user
  says "query the graph", "what connects X and Y", "impact of changing X",
  "what depends on X", "is the graph fresh", "/graph", "record the graph
  outcome", or wants a graph-first answer instead of a blind file sweep, in
  any repo that ships or can build a graphify graph. Wraps the graphify
  query, path, explain, affected, save-result, and reflect subcommands plus a
  graph-meta.json freshness check, and uses a federated pan-graph.json when
  one is present. Do NOT use to file bugs or features (use flare), to run
  code-quality or slop audits (use de-slopify), or to build or refresh the
  graph itself (run the repo's graph build/update scripts or graphify
  extract).
metadata:
  author: Geoff
  version: 1.1.0
---

# Graph

Answer a codebase question from the knowledge graph before sweeping files by
hand. This skill is a thin, accurate wrapper over the `graphify` CLI (PyPI
package `graphifyy`) and the graph's provenance metadata — it never
duplicates the CLI reference; `graphify --help` and the repo's own graph
README (commonly `scripts/graph/README.md`) are canonical.

## Instructions

### Step 1 — Pick the graph, restore it if missing

Read subcommands default to `graphify-out/graph.json`. If the repo also has
a federated graph — `graphify-out/pan-graph.json`, which merges several
related repos into one — prefer it for cross-repo questions by passing
`--graph`:

```bash
GRAPH=graphify-out/graph.json
[ -f graphify-out/pan-graph.json ] && GRAPH=graphify-out/pan-graph.json
```

If neither file exists, the graph has not been restored. Check, in order:

1. **The repo's CLAUDE.md** — it usually names the restore command. Many
   repos restore automatically from a SessionStart hook; if
   `.claude/hooks/session-start.sh` exists, read what it fetches.
2. **A published release.** Repos that git-ignore `graphify-out/` often
   publish the graph as assets on a rolling GitHub release (commonly tagged
   `knowledge-graph`):

   ```bash
   gh release download knowledge-graph --pattern graph.json --dir graphify-out
   gh release download knowledge-graph --pattern 'graph-meta.json' --dir graphify-out
   gh release download knowledge-graph --pattern 'pan-*.json' --dir graphify-out  # only if a federated graph is published
   ```

3. **A committed graph.** Small repos sometimes commit
   `graphify-out/graph.json` in-tree; then it is already present.
4. **Build locally.** Use the repo's script if it has one
   (`./scripts/graph/build.sh`), otherwise the keyless AST pass:

   ```bash
   pip install graphifyy && graphify extract . --code-only
   ```

If you cannot get a graph at all, say so and fall back to Grep/Glob rather
than inventing an answer.

### Step 2 — Choose the verb

| Question | Command |
| --- | --- |
| "what does X do / what's near it" | `graphify explain "X" --graph "$GRAPH"` |
| "how do A and B relate" | `graphify path "A" "B" --graph "$GRAPH"` |
| "what depends on X / blast radius" | `graphify affected "X" --graph "$GRAPH"` |
| open-ended "where is Y handled" | `graphify query "<question>" --graph "$GRAPH"` |
| "is the graph present / fresh" | read `graphify-out/graph-meta.json` (Step 3) |

`query` caps output with `--budget N` (default 2000 tokens); `affected` takes
`--depth N` and `--relation R`. Run `graphify <verb> --help` for the full
flag set — do not guess flags. Some repos also keep a separate docs graph
(e.g. `graphify-out/docs-graph.json`); pass it with `--graph` for product or
decision questions when the repo's CLAUDE.md says one exists.

### Step 3 — Status is a metadata read, not a subcommand

graphify has no `status` subcommand. Report graph status by reading the
provenance file `graphify-out/graph-meta.json` (or `pan-meta.json` for a
federated graph) when the repo's build writes one. It typically records
`built_at`, `sha`, `kind` (`code-only` | `code+semantic` | `pan-graph`),
node/edge counts, and the pinned `graphifyy` version:

```bash
cat graphify-out/graph-meta.json   # or graphify-out/pan-meta.json
```

Report presence, `kind`, the `built_at` age, and the `sha` the graph was built
from; compare `sha` with `git rev-parse HEAD` to say how far behind it is. If
`graph.json` exists but no meta file does, it is a local, un-provenanced build
— fall back to the file's mtime and say so rather than claiming a release
identity. If `pan-graph.json` is present but `pan-meta.json` is not, use
`graph-meta.json` for freshness.

### Step 4 — Cite `source_location`, treat hits as leads

When you state a fact from the graph, quote the node's `source_location` so it
is verifiable (`file:line`). The graph is a lead generator, not proof: for
anything you will act on, confirm the finding by reading the cited code before
editing or reporting it as certain.

### Step 5 — After code changes, refresh the graph

If you have just modified code and want a current graph, refresh it with the
repo's incremental script if it has one (e.g. `./scripts/graph/update.sh`,
AST-only, no cost), otherwise re-run `graphify extract . --code-only`. This
skill queries the graph and records query outcomes; building and refreshing
the graph itself belong to the repo's graph tooling.

### Step 6 — Record the outcome (optional memory loop)

Do this only when the repo keeps a committed graph memory directory (look for
`graph/memory/` or whatever its graph README names). When a graph-backed
answer proves out (tests pass / review LGTM) or misleads, leave a durable
trace so later sessions learn from it. Entries are small Markdown files with
YAML frontmatter (`type`, `date`, `contributor`, `outcome`, `source_nodes`),
written to the committed memory dir — never the git-ignored
`graphify-out/memory/`:

```bash
graphify save-result --question "…" --answer "…" --type query \
  --nodes NodeA NodeB --outcome useful --memory-dir graph/memory/
# wrong turn: --outcome dead_end
# graph was wrong: --outcome corrected --correction "the right answer was …"
```

Then regenerate the deterministic digest (no LLM, no cost) and commit both:

```bash
graphify reflect --memory-dir graph/memory --out graph/reflections/LESSONS.md
```

Record repo Q&A only — never user data or secrets. If the repo runs a
secret scanner in pre-commit, it must cover the memory dir.

## Examples

### Example 1 — Blast radius before a refactor
User: "what depends on `parse_config`? I want to change its signature."

```bash
graphify affected "parse_config" --graph graphify-out/graph.json
```

Report each dependent with its `source_location`, then read the top callers to
confirm the signature change is safe before editing.

### Example 2 — How two modules connect
User: "what connects the auth router and the session store?"

```bash
graphify path "auth router" "session store" --graph graphify-out/graph.json
```

Summarize the shortest path (the intermediate calls/imports), quoting each
node's `source_location`.

### Example 3 — Is the graph fresh enough to trust?
User: "/graph status"

Read `graphify-out/graph-meta.json`, then answer with presence, `kind`
(code-only vs code+semantic), the `built_at` age, how many commits its `sha`
trails HEAD, and whether a `pan-graph.json` is also present. If it is stale
(older than ~48h or many commits behind) or absent, say so and offer to
restore it (Step 1) or rebuild it (Step 5).

## Troubleshooting

### `graphify: command not found`
The CLI is not installed in the active environment. If the repo pins it
(e.g. `scripts/graph/requirements.txt`), install from that pin with the
repo's virtualenv active; otherwise `pip install graphifyy`. Note the PyPI
name has a double `y`; the command is `graphify`.

### The graph is missing or stale
See Step 1: restore it from the release or rebuild locally. Never answer from
a graph you could not load — fall back to Grep/Glob and say the graph was
unavailable.

### A node name returns nothing
Node labels are the extractor's names (function, class, file), not prose.
Try the exact symbol, the file name, or an open-ended `graphify query` to
discover the label, then retry `path`/`affected` with it.

### The user wants to file an issue or fix quality, not query
Stop and hand off: filing a bug/feature is the `flare` skill; a code-quality
or slop audit is the `de-slopify` skill. Recording a query outcome to the
memory dir is in scope (Step 6); filing issues and editing source are not.

### Looking for a `status` subcommand on the CLI
graphify has none for the graph — the only `status` it exposes is `hook
status` (git-hook wiring). Graph freshness comes from reading
`graph-meta.json` (Step 3), not from the CLI.
