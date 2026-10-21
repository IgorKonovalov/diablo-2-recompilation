# Experiments — chain (seed to world, plan 0048)

## run:2026-10-20-chain

- **Question:** (plan 0048 Phase 2) Does the composition of the reviewed models (`tools/chain.py check`) reproduce
  fresh games from known `-seed` values end to end, with the only inputs those Phase 0 kept, over every generator
  kind, act, difficulty and game type?
- **Setup:** ADR-0003 harness, slot 1 (`:8`, `workspace/wineprefix-1`), the pinned `game.exe`. Logger
  `tools/gdb/chain.gdb` (the full loggers, Phase 1 review ruling 3), `MONSPAWN_WATCH` empty. Characters `UniqNova`
  (expansion, `tools/d2s_recipes/uniqnova.json`) and `UniqClassic` (classic, `uniqclassic.json`), built with
  `tools/d2s.py build` into `workspace/runtime/p48h-chars/`, installed per session (saves tag `p48h`, set aside and
  restored by the driver; the slot's saves directory was empty before the run and is empty after it).
  Session driver `tools/chain_sessions.py run --slot 1 --tag p48h --saves workspace/runtime/p48h-chars --run p2
  <session>…`: one game per session, waypoint then `tools/d2pilot.py explore` (Teleport, Nova on F1, Energy Shield on
  F2 outside Normal, `--loot`), a watchdog (raw log cap 500 MB, wall limit 15 min from game entry, 90 s of silence,
  gdb's exit line). Each session's row (save, difficulty, seed, waypoint) is in that file's `PLAN`. Nothing the pilot
  computes feeds a model.
- **Procedure:** the 28 counted sessions below (2026-10-20 14:46 to 2026-10-21 07:09), then, from the repository root,
  each under `systemd-run --user --scope -p MemoryMax=4G`:
  ```
  python3 -I tools/chain.py check $(ls workspace/logs/chain-p2/p2-s1-*.log | grep -v raven-xn.log) \
      --o20 workspace/logs/chain-p2/out/final-o20.json                > out/final-check.txt
  python3 -I tools/chain.py check <log>                                > out/final-per-log/<log>-check.txt  # each log
  python3 -I tools/chain.py check <log> --cf monequip-off              > out/cf-monequip-off-<log>.txt      # raven-xn2, cn2
  (cd workspace/logs/chain-p1 && python3 -I ../../../tools/chain.py check $(awk '{print $2}' inputs-world.sha256)) \
                                                                       > out/p1world-check-final.txt
  ```
  Manifest `workspace/logs/chain-p2/manifest-final.txt` (sha256 prefix `e47bb1b13e2cc7ca`, 127 lines, paths relative
  to `workspace/logs/chain-p2/`, so `sha256sum -c manifest-final.txt` passes from there): the 28 logs, their
  `.session.json` and `.pilot.txt`, the development logs, the outputs above (`final-check.txt` `79c3a7a7a4a476e6`) and
  the tool revisions `out/tools-final.sha256` (`4de34c2aef962d18`, paths from the repository root; `tools/objects.py`
  is commit `dfe3e5e`'s). The checkpoint's manifest `manifest-ckpt1.txt` stays as kept.

| Log | Seed | Character | Difficulty | Levels (PLR order) | Wall min | Game min | MB | Ended |
|---|---|---|---|---|---|---|---|---|
| `p2-s1-4801-smoke.log` | 4801 | UniqNova | normal | 103, 3, 4 | 8.4 | 3.45 | 7.8 | commands done |
| `p2-s1-4802-xn2.log` | 4802 | UniqNova | normal | 103, 57 | 5.3 | 4.0 | 4.7 | commands done |
| `p2-s1-4803-xn3.log` | 4803 | UniqNova | normal | 103, 76, 77 | 15.0 | 7.97 | 16.4 | time |
| `p2-s1-4804-xn4.log` | 4804 | UniqNova | normal | 103, 106, 105, 104 | 15.0 | 6.37 | 14.9 | time |
| `p2-s1-4805-xn5.log` | 4805 | UniqNova | normal | 103, 113 | 8.2 | 4.09 | 5.4 | commands done |
| `p2-s1-4807-raven-xn2.log` | 4807 | UniqNova | normal | 103, 3, 17, 3, 2 | 15.0 | 4.84 | 9.6 | time |
| `p2-s1-4811-xm1.log` | 4811 | UniqNova | nightmare | 103, 35 | 3.0 | 1.96 | 2.7 | commands done |
| `p2-s1-4812-xm2.log` | 4812 | UniqNova | nightmare | 103, 42, 41 | 15.0 | 5.13 | 8.7 | time |
| `p2-s1-4813-xm3.log` | 4813 | UniqNova | nightmare | 103, 101 | 13.7 | 10.39 | 9.4 | commands done |
| `p2-s1-4814-xm4.log` | 4814 | UniqNova | nightmare | 103, 107 | 15.0 | 5.8 | 14.6 | time |
| `p2-s1-4815-xm5.log` | 4815 | UniqNova | nightmare | 103, 111, 110 | 15.0 | 6.18 | 17.2 | time |
| `p2-s1-4821-xh1.log` | 4821 | UniqNova | hell | 103, 3, 4, 3, 2 | 15.0 | 5.11 | 11.1 | time |
| `p2-s1-4822-xh2.log` | 4822 | UniqNova | hell | 103, 74 | 1.7 | 0.83 | 2.1 | commands done |
| `p2-s1-4823-xh3.log` | 4823 | UniqNova | hell | 103, 78 | 15.0 | 4.22 | 14.4 | time |
| `p2-s1-4824-xh4.log` | 4824 | UniqNova | hell | 103, 106, 105 | 429.3 | 2.48 | 8.2 | time |
| `p2-s1-4825-xh5.log` | 4825 | UniqNova | hell | 103, 115 | 15.0 | 7.0 | 7.9 | time |
| `p2-s1-4831-cn1.log` | 4831 | UniqClassic | normal | 103, 35 | 5.8 | 4.08 | 3.9 | commands done |
| `p2-s1-4832-cn2.log` | 4832 | UniqClassic | normal | 103, 42, 43 | 15.0 | 5.22 | 8.0 | time |
| `p2-s1-4833-cn3.log` | 4833 | UniqClassic | normal | 103, 76 | 15.0 | 7.3 | 12.8 | time |
| `p2-s1-4834-cn4.log` | 4834 | UniqClassic | normal | 103, 106, 105, 104 | 15.0 | 7.84 | 14.2 | time |
| `p2-s1-4841-cm1.log` | 4841 | UniqClassic | nightmare | 103, 3, 2, 3 | 15.0 | 7.45 | 10.1 | time |
| `p2-s1-4842-cm2.log` | 4842 | UniqClassic | nightmare | 103, 57 | 5.9 | 3.43 | 4.4 | commands done |
| `p2-s1-4843-cm3.log` | 4843 | UniqClassic | nightmare | 103, 78 | 15.0 | 5.78 | 9.2 | time |
| `p2-s1-4844-cm4.log` | 4844 | UniqClassic | nightmare | 103, 107 | 14.5 | 6.91 | 15.8 | commands done |
| `p2-s1-4851-ch1.log` | 4851 | UniqClassic | hell | 103, 6, 5, 6 | 15.0 | 7.77 | 14.8 | time |
| `p2-s1-4852-ch2.log` | 4852 | UniqClassic | hell | 103, 74 | 15.0 | 8.14 | 8.4 | time |
| `p2-s1-4853-ch3.log` | 4853 | UniqClassic | hell | 103, 101 | 3.9 | 2.89 | 3.1 | commands done |
| `p2-s1-4854-ch4.log` | 4854 | UniqClassic | hell | 103, 106, 105, 106 | 15.0 | 7.16 | 13.2 | time |

  153.8 game minutes in all. No log holds gdb's `internal-error:`; no session reached the cap.
  - **Development logs** (kept, no claim rests on them): `dev-p2-s1-4803-xn3-aborted` (the driver restarted),
    `dev-p2-s1-4812-xm2-paused` (cut by the owner's pause), `dev-p2-s1-4815-xm5-oom` (cut at 20:12 on 2026-10-20 when
    systemd-oomd killed the lane's agent and driver; the game ran on without a pilot until `d2run.py`'s timer; xm5 was
    re-run on the same seed), and `p2-s1-4807-raven-xn.log` (its collision logger error, `LOGERR collision
    MemoryError`, is fixed as `DCRF`; raven-xn2 re-ran it on the same seed).
  - **xh4** sat through a suspend of the machine (about 23:17 to 06:19; the PLR game frames stop at 3 729), so its
    wall time is 429 min for 2.48 game minutes; the watchdog ended it on resume. Its log checks clean. The 1 962 lines
    after its last `PLR` line (46 632) carry no frame, so whether they ran before the suspend or after the resume is not
    shown; no model reads wall time, and the session is admitted as a reproduction only (review ruling, plan 0048 log),
    not for any timing figure.
  - The session order differs from the resume note's (classic and Hell sessions were interleaved); every session of
    the note's list ran once, counted, besides those re-run above.
- **Observed** (`out/final-check.txt`, trimmed): `chain: 28 logs, 2 sub-checks failed`.
  ```
  levels built (level, difficulty, game type)                     156   (DrlgType 1: 56, 2: 33, 3: 67)
  levels built, difficulty 0/1/2, classic: acts 1234 each (24, 24, 20 levels); expansion: acts 12345 each (33, 26, 29)
  room populations end to end with no oracle                     1385   (N cl 232, N exp 351, NM cl 156, NM exp 231,
                                                                          H cl 192, H exp 223); creations in them 7340
  windows RW1 -> RW4 with no oracle left inside                  3140   (41 with one: OPUX 31, MTX 3, InitFn 62 3,
                                                                          InitFn 25 2, InitFn 43 1, GOLD 1)
  objects created (populate) 1817, (preset) 7240
  specials: champion packs 44, uniques and minion packs 110, special mods rolls predicted 147
  unit seeds after SUnitCreate predicted (oracle 14)             8588 of 8588 creations
  tc: TC_ResolveDrops calls reproduced (quality modelled)        2514, failed 0; monster drops with an item 849,
                                                                          items made 951; object-source calls 202
  items: creations reproduced from the affix and property lines  1286 each, failed 0
  monspawn checks 1195928, mismatches 2; monstats checks 191475, mismatches 0
  oracle 13: MonEquipInit oninit creations reproduced            class 267 1 (raven-xn2), class 234 1 (cn2); items 2
  oracle 19: LevelRoomCount reads (OG cnt) 2470; gate inputs asserted against chain/0002 § 7: pop 0 or the level id
             3121 True, preset value in {0, 0x80} 2470 True, town test = LevelIsTown 2351 True, 62 gates closed by 0x30000
  oracle 20: R3 pass rooms 3183, exact 3069, with a residue 114; residue cells +0080 136, +0100 119, +0400 16,
             +0404 3, +0800 5, +1080 34, +1100 30; object-bit residue cells: 19 with a nearest line (OU0), 0 unexplained
  ```
  The two failures, both `COLL_WHTest` position tests of the objects model inside a presets window
  (`out/final-per-log/`): cn4 line 72971 (site `0x005504B3`, (5402, 5241) 8×8, mask `0x3F11`: game `0x1100`, model
  `0x0000`) and cm4 line 53279 (site `0x00550B89`, (7742, 6264) 10×10: game `0x1500`, model `0x0400`). In both the game
  sees a live monster's bits (`0x100` footprint, `0x1000` centre) that no logged mark explains; in each, a monster
  re-created by a `MonSpawnTry` request in a neighbouring room in mode 3 (cn4: class 310, unit `48670976`, id 522, at
  (5398, 5237); cm4: class 189 at (7738, 6260) and (7736, 6262)) stands inside the tested rectangle, which
  `COLL_WHTest` centres on (x, y). Each is a monster the population pass made in mode 1 and the request re-made after
  its room's return; the re-creations have no `CM` line and the model applies no mark for them (corrected at the
  review, chain/0003 § 2; first recorded as a candidate 4 cells off the rectangle that had walked).
  The remaining oracles of the summary, by name and count, are the run's inputs and remaining oracles (the record of
  ruling 2): the state InitFns' modes and interact bytes, the timer draws (13 823), the operate and trap spawns,
  `LevelRoomCount` (59 windows), the gate inputs (3 183), the revisit restores (31), the preset units of types 1 and 5
  (574, 174: their monsters are `tools/monspawn.py`'s), InitFn 46's requests (247, predicted by `tools/monspawn.py`),
  the class-434 mode (3), MonPlace rows 5, 10 and 11 (1, 4, 3), creations outside the model with no level known (33),
  region appends by a creation outside the model (9), the presets-window cell tests whose room has no cells (28 each),
  the special-count increment in a preset's creation (3), one gold spot, and three chest interact bytes (below).
  Inputs: `AROOM` 12 133, `LG0` 4 101, `NWW` 16 541, `OG` 3 183, `PLR` 34 783, `SN` 3 183, `TCR` 2 514 (with the game
  seed at each drop), `QKMF` 333, `QMF` 338.
  - **Checker scope change during the run** (commit `dfe3e5e`): xm3 had two chests (`OperateFn` 4, classes 183 and 181,
    Durance of Hate 2) reach their operate with the lock bit `0x80` set after a creation with interact 0, and xm5 one
    (class 430) created with `0x86` reach it with 0; no logged line writes the byte in between, so the byte is taken and
    counted (`chest interact byte lock bit set` 2, `cleared to 0` 1), as the checkpoint's xn2 case (`lock bit cleared`,
    now 3). The change leaves the Phase 1 world logs' summary as it was (`out/p1world-check-final.txt` against
    `out/p1world-check.txt`: only the `--o20` lines, not requested, differ).
  - **Controls:** `--cf monequip-off` fails raven-xn2 and cn2 with one mismatch each, at the class-267 and class-234
    creations (`out/cf-monequip-off-*.txt`).
