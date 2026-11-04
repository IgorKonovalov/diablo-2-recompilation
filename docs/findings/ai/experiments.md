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

## run:2026-10-30-ai-cat-emu-4

- **Question:** (plan 0052 Phase 1, catalogue batch 4) Do the think functions of rows 66, 69, 71, 72, 75, 76, 77, 78,
  79, 80, 87 and 92 and row 65's skill-sign test map their declared inputs to the first callee they reach (or row 66's
  return), its call site, its arguments, the unit seed, `AiCtl+0x14/+0x18/+0x1C`, `Unit+0xC4`, the trap region's
  `+0x2D4` and the frame words a pointer argument addresses as [ai/0005](0005-pool-d.md) § 2 reads them; and do rows
  64, 65's `alt`, 68, 70, 73 and 74 reach their entry call with the arguments § 2 gives?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project
  copy `workspace/ghidra-r52e` (symbols replayed from `re/symbols.csv`, then from a scratch copy with reading
  signatures, `workspace/logs/r52e/b4-sym-scratch.csv`; emulation does not use them), heap 3 GB
  (`GHIDRA_HEADLESS_MAXMEM=3G`), each headless run inside `systemd-run --user --scope -p MemoryMax=4G`, one at a time.
  No wine, no slot. Models and case writer `tools/ai_cat_emu4.py` (`03bf4a7c…`), every draw from
  `random.Random("r52e-<family>")`. Files in `workspace/logs/r52e/emu/`, `manifest.sha256` (`40fa31fc…`, 77 lines,
  `check.txt` `2ad55bf8…`); `sha256sum -c manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r52e/emu
  python3 -I tools/ai_cat_emu4.py cases
  for f in skmage fetish fetishalt queen vmother vdog fmage regurg dknight aknight oknight quill ehole tmissile \
           trarrow tlarrow tpoison tmelee tnova; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r52e GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/ai_cat_emu4.py check > $D/check.txt
  python3 -I tools/ai_cat_emu4.py manifest --write
  ```
  Each case writes the game's difficulty and frame and one region pointer at `+0xF0 + 4·level`, the unit (type 1,
  class, mode, monster data, seed, path, `+0xC4`), the path's position and room, the room's DRLG room, its level and
  the level's id, the region's `+0x2D4`, the target (type, guid, path and its position), the monster data and AI
  control (state, `+0x14/+0x18/+0x1C`, no parameter record), the `AiCtx`, the MonStats `aip` block, `Skill1..3` and
  `Sk1..3mode`, and the DataTables pointer with its MonStats count; the memory spec observes 45 callees and guards the
  allocator and fatal entries (6).
- **Observed** (`check.txt`, first line of each family):
  ```
  AI52E skmage cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=1
  AI52E fetish cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=2
  AI52E fetishalt cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=1
  AI52E queen cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=64 d0_passed=0 cmp_separating=29 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=4
  AI52E vmother cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=1
  AI52E vdog cases=240 match=240 bad=0 stopped=0 traced=0 drew=200 le_separating=34 le_passed=0 d0_separating=69 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=5
  AI52E fmage cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=1
  AI52E regurg cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=77 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=6
  AI52E dknight cases=240 match=240 bad=0 stopped=0 traced=0 drew=240 le_separating=27 le_passed=0 d0_separating=136 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=4
  AI52E aknight cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=1
  AI52E oknight cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=1
  AI52E quill cases=240 match=240 bad=0 stopped=0 traced=0 drew=137 le_separating=17 le_passed=0 d0_separating=75 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=5
  AI52E ehole cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=75 d0_passed=0 cmp_separating=67 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=5
  AI52E tmissile cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=64 d0_passed=0 cmp_separating=52 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=3
  AI52E trarrow cases=240 match=240 bad=0 stopped=0 traced=0 drew=21 le_separating=0 le_passed=0 d0_separating=71 d0_passed=0 cmp_separating=53 cmp_passed=0 r4_separating=14 r4_passed=0 site_control_passed=0 boundaries=4
  AI52E tlarrow cases=240 match=240 bad=0 stopped=0 traced=0 drew=24 le_separating=0 le_passed=0 d0_separating=78 d0_passed=0 cmp_separating=62 cmp_passed=0 r4_separating=20 r4_passed=0 site_control_passed=0 boundaries=4
  AI52E tpoison cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=62 d0_passed=0 cmp_separating=56 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=3
  AI52E tmelee cases=240 match=240 bad=0 stopped=0 traced=0 drew=117 le_separating=13 le_passed=0 d0_separating=71 d0_passed=0 cmp_separating=0 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=3
  AI52E tnova cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=62 d0_passed=0 cmp_separating=44 cmp_passed=0 r4_separating=0 r4_passed=0 site_control_passed=0 boundaries=3
  AI52E total cases=4560 match=4560
  AI52E result=ok
  ```
  The `SITES` line under each family counts the cases per boundary and call site (56 site/boundary pairs and row 66's
  return over the nineteen families); the `EDGES` line the cases that meet each non-draw compare and each draw at
  equality; `drew` the cases whose seed moved before the boundary. **Development run** (rule 6): `emu/dev-1/` (the
  writer before the trap arrows' tuning, its copy `dev-1/ai_cat_emu4.py.rev` `d5364a49…`, which prints no `EDGES`
  line; the models are the same): 4 560 cases, 4 560 matching, 0 stopped, 0 traced, every control failing every case
  it separates (`dev-1/check.txt` `3d35fead…`, regenerated identically by
  `python3 -I dev-1/ai_cat_emu4.py.rev check --dir dev-1`; `dev-1/manifest.sha256` `c15f3848…`, 78 lines, passing
  from its directory). It ran into its own directory; the kept run's files are separate. The kept run's case and
  memory files and `check.txt` regenerate identically with the committed tool (`cases` into a scratch directory,
  `check` on the kept outputs there, compared with `cmp`).
- **Conclusion:** the thirteen maps are `[C]` in ai/0005 §§ 2–3, each up to its first boundary (row 65 its skill-sign
  test only); the six entry calls `[C]` as calls. Not the callees, nothing after them. No symbol raise (ADR-0015
  scope, review-fixes rule 14). (run:2026-10-30-ai-cat-emu-4)

## run:2026-10-30-ai-cat-emu-5

- **Question:** (plan 0052 Phase 1, catalogue batch 5) Do the init and think functions of rows 84 (both), 86, 101/104
  (init), 102 (both), 107 (init), 110/111 (init), 106/143 (think) and 108 map their declared inputs to the first callee
  they reach (or the return), its call site, its arguments, the unit seed and `AiCtl+0x14/+0x18/+0x1C` as
  [ai/0006](0006-summons.md) § 2 reads them; and do the other followers (rows 67 and state row 7, 101, 103, 104, 105
  and its init, 106's and 143's inits, 107, 109–112) reach their entry call with the arguments and `AiCtl` stores § 2
  gives?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project
  copy `workspace/ghidra-r52f` (symbols replayed from a scratch copy of `re/symbols.csv` with reading signatures,
  `workspace/logs/r52f/b5-sym-scratch.csv`; emulation does not use them), heap 3 GB (`GHIDRA_HEADLESS_MAXMEM=3G`), each
  batch of headless runs inside `systemd-run --user --scope -p MemoryMax=4G`, one Ghidra at a time. No wine, no slot.
  Models and case writer `tools/ai_cat_emu5.py` (`656b7c70…`), every draw from `random.Random("r52f-<family>")`. Files
  in `workspace/logs/r52f/emu/`, `manifest.sha256` (`1a5726ad…`, 93 lines, `check.txt` `ab9cec17…`); `sha256sum -c
  manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r52f/emu
  python3 -I tools/ai_cat_emu5.py cases
  for f in bwinit bwall necropet hydra sentinit asentry bladeinit blade inviso dsentry swinit swarrior sminit \
           sm2init smaster vinit vines cycle ravinit raven dwolf bear totem; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r52f GHIDRA_HEADLESS_MAXMEM=3G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done                                   # in two systemd-run --user --scope -p MemoryMax=4G invocations (12 + 11)
  python3 -I tools/ai_cat_emu5.py check > $D/check.txt
  python3 -I tools/ai_cat_emu5.py manifest --write
  ```
  Each case writes the game's difficulty and frame, the unit (type 1, class, mode, monster data, seed, path, skill
  list head `+0xA8`, `+0xC4`), the monster data and AI control (state, `+0x14/+0x18/+0x1C`, no parameter record), the
  `AiCtx`, the MonStats `aip` block, `Skill1..3` and `Sk1..3mode`, and the DataTables pointer with the Skills count,
  the Skills records pointer (for one case in eight of `bwinit` and `blade` a pointer that puts the case's record at
  address 0) and that record's `Param2`; the memory spec observes 44 callees and guards the allocator and fatal
  entries (6).
- **Observed** (`check.txt`, first line of each family):
  ```
  AI52F bwinit cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=51 cmp_passed=0 u16_separating=94 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F bwall cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=44 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=2
  AI52F necropet cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F hydra cases=240 match=240 bad=0 stopped=0 traced=0 drew=121 le_separating=21 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=58 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=3
  AI52F sentinit cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F asentry cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F bladeinit cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F blade cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=12 cmp_passed=0 u16_separating=46 u16_passed=0 site_control_passed=0 boundaries=2
  AI52F inviso cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F dsentry cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F swinit cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F swarrior cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F sminit cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F sm2init cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F smaster cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=2
  AI52F vinit cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F vines cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F cycle cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F ravinit cases=240 match=240 bad=0 stopped=0 traced=0 drew=240 le_separating=0 le_passed=0 d0_separating=153 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F raven cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F dwolf cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=2
  AI52F bear cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F totem cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52F total cases=5520 match=5520
  AI52F result=ok
  ```
  The `SITES` line under each family counts the cases per boundary and call site (24 site/boundary pairs and the five
  inits' return over the 23 families); the `EDGES` line the cases that meet each non-draw compare and each draw at
  equality; `drew` the cases whose seed moved before the boundary. **Development run** (rule 6): `emu/dev-1/` (the
  writer before two tunings, a Skills count of 0x10000 for `bwinit` and `blade` and `hydra` seeds with a first draw of
  59–61; its copy `dev-1/ai_cat_emu5.py.rev` `37add132…`; the models are the same): 5 520 cases, 5 520 matching, 0
  stopped, 0 traced, every control failing every case it separates (`dev-1/check.txt` `a538919f…`, regenerated
  identically by `python3 -I dev-1/ai_cat_emu5.py.rev check --dir dev-1`; `dev-1/manifest.sha256` `5eca94e8…`, 94
  lines, passing from its directory). It ran into its own directory; the kept run's files are separate. The kept
  run's case and memory files and `check.txt` regenerate identically with the committed tool (`cases` into a scratch
  directory, `check` on the kept outputs there, compared with `cmp`).
- **Conclusion:** the full maps are `[C]` in ai/0006 §§ 2, 4, each up to its first boundary or return; the entry
  calls `[C]` as calls, with the `AiCtl` stores before them. Not the callees, nothing after them. No symbol raise
  (ADR-0015 scope, review-fixes rule 14). (run:2026-10-30-ai-cat-emu-5)

## run:2026-11-03-ai-cat-emu-8

- **Question:** (plan 0052 Phase 1, catalogue batch 8, pool-E) Do the think functions of rows 82, 83, 85, 93, 94, 96,
  97, 98 and 114 map their declared inputs to the first callee they reach, its call site, its arguments, the unit
  seed, `AiCtl+0x14/+0x18/+0x1C` and `Unit+0xC4` as [ai/0009](0009-batch8.md) § 2 reads them; does row 89 reach
  `SkillFindByOwner` or `HasState` on its skill-sign test; and do rows 95, 113 and 115 reach their entry call with
  the arguments § 2 gives?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project
  copy `workspace/ghidra-r52h` (symbols replayed from a scratch copy of `re/symbols.csv` with reading signatures,
  `workspace/logs/r52h/b8-sym-scratch.csv`; emulation does not use them), heap 3 GB (`GHIDRA_HEADLESS_MAXMEM=3G`), the
  thirteen headless runs inside one `systemd-run --user --scope -p MemoryMax=4G`, one Ghidra at a time. No wine, no
  slot. Models and case writer `tools/ai_cat_emu8.py` (`863f38a5…`), every draw from `random.Random("r52h-<family>")`.
  Files in `workspace/logs/r52h/emu/`, `manifest.sha256` (`72d4bc65…`, 53 lines, `check.txt` `1bf38380…`); `sha256sum -c
  manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r52h/emu
  python3 -I tools/ai_cat_emu8.py cases
  for f in spawner nest priest mega arcane turret javelin blowgun spirit smith stower horde sbeast; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r52h GHIDRA_HEADLESS_MAXMEM=3G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done                                   # inside one systemd-run --user --scope -p MemoryMax=4G invocation
  python3 -I tools/ai_cat_emu8.py check > $D/check.txt
  python3 -I tools/ai_cat_emu8.py manifest --write
  ```
  Each case writes the game's difficulty and frame, the unit (type 1, class, mode, monster data, seed, path, `+0xC4`)
  and its path (x, y, room), the target (type, guid, path or none, the path's x and y and the static words
  `+0x0C/+0x10`), the monster data and AI control (state, `+0x14/+0x18/+0x1C`, `+0x20` 0 or a parameter record of
  kind 0, 1, 2 or 14 for row 96), the `AiCtx`, the MonStats `+0x03E` word, `aip` block, `Skill1..3` and
  `Sk1..3mode`, and the DataTables pointer with the MonStats count (0x2E0, 0x60, 0x61, 0x14E or 0x14F); the memory
  spec observes 42 callees and guards the allocator and fatal entries (6).
