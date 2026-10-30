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