- **Conclusion:** [chain/0003](0003-end-to-end-run.md). The run does **not** meet Phase 2's bar yet: 2 mismatches
  (not 0), and 1 222 oracle-free room populations of the 2 000 on the 26 passing logs (1 385 with cn4's and cm4's,
  which count only once those logs pass). Every other count of the bar is met on the 26 passing logs alone.
- **Review re-run** (architect, 2026-10-21, on `lane/p48h` after merging `main`, under `MemoryMax=4G`):
  `sha256sum -c manifest-final.txt` clean (`e47bb1b13e2cc7ca`, 127 lines); the 28-log check above on the merged tree
  equals `out/final-check.txt` byte for byte (paths aside) and `final-o20.json` is identical; the same check without
  cn4 and cm4, `chain: 26 logs, 0 sub-checks failed`, 1 222 populations, 148 levels, 8 231 objects, 745 drops with an
  item. Outputs `out/review-check.txt`, `out/review-check-26.txt`, `out/review-o20.json`, `out/review-meq.py` (the
  `monequip.bin` rows of classes 234 and 267), hashed in `out/review-manifest.txt` (`5ba2d0051461a63d`).

## run:2026-10-21-chain2

- **Question:** (plan 0048 Phase 2, run 2) With the revisit re-creations' marks logged and modelled, does the
  composition (`tools/chain.py check`) reproduce run 1's 28 logs and the new sessions with 0 mismatches, and do the
  passing logs together hold the bar's 2 000 oracle-free room populations?