- **Observed** (`check.txt`, first line of each family):
  ```
  AI52H spawner cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=103 d0_passed=0 cmp_separating=80 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=3
  AI52H nest cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=59 d0_passed=0 cmp_separating=51 cmp_passed=0 u16_separating=27 u16_passed=0 site_control_passed=0 boundaries=3
  AI52H priest cases=240 match=240 bad=0 stopped=0 traced=0 accounted=8 drew=233 le_separating=18 le_passed=0 d0_separating=83 d0_passed=0 cmp_separating=27 cmp_passed=0 u16_separating=59 u16_passed=0 site_control_passed=0 boundaries=14
  AI52H mega cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=99 u16_passed=0 site_control_passed=0 boundaries=2
  AI52H arcane cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=42 d0_passed=0 cmp_separating=40 cmp_passed=0 u16_separating=39 u16_passed=0 site_control_passed=0 boundaries=3
  AI52H turret cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=40 d0_passed=0 cmp_separating=58 cmp_passed=0 u16_separating=71 u16_passed=0 site_control_passed=0 boundaries=4
  AI52H javelin cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52H blowgun cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=73 le_separating=6 le_passed=0 d0_separating=33 d0_passed=0 cmp_separating=11 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=5
  AI52H spirit cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=3
  AI52H smith cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=2
  AI52H stower cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52H horde cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=168 le_separating=20 le_passed=0 d0_separating=90 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=52 u16_passed=0 site_control_passed=0 boundaries=6
  AI52H sbeast cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 site_control_passed=0 boundaries=1
  AI52H total cases=3120 match=3120
  AI52H result=ok
  ```
  The `SITES` line under each family counts the cases per boundary and call site (48 site/boundary pairs over the 13
  families); the `EDGES` line the cases that meet each non-draw compare and each draw at equality; `drew` the cases
  whose seed moved before the boundary; `accounted` the traced reads the checker accounts as row 85's corner table
  (`0x006E337C + 8k` at 0x005E0656 and `0x006E3380 + 8k` at 0x005E0665, all four `k`; it fails a family when one
  is missing). **Development run** (rule 6): `emu/dev-1/` (the writer before row 85's corner tuning and a checker
  without the corner accounting; its copy `dev-1/ai_cat_emu8.py.rev` `0592d4f9…`; the models are the same): 3 120 cases,
  3 120 matching, 0 stopped, every control failing every case it separates, `result=FAIL` for 6 traced reads (three
  corner rows; `dev-1/check.txt` `25458979…`, regenerated identically by `python3 -I dev-1/ai_cat_emu8.py.rev check --dir dev-1`;
  `dev-1/manifest.sha256` `24460b9e…`, 54 lines, passing from its directory). It ran into its own directory; the
  kept run's files are separate. The kept run's case and memory files and `check.txt` regenerate identically with the
  committed tool (`cases` into a scratch directory, `check` on the kept outputs there, compared with `cmp`).
- **Conclusion:** the maps are `[C]` in ai/0009 §§ 2, 3, each up to its first boundary; the entry calls `[C]` as
  calls. Not the callees, nothing after them. No symbol raise (ADR-0015 scope, review-fixes rule 14).
  (run:2026-11-03-ai-cat-emu-8)
## run:2026-10-30-ai-cat-emu-6

- **Question:** (plan 0052 Phase 1, catalogue batches 6 and 7) Do the functions of row 61 (think and `alt`), state rows
  5 and 6, `MERCAI_PickSkill`, the hireling's fight and follow steps, and rows 34, 44, 50 (and its target pick), 53,
  55, 59 (init and think), 90, 144 and 146 map their declared inputs to the first callee they reach (or the return),
  its call site, its arguments, the unit seed and `AiCtl+0x14/+0x18/+0x1C` (and, for the pick, its search block) as
  [ai/0007](0007-hirelings.md) § 2 and [ai/0008](0008-bosses-a.md) § 2 read them?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project
  copy `workspace/ghidra-r52g` (emulation does not use the scratch signatures), heap 3 GB (`GHIDRA_HEADLESS_MAXMEM=3G`),
  each headless run inside its own `systemd-run --user --scope -p MemoryMax=4G`, one Ghidra at a time. No wine, no
  slot. Models and case writer `tools/ai_cat_emu6.py` (`866f330d…`), every draw from `random.Random("r52g-<family>")`.
  Files in `workspace/logs/r52g/emu/`, `manifest.sha256` (`888adf58…`, 73 lines, `check.txt` `f57b484e…`);
  `sha256sum -c manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r52g/emu
  python3 -I tools/ai_cat_emu6.py cases --dir $D
  for f in hire hirealt st5 st6 pick fight follow andariel duriel mephisto mpick summoner izual brinit braven \
           griswold uizual umeph; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r52g GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/ai_cat_emu6.py check --dir $D > $D/check.txt
  python3 -I tools/ai_cat_emu6.py manifest --dir $D --write
  ```
  Each case writes the game's difficulty and frame, the unit (type 1, class, mode, monster data, seed, path, `+0xC4`)
  and its path's point and room, the target (type, guid, dynamic and static path words), an owner unit for the
  hireling helpers, the monster data and AI control (state, `+0x14/+0x18/+0x1C/+0x20`), the `AiCtx`, the MonStats
  `aidel`, `aip` block, `Skill1..8` and `Sk1..8mode`, and the DataTables pointer with the MonStats and Skills counts and
  records and one Skills record's `aurastate`; the memory spec observes 78 callees and guards the allocator and fatal
  entries (6).
- **Observed** (`check.txt`, first line of each family):
  ```
  AI52G hire cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=1
  AI52G hirealt cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=1
  AI52G st5 cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=2
  AI52G st6 cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=2
  AI52G pick cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=25 cmp_passed=0 site_control_passed=0 boundaries=2
  AI52G fight cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=31 cmp_passed=0 site_control_passed=0 boundaries=2
  AI52G follow cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=1
  AI52G andariel cases=240 match=240 bad=0 stopped=0 traced=0 drew=204 le_separating=24 le_passed=0 d0_separating=53 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=6
  AI52G duriel cases=240 match=240 bad=0 stopped=0 traced=0 drew=149 le_separating=27 le_passed=0 d0_separating=44 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=7
  AI52G mephisto cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=1
  AI52G mpick cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=1
  AI52G summoner cases=240 match=240 bad=0 stopped=0 traced=0 drew=93 le_separating=8 le_passed=0 d0_separating=16 d0_passed=0 cmp_separating=36 cmp_passed=0 site_control_passed=0 boundaries=3
  AI52G izual cases=240 match=240 bad=0 stopped=0 traced=0 drew=78 le_separating=10 le_passed=0 d0_separating=40 d0_passed=0 cmp_separating=51 cmp_passed=0 site_control_passed=0 boundaries=8
  AI52G brinit cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=1
  AI52G braven cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=1
  AI52G griswold cases=240 match=240 bad=0 stopped=0 traced=0 drew=240 le_separating=11 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=3
  AI52G uizual cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=30 cmp_passed=0 site_control_passed=0 boundaries=2
  AI52G umeph cases=240 match=240 bad=0 stopped=0 traced=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 site_control_passed=0 boundaries=1
  AI52G total cases=4320 match=4320
  AI52G result=ok
  ```
  The `SITES` line under each family counts the cases per boundary and call site (42 site/boundary pairs and three
  families' return over the 18 families); the `EDGES` line the cases that meet each non-draw compare and each draw at
  equality; `drew` the cases whose seed moved before the boundary. **Development run** (rule 6): `emu/dev-1/` (the
  same writer and models; its copy `dev-1/ai_cat_emu6.py.rev` has the same bytes as the kept run's tool,
  `866f330d…`): 4 320 cases, 4 320 matching, 0 stopped, 0 traced, every control failing every case it separates
  (`dev-1/check.txt` `f57b484e…`, the same bytes as the kept one; `dev-1/manifest.sha256` `764776ff…`, 74 lines, passing
  from its directory). The kept run ran into `emu/`, not over `dev-1/`; its case and memory files regenerate
  identically with the committed tool (`cases` into a scratch directory, compared with `cmp`), and its 18 `.out` files
  equal dev-1's byte for byte.
- **Conclusion:** the full maps are `[C]` in ai/0007 § 4 and ai/0008 § 4, each up to its first boundary or return; the
  entry calls `[C]` as calls. Not the callees, nothing after them. No symbol raise (ADR-0015 scope, review-fixes
  rule 14). (run:2026-10-30-ai-cat-emu-6)

## run:2026-11-03-ai-cat-emu-9

- **Question:** (plan 0052 Phase 1, catalogue batch 9, pool-F) Do the functions of rows 116–125, row 122's init and
  state row 16's init map their declared inputs to the first boundary they reach (or their return), its call site,
  its arguments, the unit seed, `AiCtl+0x14/+0x18/+0x1C` and `Unit+0xC4` as [ai/0010](0010-batch9.md) § 2 reads them,
  with the action helper 0x005DF850 run inside row 122; does row 124 reach `SKILLS_GetUnitSkill` or `HasState` on its
  skill-sign test; and does state row 16's think reach `HasState(U, 143)` with the arguments § 2.10 gives?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, unchanged), lane project
  copy `workspace/ghidra-r52i` (symbols replayed from a scratch copy, `workspace/logs/r52i/b9-sym-scratch.csv`;
  emulation does not use them), heap 3 GB (`GHIDRA_HEADLESS_MAXMEM=3G`), each of the thirteen headless runs inside its
  own `systemd-run --user --scope -p MemoryMax=4G`, one Ghidra at a time. No wine, no slot. Models and case writer
  `tools/ai_cat_emu9.py` (`70a14f85…`), every draw from `random.Random("r52i-<family>")`. Files in
  `workspace/logs/r52i/emu/`, `manifest.sha256` (`6fb58421…`, 53 lines, `check.txt` `8872c3de…`); `sha256sum -c
  manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r52i/emu
  python3 -I tools/ai_cat_emu9.py cases
  export GHIDRA_PROJ_DIR=workspace/ghidra-r52i GHIDRA_HEADLESS_MAXMEM=3G
  for f in minion suicide succubus witch overseer spawner imp16i imp16 impi imp catapult horror blood; do
    systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/ai_cat_emu9.py check > $D/check.txt
  python3 -I tools/ai_cat_emu9.py manifest --write
  ```
  Each case writes the game's difficulty, frame, an empty quest list and the one unit hash slot a lookup reads; the
  unit (type 1, class, mode, monster data, seed, path, game, owner and stored-unit type and guid, skill list,
  `+0xC4`, `+0xC8`) and its path; the target (type, guid, mode, path or none with its x, y and static words, stat list
  or none with one node, `+0xC6`, `+0xE4`); a second unit for the lookups; the monster data (`+0x28`, `+0x54`) and AI
  control (state, `+0x14/+0x18/+0x1C`, `+0x20` 0 or a parameter record of kind 0, 1, 2 or 14 for row 116); the
  `AiCtx`; the unit's MonStats record (`+0x03E`, the `aip` block, `Skill1..8`, `Sk1..8mode`) at the class's place
  under `DataTables+0xA78`, the `aip` blocks of the records 492–495, the skill nodes for state 16's init, and the
  DataTables pointer with the MonStats base and count; the memory spec observes 38 callees and guards the allocator
  and fatal entries (6).
- **Observed** (`check.txt`, first line of each family):
  ```
  AI52I minion cases=240 match=240 bad=0 stopped=0 traced=0 accounted=5 drew=85 le_separating=12 le_passed=0 d0_separating=44 d0_passed=0 cmp_separating=4 cmp_passed=0 u16_separating=0 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=7
  AI52I suicide cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=44 le_separating=6 le_passed=0 d0_separating=83 d0_passed=0 cmp_separating=21 cmp_passed=0 u16_separating=0 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=3
  AI52I succubus cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=218 le_separating=26 le_passed=0 d0_separating=125 d0_passed=0 cmp_separating=22 cmp_passed=0 u16_separating=69 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=9
  AI52I witch cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=223 le_separating=40 le_passed=0 d0_separating=135 d0_passed=0 cmp_separating=20 cmp_passed=0 u16_separating=64 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=13
  AI52I overseer cases=240 match=240 bad=0 stopped=0 traced=0 accounted=5 drew=132 le_separating=13 le_passed=0 d0_separating=31 d0_passed=0 cmp_separating=7 cmp_passed=0 u16_separating=0 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=5
  AI52I spawner cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=120 d0_passed=0 cmp_separating=107 cmp_passed=0 u16_separating=0 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=4
  AI52I imp16i cases=240 match=240 bad=0 stopped=0 traced=0 accounted=6 drew=240 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=1
  AI52I imp16 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=5 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=1
  AI52I impi cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=1
  AI52I imp cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=152 le_separating=14 le_passed=0 d0_separating=69 d0_passed=0 cmp_separating=6 cmp_passed=0 u16_separating=52 u16_passed=0 own_separating=119 own_passed=0 site_control_passed=0 boundaries=9
  AI52I catapult cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=240 le_separating=22 le_passed=0 d0_separating=54 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=2
  AI52I horror cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=96 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=2
  AI52I blood cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=240 le_separating=31 le_passed=0 d0_separating=143 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 own_separating=0 own_passed=0 site_control_passed=0 boundaries=5
  AI52I total cases=3120 match=3120
  AI52I result=ok
  ```
  The `SITES` line under each family counts the cases per boundary and call site (62 site/boundary pairs over the 13
  families, a return counted as one); the `EDGES` line the cases that meet each non-draw compare and each draw at
  equality; the `TAGS` line (rows 116, 120, 122) the paths ai/0010 § 3 names; `drew` the cases whose seed moved before
  the boundary; `accounted` the traced reads the checker accounts as `g_UnitHashOffsets` (`0x006E10E0 + 4·type` at
  0x00552F9C) and state 16's slot table (`0x006E34E0 + 8k` at 0x005E2D16 and 0x005E2D55, `0x006E34E4 + 8k` at
  0x005E2D61); it fails a family when one is missing. **Development runs** (rule 6): `emu/dev-1/` (the first case
  writer; its copy `dev-1/ai_cat_emu9.py.rev` `ddfcf5fa…`; `dev-1/check.txt` `a0f4dc23…`, `result=ok`;
  `dev-1/manifest.sha256` `6d717e7b…`, 54 lines) and `emu/dev-2/` (the tuned writer before row 120's stored-player
  cases and the `TAGS` line; its copy `dev-2/ai_cat_emu9.py.rev` `1343d84d…`; `dev-2/check.txt` `1ec2bee3…`,
  `result=ok`; `dev-2/manifest.sha256` `cf3c5f7c…`, 54 lines): 3 120 cases each, all matching, 0 stopped, every
  control failing every case it separates; each passes from its directory. dev-2's files were written into `emu/` and
  moved into `dev-2/` before the kept run (its copy regenerates its case files and its `check.txt` byte for byte).
  The kept run's case and memory files and `check.txt` regenerate identically with the committed tool (`cases` into a
  scratch directory, `check` on the kept outputs, compared with `cmp`).
