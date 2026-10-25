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

## run:2026-10-20-cat-emu-9c

- **Question:** (plan 0046 Phase 1, batch 9c) Do the missile server hit functions 1, 3 (and 44), 4, 7–10, 12–22 and
  24–29 map their inputs (the missile's record, `MissileData` words, owner, hit unit, path, stat lists, state lists,
  Skills and MonStats records and the seeds) to the result they return, or to the arguments, pointed-to bytes and
  seed states at the call they end in, exactly as [skills/0006](0006-missile-hit-1-29.md) §§ 3–16 say, and do they
  leave the owner's and the target's seeds as they were?
- **Setup:** as run:2026-10-20-cat-emu-9b: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m3`, symbols replayed from `re/symbols.csv`, heap 3 GB, under
  `systemd-run --user --scope -p MemoryMax=4G`), `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`;
  `EmuTrace.java` `3255db0c…`). No wine, nothing runs natively, no slot. Models, case writers and checks: the 9c
  families of `tools/skills_catalogue_emu.py` (`412e3e5c…`; `tools/rng.py`, `tools/sweep_s4b.py`), which keep 9b's
  call-site assertion and site control, run two to six negative controls per family, compare the missile's, the
  owner's and the target's seeds in every case (written and dumped by every case; a control moves the missile's draws
  to the owner's seed), and compare the bytes behind a boundary argument that points into the caller's frame (the
  packet of `AreaHitAt` and `MISSILE_BuildDamage`, hit 20's context block). All inputs synthetic (stock parameter
  values among them); every case-writer draw from `random.Random("cat9c-<family>")`. Files in
  `workspace/logs/skills-cat-9c/`, `manifest.sha256` `343ef0d7…` (28 files: cases, memory specs, expected inputs,
  outputs, the empty `.err` logs, `check.txt` `733ad44a…`, `static.txt` `1644c5cb…`, `rows.txt` `eaec0e1a…`);
  `sha256sum -c manifest.sha256` from that directory passes. The same tool revision reproduces 9a's and 9b's
  `check.txt` and `static.txt` byte for byte from their kept outputs, and its `cases --batch 9a` / `--batch 9b`
  regenerate their 27 and 39 case, memory and expectation files byte for byte.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-9c
  python3 -I tools/skills_catalogue_emu.py cases --batch 9c
  for f in area9c holy9c create9c state9c range9c; do
    systemd-run --user --scope -q -p MemoryMax=4G env GHIDRA_PROJ_DIR=workspace/ghidra-p46m3 GHIDRA_HEADLESS_MAXMEM=3G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch 9c > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 9c > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 9c --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, States
  count 190, ItemStatCost, MonStats as each family needs), names the boundaries (`observe`: 9b's and eleven more,
  skills/0006 § 2) and guards the allocator and fatal-path entries; each case passes the hit unit on the stack and
  dumps the three seeds.
- **Observed** (`check.txt`):
  ```
  CAT9C area9c   cases=1800 match=1800 bad=0 neg=829 traced=30 undeclared=0 stopped=0
  CAT9C holy9c   cases=1500 match=1500 bad=0 neg=218 traced=10 undeclared=0 stopped=0
  CAT9C create9c cases=1800 match=1800 bad=0 neg=284 traced=8  undeclared=0 stopped=0
  CAT9C state9c  cases=1800 match=1800 bad=0 neg=153 traced=30 undeclared=0 stopped=0
  CAT9C range9c  cases=1500 match=1500 bad=0 neg=182 traced=74 undeclared=0 stopped=0
  CAT9C static pins=26 pins_ok=26 ro_reads=6 table_entries=25
  ```
  8 400 cases. Every negative control fails (counts per control on its `negative control` lines, the weakest hit
  29's `left > 0` with 4 and hit 7's undead mask with 8, each beside a stronger control on another claim); the site
  control fails on all 3 941 matched boundary cases (27 `site` lines: function, boundary, return address); the
  seed control fails on the 155 and 39 cases whose missile drew. Development runs before these files (outputs in the
  session scratch, not cited): the first check found hit 44's EBX holding the y position (the model had the owner;
  corrected), `0x005A8F20`'s jump table undeclared (declared), the States count missing from `holy9c`'s spec (hit 8's
  `UNIT_HasState` read it; added), keys of JSON-loaded dicts read as integers in two models, and a decoy shared by
  the owner's hash chain and hit 22's stored unit (the writer now keeps them apart); the outputs above are from the
  final case files.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the hit functions' maps on returning cases
  (`[C]`: hit 3 with a unit, 7's type tests, 8, 10, 27 and every refusal path), and of their maps up to their boundary
  calls with the call site, the arguments, the pointed-to packet or context and all three seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0006 names each claim's boundary). The only
  seed any case steps before a boundary is the missile's (hits 1, 9, 13 through the `EType` roll; hit 7's heal); no
  case steps the owner's or the target's. A caller register that is not a boundary argument (the radius of hits 24,
  44 and 14 in EBX, EDI and ESI at `BuildDamage`) is compared but stays `[I]` (`lane/p46m3` review, ruling 1). Not
  covered: what any boundary callee does and everything after it; hit 2 (carried to batch 9d);
  faults (`MonsterOwnerRef` without MonsterData, `GameFindUnit` with a type above 5); when the game runs these
  functions or with which seed. (fn:sub_005A9FB0_MissHit07HolyBolt@0x005A9FB0, fn:sub_005AA650_MissHit10Guided@0x005AA650)

## run:2026-10-20-cat-emu-9d

- **Question:** (plan 0046 Phase 1, batch 9d) Do the missile server hit functions 31–33, 35–40, 43, 45, 47, 48,
  50–59 and the tier-A hit 2 map their inputs (the missile's record, `MissileData` words, owner, hit unit, path, room,
  object, stat lists, the owner's skill list, Skills and MonStats records, the game frame and the seeds) to the result
  they return, or to the arguments, pointed-to bytes and seed states at the call they end in, exactly as
  [skills/0007](0007-missile-hit-31-59.md) §§ 3–10 say, and do they leave the seeds the model leaves alone as they were?
- **Setup:** as run:2026-10-20-cat-emu-9c: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m4`, symbols replayed from `re/symbols.csv`, heap 3 GB),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the 9d families of `tools/skills_catalogue_emu.py` (`da004a4b…`; `tools/rng.py`,
  `tools/sweep_s4b.py`), with 9c's conventions: the call site of every boundary asserted with a site control, the
  missile's, the owner's and the target's seeds written and compared in every case (a control moves the missile's
  draws to the owner's seed in the two families that draw), a boundary's pointer argument into the caller's frame
  compared by content (the `MissileCreate` block, 0x5C bytes; the packet of `MISSILE_BuildDamage`, 0x70 bytes), and
  no model compares a callee-saved register that is not a boundary argument (`lane/p46m3` review, ruling 1). All
  inputs synthetic (stock parameter values among them); every case-writer draw from `random.Random("cat9d-<family>")`.
  Files in `workspace/logs/skills-cat-9d/`, `manifest.sha256` `6fa68cd0…` (29 files: cases, memory specs, expected
  inputs, outputs, the empty `.err` logs, `check.txt` `9ec69cf5…`, `static.txt` `d909b72d…`, `rows.txt`
  `9678d001…`, `repro.txt`); `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the
  same tool revision regenerates every case, memory and expectation file of 9a, 9b and 9c byte for byte and
  reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-9d
  python3 -I tools/skills_catalogue_emu.py cases --batch 9d
  for f in heal9d create9d nova9d area9d event9d; do
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m4 GHIDRA_HEADLESS_MAXMEM=3G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch 9d > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 9d > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 9d --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills,
  ItemStatCost, MonStats, MonStats2), names the boundaries (`observe`: 9c's and nine more, skills/0007 § 2) and
  guards the allocator; each case passes the hit unit on the stack and dumps the three seeds.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CAT9D heal9d   cases=1500 match=1500 bad=0 neg=246 traced=22 undeclared=0 stopped=0
  CAT9D create9d cases=2100 match=2100 bad=0 neg=617 traced=6  undeclared=0 stopped=0
  CAT9D nova9d   cases=1500 match=1500 bad=0 neg=462 traced=4  undeclared=0 stopped=0
  CAT9D area9d   cases=1500 match=1500 bad=0 neg=473 traced=5  undeclared=0 stopped=0
  CAT9D event9d  cases=1800 match=1800 bad=0 neg=211 traced=3  undeclared=0 stopped=0
  CAT9D static pins=50 pins_ok=50 ro_reads=5 table_entries=25 tabreads=4 tabreads_signed=4
  ```
  8 400 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 53 or more cases: `nocap43` 73, `ownseed` 140 and 181, `hp_swap` 344, `unit56` 378, `mode1` 106); the site
  control fails on all 3 796 matched boundary cases (28 `site` lines: function, boundary, return address). Development
  runs before these files (outputs overwritten, not cited): the first check found `event9d`'s object written without
  its type word, so `UnitGetRoom` (`0x00620BB0`) took the path branch for hit 35's object (58 cases observed
  `SetMode` or returned 1 where the model had the room pin; the writer now sets type 2), `area9d`'s `lenlt` control
  failing no case (no case had the rabies end frame at the length; the writer now puts 30 % of the hit-53 cases at
  the length, one under or one over) and no `area9d` control reaching 50 (`unit56` added), and one static pin one
  instruction off (hit 50's `jge` is at 0x005AC856). The outputs above are from the final case files.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the hit functions' maps on returning cases
  (`[C]`: hit 37, hit 50, hit 55's refusals, every refusal path) and of their maps up to their boundary calls with the
  call site, the arguments, the pointed-to block or packet and all three seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0007 names each claim's boundary). The seeds
  any case steps before a boundary are the missile's only: hit 31 (the `EType` roll), hit 43 (one `RNG_RangeB`), hit
  58 (re-seeded from its x, two `RNG_Range`). Row 568's `pSrvHitFunc` 64 948 is a static claim: all four reads of
  the hit table sit behind a signed `test ax, ax; jle`. Not covered: what any boundary callee does and everything
  after it; the fatal path after its first call (`0x00408090`); when the game runs these functions or with which seed.
  (fn:sub_005AC350_MissHit43HealVortex@0x005AC350, fn:sub_005ACDF0_MissHit58Reseed@0x005ACDF0)

## run:2026-10-20-cat-emu-sor

- **Question:** (plan 0046 Phase 1, batch `sor`) Do the sorceress start functions 11–14 and do functions 17–26, 28,
  29 and 144 (with the Inferno helpers `0x005C8CA0` and `0x005C8E30`) map their inputs (the Skills and Missiles
  records, the caster, its path, target link, rooms, stat and state lists, skill list and used skill, the target
  unit and its owner and alignment, the game frame, difficulty and expansion words, and the seeds) to the result they
  return, or to the arguments, pointed-to bytes, written words and seed states at the call they end in, exactly as
  [skills/0008](0008-sorceress.md) §§ 3–8 say, and do they leave the target's seed alone?
- **Setup:** as run:2026-10-20-cat-emu-9d: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m5`, symbols replayed from `re/symbols.csv`, heap 3 GB),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `sor` families of `tools/skills_catalogue_emu.py` (`7525830c…`; `tools/rng.py`,
  `tools/sweep_s4b.py`), with 9d's conventions: the call site of every boundary asserted with a site control, the
  caster's and the target's seeds written and compared in every case (a control moves do 21's draw to the target's
  seed), a boundary's pointer argument into the caller's frame compared by content (the `MissileCreate` blocks, the
  `STATE_ApplyTimed` block at ECX, the `SpawnOwnedMonster` block, do 20's 20-byte block, do 21's zeroed packet), and
  no model compares a callee-saved register that is not a boundary argument. Each case calls the function with
  `ECX` = the game, `EDX` = the caster and `(id, lvl)` on the stack (`(id, lvl, cls)` for the helpers). All inputs
  synthetic (stock parameter values among them); every case-writer draw from `random.Random("catsor-<family>")`.
  Files in `workspace/logs/skills-cat-sor/`, `manifest.sha256` `83d7c0f9…` (35 files: cases, memory specs, expected
  inputs, outputs, the `.err` logs (the scope line only), `cases.txt`, `check.txt` `961ccef7…`, `static.txt`
  `91a6de74…`, `rows.txt` `148cf553…`, `repro.txt` `9a74392b…`); `sha256sum -c manifest.sha256` from that directory
  passes. `repro.txt` records that the same tool revision regenerates every case, memory and expectation file of 9a,
  9b, 9c and 9d byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept
  outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-sor
  python3 -I tools/skills_catalogue_emu.py cases --batch sor > $D/cases.txt
  for f in start_sor inferno_sor create_sor state_sor tk_sor hydra_sor; do
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m5 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch sor > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch sor > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch sor --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills,
  Missiles, ItemStatCost, MonStats, MonStats2, the States and PetType counts), the missile table `0x0096C794` and
  the difficulty table `0x0096C8AC` at scratch tables (inputs of the claims; skills/0008 § 2), names the boundaries
  (`observe`: 9d's less `UnitsSameParty`, and fifteen more, skills/0008 § 2) and guards the allocator.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATSOR start_sor   cases=1500 match=1500 bad=0 neg=220 traced=51 undeclared=0 stopped=0
  CATSOR inferno_sor cases=1200 match=1200 bad=0 neg=246 traced=8  undeclared=0 stopped=0
  CATSOR create_sor  cases=1800 match=1800 bad=0 neg=330 traced=12 undeclared=0 stopped=0
  CATSOR state_sor   cases=1600 match=1600 bad=0 neg=153 traced=32 undeclared=0 stopped=0
  CATSOR tk_sor      cases=1200 match=1200 bad=0 neg=116 traced=65 undeclared=0 stopped=0
  CATSOR hydra_sor   cases=1200 match=1200 bad=0 neg=228 traced=80 undeclared=0 stopped=0
  CATSOR static data_stores=1 pins=35 pins_ok=35 ro_reads=7 table_entries=17
  ```
  8 500 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 60 or more cases: `inv14` 138, `inv18` 141, `c1lvl` 170, `a1_ge0` 79, `tseed` 93, `lvl_p2` 195); the site
  control fails on all 2 977 matched boundary cases (27 `site` lines: function, boundary, return address).
  Development runs before these files (outputs overwritten, not cited): two model slips (the `PlayerPairFlags`
  registers read from the wrong tuple slot; `PartyIdOfUnit`'s likewise), `UnitsSameParty` observed through 9c's
  boundary list (the batch now runs it emulated), do 26's second-argument slot outside the stack dump (now dumped at
  `0x7FF00008`), and three controls failing no case (`dist_ge`, `stun_le`, `charge_a`; the writer now places targets
  at `r`, the draw at `Param2` and charged lists on purpose). The outputs above are from the final case files.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  start 12, 13, 14, do 21's returns, every refusal path) and of their maps up to their boundary calls with the call
  site, the arguments, the pointed-to blocks, the written words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0008 names each claim's boundary). The only
  draw before a boundary is do 21's `RNG_Range(caster seed, 100)`; no case steps the target's seed. Not covered: what
  any boundary callee does and everything after it; do 27; when the game runs these functions or with which seed.
  (fn:sub_005C98F0_SkillDo21Telekinesis@0x005C98F0, fn:sub_00554200_UnitsHostile@0x00554200)

## run:2026-10-20-cat-emu-ama

- **Question:** (plan 0046 Phase 1, batch `ama`) Do the amazon start functions 4–10 and do functions 6, 7, 8 and
  10–16 map their inputs (the Skills, Missiles, MonStats and MonStats2 records, the caster, its path, target link,
  inventory word, skill list and used skill's node, the target unit and its owner and alignment, the units the node
  names, and the seeds) to the result they return, or to the arguments, pointed-to bytes, frame words, written words
  and seed states at the call they end in, exactly as [skills/0009](0009-amazon.md) §§ 3–8 say, and do they leave
  both seeds alone?
- **Setup:** as run:2026-10-20-cat-emu-sor: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m6`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `ama` families of `tools/skills_catalogue_emu.py` (`69c01d13…`), with `sor`'s conventions
  (the call site of every boundary asserted with a site control, the caster's and the target's seeds written and
  compared in every case, a boundary's pointer argument compared by content: the `MissileCreate` blocks, do 6's
  24-byte block, the `SpawnOwnedMonster` blocks, the zeroed hit packets, the counter `n`; no model compares a
  callee-saved register that is not a boundary argument). New: a boundary inside a helper (`0x00623990`,
  `0x00622870`, `0x0056BC80`, `UnitGetWeapon`) also compares the batch function's frame words written before it at
  their absolute stack address (`compare`'s ninth expectation field; every function's `EBP` is `0x7FEFFFFC`). All
  inputs synthetic (stock parameter values among them); every case-writer draw from
  `random.Random("catama-<family>")`. Files in `workspace/logs/skills-cat-ama/`, `manifest.sha256` `6a3181d8…` (37
  files: cases, memory specs, expected inputs, outputs, the `.err` logs (the scope line only), `cases.txt`,
  `check.txt` `03a40fde…`, `static.txt` `b1b51e31…`, `rows.txt` `d441af4c…` with its `rows.sh`, `repro.txt`
  `9b03d065…` with its `repro.sh`, the run script `run_ama.sh`); `sha256sum -c manifest.sha256` from that directory
  passes. `repro.txt` records that the same tool revision regenerates every case, memory and expectation file of 9a,
  9b, 9c, 9d and `sor` byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their
  kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-ama
  python3 -I tools/skills_catalogue_emu.py cases --batch ama > $D/cases.txt
  for f in start_ama hit_ama aura_ama create_ama node_ama summon_ama; do      # one at a time ($D/run_ama.sh)
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m6 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch ama > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch ama > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch ama --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills,
  Missiles, ItemStatCost, MonStats, MonStats2, the calc pool, the States and PetType counts), names the boundaries
  (`observe`: `sor`'s less `0x00623990`, plus `0x0063C9B0`, `0x00580310`, `0x0064F380`, `COMBAT_MeleeHitTest`,
  `MonAttackStats`, `COMBAT_DeliverQueued`, `UnitSetPathTargetUnit`, `InMeleeRange`) and guards the allocator and the
  fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATAMA start_ama  cases=1600 match=1600 bad=0 neg=1030 traced=7 undeclared=0 stopped=0
  CATAMA hit_ama    cases=1600 match=1600 bad=0 neg=385  traced=8 undeclared=0 stopped=0
  CATAMA aura_ama   cases=900  match=900  bad=0 neg=559  traced=2 undeclared=0 stopped=0
  CATAMA create_ama cases=1800 match=1800 bad=0 neg=513  traced=7 undeclared=0 stopped=0
  CATAMA node_ama   cases=1200 match=1200 bad=0 neg=218  traced=7 undeclared=0 stopped=0
  CATAMA summon_ama cases=1200 match=1200 bad=0 neg=915  traced=2 undeclared=0 stopped=0
  CATAMA static data_imms=0 data_stores=0 pins=34 pins_ok=34 ro_reads=4 table_entries=17
  ```
  8 300 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 96 or more cases: `filt_swap` 335, `tohit0` 175, `blk_swap` 295, `src_a` 323, `g_any` 122, `w24_zero` 715;
  the smallest, `nonorm`, 51); the site control fails on all 4 190 matched boundary cases (33 `site` lines: function,
  boundary, return address). The skills calc function count's scan names every operand form (`PTR` and `moffs`
  stores, immediates, reads): 0 stores, 0 immediates, 7 reads. The first session of this lane ran the six families at
  once and was killed by the system's out-of-memory handler before checking; the resumed lane regenerated its case
  files (byte-identical), re-ran the families one at a time and compared the new outputs with that session's before
  replacing them: byte-identical, so nothing of it is lost.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  start 4's and 5's results and every refusal path) and of their maps up to their boundary calls with the call site,
  the arguments, the pointed-to blocks, the frame words, the written words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0009 names each claim's boundary). No
  function draws before its boundary or return; no case steps either seed. Not covered: what any boundary callee does
  and everything after it (start 10's elemental draw among it); when the game runs these functions or with which
  seed. (fn:sub_005DB410_SkillDo08MultiShot@0x005DB410, fn:SKILLS_GetToHit@0x006449F0)

## run:2026-10-20-cat-emu-nec

- **Question:** (plan 0046 Phase 1, batch `nec`) Do the necromancer start functions 15–21 and do functions 30–32 and
  55–63 map their inputs (the Skills, ItemStatCost, MonStats, MonStats2 and item records, the difficulty table, the
  bit-set `DataTables+0x150`, the caster, its path, room and stat list, the target unit, its mode, flags, stat lists,
  state words, item data and room, and the seeds) to the result they return, or to the arguments, pointed-to blocks,
  frame words and seed states at the call they end in, exactly as [skills/0010](0010-necromancer.md) §§ 3–6 say, and
  do they leave both seeds alone?
- **Setup:** as run:2026-10-20-cat-emu-ama: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m7`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `nec` families of `tools/skills_catalogue_emu.py` (`27b93f23…`), with `ama`'s conventions (the call site of
  every boundary asserted with a site control, both seeds written and compared in every case, a boundary's pointer
  argument compared by content: do 30's and do 61's 0x68-byte blocks, the `SpawnOwnedMonster` blocks, the
  `COMBAT_ApplyDamage` packet, the zeroed hit packet; frame words at their absolute stack address; no model compares a
  callee-saved register that is not a boundary argument). New: a boundary inside a helper the batch function called
  (`0x005C2FF0`, `0x005C3300`, `0x005C31F0`, `0x005C5BC0`) also compares the helper's return address into the batch
  function at its absolute stack slot (ruling 1 of the `lane/p46m6` review); `static` lists every call of each helper.
  All inputs synthetic (stock parameter values among them); every case-writer draw from
  `random.Random("catnec-<family>")`. Files in `workspace/logs/skills-cat-nec/`, `manifest.sha256` `792c0cb4…` (28 files: cases, memory
  specs, expected inputs, outputs, the `.err` logs, `cases.txt`, `check.txt` `10fec33a…`, `static.txt` `c8bdc9e9…`,
  `rows.txt` `2e561e99…` with its `rows.sh`, `repro.txt` `387455f3…` with its `repro.sh`, the run script
  `run_nec.sh`); `sha256sum -c
  manifest.sha256` from that directory passes. `repro.txt` records that the same tool revision regenerates every case,
  memory and expectation file of 9a, 9b, 9c, 9d, `sor` and `ama` byte for byte and reproduces their kept `check.txt`
  and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-nec
  python3 -I tools/skills_catalogue_emu.py cases --batch nec > $D/cases.txt
  for f in start_nec curse_nec corpse_nec summon_nec; do      # one at a time ($D/run_nec.sh)
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m7 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch nec > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch nec > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch nec --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles,
  ItemStatCost, MonStats, MonStats2, the calc pool, the States and PetType counts, the bit-set at `+0x150`), sets
  `g_pDifficultyLevels`/`g_nDifficultyLevels` and `ITEMS_GetRecord`'s count and table, names the boundaries
  (`observe`: `ama`'s plus `sub_0056E780_SkillForUnitsNearTarget`, `COMBAT_ApplyDamage`, `0x0061A270`, `STATE_Set`,
  `0x0056E2F0`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATNEC start_nec  cases=1600 match=1600 bad=0 neg=295 traced=84 undeclared=0 stopped=0
  CATNEC curse_nec  cases=1400 match=1400 bad=0 neg=485 traced=4  undeclared=0 stopped=0
  CATNEC corpse_nec cases=1500 match=1500 bad=0 neg=238 traced=8  undeclared=0 stopped=0
  CATNEC summon_nec cases=1600 match=1600 bad=0 neg=1332 traced=90 undeclared=0 stopped=0
  CATNEC static data_imms=0 data_stores=0 helper_sites=8 pins=38 pins_ok=38 ro_reads=5 table_entries=19
  ```
  6 100 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 76 or more cases: `town_inv` 274, `aura1_read` 319, `nomiss0` 80, `w24_zero` 741; the weak ones fail on the
  deciding class skills/0010 § 2 names); the site control fails on all 1 891 matched boundary cases (17 `site` lines:
  function, boundary, return address). The skills calc function count's scan names every operand form (`PTR` and
  `moffs` stores, immediates, reads): 0 stores, 0 immediates, 7 reads. The first runs of the four families found three
  model faults (do 63's range exit returns 1, do 31's `0x0061A270` takes three stack words, the fatal path's return
  address is `0x00629CDA`) and low reach on the corpse and room paths; the models and case writers were fixed and every
  family re-run; the kept outputs are the last runs'.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  start 15's, 17's, 18's, 19's and 20's results and every refusal path) and of their maps up to their boundary calls
  with the call site, the helper return addresses, the arguments, the pointed-to blocks, the frame words, the written
  words and both seeds asserted (`[C]` under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md);
  skills/0010 names each claim's boundary). No function draws before its boundary or return; no case steps either
  seed. Not covered: what any boundary callee does and everything after it (do 55's and do 58's draws on the target's
  seed among it); when the game runs these functions or with which seed. (fn:sub_005C37C0_SkillDo30Curse@0x005C37C0,
  fn:sub_00645510_MonCorpseTest@0x00645510)

