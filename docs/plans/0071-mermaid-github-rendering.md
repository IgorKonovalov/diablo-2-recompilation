# 0071 — Mermaid blocks that pass gate rule E17 but GitHub refuses to draw

> **Status:** approved (owner, 2026-11-19: "2 approved"). Phase 1 is the owner's and comes first; no lane
> starts before its results are recorded.
> **Created:** 2026-11-18
> **Owner skill(s):** human (Phase 1), archivist (Phase 2), spec-writer (Phase 3a), reverser (Phase 3b),
> archivist (Phase 3c)
> **Related ADRs:** 0006-docs-gate, 0012-human-wiki

## TL;DR

**Question:** why does GitHub show "Unable to render rich display" for Mermaid blocks that gate rule E17 passes,
and what has to change, in the blocks or in E17, so that the gate fails on what GitHub refuses? The owner reported
it on 2026-11-18, with the first block of [`docs/wiki/levels.md`](../wiki/levels.md) (a `flowchart TD`) as the
example. E17 (`tools/mermaid_render.mjs`, `tools/mermaid_lint.py`) draws each block as GitHub would, with GitHub's
Mermaid version pinned. It passes that block. Either the gate's model of GitHub has drifted or the fault is outside
the repository.

When this plan is done:

- the cause is recorded here, from GitHub's own error text;
- `python3 -I tools/mermaid_lint.py` fails on the blocks GitHub refuses, and a fixture under
  `tools/gate/fixtures/` keeps that true;
- every block GitHub refuses is rewritten, and the gate is green;
- or, if the cause is outside the repository, the plan says so and closes after Phase 1 with only a note in the
  diagram conventions.

## Context

- **Why now:** diagrams are the wiki's main illustrations (ADR-0012), and plan 0070's export carries the same
  blocks. A diagram GitHub refuses is lost to every reader of the pushed repository.
- **Research map:** no row. This is gate tooling and presentation; no subsystem's status moves.
- **Scale, by `grep -c '^```mermaid'` on 2026-11-18:** 481 blocks in 132 files. `docs/specs/` holds 349 in 65 files,
  `docs/wiki/` 76 in 20, `docs/findings/` 45 in 38, `docs/formats/` 10 in 8 and `docs/tables/` 1 in 1. How many of
  them GitHub refuses is not known (Phase 1).
- **Observations by the main session on 2026-11-18,** before this plan:
  1. The pushed `docs/wiki/levels.md` is byte-identical to the local one: sha256 `415fd0cf…`, the same from
     `raw.githubusercontent.com` and from the working tree. So the fault is not a fix waiting to be pushed.
  2. `python3 -I tools/mermaid_lint.py docs/wiki/levels.md` printed "6 blocks, 0 failed" with the pinned
     `MERMAID_VERSION = "12.2.0"` (`tools/mermaid_render.mjs:31`).
  3. A scratch copy of `mermaid_render.mjs` pinned to **12.3.0** (npm, published 2026-11-03) drew the same six blocks
     with no failure.
  4. A copy pinned to **13.0.0-alpha.3** gave `{"skip":"browser run failed: no result in 240000 ms"}`. That is a
     skip, not a verdict on the blocks. The likeliest reason, *unverified*, is that the 13.x package keeps its bundle
     at a different path than the one the fetch step reads.
- The first block holds plain ASCII, quoted labels, an `A & B & C --> D` fan-in and edge labels `-->|"2"|`. None of
  these is on the E17 list of known traps (`.claude/skills/spec-writer/references/pseudocode-conventions.md`
  § Diagrams).
- The renderer pin is dated "what GitHub's diagram frame ran on 2026-11-04". Nothing re-checks it, so it can drift
  silently. That is the gap Phase 2 closes, whatever the cause turns out to be.

### Hypotheses

| # | Cause | What it predicts | Settled by |
|---|---|---|---|
| H1 | GitHub's frame moved past 12.3.0 (a 13.x build), and 13.x rejects what 12.x accepts | the error text names a version above 12.3.0 and a parse error; many pages fail, on the same constructs | Phase 1 error text, then Phase 2 |
| H2 | GitHub changes the text before Mermaid sees it in a way `GITHUB_DECODE` does not copy | the error names 12.x and a parse error at a line that parses locally | Phase 1 error text, then a minimal block in Phase 2 |
| H3 | the frame itself fails: a GitHub-side outage, or the browser blocks `viewscreen.githubusercontent.com` (an extension, a privacy setting) | no parse error, or a load or timeout message; Mermaid on other repositories fails too | Phase 1 steps 2 and 3 |
| H4 | a page-level limit (diagram count, page size) | only long pages with many blocks fail, and short ones draw | Phase 1 step 4, then bisection in Phase 2 |

## Phases

Order: the owner's observation first (no agent can see GitHub's frame), then the gate tool, then the blocks.

