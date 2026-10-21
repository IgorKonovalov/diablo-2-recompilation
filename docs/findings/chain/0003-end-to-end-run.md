# 0003 — The end-to-end run: fresh games from a seed, every act, difficulty and game type

> **Subsystem:** chain (seed to world, plan 0048)
> **Question:** does `tools/chain.py check`, with every Phase 1 model in, reproduce fresh games from known `-seed` values with no seed oracle inside the populations, over the coverage Phase 2 asks for?
> **Date:** 2026-10-21   **Plan:** 0048 (Phase 2)   **Status:** open (Phase 2 run 2: 0 mismatches over 37 logs, 2 189 oracle-free populations; review requested)

The runs are [run:2026-10-20-chain](experiments.md#run2026-10-20-chain) (run 1: 28 scripted sessions) and
[run:2026-10-21-chain2](experiments.md#run2026-10-21-chain2) (run 2: 9 more sessions, the revisit re-creations' marks
logged and modelled, and one check over all 37 logs). Both on slot 1, one game per session, logged by
`tools/gdb/chain.gdb`, checked together by `tools/chain.py check` (run 2's tool revisions in its
`tools-r2-final.sha256`). No Phase 1 model changed; the objects grid gained the re-creations' marks (§ 2) and one
checker scope changed (§ 3).

## Answer (summary)

- [C] **The composition reproduces all 37 logs with 0 mismatches** (run 1's 28 and run 2's 9, one check with run 2's
  tools, and each log alone): 1 641 203 monspawn checks and 275 898 monstats checks with 0 mismatches, 3 784
  `TC_ResolveDrops` calls and 1 913 item creations reproduced, 0 failed. Run 1's two mismatches (cn4, cm4) are gone
  with the re-creation marks of § 2, and come back exactly under `--cf recreation-off`. The Phase 1 world logs re-check
  with 0 failed, their summary unchanged but the new re-creation counts. (fn:sub_0054EC90_RoomPopulate@0x0054EC90,
  fn:TC_ResolveDrops@0x0055A6D0, run:2026-10-21-chain2)
- [C] **Coverage met on the 37 passing logs**: 176 (level, difficulty, game type) built, every generator kind
  (DrlgType 1: 65, 2: 36, 3: 75), every act of each game type in each difficulty (classic acts 1–4 and expansion acts
  1–5, in Normal, Nightmare and Hell); 13 056 objects created (2 888 by the populate pass, 10 168 presets); 63 champion
  packs and 162 unique and minion packs with 217 special mods rolls predicted; 1 314 monster drops with an item (1 492
  items) predicted from the dying unit's logged seed with no builder oracle. (fn:DRLG_LevelCreate@0x00642AE0,
  run:2026-10-21-chain2)
- [C] **Populations meet the bar**: 2 189 room populations end to end with no oracle (10 764 creations in them, 58
  levels, 43 (level, difficulty) pairs; Normal classic 323, Normal expansion 593, Nightmare 264 and 450, Hell 263 and
  296). Run 1's 28 logs hold 1 387 of them (cn4 118, cm4 47, each one more than run 1 counted: the window that failed
  now counts), run 2's nine 802. (run:2026-10-21-chain2)
- [C] **A revisit re-creation's marks are those the model predicts**: 1 903 re-creations inside a logged restore
  scope (`CMR0` .. `CMRX`, around the two `sub_00542B40_RoomInactiveUnitsRestore` calls) have their `CM` lines equal,
  line for line, to `tools/objects.py`'s prediction: 1 729 alive, 166 restored dead with MonStats2 `deadCol` 0, 8 dead
  with `deadCol` 1; `--cf recreation-off` fails r2-xn1 with 63 mismatches. The call path the marks take is a static
  reading, `[I]` (§ 2). (0x0052D142, 0x0052D205, fn:sub_00542B40_RoomInactiveUnitsRestore@0x00542B40,
  run:2026-10-21-chain2)
