---
from: reverser
to: architect
date: 2026-11-16
status: done
context: []
resolution: "Tier B check 2026-11-16: accept with fixes (4); merged into main. Phase 2 stays open: MP27, MP32, 0058b partied await the owner (another lane or named out)."
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Tier B check of plan 0065 Phase 2 (`lane/n65i`), a partial batch: the run record `run:2026-11-15-sweep8-two-clients`
([multiplayer/experiments](../../findings/multiplayer/experiments.md#run2026-11-15-sweep8-two-clients)), multiplayer/0001 § 7,
player/0002 § 13 (§ 12 at the lane), stats/0002 § 11, the plan log entries, `tools/mp_check.py` (one fix, the `rooms` null act). Please check:
(1) the counts against `workspace/logs/n65i/check-run.txt` and `manifest.sha256` (77 lines, base `workspace/logs/`);
(2) that the `pk` absence is tagged `[I]` for want of a control in that session (rule 4); (3) the unreached list and its reasons;
(4) the decision for the owner: whether the remaining cases (MP16/0058a, 0058b, MP18, MP27, MP32) get a second Phase 2 lane
with the driver fixes named in the plan log's resume note, or are named out of this plan.

**Part 2 (2026-11-16, `lane/n65i`, same branch).** The same record now carries a *Part 2* block (experiments.md, before
*Hygiene*), multiplayer/0001 § 7 (MP18, 0058a), player/0002 § 4's Phase 2 notes (the `pk2` control, 0058a, 0058b not reached).
Please also check: (5) manifest now 137 lines, `workspace/logs/n65i/manifest.sha256`, counts in `check-run.txt` (part 2 block);
(6) MP18 tagged `[C]` as a shortfall (no `0x28` with the trade open, control with one insert) and the Phase 1 ruling e
reading ("no `PKT 0x28` makes it a shortfall"); (7) 0058a: 54 kills, n = 1 in 31, bound pairs 1 inside and 5 outside (thin near
the bound: the plan's `5600 < d2 <= 6400` band has 1 pair); (8) the `pk` item now has a control (`pk2`: monster `XK0` x 2, still no
player `XK0`), kept `[I]` because the code between the entry and 0x0057E990 was not traced; (9) still not reached with reasons: 0058b
partied (the host never died in four sessions; the hostile-joiner dev run gave only the not-partied form), MP27 (the Docks
waypoint is at (5159, 5049) but the pilot cannot path to it), MP32 (no `GP0`; `pile.py` clicked 12 dead monsters' cells, no gold
seen; `two-gold.gdb` has no `KILL` line). Owner decision: whether MP27 (needs a path planner or one owner-played walk to the waypoint)
and MP32 (needs gold drops: a place with many gold-dropping monsters, or owner play) are worth a further lane, or named out.