- **Re-check under the fixed script** (`main` fd2ca68a, `lane/r55e`'s per-case copy fix, `EmuBoundary.java`
  `0c88b790…`): the kept run's 26 case and memory files copied unchanged into `workspace/logs/r52i/emu-recheck/` and
  the thirteen `emuboundary` runs repeated the same way; all 13 `.out` files are byte-identical with the kept run's
  (`cmp`, 0 differences; `emu-recheck/manifest.sha256` `ae55d8b3…`, 52 lines, passing from that directory). This run's
  memory spec has no data directive (only `observe` and `guard` lines), so the fix had nothing to change here.
- **Conclusion:** the maps are `[C]` in ai/0010 §§ 2, 3, each up to its first boundary or return; the entry call of
  state 16's think and row 124's sign test `[C]` as calls. Not the callees, nothing after them. No symbol raise
  (ADR-0015 scope, review-fixes rule 14). (run:2026-11-03-ai-cat-emu-9)

## run:2026-11-03-ai-cat-emu-10

- **Question:** (plan 0052 Phase 1, catalogue batch 10, pool-G) Do the think functions of rows 126, 127, 129, 130,
  132, 134, 136, 137, 139 and 141, the inits of rows 127, 129 and 134, row 133's class jump with the quest test of its
  three class thinks, and row 131's entry map their declared inputs to the first boundary they reach (or their
  return), its call site, its arguments, the unit seed, `AiCtl+0x14/+0x18/+0x1C/+0x3C` and `Unit+0xC4` as
  [ai/0011](0011-batch10.md) § 2 reads them?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`0c88b790…`, `lane/r55e`'s per-case copy
  fix, unchanged), lane project copy `workspace/ghidra-r52j` (symbols replayed from `re/symbols.csv` and the scratch
  `workspace/logs/r52j/b10-sym-scratch.csv`; emulation does not use them), heap 3 GB (`GHIDRA_HEADLESS_MAXMEM=3G`),
  each of the fifteen headless runs inside its own `systemd-run --user --scope -p MemoryMax=4G`, one Ghidra at a time.
  No wine, no slot. Models and case writer `tools/ai_cat_emu10.py` (`db68ae1d…`), every draw from
  `random.Random("r52j-<family>")`. Files in `workspace/logs/r52j/emu/`, `manifest.sha256` (`f5b88301…`, 61 lines,
  `check.txt` `a348deef…`); `sha256sum -c manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r52j/emu
  python3 -I tools/ai_cat_emu10.py cases
  export GHIDRA_PROJ_DIR=workspace/ghidra-r52j GHIDRA_HEADLESS_MAXMEM=3G
  for f in spotter barbi barb genspi genspawn mauler wussie statue ancient thronei throne taunt defiler tentacle bminion; do
    systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/ai_cat_emu10.py check > $D/check.txt
  python3 -I tools/ai_cat_emu10.py manifest --write
  ```
  Each case writes the game's difficulty, frame and quest list (none, or one or two nodes with an id, a data pointer
  and the data's `+0x0C` word and `+0x11` byte), and the one unit hash slot a lookup reads (row 139's owner); the unit
  (type 1, class, mode, monster data, seed, path, game, owner type and guid, `+0xC4`, `+0xC8`, `+0xD0`) and its path
  (x, y, room); the target (type, guid, mode, path or none with its `+0x00` word, x, y, static words and room,
  `+0xC6`, `+0xE4`) or none; a second unit for the lookup; the monster data's `+0x28` and the AI control (state,
  `+0x14/+0x18/+0x1C`, `+0x3C`); the `AiCtx` (with `+0x1C` 0 in row 134's `mnull` cases); the unit's MonStats record
  (the `aip` block, `Skill1..8`, `Sk1..8mode`) at the class's place under `DataTables+0xA78`, and the DataTables pointer
  with the MonStats base and count; the memory spec observes 36 callees and guards the allocator and fatal entries (6).
- **Observed** (`check.txt`, first line of each family):
  ```
  AI52J spotter cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=200 le_separating=5 le_passed=0 d0_separating=123 d0_passed=0 cmp_separating=27 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=53 self_passed=0 site_control_passed=0 boundaries=3
  AI52J barbi cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=1
  AI52J barb cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=115 le_separating=4 le_passed=0 d0_separating=31 d0_passed=0 cmp_separating=15 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=4
  AI52J genspi cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=1
  AI52J genspawn cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=45 d0_passed=0 cmp_separating=54 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=26 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=4
  AI52J mauler cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=240 le_separating=33 le_passed=0 d0_separating=81 d0_passed=0 cmp_separating=34 cmp_passed=0 u16_separating=11 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=4
  AI52J wussie cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=1
  AI52J statue cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=2
  AI52J ancient cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=7
  AI52J thronei cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=1
  AI52J throne cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=19 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=3
  AI52J taunt cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=72 d0_passed=0 cmp_separating=55 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=4
  AI52J defiler cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=2
  AI52J tentacle cases=240 match=240 bad=0 stopped=0 traced=0 accounted=5 drew=129 le_separating=7 le_passed=0 d0_separating=99 d0_passed=0 cmp_separating=17 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=3
  AI52J bminion cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=240 le_separating=41 le_passed=0 d0_separating=135 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=4 u16_passed=0 abs_separating=0 abs_passed=0 self_separating=0 self_passed=0 site_control_passed=0 boundaries=5
  AI52J total cases=3600 match=3600
  AI52J result=ok
  ```
  The `SITES` line under each family counts the cases per boundary and call site (45 site/boundary pairs over the 15
  families, a return counted as one); the `EDGES` line the cases that meet each non-draw compare and each draw at
  equality; the `TAGS` line (rows 126, 133, 139) the paths ai/0011 § 3 names; `drew` the cases whose seed moved before
  the boundary; `accounted` the traced reads the checker accounts as `g_UnitHashOffsets` (`0x006E10E0 + 4·type` at
  0x00552F9C); it fails a family when one is missing. **Development run** (rule 6): `emu/dev-1/` (the first case
  writer; its first check had 53 mismatches, all `genspawn` cases expecting row 129's `v18 ≥ aip3` command at the
  call 0x005E620B where the code's is 0x005E624C, ai/0011 § 3; the model was corrected, the outputs were not rerun);
  its copy `dev-1/ai_cat_emu10.py.rev` (`94625ccf…`, the corrected model with the first writer) regenerates its case
  files byte for byte; `dev-1/check.txt` (`2fdf2ac6…`): 3 600 cases, all matching, 0 stopped, every control failing
  every case it separates, `result=ok`; `dev-1/manifest.sha256` (`c45d64df…`, 62 lines) passes from its directory.
  The kept run's case and memory files and `check.txt` regenerate identically with the committed tool (`cases` into a
  scratch directory, `check` on the kept outputs, compared with `cmp`).
- **Conclusion:** the maps are `[C]` in ai/0011 §§ 2, 3, each up to its first boundary or return; row 131's entry
  call and row 133's quest tests `[C]` as calls. Not the callees, nothing after them. No symbol raise (ADR-0015 scope,
  review-fixes rule 14). (run:2026-11-03-ai-cat-emu-10)

## run:2026-11-03-ai-cat-emu-11

- **Question:** (plan 0052 Phase 1, catalogue batch 11, bosses-B) Do the think, init and `alt` functions of rows 51,
  128, 135, 138, 140, 145 and 147, Diablo's decision 0x005E8810, Baal's decision 0x005FC630, its three tables and its
  action 0x005FCB60, the pick callbacks 0x005E8EB0, 0x005FC000, 0x005EF5E0 and the unreferenced weighted pick 0x005FC130
  map their declared inputs to the first boundary they reach (or their return), its call site, its arguments, the
  unit seed and `AiCtl+0x14/+0x18/+0x1C` as [ai/0012](0012-batch11.md) § 2 reads them?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`0c88b790…`, unchanged), lane project copy
  `workspace/ghidra-r52k` (symbols replayed from the scratch `workspace/logs/r52k/b11-sym-scratch.csv`; emulation does
  not use them), heap 3 GB (`GHIDRA_HEADLESS_MAXMEM=3G`), each of the twenty headless runs inside its own
  `systemd-run --user --scope -p MemoryMax=4G`, one Ghidra at a time. No wine, no slot. Models and case writer
  `tools/ai_cat_emu11.py` (`d5ece728…`; a docstring-only revision of 2026-11-03, `3a831a19…`, regenerates the same cases (all 20 families, 40 case and memory files, byte-identical, compared at the lane check of 2026-11-03), and the run's revision is kept as `workspace/logs/r67/ai_cat_emu11.py.d5ece728`), every draw from `random.Random("r52k-<family>")`. Files in
  `workspace/logs/r52k/emu/`, `manifest.sha256` (`434a1e4b…`, 81 lines, `check.txt` `57f25e1a…`); `sha256sum -c
  manifest.sha256` from that directory passes.
- **Procedure:**
  ```
  D=workspace/logs/r52k/emu
  python3 -I tools/ai_cat_emu11.py cases --dir $D
  export GHIDRA_PROJ_DIR=workspace/ghidra-r52k GHIDRA_HEADLESS_MAXMEM=3G
  for f in dalt balt diablo ddec dcb bcb nihli nihl stairs pcb bcrab bclone bdec bact bmelee bblock branged wpick uberd uberb; do
    systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/ai_cat_emu11.py check --dir $D > $D/check.txt
  (cd $D && sha256sum <every file but the manifest> > manifest.sha256)
  ```
  Each case writes the image the tool's docstring declares (the game, the unit and its path, the target and its path,
  two more units for the lookups, the monster data and the AI control with its parameter ring and owner words, the
  `AiCtx`, the MonStats record, the DataTables pointer, the quest list for `nihl`, the hash slots for `bclone`, the
  weight block for `wpick`); register arguments by `r` lines (`EAX` in `bdec`, `bmelee`, `branged`, `wpick`; `ESI` in
  `bblock`); the memory spec observes 44 callees and guards the allocator and fatal entries (6).
