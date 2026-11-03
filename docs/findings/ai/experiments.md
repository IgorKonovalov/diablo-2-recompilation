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
  `tools/ai_cat_emu11.py` (`d5ece728…`), every draw from `random.Random("r52k-<family>")`. Files in
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
