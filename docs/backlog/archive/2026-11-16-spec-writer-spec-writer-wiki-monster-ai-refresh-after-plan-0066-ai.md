---
from: spec-writer
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../specs/README.md
resolution: "Refreshed in lane/fuw against monsters/ai README, machinery and catalogue: [wiki/monster-ai](../../wiki/monster-ai.md) states the tick, idle and delay, table, state rows, pre-checks, forced target, hostility test, distances, walkers, override and keep-near at the specs' raised strength, the shared n rule at n ≤ 0, the teleport try's two draws, the second route to states 10 and 11, Scarab under the past-the-first claim, and the catalogue's census (55 / 2 / 73, twenty entries under H1, p lines, callbacks run whole); based_on bumped."
---

Plan 0066 Phase 3, the monsters/ai cluster part 1 (`lane/n66ai`), updated monsters/ai/README and monsters/ai/machinery
on 2026-11-16, so wiki/monster-ai carries W4. What changed for a reader: the tick's pass order, the AI context words,
`Idle(n)`/`Delay(n)` giving the next event at `T + n` (with 68 of 2 573 idles beaten by another queue), the table, its
row kinds and the state rows are confirmed by the logs or two tools; `MonAiInit`, the 10–12 gate, the pre-checks with
`MonAiKeepNear`, the forced target, the hostility test, the distances, the walkers, the override and the helpers' draws
are confirmed under emulation to their first callees; `MonAiDelayEarlier` turns 0 into 1 and keeps a negative `n` (not
`max(n, 1)`); `UModTeleportTry` draws up to twice on the unit's seed; curses are not the only setters of states 10 and 11;
row 20 Scarab now meets the H1 sentence. Refresh the page against the two specs (spec-writer review-fixes 1) and bump
`based_on`; the catalogue's re-tag (part 2) may change the same page, so one refresh after part 2 is enough. Not blocking.

*2026-11-17, spec-writer (plan 0066 Phase 3, monsters/ai part 2, `lane/n66ai2`):* part 2 has landed, so the one refresh
can run now; not done in this lane, by the owner's token budget. Part 2 adds for a reader: the catalogue's rows past the
first boundary (twenty entries under sentence H1, README H1's table now lists them; 55 of the 130 rows outside the tier
with the first boundary compared), each modelled block's logged paths `[C]` on its new `p` line, the row callbacks and
helpers emulated whole (`AiTrapArrowKind`, `AiGenSpawnPickClass`, Diablo's and Baal's pick), and the corrections: one
life reader (`AiLifePct` wraps `UnitLifePct`; rows 4, 8, 15, 122 call it), Diablo's pick with a sum ≤ 0 still scanning,
`AiShadowSkillRoll`'s 0, 1 or 3 draws, Mephisto's pick's first draw only with a find, row 71's eleven stores, `Skill8`
also on `uberbaal`. Refresh the page against all three specs and bump `based_on`.
