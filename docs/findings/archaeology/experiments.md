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

## run:2026-11-04-sound-pair

- **Question:** with the same seed, the same save and the same scripted inputs, is the game seed's stream the same with `-ns` and with `--sound`, and does `--sound` open the sound device on this harness? ([archaeology/0003](0003-sound-draws.md) § 6; backlog `reverser-sound-pair-session-next-harness`.)
- **Setup:** slot 2 (display `:9`), `tools/saves.py --slot 2 aside snd`, the act-5 save `smpsor.d2s` installed, Normal, seed 12345. Logger `tools/gdb/sound-pair.gdb` (sha256 in `workspace/logs/snd/tools-hash.txt`): `tools/gdb/mon-spawn.gdb` with a one-shot breakpoint at `0x00482C20`, ignore count 2000, that prints `0x00881768`, `0x007C545C`, `0x007C8C78` and the 8 bytes at `[0x007A6A70]+0x20`, then disables itself. Steps `tools/gdb/sound-pair.steps` is `preset-harrogath-pop.steps` with the three `shot` paths moved under `workspace/logs/snd/` (nothing else changed). A fresh process per run, `slots.py stop 2` between runs, `--after 60`. Saves restored at the end.
- **Procedure:** `d2run.py --slot 2 --seed 12345 --gdb tools/gdb/sound-pair.gdb --steps tools/gdb/sound-pair.steps --after 60 --log workspace/logs/snd/pair-{A1,A2}.log` (A1, A2 with `-ns`), the same with `--sound` for `pair-B.log`. Then `tools/sound_pair.py stream` on the three, and `tools/sound_pair.py seeds` (new subcommand: every event line's tag and `xxxxxxxx:xxxxxxxx` seed fields in order, which includes each `gs`) on A1/A2 and A1/B, output `seeds.txt`. The `gs` first-difference positions and the heap-address remark are from an ad hoc session comparison, not kept.
- **Observed:**
  ```
  device words at the 2000th hit of 0x00482C20 (0x00881768 / 0x007C545C / 0x007C8C78)
    A1  0x00000000 / 0x00000000 / 0x00000000      client seed +0x20: d20415c0 5de8b65f
    A2  0x00000000 / 0x00000000 / 0x00000000      client seed +0x20: ba498698 4b4d7291
    B   0x00dc519c / 0x00000001 / 0x00000001      client seed +0x20: 34310a76 0fc85e31
  game seed ("gs" field): 147 values in each log, first differing position: A1/A2 none, A1/B none, A2/B none
  stream.txt: each log 147 values, 0 breaks, gaps (0:132, 1:10, 2:2, 3:1, 4:1), identical in the three
  event lines carrying seed fields (2 565 lines in each, `seeds.txt`): tag and seed fields identical in order for A1/A2 and A1/B
  lines that differ A1 vs B: heap addresses only (room, ps, level base, WNDARM base); A1 vs A2 differ in none
  ```
  Both A logs have 14 `LC0` lines, 790 `RC`/`RW0`/`AROOM`/`RACT` lines; B has the same counts. The three session screenshots of each run (`shots-*`) show the walk happening in Harrogath.
- **Conclusion:** (1) **The two `-ns` runs agree** on every seed stream and every event line (addresses included); they differ in one thing, the client player's seed at the sampled frame. (2) **The device opened in B** (`0x00881768` non-zero, the two flags 1) and did not in A1 and A2 (all 0). (3) **The game seed's stream is identical with and without sound for this walk**: seed 12345, the act-5 `smpsor.d2s` character on Normal, the `preset-harrogath-pop` steps, 147 logged `gs` values, 14 level creations, room activation order and every seed field of every logged line equal. [C] for that scope; it says nothing about other acts, other inputs, sound-heavy play (NPC speech, combat sounds) or longer sessions. (4) **The control is weaker than the finding hoped**: the client seed at one sampled frame differs between A and B, but it also differs between A1 and A2, so the difference can't be assigned to sound. The sound-dependent client draws stay `[I]`.
- **Not shown:** that the sound path drew on the client seed (the one sample moves between two identical `-ns` runs, and the client seed's initial value was not read); anything after the `--after 60` window.
