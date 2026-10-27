---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../findings/save/0001-d2s-io.md#plan-0038-lanerlg-the-legacy-and-version-92-readers-static-2026-10-27
  - ../../plans/0038-inferred-claims-sweep.md
  - 2026-10-27-archivist-reverser-d2s-legacy-and-v92-readers-static-reading.md
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (4): D2S_ReadSave sends 0..91, so 0..70 fail the header's version test with 1; the header's left/right skills are applied by the caller after the skills section when non-zero; the per-version base-adjustment constants added; the ItemStatCost table doc linked. Ruling 3 kept: the legacy rows stay shortfalls. Plan 0038 log."
---

Review `lane/rlg` (reverser, static, no harness, no emulation): the archivist's legacy and version-92 readers entry
(closed), written in [save/0001 § Plan 0038 lane/rlg](../../findings/save/0001-d2s-io.md#plan-0038-lanerlg-the-legacy-and-version-92-readers-static-2026-10-27)
with a short note in save/0002 § 1, 17 new `re/symbols.csv` rows (all I) and `tools/rlg_static.py` (its output
`workspace/logs/rlg/static.txt`, manifest `rlg-manifest.sha256`, `RLG_STATIC hits=73 functions=42`).

To check:
1. (a) the legacy layout: section order, the header table, the codes, the swallowed failures after the skills, the
   version-71 record forms (`static.txt` § v71record, § header).
2. Ruling 3: the reading finds no legacy version refused, so hirelings 3, 30, 33, player-creation 1 and
   items-uniques-sets 21 stay shortfalls (b) and wait for a builder (archivist entry
   [2026-10-27-reverser-archivist-d2s-legacy-layouts-for-a-builder](../2026-10-27-reverser-archivist-d2s-legacy-layouts-for-a-builder.md)); no row is
   proposed to move.
3. (b) and (c): the classification of the 73 compares (5 not version tests, 29 met by 92..96 with a version-dependent
   result, 39 not), and the claim that 93..95 differ from 96 in three places only.
4. (d) the mask width ⌈`0x029`/8⌉ and (e) the ear's realm bit and the `+0x20` write condition, both now in save/0001.
5. The one `[C]` the section cites is H1a's existing `v91` return; its attribution to the `+0x20` length test is
   argued by elimination and left `[I]`.
