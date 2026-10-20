# Skills experiments

Runtime records for [skills/0001](0001-dispatch.md) and the later skills findings (plan 0045 Phase 2). Harness and
evidence rules: ADR-0003, ADR-0004, ADR-0011, ADR-0013, ADR-0014;
[tooling](../../../.claude/skills/reverser/references/tooling.md),
[harness-play](../../../.claude/skills/reverser/references/harness-play.md).

Plan 0045 Phase 2's harness runs: none yet. Plan 0046's emulated runs (ADR-0015) follow.

## run:2026-10-20-cat-emu-9a

- **Question:** (plan 0046 Phase 1, batch 9a) Do the missile server do functions 2, 6–12 and 14–18 map their inputs
  (the missile's record, `MissileData` words, owner, path and seed) to the arguments of the calls they end in, and to
  the bytes and seed they write before them, exactly as [skills/0004](0004-missile-do-1-18.md) §§ 3–11 say?
- **Setup:** Ghidra 12.1.2 p-code emulator (`EmulatorHelper`) on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m1`, symbols replayed from `re/symbols.csv`, heap 3 GB, under
  `systemd-run --user --scope -p MemoryMax=4G`). No wine, nothing runs natively, no slot. New script
  `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, `tools/ghidra.sh emuboundary`): `EmuTrace.java` plus `observe
  <addr>` lines in the memory spec; a case that reaches one ends there and prints its registers and the 64 bytes at
  ESP (skills/0004 § 2). Models, case writers and checks: `tools/skills_catalogue_emu.py` (`b2a6afd8…`, which uses
  `tools/rng.py` and `tools/sweep_s4b.py`'s image reader). All inputs synthetic (stock parameter values among them);
  every case-writer draw from `random.Random("cat9a-<family>")`. Files in `workspace/logs/skills-cat-9a/`,
  `manifest.sha256` `58e190a9…` (48 files: cases, memory specs, expected inputs, outputs, the empty `.err` logs,
  `check.txt` `3e1f2587…`, `static.txt` `e2b2f9a1…`, `rows.txt` `6cfad638…`); `sha256sum -c manifest.sha256` from that
  directory passes.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-9a
  python3 -I tools/skills_catalogue_emu.py cases
  for f in cellsub orb spiral scatter chest homing periodic sublob guided; do
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m1 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read, names the nine
  boundaries (`observe`) and guards the allocator and fatal-path entries; each case writes only the fields its
  function reads, so any other read is traced.
- **Observed** (`check.txt`):
  ```
  CAT9A cellsub  cases=1800 match=1800 bad=0 neg=173 traced=2   undeclared=0 stopped=0
  CAT9A orb      cases=1500 match=1500 bad=0 neg=266 traced=130 undeclared=0 stopped=0
  CAT9A spiral   cases=1500 match=1500 bad=0 neg=223 traced=0   undeclared=0 stopped=0
  CAT9A scatter  cases=2400 match=2400 bad=0 neg=394 traced=4   undeclared=0 stopped=0
  CAT9A chest    cases=1500 match=1500 bad=0 neg=247 traced=1   undeclared=0 stopped=0
  CAT9A homing   cases=1500 match=1500 bad=0 neg=22  traced=3   undeclared=0 stopped=0
  CAT9A periodic cases=1200 match=1200 bad=0 neg=149 traced=0   undeclared=0 stopped=0
  CAT9A sublob   cases=1200 match=1200 bad=0 neg=187 traced=4   undeclared=0 stopped=0
  CAT9A guided   cases=1200 match=1200 bad=0 neg=128 traced=79  undeclared=0 stopped=0
  CAT9A static   data_stores=0 pins=18 pins_ok=18 ro_reads=3
  ```
  (`traced` counts aggregated rows of declared image reads; the branches reached are on each family's `outcomes`
  line.) Development runs before the final declared sets: the first `check` listed three undeclared image reads (the
  `CALC_Eval` jump table, `UNIT_GetSizeX`'s jump table, a target's `+0xC6`), each then declared or written by the case
  writer; the outputs above are from the final case files.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015, ADR-0021) of the 13 functions' maps up to their boundary
  calls, 13 800 cases, 0 mismatches; raises skills/0004 §§ 3–11's `[C]` statements up to their boundaries (do 7's re-plan and do 13 not covered).
  *Architect ruling (`lane/p46m1` review, 2026-10-20):* the `observe` boundary does not meet ADR-0015 (1) and (3) as
  written; the proposed [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md) admits it. Until the owner
  accepts it, the statements that rest on cases ending at a boundary are `[I]`; the refusal paths that return are `[C]`
  (skills/0004 § 2). *ADR-0021 accepted by the owner (2026-10-20):* those statements are `[C]` without a re-run, each
  up to its boundary, covering nothing after it (skills/0004 § 2). The review checked the call site of every observed boundary from the kept outputs
  (`workspace/logs/skills-cat-9a-review/callsites.txt` `8ea8058b…`: one site per function and boundary). Not covered: what any
  boundary callee does; faults (§ 1); when the game runs these functions or with which seed.
  (fn:sub_005A9820_MissSubNearReseed@0x005A9820, fn:sub_005AF030_MissDo15OrbBolts@0x005AF030)

