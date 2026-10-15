# Object experiments

## run:2026-10-14-objects-window

- **Question:** (plan 0023 Phase 1) Does the slot loop of [objects/0001](0001-object-population.md), written from the
  code, account for every room-seed draw of the objects window (`RW3` → `RW4`) in the logs already on disk? Does the
  inactive-unit restore draw nothing on a first activation (`RW2` → `RW3`)?
- **Setup:** no new game run. This is a re-analysis of 22 existing logs from three earlier runs, all written by
  `tools/d2run.py` under the ADR-0003 harness:
  - run:2026-10-13-mon-spawn: `workspace/logs/monspawn-s1-12345-normal-a1.log`, `monspawn-s2-12345-normal-a2-5.log`,
    `monspawn-s3-1-hell-a1.log`
  - run:2026-10-14-collision: `workspace/logs/collision-s1-2026-normal.log` … `collision-s7-2026-normal-a1.log` (7 logs)
  - run:2026-10-14-mon-special: `workspace/logs/monspecial-s1-2101-normal.log` … `monspecial-s12-2112-nightmare.log` (12 logs)

  Their loggers (`mon-spawn.gdb`, `collision.gdb`, `mon-special.gdb`) all write `RW0`..`RW4`: the room seed `rs` and
  game seed `gs` (`low:high`) after each out-of-scope call of `sub_0052D160_NewRoomsUpdate`, with the room's level id.
  `RW2` follows the preset units, `RW3` the inactive-unit restore and `RW4` the object population. Tables:
  `levels.bin`, `objgroup.bin` and `objects.bin` from `workspace/merged/data/global/excel`. Checker:
  `tools/objects.py` (sha256 prefix `ed5077d5d9d284a6`).
- **Procedure:**
  ```
  L=workspace/logs
  python3 -I tools/objects.py window $L/monspawn-s1-12345-normal-a1.log $L/monspawn-s2-12345-normal-a2-5.log \
      $L/monspawn-s3-1-hell-a1.log $L/collision-s[1-7]-*.log $L/monspecial-s[0-9]*-*.log -v
  ```
  The model is in the docstring of `tools/objects.py`. Three things in the window are unknown to the logs: the
  placement attempts of the shrine and well handlers, their caps, and the gate and forced-shrine state. The checker
  enumerates them and requires that exactly the logged `RW4` room seed is reached. A room is "exact" when no unknown
  besides the gate was needed.
- **Observed:**
  ```
  objects-window: logs=22 rooms=2090 restore_checked=2090 restore_moved=0 closed=685 closed_town=222 exact=915
  branched=490 forced=3 fail=0 slot_passes=2307 member_none=259 shrine=420 well=359 trap=35 init46=24 other_handlers=1210
  FORCED monspecial-s10-2110-hell.log 44024832 76
  FORCED monspecial-s10-2110-hell.log 44024704 76
  FORCED monspecial-s1-2101-normal.log 56248448 4
  ```
  - 2090 first activations. The inactive-unit restore left the room and game seed unchanged in all 2090.
  - 685 windows drew nothing: 222 in towns, 463 in levels with object groups (gate closed).
  - 1405 windows drew, and each one is accounted for:
    - 915 with no unknown: 8 slot draws, plus one pick draw per passing slot, plus one draw per trap handler.
    - 490 that needed the placement-attempt or cap unknowns of the shrine and well handlers, or InitFn 46's
      monster draws (24 picks of object 369, City of the Damned).
  - 2307 slots passed. 259 of them picked no member, because the draw was at least the members' `PROB` sum.
  - 3 windows only fit with the forced rule: `r = 100` on slots whose group index names an Objects row with
    `SubClass ≠ 0`, in Spider Forest (2) and Stony Field (1).
  - A first version of the model without that rule failed exactly these 3 rooms, plus 6 rooms of City of the Damned
    (InitFn 46) that the wildcard now covers.
