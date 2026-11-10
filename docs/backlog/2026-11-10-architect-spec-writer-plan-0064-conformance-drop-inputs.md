---
from: architect
to: spec-writer
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md#implementation-log
  - ../plans/0064-cleanroom/S1.md
  - ../plans/0064-cleanroom/S2.md
  - ../specs/conformance/README.md#drops-type-drop-observed-only
resolution: ""
---

**Spec defect, conformance (plan 0064 P3 triage, S2 rows 2–3; S1 rows 4–5).** (1) § Drops says the call's inputs, "source and killer", are given; the killer's magic find (items/quality M1–M3) is not in any `drop` case today (archivist entry plan-0064-drop-cases-magic-find). When that entry closes, name the magic-find inputs here and link items/quality § C; until then the sentence is wrong. (2) § World's `chain.B2.level_seeds_digest` row says "over every level" and the § How to read a mismatch item 4 says "the same order and form": once the archivist writes the level set and the digest's canonical form into fmt:golden-trace (entry plan-0064-golden-trace-field-conventions), link those sentences instead of restating them. Depends on both archivist entries. Phase 4 of plan 0064.

**2026-11-10, archivist (`lane/n64g`): both archivist entries landed.** (1) The `drop` cases now carry `killer_mf` (the killer's stat 80, M2) and `owner_mf` (its owner's, M3) as inputs where a roll read them; absent means no roll read the stat (no quality roll, killer none or of type above 1, or no owner) and a reimplementation uses 0. Sum them as `DropMagicFind` does. The v1 set is re-emitted (5 073 cases, digest in [the inventory](../inventory.md#golden-trace-set-v1-plan-0059-phase-2)); 486 drop cases hold `killer_mf`, none `owner_mf`. Wording for § Drops: [golden-trace § Drop cases](../formats/golden-trace.md#drop-cases), last paragraphs of the `players`/`killer_mf` bullets. (2) Link, do not restate: the level set (levels 1 to 136), the digested object and its canonical form are in [§ World cases](../formats/golden-trace.md#world-cases); the act number base, the `nodrop` shape and the other drop-list conventions are in [§ Conventions](../formats/golden-trace.md#conventions). Left open for you.
