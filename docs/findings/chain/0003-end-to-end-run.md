# 0003 — The end-to-end run: fresh games from a seed, every act, difficulty and game type

> **Subsystem:** chain (seed to world, plan 0048)
> **Question:** does `tools/chain.py check`, with every Phase 1 model in, reproduce fresh games from known `-seed` values with no seed oracle inside the populations, over the coverage Phase 2 asks for?
> **Date:** 2026-10-21   **Plan:** 0048 (Phase 2)   **Status:** open (Phase 2 run 1; the bar is not met: 2 mismatches, 1 222 of 2 000 populations on the 26 passing logs)

The run is [run:2026-10-20-chain](experiments.md#run2026-10-20-chain): 28 scripted sessions on slot 1, one game each,
logged by `tools/gdb/chain.gdb`, checked together by `tools/chain.py check` (tool revisions in the run's
`tools-final.sha256`). No model changed in this phase; one checker scope changed (§ 3).

## Answer (summary)

- [C] **The composition reproduces 26 of the 28 logs with 0 mismatches**, and the other two fail on one objects-grid
  position test each (§ 2); 1 195 928 monspawn checks with 2 mismatches, 191 475 monstats checks with 0, 2 514
  `TC_ResolveDrops` calls and 1 286 item creations reproduced, 0 failed. (fn:sub_0054EC90_RoomPopulate@0x0054EC90,
  fn:TC_ResolveDrops@0x0055A6D0, run:2026-10-20-chain)
- [C] **Coverage met on the 26 passing logs** (counted at the review without cn4 and cm4, whose counts do not stand
  while each fails): 148 (level, difficulty, game type) built, every generator kind (DrlgType 1: 54, 2: 33, 3: 61),
  every act of each game type in each difficulty (classic acts 1–4 and expansion acts 1–5, in Normal, Nightmare and
  Hell); 8 231 objects created (1 606 by the populate pass, 6 625 presets); 41 champion packs and 108 unique and minion
  packs with 142 special mods rolls predicted; 745 monster drops with an item (843 items) predicted from the dying
  unit's logged seed with no builder oracle. Over all 28 logs: 156 levels, 9 057 objects, 44 and 110 packs, 147 mods
  rolls, 849 drops (951 items). (fn:DRLG_LevelCreate@0x00642AE0, run:2026-10-20-chain)
- [C] **Populations short of the bar**: 1 222 room populations end to end with no oracle on the 26 passing logs (6 584
  creations in them, 41 levels); the 28-log total of 1 385 includes cn4's 117 and cm4's 46, which count only once those
  logs pass. 778 more are needed: at about 50 per 15-minute session, about 16 more sessions. (run:2026-10-20-chain)
- [C] **Oracle 13 is reached and reproduced**: Blood Raven (class 267, raven-xn2) and a flying scimitar (class 234, cn2)
  are created with their `oninit` MonEquip row, the unit seed after `MonEquipInit` predicted by the model, and their
  one item each made by the item chain; `--cf monequip-off` fails both. This is the creation Phase 1 review ruling 2
  named, so the MonEquip model of chain/0002 § 11 is raised to `[C]` **in part**: the path of the two stock rows (one
  row, one location, one item); the level skip, further rows, two or three locations and an occupied location stay
  `[I]`, unreachable with the stock table. (fn:sub_005D6B60_MonEquipInit@0x005D6B60,
  fn:sub_00573B20_MonEquipItemCreate@0x00573B20, run:2026-10-20-chain)
- [C] **Oracle 14 has no remainder on these logs**: 8 588 unit seeds after `SUnitCreate` predicted, of 8 588
  creations. The region appends by a creation outside the model (9) and the creations with no level known (33) are
  counted oracles of the windows they sit in. (fn:sub_00555230_SUnitCreate@0x00555230, run:2026-10-20-chain)
- [C] **Oracles 19 and 20 stay inputs, counted**: 2 470 `LevelRoomCount` reads; every `OG` line's DRLG inputs agree
  with chain/0002 § 7's reading (3 121, 2 470 and 2 351 assertions, 62 gates closed by flags `0x30000`); R3 residue in
  114 of 3 183 pass rooms, by bit in § 4, and every one of the 19 object-bit residue cells has a creation line before
  the snapshot (`OU0`), none unexplained. (fn:OBJ_PopulateGate@0x00552560, fn:LOGIC_BarrierGridBuild@0x0066C870,
  run:2026-10-20-chain)
- [I] **The two mismatches are monsters whose creation marks the model lacks** (corrected at the review): the game's
  test sees `0x100` and `0x1000` (a monster's footprint and centre) where the model has none. `COLL_WHTest` centres
  its rectangle on (x, y), and in both logs the cell where a `MonSpawnTry` request re-created, in mode 3, a monster
  the population pass had made (same unit id, after the room's release and return), in the neighbouring room, lies
  inside the tested rectangle. The log has no `CM` line for a re-created monster's marks and the model applies none,
  so the bits the game reports are those of the monsters at their re-creation cells. No move is needed to explain
  either result (§ 2). (fn:COLL_WHTest@0x0064D800,
  fn:sub_005B2A00_MonSpawnTry@0x005B2A00, run:2026-10-20-chain)

## 1. The sessions

Each session is one fresh game (`d2run.py --seed N`), a waypoint, then the pilot's exploration of that level and the
levels next to it, 15 minutes of wall time from game entry at most. The 28 counted logs, with seeds, levels and game
minutes, are in the run record's table: 6 sessions per difficulty and game type in expansion (5 acts plus the smoke
or raven-xn2 session in Normal), 4 per difficulty in classic. The session plan and why each waypoint was chosen (each
generator kind in each game type) are `tools/chain_sessions.py`'s `PLAN`. [C] All 28 logs are free of gdb's
`internal-error:` and under the 500 MB cap (the largest 17.2 MB). (run:2026-10-20-chain)

The sessions cut short by the 2026-10-20 out-of-memory kill (xm5), the owner's pause (xm2) and the collision logger
error (raven-xn) were re-run on the same seeds; the cut logs are kept as development logs.

## 2. The two mismatches

| Log | Line | Site | Rectangle | Mask | Game | Model | Candidate |
|---|---|---|---|---|---|---|---|
| cn4 | 72971 | `0x005504B3` | (5402, 5241) 8×8, cells 5398–5405 × 5237–5244 | `0x3F11` | `0x1100` | `0x0000` | class 310 (size 2), created at (5398, 5237), mode 3, line 72742 |
| cm4 | 53279 | `0x00550B89` | (7742, 6264) 10×10, cells 7737–7746 × 6259–6268 | `0x3F11` | `0x1500` | `0x0400` | class 189 (size 3), created at (7738, 6260) and (7736, 6262), mode 3, lines 51136, 51152 |

- [C] Both are `COLL_WHTest` calls of the objects model inside a presets window (`RW1` to `RW4`) of a room that is
  activating; each window's other tests and seeds match, and the rest of each log passes. (fn:COLL_WHTest@0x0064D800,
  0x005504B3, 0x00550B89, run:2026-10-20-chain)
- [I] The extra bits are a monster's: `0x100` is the live-monster footprint and `0x1000` a unit's centre (drlg/0005's
  bit table). `COLL_WHTest` with w or h above 1 tests the rectangle from (x − (w >> 1), y − (h >> 1)) (`tools/collision.py
  wh_test`), so each candidate's creation cell is inside it: (5398, 5237) is cn4's top-left cell; cm4's two class-189
  creations' 3×3 footprints overlap its left columns. (Corrected at the review: this bullet first read the rectangle as
  starting at (x, y) and said neither footprint overlaps.) (fn:COLL_WHTest@0x0064D800, fn:COLL_PatternMark@0x0064EA90,
  run:2026-10-20-chain)
