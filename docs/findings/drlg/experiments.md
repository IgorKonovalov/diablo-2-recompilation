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
