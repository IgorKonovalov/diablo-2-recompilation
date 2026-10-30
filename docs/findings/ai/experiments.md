# Experiments — monsters/ai

## run:2026-10-27-ai-emu

- **Question:** (plan 0052 Phase 1, batch P1.1) Do `MonAiEntryGet`, `AiDistToPoint`, `MonAiWanderRing`,
  `MonAiWalkToUnitType56` and `MonAiStepAway` map their declared inputs to their return or to the arguments and seed at
  their first observed boundary as [ai/0001](0001-machinery.md) §§ 3, 6, 7 say?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project copy
  `workspace/ghidra-r52` (symbols replayed from `re/symbols.csv`), heap 3 GB, under `systemd-run --user --scope -p
  MemoryMax=4G`. No wine, no slot. Models and case writers `tools/ai_emu.py` (`b31f8ec2…`), every draw from
  `random.Random("r52-<family>")`. Files in `workspace/logs/r52/emu/`, `manifest.sha256` (`33e3d6dd…`, 16 lines,
  `check.txt` `feea3103…`); `sha256sum -c manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r52/emu
  python3 -I tools/ai_emu.py cases
  for f in entry dist ring typedraw flee; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r52 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/ai_emu.py check > $D/check.txt
  python3 -I tools/ai_emu.py manifest --write
  ```
  Each case writes only the unit, path, monster data and MonStats fields its function reads; the memory specs observe
  `0x005DEB60` and/or `0x005DE190` and guard the allocator and fatal entries.
- **Observed** (`check.txt`):
  ```
  AI52 entry cases=554 match=554 bad=0 stopped=0 traced=0 neg_separating=143 neg_passed=0
  AI52 dist cases=240 match=240 bad=0 stopped=0 traced=0 neg_separating=240 neg_passed=0
  AI52 ring cases=200 match=200 bad=0 stopped=0 traced=0 neg_separating=177 neg_passed=0 boundary_cases=200 site_control_passed=0
  AI52 typedraw cases=120 match=120 bad=0 stopped=0 traced=0 neg_separating=120 neg_passed=0 boundary_cases=120 site_control_passed=0
  AI52 flee cases=200 match=200 bad=0 stopped=0 traced=0 neg_separating=69 neg_passed=0 boundary_cases=192 site_control_passed=0
  AI52 result=ok
  ```
- **Conclusion:** the five maps are `[C]` in ai/0001 §§ 3, 6, 7 and 12, each up to its boundary; not the callees after
  it, not what the game stores at those offsets. No symbol raise (ADR-0015 scope, review-fixes rule 14). (run:2026-10-27-ai-emu)

## run:2026-10-30-ai-cat-emu-1

- **Question:** (plan 0052 Phase 1, catalogue batch 1) Do the think functions of rows 2, 3, 4, 5, 7, 9, 12, 14, 16 and
  142 map their declared inputs to the first callee they reach, its call site, its arguments and the unit seed as
  [ai/0002](0002-pool-a.md) § 2 reads them?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project
  copy `workspace/ghidra-r52b` (symbols replayed from a scratch copy of `re/symbols.csv` with reading signatures,
  `workspace/logs/r52b/b1-sym-scratch.csv`; emulation does not use them), heap 3 GB, under `systemd-run --user --scope
  -p MemoryMax=4G`. No wine, no slot. Models and case writer `tools/ai_cat_emu.py` (`91dc3928…`), every draw from
  `random.Random("r52b-<family>")`. Files in `workspace/logs/r52b/emu/`, `manifest.sha256` (`3dbe9d13…`, 31 lines,
  `check.txt` `a3dca9e0…`); `sha256sum -c manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r52b/emu
  python3 -I tools/ai_cat_emu.py cases
  for f in brute skeleton zombie bighead bloodhawk wraith goatman quillrat viper viperex; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r52b GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/ai_cat_emu.py check > $D/check.txt
  python3 -I tools/ai_cat_emu.py manifest --write
  ```
  Each case writes the game's difficulty and frame, the unit, its monster data and AI control, the `AiCtx`, the
  MonStats `aip` block and `Skill1`/`Sk1mode` (and, for the vipers, the target with a path); the memory spec observes
  23 callees (every AI helper the ten functions call, the life, room and level readers, `STATE_Set`,
  `MonSkillTargetOk`, `GameFindUnit`, the parameter pop) and guards the allocator and fatal entries.
