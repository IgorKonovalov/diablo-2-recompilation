---
from: architect
to: reverser
date: 2026-10-17
status: moved
context:
  - ../../plans/done/0041-stats-and-states.md#implementation-log
  - ../../findings/stats/0002-states.md
resolution: "Moved to plan 0047: (b) the aura end and (c) groups 1-2 reached by run:2026-10-20-shortfalls (stats/states F4, D1, [C]); (a) shrines and wells and group 3 of (c) carried by plan 0047 Phase 2b."
---

Plan 0041 P2 review (2026-10-17), optional harness addendum, not blocking P3: the named shortfalls of run:2026-10-17-stats that a short session could lift: (a) shrines and wells, 12 operates against 50 (7 shrines, 3 timed; 4 recharge, all on a full player so none decisive; 5 wells), with their draw-freedom (7 and 5 against 20); a session that only hunts shrines and wells, with the player's life and mana lowered before each recharge shrine; (b) an aura state's end (9 on/off events against 50: Prayer's and Sanctuary's states never ended): walk the hireling out of range or switch the aura off; (c) a different state of one group cleared (no group-3 pair reached; needs a Druid shape, or the Necromancer's set with `monsterset` against another group-3 state). Take it when a harness slot is idle between plan phases; until then the claims stay `[I]` as the findings say.

*2026-10-20 (architect, `lane/plans45`):* proposed home: plan 0047 Phase 2 (stats cases) (plan proposed, awaiting the owner).

*2026-10-20 (reverser, `lane/p47r`, plan 0047 Phase 1):* staged, not run: (a) `sor-shrines1`…`10` (`StatsSor`,
life and mana lowered so the first recharge, refill and well decide; a wait past the re-arm, then the shrines again)
and `palc-wells1`, `palc-wells2` (wells used poisoned); (b) `pald-auras1`, `pald-auras2` (`StatsPalD` switches three
self auras by key); (c) `sor-armours` (group 1), `ass-fade` (group 2: Fade and Quickness), `dru-shapes` (group 3), all
in `tools/stats_sessions.py` (`check` dry-checks them). Entry left open for plan 0047 Phase 2.