- [I] Each candidate is a **re-creation** of a monster the population pass made earlier, after its room came back:
  cn4's unit 522 (class 310) is created at (5398, 5237) in mode 1 at line 64416, then by `MonSpawnTry` requests
  (`MT0` with `a14` = 522, the same request seed `0a325233:31124861` both times, mode 3) at lines 71869 and 72737, each
  after the room's release (`RREL`) and return; cm4's two class-189 units are created in mode 1 at lines 43499 and
  43553 and again in mode 3 at 51136 and 51152. The mode-1 creations have their `CM` `PM` lines (for example lines
  72168–72172 for the class-310 unit at (5445, 5202) created at line 72144); the mode-3 re-creations have none, and the
  objects model applies no mark for them. A monster standing on its re-creation cell gives exactly the game's bits in
  both tests; whether it moved and came back is not shown, and need not be. (fn:sub_005B2A00_MonSpawnTry@0x005B2A00,
  run:2026-10-20-chain)
- Such a test is the first of its kind in the kept logs: a window's rectangle reaching into a neighbouring room that
  holds re-created monsters. Open question 1 is the route.

## 3. Checker scope change: a chest's interact byte

- [C] Three chests reach `OperateFn` 4 with an interact byte that differs from the one their InitFn left, with no
  logged line writing it in between: xm3's classes 183 and 181 (Durance of Hate 2) with the lock bit `0x80` set after
  a creation with 0, and xm5's class 430 created with `0x86`, reaching it with 0. `tools/objects.py` (commit
  `dfe3e5e`) now takes the byte there and counts it by kind, as it does for the checkpoint's xn2 case (the lock bit
  cleared, 3 on these logs); without the change each was a mismatch. The writer is not read. The Phase 1 world logs'
  summary is unchanged by it. (fn:OBJINIT_Chest@0x0054FCB0, run:2026-10-20-chain)

## 4. Oracle 20's residue, by bit

- [C] Of the 3 183 pass rooms, 3 069 have a composed grid equal to the snapshot; the 114 others differ only by bits the
  snapshot has and the model lacks: `0x0080` 136 cells, `0x0100` 119, `0x1080` 34, `0x1100` 30, `0x0400` 16, `0x0800` 5,
  `0x0404` 3. The 19 object-bit cells (`0x400`, `0x404`) each have a creation (`OU0`) before the snapshot, listed with
  the nearest line in the run's `final-o20.json`. (fn:sub_0054EC90_RoomPopulate@0x0054EC90, run:2026-10-20-chain)

## Data touched

No table read is new in this phase; the models' reads are in chain/0002 and the subsystem findings it links.

## Open questions

1. **The marks of a re-created monster** (route ruled at the review): log the `CM` lines of the mode-3 re-creations
   (find the mark call they take, which the `CM` hook does not catch now), model them as for in-pass creations, and
   re-check cn4 and cm4 on their kept logs. A test that
   only a moved monster explains would then be a simulation input (its marks logged), not taken as the test's result.
2. **Who writes a chest's interact byte between its creation and its operate?** (§ 3; four kinds now: lock bit set,
   lock bit cleared, cleared to 0.) Read the writers of the object's interact field reached from the player's
   interaction request.
3. **The 778 missing populations** (615 if cn4 and cm4 pass). About 16 more sessions; the outdoor levels give the most.
