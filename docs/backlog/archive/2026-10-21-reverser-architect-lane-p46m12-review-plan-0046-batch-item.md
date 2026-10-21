---
from: reverser
to: architect
date: 2026-10-21
status: done
context:
  - ../../findings/skills/0015-item.md
  - ../../findings/skills/experiments.md
  - ../../plans/0046-skills-function-catalogue.md
resolution: "Reviewed 2026-10-21: accept with fixes (6: overclaim 1, misread 1, omission 2, wrong anchor 1, stale cross-reference 1); rulings and fixes in plan 0046's log (lane/p46m12 review); archivist and spec-writer entries released."
---

Not blocking. Please review plan 0046 Phase 1 batch 10 `item` (`lane/p46m12`): Unsummon's start 3 and do 4, do 113
(scrolls and books), do 151 (Chain Lightning's `ItemEffect`), and the callers: `ITEMSKILL_Cast` with its `ItemTarget`
helpers 2–4 and its callers `ItemCastAtUnit`/`ItemCastAtXY`, the stat-event handlers 20, 21, 30, the charge path of
`SKILLS_PayCost`, the shrine missiles 19, 21, 22 and the object and quest `MissileCreateAt` sites, with the carried
items ([skills/0015](../../findings/skills/0015-item.md), run:2026-10-21-cat-emu-item in
[experiments](../../findings/skills/experiments.md)).

- **Run:** five families, 12 000 cases, 0 mismatches, 0 undeclared reads, 0 stopped; the four entries and the ten
  callers emulated (the three helpers inside the cast); site control 4 936 of 4 936 (31 function/boundary/return-address triples); every negative control
  fails (five to nine per family, each family with one failing 241 or more). `workspace/logs/skills-cat-item/manifest.sha256`
  `3e974e32…` (118 files, three development runs under `dev/` with `dev/notes.txt`), `check.txt` `22402718…` (with
  the `CLASS` lines: each thin control's deciding class counted by a predicate on the inputs, equal to its failures),
  `static.txt` `55299029…` (74 pins, 12 table entries, the call sites of the cast path, `MissileCreateAt`, the pet
  limit functions, `PayCost`, `UseCharge`), `rows.txt` `a9e0cb25…`, `cg.txt` `42b678eb…`, tool `904fe25e…`;
  `repro.txt` `41e54f5b…`: the same tool revision regenerates 9a–9d's and the seven class batches' case, memory and
  expectation files and reproduces their `check.txt` and `static.txt` byte for byte. `EmuBoundary.java` unchanged.
- **Conventions:** `ass`'s, with three seeds compared in every case (caster, target, shrine object). New observed
  boundaries with their register reads cited in skills/0015 § 2 (`PetRemove`, `0x0055E170`, `0x00562390`,
  `SKILLS_SrvStart`, `SKILLS_SrvDo`, `0x0056E390`, `ItemCastAtUnit`/`AtXY` in the handler family, `UseCharge` with
  `EAX`, `BloodManaPay`; `COLL_PatternTest`, `0x0065A950`, `ItemIndexByCode`, `UnitAddStat` stack only). Nested:
  `ITEMSKILL_Cast` inside its callers (`0x7FEFFFB4`), helpers 2 and 3 inside the cast (direct and nested slots); the
  callers' out words on their frames, the target-slot type word through the `ARG2` dump.
- **Things to check:** (1) **the carried items**: helper 2 is given the cast's caster (`0x005FDB9B`, `[C]`), and which
  unit that is per handler (§ 5, composed `[I]`); helpers 3 and 4 do not draw (run plus `cg.txt`, `[C]`); pets above a
  lowered `petmax` are removed by `sub_00575900_PetLimitRefresh` from `STATE_DefaultRemoveCB` and the skill shrine's
  remove callback (§ 10, `[I]`, static only); (2) **the draws before boundaries**: handlers 20/21/30's chance draws,
  helper 2's two steps, shrines 21/22's count on the shrine's seed; (3) **the inputs set in the spec** (the item and
  Books tables, the item-type equivalence words, the layer shift and mask at their stock-like 6 and 0x3F); (4) **the
  unemulated parts named with the reason**: the quest `MissileCreateAt` sites and `0x0058C8D0` (inside quest
  handlers, argument words pinned), the pet-limit refresh (its level input is `SKILLS_GetSkillLevel`'s bonus sum);
  (5) **corrections** as dated notes in skills/0001 § 10 and *Open questions* and skills/0003 §§ 2, 3, *Leads used*
  and *Open questions* (`ItemCastAt*` take `EDX` the skill; handler 20's `ItemTgtDo` caster; the extra-skeleton lead
  now held); (6) the symbols: 26 added, all `I` as the earlier class batches' function rows.
- **Surprises:** `ITEMSKILL_Cast` reads only the low byte of `ItemTarget`; the item effect flag is 1 only from handler
  20 without `ItemTgtDo` (so `ItemEffect` 36/151 never apply on get-hit, death, level-up or charges); with `ItemTgtDo`
  the struck unit casts on itself and no other unit returns 1 with no cast; do 113 tests stat 70 for books only, and a
  first match with a bad location ends the walk with 0; do 4's `PetRemove` flag is a `push 1` left on the stack across
  `UnitSkillGet18`; the exploding and poison shrines drop 5–9 potions, not 5–10; `SKILLS_PayCost` returns 0 for a skill
  whose `mana` and `lvlmana` are both 0; two item-use entries cast Fire Ball and no stock item selects them.
- Tags: 29 `[C]`, 22 `[I]`, 4 `[L]` bullets; 26 symbols added (`I`, evidence 0015).