## run:2026-10-20-cat-emu-9b

- **Question:** (plan 0046 Phase 1, batch 9b) Do the missile server do functions 19–23 and 25–36 and the damage
  functions 1–5 and 7–14 map their inputs (the missile's record, `MissileData` words, owner, target, path, stat lists,
  Skills, MonStats and MonStats2 records, the packet and the seeds) to the arguments of the calls they end in, the bytes
  and seeds they write, and (damage functions) the packet they return, exactly as
  [skills/0005](0005-missile-do-19-36-damage.md) §§ 3–18 say?
- **Setup:** as run:2026-10-20-cat-emu-9a: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m2`, symbols replayed from `re/symbols.csv`, heap 3 GB, under
  `systemd-run --user --scope -p MemoryMax=4G`), `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine,
  nothing runs natively, no slot. Models, case writers and checks: the 9b families of `tools/skills_catalogue_emu.py`
  (`540cf98e…`; `tools/rng.py`, `tools/sweep_s4b.py`), which now assert the **return address** of every observed
  boundary (ADR-0021 (b)) and run a site control and two negative controls per family. All inputs synthetic (stock
  parameter values among them); every case-writer draw from `random.Random("cat9b-<family>")`. Files in
  `workspace/logs/skills-cat-9b/`, `manifest.sha256` `cda8abef…` (68 files: cases, memory specs, expected inputs,
  outputs, the empty `.err` logs, `check.txt` `7b5c1f6f…`, `static.txt` `16672f27…`, `rows.txt` `9152e7da…`);
  `sha256sum -c manifest.sha256` from that directory passes. The same tool revision reproduces 9a's `check.txt` and
  `static.txt` byte for byte from 9a's kept outputs, and its 9a `cases` regenerate 9a's case files byte for byte.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-9b
  python3 -I tools/skills_catalogue_emu.py cases --batch 9b
  for f in create9b vines rabies reseed9b scatter25 wake regen tornado fx dmgconv dmgelem dmgpkt knock; do
    systemd-run --user --scope -q -p MemoryMax=4G env GHIDRA_PROJ_DIR=workspace/ghidra-p46m2 GHIDRA_HEADLESS_MAXMEM=3G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch 9b > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 9b > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 9b --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read, names the
  boundaries (`observe`: 9a's nine and twelve more, plus do 20's entry in `create9b` only) and guards the allocator and
  fatal-path entries; the damage cases pass `(unit, packet)` on the stack and dump the packet.
