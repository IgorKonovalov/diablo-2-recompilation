# DRLG experiments

## run:2026-10-11-drlg-roomk

- **Question:** (plan 0008 Phase 2) Does the k model of [drlg/0002](0002-room-build-draws.md) predict, for
  every DRLG room activated in a run, the room seed at the activation draw (RACT, and so k and the
  active-room seed), for server and client copies, outdoor (type 1) and preset (type 2) rooms, a preset
  town of another act and maze levels? Do the rooms of run:2026-10-11-seed-tree-p1 get the same k again?
- **Setup:** the ADR-0003 harness as in run:2026-10-11-seed-tree (game dir `workspace/runtime/game/`,
  prefix `workspace/wineprefix`, display `:7`), wine 11.17, GNU gdb 17.2 with its Python. Map seed by
  `-seed N`. Logger `tools/gdb/drlg-roomk.gdb`, which sources `tools/gdb/drlg-roomk.py` (sha256
  `f0e42380…7f6f` and `d6b2e6e0…e5be`). Model and checker `tools/drlg.py` (`roomk`, `p1cmp`, `tables`),
  which reads the DT1, DS1, `lvlsub.bin` and `lvlwarp.bin` files from `workspace/merged` (the tree of the
  MPQs the harness game loads) and the two remap tables from the pinned `game.exe`. Saves: the harness
  character `seedtest` (sha256 `cabccb01…`) for the town, Blood Moor and Act II cases; for the maze
  cases `workspace/samples/d2s-waypoints/smpsor-a.d2s` (`setwp … normal 0,2,6,8`, run:2026-10-11-d2s-waypoints)
  and `workspace/runtime/saves-backup/s5-human/seedtest-played.d2s` (clvl 71, all nine Act I normal
  waypoints; sha256 `9179ef03…2030`), each copied alone into an emptied saves directory
  (`mv "$SAVES" "$SAVES.keep-roomk" && mkdir "$SAVES"`) and restored afterwards (sha256 of the seven
  `seedtest.*` files identical before and after).
