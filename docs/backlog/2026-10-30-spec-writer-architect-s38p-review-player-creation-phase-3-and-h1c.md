---
from: spec-writer
to: architect
date: 2026-10-30
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../specs/player/creation.md
  - ../specs/hirelings/README.md#h-the-mercenary-from-a-save-d2s_readmercheader-merc_create
resolution: ""
---

Review request: `lane/s38p`, plan 0038 Phase 3 for player/creation (S3a, S3b, H1a, H1c, H6g and the h6gs static
read with its check and audit) and the H1c re-tags of hirelings (rows 3, 30, 33), save/d2s (row 126, § D's name
bullet, D3b's legacy reader) and items/uniques-sets (row 21). Counts (gate reader): player/creation C 85 → 121, I 49 →
39; hirelings C 137 → 141; save/d2s C 240 → 244; uniques-sets C 100 → 101; no `[L]` change. The J2 wording entry is
closed (step 0, the signed cut `T(L + 1) − T(L)`, the unsigned need, all `[I]`). For the reviewer: (1) the split of
rows 3/30 into the loss and corpse-creation `[C]` (four deaths, shares below `0x100000`) and the h6gs field
correspondence `[C]`, with the killer-type skip, the share above `0x100000` and the pickup's run `[I]`; (2) F2's
column-0 clamp kept `[I]` beside S3b's raise of the cell read (scoped to the class-7 d-none ruling); (3) row 1 as two
Entry points rows; (4) save/d2s D3b's new `[C]` summary of the legacy reader from save/0001 § H1c, which the H1c ledger
counts under no row (the layout statements stay in formats/d2s); (5) the wiki rewrites on characters and saves. Not
blocking. Plan log entry dated 2026-10-30; ledger row added (tokens and wall unknown, 0).
