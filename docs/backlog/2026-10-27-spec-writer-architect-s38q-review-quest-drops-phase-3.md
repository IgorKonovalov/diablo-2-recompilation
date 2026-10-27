---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../specs/items/quest-drops.md
  - ../specs/objects/README.md
  - ../wiki/items-other-paths.md
resolution: ""
---

Review request: plan 0038 Phase 3, the **items/quest-drops** cluster and the **objects § L follow-up**, on
`lane/s38q` (from `main` `fd841611`). items/quest-drops {C 86, I 86, L 2} → **{C 159, I 76, L 2}**, `updated:`
2026-10-27; objects and items/economy counts unchanged (cells re-tagged inside). Wiki: items-other-paths refreshed
(`based_on` 2026-10-27), objects and economy text refreshed. Entries closed: H6d ((a)–(g)), H4a (quest-drops 48), H6e1,
H6e2 (the quest-drops parts, the wiki sentence and the objects follow-up); the S2c entry annotated ((b), (c) done;
(a), (d)–(g) open for cube, vendors and sockets-runewords). Counts entry:
[2026-10-27-spec-writer-architect-s38q-quest-drops-counts-for-the-research-map](2026-10-27-spec-writer-architect-s38q-quest-drops-counts-for-the-research-map.md).

Suggested spot-checks (statement → batch section):
- § E, E1b and its step notes (H6e2 and its follow-up: `heart4` 8, `eye4c` 5, `brain4c` 7 piles first, then the part,
  then `ObjectChestDrop`; the held-part refusal `[I]`);
- B6a and B7 (H6d qd 11: the Rogue Scout and the Hydra, the owner's record, the unresolved killer at `TC_DropByIndex`;
  the `exp`-state lines `[I]`);
- D6 (H6d qd 27: bounds 1 500 / 3 000, 2 178, one pile, no draw with bit 0 set; the pile split `[I]`);
- F0 (H6e1 qd 44 and its review fix: the leg 61 → 66 identified, the economy2 `cap` 10 of 12 unidentified;
  `ItemCanRepair`'s ethereal refusal `[I]`);
- § G (H4a qd 48: four more classes in expansion Nightmare, five of 25 met, Hell for Andariel only).

Points for the reviewer:
1. **Beyond the inventory rows (rule 8).** § Entry points' operate row names the slots the H6e2 operates logged (33,
   12, 28, 39–41, 57–59) `[C]`, from the finding's `[C]` chest and object bullets; the altar, Malus and orifice slots
   stay `[I]`. § E's `g34`/`xyz` row is raised from H6e1's given-items `[C]` (Meshif and Alkor, 20 calls) though H6e2's
   ledger counts that row a shortfall: H6e2 did not run it, H6e1 did.
2. **Rule 2 inline tags.** F1–F3's server refusal lines get an inline `[I]`: H6e1 found every refusal was the client's,
   so `NPC_MenuAction`'s own refusal paths never ran. F3's header "all of F3" is scoped "but the refusal". The same is
   done for C1's player source, random base and free cell, C2's durability write and drop-when-full, F2's quality 9
   and F5's `clvl` halves.
3. **The quality-7 cause** is split by entry: `[C]` for `j34` and `mss` (items/0004 us 13) and for `tr2` and `g34`
   (H6e1 ruling (b), `xyz` separating `unique` from `quest`); `[I]` for `ass`, `bks` and `bbb` (H6e2's After). The
   created-at-7 observation itself is `[C]` for all seven.
4. **S2c's (c)** (add Baal's death to the non-item draws) is applied as H6d corrected it: Baal's death draws the quest
   seed for its gold piles, which are items, so it is listed next to the five non-item functions, not among them.
5. **qd 20 and the "five classes"**: the "Exactly five classes" paragraph was already `[C]`; the "No quest TC" bullet
   is raised on the same data check plus the owner-played Countess and Cow King kills (no B6 test).
6. **D7** is split: the call-graph walk `[C]` (qd 28, with its refinement on the engine entries), "so their drops are
   their TCs" `[I]` (no Diablo kill). F4's Ancients and Nihlathak line stays `[I]` per the H6e1 review, citing D7.
7. **items/economy F7** carries H6e1's qualifier (the leg repaired) inside its `[C]`; wiki/economy follows.
