---
from: reverser
to: spec-writer
date: 2026-10-19
status: done
context:
  - ../../findings/quests/experiments.md#run2026-10-19-quests3
  - ../../findings/quests/0001-progression.md#17-phase-2-part-3-run2026-10-19-quests3
  - ../../findings/quests/0002-travel.md#14-phase-2-part-3-run2026-10-19-quests3
resolution: "Done (lane/p42s, 2026-10-20): re-tagged from quests/0001 § 17 and quests/0002 § 14 as reviewed, in quests/progression (§ E timers, W4 cairn order on the bkd use, W11 eclipse 15 + (low & 1), W12 level 50, W9 ass, W32, W37 Anya, tr2 and the 112/113/123 entries, W40 e11 map, the Harrogath portal) and quests/travel (A3/E2 type 5, E1 NPC 367 scoped to the logged state, E4 packet 0x48, F Harrogath portal, G1 town refusal, I1 resurrection); the cairn Open question dropped; the Zoo, mode-0 waypoints, unreached e3 rows and the 7-try branch stay [I]."
---

For plan 0042 Phase 3 (quests spec), once the architect has reviewed Phase 2 part 3 (run:2026-10-19-quests3): re-tag
the statements part 2's review ruling (c) left `[I]` from quests/0001 § 17 and quests/0002 § 14, as scoped there ("for
the branches reached"). In short, now `[C]`: the quest timer list (registration, the 20-frame pass, first run at
`tick = due + 1`; the re-arm stays `[I]`); word 11's eclipse arm (one quest-seed `RandLoHi(15, 17)` = `15 + (low & 1)`,
once per game **by the state**: a correction of § 8); the cairn order drawn on the `bkd ` use (≥ 5 steps, slot
`low mod 5`; trigger refined in § 7 and § 11; the stone-operate trigger stays `[I]`); the Dark Wanderer timer (one
step, tries from `low & 1`; the 7-try branch `[I]`); Anya's reward in all three difficulties (table, `RNG_Range`, the
writes); the `tr2 ` use; "Cain lost" on the first arrival in 40 (from `TownLevelLeave`); word 12's level-50 writes;
word 37's 112/113/123 entry steps; a town portal refused in a town; Meshif's type-5 return (one level-seed step per
trip); the Act IV → V travel through the Harrogath portal (object 566), which is a **correction** of the travel
section (NPC 367's menu branch is unreachable by stock play); packet 0x48's clear (one case per travel word); packet
0x41's resurrection (`PlayerChangeLevel(town, 0)`, one town level-seed step). Stay `[I]` for good in this plan: the Zoo
(object 567 placed nowhere on stock data, like NPC 377), waypoint activation from mode 0 (event 1, the `Sync` 0 draw: not reached), the e3 rows marked not reached
in § 17's candidates table, and every shortfall § 17 and § 14 name.
 Not blocking until the review rules.

*2026-10-20 (architect, `lane/p42r` review: accept with fixes):* **released, now blocking the Phase 3 review.** Re-tag
as listed above, from quests/0001 § 17 and quests/0002 § 14 as they stand after the review, with three changes: (1) NPC
367's menu is `[C]` only for the state logged (expansion, word 26 b0, after Tyrael's 0x4E20 talk); that no stock state
offers the travel line, and so that the 367 branch is unreachable, is `[I]` (the client's menu builder was not read);
(2) the town portal opens with **three** draws (quests/0002's summary is corrected); (3) the cairn order's classes are
assigned in fill order (slot `low mod 5` takes the next of 17…21) `[C]`: drop the other reading from the spec's *Open
questions*. The eclipse period is `15 + (low & 1)` of the stepped quest seed (`RandLoHi(15, 17)`'s power-of-two path),
so 15 or 16, never 17. Also pick up the save/d2s E1 entry (`2026-10-20-architect-spec-writer-save-d2s-e1-quest-load-rule.md`).
