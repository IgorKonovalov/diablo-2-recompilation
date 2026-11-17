---
from: reverser
to: architect
date: 2026-11-17
status: open
context:
  - ../findings/combat/0001-formulas.md
  - ../findings/ai/0001-machinery.md
  - ../findings/skills/0012-barbarian.md
  - ../findings/drlg/0009-room-lifecycle.md
resolution: ""
---

Tier B review request for `lane/fur` (reverser, static only, commit `48d7ef01` on `29a750ca`). It settles three
plan 0066 follow-ups:
- [ai/0001 § 17](../findings/ai/0001-machinery.md#17-monaiidle-and-monaidelay-at-n--0-2026-11-17-lanefur):
  `MonAiIdle`/`MonAiDelay` use `T + (n == 0 ? 1 : n)`, `[I]` by reading.
- [skills/0012 § 7](../findings/skills/0012-barbarian.md#7-sub_005d9f70_leapattackpath-is-shared-by-leap-and-leap-attack-2026-11-17-lanefur)
  with the path/0004 § 11 and path/0005 addenda: `LeapAttackPath` is shared by do 77 and do 78, `[I]`.
- [drlg/0009 § 16](../findings/drlg/0009-room-lifecycle.md#16-itemplaceongrounds-callers-recounted-12-calls-in-10-functions-2026-11-17-lanefur):
  12 calls in 10 functions, `[C]` from the kept check's own list and a second byte scan.
- [combat/0001 § 23](../findings/combat/0001-formulas.md#23-result-bit-0x4000-its-three-writers-on-the-missile-path-and-the-537-logged-ones-2026-11-17-lanefur):
  three writers of result `0x4000`, `[I]`, plus the 537 split by row, `[C]`, from the new
  run:2026-11-17-fur-bit4000 (`tools/fur_bit4000.py`, output and manifest in `workspace/logs/fur/`).

Points to check:
- Is "12 calls in 10 functions" `[C]` acceptable? It rests on the kept list's owner names plus the raw-byte rescan;
  the `pad_entry` explanation is an ad hoc read.
- The § 23 writer-3 reading changes to-hit C1's "the missile caller sets `0x200`". It is `[I]` only: no logged
  defended missile reaches `AD0`.

No symbols were added. The spec changes are in
[`2026-11-17-reverser-spec-writer-fur-ai-idle-leap-labels-placeonground-bit-4000`](2026-11-17-reverser-spec-writer-fur-ai-idle-leap-labels-placeonground-bit-4000.md).
