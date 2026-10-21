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
    wall time is 429 min for 2.48 game minutes; the watchdog ended it on resume. Its log checks clean.
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
  created a few seconds before by a `MonSpawnTry` request in a neighbouring room in mode 3 (cn4: class 310, unit
  `48670976`, at (5398, 5237); cm4: class 189 at (7738, 6260)) is the nearest candidate. The log carries no line for a
  monster's movement between windows.
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
  (not 0), and 1 385 oracle-free room populations of the 2 000. Every other count of the bar is met.