- [I] **Run 1's two mismatches were re-created monsters' marks the model lacked**: in each, the `COLL_WHTest` rectangle
  (centred on (x, y)) holds the re-creation cell of a monster the population pass had made and a `MonSpawnTry` request
  re-made after its room's release and return; with the predicted re-creation marks both tests match on the kept logs.
  On run 1's logs (no restore scope) those marks are checked only through the later tests and snapshots. Whether
  either monster moved and came back is not shown, and need not be. (fn:COLL_WHTest@0x0064D800,
  fn:sub_005B2A00_MonSpawnTry@0x005B2A00, run:2026-10-21-chain2)
- [C] **Oracle 13 is reached and reproduced** in four creations: Blood Raven (class 267) in raven-xn2, r2-xn2 and r2-xm1
  (Nightmare), a flying scimitar (class 234) in cn2, each with its `oninit` MonEquip row, the unit seed after
  `MonEquipInit` predicted and its one item made by the item chain; `--cf monequip-off` fails each case it was run on
  (raven-xn2, cn2, r2-xn2, r2-xm1). The raise of chain/0002 § 11 stays **in part** (one row, one location, one item);
  the level skip, further rows, two or three locations and an occupied location stay `[I]`, unreachable with the stock
  table. (fn:sub_005D6B60_MonEquipInit@0x005D6B60, fn:sub_00573B20_MonEquipItemCreate@0x00573B20,
  run:2026-10-21-chain2)
- [C] **Oracle 14 has no remainder on these logs**: 12 580 unit seeds after `SUnitCreate` predicted, of 12 580
  creations. The region appends by a creation outside the model (12) and the creations with no level known (34) are
  counted oracles of the windows they sit in. (fn:sub_00555230_SUnitCreate@0x00555230, run:2026-10-21-chain2)
- [C] **Oracles 19 and 20 stay inputs, counted**: 3 885 `LevelRoomCount` reads; every `OG` line's DRLG inputs agree
  with chain/0002 § 7's reading (4 801, 3 885 and 3 676 assertions, 82 gates closed by flags `0x30000`); R3 residue in
  160 of 4 883 pass rooms, by bit in § 4, and every one of the 31 object-bit residue cells has a creation line before
  the snapshot (`OU0`), none unexplained. (fn:OBJ_PopulateGate@0x00552560, fn:LOGIC_BarrierGridBuild@0x0066C870,
  run:2026-10-21-chain2)

## 1. The sessions

Each session is one fresh game (`d2run.py --seed N`), a waypoint, then the pilot's exploration of that level and the
levels next to it, 15 minutes of wall time from game entry at most. Run 1's 28 counted logs are 6 sessions per
difficulty in expansion (5 acts plus the smoke or raven-xn2 session in Normal) and 4 per difficulty in classic; run 2's
nine (seeds 4861..4911, `tools/chain_sessions.py` `PLAN2`) are mostly outdoor waypoints, in each difficulty and game
type. Seeds, levels and game minutes are in each run record's table. [C] All 37 logs are free of gdb's
`internal-error:` and under the 500 MB cap (the largest 17.2 MB). (run:2026-10-20-chain, run:2026-10-21-chain2)

The sessions cut short by the 2026-10-20 out-of-memory kill (xm5), the owner's pause (xm2) and the collision logger
error (raven-xn) were re-run on the same seeds; the cut logs are kept as development logs. In run 2, r2-cn1's game
process ended on its own at game frame 10 920 (cause not shown); its log is whole up to the exit and checks clean.

## 2. Run 1's two mismatches and the re-creations' marks

| Log | Line | Site | Rectangle | Mask | Game | Run 1's model | Candidate |
|---|---|---|---|---|---|---|---|
| cn4 | 72971 | `0x005504B3` | (5402, 5241) 8×8, cells 5398–5405 × 5237–5244 | `0x3F11` | `0x1100` | `0x0000` | class 310 (size 2), re-created at (5398, 5237), line 72742 |
| cm4 | 53279 | `0x00550B89` | (7742, 6264) 10×10, cells 7737–7746 × 6259–6268 | `0x3F11` | `0x1500` | `0x0400` | class 189 (size 3), re-created at (7738, 6260) and (7736, 6262), lines 51136, 51152 |

