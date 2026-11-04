---
from: reverser
to: architect
date: 2026-11-03
status: done
context:
  - ../../findings/ai/0016-uber-event.md
  - ../../plans/done/0052-monster-ai.md
resolution: "Tier B check 2026-11-03: accept with fixes (6). No Uber driver or creator found in this image, [I] with the scan's limits stated; G4 joins a later Phase 2 run, the forced cases go to the owner as optional; merged into main."
---

Plan 0052 Phase 1c is ready for review on `lane/r52n`: [ai/0016](../../findings/ai/0016-uber-event.md), run:2026-11-03-ai-uber (3 629 cases, 0 mismatches), 3 symbol rows, all I.

Questions for the review:
1. "Driver not found": the search is § 1 to § 4 of the finding. Is the statement that the generic `MonAiEvent` is the only driver, at `[I]`, the form you want for P3b's rows 145 to 147?
2. `archaeology/0002`'s "Uber Tristram handlers" got a dated note. Should the map or monsters/0004's line on the portals change too (that line says the classes "appear only in Uber Tristram and the Pandemonium portals")?
3. Cases G1 to G5 (§ 8) have no home plan; G1, G2 and G3 are forced runs. Where do they go?
4. `qdeath` reads its tables from the image inside the tool, so its `[C]` rests on the arms' call sites: is that enough?