- **Observed** (`check.txt`, first line of each family):
  ```
  AI52B brute cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=29 le_passed=0 d0_separating=37 d0_passed=0 site_control_passed=0 boundaries=5
  AI52B skeleton cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=31 le_passed=0 d0_separating=128 d0_passed=0 site_control_passed=0 boundaries=4
  AI52B zombie cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=26 le_passed=0 d0_separating=50 d0_passed=0 site_control_passed=0 boundaries=4
  AI52B bighead cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 site_control_passed=0 boundaries=2
  AI52B bloodhawk cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=34 le_passed=0 d0_separating=106 d0_passed=0 site_control_passed=0 boundaries=6
  AI52B wraith cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=38 le_passed=0 d0_separating=119 d0_passed=0 site_control_passed=0 boundaries=3
  AI52B goatman cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=40 le_passed=0 d0_separating=138 d0_passed=0 site_control_passed=0 boundaries=3
  AI52B quillrat cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=5 le_passed=0 d0_separating=44 d0_passed=0 site_control_passed=0 boundaries=6
  AI52B viper cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=18 le_passed=0 d0_separating=87 d0_passed=0 site_control_passed=0 boundaries=7
  AI52B viperex cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=28 le_passed=0 d0_separating=114 d0_passed=0 site_control_passed=0 boundaries=8
  AI52B result=ok
  ```
  The `SITES` line under each family counts the cases per boundary and call site (48 site/boundary pairs over the ten
  functions). **Development run** (`emu/dev/`, the same writer with `--no-tune`: the viper and quill-rat inputs
  without the tuning that reaches their later branches more often): 2 400 cases, 2 400 matching, 0 stopped, 0 traced,
  every control failing every case it separates (`dev/check.txt` `58ed6a77…`, `dev/manifest.sha256` `4135ceb2…`, 31
  lines, passes from `emu/dev/`). It was first run before the tuning was added and its first outputs were overwritten
  by the kept run's; the `dev/` files are its rerun with the committed tool. The kept run's case files and `check.txt`
  regenerate identically with the committed tool (`cases`, then `check`, compared with `cmp` and the manifest).
- **Conclusion:** the ten maps are `[C]` in ai/0002 §§ 2–3, each up to its first boundary; `bighead`'s only as the map
  of its two draw-free tests. Not the callees, nothing after them. No symbol raise (ADR-0015 scope, review-fixes rule
  14). (run:2026-10-30-ai-cat-emu-1)

## run:2026-10-30-ai-cat-emu-2

- **Question:** (plan 0052 Phase 1, catalogue batch 2) Do the think functions of rows 17, 18, 19, 20, 21, 22, 24 and
  27, row 30's record test and row 29's `alt` map their declared inputs to the first callee they reach, its call site,
  its arguments, the unit seed, `AiCtl+0x14/+0x18` and (at a unit search) the search block as
  [ai/0003](0003-pool-b.md) § 2 reads them?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project
  copy `workspace/ghidra-r52c` (symbols replayed from a scratch copy of `re/symbols.csv` with reading signatures,
  `workspace/logs/r52c/b2-sym-scratch.csv`; emulation does not use them), heap 3 GB, under `systemd-run --user --scope
  -p MemoryMax=4G`. No wine, no slot. Models and case writer `tools/ai_cat_emu2.py` (`514609f3…`), every draw from
  `random.Random("r52c-<family>")`. Files in `workspace/logs/r52c/emu/`, `manifest.sha256` (`622a2256…`, 31 lines,
  `check.txt` `5ee4033c…`); `sha256sum -c manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r52c/emu
  python3 -I tools/ai_cat_emu2.py cases
  for f in leaper panther swarm scarab mummy gmummy mosquito thornhulk fetish batalt; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r52c GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/ai_cat_emu2.py check > $D/check.txt
  python3 -I tools/ai_cat_emu2.py manifest --write
  ```
  Each case writes the game's difficulty and frame, the unit (type, class, mode, monster data, seed), its monster data
  and AI control (state, `+0x14/+0x18/+0x1C`, the parameter-list head, the owner link), one parameter record, the
  `AiCtx`, the MonStats `aip` block, `Skill1..3` and `Sk1mode`, and the DataTables pointer with its MonStats count; the
  memory spec observes 33 callees and guards the allocator and fatal entries.