- **Conclusion:** this upgrades the following claims of [objects/0001](0001-object-population.md) to confirmed for the
  room seed (this is a bit-exact check of the room-seed draw sequence; the object-region seed is not logged):
  - the slot loop: draw, comparison, group 0, member pick, sum below 100;
  - which handlers draw the room seed (2, 8, 9) and which do not (1, 3, 4, 5, 6, 7);
  - the trap handler's single draw;
  - the shape of the shrine and well draws (`1 + 2a`);
  - closed town windows;
  - the forced-slot rule as an outcome;
  - the restore's "no draw" on a first activation.

  What stays inferred: placement positions, the object-region draws, the trigger of the forced rule and the gate
  conditions other than town. Raw logs: the 22 files above. No new log was written.

## run:2026-10-15-objects

- **Question:** (plan 0023 Phase 2) Does the model of [objects/0001](0001-object-population.md) reproduce, bit for bit,
  the objects window of every room (RW1 → RW4: preset objects, the restore, the populate pass), every object's creation
  draws and every container's operate draws up to the TC call, on the room, object-region, game and unit seeds, with
  the seeds at the population pass entry predicted rather than taken? And do the three older runs still account for
  their windows under the Phase 2 bounds?
- **Setup:** ADR-0003 harness, slot 0 (`:7`, `workspace/wineprefix`), the pinned `game.exe`.
  - Logger `tools/gdb/objects.gdb`: the loggers of `mon-special.gdb` (with `os`, the object-region seed, added to the RW
    lines of `mon-spawn.py`), plus `tools/gdb/objects.py` (sha256 prefix `85a949bafc074ff7`; tags in its header: OGC, the
    OD watchpoint on the object-region seed's low word, OG/OS/OK/OH0/OHX for the pass, OT at the seven `COLL_WHTest` call
    sites, OPU0/OPUX, OU0/OUX, OI0/OIX, OGP0/OGPX, OO0/OOX, OC0/OCT/OCX), plus `tools/gdb/tc-drops.gdb`. Run with
    `MONSPAWN_WATCH=` empty: the watchpoint needs the debug register that the MonWndr watchpoints would take.
  - Characters, built with `tools/d2s.py build` (ADR-0003 tool-built inputs): `ObjNova` from
    `tools/d2s_recipes/objnova.json` (sha256 prefix `784cfe25`, expansion, base `workspace/samples/d2s-owner/smpsor-l50.d2s`,
    save `d54d5dc3`) and `ObjClassic` from `tools/d2s_recipes/objclassic.json` (`9d5c8c55`, classic, base
    `workspace/runtime/monspawn-chars/cls/smpsor.d2s`, save `0f1afac1`). Both are the spec recipes plus a stack of 12
    keys; the classic one has Nova on the right button. Sessions 7 and 8 used an earlier `objclassic.json` build on the
    expansion base, which is an expansion character. Sessions 10–23 ran with both saves in the directory, and the game
    picked `ObjClassic`. The table gives each session's character from the log's P0 `exp` flag.
  - Scripted play per [harness-play](../../../.claude/skills/reverser/references/harness-play.md): waypoint travel
    (`d2pilot.py wp`, with the new `--wp-find`), then `d2pilot.py explore --nova 3 --loot 18 --persist 8`, adding
    `--es 30` in Nightmare and Hell. `--loot` is new: it operates the containers within 18 sub-tiles, hovering before the
    click. `--persist` is new too: a random hop instead of stopping on "no target".
  - Checker `tools/objects.py check` (sha256 prefix `4949b4e9476c9b5e`); tables from `workspace/merged/data/global/excel`.
