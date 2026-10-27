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
