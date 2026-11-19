---
name: walkthrough
description: >-
  Hand-hold the user through a human-action ops ticket (vendor console setup,
  credential provisioning, store or billing configuration) one gated block at
  a time. Use when the user says "walk me through", "/walkthrough", "help me
  do the human action issue", "walk me through setting up the payment
  provider", "provision the OAuth credentials", or names an ops ticket they
  have to click through themselves. Verifies the ticket's claims against HEAD
  and against the vendor's current documentation before giving a single
  instruction, because console UIs drift and issue bodies go stale. Then
  delivers ONE doable block at a time — exact click path or exact command —
  and stops at a gate the user clears by pasting back non-sensitive evidence.
  Do NOT use for coding tickets (use continue-epic), for PR review feedback
  (use address-feedback), or to perform the console steps itself — the whole
  point is that a human holds these credentials.
metadata:
  author: Geoff
  version: 1.0.0
---

# Walkthrough — a human-in-the-loop ops runbook

The user owns the accounts. You own the *sequencing, the verification, and the
proof*. They should never have to hold the whole ticket in their head, guess
which console tab they are in, or wonder whether a step actually worked.

## The three rules that make this useful

1. **One block at a time.** A block is what a person can finish in a sitting
   without switching accounts or waiting on someone else. Never print the whole
   runbook. Never queue two console visits in one block.
2. **Every block ends at a gate.** The user pastes evidence; you confirm it or
   send them back. No "let me know when you're done" — that is not a gate.
3. **Never ask for a secret or PII.** See "Gate safety" below. This is absolute:
   a walkthrough that leaks a client secret into a transcript has done more harm
   than the ticket was worth.

## Instructions

### Phase 0 — pick the ticket and read it whole

Human-action tickets are usually marked by a title prefix or label — check the
repo's conventions (`gh label list`); `[HUMAN ACTION]` is a common one.

```bash
gh issue list --state open --search "HUMAN ACTION in:title" --json number,title
gh issue view <N> --json title,body,labels,comments
```

Read the **entire** body and every comment before saying anything. These tickets
often carry audit notes in comments that supersede the original text.

If the user named no ticket and there is more than one, list them with a
one-line "what this unlocks" each and ask which. That is the one question worth
asking up front.

### Phase 1 — verify before you instruct

**Do not skip this and do not do it silently.** Two independent checks:

#### 1a. Does the repo still match the ticket?

Check every file, env var and symbol the ticket names. Issue bodies routinely
describe architecture that has since moved. An ops ticket sending the user to
create a credential for a variable the code no longer reads wastes an afternoon
in someone else's console.

```bash
grep -rn "OAUTH_CLIENT_ID" --include='*.py' --include='*.ts' --include='.env*' .
git log -1 --format='%h %cr' -- <file the ticket names>
```

#### 1b. Do the vendor's docs still match the ticket?

**Console UIs change and the ticket may be a year old.** Before you tell the
user to click something, confirm the path exists *today* with
WebSearch/WebFetch against the vendor's own documentation (cloud console,
app-store developer portal, payment provider, hosting platform). Prefer the
vendor's docs over blog posts and over your own memory.

Report what you checked, with URLs. When the ticket and the live docs disagree,
say so plainly and follow the docs — then note it on the ticket at close-out.

**If you cannot verify a step, say "I could not confirm this path" rather than
inventing a menu item.** A wrong click path in a billing or credentials console
is worse than an admission.

### Phase 2 — show the map, then start

Give the user, in one short message:

- **What this unlocks** in one sentence (why bother).
- **The blocks**, numbered, each with a rough time and what account it needs.
- **What they'll need open** — which accounts, any card, any device.
- **Where it can't be undone**, if anywhere. Publishing an OAuth consent screen,
  taking a product live, rotating a token other things use: flag these *before*
  they start, not in the block.
- **Anything genuinely blocked** on a decision only the user can make (naming a
  bundle ID, choosing a price). Ask those now, not mid-flow.

Then start block 1. Do not wait for permission to begin.

### Phase 3 — deliver one block

Each block is one message: a title with block number, time and console; a
one-line **Why**; numbered **Do this** steps; an explicit "do NOT paste me X"
where a secret appears on screen; and a **Gate** stating exactly what to paste
back. See Example 1 for the full shape.

Writing good instructions:

- **Name the exact UI label in bold**, as it appears on screen today.
- **Deep-link where a deep link exists.** A direct console URL beats "navigate
  to APIs & Services then Credentials".
- **Say which account/project/org**, every time. Wrong-project is the single most
  common way these go sideways.
