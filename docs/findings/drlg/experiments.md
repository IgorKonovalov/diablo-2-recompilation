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
