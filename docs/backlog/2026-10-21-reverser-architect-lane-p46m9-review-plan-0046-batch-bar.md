---
from: reverser
to: architect
date: 2026-10-21
status: open
context:
  - ../findings/skills/0012-barbarian.md
  - ../findings/skills/experiments.md
  - ../plans/0046-skills-function-catalogue.md
resolution: ""
---

Not blocking. Please review plan 0046 Phase 1 batch `bar` (`lane/p46m9`): the barbarian start functions 32–34 and
38–41 and do functions 2, 9, 68–72 and 74–78, 19 entries (tier A: start 32, do 2)
([skills/0012](../findings/skills/0012-barbarian.md), run:2026-10-21-cat-emu-bar in
[experiments](../findings/skills/experiments.md)).

- **Run:** four families, 6 800 cases, 0 mismatches, 0 undeclared reads, 0 stopped; all 19 entries emulated; site
  control 2 397 of 2 397 (39 function/boundary/return-address triples); every negative control fails (three to six per
  family, each family with one failing 90 or more). `workspace/logs/skills-cat-bar/manifest.sha256` `737c8b4f…` (28
  files), `check.txt` `13b1a4d2…`, `static.txt` `4808f177…` (45 pins, the table entries, the read-only tables, the calc
  count's scan in every operand form, every call of each nested helper), `rows.txt` `9646927a…`, tool `613471e3…`;
  `repro.txt` `65c7b964…`: the same tool revision regenerates 9a–9d's, `sor`'s, `ama`'s, `nec`'s and `pal`'s case,
  memory and expectation files and reproduces their `check.txt` and `static.txt` byte for byte. `EmuBoundary.java`
  unchanged.
- **Conventions:** `pal`'s. Only `g_pDataTables` (and the cookie) is set in the spec. Nested boundaries (skills/0012
  § 2): eight helper returns compared at their stack slots (do 70 → start 32, start 38 → `0x00571B70` from two sites,
  do 68 → `NovaAtUnit`, do 71 → `0x005D8510` and `0x0056BBC0`, start 40 → `0x005D9A10`, start 41 → `0x00645CA0`, do 74
  → `UnitGetWeapon`); do 70's two-deep reach chain by single call sites (`0x0056E510` once in do 70, `0x00622870` once
  in `0x0056E510`), all listed in `static.txt`.
- **Things to check:** (1) **register arguments at new boundaries**: start 32's `0x0056E520(ECX caster, EDX calc3)`,
  do 78's `0x005DA120`/`0x005DA660` (`EAX` caster) and `0x005D9F70` (`EDI` caster), do 71's `0x0056E2F0(ECX, EDX)`:
  each callee reads the register before writing it (objdump cited in § 3, § 6), compared as pal ruling 1 admits;
  (2) **thin claims**: do 77 ends at `UNIT_CancelEvents` after its node test, do 74 at `UnitGetWeapon`'s inventory
  query, start 39 at `MeleeHitTest`, do 71 with a monster target at `0x0056E2F0` (its curse block never reached);
  (3) **the weak controls** (`town_any` 42, `ovl_lt` 15, `end_nomax` 15, `pt_swap` 36, `sk34` 33, `size2` 41,
  `noscale` 22, `mask_swap` 27, `f200` 23), each with its deciding class in § 2; (4) **corrections** as dated notes in
  skills/0001 § 11, skills/0003 § 5 (the Kick row kept in step) and items/0001's Functions row for
  `sub_005D8780_CorpseFindItem` (its rolls are on the caster's seed, `[I]` from objdump, not the monster's); the
  items/0001 row stays `C` for its role, which rests on its harness logs, not on the seed.
- **Surprises:** do 2's overlay and target-state blocks return 1 **without delivering** when the caster has no queued
  hit on the target; do 9 and do 70 branch on bit 8 of the caster's `+0x38`; do 68 sets bit 6 before its record test
  and admits missile class 0 (unlike do 73/80); Find Potion and Grim Ward's corpse test adds MonStats2 flag 12
  (`soft` by the layout) to Find Item's; start 40 pulls a player's leap point in to `aurarangecalc` (`(x − ux) · range
  / d + ux`, `d` the `(min + 2·max)/2` distance); start 41 aims two steps past the path's target point; do 72's two
  rolls are on the caster's seed. Draws before the boundaries: none.
- Tags: 31 `[C]`, 22 `[I]`, 4 `[L]` bullets; 32 symbols added (`I`, evidence 0012).