- [C] Both are `COLL_WHTest` calls of the objects model inside a presets window (`RW1` to `RW4`) of a room that is
  activating; with run 1's tools each test was the log's one mismatch. With run 2's tools both logs check with 0
  sub-checks failed, and `--cf recreation-off` (the re-creations make no marks) restores exactly these two results.
  (fn:COLL_WHTest@0x0064D800, 0x005504B3, 0x00550B89, run:2026-10-21-chain2)
- [I] The extra bits are a monster's: `0x100` is the live-monster footprint and `0x1000` a unit's centre (drlg/0005's
  bit table). `COLL_WHTest` with w or h above 1 tests the rectangle from (x − (w >> 1), y − (h >> 1)) (`tools/collision.py
  wh_test`), so each candidate's re-creation cell is inside it: (5398, 5237) is cn4's top-left cell; cm4's two
  class-189 footprints overlap its left columns. (fn:COLL_WHTest@0x0064D800, fn:COLL_PatternMark@0x0064EA90,
  run:2026-10-20-chain)
- [I] Each candidate is a **re-creation** of a monster the population pass made earlier, after its room came back:
  cn4's unit 522 (class 310) is created at (5398, 5237) in mode 1 at line 64416, then by `MonSpawnTry` requests (`MT0`
  with `a14` = 522, the same request seed `0a325233:31124861` both times) at lines 71869 and 72737, each after the
  room's release (`RREL`) and return; cm4's two class-189 units are created at lines 43499 and 43553 and again at 51136
  and 51152. (fn:sub_005B2A00_MonSpawnTry@0x005B2A00, run:2026-10-20-chain)
- [I] **The call the re-creations' marks take** (static reading of the pinned image): a room whose driver flag bit 0 is
  set gets no `RW` window; `sub_0052D0F0_RoomUpdateOne` (`0x0052D142`) and `sub_0052D160_NewRoomsUpdate`
  (`0x0052D205`) call `sub_00542B40_RoomInactiveUnitsRestore` directly, whose monsters go through
  `sub_005B30E0_SpawnWithId` to `sub_005B2A00_MonSpawnTry` with request flags `0x62`, `0x6A` or `0xE2`. Flag `0x20`
  makes the `SUnitCreate` create flags 3 (`0x005B2E10`; the `MU0` "mode" field is these flags), and bit 0 runs
  `sub_00554850_SUnitPathCreate`, whose monster branch marks through the same `UNIT_CollMark` calls as a pass creation
  (`PATH_DynamicCreate` at `0x00649E9A`, `sub_005A7C20_MonSetMode` at `0x005A7CB1`, both into `COLL_PatternMark`
  returning to `0x006494D5`), then MonSpawnTry's alignment refresh (`0x005B2EAB`). A record restored dead (`a10` = 12)
  has no MonSetMode mark (`sub_005541B0_UnitIsDead` tested at `0x005A7CA7`); with MonStats2 `deadCol` 0 the corpse call
  (`sub_00649F70_UnitCorpseColl`, `RectOrWH` 3×3 `0x8000` at `0x00649FD8`) and SUnitCreate's corpse re-mark
  (`0x0055546F`..`0x005554A3`) follow; `deadCol` 1 keeps the one live mark. Run 1's logger caught no `CM` line for them
  because `tools/gdb/collision.py` logged marks only inside an `RW1`..`PX` window, and the restore runs outside one.
  (fn:sub_00542B40_RoomInactiveUnitsRestore@0x00542B40, fn:sub_005B30E0_SpawnWithId@0x005B30E0,
  fn:sub_00554850_SUnitPathCreate@0x00554850, fn:PATH_DynamicCreate@0x00649D00, fn:sub_005A7C20_MonSetMode@0x005A7C20,
  fn:sub_00649F70_UnitCorpseColl@0x00649F70)
