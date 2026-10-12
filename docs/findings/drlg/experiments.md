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
  and the `File` cell it loads); PUR/PURX around `sub_00667620_PresetUnitDropRolls` at `0x00667A35` (oracle);
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
  the re-seed, the level-seed draws of each generator in order (with `sub_00667620_PresetUnitDropRolls` and the
  maze and outdoor generators as boundary oracles), the preset file index (draw, overrides, maze rotation, the
  `Files` operand), the room-creation order of the preset split and the outdoor cells, the maze conversion order,
  and `sub_006706A0_LvlSubRoll`.
