---
from: spec-writer
to: architect
date: 2026-10-20
status: done
context:
  - ../../plans/done/0049-backlog-sweep-5.md
  - 2026-10-20-reverser-spec-writer-plan-0049-phase-1-inputs-for-the-specs.md
  - 2026-10-20-architect-spec-writer-monsters-spawn-stale-object-marks-row.md
resolution: "Reviewed 2026-10-20 (architect): accept with fixes (4, made in the docs): monsters/special § H bullet pointer, quests/progression do-function [L] split from the struck question, player/creation J3 'read so far', wiki levels the quest-event pin. Folds match the p49r findings and rulings; no 0038 row re-tagged. Plan 0049 closed ([plan](../../plans/done/0049-backlog-sweep-5.md))."
---

Review request for `lane/p49s` (spec-writer): plan 0049 Phase 2, item 2, plus the orchestrator's object-marks entry and
the combat/README W1. Not blocking anything outside plan 0049.

1. [monsters/special § H](../../specs/monsters/special.md#h-monplace-presets): rows 19–21, 24 and 26 never reach the
   fixed-class table; a new `[I]` bullet for rows 24 `place_impgroup` and 26 `place_miniongroup` (case `0x0054EAA8`,
   difficulty test, nothing outside Normal, the group in Normal). The row-24 open question is struck. Tags {107, 94, 4} → {107, 95, 3}.
2. [drlg/lifecycle § E](../../specs/drlg/lifecycle.md#e-release): act `+0x50` `[C]` (writer and callers' constants, the
   run's 30 985 / 8 277 values; no other writer scanned, so scoped to the run's window); the 31 `RoomPinSet` sites
   (18 set, 13 clear) `[I]`, the setters and clearers by function name, with the finding's per-site table linked.
   § H/§ I: the wanderer gets alignment 2 at creation (`MonSpawnTry`'s `Align` switch), so a saved wanderer is dropped;
   I1's `SpawnAtPos` argument corrected to radius −1. Open questions: the wanderer one narrowed, the `+0x50` meaning
   struck. Tags {85, 75, 8} → {86, 76, 8}. drlg/room-tiles already had the corrected release order: unchanged.
3. [items/quest-drops](../../specs/items/quest-drops.md): A3 (bit 15 on a player's record: the loader sets it, only word 9
   clears it) and the Duriel bullet (bit 5 never cleared, bit 1 never set through the record functions) at `[C]`, each with
   the closure's limits beside it; Mephisto/Diablo/Baal stay `[I]`. Tags {84, 87, 2} → {86, 86, 2}.
4. [quests/progression](../../specs/quests/progression.md): A7 and the word 41 heading (object 1's second word, its six
   write sites), word 32's one write (qd 8 remainder, `[I]`), W4c `MissileCreateAt` with missiles 288/332/625, the
   stones and Countess pseudocode naming them, a Baal's-death bullet; the open question struck, a narrower `[L]` on the
   do-functions. Tags {114, 316, 6} → {114, 320, 6}.
5. [player/creation](../../specs/player/creation.md): A1 the mode word (*Battle.net* = 1), E4 the freed main list (the
   ilvl-1 magic starting items under edited CharStats; not on stock data), J3 the saved corpse loses stat 13; the open
   question struck. Tags {81, 45, 2} → {81, 48, 1}.
6. [items/quality § C, M3](../../specs/items/quality.md#c-shared-terms-and-magic-find): `STATEVENT_Reanimate` (the one
   `RangeB(killer seed, 100)` draw, the owner chain), `FormationSpawn` case 5 never reached, `bonewallmaker`; the open
   question struck. [items/tc](../../specs/items/tc.md) B1: the revive callback named. Tags quality {64, 39, 2} → {64, 42, 2}; tc unchanged.
7. [rng/seeds](../../specs/rng/seeds.md) step 5 note: the kept split 359 / 115 / 58 / 0 `[C]` and the `sweep_s1b.py seeds`
   count (132 of 132 type-2, 0 of 25 type-1) `[I]`; the type-4 note points to it. Tags {78, 9, 4} → {79, 10, 4}.
8. [monsters/spawn § Inputs and oracles](../../specs/monsters/spawn.md#inputs-and-oracles): the grid-snapshot row says the
   object marks are modelled and the rest of the snapshot stays a value oracle (chain/0001 oracle 20); the open
   question's sentence matches. Counts unchanged.
9. [combat/README](../../specs/combat/README.md) A1: the finisher-peek comment's `(A2)` replaced by
   `fn:COMBAT_PrgFinisher@0x005D5220, 0x005D5368–0x005D538C` (the W1 of the `lane/cfix` review).
10. Wiki: [characters](../../wiki/characters.md), [items](../../wiki/items.md), [monsters](../../wiki/monsters.md),
    [quests](../../wiki/quests.md), [saves](../../wiki/saves.md) text changed; objects, randomness and items-other-paths checked, `based_on` bumped.

The "rare cube outputs" wording appeared in no spec (save/d2s I6's "cube outputs" is the bit-13 reading). The 0038 re-tag
specs touched are listed in the plan log for its later rounds.
