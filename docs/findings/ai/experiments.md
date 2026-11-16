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
- **Plan and seeds.** `PathPlan`: 9 934 entries inside decisions (types 2, 5, 6, 7, 13, 15 observed, 148/217/203/1 961/5 825/1 580, `PLANTYPES`),
  9 618 of them entry/exit pairs (`pp_pairs`), 0 with a changed unit seed; the other 316 have no exit line. Seed accounting: every logged point of every decision (entry, think
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

- **Addendum 2026-11-10: plan 0066 batch S1d** (`lane/n66d`): first-boundary hand maps over this run's 31 case logs with the other three runs' (R11, R15, R23, R26, R48, R49, R56, R96, R99, R100, R130); the record and counts are under [run:2026-11-04-r72](#run2026-11-04-r72).

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
- **Addendum 2026-11-10: plan 0066 batch S1d** (`lane/n66d`): first-boundary hand maps over this run's 21 case logs with the other three runs' (R15, R23, R26, R96, R99, R100); the record and counts are under [run:2026-11-04-r72](#run2026-11-04-r72).

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
- **Addendum 2026-11-10: plan 0066 batch S1a** (`lane/n66a`, static, no game; tools at `2172cedd`: `tools/ai_resume_flip.py` sha256 `98484cb5…281e`, `tools/ai_move_refusal.py` `d31d1fb7…39d1`). The 21 rev 4 case logs of run:2026-11-03-ai-3 and the 17 rev 6 launch logs of this run (the second Countess launch left out, as in `resume-run-2026-11-04-ai-r5.txt`), 38 in all, listed in `workspace/logs/ai/sweep2-s1a/logs.txt`. Outputs in `workspace/logs/ai/sweep2-s1a/`, `manifest.sha256` (passes from that directory); the inputs (the 38 logs, both `resume-run` files, `review-p52c/flip-rows-full.txt`) in `workspace/logs/ai/manifest-sweep2-s1a-inputs.sha256` (passes from `workspace/logs/ai`).
  - **Procedure** (from `workspace/logs/ai`, each under `systemd-run --user --scope -p MemoryMax=4G`): `ai_resume_flip.py check <38 logs> --rows 3,4,5,15,23,52,63,65,68,70,78,79,96,118 --key rowthink --cap 1000000` (`flip-s1a-rows.txt`); `ai_resume_flip.py check <38 logs> --key think --thinks 5e8140,5e8340 --cap 1000000` (`flip-s1a-states.txt`); `ai_move_refusal.py <38 logs>` (`move-refusal.txt`). `--key` groups a row's decisions by its own think (`rowthink`) or a state row's decisions by think across rows (`think`); the default output is unchanged: rows 13 and 21 on the rev 4 logs give `review-p52c/flip-rows-full.txt`'s lines byte for byte (`flip-reg-13-21.txt`). Every resumed decision is flipped (no sample). Mismatch counts: the `RROW` lines of both `resume-run` files (`rrow-s1a.txt`).
  - [C] (run:2026-11-04-ai-r5, run:2026-11-04-ai-resume, `flip-s1a-rows.txt`, `flip-s1a-states.txt`, 0x005B186F) **Sentence H1's rule is met** (0 mismatches, at least 50 resumed decisions with no unknown-value branch, at least one call past the first, every two-way site of those decisions failing at least one decision alone) **by these thinks, over their fork-free decisions:** row 3 (0x005EFE20) 136 decisions (rev 4), 381 calls past the first, two-way sites 4 of 4; row 4 (0x005EFF50) 353 (342 and 11), 740, 7 of 7; row 5 (0x005F00E0) 271 of 272 resumed (1 stopped), 251, 6 of 6; row 15's think 0x005F1800 107 (62 and 45), 167, 9 of 9; row 52 (0x005F8260) 400 (rev 4), 406, 1 of 1; row 63 (0x005F9490) 54 (rev 4), 147 in 49 decisions, 10 of 10; row 65 (0x005F9A80) 89 (27 and 62), 370, 5 of 5; row 68 (0x005FA010) 79 (rev 4), 259, 6 of 6; row 96 (0x005E1250) 117 of 118 resumed (1 stopped), 264, 10 of 10; state think 0x005E8340 (S12) 56 (rev 4; rows 37 and 64), 230, 3 of 3; state think 0x005E8140 (S11) 66 of its 134 (rows 12 and 64), 66, the one two-way site among the 3 of the subset. In each of these decisions no branch the model ran depended on an unknown value; with the logged inputs and the logged results of the boundary calls as oracles, the game's code gives exactly one sequence of boundary calls, equal to the logged one in callee, call site and every word the model knows, and the code then returns with no further call. Logged paths only; no role, symbol or catalogue reading is raised. S12's 52 row 37 decisions are inside row 37's 81 of README H1 by row; here they are counted by think.
  - [I] (`flip-s1a-rows.txt`, `flip-s1a-states.txt`, `FUNK` lines) **Not met:** row 23 (0x005F3170): 8 mismatches in the rev 4 logs (cluster F), 500 of 679 resumed decisions fork-free, two-way sites 24 of 25: 0x005F356C fails none of its 21 decisions alone (it changes the call only when the y words compared at 0x005F356E are equal); the 179 others branch at 0x005F33F4 on 0x0064E7B0's return. Row 70 (0x005FA380): 0 of 154 fork-free, every decision branches at 0x005FA3C1 and 0x005FA3E5 on the words `+0x32`/`+0x34` through `ESI`. Row 118 (0x005E1E00): 0 of 56, every decision branches at 0x005E1E36 on the return of 0x00625760, not a boundary. Row 78 (0x005FB6C0): 66 of 199 fork-free with 0 calls past the first; the rest branch at 0x005FB71C/0x005FB723 on a point read through 0x00620870. Row 79 (0x005FB7E0): 18 of 53 fork-free, 0 calls past the first; the rest branch at 0x005FB83C/0x005FB843. S11's other 68 branch at 0x005E81E1, 0x005E81F5 and 0x005E8201 on the words read at 0x005E81DA. The catalogue `r` lines' "an unknown value deciding N of M later steps" counts calls with several offers, not branch steps: rows 70 and 118 read "0" there and fork in every decision.
  - [C] (run:2026-11-04-ai-r5, run:2026-11-03-ai-3, `move-refusal.txt`, 0x005DEBCC, 0x005DEC0F, 0x005DEC3F) **After a refused `MonAiMove` command** (`MSM0` at return address 0x005DEBCC, its `MSM1` `eax` 0), by the helper's logged words: `MonAiWalkToUnit` with word 0 (44, rows 6 and 96), `MonAiWanderRing` (59) and `MonAiStepAway` with its third word 0 (16) or non-zero (255) return 0 with the unit's seed 0 steps from `MSM1` to the helper's `AIR` and no further `MSM0` in the call. The draw at 0x005DEC15, had it been taken, would have sent 255 of these 374 to the ring (low word mod 100 below 70) and 119 to the idle, so a drawing reading fails every one. `MonAiWalkToUnit` with word 7 (143, eleven rows) returns 1 with 1 step and no further command in the 47 whose step's low word mod 100 is 70 or more, and with 5 steps and the ring's own `MonAiMove` command in the 96 below 70: 143 of 143. The flags each helper passes are read from the code, `[I]`: `MonAiWalkToUnit` its second word (0x005DEC83), `MonAiStepAway` 4 or 0 (0x005DF105..0x005DF112), `MonAiWanderRing` 0 (0x005DE2F8). Calls whose `MSM1` was not logged (the 600-call limit) are left out (`nomsm1`, 40 for these three helpers).
  - [I] (`move-refusal.txt`, 0x005DEBE8, 0x005DEC60) **Not told apart by these logs:** `MonAiWalkToUnit` with word 1 (no case); whether a flags-0 refusal idles (`MonAiIdle` inside `MonAiMove` writes no logged line; the next decision came 15 frames later in all 111 flags-0 refusals with a next decision, where the 1-step idle side of word 7 shows 10 in 22 of 34, which is not a modelled observable); flag 1's `AiCtl+0x08` bit `0x40` (the `AID` `ctl` word is read after the search that clears it: 0 of the 113 word 7 refusals with a next decision show it); and which of bits 1 and 2 brings the draw (word 7 sets both, and no case has one alone).
- **Addendum 2026-11-10: plan 0066 batch S1b** (`lane/n66c`, static, no game; tools at `f2373e64`: `tools/ai_model_check.py` sha256 `20ace4d7…8ee7`, its test `tools/test_ai_model_check.py` `932b6db4…5edc`). The same 38 logs as S1a (`workspace/logs/ai/sweep2-s1b/logs.txt`, the inputs hashed in `manifest-sweep2-s1a-inputs.sha256`). Outputs in `workspace/logs/ai/sweep2-s1b/` (`model-check.txt`, `test-output.txt`), `manifest.sha256` (passes from that directory).
  - **Procedure** (from `workspace/logs/ai`, under `systemd-run --user --scope -p MemoryMax=4G`): `ai_model_check.py check --logs sweep2-s1b/logs.txt --out sweep2-s1b/model-check.txt`. The tool holds one model per catalogue entry, each the entry's pseudocode block transcribed from the spec text at `b5999f5e` (not from `ai_resume.py`'s interpreter, not from a decompile). Each logged decision of the entry's think runs through its model: the AID words are the inputs; at each call of a logged boundary function the model's callee, the argument words the block names (a convention table, `CONV`, gives their registers and stack places), the unit seed after the model's own draws, the control words `v14`, `v18`, `v1C` after its own stores, `Unit+0xC4` and, for searches and `MonHelpBlock`, the words of the block the pointer argument addresses, are compared with the next logged call; the logged return (`EAX`, the seed, the control words, `+0xC4`, the output block) then feeds the model (ADR-0004). At the return the logged calls must be used up and the AIX exit seed must equal the model's. A value the log does not hold forks the model (both sides run); forked decisions are counted apart and support no claim. Controls over the fork-free decisions: each branch and each store reversed or skipped alone (`FLIP`; a store also counts as failing when the unit's next decision of the same think logs other control words), `le` and `lecmp` (`<=` for `<` in draws and in other compares), `d0` (the Normal column: all 38 logs are Normal, so it separates nothing), R43's `sdiv`, and the R78/R79 axis swaps (`R78y`, `R79x`). Call sites are not predicted: `SITE` lists the logged sites per block call; no label has two sites except R3's two `SetModeAtUnit` calls (one per mode, 0x005EFE93 and 0x005EFEA9) and R23's loop test (0x005F3543 first, 0x005F3582 after), and the shared sites are identical calls of one block (R4's `SetModeAtUnit(5, t)` at 0x005F003E, R70's `UseSkill1(t)` at 0x005FA458, the idles of R95, R124, R130).
  - **The rule applied** (the batch's method, inventory § 4): a block's step is raised where the fork-free decisions take it, with 0 mismatches over all the entry's decisions, at least 30 fork-free decisions, and every branch and store on the step failing at least one decision when reversed alone. The `<` of a compare against `≤` is raised only where `EDGE` counts an equal pair. Untaken arms, arms behind a fork, and non-boundary calls (`DelayE`, `MonAiMoveToUnitDist`, `UnitGetPos`, the `MonsterData`/MonStats reads) stay inferred. A row whose block has any such remainder is "raised in part". Positions: R43's cell test, R63's point and R78/R79's axis test use the AID line's `x`, `y` and the target's `x`, `y` (the logger's own words) for `U.x`, `U.y`, `t.x`, `t.y`; the swapped-axis controls fail 123 of 199 (R78y) and 14 of 53 (R79x).
  - [C] (run:2026-11-03-ai-3, run:2026-11-04-ai-r5, `model-check.txt`, 0x005B186F) **Met, on the logged paths named** (entry: decisions, fork-free, calls past the first; mismatches 0 in each):
    - R3 (0x005EFE20) 136, 136, 381: in melee range A1 or A2 on `chance(4)` (3 and 2); otherwise `St3or19` 0 in all 131, the `dist < aip(2)` test both ways (3 equal pairs) with `chance(1)` both ways, then the run (`Ovr(0, 100, 0)`, `RunToUnit(t)`, 12) or the room's level and `Ring(3)` at levels 4, 36, 37 (119).
    - R4 (0x005EFF50) 353, 353, 740: step 1's A2 (1); at or above `aip(1)` life A1 in melee range (51), `Walk(t, 7)` after `FindHostile` with no draw below `aip(3)` (77) or no hostile (9) within 15 (12 equal pairs at 15), and beyond 15 (213); below it (2), not within 3, `WalkStop(t, 6)` beyond 15 (1) and step 6's A2 at `t` (1).
    - R5 (0x005F00E0) 271, 271, 251: the flag's A1 (`v14` 1, in melee range, 21); out of melee range the swoop (`Ovr(0, aip(5), dist)`, `v14 ← 1` seen at the walk, `Walk(t, 0)`, 65), the ring-4 retreat (151) and ring 3 (20) beyond 3; in melee range with `chance(3)` missed, step 4's override and `StepAway(t, 4, 1)`, accepted (13) or refused with A1 (1); `chance(1)`, `(2)`, `(3)` met at equality 5 times (`le` fails 5).
    - R12 (0x005F12A0) 603, 603, 0: every arm of the block, walk 350, idle 108, A1 114, idle 31; both draws met at equality (`le` fails 5); no second draw after the melee miss (exit seed, 31).
    - R15 (0x005F1800) 107, 107, 167: `ph` 0, 1, 2 (never 3), life at or above 25 in all; step 5's A1 (2) and miss (3); step 6's A2 at `h` (14, 2 of them with `h ≠ t`), `hd` the word `FindHostile` wrote (0x7FFFFFFF in the one decision with no hostile); step 7's `T56(t, 6, 0)` (20); step 8's walk with `v14 ← 2` (16, seen at the next decision in 12) and the lay (`v1C + 1`, `v14 ← 1`, `UseSkill3(t)`, 8).
    - R19 (0x005F2460) 122, 122, 0: every arm, walk 60, idle 50, A1 6, idle 6; no equal pair at either draw.
    - R26 (0x005F4510) 46, 46, 91: `v14` 0 or 2 (never 1); out of melee range `St3or19` 0, `v18 = 1` → `Walk13(t, 0)` (15), the `v1C` count (no wrap past 20) with the approach at `v1C = 1` (3), `Ring(6)` (9) or `Idle(15)` (18); in melee range (1) `v14 ← 2`, no A1, life at or above `aip(5)`, `Idle(15)`. The stores `v18 ← 0` and `v18 ← 1` of step 3 separate nothing.
    - R43 (0x005F6650) 32, 32, 8: `Idle(25)` beyond 20 (24); the timer test both ways (4 and 4), `v14 ← T` seen at the cell test, the cell test with class 206 (`ECX`), `U`'s room and position, accepted, `v18 + 1`, `UseSkill1(t)` (4); `Idle(20 + low mod 10)` with an unsigned remainder (3 of 4 lows at or above 2³¹; `sdiv` fails 3).
    - R52 (0x005F8260) 400, 400, 406: `v1C = 0` beyond 12 (6): `UseSkill1(t)` with `x`, `y` 0, `Delay(8)`, `v1C ← 1` seen at the take-off, `TakeOff`; `v1C = 1` at 20 or more (394): `TakeOff`, `Delay(24)`, `v18 + 1` (seen at the next decision in 388). The `Skill2 ≥ 0` test separates nothing.
    - R63 (0x005F9490) 54, 54, 147: the cooldown idle with `v14 ← 0` (5; 49 equal pairs at `0 < v14`, `lecmp` fails 49); `UnitSetPathTargetUnit(U, t)`, the point on the unit's row or column both ways (3 equal pairs), the facing through R63a's map for directions 7 → 31, 40 → 0, 56 → 17 (49); the shot (`UseSkill1(t)`, `v14 ← aip(3)`, 9) and `Idle(aip(4))`, every term of step 5 both ways but `Skill1 ≥ 0`.
    - R65 (0x005F9A80) 89, 89, 370: `n` the skill level (9 or 10, never the default); the breath at `dist < n` (2) with the kind-1 block (`+0x08` 1, `+0x0C` the target's id, `+0x10` its type) and `UseSkill1(t)`; state 12 absent in all; the search with the block R65's step 4 states; a dead found (22): `chance(1)` both ways, `MonSkillTargetOk(Skill3, dead, 0, 0)` both ways, the kind-14 block (`+0x08` 14, `+0x10` 1), `WanderNear(dead, 10)` with `deadD2` 153 to 1170 against `aip(3)` 15 (5); `T56(t, 4, 0)` (53), `Idle(10)` (29).
    - R68 (0x005FA010) 79, 79, 259: the chain position of `U`'s class, the chain step with `ECX` 301 and `EDX` the position; `v14 < aip(1)` and alignment 0 in all; `chance(3)` both ways; the search `{child, 25, 0}`, kind 12, no callback (20); the spawn call `(t, M)` with `M` the MonStats record, accepted with `v14 + 1` (18, seen at the next decision in 12) or refused (2); A1 (5) or `Idle(aip(7))` (3) in melee range; the `D100() ≥ aip(5)` arm's `T56(t, 4, 0)` (5) or `Idle(15)` (12); `Walk(t, 7)` (36).
    - R69 (0x005FA280) 78, 78, 0: every arm, the first event's `v14 ← 1` and `Idle(5)` (18), A1 (4), `Idle(aip(2))` (2), walk (43), `Idle(10)` (11); `chance(3)` met at equality once.
    - R70 (0x005FA380) 154, 154, 481: life, `St3or19` both ways (its arm: not in melee range, `UseSkill1(t)` within `aip(5)`, 1); `v14 ≠ 1` in all; `MonsterOwner` both ways, life at or above `aip(4)` where the owner is 0 (119); in melee range A1 (10), `UseSkill1(t)` on `Range(100) < aip(2)` (1), `T56(t, 5, 0)` (2); at or beyond `aip(5)` `Walk(t, 7)` below `aip(7)` (95); within it `UseSkill1(t)` (25), `Walk(t, 0)` with state 84 on the target (1), `Idle(aip(8))` (19).
    - R78 (0x005FB6C0) 199, 195, 0: `Idle(40)` outside `[aip(1), aip(2)]` (66; 120 equal pairs at `aip(1)`, `lecmp` fails 120), `Idle(30)` with the target more than 2 off the trap's x (127) or with the timer not passed (2).
    - R79 (0x005FB7E0) 53, 39, 0: the same arms on y, `Idle(40)` (18), `Idle(30)` (9 and 12).
    - R95 (0x005E1080) 43, 43, 48: `FindHostile` with `dist` in the frame word, `d` the word it wrote; within 8 no `chance(4)` (5); beyond `aip(6) − 6` `WanderNear(t, 4)` (19); with a hostile within `aip(6)` A1 at `h` (15) or `Idle(aip(5))` (4); the search `{0, 0x7FFFFFFF}` with the callback 0x005B0D00, its unit at or within `aip(3)` (2) or none (3), `Idle(aip(5))`.
    - R96 (0x005E1250) 118, 117, 264 (1 stopped, no AIR): `Head`; a kind-14 record (10): `GameFindUnit(G, +0x10, +0x0C)` found, the clear, `Ovr(13, 50, 0)`, `Walk(u, 0)`, `Pop`; no record (107): beyond `aip(1)` the override and `WanderNear(t, 6)` (38), `dist ≥ 6` to the hunt (58), else `chance(2)` both ways; `FindHostile`; state 0 (60) with `v18 + 1` and the `low mod 3 + 3 < v18` draw both ways, A1 at `h` (56) or `T56(t, 4, 0)` (4); state 1 (4) the clear, `Ovr(0, 50, 0)`, `T56(t, 6, 1)` accepted; state 2 (5) within 13 `Ovr(2, 50, 0)`, `StepAway(t, 14, 1)` accepted (4) or refused with A1 at `h` and the clear (1).
    - R99 (0x005E9F10) 225, 225, 0: `+0xC4 |= 0x20000` before the call (19 decisions tell it); `t` set in all; beyond 5 with `v14` 0, `Idle(15)` (219); within 5 with `v14` 0, `v14 ← 1`, `v18 ← T`, `SetModeAtUnit(9, t)` (6); no draw on either path.
    - R114 (0x005E1540) 31, 31, 28: in melee range `Idle(aip(2))` (3); out of it the approach test both ways, the charge's range test both ways and its draw missed (2), `Walk(t, 0)` (6), `Toward(t, 4, 0)` (15), `Idle(aip(7))` (7). The `+0xC4 |= 0xE` store separates nothing (the bits were set).
    - R124 (0x005E3530) 48, 48, 144: `GetUnitSkill`, the level 4 as the distance (8 within); `chance(3)` both ways, state 12 absent, `UseSkill1(t)` (5); state 12 absent at step 3 (43); A1 (3), `Idle(aip(4))` (2), `WalkZ(t)` (15), `Idle(aip(4))` (23).
    - R130 (0x005EE260) 34, 33, 0 (1 stopped): A1 (4) or `Idle(15)` (1) in melee range; within `aip(3)` the skill (5); `Walk(t, 0)` (18), `Idle(15)` (5).
    - S10 (0x005E8020, in the classes of rows 6, 12, 37 and 64) 632, 621, 0: out of melee range `Ring(3)` on `D100() < 20` (123) or `Idle(10)` (498), 9 equal pairs (`le` fails 9). The 11 melee decisions fork.
    - S11 (0x005E8140) 134, 66, 66: state 56 present, `Idle(10)` beyond the limit, the limit 30 (`v14` 0 in all 66). The other 68 fork on `MonModeAllowed`.
    - S12 (0x005E8340) 56, 56, 230: no target (1): `MonAiInit(ctl, 0)`, `CancelEvents(2, 0)`, `UnitQueueEvent(2, T + 1, 0, 0)`; a target not in a town room (55): `v14 = 0` → `v14 ← 1`, `Walk13(t', 7)` (3); in melee range A1 at `t'` (47); else the search's unit with `m` 0 → `UnitSetPathTargetUnit(U, t')`, `Walk13(t', 7)` (5); no draw.
  - [I] (`model-check.txt`, 0x005B0CD0, 0x005F33EC, 0x005E1E36) **Not met:** R1 (0x005B0CD0): its think lies outside the logger's return-address windows (`THINK_LO`, tools/gdb/ai.py), so its 4 decisions log no call. R23 (0x005F3170): 8 rev 4 decisions end at `UnitGetRoom(t)` at 0x005F33EC with no further logged call (R23d's cluster F), 179 fork on `FreeNearFallback`'s return; on the 500 fork-free decisions the loop's reading "an equal axis is not stepped" matches and "an equal axis steps + 1" fails 1 (`R23x`, `PathDist` at 0x005F3582). R54 (0x005E73A0): all 302 fork on `AiNearestPlayer`. R118 (0x005E1E00): 50 fork on `StatListFindFlag`, 6 stop in the curse arm the tool does not model. R100 (0x005E7F50): 4 decisions, under the floor. The alts of rows 15 (1 decision), 52 and 65 (none), and the inits of rows 43 and state 11 (not think calls) have no decision to compare. `AiVileMotherSpawn`'s interior is inside a boundary call (not logged without `AI_NESTED=1`).
- **Addendum 2026-11-10: plan 0066 batch S1d** (`lane/n66d`): first-boundary hand maps over this run's 17 logs with the other three runs' (R15, R23, R26, R48, R49, R96, R99, R130); the record and counts are under [run:2026-11-04-r72](#run2026-11-04-r72).

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
- Conclusion: the pseudocode and the instructions are the same map from the declared returns. Not ADR-0015's emulator and not logged returns, so the reading stays `[I]`. It says nothing of what the callees return in play or of what the offsets' columns mean. The tables' equalities are `[C]` on the image's elements only (ADR-0031; 0x006E33A0, 0x006E33E0, 0x005F39E1).
- Review addendum, 2026-11-04 (`lane/r71`, architect): the Setup's "every callee but RNG_Range a stub" was wrong: `RNG_Range` is a stub too, stepping the seed with the `Seed` class the model shares, so its range and order are compared and its body is not (corrected in the tool's docstring and ai/0019 § 1.6; the body read at 0x0045C390, its own `[C]` run:2026-10-11-rng-emu). Revisions: `tools/ai_sm_check.py` `26ce09ad…` adds `--minus` and changes no case; `tools/ai_const_survey.py` `c78dfae1…` adds `rulescan`, `reach`, class counts in `logs`, and the doc check (`doc_missing`, `doc_mismatches`, baseline changed in the same commit). From the worktree: `python3 -I tools/ai_sm_check.py check --cases 6000 --minus --out workspace/logs/r71/review/sm-check-minus.txt`; `python3 -I tools/ai_const_survey.py rulescan workspace/install/app/game.exe`, `reach workspace/merged/data/global/excel`, `logs workspace/logs/ai`, each to its `review/` file (`rulescan.txt`, `reach.txt`, `logs-rows.txt`); `workspace/logs/r71/review/manifest.sha256`, 4 lines. Observed: trace `492df4f5669fd9b1`, 0 mismatches, as the kept run; of 84 `-1` controls only `use1_held` fails 0, `p_hi-1` fails 4; `doc_missing=0 doc_mismatches=0`; no form of the rule scan gives `A` or `B` (best 11 of 28 rows; 7 of 28 elements per column); 0 lines of the 13 classes in 160 logs, 64 AI rows present. The doc check was tested by altering one listed value in a copy: it counts 1 mismatch.


## run:2026-11-04-r72

Owner-played (ADR-0028: five processes, each one case; plan 0052 P1b-1 and the Countess). Analysis without a game: [ai/0020](0020-owner-played-duriel-countess.md).

- **Question:** does Duriel's melee choice follow three fresh draws or the community page's 33 : 50 : 17; does row 44 meet the promotion rule; which unit holds state 13, when, and does S13's block give its decisions; what can a late attach not test?
- **Cases** (`workspace/logs/ai/`; each attached late by `tools/d2run.py --attach-file`, `--fullscreen`, `--sound`, `AI_CAP_ROW=2000 AI_CAP_SESSION=8000` for the `ai-g4` logs):

  | Process (stem) | Seed | `.gdb` | Save, recipe | Attached | AID, frames, rows | Note |
  |---|---:|---|---|---|---|---|
  | `owner-ai-duriel-L1` | 3364 | `tools/gdb/ai-g4.gdb` | `saves-owner/AiDur.d2s` | at the orifice | 29, 3772–4110, 44: 9, 61: 20 | the mercenary killed Duriel |
  | `owner-ai-duriel-L2` | 3364 | `tools/gdb/ai-g4.gdb` | `saves-owner/nomerc/AiDur.d2s`, `tools/d2s_recipes/ai-dur-nomerc.json` | at the orifice | 300, 1054–9053, 44: 300 | |
  | `owner-ai-countess-L1` | 5901 | `tools/gdb/ai-g4.gdb` | `saves-owner/nomerc/CombatSor.d2s`, `tools/d2s_recipes/combatsor-nomerc.json` | on arrival, Tower Cellar Level 5 | 42, 2726–2782, 6: 17, 10: 25 | the owner killed her |
  | `owner-ai-countess-L2` | 5901 | `tools/gdb/ai-g4.gdb` | as L1 | on arrival | 71, 1482–1580, 6: 38, 35: 33 | lag stopped them reaching her |
  | `owner-ai-countess-L3` | 5901 | `tools/gdb/ai.gdb`, `AI_RADIUS=40` | as L1 | after the owner cleared the level | 184, 2070–6350, 10: 184 | |

  `dev-owner-ai-duriel-lagged.log` is development only (lag) and in the manifest; no count here rests on it.
- **Procedure** (from `workspace/logs/ai`, `tools/` being the repository's by its path; tools at `a2a78e7c`; `ai_resume`, flip and census under `systemd-run --user --scope -p MemoryMax=4G`):
  ```
  python3 -I tools/ai_duriel_c10.py owner-ai-duriel-L1.log owner-ai-duriel-L2.log > r72/c10-run.txt
  python3 -I tools/ai_resume.py check <the two> --rows 44 --out r72/resume-44.txt
  python3 -I tools/ai_resume_flip.py check <the two> --rows 44 --cap 1000000 --out r72/flip-44.txt
  python3 -I tools/ai_resume.py check owner-ai-countess-L1.log owner-ai-countess-L3.log --rows 10 --out r72/resume-10.txt
  python3 -I tools/ai_resume_flip.py check <those two> --rows 10 --cap 1000000 --out r72/flip-10.txt
  python3 -I tools/ai_s13_check.py <those two>, then --control for each of the 15 (r72/s13-check.txt)
  python3 -I tools/ai_s13_check.py --r10 [two-draws] <those two> (r72/r10-check.txt)
  python3 -I tools/ai_s13_census.py --ds1 <merged>/data/global/tiles/act1/crypt/cryptcountess1.ds1 --skills 357 <those two> > r72/s13-census.txt
  python3 -I tools/ai_owner_fields.py <the five and the dev log>; --scan <the logger's files>; --setters game.exe (r72/fields.txt)
  python3 -I tools/ai.py check <the two>, <the three> --out r72/check-duriel.txt, r72/check-countess.txt
  ```
- **Outputs:** `manifest-r72.sha256`, 22 lines, passes from `workspace/logs/ai`: the five raw logs, the dev log, the first checks `owner-dur-check/check-first.txt` and `check-countess-first.txt`, the three saves used, and 11 outputs. The reruns of `tools/ai.py check` equal the first checks.
- **Rule 17:** no line of the logger's files writes to the game (`fields.txt` `SCAN`; the one hit is a comment).
- **Result, Duriel:** 309 decisions, 308 melee (L1 9, L2 299), Smite 102, Jab 116, A1 90; exact intervals exclude the page's 50 and 17 and contain the code's values; power at 300, on A1, 0.999998; replay 308 of 308 by arm, seed at the call and exit; six other readings fail 90 to 234. Resume: 309, 0 mismatches, 619 calls, 310 past the first; flip: 309 of 309 fork-free, 3 of 3 two-way sites failing alone: the promotion rule is met.
- **Result, state 13:** 160 decisions, one unit per process, no unit with two states; block check 160 of 160, 0 mismatches, 158 chained pairs; arms and controls in ai/0020 §§ 2.2, 2.3; the four fire points equal the DS1's one path at (12500, 11000); stock census 1 of 160 fork-free, with the three given words 160 of 160, 1 148 calls with one offer, 7 of 7.
- **Result, row 10's state 0:** 49, 0 mismatches, 0 fork-free, control `two-draws` fails 28.
- **Limits:** Normal only; player and, for 9, mercenary as target; first logged decisions not first decisions (ai/0020 § 3); no `AGM`; no chain between Duriel's decisions (1 pair).
- **Conclusion:** [C] C10's contradiction is settled for record 211, Normal, and row 44's sentence holds for these 309; [C] S13's block on its reached arms, its path list against the file; [I] everything else in ai/0020's lists. (0x005F6861, 0x005E5C02)
- Review addendum, 2026-11-04 (`lane/r72`, architect): reran `ai_resume` and `ai_resume_flip` on row 44 and `ai_duriel_c10`, `ai_s13_check`, `ai_s13_census`: byte-identical to the kept outputs (the census also after its control flags were added, `review/census-rerun.txt`). New, from `workspace/logs/ai`, `G` the repository's `tools/gdb`: `python3 -I tools/ai_r72_review.py . <merged>/data/global/excel <merged>/data/global/tiles/act1/crypt G > r72/review/review.txt`, and `python3 -I tools/ai_s13_census.py --ds1 <merged>/data/global/tiles/act1/crypt/cryptcountess1.ds1 --skills 357 [--count 3 | --count 5 | --skills 321 | --skills 322 | --base-delta 0x1A8 | --base-delta 2] <the two countess logs>` to `r72/review/census-count3.txt`, `-count5`, `-skills321`, `-skills322`, `-basedelta0x1A8`, `-basedelta2`, and `--ds1 …/cryptcountess2.ds1` to `census-file2.txt`, under the scope. `manifest-r72-review.sha256`, 9 lines, passes from `workspace/logs/ai`. Observed: the numbers of ai/0020's review text (player-only tally, `CHAIN`, `STATES`, `DS1`, `OFFSET`, `P12`, the words' controls). **Corrected:** rule 17's scan had left out `tools/gdb/ai-p1b2.py`, which `ai-g4.gdb` sources; `P12` lines 0 in all logs. Distinct outcomes (ADR-0028 (7)): row 44's first boundary 1, 4 paths past it; state 13's first boundary 1, 6 paths past it; `tools/ai.py` has no model of row 10 (`ROW 10` `unmodelled=209`).
- **Addendum 2026-11-10: plan 0066 batch S1c** (`lane/n66d`, static, no game; tools at `cd663109`: `tools/ai_model_check.py` revision 2, sha256 `de9bb5ed…bc83`, its test `tools/test_ai_model_check.py` `932b6db4…5edc` unchanged). The S1b block-model checker (addendum S1b under [run:2026-11-04-ai-r5](#run2026-11-04-ai-r5)), extended with R44's and S13's blocks transcribed from the spec text at `b5999f5e` (`tools/ai_s13_check.py` and `tools/ai_duriel_c10.py` were the patterns, not the source), over the five owner-played logs of this run (`sweep2-s1cd/logs-s1c.txt`). Output `workspace/logs/ai/sweep2-s1cd/s1c-model-check.txt` (`fb54d78f…99b5`, 100 lines) under `sweep2-s1cd/manifest.sha256` (passes from that directory); the inputs in `workspace/logs/ai/manifest-sweep2-s1cd-inputs.sha256` (74 logs, passes from `workspace/logs/ai`). Revision 2 leaves revision 1's entries alone: `--rows` with S1b's 32 names reproduces `sweep2-s1b/model-check.txt` byte for byte.
  - **Procedure** (from `workspace/logs/ai`, under `systemd-run --user --scope -p MemoryMax=3G`): `ai_model_check.py check --logs sweep2-s1cd/logs-s1c.txt --rows R44,S13 --out sweep2-s1cd/s1c-model-check.txt`. Method, rule and controls as S1b's. The calls added to `CONV` take the words `ai_s13_check.py` compares (`ParamsFind`: `ECX` U, `EDX` 10, 0; `LogicRegionId` (room, x, y); `PathOvrSet`: `EDX` 1, (0, 0); `RunToPoint` (x, y)) and `GetRightSkill(U)` on the stack, as logged. R44's grant is modelled as its two calls (`UnitSkillAdd`, `PlayerSetSkill`, both in the logger's BND), their words not compared. S13's path count is a given word per unit, the highest fired index + 1 read from the logged fires (`v14` at each `MonAiUseSkill` call: README H1b's given words, taken as `ai_s13_check.py` takes them), so `v14 < count` is tested only against it, its 138 equal pairs are made by that word and separate nothing, and the points' x, y are not compared.
  - [C] (run:2026-11-04-r72, `s1c-model-check.txt`, 0x005B186F) **Met, on the logged paths named**, 0 mismatches:
    - R44 (0x005F67B0) 309 decisions, 309 fork-free, 619 calls, 310 past the first. Step 1: `Skill4` 114 ≥ 0 and `GetRightSkill(U)` non-zero in all 309, so no grant; each test reversed alone fails 309 of 309. Not in melee range (1): `Skill1` ≥ 0, one draw against `aip(5)` (0) missed, then `Ovr(13, 0, 0)` and `Walk(t, 7)`; the melee test and the draw each fail it alone, and the exit seed holds the draw. In melee range (308): `UseSkill3(t)` (102), `UseSkill2(t)` (116), `SetModeAtUnit(4, t)` after the third draw missed (90); each branch fails alone (308, 206, 90 decisions), and the draws meet an equal pair 5 times (`le` fails 5). `NEXT`: no store; the control words equal at all 307 next decisions.
    - S13 (0x005E5C50) 160 decisions, 160 fork-free, 1 148 calls, 988 past the first. `M` and the room present; `ParamsFind(U, 10, 0)` returns the logged head, its words non-zero; home's and U's regions equal in all 160; the target's region differs once, U not at home, RunHome accepted (`PathOvrSet`, `RunToPoint(home)`, 1); otherwise `AiPathDistToPoint` ≤ 40 (values 0 to 29, 159); `AiPathSkillStep` fires (21: mode 4, `Skill1` 321, `v14 + 1` and `v18 ← T`, each store seen at the next decision in 21 of 21), resets `v14` at gaps over 700 (5), else falls through (133); then `Range(100)` and melee A1 (97), melee `Idle(aip(2))` (8), far `Ovr(0, 100, 0)`, `RunToUnit(t)` (28), far `Idle(aip(2))` (5). Every branch and store on these paths fails alone (the melee test 126 of 138, the others all of theirs) but step 2's two tests (the record found, its words non-zero), whose flips stop in 160 of 160 at the push and refill the model does not hold, so they stay `[I]` (review fix); one draw at an equal pair (`le` fails 1). The arms and counts are S13d's (`ai_s13_check.py`), reached by a second transcription.
  - [I] **Not separated:** R44's grant (`GetRightSkill` 0) and `Skill4 < 0`; the true sides of `chance(5)` and `chance(4)` (`aip` 0); step 2's `UseSkill1`. S13's push and refill (their flips stop: no log reaches them), every refused RunHome with its `CancelEvents(2, 0)`, step 3's RunHome, step 4 at home, step 5's RunHome (distances 30 to 40 not logged), `AiPathSkillStep`'s early returns and range tests, the pushed 4 against `Sk1mode` (also 4), the limit's exact 700 and `>` (no gap 700 to 703), the list's count and points; Nightmare, Hell and record 708. (0x005F67E3, 0x005E5C27, 0x005E5F22)
- **Addendum 2026-11-10: plan 0066 batch S1d** (`lane/n66d`, static, no game; tools at `cd663109`: `tools/ai_first_check.py` sha256 `e4eb1802…d4a6`, which runs `tools/ai_model_check.py` revision 2's models). First-boundary hand maps (README G5) for the 16 catalogue rows whose `l` line reads "Logged, not compared", over the 74 kept logs those lines cite: the 31 case logs of run:2026-11-03-ai, the 21 of run:2026-11-03-ai-3, the 17 of run:2026-11-04-ai-r5 and the 5 of this run (`sweep2-s1cd/logs-s1d.txt`, hashed in `manifest-sweep2-s1cd-inputs.sha256`). Output `sweep2-s1cd/s1d-first-check.txt` (`f41b2f45…78ae`, 116 lines) under the same `manifest.sha256`. The route named `tools/ai.py check`; the maps are a separate tool so that `ai.py`, the hashed checker behind those runs' kept first-boundary outputs, is unchanged.
  - **Procedure** (from `workspace/logs/ai`, under the scope): `ai_first_check.py check --logs sweep2-s1cd/logs-s1d.txt --out sweep2-s1cd/s1d-first-check.txt`. A map is the row's block head up to its first call of a logger boundary function (BND, tools/gdb/ai.py): the S1b models for R15, R23, R26, R96, R99, R100 and R130, new heads for R10's think, R11, R15's alt, R48, R49 and R56, and `m_s13` for R10's state-13 decisions. Each run stops at that call and compares the callee, its return address, the words the block names, the unit seed, `v14`, `v18`, `v1C` and `+0xC4`; the return is not used. The sites are read from the code, not the logs: the one call to that callee in the think (objdump of the pinned game.exe), or, for R99 and R130, which call `SetModeAtUnit` or `Idle` from several sites, the sites of the emulated families `soul` (`tools/ai_cat_emu12.py`) and `mauler` (`tools/ai_cat_emu10.py`). Controls: every site + 1 (fails every decision by construction), each branch before the first call reversed alone, `le`.
  - [C] (`s1d-first-check.txt`, 0x005B186F) **Compared, 0 mismatches**, every decision fork-free (decisions per run: run:2026-11-03-ai, -ai-3, run:2026-11-04-ai-r5, this run):
    - one first-call outcome each, so each confirms that call and its words, no branch choice (README G3): R10's think 49 (this run) at `UnitGetRoom(U)` 0x005F0B2C and its 160 state-13 decisions (this run) at `UnitGetRoom(U)` 0x005E5C77, 209 in all; R11 17 (17) `UnitLifePct(U)` 0x005F0D06; R15's think 177 (70 + 62 + 45) `FindHostile(…, 0)` 0x005F1833; R23 1 062 (375 + 431 + 256) `UnitDistSq` 0x005F31C9; R26 119 (73 + 28 + 18) `UnitLifePct(U)` 0x005F4544; R48 321 (200 + 121) `UnitLifePct(U)` 0x005F6ECB; R49 74 (57 + 17) `UnitLifePct(U)` 0x005F72FE; R56 16 (16) `MonsterOwner(U)` 0x005F8FB1; R96 179 (61 + 61 + 57) `ParamsHead(U)` 0x005E1281; R100 16 (12 + 4) `UnitGetRoom(U)` 0x005E7F5C.
    - R99 468 (243 + 25 + 200), two outcomes: `Idle(15)` 0x005EA070 (450), and `SetModeAtUnit(9, t)` 0x005E9F83 after `v14 ← 1`, `v18 ← T` (18); `+0xC4 |= 0x20000` before either (its skip fails 36); reversed alone, `dist < 5` fails 468, `v14 ≠ 0` 450, `v14 = 0` and both stores 18 each, `t = 0` 18.
    - R130 119 (85 + 34), four outcomes: A1 0x005EE2CE (12), `Idle(15)` 0x005EE3AD (4 in melee range, 27 at step 4), `UseSkill1(t)` 0x005EE34A (22), `Walk(t, 0)` 0x005EE39D (54); reversed alone, the melee test fails 104 of 119, `chance(1)` 16 of 16, `dist < aip(3)` 103 of 103, `chance(4)` 29 of 29, `chance(2)` 81 of 81, `Skill1 ≥ 0` 29 of 103; one draw at an equal pair (`le` 1).
  - [I] **Not compared:** R15's alt (0x005F1750), 4 decisions: every one forks on the kind-14 record's `+0x18`, which the log does not hold (`ARM` none; status ok, forked 4). R1 (0x005B0CD0), 104 decisions: the think lies outside the logger's windows (`THINK_LO`, tools/gdb/ai.py), so no call is logged. R32 (0x005E7130), 1 167 decisions: its first step, `AiNpcSaveHome`, branches on the kind-10 home record's `+0x0C`/`+0x10`, which the log does not hold (the AID `head` is the `+0x20` record; tools/ai_cat_emu12.py `f6800` finds kind 10 from the ring's second node), so every decision forks before its first call. R54 (0x005E73A0), 489: `AiNearestPlayer`'s search returns at 0x005DDF5B, outside the windows, so `p` is unknown before the first call (`ai_model_check.m_r54`; S1b's 302 of 302 forked). R118 (0x005E1E00), 108: `StatListFindFlag` (0x00625760) is not a boundary and decides the first call (`m_r118`; S1b's 50 of 50 forked, 6 stopped). (0x005B0CD0, 0x005E6800, 0x005DDF5B, 0x00625760)

## run:2026-11-15-sweep2-s1e

- **Question:** (plan 0066 Phase 1, batch S1e) Do the catalogue's search callbacks and helpers map their declared
  image to their return value, the words they write and the unit seed as the monsters/ai catalogue states them (at
  `b5999f5e`), with **every callee run whole** (no observed boundary, no declared return: inventory ruling R2)?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`d516ae47…`, unchanged since `1bedef6c`),
  lane project copy `workspace/ghidra-n66e`, heap 3 GB (`GHIDRA_HEADLESS_MAXMEM=3G`), one headless run inside
  `systemd-run --user --scope -p MemoryMax=4G`. No wine, no slot. Models, case writer and checker `tools/ai_s1e_emu.py`
  (committed at `9d00a53b`, sha256 `6d0287cd…`, unchanged by this run), every draw from `random.Random("n66e-<family>")`.
  24 families of 240 cases each (5 760), one memory spec (`s1e.mem`) and one case file. The declared image (the
  tool's docstring): the DataTables pointer and the MonStats, MonStats2, Skills and ItemStatCost arrays (zero but for
  each MonStats record's `+0x02`), the game (difficulty, frame, region array, unit hash slots), units, monster and
  player data, AI controls, paths, stat lists with their node chains, the player relation list, rooms with their near
  lists and unit lists, regions, the search and weight blocks, the seeds. Image constants read unwritten:
  `g_BitMask32` 0x006CE268, `g_UnitHashOffsets` 0x006E10E0, `g_AiSearchKinds` 0x006E3300, the jump and byte tables at
  0x005EB7D8..0x005EB7E7 (`AiShadowMasterCb`) and 0x005EAD34..0x005EAD47 (`AiShadowSkillFits`). Guards: the fatal
  path (0x00408090, 0x00408A60, 0x00681E09). Callees run whole: `UnitDistSq`, the stat getters with 0x00624F60's
  search, `UnitMaxHp`, `UnitLifePct`, `UnitAlignGet`, `AlignSame02`, `UnitsHostile` with the player relation list,
  `MonsterOwner` and `GameFindUnit`, `UnitGetOwner`, `UNIT_HasState`, the state-set-33 test, `MonTypeFlag`,
  `MonStats2FlagTest`, `MonBaseId`, `MonClassCheck`, `MonIsDeathMode`, `UnitIsDead`, `UnitGetRoom`,
  `RoomGetLevelId`, `MonRegionGet`, `RNG_RandLoHi`, `RNG_Range`, `AiShadowSkillFits` on its declared paths, and for
  Mephisto's pick `AiUnitSearch` kind 1 with `AiSearchNearRooms`.
- **Procedure** (from the worktree root; `D=workspace/logs/ai/sweep2-s1e`):
  ```
  python3 -I tools/ai_s1e_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66e GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
    tools/ghidra.sh emuboundary $D/s1e.cases $D/s1e.mem > $D/s1e.out 2> $D/s1e-ghidra.err
  python3 -I tools/ai_s1e_emu.py check --dir $D > $D/check.txt
  python3 -I tools/ai_s1e_emu.py manifest --dir $D --write
  ```
  Controls: every named test of a model is reversed alone, and every ordered compare has its strictness switched alone
  (`name~`); a control's `sep` counts the cases whose predicted outputs it changes, `passed` those the emulator output
  still matches (must be 0). The site control of ADR-0021 does not apply (no case ends at a boundary).
- **Outputs:** `$D/manifest.sha256` (`77befdea…`, 12 lines: `check.txt` `86d920a6…`, `s1e.out` `c0c12a75…`,
  `s1e.cases` `01e0f560…`, `s1e.mem`, `s1e-ghidra.err`, the seven table and arena images); `sha256sum -c manifest.sha256`
  passes from `$D`. Rerun into a scratch directory: `cases` regenerates `s1e.cases` and the images byte for byte and
  `s1e.mem` but for its absolute image paths; `check` on the kept `s1e.out` reproduces `check.txt` byte for byte. The
  development runs of 2026-11-10 were in session scratch and are not kept (resume note in plan 0066); no count here rests
  on them.
- **Observed** (`check.txt`, one line per family, then its controls `name:sep/passed`):
  ```
  S1E <24 families> cases=240 match=240 bad=0 stopped=0   (each)
  drew: trkind 49, shroll 145, mephpick 74, genspawn 202, wpick 125; 0 in the other 19
  UNSEPARATED: trkind hi<=lo~; shroll v18<lo~; genspawn count>453 count>453~; none in the other 21
  S1E life pairs: AiLifePct = UnitLifePct on 240 of 240 images (93 non-zero)
  S1E traced reads accounted: AiShadowMasterCb jump and byte tables 122, AiShadowSkillFits jump and byte tables 8,
      g_AiSearchKinds 480, g_BitMask32 4772, g_UnitHashOffsets 312
  S1E traced unaccounted: 0
  S1E total cases=5760 match=5760
  S1E result=ok
  ```
  Every separated control has `passed` 0 (244 controls, 240 separated, 4 not; per family in `check.txt`).
- **Results by family** (function, catalogue line at `b5999f5e`; counts from `check.txt`; each `[C]` for the function's
  map on the declared image, run whole):
  - [C] `nearally` `AiNearAllyCb` 0x005F06B0 (R8b, line 289): candidate ≠ searcher, type 1, `UnitAlignGet` 0,
    `MonIsDeathMode` 0, `UnitDistSq` strictly below the best; 7 controls, all separated (`d<best~` 39); 103 taken; 5
    cases whose `dx² + dy²` reaches 2³¹ match the 32-bit signed wrap. No draw. (fn:sub_005F06B0_AiNearAllyCb@0x005F06B0)
  - [C] `samebase` `AiSameBaseNearCb` 0x005B0D00 (R18a, line 598): type 1, ≠ searcher, the searcher's `MonBaseId`, not in a
    death mode, strictly nearer; 7 controls separated (`d<best~` 24); 37 taken. (fn:sub_005B0D00_AiSameBaseNearCb@0x005B0D00)
  - [C] `wounded` `AiWoundedNearCb` 0x005F30F0 (R23b, line 687): type 0 or 1, ≠ itself, `MonIsDeathMode` 0 (0 for every
    player: 16 players taken), `UnitDistSq ≤ blk+4`, stat 6 ≤ `UnitMaxHp ÷ 100 · blk+8` (truncating); the kept unit's
    distance goes to `blk+4`, so ties replace (`d<=best~` separates 8). 8 controls separated. (fn:sub_005F30F0_AiWoundedNearCb@0x005F30F0)
  - [C] `zakheal` `AiZakarumHealCb` 0x005F7240 (R49b, line 1220): the line's tests in its order; `+0x08` rewritten to
    `0x7FFFFFFF` only when ≤ 0 (8), never set from a life; each unit at `UnitLifePct ≤ 60` counts in `+0x04` and is taken
    when its life is below `+0x08` (49 taken, 7 counted and not taken, with a case-written `+0x08` ≤ 60); 15 controls
    separated (`life<=60~` 1). (fn:sub_005F7240_AiZakarumHealCb@0x005F7240)
  - [C] `fetrev` `AiFetishReviveCb` 0x005F99A0 (R65c, line 1397): the line's tests and filter cases; mode 12 strictly nearer
    to `s.dead` (18), any other counted (42) and strictly nearer to `s.live`; 21 controls separated. (fn:sub_005F99A0_AiFetishReviveCb@0x005F99A0)
  - [C] `regurg` `AiRegurgitatorCb` 0x005FA690 (R71b, line 1560): bit `0x200` clear, bit `0x02` set, in a death mode, not in
    state set 33, alignment 0, `MonStats2FlagTest` of flag 12, `UnitDistSq ≤ best`; ties replace (17 taken at an equal
    distance; `d<=best~` separates 17); 11 controls separated. (fn:sub_005FA690_AiRegurgitatorCb@0x005FA690)
  - [C] `oblkn` `AiOblivionKnightCb` 0x005FAE40 (R74b, line 1643): the line's tests; `MonBaseId` in `[0, count)` and 310;
    `UnitDistSq ≤ blk+8`; strictly nearer to `s.knight`, strictly nearer and `UnitLifePct < 40` to `s.weak` (25); 18
    controls separated. (fn:sub_005FAE40_AiOblivionKnightCb@0x005FAE40)
  - [C] `trkind` `AiTrapArrowKind` 0x005FB650 (R78, line 1736, the block): a region word ≥ 0 kept (115); below 0, set to 0
    below level 40 (76) or to `RNG_RandLoHi(U's seed, 0, 3)` (49 drawn); 6 of 7 controls separated. (fn:sub_005FB650_AiTrapArrowKind@0x005FB650)
  - [C] `randlohi` `RNG_RandLoHi` 0x004BC500 (R78b, line 1747): `lo` with no step for `hi ≤ lo` (signed; 81), else one step
    and `lo + low mod (hi − lo)`, a power-of-two span by the mask (71); 3 controls separated (`hi<=lo~` 12).
    (fn:RNG_RandLoHi@0x004BC500)
  - [C] `shroll` `AiShadowSkillRoll` 0x005EAD50 (R105, line 2031, the block): 0 when the class or `AiShadowSkillFits`
    refuses; 1 for id 0 with no draw (4); else `Range(100) > 100 − 160·q ÷ 100` refuses, `T < v14` refuses, `v18` reset to
    `lo` outside `[lo, 32·hi]` (62), `Range(v18)` then `Range(100)`, the second below the first refuses (22), else the
    `v18` add and 1 (64 with three draws); 12 of 13 controls separated. (fn:sub_005EAD50_AiShadowSkillRoll@0x005EAD50)
  - [C] `shmcb` `AiShadowMasterCb` 0x005EB6D0 (R106b, line 2277): the hostile part's two distance blocks and counters,
    `AiShadowPriorityTarget` to `blk+0x24` (5); an ally of base 410 to 416 counted in `blk+0x20` but 414, which goes on to
    the hostile part (12), by the byte table; 21 controls separated. (fn:sub_005EB6D0_AiShadowMasterCb@0x005EB6D0)
  - [C] `mephcb` 0x005F7700 and `mephpick` 0x005F77C0 (R50c, line 2697): the callback's tests and its four blocks
    (`blk[5..6]` only for a player searcher, 4 and 43); the pick with `AiUnitSearch` kind 1 walking the near rooms' unit
    lists run whole; 16 and 22 controls separated. (fn:sub_005F7700_AiMephistoPickCb@0x005F7700, fn:sub_005F77C0_AiMephistoPickTarget@0x005F77C0)
  - [C] `priest` `AiPriestHealCb` 0x005E0430 (R85b, line 2960): the line's tests, lowest `UnitLifePct ≤ 75` below
    `blk[1]` kept; the priest itself taken once (no test excludes it); 11 controls separated. (fn:sub_005E0430_AiPriestHealCb@0x005E0430)
  - [C] `imp` `AiImpNearCb` 0x005E1720 (R113b, line 3164): the line's tests, the searcher's owner by `UnitGetOwner`, the
    candidate's AI control by 0x00541860; returns the candidate (34) or 0; 11 controls separated. [I] The guard `count > 492 ? 492 : −1` has no control of its own (`base492` is the only one on the base). (fn:sub_005E1720_AiImpNearCb@0x005E1720)
  - [C] `overseer` `AiOverseerMinionCb` 0x005E26D0 (R120b, line 3359): counted 63, `blk[3]` 15, `blk[4]` 33, each only while
    0; 18 controls separated. (fn:sub_005E26D0_AiOverseerMinionCb@0x005E26D0)
  - [C] `mincount` `AiMinionCountCb` 0x005E2B70 (R121a, line 3380): base 453 (62) or 461 (45), alignment 0, no distance
    test; 6 controls separated. (fn:sub_005E2B70_AiMinionCountCb@0x005E2B70)
  - [C] `genspawn` `AiGenSpawnPickClass` 0x005E6020 (R129, line 3593, the block, as corrected below): drawn entry taken 26,
    first flagged entry 63, n = 0 with entry 0's class 2 and the 496 fallback 36; 6 of 8 controls separated. (fn:sub_005E6020_AiGenSpawnPickClass@0x005E6020)
  - [C] `wpick` 0x005FC130 (R51, line 3916, as corrected below): sum > 0, `k` returned 125; sum ≤ 0, no draw, `k`
    returned 27; fallback 1 88; 5 controls separated (`sum>0~` 82, `r<run~` 22). (fn:sub_005FC130_WeightedPickUnref@0x005FC130)
  - [C] `alife` 0x005DD280 and `ulife` 0x00621F20 on the same 240 images: `(stat 6 >> 8) · 100 ÷ (UnitMaxHp >> 8)`,
    truncating, 0 for a zero maximum; 3 controls each separated (`sar8` 79, `max=0` 188, `trunc` 9); equal on 240 of 240.
    (fn:sub_005DD280_AiLifePct@0x005DD280, fn:sub_00621F20_UnitLifePct@0x00621F20)
  - [C] `st319` `AiMonState3or19` 0x005DD2B0: 1 for `MonsterData+0x54` 3 (9) or 19 (9), else 0 (222). (fn:sub_005DD2B0_AiMonState3or19@0x005DD2B0)
  - [C] `owner` `MonsterOwner` 0x0058F0D0: the AI control's owner words `+0x30` type and `+0x2C` guid looked up by
    `GameFindUnit` in the game's hash slot (type 5 at `+0x1B20`); 0 for a null, non-monster or controlless unit; 7
    controls separated. (fn:sub_0058F0D0_MonsterOwner@0x0058F0D0)
  - [C] `entry` `MonAiEntryGet` 0x005B15D0 (S0, line 115): a state word ≠ 0 gives state row `0x0073D358 + 16·state`
    (179); 0 gives the class's row `0x0073CA18 + 16·MonStats+0x1E` (25), row 0 when that word is outside `[0, 0x94)`
    (36); 2 controls separated. (fn:sub_005B15D0_MonAiEntryGet@0x005B15D0)
- **Corrections to the catalogue** (each from the kept run and read again in the code by objdump):
  1. [C] **The weighted pick with sum ≤ 0 still scans.** 0x005FC130 sets `r = 0` with no step (`xor edx, edx; jmp`,
     0x005FC153) and runs the same scan, so a positive prefix (weights summing ≤ 0 overall) returns its `k`: 27 of 240
     cases; the fallback 1 only when no running sum exceeds 0. Line 3917's "if sum ≤ 0: the fallback" is wrong for this
     function. [I] Diablo's inline pick has the same shape (`cmp ecx, ebx; jle 0x005E8E80` at 0x005E8E2A with `edx` 0 from
     the summing loop's count, `ebx` 0), read only, not run. (0x005FC14F–0x005FC155, 0x005E8E2A)
  2. [C] **`AiGenSpawnPickClass` with n = 0 draws nothing and still tests entry 0** (`xor edx, edx; jmp 0x005E60BC`,
     0x005E6075): entry 0's class is taken when flagged (2 cases), else the scan is empty and the 496/−1 store ends it
     (36). The first store `*out ← 453 or −1` (0x005E6054) is dead: each of the three exits stores `*out` again
     (0x005E60F7, 0x005E616D, 0x005E617C), so no case separates its test (`count>453`, `count>453~` sep 0). Its count
     test stays a reading with no observable.
  3. [C] **`AiLifePct` is `UnitLifePct`.** 0x005DD280 is `push ecx; call 0x00621F20; ret`: the same map behind a register
     argument, equal on 240 of 240 images. Lines 58 and 4689's "two different readers … keep them apart" describe one
     map with two calling conventions (`ECX` against the stack).
  4. [C] **Mephisto's pick takes its first draw only when the search found a candidate.** `cmp [ebp−0x1C], 0; je 0x005F7857` at
     0x005F780B skips the first draw when `blk[3]` is 0, and the second draw is tested on `blk[5]` (0x005F7857): 166
     cases with no first draw. Line 2697's "returns `blk[3]` on `D100() < aip(2)`" holds only after a find; with none, no
     first draw. With `blk[5]` also 0 (a monster searcher; the pick's one caller, Mephisto, is `[I]`) it returns `t` with no
     draw at all; `blk[5]` is set for a player searcher (4 and 43 cases), whose second draw is then taken.
  5. [C] **`AiWoundedNearCb`'s "not dying" is `MonIsDeathMode`**, which is 0 for every player (type 0), and its distance
     compare is `≤`: the later of two equal candidates replaces the earlier (refines line 687's "keeping the nearest").
  6. [C] **`AiShadowSkillRoll` draws 0, 1 or 3 times**, not "three per tried skill": none on a class or `Fits` refusal or
     id 0, one when the first draw or `T < v14` refuses, three otherwise. It never reads its fourth stack argument
     (`ret 0x14`; no `[ebp+0x14]` in 0x005EAD50–0x005EAEFC): melee reaches `AiShadowSkillFits` from `ctx+0x18`.
- [I] **Unseparated controls**, each with no observable: `trkind` `hi<=lo~` (the call is always `RNG_RandLoHi(…, 0, 3)`;
  the `randlohi` family separates it, 12); `shroll` `v18<lo~` (at `v18 = lo` the reset writes the value already there);
  `genspawn` `count>453`, `count>453~` (the dead store, correction 2).
- [I] **Not run:** `AiShadowSkillFits` past its declared paths (the case writer keeps Skills `+0xBC` at 0, so 0x005EAB20
  returns 1 at once, and asserts off the `+0x04 & 4` path through 0x006256B0 and 0x00625D00), and the bonus-level
  branch of `SKILLS_GetSkillLevel` (the call to 0x00644180 at 0x006442C3: not modelled, and no case needs it to match); the callers' block words (initial values, the frame offsets, what each
  think reads after the search) and the caller sets; the AI-search kinds other than 1.
- **Conclusion:** the 24 maps are `[C]` on their declared image, every callee run whole, with corrections 1 to 6. No
  symbol raise: an ADR-0015/0021 emulation over a declared scratch image confirms the map, not the role a name states
  (review-fixes rule 14). (run:2026-11-15-sweep2-s1e)

## run:2026-11-15-ai-tour-1

- **Question:** (plan 0069 Phase 2) Does the rev 7 logger keep every rev 6 line and add the words of the plan's rev 7 list
  without disturbing the decisions, and do the Act I cases of plan 0069's tour, with the models of Phases 1b and 1c and
  the revision 6 words, check with 0 mismatches? Which statements of the H1a to H1d, H1g and H1h batches do those cases
  reach (the raise itself is Phase 4's)?
- **Setup:** `tools/gdb/ai.py` rev 7 through `tools/gdb/ai-g4.gdb` (the AI logger with the G4 and P1b2 sources, unchanged),
  slot 2 (display `:9`, `workspace/wineprefix-2`), every launch inside `systemd-run --user --scope -p MemoryMax=4G`,
  runner `tools/ai_sessions.py` (the library runner, `--fresh`: one game process per case, ADR-0028 item 1), characters
  built from the recipes by `ai_sessions.py build --saves workspace/logs/n69d/saves` (CombatSor `1d9de374…`, the kept
  character). Seeds are the case table's (plan 0069 Phase 1a: Act I 7159; the four H1h reruns keep their kept cases'
  seeds 5803, 5602, 5401, 5802). The model checker is `tools/ai_model_check.py` revision 6 and `tools/ai.py`.
  The rev 7 additions (read-only, harness-play rule 17): `R7W` word lines at breakpoints of the think code (MonPlayerBonus's
  difficulty word at 0x005F0B37, MonsterOwnerRef's (guid, type) at 0x005F6EED, AiNearestPlayer's (p, f, unit type of p) at
  0x005E73BD and 0x005E690E, StatListFindFlag's result at 0x005E1E34 and 0x005E215C, AiTrapArrowKind's region word at
  0x005FB674; MonStats Velocity and Run for rows 48 and 70, the Skills `aurastate` of `Skill2` and `MonsterData+0x0E` for
  row 73, all at the think call), `AII`/`AIQ` lines at `MonAiInit`'s init call (0x005B0F18, return 0x005B0F1B) for the
  inits 0x005F6630 (row 43) and 0x005E80E0 (state 11), the think window 0x005B0CD0..0x005B0D00 (row 1) with its two return
  sites in `tools/gdb/ai-retsites.txt` (2 287 sites, `tools/ai_retsites.py check`), and the calls inside
  `AiVileMotherSpawn` 0x005F9E30 logged although it is a pending boundary. Not in rev 7 (reasons in the plan log): R32's
  home and script words, `objects.py`'s lines beside the logger, and the Phase 1c words of R56, R71, R85 and R128.
- **Predictions** (committed before the first kept log; the development logs `dev-*` of 2026-11-15, three smokes of
  `t-h1h-a1-stony`, `t-a1-stony` and the shared pair `t-a1-town`, `t-a1-cold`, preceded them and are not kept):
  1. Every kept log's first logger line is `AI logger armed rev 7 bmax 48`, and a rerun of the kept rev 6 case `a2-oasis`
     (seed 5201) shows 0 first-boundary mismatches by `tools/ai.py check`, its rev 6 lines unchanged in form.
  2. `ai_model_check.py check` over the Act I logs gives 0 mismatches for every entry (a stop is allowed), and over the 38 kept
     rev 4 and rev 6 logs `regress` stays byte-identical to S1b's `model-check.txt` apart from the SEP lines.
  3. Decisions by case, from the predicted pools (`workspace/logs/n69a/pools.txt`, Act I seed 7159; each at least 1, at most the
     per-row cap of 200 a game):
     - `t-a1-cold` (level 3, pool brute1, corruptrogue1, cr_lancer1): R7, R10, R36. R59 (Blood Raven, a `hunt` on the Burial
       Grounds border) is not pool-placed: at least 1 decision only if the border walk crosses into the Burial Grounds.
     - `t-a1-stony` (level 4, goatman1, cr_archer1, crownest1): R43, with at least one `AII` and `AIQ` line of the init 0x005F6630
       per crownest created near the player.
     - `t-a1-darkwood` (level 5, corruptrogue2, quillrat2, cr_lancer2): R10, R14, R36.
     - `t-a1-marsh` (level 6, brute2, goatman2, crownest2): R7, R43 and its `AII`/`AIQ` pair.
     - `t-a1-barracks` (level 27, corruptrogue4, fallenshaman3, quillrat4): R10, R14. R98 (the Smith, a `hunt`) only if reached.
     - `t-a1-catacombs` (level 35, bighead2, fallenshaman4, arach1): R4, R26.
     - `t-a1-town` (Rogue Encampment, a town walk): R32 and R60; R58 (`navi`, the Blood Moor preset) only if the border walk
       reaches it; S5 and S6 not predicted (the unhired mercenary's state think is not shown to run near the player).
     - `t-h1h-a1-stony` (seed 5803): R1 at least 1 decision, each `ok`. `t-h1h-a3-flayer-p8` (5602): R78. `t-h1h-s-barb-flayer`
       (5401): R79. `t-h1h-s-necro-curse` (5802): S11, with an `AII` of the init 0x005E80E0.
  4. Word lines: each R10 decision that reaches step 2 carries exactly one `MonPlayerBonus` word; each R54 and R32 decision that
     reaches `AiNearestPlayer` carries its word, with the unit type of p; each R78 and R79 decision that reaches
     `AiTrapArrowKind` carries one `arrow.region` word. A rev 7 decision the model checks with its word is fork-free where the
     fork was only that word (R10 step 2, R54 step 2, R118 and R119 step 1, R78 and R79's region).
  5. The separation lines (ADR-0028 item 7) and the decision counts per entry are reported as the checker prints them; a
     row with 1 outcome is reported as confirming it. The sharing decision (launch against switch) is made from the
     measured wall of this run's marks.

### Results of `run:2026-11-15-ai-tour-1` (plan 0069 Phase 2, `lane/n69d`)

Kept outputs in `workspace/logs/n69d/` (`manifest.sha256`, 63 lines, `sha256sum -c` passes from that directory; paths are
`../ai/…` and local names): the 12 case logs of the table below with their launch logs, marks, the pilot files, the status
files and the 8 + 3 screenshots, the runners' stdout, and the checks (`model-check.txt`, `ai-check.txt`, `words.txt`,
`flip-rows.txt`, `flip-states.txt`, `regress.txt`, each with its stdout). `manifest-ckpt1.sha256` (the checkpoint's) is
superseded: its `…-s2.pilot.txt` line fails because the pilot file is appended by the later batch. Tools at the commit of this
entry: `tools/gdb/ai.py` rev 7, `tools/ai_model_check.py` revision 6 with the AIL stop below, `tools/ai.py`,
`tools/ai_tour_words.py`. Slot 2, `--fresh` (one game process per case), every launch under `MemoryMax=4G`.

| case | seed | launch (pid) | decisions | wall |
|---|---|---|---|---|
| `t-a1-town` | 7159 | L1 (177637) | 421 | 111 s |
| `t-a1-cold` | 7159 | L2 (180384) | 655 | 335 s |
| `t-a1-stony` | 7159 | L3 (188215) | 399 | 227 s |
| `t-a1-darkwood` | 7159 | L1-r2 (323701) | 437 | 226 s |
| `t-a1-marsh` | 7159 | L2-r2 (336003) | 257 | 229 s |
| `t-a1-barracks` | 7159 | L3-r2 (360120) | 368 | 245 s |
| `t-a1-catacombs` | 7159 | L4 (381416) | 402 | 247 s |
| `t-h1h-a1-stony` | 5803 | L5 (402778) | 217 | 163 s |
| `t-h1h-a3-flayer-p8` | 5602 | L6 (424002) | 488 | 274 s |
| `t-h1h-s-barb-flayer` | 5401 | L7 (455442) | 329 | 184 s |
| `t-h1h-s-necro-curse` | 5802 | L9 (471439) | 781 | 321 s (kept after a first try, L8, 90 decisions, ended by the runner's relaunch; L8 is in the manifest, not checked) |
| `a2-oasis` (regression, own batch, run id `…-tour-1-oasis`) | 5201 | L1 (511446) | 399 | 176 s |

The second batch's launch numbers restarted at L1 (the runner counts launches per invocation), so its first three launches
are `L1-r2` to `L3-r2` (the runner's `-r2` naming; the kept L1 to L3 were not overwritten, `sha256sum -c` of
`manifest-ckpt1.sha256` passes for everything but the pilot file). An earlier start of this batch, stopped after its first
launch to keep the numbering, is `workspace/logs/n69d/dev/` (`2026-11-15-ai-tour-1-s2-7159-L1-r2.*`, `aborted-batch2-stdout.txt`).

- **Prediction 1 held.** All 12 logs open with `AI logger armed rev 7 bmax 48`. `a2-oasis` (399 decisions, rows 19, 20, 23, 32,
  54, 61): `ai.py check` 0 mismatches. `ai.py check` over the 12 logs: 5 153 decisions, 0 mismatches.
- **Prediction 2 held, after one checker change.** `ai_model_check.py check --logs` over the 12 logs: 95 entries, 0 mismatches
  in every entry except the control `R79x` (2 mismatches, the control failing as required). The first check gave 2 more, in R23
  and R23x (both the flayer-p8 log, decisions 7525 and 8657, `5.ovr7: the model calls Ovr, the log has no further call`).
  Cause, from the log: each of the two decisions carries an `AIL` line (`out` 601, `pend` 0) before its `AIX`, the logger's
  `OUT_LIMIT` of 600 calls made outside the think (the 601st is `RoomAtSubtile` 0x00463740, called from `FreeNearFallback`
  0x0064E7B0's search at 0x0064D118) which disarms the boundary breakpoints, so the calls after the fallback are not logged. The
  fallback's code after its call returns to 0x005F3443 and calls `Ovr` (0x005DE190) at 0x005F344E `[I]` (read, not logged). The
  checker now stops such a decision (`Stop("AIL")`, as `finish` already did for a decision that ends on time) instead of
  reporting a mismatch (`ai_model_check.py`, `Run.call`; test `Revision6.test_ail_truncated_decision_stops`, 98 tests OK).
  `regress`: byte-identical to S1b's `model-check.txt` (32 entries, 38 logs), run after the change. R23 and R23x: 122
  decisions, 119 ok (72 fork-free), 0 mismatches, 3 stops (the two AIL stops and one `no AIR line`).
- **Stops** over the 12 logs: R4 1 and R96 1 (`no AIR line`, the decision's last return not logged), R32 61 (`a path action is
  not modelled`, of 469), R23 3. Every other entry 0.
- **Prediction 3 (decisions by case, from `words.txt`).**
  - Held: `t-a1-cold` R7 10, R10 178, R36 21; `t-a1-stony` R43 4 with 3 `AII` and 3 `AIQ` lines of 0x005F6630;
    `t-a1-darkwood` R10 24, R14 51, R36 11; `t-a1-marsh` R7 1, R43 1 with 3 `AII`/`AIQ` lines; `t-a1-barracks` R10 100, R14 26;
    `t-a1-catacombs` R4 94, R26 29; `t-a1-town` R32 200; `t-h1h-a1-stony` R1 4 (41 over the three logs that have it), each ok
    and fork-free; `t-h1h-a3-flayer-p8` R78 14; `t-h1h-s-barb-flayer` R79 10; `t-h1h-s-necro-curse` S11 (32 decisions) with
    17 `AII` lines of 0x005E80E0.
  - Not held: R60 (not seen in any of the 12 logs; `t-a1-town` has rows 1, 3, 6, 32, 54, 61 only); R59 and R98 (conditional, not
    reached); R58 (conditional, not reached); S5 and S6 not seen (as predicted).
- **Prediction 4**: the checker's own counts, not a per-decision recount of the word lines: R10 302 of 302 fork-free, R54 88
  of 88, R78 14 of 14, R79 10 of 10, R1 41 of 41; R118 and R119 are Act IV and V rows and are not in this run.
- **Prediction 5, separations** (`model-check.txt`, ADR-0028 item 7): R3 1 outcome over 34, R4 3 over 93, R5 6 over 88, R12 3 over 231,
  R19 3 over 65, R23 14 over 72, R26 5 over 29, R43 3 over 5, R54 1 over 88 (confirms it: the path is `4.idle`). Resume flip (`flip-rows.txt`, rows 3, 4, 5, 15, 23, 26, 43, 52, 54, 63, 65, 68, 70, 78, 79, 96, 118, `--key
  rowthink --cap 1000000`; `flip-states.txt`, thinks 5e8140 and 5e8340): fork-free decisions 23@5f3170 72, 26@5f4510 29, 3@5efe20
  34, 43@5f6650 5, 4@5eff50 93, 5@5f00e0 88, 63@5f9490 7, 65@5f9a80 95, 78@5fb6c0 14, 79@5fb7e0 1, 96@5e1250 98, 54@5e73a0 0; every
  two-way site fails alone (`two_way_sep` = `two_way`) except row 63's, 4 of 5. The raise itself is Phase 4's.
- **Sharing decision.** Launch to ready 18.6 s and 19.1 s and a switch 18.7 s (dev, checkpoint): no saving, the tour stays fresh
  per case (harness-play § Fresh process). The 12 cases took 2 738 s of game wall (the marks' walls).
- **Not covered by this run:** Act II to V cases (the next batches), the Phase 1c words of R56, R71, R85, R128, R32's home and script
  words, `objects.py`'s lines beside the logger.

## run:2026-11-16-ai-tour-2

- **Question:** (plan 0069 Phase 3a, `lane/n69e`) Do the Act II and Act III cases of plan 0069's tour (17 cases: `t-a2-town`,
  `t-a2-dryhills`, `t-a2-oasis`, `t-a2-lostcity`, `t-a2-canyon`, `t-a2-palace`, `t-a2-arcane`, `t-a2-halls`, `t-a3-town`,
  `t-a3-spider`, `t-a3-marsh`, `t-a3-flayer`, `t-a3-lower`, `t-a3-bazaar`, `t-a3-upper`, `t-a3-travincal`, `t-a3-durance`) check with
  0 mismatches against the models of Phases 1b and 1c, and which statements of the H1a to H1d, H1g and H1h batches do they reach
  (the raise itself is Phase 4's)?
- **Setup:** as `run:2026-11-15-ai-tour-1`: `tools/gdb/ai.py` rev 7 (unchanged), slot 2, `--fresh` (one game process per case),
  every launch inside `systemd-run --user --scope -p MemoryMax=4G`, runner `tools/ai_sessions.py`, characters built by
  `ai_sessions.py build --saves workspace/logs/n69e/saves`, seeds the case table's (Act II 8723, Act III 7842), checker
  `tools/ai_model_check.py` revision 6 and `tools/ai.py`. Model prerequisite of this lane: `Revision6.test_nested_calls_inside_a_pending_boundary_are_not_offered`
  (99 tests): `top_level` already drops the calls logged between a pending boundary's AIB and AIR lines, so R68 needs no model
  change for the calls inside `AiVileMotherSpawn`. No rev 7 word is added for R56, R85 (their tests fork, the fork-free count is
  lower), R32's home and script words, or `objects.py`'s lines.
- **Predictions** (committed before the first kept log; predicted pools: `workspace/logs/n69a/pools.txt`):
  1. Every kept log's first logger line is `AI logger armed rev 7 bmax 48`; `ai.py check` gives 0 mismatches over the 17 logs.
  2. `ai_model_check.py check --logs` over the 17 Act I, II and III logs together with the 12 Act I logs gives 0 mismatches for every
     entry except the control `R79x` (2, as required; a stop is allowed); `regress` over the 38 kept rev 4 and rev 6 logs stays
     byte-identical.
  3. Decisions by case (each at least 1, from the predicted pools; the rows of a town case need the NPC near the player):
     - `t-a2-dryhills` (level 42: sandleaper2, pantherwoman2, vulture2): R17, R18, R23; R95 only if the sweep meets a desert turret.
     - `t-a2-oasis` (43: sandmaggot1, vulture2, crownest3): R15, R23, R43 with `AII`/`AIQ` lines of 0x005F6630; R38, R40, R66 only
       if Maggot Lair is reached by the warp steps.
     - `t-a2-lostcity` (44: sandraider2, sandleaper3, slinger6; 45: clawviper2, clawviper3, unraveler2): R8, R17, R95, R16.
     - `t-a2-canyon` (46: brute4, sandmaggot3, slinger4): R7, R15, R95; R45 and R94 only if the tomb's presets are reached.
     - `t-a2-palace` (52: sandraider3, baboon1, blunderbore1): R8, R11, R39. `t-a2-arcane`: R93 and R53 only if the sweep and the hunt
       reach them. `t-a2-halls` (57: unraveler1, slinger2): R95; R77 and R92 only if the loot walk springs a trap.
     - `t-a3-spider` (76: baboon3, mosquito1, thornhulk1): R24, R27, R11; R56 and R57 only if a tentacle exists there.
     - `t-a3-marsh` (77: willowisp1, thornhulk2, frogdemon1): R25, R27, R52; R65 and R56 and R57 not predicted.
     - `t-a3-flayer` (78: fetish4, frogdemon3, fetishshaman3): R52, R65; R23 not predicted.
     - `t-a3-lower` (79: sandleaper4, vulture3, zealot1): R17, R23, R48; R11 not predicted; R77, R80, R92 only if the loot walk springs
       a trap. `t-a3-bazaar` (80: thornhulk3, zealot2, cantor1): R27, R48, R49. `t-a3-upper` (81: vulture4, thornhulk3, zealot3): R23, R27, R48.
     - `t-a3-travincal` (83: vampire2, cantor3): R49; R85 only if the `hunt` reaches the council. `t-a3-durance` (101: mummy5, vampire3,
       blunderbore3): R39; R50 and R85 only if the `hunt` reaches Mephisto.
     - The town cases `t-a2-town`, `t-a3-town`: R32 and R41 (a Towner near the player); R42, S5, S6 not predicted.
  4. Word lines as in `run:2026-11-15-ai-tour-1` prediction 4: each R10, R54, R32, R78, R79 decision carries its word line and is
     fork-free where the fork was only that word.
  5. Separation lines and decision counts per entry are reported as the checker prints them; a row with 1 outcome is reported as
     confirming it. Sharing: fresh per case, as in Phase 2 (the launch cost is unchanged).

### Results of `run:2026-11-16-ai-tour-2` (plan 0069 Phase 3a, `lane/n69e`)

Kept outputs in `workspace/logs/n69e/` (`manifest.sha256`, 86 lines, `sha256sum -c` passes from that directory; paths are `../ai/…`
and local names): the 18 launch logs with their per-case logs (`split`), marks, the two pilot files, the status files, the screenshots
(`wpfail-…` of the first waypoint attempts of `t-a2-oasis` and `t-a3-flayer`, `stall-…` of the Act III batch), the runners' stdout
(`batch-a2-stdout.txt`, `batch-a3-stdout.txt`) and the checks (`model-check.txt` over the 17 kept logs, `model-check-all29.txt` over
them and the 12 of Phase 2, `ai-check.txt`, `words.txt`, `flip-rows.txt`, `flip-states.txt`, `regress.txt`, each with its stdout; the log
lists `logs-tour2.txt` and `logs-all29.txt`). Tools at the commit of this entry: `tools/gdb/ai.py` rev 7, `tools/ai_model_check.py`
revision 6 (unchanged), `tools/ai.py`, `tools/ai_tour_words.py`, `tools/ai_resume_flip.py`. Slot 2, `--fresh` (one game process per
case), every launch under `MemoryMax=4G`. Two batches: Act II under run id `2026-11-16-ai-tour-2` (seed 8723), Act III under
`2026-11-16-ai-tour-2b` (seed 7842), so that the launch numbers (L1 to L9 each) are not reused.

| case | seed | launch (pid) | position (level) | decisions | wall |
|---|---|---|---|---|---|
| `t-a2-town` (first try, failed: stage not reached, stayed in level 103) | 8723 | L1 (1038862) | 103 | 115 | - (kept, unchecked) |
| `t-a2-town` | 8723 | L2 (1040882) | Lut Gholein 40, walk 40 hops | 527 | 113 s |
| `t-a2-dryhills` | 8723 | L3 (1051143) | 42, sweep | 318 | 230 s |
| `t-a2-oasis` | 8723 | L4 (1074408) | 43, sweep; warps to 62, 63, 64 not taken (no hop to the warp; no warp 49), hunt 284 timed out | 845 | 522 s |
| `t-a2-lostcity` | 8723 | L5 (1125227) | 44, sweep, border walk (40 hops) | 344 | 214 s |
| `t-a2-canyon` | 8723 | L6 (1140642) | 46, sweep, descent 46 to 66 | 601 | 482 s |
| `t-a2-palace` | 8723 | L7 (1186431) | 52, sweep | 399 | 218 s |
| `t-a2-arcane` | 8723 | L8 (1196979) | 74, sweep, hunt 250 timed out (class never seen) | 342 | 267 s |
| `t-a2-halls` | 8723 | L9 (1206762) | 57, sweep, loot walk (60 hops) | 378 | 223 s |
| `t-a3-town` | 7842 | L1 (1215456) | Kurast Docks 75, the walk ended at hop 1 (no target, level done) | 28 | 27 s |
| `t-a3-spider` | 7842 | L2 (1216701) | 76, sweep | 330 | 232 s |
| `t-a3-marsh` | 7842 | L3 (1232445) | 77, sweep | 565 | 240 s |
| `t-a3-flayer` | 7842 | L4 (1258234) | 78, sweep | 746 | 246 s |
| `t-a3-lower` | 7842 | L5 (1272609) | 79, sweep, loot walk (60 hops, frontier 10) | 420 | 254 s |
| `t-a3-bazaar` | 7842 | L6 (1301735) | 80, sweep | 224 | 225 s |
| `t-a3-upper` | 7842 | L7 (1319724) | 81, sweep | 300 | 233 s |
| `t-a3-travincal` | 7842 | L8 (1370720) | 83, sweep, hunt 345 timed out (class never seen) | 424 | 267 s |
| `t-a3-durance` | 7842 | L9 (1396218) | 101, sweep, the warp to 102 not reached, hunt 242 timed out | 352 | 278 s |

Cases kept: 17 of 17 (Act II 8, Act III 9). Decisions per case are `ai-check.txt`'s `LOG` lines (the runners' stdout counts `t-a2-palace`, `t-a3-flayer` and `t-a3-upper` one lower, 398, 745, 299). One rerun: `t-a2-town`'s first launch (L1) failed at the stage gate (the waypoint click left
the player in level 103, 115 decisions) and the runner relaunched it fresh; L1 is in the manifest, not checked. Decisions in the 17 kept
logs: 7 143 (`ai.py check`). Wall of the 17 cases: 4 271 s (the marks' walls; the batches' own totals 2 306 s and 2 003 s). Sharing decision: fresh per case, unchanged.

- **Prediction 1 held.** All 17 logs open with `AI logger armed rev 7 bmax 48` (`words.txt`). `ai.py check` over the 17 logs: 7 143
  decisions, 7 191 `AIN` lines, 0 mismatches (`ai-check.txt`). The `a2-oasis` regression case is Phase 2's (kept, 0 mismatches).
- **Prediction 2 held.** `ai_model_check.py check --logs` over the 17 logs: 95 entries, **0 mismatches** in every real entry. The control
  `R78y` (y for x) fails 8 of its 13 decisions, as a control must (R78 itself 13 of 13, fork-free); the control `R23x` (the loop's
  other reading) fails 1 decision (`t-a2-dryhills` n=3207, `5.loopdist: PathDist edx 12a0/129f`, one off) where R23 matches. The
  control `R79x` has 0 decisions in these logs (R79 not reached); over the 29 logs (`model-check-all29.txt`) `R79x` fails 2 of 10
  (required), `R78y` 8 of 27, `R23x` 1, and no real entry mismatches. `regress` over the 38 kept rev 4 and rev 6 logs:
  byte-identical to S1b's `model-check.txt` (32 entries, 38 logs, 32 SEP lines).
- **Stops** over the 17 logs: R23 4 (3 `AIL`, 1 `no AIR line`), R41 18 and R32 82 (`a path action is not modelled`), no other entry.
- **Decisions, fork-free count and separation line per entry** (the checker's `model-check.txt`, over the 17 logs; separation line =
  distinct outcomes over the fork-free decisions, ADR-0028 item 7; an entry not in the list had 0 decisions):

| entry | decisions | fork-free | forked | mismatch | stop | separation line |
|---|---:|---:|---:|---:|---:|---|
| R3 | 46 | 46 | 0 | 0 | 0 | 3 over 46 |
| R5 | 200 | 200 | 0 | 0 | 0 | 5 over 200 |
| R7 and the notes row | 91 | 91 | 0 | 0 | 0 | 3 over 91 |
| R8 | 211 | 211 | 0 | 0 | 0 | 11 over 211 |
| R11 | 93 | 93 | 0 | 0 | 0 | 2 over 93 |
| R12 | 104 | 104 | 0 | 0 | 0 | 3 over 104 |
| R15 | 148 | 148 | 0 | 0 | 0 | 6 over 148 |
| R17 | 145 | 145 | 0 | 0 | 0 | 8 over 145 |
| R18 | 47 | 47 | 0 | 0 | 0 | 6 over 47 |
| R23 | 491 | 367 | 120 | 0 | 4 | 22 over 367 |
| R24 | 29 | 29 | 0 | 0 | 0 | 3 over 29 |
| R25 | 30 | 30 | 0 | 0 | 0 | 7 over 30 |
| R27 | 26 | 26 | 0 | 0 | 0 | 3 over 26 |
| R32 | 507 | 0 | 425 | 0 | 82 | none (all forked: its home and script words are not logged) |
| R38 | 41 | 41 | 0 | 0 | 0 | 4 over 41 |
| R39 | 76 | 76 | 0 | 0 | 0 | 4 over 76 |
| R40 | 14 | 14 | 0 | 0 | 0 | 2 over 14 |
| R41 | 200 | 0 | 182 | 0 | 18 | none (all forked, as R32) |
| R42 | 20 | 20 | 0 | 0 | 0 | 2 over 20 |
| R48 | 270 | 0 | 270 | 0 | 0 | none (all forked) |
| R49 | 82 | 82 | 0 | 0 | 0 | 9 over 82 |
| R52 | 400 | 400 | 0 | 0 | 0 | 4 over 400 |
| R54 | 140 | 140 | 0 | 0 | 0 | 1 over 140 (confirms it: the path is `4.idle`) |
| R56 | 76 | 0 | 76 | 0 | 0 | none (its `owner.mode` word is not logged, so its tests fork) |
| R57 | 52 | 52 | 0 | 0 | 0 | 3 over 52 |
| R65 | 53 | 53 | 0 | 0 | 0 | 5 over 53 |
| R78 | 13 | 13 | 0 | 0 | 0 | 2 over 13 |
| R94 | 21 | 21 | 0 | 0 | 0 | 5 over 21 |
| R95 | 149 | 149 | 0 | 0 | 0 | 6 over 149 |
| R96 | 108 | 108 | 0 | 0 | 0 | 7 over 108 |

  Entries aimed at by Phase 3a's cases and not reached (0 decisions in any of the 17 logs): R16, R43 (its `AII`/`AIQ` init pair of
  0x005F6630 is logged 3 times in `t-a2-oasis`, but no R43 think decision), R45, R50, R53, R66, R77, R80, R85, R92, R93, S5, S6.
  R79 (not an Act II or III aim) not seen. R60 and R59 are Act I rows (Phase 2) and stay untested.
- **Prediction 3 (decisions by case, from `words.txt`).**
  - Held: `t-a2-dryhills` R17 56, R18 47, R23 74; `t-a2-oasis` R15 85, R23 200, the `AII`/`AIQ` lines of 0x005F6630 (3 each),
    R38 2 and R40 7 (the conditional ones: the Maggot Lair rows were seen; the warps to 63 and 64 were not taken, the larva and egg
    came from level 43 and the tomb); `t-a2-lostcity` R8 69, R17 42, R95 23; `t-a2-canyon` R7 91, R15 67, R95 110; `t-a2-palace` R8 142,
    R11 30, R39 39; `t-a2-halls` R95 16; `t-a3-spider` R24 29, R27 6, R11 49; `t-a3-marsh` R25 30, R27 13, R52 200 (with R56 76 and R57 52,
    R65 4: not predicted, seen); `t-a3-flayer` R52 200, R65 42 (R78 13 also seen); `t-a3-lower` R17 47, R23 130, R48 13 (R11 14 not predicted,
    seen); `t-a3-upper` R23 87, R48 57; `t-a3-travincal` R49 76; `t-a3-durance` R39 37; `t-a2-town` R32 200, R41 200 (R42 20 seen); `t-a3-town` R32 10.
  - Not held: `t-a2-oasis` R43 (no think decision); `t-a2-lostcity` R16 (not seen); `t-a3-bazaar` R48 and R49 (not seen; the case's
    decisions are R27 7 with the mercenary and R32/R54 only, 224 decisions, `t-a3-bazaar` pool entries R48 and R49 not met); `t-a3-upper` R27
    (not seen; R49 6 seen); `t-a3-town` R41 (not seen; the walk ended at hop 1, "no target (level done)", 28 decisions in 27 s).
  - Conditional, not reached: R95 in `t-a2-dryhills` (not seen there; seen in 3 other cases), R94 predicted only in the canyon (seen in
    `t-a2-lostcity`, 21 decisions, 5 outcomes), R45 (not seen), R93 and R53 (the hunt for class 250 timed out: "class never seen"), R77
    and R92 (the loot walks sprang no trap), R66 (the hunt for class 284 timed out), R85 and R50 (the hunts for classes 345 and 242
    timed out), R77/R80/R92 in `t-a3-lower` (not seen).
- **Prediction 4**: R54 140 of 140 fork-free (as predicted), R78 13 of 13; R10, R79 not in these logs; the rev 7 word lines of
  `words.txt`: `AiNearestPlayer` 13 to 78 lines per log where R32 and R54 are present, `speed` (270 lines) and `MonsterOwnerRef` (192) for row 48's decisions in `t-a3-lower`, `t-a3-upper`, `t-a3-travincal`. R32 stays all-forked (its words are not in rev 7). R48's 270 decisions are all forked although `speed` is logged for all of them
  and `MonsterOwnerRef` for 192: the model's `3.ownertype=0`, `3.act=2` and `3.quest21` tests read words rev 7 does not log (`m_r48`).
- **Prediction 5, separations** above; R54's 1 outcome is reported as confirming it. Resume flip (`flip-rows.txt`, rows 3, 4, 5, 15, 23,
  26, 43, 52, 54, 63, 65, 68, 70, 78, 79, 96, 118, `--key rowthink --cap 1000000`; `flip-states.txt`, thinks 5e8140 and 5e8340, no
  decision): fork-free decisions 15@5f1800 148, 23@5f3170 367, 3@5efe20 46, 52@5f8260 400, 5@5f00e0 200, 65@5f9a80 53, 78@5fb6c0 5, 96@5e1250 108;
  every two-way site fails alone (`two_way_sep` = `two_way`) except 23@5f3170's 24th: the site 0x005F356C is two-way with `nosep` (11
  decisions, flipping it changes nothing the log shows), so R23's two-way count is 23 of 24; Phase 4 reads it. The raise itself is Phase 4's.
- **Observations, not claims.** (1) `t-a2-town` shows think 0x005E7590 (inventory row 81, no entry or model in this plan, Phase 1a's
  "not placed" list) with 5 decisions in the Act II town; it is a lead for the out-of-plan batch H1p. (2) R94 (the desert turret) was
  met in the Lost City, not the canyon the case table lists. (3) The runner's launch to the first waypoint failed once in the
  Act II batch (`t-a2-town`) and the waypoint click needed 2 tries in `t-a2-oasis` and `t-a3-flayer` (`wpfail-…` shots); no logger
  line is affected.
- **Contradictions:** none. 0 mismatches in every real entry; nothing is filed for the spec.
- **Not covered by this run:** Act IV, Act V and Nightmare (Phase 3b), the entries listed as not reached, R32's home and script
  words, the Phase 1c words of R56, R71, R85, R128 and `objects.py`'s lines (R56 stays all-forked), R68 (Act IV: the nested-call
  test covers the logged calls inside `AiVileMotherSpawn`, no Act IV log yet).

## run:2026-11-16-ai-tour-3

- **Question:** (plan 0069 Phase 3b, `lane/n69f`) Do the Act IV, Act V and Nightmare cases of plan 0069's tour (17 cases:
  `t-a4-town`, `t-a4-steppes`, `t-a4-cotd`, `t-a4-river`, `t-a4-chaos`, `t-a5-town`, `t-a5-foothills`, `t-a5-highlands`,
  `t-a5-plateau`, `t-a5-crystal`, `t-a5-glacial`, `t-a5-tundra`, `t-a5-halls`, `t-a5-wsk1`, `t-a5-wsk`, `nm-a5-crystal`,
  `nm-a5-wsk`) check with 0 mismatches against the models of Phases 1b and 1c, and which statements of the H1a to H1d, H1g and H1h
  batches do they reach (the raise itself is Phase 4's)? The aims named by the lane: R68, R118, R119, R128.
- **Setup:** as `run:2026-11-16-ai-tour-2`: `tools/gdb/ai.py` rev 7 (unchanged), slot 2, `--fresh` (one game process per case),
  every launch inside `systemd-run --user --scope -p MemoryMax=4G`, runner `tools/ai_sessions.py`, characters built by
  `ai_sessions.py build --saves workspace/logs/n69f/saves`, seeds the case table's (Act IV 7055, Act V 6908, Nightmare 6927), checker
  `tools/ai_model_check.py` revision 6 and `tools/ai.py`. Batches by seed: Act IV under run id `2026-11-16-ai-tour-3` (7055), Act V under
  `2026-11-16-ai-tour-3b` (6908), Nightmare under `2026-11-16-ai-tour-3c` (6927), so that launch numbers are not reused. R56, R85,
  R32's home and script words stay unlogged (no logger change).
- **Predictions** (committed before the first kept log; predicted pools: `workspace/logs/n69a/pools.txt`):
  1. Every kept log's first logger line is `AI logger armed rev 7 bmax 48`; `ai.py check` gives 0 mismatches over the 17 logs.
  2. `ai_model_check.py check --logs` over the 17 logs together with the 29 of Phases 2 and 3a gives 0 mismatches for every entry
     except the control `R79x` (2, as required; a stop is allowed); `regress` over the 38 kept rev 4 and rev 6 logs stays
     byte-identical.
  3. Decisions by case (each at least 1, from the predicted pools; the town cases need the NPC near the player):
     - `t-a4-town` (stay in town): R32 and R54. `t-a4-steppes` (104: fingermage1, regurgitator1, doomknight1): R72; R55 only if the
       hunt for 256 (Izual) reaches him.
     - `t-a4-cotd` (106: bighead5, vilemother2, regurgitator2): R4, R68 (with the calls logged inside `AiVileMotherSpawn` between its
       AIB and AIR lines) and R71; R70 and R73 only if their units are met.
     - `t-a4-river` (107: blunderbore4, vilemother3, doomknight2): R39, R68, R73; R70, R71 conditional; R33, R98, R100 only if the
       hunt for 409 (Hephasto) reaches him.
     - `t-a4-chaos` (108: fingermage3, doomknight3, megademon3): R74 and R70.
     - `t-a5-town`: R32; S5, S6 not predicted. `t-a5-foothills` (110: overseer1, imp1): R120, R122; R116, R123, R126, R129 conditional.
     - `t-a5-highlands` (111: siegebeast2, imp1): R115, R122. `t-a5-plateau` (112: minion2, overseer2): R116, R120.
     - `t-a5-crystal` (113: succubus3, frozenhorror1, bloodlord1): R124 and **R118**; R80 only if the loot walk springs a trap.
     - `t-a5-glacial` (115: reanimatedhorde2, frozenhorror2, deathmauler3): R114, R124. `t-a5-tundra` (117: siegebeast2, imp4): R115, R122.
     - `t-a5-halls` (123: reanimatedhorde4, deathmauler2, putriddefiler1): R137, R114; **R128** only if the hunt for 526 (Nihlathak)
       reaches him (the warp 77 to 124 is not taken in 3a's experience; a timed out hunt is reported as such).
     - `t-a5-wsk1` (128: reanimatedhorde5, succubuswitch2, putriddefiler3): **R119**, R137; R136, S15 not predicted.
     - `t-a5-wsk` (129: minion7, suicideminion6; 130: imp5, bloodlord5, putriddefiler4): R116, R117, R137, if the warp 82 to 130 is taken.
     - `nm-a5-crystal` (Nightmare 113: frozenhorror1, bloodlord3, clawviper6): R142. `nm-a5-wsk` (129: suicideminion6, clawviper10,
       willowisp6; 130: overseer4, fetishblow8, dkmag2): R142, R25; R74 only if the warp is taken.
  4. Word lines as in `run:2026-11-15-ai-tour-1` prediction 4: each R10, R54, R32, R78, R79 decision carries its word line and is
     fork-free where the fork was only that word.
  5. Separation lines and decision counts per entry are reported as the checker prints them; a row with 1 outcome is reported as
     confirming it. Sharing: fresh per case, as in Phases 2 and 3a.

### Results of `run:2026-11-16-ai-tour-3` (plan 0069 Phase 3b, `lane/n69f`)

Kept outputs in `workspace/logs/n69f/` (`manifest.sha256`, 84 lines, `sha256sum -c` passes from that directory; paths are `../ai/…` and
local names): the 17 launch logs with their marks and per-case logs (`split`), the three pilot files, the screenshots, the status
files and the runners' stdout (`batch-a4-stdout.txt`, `batch-a5-stdout.txt`, `batch-nm-stdout.txt`), and the checks
(`model-check.txt` over the 17 kept logs, `model-check-all46.txt` over them and the 29 of Phases 2 and 3a, `ai-check.txt`, `words.txt`,
`flip-rows.txt`, `flip-states.txt`, `regress.txt`, `r118-probe.txt`, each with its stdout; the log lists `logs-tour3.txt` and
`logs-all46.txt`). Tools at the commit of this entry: `tools/gdb/ai.py` rev 7 (unchanged), `tools/ai_model_check.py` revision 6
(unchanged), `tools/ai.py`, `tools/ai_tour_words.py`, `tools/ai_resume_flip.py`, `tools/ai_r118_probe.py` (new, read-only). Slot 2,
`--fresh` (one game process per case), every launch under `MemoryMax=4G`. Three batches: Act IV under run id `2026-11-16-ai-tour-3`
(seed 7055), Act V under `-3b` (6908), Nightmare under `-3c` (6927); launch numbers L1 to L5, L1 to L10, L1 and L2. Predictions were
committed at `13c02e50`, before the first kept log.

| case | seed | launch (pid) | position (level) | decisions | wall |
|---|---|---|---|---|---|
| `t-a4-town` | 7055 | L1 (1467459) | Pandemonium Fortress 103, walk ended at hop 2 ("no target, level done") | 13 | 21 s |
| `t-a4-steppes` | 7055 | L2 (1468931) | 104, border walk (60 hops, stopped at hop 54 with 125 rooms left), hunt 256 timed out (class never seen) | 383 | 184 s |
| `t-a4-cotd` | 7055 | L3 (1481260) | 106, sweep 240 s | 482 | 268 s |
| `t-a4-river` | 7055 | L4 (1487723) | 107, sweep, hunt 409 timed out (class never seen) | 446 | 287 s |
| `t-a4-chaos` | 7055 | L5 (1494029) | 107, sweep 30 s, border walk 60 hops (frontier 499 rooms; level 108 not entered) | 319 | 149 s |
| `t-a5-town` | 6908 | L1 (1497519) | Harrogath 109, walk ended at hop 6 ("no target, level done") | 121 | 35 s |
| `t-a5-foothills` | 6908 | L2 (1498409) | 109, border walk (80 hops), 110 | 646 | 186 s |
| `t-a5-highlands` | 6908 | L3 (1502682) | 111, sweep | 344 | 227 s |
| `t-a5-plateau` | 6908 | L4 (1508098) | 112, sweep | 351 | 168 s |
| `t-a5-crystal` | 6908 | L5 (1513058) | 113, sweep, loot walk (60 hops) | 391 | 247 s |
| `t-a5-glacial` | 6908 | L6 (1518367) | 115, sweep | 241 | 226 s |
| `t-a5-tundra` | 6908 | L7 (1524192) | 117, sweep | 340 | 227 s |
| `t-a5-halls` | 6908 | L8 (1530720) | 123, sweep; descent 77 to 124 not made ("4 hops without moving", time out); hunt 526 timed out (class never seen) | 702 | 568 s |
| `t-a5-wsk1` | 6908 | L9 (1544581) | 129; "every room activated or skipped, no warp 81 to 128" (level 128 never entered) | 537 | 247 s |
| `t-a5-wsk` | 6908 | L10 (1550669) | 129; "no warp 82 to 130" (level 130 never entered) | 563 | 260 s |
| `nm-a5-crystal` | 6927 | L1 (1557469) | Nightmare 113, sweep | 398 | 227 s |
| `nm-a5-wsk` | 6927 | L2 (1563506) | Nightmare 129; "no warp 82 to 130" | 475 | 176 s |

Cases kept: 17 of 17 (Act IV 5, Act V 10, Nightmare 2); 0 reruns, 0 failed launches. Decisions per case are `words.txt`'s `DECISIONS` lines
(the runners' stdout counts `t-a4-river`, `t-a4-chaos`, `t-a5-crystal`, `t-a5-glacial`, `t-a5-halls`, `t-a5-wsk1`, `t-a5-wsk` and `nm-a5-wsk` one lower).
Decisions in the 17 kept logs: 6 752 (`ai.py check`: `CHECK logs=17 decisions=6752 ain=7746 sst=641 caps=24`). Wall of the 17 cases: 3 703 s (the batches' own totals 909 s, 2 391 s and 403 s).
Sharing decision: fresh per case, unchanged.

- **Prediction 1 held.** All 17 logs open with `AI logger armed rev 7 bmax 48` (`words.txt`). `ai.py check` over the 17 logs: 6 752
  decisions, 0 mismatches (`ai-check.txt`, its `TOTAL` line).
- **Prediction 2 held in part: one entry fails, R118.** `ai_model_check.py check --logs` over the 17 logs: 95 entries, **0 mismatches in
  every entry but R118** (12; below). Over the 46 logs (`model-check-all46.txt`) the only entries with mismatches are R118 (12), and the
  controls as required: `R78y` 8 of 27, `R79x` 2 of 10, `R23x` 1 of 613 (all three have 0 decisions in the 17 logs of this run; the counts
  are those of the earlier logs). `regress` over the 38 kept rev 4 and rev 6 logs: byte-identical to S1b's `model-check.txt` (32 entries,
  38 logs, 32 SEP lines; `regress.txt`). Stops over the 17 logs: R118 16, R32 61, R4 1, R39 1.
- **Decisions, fork-free count and separation line per entry** (`model-check.txt`, the 17 logs; separation line = distinct outcomes over the
  fork-free decisions, ADR-0028 item 7; an entry not in the list had 0 decisions):

| entry | decisions | fork-free | forked | mismatch | stop | separation line |
|---|---:|---:|---:|---:|---:|---|
| R1 | 41 | 41 | 0 | 0 | 0 | 1 over 41 |
| R4 | 100 | 99 | 0 | 0 | 1 | 3 over 99 |
| R7 and the notes row | 6 | 6 | 0 | 0 | 0 | 1 over 6 |
| R25 | 163 | 163 | 0 | 0 | 0 | 8 over 163 |
| R32 | 499 | 0 | 438 | 0 | 61 | none (all forked: its home and script words are not logged) |
| R33 | 18 | 18 | 0 | 0 | 0 | 2 over 18 |
| R39 | 150 | 149 | 0 | 0 | 1 | 4 over 149 |
| R54 | 88 | 88 | 0 | 0 | 0 | 1 over 88 (confirms it) |
| R68 | 104 | 104 | 0 | 0 | 0 | 6 over 104 |
| R69 | 91 | 91 | 0 | 0 | 0 | 5 over 91 |
| R70 | 13 | 13 | 0 | 0 | 0 | 3 over 13 |
| R71 | 120 | 117 | 3 | 0 | 0 | 10 over 117 |
| R72 | 35 | 35 | 0 | 0 | 0 | 4 over 35 |
| R73 | 98 | 98 | 0 | 0 | 0 | 6 over 98 |
| R99 | 86 | 86 | 0 | 0 | 0 | 2 over 86 |
| R100 | 13 | 13 | 0 | 0 | 0 | 1 over 13 (confirms it) |
| R114 | 212 | 212 | 0 | 0 | 0 | 6 over 212 |
| R115 | 20 | 20 | 0 | 0 | 0 | 4 over 20 |
| R116 | 739 | 739 | 0 | 0 | 0 | 4 over 739 |
| R117 | 164 | 164 | 0 | 0 | 0 | 4 over 164 |
| **R118** | 44 | 8 | 8 | **12** | 16 | 2 over 8 |
| R120 | 31 | 0 | 31 | 0 | 0 | none (all forked) |
| R122 | 320 | 320 | 0 | 0 | 0 | 15 over 320 |
| R123 | 3 | 3 | 0 | 0 | 0 | 2 over 3 |
| R124 | 87 | 87 | 0 | 0 | 0 | 6 over 87 |
| R126 | 33 | 24 | 9 | 0 | 0 | 2 over 24 |
| R129 | 11 | 9 | 2 | 0 | 0 | 3 over 9 |
| R130 | 246 | 246 | 0 | 0 | 0 | 5 over 246 |
| R136 | 151 | 151 | 0 | 0 | 0 | 3 over 151 |
| R137 | 81 | 81 | 0 | 0 | 0 | 5 over 81 |
| R142 | 131 | 131 | 0 | 0 | 0 | 11 over 131 |
| S16 | 8 | 8 | 0 | 0 | 0 | 3 over 8 |

  The four aimed entries: **R68 reached** (104 decisions, 0 mismatches, 6 outcomes; the calls logged inside `AiVileMotherSpawn` between
  AIB and AIR lines are dropped by `top_level` as the 3a test states, so the model needed no change); **R118 reached, 12 mismatches**
  (below); **R119 and R128 not reached** (0 decisions: no warp 81 to level 128 from 129 was found, and the descent 77 to 124 and the hunt
  for 526 did not reach Halls of Vaught or Nihlathak). Entries aimed at by Phase 3b's cases and not reached (0 decisions in any of the 17
  logs): R55, R74, R98, R119, R128, R80 and S15. Reasons: R55 (hunt 256 timed out), R74 (levels 108 and 130 not entered), R98 (hunt 409 timed out), R119 and R128 as above; R80 and S15 had no decision in any of the 17 logs (no further reason is recorded). R56, R85 and R32's unlogged
  words are as in `run:2026-11-16-ai-tour-2`: R32 stays all-forked (499 decisions, 0 fork-free); R85 had no decision.
- **R118: 12 mismatches, named as a contradiction candidate.** All 12 are in `t-a5-crystal` (44 R118 decisions, unit class 471, the only log
  with R118): 5 `4.idle` seeds, 2 `4.walk` calls and 5 `2.setmode4` (3 seeds, 2 calls) where the model's seed (two steps) or its chosen call
  (Walk 0x005DEC80, SetModeAtUnit 0x005DDF90) differs from the log's (one step; `Idle` 0x005DE080 at 0x005E210E or 0x005E202A). `tools/ai_r118_probe.py` over the
  `t-a5-crystal` log (`r118-probe.txt`, 44 decisions): the 12 far decisions (dist ≥ aip(4)) take one seed step each and the model matches
  all 12; of the 32 near decisions (dist < aip(4)), the 25 with the rev 7 word logged all take exactly one seed step (12 mismatch,
  13 stop), and of the 7 without the word 4 take two steps (model ok, forked) and 3 take one (stop). The probe's second tally (first boundary of the near
  decisions, `r118-probe.txt`): the 25 with the word logged call `SetModeAtUnit` (6), `Idle` (9) or `Walk` (10) first, none enters the
  curse arm; the 3 that call `UnitGetMaxHp` 0x00625D10 (the arm's test, 0x005E1F3B) are among the 7 without the word line. The model's
  chance(3) draw plus the later chance draw gives two steps for a near decision whose chance(3) fails; the log has one. Reading `[I]`,
  unresolved at the lane's time box: the 25 behave as if the flag test at 0x005E1E36 had been taken (no step-1 draw, one draw for the
  later test, no curse), while the rev 7 word `R118.flag0x20` (EAX at 0x005E1E34) reads 0 in all 33 lines that carry it, which
  the model reads as "not taken". Either the word does not read what row 118 says, or the flag differs from the word at the test.
  Other readings the same data allow: the `dist` or `aip(4)` the test at 0x005E1E45 compares differs from the checker's `ctx[5]` and `aip(4)`; or the rev 7 word breakpoint at 0x005E1E34 perturbs the path (the 7 near decisions with no word line behave as the model does). Both exits of the tests at 0x005E1E36 and 0x005E1E48 go to 0x005E1FBE, so no change of the block's structure gives one step.
  Catalogue rows 347 and 348 stay `[I]`; the far case (12 decisions) matches. Filed for the spec and the
  architect: backlog entry `2026-11-16-reverser-spec-writer+architect-plan-0069-p3b-r118-step-1-draw-contradiction`.
  - **Read again 2026-11-16 (logger rev 8, `lane/n69h`, architect review):** the word above is not the call's result. Rev 7's `w_eax` (`tools/gdb/ai.py`) was `s32(reg("eax"))` and `s32` reads memory, so `R118.flag0x20` held the dword at the address in EAX, and a decision whose `StatListFindFlag` returned 0 raised a `MemoryError` and wrote no line. The 33 lines are decisions with the flag set (the `jne` at 0x005E1E36 taken: one step), the 7 near decisions without a line are flag 0 (two steps, as modelled), and the 12 mismatches are the checker reading a dereferenced word as the flag. `[I]` (the logger source, git history of `tools/gdb/ai.py` at 30c71622 and e6d746ed, 0x005E1E2F, 0x005E1E34); no kept log yet reads EAX itself, so rows 347 and 348 stay `[I]` until a kept rev 8 run. The checker keeps the rev 7 reading of rev 7 logs (so `regress` and this run's `model-check-all84.txt` stay byte-identical): its R118 and R119 results on rev 7 logs that carry the word are not evidence about the block.
- **Prediction 3 (decisions by case, from `words.txt`).**
  - Held: `t-a4-town` R32 6, R54 2; `t-a4-steppes` R72 35; `t-a4-cotd` R4 100, R68 44, R71 56; `t-a4-river` R39 81, R68 31, R73 62, R33 18
    and R100 12 (the conditional ones, with R98 not seen); `t-a5-town` R32 81; `t-a5-foothills` R116 90 and R126 21 (conditional);
    `t-a5-highlands` R115 7, R122 169; `t-a5-plateau` R116 168, R120 31; `t-a5-crystal` R124 65 and R118 44; `t-a5-tundra` R115 13, R122 150;
    `t-a5-halls` R137 81, R114 200; `t-a5-wsk` R116 200, R117 68; `nm-a5-crystal` R142 22; `nm-a5-wsk` R142 109, R25 163.
  - Not held: `t-a4-steppes` R55 (hunt timed out), `t-a4-chaos` R74 and R70 (level 108 not entered, 319 decisions in 107: R73 36, R39 69),
    `t-a5-foothills` R120 and R122 (not seen there; R120 in the plateau, R122 in the highlands and tundra), `t-a5-glacial` R124 (not seen;
    R114 12, R130 12), `t-a5-wsk1` R119 and R137 (level 128 not entered; R116 200, R117 66, R136 54), `t-a5-wsk` R137 (level 130 not
    entered), `nm-a5-wsk` R74 (conditional on level 130), `t-a5-halls` R128 (conditional: Halls of Vaught not entered).
  - Seen, not predicted: R70 13 and R71 64 in `t-a4-steppes`, R69 37 and R99 86 in `t-a4-cotd`, R69 25 in `t-a4-river` and `t-a4-chaos`,
    R1 in the Act V cases, R130 in the Act V cases, R136, R129 11 in the highlands, R123 3 in the tundra, R7 6 in `t-a5-crystal`.
- **Prediction 4**: R54 88 of 88 fork-free (as predicted, 1 outcome); R10, R78, R79 not in these logs; the rev 7 word lines of `words.txt`:
  `AiNearestPlayer` 14 lines where R32 and R54 are present in a case, `R73.aurastate` and `R73.md0e` 36 lines in `t-a4-chaos`.
- **Prediction 5, separations** above. Resume flip (`flip-rows.txt`, rows 3, 4, 5, 15, 23, 26, 43, 52, 54, 63, 65, 68, 70, 78, 79, 96, 118,
  `--key rowthink --cap 1000000`; `flip-states.txt`, thinks 5e8140 and 5e8340, no decision in these logs): the rows with decisions here
  are R118 (44 resumed: 11 sites, 10 separate, 1 `nosep` at 0x005E203B, 4 two-way all separate), R4 (99: 9 sites, 8 sep, 1 `nosep`,
  3 two-way all sep), R54 (88: 3 sites, 3 `nosep`: the same `Idle` follows every branch), R68 (104: 11 sites, 11 sep, 5 two-way all sep) and
  R70 (13: 12 sites, 11 sep, 1 `nosep`, 2 two-way all sep). Phase 4 reads them. The raise itself is Phase 4's.
- **Observations, not claims.** (1) `t-a5-wsk1` and `t-a5-wsk` stood in level 129 and found no warp 81 or 82 (the pilot's "every room
  activated or skipped"): R119's pool level 128 and the Worldstone 130 cases (R74, R137) need another route; this is a lead for a later rerun.
  (2) `t-a4-chaos` never left the River of Flame (107): the border walk of the case table did not reach Chaos Sanctuary. (3) A `LOGERR ai f
  MemoryError('Cannot access memory at address 0x0')` line (the `f` reader of `w_nearest`, a logged rev 7 word with the pointer 0) sits in
  the R118 decisions without a word line; the word lines of the others are unaffected. It is a lead for the logger, not a claim. Read again at the rev 8 review: the `f` in that line is also the name of every rev 7 word reader (`on_word`), and the R118 decisions reach no `AiNearestPlayer` site, so the line is `R118.flag0x20`'s reader dereferencing EAX 0 (above).
- **Contradictions:** one, R118 above (filed). 0 mismatches in every other real entry.
- **Not covered by this run:** R119, R128, R55, R74, R98 (Act IV and V, not reached), R32's home and script words, R56 and R85 (rev 7 does
  not log their words), R10, R78, R79 (no decision in these logs).
- **Addendum 2026-11-16: plan 0069 Phase 4, the settle** (`lane/n69g`, static, no game; tools at the commit of this entry:
  `tools/ai_model_check.py` revision 6, unchanged, sha256 `257e3fac…`; `tools/ai_resume_flip.py` `98484cb5…`, `tools/ai_resume.py`
  `187dcaaf…`, both unchanged; `tools/ai_tour_settle.py` new, `105e9fee…`, its test `tools/test_ai_tour_settle.py`, 5 tests OK). The 84
  logs: the 38 kept rev 4 and rev 6 logs of S1b and the 46 tour logs of this run, run:2026-11-15-ai-tour-1 and run:2026-11-16-ai-tour-2
  (`workspace/logs/n69g/logs-all84.txt`; per group `logs-kept38.txt`, `logs-tour1.txt`, `-tour2`, `-tour3`). Outputs in
  `workspace/logs/n69g/`, `manifest.sha256` (105 lines: the 21 outputs and the 84 logs as `../ai/…`; passes from that directory).
  - **Procedure** (from `workspace/logs/ai`, each replay under `systemd-run --user --scope -p MemoryMax=4G`): `ai_model_check.py check
    --logs ../n69g/logs-all84.txt` (`model-check-all84.txt`) and the same per group (`model-check-kept38.txt`, `-tour1`, `-tour2`,
    `-tour3`); `ai_resume_flip.py check <84 logs> --rows 1,7,23,26,32,43,48,49,54,70,71,73,78,79,95,100,114,118,124 --key rowthink --cap
    1000000` (`flip-rows-all84.txt`) and `ai_resume.py check <84 logs>` on the same rows (`resume-all84.txt`, the `RROW` mismatch counts);
    `ai_model_check.py regress` (`regress.txt`: byte-identical, 32 entries, 38 logs). Then `ai_tour_settle.py`: `entries` (S1b's rule per
    entry: 0 mismatches over all the entry's decisions, at least 30 fork-free, each named branch and store classed by its `ARM` and `FLIP`
    lines, `entries.txt`), `runs` (the log groups holding each entry's decisions, `runs.txt`), `h1` (sentence H1's four tests per row's own
    think, `h1.txt`), `inits` (the rev 7 `AII`/`AIQ` pairs, `inits.txt`), `tally` and `ready` over the inventory file (`tally.txt`,
    `ready.txt`).
  - [C] (run:2026-11-15-ai-tour-1, run:2026-11-16-ai-tour-2, run:2026-11-16-ai-tour-3, `model-check-all84.txt`, `entries.txt`, 0x005B186F)
    **S1b's block rule is met on the logged paths** (0 mismatches over every decision of the entry, at least 30 fork-free, each raised arm's
    branch failing alone) by these entries of the tour's batches (decisions, fork-free): R7 and the notes row (0x005EFB80) 131, 131;
    R8 (0x005F0700) 211, 211; R10 (0x005F0B00) 302, 302, with the rev 7 `MonPlayerBonus` word; R11 (0x005F0CD0) 93, 93; R14 (0x005F1140)
    77, 77; R142 (0x005F1DE0) 131, 131; R17 (0x005F20A0) 145, 145; R18 (0x005F22B0) 47, 47; R25 (0x005F39B0) 193, 193 (gather trigger,
    state 1 and states 0, 2, 3; the dance separates nothing, the grant and state 4 are not run); R36 (0x005F5D50) 32, 32; R38 (0x005F6220)
    41, 41; R39 (0x005F6340) 226, 225; R49 (0x005F72D0) 99, 99; R57 (0x005F9270) 52, 52; R71 (0x005FA710) 129, 126; R72 (0x005FAA90) 35, 35;
    R73 (0x005FAB80) 269, 98 (the rev 7 ones); R114's `+0xC4 |= 0xE` (0x005E1540, 243, 243: skipped alone it fails 15); R116 (0x005E1B60)
    739, 739; R117 (0x005E1D30) 164, 164; R122 (0x005E2FF0) 320, 320; R136 (0x005EF710) 151, 151; R137 (0x005EFA90) 81, 81; R1
    (0x005B0CD0) 86, 82 (the rev 7 window; the no-room arm never met); R54 (0x005E73A0) 618, 316 (one outcome, `4.idle`: its first call
    and its exit seed, no branch separated). The arms, stores and equal pairs raised per row are in the inventory rows
    (`0066-inventory/monsters-ai-catalogue.md`, the rows `ready.txt` lists).
  - [C] (run:2026-11-15-ai-tour-1, run:2026-11-16-ai-tour-2, run:2026-11-16-ai-tour-3, `h1.txt`, `resume-all84.txt`, `flip-rows-all84.txt`)
    **Sentence H1's rule is met** (0 mismatches, at least 50 fork-free, a call past the first, every two-way site failing alone) by the
    own thinks of row 7 (0x005EFB80: 131, 212 past the first, 3 of 3), row 26 (0x005F4510: 75, 145, 7 of 7), row 49 (0x005F72D0: 99,
    385, 12 of 12), row 71 (0x005FA710: 126 of 129, 161, 12 of 12), row 95 (0x005E1080: 192, 219, 9 of 9), row 114 (0x005E1540: 243,
    221, 8 of 8) and row 124 (0x005E3530: 135, 406, 6 of 6). Logged paths only; no role or symbol is raised.
  - [I] (`entries.txt`, `h1.txt`, `inits.txt`, 0x005F6630, 0x005E1E36) **Not met:** under the block floor of 30 fork-free: R24 29, R27 26,
    R33 18, R40 20, R94 21, R115 20, R123 3, S16 8, R126 24, R129 9, R42 20, R100 17, and R43's init 0x005F6630 (9 `AII`/`AIQ` pairs in 3
    logs; `v14` equals the line's frame after the call in 9 of 9, the word before differing in all 9; `v18` 0 before and after); all
    forked: R32 2 226 (364 stop at the path action), R41 200, R48 391, R56 76, R120 31; R23 8 mismatches (the rev 4 cluster, unchanged)
    with a two-way site that fails nothing (24 of 25); R118 12 mismatches (the Phase 3b ruling holds it); state 11's init 0x005E80E0
    (17 pairs, the control block unchanged, its calls not logged). H1 not met by rows 43 (37 fork-free), 79 (19), 100 (17), 78 (no call
    past the first) and 32, 48, 54, 70, 73, 118 (0 fork-free: the resume interpreter forks on words it does not take from rev 7's lines). Row 1's `RROW` in `resume-all84.txt` (86 decisions, 4 resumed, 82 "mismatches") is the interpreter's window, not the
    game: `tools/ai_resume.py`'s `THINK_WINDOWS` lacks rev 7's R1 window 0x005B0CD0..0x005B0D00 (`tools/gdb/ai.py` `THINK_LO`), so at
    0x005B0CDC, where the 82 rev 7 decisions log `UnitGetRoom` 0x00620BB0, it offers no call ("the model has no further call"). R1's `r`
    line is d-none and outside this phase; its `l` line rests on `ai_model_check.py` (0 mismatches, 82 fork-free). (Added at the Phase 4
    review.)
    Not reached (0 decisions in the 84 logs): R16, R74, S15, R119, S5, S6, R58, R60, R45, R66, R77, R80, R92, R50, R53, R55, R59, R85,
    R128, R93, R98, and the alts 0x005F81D0 and 0x005F9950; their rows wait on the owner (a rerun with a changed route, or d-owner).
  - **Rows:** 211 settled (the 241 of the tour's scope less Phase 1a's 30 moved to H1p): 22 raised, 41 raised in part, 148 kept
    (`tally.txt`). No contradiction is new; no symbol row is raised (the models feed on the logged returns as oracles and compare the
    calls, not the callees' roles, as at S1b).

## run:2026-11-16-sweep2-s1f

Plan 0066 Phase 1, batch S1f part 1 and batch S1o part 1 (reverser-static, `lane/n66x`). A static second source: no game,
no Ghidra, no harness slot. Tool `tools/ai_s1fo.py` (`22acb79b…`; sections `entry`, `tables`, `init`, `more`, `totals`),
built on the helpers of `tools/quests_s3c.py`, `tools/skills_s2c.py` and `tools/sweep2_s7a.py`: every reference scan three
ways (raw-byte rel32/abs32, objdump's linear listing, r2 re-decoding each site), every claimed instruction decoded by
objdump and by r2 (both must agree and match), call arguments by two walkers, image words by Python and by r2 `pxwj`, table
cells by the plain `.txt` reader and by the compiled `.bin`. Kept output `workspace/logs/n66x/s1fo/check-s1fo-p1.txt`
(`89bffa81…`, 91 check lines, `S1fo total bad=0`), `manifest-s1fo-p1.sha256` (`24ec251c…`) passing from
`workspace/logs/n66x/s1fo`; development outputs (and the same run taken before merging `main` `858b7eea`, `check-s1fo-p1-premerge.txt`, which differs only in the totals line) in `dev/` with `manifest-dev.sha256`. Run under a 4 GB scope, about 30 s.

- **Case.** The pinned `Game.exe` and the merged excel tables; the check names give the inventory rows (C catalogue, M
  machinery, R README of `docs/plans/0066-inventory/monsters-ai-*.md`).
- **Process.** `python3 -I tools/ai_s1fo.py all` once; every count line is the check's own.
- **Results (each `[C]` by the second tool, at the scope stated):**
  - *The event and the think call* (C1, R1, R2, R16). `g_MonEventFuncs[2]` = 0x005B1740 by both readers; `MonAiEvent`'s
    only reference in the image is that slot (abs32 at 0x006E2498; 0 rel32 by all three tools). Nine `.text` loads of the
    slot, each followed by `call eax` at 0x005A80F5, 0x005A813F, 0x005A818E, 0x005A81ED, 0x005A822E, 0x005A8267,
    0x005A82AD (`MonModeEndGeneric`, 7), 0x005A83D1 (`MonModeEndToS1`) and 0x005A8481 (`MonModeEndToS1b`); the table
    base's one other `.text` user is `MonEventDispatch` (0x005A7FC2). The think call: `mov eax,[ebp-0x24]; mov
    eax,[eax+0x4]; lea edx,[ebp-0x24]; push edx; call eax` (0x005B1861–0x005B186F), after the three pre-steps at 0x005B1806,
    0x005B1817, 0x005B1828; the second stops the event on a non-zero return (`test eax,eax; jne`, 0x005B181C).
  - *The two AI tables* (C2, C16, C274, C275, C372, C440, C443, C473, R4, R26, M1, M57). Read twice, equal. The only
    `.text` operands into 0x0073CA18–0x0073D477 are `MonAiEntryGet`'s three (0x005B1618, 0x005B1635, 0x005B163D), and no
    aligned data dword points into them. `MonAiEntryGet` has 3 calls in 2 functions: `MonAiTargetByKind` reads the stored
    state's row at `+0` only (0x005B1655–0x005B1673); `MonAiInit` reads `+8` and `+0xC` of the current state's row and
    stores `state` and `alt` (0x005B0E77–0x005B0E99), and calls `[row+4]` and stores `state` and `think` (or 0x005B0CD0)
    from the new state's row (0x005B0EBE–0x005B0F2D). Alias words: state 1 = row 1 (0x005B0CD0), state 4 = row 61 (think
    and alt), state 5 = row 60, state 7 = row 67, state 15 = row 117; these five are the only state rows whose think is a
    first-table think; 10 and 17 share 0x005E8020, in no first-table row. The four dwords after state row 17 point to
    "English", "Spanish", "German", "French"; `MonAiInit` bounds the state with `cmp ebx,0x12; jge` (0x005B0E4D). 147
    distinct thinks, rows 106 and 143 sharing; 146 rows named by the 734 MonStats records (`.txt` and `.bin` alike), 0
    `None` and 143 `ShadowMasterNoInit` not. Kinds 0: 26, 1: 104, 2: 16, 4: 1 (15), 5: 1 (52); 19 inits, 11 alts. Row 0's
    think is `c2 04 00`; row 1's `AiIdle` calls `MonAiIdle(200)` after the room test (0x005B0CD7–0x005B0CE9). Of the 18 tier
    rows only 29 and 61 have an alt, none an init, kind 0 only 61 and 67. Rows 145, 146, 147 are `c2 04 00`; 145's alt
    0x005FCF30 is also rows 135 and 140's, 147's 0x005E8480 also row 51's. Row 60 has one record, 270 `rogue2`, and no
    `*aip` description in `monai.txt`. The kind switch (table 0x005B1720): 1 → `MonAiTargetOrIdle`, stop when the target is
    0; 2 → `MonAiFindTarget`, go on; 4 → `MonAiTargetOrWait`, stop when 0; 5 → the same, go on; 3 and above 5 → stop;
    `MonAiFindTarget`'s 11 direct callers include `MonAiTargetByKind` 0x005B16B9, `MonAiTargetOrIdle` 0x005DE8AD and
    `MonAiTargetOrWait` 0x005DE9E9.
  - *`MonAiInit`'s callers* (C514, R3, R34, R35). 33 direct calls by all three tools in 28 functions, no jump or dword
    reference; state argument by both walkers: 21 immediates (0: 11, 5: 2, 6: 2, 10, 11, 13, 15: 1 each, 16: 2) and 12
    registers, none of the immediates 1–4, 7–9, 12, 14 or 17. The register sites' last writes, decoded twice:
    `InactiveMonstersRestore` `[ebx+0x28]` (the record word `InactiveMonsterSave` stores from `[eax+0x28]` at 0x005422C9 →
    0x005422D7), `SpawnOwnedMonster` `[ebx+0xc]`, `CurseSetAiState` `esi` (twice), 0x005E817B `eax` after a call, and the
    seven alts' `[reg]` loads. `MonsterInit` 0x00574307 passes 0. `SpawnOwnedMonster` has 15 direct calls in 14 functions.
  - *Row details.* C73: row 23 (`Vulture`, 0x005F3170) is kind 1; `test edi,edi` at 0x005F3184, 0x005F31D3, 0x005F325D,
    0x005F33C1. C87/C89: from the think's entry 0x005F39B0 to 0x005F3E07 no control transfer; 132 dword frame stores in
    0x005F39E1–0x005F3E07 (immediates, or a register holding a constant), objdump and r2 equal, 56 in `A`, 56 in `B`, 10 in
    `A5`, 10 in `B5`, every entry written, none outside; the one `(0, 0)` of `B` is entry 52 (`v14` 12, place 4) and `B5`
    has none. C155: the filter tests at 0x005F99E8 (`[esi+0x18]` against the 0 left by `test eax,eax; jne` at 0x005F99DC),
    0x005F9A06/0x005F9A0D (classes 141, 396), 0x005F9A14 (`= 1`), 0x005F9A24 (`< 3`, then `MonTypeFlag`); row 65's eight
    records' `aip2` Normal/Nightmare/Hell: `fetishshaman1`–`2` 0/1/2, `3` 0/2/2, `4`–`8` 0/2/3, `.txt` and `.bin` equal.
    C236: `pgsv` rows 122–127, the six `progressive_*`, in both readers. C244: `lea ebx,[ebx+ecx*4+0x3]` (0x005EC19F),
    case 8's `lea esi,[eax+eax]` (0x005EC31F) and `add esi,esi` (0x005EC328), `cmp esi,[ebp+eax-0x450]` then `jle`
    (0x005EC4FF, signed); the bounds computed: (−32 768)² = 1 073 741 824, (−32 769)² = 1 073 807 361 ≤ 2³¹ − 1; 4·(2²⁹ − 1)
    = 2 147 483 644, 4·2²⁹ → −2³¹, 4·(−2²⁹) = −2³¹, 4·(−2²⁹ − 1) → 2 147 483 644; 2·2³⁰ → −2³¹, 2·(2³⁰ − 1) = 2 147 483 646;
    2³¹ ÷ 10 = 214 748 364. Skills `aitype`: 357 rows, 32 non-zero, values 1–5 and 10–13 (no 8), maximum 13, `.txt` and
    `.bin` equal. C245: the record index is 20·k (`lea eax,[ecx+ecx*4]`, `add eax,eax` twice) and five dwords are stored
    at `EBP−0x444 + 20k` (0x005EC50B–0x005EC52F), so (0x444 − 0x84) ÷ 20 = 48 records fit above `EBP−0x84`. C247: the mask
    table 0x006CE268 reads 1, 2, 4, 8, …; entry 2 is 4. C282/R55: rows 44's two records (211 `duriel`, 708
    `uberduriel`) have `aip4` and `aip5` 0 (blank) in all three difficulties and `aip2` 33, `aip3` 50, both readers; with
    `D100()` uniform on 0..99 and `draw < aip`, Smite 33/100, Jab 67/200, A2 0, A1 67/200 in each of the six columns.
    C313: `CORNER` 0x006E337C = (−5, −5), (5, −5), (5, 5), (−5, 5) by both readers, used at 0x005E0659 and 0x005E0668
    (`AiHighPriest`). C52: row 15's alt is 0x005F1750 (kind 4); it gets its record by `AiCtlParamGet(14, 0)` and tests
    `[eax+0x18] = 1` (0x005F1757–0x005F1764).
  - *S1e remainders.* 288: `0x005F77C0` has one call, 0x005F7BDE in `AiMephisto` (row 50's think), no jump or dword. 356:
    0x005E26D0 is pushed at 0x005E2918 (`AiOverseer`) and 0x005EE906 in `AiNihlathak` 0x005EE5D0, row 128's think; States
    row 141 is `bloodlust`. 518: `AiLifePct` (`push ecx; call 0x00621F20; ret`) has 4 calls: rows 4 (0x005EFF8A), 8
    (0x005F07E9), 15 (0x005F1939) **and 122 `Imp` (0x005E31BB)**; `UnitLifePct` 38, among them row 11's.
  - *Two findings against the specs.* (1) M82, machinery T30a "no writer of a kind-14 record with a unit was found": row
    65's think builds a block with `+0x08` 14, `+0x0C` the unit's `[+0xC]` and `+0x10` 1 at `EBP−0x28` and passes it to
    `MonHelpBlock` (0x005F9C17–0x005F9C33), as ai/0005 § 2.18 already reads. (2) S1e row 518, catalogue line 4689 "rows 4, 8
    and 15 `AiLifePct`": row 122 is a fourth (0x005E31BB, also in the spec's own R122b). Both go to Phase 3 through the
    backlog entry of this batch.
  - *Observed, not settled in part 1.* MonStats `Skill8` is set on 333 `diabloclone`, 705 `uberdiablo` **and 709
    `uberbaal`** (Chilling Armor, row 145): catalogue R51a's "only on `diabloclone` and `uberdiablo`" holds for the records
    of Diablo's block (rows 51 and 147) only. Row C422 is part 2's.
- **Not covered by this run** (part 2): catalogue rows 171, 422, 431 and the S1e remainders 196 and 420; machinery 10, 15,
  19, 20, 40, 41, 42, 44, 45, 54, 88, 94; README 21, 23, 33, 38.

### Part 2 (2026-11-16, same branch)

S1f's catalogue rows 171, 422, 431 with the S1e remainders 196 and 420, and S1o's 16 other rows. Tool `tools/ai_s1fo.py`
(`842c1e79…`) with two new sections, `p2f` and `p2o`, on the same helpers plus `tools/light_radius_scan.py`'s getter list;
part 1's sections unchanged (their 91 lines of the new output equal `check-s1fo-p1.txt` but for the totals). Kept output
`workspace/logs/n66x/s1fo/check-s1fo-p2.txt` (`68d4c1ee…`, `python3 -I tools/ai_s1fo.py all`, 178 check lines, 87 of
them part 2's, `S1fo total bad=0`), `manifest-s1fo-p2.sha256` (`95c37bbc…`) passing from `workspace/logs/n66x/s1fo`;
development outputs and the exploration scripts in `dev2/` with `manifest-dev2.sha256` (passing from `dev2/`). About 5
minutes under a 4 GB scope; no game, no Ghidra.

- **Results (each `[C]` by the second tool, at the scope stated; run:2026-11-16-sweep2-s1f, `check-s1fo-p2.txt`):**
  - *Row 71's `v14`* (C171). The think 0x005FA710–0x005FAA8F stores `[esi+0x14]` **eleven** times by objdump and r2 (0,
    3, 0, 0, 4, 0, 5, 2, 3, 0, 2; the register zeros from `xor`, 0x005FA7DD's `ecx` from `xor ecx,ecx` at 0x005FA771 on
    both jumps to it), none 1; its other `+0x14` operands are the state read 0x005FA72E and `cmp [esi+0x14],0x1`
    (0x005FA8D7) after `AiUnitSearch`. `EDX` = `eax − 1` under `state = 2` (0x005FA767), `eax − 2` under `state = 3`
    (0x005FA803). The specs' "twelve" is a miscount (backlog item 4).
  - *The arrow kind* (C196). `RNG_RandLoHi` 16 calls, one in 0x005DC000–0x005FE000 (`AiTrapArrowKind` 0x005FB69D); that
    function's 2 calls are rows 78 and 79's thinks (0x005FB749, 0x005FB869); the image's six `[r+0x2d4]` operands
    (objdump, r2, raw disp32 alike) are in `MonRegionsBuild` and `AiTrapArrowKind`; the three writes are the −1 at
    0x00547AB4 and the guarded 0 or draw at 0x005FB682, 0x005FB6A2.
  - *The inline picks* (C420). Diablo's 0x005E8E16–0x005E8EA1 and Baal's three (0x005FC280, 0x005FC3C1, 0x005FC5B0 to
    their `ret`) have 0x005FC130's shape: one multiplier step, mask or `div`, sum ≤ 0 skipping the step with `edx` 0 from
    the summing loop's counter, a signed scan from a zero running sum (`ebx` zeroed at entry, epilogue pops only), 17 words
    and fallback 11 (Diablo), 16 and 1 (Baal).
  - *Diablo's tables* (C422). The three templates' constant stores at `EBP−0xA4` equal ai/0012 § 2.3's start words; w0,
    w11, w16 are stored only from the zero `ebx`, and no store, read-modify-write or indexed store touches them in the copy
    at `EBP−0x60`; the score test `jbe` 0x005E8D48; the difficulty word `EBP−0xBC` of `EBP−0xC8`. `Skill8`: records 333,
    705 and 709 (`uberbaal`, row 145).
  - *Baal's tables* (C431). The three start words equal ai/0012 § 2.8 (melee `EBP−0x40`, blocked `EBP−0x48`, ranged
    `EBP−0x54`); w0 only ever 0; the ranged w7 is stored 0 twice (0x005FC481, `P`'s 0x005FC5A4) and has no other write; the
    level compare `0x84` at 0x005FC74F.
  - *Target lists* (M10). `TargetListAddPlayer` 1 call (`SUnitCreate`), type 0, first free of slots 0–7, `Game+0x8C` ≤ 8;
    `TargetListAttach` 15 calls in 14 functions, `i < 8`, after the head; `TargetListAdd` 9 calls, lists 8 (`WandererSpawn`,
    `AiNpcBarb`, `AiWussie`) and 9 (six), at the head.
  - *The unit search* (M15). `g_AiSearchKinds`: 13 pairs, walkers 0,0,1,0,0,2,0,0,0,3,3,2,0; the dispatch 0x005DD0B7–
    0x005DD127; 29 calls, kind 1 ×19, 6 ×2, 2, 3, 5, 7, 8, 9, 11, 12 ×1 (three kind-1 pushes stand well before the call:
    0x005EE8F8, 0x005FA8C0, 0x005FAF20).
  - *Stat 89* (M19). The ten getters' 1 418 calls (the spec's "215 register-id calls" is 205 here, unreconciled): 1 213 with an immediate id by the objdump walker, 161 ids, none 89, and
    no 89 by r2's walker at the 11 calls where the two walkers differ; 7 `push 0x59` and 2 `mov r32,0x59`, none within ten
    instructions before a getter call; the five search functions call no getter.
  - *Others.* M20 13 calls in 10 AI functions, the mask byte 1 against Skills `+0x08`. M40 `MonAiPathOverride` 103 calls,
    EDX 0 ×55, 7 ×12, 1 ×6, 2 ×10, 13 ×7, 15 ×3, 5 ×1, nine registers resolved by their decoded sources; `AiPathOverrideSet`
    9 calls. M41 `PathPlan` 68 calls, the eight monster-mode and AI ones the claim's. M44 `AiCtlFollowSet` 4 calls and its
    pair. M45 the owner link `AiCtl+0x28/+0x2C/+0x30`, written by `MonSetOwner`, read by `MonsterOwner` and
    `MonGroupForEach` (then `+0x34`). M88 row 37's think and callees to depth 2 (19 functions, 1 447 instructions): no
    displacement 0x170–0x19F. R21 `UnitQueueEvent` 265 calls, kind 2 ×30; `UNIT_CancelEvents` 141, kind 2 ×66. R38
    Hireling's four classes all row 61; the 32 Skills `summon` classes' rows.
  - *A finding against the specs.* M54: `UModTeleportTry` draws `Range(100)` up to twice on the acting unit's seed (0x005B12DB
    `< 15`; 0x005B1355 `< 25` with life below 30) besides `SpawnPosPick` (0x005B1318); machinery § F gives none
    (backlog item 5).
- **Not settled** (reasons in the inventory rows): machinery 42 (`PathPlan`'s `0x40000` exit to `PathPlanStraight`
  0x006499B9 comes before the one `PathTargetNotTown` call, 0x00649AE5), 94; README 23, 33.

## run:2026-11-16-sweep2-s1m

Plan 0066 Phase 1, batch S1m (`lane/n66m1`, reverser-static). No game, no Ghidra: new checks over kept logs.

- **Question:** do the kept AI logs reproduce the 40 a-logs statements of batch S1m (monsters/ai/machinery and
  monsters/ai/README; rows as in [plan 0066's inventory](../../plans/0066-inventory/monsters-ai-machinery.md)): the AI
  helpers' arguments, results and seeds, `MonSetMode`'s command blocks and seeds, the plan types, the next-event frames,
  the next AID's control and head words?
- **Inputs:** the 38 logs of S1a (`logs.txt`: the 21 rev 4 case logs of run:2026-11-03-ai-3 and the 17 rev 6 launch logs of
  run:2026-11-04-ai-r5, hashed in `workspace/logs/ai/manifest-sweep2-s1a-inputs.sha256`); for the command-byte and pair
  checks also the 31 case logs of run:2026-11-03-ai (`first-run-logs.txt`, in `manifest-run-2026-11-03-ai.sha256`); the
  six gap walks of run:2026-11-04-h1's review (`workspace/logs/skills/review-p52d/gaps-*.txt`) with their logs; the image
  (`MonModeEveryFrame`'s table, `g_MonAiTable`, the state rows, each read by Python and r2 through `tools/ai_s1fo.py`) and
  the MonStats, MonStats2, MonAI, Skills and States tables (the plain `.txt` reader and the `.bin`).
- **Procedure** (from `workspace/logs/ai`, the repo's tools by absolute path; tool `tools/ai_s1m.py`, sha256
  `e7147b50…7456`):
  ```
  O=../n66m1/s1m
  { systemd-run --user --scope -p MemoryMax=4G python3 -I tools/ai_s1m.py logs --logs $O/logs.txt --first $O/first-run-logs.txt
    python3 -I tools/ai_s1m.py tables; python3 -I tools/ai_s1m.py gaps ../skills/review-p52d
    python3 -I tools/ai_s1m.py totals; } > $O/check-s1m.txt
  ```
  Output `workspace/logs/n66m1/s1m/check-s1m.txt` (`8de1e5b7…7fa8`, 74 check lines, `S1m total bad=0` in each section; its `totals` line is the inventory's after the move of machinery 110, the first run's copy with 623 and 23 is `dev/check-s1m-before-totals.txt`),
  `manifest-s1m.sha256` (passes from `workspace/logs/n66m1/s1m`, with the run's copy of the tool `ai_s1m.py.rev`);
  development passes in `dev/` (`manifest-dev.sha256`, passes from `dev/`). Conventions: a helper's words are `CONV`'s of
  `tools/ai_model_check.py` (ECX, EDX, then the stack); a draw is the stepped seed's low word mod 100.
- [C] (run:2026-11-04-ai-r5, run:2026-11-03-ai-3, `check-s1m.txt`, fn:sub_005DDF90_MonAiSetModeAtUnit@0x005DDF90,
  fn:sub_005DEAD0_MonAiUseSkill@0x005DEAD0, fn:sub_005DE000_MonAiUseSeqSkill@0x005DE000) **The commands.** Each
  `SetModeAtUnit` (999), `UseSkill` (295) and `UseSeqSkill` (61) call holds exactly one `MSM0`, whose block has the call's
  mode (14 for `UseSeqSkill`), the unit and the target or point; each `UseSkill` holds one `SST0` of the same skill and
  returns 1 when the mode started (283; 12 with no `MSM1` logged); `Unit+0xC4` bit 0x40 is set after it in modes 4, 5, 7, 8
  and 9 (151 of 151, 100 of them set by the call) and clear after it in mode 14 (144). `MonAiFindHostile`: 4 197 calls
  from think code, ECX the decision's game and EDX its own unit in all. `MonSetMode`'s return addresses: `MonAiMove`
  0x005DEBCC 5 482, `MonAiWanderNearUnit` 1 561, `SetModeAtUnit` 1 083, `UseSkill` 533, `MonAiMoveToUnitDist` 453,
  `MonAiMoveToPoint` 210, `MonAiWalkToPoint` 198, `MonAiWalkToPointCmd` 134, `UseSeqSkill` 61, `MonAiWalkToPointOrStop` 42,
  `MonAiWalkToUnitOrZero` 34, `MonAiIdle` 4, `MonAiWanderRingDirect` 4. No `MonAiSetMode` and no direct `MonAiMove`
  call is logged; the logger's `MSM0` `flag` is the stack's first word (the game), so `MonSetMode`'s flag is not logged.
- [C] (`check-s1m.txt`, fn:sub_005A7E60_MonCmdInit@0x005A7E60, fn:sub_005A6B10_MonModeEveryFrame@0x005A6B10,
  fn:sub_005A63F0_MonMovePlan@0x005A63F0) **The path byte.** `MonModeEveryFrame`'s table 0x006E23D0 (16 × 3 words, Python
  and r2 agree): modes 2, 13, 14, 15 always, 0, 1, 3, 6, 12 never, 4, 5, 7–11 by the class's MonStats2 bit at `+0x104`
  (`*mv`, .txt = .bin over 734 records). Over 19 431 `MSM0` in 69 logs, `+0x15` is 101 exactly where that says every-frame
  and 100 elsewhere, 0 other; modes 8 and 9 take both by class (475/283, 56/88). For commands of callers that set no
  override, with no override-setting or unlisted call earlier in the decision and under the logger's per-decision cap,
  100 plans nothing (805) and 101 plans type 13 first (2 214), 0 other.
- [C] (`check-s1m.txt`, fn:sub_005DE190_MonAiPathOverride@0x005DE190, fn:sub_005F5830_AiAndariel@0x005F5830)
  **The override.** `MonAiPathOverride(type)` and the first plan of the next command (whose `MSM1` is logged): type 1 → 7
  (39, two of them Andariel's at 0x005F59FF), 2 → 2 (205), 7 → 7 (1 646), 13 → 13 (456), 0 → the command's own (13 in 839,
  5 or 6 in 4); a non-zero byte is the path's `+0x90` in 127 of 127. Andariel's `UseSkill` after three draws on the
  unit's seed (2 decisions).
- [C] (`check-s1m.txt`, fn:sub_005DEB60_MonAiMove@0x005DEB60, fn:sub_005DEC80_MonAiWalkToUnit@0x005DEC80) **A refused
  `MonAiMove` under `Walk`.** Flags 7: 1 step, no further command, result 1 where the step's low word mod 100 is 70 or
  more (47; the next event 10 frames on in 28, 11 none, 8 later), 5 steps with the ring's command below 70 (96). Flags 0
  (44): 0 steps, no command, result 0.
- [C] (`check-s1m.txt`, fn:sub_005DE080_MonAiIdle@0x005DE080, fn:sub_005DE0F0_MonAiDelay@0x005DE0F0) **The next event.**
  A rev 6 decision whose last call is `Idle(n)` (2 573, n ≥ 1 in all, no `MSM0` inside): the unit's next AID or AIN at
  `fr + n` in 2 358; 111 none and 36 later (66 of them after the log's AIN cap, the rest outside the window or in a
  capped row); 68 earlier, each an AID in mode NU 1 to 7 frames early (another queue, not attributed). `Delay(n)` (318,
  no `MSM0` inside): at `fr + n` in 294, 5 earlier, 19 none or later.
- [C] (`check-s1m.txt`, fn:sub_005A7C20_MonSetMode@0x005A7C20, fn:SKILLS_SrvStart@0x0056F640) **`MonSetMode`'s seed.**
  Of 9 416 calls with an `MSM1`, 9 166 leave the unit seed unmoved (362 with a skill start inside) and 175 move it with
  one `SST0` inside, entered at `MSM0`'s seed and exiting at `MSM1`'s. [I] The other 75, A1 or A2 commands of
  `SetModeAtUnit` (1 or 2 steps; classes such as 311, 97, 136), move it with no skill start logged and no skill of that
  mode in the class's slots: the draw's source is not read here.
- [C] (`check-s1m.txt`, fn:sub_005EFCF0_AiSkeleton@0x005EFCF0, fn:sub_005F0A20_AiWraith@0x005F0A20, 0x005B186F) **Rows 2
  and 9 by their blocks.** Every decision (260 and 92) has the block's one call (callee, word and unit seed after the
  block's draws) and no other, and exits with that call's `AIR` seed. Row 2: out of melee range `Walk(t, 7)` 163 and
  `Idle(aip2)` 63 after one draw; in it A2 21 and A1 5 after two, `Idle` 8 after one. Row 9: `Toward(t, 12, 0)` 55,
  `Idle` 35, A1 2. Row 125: 38 decisions, one call each.
- [C] (`check-s1m.txt`, 0x005F283F, fn:sub_005F2540_AiScarab@0x005F2540) **Row 20's clear.** In the 85 decisions of step
  4's walk (`Ovr(2, 0, 4)`, `Walk(t, 7)`, `v14 ≠ 0`, not melee) the exit seed is one step after the walk's `AIR` in all;
  with a next AID logged (70), `AiCtl+0x14` is 0 there where that step's low word mod 100 is above 10 (59) and unchanged
  where not (11). So the site no call can see is told apart by the next decision's control word; with
  run:2026-11-04-ai-r5's census (`resume-run-…`: 205 decisions, 0 mismatches, 346 calls past the first; `flip-run-…`:
  9 of 10 two-way sites failing alone on its 60-decision sample), row 20 meets README H1's rule. No row-20 decision has a
  head record of another kind (7 kind 1, 183 none).
- [C] (`check-s1m.txt`, fn:sub_005F2850_AiMummy@0x005F2850, tbl:MonStats.txt:aip1) **Row 21.** At `dist = aip1` the
  in-range arm runs (15, the walk), at `aip1 + 1` the other (13); `aip3` is 100 in the 18 cells of the six Mummy records,
  and all 29 melee draws pass, so the failed-`aip3` path is reached only on edited data.
- [C] (`check-s1m.txt`, fn:sub_0058F730_MonHelpBlock@0x0058F730) **`MonHelpBlock`.** 146 calls (rows 13 126, 6 11, 20 2,
  65 7): rows 6, 13 and 20 pass kind 1 with four other non-zero words; 81 blocks reappear word for word, all five words, as
  a later AID head record of another unit. Row 30 has no decision with a head record in these logs.
- [C] (`check-s1m.txt`, fn:sub_005B1740_MonAiEvent@0x005B1740, fn:sub_005B1650_MonAiTargetByKind@0x005B1650) **The
  event.** 14 063 AID: ctx `+0x00` the AiCtl, `+0x1C` the MonStats record, `+0x04/+0x0C/+0x10` 0 in all; 18 076 AIN. Row
  kinds (table read twice): 0 26, 1 104, 2 16, 4 1, 5 1; the 8 496 decisions of kind-1 states all have a target; 56
  state-12 decisions (state row kind 0) of kind-1 classes have target, distance and melee 0. States: 0 13 241, 10 632,
  11 134, 12 56; state 2 in none.
- [C] (`check-s1m.txt`, run:2026-11-04-h1) **The 8 open H1 gaps:** first disagreement an `AD0` whose attacker is the gap's
  unit, 1 (5), 3 (2) or 4 (1) steps past the walking seed.
- [I] (`check-s1m.txt`) **Shown but not separating:** decision pairs of one unit with no AIN between keep the seed after S2,
  S3, S4 and NU commands (94, 46, 172, 5) and in 9 094 of 9 203 WL, 1 536 of 1 541 RN and 11 692 of 11 818 commandless
  ones; the moves are not attributed. Each unit's first logged decision shows the init words (−1, 1, −1, 1) in 1 076 of
  1 635 (the rest written before the log saw them). Curse states: `s-barb-howl` 12 (56) and 11 (20), `s-necro-curse` 11
  (78) and 10 (38), against `auratargetstate` Taunt 27, Howl and Terror 56, Dim Vision 23; states 10 (594) and 11 (36)
  also occur in the Countess launches with no curse cast.
- **Conclusion:** per inventory row in plan 0066's `monsters-ai-machinery.md` and `monsters-ai-README.md` (S1m notes):
  raised 10, raised in part 24, not raised 3 (README 7, 32, 36: the [I] bullet above), not settled 2, moved 1. No symbol raised (no logged return names a role).

## run:2026-11-16-sweep2-s1ne

- **Question:** (plan 0066 Phase 1, batch S1ne part 1) Do twelve monsters/ai machinery and README functions map their
  declared image to their return, the words they write, or the arguments of their one observed boundary call as the
  specs state them (at `b5999f5e`)? Ruling R2 applies: every callee runs whole, and the boundary ends the case.
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (unchanged), lane project copy
  `workspace/ghidra-n66ne` (`import-symbols` first), heap 3 GB, one headless run inside
  `systemd-run --user --scope -p MemoryMax=4G`. No wine, no slot. Models, case writer and checker are
  `tools/ai_s1ne_emu.py` (`48908a51…`). It imports `tools/ai_s1e_emu.py` unchanged (its `Mem`, `W`, `E` and callee
  models, and its memory spec without the guard lines) and draws every case from `random.Random("n66ne-<family>")`.
  12 families × 240 cases = 2 880. The declared image is S1e's plus a state-mask array at DataTables `+0x0D4`. The
  `ovr` cases with no MonsterData declare 0x00–0x3F as case memory (the stores through `ECX` 0). Image constants
  read unwritten: `g_BitMask32`, `g_UnitHashOffsets`, and the `UNIT_GetSizeX` jump table 0x0062057C. Guards: the fatal
  path (0x00408090, 0x00408A60, 0x00681E09) and the pool entries (0x0040B430, 0x0040B480, 0x0040B4B0). Observe:
  `UnitQueueEvent` 0x005417D0. The route listing is `tools/ai_s1ne_routes.py` (`30b33c81…`): the S7e walker plus
  room-walker marks and each root's call sites.
- **Procedure** (from the worktree root; `D=workspace/logs/n66ne/s1ne/run`):
  ```
  python3 -I tools/ai_s1ne_routes.py > workspace/logs/n66ne/s1ne/routes/routes.txt
  python3 -I tools/ai_s1ne_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66ne GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
    tools/ghidra.sh emuboundary $D/s1ne.cases $D/s1ne.mem > $D/s1ne.out
  python3 -I tools/ai_s1ne_emu.py check --dir $D > $D/check.txt
  python3 -I tools/ai_s1ne_emu.py manifest --dir $D --write
  ```
  The controls are S1e's: every named test is reversed alone, and every ordered compare has its strictness switched
  alone (`name~`). This run adds signedness controls (`pending>T unsigned`, `pending<T+n signed`, `dsq unsigned`) and
  `mask 0xC` in `gmummy`. The cases that end at the boundary are checked for the return address of the call site
  (0x005A7428 or 0x005A7482 for `neutral`, 0x005DE186 for `dearl`).
- **Outputs:** `$D/manifest.sha256` (`25f3755b…`, 12 lines: `check.txt` `a88ddd26…`, `s1ne.out` `34e0acc1…`,
  `s1ne.cases` `a6a1ae35…`, `s1ne.mem`, `tool.sha256`, the seven images). `sha256sum -c manifest.sha256` passes from
  `$D`. `tool.sha256` hashes the six tools and scripts and passes from the worktree root. `routes/manifest.sha256`
  (`routes.txt` `734b4230…`) passes from `workspace/logs/n66ne/s1ne/routes`. `cases` regenerates `s1ne.cases`
  byte for byte, and `check` reproduces `check.txt` byte for byte. Development runs: `workspace/logs/n66ne/s1ne/dev0`
  (the run before the `mask 0xC` control; its own manifest) and session scratch. Neither is cited.
- **Observed** (`check.txt`):
  ```
  S1NE <12 families> cases=240 match=240 bad=0 passed=0, every control separated     (each)
  obs: neutral 167, dearl 199; fatal: ovr 82 (guard 0x00408090)
  controls: adu 3, adps 3, dsq 0, ovr 8, ovs 5, neutral 7, dearl 5, entry 7, gate 3, deadmin 7, fallen 12, gmummy 19
  S1NE traced reads accounted: UNIT_GetSizeX jump table 720, g_BitMask32 1047, g_UnitHashOffsets 42
  S1NE traced unaccounted: 0
  S1NE total cases=2880 match=2880
  S1NE result=ok
  ```
- **Results** ([ai/0001 § 14](0001-machinery.md#14-plan-0066-batch-s1ne-part-1-twelve-maps-emulated-the-routes-read-2026-11-16-lanen66ne)
  holds the claims and counts; the inventory rows hold the raises):
  - `adu`, `adps`, `dsq`: the distance maps, with `UNIT_GetSizeX` for types 0, 1, 2, 4 and 5. `adps`'s `shr` of a
    negative size is a refinement. `dsq` has no named test: its map rests on the 240 matches, 84 of them with a sum past
    2³¹ − 1.
  - `ovr`, `ovs`: D2 as stated, plus the `ECX` 0 stores of a unit with no MonsterData.
  - `neutral`: C1 for a monster already in NU, up to the queue call. The exit with no MonStats record is new.
  - `dearl`: C4 with two corrections, `n = 0 → 1` (a negative `n` kept) and the unsigned compare.
  - `entry`, `gate`: D1 for states 10–12 through the gate and for 18 and past. D1b holds.
  - `deadmin`, `fallen`, `gmummy`: T13a and T22a, the callbacks' maps. In `gmummy`, `IsUndead` covers bits 3 or 4,
    and 2 champion corpses are taken with `uniquesToo` 0.
- **Not covered:** every path past `UnitQueueEvent`; `SUNIT_SetMode` with a mode change (the anim chain to `wsprintfA`);
  `UNIT_CancelEvents`' unlink path; `UNIT_GetSizeX` of an item; the think words that fill the callbacks' blocks.
