# 0057 — Quirks catalogue: the behaviour a faithful reimplementation must keep, in one index

> **Status:** draft (architect, `lane/plans57`, 2026-10-30), for the owner's approval
> **Created:** 2026-10-30
> **Owner skill(s):** spec-writer (phases 1, 3, 4), reverser (phase 2)
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0007-fetched-leads-only, 0012-human-wiki, 0015-emulated-reproduction

## TL;DR

Which behaviours of the 1.14d `Game.exe` would a careful reimplementer "fix" by accident, and so must be told to keep?
Off-by-ones, wraps and overflows, signed and unsigned mixes, truncation and float rounding, order-dependent draws,
table reads past an end, unreachable or dead branches that still draw, and the community-known bugs. The reviewed specs
already state most of them, scattered: their *Reimplementation notes* sections hold **439 bullets over 44 specs**
(count of 2026-10-30), plus step notes like player/creation G3's "/256 factors, not percentages". When this plan is
done, `docs/specs/quirks/README.md` (row `quirks`, a cross-cutting index) lists each quirk once, with its class, its
tag, its anchor and a link to the owning spec section; a finding records a verdict for each community-known bug that
was compared; and a wiki page gives the human reading.

## Context

- **No new mechanics.** Every entry restates a tagged statement of a reviewed spec, with the same tag and anchor, and
  links it. The owning spec wins on disagreement, and a disagreement found by the harvest goes to the spec-writer's
  backlog as a fix of the owning spec, not a second version here.
- **Where the pieces live now** (examples, not the list): `rng/README` (unguarded forms, `RangePow2Plus` with no
  caller), `player/creation` G1–G4 (the `0x7FFFFF` clamp, the /256 penalty factors, the overflow branch of the ratio
  shift) and J4 (the party share's f32 quotient and its unrounded f64 product), `monsters/stats` § A (`MulDiv` signed
  and truncating), `drlg/room-tiles` (12 wrap and overflow mentions), `items/economy` (8), `drlg/lifecycle` (8),
  `rng/seeds` (7), `data/calc` (6), `combat/delivery` (the player count in the crushing-blow divisor), `stats/states`
  (stat 74 added whatever its sign).
- **Community bugs** are leads only (ADR-0001, ADR-0007): each is fetched in the lane's session and registered in
  `docs/sources.md` before use. A bug a page names gets a verdict against the code (`confirmed`, `contradicted`,
  `not in 1.14d`, `not found`), never a tag raised on agreement alone.
- **Dependencies:** none open. Every source spec is reviewed. It does not wait on plans 0038, 0046, 0052, 0054 or
  0055; their later raises update the index in Phase 3 or at each later spec promotion (one line per quirk).

## Phases

### Phase 1 — The harvest
- **Owner skill:** spec-writer (Opus; no Ghidra, no slot)
- **What:** read the *Reimplementation notes* and the step notes of every reviewed spec, take each statement that
  describes behaviour a straightforward reimplementation would get wrong, and write it into the index with a class
  (arithmetic width and sign; rounding and float; wrap and overflow; bounds and table edges; draw order and dead draws;
  data-dependent branches; timing and frame edges; multiplayer edges), its tag, its anchor and its link.
- **Outputs:** `docs/specs/quirks/README.md` (spec front matter, tag counts); research-map row `quirks` to
  `draft spec`; backlog entries for any disagreement between two specs the harvest meets.
- **Done when:** every spec with a *Reimplementation notes* section is listed in the index's coverage table with the
  count of its notes taken and skipped (skipped ones by reason: presentation, already a table rule, not a trap), every
  entry links a section that holds the same statement with the same tag, and the gate is green.

### Phase 2 — Community-known bugs, compared
- **Owner skill:** reverser (static; Ghidra optional, emulation under ADR-0015 where a value decides; no slot)
- **What:** fetch and register the community pages that list 1.14d-era bugs and oddities (at most 30 claims, the
  owner's bound, question 3), and give each a verdict against the code and the reviewed specs; a claim the specs do not
  cover is read in the binary.
- **Outputs:** `docs/findings/quirks/0001-community-bugs.md` (one row per claim: the claim, its `src:`, the verdict, the
  anchor, the owning spec section or "none"); `docs/sources.md` rows; backlog entries for owning specs a verdict
  changes.
- **Done when:** every compared claim has a verdict with an anchor; each `contradicted` names the reviewed statement
  that contradicts it; each claim the specs did not cover is `[I]` or better from the code, or `[L]` under the finding's
  open questions with the reason.

### Phase 3 — The verdicts in the index
- **Owner skill:** spec-writer (Sonnet suffices)
- **What:** add the `confirmed` claims to the index under their class (linking the finding until an owning spec takes
  them), and list the `contradicted` ones in a "community claims that do not hold" section.
- **Outputs:** `docs/specs/quirks/README.md`; research-map row `quirks` to `reviewed` at the Tier A review.
- **Done when:** every Phase 2 verdict is either an index entry, a "does not hold" entry or an open question, and the
  gate is green.

### Phase 4 — Wiki page
- **Owner skill:** spec-writer (wiki; Sonnet)
- **What:** `docs/wiki/quirks.md`, the human reading of the index (ADR-0012), no claims of its own.
- **Done when:** the page links every class of the index, and the wiki index lists it.

## Resources and limits

- No harness slot, no headless Ghidra beyond one optional session in Phase 2 (`-Xmx3G`), so it runs beside the two
  static lanes and the two harness lanes. It takes the spec-writer, which is mostly free on 2026-10-30.
- **Estimate** (not measured): P1 one or two spec-writer runs (44 specs, read by section with `grep -n`); P2 one
  reverser run; P3 and P4 one short run each; one Tier A review for P1 + P3 (spec), Tier B for P2 and P4.

## Owner questions (recommendations)

1. **Index or spread?** *Recommendation: an index row `quirks` that restates and links,* with the owning spec winning
   on disagreement. Spreading the classes into each spec is what exists now; the gap is the single list.
2. **What counts as a quirk?** *Recommendation: behaviour a reimplementer would plausibly "fix"*, by the eight classes
   above, plus deliberate oddities that look like bugs. Not included: presentation, wall-clock timing, and table
   values that merely look odd.
3. **How many community claims in Phase 2?** *Recommendation: at most 30*, from two or three fetched pages, most-cited
   first; more can follow as a later batch.
4. **Harness?** *Recommendation: none.* A quirk at `[I]` stays `[I]`, and the companion `[I]` sweep (queued after
   0055·P2a) may take it as a target.
5. **Crash and hang paths** (a read past a table's end, a null unit): *Recommendation: catalogue them from the code
   (`[I]`)*, never provoke them in the harness.

## Open questions

- Whether the index needs a machine-readable form (one line per quirk, class and anchor) for the golden traces of
  plan 0059; decided at the Phase 1 review.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-30 — Drafted (architect, `lane/plans57`).** Status `draft`; rank 1 of the 2026-10-30 batch (cheapest,
  no slot, no open dependency); five owner questions.
