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
  ([entry](../backlog/archive/2026-10-30-spec-writer-spec-writer-quirks-harvest-tag-disagreements.md)). The machine-readable
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
- **2026-11-03 — Phase 1 routing entry: the three tag disagreements fixed (spec-writer, `lane/s63`, from `main`
  `00c53f7f`).** Backlog [2026-10-30-spec-writer-spec-writer-quirks-harvest-tag-disagreements](../backlog/archive/2026-10-30-spec-writer-spec-writer-quirks-harvest-tag-disagreements.md)
  closed. Each overview note split, the clause the owning spec raises stated `[C]` with that spec's anchor and run:
  [combat/README](../specs/combat/README.md#reimplementation-notes) n4 (entries 37, 39, 41 and 143 step once at entry
  `[C]`, ADR-0021, run:2026-10-21-cat-emu-ass, as combat/delivery n9 and skills/dispatch n4; the peek and entry 38
  `[I]`) and n5 (stat 337 drawn at 0 `[C]`, run:2026-10-25-skills, as skills/missiles n3; deadly strike and mastery
  `[I]`): C 41 → 43; [skills/README](../specs/skills/README.md#reimplementation-notes) n2 (stat 337 at 0 `[C]`; "not
  the melee build's" `[I]`): C 23 → 24; [anim/README](../specs/anim/README.md#reimplementation-notes) n2 `[I]` → `[C]`
  (run:2026-10-27-anim, as anim/timing n1, the server's start scoped to L4's cases): C 13 / I 14 → C 14 / I 13. The
  quirks index adds no second version: Q136, Q138 and Q374 now also cite the overview notes, Q140's stat-337 clause
  points at Q138, the anim/README coverage row takes n2 (taken 411 of 439, weaker duplicate 0). `tools/quirks.py
  check`: the one error left (Q3 `skills/catalogue.md` has no coverage row) is on `main` before this lane. Wiki
  `based_on` dates of combat, skills and animation moved to 2026-11-03 (their text already said what the raised
  clauses say). Research-map rows of the three overviews and the quirks row updated.
- **2026-11-03 — `lane/s63` Tier A review (architect): accept with fixes (2)**, both in the player/creation half; this
  entry's three overview notes and the index edits pass unchanged. The review and the Q3 route
  ([2026-11-03-architect-spec-writer-quirks-catalogue-coverage-row](../backlog/archive/2026-11-03-architect-spec-writer-quirks-catalogue-coverage-row.md))
  are in [plan 0038's log](0038-inferred-claims-sweep.md#implementation-log).
- **2026-11-03 — Q3 coverage row: skills/catalogue harvested (spec-writer, `lane/s64`, from `main` `7fddf41d`).**
  Backlog [2026-11-03-architect-spec-writer-quirks-catalogue-coverage-row](../backlog/archive/2026-11-03-architect-spec-writer-quirks-catalogue-coverage-row.md)
  closed. The 8 [skills/catalogue](../specs/skills/catalogue.md#reimplementation-notes) notes, harvested by Phase 1's
  rules: 7 taken, 1 skipped. Nine new entries, each at the end of its class: Q436 (n7, the signed and unsigned tests,
  class 1, C), Q437 (n4, the fatal path `0x00408090` on reachable data, class 4, C, a crash path), Q438 (n1, do 112's
  step before any test, class 5, C), Q439 and Q440 (n2, the draws on a seed not the caster's, class 5, C and I), Q441
  and Q442 (n3, the words read before any write and mhit 52's row-0 missiles, class 9, C and I), Q443 and Q444 (n6, the
  return values, class 9, C and I). No second version: n1's finisher half is Q136 and n8's endless loop is Q50, which
  now also cite the catalogue notes. n5 (identical bodies) is skipped as not a trap: it says which functions share
  code, which a reimplementation built from the catalogue's blocks gets right either way. Index: 444 entries, C 340 /
  I 104 / L 0; coverage 447 notes, 418 taken, 29 skipped (not a trap 10); crash and hang paths 8 (Q437 the second
  reached in a kept run). `tools/quirks.py check` 0 errors. Research-map quirks row counts updated.
- **2026-11-03 — `lane/s64` Tier A review (architect): accept.** Each of the nine entries was read against its
  catalogue note and § table. The tags are the owner's: n2, n3 and n6 split by tag into Q439/Q440, Q441/Q442 and
  Q443/Q444. Q438's "before any test" is the catalogue § draw table's do 112 row and the P2 block's `draw#1`. Anchors
  are copied from the notes. Ids are at the end of their classes. One version only: Q438 holds do 112 alone and points
  to Q136 for prg 37, 39, 41 and 143. Q442 is n3's `[I]` consequence (row 0 by the callee's reading), not a restatement
  of Q441's unwritten words. The three rulings: (1) **n5 skip upheld.** do 152 = do 95, st 59 = st 53 with calc1 for
  calc2, and do 148/149 differing in the monster-data byte (+0x0E or +0x0F) are each stated in the catalogue's own
  block. A reimplementation built from those blocks gets the same behaviour whether or not it shares code, and the one
  difference a merge could lose is the one the blocks spell out. The note is about how the code is organised, not a
  trap. (2) **n3 in class 9 upheld.** A read of a stack slot or struct word no one has written looks like a bug, and a
  careful reimplementer would "fix" it by zeroing. Class 9 is where the index keeps such behaviour (Q74's heap
  over-read sits in class 4 because its trap is the buffer edge, not the stale value). (3) **n8 folded into Q50
  upheld.** n8's rings of prg 37 and 143 and their range 0x005D4657–0x005D467D fall inside combat/delivery n11, which
  Q50 restates. Both are `[I]`, and n11 adds the negative count, so a separate entry would be a second, narrower version
  of the same statement. Counts recounted by script: front matter and by-class (23/19/9/68/137/122/19/11/36, C 340 /
  I 104 / L 0, 444 entries), coverage 48 rows, 447 notes, 418 taken, 29 skipped (presentation 5, table rule 12, not a
  trap 10, wall-clock 2). The crash list has 8 entries (six `[I]` code readings, plus Q89 and Q437 reached in runs dated
  before this plan's approval). The research-map row was rewritten whole and matches. `tools/quirks.py check`: 0
  errors. Gate green, W7 0 warnings, no warning on a touched file. Fixes (0).
- **2026-11-03 — Phase 2 filed (reverser, `lane/r57b`).** [quirks/0001](../findings/quirks/0001-community-bugs.md): 30 claims (the owner's bound) from `src:d2-massive-bug-list` (27), `src:flux-decahedron-9` (2) and `src:pd-gamebreaking-bugs` (1): 19 confirmed, 5 contradicted, 3 not in 1.14d, 3 not found and held `[L]` with reasons. Surprises: a `manahit` boss's factor reads 256, not the page's 512; Hratli's header cause holds and its value (1) does not; no misspelled runeword code remains in the 1.14d table. Static only: no emulation, so no run record. Two pages could not be fetched and are registered as not read, so "next hit always misses" has no claim. [Backlog for the owning specs](../backlog/archive/2026-11-03-reverser-spec-writer-quirks-community-owning-specs.md); [review request](../backlog/archive/2026-11-03-reverser-architect-review-r57b-community-bugs.md).
- **2026-11-03 — Phase 2 Tier A audit (architect, `lane/r57b`): accept with fixes (10).** Audit of the Sonnet check, against objdump of the pinned `Game.exe`. Nineteen rows read (1–8, 11–14, 16–19, 27–29), plus the `[L]` rows' reasons; the anchors say what the rows say except as below. **Counts now 20 confirmed, 4 contradicted, 3 not in 1.14d, 3 not found**; the filed entry above keeps its original count. **Row 11 flipped to `confirmed`:** its `contradicted` cited combat/damage step 3, the player's doubling, while step 10 of the same spec states the monster's (`sub_005A5560_MonCritDouble`, `[C]`, 89 doublings), and its address was the player's. **Row 18 scoped:** "the callers are melee and calc paths" was false, do 74 (Double Throw) adds `SKILLS_GetToHit` to the missile's stat 19 (0x005D8965–0x005D896E). **Row 12 ruling: stays `contradicted`,** since no field counts twice on the `El` path, but the check's `[C]` for "each field once" covered mana and stamina, which delivery B4 holds `[I]`, so it is split again; the life term is a reviewed statement, not this lane's refinement; the one form that can double, a drain already in the packet, is stated with its stock reach. **Row 3 settled:** `not in 1.14d` on all four `Kick` rows; Dragon Talon's hit reaches damage only through `SkillKickPhysDamage`, whose build runs with the weapons' damage stats unlinked (0x005D57DB–0x005D586A), and the off-hand's missing relink is no quirk, stats/aggregate B1 links it without damage already. **Row 19:** the removal is readable (0x005CEFD5–0x005CEFFD), and the owner is do 65, not "none". Rows 4, 13, 17 gain their scopes (the `SkillKickPhysDamage` path, the mana held, record byte `+0x18B`). Held as read: row 13's `256·v` (0x005A20BF–0x005A20DE, 0x0057A8EF, 0x0057C47D–0x0057C486, 0x0057C61D–0x0057C628, 0x0057AA60); stat 137 twice (0x006462A5–0x006462AA, 0x0064639D–0x006463A1, 0x00646431–0x00646436); stat 19 twice (0x0056ED97–0x0056ED9E, 0x0059FE85, 0x005AE05F–0x005AE06F, 0x0057DB93–0x0057DBB6); Smite's forced bit (0x005CEBA8–0x005CEBB0) and mode 5 (0x005CEBB6, mask `0x10` at 0x005A50D0). Rows 9, 23 and 30 state their reasons, and row 30 proposes a reading only, as decision 5 asks. Routes: [the owning-specs entry](../backlog/archive/2026-11-03-reverser-spec-writer-quirks-community-owning-specs.md) corrected; [two reviewed statements](../backlog/archive/2026-11-03-architect-spec-writer-r57b-audit-spec-statements.md) filed. Ledger, for the orchestrator: `audit of lane/r57b: misread 2, under-claim 2, overclaim 1, omission 5; reject-grade missed: yes` (row 11, a reversed verdict with the wrong address under it, readable from the spec alone; row 12's `[C]` with no second source for mana and stamina, written by the check itself). **P3 may start** once this lane is merged, from the corrected finding (spec-writer).
- **2026-11-04 — Phase 3 done (spec-writer, `lane/s68`, from `main` `97651d23`).** Both entries closed: [the audit's two statements](../backlog/archive/2026-11-03-architect-spec-writer-r57b-audit-spec-statements.md) and [the owning specs](../backlog/archive/2026-11-03-reverser-spec-writer-quirks-community-owning-specs.md). **Audit statements, both `[I]`:** combat/damage step 5 shows the drain roll's base, with a step note holding `field + (field + roll) × srcdam ÷ 128` and its below-floor form; combat/to-hit's `arPct` row says 0 for a monster's melee test and the missile's stat 19 for its line missile. **Owning specs, at the finding's tags** (all new statements `[I]` unless marked): skills/catalogue J1 (Blessed Aim and Penetrate), J2 (Smite's forced bit, no flag `0x40`, mode 5), K14 (do 74's to-hit), M2 (do 42 and do 33's level difference); skills/dispatch I4 (stat 137 twice, the weapons' damage stats out of the kick build), L2 (no `noRatio` test); skills/missiles B2 (no to-hit for a player's skill missile), E1 (stat 19 twice); combat/to-hit A2 (stat 19 twice), A6 (the mercenary's stat 117); combat/delivery B4 (`256·v` mana), E1 (stat 36 at 100 or more: `[C]` for the formula, `[I]` for the player's divisor); combat/damage step 10 (the missile's call); monsters/stats B8 (no regeneration at few hit points), § G (pointer to B4); items/tc `MAX_DROP` (`Picks` 7 on the stock boss rows, `[C]`, run:2026-10-12-quality with the table read). **Index:** Q454–Q473, each at the end of its class (class 2 one, class 4 four, class 5 one, class 6 two, class 9 twelve), for the 19 confirmed rows that had no entry; row 15 splits by tag into Q455 `[C]` and Q456 `[I]`; row 11 is the existing Q254, so no second version. Q474 restates the step 5 note: it is not a verdict, but the "does not hold" text of row 12 points at it. A new section *Community claims* gives every one of the 30 verdicts its place, with a "do not hold" table (rows 12, 20, 26, 28 contradicted; 3, 25, 29 not in 1.14d; rows 12 and 20 split by tag) and rows 9, 23, 30 as `[L]` open questions. Index: 474 entries, C 350 / I 124; the page's tags C 355 / I 128 / L 3 with the "do not hold" rows and the open questions. **Tool:** `tools/quirks.py list` (JSON Lines, the Phase 1 ruling), and `check` gains Q4, which holds the community table to the finding's verdicts; a deliberate wrong row was caught before the page was restored. `tools/quirks.py check`: 0 errors, 49 specs, 454 notes, 425 taken (no note added, so the coverage table is unchanged). **Wiki reconciled:** combat, skills, items and monsters gain the new statements in the "read from the code" wording; objects and seed-to-world had nothing stale; `based_on` moved on all six. **For the review:** row 5's entry Q465 restates H4's `[I]` clause, while `a ← 0` itself is H4's `[C]`; the finding's `fn:sub_005DA940_SkillSt06Hit@0x005DA940` is not in that section, so the entry cites `fn:SKILLS_GetToHit@0x006449F0`. The finding's "Owning spec" cells still say "none" for the rows now owned: that document is the reverser's. Status stays `draft spec`, the research map row to `reviewed` at the Tier A review.
- **2026-11-04 — Phase 3 Tier A review (architect, `lane/s68`): accept with fixes (10).** Read against objdump of the pinned `Game.exe` (`631066c1…`), the excel tables and the kept logs. Tags against the finding: every new statement matches; rows 20–26, which the Phase 2 audit did not read, were re-read here (`fade`'s `curse` cell blank, `HratliMagicLvl` the only such header, 508 `T1Code` cells and 0 unknown codes, `TC_GetByIndex`'s unbounded `[ecx+0x2C]`). `Skills.EType` holds no life, mana or stam; Blessed Aim and Penetrate both name `penetrate`; do 74 is Double Throw alone. **Rulings on the lane's flags.** (1) **The floor form is right, and § C1 was the wrong side.** `COMBAT_RollElemStat` takes five stack arguments and no `srcdam`; the no-draw path returns `max(field, 0)` (0x0057A8F7–0x0057A905), and the caller multiplies and shifts whatever comes back (0x0057BA83–0x0057BA93 for the drains; 0x0057B959–0x0057B96A for the elements, behind `srcdam` ≠ 128 at 0x0057B935). `tools/combat.py` models it so; § C1's pseudocode put the scale in the callee and left the first return unscaled, which is wrong for a positive field with no stat. § C1 rewritten, the no-draw scale `[I]`, a note added; step 5's note now says `max(field + roll, 0)` and names the path instead of "the roll's floor". (2) **Q455's `[C]` did not hold as written.** The cut is `[C]` at the values logged; the cap, `cb` = 0, "no branch on the defender's kind" and the player are `[I]`. Survey: `print stat(d, 36)` added to a scratch copy of `tools/combat.py`'s `crushing`, run over `workspace/logs/combat/*.log` (77 logs, 1 856 blows that reached the cut): 0: 1 698, 15: 66, 20: 18, 25: 5, 40: 12, 50: 45, 80: 6, 90: 6; nothing at 100 or more (run:2026-10-16-combat's own list: 316 blows, 0, 15, 20, 40, 50, 90). Those 77 include logs outside any 0-mismatch list (453 mismatches, none read here): the survey is a count of values, not a reproduction. E1 and its pseudocode split, the zero moved from Q455 to Q456, so the class counts and totals stand; wiki/combat follows. (3) **Q457's table read holds, with a scope.** 30 rows have `Picks` 7, the table's largest, all the five act bosses' (plain and quest, three difficulties), and Duriel's are the `- Base` rows under a `Picks` 5 row. Items/tc's `[C]` names them, and an `[I]` holds the other four bosses' rows, which the stop reads no cell of and no logged call of which it decided. (4) **Q465 takes the anchor**, and catalogue H4's `[I]` line with it: the statement is about what `sub_005DA940_SkillSt06Hit` passes (`push 0`, `push 0` at 0x005DA9A5, call at 0x005DA9AF); `SKILLS_GetToHit` alone is the function it does not call. (5) **Q474 stays.** It restates one tagged statement of a reviewed spec and is something a reimplementer would "fix", which is all the index asks; being no verdict matters only to the map row and Coverage, which now say so (20 from the verdicts, Q474 from the step 5 note). (6) **Routed** to the [reverser](../backlog/2026-11-04-architect-reverser-quirks-0001-owning-spec-cells-rows-15-22.md): the "none" cells, row 15's scope, row 22's runs. (7) **Tests written:** `tools/test_quirks.py`, 9 cases over Q4 and `list`. (8) **Yes, that run shows it.** Per-call replay of `tools/tc.py` with `nomax` on the two runs' logs: one deciding call in run:2026-10-12-quality, `Durielq (N)` (class 211, Nightmare, 6 items), and three in run:2026-10-16-quest-drops (`Durielq` twice, `Duriel`), which agrees with items/0001's four. Their rows are all Duriel's, so the first run alone was thin: the statement now names both. **Fixes:** overclaim 3 (E1's cut at 100 or more; `Picks` 7 stated for all five bosses; the drain base under step 5's `[C]` header), misread 1 (§ C1's unscaled return), wrong anchor 2 (Q465; Q457 and items/tc's one run), miscount 2 (wiki/skills' "three skills" for four; the map's "21 from the verdicts"), omission 2 (no test file; Coverage's step-note list without the new sources). Spot checks that held, against objdump: 0x005AD884 (the missile's doubling), 0x005AE04C–0x005AE06F, 0x005CEBA8–0x005CEBB6, 0x005D5AF7, 0x005D31D9–0x005D31E5, 0x0056F42A, 0x005D8965–0x005D896E, 0x005D560F, 0x0057D810–0x0057D847, 0x00573FF6–0x00574058. Wiki: says nothing the specs do not after the fixes; `based_on` reconciled (W4 clean). **`quirks` promoted to `reviewed`.** Totals by recount: index 474 entries, C 350 / I 124; page C 355 / I 128 / L 3. Phase 3's *Done when* is met. Ledger, for the orchestrator: `architect-review`, accept with fixes, overclaim 3, misread 1, wrong anchor 2, miscount 2, omission 2. **Phase 4 may start** once this lane is merged (spec-writer, wiki, Sonnet).
