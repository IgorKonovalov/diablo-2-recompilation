# Plan 0066 inventory: anim/README

- **Spec:** [anim/README](../../specs/anim/README.md), read at `main` `b5999f5e`.
- **Front matter `I`:** 13; the *Count* column sums to 13.
- Classes, batches and conventions as in [the inventory README](README.md#conventions).

| # | Line | Section | Claim (excerpt) | Anchor | Class | Route or reason | Batch | Count |
|---|---|---|---|---|---|---|---|---|
| 1 | 49 | Entry points | A unit's mode changes — (timing § C) | `fn:UNIT_SetMode@0x00624690` | a-logs | as anim-timing rows 1 and 22 (MSET then the `UNIT_AnimInit` SR over all4) | S6b | 1 |
| 2 | 51 | Entry points | The unit event lists run, each game frame — (timing § H) | `fn:sub_005414D0_GameRunUnitEvents@0x005414D0` | a-logs | as anim-timing row 3 (run:2026-10-30-frame-emu-2 and the EF phase lines) | S6b | 1 |
| 3 | 79 | The ADR-0014 boundary | The catalogue's reschedules, its speed writers (Charge, Leap Attack), … — taken as given where logged; the rest an uncompared … | `fn:sub_00553DC0_RescheduleAt@0x00553DC0` | a-logs | as anim-timing rows 8 and 38 (RSC and CQ lines in the rev-6 logs); part 1's 124 stay named | S6b | 1 |
| 4 | 80 | The ADR-0014 boundary | Everything else: the record, the start frame, the schedule, … — where or compares it (the timing and movement sections … | run:2026-10-27-anim | d-none | a summary whose rows are classified in anim-timing and anim-movement | – | 1 |
| 5 | 89 | A. The event kinds | frame event (kind 0) — the do's and the hit's (skills, combat), none of … | `fn:sub_00580460_PlrModeSkillFrame@0x00580460` | c | a call-graph scan with a second tool from `PlrModeSkillFrame`: no animation draw | S6c | 1 |
| 6 | 90 | A. The event kinds | mode end (kind 1) — the next start's, PlayerModeAllowed's, the AI's | `fn:sub_00581020_PlayerModeEnd@0x00581020` | c | a call-graph scan with a second tool from `PlayerModeEnd` and the monster end functions | S6c | 1 |
| 7 | 101 | B. Chaining (ADR-0014) | The animation adds no seed of its own. An object's start draw chains on the … | – | c | as anim-timing row 121 | S6c | 1 |
| 8 | 107 | B. Chaining (ADR-0014) | The object start draw and the Concentration draw have no chained pair in the run | `fn:sub_0057CB00_GetHitRoll@0x0057CB00` | b | as anim-timing row 123 | H6b | 1 |
| 9 | 113 | C. Branches | Two clocks: scheduled modes (players' actions, get-hit, block, death; monsters' non-mv A1–S2, | – | a-logs | as anim-timing row 13 | S6b | 1 |
| 10 | 117 | C. Branches | Unit types: players and monsters through the rate and the record; objects from their Objects … | – | a-logs | as anim-timing row 23 | S6b | 1 |
| 11 | 129 | Worked example | See timing § Worked example (a cast's length, its do frame and its breakpoint) and | – | d-none | a pointer to the worked examples, classified in anim-timing and anim-movement | – | 1 |
| 12 | 134 | Reimplementation notes | A scheduled mode does not follow a rate change. Its events stay where its start … | – | a-logs | `fire` over all4 (timing J7) and the RSC reschedules as anim-timing row 38 | S6b | 1 |
| 13 | 159 | Open questions | … at 29 of 30 and the player knockbacks at none new, and their statements stay | – | d-none | an open-question bullet; the tag is a reference to the short floors, no claim | – | 1 |

**Totals by class:** a-logs 6, b 1, c 3, d-none 3 (sum 13).
