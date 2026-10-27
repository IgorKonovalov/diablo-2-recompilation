---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../findings/skills/0002-missiles.md#6-the-packet-at-the-hit-missile_builddamage
  - ../../findings/monsters/0003-special-monsters.md#lane-rbd-monpostcreateboss-and-the-h4a-chained-models-2026-10-27
  - ../../findings/drlg/0002-room-build-draws.md#lane-rbd-entry-bit-0x400-on-a-neighbours-walls-2026-10-27
  - ../../findings/monsters/experiments.md#addendum-2026-10-27-lanerbd-the-chained-models-re-checked
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (6). Manifests pass; the H4a, regression and skills re-runs reproduce the kept outputs byte for byte; anchors confirmed by objdump. Four symbols raised to C (rule 14), the dev manifest moved into dev/, the s5b failure linked to H4b's recorded deviation, tail 60's [C] scoped (no tag move), the window rule's limits written in. Rulings: the chaos7 change is legitimate under ADR-0004; the [C] raises stay within the logs; no H4a outcome or total changes. Both spec-writer entries released. See the plan 0038 log."
---

Review request, lane/rbd (static, objdump only; no Ghidra, no harness). Two reverser entries closed. (1) skills/0002 § 6: MISSILE_BuildDamage's bounds and mastery read on the missile, the > 0 tests before the mastery, the inverted-pair swap, all [I]; the Answer bullet carries it; tools/skills.py bd swaps (test_bd_swap both ways); both runs' 33 logs re-checked: 4 118 builds, 0 mismatches, no inverted pair (workspace/logs/skills/rbd/, manifest 3c6bdf04…); whether a missile carries its owner's masteries is an [L] open question (0 of 54 655 MH0 lists hold one). (2) the H4a chained-model mismatches: council = client wall-fade bit 0x400 on a near room ([I] code, [C] the 33 entries); nihl2 = MonPostCreateBoss's mod 22 ([C] for BaseId 526, its case table [I]) plus tail 60's escorts newly chained ([C]); chaos7 = the logger's CM window, the model now applies its own marks outside it. The twelve H4a logs rc 0 with main's tools as the control; the 63 kept logs identical under both (workspace/logs/h4a/check-rbd/, manifest f34f23c5…). Tool changes: drlg.py, collision.py, monspawn.py, monspecial.py, skills.py, test_skills.py, new cb_entry_bits.py. Points to look at: the window rule (mark_window_open from the last RW1/CMR0 vs RW0/PX/CMRX line), and whether the tail-60 raise is a symbol or spec matter. Spec-writer entry filed for special § J and room-tiles 9d.