- **Procedure:** for each session, `saves.py --slot 0 restore obj23`, `aside obj23` and `install obj23 SAVE`; then
  `MONSPAWN_WATCH= python3 -I tools/d2run.py --slot 0 --seed N --gdb tools/gdb/objects.gdb --steps
  tools/gdb/enter-DIFF.steps --after 3600 --log workspace/logs/objects-sK-N-DIFF.log`; the pilot as above; then
  `tools/slots.py stop 0`. Checks:
  ```
  python3 -I tools/objects.py check workspace/logs/objects-s{2..30}-*.log -v
  python3 -I tools/monspawn.py check workspace/logs/objects-s2-2302-normal.log    # and s5, s11, s13
  L=workspace/logs; python3 -I tools/objects.py window $L/monspawn-s1-12345-normal-a1.log \
      $L/monspawn-s2-12345-normal-a2-5.log $L/monspawn-s3-1-hell-a1.log $L/collision-s[1-7]-*.log $L/monspecial-s[0-9]*-*.log
  ```
  Session 1 (`objects-s1-2301-normal.log`) and the smoke log came before the OPUX room seed and the OPU0 level were
  logged. They are development logs, not part of the record.

| Log | Seed | Character | Difficulty | Levels with gated windows | Windows RW1→RW4 | Objects created | Operates | Checks |
|---|---|---|---|---|---|---|---|---|
| `objects-s2-2302-normal.log` | 2302 | ObjNova (expansion) | Normal | 3 | 88 | 74 | 2 | 4860, 0 mismatches |
| `objects-s3-2303-normal.log` | 2303 | ObjNova (expansion) | Normal | 79 | 69 | 272 | 17 | 12282, 0 mismatches |
| `objects-s4-2304-nightmare.log` | 2304 | ObjNova (expansion) | Nightmare | 76 | 65 | 115 | 3 | 6997, 0 mismatches |
| `objects-s5-2305-hell.log` | 2305 | ObjNova (expansion) | Hell | 110, 111, 125 | 129 | 304 | 9 | 17635, 0 mismatches |
| `objects-s6-2306-nightmare.log` | 2306 | ObjNova (expansion) | Nightmare | 42, 43 | 75 | 118 | 1 | 5485, 0 mismatches |
| `objects-s7-2307-normal.log` | 2307 | ObjNova (expansion) | Normal | 5 | 42 | 78 | 2 | 3860, 0 mismatches |
| `objects-s8-2308-nightmare.log` | 2308 | ObjNova (expansion) | Nightmare | town only | 9 | 33 | 0 | 1013, 0 mismatches |
| `objects-s9-2309-nightmare.log` | 2309 | ObjClassic (classic) | Nightmare | 107 | 45 | 76 | 0 | 5172, 0 mismatches |
| `objects-s10-2310-nightmare.log` | 2310 | ObjClassic (classic) | Nightmare | 107 | 30 | 55 | 0 | 3457, 0 mismatches |
| `objects-s11-2311-hell.log` | 2311 | ObjClassic (classic) | Hell | 6, 11 | 72 | 133 | 4 | 6618, 0 mismatches |
| `objects-s12-2312-normal.log` | 2312 | ObjClassic (classic) | Normal | 43 | 66 | 79 | 0 | 4401, 0 mismatches |
| `objects-s13-2313-hell.log` | 2313 | ObjClassic (classic) | Hell | 44 | 49 | 122 | 1 | 5225, 0 mismatches |
| `objects-s14-2314-normal.log` | 2314 | ObjClassic (classic) | Normal | town only | 9 | 17 | 0 | 703, 0 mismatches |
| `objects-s15-2315-normal.log` | 2315 | ObjClassic (classic) | Normal | town only | 12 | 24 | 0 | 1009, 0 mismatches |
| `objects-s16-2316-normal.log` | 2316 | ObjClassic (classic) | Normal | 57 | 23 | 45 | 1 | 2089, 0 mismatches |
| `objects-s17-2317-normal.log` | 2317 | ObjClassic (classic) | Normal | town only | 12 | 11 | 0 | 472, 0 mismatches |
| `objects-s18-2318-nightmare.log` | 2318 | ObjClassic (classic) | Nightmare | town only | 9 | 17 | 0 | 703, 0 mismatches |
| `objects-s19-2319-hell.log` | 2319 | ObjClassic (classic) | Hell | town only | 9 | 17 | 0 | 703, 0 mismatches |
| `objects-s20-2320-normal.log` | 2320 | ObjClassic (classic) | Normal | town only | 12 | 11 | 0 | 472, 0 mismatches |
| `objects-s21-2321-normal.log` | 2321 | ObjClassic (classic) | Normal | town only | 12 | 11 | 0 | 469, 0 mismatches |
| `objects-s22-2322-nightmare.log` | 2322 | ObjClassic (classic) | Nightmare | town only | 15 | 24 | 0 | 1074, 0 mismatches |
| `objects-s23-2323-normal.log` | 2323 | ObjClassic (classic) | Normal | 27 | 33 | 87 | 5 | 3095, 0 mismatches |
| `objects-s24-2324-normal.log` | 2324 | ObjNova (expansion) | Normal | 29, 30 | 23 | 189 | 15 | 6193, 0 mismatches |
| `objects-s25-2325-normal.log` | 2325 | ObjNova (expansion) | Normal | 106, 107 | 72 | 263 | 1 | 11632, 0 mismatches |
| `objects-s26-2326-nightmare.log` | 2326 | ObjNova (expansion) | Nightmare | 113 | 45 | 115 | 3 | 5090, 0 mismatches |
| `objects-s27-2327-normal.log` | 2327 | ObjNova (expansion) | Normal | 48 | 21 | 104 | 0 | 3309, 0 mismatches |
| `objects-s28-2328-hell.log` | 2328 | ObjNova (expansion) | Hell | 80, 92 | 57 | 361 | 11 | 15272, 0 mismatches |
| `objects-s29-2329-hell.log` | 2329 | ObjNova (expansion) | Hell | 43, 62 | 81 | 144 | 10 | 7227, 0 mismatches |
| `objects-s30-2330-normal.log` | 2330 | ObjNova (expansion) | Normal | 4, 38 | 81 | 110 | 4 | 6023, 0 mismatches |

  Sessions 8, 14, 15 and 17–22 never left town: the waypoint list did not open, or the save started in another town.
  Their windows (town presets, closed gates) are checked all the same.