- **Observed** (`check.txt`, first line of each family):
  ```
  AI52K dalt cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K balt cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K diablo cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=2
  AI52K ddec cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=4
  AI52K dcb cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=27 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=21 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K bcb cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=26 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=7 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K nihli cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K nihl cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=25 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=2
  AI52K stairs cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K pcb cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=2
  AI52K bcrab cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K bclone cases=240 match=240 bad=0 stopped=0 traced=0 accounted=5 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=2
  AI52K bdec cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=5
  AI52K bact cases=240 match=240 bad=0 stopped=0 traced=0 accounted=15 drew=0 le_separating=0 le_passed=0 d0_separating=6 d0_passed=0 cmp_separating=29 cmp_passed=0 u16_separating=6 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=16
  AI52K bmelee cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=160 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K bblock cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=160 d0_passed=0 cmp_separating=26 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K branged cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=160 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K wpick cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=138 le_separating=41 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=19 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K uberd cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K uberb cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 abs_separating=0 abs_passed=0 uns_separating=0 uns_passed=0 site_control_passed=0 boundaries=1
  AI52K total cases=4800 match=4800
  AI52K result=ok
  ```
  The `SITES` line under each family counts the cases per boundary and call site (46 site/boundary pairs over the 20
  families, a return counted as one); the `EDGES` line the cases that meet each ordered compare at equality; the
  `TAGS` line the paths ai/0012 § 4 names; `drew` the cases whose seed moved before the boundary; `accounted` the traced
  reads the checker accounts (`g_UnitHashOffsets` at 0x00552F9C in `bclone`, the jump table `0x005FCEF0 + 4(k−1)` at
  0x005FCBC0 in `bact`); it fails a family when one is missing. **Development runs** (rule 6): `emu/dev-1/` (the first
  tool, `dev-1/ai_cat_emu11.py.dev1` `9167167d…`; `check.txt` `90ba44e7…`, `result=FAIL`: `bcrab` 240 and `bclone` 38
  register mismatches at the pick, `bdec` 240 ended at its own entry on the observe list, 56 and 15 unaccounted traced
  reads; ai/0012 § 4) and `emu/dev-2/` (the corrected models, `dev-2/ai_cat_emu11.py.dev2` `97008dcc…`; `check.txt`
  `391a669e…`, 4 800 cases, all matching, `result=ok`); manifests `c8e22d3b…` and `50b004fc…`, 82 lines each, each passes
  from its directory. Each tool copy regenerates its run's case and memory files byte for byte and reproduces its
  `check.txt`; the kept run's case and memory files and `check.txt` regenerate identically with the committed tool
  (`cases` into a scratch directory, `check` on the kept outputs, compared with `cmp`).
- **Conclusion:** the maps are `[C]` in ai/0012 §§ 2, 4, each up to its first boundary or return. Not the callees,
  nothing after them. No symbol raise (ADR-0015 scope, review-fixes rule 14). (run:2026-11-03-ai-cat-emu-11)

## run:2026-11-03-ai-cat-emu-12

- **Question:** (plan 0052 Phase 1, catalogue batch 12, towns, NPCs and the state rows) Do the think and init functions of rows 31, 32, 41, 42,
  54, 58, 62, 81, 88, 91, 99, 100, of state rows 2, 3, 8–14 and 17, and the town helpers `AiNpcSaveHome`, `AiNpcHomeLeash`, `AiNpcScriptStep`,
  `AiNpcPathPick` with its five actions, 0x005E7350, 0x005E77A0, `AiPathSkillStep`, 0x005E5710, 0x005E7D30, `AiNearestPlayer` with its callback and
  the two list tests map their declared inputs to the first boundary they reach (or their return), its call site, its arguments, the unit seed, the AI
  control words and the named memory as [ai/0013](0013-batch12.md) § 2 reads them?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`0c88b790…`, unchanged), lane project copy `workspace/ghidra-r52l`
  (symbols replayed from `re/symbols.csv`; emulation does not use them), heap 3 GB (`GHIDRA_HEADLESS_MAXMEM=3G`), the runs in sequence inside one
  `systemd-run --user --scope -p MemoryMax=4G`, one Ghidra at a time. No wine, no slot. Models and case writer `tools/ai_cat_emu12.py` (`a8b42f49…`),
  every draw from `random.Random("r52l-<family>")`. Files in `workspace/logs/r52l/emu/`, `manifest.sha256` (`31a52769…`, 165 lines, `check.txt`
  `f2d6e75f…`); `sha256sum -c manifest.sha256` from that directory passes. Development run `emu/dev-1/` (own manifest, 166 lines, its tool copy
  `ai_cat_emu12.py.rev`), `result=FAIL` on the first-model errors of ai/0013 § 5.
- **Procedure:**
  ```
  D=workspace/logs/r52l/emu
  python3 -I tools/ai_cat_emu12.py cases --dir $D
  export GHIDRA_PROJ_DIR=workspace/ghidra-r52l GHIDRA_HEADLESS_MAXMEM=3G
  systemd-run --user --scope -p MemoryMax=4G bash -c 'for f in <the 41 families>; do
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err; done'
  python3 -I tools/ai_cat_emu12.py check --dir $D > $D/check.txt
  python3 -I tools/ai_cat_emu12.py manifest --dir $D --write
  ```
  Each case writes the image the tool's docstring declares; the memory spec observes 79 callees and guards the allocator and fatal entries (6). No `r` lines.
- **Observed** (`check.txt`, first line of each family):
  ```
  AI52L npc cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=7
  AI52L nstat cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=4
  AI52L towner cases=240 match=240 bad=0 stopped=0 traced=0 accounted=7 drew=72 le_separating=15 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=83 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=17
  AI52L jarjar cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L oot cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=6
  AI52L trogue cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=1
  AI52L st8 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=1
  AI52L navi cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=3
  AI52L buffy cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L st9 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L st10 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=1 drew=152 le_separating=41 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=3
  AI52L st11i cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=1
  AI52L st11 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=1
  AI52L st12 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=1
  AI52L vendor cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=240 le_separating=62 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L soul cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=26 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=7
  AI52L illus cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L dark cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=1
  AI52L st2 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=73 le_separating=13 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=16 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=47 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=4
  AI52L st3i cases=240 match=240 bad=0 stopped=0 traced=0 accounted=1 drew=98 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=1
  AI52L st3 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L st13 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=3
  AI52L st14 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=240 le_separating=29 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=3
  AI52L h6800 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=192 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L h6860 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=4 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=46 arg_passed=0 site_control_passed=0 boundaries=3
  AI52L h6ae0 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=3 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=75 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=69 arg_passed=0 site_control_passed=0 boundaries=13
  AI52L h7080 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=7 drew=190 le_separating=45 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=226 arg_passed=0 site_control_passed=0 boundaries=5
  AI52L act1 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=192 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L act2 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=181 arg_passed=0 site_control_passed=0 boundaries=3
  AI52L act3 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=188 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L act4 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=80 arg_passed=0 site_control_passed=0 boundaries=4
  AI52L act5 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=81 arg_passed=0 site_control_passed=0 boundaries=4
  AI52L h7350 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L h77a0 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=4
  AI52L h5b70 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=45 cmp_passed=0 u16_separating=7 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L h5710 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L h7d30 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L hp cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L hcb cases=240 match=240 bad=0 stopped=0 traced=0 accounted=2 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=23 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=2
  AI52L il0 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=1
  AI52L il1 cases=240 match=240 bad=0 stopped=0 traced=0 accounted=0 drew=0 le_separating=0 le_passed=0 d0_separating=0 d0_passed=0 cmp_separating=0 cmp_passed=0 u16_separating=0 u16_passed=0 lo8_separating=0 lo8_passed=0 arg_separating=0 arg_passed=0 site_control_passed=0 boundaries=1
  AI52L total cases=9840 match=9840
  AI52L result=ok
  ```
- **Conclusion:** [C] the maps of ai/0013 § 5, each ending at its first callee (ADR-0021); the code as a map over a declared image, no symbol raised (ADR-0015, `lane/p46m12` ruling 7). Separation: `le` 205, `cmp` 272, `u16` 7, `lo8` 47, `arg` 1 255 cases, none passing; `d0` separates none, no emulated path reading the difficulty before a boundary; the site control passes none. (run:2026-11-03-ai-cat-emu-12, fn:sub_005E6AE0_AiNpcScriptStep@0x005E6AE0)
- **Left `[I]`:** everything after a boundary, among them the five path actions' walk and their records past `Ovr` or `MonModeAllowed` (`SITES`), `AiNpcNearPlayer`'s body (past the search), the size branch of `UNIT_GetSizeX`, the unit-null guards, the unsigned reading of row 99's positions. (fn:sub_005E68F0_AiNpcNearPlayer@0x005E68F0)

## run:2026-11-03-ai

