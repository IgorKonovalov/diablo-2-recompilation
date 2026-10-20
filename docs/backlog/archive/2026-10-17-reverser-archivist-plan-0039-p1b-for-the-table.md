---
from: reverser
to: archivist
date: 2026-10-17
status: done
context:
  - ../../tables/States.md
  - ../../findings/data/0001-excel-loader.md#plan-0039-batch-p1b-2026-10-17
  - ../../tables/Objects.md
  - ../../findings/objects/0001-object-population.md#plan-0039-batch-p1b-2026-10-17
  - ../../formats/d2s.md
resolution: "Done: (a) attred bit 10, immed not compiled, red bits and group s16 in [States](../../tables/States.md) and the layout (excel_layout, stats baselines regenerated); (b) [Objects](../../tables/Objects.md) § Code semantics; (c) [d2s.md](../../formats/d2s.md) header 0x0CF, status bit 1, corpse bytes; (d) version note in Weapons, Armor, Misc."
---

[2026-10-17] from reverser → archivist: plan 0039 P1b, for the table and format docs. (a) [States](../../tables/States.md): the layout gaps are closed by the `states` descriptor (`STATES_Load` 0x00618100): `attred` is flag bit 10, `immed` has no descriptor entry (the compiler ignores it), `rfred`/`rcred`/`rlred` are bits 26/27/28; `group` is written as an s16 at `+0x1E` ([data/0001 § Plan 0039 batch P1b](../../findings/data/0001-excel-loader.md#plan-0039-batch-p1b-2026-10-17)). (b) [Objects](../../tables/Objects.md): `SpawnMax` and `Act` have no reader in the image, `TrapProb` none among the record fetchers ([objects/0001 § P1b](../../findings/objects/0001-object-population.md#plan-0039-batch-p1b-2026-10-17)). (c) [d2s.md](../../formats/d2s.md): the corpse record's first u32 is uninitialised stack and none of its 12 bytes is read on load; header `0x0CF` is one of three host bytes; status bit 1 is set only by the creation screen ([save/0001 § P1b](../../findings/save/0001-d2s-io.md#plan-0039-batch-p1b-2026-10-17)). (d) [Weapons](../../tables/Weapons.md) (and Armor, Misc) `version`: 0 places the row in the classic index map read by the version-`0x47` item reader (361 rows). Not blocking.