- Prefer a **terminal command** to a click whenever the vendor has a CLI
  (`gh secret set`, the hosting platform's `variables` command, a store CLI).
  Commands are copy-pasteable, verifiable, and produce a gate for free.
- If a step takes minutes to propagate (DNS, store builds, consent screen
  review), **say so** and make the gate check the effect rather than the click.

### Phase 4 — gate safety (the part that matters most)

**Never ask the user to paste:**

- client secrets, API tokens, private keys, `.p8` / `.pem` / keystore files
- webhook signing secrets, session cookies, bearer tokens, recovery codes
- passwords, 2FA codes, or anything from a password manager
- full customer records, real email addresses, or anything identifying a user
- screenshots of a console page that also shows any of the above
- the *value* of any variable named `*_SECRET`, `*_TOKEN`, `*_KEY`, `*_PASSWORD`

**Prefer gates that prove the effect without revealing the value.** In order of
preference:

1. **A command that checks presence, not content.**
   ```bash
   <platform-cli> variables --json | jq 'keys'   # names only
   [ -n "$PAYMENT_API_TOKEN" ] && echo SET || echo UNSET
   echo -n "$SECRET" | wc -c                     # length, not value
   ```
2. **An external observation of the effect.**
   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' https://<api>/health
   gh api repos/<owner>/<repo>/actions/secrets --jq '.secrets[].name'
   ```
3. **A public identifier** — an OAuth client ID, a bundle ID, a product
   permalink. These already ship in client bundles; they are safe.
4. **A quoted UI string** — "paste the green banner text" — when nothing else
   is available.

If the only possible proof is sensitive, **redesign the gate**: ask for a
derived fact (length, prefix, last 4, exit code, HTTP status). If even that is
not possible, say "I can't verify this one without a secret, so I'm trusting
you — tell me it's done" and mark it *unverified* at close-out. Be honest that
it is weaker.

### Phase 5 — clear the gate

- **Passed:** say what the evidence proves in one line, then go straight to the
  next block. No ceremony.
- **Failed or ambiguous:** do not advance. Say exactly what you expected versus
  what you saw, give the single most likely cause, and give one corrective
  action. Never say "try again".
- **Unexpected output:** treat it as information about the world, not as the
  user making a mistake. Vendor UIs change; your instruction may be the wrong
  thing. Re-check the docs before blaming the paste.

### Phase 6 — close out

When every block is cleared:

1. **Tick the ticket's acceptance criteria** that are genuinely met, and say
   plainly which are not. Never tick one you did not verify.
2. **Comment on the ticket** with: what was provisioned, which values live where
   (names only — never values), anything that diverged from the ticket, and
   anything left undone with why.
3. **Correct the ticket body** where the live docs contradicted it, so the next
   person is not misled.
4. **Close it** only if every AC is met. Otherwise leave it open with a comment
   saying exactly what remains, and file a follow-up for anything new you found.
5. **Say what changed for the product** in one line — "social sign-in is now
   live on web; iOS needs a fresh store build" — so the user knows what to go
   look at.

### When to stop and ask

- A step **costs money** or changes a plan tier.
- A step is **irreversible and unverifiable** beforehand (publishing a consent
  screen, taking a product live, rotating a token other systems use).
- The ticket's premise turns out to be **false** — stop, report, and offer to
  correct the ticket rather than improvising a path it never specified.
- Anything touching **a real customer's data**.

## Examples

### Example 1 — One block, in full

> **Block 3 of 6 — Create the Google Web client ID** *(~5 min, Google Cloud Console)*
>
> **Why:** this is the only client ID the web app needs, and web ships without a
> store build — so this is the fastest path to a visible working button.
>
> **Do this:**
> 1. Go to https://console.cloud.google.com/apis/credentials (project selector
>    top-left — make sure it shows your app's project, not a personal one).
> 2. **+ Create credentials** → **OAuth client ID**.
> 3. Application type: **Web application**.
> 4. Authorised JavaScript origins → **+ Add URI** → `https://<your-app-domain>`
> 5. Authorised redirect URIs → **+ Add URI** → `https://<your-app-domain>`
> 6. **Create**. A dialog shows the client ID and client secret.
>
> **Do NOT paste me the client secret.** You do not need it for this flow and I
> will not ask for it at any point.
>
> **Gate — paste this back:**
> ```
> the Client ID only (it ends in .apps.googleusercontent.com)
> ```
> It is a public identifier that already ships inside the web bundle, so it is
> safe here. If you would rather not, paste just the last 12 characters and I
> will work with that.

### Example 2 — Ticket premise is stale

User: "walk me through the webhook setup ticket"

Phase 1a finds the ticket asks for `PAYMENTS_WEBHOOK_SECRET`, but `grep` shows
the code now reads `BILLING_WEBHOOK_SECRET` (renamed two months ago per
`git log`). Do not start block 1. Report the mismatch with the `file:line`
that reads the new name, offer to correct the ticket body, and only then show
the map with the corrected variable name.

### Example 3 — Gate redesigned around a secret

The block sets an API token as a hosting-platform variable. Instead of asking
for the token, the gate is: "run `[ -n \"$PAYMENT_API_TOKEN\" ] && echo SET`
in the deployed shell and paste the output, then paste the HTTP status from
`curl -s -o /dev/null -w '%{http_code}' https://<api>/billing/health`." `SET`
plus a `200` proves the effect without the value ever touching the transcript.

## Troubleshooting

### The user pastes a secret anyway
Tell them immediately, in the next message, that it appeared in the transcript
and should be rotated. Do not quietly continue. Do not repeat the value back.
Add the rotation as its own block before resuming.

### The user goes quiet mid-walkthrough and comes back later
Re-establish state from the last cleared gate before continuing — do not assume
the intervening blocks happened. Ask for the gate evidence of the next block
if they say they did it on their own.

### The console doesn't show the menu item you named
The UI drifted. Stop, re-check the vendor docs (Phase 1b), and reissue the
block with the current path. If the docs don't settle it, ask for a
description or screenshot of what *is* on screen (with secrets cropped) rather
than guessing a second time.

### No human-action ticket exists, just a verbal request
Run the same phases against the request itself: verify the repo (1a) and the
docs (1b), show the map, and offer to file the ticket at close-out (via the
flare skill) so the provisioning is recorded.
