# Experiments — path/search

## run:2026-11-03-path-emu-1

- **Question:** (plan 0054 Phase 1, batch P1.1) Do `PathPlan`'s entry, its target refresh and object step, the town
  test, the free-target step and the player extension, `PathPointsOutsideRoom`, `PathPlanStraight` with
  `PathPlanToUnit`, `PathSetType`, the six path setters, `PathAimNextPoint` with `PathDirection` and `PathFaceDir`,
  `PathReplan` and `SUnitPathCreate` map their declared inputs to their return, or to the call, call site and arguments
  of their first observed boundary, with every byte of the path record they write, as
  [path/0001](0001-pathplan-register.md) §§ 1–9 read them?
- **Setup:** Ghidra p-code emulator via `re/ghidra_scripts/EmuBoundary.java` (`0c88b790…`, the `lane/r55e` revision
  that re-applies each per-case memory directive from a fresh copy; copied unchanged into this lane), lane project
  copy `workspace/ghidra-r54a` (symbols replayed from `re/symbols.csv`), heap 3 GB, under `systemd-run --user --scope
  -p MemoryMax=4G`. No wine, no slot. Models and case writer `tools/path_emu1.py` (`88d5f01c…`, copy
  `path_emu1.py.rev` in the run directory), every draw from `random.Random("r54a-<family>")`. The image: eight
  `DungeonRoom` records with near lists, DRLG rooms, levels and `CollMap`s, the cells predicted by
  `tools/collision.py`'s activation model from two kept run:2026-10-14-collision logs (`grids` command;
  `grids.json` `b836aba6…`: block T, levels 75 and 76, and block J, level 29; 362 and 44 model checks, 0 failures),
  each block once as predicted and once with seeded unit marks. Files in `workspace/logs/r54a/emu/`,
  `manifest.sha256` (`1585108e…`, 51 lines, `check.txt` `4f5353f5…`); `sha256sum -c manifest.sha256` from that
  directory passes. The development run (`dev-1/path_emu1.py.rev`, the revision before the `sign` control and the 60
  cases written for it; a probe of the import slot's value under `dev-1/probe/`, its own manifest) is under
  `emu/dev-1/`, its own manifest (51 lines).
- **Procedure:**
  ```
  D=workspace/logs/r54a/emu
  python3 -I tools/path_emu1.py grids --dir $D
  python3 -I tools/path_emu1.py cases --dir $D
  for f in plan plannoop free town outside settype setters aim replan create; do
    GHIDRA_PROJ_DIR=workspace/ghidra-r54a GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/path_emu1.py check --dir $D > $D/check.txt
  python3 -I tools/path_emu1.py manifest --dir $D --write
  ```
  The memory specs write the rooms once (`const`), observe each family's boundaries (the unit unmark 0x00649560 in
  `plan` only, the re-mark 0x00649400, the x87 offset 0x00679190, the random walk 0x0067A240, the spiral 0x0067A140,
  the `IsBadCodePtr` import at the IAT slot's emulator value 0x00303946; PathPlan 0x00649970 and 0x0064C040 for
  `replan`; 0x00649D00, 0x00640E90, 0x00620AE0, 0x00553060 for `create`; the assert entry 0x00408090 for `settype`
  and `setters`) and guard the allocator and fatal entries elsewhere.
- **Observed** (`check.txt`):
  ```
  PATH54 plan cases=600 match=600 bad=0 stopped=0 traced=0 ... cmp_separating=15 cmp_passed=0 force_separating=5 force_passed=0 npc_separating=17 npc_passed=0 boundary_cases=332 site_control_passed=0 boundaries=5
  PATH54 plannoop cases=600 match=600 bad=0 stopped=0 traced=0 ... cmp_separating=21 cmp_passed=0 force_separating=8 force_passed=0 npc_separating=26 npc_passed=0 boundary_cases=318 site_control_passed=0 boundaries=6
  PATH54 free cases=560 match=560 bad=0 stopped=0 traced=0 ... noalt_separating=97 noalt_passed=0 ext4_separating=33 ext4_passed=0 sign_separating=60 sign_passed=0
  PATH54 town cases=400 match=400 bad=0 stopped=0 traced=0 ... floor_separating=56 floor_passed=0 npc_separating=5 npc_passed=0
  PATH54 outside cases=300 match=300 bad=0 stopped=0 traced=0 ... le_separating=25 le_passed=0
  PATH54 settype cases=400 match=400 bad=0 stopped=0 traced=0 ... mask_separating=101 mask_passed=0 boundary_cases=132 site_control_passed=0
  PATH54 setters cases=360 match=360 bad=0 stopped=0 traced=0 ... cap_separating=20 cap_passed=0 boundary_cases=49 site_control_passed=0
  PATH54 aim cases=500 match=500 bad=0 stopped=0 traced=0 ... face0_separating=308 face0_passed=0 sar7_separating=417 sar7_passed=0
  PATH54 replan cases=300 match=300 bad=0 stopped=0 traced=0 ... swap_separating=63 swap_passed=0 boundary_cases=251 site_control_passed=0
  PATH54 create cases=300 match=300 bad=0 stopped=0 traced=0 ... act_separating=72 act_passed=0 boundary_cases=300 site_control_passed=0
  PATH54 total cases=4320 match=4320
  PATH54 result=ok
  ```
  (`...` the `accounted=` image-table read counts, listed in full in `check.txt`.)
- **Conclusion:** the maps of path/0001 §§ 1, 3–5, 6 (the slot argument), 7–9 are `[C]` up to each family's boundary,
  over the declared domain (collision test points one subtile inside a room for the plus and 3 × 3 patterns); not
  `PathPlan`'s tail after the import, not `PATH_DynamicCreate`, not the planners, not what the game stores at the
  declared offsets. No symbol raise (ADR-0015 scope, review-fixes rule 14). (run:2026-11-03-path-emu-1)