- **Observed** (`check.txt`, first line of each family):
  ```
  AI52C leaper cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=17 le_passed=0 d0_separating=45 d0_passed=0 site_control_passed=0 boundaries=6
  AI52C panther cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=26 le_passed=0 d0_separating=99 d0_passed=0 site_control_passed=0 boundaries=4
  AI52C swarm cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=34 le_passed=0 d0_separating=120 d0_passed=0 site_control_passed=0 boundaries=3
  AI52C scarab cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=28 le_passed=0 d0_separating=71 d0_passed=0 site_control_passed=0 boundaries=9
  AI52C mummy cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=25 le_passed=0 d0_separating=101 d0_passed=0 site_control_passed=0 boundaries=7
  AI52C gmummy cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=20 le_passed=0 d0_separating=106 d0_passed=0 site_control_passed=0 boundaries=4
  AI52C mosquito cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=16 le_passed=0 d0_separating=26 d0_passed=0 site_control_passed=0 boundaries=7
  AI52C thornhulk cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=28 le_passed=0 d0_separating=42 d0_passed=0 site_control_passed=0 boundaries=7
  AI52C fetish cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 site_control_passed=0 boundaries=4
  AI52C batalt cases=240 match=240 bad=0 stopped=0 traced=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 site_control_passed=0 boundaries=3
  AI52C result=ok
  ```
  The `SITES` line under each family counts the cases per boundary and call site (54 site/boundary pairs over the ten
  families). **Development run** (`emu/dev-1/`, the writer before the thorn hulk and scarab tuning, its copy
  `dev-1/ai_cat_emu2.py.rev` `89a00be0…`; the models are the same): 2 400 cases, 2 400 matching, 0 stopped, 0 traced,
  every control failing every case it separates (`dev-1/check.txt` `db6894e9…`, regenerated identically by
  `python3 -I dev-1/ai_cat_emu2.py.rev check --dir dev-1`; `dev-1/manifest.sha256` `666c3d60…`, 32 lines, passes from
  `emu/dev-1/`). It was run first, into its own directory; the kept run's files are separate. The kept run's case files
  and `check.txt` regenerate identically with the committed tool (`cases` into a scratch directory and `check`,
  compared with `cmp`).
- **Conclusion:** the eight maps are `[C]` in ai/0003 §§ 2–3, each up to its first boundary; `fetish`'s and `batalt`'s
  only as the maps of their draw-free tests. Not the callees, nothing after them. No symbol raise (ADR-0015 scope,
  review-fixes rule 14). (run:2026-10-30-ai-cat-emu-2)

## run:2026-10-30-ai-cat-emu-3

- **Question:** (plan 0052 Phase 1, catalogue batch 3) Do the think functions of rows 33, 36, 37, 38, 39, 40, 43, 45,
  46, 47, 52, 57 and 63 and row 52's `alt` map their declared inputs to the first callee they reach, its call site, its
  arguments, the unit seed, `AiCtl+0x14/+0x18/+0x1C`, `Unit+0xC4` and (at a `FindHostile` call) the frame word its
  pointer argument addresses as [ai/0004](0004-pool-c.md) § 2 reads them?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project
  copy `workspace/ghidra-r52d` (symbols replayed from `re/symbols.csv`, then from a scratch copy with reading
  signatures, `workspace/logs/r52d/b3-sym-scratch.csv`; emulation does not use them), heap 3 GB
  (`GHIDRA_HEADLESS_MAXMEM=3G`, one headless run at a time, not under a `systemd-run` scope). No wine, no slot. Models
  and case writer `tools/ai_cat_emu3.py` (`af06ff4a…`), every draw from `random.Random("r52d-<family>")`. Files in
  `workspace/logs/r52d/emu/`, `manifest.sha256` (`6592cf02…`, 57 lines, `check.txt` `6eb97eb9…`); `sha256sum -c
  manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r52d/emu
  python3 -I tools/ai_cat_emu3.py cases
  for f in meteor lancer skelbow larva pinhead egg nest sarco beast scimitar frog frogalt thead garg; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r52d GHIDRA_HEADLESS_MAXMEM=3G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/ai_cat_emu3.py check > $D/check.txt
  python3 -I tools/ai_cat_emu3.py manifest --write
  ```
  Each case writes the game's difficulty and frame, the unit (type 1, class, mode, monster data, seed, path, `+0xC4`),
  the path's position and room, its monster data and AI control (state, `+0x14/+0x18/+0x1C`, no parameter record), the
  `AiCtx` with its MonStats and MonStats2 records, the MonStats `aip` block, `Skill1..3` and `Sk1..3mode`, the
  MonStats2 `+0x0E` byte, and the DataTables pointer with its MonStats count; the memory spec observes 33 callees and
  guards the allocator and fatal entries (6).
