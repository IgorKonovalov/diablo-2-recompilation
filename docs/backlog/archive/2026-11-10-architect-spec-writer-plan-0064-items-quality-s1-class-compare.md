---
from: architect
to: spec-writer
date: 2026-11-10
status: done
context:
  - ../../plans/done/0064-clean-room-test.md
  - ../../plans/0064-cleanroom/S2.md
resolution: "Done 2026-11-10 (lane n64w, plan 0064 P4): [items/quality § B](../../specs/items/quality.md#b-the-itemratio-row--itemratio_select) S1 now says (1) the Class byte is the playerclass row index, 0 ama .. 6 ass, the Expansion marker taking none [C] (PlayerClass § Row identity), the numbering of the unit's class word [I] (data/0006 § 2.2); (2) Class is a u8, so a blank (0xFF) is not < 7 and gives cls 0, and 'signed, bounds-checked' belongs to rec.type, not Class: [I] for the reading (fn:ITEMS_IsClassSpecific@0x00629F70, items/0002 § 2, which gives the field as u8 with blank 0xFF), [C] for the outcome (the model with this test reproduces the logged row of all 1607 S2a rolls, items/0002 quality 13). The Inputs row names the index space too. No new finding was needed: the stored values are only 0-6 and 0xFF (a failed code lookup also stores -1 at the field width, data/0004), so the u8 width and the logged rows decide the compare for every value the game can hold. The table-doc contradiction (ItemTypes Row identity vs blank 0xFF) is the archivist's entry plan-0064-itemtypes-blank-class-vs-row-identity."
---

Plan 0064 S2 row 12, disputed, settled by a fresh clean-room reader (2026-11-10): it needed two guesses, so the row is a spec defect. items/quality § B step S1 says 'cls ← 1 if ItemTypes[rec.type].Class < 7 else 0 ; signed type, bounds-checked, else 0'. No sentence says whether the Class compare is unsigned (0xFF blank → false) or signed (-1 → true unless the bounds check returns first), and none says the Class byte is the playerclass row index (ama = 0). State both, with the finding's anchor (fn:ITEMS_IsClassSpecific@0x00629F70).