- [C] **The marks, compared line for line** (run 2's logs): `tools/gdb/collision.py` writes `CMR0 {th, room}` at the two
  restore calls and `CMRX` at their returns (`0x0052D147`, `0x0052D20A`), and logs the `CM` lines between them; for
  each re-creation (`MT0` with a saved unit id, outside a window) `tools/objects.py` `recreation` predicts the
  ordered `PM`/`PU` and corpse `RO` lines from MonStats and MonStats2 and compares cell, room, size and mask. On run 2's
  nine logs, 1 942 re-creations in 1 000 scopes: 1 903 equal (1 729 alive, 166 dead with `deadCol` 0, 8 dead with
  `deadCol` 1), 39 requests made no unit, 0 different. Under `--cf recreation-off` r2-xn1 fails with 63 mismatches, each
  a re-creation's logged marks against an empty prediction. The dead sequence was first predicted wrong from the code
  alone and corrected from r2-xn1's log (`out/dev-r2-xn1-check-deadlist0.txt`: 18 dead re-creations mismatched, every
  alive one matched); the other eight run-2 logs' dead cases (134 with `deadCol` 0, 6 with `deadCol` 1) were not the
  correction's evidence and match it. (0x0052D142, 0x0052D205, 0x006494D5, run:2026-10-21-chain2)
- [C] On run 1's 28 logs, which have no scope, the same prediction is applied to the grid unchecked (5 348
  re-creations: 4 953 alive, 328 dead `deadCol` 0, 3 `deadCol` 1, 64 made no unit) and is checked only through the
  later position tests and snapshots, which all pass; the Phase 1 world logs likewise (529). (run:2026-10-21-chain2)

## 3. Checker scope change: a chest's interact byte

- [C] Chests reach `OperateFn` 4 with an interact byte that differs from the one their InitFn left, with no logged line
  writing it in between: run 1's xm3 (classes 183 and 181, Durance of Hate 2) with the lock bit `0x80` set after a
  creation with 0, xm5's class 430 created with `0x86` reaching it with 0, run 2's r2-xm1 one more "cleared to 0".
  `tools/objects.py` (commit `dfe3e5e`) takes the byte there and counts it by kind (on the 37 logs: lock bit set 2,
  lock bit cleared 3, cleared to 0 2); without the change each was a mismatch. The writer is not read. The Phase 1 world
  logs' summary is unchanged by it. (fn:OBJINIT_Chest@0x0054FCB0, run:2026-10-21-chain2)

## 4. Oracle 20's residue, by bit

- [C] Of the 4 883 pass rooms, 4 723 have a composed grid equal to the snapshot; the 160 others differ only by bits the
  snapshot has and the model lacks: `0x0080` 192 cells, `0x0100` 166, `0x1080` 48, `0x1100` 43, `0x0400` 28, `0x0800` 5,
  `0x0404` 3. The 31 object-bit cells (`0x400`, `0x404`) each have a creation (`OU0`) before the snapshot, listed with
  the nearest line in run 2's `r2final-o20.json`. (fn:sub_0054EC90_RoomPopulate@0x0054EC90, run:2026-10-21-chain2)

## Data touched

No table read is new in this phase; the models' reads are in chain/0002 and the subsystem findings it links. The
re-creation marks read MonStats (size) and MonStats2 `deadCol` through `tools/objects.py` `MonTables`.

## Open questions

1. ~~The marks of a re-created monster~~ — closed by run 2: logged and modelled (§ 2), cn4 and cm4 pass on their kept
   logs. No test in the 37 logs needs a moved monster's marks as a simulation input.
2. **Who writes a chest's interact byte between its creation and its operate?** (§ 3; three kinds: lock bit set, lock
   bit cleared, cleared to 0.) Read the writers of the object's interact field reached from the player's interaction
   request. Not read in run 2 (no cheap static anchor); for Phase 3's *Open questions*.
3. ~~The missing populations~~ — closed by run 2: 2 189 of the 2 000.
