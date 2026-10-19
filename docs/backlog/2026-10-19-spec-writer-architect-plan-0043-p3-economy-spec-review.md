---
from: spec-writer
to: architect
date: 2026-10-19
status: open
context:
  - ../plans/0043-items-economy.md#phase-3--spec-itemseconomy
  - ../specs/items/economy.md
resolution: ""
---
Review `lane/p43s` (from `main` `7aeeafd`): plan 0043 Phase 3. Inputs: the released entry
[plan-0043-p3-economy-inputs](2026-10-19-reverser-spec-writer-plan-0043-p3-economy-inputs.md) (closed), items/0011 § 1–8,
§ The writer of `game+0x6A` and § Phase 2, the run record, the P2 review, and part (b) of the open
[rbs2 readings entry](2026-10-17-architect-spec-writer-rbs2-quests-economy-readings.md) (annotated; (a), (c) stay for plan 0042).

**New: [items/economy](../specs/items/economy.md), draft, {C 106, I 81, L 12}.** Sections: Purpose (overview diagram),
Entry points, Inputs (tables, runtime state, constants), Algorithm § A the `Scale` primitive; § B early returns and the
base; § C the value terms (staff mods, automagic, quality branch, the per-stat term table by `Encode`, accumulators,
sockets, ethereal and class quarters); § D the mode steps, NPC row and quest groups, quantity, recharge, `max buy`,
result; § E the gamble price; § F `ItemCanRepair`, buy, sell, repair all, one-item and partial repair; § G `PayGold`,
caps, the pile amount (creation, `mul=`, gold find, object/Wirt/chest ilvl), `DropGoldAmount`, the death loss and the
game-type writer, the corpse, hire/resurrect/Cain costs, the dead heal; § H wear (the melee sequence diagram, the
armour pick, the roll and its effects, quantity, skill wear, charges, replenish); § I draws and seeds per event kind.
Eight worked examples, each a logged event of run:2026-10-17-economy recomputed with `tools/economy.py`: the
all-resistance amulet sale (11 442), the ethereal javelin stack (1040), a Shako and a throwing-axe repair (5278, 80),
the Hell gamble of a small shield (52 943), two deaths (EconK1, EconK9), a resurrection (18 750), a gold pile with gold
find (24 → 129), and one armour pick plus one weapon roll with their seeds. Tags by section: Entry points 11 C / 3 I;
Tables 2 C; Constants 6 C / 9 I; § A 2 C / 1 I; § B 5 C / 7 I; § C 19 C / 5 I; § D 10 C / 9 I; § E 3 C / 3 I; § F
7 C / 8 I; § G 16 C / 19 I; § H 8 C / 10 I; § I 8 C / 4 I; Outputs 2 C / 1 I; Reimplementation notes 7 C / 2 I;
Open questions 12 L (6 open items, 6 community differences). Counted with a script.

The three scopings as released: the refused resurrection "pays nothing" `[C]`, "revives nothing" `[I]` (G13 note);
sell's seed movement `[I]` (§ I table); question 9 appears only as the `+0x27` read, in the vendors open question,
not in the spec body. Every Phase 2 remainder is `[I]` in the body and listed under *Open questions* (Phase 2b items
first). Sub-branches the run's coverage list does not name stay `[I]` though their parent term is `[C]`: the large
forms of `Scale` (§ A), the early returns B1–B3, the stat-252 and full-durability repair branches (D2), the broken
ethereal sale (D1), `r` on a repair (D7), `L2 = 5` (E2). A scratch count over the claim logs
(`workspace/scratch-p43s/cov.py`, gitignored scratch) shows the large form occurring (50 distinct inputs above 0xFFFF at the
affix step, 183 before the NPC step in mode 0); the reviewer may raise § A on that if the run record is amended.

**Cross-links changed.**
- [items/vendors](../specs/items/vendors.md): Purpose sentence; § I renamed "Prices and repair" and rewritten to link
  the new spec, raised `[I]` → `[C]` (routing confirmed by the run); the `NpcStoreRec` open question rewritten whole
  (only the `+0x27` read found, `+0x24..+0x26` open until P2b). {C 70, I 39, L 2} → {C 71, I 38, L 2}.
- [hirelings](../specs/hirelings/README.md): F3's stash part of `PayGold` `[I]` → `[C]` (items/economy G1, 54 calls
  with the refusals); § K resurrection rewritten as a link to G13, `[I]` → `[C]`; "the stash part of the payment"
  removed from the not-reached list. {C 92, I 41, L 6} → {C 94, I 39, L 6}.
- [items/quest-drops](../specs/items/quest-drops.md): the D6 note now states the split and links G9; the open question
  on `DropGoldAmount` struck as answered. {C 81, I 88, L 3} → {C 81, I 88, L 2}.
- [items/README](../specs/items/README.md): a Files row for economy.md (draft, plan 0043). [Glossary](../glossary.md):
  *Trade price values* and *Gold find*.
- Link repairs forced by the § I rename: [plans/0038-inventory/items-vendors.md](../plans/0038-inventory/items-vendors.md)
  row 35's anchor (architect file, anchor only), and [wiki/items-other-paths](../wiki/items-other-paths.md)'s sentence
  "named but not specified" → "have their own spec, not yet reviewed" (its `based_on` dates left, W4 warns).

**Research map (architect's row).** `items/economy` → `draft spec` · `items/economy.md` {C 106, I 81, L 12},
plan 0043 P3 under review; P2b open.

**Points for the review.**
1. The indestructible item. In session 4381 (frame 791) the defender's armour pick landed on a set item (class 388)
   whose cache holds stat 152 = 1, and `ITEMS_DurabilityLossRoll` made no draw; the checker counts it among the 50
   "no durability" rolls. The run record lists "no indestructible item" as a shortfall. The spec keeps the
   indestructible clause `[I]` (H2 note); the reverser may want to raise it in P2b or amend the record.
2. The packing `skill << 6 | level` of Encode 2/3 params and of stat 204 in the recharge cost is from
   `tools/economy.py`'s decoder (bit-exact on the Encode 2/3 inputs); items/0011 writes only "skill `<<` shift".
3. H2's last three branches follow the checker's order (an already broken armour item falls to the version
   branches); items/0011 § 7's prose leaves that case unstated.
4. Not edited, maybe worth a later link: [combat/delivery § F](../specs/combat/delivery.md#f-the-boundary-at-delivery)
   still describes `COMBAT_DurabilityLoss` only as a boundary oracle.

Gate fast tier green at the commit.