- **Observed:**
  ```
  objects: 142540 checks, 0 mismatches          (29 logs)
  windows predicted RW1 -> RW4 (room, object-region and game seed) 1265; restore windows: no draw 1265
  windows closed at the gate 506; past the gate 759; slots 6072, passed 1127, no member 95; theme rolls 20
  objects created: populate 644, preset 2365 (548 re-created by the restore on a revisit); PreOperate rolls 510
  PopulateFn calls {1: 87, 2: 190, 3: 592, 4: 17, 6: 47, 7: 1, 8: 78, 9: 15}; position tests 5767
  placements accepted at attempt 1..5: 153, 87, 67, 51, 29; with no spot after 5 attempts 911
  InitFn runs: 1: 65, 2: 397, 3: 212, 27: 2, 28: 14, 34: 20; oracles InitFn 46: 16, 54: 7, 62: 4
  operates: casket 1, urn 37, chest 40, barrel 11; TC_ResolveDrops oracle calls 59
  object timer event draws 3042 (all at 0x0058176F)
  populated rooms 316: (difficulty, expansion, act) n 0 1, n 0 2, n 1 1, n 1 2, n 1 3, n 1 4, m 0 4, m 1 2, m 1 3,
                       m 1 5, h 0 1, h 0 2, h 1 2, h 1 3, h 1 5
  shrines 65 (codes 1, 2, 3, 6, 7, 8, 10, 11, 12, 13, 14, 15, 18, 20)
  containers created 609: trapped 25, locked 26; super chests (DS1 580) 4, all sparkle
  urns: r < 21 (drop) 9 of 37, one at r = 20 dropped; chests: empty (r <= 24) 11, locked opened 6, sparkle 3 (quality 4)
  placements that needed retries 234; gold piles 14 (counts 2..9)
  forced slots (r = 100): 1, level 48 slot 2 group 5
  monspawn (s2, s5, s11, s13): 0 mismatches, collision 0; pass entries predicted end to end 88 + 129 + 72 + 49
  objects-window (22 older logs): rooms=2090 restore_moved=0 closed=685 exact=915 branched=490 forced=3 fail=0 shrine_due=2
  ```
  - Every object-region draw of the run was compared as it happened (the OD watchpoint lines). Inside the windows and
    operates the model made the draw. Outside them (the object timer events, objects/0001 § 12) the draw was stepped
    and compared.
  - The Phase 1b cases:
    - The urn chance is 21/100: an urn drew exactly 20 and dropped.
    - The three sparkle chests used the act chest TC (`Act 3 Chest B` twice, `Act 1 Chest A`) with forced quality 4
      on every drop.
    - The gold-pile counts are `low mod 9 + 1`.
    - `MonLvl1` drives the trap and lock chances in Nightmare and Hell too: the 212 chests and 397 containers include
      Nightmare and Hell levels, and every lock and trap roll reproduced on the normal-difficulty column.
  - The ObjGroup slots of the gated levels with `ObjPrb` > 0 that no window drew (unreached, not contradicted): level 11
    (groups 6, 4), 30 (51, 15, 3), 38 (45), 48 (26, 5), 62 (29), 92 (65), 110 (100, 101, 106), 125 (49). The other 86
    level slots were drawn.
  - The older runs: the `window` replay, now bounded by the Phase 2 handler shapes (at most 15 shrine attempts unless the
    health shrine is due), still accounts for all 1405 drawing windows; 2 need the due rule's 30 tries. Their logs hold
    no per-object lines, so the shrine and well attempt counts stay unknowns there; the new run predicts them.