- **Observed** (`check.txt`):
  ```
  CAT9B create9b  cases=1500 match=1500 bad=0 neg=299 traced=2  undeclared=0 stopped=0
  CAT9B vines     cases=1200 match=1200 bad=0 neg=497 traced=3  undeclared=0 stopped=0
  CAT9B rabies    cases=1200 match=1200 bad=0 neg=242 traced=5  undeclared=0 stopped=0
  CAT9B reseed9b  cases=1500 match=1500 bad=0 neg=347 traced=4  undeclared=0 stopped=0
  CAT9B scatter25 cases=900  match=900  bad=0 neg=297 traced=4  undeclared=0 stopped=0
  CAT9B wake      cases=1200 match=1200 bad=0 neg=503 traced=4  undeclared=0 stopped=0
  CAT9B regen     cases=1200 match=1200 bad=0 neg=184 traced=5  undeclared=0 stopped=0
  CAT9B tornado   cases=900  match=900  bad=0 neg=365 traced=4  undeclared=0 stopped=0
  CAT9B fx        cases=1200 match=1200 bad=0 neg=180 traced=0  undeclared=0 stopped=0
  CAT9B dmgconv   cases=1500 match=1500 bad=0 neg=421 traced=43 undeclared=0 stopped=0
  CAT9B dmgelem   cases=1200 match=1200 bad=0 neg=137 traced=32 undeclared=0 stopped=0
  CAT9B dmgpkt    cases=2400 match=2400 bad=0 neg=70  traced=5  undeclared=0 stopped=0
  CAT9B knock     cases=1200 match=1200 bad=0 neg=62  traced=2  undeclared=0 stopped=0
  CAT9B static data_stores=0 pins=26 pins_ok=26 ro_reads=4 table_entries=30
  ```
  17 100 cases. Every family's two negative controls fail (counts per control on its `negative control` lines); the
  site control fails on all 8 762 matched boundary cases (40 `site` lines: function, boundary, return address).
  Development runs before these files: the first check found do 28's point in the block's target words (the model
  had the start words; corrected), two controls that could not fail (do 31's `Explosion`, damage 3's `≤`; replaced),
  and undeclared reads of the three `EType` jump tables and of `MissileData+0x0C` by `MISS_EvalCalc` (declared, and
  written by the case writer); the outputs above are from the final case files.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the damage functions' maps on returning
  cases (`[C]`), of the do functions' refusal paths that return (`[C]`), and of the do functions' maps up to their
  boundary calls with the call site asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md), accepted by the owner 2026-10-20 and applied at the
  `lane/p46m2` review; skills/0005 names each claim's boundary). Not covered:
  what any boundary callee does and everything after it; the `fMin` floor of `StatListGetValue`; faults
  (`GameFindUnit` with a type above 5); when the game runs these functions or with which seed.
  (fn:sub_005AD050_MissDmg01ConvertPct@0x005AD050, fn:sub_005B0010_MissDo30Contagion@0x005B0010)
- **Review checks** (`lane/p46m2` review, 2026-10-20; `workspace/logs/skills-cat-9b-review/`, `manifest.sha256`
  `02466fbf…`, 9 files): `sha256sum -c` of the run's manifest passes (68 files); `check rabies reseed9b` from the kept
  outputs gives `check.txt`'s lines; `cases --batch 9a` and `cases --batch 9b` regenerate every kept case, memory and
  expectation file byte for byte (27 and 39); `check --batch 9a` and `static --batch 9a` reproduce 9a's kept files byte
  for byte (tool `540cf98e…`; `EmuBoundary.java` `286393aa…`); do 30's 90 creation cases leave the missile's, the
  owner's and the decoy's seeds unchanged (270 of 270, `seeds-do30.txt`, from the kept `rabies.out`); objdump of do 28
  (0x005AFCAA–0x005AFD50), do 30 (0x005B0140–0x005B0187), damage 14 (0x005AD67C–0x005AD69E) and do 31's end code
  (0x005B0289–0x005B0336) in `objdump-spot.txt`. (fn:sub_005B0010_MissDo30Contagion@0x005B0010)
