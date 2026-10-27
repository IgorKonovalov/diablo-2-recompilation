---
from: archivist
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0051-backlog-sweep-6.md#implementation-log
  - ../tables/Skills.md
  - ../tables/MonEquip.md
resolution: ""
---

Please review plan 0051 Phase 0b on `lane/p51b`: the seven plan 0046 column-reader entries of 2026-10-21 (8a, 8b, 8c,
`ass`, `bar`, `dru`, `item`) folded into Skills, Missiles, MonStats2, MonStats, States, Levels, PetType, Books, Shrines
and Misc and closed, and the new [MonEquip](../tables/MonEquip.md) table doc (item 16) with its `monequip` layout in
`tools/excel_layouts.py` and the regenerated `excel_layout` baseline. Check against the batch reviews (`lane/p46m9`
to `lane/p46m15`): each reader keeps the finding's tag, with every ADR-0021 boundary named, and the reviews' fixes to
the entries applied (`dru` fix 2, 8c fix 3, `item` fix 3, the `ass` `[I]` readings). The three data questions: two are
answered from the layouts and the data (`bar`'s bit is `InTown`; 8c's bytes are MonStats2 `S3v`/`S4v` variants,
`[I]` by monsters/0004 § 6), one goes to Phase 1b (`dru`'s DataTables `+0x17C` list); details in the
[plan log](../plans/0051-backlog-sweep-6.md#implementation-log). Not blocking.