- **Conclusion:** the claims of objects/0001 that the run exercised are now confirmed (§ 12 and the tags there):
  - the object-region seed from game-seed draw 2, and its game-wide stream;
  - the gate's counters and the theme roll;
  - the slot loop and the forced rule;
  - PopulateFn 1, 2, 3, 4, 6, 7, 8 and 9, with their placers and position-test shapes;
  - creation: the unit seed, InitFn 1, 2, 3, 27, 28 and 34, PreOperate, the animation draw;
  - the pseudo-objects 580 and 581;
  - the restore: nothing on a first activation, a full re-creation on a revisit;
  - the operate draws of OperateFn 3, 4 and 5 up to each drop.

  Boundaries: the `COLL_WHTest` results and the gate's DRLG inputs are logged values. The monster and quest InitFns, the
  preset monsters, `TC_ResolveDrops`, the gold drop and the operate monster spawn are seed oracles. When an object timer
  event runs comes from the log. Not reached: PopulateFn 5, InitFn 57 and 58, the class-397 table, the casket after an
  item, the caps, the forced shrine conversion, and pseudo-objects 574–579. Raw logs: the 29 files above, in
  `workspace/logs/`.
- **Addendum 2026-10-15: re-analysis for the objects/0001 § 13 details (plan 0023 Phase 3 follow-up).** No new game
  run. `tools/objects.py` (sha256 prefix `55e94a32bb3f59f5`) gained counters for the six details and two model fixes
  that the run cannot see: the closing `UNIT_SetMode(u, 0)` of `OBJ_PresetSuperChest`, and `OBJTRAP_MonsterSpawn`'s pc
  range among the timer-event draw sites. Command:
  `python3 -I tools/objects.py check workspace/logs/objects-s{2..30}-*.log`. Observed (trimmed):
  ```
  objects re-created by the inactive-unit restore (revisit)                  548
  revisit re-creations after another of the same restore: in the earlier creation order 362
  orientation-1 placement attempts: margin passed                            121
  cov shrine picks whose 8 tries all failed LevelMin, the last kept (level, class, code) 1 [(3, 4, 6)]
  super chests: Maggot Lair P100 draw after the creation draws               2
  oracle OperateFn 23 (not a container) 23; OperateFn 7 1; OperateFn 8 1
  objects: 142540 checks, 0 mismatches
  ```
  - No "NOT in the earlier creation order" line and no "PopulateFn 1 follower walks after a class whose size differs
    from the member's" line was printed, so both counts are 0.
  - Conclusion ([objects/0001 § 13](0001-object-population.md#13-details-for-the-spec-plan-0023-phase-3-follow-up-2026-10-15)):
    - `[C]` (run:2026-10-15-objects) for the revisit order (§ 13.5), the orientation-1 placer's margin and test (§ 13.2), `ShrinePick`
      keeping the eighth code (§ 13.3), the 580 Maggot Lair draw after the creation draws (§ 13.4), and no
      object-region draw in OperateFn 7, 8 and 23 (§ 13.6; the existing check that the seed is unchanged from OO0 to
      OOX).
    - Not settled by this run: the follower size of handler 1 (every list it reached is 1 × 1), orientation 2, and
      OperateFn 26, 48 and 68 (never operated). These stay `[I]` (fn:OBJPOP_Clusters@0x00550C20,
      fn:OBJOP_Bookshelf@0x00584060).
- **Addendum 2026-10-15: the position tests and the object marks on the grid model (plan 0027 Phase 2).** No new game
  run. `tools/objects.py` keeps the room grids of `tools/collision.py` (fed with the log's `TL`, `CB`, `TCU`, `RRESEED`),
  makes every object's mark itself and predicts every `COLL_WHTest`; the logged results and `CM` lines are the checks
  ([objects/0001 § 14](0001-object-population.md#14-the-position-tests-and-the-object-marks-on-the-grid-model-plan-0027-phase-2-2026-10-15),
  [drlg/0005 § 14](../drlg/0005-collision.md#14-plan-0027-phase-2-the-objects-window-on-the-grid-model-2026-10-15)).
  Commands and observed (trimmed):
  ```
  python3 -I tools/objects.py check workspace/logs/objects-s{2..30}-*.log
    position tests predicted by the grid model (COLL_WHTest): blocked 4816, free 1043   (5767 placer tests + 92 gold-pile tests)
    object marks predicted and compared with the logged CM: mask 0x0400 1813, 0x0404 13, 0x0806 7, 0x8000 2
    object marks predicted inside a seed oracle (objects under preset monsters), compared  12
    object marks: none (HasCollision 0 for the mode) 742; outside a logged window (not compared) 433
    marks applied from the log: monsters (PM/PU) 8400 + 2157 inside oracles, corpse squares 21, gold-drop items 0x200 71
    gold-pile room tests predicted (the object's room) 92
    objects: 150338 checks, 0 mismatches
  python3 -I tools/collision.py check workspace/logs/objects-s{2..30}-*.log
    monspawn: 279524 checks, 0 mismatches; collision: 28177 checks, 0 mismatches
  python3 -I tools/drlg.py roomk workspace/logs/objects-s{2..30}-*.log      (the tile-entry flags, drlg/0002)
    3995 activations, 138417 checks, 0 mismatches; 1 786 086 entries compared, 383 742 AnimTilesBuild frames
  ```
  The 13 logs of this record with `OD0` lines are also in the 40-log `drlg.py gen` check of the run:2026-10-14-collision
  addendum (2660 activations, 896 793 entries, 773 type-1 rooms on predicted grids, 0 mismatches).
  - Conclusion: `COLL_WHTest`, the object marks (`UNIT_CollMarkRect`, `UNIT_GetCollMask` for objects), `OBJINIT_Portal`'s
    early mark and InitFn 28's running position are `[C]`; the test results and the object marks are no longer logged
    inputs. The monster marks and the gold drop's item marks stay logged (seed oracles). (fn:COLL_WHTest@0x0064D800,
    fn:UNIT_CollMarkRect@0x00620A70, fn:OBJINIT_Portal@0x0054FE70, fn:OBJINIT_GoldPiles@0x0054F8C0, run:2026-10-15-objects)