- **Setup:** as [run:2026-10-20-chain](#run2026-10-20-chain): ADR-0003 harness, slot 1 (`:8`,
  `workspace/wineprefix-1`), the pinned `game.exe`, logger `tools/gdb/chain.gdb`, characters `UniqNova` and
  `UniqClassic` from `workspace/runtime/p48h-chars/` (saves tag `p48r2`; the slot's saves directory was empty before
  the run and is empty after it). Driver `tools/chain_sessions.py run --slot 1 --tag p48r2 --saves
  workspace/runtime/p48h-chars --run p2r2 <session>…`, its `PLAN2` rows (seeds 4861..4912, mostly outdoor waypoints),
  same watchdog. New in the logger (commit `53ffb95`): `tools/gdb/collision.py` writes `CMR0 {th, room}` .. `CMRX`
  around the two `sub_00542B40_RoomInactiveUnitsRestore` calls (`0x0052D142`, `0x0052D205`) and logs the `CM` mark
  lines inside that scope as inside a window. New in the checker (same commit): `tools/objects.py` `recreation`
  predicts each re-creation's marks and compares them with the scope's `CM` lines (on run 1's logs, which have no
  scope, it applies them unchecked); `--cf recreation-off` is its control. Tool revisions `out/tools-r2-final.sha256`
  (`797865e9ba9fac87`, paths from the repository root; every listed tool is commit `53ffb95`'s, unchanged since the
  run's checkpoint `out/tools-r2-ckpt1.sha256`).
- **Procedure:** the nine sessions below (2026-10-21, two before the owner's pause, seven after), then, from the
  worktree root, each under `systemd-run --user --scope -p MemoryMax=4G`:
  ```
  python3 -I tools/chain.py check $(ls workspace/logs/chain-p2/p2-s1-*.log | grep -v raven-xn.log) \
      workspace/logs/chain-p2/p2r2-s1-*.log --o20 out/r2final-o20.json        > out/r2final-check.txt
  python3 -I tools/chain.py check <log>                       > out/r2final-per-log/<log>-check.txt   # each of the 37
  python3 -I tools/chain.py check <log> --cf recreation-off   > out/r2final-cf-recreation-off-<log>.txt  # cn4, cm4, r2-xn1
  python3 -I tools/chain.py check <log> --cf monequip-off     > out/r2final-cf-monequip-off-<log>.txt    # r2-xn2, r2-xm1
  (cd workspace/logs/chain-p1 && python3 -I <worktree>/tools/chain.py check $(awk '{print $2}' inputs-world.sha256)) \
                                                              > out/r2final-p1world-check.txt
  ```
  `out/r2final-recreations.txt` tabulates the per-log outputs (populations and re-creations by kind). Manifest
  `workspace/logs/chain-p2/manifest-r2-final.txt` (sha256 prefix `e1d9e622a85995f5`, 169 lines, paths relative to
  `workspace/logs/chain-p2/`; `sha256sum -c` passes from there): the 37 counted logs with their `.session.json` and
  `.pilot.txt`, the outputs above, the development outputs `out/dev-r2-*` and the tool hashes. Run 1's
  `manifest-final.txt` and the checkpoint's `manifest-r2-ckpt1.txt` stay as kept (the checkpoint's stub
  `p2r2-s1-4871-r2-xm1.pilot.txt`, empty, is renamed `dev-p2r2-s1-4871-r2-xm1-paused.pilot.txt` so the session could
  run under its name; its line in `manifest-r2-ckpt1.txt` now fails `sha256sum -c`, because the name holds the
  session's pilot: the empty stub's hash, `e3b0c442…`, is in `manifest-r2-final.txt` under the new name (corrected at
  the review; the run first said the line no longer resolves)).

| Log | Seed | Character | Difficulty | Levels (PLR order) | Wall min | Game min | MB | Ended |
|---|---|---|---|---|---|---|---|---|
| `p2r2-s1-4861-r2-xn1.log` | 4861 | UniqNova | normal | 103, 106, 105, 104 | 15.0 | 7.95 | 14.9 | time |
| `p2r2-s1-4862-r2-xn2.log` | 4862 | UniqNova | normal | 103, 3, 2, 3, 17 | 15.0 | 6.85 | 12.1 | time |
| `p2r2-s1-4863-r2-xn3.log` | 4863 | UniqNova | normal | 103, 76, 78 | 15.0 | 7.93 | 17.0 | time |
| `p2r2-s1-4871-r2-xm1.log` | 4871 | UniqNova | nightmare | 103, 3, 4, 3, 17, 3, 2 | 15.0 | 7.56 | 14.4 | time |
| `p2r2-s1-4872-r2-xm2.log` | 4872 | UniqNova | nightmare | 103, 106, 105, 104, 103, 104 | 15.0 | 8.44 | 17.0 | time |
| `p2r2-s1-4881-r2-xh1.log` | 4881 | UniqNova | hell | 103, 6, 7, 6 | 15.0 | 7.58 | 13.6 | time |
| `p2r2-s1-4891-r2-cn1.log` | 4891 | UniqClassic | normal | 103, 106, 105 | 14.3 | 7.28 | 12.6 | quiet: log unchanged for 90 s |
| `p2r2-s1-4901-r2-cm1.log` | 4901 | UniqClassic | nightmare | 103, 106, 105, 104 | 15.0 | 8.47 | 14.6 | time |
| `p2r2-s1-4911-r2-ch1.log` | 4911 | UniqClassic | hell | 103, 106, 105 | 12.7 | 5.71 | 9.9 | commands done |

  67.8 game minutes in all. No log holds gdb's `internal-error:`; no session reached the cap.
  - **cn1**: the game process ended on its own at game frame 10 920 (gdb: `[Inferior 1 … exited normally]`), the
    pilot still exploring level 105; the cause is not shown (the last screenshot is a live game). The log is whole up
    to the exit and checks clean; the watchdog ended the session on silence.
  - The queue was the resume note's first seven sessions (r2-xm1 r2-xh1 r2-cn1 r2-cm1 r2-ch1 r2-xn3 r2-xm2), run in
    that order; the passing logs held 2 000 after them, so the optional seven were not run.
  - **Development outputs** (kept, no claim rests on them): `out/dev-r2-*` from the checkpoint (run before the
    final tools were fixed, or as the checkpoint's controls), and `out/dev-r2-p1world-check-maintools.txt`: a Phase 1
    re-check whose `../../../tools/chain.py` resolved through the `workspace` symlink to the main checkout's (run 1's)
    tools; it is byte-identical to run 1's `p1world-check-final.txt` and was re-run with the worktree's tools.
- **Observed** (`out/r2final-check.txt`, trimmed): `chain: 37 logs, 0 sub-checks failed`.
  ```
  levels built (level, difficulty, game type)                     176   (DrlgType 1: 65, 2: 36, 3: 75)
  levels built, difficulty 0/1/2, classic: acts 1234 each (24, 24, 20 levels); expansion: acts 12345 each (35, 36, 37)
  room populations end to end with no oracle                     2189   (N cl 323, N exp 593, NM cl 264, NM exp 450,
                                                                          H cl 263, H exp 296); creations in them 10764;
                                                                          58 levels, 43 (level, difficulty) pairs
  windows RW1 -> RW4 with no oracle left inside                  4827   (56 with one: OPUX 39, MTX 9, InitFn 62 1,
                                                                          InitFn 62 and OPUX 2, InitFn 25 2, InitFn 43 2,
                                                                          GOLD 1)
  objects created (populate) 2888, (preset) 10168
  specials: champion packs 63, uniques and minion packs 162, special mods rolls predicted 217
  unit seeds after SUnitCreate predicted (oracle 14)             12580 of 12580 creations
  tc: TC_ResolveDrops calls reproduced (quality modelled)        3784, failed 0; monster drops with an item 1314,
                                                                          items made 1492; object-source calls 265
  items: creations reproduced from the affix and property lines  1913 each, failed 0
  monspawn checks 1641203, mismatches 0; monstats checks 275898, mismatches 0
  re-creations by the revisit restore                            7290: marks compared with the logged CM lines 1903
                                                                          (alive 1729, dead deadCol 0 166, deadCol 1 8),
                                                                          applied unchecked on run 1's logs 5284 (4953,
                                                                          328, 3), request made no unit 103;
                                                                          restore scopes logged (CMR0 .. CMRX) 1000
  oracle 13: MonEquipInit oninit creations reproduced            class 267 3 (raven-xn2, r2-xn2, r2-xm1), class 234 1
                                                                          (cn2); items 4
  oracle 19: LevelRoomCount reads (OG cnt) 3885; gate inputs asserted against chain/0002 § 7: pop 0 or the level id
             4801 True, preset value in {0, 0x80} 3885 True, town test = LevelIsTown 3676 True, 82 gates closed by 0x30000
  oracle 20: R3 pass rooms 4883, exact 4723, with a residue 160; residue cells +0080 192, +0100 166, +0400 28,
             +0404 3, +0800 5, +1080 48, +1100 43; object-bit residue cells: 31 with a nearest line (OU0), 0 unexplained
  ```
  Per log (`out/r2final-recreations.txt`): every one of the 37 checks alone with 0 sub-checks failed; run 1's 28 logs
  hold 1 387 populations (cn4 118, cm4 47) and 5 348 re-creations, run 2's nine 802 populations (xn1 94, xn2 73, xn3
  75, xm1 99, xm2 120, xh1 73, cn1 90, cm1 107, ch1 71) and 1 942 re-creations, of which 1 903 compared line for line
  and 39 made no unit.
  The remaining oracles and inputs of the summary, by name and count: the state InitFns' modes (952) and interact
  bytes (49), the object timer draws (20 109), the operate and trap spawns (6, 25, 2), the non-container OperateFns
  (53), `LevelRoomCount` (88 windows), the gate inputs (4 883), the revisit object restores (35), the preset units of
  types 1 and 5 (695, 281: their monsters are `tools/monspawn.py`'s), InitFn 46's requests (491, predicted by
  `tools/monspawn.py`), InitFns 25, 43 and 62 (2, 2, 7), the class-434 mode (3), MonPlace rows 5, 10 and 11 (3, 4, 3),
  creations outside the model with no level known (34), region appends by a creation outside the model (12), the
  presets-window cell tests whose room has no cells (35 each), the special-count increment in a preset's creation (8),
  one gold spot, and the chest interact bytes taken at the operate (lock bit set 2, lock bit cleared 3, cleared to 0 2;
  r2-xm1 holds the second "cleared to 0"), and oracle 25 (chain/0001: the restored monster's state, a simulation
  input): each revisit re-creation's class and unit id (`MT0`), cell (`MU0`) and alive or dead (`a10`) are taken from
  the log, 7 290 re-creations (103 of them made no unit; added at the review). Inputs: `AROOM` 18 459, `LG0` 7 343, `NWW` 21 943, `OG` 4 883, `PLR`
  51 214, `SN` 4 883, `TCR` 3 784 (with the game seed at each drop), `QKMF` 473, `QMF` 479.
  - **Phase 1 world logs** (`out/r2final-p1world-check.txt`): `chain: 62 logs, 0 sub-checks failed`; the summary equals
    run 1's `out/p1world-check-final.txt` line for line but four new re-creation lines (529 re-creations, marks applied
    unchecked: 498 alive, 26 dead deadCol 0; 5 made no unit). No regression.
  - **Controls:** `--cf recreation-off` fails cn4 and cm4 with exactly run 1's two mismatches (cn4 line 72971, cm4
    line 53279, the same `COLL_WHTest` results) and fails r2-xn1 with 63 mismatches, every one a re-creation's logged
    marks against an empty prediction (a floor, not 288: after each mismatch the checker resyncs to the next `RW1`,
    `OO0`, `OGC` or `OPU0`, so the rest of that restore stretch is not tested; added at the review); `--cf monequip-off` fails r2-xn2 (line 48791) and r2-xm1 (line 52802), each at
    a class-267 `MonEquipInit` unit seed.
- **Conclusion:** [chain/0003](0003-end-to-end-run.md). With run 2's tools the 37 logs reproduce with 0 mismatches
  and hold 2 189 oracle-free room populations; every other count of the Phase 2 bar is met on the same logs.
