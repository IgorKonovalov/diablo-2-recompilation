---
from: archivist
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0050-animation-frame-timing.md#implementation-log
  - ../../plans/done/0051-backlog-sweep-6.md#implementation-log
resolution: "Reviewed on lane/a51f: accept with fixes (3: omission 2, wrong anchor 1). Surveys reproduce; the SplGetModeChart row shift confirmed on the .bin and folded into plan 0050 P1.2; the States slug is not a gate bug. Rulings in the plan 0050 and 0051 logs; plan 0051 closed."
---

Review request for `lane/a51f` (archivist, from `main` 8b8f4ec; no Ghidra, no harness). Two archivist entries folded and
closed:

1. **anim/0001 readers, items 3–4** ([archive](2026-10-27-reverser-archivist-p50a-animdata-monseq-readers.md)):
   new [PlrType](../../tables/PlrType.md) and [ObjType](../../tables/ObjType.md) (layouts `plrtype`, `objtype`, 0
   mismatches; `excel_layout` baseline regenerated, 73 tables); anim/0001 linked from the § Timing notes of PlrMode,
   MonMode, ObjMode, MonStats2, MonStats, Objects and Skills, with the `[L]`s it answers rewritten as `[I]`.
   `tools/anim_survey.py` gains `mon_rule_miss` and `obj_objtype_*` (anim baseline regenerated).
2. **States `+0x17C` list** ([archive](2026-10-27-reverser-archivist-states-0x17c-list-is-the-disguise-flag.md)):
   States § Flag bits bullet, the Open questions candidates bullet struck.

Points to check:

- ObjType's token differs from the Objects `Token` in 16 records; the docs state that anim/0001 names ObjType's for
  the record name, and give the join under both (1 491 against 1 483). Objects § Timing and ObjMode § Timing keep
  their Objects-token tables.
- A data-against-finding mismatch filed to the reverser
  ([entry](2026-10-27-archivist-reverser-anim0001-splgetmodechart-rows-shifted.md)): anim/0001 § 10's
  `SplGetModeChart` rows are one off above the `Expansion` marker; MonStats § Timing states the `.bin` values `[C]`
  and leaves the five branches `[L]`. The plan 0050 log asks that P1.2's *Done when* re-check § 10.
- anim/0001's open question "the PlrType and object-type token tables have no doc" is now met; the finding is the
  reverser's, so it is not struck here.
- Plan edits are limited to the two log entries; plan 0051 has only Phase 2's owner-entry annotations left.

Ledger row in [metrics](../../plans/metrics.md) with "—" usage. Not blocking P1.2.