- **Observed** (`check.txt`, first line of each family):
  ```
  AI52D meteor cases=240 match=240 bad=0 stopped=0 traced=0 drew=157 le_separating=16 le_passed=0 d0_separating=151 d0_passed=0 site_control_passed=0 boundaries=2
  AI52D lancer cases=240 match=240 bad=0 stopped=0 traced=0 drew=160 le_separating=25 le_passed=0 d0_separating=106 d0_passed=0 site_control_passed=0 boundaries=8
  AI52D skelbow cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 site_control_passed=0 boundaries=2
  AI52D larva cases=240 match=240 bad=0 stopped=0 traced=0 drew=153 le_separating=20 le_passed=0 d0_separating=131 d0_passed=0 site_control_passed=0 boundaries=4
  AI52D pinhead cases=240 match=240 bad=0 stopped=0 traced=0 drew=237 le_separating=23 le_passed=0 d0_separating=116 d0_passed=0 site_control_passed=0 boundaries=6
  AI52D egg cases=240 match=240 bad=0 stopped=0 traced=0 drew=110 le_separating=11 le_passed=0 d0_separating=98 d0_passed=0 site_control_passed=0 boundaries=3
  AI52D nest cases=240 match=240 bad=0 stopped=0 traced=0 drew=28 le_separating=0 le_passed=0 d0_separating=48 d0_passed=0 site_control_passed=0 boundaries=4
  AI52D sarco cases=240 match=240 bad=0 stopped=0 traced=0 drew=79 le_separating=0 le_passed=0 d0_separating=84 d0_passed=0 site_control_passed=0 boundaries=4
  AI52D beast cases=240 match=240 bad=0 stopped=0 traced=0 drew=49 le_separating=5 le_passed=0 d0_separating=46 d0_passed=0 site_control_passed=0 boundaries=6
  AI52D scimitar cases=240 match=240 bad=0 stopped=0 traced=0 drew=240 le_separating=35 le_passed=0 d0_separating=120 d0_passed=0 site_control_passed=0 boundaries=5
  AI52D frog cases=240 match=240 bad=0 stopped=0 traced=0 drew=95 le_separating=18 le_passed=0 d0_separating=54 d0_passed=0 site_control_passed=0 boundaries=14
  AI52D frogalt cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 site_control_passed=0 boundaries=2
  AI52D thead cases=240 match=240 bad=0 stopped=0 traced=0 drew=18 le_separating=3 le_passed=0 d0_separating=27 d0_passed=0 site_control_passed=0 boundaries=5
  AI52D garg cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 site_control_passed=0 boundaries=2
  AI52D total cases=3360 match=3360
  AI52D result=ok
  ```
  The `SITES` line under each family counts the cases per boundary and call site (67 site/boundary pairs over the
  fourteen families); `drew` counts the cases whose seed moved before the boundary. **Development runs** (rule 6):
  `emu/dev-1/` (the writer before the nest, sarcophagus, elemental beast and tentacle head tuning, its copy
  `dev-1/ai_cat_emu3.py.rev` `78395f4d…`) and `emu/dev-2/` (the writer before the tentacle head's distance tuning,
  `dev-2/ai_cat_emu3.py.rev` `96d5ceb2…`); the models are the same in all three. Each: 3 360 cases, 3 360 matching, 0
  stopped, 0 traced, every control failing every case it separates (`dev-1/check.txt` `b246ec3a…`, `dev-2/check.txt`
  `3bfd118b…`, each regenerated identically by `python3 -I dev-K/ai_cat_emu3.py.rev check --dir dev-K`;
  `dev-1/manifest.sha256` `2522af4b…` and `dev-2/manifest.sha256` `a0d34831…`, 58 lines each, each passing from its
  directory). Each ran into its own directory first (dev-2's files were moved there from `emu/` before the kept run);
  the kept run's files are separate. The kept run's case and memory files and `check.txt` regenerate identically with
  the committed tool (`cases` into a scratch directory, `check` on the kept outputs there, compared with `cmp`).
- **Conclusion:** the fourteen maps are `[C]` in ai/0004 §§ 2–3, each up to its first boundary; `skelbow`'s,
  `frogalt`'s and `garg`'s only as the maps of their draw-free tests. Not the callees, nothing after them. No symbol
  raise (ADR-0015 scope, review-fixes rule 14). For `nest` and `sarco`, where `le` separates nothing, the lane check
  added two controls on these outputs (compare flipped, range moved by one; ai/0004 § 3), both failing every case
  they separate. (run:2026-10-30-ai-cat-emu-3)