- **Logged** (one JSON line per event, `tools/gdb/drlg-roomk.py` header): RRESEED `0x0066EE40` (room rect,
  flags, type, level and level type, DT1 file list, neighbour list, warp nodes as LvlWarp rows, the
  level's warp ids); LSUB `0x006707A0` (seed, pass type/theme/mask, the three OutRoom grids at entry);
  LSUBX `0x00670808` (seed after the pass, and the substitution groups of each record used, as the game
  holds them); TINIT `0x0066EE70` (seed, the grids the tile build walks, each neighbour's built state and
  seed); O89 `0x0066D9E0` / O89D `0x0066DAC1` (oracle `sub_0066D9E0_Orient89Unit`: seed in, and its one
  `RNG_Range` call); RACT `0x0064233A`; AROOM `0x0064236E`; RTFREE `0x0066F0B0`.
- **Procedure:**
  1. Kill stale timers first (`pgrep -af tools/d2run.py`; none were left during this run, see the d2run
     fix in plan 0008's log).
  2. Act I town, two seeds:
     `python3 -I tools/d2run.py --seed 12345 --gdb tools/gdb/drlg-roomk.gdb --steps tools/gdb/enter-sp.steps --after 15 --log workspace/logs/roomk-12345-town.log`,
     and the same with `--seed 777` → `roomk-777-town.log`.
  3. Blood Moor: `--seed 12345 --steps tools/gdb/drlg-roomk-bloodmoor.steps --after 10` →
     `roomk-12345-bloodmoor.log` (enters, runs north-east out of the camp).
  4. Act II town: `--seed 12345 --steps tools/gdb/enter-sp.steps --after 15 --game-args "-act 2"` →
     `roomk-12345-act2.log`.
  5. Maze, save smpsor-a: `--seed 1 --steps tools/gdb/enter-sp.steps --after 1200` →
     `roomk-1-catacombs.log`; then by hand with `tools/xdrive.py --display :7 --window "Diablo II"`: the
     clicks of `tools/gdb/d2s-wp-open.steps` one at a time with a `shot` after each (the replayed file
     drifted under the logger, so the pad was clicked where the screenshot showed it, window (345, 85)),
     *Catacombs Level 2* at (230, 418), a few walks; then the window was moved to a visible workspace and
     the owner walked on (into Catacombs Level 3). The session was ended with `wineserver -k`.
  6. Maze, save seedtest-played: `--seed 1 --gdb tools/gdb/drlg-roomk.gdb --after 900` (no steps) →
     `roomk-1-catacombs-b.log`; the owner played it on a visible workspace: Single Player, Normal,
     waypoint to Catacombs Level 2, walked through Catacombs Levels 2–4; ended with `wineserver -k`.
  7. Check: `python3 -I tools/drlg.py roomk workspace/logs/roomk-{12345-town,777-town,12345-bloodmoor,12345-act2,1-catacombs,1-catacombs-b}.log`
     and `python3 -I tools/drlg.py p1cmp workspace/logs/run-p1-12345-a.log workspace/logs/roomk-12345-town.log`
     (also against `roomk-12345-bloodmoor.log`, and `run-p1-777-a.log` against `roomk-777-town.log`).
- **Observed:**
  ```
  roomk-12345-town      54 activations  client/type1=8 (k 150..376) client/type2=37 (k 50..81) server/type1=3 (k 239..372) server/type2=6 (k 55..79); levels [1, 2]
  roomk-777-town        49 activations  client/type1=3 (k 86..254) client/type2=37 (k 56..81) server/type2=9 (k 58..78); levels [1, 2]
  roomk-12345-bloodmoor 88 activations  client/type1=20 (k 144..376) client/type2=46 (k 15..81) server/type1=13 (k 144..372) server/type2=9 (k 40..79); levels [1, 2, 8]
  roomk-12345-act2      29 activations  client/type2=20 (k 0..93) server/type2=9 (k 60..93); levels [40]
  roomk-1-catacombs     123 activations client/type1=6 client/type2=76 (k 56..171) server/type2=41 (k 56..171); levels [1, 2, 35, 36]
  roomk-1-catacombs-b   177 activations client/type1=3 client/type2=95 (k 0..207) server/type2=79 (k 0..208); levels [1, 2, 35, 36, 37]
    maze levels in -b: 35 server 6 / client 9, 36 server 32 / client 22, 37 server 14 / client 12
  coverage (all six logs): picks with a draw 39652, picks with candidates but rarity sum 0 14154,
    (10,0,0) fallback 0; bit-2 new 11768, bit-2 merge 6835, of which re-pick on the neighbour's seed 354;
    filler floors 1450; LvlSub stamps 350; LvlSub records 10, 11, 12, 14, 15 (Trials 5/20) and 6, 9
    (Trials -1, the shuffle: 5 passes); truncated group of rec 11 drawn 4 times (w,h = 0,0);
    Orient89Unit oracle calls 526, oracle draws 0; warp tiles visible 24, hidden 15
  roomk: 520 activations, 8776 checks, 0 mismatches
  p1cmp: 45 rooms in run-p1-12345-a.log, 45 with the same RACT seeds (k) in roomk-12345-town.log
  p1cmp: 45 rooms in run-p1-12345-a.log, 45 with the same RACT seeds (k) in roomk-12345-bloodmoor.log
  p1cmp: 40 rooms in run-p1-777-a.log, 40 with the same RACT seeds (k) in roomk-777-town.log
  LvlSub rec 11 (Act1/Outdoors/Trees.ds1) last group as held in memory, 27 loads:
    [0,0,0,0] x 26, [0,229120,245560,1] x 1 (roomk-1-catacombs-b; that pass did not draw it)
  ```
  Checks per room: seed at every LSUB, LSUBX, TINIT, RACT and AROOM; the modelled LvlSub stamping plus
  theme fill and border bits against the next LSUB and the TINIT grids; every neighbour's built state and
  seed at TINIT against the model's; each O89/O89D seed in; every O89 line consumed; LvlSub groups in
  memory against the DS1 file. No RTFREE was logged. No LOGERR line.
- **Raw logs:** `workspace/logs/roomk-12345-town.log` (sha256 `1faa5b13…655c`), `roomk-777-town.log`
  (`72457891…b1aa`), `roomk-12345-bloodmoor.log` (`55fccd12…0797`), `roomk-12345-act2.log`
  (`24e4b8fd…95fd`), `roomk-1-catacombs.log` (`a7a678d8…1eb3`), `roomk-1-catacombs-b.log` (`a4f9f362…17b3`);
  screenshots `workspace/logs/wp-c*.png`, `roomk-bloodmoor.png`. Development logs `roomk-test1.log`
  (logger without the LSUBX groups) and `roomk-test2.log` (= `roomk-12345-town.log`) are not part of the record.
- **Deviations:** the maze cases were driven by hand and by the owner (steps 5–6), so they are rerun by
  playing, not by replaying a steps file; any walk that reaches a maze level gives a valid check, since
  the checker needs no prior knowledge of which rooms activate.
- **Conclusion:** promotes in [drlg/0002](0002-room-build-draws.md) to `[C]`: k as modelled (k_sub of the
  LvlSub passes, k_tile of the tile build, the bit-2 path against the neighbours built in the same act
  copy, the hidden and visible warp picks, the filler floor, the rarity-sum draw rule), for outdoor,
  preset and maze rooms, server and client copies, with `sub_0066D9E0_Orient89Unit` as the boundary
  oracle (526 calls, none drew: its `Range(3)` is not exercised). Corrects drlg/0002: the merge re-pick
  `0x0066E8F7` draws on the **neighbour's** seed, and hidden-warp picks use orientation 0. The k of every
  p1 room repeats. Open: the truncated `Trees.ds1` group (heap bytes; drlg/0002 § Open questions).
- **Addendum 2026-10-12: checker rerun for fixes F1–F2 (no new game run).** `tools/drlg.py` (sha256
  `bde62c8f…9093`) now also rebuilds the type-2 grids (`preset_prepare`: the
  `sub_006667D0_PresetRoomGridPrepare` views and writes on the DS1 read through `tools/ds1.py`, in a DS1 cache
  per log as `DS1_LoadCached` keeps one), checks each room's DT1 list against `LvlTypes` `File i+1` under
  `+0x50` plus the three fixed files, and checks `+0x50` itself (type 2: `LvlPrest.Dt1Mask`; type 1: the
  level-type value OR the `Dt1Mask` of the SubType records picked). The same six logs (sha256 as above) and
  the same command line as step 7:
  ```
  roomk: 520 activations, 11208 checks, 0 mismatches          (was 8776 checks)
    DT1 list checked: type 1 56, type 2 464
    type-2 mask = LvlPrest.Dt1Mask: 464 (rooms on DrlgType 1 levels 92, DrlgType 2 349, DrlgType 3 23)
    type-1 mask = level-type value | picked SubType Dt1Masks: 56 (Blood Moor: 28 x 0x44103, 28 x 0x444103)
    type-2 grids reproduced: 464 of 464; file unique 457 (1 candidate 61, 2: 39, 3: 2, 4: 354, 5: 1),
      2 or 3 identical files fit 7; one file fits every room of each preset instance;
      persistent DS1 cache and a fresh DS1 per room give the same grids in every room
  p1cmp: 45/45, 45/45, 40/40 (unchanged)
  ```
  The new checks are 464 grid-set comparisons (every layer and cell), 464 instance-consistency checks, 464
  layer-count checks, 520 DT1 lists and 520 masks. Mutation check: the checker fails when any one write is
  removed (wall-0 border: 912 mismatches; floor border or shadow border: 928; the `i << 18` bits: 760),
  or when the stride is off by one (1393). The DS1 file index is not in these logs, so the checker finds it
  as the `LvlPrest` file that reproduces the grids; Phase 3 logs it. **Conclusion:** promotes in
  [drlg/0002](0002-room-build-draws.md) to `[C]`: the type-2 grid prepare (views and `0x84`/`i << 18`
  writes), the DT1-list rule, the maze-room (and every preset room's) mask = `LvlPrest.Dt1Mask`, and the
  outdoor mask rule with `sub_006706A0_LvlSubRoll` for level type 2.
- **Addendum 2026-10-16: plan 0038 batch S4a (static, no new session; `tools/sweep_s4a.py` sha256 `fafe0406c61b4363…`).** The room-tiles model (`tools/drlg.py`,
  `Model`/`run_log`, unchanged) re-run with counters by `tools/sweep_s4a.py` over every log with roomk lines, which are
  the six logs above, the 7 of run:2026-10-14-collision and the 29 of run:2026-10-15-objects. Commands:
  `python3 -I tools/sweep_s4a.py pick`, `… roomk`, `… kill`, `… pflags`. Observed (trimmed):
  ```
  pick   entries compared 1 852 097, tile = model's choice (candidates newest-indexed first, 3d walk) in all;
         file-order control 781 380 differ; animated entries of Animate rooms (rarity-0 frame) 42 881, all rarity 0;
         picks with two or more candidates 234 716; (10, 0, 0) fallbacks 1280; roomk model mismatches 0
  roomk  bit-2 merges 39 096: entry flag 0x1 38 509, row -1 (o 0) 530, cell bit 7 57, neighbour re-picks 587;
         rows 0-5 / row -2 / 8-9 edge: 0; Def 1 rooms 620, Def 108 0, Animate rooms 187 (k checked);
         PLDX with 0x1000000 5568 of 5568; type-2 TINIT with 0x1000000 | 0x2000000 5098 of 5098;
         PRC file = LvlPrest File(idx + 1) 56 422 of 56 422
  kill   type-2 rooms KillEdge 1: 3736, FillBlanks 1: 4911; mismatches: stock 0, KillEdge ignored 26 517,
         FillBlanks ignored 4168 (42 logs)
  pflags released type-2 rooms: 0x8000000 iff Animate (104 with, 3540 without)
  ```
  `python3 -I tools/drlg.py roomk` on the six logs: 520 activations, 11 734 checks, 0 mismatches (the checker's count
  since plan 0027 Phase 2 added the grid checks, `a14c875`; plan 0027's log records the same 11 734, against the 11 208
  above). Conclusion: [drlg/0002 § Plan 0038 batch S4a](0002-room-build-draws.md#plan-0038-batch-s4a-2026-10-16)
  and [drlg/0004 § Plan 0038 batch S4a](0004-preset-units.md#plan-0038-batch-s4a-2026-10-16).

## run:2026-10-12-drlg-gen

- **Question:** (plan 0008 Phase 3) For every level the game builds, does the dispatch model of
  [drlg/0003](0003-generator-dispatch.md) reproduce the level-seed sequence (the create-time and build-time
  `Init`, every modelled draw, the oracle windows' entry seeds and the seed at the end of the build), the
  preset file index of every preset instance, the room count and the room-creation order, for the
  preset, outdoor and maze generators?
- **Setup:** the ADR-0003 harness as in run:2026-10-11-drlg-roomk (game dir `workspace/runtime/game/`, prefix
  `workspace/wineprefix`, display `:7`), wine 11.17, GNU gdb 17.2. Map seed by `-seed N`. Logger
  `tools/gdb/drlg-gen.gdb`, which sources `tools/gdb/drlg-gen.py` (sha256 `dcd466c9…a1b4` and `5aebdb84…16e2`).
  Model and checker `python3 -I tools/drlg.py gen` (sha256 `6e12f906…aa61`; tables from `workspace/merged`). Save: the harness character
  `seedtest` (sha256 of the seven `seedtest.*` files identical before and after the runs, `cabccb01…` for the `.d2s`).
- **Logged** (one JSON line per event, header of `tools/gdb/drlg-gen.py`): LC0/LC1 `DRLG_LevelCreate` after its
  `RNG_SeedInit` and after the create dispatch; LI0/LI1 `sub_006424A0_LevelInit` after its re-seed and after each
  build; RC `DRLG_RoomCreate` entry (level seed, caller); RL `sub_0066B970_LevelRoomLink` (room rect, type, `+0x04`,
  preset def and index); PIC/PICX `sub_00666ED0_PresetInstanceCreate` entry and exit; PIO
  `sub_00666EC0_PresetSetFile`; MFR/MFRX `sub_006738C0_MazePresetFile`; PRC `sub_00667ED0_PresetRoomsCreate` (index
  and the `File` cell it loads); PUR/PURX around `DRLG_PresetUnitDropRolls` at `0x00667A35` (oracle);
  MZ0/MZ1 the maze generator window (`0x00673B41`, `0x00673F44`, with the room list); OD0/OD1 the outdoor act
  generator window (`0x00675360`, `0x006750F0`); LSR/LSRX `sub_006706A0_LvlSubRoll`.
- **Procedure:**
  1. `pgrep -af tools/d2run.py` showed nothing before each run.
  2. Act I town, two seeds: `python3 -I tools/d2run.py --seed 12345 --gdb tools/gdb/drlg-gen.gdb --steps tools/gdb/enter-sp.steps --after 15 --log workspace/logs/gen-12345-town.log`,
     and the same with `--seed 777` → `gen-777-town.log`.
  3. Blood Moor: `--seed 12345 --steps tools/gdb/drlg-roomk-bloodmoor.steps --after 10` → `gen-12345-bloodmoor.log`
     (the walk makes the game build the Den of Evil, a maze level).
  4. Preset towns: `--seed 12345 --steps tools/gdb/enter-sp.steps --after 15 --game-args "-act 2"` →
     `gen-12345-act2.log` (also builds Act II's Sewers Level 1, a maze); `--game-args "-act 4"` → `gen-12345-act4.log`.
  5. Maze by waypoint, one scripted try: saves directory moved aside (`mv "$SAVES" "$SAVES.keep-gen" && mkdir "$SAVES"`),
     `workspace/samples/d2s-waypoints/smpsor-a.d2s` copied in alone, then
     `--seed 1 --steps tools/gdb/drlg-gen-catacombs.steps --after 10` → `gen-1-catacombs.log`. The game stayed on
     the main menu (screenshot `workspace/logs/gen-catacombs-enter.png`: the SINGLE PLAYER click was lost),
     so no level was built. Saves directory restored; not retried (see Pending).
  6. Check: `python3 -I tools/drlg.py gen workspace/logs/gen-12345-town.log workspace/logs/gen-777-town.log workspace/logs/gen-12345-bloodmoor.log workspace/logs/gen-12345-act2.log workspace/logs/gen-12345-act4.log`.
- **Observed:**
  ```
  gen-12345-town      40 levels created; LevelInit by DrlgType: {2: [1, 1], 3: [2, 2, 3, 3]}
  gen-777-town        40 levels created; LevelInit by DrlgType: {2: [1, 1], 3: [2, 2, 3, 3]}
  gen-12345-bloodmoor 40 levels created; LevelInit by DrlgType: {1: [8, 8], 2: [1, 1], 3: [2, 2, 3, 3]}
  gen-12345-act2      19 levels created; LevelInit by DrlgType: {1: [47, 47], 2: [40, 40, 50, 50], 3: [41, 41]}
  gen-12345-act4      10 levels created; LevelInit by DrlgType: {2: [103, 103], 3: [104, 104]}
  levels created 149 (DrlgType 1: 33, 2: 48, 3: 68); LevelInit 32 (1: 4, 2: 12, 3: 16)
  RoomCreate modelled (one level draw) 1858; inside the maze window 34
  PresetInstanceCreate: preset level 12 (4 draw, 8 Files 0), outdoor cell 914 (830 draw, 84 Files 0),
    maze room 34; outdoor index from the cell 914; maze index forced 4, kept 12, rotated 18 (16 first-use draws)
  preset files checked 960 (Files/named: 0/2 2, 0/3 4, 0/4 86, 1/1 400, 2/2 34, 3/3 76, 3/4 46, 3/5 274,
    4/4 6, 5/5 20, 6/6 12); preset level index changed after create: level 1 x6, level 40 x2
  oracle sub_00667620 (level seed) 52 calls, 2 drew; oracle windows: maze 4, outdoor 16
  LvlSubRoll 466 (408 with 6 records, 58 with 7)
  gen: 14545 checks, 0 mismatches
  ```
  Checks: `Init(base + id)` at LC0 and LI0; the create-time index and seed (LC1); the level seed before every
  RoomCreate outside the oracle windows and at every RL, with `room+0x04 = step(Init(level.lo)).lo`; seed in
  and out of every PresetInstanceCreate and its index; every MazePresetFile index and seed; the index and the
  `File` cell at every PresetRoomsCreate; the seed into each oracle; the seed at the end of each build; the room
  count of each build; rows-then-columns order of each 8×8 preset split and of the out rooms; the maze
  conversion order against the room list; every LvlSubRoll mask and room seed.
- **Raw logs:** `workspace/logs/gen-12345-town.log` (sha256 `8d85cf02…7adb`), `gen-777-town.log` (`b83e3af9…498f`),
  `gen-12345-bloodmoor.log` (`90ecc5b6…8961`), `gen-12345-act2.log` (`981f851b…5f49`), `gen-12345-act4.log`
  (`a7c8707f…9b01`); the failed try `gen-1-catacombs.log` (`184885c1…e45c`, no events) and its screenshots
  `gen-catacombs-{enter,menu,arrive}.png`.
- **Deviations:** the scripted maze levels are Den of Evil and Sewers Level 1, which the game built on the way
  (Blood Moor walk, Act II start). The plan's waypoint maze (Catacombs) was played by the owner (addendum below).
- **Addendum 2026-10-12: owner-played Catacombs entry (was § Pending).**
  - *Save:* `workspace/samples/d2s-owner/smpsor-l50.d2s`. It is the smpsor-a waypoint sample (normal waypoints 0, 2,
    6, 8) raised to a level-50 sorceress with
    `python3 -I tools/d2s.py setstats <excel> smpsor-a.d2s smpsor-l50.d2s 4=245 5=49 6=22784 7=22784 8=34048 9=34048 10=31488 11=31488 12=50 13=47116709`.
    It was copied alone into an emptied saves directory as `smpsor.d2s`. The `seedtest.*` files were restored afterwards, sha256-identical.
  - *Command:* `python3 -I tools/d2run.py --seed 1 --sound --gdb tools/gdb/drlg-gen.gdb --after 2400 --log workspace/logs/gen-1-catacombs-owner.log`
    (`--sound` omits `-ns`). The window was moved to a visible workspace. The owner played Single Player, Normal:
    waypoint to Catacombs Level 2, then down to Levels 3 and 4. Ended with `wineserver -k`.
  - *Check:* `python3 -I tools/drlg.py gen workspace/logs/gen-1-catacombs-owner.log` (log sha256 `229ebbeb…37be`):
    ```
    levels created 52 (DrlgType 1: 16, 2: 20, 3: 16); LevelInit 20; maze generator windows 8;
    maze preset conversions 8; sub_006738C0 first-use RangeB draws 42, rotations 73
    gen: 6608 checks, 0 mismatches
    ```
  - *Checker fix:* the first check gave 226 mismatches, all in rebuilds of the same level object. Level 35 was
    built three times (objects `0x41353216`, `0x41366528`, `0x41366528` again), level 36 likewise, level 34 twice:
    the game unloads a level and runs LevelInit again on re-entry, and repeats the identical first-use draws and
    indices. `tools/drlg.py` had kept the `sub_006738C0` counters across builds; it now resets them at each LI0
    (commit `6f335bd`). The five scripted logs still give 14545 checks, 0 mismatches.
  - *Conclusion:* the maze dispatch tags of drlg/0003 stand, now with the plan's waypoint case. The rotation
    counters are per build, and a rebuilt level repeats its room sequence, `[C]`.
- **Conclusion:** promotes in [drlg/0003](0003-generator-dispatch.md) to `[C]`: the two `DrlgType` dispatches and
  the re-seed, the level-seed draws of each generator in order (with `DRLG_PresetUnitDropRolls` and the
  maze and outdoor generators as boundary oracles), the preset file index (draw, overrides, maze rotation, the
  `Files` operand), the room-creation order of the preset split and the outdoor cells, the maze conversion order,
  and `sub_006706A0_LvlSubRoll`.
- **Addendum 2026-10-14: maze window replay (plan 0022 Phase 1).** No new run. The logs above were replayed against
  the static reading of [drlg/0006](0006-maze.md) with
  `python3 -I tools/maze_replay.py workspace/merged/data/global/excel workspace/logs/gen-12345-bloodmoor.log workspace/logs/gen-12345-act2.log workspace/logs/gen-1-catacombs-owner.log`
  (`tools/maze_replay.py` sha256 `e47128c7641eaf58…`). For each `MZ0`→`MZ1` window it checks the level seed after
  the window and the logged room list: the order, `Def`, forced index and each rectangle relative to the bounding box.
  The first room's seed comes from the `RC` before `MZ0`.
  ```
  windows 12 mismatches 0     (levels 8 x2, 47 x2, 34 x2, 35 x3, 36 x3)
  ```
  Negative controls on scratch copies: dropping the merge draw gives 8 mismatching windows, dropping the theme
  swaps 10, and replacing the probe by a test without the room creation 2. *Conclusion:* placement, growth, merge,
  `Def` from exits, the finder probes, the special placement and the theme pass are `[C]` for types 3, 10 and 13 on
  normal difficulty ([drlg/0006](0006-maze.md)).
- **Addendum 2026-10-14: outdoor window replay (plan 0026 Phase 1).** No new run. Every log under `workspace/logs/` with an
  `OD0` line (63 logs from this run, run:2026-10-13-drlg-preset, run:2026-10-13-mon-spawn, run:2026-10-14-mon-special and
  run:2026-10-14-collision; `L` below is that list, `grep -l '^OD0' workspace/logs/*.log`) was replayed against the static
  reading of [drlg/0008](0008-outdoor.md):
  ```
  python3 -I tools/outdoor_replay.py workspace/merged workspace/install/app/game.exe $L
  windows 106, mismatches 0          (Acts I, II, IV, V: 19 levels; 294 windows with -v)
  python3 -I tools/jungle_replay.py workspace/merged/data/global/excel workspace/install/app/game.exe $L
  windows 76, mismatches 0           (Act III: levels 76-79)
  ```
  (`tools/outdoor_replay.py` sha256 `6bc8bde5fff3ea11…`, `tools/jungle_replay.py` sha256 `4614258f15877648…`.) Per window the
  scripts model the level rect, links, adjacency list and outdoor flags from the map seed (the act link builder, or Act III's
  jungle layout on the act seed), run the window from the `OD0` seed, and compare the `OD1` seed, every preset anchor after
  `OD1` (`Def`, position, file index; grid0 flags for Acts I, II, IV, V) and, for Acts I, II, IV, V, every out-room rectangle.
  For map seed 12345 the jungle layout takes 119 act-seed steps, the count of run:2026-10-11-seed-tree. *Conclusion:* the
  outdoor generators of the logged levels (2–7, 17, 41–45, 76–79, 104–106, 108, 110–112) are `[C]`, with the branch coverage
  and the unreached paths listed in [drlg/0008 § 13](0008-outdoor.md#13-reading-check-the-logged-windows).
- **Addendum 2026-10-16: plan 0038 batch S4a (static, no new session; `tools/sweep_s4a.py` sha256 `fafe0406c61b4363…`).** Scans and counted re-runs of `tools/drlg.py gen`
  (unchanged) by `tools/sweep_s4a.py` over the gen-family logs of this run, run:2026-10-15-drlg-maze,
  run:2026-10-15-drlg-outdoor and run:2026-10-15-acts-3-5. The scans read every log of the drlg and objects runs.
  Commands: `python3 -I tools/sweep_s4a.py ltype`, `… lsr`, `… lc1`, `… outroom`. Observed (trimmed):
  ```
  ltype   +0x1C0 = Levels.LevelType in LC0 5170, LI0 2047, RRESEED 5954 (123 levels, 108 logs); 10 486 early RRESEED
          lines carry no type
  lsr     LSR with SubType and SubTheme -1: 1636, seed unchanged and mask 0 in all; typed calls 14 830, all drew;
          levels.txt: no SubType without a record, no SubTheme above 4, one level with a single -1 (120)
  lc1     creations with no draw: DrlgType 1 1378 of 1378, 3 2500 of 2500; DrlgType 2 drew 1114, not 178 (Files 0)
  outroom out rooms predicted 11 516; maze builds 393 (LevelInit DrlgType 1), rotations 2424, first uses 1648;
          windows of 41 / 45 / 46: 20 / 24 / 8 (44 with ODD); gen mismatches 0
  ```
  Conclusion: [drlg/0003 § Plan 0038 batch S4a](0003-generator-dispatch.md#plan-0038-batch-s4a-2026-10-16).

## run:2026-10-13-drlg-preset

- **Question:** (plan 0016 Phase 2) Does the preset-unit model of [drlg/0004](0004-preset-units.md) reproduce,
  bit-exactly and with no boundary oracle, every instance unit list after the keep/drop rolls (both callers, with the
  seed in and out), after `PresetRoomLoadDs1` (centre monster, client river objects) and before and after
  `PresetUnitsToRoom`, and every room unit list the server walks? And for the three Phase 1b contradictions: does
  `Populate` 0 stop preset spawns, who reads the `Logicals` boxes, and who reads `PopPad`?
- **Setup:** the ADR-0003 harness as in run:2026-10-12-drlg-gen (game dir `workspace/runtime/game/`, prefix
  `workspace/wineprefix`, display `:7`), wine 11.17, GNU gdb 17.2. Map seed by `-seed N`.
  - *Loggers:* `tools/gdb/drlg-preset.gdb` sources `tools/gdb/drlg-gen.py` (unchanged, `5aebdb84…16e2`) and
    `tools/gdb/drlg-preset.py` (new tags PSL, PRR/PRRX, PLD/PLDX, PTR0/PTR1, RPU, PSP, RPL, L27/L27X, LIP; header of
    the file). `drlg-preset-poppad.gdb` and `drlg-preset-logicals.gdb` add `tools/gdb/drlg-preset-wp.py` (WPSET/WPHIT
    hardware read watchpoints, POPR/POPU/POPS, LGB, LGW). Final sha256: `drlg-preset.py` `518f572c…d134`,
    `drlg-preset-wp.py` `13f598df…21d8`, `drlg-preset.gdb` `e1ebdfea…6f2b`, `drlg-preset-poppad.gdb` `6018cdbe…3016`,
    `drlg-preset-logicals.gdb` `ed90eff8…d5ce`. Versions during the run (only tags were added, no tag changed):
    the FLG and PUC tags of `drlg-preset.py` were added after the Act III play, so the logs before
    `preset-play-act4.log` have none. `drlg-preset-wp.py` placed its box watches on the first `Logicals` 1 room of
    levels 103/109 in `preset-12345-act4-logicals.log`, and on the player's box (LGW) in the five play logs.
  - *Model and checker:* `python3 -I tools/drlg.py gen` (sha256 `92dc880f…9fbc`; tables from `workspace/merged`,
    `g_Ds1ObjectIds` from the pinned `game.exe`). Default: `DRLG_PresetUnitDropRolls` modelled.
    `--preset-oracle` restores the plan 0008 oracle.
  - *Characters:* `python3 -I tools/preset_saves.py workspace/runtime/p16chars` (sha256 `0cf05962…be44`) writes
    `act1..act5/smpsor.d2s`: the `exphell` Sorceress of run:2026-10-12-mon-pool-p2 (level 50, progression 10), every
    waypoint bit in every difficulty, the three difficulty bytes = act − 1 with bit 7 clear (sha256 first 16 hex:
    act1 `3915ce4d7b9f4ea9`, act2 `895a15f388e95f61`, act3 `7ed27ba34aaa01b8`, act4 `7d81c8316c32925d`, act5
    `cbecb805f6c73edd`). `tools/d2s.py survey` reads all five cleanly. Waypoint tabs of acts II–V stay hidden (no
    quest progress, docs/formats/d2s.md § Quests), so only Act I could travel by waypoint.
  - *Saves directory:* only through `tools/saves.py`: `aside p16`, then before each game `restore p16`, `aside p16`,
    `install p16 workspace/runtime/p16chars/actN/smpsor.d2s`; `restore p16` at the end (all seven `seedtest.*`
    sha256 match, no aside open).
- **Procedure:**
  1. Before each game `pgrep -af 'tools/d2run[.]py'` was empty. Each `saves.py` call ran as its own command (a chained
     command line containing `tools/d2run.py` makes its liveness check refuse).
  2. Scripted town entries, 20 games: for each `act:difficulty:seed` in `1:normal:12345 2:normal:12345
     3:normal:12345 4:normal:12345 5:normal:12345 1:normal:777 2:normal:777 3:normal:777 5:normal:777 2:normal:1
     2:normal:2 2:normal:3 2:nightmare:4 3:hell:5 5:hell:6 1:nightmare:7 2:normal:8 2:normal:9 2:hell:10 4:hell:11`,
     install `actN`, then `python3 -I tools/d2run.py --seed S --gdb tools/gdb/drlg-preset.gdb --steps
     tools/gdb/enter-D.steps --after 15 --log workspace/logs/preset-S-actN-D.log` (`enter-normal/nightmare/hell.steps`:
     main menu → Single Player → OK → the difficulty button).
  3. `PopPad` case: `act5`, `--seed 12345 --gdb tools/gdb/drlg-preset-poppad.gdb --steps
     tools/gdb/preset-harrogath-pop.steps --after 8` (walk west into Harrogath's pop rectangle and back) →
     `preset-12345-act5-poppad.log`.
  4. `Logicals` box test: `act4`, `--seed 12345 --gdb tools/gdb/drlg-preset-logicals.gdb --steps
     tools/gdb/preset-fortress-walk.steps --after 8` (a loop around the Pandemonium Fortress start) →
     `preset-12345-act4-logicals.log` (box-placement version of `drlg-preset-wp.py`, see Setup).
  5. Owner play, one game per act, Normal: `python3 -I tools/d2run.py --seed 2N --sound --gdb
     tools/gdb/drlg-preset-logicals.gdb --after 1500 --log workspace/logs/preset-play-actN.log` (N = 1..5, seeds
     21..25), the `Xwayland on :7` window moved to workspace 8, ended with `wineserver -k` when the owner said done.
     - Act I: waypoints to Outer Cloister and Catacombs Level 2, back to town and in again.
     - Act II: Lut Gholein sewers, then the Rocky Waste.
     - Act III: Spider Forest into the Flayer Jungle (the character died; Spider Cave, level 84, was built and
       none of its rooms activated).
     - Act IV: Fortress walls, Outer Steppes, Plains of Despair.
     - Act V: under Harrogath's roof, then the Bloody Foothills.
  6. Check: `python3 -I tools/drlg.py gen workspace/logs/preset-*.log` (27 logs).
  7. Oracle replay (ADR-0004): `python3 -I tools/drlg.py gen` on the six logs of run:2026-10-12-drlg-gen (the five
     scripted ones and `gen-1-catacombs-owner.log`), with and without `--preset-oracle`. Then `python3 -I
     tools/drlg.py roomk` on the six logs of run:2026-10-11-drlg-roomk.
- **Observed:**
  ```
  27 logs: levels created 578 (DrlgType 1: 108, 2: 140, 3: 330); LevelInit 221; rebuilt levels (LevelInit twice on
    one level object) Act I 1, 2, 12, 34, 35, 36 and Act II 41, 42, 50 (play logs)
  preset rooms reproduced 2210 (1088 with units): client copy 1416, server copy 794; act I 506, II 556, III 458,
    IV 277, V 413; levels 1 2 7 26 27 28 31 32 33 35 36 40 41 42 47 48 50 75 76 78 103 104 105 109 110 111
  instance lists checked: after the level-seed rolls 391, after the room-seed rolls 571, after PresetRoomLoadDs1 3334
  drop-roll calls: level seed 391 (34 draw), room seed 571 (10 draw)
    MonStats 204 kept 10 / dropped 10; 205 kept 6 / dropped 14; MonPlace 34 (place_group50) kept 6 / dropped 4;
    MonPlace 35 (place_group75) kept 2; object 581 kept 8 / dropped 4
  act rewrites in rolled DS1s: act index 2, 297 -> object 382 (8); act index 4, 514 -> object 461 (10)
  client river objects: Def 1 (5), 26 (3), 27 (3); centre monster: not reached
  level 27: index draw (link value 3) 6, level 27 built with that index 2
  server handover (RoomPresetUnits): 689 walks, the modelled room list is the tail of every one; units at the
    head added by other code, objects 14 15 16 23 24 25 27 64 449 and type-5 units 2 14 17..24 36 51; walk order
    non-monsters first, then monsters, in all 373 walks with spawns
  server preset spawns: monsters 286 created, 141 no unit; objects 960; type 5: 14
  RoomPopLevelId on preset rooms: Populate 0 241 (all 0), Populate 1 4097 (45 return 0: 16 with FLG at 0x0066BD92
    "next to a town room", 29 in logs without FLG lines); Populate-0 rooms: preset monster spawns 48 created
  room flag 0x800000 at 0x0066BD92: 22 flag sets on 22 distinct preset rooms (preset-play-act4 10, -act5 12; the only
    logs with FLG lines). The 16 above are RoomPopLevelId calls, not rooms: 8 of the 22 rooms were populated, two
    calls each, all 0; the other 14 had no RoomPopLevelId call. 0x0066E37E: no FLG line
  logic records: Logicals 0 -> flags bit 0 (one box), Logicals 1 -> bit 1, on 1540 preset rooms
  pop trigger positions: 6443 reproduced (PopPad 0: 5013, -4: 992, -5: 438), 168 inside a pop area, 70 where PopPad
    decides (PopPad 0 would give another result)
  gen: 123606 checks, 0 mismatches (sub_00667620 modelled)

  watch reads (WPHIT, $pc after the reading instruction):
    LvlPrest[863].PopPad +0x3C   0x00667258, 0x00667264 (322; caller 0x0061AD0C), nothing else
    LvlPrest[863].Pops +0x38     0x006679ED (2, in PresetMapScan; control)
    box +0x28 at build           0x0066C796/0x0066C7A3/0x0066CFFC (server and client; DrlgLogic.cpp code)
    client wall entry +0x10      0x004DD075 (7114, ret 0x004DD1FE); 0x00475522 (206)
    client box +0x28             0x004DD085 (54688, ret 0x004DD1FE); 0x0066CEA4 (10530, ret 0x0061B15B);
                                 0x0046E57F/0x0046E5E8/0x0046E6D4/0x0046E8A9/0x00470A4A (245 together)
    server box +0x28 (player's)  0x0066C796 only (7)

  oracle replay, run:2026-10-12-drlg-gen (6 logs):
    modelled:        drop rolls level seed 91 calls, 2 draw (204, 205 dropped)   21244 checks, 0 mismatches
    --preset-oracle: 91 oracle calls, 2 drew                                      21153 checks, 0 mismatches
  roomk (6 logs of run:2026-10-11-drlg-roomk): 520 activations, 11208 checks, 0 mismatches (unchanged)
  ```
  Checks: the room seed into every room-seed roll equals `step(Init(level lo))` from that room's `DRLG_RoomCreate`
  (the RL line). The seed out of both callers matches, as do the instance list after each caller and after
  `PresetRoomLoadDs1` (the `pending` flag, the DS1 slot), the instance and room lists around `PresetUnitsToRoom`, the
  tail of each server walk, `Populate` 0 ⇒ `RoomPopLevelId` 0, the logic flag per `Logicals`, the level-27 index and
  act seed after its draw against the logged act seed before (the act seed's earlier draws are `drlg/warps` input),
  and the pop index at every logged player position.
- **Inputs taken from the log** (named in the architect's Phase 2 review; none carries a seed):
  - the units at the head of each server walk, added by other code after `PresetUnitsToRoom` (the modelled list
    is asserted as the tail);
  - the act seed just before the level-27 draw. It is not predicted, because the earlier draws are
    `LevelLinkBuild`'s (`drlg/warps`). So the run confirms the index formula and the single step, not the draw's
    place in the act-seed sequence;
  - the room list that already exists when `PresetUnitsToRoom` runs again for a room (108 re-prepares). The
    first version of the checker took it from the log unchecked. **Re-check 2026-10-13** (review fix 2,
    `tools/drlg.py` sha256 `2487dcb4…5a43`): the room's previous modelled list is now asserted as its tail. The head
    holds 1 or 3 units added by other code in 34 rooms, and in 19 monster units the path pointer had become null in
    between, which is the one difference allowed. No re-prepare moved a unit (the instance list lost them on the
    first pass). With the 27 logs: `gen: 123714 checks, 0 mismatches` (108 checks more). run:2026-10-12-drlg-gen
    still gives 21 244 checks, 0 mismatches.
- **Logic regions:** the checker tests only `flags & 3` per `Logicals` (the builder selection) and counts the watch
  reads. The regions, boxes and wall pointers the builders produce are not reproduced.
- **Raw logs:** `workspace/logs/preset-*.log`, sha256 (first 8 … last 4): `preset-12345-act1-normal`
  `7a2897a0…9812`, `-12345-act2-normal` `4acefba8…9313`, `-12345-act3-normal` `704a6b2c…171f`, `-12345-act4-normal`
  `7ef79756…4a65`, `-12345-act5-normal` `0f4a4e1a…8b16`, `-777-act1-normal` `999e41cf…d6a4`, `-777-act2-normal`
  `33856675…355b`, `-777-act3-normal` `7583591b…664c`, `-777-act5-normal` `2fba4b38…1190`, `-1-act2-normal`
  `a7142a01…bd03`, `-2-act2-normal` `f6e856c3…4983`, `-3-act2-normal` `96a1a1e5…a4bf`, `-4-act2-nightmare`
  `88edf179…ad86`, `-5-act3-hell` `7c7723a4…7a2b`, `-6-act5-hell` `d73e9f92…6660`, `-7-act1-nightmare`
  `accd5656…6464`, `-8-act2-normal` `c8b9ff47…5806`, `-9-act2-normal` `5ca4aa17…b836`, `-10-act2-hell`
  `5b89128f…f51f`, `-11-act4-hell` `9d050a3a…3f17`, `-12345-act5-poppad` `3b9eadfc…3cae`, `-12345-act4-logicals`
  `c85c4bf4…1904`, `-play-act1` `f5eccf4c…be7c`, `-play-act2` `20a964b1…3e84`, `-play-act3` `11d92788…912a`,
  `-play-act4` `68dbedb1…9645`, `-play-act5` `d3848591…7ed4`. Screenshots `workspace/logs/preset-pop-{0,1,2}.png`,
  `preset-lg-{0..3}.png`.
- **Deviations:**
  - Waypoint travel worked in Act I only (the save's quest words are zero), so the acts II–V cases were walked from
    town. No maze preset room was activated in Act III (cave built, not entered) or Act V (none reached). Act IV has
    no maze level on the route. The maze case is met in Acts I (Barracks 28, Jail Level 3 31, Catacombs Level 2/3
    35/36) and II (Sewers Level 1/2 47/48).
  - Not reached: the room-seed draws of objects 196/261, MonStats 371/372 and `place_group25`; `place_group75`
    dropped; the Blood Moor centre monster. Those branches rest on the code; drlg/0004 keeps them inferred.
  - Population reads of the boxes were not caught: the player's box got its watches only after the room had been
    populated (LGW is placed when the player enters a box). The 29 `Populate` 1 rooms with pop level 0 in the
    Act I–III play logs predate the FLG tag, so their writer is not attributed.
  - The development logs of this session (`preset-test-act2.log`, an earlier logger with the default character)
    were discarded.
- **Conclusion:** promotes in [drlg/0004](0004-preset-units.md) to `[C]`, with no boundary oracle: the keep/drop
  rolls (order, seed per caller, the `r` tests of the ids drawn), the instance copy offsets, the act rewrites of act
  index 2 and 4 (the ids seen), `PresetRoomLoadDs1`'s once-per-instance roll, the client river objects,
  `PresetUnitsToRoom`, the server walk's order and the modelled list as its tail, `Populate` 0 → `RoomPopLevelId` 0 with preset
  monsters still spawning, `Logicals` → the builder selection (logic flag bit) and the client wall cut-away reader, the `PopPad` reader and its
  formula, the re-prepared room list, and the level-27 index formula (its place in the act-seed sequence stays `[I]`). run:2026-10-12-drlg-gen and run:2026-10-11-drlg-roomk replay with the oracle
  replaced, every seed asserted.
- **Addendum 2026-10-16: plan 0038 batch S4a (static, no new session; `tools/sweep_s4a.py` sha256 `fafe0406c61b4363…`).** The 27 logs above and the 6 of
  run:2026-10-15-acts-3-5, re-read by `tools/sweep_s4a.py`. It re-runs `tools/drlg.py gen` (unchanged; 139 032 and
  155 215 checks, 0 mismatches) with counters added. Commands: `python3 -I tools/sweep_s4a.py punits`
  (`S4A_PUNITS_SURVEY=1` for every DS1 that `lvlprest.bin` names), `… pflags`, `… pcopies`, `… dispatch`, `… warpunit`. And the
  xrefs: `GHIDRA_PROJ_DIR=<copy> tools/ghidra.sh xrefs 0x00667620` / `0x00667890`; `r2 -q -c 'aaa; axt @ 0x00667620;
  axt @ 0x00667890' game.exe`; `r2 -q -c '/x 20766600; /x 90786600' game.exe`. Observed (trimmed):
  ```
  xrefs    0x00667620 <- 0x006678E2, 0x00667A35 (both tools); 0x00667890 <- 0x0061B752, 0x0061B343 (both); no pointer
  punits   492 DS1 files in the reproduced lists (2043 in lvlprest): MonPreset kinds 1/2/0 262/16/379, type 2 v6+ id<150
           2362, paths attached 105 (117); no skip, v<6, id>=150 or dropped-path case in any file; units type 1 mode 1
           48 916, type 2 mode 0 128 951
  pflags   RL type-2 rooms 141 130: none with 0x2000000, 0x80000 iff Outdoors (119 183); PLDX 5568 all with 0x2000000
  pcopies  instance pairs, same first room 888 (seed and list equal), different first rooms 4 (seeds differ; no drawing unit)
  dispatch PSP: type 1 monster 348 / none 165; type 2 < 573 class = id 1591; > 573 another class 16; type 5 kept 21
  warpunit type-5 units of the walks at a warp cell x 5 + LvlWarp OffsetX/Y, class = Id: 21 of 21
  ```
  Conclusion: [drlg/0004 § Plan 0038 batch S4a](0004-preset-units.md#plan-0038-batch-s4a-2026-10-16) and
  [drlg/0007 § Plan 0038 batch S4a](0007-warps.md#plan-0038-batch-s4a-2026-10-16).

## run:2026-10-14-collision

- **Question:** (plan 0017 Phase 2, boundary B with R1–R3) Does the model of [drlg/0005](0005-collision.md) reproduce,
  cell for cell, each active room's collision grid at activation from the DT1 sub-tile bytes of the room and its active
  near rooms? And on the grid snapshot at pass entry plus the modelled in-pass marks, does it predict every call of
  `CollisionTest`, `LogicRegionIdAt`, `SpawnClassCellTest`, `NearWarpTest` and `SpawnPosOnTile` in the room-population
  pass? Also: the § 12 required cases, R1 (level seed and active rooms around `NearWarpTest`), R2 (a placement accepted on
  a cell marked only `0x100`), R3 (the snapshot against the activation model), C1 (`deadCol` corpses) and C2 (Missiles
  `Collision` marks `0x40`).
- **Setup:** the ADR-0003 harness (`workspace/runtime/game/`, prefix `workspace/wineprefix`, windowed on display `:7`), wine
  11.17, GNU gdb 17.2. Play was **agent-driven** (scripted `tools/xdrive.py` input decided from screenshots; no human play), by
  the owner's choice. Map seed `-seed 2026` in every session; expansion game, Normal difficulty.
  - Logger `tools/gdb/collision.gdb` (`853f0a76…9bc1ce5`), which sources `tools/gdb/drlg-gen.py` (`91feac40…5c970580`),
    `tools/gdb/drlg-roomk.py` (`d6b2e6e0…6340ce5be`), `tools/gdb/mon-spawn.py` (`6ad436e8…a2438352`) and
    `tools/gdb/collision.py`. Two versions of the last: sessions 1–2 `1b10c4cc…2eefc1b5e` (snapshot of the room and its
    near rooms, floors of the room only); sessions 3–7 `1d5d4b25…e88449f` (the version committed: the snapshot also holds
    the near rooms of the near rooms and every snapshot room's floor entries, added after session 2 showed a frog demon
    placed on a neighbour room's tile).
  - Model and checker `tools/collision.py` (`549b2574…b9ec471`) with `tools/monspawn.py` (`85053441…24280ed8`), which runs
    `tools/drlg.py` (`eb9fe18b…8a60ee65`) and `tools/monpool.py` on the same logs; DT1 files through `tools/dt1.py`
    (`45e66935…5f636aca`) from `workspace/merged`; tables by position from `workspace/merged/data/global/excel`.
  - **Characters** (tool-built inputs, ADR-0003; installed and restored only through `tools/saves.py`, tags `colls1` and
    `colls2`): `CollSorc.d2s` (`28af8e29…c66588257`), built with
    `python3 -I tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/collsorc.json workspace/samples/d2s-owner/smpsor-l50.d2s workspace/runtime/collision-chars/CollSorc.d2s`;
    `tools/d2s_recipes/collsorc.json` (`70a84af6…f944e67`) is `novasorc.json` with name `CollSorc`, the act byte on Act IV
    (`difficulty` `[131, 0, 0]`, so the game starts next to the Pandemonium Fortress waypoint), the `quests: all` key,
    Fire Wall 20 and Warmth 20, mana 1500, left button Fire Wall, right button Teleport. Sessions 5–7 used `CollNova.d2s`
    (`b164aec5…3f0cdf643`) from `tools/d2s_recipes/collnova.json` (`88027823…d15e851`): the same with name `CollNova`, left
    Teleport (cast with Shift), right **Nova**. That change follows the owner's feedback during session 4: Fire Wall kills
    poorly and needs aim, Nova needs none; teleport hops were shortened from about 260 to 180 screen pixels so that fewer
    targets land on unstandable ground. The game rewrites the save on an act change, so before each session the build was
    installed again (`tools/saves.py install`).
- **Logged** (header of `tools/gdb/collision.py`): TL (each DT1 tile record seen: file, index, key, flags16, the 25
  sub-tile bytes); CB at `COLL_MapBuild`'s end `0x0064C9FF` (room, near list, every near room's floor / wall / shadow entries,
  the cells); TCU (`sub_0064C860_TileCollisionUpdate`); CM (every `COLL_PatternMark` / `PatternUnmark` / `RectOrWH` / `RectClearWH`
  / `SizeMark` / `SizeUnmark` call from the room driver's RW1 point to the pass exit); SN at `0x0054EC91` (the snapshot: the
  rooms within two hops, each with rect, near list, cells, logic record as box ids, floor entries; the level seed); NWP
  `0x0054DB96` and NWW `0x0054DBEE` (warp points, `WarpDist`, the type-11 point); NW0 / NW1 around the `NearWarpTest` call
  (level seed `+0x1C4`, the level's active rooms); LG0 / LG1 / LG2 in `sub_0066D110_LogicRegionsFromDs1` (inputs before the
  flood, id grid and boxes after it, boxes after the neighbour merge); DC / DCX / DCR at the `deadCol` tests `0x004B05DB` /
  `0x004B09FB` and after the corpse call (5×5 cells), and again at later passes; MS / MSX at `PATH_SetMarkMask` with mask `0x40`
  (5×5 cells before and after). Plus all plan 0014 and plan 0008 tags.
- **Procedure:**
  1. `tools/saves.py aside colls1`, `install colls1 …/CollSorc.d2s` (later `restore colls1`, `aside colls2`, `install colls2
     …/CollNova.d2s`). Before each session `pgrep -af 'tools/d2run[.]py'` was empty.
  2. Per session: `MONSPAWN_WATCH= python3 -I tools/d2run.py --seed 2026 --gdb tools/gdb/collision.gdb --steps
     tools/gdb/enter-normal-act4.steps --after 7200 --log workspace/logs/<log>`; then the waypoint (window click 712,62),
     the act tab and the row; then scripted teleport walks in the eight directions with Fire Wall rings (sessions 1–4) or
     Nova casts (sessions 5–7), and belt potions. Each session ended with `wineserver -k` on the prefix and
     `pkill -f 'tools/d2r[u]n.py'` (no timer left; `pgrep` empty).

     | log | character | waypoint | levels with passes |
     |---|---|---|---|
     | `collision-s1-2026-normal.log` | CollSorc | City of the Damned | 106, 105 |
     | `collision-s2-2026-normal-a3.log` | CollSorc | Great Marsh (cut short to change the logger) | 77 |
     | `collision-s3-2026-normal-a3.log` | CollSorc | Great Marsh | 77, 76 |
     | `collision-s4-2026-normal-a3.log` | CollSorc | Flayer Jungle | 78, 76 |
     | `collision-s5-2026-normal-a2.log` | CollNova | Lost City | 44 |
     | `collision-s6-2026-normal-a1.log` | CollNova | Jail Level 1 | 29 |
     | `collision-s7-2026-normal-a1.log` | CollNova | Stony Field | 4, 38 |
  3. `tools/saves.py restore colls2`: the seven `seedtest.*` files back, every sha256 equal to the manifest, no aside left
     (`status`: aside none, harness idle).
  4. Check: `python3 -I tools/collision.py check workspace/logs/collision-s1-2026-normal.log workspace/logs/collision-s2-2026-normal-a3.log workspace/logs/collision-s3-2026-normal-a3.log workspace/logs/collision-s4-2026-normal-a3.log workspace/logs/collision-s5-2026-normal-a2.log workspace/logs/collision-s6-2026-normal-a1.log workspace/logs/collision-s7-2026-normal-a1.log`.
  5. The plan 0014 logs again: `python3 -I tools/collision.py check workspace/logs/monspawn-s1-12345-normal-a1.log workspace/logs/monspawn-s2-12345-normal-a2-5.log workspace/logs/monspawn-s3-1-hell-a1.log`.
- **Observed** (step 4, trimmed):
  ```
  drlg gen and roomk on all seven logs: 0 mismatches
  passes: empty 131, gate 143, populated 86; creations 410; levels 4, 29, 38, 44, 76, 77, 78, 105, 106
  predicted by the collision model: CollisionTest 1764, LogicRegionIdAt (pos pick) 1046, LogicRegionIdAt (ring) 1619,
    NearWarpTest 1645, SpawnClassCellTest 1782, SpawnPosOnTile 195
  oracle SpawnPosOnTile (model needs floor entries) 1 call (session 2, logger v1)
  CollisionTest calls by (size, mask): (2, 0x3c01) 1276, (3, 0x3c01) 478, (3, 0x3f11) 10
  CollisionTest rejections with result bit 0: 956, bits 1/2/5: 94 (83 results are exactly 0x27), bit 10: 12, bit 12: 306
  tests rejected only by in-pass marks: size 2 on size-2 marks 142, size 2 on size-3 marks 4, size 2 on both 4,
    size 3 on size-3 marks 107, size 3 on size-2 marks 4, size 3 on both 1
  R2: accepted placements on a cell whose value is exactly 0x100: 67
  in-pass creations marked: pattern 1: 271, pattern 2: 135, pattern 5: 4; post-create pattern refresh 5 -> 1: 4
  TL 5600 tile records checked against the DT1 files (74 files), 0 differ
  activation dumps compared 1439 (2 343 400 cells), 0 differ; DRLG room type 1: 141, type 2: 1298;
    LvlTypes 2 (Act 1 Wilderness) 286, 3 (Act 1 Cave) 2, 7 (Barracks) 1, 8 (Jail) 22, 11 (Tristram) 1, 16 (Act 2 Desert) 266,
    20 (Act 3 Town) 57, 21 (Jungle) 453, 24 (Dungeon) 10, 26 (Act 4 Town) 147, 27 (Mesa) 191, 28 (Lava) 3
  activation dumps of Logicals 1 rooms 413; Logicals 1 floods compared 378 (id grid, nBoxes, level counter, box list), 0 differ
  activation: entry flag bits 0x01 over a tile 21176, 0x10 4962, 0x11 12 (0x04 never)
  activation order: rooms activated after their right/bottom neighbour 702; border tiles stamped into no grid 5970;
    cells of the earlier room those tiles would have changed 112
  TileCollisionUpdate calls 4, each with the tile's top-left in no active room (nothing written)
  SpawnClassCellTest: BaseId 206 (crownest) offset-cell tests 28; BaseId 298 passes with flag 1: 71
  SpawnPosOnTile: tile found 24, tile centre holds 0x100 (or no room) 53; spawnCol 1 creations on a tile 15
  NearWarpTest: near a warp point 543, type-11 lookups 1102, near the type-11 point 56
  R1: calls asserted 1646; Position 0 lookups, level seed kept 1083; Position level 38, level seed stepped once 20;
    waypoint room activated inside the call (a CB inside the call, the room holding the type-11 point): 17 (levels 4, 44, 76, 106)
  C1: deadCol 0 deaths re-marked as a 0x8000 plus 396; deadCol 1 deaths 12 (classes 273 gargoyletrap, 403 and 404 trappedsoul),
    each keeping its 0x100 plus, mark mask and pattern
  C2: Collision missiles (class 69 firewall, size 1) marked 0x40 as SizeMark(1): 5702
  R3: 360 pass rooms; cells differing 1685 before the window marks, 65 after (1620 explained by the logged preset and object
    marks); rooms exact 345, with residue 15; residue bits +0x0080 32 cells, +0x0100 18, +0x1080 8, +0x1100 7
  monspawn: 75756 checks, 0 mismatches; collision: 20537 checks, 0 mismatches
  ```
  Step 5: `monspawn: 114189 checks, 0 mismatches` (110302 in the plan 0014 record; the difference is the new
  SpawnClassCellTest predictions). The plan 0014 logs hold no grid snapshot, warp points or logic boxes, so `CollisionTest`
  (3903 calls), `LogicRegionIdAt` (1384 + 3439), `NearWarpTest` (1919) and the 21 `SpawnClassCellTest` calls of class
  `crownest1` stay value oracles there; the other 3887 `SpawnClassCellTest` calls are predicted (classes outside the five
  `BaseId`s pass without a test). Those logs are covered by this run instead.
- **Required cases:**

  | Case | Result |
  |---|---|
  | § 12: a size-3 class next to a size-2 one | reproduced: 9 tests rejected only by marks of the other size (and 249 by the same size) |
  | § 12: a wraith group (pattern 5) | reproduced: 4 `wraith2` creations in Jail Level 1; see the post-create refresh below |
  | § 12: a crow nest (`0x3F11`, (x, y+3)) | reproduced: 28 offset-cell tests and 10 `0x3F11` tests (Stony Field) |
  | § 12: a frog-demon level for `SpawnPosOnTile` | reproduced: 195 calls in levels 77 and 78, 15 creations |
  | § 12: a `Logicals` 1 room | reproduced: 413 activation dumps, 378 floods |
  | § 12: a room whose left or top neighbour activated after it | reproduced: 702 rooms, 5970 border tiles in no grid |
  | R1: level seed and active rooms around every `NearWarpTest` | reproduced: 1646 calls; Position level with population (Tristram, 38): 20 calls step the level seed once |
  | R2: a placement accepted on a cell marked only `0x100` | reproduced: 67 |
  | R3: snapshot minus the activation model | reported above (non-gating) |
  | C1: a `deadCol` 1 corpse keeps `0x100` | reproduced: 12 deaths (immediately after the corpse call); later re-dumps: 18 still `0x100`, 24 not (the corpse is removed later; removal not traced) |
  | C2: a `Collision` missile marks `0x40` | the mark is reproduced (5702); a placement test whose mask reads `0x40` is **unreached** (no `spawnCol` 1 ring placement and no `suckernest1` in the run) |
  | bits read by the spawn masks | exercised as rejection bits: 0, 10, 12 (and 1, 2, 5 through `0x27`); `0x100` through `SpawnPosOnTile`'s centre test; unreached as rejection bits: 4, 8, 9 (`0x3F11` tested, never rejected), 11, 13, and 6, 7 (`0x01C0`) |
  | entry flags `0x02`, `0x40`, `0x80` | `0x02` → grid `0x10` and `0x40` → `0x01` reproduced; `0x80` → `0x04` unreached |
  | `TileCollisionUpdate` clear and re-stamp | unreached (4 calls, none with the tile in an active room) |
  | `SpawnClassCellTest` `BaseId`s 228, 334, 528 | unreached |
  | sizes 0 and 1 in `CollisionTest` | unreached as placement tests (the cell test is exercised through `PlusTest` edges and `SpawnPosOnTile`) |
  | `flying` spawn branch (Phase 1b gap) | unreached (no flying class with `spawnCol` 0 placed on a bit-0 cell) |

- **Surprises:**
  - A **wraith's mark changes after creation.** `SUnitCreate` marks pattern 5 (two `UNIT_CollMark` calls, both returning to
    `0x006494D5`). Then the post-create alignment setter `0x005543B0` calls `0x00554340`, which calls `0x00649CA0`: `UNIT_CollUnmark`,
    pattern = `PATH_PatternFromSize(size)`, `UNIT_CollMark`. `PATH_PatternFromSize` has no wraith case, so the wraith ends the
    creation with pattern 1 (plus and the `0x1000` centre). Every creation shows this unmark / re-mark pair (410 of 410).
  - **`NearWarpTest`'s waypoint lookup activates a room inside the population pass** in Position 0 levels as well: 17 times the
    room holding the type-11 point was re-seeded, built and activated (RRESEED … AROOM, CB) between NW0 and NW1, with the
    level seed unchanged. In Tristram (`Position` 1) the lookup stepped the level seed once per call (20 calls).
  - A frog demon placed by `SpawnPosOnTile` can land in a near room. Its group and minions then draw from that room's seed (taken
    from the log at its first request, 2 times, a seed oracle) and test with that room as the hint.
- **Raw logs:** `workspace/logs/collision-s1-2026-normal.log` (sha256 `a3326ae5…1b9ec471`),
  `collision-s2-2026-normal-a3.log` (`2d0ff4a0…fd69d06`), `collision-s3-2026-normal-a3.log` (`7599c033…2dec807a`),
  `collision-s4-2026-normal-a3.log` (`7514e9f8…762ecbce`), `collision-s5-2026-normal-a2.log` (`81133827…f738293`),
  `collision-s6-2026-normal-a1.log` (`2d96c1fc…d41d3`), `collision-s7-2026-normal-a1.log` (`041c6f5e…ccaf`).
- **Deviations and limits:**
  - Not part of the record: `collision-dev-1.log` (logger development: `NearWarpTest` logged `WarpDist` from the wrong
    register, fixed before session 1), `collision-dev-s4-docks.log`, `collision-dev-s4b-docks.log`, `collision-dev-s4c-docks.log`
    (sessions that landed in Kurast Docks: the save had been rewritten on an act change) and `collision-dev-s8-wp-refused.log`
    (the Arcane Sanctuary and Canyon of the Magi waypoints did not respond to the menu click with this save, so no session
    reached level 74 or 46).
  - Oracles (ADR-0004), named as boundary B requires: **the grid snapshot at pass entry** (the room and the rooms within two
    hops: cells, near lists), the logic-box grids of those rooms (DRLG state; the flood that builds them is checked separately
    at LG1), the warp points and the type-11 point (owner `drlg/warps`), the tile choice of each entry and the entry flags at
    activation (owner `drlg/room-tiles`; every TL record matches its DT1 file), the barrier grid of the flood
    (`LOGIC_BarrierGridBuild` not modelled), the seed of another room at its first request (2), and the plan 0014 oracles
    (presets / restore / objects window, mod handlers, special mods).
  - Only Normal difficulty, one map seed, no classic game, no multiplayer.
- **Conclusion:** [drlg/0005](0005-collision.md) §§ 1, 3–5 (monster, corpse and missile marks), 7, 8 (`BaseId`s 206, 298 and
  the pass-through), 9 and 10 are reproduced bit-exactly, `[C]` under the oracles named; the four position predicates of
  [monsters/0002 § 6](../monsters/0002-room-population.md#6-placement-monspawntry) and `SpawnPosOnTile` are no longer oracles
  in logs that carry the snapshot. The wraith claim of drlg/0005 § 5 is corrected (post-create refresh).
  (run:2026-10-14-collision, fn:sub_0064D9B0_CollisionTest@0x0064D9B0, fn:sub_005B2700_SpawnPosOnTile@0x005B2700, fn:sub_00649CA0_PathPatternRefresh@0x00649CA0)
- **Addendum 2026-10-15: roomk on the predicted out-room grids, and the tile-entry flags (plan 0027 Phase 2).** No new
  game run. `tools/drlg.py gen` now runs the roomk passes in every log with `OD0` and `LSUB` lines, with the type-1 grids
  of each room's first `LSUB` taken from the drlg/0008 § 16.4 prediction (the logged grids stay the check), and in logs
  with `TL`/`CB` lines it compares every activation dump's tile-entry arrays with the model
  ([drlg/0002 § Entry flags](../drlg/0002-room-build-draws.md#entry-flags-in-full-and-the-entry-chains-plan-0027-phase-2-2026-10-15)).
  Logs of this record used: `collision-s4`, `s5`, `s7` (the three with `OD0`). Command: `python3 -I tools/drlg.py gen <those logs>`. Observed:
  ```
  roomk inside gen: 763 activations, 26 802 checks, 0 mismatches
  type-1 rooms: first LvlSub grids from GenModel's prediction  141
  entry flags compared (walls, floors, shadows of every near room at each CB)  266 664
  gen: 34 313 checks, 0 mismatches
  ```
  The collision reruns are unchanged: `python3 -I tools/collision.py check workspace/logs/collision-s[1-7]-*.log`:
  75 812 population and 20 537 collision checks, 0 mismatches.
  Conclusion: the room-tiles model takes no type-1 grid from these logs any more, and the entry flags are `[C]`
  (drlg/0002). Together with the other four record families: 40 logs, 12 974 activations, 434 721 roomk checks, 2884 type-1
  rooms, 3 684 791 entries, 0 mismatches (the 38 logs of the plan 0026 addendum plus `objects-s29`/`s30`).
  (fn:sub_0066DB20_RoomTileSetFlags@0x0066DB20, fn:sub_0067D2D0_OutRoomGridPrepare@0x0067D2D0)
- **Addendum 2026-10-16: plan 0038 batch S4a (static, no new session; `tools/sweep_s4a.py` sha256 `fafe0406c61b4363…`).** The seven logs above and the 29 of
  run:2026-10-15-objects (`tools/gdb/objects.gdb` carries the collision tags), re-read by `tools/sweep_s4a.py`. It
  imports `tools/collision.py`, `tools/drlg.py` and `tools/dt1.py` and changes none. Commands: `python3 -I
  tools/sweep_s4a.py flood`, `… logic`, `… barrier`, `… bits`, `… orpath`, `… tl`, `… nww`; unit tests `python3 -I
  tools/test_sweep_s4a.py` (9, OK). Regression: `python3 -I tools/collision.py check` gives 75 812 and 20 537 checks on
  these logs and 279 524 and 28 177 on the objects logs, 0 mismatches. Observed (trimmed):
  ```
  flood   1475 floods; rule entries read 30, 28 sensitive to one flipped bit; orientations at barriers 16, all sensitive
  logic   LG0 base predicted 1475 of 1475 (76 after a single box; 74 single boxes after a flood); LG2 box ids after the
          neighbour merge 1475 of 1475 (1349 relabelled); SN box grids 4478 and single-box records 9333 (first id 1);
          control with the logic record kept at RoomTilesRelease: 200 mismatches
  barrier LG0 barrier grids rebuilt from the room-tiles model's entries 1475 of 1475 (611 with tiles only from a near
          room's bit-2 node; 641 walls excluded only by their tile's flags16 bit 2)
  bits    5434 dumps: bit 1 195 834, bit 2 1 446 257, bit 4 775 275, bit 5 10 139 cells, no unit bit; DT1 bit 4 only in
          tombsteps.dt1; CM masks 0x806 12, 0x404 21, 0x200 (RectOrWH 1x1, ret 0x00620ACF) 85; patterns 0/1/2 by SizeX
          39/7045/2129; 0x40 marks 5850 (size = Missiles +0x18A; size 2 a plus, 34 cells unlike a 2x2 rect);
          SN 0x80 footprints: plus with 0x1000 centre 1162, cut by the room edge 580, other 0
  orpath  dumps equal to the OR build 5434 of 5434; overwrite build would differ in 3789 (641 892 cells)
  tl      TL records 24 035 (7111 tiles, 150 files): memory +0x06 = file sound | animated << 8 in all
  nww     type-11 points: Position 0 levels, the waypoint object's tile 26; Position set, a slot-33 cell 1; no source
          logged 5 (levels 4, 44, 110; Tristram twice)
  ```
  Conclusion: [drlg/0005 § Plan 0038 batch S4a](0005-collision.md#plan-0038-batch-s4a-2026-10-16) and
  [drlg/0007 § Plan 0038 batch S4a](0007-warps.md#plan-0038-batch-s4a-2026-10-16).

## run:2026-10-15-drlg-maze

- **Question:** (plan 0022 Phase 2) Does the model of [drlg/0006](0006-maze.md) and [drlg/0007](0007-warps.md) in
  `tools/drlg.py` reproduce, with no maze oracle, every maze window (the level-seed draws one by one, the room list with
  absolute rectangles, `Def`s and forced indices, the seed after the window), the act link builder of Acts I, II, IV and V
  (the act-seed-copy draws, the rects, the choices, level 27's index draw, the `LevelLinks` list), the room flags'
  warp-slot and waypoint bits, the warp point list `level+0x1E0` of every build, and the warp pairings?
- **Setup:** harness slot 4 (ADR-0011: display `:11`, prefix `workspace/wineprefix-4`), game dir `workspace/runtime/game/`,
  wine 11.17, GNU gdb 17.2, map seed `-seed 2027` in every session. Play was **agent-driven** (no human play): waypoint
  travel computed from the log (the level's waypoint object from its `PRC` instance and DS1 units), Teleport walks
  (`tools/d2pilot.py hop`/`explore`, `--to-rect` towards the room the warp-point model names for a target level, `farm
  --descend` for the Basement stairs).
  - Logger `tools/gdb/drlg-maze.gdb`, which sources `tools/gdb/drlg-gen.py`, `tools/gdb/drlg-maze.py` and
    `tools/gdb/pilot.py` (its `RL` renamed `PRL`). `drlg-maze.py` versions: sessions 1–8 without `OBJP` (session 1 logs
    the level-27 write as `L27X`, later sessions as `LK27`; session 1 has no `WPR`), sessions 9–10 with `OBJP` for the portal
    classes only, sessions 11–14 the committed version (sha256 `f6c48da55cc056e6…`).
  - Model and checker `python3 -I tools/drlg.py gen` (sha256 `15e29bb80be64e49…`), tables from `workspace/merged`.
  - **Characters** (installed and restored only through `tools/saves.py --slot 4`, tags `maze4`, `maze4c`): `UniqNova.d2s`
    (`2c793a3df3773c0f…`) from `tools/d2s_recipes/uniqnova.json` (`3c2f57dc8921dc3d…`) and `UniqClassic.d2s` (`19dbfc5bcf035ee3…`)
    from `tools/d2s_recipes/uniqclassic.json` (`e58db6391cccb235…`), both built with
    `python3 -I tools/d2s.py build workspace/merged/data/global/excel <recipe> workspace/samples/d2s-owner/smpsor-l50.d2s workspace/runtime/maze-chars/<name>.d2s`.
- **Logged** (header of `tools/gdb/drlg-maze.py`): the drlg-gen tags; `MZA` (act fields and rects the maze reads), `MZD`
  (a hardware write watchpoint on the level seed for the whole window: every step), `MZF` (rooms freed in the window),
  `LNK0`/`LNKL`/`LK27`/`LNK1` (each `LevelLinkBuild` call: entry seed, per-level rect and index writes, the level-27 draw, the
  `LinkBuild` struct at exit), `LNKS` (the act's `LevelLinks` list after `ActLinkInit`), `LWP` (after
  `LevelWarpPointsBuild`: the room list with flags and the point list), `WPR` (each warp pairing), `OBJP` (pilot aid only).
- **Procedure:** per session `python3 -I tools/d2run.py --slot 4 --seed 2027 --gdb tools/gdb/drlg-maze.gdb --steps <enter steps> --after 3600 --log workspace/logs/maze/<log>`,
  then waypoint chains and walks; each session ended with `python3 -I tools/slots.py stop 4`.

  | log | mode, difficulty | what was played | maze levels built |
  |---|---|---|---|
  | `maze-s1-2027-normal.log` | expansion, normal | waypoints 107, 113, 115, 123, 118, 129, 48, 57, 52, 74, 101, 29, 35; explore 101 | 28–30, 34–36, 48, 49, 51–53, 57, 74, 100, 101, 107, 113–115, 118, 122, 123, 129 |
  | `maze-s2a-2027-nightmare.log` | expansion, nightmare | aborted (surrounded in 107) | 107 |
  | `maze-s2-2027-nightmare.log` | expansion, nightmare | the same chain; explore 115 | as s1 without 100, plus 116 |
  | `maze-s3-2027-hell.log` | expansion, hell | the same chain; explore 101 (death to lightning-immune Maulers) | as s1 without 100 |
  | `maze-s4-2027-classic-normal.log` | expansion, normal (see the correction below) | waypoints 48, 57, 52, 74, 29, 35 (ended by a stray *Save and Exit* click) | 28–30, 34–36, 48, 49, 51–53, 57, 74 |
  | `maze-s5-2027-normal.log` | expansion, normal | 52, then the stairs down twice | 51–54 |
  | `maze-s6-2027-normal.log` | expansion, normal | 101, explore | 100–101 (102 preset) |
  | `maze-s7-2027-normal.log` | expansion, normal | Spider Forest, Flayer Jungle (Great Marsh built on the way) | 84–86, 88 |
  | `maze-s8-2027-normal.log` | expansion, normal | Kurast Bazaar, Far Oasis, Cold Plains, Burial Grounds | 9, 18, 19, 62, 92 |
  | `maze-s9-2027-normal.log`, `maze-s10-2027-normal.log` | expansion, normal | Frigid Highlands (portal search) | — |
  | `maze-s11-2027-normal.log` | expansion, normal | Frigid Highlands explore, the red portal | 125 |
  | `maze-s12-2027-normal.log` | expansion, normal | Ancients' Way explore | 118, 119 |
  | `maze-s13-2027-normal.log` | expansion, normal | Lost City, Valley of Snakes | 58, 61, 65 |
  | `maze-s14-2027-normal.log` | expansion, normal | Travincal | 100 |

  Checks: `python3 -I tools/drlg.py gen workspace/logs/maze/maze-s*.log workspace/logs/gen-12345-town.log workspace/logs/gen-777-town.log workspace/logs/gen-12345-bloodmoor.log workspace/logs/gen-12345-act2.log workspace/logs/gen-12345-act4.log workspace/logs/gen-1-catacombs-owner.log`
  (this run's logs and those of run:2026-10-12-drlg-gen, now with the maze model instead of the `MZ0`–`MZ1` oracle); then
  `python3 -I tools/outdoor_replay.py workspace/merged workspace/install/app/game.exe $L` over every log with an `OD0` line
  (the link builder now imported from `tools/drlg.py`), `python3 -I tools/maze_replay.py …` as in the Phase 1 addendum, and
  `python3 -I tools/collision.py check` on the run:2026-10-14-collision and plan 0014 logs.
- **Observed:**
  ```
  drlg gen (15 + 6 logs): 189355 checks, 0 mismatches
  maze windows 230 (difficulty 0: 131, 1: 53, 2: 46), 41 distinct maze levels, all 20 maze level types
    Act I 8, 9, 18, 19, 28, 29, 30, 34, 35, 36; Act II 47, 48, 49, 51, 52, 53, 54, 57, 58, 61, 62, 65, 74;
    Act III 84, 85, 86, 88, 92, 100, 101; Act IV 107; Act V 113, 114, 115, 116, 118, 119, 122, 123, 125, 129
    all three difficulties: 28, 29, 30, 34, 35, 36, 48, 49, 51, 52, 53, 57, 74, 101, 107, 113, 114, 115, 118, 122, 123, 129
    classic and expansion: none in this run (correction below); see run:2026-10-15-drlg-outdoor
    level-seed draws in the windows checked one by one (MZD) 12388; maze inputs against MZA 218
    forced indices at MazePresetFile predicted 3135 (454 forced, 2681 none)
    level-specific branches: 28 x8, 61 x2, 74 x8, 92 x2, 107 x8, 114 x6, 116 x2, 119 x2
  link builder: 196 LevelLinkBuild calls predicted (Acts I, II, IV, V; seed copy, rects, dir/dir0/step/flip0, act seed);
    level rects 495; town indices (levels 1, 40) 30; level-27 index draw 16; LevelLinks lists 69 (Act III's 16: logged input)
  warp cells: preset room flags 21728 predicted from the DS1 scan (770 with warp or waypoint bits); outdoor rooms 988 from the log
  warp point lists 389 predicted (351 levels with no outdoor room, 38 with outdoor-room flags from the log);
    level room list = RL order reversed 389
  warp pairings 172 predicted: by rank 162 (rank 1 on a repeated destination 32), the fallback 10 (below)
  outdoor_replay: windows 148, mismatches 0; maze_replay: windows 12, mismatches 0
  collision (run:2026-10-14-collision logs): 20791 checks, 0 mismatches; NearWarpTest warp points predicted 1392 calls
    (levels 29, 38, 76, 77, 78, 106); levels 4 and 44: 254 calls whose outdoor-room point stays a logged input,
    their preset-room points predicted in order
  monspawn (plan 0014 logs): 114363 checks, 0 mismatches (no NWP lines there: NearWarpTest stays the plan 0014 value oracle)
  ```
- **Required cases:**

  | Case | Result |
  |---|---|
  | run:2026-10-12-drlg-gen rerun with the maze window predicted | 12 windows (levels 8, 47, 34–36), 0 mismatches, absolute rects |
  | ≥ 25 maze levels, all five acts, every maze level type | 41 levels, 20 types |
  | three difficulties for ≥ 5 levels (room counts per difficulty) | 22 levels |
  | classic and expansion for ≥ 3 Act I–IV levels | not met in this run (correction below); met by run:2026-10-15-drlg-outdoor: 7 maze levels built in both modes |
  | branches 28, 61, 92, 107, 114, 116, 119 | all reached |
  | finishers read only `[I]` (Arcane, Tomb/Baal, Act V hell, Durance 100/101, 107) | 74; 57, 58, 61 / 129; 125; 100, 101; 107 |
  | act links of Acts I, II, IV, V, level 27's index from the level-6 draw | 196 calls, 16 draws |
  | warp cells and point lists of every logged level | 389 builds; outdoor-room bits stay drlg/outdoor's |
  | run:2026-10-14-collision and plan 0014 logs with predicted warp points | above |
  | Basement 3 (54) slots 2/3 | its NW and SE rooms take the forced `File4` (`CelNW3.ds1`, `CelSE3.ds1`), which hold no warp-slot cell: no slot 2/3 bit, no point (s5) |
  | the Durance slot by rotation draw and its pairing | 100's Prev faced slot 2 in this seed: 83 slot 0 ↔ 100 slot 2 by rank 0; 101 → 102 and 101 → 100 take the fallback (below) |

- **Surprises:**
  - **Warp pairing falls back** when the destination has no room with the rank slot's bit: `WarpPairLink` then takes the
    first slot of the destination naming the source whose room exists (10 pairings: Durance 101 ↔ 102 and 101 ↔ 100, Ice
    caves). A Durance level carries only the slot its finisher's rotation faced, so rank pairing alone mispredicts there.
  - **The room-flag grid is pre-filled.** `DRLG_PresetMapScan` ORs into every room of the instance the
    `PresetRoomsCreate` flags and `0x10 << k` for every `Vis` slot k with `Warp` −1 (a seam) before the DS1 scan.
  - **A maze level's rect** is `LevelSetPosition`'s (`0x00642D10`): `SizeX/SizeY` of the difficulty at `OffsetX/OffsetY`
    plus the `Depend` level's position (level 27 from 26's builder rect).
  - The Act V red portals are not DS1 or object-group objects: a `Permanent town portal` (class 60) object was found in
    Frigid Highlands by the `OBJP` scan (where it comes from is not read).
- **Raw logs:** `workspace/logs/maze/`: s1 `efe231047078c626…`, s2a `69cd3b22d159791b…`, s2 `f3386adb42e2ce61…`, s3
  `de91c981a5bc04ad…`, s4 `37ccbcc269a91db1…`, s5 `d80b81b4f26e8da3…`, s6 `c3d40a3f1171b457…`, s7 `139244dfff6a4d19…`, s8
  `a9be1073dd7aac2d…`, s9 `3ef5a560fcf69566…`, s10 `da43cc10a4813446…`, s11 `5d527577d73545e2…`, s12 `5506ee7a5b52d576…`, s13
  `98363eb2ded927d2…`, s14 `f925ef68a2097d6c…`.
- **Deviations and limits:**
  - Slot 4's display was 544 rows high until main's `tools/d2run.py` change: the menu steps used the Return key for OK, and
    the pilot measured the frame height (`--view-h 0`).
  - Boundaries (ADR-0004), named: **Act III's level rects and `LevelLinks` list** (the jungle layout, plan 0026; `LNKS` is a
    logged input there); **outdoor rooms' warp-slot bits** (written by the outdoor generators, drlg/outdoor: their rooms'
    flags are taken from `LWP`, and in the collision logs their points stay logged); the outdoor act generator window
    (`OD0`–`OD1`, unchanged).
  - Unreached: `sub_00672420_MazeFindWest` (level 27's index was 1 in every log, so the Barracks took `FindSouth`), the
    Barracks indices 0 and 2, the Tomb finisher's true-tomb and Kaa branches (no tomb 66–72 built), `MazeSpecialAttach`'s
    fallback when no room can take a special, `MazeLevelPlace`'s fatal error.
  - One map seed (2027) plus the two of run:2026-10-12-drlg-gen; no multiplayer.
- **Conclusion:** the maze generator ([drlg/0006](0006-maze.md)), the act link builder of Acts I, II, IV and V, the room
  warp/waypoint flags, the warp points and the warp pairing ([drlg/0007](0007-warps.md)) are reproduced bit-exactly, `[C]`
  for the paths listed above; the maze oracle of [drlg/0003](0003-generator-dispatch.md) and the logged warp points of
  [drlg/0005 § 9](0005-collision.md#9-nearwarptestgame-room-x-y-and-the-warp-points) are replaced.
  (run:2026-10-15-drlg-maze, fn:sub_00673B30_MazeLevelBuild@0x00673B30, fn:sub_006772C0_LevelLinkBuild@0x006772C0, fn:sub_006423D0_LevelWarpPointsBuild@0x006423D0, fn:sub_0066C220_WarpPairLink@0x0066C220)

- **Correction (architect, 2026-10-15, review of plan 0026 Phase 2).** The `UniqClassic.d2s` used in session s4 (`19dbfc5b…`) has status byte `0x20` (expansion); loaded in run:2026-10-15-drlg-outdoor it showed five act tabs. Session s4 is an expansion session, so this run has no classic window. The classic coverage of the maze model comes from the four classic sessions of run:2026-10-15-drlg-outdoor (s3, s5, s8, s10, a status-0 build): 46 maze windows of levels 9, 56, 65, 84, 86, 92, 100 and 107, 0 mismatches with the same mode-free model; all but 56 were also built in expansion here.
- **Addendum 2026-10-16: plan 0038 batch S4a (static, no new session; `tools/sweep_s4a.py` sha256 `fafe0406c61b4363…`).** `tools/drlg.py gen` (unchanged) re-run with
  counters by `tools/sweep_s4a.py` over this run's logs and the run:2026-10-12-drlg-gen, run:2026-10-15-drlg-outdoor and
  run:2026-10-15-acts-3-5 logs. Regression without counters: `python3 -I tools/drlg.py gen` on this record's list,
  206 937 checks, 0 mismatches; `tools/maze_replay.py` 12 windows, 0. Commands: `python3 -I tools/sweep_s4a.py maze`,
  `… r0`, `… lnks`, `… wgen`, `… l27`. Observed (trimmed):
  ```
  maze  393 windows, MZD steps 23 282; specials by match 390, attaches 337 (154 after failed candidates, 313 failed
        candidates), no room took it 0
  r0    230 windows with R0 moved by (37, -53), (-1000, 999), (4096, 4096): 0 mismatches each; second room moved by
        one tile: 3019 mismatches
  lnks  levels.txt 27<->28, 107<->108 Warp -1 in the naming slots (4 of 4); WPR pairings 431, none between them;
        windows placed against the neighbour level: 28 x8, 107 x28
  wgen  preset room flags from the DS1 scan: preset levels 6120 (warp bits 100, waypoint 184), maze rooms 19 389
        (805, 163), outdoor embedded presets 65 052 (882, 240); 0 mismatches
  l27   LevelLinkBuild calls checked 394, LK27 40; level 6 link value 3 x17, 1 x4, 0 x6 (no draw, no write)
  ```
  Conclusion: [drlg/0006 § Plan 0038 batch S4a](0006-maze.md#plan-0038-batch-s4a-2026-10-16),
  [drlg/0007 § Plan 0038 batch S4a](0007-warps.md#plan-0038-batch-s4a-2026-10-16) and
  [drlg/0004 § Plan 0038 batch S4a](0004-preset-units.md#plan-0038-batch-s4a-2026-10-16).

## run:2026-10-15-drlg-outdoor

- **Question:** (plan 0026 Phase 2) Does the outdoor model of [drlg/0008](0008-outdoor.md) in `tools/drlg.py` (class
  `Outdoor`, Act III's `act_links_a3`), with no outdoor oracle, reproduce every outdoor window of Acts I–V: every level-seed
  step of the window, the final def grid, grid0 and cell grid with the outdoor flags, the seed after the window, the preset
  anchors with their file indices and flags, the out rooms and their `+0x28` flags? And does it leave the
  run:2026-10-12-drlg-gen and run:2026-10-15-drlg-maze checks at 0 mismatches?
- **Setup:** harness slots 1 and 2 (displays `:8`, `:9`; prefixes `workspace/wineprefix-1`, `-2`), game dir
  `workspace/runtime/game/`, wine 11.17, GNU gdb 17.2. Play was **agent-driven** (no human play): waypoint chains only, no
  fighting beyond Nova bursts to clear a waypoint.
  - Logger `tools/gdb/drlg-outdoor.gdb` (sha256 `56434a2ef6e35970…`), which sources `tools/gdb/drlg-gen.py`
    (`e0ce7368db048958…`), `tools/gdb/drlg-maze.py` (`f6c48da55cc056e6…`), `tools/gdb/drlg-outdoor.py` (`766827691f5b491a…`)
    and `tools/gdb/pilot.py` (`1ad48a4cae8478e2…`).
  - Model and checker `python3 -I tools/drlg.py gen` (`d0e6717a3682cf8b…`), tables from `workspace/merged`.
  - Driver `tools/d2pilot.py wp` (the Act IV town waypoint at its default position) then `wpchain` (each hop clicks the
    waypoint the log's `OBJP` line places, at a few offsets; sessions s7 onwards with a Nova burst before each retry; final
    version `993dda6d904b66e2…`).
  - **Characters** (installed only through `tools/saves.py --slot N`, tags `od26a` on slot 1, `od26b` on slot 2; restore,
    aside and install again before each session): expansion `UniqNova.d2s` (`2c793a3df3773c0f…`, the run:2026-10-15-drlg-maze
    build of `tools/d2s_recipes/uniqnova.json`); classic `UniqClassic.d2s` (`68e46a96698d9899…`, status byte 0), built with
    `python3 -I tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/uniqclassic.json workspace/runtime/monspawn-chars/cls/smpsor.d2s workspace/runtime/outdoor-chars/UniqClassic.d2s`;
    `keynova.d2s` (`88ebd25f6db285ef…`) from `tools/d2s_recipes/keynova.json` (`b7741de7d6c51469…`; UniqNova's gear, the
    cube with the three Pandemonium keys) on `workspace/samples/d2s-owner/smpsor-l50.d2s`.
- **Logged** (header of `tools/gdb/drlg-outdoor.py`): the drlg-gen, drlg-maze and pilot tags, plus `ODD` (a hardware write
  watchpoint on the level seed from the outdoor build's entry `0x00675360` to `OutdoorRoomsCreate` `0x006750F0`: every
  step's new seed lo and `$pc`, one line per window) and `ODG` (at `0x006750F0`: the level rect, the outdoor flags, cw/ch and
  the def grid, grid0 and cell grid, row-major).
- **Procedure:** per session `python3 -I tools/d2run.py --slot N --seed S --gdb tools/gdb/drlg-outdoor.gdb --steps tools/gdb/enter-<difficulty>.steps --after 3600 --log workspace/logs/outdoor/<log>`;
  the character starts in the Act IV town; `d2pilot.py --slot N wp <log> 4 2`; then
  `d2pilot.py --slot N wpchain <log> --chain "<hops>"` (classic: `--wp-tab-x0 120 --wp-tab-w 78`); then
  `python3 -I tools/slots.py stop N`. Entering a level by waypoint builds it and the levels its `Vis` slots name, so the
  chain 4,3 (River of Flame: 106–108), 5,2 / 5,3 / 5,7 (Frigid Highlands, Arreat Plateau, Frozen Tundra: 110–112, 117),
  1,2 / 1,4 / 1,5 (Cold Plains, Dark Wood, Black Marsh: 1–7, 17), 2,3 / 2,5 / 2,6 (Dry Hills, Far Oasis, Lost City: 41–45),
  2,9 (Canyon of the Magi: 46), 3,2 / 3,3 / 3,4 / 3,6 / 3,8 (the jungles, Kurast Bazaar, Travincal: 76–83) builds every
  reachable outdoor level; Act IV's 104 is built in the town.

  | log | mode, difficulty | hops | outdoor windows |
  |---|---|---|---|
  | `od-s1-3101-normal.log` | expansion, normal | 4,2 then 14 (no 2,9) | 58 |
  | `od-s2-3102-nightmare.log` | expansion, nightmare | 4,2 then 15 (no 2,9) | 56 |
  | `od-s3-3103-classic-normal.log` | classic, normal | 4,2 then 12 | 50 |
  | `od-s4-3104-hell.log` | expansion, hell | 4,2 then 15 | 58 |
  | `od-s5-3105-classic-nightmare.log` | classic, nightmare | 4,2 then 12 | 48 |
  | `od-s6-3106-normal.log` | expansion, normal | 4,2 then 7 (stopped: monsters on Black Marsh's waypoint took the clicks) | 30 |
  | `od-s7-3107-normal.log` | expansion, normal | 4,2 then 16 (with 2,9) | 58 |
  | `od-s8-3108-classic-hell.log` | classic, hell | 4,2 then 13 (with 2,9) | 50 |
  | `od-s9-3109-nightmare.log` | expansion, nightmare | 4,2 then 16 (with 2,9) | 60 |
  | `od-s10-3110-classic-normal.log` | classic, normal | 4,2 then 13 (with 2,9) | 50 |
  | `od-k1-3201-hell.log` | expansion, hell | 5,1 to Harrogath; cube opened, Transmute clicked three times with the three keys inside: no portal, the keys stayed | 4 |

  Checks: `python3 -I tools/drlg.py gen` on the 11 logs; on the run:2026-10-12-drlg-gen and run:2026-10-15-drlg-maze logs
  (the list of that record); on every older log with an `OD0` line (93); `tools/outdoor_replay.py` and
  `tools/jungle_replay.py` on the 93 + 11 logs; `tools/maze_replay.py` as in the run:2026-10-12-drlg-gen addendum;
  `tools/collision.py check` on the run:2026-10-14-collision logs; `tools/monspawn.py check` on the plan 0014 and plan
  0015 logs (`monspawn-s*`, `monspecial-s*`).
- **Observed:**
  ```
  drlg gen (this run, 11 logs): 572211 checks, 0 mismatches
    outdoor windows 522 (29 levels; act x difficulty: I 70/42/28, II 44/32/22, III 68/50/34, IV 40/24/18, V 24/16/10)
    level-seed steps in the window checked one by one (ODD) 1443544; grid cells checked (ODG) 55676 per grid x 3
    preset anchors 22422 (Def, position, file index at PIO), PRC flags 22422 (3496 non-zero), out rooms 7376
    out-room +0x28 at LWP 6092 (shrine 1000, warp slot 150, waypoint 134); warp point lists with out rooms 292
    LevelLinks lists predicted: Act I 20, II 20, III 18 (now modelled), IV 22, V 14
    branches: Act II cliff layouts 0-7 (10, 12, 4, 10, 6, 4, 6, 2); Kurast rings 79/80/81 20/18/18; Act V gates 907-910;
      stamps of Type 0, 1, 2, 3, 12 (92, 246, 576, 454, 104); A1 cliff runs and caves 38, corner caves 24, rivers 26,
      bridges 10, roads with 2/3/4 endpoints 40/60/20; PlaceNear fallbacks 8; PlaceRandom failures 338
  per level (windows, map seeds; every level in normal, nightmare and hell):
    2-7, 17: 20 each, 10 seeds, classic and expansion      41-45: 18 each, 9 seeds, classic and expansion
    46: 8, 4 seeds (3107-3110), classic and expansion      76, 77, 80-83: 18 each, 78: 24, 79: 20; 9 seeds, both modes
    104: 22, 11 seeds; 105, 106, 108: 20 each, 10 seeds; both modes
    110: 14, 7 seeds; 111, 112, 117: 12 each, 6 seeds; expansion only
  drlg gen, run:2026-10-12-drlg-gen + run:2026-10-15-drlg-maze logs: 206937 checks, 0 mismatches (189371 before the
    outdoor checks: +16 Act III LevelLinks lists)
  drlg gen, the 93 older logs with an OD0 line: 719282 checks, 0 mismatches
  outdoor_replay (93 + 11 logs, all five acts): windows 460, mismatches 0; jungle_replay: windows 266, mismatches 0
  maze_replay: windows 12, mismatches 0
  collision (run:2026-10-14-collision): monspawn 75812, collision 20537 checks, 0 mismatches; NearWarpTest warp points of
    levels 4 and 44 now predicted (were logged inputs)
  monspawn (plan 0014 + 0015 logs): 506081 checks, collision 31485 checks, 0 mismatches
  ```
- **Required cases:**

  | Case | Result |
  |---|---|
  | every outdoor level of Acts I–V, three game seeds, two difficulties, classic and expansion where it exists | 29 of 31 levels, 4–11 seeds each, all three difficulties; Acts I–IV in both modes. Not reached: 39, 134 (boundaries, below) |
  | final grid cell for cell, room list and file indices | 522 windows, 0 mismatches |
  | level seed after the generator | 522 windows, and every step inside (1443544) |
  | run:2026-10-12-drlg-gen rerun with the oracle replaced | 0 mismatches (with the run:2026-10-15-drlg-maze logs) |
  | the levels and branches Phase 1 left (39, 46, 134, Act II layouts 1 and 4, 80–83, the jungle restart and path retry, 117, the prisons' fallback) | 46, layouts 1 and 4, 80–83, 117, jungle restart and retry reached; 39, 134 and the prisons' fallback not |
  | level 111's waypoint room flag (architect ruling on `lane/a-sweep6`) | the `To Siege` preset (880) room holding the waypoint unit carries `0x30000` and gives the level's one warp point, predicted from the DS1 scan in every build |
  | Phase 1b cases | none were raised (no contradicted lead) |

- **Surprises:**
  - An out room's `+0x28` is grid0 `| 0x80000` (`| 0x40000` on the client copy).
  - Canyon of the Magi was reached by waypoint (Act II row 9) with both characters, so the "refused" waypoint of
    run:2026-10-14-collision (backlog architect → reverser 2026-10-14) is not a quest gate for 46 with these saves.
  - The `UniqClassic.d2s` of run:2026-10-15-drlg-maze (`19dbfc5bcf035ee3…`, built on `smpsor-l50.d2s`) has status byte
    `0x20` (expansion): loaded here (dev session, `od-dev2-…`) its waypoint menu showed five act tabs. This run's classic
    sessions use the status-0 build above. Backlog entry to the architect.
- **Raw logs:** `workspace/logs/outdoor/`: s1 `fc15891672ee444a…`, s2 `29ecee616cf83095…`, s3 `ac47db8afde55902…`, s4
  `03d1b1f44535f03b…`, s5 `24eb7e93a1b37138…`, s6 `0c4b2f15c1eb9132…`, s7 `c986066aa01c84c0…`, s8 `4e62e3e91b773159…`, s9
  `c5c57365fd01d91d…`, s10 `22073f6e6712e006…`, k1 `04a2f33314a312a7…`; dev sessions (not in the checks) `od-dev1-3101-normal.log`
  (`80282dec0b8015d7…`, logger with a `$eip` read error, 0 model mismatches) and `od-dev2-3103-expansion-misbuilt.log`
  (`f39759241f91f438…`, the expansion-status character).
- **Deviations and limits:**
  - **Boundaries (ADR-0004), named:** level 39 (the cow portal needs Wirt's Leg and a Tome of Town Portal in the cube;
    `tools/d2s.py build` cannot write a tome yet: backlog to the archivist) and level 134 (the Pandemonium key transmute did
    nothing in a single-player hell game, session k1; the code path that refuses it was not read). Both stay inferred; their
    generator code is the Act I area list (39) and Act II's valley fills (134, shared with 46, which this run reaches).
  - Unreached branches: a link-builder backtrack, a vertex merge, the Act V prisons' fallback scan, a waypoint with no free
    cell, roads with 5 or 6 endpoints or a failed search, `BridgeFind` on a non-square Blood Moor.
  - Session s6 stopped at its eighth hop; its Acts IV, V and I windows are in the checks.
  - No multiplayer; single map seed per session.
- **Conclusion:** the outdoor generators of [drlg/0008](0008-outdoor.md) and Act III's link layout are reproduced
  bit-exactly, `[C]` for the paths above; the outdoor oracle of [drlg/0003](0003-generator-dispatch.md) and the logged
  Act III `LevelLinks` list and outdoor-room flags of [drlg/0007](0007-warps.md) are replaced.
  (run:2026-10-15-drlg-outdoor, fn:sub_00675360_OutdoorLevelBuild@0x00675360, fn:sub_006789B0_ActLinkAct3@0x006789B0)
- **Addendum 2026-10-15: out-room grids at the first `LvlSub` pass (plan 0026 Phase 3 follow-up, architect ruling).** No
  new game run: the check re-analyses logs this record already checks (its "every older log with an `OD0` line" set).
  `tools/drlg.py gen` (sha256 `74853cba501a3513…`) now keeps each Act I road's jittered polyline
  ([drlg/0008 § 16.3](0008-outdoor.md#163-act-i)) and, in logs that also carry `tools/gdb/drlg-roomk.py` lines, predicts the
  three OutRoom grids every type-1 room has at its first `LSUB` line from the latest outdoor model of its level
  ([§ 16.4](0008-outdoor.md#164-room-prepare-of-an-out-room-0x0067d2d0-and-the-road-tiles)): orientation and wall all zero, the floor
  `0x40002` on the 8×8 cells, and on Act I levels the road tiles of `OutRoomRoadGrid` coded through `g_RoadCodes`.
  - *Logs:* the 38 logs in `workspace/logs/` with both an `OD0` line and `LSUB` lines (`collision-*` 3, `monspawn-*` 5,
    `monspecial-*` 11, `monstats-*` 8, `objects-*` 11): `cd workspace/logs && grep -l "^OD0" *.log | xargs grep -l '^LSUB '`.
  - *Commands and observed:*
    ```
    python3 -I tools/drlg.py gen <the 38 logs>
      out-room grids at the first LvlSub pass: rooms checked act 1 1868, act 2 267, act 3 50, act 5 527 (2712);
      rooms with road tiles 744
      gen: 352204 checks, 0 mismatches            (346780 before: + 2 checks per room)
    python3 -I tools/drlg.py gen <the 11 logs of this run>              572211 checks, 0 mismatches (no LSUB lines)
    python3 -I tools/drlg.py gen <the run:2026-10-12-drlg-gen + run:2026-10-15-drlg-maze list>   206937 checks, 0 mismatches
    python3 -I tools/drlg.py gen <every workspace/logs/*.log with an OD0 line, 104 today>        690830 checks, 0 mismatches
    python3 -I tools/drlg.py roomk <the six logs of run:2026-10-11-drlg-roomk>                   11208 checks, 0 mismatches
    tools/outdoor_replay.py, tools/jungle_replay.py (those 104 + the 11 logs)                    505 / 252 windows, 0 mismatches
    ```
  - *Conclusion:* the jitter points (§ 16.3), `OutRoomGridPrepare`'s fill before the first pass, `OutRoomRoadGrid`,
    `GridLineOp` and `g_RoadCodes` (§ 16.4) are reproduced bit-exactly on every logged out room: `[C]`.
    (fn:sub_00681240_A1PathJitter@0x00681240, fn:sub_0067D2D0_OutRoomGridPrepare@0x0067D2D0,
    fn:sub_00680C80_OutRoomRoadGrid@0x00680C80)
- **Addendum 2026-10-15: session k1 read against the code (plan 0027 Phase 2).** No new run and no re-analysis of a log:
  the Pandemonium transmute that did nothing in k1 is explained by the code. The cube's portal outputs 2 and 3 are stubs
  that return 0 (`data:g_CubePortalFns@0x006E11C8`), so the recipe creates nothing and keeps its inputs, as k1 saw
  ([save/0002 § 6](../save/0002-quest-words.md#6-the-pandemonium-key-transmute-level-134-plan-0027-phase-2-2026-10-15)).
  Level 134 cannot be reached through the cube in this `Game.exe`. The Canyon (46) sessions also show that the
  waypoint list has no level-specific gate, which § 5 of that finding reads for Arcane Sanctuary (74).
- **Addendum 2026-10-16: plan 0038 batch S4a (static, no new session; `tools/sweep_s4a.py` sha256 `fafe0406c61b4363…`).** `tools/drlg.py gen` (unchanged; 572 211
  checks, 0 mismatches on the 11 logs) re-run with counters by `tools/sweep_s4a.py`. Commands: `python3 -I
  tools/sweep_s4a.py odg`, `… adj`, `… placefar`, `… expansion`, `… lc1`. Observed (trimmed):
  ```
  odg        528 final cell grids (30 levels, 56 204 cells): bits 20-25 clear in all; grid0 warp-slot bits 5772
  adj        inserts 177 (into two or more nodes 19; head skipped and the new node sorting before it 5, all on
             another side); full-compare control: 0 mismatches
  placefar   PlaceFar calls 4; exclusive bounds: 0 mismatches
  expansion  classic sessions (s3, s5, s8, s10): PIC 9407, none on an Expansion-1 record; the 227 Expansion-1 records
             of lvlprest are all Act V
  ```
  Conclusion: [drlg/0008 § Plan 0038 batch S4a](0008-outdoor.md#plan-0038-batch-s4a-2026-10-16) and
  [drlg/0003 § Plan 0038 batch S4a](0003-generator-dispatch.md#plan-0038-batch-s4a-2026-10-16).

## run:2026-10-15-acts-3-5

- **Question:** (plan 0020 Phase 4) On a `quests: all` save under the `drlg-preset` logger with a row-skip counter,
  does the preset-unit model of [drlg/0004](0004-preset-units.md) in `tools/drlg.py gen` reproduce, with no oracle, the
  cases run:2026-10-13-drlg-preset did not reach: a maze preset room in Act III and in Act V, the act-index-2 rewrite of
  MonStats 366, the act-index-4 rewrites 537..539, the draws of MonStats 371/372, MonPlace 33 and objects 196/261,
  MonPlace 35 dropped, and at least one client row skip on a floor main (`DRLG_PresetClientUnitsB`, switch
  `0x0066638C`)? The load test of [save/0002](../save/0002-quest-words.md) is recorded in
  [save experiments](../save/experiments.md#run2026-10-15-acts-3-5-load) (run:2026-10-15-acts-3-5-load).
- **Setup:** harness slot 1 (ADR-0011: display `:8`, prefix `workspace/wineprefix-1`), game dir
  `workspace/runtime/game/`, wine 11.17, GNU gdb 17.2, Normal, expansion. Play was **agent-driven** (no human play):
  waypoint chains (`tools/d2pilot.py wpchain`, which clicks the waypoint the log's `OBJP` line places), Teleport
  exploration (`explore`) and warp taking (`farm --descend`), per
  [harness-play](../../../.claude/skills/reverser/references/harness-play.md).
  - Logger `tools/gdb/drlg-preset-play.gdb` (new, sha256 `04b4392a590394a5…`), which sources `tools/gdb/drlg-gen.py`
    (`e0ce7368db048958…`), `tools/gdb/drlg-preset.py` (`63863bddbe3b79ba…`), `tools/gdb/drlg-maze.py`
    (`f6c48da55cc056e6…`, for the `OBJP` waypoint lines; its maze, link and warp tags are checked as well) and
    `tools/gdb/pilot.py` (`1ad48a4cae8478e2…`, `RL` renamed `PRL`). `drlg-preset.py` gained two tags: **RSK** at
    `0x00666368`, the `add dword [ebp-0xC], 3` of `DRLG_PresetClientUnitsB` that the switch at `0x0066638C` reaches
    for a style-4 floor cell of main 0/4/8/16/29/39 (instance ESI, the DS1 row `[ebp-0xC]` before the skip, the main
    index EAX), and **RSKON**, written once when the file loads, which marks a log whose logger has the RSK breakpoint.
  - Model and checker `python3 -I tools/drlg.py gen` (sha256 `619d6e98bdee1002…`), tables from `workspace/merged`.
    New in this run: `client_objects` returns the (row, main) of every skip it takes, and at each `PLDX` of a log
    with RSKON the logged RSK lines of that instance must equal the modelled skips (empty when the instance gets no
    client objects); a counter of preset room lists reproduced in maze levels (DrlgType 1) per act and copy.
  - **Character** (installed and restored only through `tools/saves.py --slot 1`, tag `h20p4`; restore, aside and
    install again before each session): `UniqNova.d2s` (`2c793a3df3773c0f…`, status `0x20`, progression 15, quest
    words 7, 15, 23, 26 and 28 = `0x0001` in all three blocks) built with
    `python3 -I tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/uniqnova.json workspace/samples/d2s-owner/smpsor-l50.d2s workspace/runtime/h20p4-chars/UniqNova.d2s`
    (recipe `3c2f57dc8921dc3d…`, which has `"quests": "all"` and every waypoint; the same bytes as the
    run:2026-10-15-drlg-maze build). The character starts in the Act IV town.
- **Target data** (`tools/ds1.py` parse with the `DS1_Parse` mapping, done before the run to pick the route): MonStats
  371 is in the Arcane Sanctuary DS1s (Defs 510–524, with object 196); 372 in Act II outdoor and tomb presets (Defs
  389, 413, 425); MonPlace 35 in the Durance (`Meph*`, Defs 757–791), the Kurast temples (750–753) and two Act I jail
  themes; MonPlace 33 in `Cott4A.ds1` (Def 48 file index 3, `Pops` 2: rolled on the level seed), `Wild1.ds1` (Def 32),
  `CryptCountess2.ds1` (Def 159) and `MephSW2.ds1` (Def 758); object 261 in the Act II tomb DS1s (Halls of the Dead,
  Tal Rasha's tombs); 366 in `TravN.ds1` (Def 654, `Scan` 1); 537..539 in `MtnTop.ds1` (Def 1089, level 120, `Scan` 1).
  A row skip needs a client-object Def (1, 3, 26, 27, 28, 300) with a style-4 floor cell of a listed main in a placed
  column: `TownE1.ds1` (Def 1 file index 1, row 15, main 16) and `BridgeU/L/S.ds1` (Def 28) are the only ones.
- **Procedure:** per session `python3 -I tools/d2run.py --slot 1 --seed S --gdb tools/gdb/drlg-preset-play.gdb --steps tools/gdb/enter-normal.steps --after 3600 --log workspace/logs/acts35/a35-sK-S-normal.log`,
  then `python3 -I tools/d2pilot.py --slot 1 wpchain <log> --chain "<hops>" --shots workspace/logs/acts35/sK`, then
  `python3 -I tools/slots.py stop 1`.

  | log | map seed | what was played |
  |---|---|---|
  | `a35-s1-21-normal.log` | 21 | load test (below); waypoints 2,8 (Arcane Sanctuary) 3,6 (Kurast Bazaar) 3,8 (Travincal) 3,9 (Durance Level 2) 5,4 (Crystalline Passage) 5,8 (Ancients' Way) 1,1 1,2 1,4 1,5, then 3,9; `explore` of Durance Level 2 to its last room (25 hops); back to its waypoint, 5,8; `farm --descend 74` took the up warp to 117 (LvlWarp row 74 is *Ice Caves Up*), `--descend 71` back to 118; `explore` 61 hops of Ancients' Way, which activated the rooms at the summit's border and initialised level 120; `--descend 77` (*Ice Caves Down*, to 120) timed out |
  | `a35-s2-22-normal.log` | 22 | 2,5 (Far Oasis), 2,6 (Lost City), 3,9, 1,2, 1,4, 1,5, 1,7 (Jail Level 1); the first `wpchain` stopped after 2,5 on a missing screenshot directory and was restarted from Far Oasis |
  | `a35-s3-23-normal.log` | 23 | 2,4 (Halls of the Dead Level 2), 1,2, 1,4, 1,5 |
  | `a35-s4-24-normal.log` … `a35-s6-26-normal.log` | 24, 25, 26 | 1,2, 1,4, 1,5, 3,9 (Act I outdoor cottages for MonPlace 33, the Durance for MonPlace 35) |

  Checks: `python3 -I tools/drlg.py gen workspace/logs/acts35/a35-s*.log`; regression with the new checker on the
  run:2026-10-13-drlg-preset logs (`workspace/logs/preset-*.log`), the run:2026-10-12-drlg-gen + run:2026-10-15-drlg-maze
  list and the 11 run:2026-10-15-drlg-outdoor logs.
- **Observed:**
  ```
  drlg gen (6 logs): 155215 checks, 0 mismatches
    levels created DrlgType 1/2/3: 141/156/283; maze windows 42 (MZD draws checked 2764); outdoor windows 116
    preset rooms reproduced 1184 (602 with units), acts I-V, levels 1 2 3 5 6 7 11 20 29 43 44 57 74 80 81 83 101 102
      103 113 117 118 120
    preset rooms in maze levels (client / server copy): act I 8/3, act II 25/9, act III 52/36, act V 103/92
      (act III: Durance Level 2, 101, in s1, s2, s4, s5, s6; act V: 113 and 118 in s1)
    instance lists checked: after the level-seed rolls 562, after the room-seed rolls 1282, after PresetRoomLoadDs1 2234
    drop-roll calls: level seed 562 (37 draw), room seed 1282 (74 draw)
  drop-roll outcomes (each counted once per copy that rolls it; s = session):
    MonStats 371 kept 2 / dropped 6 (s1)           MonStats 372 kept 6 / dropped 6 (s2)
    MonPlace 33 kept 2 / dropped 2 (s4, Cott4A)    MonPlace 35 kept 12 / dropped 26 (s1 kept only; s2, s4, s5, s6)
    object 196 kept 20 / dropped 28 (s1)           object 261 kept 2 / dropped 6 (s3)
    also MonStats 204 dropped 3; 205 kept 1 / dropped 2; MonPlace 34 kept 10 / dropped 8; object 581 kept 134 / dropped 54
  act rewrites in rolled DS1s: act index 2 297 -> 382 (5), 366 -> 404 (2, TravN.ds1, s1);
    act index 4 514 -> 461 (1), 537 -> 476, 538 -> 475, 539 -> 474 (3 each, MtnTop.ds1, s1)
  client row skips (RSK): 5 logged, 5 modelled, all Def 1 file index 1 (TownE1.ds1), row 15, floor main 16 (s1-s5;
    s6's town took another file); client river objects Def 1 (6), Def 27 (6)
  level-27 index draw: link value 3 (6), link value 1 (4: s2, s5; r & 1 = 1 in both seeds, index 1), index and act
    seed after predicted
  regression: preset-*.log (27) 139032 checks, 0 mismatches; drlg-gen + drlg-maze list 206937, 0;
    run:2026-10-15-drlg-outdoor (11) 572211, 0 (the last two unchanged from their records)
  ```
- **Required cases:**

  | Case | Result |
  |---|---|
  | a maze preset room in Act III | reproduced: 88 room lists in Durance Level 2 (101), five sessions |
  | a maze preset room in Act V | reproduced: 195 room lists in Crystalline Passage (113) and Ancients' Way (118), s1 |
  | the act-index-2 rewrite of 366 | reproduced: `TravN.ds1` rolled on the level seed (`Scan` 1) when Travincal was built, s1 |
  | the act-index-4 rewrites 537..539 | reproduced: `MtnTop.ds1`, 537 → 476, 538 → 475, 539 → 474, s1 |
  | the draws of MonStats 371/372 | reproduced, both outcomes each (`r % 3 == 0` kept) |
  | the draw of MonPlace 33 | reproduced, both outcomes (`r & 3 ≠ 0` kept) |
  | the draws of objects 196/261 | reproduced, both outcomes each (`r & 1 == 0` kept) |
  | MonPlace 35 dropped | reproduced (26) |
  | at least one client row skip on a floor main | reproduced: 5 RSK lines equal the modelled skips |

  No case was left unreached.
- **Raw logs:** `workspace/logs/acts35/`: s1 `86e3e40002679d95…`, s2 `30d9eb7776d1d23d…`, s3 `1fea703ff4a3f808…`, s4
  `64edc517c14a386f…`, s5 `dce5af9062ff4e85…`, s6 `deea153fd0df2e7a…`. Screenshots: `a35-s1-wptabs-*.png` (load test),
  `wpchain-*.png` per hop (s1 in `workspace/logs/acts35/`, the others in `workspace/logs/acts35/sK/`), `pilot-s1-*.png`.
- **Deviations and limits:**
  - Normal only, expansion only, one character; no classic or Nightmare/Hell session (the cases are difficulty-free
    draws, but no other difficulty was logged here).
  - The RSK equality is checked only in logs carrying RSKON; the 27 run:2026-10-13-drlg-preset logs have none. Three of
    their instances (`preset-7-act1-nightmare`, `preset-play-act1` twice) take the same Def 1 file index 1 skip, which
    their instance lists after `PresetRoomLoadDs1` already matched; this run adds the direct observation.
  - Level 120 was initialised but never entered: the summit's `Scan` roll and rewrites happen when the level's rooms
    are created, which the activation at the 118/120 border did.
  - Not reached (not cases of this phase): the Blood Moor centre monster; the walk filters of levels 133–136.
- **Conclusion:** every drlg case of plan 0020 Phase 4 is reproduced bit-exactly, with no oracle. In
  [drlg/0004](0004-preset-units.md) the four drop tests left `[I]` (371/372, MonPlace 33, MonPlace 35 dropped,
  196/261), the rewrites 366 and 537..539 and the client row skip become `[C]`; the `v = 1` level-27 branch is `[C]` for
  the outcome seen (`r & 1 = 1`, index 1; index 2 stays `[I]`); and the maze preset rooms of Acts III and V join the
  checked set.
  (run:2026-10-15-acts-3-5, fn:DRLG_PresetUnitDropRolls@0x00667620, fn:DS1_Parse@0x00665950,
  fn:DRLG_PresetClientUnitsB@0x00666220, fn:sub_006772C0_LevelLinkBuild@0x006772C0)

## run:2026-10-15-cow-arcane

- **Question:** (plan 0027 Phase 3) Are the outdoor window of level 39 (Moo Moo Farm) and the maze window of level 74
  (Arcane Sanctuary, entered by waypoint) reproduced by `tools/drlg.py gen`, and does Act II row 8 of the waypoint
  menu take a `quests: all` character to 74 ([save/0002 § 5](../save/0002-quest-words.md#5-arcane-sanctuary-74-in-the-waypoint-menu-plan-0027-phase-2-2026-10-15))?
- **Setup:** pinned `game.exe` in `workspace/runtime/game` (stock data), slot 3, logger `tools/gdb/drlg-outdoor.gdb`.
  Character `CowNova` (expansion Sorceress, `tools/d2s_recipes/cownova.json` `763a25c9…d4f45eb3`, save
  `8c66964b…389efbc8`): `quests: all` (quest word 4 = `0x1`, so bit 10 clear; word 40 bit 0 set, in every difficulty),
  all waypoints, a Horadric Cube in the inventory holding Wirt's Leg (`leg`) and a Tome of Town Portal (`tbk`).
  Installed with `d2run.py --install h27`. Agent-driven, expansion Normal, seed 3301, one session.
- **Procedure:** `tools/d2run.py --slot 3 --seed 3301 --gdb tools/gdb/drlg-outdoor.gdb --steps
  tools/gdb/enter-normal.steps --after 3000 --log workspace/logs/cow-3301-normal.log --install h27 …CowNova.d2s`;
  `d2pilot.py --slot 3 wp <log> 2 8` (from the Act IV town: level 103 → 74 after 4.5 s); `explore --hops 15`, then
  `explore --to-rect 5088,1088,3,3` back to the waypoint (object class 402 at (25449, 5449)); `wpchain --chain "1,1"`
  (74 → Rogue Encampment, level 1); `xdrive key i`, `rclick 446 342` (the cube at inventory (0, 0)), `click 238 338`
  (Transmute): a red portal opened next to the player (screenshot `workspace/logs/cow-s3/portal-s3.png`); clicking it
  took the character to level 39; `explore --hops 40`; `slots.py stop 3`. Log manifest `cow-arcane-manifest.txt`
  (`212c39e2…e84c0e33`).
- **Result:**
  ```
  python3 -I tools/drlg.py gen workspace/logs/cow-3301-normal.log
  59 levels created; LevelInit by DrlgType: {1: [74], 2: [1, 1, 40, 103], 3: [2, 2, 39, 39, 104]}
    maze level-specific branch reached: 74                  2
    outdoor windows modelled: level 39                      2
  gen: 8778 checks, 0 mismatches
  ```
  (each window counted on the server and the client.)
  - Level 74 by waypoint: row 8 of the Act II tab with waypoint bit 16 set; no other gate fired.
  - The cow portal opened in single-player Normal from the cube recipe with the stock tables, on a character whose
    quest word 4 bit 10 is clear (items/0008 § 5.1).
  - Level 39's outdoor window (base 4, `Type` 0–3, drlg/0008) and level 74's maze window are generated as the models
    predict.
- **Not covered:** level 134 (named boundary, architect ruling 2026-10-15: the cube's Pandemonium outputs are stubs).
  The logger has no collision lines, so 74 adds no `Position` 1 level to drlg/collision.

## run:2026-10-16-sweep-roomk

- **Question:** (plan 0038 Phase 2, batch H5c, [inventory § 5](../../plans/0038-inventory/README.md#5-batch-list), plus the
  9 statements S4a returned to it, [inventory § 2.6](../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews))
  Do the release, unload and restore paths, the activation flags and RoomTile counts, PresetLevelBuild's act callbacks,
  the TINIT-exit flags, the cell build's level exceptions, Orient89Unit's draw, the warp exit and the warp pairing at
  activation, the act-seed steps, LevelCreate's and LevelInit's callers, the client unit's (x, y) test and the `-seed`
  parsing behave at runtime as drlg/0002, 0003, 0004, 0007 and rng/0002 read them?
- **Setup:** the ADR-0003 harness on **slot 4** (display `:11`, prefix `workspace/wineprefix-4`, game in
  `workspace/runtime/game`), wine and gdb as in run:2026-10-14-collision. Expansion, Normal, agent-driven (scripted
  `tools/d2pilot.py`; no owner play). Character `SpecNova` built with `python3 -I tools/d2s.py build
  workspace/merged/data/global/excel tools/d2s_recipes/specnova.json workspace/samples/d2s-owner/smpsor-l50.d2s
  workspace/runtime/h5c-chars/SpecNova.d2s` (recipe `a05e9959…1c7dc595`, save `649f8450…eba02dd5`, the save of
  run:2026-10-14-mon-special); the slot's empty saves directory set aside as tag `h5c` and the save installed on every
  launch with `d2run.py --install h5c`.
  - **Logger** `tools/gdb/sweep-roomk.gdb` (`9b331bc6…`): `drlg-gen.py`, `drlg-roomk.py`, `mon-spawn.py` (`83e7ab4b…`),
    `collision.py` (`1d10349e…`), `mon-special.py` (`73f0bc52…`) and `seed-tree-core.gdb` (`0ee24ceb…`). The H5c lines
    are listed in the headers of those files. **Revision per session** (`drlg-gen.py` / `drlg-roomk.py`):

    | Sessions | Commit | `drlg-gen.py` | `drlg-roomk.py` | Missing against the final logger |
    |---|---|---|---|---|
    | s1 | development | — | — | PLB and LUL0 wrote `client` = act `+0x478` (a memory context) instead of `dclient`; no PLBX at `0x006681F0`; no WRP, RNE/WPL, `r64` |
    | s2 | `b8b2a64` | `a9e89902…` | `74867c3d…` | PLBX at `0x006681F0`, WRP, RNE/WPL, `r64` |
    | s3–s5 | `6a06378` | `6dfeeef9…` | `c24c1676…` | RNE/WPL, `r64` |
    | s6 | `832c013` | `6dfeeef9…` | `3f14e6fa…` | `r64` |
    | s7–s11 | `62a32e5` | `6dfeeef9…` | `38effa7c…` | — |

    The checker reads every revision: a line a session lacks is not checked there.
  - **Checkers** `tools/drlg.py` (`fa9afa53…`: `roomk`, `gen`; the H5c checks are `h5c_event`, `h5c_ract`,
    `h5c_rne_close`, `plb_check`), `tools/collision.py` (`41462f10…`) with `tools/monspawn.py`, `tools/rng.py`
    (`2f87487e…`: `seedtree`).
  - **Regression before the first session** (the review's condition): the checkers before and after the edits on kept
    logs. `drlg.py roomk` on the six run:2026-10-11-drlg-roomk logs: 11 734 checks both, 0 mismatches. `drlg.py gen` and
    `collision.py check` on `collision-s1`…`s7`: gen 65 748, monspawn 75 812, collision 20 537 checks both, 0 mismatches.
    `rng.py seedtree` on the twelve `run-*.log` of run:2026-10-11-seed-tree and -p1: 5 954 → 5 976 checks (22 new: each
    ACTEND against the act model of `drlg.py`), 0 mismatches. After `main` (S4a) was merged in: `test_sweep_s4a.py` OK;
    `sweep_s4a.py pick`, `roomk`, `logic`, `barrier` give S4a's recorded counts (1 852 097 entries compared, 4 224 not
    compared, 1 280 `(10, 0, 0)` fallbacks; 38 509 flag-`0x1` merges; 1 475 floods and the 200-mismatch release-off
    control; 1 475 barrier grids), 0 mismatches.
- **Procedure** (per session: `MONSPAWN_WATCH= python3 -I tools/d2run.py --slot 4 --seed N --gdb
  tools/gdb/sweep-roomk.gdb --steps tools/gdb/enter-normal.steps --after 600…3000 --install h5c
  workspace/runtime/h5c-chars/SpecNova.d2s --log workspace/logs/<log>`; the game starts in the Act IV town; after
  `d2pilot.py hop <log> 0 0` (focus) the play below; end with `python3 -I tools/slots.py stop 4`; pilot options
  `--hop 10|12 --nova 2 --drink 0.6`, screenshots in `workspace/logs/sweep-roomk-shots/`):

  | Session | Log (`workspace/logs/`) | Seed | Play (`d2pilot.py --slot 4 …`) |
  |---|---|---|---|
  | s1 | `sweep-roomk-s1-777-normal.log` | 777 | `wp 1 2` (Cold Plains); `explore --hops 150` (level done after 96); four `wp` tries away from a waypoint failed |
  | s2 | `sweep-roomk-s2-12345-normal.log` | 12345 | `wp 1 2`; `wp 1 3 --wp-x 585 --wp-y 290`; `wpchain --chain "1,2 1,4 1,5 1,2 3,1 2,1 5,1 4,1 1,2" --linger 3` |
  | s3 | `sweep-roomk-s3-4242-normal.log` | 4242 | `wp 5 2` (Frigid Highlands, 111); `explore --hops 200` |
  | s4 | `sweep-roomk-s4-4343-normal.log` | 4343 | `wp 5 3` (Arreat Plateau, 112); `explore --hops 170` |
  | s5 | `sweep-roomk-s5-4444-normal.log` | 4444 | `wp 5 7` (Frozen Tundra, 117); `explore --hops 170` |
  | s6 | `sweep-roomk-s6-4545-normal.log` | 4545 | `wp 4 2` (City of the Damned, 106); `explore --hops 170` (done after 100) |
  | s7 | `sweep-roomk-s7-4646-normal.log` | 4646 | `wp 2 4` (Halls of the Dead 2, 57); `explore --hops 150` (done after 67); `farm --descend 45,46 --descend-time 150..200 --time 20..30` four times (57 → 56 → 57 → 56 → 57) |
  | s8 | `sweep-roomk-s8-4747-normal.log` | 4747 | `wp 2 8` (Arcane Sanctuary, 74); `explore --hops 120` (no path after 37) |
  | s9 | `sweep-roomk-s9-neg2147483648-normal.log` | `--seed=-2147483648` | `wp 1 2`; `explore --hops 50` |
  | s10 | `sweep-roomk-s10-2147483648-normal.log` | 2147483648 | town only, `--after 600` |
  | s11 | `sweep-roomk-s11-5151-normal.log` | 5151 | `wp 5 1` (Harrogath); `explore --any-level --hops 200` into Bloody Foothills (110) |

  The slot was yielded once to an owner session on slot 0, between s5 and s6.
  Check: `python3 -I tools/drlg.py roomk <all eleven logs>`; `python3 -I tools/drlg.py gen`, `python3 -I
  tools/collision.py check` and `python3 -I tools/rng.py seedtree` on the nine logs with an applied `-seed` (all but s9
  and s10; those two are the `-seed` observation, below).
- **Observed:**
  ```
  roomk (11 logs): 2071 activations, 87223 checks, 0 mismatches
  gen (9 logs): 99339 checks, 0 mismatches (roomk inside gen, 5 logs with OD0: 1456 activations, 61241 checks)
  monspawn: 150095 checks, 0 mismatches; collision: 14456 checks, 0 mismatches
  seedtree (9 logs): 117395/117395 match
  RoomTilesRelease of a built room (0x100000 cleared, act counter +1, RoomTile freed, warp nodes zeroed,
    0x1000000 / 0x2000000 / +0x2C / +0x04 kept, +0x30 = 0)  1516, of which 0x200000 set (EDX non-zero) 626;
    rooms with warp nodes 35; all 1516 through the wrapper 0x0066B4C0 (+0x60 = the active room's flags bit 0);
    nested outer calls that change nothing more 890
  RoomTilesRelease of an unbuilt room (only +0x30 cleared)  539
  logic record +0x64 = 0 at every release exit (s7-s11): freed 267, already 0 107
  re-activations of released rooms 235 (+0x04, level and DT1/DS1 bits kept): k equal to the first build 183, different 52
  neighbour entries last merged by a room that was later released, compared at a CB  3264
  LevelUnload keep 1 (0x00643245)  85; keep 0 (act free 0x006421B6)  103: +0x10, +0x08, +0x1CC, +0x1B0 zero;
    rotation list non-empty and freed 76; built rooms' RoomTiles freed through RoomFree 48
  LevelRoomStateRestore with the saved array 25 builds, rooms whose bit 0 it set 90; first builds 166
  LevelInit callers: ActCreate 23, RoomFromCoords 28, PresetLevelBuild 1, sub_0066B2B0 16, sub_0066C220 123
    (59 of the 191 builds were rebuilds of an unloaded level object); a level built twice without an unload 0
  PresetLevelBuild: client towns 40 / 103 / 109 -> one act[+0x488] call each (1 / 12 / 3; one of the 12 is s1's, act copy not logged); client levels 1 and 75,
    AutoMap 1 -> act[+0x454] per room; AutoMap 0 (levels 20, 50) -> none; server: both callbacks null (27 builds)
  activation flags 0 / 1 / 4: 606 / 133 / 1332, each = 4 if +0x28 & 0x40000 else 1 if +0x60 & 1 else 0
  RoomTile counts = the model's wall / floor entries 2066, above them by animation frames 5; RA0 (no wall) 351,
    all with floors; a room with neither: none
  TINIT exit 0x100000: 2071; HiddenWarpTilesAdd calls = the model's hidden-warp cells, 0x800000 at the exit (25 rooms)
  hidden orientation 8/9 built (not the oracle return) in levels 111 / 112 / 117: 51 / 4 / 57
  level 74 filler floors with key sub 1 (0x1E00100): 2973
  outdoor room mask by level type: 2 (0x44103) 240, 31 (0x11) 145
  Orient89Unit draws (tomb doors 91 / 92, level 57): 44, Range(3) = 0 / 1 / 2: 10 / 24 / 10; unit skipped on 0 (10),
    created otherwise (34)
  warp exits (rows 45, 46): 4, each = paired warp + LvlWarp ExitWalkX/Y of its row; the unit placed on the warp first
  RoomNeighboursEnsure (s6-s11): 695 calls (RoomActivateB 48, sub_0061B390 647), one WarpPairLink per warp bit in slot
    order each; Warp -1 (mark only) 725, paired 12; a room ensured again after LevelUnloadCheck cleared +0x2C: 1
  bit-2 merges 11490: entry flag 0x1 11447, row -1 (o 0 kept) 39, cell bit 7 4; through rows 0-5, row -2 or the 8/9
    edge rule: none
  act-seed steps after the act draws = drlg.py's act model, every act creation (42); seed 777 Act I: one LevelLinkBuild
    step (level 6, link 3, value (~lo) & 1 = 0) per copy
  LevelCreate callers: LevelEnsure 346, LevelUnloadCheck 29, LevelAddRef 5; a level id created twice in one act 0
  client units at (x, y) = (0, 0): 252, no ClientRoomAt call, seed {1, 666}; others 24565
  room-driver tests with flags bit 0: 2072 (290 on rooms whose activation flags were 1); a population pass after one 0;
    population passes 558, each after a test with bit 0 clear
  -seed -2147483648 (s9): GAME line from the no-override path 0x0052C2E2 (override 0, map 6b2d30db, entropy)
  -seed 2147483648 (s10): override 1, map 7fffffff, game seed 7fffffff:0000029a
  ```
- **The `-seed` parse (s9, s10), read with the code.** `sub_004058A0_ConfigParseCmdLine` scans the command line for
  `-` and hands the rest to `0x00405710`, which copies the switch text **up to the next `-`** (`0x00405784`). So
  `-seed -2147483648` gives `seed` an empty value, `atol` returns 0, and 0 is not an override: the game takes the entropy
  path. A value of 2³¹ or more written in positive decimal reaches `atol`, which saturates at `0x7FFFFFFF`. Neither form
  gives a seed of `0x80000000` or above from the command line. (fn:sub_004058A0_ConfigParseCmdLine@0x004058A0, 0x00405784,
  fn:GAME_InitSeeds@0x0052C280)
- **Raw logs** (sha256 in `workspace/logs/sweep-roomk-manifest.sha256`, `f86acdbf…4d2b97`): s1 `fe4b9c37…a811f914`,
  s2 `cc757f4e…5effeb06`, s3 `ad77b5e9…d8f9de9c`, s4 `afdfc6b3…96538153`, s5 `2172af1f…41eb2aa8`, s6 `bcc09024…2d986d77`,
  s7 `05414544…f982e13a`, s8 `cdcc1503…b001a2ed`, s9 `dadb0699…4cef6633`, s10 `f28a55b8…20864428`, s11
  `dacad9fe…2626dc15`; screenshots `workspace/logs/sweep-roomk-shots/`.
- **Deviations:** s1 ran a development logger (table above). The waypoint chain needs the character on the waypoint:
  an arrival from the town can leave it beside the waypoint, so s2's second hop used `--wp-x/--wp-y` from a
  screenshot. s9 and s10 are excluded from `gen`, `collision` and `seedtree`, which take the map seed from the
  `# d2run seed=` header: in s9 the game used an entropy seed and in s10 `0x7FFFFFFF`, so those models do not apply
  (`seedtree` on the two: 5455/6931; `gen` 330 mismatches, all in s10's outdoor windows). `roomk` needs no map seed
  and covers all eleven.
- **Not reached:** a bit-2 merge through the remap rows 0–5, the row −2 return or the 8/9 edge rule, and any merge
  into or out of orientation 3 (walled levels tried: Act V 110–112 and 117, City of the Damned, Halls of the Dead,
  Arcane Sanctuary, besides S4a's 42 logs; three attempts in a row, so the batch stopped trying); a room with no wall
  and no floor entry; LevelInit from `sub_0066B030`; LevelCreate from LevelRoomCount, RoomFromCoords and
  LevelSetPosition; outdoor masks of level types 16–30 in these logs (types 16 and 21 are in run:2026-10-14-collision);
  the player standing on a warp exit position (its walk is not followed to the end).
- **Conclusion:** raises the claims listed in the "Plan 0038 batch H5c" sections of drlg/0002, 0003, 0004, 0007 and
  rng/0002; contradicts rng/seeds step note 2's negative-decimal advice (above); corrects two readings: the release
  nests on the same room, and RoomNeighboursEnsure also runs on a room activated before, once LevelUnloadCheck has
  cleared its neighbour list (`0x006431C0`).