- **Question:** (plan 0052 Phase 2, first lane run, also plan 0056 Phase 3's pilot on the runner library) Do the AI
  decisions of the game, logged per event, match the first-boundary maps of [ai/0002](0002-pool-a.md)–[ai/0010](0010-batch9.md)
  (the emulated think functions) and the first-callee maps read for the five unemulated tier AIs, and what do the
  events' seeds, commands, path plans and skill starts do around them?
- **Setup:** slot 2 (display `:9`, `workspace/wineprefix-2`), game 1.14d expansion, Normal, character `CombatSor`
  (`tools/d2s_recipes/combatsor.json` on `workspace/samples/d2s-owner/smpsor-l50.d2s`, `1d9de374…`; clvl 85
  Sorceress, Teleport and Nova, Act V Barbarian mercenary) and, for the Necromancer case, `AiNec`
  (`tools/d2s_recipes/ai-nec.json` on `workspace/samples/d2s/smpnec.d2s`, `ea62db6a…`; Clay Golem, Raise Skeleton).
  Logger `tools/gdb/ai.gdb` + `tools/gdb/ai.py` (rev 2 for the first batch, rev 3 for the later ones; rev 1 only in the
  development logs), sessions `tools/ai_sessions.py` on `tools/harness_runner.py`, driven by `tools/d2pilot.py farm`
  (waypoint, Nova sweep) and `hunt`, checker `tools/ai.py` (`check` over the kept case logs; `tools/test_ai.py`, 12
  no-game tests). Tool revisions: the first batch (launches 5201–5204, 17 cases) ran with `706dccdf`; the later batches
  with `70b2f480`, `008aff02` and `d56f99d6` (changes between them: the logger's return-address windows (rev 3), the
  staged-level check, the case table, the checker's chain and histogram lines; no change to a kept session's clicks).
  Logger: the unit seed and the AI control at the event entry, the think call (`0x005B186F`, the AiCtx, the AI
  control's 0x40 bytes, the parameter head record, MonStats `aip` and skills, the target), the first eight calls of the
  models' boundary functions (136 addresses, the union of the emulations' `OBSERVE` sets without the image-run helpers)
  from the think code, `MonSetMode` and `PathPlan` entry and exit seeds, `SKILLS_SrvStart` entry and exit, and the event
  exit (`0x005B1876`); filter: server monsters within 80 sub-tiles of the first player per axis; caps per game 200 per AI
  row, 3 000 decisions, 600 events that end before the think call.
- **Cases:** 31 kept case logs in 9 launches (a tenth launch, 5401, kept nothing and was run again as 5402) (`<RUN>-s2-<seed>-L<k>.log` with `.marks.tsv`, cut by
  `harness_runner.py split` into `-<case>.log`): launches 5201 (8 cases), 5202 (7), 5203 and 5204 (one case each, fresh
  processes, the repeats of `a1-jail` and `a2-halls`), 5301 (8), 5302 (`a1-necro`), 5402 (5), 5501 and 5502 (`a1-andariel-p8`,
  `/players 8`, two fresh processes). Stages: Jail 1, Stony Field, Dark Wood, Black Marsh, Inner Cloister, Catacombs 2–4
  (Andariel), Halls of the Dead 2, Far Oasis, Arcane Sanctuary, Palace Cellar 1, Flayer Jungle, Travincal, Durance 2,
  City of the Damned, River of Flame, Crystalline Passage, Halls of Pain, Glacial Trail (each: the waypoint from the
  Act IV town, Nova sweep 130–300 s). Not kept: two cases of launch 5202 that stayed in the town (the waypoint list did not
  open, `a4-cotd`, `a5-crystal`; kept as `dev-stayed-in-town-*`) and the first try of `a1-jail-2` (5401, same cause,
  `dev-failed-try-*`); launch 5401 was run again as 5402. Development: 9 launches (`dev-*`, `dev-aborted-r1-*`; manifest
  `manifest-dev.sha256`, 44 lines): the first logger, the wrong waypoint click point, rev 1's missing `MonSetMode`
  argument read (the command is the second stack word) and PathPlan's three late returns, the Necromancer smoke.
- **Result** (`check-run-2026-11-03-ai.txt`, in the manifest): 14 645 decisions in 31 logs, 17 679 more events
  that ended before the think call. 10 374 compared with an emulated model, 2 240 with a hand map, 2 016 in rows with no
  model (batches 10–12 not emulated, town rows 32 and 54, three rows with an unlogged input), 15 not comparable (rev 2
  window, Scarab, § below): **0 mismatches** in the 12 614 compared, at each decision's first boundary only; the 2 016 no-model decisions, the 15 not comparable and the 17 679 events that end before the think call are outside the 0. Tier AIs (decisions, all compared): Skeleton (row 2) 357,
  Fallen (6) 1 393, Wraith (9) 70, FallenShaman (13) 363, Scarab (20) 180 (15 not comparable), Mummy (21) 168, GreaterMummy (22) 71,
  Vampire (28) 279, BatDemon (29) 115, Fetish (30) 130, Andariel (34) 64, CorruptArcher (35) 95, SkeletonBow (37) 278,
  Hireable (61) 5 697, SkeletonMage (64) 226, NecroPet (67) 184, Megademon (89) 98, BloodLord (125) 55: every tier AI has at least 50.
- **What the comparison separates** (architect check, `tools/ai.py` models and hand maps run over the 31 logs, distinct
  predicted (function, call site) first boundaries per tier AI over its compared decisions; the checker prints no such
  line, so this is a recount, not a kept output): Skeleton 4 of 357, Fallen 1 of 1 393, Wraith 3 of 70, FallenShaman 2
  (358 and 5), Scarab 5, Mummy 5, GreaterMummy 3, Vampire 1 of 279, BatDemon 1 of 115 (110 think, 5 alt), Fetish 1 of 130,
  Andariel 5 of 64, CorruptArcher 1 of 95, SkeletonBow 1 of 278, Hireable 1 of 5 697, SkeletonMage 1 of 226, NecroPet 1
  of 184, Megademon 1 of 98, BloodLord 5 of 55. Ten tier AIs have one predicted first boundary in this window, so for them
  the 0 shows that first callee, its registers, stack words and seed (emulated models also the control words and the
  block), not a branch choice; the Fallen hand map's mode 0/12 return branch was never taken. No live negative control was
  run: the separation controls are the no-game ones of `tools/test_ai.py` (a corrupted site, seed, function or `aip` block
  on a synthetic log is found).
- **Unlogged sites.** The rev 2 window did not cover the `GameFindUnit` call inside `MonsterOwner` (`0x0058F0FF`), which
  the Scarab model predicts as its first boundary when the owner words are set: 15 first-batch Scarab decisions are
  counted `unlogged`, not as matches; rev 3 covers it and the 95 Scarab decisions of `a2-oasis-3` all compare.
- **Chaining.** Decision pairs on one seed (a decision's exit seed is the unit's next decision's entry seed): 12 368,
  9 687 of them with draws; 37 rows have at least 20 drawing pairs; short with counts: rows 7 (3), 11 (2), 14 (15), 30
  Fetish (2), 34 Andariel (5), 36 (6), 65 (12), 70 (15), 95 (6), 98 (1), 114 (9). Decision to `SKILLS_SrvStart`: 899
  skill starts run inside a decision's event (between the think call and the exit), all 899 at the decision's last
  logged seed advanced 0–12 steps (the steps per row in `SKCHAIN`), and all 899 exit with the event's exit seed.
- **Plan and seeds.** `PathPlan`: 9 618 entry/exit pairs inside decisions, 0 with a changed unit seed (types 2, 5, 6, 7,
  13, 15 observed, 148/217/203/1 961/5 825/1 580). Seed accounting: every logged point of every decision (entry, think
  call, boundaries, `MonSetMode`, `PathPlan`, skill start, exit) follows the previous one by whole LCG steps of the same
  unit seed, 0 violations (steps 0–7).
- **State.** `AiCtl.state` is 0 at all 32 324 events (14 645 decisions and 17 679 others); no event in states 10–13.
  Window: the 31 kept logs, Normal, the stages above, a clvl 85 character and a Barbarian mercenary or a Necromancer's
  summons, no curse, cloak, flee or super-unique case staged. So the control (an event in a non-zero state) is absent and
  the reading "no setter" for state rows 2, 3, 8, 9, 14, 17 is not tested by absence here; it needs a window with a live
  control (a curse by Amplify Damage or Terror on a monster, `MonFleeFrom`).
- **Library pilot (plan 0056 Phase 3).** Launches 19 (10 batch, 9 development; 9 with kept cases); kept case logs 31 (15 of the first
  batch's 17 runner-kept cases, 9, 5 and 2); launches per kept case 10/31 = 0.32 (19/31 = 0.61 with development); case
  switch 18.7 s (`a2-halls`, launch 5202 onward `next_case`), batches 2 237 s (17 cases), 1 744 s (9), 1 195 s (5), 360 s
  (2) of wall, 131, 194, 239 and 180 s per case. The lane's prompt supplied the per-batch opt-in to share processes (owner answer 2 of plan 0056, harness-play.md §
  Fresh process; plan 0056 Phase 3 names this batch as the pilot, so no further owner decision is needed): the checker models no process state, and the two fresh-process repeats (`a1-jail` 385
  decisions, `a2-halls` 522) check with 0 mismatches as the shared-process cases do. Waypoint clicks: 9 retries in the
  first and third batches, 3 cases without a level change.
- **Deviation, § Fresh process rule 5** (recorded by plan 0056 Phase 4, architect; recount `tools/pilot0056_recount.py`, `workspace/logs/p56/phase4-recount.txt`). Launch 5202 ran `a5-glacial`, `a1-cloister`, `a1-catacombs` and `a3-durance` after `a4-cotd` and `a5-crystal` had stayed in the town: the first batch's runner had no stage check and reported them kept. The four stay, since the checker reads no carried state; without them, 27 logs, 13 355 decisions, 11 472 compared, 0 mismatches, every tier AI still at least 50 (Andariel 60, BloodLord 55, Wraith 68). Batch wall sums to 92.3 min, 3.0 per kept case.
- **Launch 5202 and rule 5** (added by `lane/p52b`, 2026-11-03): harness-play.md § Fresh process rule 5 (a stage not reached is a failure; the rest of
  the batch starts in a fresh process) was not applied in launch 5202. Its marks (`2026-11-03-ai-s2-5202-L2.marks.tsv`) list `a3-travincal`,
  `a4-cotd`, `a5-crystal`, `a5-glacial`, `a1-cloister`, `a1-catacombs`, `a3-durance` in one process; `a4-cotd` and `a5-crystal` stayed in the town
  (kept as `dev-stayed-in-town-*`) and the next four cases ran in the same process, one batch's opt-in notwithstanding. The checker reads no
  carried state (rule 2: it models no process state) and the two fresh repeats (`a1-jail`, `a2-halls`) check with 0 mismatches as the shared cases
  do, so the four cases stay in the record's counts; this is the lapse the plan 0056 Phase 4 text of rule 5 names. (run:2026-11-03-ai)
- **Not done in this run** (named short): the 331 monster gaps of the H1 oracle replacement (the kept skills logs of
  run:2026-10-25-skills and run:2026-10-27-skills hold 0 `AID` or `AIB` lines, so none can close from them; the re-walk
  needs a session with both loggers); H3's Raven calls; the Phase 1b cases P1b-1 (Duriel, 300 melee decisions) and P1b-2
  (Greater Mummy and a champion corpse); a live control for the state record; one pilot of each P1 batch outside the
  tier for batches 5 (rows 84, 86, 101–112), 7 (Duriel…), 10 (row 130 logged, no model), 11 and 12 (rows 32, 54 logged,
  no model).
- **Conclusion** (run:2026-11-03-ai, 0x005B186F): the first-boundary maps are `[C]` against live decisions for the 18 tier AIs (13 emulated maps, five
  first-callee maps) up to their first boundary, nothing after it; the rest are `[I]` as before. See
  [ai/0015](0015-phase2-first-run.md). Manifests: `workspace/logs/ai/manifest-run-2026-11-03-ai.sha256` (72 lines,
  `sha256sum -c` passes from `workspace/logs/ai`), `manifest-dev.sha256` (44 lines).


## run:2026-11-03-ai-2

- **Question:** (plan 0052 Phase 2, second lane run `lane/p52b`, **checkpoint**) The first run's 0 mismatches is a weak separator (ten tier AIs with one
  predicted first boundary, a claim that ends at the first boundary): what does each tier AI's comparison separate, does a wrong map fail on the
  kept logs, and can a decision be compared past its first boundary?
- **Setup:** slot 2 (display `:9`, `workspace/wineprefix-2`), game 1.14d expansion, Normal, character `CombatSor` (as run:2026-11-03-ai), one game process
  per case from the coordinator's message on (plan 0056 Phase 4: `tools/ai_sessions.py run --fresh`; launches r4a and r4b ran before it, r4c's cases are
  marked `fresh:`). Tools: `tools/ai.py` (`c0fd95ec`: `MIX`, `MIXSUM`, `--controls`; later `51c4497f`), `tools/gdb/ai.py` rev 4 (`3599e2ac`: AIR lines,
  `bmax 48`; `6f22c961`: no nested boundary lines, first used by the next launch), `tools/gdb/ai-retsites.txt` and `tools/ai_retsites.py`, `tools/ai_resume.py`
  (`3599e2ac`, decode fixes up to `51c4497f`), `tools/test_ai.py` (18) and `tools/test_ai_resume.py` (14) no-game tests.
- **Kept sessions: none.** The kept output of this checkpoint is the checker over the 31 kept logs of run:2026-11-03-ai: `check-mix-2026-11-03-ai.txt`
  (`python3 -I tools/ai.py check --controls <the 31 case logs> --out check-mix-2026-11-03-ai.txt`, run from `workspace/logs/ai` with the repo's tools by absolute
  path; manifest `manifest-run-2026-11-03-ai-2.sha256`, 1 line, passes from `workspace/logs/ai`).
