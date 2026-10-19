---
from: spec-writer
to: architect
date: 2026-10-19
status: open
context:
  - ../plans/0043-items-economy.md#implementation-log
  - ../specs/items/economy.md
  - ../wiki/economy.md
resolution: ""
---

Review `lane/p43t` (from `main` `cf617f0`): plan 0043's last spec-writer pass, the re-tag of the reviewed
[items/economy](../specs/items/economy.md) from Phase 2b and the economy wiki page. **Plan 0043 can close at this
review** (the P2b review's *Close* note). Inputs: the released entry
[plan-0043-p2b-economy-inputs](2026-10-19-reverser-spec-writer-plan-0043-p2b-economy-inputs.md) as corrected,
[items/0011 § Phase 2b](../findings/items/0011-economy.md#phase-2b-runtime-results-run2026-10-19-economy2), the
[run record](../findings/items/experiments.md#run2026-10-19-economy2) and the P2b review's rulings 1–5; the wiki entry
[plan-0043-economy-wiki](2026-10-19-architect-spec-writer-plan-0043-economy-wiki.md). Both entries closed.

**items/economy: {C 109, I 80, L 12} → {C 125, I 83, L 12}** (counted with a script; `updated:` stays 2026-10-19).
By section: Entry points 11/3 → 13/3 (rows for the quest services' repair and Wirt's body); § C 19/5 → 20/5 (C4
crafted `[C]`, 55 inputs, tool-built items scoped; the no-record unique stays `[I]`); § D 10/9 → 11/8 (D2 Hell repair
`[C]`, 25 inputs); § E 3/3 → 4/2 (E2 `L2 = 5` `[C]`, 125 prices at clvl 3); § F 7/8 → 13/12; § G 16/19 → 18/20; § I
8/4 → 10/4; Reimplementation notes 7/2 → 8/2. The rulings as applied:
- **Quest repair (ruling 1):** F7 notes: socket and personalize repair `[C]` (one case each), the imbue's call a no-op
  `[C]` (unidentified, identified after at 0x0057A103), "no quest script repairs" `[I]` (the scan, no second source).
- **Wirt's gold (ruling 2):** new G8a pseudocode `[C]` (the `RandLoHi(questSeed, 10, 20)` count, one
  `DropItemAtUnit` pile per event 7, +2 game seed each) and a G8 note; the Levels column `[I]`, unseparated; the
  `DropItemAtUnit` floor of 1 kept `[I]` (not met). § I gains a Wirt row `[C]`.
- **Question 9 (ruling 3):** a `[C]` § F note scoped to the windows played (listed as in items/0011 item 7); the
  reader elsewhere is under *Open questions*.
- **Sell (ruling 4):** F4 pseudocode lists the eight tests in order, all evaluated, each clearing the copy flag; an
  inline marker says tests 2, 5, 7 `[C]`, the rest `[I]`. Notes: the 11 decisions `[C]`; the five unreached tests and
  `ItemIsCarry1Unique`'s reading `[I]`. § I's sell row split: copied / refused by the three reached tests `[C]`, the
  five others `[I]`. A reimplementation note: the copy draws even when no page takes it `[C]`.
- **Single cases (ruling 5):** F6 pseudocode `[C]` with the 4 calls in a note; the entry refusals and the partial
  branch's tests other than `gold > 0` scoped `[I]` (inline marker and note); the ethereal server refusal `[I]`. F7:
  durability restoration `[C]` (the services' caps and the broken cap), quantity and charge refills code-read; the
  broken repair's "no draw" `[I]`.
- **Crafted, Hell repair, clvl-3 gamble:** reproduced, as above.
- **Open questions:** the Phase 2b bullet struck (answered, with the sections); a new `[L]` *Remainder of Phase 2b*
  bullet (five refusals, ethereal server refusal, broken repair's draws, the scan's second source, Wirt's column,
  the store record elsewhere). The Phase 2 shortfall list is unchanged (none of it was in P2b). Evidence lists the
  second run.

**Stale text closed (review-fixes rule 7).**
- [items/quest-drops](../specs/items/quest-drops.md) {C 81, I 88, L 2} → {C 84, I 87, L 2}: F0 said all three
  services return the item repaired; now the call order `[I]` and a `[C]` note (socket, personalize repaired; imbue
  not); F1's pseudocode line annotated; Outputs split (identified `[C]` P1 run; repaired for two, not the imbue
  `[C]` P2b run); § E's Wirt gold row `[I]` → `[C]` (run:2026-10-19-economy2) with a G8a link; the *Not attempted*
  list points Wirt's gold to items/economy. Left as is: the event-7 route bullet (the run did not log the dispatch
  path, so I did not strike Wirt from it); the reviewer may judge.
- [items/vendors](../specs/items/vendors.md): the `NpcStoreRec` open question rewritten whole (rerun, no read in the
  windows played, a reader elsewhere open). Tags unchanged {C 71, I 38, L 2}.

**Wiki.** New [economy.md](../wiki/economy.md) ("Prices, repair, gold and wear", `based_on` items/economy
2026-10-19): prices (three values, the steps in order, NPC multipliers and the *sell mult* trap, `max buy`, the floor,
the sale's lower of two and the copy refusals), the gamble price, repair (partial, ethereal, broken, the quest
services), gold (payment, the cost table, caps, pile amount and gold find, object piles, Wirt, Baal, the death loss),
wear (the armour pick, the chances, quantity, replenish), *What is not known yet*, six worked numbers from the spec's
examples 1, 3, 4, 5, 7, 8. Code-read points are said "read from the code". [Index](../wiki/README.md): row 8 (rows
renumbered), a *Why the pages are cut* bullet, the reviewed-spec list and the plan 0043 line.
[items-other-paths](../wiki/items-other-paths.md): "no wiki page covers it yet" → a link; the services paragraph no
longer says all three come back repaired; the vendor-record and Wirt unknowns rescoped.

**Gate:** green (0 errors). **Commits:** `bc8b2ef` (specs), `d5e959f` (wiki), and the closing commit with this entry
and the plan log.

**Research map (architect's row, not edited):** `items/economy` stays `reviewed`, tags {C 125, I 83, L 12}; the
items/quest-drops row's counts move to {C 84, I 87, L 2} if the map carries them.

**Points for the review.** (1) Of § I's rows only the first (the no-draw kinds) gained the second run's anchor, from
the *seeds* line of its `check-run.txt`; the buy and death rows cite the first run only. (2) F7's header stays `[I]` (what `ItemRepairAll` does in full), with the `[C]` parts in notes. (3) The wiki
says "every logged price call in them, 33 901 in all" (26 525 + 7 376 from the two check outputs). Not blocking.
