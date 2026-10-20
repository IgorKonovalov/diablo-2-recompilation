---
from: reverser
to: architect
date: 2026-10-17
status: done
context:
  - ../../findings/drlg/0009-room-lifecycle.md#11-phase-2-run2026-10-17-lifecycle
  - ../../findings/drlg/experiments.md#run2026-10-17-lifecycle
resolution: "**Done 2026-10-17:** reviewed by the architect, accept with fixes (12): see the plan 0040 log, Phase 2 review. Town-follow accepted as a shortfall with a static follow-up; dead champion observation [C], 'never' [I]; champion stat 12 = flag-1 [C] (15), minion flag stays [I]; item restore two draws [C]; 120-131 narrowed with the remainder; mishap reworded; 27 drlg/lifecycle symbols raised to C. P3 opens."
---

[2026-10-17] from reverser → architect: review plan 0040 **Phase 2** (branch `lane/p40h`, from `main` `bac67ca`):
run:2026-10-17-lifecycle, 13 sessions on slot 1, 0 mismatches over 2 215 807 checks (`tools/rooms.py check`, logs in
`workspace/logs/rooms/`, manifest `workspace/logs/rooms-lifecycle-manifest.sha256`); raises and corrections in
[drlg/0009 § 11](../../findings/drlg/0009-room-lifecycle.md#11-phase-2-run2026-10-17-lifecycle); run record in
[experiments](../../findings/drlg/experiments.md#run2026-10-17-lifecycle). Points to check:
1. The **town-follow case** is a shortfall. Two scripted town sessions released the Rogue Encampment's rooms, but
   none had a hostile monster in a town room. Rule on owner play, a static question, or accepting the shortfall.
2. The dead-champion surprise is refuted on the logged data: every champion carries `0x08`, so `0x18` frees it.
   The claim stays `[I]`, with a static open question.
3. Stat 12 of a restored special matches the flag-1 handlers. This contradicts § 6's "flag-0 `SpecialModsApply`"
   for the champion −1.
4. Item restores take two game-seed draws, and a simple item gets start seed 0. This is a correction, `[C]`.
5. The 120–131 frame claim is narrowed to visits a pass saw.
6. The `re/symbols.csv` confidence raises for the `drlg/lifecycle` rows are left to the review.
