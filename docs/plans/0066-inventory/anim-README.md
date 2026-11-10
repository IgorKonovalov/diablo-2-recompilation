# Plan 0066 inventory: anim/README

- **Spec:** [anim/README](../../specs/anim/README.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 13; the *Count* column sums to 13.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 49 | Entry points | A unit's mode changes — (timing § C) | `fn:UNIT_SetMode@0x00624690` | ? | ? | ? | 1 |
| 2 | 51 | Entry points | The unit event lists run, each game frame — (timing § H) | `fn:sub_005414D0_GameRunUnitEvents@0x005414D0` | ? | ? | ? | 1 |
| 3 | 79 | The ADR-0014 boundary | The catalogue's reschedules, its speed writers (Charge, Leap Attack), … — taken as given where logged; the rest an uncompared … | `fn:sub_00553DC0_RescheduleAt@0x00553DC0` | ? | ? | ? | 1 |
| 4 | 80 | The ADR-0014 boundary | Everything else: the record, the start frame, the schedule, … — where or compares it (the timing and movement sections … | run:2026-10-27-anim | ? | ? | ? | 1 |
| 5 | 89 | A. The event kinds | frame event (kind 0) — the do's and the hit's (skills, combat), none of … | `fn:sub_00580460_PlrModeSkillFrame@0x00580460` | ? | ? | ? | 1 |
| 6 | 90 | A. The event kinds | mode end (kind 1) — the next start's, PlayerModeAllowed's, the AI's | `fn:sub_00581020_PlayerModeEnd@0x00581020` | ? | ? | ? | 1 |
| 7 | 101 | B. Chaining (ADR-0014) | The animation adds no seed of its own. An object's start draw chains on the … | – | ? | ? | ? | 1 |
| 8 | 107 | B. Chaining (ADR-0014) | The object start draw and the | `fn:sub_0057CB00_GetHitRoll@0x0057CB00` | ? | ? | ? | 1 |
| 9 | 113 | C. Branches | Two clocks: scheduled modes (players' actions, get-hit, block, death; monsters' non-mv A1–S2, | – | ? | ? | ? | 1 |
| 10 | 117 | C. Branches | Unit types: players and monsters through the rate and the record; objects from their Objects … | – | ? | ? | ? | 1 |
| 11 | 129 | Worked example | See timing § Worked example (a cast's length, its do frame and its breakpoint) and | – | ? | ? | ? | 1 |
| 12 | 134 | Reimplementation notes | A scheduled mode does not follow a rate change. Its events stay where its start … | – | ? | ? | ? | 1 |
| 13 | 159 | Open questions | … at 29 of 30 and the player knockbacks at none new, and their statements stay | – | ? | ? | ? | 1 |
