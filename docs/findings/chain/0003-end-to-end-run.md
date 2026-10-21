# 0003 — The end-to-end run: fresh games from a seed, every act, difficulty and game type

> **Subsystem:** chain (seed to world, plan 0048)
> **Question:** does `tools/chain.py check`, with every Phase 1 model in, reproduce fresh games from known `-seed` values with no seed oracle inside the populations, over the coverage Phase 2 asks for?
> **Date:** 2026-10-21   **Plan:** 0048 (Phase 2)   **Status:** open (Phase 2 run 1; the bar is not met: 2 mismatches, 1 385 of 2 000 populations)

The run is [run:2026-10-20-chain](experiments.md#run2026-10-20-chain): 28 scripted sessions on slot 1, one game each,
logged by `tools/gdb/chain.gdb`, checked together by `tools/chain.py check` (tool revisions in the run's
`tools-final.sha256`). No model changed in this phase; one checker scope changed (§ 3).

## Answer (summary)

- [C] **The composition reproduces 26 of the 28 logs with 0 mismatches**, and the other two fail on one objects-grid
  position test each (§ 2); 1 195 928 monspawn checks with 2 mismatches, 191 475 monstats checks with 0, 2 514
  `TC_ResolveDrops` calls and 1 286 item creations reproduced, 0 failed. (fn:sub_0054EC90_RoomPopulate@0x0054EC90,
  fn:TC_ResolveDrops@0x0055A6D0, run:2026-10-20-chain)
- [C] **Coverage met**: 156 (level, difficulty, game type) built, every generator kind (DrlgType 1: 56, 2: 33, 3: 67),
  every act of each game type in each difficulty (classic acts 1–4 and expansion acts 1–5, in Normal, Nightmare and
  Hell); 9 057 objects created (1 817 by the populate pass, 7 240 presets); 44 champion packs and 110 unique and minion
  packs with 147 special mods rolls predicted; 849 monster drops with an item (951 items) predicted from the dying
  unit's logged seed with no builder oracle. (fn:DRLG_LevelCreate@0x00642AE0, run:2026-10-20-chain)
- [C] **Populations short of the bar**: 1 385 room populations end to end with no oracle (7 340 creations in them),
  in 45 levels; at about 50 per 15-minute session, about 13 more sessions reach 2 000. (run:2026-10-20-chain)
- [C] **Oracle 13 is reached and reproduced**: Blood Raven (class 267, raven-xn2) and a flying scimitar (class 234, cn2)
  are created with their `oninit` MonEquip row, the unit seed after `MonEquipInit` predicted by the model, and their
  items made by the item chain; `--cf monequip-off` fails both. This is the creation Phase 1 review ruling 2 named, so
  the MonEquip model of chain/0002 § 11 is raised to `[C]`. (fn:sub_005D6B60_MonEquipInit@0x005D6B60,
  fn:sub_00573B20_MonEquipItemCreate@0x00573B20, run:2026-10-20-chain)
- [C] **Oracle 14 has no remainder on these logs**: 8 588 unit seeds after `SUnitCreate` predicted, of 8 588
  creations. The region appends by a creation outside the model (9) and the creations with no level known (33) are
  counted oracles of the windows they sit in. (fn:sub_00555230_SUnitCreate@0x00555230, run:2026-10-20-chain)
- [C] **Oracles 19 and 20 stay inputs, counted**: 2 470 `LevelRoomCount` reads; every `OG` line's DRLG inputs agree
  with chain/0002 § 7's reading (3 121, 2 470 and 2 351 assertions, 62 gates closed by flags `0x30000`); R3 residue in
  114 of 3 183 pass rooms, by bit in § 4, and every one of the 19 object-bit residue cells has a creation line before
  the snapshot (`OU0`), none unexplained. (fn:OBJ_PopulateGate@0x00552560, fn:LOGIC_BarrierGridBuild@0x0066C870,
  run:2026-10-20-chain)
- [I] **The two mismatches are a live monster the log does not place**: the game's test sees `0x100` and `0x1000`
  (a monster's footprint and centre) where the model has none; the nearest candidate in both is a monster that a
  `MonSpawnTry` request created a few seconds earlier, in walk mode, in a neighbouring room, and the logger writes no
  line when a monster moves (§ 2). (fn:COLL_WHTest@0x0064D800, fn:sub_005B2A00_MonSpawnTry@0x005B2A00, run:2026-10-20-chain)

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
| cn4 | 72971 | `0x005504B3` | (5402, 5241) 8×8 | `0x3F11` | `0x1100` | `0x0000` | class 310, created at (5398, 5237), mode 3 |
| cm4 | 53279 | `0x00550B89` | (7742, 6264) 10×10 | `0x3F11` | `0x1500` | `0x0400` | class 189, created at (7738, 6260), mode 3 |

- [C] Both are `COLL_WHTest` calls of the objects model inside a presets window (`RW1` to `RW4`) of a room that is
  activating; each window's other tests and seeds match, and the rest of each log passes. (fn:COLL_WHTest@0x0064D800,
  0x005504B3, 0x00550B89, run:2026-10-20-chain)
- [I] The extra bits are a monster's: `0x100` is the live-monster footprint and `0x1000` a unit's centre (drlg/0005's
  bit table), and the cn4 candidate stands 4 cells off the rectangle's corner at its creation. Neither candidate's
  footprint at creation overlaps the rectangle, and the logs carry no line for a monster's later moves, so which unit
  stood there is not shown. (fn:COLL_PatternMark@0x0064EA90, fn:sub_005B2A00_MonSpawnTry@0x005B2A00,
  run:2026-10-20-chain)
- Such a test is the first of its kind in the kept logs: a window's room tested next to a monster that had time to
  walk. Settling it needs the monster's position at the window (a logged mark or unmark of a moving unit, or the cell
  values at the test), Open question 1.

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

1. **What stands in the two rectangles?** Log a moving monster's marks between windows (or the cells under each
   `COLL_WHTest`), re-run cn4 and cm4 on their seeds and see whether the extra bits are the candidates'.
2. **Who writes a chest's interact byte between its creation and its operate?** (§ 3; four kinds now: lock bit set,
   lock bit cleared, cleared to 0.) Read the writers of the object's interact field reached from the player's
   interaction request.
3. **The 615 missing populations.** About 13 more sessions of the same kind; the outdoor levels give the most.
