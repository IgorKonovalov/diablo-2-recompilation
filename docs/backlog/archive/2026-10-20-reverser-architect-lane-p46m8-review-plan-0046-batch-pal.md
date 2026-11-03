---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0011-paladin.md
  - ../../findings/skills/experiments.md
  - ../../plans/done/0046-skills-function-catalogue.md
resolution: "Reviewed 2026-10-20 (architect, lane/p46m8 at d8c384b): accept with fixes, 6 (overclaim 4, omission 2); aura boundary's ECX/EDX are arguments ([C]); thin claims admitted; stats/0002 § 7 [C] narrowed to the run's count; do 81's roll stays [I]; next batch bar. Plan 0046 log."
---

Not blocking. Please review plan 0046 Phase 1 batch `pal` (`lane/p46m8`): the paladin start functions 29, 31, 35,
36, 37 and do functions 64–67, 73, 79–82 and 150, 15 entries (tier A: start 36, do 65, do 66)
([skills/0011](../../findings/skills/0011-paladin.md), run:2026-10-20-cat-emu-pal in
[experiments](../../findings/skills/experiments.md)).

- **Run:** three families, 4 950 cases, 0 mismatches, 0 undeclared reads, 0 stopped; all 15 entries emulated; site
  control 2 615 of 2 615 (21 function/boundary/return-address triples); every negative control fails (five per family,
  each family with one failing 134 or more). `workspace/logs/skills-cat-pal/manifest.sha256` `12c8d5c0…` (23 files),
  `check.txt` `989e5367…`, `static.txt` `5fd43532…` (40 pins, the table entries, the read-only tables, the calc count's
  scan in every operand form, every call of each helper), `rows.txt` `dc96db87…`, tool `c1630af4…`; `repro.txt`
  `daf042cc…`: the same tool revision regenerates 9a–9d's, `sor`'s, `ama`'s and `nec`'s case, memory and expectation
  files and reproduces their `check.txt` and `static.txt` byte for byte. `EmuBoundary.java` unchanged.
- **Conventions:** `nec`'s. Only `g_pDataTables` (and the cookie) is set in the spec. Nested boundaries: the aura
  boundary inside `0x0056B740` compares its return into each of do 65, 66, 81, 82 at the stack slot (and `static`
  lists its four calls, one per function); do 79's `0x0056E2F0` inside `0x005D02B0` compares `0x005D03CC` at its slot;
  start 37's two-deep `InvQuery`/`MeleeInv` rely on single call sites (`0x0056E510` once in start 37, `0x00622870` once
  in `0x0056E510`), both listed in `static.txt`.
- **Things to check:** (1) **the aura boundary** is `AURA_ApplyToTarget`, reached by `0x0056B740`'s indirect `call
  [ebp+8]`, with `ECX` = the 16-byte context and `EDX` = the caster; both are register arguments of the fastcall callee
  (not callee-saved values), the context and block compared by content: admissible under ADR-0021 (a)/(c)?;
  (2) **thin claims**: do 67 ends at its first call after the used-skill test (`0x006633B0`, the animation data), and
  start 29, do 150 and start 31 with a target at `InMeleeRange`; Phase 3 keeps everything after them `[I]`;
  (3) **the weak controls** (`len5` 44, `as0` 27, `reach0` 23, `qhf_tgt` 29, `hp_nomin` 20, `align_any` 7,
  `base100` 34, `v67_floor` 33), each with its deciding class in § 2; (4) **corrections** carried as dated notes into
  skills/0003 § 5 (rows 98, 102, 117 kept in step) and stats/0002 §§ 4 and 7; the § 7 one ("once per hit" is once
  per run of do 66) is a reading, `[I]`, on a `[C]` bullet from a run: does it need its own check?
- **Surprises:** start 36 reads no skill record; start 35 (Vengeance) has no range test before its hit test; do 65's
  `aurastat` values are gated by mana like its `passivestat`s, and `aurastate` 0 is skipped while `auratargetstate` 0 is
  admitted; do 73 and do 80 refuse missile class 0 (`jle`); do 80 does not set bit 6; do 81's per-unit callback rolls a
  20 % state 107 on each unit's own seed by an inline LCG step; `0x005CF8C0` tests one byte read before its loop.
- **Class-3 self-hit (skills/0010):** nothing in the batch tests the caster's class or calls `0x005C2FF0`; Sacrifice's
  own self-hit (do 64) builds a packet of the same shape without `+0x04 |= 4` (§ 6, `[I]`).
- Tags: 25 `[C]`, 12 `[I]`, 4 `[L]` bullets; 29 symbols added (`I`, evidence 0011).