- **Development launches** (listed separately, `manifest-dev-2.sha256`, 40 lines, passes from `workspace/logs/ai`): r4a (2 launches, seed 5601: a Jail 1
  case that stayed in the town twice, rev 4's first logger: AIR lines, no cap fix), r4b (1 launch, seed 5201, Jail 1 kept as dev: 194 decisions; the
  logger that cleared pending returns at 600 non-think calls, 2 289 AIR lines for 2 323 AIB), r4c (4 launches, seeds 5201–5204, `--fresh`: Jail 1 first
  try in the town, Jail 1 rerun, Halls of the Dead 2 in the town (not rerun: the batch's rerun was spent), Catacombs 2–4 with Andariel: 4 logs, 1 313 decisions).
  Waypoint clicks left the case in the town on the first try in 4 of the 7 launches.
- **Result, the checker** (`check-mix-2026-11-03-ai.txt`, 14 645 decisions, 0 mismatches as ai/0015 states them): `MIXSUM tier_ais_with_one_outcome=10
  rows=6,28,29,30,35,37,61,64,67,89 tier_ais_with_more=8`; per tier AI (decisions, distinct predicted first boundaries): Skeleton 357 / 4, Fallen 1 393 / 1,
  Wraith 70 / 3, FallenShaman 363 / 2, Scarab 180 / 5, Mummy 168 / 5, GreaterMummy 71 / 3, Vampire 279 / 1, BatDemon think 110 / 1 (alt 5 / 1), Fetish 130 / 1,
  Andariel 64 / 5, CorruptArcher 95 / 1, SkeletonBow 278 / 1, Hireable 5 697 / 1, SkeletonMage 226 / 1, NecroPet 184 / 1, Megademon 98 / 1, BloodLord 55 / 5.
  Negative control (live, on those logs): `CONTROL site compared=12629 failed=12629`; `CONTROL fallen compared=1393 failed=1393`; `CONTROL melee compared=12620
  failed=2114` with 26 rows not separated (the ten one-outcome tier AIs among them); `CONTROLS site=FAILS-AS-REQUIRED fallen=FAILS-AS-REQUIRED
  melee=FAILS-AS-REQUIRED`. (run:2026-11-03-ai-2, fn:sub_005B1740_MonAiEvent@0x005B1740)
- **Result, the resumable model** (development logs only, `dev-resume-r4c.txt`; the claim for the run needs kept sessions): 1 313 decisions, 1 028 resumed to
  their end, **0 mismatches**, 14 485 boundary calls matched, 13 173 after the first; stopped 285 (213 + 34 + 20 capped at 48 calls, 18 at a `call esi`).
  Controls: every known branch reversed, 1 200 of 1 313 mismatches (113 still ok); a seed one step off, 1 312 of 1 313. Per row in finding ai/0017 § 4.
  (run:2026-11-03-ai-2, 0x005B186F)
- **Not done in this checkpoint** (named, with their state): the kept batch with logger rev 4; the staged variety sessions; the state control window (recipes
  `ai-nec-curse.json` (Dim Vision 23 → state 10, Terror 56 → 11) and `ai-barb.json` (Howl, Taunt 27 → 12; Howl and Grim Ward reach `MonFleeFrom` through
  `StatEv08Howl` 0x005BFA10 and `MissHit28WardScare`) build, no session run, so states 10, 11, 12 are **not** observed and the absence of states 2, 3, 8, 9, 14, 17
  still counts for nothing); P1b-1 (no route to Duriel's lair yet: the staff in the orifice of the right one of the seven Tal Rasha tombs, level 73 the lair) and
  P1b-2; H1; H3; Fetish and Andariel at `/players 8`; the catalogue sample; the review request.
- **Conclusion:** [C] the outcome mix and the negative control on the first run's kept logs (above); [I] the resume model's figures (development logs). See
  [ai/0017](0017-phase2-second-run.md). Manifests: `workspace/logs/ai/manifest-run-2026-11-03-ai-2.sha256`, `manifest-dev-2.sha256`.
## run:2026-11-03-ai-3

- **Question:** (plan 0052 Phase 2, second lane run `lane/p52b`, second part) The kept batch the checkpoint (run:2026-11-03-ai-2) lacked: how far do decisions compare per tier AI
  with logger rev 4 and the resumable model, what stops a resume, which branches stay unseen; the state control (states 10, 11, 12 live); P1b-2 (a champion corpse for the Greater Mummy);
  P1b-1 (Duriel); G4 (the seven Uber helpers, breakpoints).
- **Setup:** slot 2 (display `:9`, `workspace/wineprefix-2`), game 1.14d expansion, Normal, one game process per case (`tools/ai_sessions.py run --fresh`), seeds 5801 + launch (batch 1, 22 launches), 5901 + launch
  (batch 2, 13 launches), 6101 + launch (P1b-2, 3 launches), 3364 + launch (Duriel development, 2 launches). Logger `tools/gdb/ai-g4.gdb` = `tools/gdb/ai.py` rev 4 (`AI logger armed rev 4 bmax 48`) + `tools/gdb/ai-g4.py` rev 1 (G4)
  (+ `tools/gdb/ai-p1b2.py` rev 2, only with `AI_P1B2=1`); commit `e0e45d03` for the tools of this part. Characters (built with `tools/ai_sessions.py build`): `CombatSor`, `AiNec`, `AiNecC` (`ai-nec-curse.json`), `AiBar` (`ai-barb.json`), `AiDur` (`ai-dur.json`,
  development only). Pilot options as the cases of `tools/ai_sessions.py` hold them (the melee cases `s-*`: `explore --walk --melee`, with `--melee-button 3 --curse-keys F1,F2 --keys-cycle` for the curse cases).
- **Kept sessions: 23.** 21 in run:2026-11-03-ai-3 (batch 1: 11 of 22 launches, batch 2: 10 of 13; the other 14 launches left the character in the Act IV town: "the waypoint list did not open", rerun) and 2 in run:2026-11-04-ai-3p
  (`a2-halls-p12`, `a2-halls-long`; the first of 3 launches stayed in the town). The 14 + 1 failed tries are under `workspace/logs/ai/dev/`. Manifests (both pass from `workspace/logs/ai`): `manifest-run-2026-11-03-ai-3.sha256`
  (84 lines: 23 case logs, the 23 launch logs and marks, the checks, the status files, `g4-run-2026-11-03-ai-3.txt`, `p1b2-run-2026-11-04-ai-3p.txt`, the pilot records), `manifest-dev-3.sha256` (106 lines: the development logs, the failed
  tries, the screenshots).
- **Procedure** (from `workspace/logs/ai`, the repo's tools by absolute path):
  ```
  python3 -I tools/ai.py check <the 21 case logs 2026-11-03-ai-3-s2-*-fresh:*.log> --controls --out check-run-2026-11-03-ai-3.txt > check-stdout-2026-11-03-ai-3.txt
  systemd-run --user --scope -p MemoryMax=4G python3 -I tools/ai_resume.py check <the same logs> --controls --examples 200 --out resume-run-2026-11-03-ai-3.txt > resume-stdout-2026-11-03-ai-3.txt
  python3 -I tools/ai_g4.py <the 23 kept launch logs> > g4-run-2026-11-03-ai-3.txt
  AI_P1B2=1 python3 -I tools/ai_sessions.py run ... a2-halls-p12 a2-halls-long ; python3 -I tools/ai_p1b2.py <the 2 case logs> > p1b2-run-2026-11-04-ai-3p.txt
  ```
- **Result:** the first-boundary check over 7 539 decisions: 6 272 compared, 0 mismatches, 1 265 in rows with no model, 2 truncated at a log's end (`unlogged`); controls site 6 272 of 6 272, fallen 814 of 814, melee 1 187 of 6 272 (23 rows not separated).
  The resume model: 7 135 resumed, **112 mismatches**, 292 stopped, 72 183 boundary calls matched, 64 689 after the first; controls: reversed branches 7 273 of 7 539, seed 7 497 of 7 539. State control: states 10 (38 decisions), 11 (98 decisions, 41 events),
  12 (56 decisions) live in `s-necro-curse` and `s-barb-howl`; no other nonzero state in 7 539 decisions and 10 721 events. P1b-2: 17 champion-flag and 16 unique-flag corpses placed, 4 champion corpses reached `MonSkillTargetOk` (2 accepted, 2 refused), 0 unique.
  G4: 0 helper hits in 23 launches, control 0x005B1CF0 live in 23, 0x005A3250 in 2. Per tier AI and the stop reasons: ai/0017 §§ 6 to 12.
- **Development launches:** `dev-2026-11-03-ai-3` (seeds 5701, 5702, 5703, 5711, 5721: the curse cases; `s-necro-curse` first built with 40 hops, then 80), `dev-2026-11-03-ai-3p` (6001: the P1b-2 logger, rev 1 without the unit pointer), `dev-2026-11-04-ai-3d`
  (3364 and 3365: Duriel, one attempt; the first launch stayed in the town, the second went to Canyon of the Magi and not into a tomb; stopped by hand).
- **Not done:** P1b-1 (no decision of row 44), H1, H3, the catalogue sample, the 112 resume mismatches' cause. The Duriel route is from the plan 0032 session 3364 log's positions (ai/0017 § 11).
- **Review recheck** (`lane/p52b` Tier A review, 2026-11-04, no game): `tools/ai_resume.py` reproduced the kept 112 line for line. `tools/ai_resume_review.py` (retired at `bf720f11`; last present at `8707b4e1`) `classify resume-stdout-2026-11-03-ai-3.txt <the 21 logs>` and `check P,B,C,N,E,D <the 21 logs> --controls`, from `workspace/logs/ai`, under `systemd-run --user --scope -p MemoryMax=4G`; `tools/ai.py` at the lane's head over the first run's 31 logs (`review-p52b/check-run1.txt`). Outputs in `workspace/logs/ai/review-p52b/`, `manifest.sha256` passes from that directory. Result: the classification of ai/0017 § 7; 7 444 resumed, 8 mismatches (cluster F alone), 87 stopped (row 32's `call esi` 80, a return site not armed 4, a log's end 3), 72 865 calls matched, 65 332 after the first; the controls still fail: reversed branches 7 290 of 7 539 (rows 15 and 54 not separated), a seed one step off 7 529 of 7 539. First run: 14 645 decisions, 12 614 compared, 0 mismatches.
- **Conclusion:** [C] the kept first-boundary comparison, the controls, the state control as a statement about the logged lines (ai/0017 § 8) and G4 for its window, as stated in ai/0017 § Answer; [I] the resume figures (112 mismatches, classified at the review: 104 model faults, 8 a logger limit). (run:2026-11-03-ai-3, 0x005B186F) Manifests as above.

## run:2026-11-04-ai-3p

- **Question:** (plan 0052 Phase 1b, P1b-2) Does a champion corpse reach the Greater Mummy's `MonSkillTargetOk` through its search callback 0x005F2A00, and a unique corpse (control) not?
- **Setup:** as [run:2026-11-03-ai-3](#run2026-11-03-ai-3), seeds 6101 to 6103, `AI_P1B2=1` (`tools/gdb/ai-p1b2.py` rev 2: a built state, flag 4 or 8 written at the callback's entry on dead candidates), cases `a2-halls-p12` and `a2-halls-long`; kept sessions 2 of 3 launches (manifest: `manifest-run-2026-11-03-ai-3.sha256`).
- **Result:** 17 champion-flag and 16 unique-flag corpses placed; 4 champion corpses reached `MonSkillTargetOk` (2 accepted and commanded, mode 14; 2 refused), 0 unique (`p1b2-run-2026-11-04-ai-3p.txt`, `tools/ai_p1b2.py`). A built state: the flags are written by the logger.
- **Deviation, ADR-0003** (recorded by the `lane/p52b` review, 2026-11-04): `tools/gdb/ai-p1b2.py` writes game memory at a breakpoint, flag 4 or 8 at `Unit+0x14 -> +0x16`, where ADR-0003 says a breakpoint "never writes game memory or registers". ADR-0010 and ADR-0013 cover cells of one table through a loose `.bin`, not this. Plan 0012's review accepted one such write (`MONPOOL_FORCE_DIFF`, F1) as a stated intervention before those ADRs existed, with a natural game required beside it; it is not a rule for this run. The result is forced, not natural.
- **Conclusion:** [I] as run (0x005F2A00, 0x005FD470); ai/0017 § 9. C40's required case stays open: a `-forced` run (ADR-0013) with natural champions, plan 0052 log.

## run:2026-11-04-ai-resume

Plan 0052 Phase 2, `lane/p52c`, no game. Tools at commit `bf720f11`.

- **Question:** with the review's six fixes in the model, what do the 21 rev 4 logs of run:2026-11-03-ai-3 say past the first boundary, per tier AI? Do H3's 2 218 calls take the owner pair?
- **Procedure** (from `workspace/logs/ai`, the repo's tools by absolute path):
  ```
  systemd-run --user --scope -p MemoryMax=4G python3 -I tools/ai_resume.py check <the 21 case logs 2026-11-03-ai-3-s2-*-fresh:*.log> --controls --examples 200 --out resume-run-2026-11-04-p52c.txt --tier resume-tier-2026-11-04-p52c.txt > resume-stdout-2026-11-04-p52c.txt
  python3 -I tools/ai_h3.py check ../skills/2026-10-25-skills-dru-1.log ../skills/2026-10-25-skills-dru-2.log --out h3-2026-11-04-p52c.txt
  python3 -I tools/ai.py counts <the case logs 2026-11-03-ai-s2-*-L*-*.log and 2026-11-03-ai-3-s2-*-fresh:*.log> > catalogue-rows-2026-11-04-p52c.txt
  ```
- **Outputs:** `manifest-run-2026-11-04-ai-resume.sha256` (passes from `workspace/logs/ai`). A first pass before rev 5's parser change is kept as `dev/dev-resume-*-p52c-before-rev5.txt`, in `dev/manifest-dev-p52c.sha256`, which passes from `dev/`.
- **Result:** 7 444 of 7 539 resumed, 8 mismatches (all row 23), 87 stopped, 72 865 calls matched, 65 332 after the first; reversed branches fail 7 290, rows 15 and 54 not separated; a seed one step off fails 7 529. H3: 2 320 calls, 2 218 with a list, 101 first calls and 2 117 later calls match, 0 seed differences; the alternative levels and no pair fail all 101 first calls. Logger rev 5 was not run.
- **Conclusion:** [I] the fixed model's totals, and [C], as proposed by the lane and narrowed at its review, six rows' fork-free decisions (run:2026-11-04-ai-resume-flip) and H3 at one level, as scoped in ai/0017 § 13. (run:2026-11-04-ai-resume, 0x005B186F, fn:sub_0056E050_MonOwnerSkillDamage@0x0056E050)
- **Review recheck** (`lane/p52c` Tier A review, 2026-11-04, no game): the tools at this branch's head, unchanged from `bf720f11`, reproduce `resume-run-2026-11-04-p52c.txt`, `resume-tier-2026-11-04-p52c.txt` and `h3-2026-11-04-p52c.txt` byte for byte (`review-p52c/rerun-*.txt`); the `RROW`, `RSTOP`, `RMISMATCH`, `RTOTAL` and `RCONTROL` lines equal `review-p52b/check-fixed.txt`. The retired script's outputs stay hashed in `review-p52b/manifest.sha256`, and its last revision is `8707b4e1`.

## run:2026-11-04-ai-resume-flip

Plan 0052 Phase 2, `lane/p52c` review, no game. `tools/ai_resume_flip.py` at commit `40e5ed1f`, over the same 21 rev 4 logs.

- **Question:** per row, how many decisions has the model decided with no unknown value, and which known branches, reversed one at a time, make a decision fail?
- **Procedure** (from `workspace/logs/ai`, the repo's tools by absolute path; each under `systemd-run --user --scope -p MemoryMax=4G`):
  ```
  python3 -I tools/ai_resume_flip.py check <the 21 case logs> --rows 2,9,13,15,19,21,22,28,29,30,32,34,35,37,54,64,67,89,99,100,125 --cap 1000000 --out review-p52c/flip-rows-full.txt
  python3 -I tools/ai_resume_flip.py check <the 21 case logs> --rows 61 --cap 200 --per-path 4 --out review-p52c/flip-row61-cap200.txt
  python3 -I tools/ai_resume_flip.py check <the 21 case logs> --rows 6 --cap 60 --per-path 1 --out review-p52c/flip-row6-cap60.txt
  ```
- **Outputs:** `review-p52c/manifest.sha256` (passes from `workspace/logs/ai/review-p52c`). The sites of rows 6 and 61 are a fixed sample (the cost: a full pass of Fallen did not end in 9 minutes); their census lines count every resumed decision.
- **Result:** no unknown-value branch in every resumed decision of rows 13 (103), 21 (205), 30 (316), 89 (77), and in 81 of 86 of row 37 and 79 of 91 of row 64; in none of rows 6 (814), 61 (2 061), 67 (53). Sites reversed alone: ai/0017 § 13's table. Row 54: 0 of 3 sites fail a decision; row 15: 15 of 16.
- **Conclusion:** [C] the fork-free decisions' reproduction, and [I] the rest as a consistency check, ai/0017 § 13. (run:2026-11-04-ai-resume, 0x005B186F)

## run:2026-11-03-ai-uber

- **Question:** (plan 0052 Phase 1c, the Uber event) Do the unreferenced helpers 0x005DD140, 0x005E9DD0, 0x005F7F10, 0x005FD0F0, the drop 0x005E0070, the death callee 0x005A3250, the preset walk 0x005559A0, Baal's action at `k` 14, `UModAura` and `MonPostCreateBoss` map their declared inputs to the first boundary they reach (or their return), its call site, arguments, the unit seed and the named memory, as [ai/0016](0016-uber-event.md) § 7 reads them?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (unchanged), lane project copy `workspace/ghidra-r52n` (symbols replayed from `re/symbols.csv`; emulation does not use them), heap 3 GB, the runs in sequence inside one `systemd-run --user --scope -p MemoryMax=4G`, one Ghidra at a time. No wine, no slot. Models and case writer `tools/ai_uber_emu.py`, its run copy `emu/ai_uber_emu.py.rev` (`6049fb90…`), every draw from `random.Random("r52n-<family>")`. Files in `workspace/logs/r52n/emu/`, `manifest.sha256` (`04983652…`, 42 lines, `check.txt` `d3c307f4…`); `sha256sum -c manifest.sha256` from that directory passes. Development run `emu/dev-1/` (own manifest, 42 lines, tool copy `ai_uber_emu.py.dev1`): `result=FAIL` on one unaccounted static read in each of two families (the `UNIT_GetSizeX` jump table, 0x00620521 → 0x00620580), all cases matching; its cases differ from the kept run's in `presets` only, the generator raised to separate `pass` and `cnt` (7 and 7 cases there, 30 and 21 here).
- **Procedure:**
  ```
  D=workspace/logs/r52n/emu
  python3 -I tools/ai_uber_emu.py cases --dir $D
  export GHIDRA_PROJ_DIR=workspace/ghidra-r52n GHIDRA_HEADLESS_MAXMEM=3G
  systemd-run --user --scope -p MemoryMax=4G bash -c 'for f in ucount dhole umin bmin drop qdeath presets bact14 aura postc; do
    tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err; done'
  python3 -I tools/ai_uber_emu.py check --dir $D > $D/check.txt
  (cd $D && sha256sum *.cases *.mem *.out *.err check.txt ai_uber_emu.py.rev > manifest.sha256)
  ```
  Each case writes the image the tool's docstring declares; the memory spec observes the boundaries and guards the allocator and fatal entries.
- **Observed** (`check.txt`):
  ```
  AI52N ucount cases=240 match=240 bad=0 stopped=0 traced=0 accounted=1 cmp_separating=21 cmp_passed=0 cls_separating=7 cls_passed=0
  AI52N dhole cases=240 match=240 bad=0 stopped=0 traced=0 boundaries=2
  AI52N umin cases=240 match=240 drew=240 lo3_separating=210 lo3_passed=0
  AI52N bmin cases=240 match=240 drew=240 lo3_separating=114 lo3_passed=0
  AI52N drop cases=240 match=240 cls_separating=49 cls_passed=0 boundaries=3
  AI52N qdeath cases=1469 match=1469 accounted=341 boundaries=9
  AI52N presets cases=240 match=240 pass_separating=30 pass_passed=0 cnt_separating=21 cnt_passed=0 boundaries=4
  AI52N bact14 cases=240 match=240 accounted=2 b709_separating=87 b709_passed=0 boundaries=2
  AI52N aura cases=240 match=240 accounted=32 boundaries=3
  AI52N postc cases=240 match=240 accounted=10 base_separating=124 base_passed=0 boundaries=10
  AI52N total cases=3629 match=3629
  AI52N result=ok
    ARM 005e0070 classes 704,705,709
  ```
  Trimmed; every family's `site_control_passed=0`, `bad=0`, `stopped=0`, `traced=0`.
- **Conclusion:** [C] the maps of ai/0016 §§ 3, 5, 6, 7, each ending at its first callee or return (ADR-0021). Not the callees, not reach, nothing after a boundary; `qdeath`'s tables come from the image. No symbol raise (ADR-0015 scope, review-fixes rule 14). (run:2026-11-03-ai-uber, fn:sub_005A3250_UModQuestCompleteDeath@0x005A3250)

## run:2026-11-04-ai-wp

- **Question:** (plan 0052 Phase 2, `lane/p52d`, step B; the waypoint entry `2026-11-04-architect-reverser-plan-0052-waypoint-list-and-pinned-seed-rerun`) why does `tools/d2pilot.py wp` give up on the Act IV start, and does a fix hold in a kept batch?
- **Setup:** slot 1 (display `:8`, `workspace/wineprefix-1`), the case `wp-probe` of `tools/ai_sessions.py` (Jail Level 1 by the waypoint, 10 s of Nova; `tools/gdb/ai-g4.gdb`), `run --fresh`, character `CombatSor`, one game process per launch, no rerun. Tools: before, the working tree of `lane/p52d` at `9412f1c1` with a trace added to `wp_travel` (the dark share of the list's panel and the player's position, no change of behaviour); after, `wp_click_until_open` (`tools/d2pilot.py`, test `tools/test_d2pilot_wp.py`). Logs `workspace/logs/ai/dev-p52d-wp-*`, `dev-p52d-wp2-*`, `dev-p52d-wp3-*` (launch logs, `.marks.tsv`, `.pilot.txt`, shots; development logs).
- **Observed, before:** 12 launches (6 in `dev-p52d-wp`, 6 in `dev-p52d-wp2`), **4 failed** (seeds 7001 and 7006 of `-wp`, which carried no share trace, and two of `-wp2`): `wp: no level change`, then two attempts with `did not open`; the two of `-wp2` print `wp: list seen at 0.0 s, dark share 1.00, player (5048, 5043)` first. The 4 launches of `-wp2` that held show the panel at share 0.13 to 0.17 until the player stands at (5045, 5022) and 0.96 at 2.3 to 2.5 s after the click.
- **Cause:** [I] (run:2026-11-04-ai-wp; `tools/d2pilot.py` `Pilot.menu_open`, `wp_travel`) the list is recognised by a panel that is more than 75 % dark, and the screen is black at the first click of a game in 4 of 12 launches (share 1.00 at 0.0 s), (share measured in 2 of those 4, the 2 of `-wp2`; `-wp` carried no trace; corrected at the review, 2026-11-04), so `menu_open()` was true before the character had left (5048, 5043); the tab click (y 73) and the row click (230, 133) went to the ground and the character walked up-left (north 4 to 9 sub-tiles, then west: the logged tracks of seeds 7001 and 7006), the list never opened, and the outer retry of `tools/ai_sessions.py` moved its click by the distance walked, away from the waypoint. The first reading, that the character was still walking or the object not yet targetable, is not what the traces show: the character walks to the waypoint in 2.3 to 2.5 s after a click on a lit screen (the old "menu after 3.7 s" included the 0.6 s sleep and the tab clicks). Of the 6 launches with the trace the 2 failing ones had the black screen at the click and the 4 holding ones none (share 0.13 to 0.17 before the list), so it separates them in that sample; the 2 failures of `-wp` show the same walk (north, then west) without the number; why the black lasts to the click (the fade-in of the load) is not examined; after the fix the first sample before the click is above 0.5 in all 12 probe launches and in 12 of the 18 kept ones (`lit after` 0.0 in 6), so "a third of the launches" is the old rule's click timing, not how often the screen starts dark.
- **Fix:** `wp_click_until_open`: wait until the panel's share is 0.5 or less (20 s at most, no click into a black screen), click, count the list as open when two samples 0.3 s apart are above 0.75, click again in the same process after 8 s when the player stood still (one more wait when it was still walking). No new process.
- **Observed, after:** `dev-p52d-wp3`, 12 launches, **0 failed** (`wp: list open 2.5 to 2.7 s after click 1`, screen lit after 0.2 to 0.6 s, level 103 to 29 after 5.7 to 6.7 s). All 12 opened at click 1, so the before/after is no effect of a retry (review, 2026-11-04). Control: the fake-pilot tests replay the black start (the old rule takes it for the list), a lit start, a lost first click, a slow walk and a screen that never lights. The Done-when's number (below 1 launch in 10) is judged on the kept batch of `run:2026-11-04-ai-r5`, below.

## run:2026-11-04-ai-r5

- **Question:** (plan 0052 Phase 2, `lane/p52d`, step C; the `lane/p52c` review's order 1 to 5) the kept batch on logger rev 5: does the rev 5 logger hold at the first boundary; which thin tier rows reach 50 decisions; what do `/players 8` and the Countess add; how many of H1's 331 gaps close with both loggers?
- **Predictions, committed before the first log of this run exists** (what each outcome would mean is in the finding, ai/0018):
  1. Far Oasis (`a2-oasis`, seeds 5201 and 5301, one fresh process each): both logs say `AI logger armed rev 5`; 0 first-boundary mismatches; 0 `AIB` lines between a decision's `MSM0` and `MSM1`; Scarab (row 20) 50 or more decisions in the two logs together (the rev 3 runs on these seeds gave 85 and 95).
  2. `/players 8`: `a1-andariel-p8` gives Andariel (row 34) at least 41 more decisions (50 in the rev 5 logs) and fewer than 20 chained pairs; `a3-flayer-p8` gives Fetish (row 30) 20 or more chained pairs.
  3. Thin rows (rev 5 logs only): Vampire reaches 50, CorruptArcher reaches 50; BatDemon, GreaterMummy and BloodLord are each more likely than not to stay short in the stages named for them.
  4. State 13: at least one decision with state 13 in `a1-countess`, with no breakpoint write; no `AI_P1B2`. If none, the record says what the window held (levels, difficulty, caps), and the absence is `[C]` for that window only.
  5. H1 under both loggers: fewer than half of the 331 gaps close; the rest stay for a named reason (a decision of the AI is not in the window, or an unlogged input).
  6. Waypoint: 0 launches of the batch stay in the town (the 12 probe launches after the fix gave 0).
  7. Row 23 (`s-barb-flayer`, `s-barb-oasis`): any `AIL` line with `pend` 0 settles the 600-call limit's part of cluster F; none leaves it `[I]`.
- **Rules held to:** no breakpoint writes game memory or registers (rule 17); the promotion rule of the `lane/p52c` review for rows past the first boundary (0 mismatches, at least 50 resumed decisions with no unknown-value branch by `tools/ai_resume_flip.py`'s census, at least one call past the first, every two-way site failing at least one decision alone); every launch here runs under `-ns`, the launcher's default. run:2026-11-04-sound-pair found the game seed's stream the same with and without sound for one scripted Harrogath walk, which does not cover these stages, so that sound leaves an AI decision unchanged is assumed here, not tested (wording corrected at the review, 2026-11-04).
- **Result of run:2026-11-04-ai-r5** (the predictions above, as found; details in ai/0018): (1) held in part: Scarab 205 decisions, but the first rev 5 logs showed 36 first-boundary mismatches (a logger fault, rev 6 fixes it, `e1fd1181`), then 0 over 321 decisions on the same seeds; 0 `AIB` between `MSM0` and `MSM1` in closed spans. (2) wrong: Andariel 42 decisions and 2 chained pairs, Fetish 15 decisions and 11 pairs at `/players 8`. (3) Vampire, CorruptArcher held; BatDemon reached 215 (the prediction said short); GreaterMummy 35 and BloodLord 16 stayed short. (4) not met: two Countess launches, states 0 only (the descent stopped at levels 24 and 23). (5) H1: not walkable, 0 of 42 gaps closed by the span rule, 187 of 244 decision exits are 0 steps from the next observation. (6) 0 launches stayed in the town, 5 first attempts failed to open the list (a hover reading, not tested) and the runner's retry opened it. (7) no `AIL` with `pend` 0 in 334 `AIL` lines of the 17 logs (396 of 18; 2 of them row 23's), so the 600-call limit's part of cluster F stays `[I]`; row 23 has 256 resumed decisions and 0 mismatches. Checks: first boundary 6 524 decisions, 0 mismatches, controls fail as required; resumed 6 438, 0 mismatches, 86 stopped; promotion rule met by rows 28, 29, 35, not by 20 (one two-way site fails none), under the floor for 22, 34, 125. Manifests: `workspace/logs/ai/manifest-run-2026-11-04-ai-r5.sha256` (80 lines, with the development rev 5 logs, shots, checks), `workspace/logs/skills/manifest-2026-11-04-h1.sha256` (49). Commands: `ai_sessions.py run --fresh … --saves workspace/logs/ai/saves-owner` (`--seed` 5201, 5301, 5401, 5501, 5601, 5801, 5701, 5901), `ai.py check --controls`, `ai_resume.py check --controls --examples 200`, `ai_resume_flip.py check --rows 20,22,28,29,34,35,125`, `ai_r5_scan.py`, `skills_sessions.py run --gdb tools/gdb/ai-skills.gdb ass-3 ass-1 amaj-3 sor-1 amaj-1 sor-3`, `ai_h1.py`. The waypoint failure rate: 12 of 12 probe launches after the fix (run:2026-11-04-ai-wp), and in the kept batch 5 first attempts of the 18 launches failed, 0 launches stayed in the town. Slot 1 only; `-ns` as stated above. **Corrected or added at the review, 2026-11-04:** the 3 first attempts are 5; (5)'s "0 of 42" is retired, below in run:2026-11-04-h1; (2) and (3): with the rev 4 logs the order counts, Andariel 51 and GreaterMummy 62 decisions.
- **Cases (ADR-0028 item 1; every case a fresh process, position 1; review, 2026-11-04):** `a2-oasis` `…-5201-L1` and `…-5301-L1`; `s-barb-flayer` `…-5401-L1`; `s-barb-oasis` `…-5501-L1`; `a1-andariel-p8` `…-5601-L1`; `a3-flayer-p8` `…-5602-L2`; `a2-halls-long` `…-5701-L1`; `a4-cotd-long` `…-5702-L2`; `a1-cloister-2` `…-5703-L3`; `a1-marsh` `…-5704-L4`; `a5-crystal` `…-5705-L5`; `a5-glacial` `…-5706-L6`; `a3-travincal` `…-5707-L7`; `a2-arcane` `…-5708-L8`; `a1-countess` `…-5801-L1` and `…-5901-L1`; `s-necro-curse` `…-5802-L2`; `s-barb-howl` `…-5803-L3` (stem `2026-11-04-ai-r5-s1`, seed in the stem). No piece was split. **Run and not kept:** `dev-rev5` `a2-oasis` on 5201 and 5301 (rev 5, stopped at the mismatches; logs kept); `dev-rev5` `s-barb-flayer` and `s-barb-oasis`, 4 launches (5401, 5402, 5501, 5502), failed in under a second on a save path that held no `.d2s`, marks only, no log.
- **Review recheck** (`lane/p52d` Tier A review, 2026-11-04, no game, `workspace/logs/ai/review-p52d/`, `manifest.sha256`): `ai.py check --controls`, `ai_resume.py check --controls --examples 200` and `ai_resume_flip.py check --rows 20,22,28,29,34,35,125` over the 17 logs are byte-identical to the kept `r5/` files at the head; `ai.py check --controls` over the 21 rev 4 logs is byte-identical to `check-run-2026-11-03-ai-3.txt`; `ai_resume.py` over the 2 rev 5 logs in `resume-dev-rev5.txt`; `ai.py check` over 5901 in `check-5901.txt`; the fork census in `census.txt` (`census.py`, kept beside it); `ai_resume_flip.py check <the 21 and the 17> --rows 22,34,125` in `flip-union-22-34-125.txt`; the chain sum in `chain-sum.txt`. `manifest-dev-p52d-wp.sha256` adds the probe logs and the 4 dev-rev5 files no manifest listed.

## run:2026-11-04-h1

- **Question:** (plan 0052 H1, `lane/p52d`) with the AI logger loaded beside the skills logger, how many of the 331 monster gaps of run:2026-10-25-skills and run:2026-10-27-skills close, and why not the rest?
- **Setup:** slot 1, `tools/skills_sessions.py run --gdb tools/gdb/ai-skills.gdb` on 6 of the 21 sessions that hold the gaps (ass-3, ass-1, amaj-3, sor-1, amaj-1, sor-3; the saves of the earlier runs, rebuilt bit-identically for the sessions' recipes), logger `tools/gdb/ai-skills.gdb` (`ai.py` rev 6 and `skills.py`). Logs `workspace/logs/skills/2026-11-04-h1-*.log`, manifest `manifest-2026-11-04-h1.sha256` (49 lines).
- **Procedure:** `tools/skills.py check LOG --gaps h1/gaps-N.txt` (the gap walk takes a monster's `AID`..`AIX` as a seed-carrying span), the control with that rule removed (`h1/noai-gaps-N.txt`), `tools/ai_h1.py LOG...` (`h1/h1-steps.txt`).
- **Result:** 49 monster gaps in the 6 logs (the original runs' logs of the same sessions: 51, 48, 47, 31, 26, 21); the first 4 logs, 42 gaps, closed 0 by the span rule (identical to the control): retired below; 187 of 244 decision exits are 0 steps from the next skill-side observation of the unit, 57 are 1 to 11 steps or farther, 91 decisions have none. The 15 other sessions were not run. Conclusion in ai/0018 § 6.
- **Review correction** (`lane/p52d` Tier A review, 2026-11-04, no game, `workspace/logs/skills/review-p52d/`, `manifest.sha256`): the first form of the span rule compared lines inside the decision with its entry seed, and the two loggers' `n` collided. With both fixed (`tools/skills.py`, tests in `test_skills.py`): `skills.py check LOG --gaps review-p52d/gaps-N.txt` gives **41 of the 49 closed**, 8 left, all at `AD0`; sor-3's 4 `BD.elem` mismatches in the kept check are gone. `ai_h1_close.py new <the 6 first-form lists and logs>` > `close.txt` (rows, resume status), `ai_h1_close.py orig 2026-10-27-skills-gaps.txt 2026-10-27-skills-part1-gaps.txt` > `orig.txt` (the 331 by class and tag). Old logs: `skills.py check` over the 15 `2026-10-27-skills-*.log` outside `-part1`, `main`'s revision against this one, byte-identical check and gap list (`workspace/logs/ai/review-p52d/rerun-skills-lane.txt`, `rerun-gaps-lane.txt`). No game time; run under `-ns` as above.

## run:2026-11-04-ai-t28

- Question: does row 28's block as written in monsters/ai/machinery T28, read from 0x005F4A70–0x005F4FCC at the `lane/s52a` review, give each logged decision's boundary calls and draws?
- Setup: no game. The kept logs of run:2026-11-03-ai-3 (21, rev 4) and run:2026-11-04-ai-r5 (18 files, rev 6: the 17 and the second Countess launch). Tool `tools/ai_t28_check.py`; it imports `tools/ai.py` and `tools/ai_resume.py`'s `top_level` and `bnd_set`.
- Procedure: from `workspace/logs/ai/`: `python3 -I tools/ai_t28_check.py <logs>`, then once for each `--control always-y|b0-first|no-second|byte3`. Output kept: `workspace/logs/ai/review-s52a/t28-check.txt`.
- Observed: `decisions=100 ok=99 mismatches=0 stopped=1` (a return site not armed, 5708-L8). Arms reached: far-wait 13, far-walk 12, in-pair 13, in-walk 4, keep-idle 17, keep-step 2, keep-walk 10, melee-a1 2, melee-idle 1, melee-pair 1, engaged-flee 1, `T56` at 0x005F4E55 17 and at 0x005F4F46 6; `Pair` Skill1 8, Skill4 6. Controls: byte3 fails 23, no-second 2, always-y 1, b0-first 0.
- Conclusion: the block's draw order, `T56`'s three arguments, `v14`, `v18`, `v1C` and the sites hold on those paths with the logged inputs and results as oracles (ADR-0004). Step 2's melee arm, the fleeing arm (`v14` = 2), `Skills` and `T56` at 0x005F4D83 are reached by no log and stay `[I]`; b0-first passes because of that, which is the control's finding. It upgrades [T28c](../../specs/monsters/ai/machinery.md#t28-row-28-vampire-fnsub_005f4a70_aivampire0x005f4a70) only.

## run:2026-11-04-r71-sm

- Question: does row 106's think as written in [ai/0019](0019-row-tables-and-scoring.md) §§ 1.2 to 1.5 give the instructions' callee words, draws, list and control words, and do the tables of rows 94 and 25 equal their rules and stores?
- Setup: no game, no Ghidra. `tools/ai_sm_check.py` (`12bc7d6b…`) over `tools/ai_resume.py`'s interpreter (`187dcaaf…`), the pinned image through objdump; `tools/ai_const_survey.py` (`ffe3ab87…`), gate survey `ai_const`. Cases from `random.Random("r71-sm")`, records synthetic; every callee but RNG_Range a stub returning the case's value.
- Procedure: from the worktree, `python3 -I tools/ai_sm_check.py check --cases 6000 --out workspace/logs/r71/sm-check.txt`; `python3 -I tools/ai_const_survey.py summary|emu|values workspace/install/app/game.exe`, `skills workspace/merged/data/global/excel`, `logs workspace/logs/ai`. Outputs in `workspace/logs/r71/`, `manifest.sha256` (7 lines; `dev-sm-check-1.txt` is the run before six unused control names were removed, same cases, same trace hash).
- Observed: `CASES 6000 mismatches=0 stopped=0 trace_sha256=492df4f5669fd9b1`; `Idle` 4 554, `RunToUnit` 267, return 1 179. 99 one-term controls: 98 fail between 1 and 2 635 cases, `p_hi` 0. 142 conditional branches, 136 both ways, 6 listed. `step_rule_mismatches=0`, `wisp_b5_rule_mismatches=0`, `sweep_cells_outside_cases=1`, `wisp_stores=132`, `emu_differences=0`. Logs: 160 files, 0 `AID` lines of rows 25, 94, 106, 143, 1 530 of row 2.
- Conclusion: the pseudocode and the instructions are the same map from the declared returns. Not ADR-0015's emulator and not logged returns, so the reading stays `[I]`. It says nothing of what the callees return in play or of what the offsets' columns mean. The tables' equalities are `[C]` on the image's elements only (ADR-0031).