## run:2026-10-20-cat-emu-pal

- **Question:** (plan 0046 Phase 1, batch `pal`) Do the paladin start functions 29, 31, 35, 36, 37 and do functions
  64–67, 73, 79–82 and 150 map their inputs (the Skills, CharStats and MonStats records, the caster, its path, used
  skill node, queued hits, stat list and inventory word, the target unit, its stat lists and room, the game frame, and
  the seeds) to the result they return, or to the arguments, pointed-to blocks, node and frame words and seed states at
  the call they end in, exactly as [skills/0011](0011-paladin.md) §§ 3–5 say, and do they leave both seeds alone?
- **Setup:** as run:2026-10-20-cat-emu-nec: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m8`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `pal` families of `tools/skills_catalogue_emu.py` (`c1630af4…`), with `nec`'s conventions (the
  call site of every boundary asserted with a site control, both seeds written and compared in every case, a
  boundary's pointer argument compared by content: the aura functions' 0x50-byte blocks and their 16-byte context
  passed in `ECX`, the `COMBAT_ApplyDamage` packet, the zeroed hit packet, the `MissileCreate` blocks; the used skill's
  node words dumped and compared; no model compares a callee-saved register that is not a boundary argument; a boundary
  inside a helper compares the helper's return address at its stack slot, or the helper's single call site is listed by
  `static`). New: `0x0056B740` runs emulated, so the aura boundary is `AURA_ApplyToTarget` entered through an indirect
  call. All inputs synthetic (stock parameter values among them); every case-writer draw from
  `random.Random("catpal-<family>")`. Files in `workspace/logs/skills-cat-pal/`, `manifest.sha256` `12c8d5c0…` (23
  files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`, `check.txt` `989e5367…`,
  `static.txt` `5fd43532…`, `rows.txt` `dc96db87…` with its `rows.sh`, `repro.txt` `daf042cc…` with its `repro.sh`, the
  run script `run_pal.sh`); `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the
  same tool revision regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama` and `nec` byte
  for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-pal
  python3 -I tools/skills_catalogue_emu.py cases --batch pal > $D/cases.txt
  for f in aura_pal melee_pal move_pal; do      # one at a time ($D/run_pal.sh)
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m8 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch pal > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch pal > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch pal --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles,
  ItemStatCost, MonStats, MonStats2, CharStats, the calc pool, the States and PetType counts), names the boundaries
  (`observe`: `nec`'s plus `AURA_ApplyToTarget`, `0x0063C8F0`, `0x006633B0`, `sub_00648690_PathSetSpeed`,
  `0x00649050`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATPAL aura_pal  cases=1600 match=1600 bad=0 neg=907 traced=3 undeclared=0 stopped=0
  CATPAL melee_pal cases=1750 match=1750 bad=0 neg=213 traced=9 undeclared=0 stopped=0
  CATPAL move_pal  cases=1600 match=1600 bad=0 neg=381 traced=8 undeclared=0 stopped=0
  CATPAL static data_imms=0 data_stores=0 helper_sites=16 pins=40 pins_ok=40 ro_reads=4 table_entries=15
  ```
  4 950 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 134 or more cases: `npf6` 552, `inv_any` 134, `xy73` 153; the weak ones fail on the deciding class
  skills/0011 § 2 names); the site control fails on all 2 615 matched boundary cases (21 `site` lines: function,
  boundary, return address). The skills calc function count's scan names every operand form (`PTR` and `moffs` stores,
  immediates, reads): 0 stores, 0 immediates, 7 reads. Every family matched on its first emulation; one tool fault (a
  pal model helper that shadowed a `sor` helper of the same name) was caught by `repro.sh` before the kept files were
  written and renamed; the case files did not change.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  start 36's and start 37's results, do 64's and do 65's 1, every refusal path) and of their maps up to their boundary
  calls with the call site, the helper return addresses, the arguments, the pointed-to blocks and context, the node and
  frame words and both seeds asserted (`[C]` under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md);
  skills/0011 names each claim's boundary). No function draws before its boundary or return; no case steps either
  seed. Not covered: what any boundary callee does and everything after it (the aura target passes and their draws on
  the caster's and the units' seeds, start 35's and do 79's draws on the caster's seed among it); when the game runs
  these functions or with which seed. (fn:sub_005CF010_PalAuraDo@0x005CF010, fn:sub_005CE8E0_SkillDo64SacrificeSelfHit@0x005CE8E0)

## run:2026-10-21-cat-emu-bar

- **Question:** (plan 0046 Phase 1, batch `bar`) Do the barbarian start functions 32–34 and 38–41 and do functions 2,
  9, 68–72 and 74–78 map their inputs (the Skills and MonStats2 records, the caster, its path, used-skill node, unit
  skill chain, queued hits, stat lists, `+0x38` word and inventory word, the target unit, its stat lists, room and
  position, the rooms, the game frame and pool word, and the seeds) to the result they return, or to the arguments,
  pointed-to blocks, node, path and frame words and seed states at the call they end in, exactly as
  [skills/0012](0012-barbarian.md) §§ 3–6 say, and do they leave both seeds alone?
- **Setup:** as run:2026-10-20-cat-emu-pal: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m9`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `bar` families of `tools/skills_catalogue_emu.py` (`613471e3…`), with `pal`'s conventions
  (the call site of every boundary asserted with a site control, both seeds written and compared in every case, a
  boundary's pointer argument compared by content: the hit packet, do 75's and start 40's points, `NovaAtUnit`'s block,
  do 71's search context; the node, path and list words dumped and compared; register arguments compared only where the
  callee reads them before writing them; no model compares a callee-saved register that is not a boundary argument; a
  boundary inside a helper compares the helper's return address at its absolute stack slot, the helpers' call sites
  listed by `static`). All inputs synthetic (stock parameter values among them); every case-writer draw from
  `random.Random("catbar-<family>")`. Files in `workspace/logs/skills-cat-bar/`, `manifest.sha256` `737c8b4f…` (28
  files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`, `check.txt` `13b1a4d2…`,
  `static.txt` `4808f177…`, `rows.txt` `9646927a…` with its `rows.sh`, `repro.txt` `65c7b964…` with its `repro.sh`, the
  run script `run_bar.sh`); `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the
  same tool revision regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec` and
  `pal` byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-bar
  python3 -I tools/skills_catalogue_emu.py cases --batch bar > $D/cases.txt
  for f in cry_bar hit_bar corpse_bar move_bar; do      # one at a time ($D/run_bar.sh)
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m9 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch bar > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch bar > $D/static.txt
  $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch bar --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles,
  ItemStatCost, MonStats, MonStats2, the calc pool, the States, PetType and overlay counts, the `+0x150` state set),
  names the boundaries (`observe`: `pal`'s plus `0x0056E520`, `UnitQueueEvent`, `FreeNearFallback`, `PathSetType`,
  `MonSkillAttackDo`, `COLL_PatternTestBool`, `0x005D9460`, `0x00553DC0`, `0x006212C0`, `0x005DA120`, `0x005D9F70`,
  `0x005DA660`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATBAR hit_bar    cases=1750 match=1750 bad=0 neg=357 traced=67 undeclared=0 stopped=0
  CATBAR corpse_bar cases=2500 match=2500 bad=0 neg=233 traced=7 undeclared=0 stopped=0
  CATBAR cry_bar    cases=800 match=800 bad=0 neg=542 traced=9 undeclared=0 stopped=0
  CATBAR move_bar   cases=1750 match=1750 bad=0 neg=236 traced=21 undeclared=0 stopped=0
  CATBAR static data_imms=0 data_stores=0 helper_sites=49 pins=45 pins_ok=45 ro_reads=6 table_entries=19
  ```
  6 800 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more cases: `par_low` 224, `no12` 109, `vel1` 257, `x1` 90; the weak ones fail on the deciding class
  skills/0012 § 2 names); the site control fails on all 2 397 matched boundary cases (39 `site` lines: function,
  boundary, return address). The skills calc function count's scan names every operand form (`PTR` and `moffs` stores,
  immediates, reads): 0 stores, 0 immediates, 7 reads. `hit_bar` and `cry_bar` matched on their first emulation (one
  fix to the declared read set: `NovaAtUnit`'s offsets); the first `corpse_bar` and `move_bar` runs mismatched on tool
  faults (missing dumps of the compared node, path and list words; do 76's `+0xC6` byte written over the compared
  `+0xC4` word; too few points inside rooms to reach two free-spot calls), fixed in the case writers before the kept
  run; those first outputs were overwritten by the kept run of the same file names.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  start 33's and start 34's results, do 78's 1 with its node word, every refusal path) and of their maps up to their
  boundary calls with the call site, the helper return addresses, the arguments (register arguments where the callee
  reads them first), the pointed-to blocks, the node, path and frame words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0012 names each claim's boundary). No function
  draws before its boundary or return; no case steps either seed. Not covered: what any boundary callee does and
  everything after it (do 69's and do 72's draws on the caster's seed, do 69's inline step, the hits' elemental rolls
  among it); when the game runs these functions or with which seed. (fn:sub_005D81C0_SkillDo69FindPotion@0x005D81C0,
  fn:sub_005D9A10_LeapPoint@0x005D9A10)

## run:2026-10-21-cat-emu-dru

- **Question:** (plan 0046 Phase 1, batch `dru`) Do the druid start functions 56–58, do functions 114–124 and do-table
  entries 145 and 146 map their inputs (the Skills and Missiles records, the caster, its path, used-skill node, unit
  skill chain, stat lists and state words, the target unit and its position, the rooms and their collision maps, the
  state list at `DataTables+0x17C`, the game frame and pool word, and the seeds) to the result they return, or to the
  arguments, pointed-to blocks, node, frame and argument-slot words and seed states at the call they end in, exactly
  as [skills/0013](0013-druid.md) §§ 3–7 say, and which seed does each draw before its boundary step?
- **Setup:** as run:2026-10-21-cat-emu-bar: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m10`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `dru` families of `tools/skills_catalogue_emu.py` (`11b763dd…`; the kept outputs were
  emulated from case files that this revision regenerates byte for byte, and it reproduces the kept `check.txt` byte
  for byte), with `bar`'s conventions (the call site of every boundary asserted with a site control, both seeds written
  and compared in every case, a boundary's pointer argument compared by content: the spawn blocks, the hit packets,
  the `MissileCreate` blocks, `COLL_RectTest`'s rectangle; the node and argument-slot words dumped and compared;
  register arguments compared only where the callee reads them before writing them; no model compares a callee-saved
  register that is not a boundary argument; a boundary inside a helper compares the helper's return address at its
  absolute stack slot, the helpers' call sites listed by `static`). All inputs synthetic (stock parameter values among
  them); every case-writer draw from `random.Random("catdru-<family>")`. Files in `workspace/logs/skills-cat-dru/`,
  `manifest.sha256` `d1a77e1f…` (69 files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`,
  `check.txt` `592baf51…`, `static.txt` `d2c98496…`, `rows.txt` `fba56eef…` with its `rows.sh`, `repro.txt`
  `c6f4b37b…` with its `repro.sh`, the run script `run_dru.sh`, and the two development runs under `dev/` with
  `dev/notes.txt`); `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the same tool
  revision regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal` and `bar`
  byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-dru
  python3 -I tools/skills_catalogue_emu.py cases --batch dru > $D/cases.txt
  $D/run_dru.sh $D summon_dru shape_dru melee_dru miss_dru     # one EmuBoundary instance at a time, each in a 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch dru > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch dru > $D/static.txt
  $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch dru --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles,
  ItemStatCost, MonStats, MonStats2, the calc pool, the States, PetType counts and the States record base), names the
  boundaries (`observe`: `bar`'s less `COLL_WHTest`, which runs here, plus `COMBAT_BuildDamage`, `StatListSetEnd`,
  `UNIT_UnlinkStatList`, `COLL_RectTest`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATDRU summon_dru cases=1500 match=1500 bad=0 neg=1622 traced=7 undeclared=0 stopped=0
  CATDRU shape_dru  cases=2500 match=2500 bad=0 neg=620 traced=84 undeclared=0 stopped=0
  CATDRU melee_dru  cases=2400 match=2400 bad=0 neg=438 traced=41 undeclared=0 stopped=0
  CATDRU miss_dru   cases=2000 match=2000 bad=0 neg=441 traced=9 undeclared=0 stopped=0
  CATDRU static data_imms=0 data_stores=0 helper_sites=25 pins=43 pins_ok=43 ro_reads=4 table_entries=16
  ```
  8 400 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more cases: `w24_zero` 735, `notown` 134, `rf_ignored` 171, `c1_ge0` 156; the weak ones fail on the
  deciding class skills/0013 § 2 names); the site control fails on all 3 967 matched boundary cases (33 `site` lines:
  function, boundary, return address; 747 + 1 694 + 931 + 595). The skills calc function count's scan names every
  operand form: 0 stores, 0 immediates, 7 reads. Two development runs came first and are kept under their own names in
  `dev/` (`dev/notes.txt`): the first mismatched on 3 do 121 cases (the model walked the whole state list where the
  case wrote a count of 0) and had one control that did not fail (no class past the Missiles count); the second matched
  in full; the writers were re-weighted between them and one control added before the kept run.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, do 119's and do 123's 0, do 118's and do 120's 1) and of their maps up to their boundary calls
  with the call site, the helper return addresses, the arguments (register arguments where the callee reads them
  first), the pointed-to blocks, the node, frame and argument-slot words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0013 names each claim's boundary). Two
  functions draw before their boundary, each one `RNG_Range` on the caster's seed: do 124 (`0x10000`, the value at
  `ebp−0xC`) and do 123 (`0x100`, the low byte at `[ebp+0x8]`); no case steps the target's seed. Not covered: what any
  boundary callee does and everything after it (entry 146's re-seed of the caster's seed and its free-point draws,
  entry 145's damage rolls, the hits' elemental rolls among it); when the game runs these functions or with which seed.
  (fn:sub_005C8190_SkillDo124PeriodicState@0x005C8190, fn:sub_005C8080_SkillDo123Volcano@0x005C8080)

## run:2026-10-21-cat-emu-ass

- **Question:** (plan 0046 Phase 1, batch `ass`) Do the assassin start functions 22–28, do functions 33–52 and 54 and
  the progressive entries 36–41 and 143 map their inputs (the Skills, Missiles and Levels records, the caster, its
  path, used-skill node, unit skill chain, stat lists, state words, inventory word and queued hits, the target unit and
  its position, the rooms, a monster caster's owner, the game frame and pool word, and the seeds) to the result they
  return, or to the arguments, pointed-to blocks, node, frame, argument-slot and stack-seed words and seed states at the
  call they end in, exactly as [skills/0014](0014-assassin.md) §§ 3–6 say, and which seed does each draw before its
  boundary step?
- **Setup:** as run:2026-10-21-cat-emu-dru: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m11`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged. No wine, nothing runs natively, no slot. Models, case writers and
  checks: the `ass` families of `tools/skills_catalogue_emu.py` (`b38bba31…`; the kept outputs were emulated from case
  files this revision regenerates byte for byte, and it reproduces the kept `check.txt` byte for byte), with `dru`'s
  conventions (the call site of every boundary asserted with a site control, both seeds written and compared in every
  case, a boundary's pointer argument compared by content: the hit packets, the `MissileCreate`, spawn and
  `ApplyTimed` blocks; the node, argument-slot, frame and stack-seed words dumped and compared; register arguments
  compared only where the callee reads them before writing them; no model compares a callee-saved register that is not
  a boundary argument; a boundary inside a helper compares the helper's return address at its absolute stack slot, the
  helpers' call sites listed by `static`). All inputs synthetic (stock parameter values among them); every case-writer
  draw from `random.Random("catass-<family>")`. Files in `workspace/logs/skills-cat-ass/`, `manifest.sha256`
  `04f487b6…` (70 files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`, `check.txt`
  `dd6ed294…`, `static.txt` `fcf4be4f…`, `rows.txt` `3f8ff8a8…` with its `rows.sh`, `repro.txt` `43e65419…` with its
  `repro.sh`, the run script `run_ass.sh`, and the two development runs under `dev/` with `dev/notes.txt`);
  `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the same tool revision
  regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal`, `bar` and `dru`
  byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-ass
  python3 -I tools/skills_catalogue_emu.py cases --batch ass > $D/cases.txt
  $D/run_ass.sh $D start_ass hit_ass prg_ass trap_ass     # one EmuBoundary instance at a time, each in a 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch ass > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch ass > $D/static.txt
  $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch ass --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles,
  ItemStatCost, MonStats, MonStats2, the calc pool, the States, PetType counts and the Levels records at `+0xC58`/
  `+0xC5C`), sets the missile table and count `MissileSpeedAtLevel` reads (`0x0096C794`/`0x0096C79C`, as in `sor`),
  names the boundaries (`observe`: `dru`'s plus `COMBAT_PrgFinisher`, `InvGetBodyLocItem`, `UnitTeleport`,
  `0x006229F0`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATASS start_ass cases=2100 match=2100 bad=0 neg=507 traced=64 undeclared=0 stopped=0
  CATASS hit_ass   cases=2100 match=2100 bad=0 neg=632 traced=63 undeclared=0 stopped=0
  CATASS prg_ass   cases=2100 match=2100 bad=0 neg=1559 traced=12 undeclared=0 stopped=0
  CATASS trap_ass  cases=2400 match=2400 bad=0 neg=511 traced=97 undeclared=0 stopped=0
  CATASS static data_imms=0 data_stores=0 helper_sites=22 pins=66 pins_ok=66 ro_reads=5 table_entries=29
  ```
  8 700 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more cases: `st25_inv` 300, `parity_inv` 350, `noseed` 1 200, `pet_keep` 165; the weak ones fail on
  the deciding class skills/0014 § 2 names); the site control fails on all 3 020 matched boundary cases (37 `site`
  lines: function, boundary, return address; 685 + 753 + 674 + 908). The skills calc function count's scan names every
  operand form: 0 stores, 0 immediates, 7 reads. Two development runs came first and are kept under their own names in
  `dev/` (`dev/notes.txt`): the first mismatched on 131 do 46 and do 52 cases and one start 26 case (the model read the
  json row's stat values by integer key; the keys are strings) and had two controls that did not fail; the second
  matched in full; the writers were re-weighted between them and before the kept run.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, start 22's and 25's results, do 35's 1, entry 39's and 41's 1, do 54's town 1) and of their maps
  up to their boundary calls with the call site, the helper return addresses, the arguments (register arguments where
  the callee reads them first), the pointed-to blocks, the node, frame, argument-slot and stack-seed words and both
  seeds asserted (`[C]` under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0014 names each
  claim's boundary). Four entries draw before their boundary, each one inline step of the caster's seed at entry before
  the record test: 37 and 143 (then one step of the ring's stack seed), 39 (then two `RNG_Range` of its stack seed per
  try) and 41 (then two steps of its stack seed); no case steps the target's seed. Not covered: what any boundary
  callee does and everything after it (do 33's knock step and do 42's `RNG_Range(100)` on the caster's seed, the
  physical and elemental rolls, the finisher, the rings' later creations among it); when the game runs these functions
  or with which seed. (fn:sub_005D4E70_SkillPrgDo37Ring@0x005D4E70, fn:sub_005D3F90_SkillPrgDo39Scatter@0x005D3F90,
  fn:sub_005D5080_SkillPrgDo41Scatter@0x005D5080)

## run:2026-10-21-cat-emu-item

- **Question:** (plan 0046 Phase 1, batch 10 `item`) Do Unsummon's start 3 and do 4, do 113, do 151, `ITEMSKILL_Cast`
  with its `ItemTarget` helpers and its two callers `ItemCastAtUnit` / `ItemCastAtXY`, the stat-event handlers 20, 21
  and 30, the shrine functions 19, 21 and 22 and `SKILLS_PayCost` map their inputs (the Skills, PetType, Books, Shrines
  and item records, the item-type equivalence words, the caster, its path, used node, pet lists, inventory and items,
  stat lists and state words, the target, the stored unit, the event packet, the shrine and its context, and the
  seeds) to the result they return, or to the arguments, pointed-to blocks, path, node, frame and out words and seed
  states at the call they end in, exactly as [skills/0015](0015-item.md) §§ 3–8 say, and which seed does each draw
  before its boundary step?
- **Setup:** as run:2026-10-21-cat-emu-ass: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m12`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged. No wine, nothing runs natively, no slot. Models, case writers and
  checks: the `item` families of `tools/skills_catalogue_emu.py` (`904fe25e…`; the kept outputs were emulated from case
  files this revision regenerates byte for byte, written by `fc207804…`, which differs only in the `CLASS` lines of
  `check`), with `ass`'s conventions (the call site of every boundary asserted with a site control; the caster's, the
  target's and the shrine's seeds written and compared in every case; a boundary's pointer argument compared by
  content: the `MissileCreate` blocks and shrine 19's search block; the node, path, out, argument-slot and frame words
  dumped and compared; register arguments compared only where the callee reads them before writing them, `EAX`
  among them for `UseCharge`; a boundary inside a helper or inside `ITEMSKILL_Cast` called by its callers compares the
  return address at its absolute stack slot). All inputs synthetic (stock parameter values among them); every
  case-writer draw from `random.Random("catitem-<family>")`. Files in `workspace/logs/skills-cat-item/`,
  `manifest.sha256` `3e974e32…` (118 files: cases, memory specs, expected inputs, outputs, the `.err` logs,
  `cases.txt`, `check.txt` `22402718…`, `static.txt` `55299029…`, `rows.txt` `a9e0cb25…` with its `rows.sh`, `repro.txt`
  `41e54f5b…` with its `repro.sh`, `cg.txt` `42b678eb…` with `cg.sh` and the five call-graph files, the run script
  `run_item.sh`, and the three development runs under `dev/` with `dev/notes.txt`); `sha256sum -c manifest.sha256`
  from that directory passes. `repro.txt` records that the same tool revision regenerates every case, memory and
  expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal`, `bar`, `dru` and `ass` byte for byte and reproduces
  their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-item
  python3 -I tools/skills_catalogue_emu.py cases --batch item > $D/cases.txt
  $D/run_item.sh $D use_item cast_item event_item shrine_item cost_item   # one EmuBoundary instance at a time, 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch item > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch item > $D/static.txt
  $D/rows.sh > $D/rows.txt; $D/cg.sh > $D/cg.txt; $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch item --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, the calc
  pool, ItemStatCost, the States, PetType counts and records, the item-type count, stride and equivalence words, the
  item-skill layer shift 6 and mask 0x3F), sets `ITEMS_GetRecord`'s and `BOOKS_GetRecord`'s counts and tables
  (`0x0096CA58`/`0x0096CA5C`, `0x0096CC60`/`0x0096CC64`) and the cookie, names the family's boundaries (`observe`) and
  guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATITEM use_item    cases=2400 match=2400 bad=0 neg=1069 traced=13 undeclared=0 stopped=0
  CATITEM cast_item   cases=3000 match=3000 bad=0 neg=1701 traced=11 undeclared=0 stopped=0
  CATITEM event_item  cases=3000 match=3000 bad=0 neg=1757 traced=2 undeclared=0 stopped=0
  CATITEM shrine_item cases=1800 match=1800 bad=0 neg=2474 traced=1 undeclared=0 stopped=0
  CATITEM cost_item   cases=1800 match=1800 bad=0 neg=597 traced=2 undeclared=0 stopped=0
  CATITEM static data_imms=0 data_stores=0 helper_sites=72 pins=74 pins_ok=74 ro_reads=4 table_entries=12
  ```
  12 000 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more: `flag0` 531, `aim_none` 471, `layer_full` 1 037, `sh_noseed` 784, `no_min` 241; the thinner ones
  equal their deciding classes on the `CLASS` lines); the site control fails on all 4 936 matched boundary cases (31
  `site` lines: function, boundary, return address; 934 + 1 317 + 386 + 1 800 + 499). The skills calc function count's
  scan names every operand form: 0 stores, 0 immediates, 7 reads. The static call graphs (`cg.txt`): helpers 3 and 4
  and `0x0056E390` hold no LCG step or RNG call (586, 554, 578 functions; 56, 54, 56 indirect calls not followed),
  helper 2 only its own (564), `SKILLS_PayCost` none (619; 57). Three development runs came first and are kept in
  `dev/` (`dev/notes.txt`): the first mismatched on 61 `cast_item` cases (the writer left the caster's hash slot
  unwritten and the emulator, which keeps memory between cases, read an earlier case's slot); the second and third
  matched in full; the writers were re-weighted between them.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, start 3's mark and 1, the cast's restore, `ItemTgtDo`'s 1 with no other unit, the cost's 0s)
  and of their maps up to their boundary calls with the call site, the nested return addresses, the arguments
  (register arguments where the callee reads them first), the pointed-to blocks, the path, node, out and frame words
  and the three seeds asserted (`[C]` under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md);
  skills/0015 names each claim's boundary). Draws before the boundaries: handlers 20 (packet condition) and 30 one
  inline step of the unit's seed, handler 21 `RNG_RangeB(unit, 100)`, `ITEMSKILL_Cast`'s helper 2 two steps of the
  cast's caster's seed, shrines 21 and 22 `RNG_RangeB(shrine, Arg1 − Arg0)` on the shrine's seed; no other case steps a
  seed. Not covered: what any boundary callee does and everything after it (the casts' do functions, helper 2's later
  tries, the potions and missiles of the shrines, `UseCharge`); when the game runs these functions or with which
  seed. (fn:ITEMSKILL_Cast@0x005FDA80, fn:sub_005FD850_ItemTargetRandomPoint@0x005FD850,
  fn:sub_005C0470_StatEv20SkillOnEvent@0x005C0470, fn:SHRINE_Exploding@0x005830E0)

## run:2026-10-21-cat-emu-8a

- **Question:** (plan 0046 Phase 1, batch 8a) Do the monster start functions 42–53 and do functions 83–98, 110 and 111
  map their inputs (the Skills, Missiles, MonStats and MonStats2 records, the caster, its path, used node, stat lists,
  state words, frame words and owner link, the target, its path, stat list and state words, the rooms, the game frame
  and pool word, and the seeds) to the result they return, or to the arguments, pointed-to blocks, node, path, frame and
  argument-slot words and seed states at the call they end in, exactly as [skills/0016](0016-monster-8a.md) §§ 3–6
  say, and which seed does each draw before its boundary step?
- **Setup:** as run:2026-10-21-cat-emu-item: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m13`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged. No wine, nothing runs natively, no slot. Models, case writers and
  checks: the `8a` families of `tools/skills_catalogue_emu.py` (`e2f67728…`; the kept outputs were emulated from case
  files this revision regenerates byte for byte, and it reproduces the kept `check.txt` and `static.txt` byte for byte),
  with `item`'s conventions (the call site of every boundary asserted with a site control; the caster's and the target's
  seeds written and compared in every case; a boundary's pointer argument compared by content: the hit packets and the
  `MissileCreate` blocks; the node, path, frame and both argument-slot words dumped and compared, each dumped byte
  written by the case; register arguments compared only where the callee reads them before writing them; a boundary
  inside a helper compares the helper's return address at its absolute stack slot). All inputs synthetic (stock
  parameter values among them); every case-writer draw from `random.Random("cat8a-<family>")`. Files in
  `workspace/logs/skills-cat-8a/`, `manifest.sha256` `10a8ce1f…` (106 files: cases, memory specs, expected inputs, outputs, the `.err` logs,
  `cases.txt`, `check.txt` `b06f25a1…`, `static.txt` `f4ed00d9…`, `rows.txt` `d842e64a…` with its `rows.sh`, `repro.txt`
  `485fdbef…` with its `repro.sh`, the run script `run_8a.sh`, and the three development runs under `dev/` with `dev/notes.txt`);
  `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the same tool revision
  regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal`, `bar`, `dru`,
  `ass` and `item` byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept
  outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-8a
  python3 -I tools/skills_catalogue_emu.py cases --batch 8a > $D/cases.txt
  $D/run_8a.sh $D hit_8a move_8a summon_8a miss_8a aura_8a   # one EmuBoundary instance at a time, 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch 8a > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 8a > $D/static.txt
  $D/rows.sh > $D/rows.txt; $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 8a --write
  ```
  The memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles
  with count 48, ItemStatCost, MonStats, MonStats2, the calc pool, the States and PetType counts, the state set at
  `+0xD4`, the overlay count), sets `MONSTATS_GetClassChainPos`'s table and count (`0x0096C6A8`/`0x0096C6B0`) and the
  cookie, names the boundaries (`observe`; the allocator `0x0040B430` in `aura_8a` only) and guards the allocator and
  the fatal path elsewhere.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CAT8A hit_8a    cases=2400 match=2400 bad=0 neg=679 traced=31 undeclared=0 stopped=0
  CAT8A move_8a   cases=2600 match=2600 bad=0 neg=953 traced=7 undeclared=0 stopped=0
  CAT8A summon_8a cases=2500 match=2500 bad=0 neg=795 traced=346 undeclared=0 stopped=0
  CAT8A miss_8a   cases=2500 match=2500 bad=0 neg=432 traced=434 undeclared=0 stopped=0
  CAT8A aura_8a   cases=600 match=600 bad=0 neg=409 traced=5 undeclared=0 stopped=0
  CAT8A static data_imms=0 data_stores=0 entry_words=30 helper_sites=51 pins=52 pins_ok=52 ro_reads=8 table_entries=30
  ```
  12 600 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more: `q40` 249, `f_le1` 200, `keep3c` 251, `axis_swap` 162, `r_lvl1` 409; the thinner ones equal their
  deciding classes on the nine `CLASS` lines); the site control fails on all 5 135 matched boundary cases (31 `site`
  lines: function, boundary, return address; 1 041 + 1 459 + 970 + 1 159 + 506). The `.data` reads have no writer in
  `.text`: the skills calc function count (0 stores, 0 immediates, 7 reads) and the byte map `0x00745600` (three reads
  in `0x007455C0`–`0x007456FF`, no store, no immediate). Three development runs came first and are kept in `dev/`
  (`dev/notes.txt`): the start 32 return slot guessed, do 98 modelled after an id test it does not make, `PathDirection`'s
  ratio leaving its table for far points (the writer now keeps do 87's and do 88's points within 250 subtiles), and do
  93's target words read as a point (they are offsets).
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, start 46's node words, start 51's and 52's flag words, do 94's frame test, start 53's state-12
  return, do 86's `n ≤ 0` return) and of their maps up to their boundary calls with the call site, the nested return
  addresses, the arguments (register arguments where the callee reads them first), the pointed-to blocks and packets,
  the node, path, argument-slot and frame words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0016 names each claim's boundary). One draw
  before a boundary: do 96's `RNG_RangeB(caster, hi − lo)`; no other case steps a seed. Not covered: what any boundary
  callee does and everything after it (the spawns, the hits' delivery, the missiles, the continuations after
  `CancelEvents`, do 111's loop); when the game runs these functions or with which seed.
  (fn:sub_005CC840_SkillDo96Heal@0x005CC840, fn:sub_0064FC60_PathDirection@0x0064FC60,
  fn:sub_005CAE40_SkillSt42FireHit@0x005CAE40)

## run:2026-10-21-cat-emu-8b

- **Question:** (plan 0046 Phase 1, batch 8b) Do the monster start functions 54, 55, 59, 60, 64 and do functions
  99–109, 112, 125–127, 141 and 152 map their inputs (the Skills, Missiles, MonStats and MonStats2 records, the caster,
  its path, used node, stat lists, state words, frame words, queued hits and owner link, the target, its path and stat
  list, the rooms, the game frame and the seeds) to the result they return, or to the arguments, pointed-to blocks and
  packets, node, path and argument-slot words and seed states at the call they end in, exactly as
  [skills/0017](0017-monster-8b.md) §§ 3–5 say, and which seed does each draw before its boundary step?
- **Setup:** as run:2026-10-21-cat-emu-8a: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m14`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged. No wine, nothing runs natively, no slot. Models, case writers and
  checks: the `8b` families of `tools/skills_catalogue_emu.py` (`ba63f2a8…`; the kept outputs were emulated from case
  files this revision regenerates byte for byte, and it reproduces the kept `check.txt` and `static.txt` byte for byte),
  with 8a's conventions (the call site of every boundary asserted with a site control; the caster's and the target's
  seeds written and compared in every case; a boundary's pointer argument compared by content: the `MissileCreate`
  blocks, the hit packets, do 112's curse block, do 141's area block; the node, path, frame and argument-slot words
  dumped and compared, each dumped byte written by the case; register arguments compared only where the callee reads
  them before writing them; a boundary inside a helper compares the helper's return address at its absolute stack
  slot). All inputs synthetic (stock parameter values among them); every case-writer draw from
  `random.Random("cat8b-<family>")`. Files in `workspace/logs/skills-cat-8b/`, `manifest.sha256` `1c9c42ff…` (118
  files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`, `check.txt` `2f000a04…`,
  `static.txt` `4c181a27…`, `rows.txt` `46d85e01…` with its `rows.sh`, `repro.txt` `948be1e1…` with its `repro.sh`, the run
  script `run_8b.sh`, and the four development runs under `dev/` with `dev/notes.txt` and the first repro
  `dev/repro-dev1.txt`); `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the same
  tool revision regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal`,
  `bar`, `dru`, `ass`, `item` and 8a byte for byte and reproduces their kept `check.txt` and `static.txt` byte for
  byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-8b
  python3 -I tools/skills_catalogue_emu.py cases --batch 8b > $D/cases.txt
  $D/run_8b.sh $D curse_8b move_8b hit_8b miss_8b   # one EmuBoundary instance at a time, 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch 8b > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 8b > $D/static.txt
  $D/rows.sh > $D/rows.txt; $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 8b --write
  ```
  The memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills with count 3,
  or 92 for `curse_8b` so that do 112's curse rows exist; Missiles with count 48; ItemStatCost, MonStats, MonStats2,
  the calc pool, the States and PetType counts, the state set at `+0xD4`, the overlay count), sets
  `MONSTATS_GetClassChainPos`'s table and count, `sub_00663270_MissileSpeedAtLevel`'s missile table and count
  (`0x0096C794`/`0x0096C79C`) and the cookie, names the boundaries (`observe`) and guards the allocator and the fatal
  path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CAT8B miss_8b  cases=3200 match=3200 bad=0 neg=1088 traced=11 undeclared=0 stopped=0
  CAT8B hit_8b   cases=2800 match=2800 bad=0 neg=374 traced=10 undeclared=0 stopped=0
  CAT8B move_8b  cases=2400 match=2400 bad=0 neg=1129 traced=48 undeclared=0 stopped=0
  CAT8B curse_8b cases=800 match=800 bad=0 neg=1158 traced=12 undeclared=0 stopped=0
  CAT8B static d152_differ=0 data_imms=0 data_stores=0 entry_words=22 helper_sites=11 pins=64 pins_ok=64 ro_reads=6 table_entries=22
  ```
  9 200 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more: `speed0` 265, `rf_ignored` 152, `t64_inv` 400, `k_mod4` 578; every control equals its deciding
  class on the 24 `CLASS` lines); the site control fails on all 3 698 matched boundary cases (27 `site` lines:
  function, boundary, return address; 1 296 + 1 172 + 703 + 527). The one `.data` read, the skills calc function count,
  has no writer in `.text` (0 stores, 0 immediates, 7 reads). `static.txt` also finds do 152's 147 instructions equal
  to do 95's, start 59's 63 equal to start 53's but one, and computes the two shift bounds (`wrap` lines). Four
  development runs came first and are kept in `dev/` (`dev/notes.txt`): the stale target link's `+0x58` clearing and
  `0x0061A270`'s three stack words modelled wrong, one control that failed on no case, then the deciding classes and
  the writer's tuning; and a first repro whose `ass` static step ended with no output under one shared 4 GB scope.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, start 54's node and path words, start 55's count on its local seed, start 64's result, do 102's
  and do 105's `n ≤ 0` returns, do 103's last return, do 100's no-target 1) and of their maps up to their boundary
  calls with the call site, the nested return addresses, the arguments (register arguments where the callee reads them
  first), the pointed-to blocks and packets, the node, path and argument-slot words and both seeds asserted (`[C]`
  under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0017 names each claim's boundary). One
  draw on a unit's seed before a boundary: do 112's inline step of the caster's seed; start 55 draws on a local seed. Not
  covered: what any boundary callee does and everything after it (the further creations, the damage rolls, the leech
  and corpse heals after their calls, the inferno repeats); when the game runs these functions or with which seed.
  (fn:sub_005CE2B0_SkillDo112MonCurse@0x005CE2B0, fn:sub_005CD910_SkillSt55LocalSeed@0x005CD910,
  fn:sub_005CC690_SkillDo152DiabLight@0x005CC690)

## run:2026-10-21-cat-emu-8c

- **Question:** (plan 0046 Phase 1, batch 8c) Do the monster start functions 61–63 and do functions 128–137, 139, 140
  and 147–149 map their inputs (the Skills, Missiles, MonStats and MonStats2 records, the caster, its path, used node,
  stat list, monster data, owner links and `+0xC4`, the target, its path, stat list, state words, alignment list and
  owner link, the rooms, the game's frame and difficulty bytes, and the seeds) to the result they return, or to the
  arguments, pointed-to blocks and packets, node, frame and argument-slot words and seed states at the call they end
  in, exactly as [skills/0018](0018-monster-8c.md) §§ 3–5 say, and which seed does each draw before its boundary step?
- **Setup:** as run:2026-10-21-cat-emu-8b: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m15`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged. No wine, nothing runs natively, no slot. Models, case writers and
  checks: the `8c` families of `tools/skills_catalogue_emu.py` (`8911d02a…`; the kept outputs were emulated from case
  files this revision writes, and it gives the kept `check.txt` and `static.txt`), with 8a's and 8b's conventions (the
  call site of every boundary asserted with a site control; the caster's and the target's seeds written and compared
  in every case; a boundary's pointer argument compared by content: the `MissileCreate` block, the hit packet, the
  timed-state blocks; the node, frame and argument-slot words dumped and compared, each dumped byte written by the case;
  register arguments compared only where the callee reads them before writing them; a boundary inside a helper compares
  the helper's return address at its absolute stack slot). All inputs synthetic (stock parameter values among them);
  every case-writer draw from `random.Random("cat8c-<family>")`. Files in `workspace/logs/skills-cat-8c/`,
  `manifest.sha256` `9dc63588…` (92 files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`,
  `check.txt` `500b673c…`, `static.txt` `873640da…`, `rows.txt` `21a02907…` with its `rows.sh`, `repro.txt` `2a44bd63…`
  with its `repro.sh`, the run script `run_8c.sh`, and the three development runs under `dev/` with `dev/notes.txt`);
  `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the same tool revision (which also
  carries the `near8` docstring fix of the `lane/p46m13` review, fix 2) regenerates every case, memory and expectation
  file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal`, `bar`, `dru`, `ass`, `item`, 8a and 8b byte for byte and
  reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs (14 `REPRO` lines, each
  `differ=0 check=same static=same`).
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-8c
  python3 -I tools/skills_catalogue_emu.py cases --batch 8c > $D/cases.txt
  $D/run_8c.sh $D miss_8c hit_8c curse_8c move_8c   # one EmuBoundary instance at a time, 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch 8c > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 8c > $D/static.txt
  $D/rows.sh > $D/rows.txt; $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 8c --write
  ```
  The memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills with count
  3; Missiles with count 48; ItemStatCost, MonStats with count 4, or 600 for `curse_8c` so that `MonClassCheck` admits
  the bases 453, 546 and 551; MonStats2, the calc pool, the States and PetType counts, the state sets at `+0xD4` and
  `+0x150`, the overlay count), sets `MONSTATS_GetClassChainPos`'s table and count, `MissileSpeedAtLevel`'s missile
  table and count and the cookie, names the boundaries (`observe`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CAT8C miss_8c  cases=3200 match=3200 bad=0 neg=605 traced=12 undeclared=0 stopped=0
  CAT8C hit_8c   cases=1200 match=1200 bad=0 neg=260 traced=9 undeclared=0 stopped=0
  CAT8C curse_8c cases=2000 match=2000 bad=0 neg=204 traced=29 undeclared=0 stopped=0
  CAT8C move_8c  cases=2400 match=2400 bad=0 neg=1109 traced=6 undeclared=0 stopped=0
  CAT8C static d148_differ=1 entry_words=18 helper_sites=29 pins=68 pins_ok=68 rng_calls=1 rng_mult=3 ro_reads=5 table_entries=18
  ```
  8 800 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 75 or more: `lob_inv` 271, `corpse_any` 100, `base_any` 75, `mode_x` 359; every control equals its deciding
  class on the 18 `CLASS` lines); the site control fails on all 2 376 matched boundary cases (23 `site` lines: function,
  boundary, return address; 892 + 370 + 227 + 887). `static.txt` also finds do 148's and do 149's 101 instructions equal
  but one, scans the batch's bodies and helpers for the RNG functions and the multiplier (one `RNG_Range` call in do
  131, the multiplier three times in do 140, nothing else), prints `0x0063EFA0`'s first switch table and do 130's
  offsets, and computes do 128's frame-sum wrap (`wrap` line). Three development runs came first and are kept in `dev/`
  (`dev/notes.txt`): one case-writer error (two owners written as one unit) and two classes too wide, then the writer's
  tuning for the thin controls.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, start 62's node words from `SkillSummonClass`, do 140's no-room return with the seed stepped
  `1 + 2n` times, do 147's no-owner 1) and of their maps up to their boundary calls with the call site, the nested
  return addresses, the arguments (register arguments where the callee reads them first), the pointed-to blocks and
  packets, the node, frame and argument-slot words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0018 names each claim's boundary). Draws on a
  unit's seed before a boundary: do 131's `RNG_Range(caster, 100)` and do 140's inline steps of the caster's seed. Not
  covered: what any boundary callee does and everything after it, `0x0063EFA0`'s arms other than the default one (Baal's
  among them); when the game runs these functions or with which seed. (fn:sub_005D1F70_SkillDo131OverseerWhip@0x005D1F70,
  fn:sub_005D2C20_SkillDo140BaalTentacle@0x005D2C20, fn:sub_005D1AB0_SkillDo129ImpTeleport@0x005D1AB0)
