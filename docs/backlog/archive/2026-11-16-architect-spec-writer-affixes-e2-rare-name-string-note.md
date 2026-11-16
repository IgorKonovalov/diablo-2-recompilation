---
from: architect
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../specs/items/affixes.md#e-the-rare-builder--items_buildrare--items_buildrareaffixes
  - ../../specs/data/strings.md#d-key--index--strtable_getbykey
resolution: "items/affixes E2's step note now points at [data/strings § D](../../specs/data/strings.md#d-key--index--strtable_getbykey) *Rare names* at [C] (C 154, updated 2026-11-16); strings' Open questions keep only the %n join, which the note names; wiki/items' stale open question rewritten (lane/ill1)"
---

Not blocking. items/affixes § E2's step note says "Which string a name id is shown as is not traced in any finding", but data/strings § D's step note "Rare names, a load-time key and a client-side index" (with "The rare name line is RareFormat") traces it: the load stores STRTABLE_GetByKey(name) at record +0x0C and the client shows STRTABLE_GetByIndex of it, [C] by run:2026-10-27-sweep-data-load (data/0003 § H3b). Replace the affixes note with a link to that strings step note and check whether strings' Open questions still carry the gap. Found at the lane/site1 review (tools/tc_anim.py now shows rare names through tools/tbl.py).
