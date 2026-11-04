# Archaeology experiments

## run:2026-11-04-sound-logs

- **Question:** do the checkers that hold on `-ns` logs hold on the kept logs whose run records have `--sound`, with the seed stream intact, and does a sound-on and `-ns` pair exist? (Backlog `-ns` priority; [archaeology/0003](0003-sound-draws.md) § 5.)
- **Setup:** no game started. Replay of kept logs only, each under `systemd-run --user --scope -p MemoryMax=4G`. Tools at this commit, `tools/sound_pair.py` and `tools/sound_draws_scan.py` new. The 20 logs and their sha256: `workspace/logs/r63/manifest-inputs.txt` (run from `workspace/logs`).
- **Procedure** (`L=workspace/logs`, `O=workspace/logs/r63`, `python3 -I`):
  1. `tools/drlg.py gen $L/<log>.log` for `gen-1-catacombs-owner`, `preset-play-act1..5` → `gen-*.txt`; `tools/drlg.py roomk $L/gen-1-catacombs-owner.log` → `roomk-owner.txt`.
  2. `tools/monspawn.py check $L/<log>.log` for the three `monspawn-s*` logs → `check-*.txt`; `tools/chain.py check` on those, `tc-quality-1..3` and `quests-s0-3507-owner-forge-hell` → `chain-*.txt`.
  3. `tools/tc.py replay $L/<log>.log` for `tc-champion-1`, `tc-quality-1..3` → `replay-*.txt`. `tools/quality.py check` with `--mf 100`, `--mf 100`, `--mf 10`, none → `q-*.txt`.
  4. On each `quests-s0-350N-owner-*`: `tools/questdrops.py check` → `qd-*.txt`; `tools/tc.py replay --excel workspace/merged/data/global/excel` → `tc-*.txt`; `tools/items_chain.py affixes --excel …` → `ic-*.txt`; `tools/monpool.py check workspace/merged/data/global/excel` → `mp-*.txt`.
  5. `tools/sound_pair.py` on the seven pairs and seed 1 → `pair.txt`. `tools/sound_pair.py stream` on the monspawn logs → `gs-stream-sound.txt`.
  6. `tools/sound_pair.py mutate` on `monspawn-s1`, 16 tag and field choices, then `tools/monspawn.py check` and `stream` on each → `mutation-control.txt`; the mutated logs were not kept, being one-bit copies regenerable by the command.
  7. `tools/sound_draws_scan.py <game.exe> <section>` → `scan-*.txt`, static, the finding's route 1.
- **Observed** (trimmed; per-log in the outputs):
  ```
  drlg gen   7944 22855 18339 11535 10254 11064 checks, 0 mismatches
  monspawn   2659 81608 31528 checks, 0 mismatches; drlg gen 6816 36480 19710; roomk 3324 23427 18275
  chain      7 logs, 0 sub-checks failed
  tc replay  124, 1269, 944 calls, 0 failed; classic 485 reproduced; quests 14 9 22 14 127 31
  quality    65 782 574 229 pairs, 0 failed
  items      17 52 74 61 68 52 31 creations, 0 failed;  monpool 309 844 993 821 702 507 561 match
  questdrops 7 logs, 0 mismatches (no seed stream); roomk on gen-1-catacombs-owner: 0 checks (no lines)
  pair       levels created in both 63, same create seed 63; levels with RC in both 15, a common room sequence 15 (1152 rooms)
  stream     gs values 1519, 34608, 15687; breaks 0
  mutation   caught: P0 gs, P0 rs, PX gs, PX rs, RW1 rs, RW4 gs, RW4 rs, SP0 rs; not caught: MT0 gs, MT0 rs, MTX gs, MU gs, MU rs, RW1 gs, MU us, SPX rs
  ```
- **Conclusion:** [archaeology/0003](0003-sound-draws.md)'s two confirmed Answer bullets (run:2026-11-04-sound-logs). A checker's 0 is not evidence about a game-seed draw between its windows, and these runs don't prove the device opened; the pair session is § 6 of the finding.