### Phase 1 — Capture GitHub's verdict
- **Owner skill:** human
- **What:** record GitHub's error text and the failure's extent, so that one hypothesis is left standing.
- **Steps (an estimate: about 10 minutes):**
  1. Below two or three failing boxes on different pages, copy the error text word for word, the
     `mermaid version X.Y.Z` line included.
  2. Reload, then open the page in a private window or another browser. Does the box persist?
  3. Open a Mermaid diagram in another public repository. Does it draw?
  4. List the failing wiki pages, and for each one say whether every block fails or only some.
- **Outputs:** the *Phase 1 results* section of this plan, filled in.
- **Done when:** the results name the version GitHub reports (or no parse error), and the architect has written
  which hypothesis they leave standing into the implementation log. **Under H3, the plan closes here:** add one line
  to `pseudocode-conventions.md` § Diagrams ("Unable to render rich display" with no parse error is GitHub's frame,
  not the block), then move the plan to `done/`.

### Phase 2 — Make E17 fail where GitHub fails
- **Owner skill:** archivist (Sonnet, a tools writer lane; Tier B lane check)
- **What:** change `tools/mermaid_render.mjs` until it refuses the Phase 1 blocks, then sweep the tree.
- **By hypothesis:**
  - H1: bump `MERMAID_VERSION` and `MERMAID_INTEGRITY` to the version GitHub reports. If its package keeps the bundle
    elsewhere, teach the fetch step the new path; that would explain observation 4.
  - H2: copy the transform in `GITHUB_DECODE`, or in a step next to it.
  - H4: find the limit by bisecting one failing page, and add it as a per-file check.
  - Every case: accept `MERMAID_VERSION_OVERRIDE` with a matching `MERMAID_INTEGRITY_OVERRIDE`, so a candidate
    version can be tried without editing the file.
- **Outputs:** `tools/mermaid_render.mjs`; one fixture in `tools/gate/fixtures/` that fails E17 for the found cause
  (and that passed before the change); `tools/test_gate.py` covering it; the sweep's failing-block list, grouped by
  construct, in the lane's scratch area and summarised in the implementation log (count per folder, construct
  names).
- **Done when:** `python3 -I tools/mermaid_lint.py docs/wiki/levels.md` fails on the blocks Phase 1 named;
  `python3 -I tools/test_gate.py` passes, the new fixture included; and the sweep's per-folder counts are in the log.
  The gate stays red on the swept blocks until Phase 3, so this lane lands together with Phase 3a on one branch, or
  behind a reviewed temporary waiver. The architect rules which, at the Phase 2 check.

### Phase 3a — Rewrite the refused blocks in specs and wiki
- **Owner skill:** spec-writer (Opus; Tier A review per ADR-0023)
- **What:** rewrite every block from the Phase 2 list under `docs/specs/` and `docs/wiki/`, applying one rewrite
  rule per construct.
- **Outputs:** the touched specs and wiki pages; one rule per construct added to `pseudocode-conventions.md`
  § Diagrams, next to the existing E17 traps.
- **Done when:** `mermaid_lint.py` is clean over `docs/specs/` and `docs/wiki/`, and the gate is green. The review
  diffs the node and edge text of every rewritten block, and none of them states anything the prose beside it does
  not (CLAUDE.md: a diagram carries no claim of its own). No `based_on` or tag changes, because no statement
  changes.

### Phase 3b — Rewrite the refused blocks in findings
- **Owner skill:** reverser (Sonnet, mechanical; Tier B lane check)
- **What:** apply the Phase 3a rules to the listed blocks under `docs/findings/`. Skip this phase if the list holds
  none there.
- **Outputs:** the touched findings.
- **Done when:** `mermaid_lint.py` is clean over `docs/findings/`.

### Phase 3c — Rewrite the refused blocks in formats and tables
- **Owner skill:** archivist (Sonnet, mechanical; Tier B lane check)
- **What:** the same for `docs/formats/` and `docs/tables/`. Skip this phase if the list holds none there.
- **Outputs:** the touched format and table docs.
- **Done when:** `python3 -I tools/mermaid_lint.py` with no path argument (every tracked `.md`) reports 0 failed.
  The owner pushes and confirms that the Phase 1 pages draw on GitHub. That confirmation closes the plan.

## Open questions

- Which version GitHub's frame runs today (Phase 1).
- Whether E17 should check the pin against GitHub on a schedule. Deferred: no poller. The owner's eye on the pushed
  page stays the trigger, and the override in Phase 2 makes the follow-up check cheap.
- Whether plan 0070's export site, which draws Mermaid with its own version in the export repository's CI, has the
  same problem. Out of scope here. If Phase 1 lands on H1, the architect files a backlog entry against 0070.

## Phase 1 results

_(the owner fills this in: the error text, the browser checks, the failing pages)_

## Implementation log

- 2026-11-18 — drafted by the main session from the owner's report and observations 1–4. Re-cut to the plan
  template by the architect the same day: one owner per phase, Phase 3 split by doc owner, the gate note moved to
  the spec-writer's diagram conventions, the scale counted, and the 13.x path explanation marked unverified.
- 2026-11-19 — approved by the owner ("2 approved"); recorded by the main session. Waiting on Phase 1.
