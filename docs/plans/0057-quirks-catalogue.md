# 0057 — Quirks catalogue: the behaviour a faithful reimplementation must keep, in one index

> **Status:** approved (owner, 2026-10-30: "approve all of them", every scoping question answered as recommended); drafted 2026-10-30 (architect, `lane/plans57`)
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
4. **Harness?** *Recommendation: none.* A quirk at `[I]` stays `[I]` (the companion sweep is **owner 2026-10-30: may be drafted, as `draft` only, never started** (no plan after the approved roster is approved or started)), and the companion `[I]` sweep (queued after
   0055·P2a) may take it as a target.
5. **Crash and hang paths** (a read past a table's end, a null unit): *Recommendation: catalogue them from the code
   (`[I]`)*, never provoke them in the harness.

## Open questions

- ~~Whether the index needs a machine-readable form (one line per quirk, class and anchor) for the golden traces of
  plan 0059; decided at the Phase 1 review.~~ **Ruled at the Phase 1 review (2026-10-30): no second file.** The entry
  tables are the form (five fixed cells, parsed by `tools/quirks.py`); the ids are permanent from that review (never
  renumbered or reused, new entries take the next free id) because golden-trace cases cite them in their `quirks` list;
  Phase 3 adds `tools/quirks.py list` (JSON Lines: id, class, tag, anchors, sources) for a consumer to read.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-30 — Drafted (architect, `lane/plans57`).** Status `draft`; rank 1 of the 2026-10-30 batch (cheapest,
  no slot, no open dependency); five owner questions.
- **2026-10-30 — Approved (owner; recorded by the architect, `lane/appr2`).** "Approve all of them": all five questions as recommended: an index row `quirks` that restates and links (the owning spec wins); a quirk is behaviour a reimplementer would plausibly "fix", by the eight classes, plus deliberate oddities; at most 30 community claims in Phase 2; no harness; crash and hang paths catalogued from the code (`[I]`), never provoked. **P1 starts now** (`lane/s57`, spec-writer). Status `approved`.
- **2026-10-30 — Phase 1 done (spec-writer, `lane/s57`).** `docs/specs/quirks/README.md`, status `draft`, research-map
  row `quirks` to `draft spec` (C 334 / I 101 / L 0). The harvest covers all 47 specs with a *Reimplementation notes*
  section (the plan's count said 44), 439 bullets: 410 taken into 435
  entries, 29 skipped (presentation 5, table rule 12, not a trap 9, wall-clock 2, weaker duplicate 1). Entries by class:
  arithmetic width and sign 22, rounding and float 19, wrap and overflow 9, bounds and table edges 67, draw order and
  dead draws 134, data-dependent branches 122, timing and frame edges 19, multiplayer edges 11, deliberate oddities 32;
  7 of them are crash or hang paths, all from the specs' code readings. Step notes beyond the notes sections: player/creation
  § G and § J, monsters/stats § A, stats/states § E, data/calc § D, rng/README § Algorithm. 37 notes (data/calc 4,
  data/excel 11, drlg/lifecycle 8, quests/progression 8, quests/travel 6) carry no tag of their own; the 22 of them taken
  cite the section that holds their tagged form. `tools/quirks.py` (`harvest`, `check`) holds each entry to its source's
  tag and anchors and the coverage table to the notes; it reports 0 errors. Three tag disagreements between overviews and
  the specs that raise the same statement went to the backlog
  ([entry](../backlog/2026-10-30-spec-writer-spec-writer-quirks-harvest-tag-disagreements.md)). The machine-readable
  form stays the open question for the review.
- **2026-10-30 — Phase 1 review (architect, Tier A, `lane/s57`): accept with fixes (17).** Merged `main` first (plan log
  kept both entries; the research-map row keeps main's approval date with the lane's draft-spec status; ledger rows kept
  both). `tools/quirks.py check` 0 errors; its tag test passes any entry whose cited note holds both tags, so all 64 such
  entries were read by hand, with the 22 untagged-note entries, the 12 section-only ones, the 7 crash and hang paths and
  about 30 single-tag entries across the nine classes (about 130 in all). The restatements hold; fixes, written into
  the index: **anchors** (9: wrong anchor 2, omission 7) Q357's anchors were those of the `[I]` clause of save/d2s n9, now § I3's
  (`0x00630A19`–`0x00630CF3`, the two runs) with § I cited; Q318 carried only a table-doc link (the gate's one W1 on the
  page), now `tbl:Runes.txt:Rune1` with § D cited; Q118, Q184, Q223, Q234, Q271 and Q322 had dropped a run or function
  their `[C]` note names, and Q405 the `src:` and `struct:` anchors of player/creation n8; **scope** (3: overclaim 2, other 1) Q25
  the two-member parties of the run, Q89 the fault logged on row 83 only, Q46 "stock data cannot reach it" for a bare
  parenthesis; **source** (1, omission) Q176's "before any other test" is lifecycle § F's step 1, now cited;
  **definitions** (4: misread 2, omission 2) the page's crash-path text said "code readings only" and the lane
  entry above "all from the specs' code readings", but Q89 is a `[C]` fault a kept run logged (six `[I]`, one `[C]`);
  the table-rule skip was described as rules "the table docs already own", while 10 of the 12 are data/excel's and
  data/calc's (the definition now says so and points the loader writer at data/excel's notes whole); Q387 keeps a
  240 000 ms `GetTickCount` test the two wall-clock skips leave out (the definition now scopes the wall-clock skip to a
  note that is only a clock rule, and Q387 says it is one); the page now says which entries the check cannot judge.
  **Rulings:** (1) class boundaries accepted as drawn, including the wide data-dependent class and the comparison
  off-by-ones under bounds; (2) the 29 skips stand, the 12 table-rule ones included (data/excel n3, n6 and n8 are traps,
  but data/excel is the loader's own spec and its notes are read whole); the wall-clock and weaker-duplicate reasons are
  accepted; (3) the three routed tag disagreements are real (combat/README n4 and n5, skills/README n2, anim/README n2
  each keep `[I]` beside a `[C]` of the owning spec) and stay with the spec-writer; (4) merges across specs accepted;
  (5) machine-readable form: no second file, ids permanent, `quirks.py list` in Phase 3 (open question above);
  (6) ADR-0024 passes: the lane touched no finding and no document it does not own beyond its routing entry. Research
  map row rewritten (P1 accepted, P2 next). **P2 may start** (reverser, static). Ledger: architect-review row;
  the lane's usage left to the orchestrator. Categories: overclaim 2, misread 2, omission 10, wrong anchor 2,
  other 1.
