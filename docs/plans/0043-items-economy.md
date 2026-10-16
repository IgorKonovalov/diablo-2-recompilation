# 0043 — Item economy: prices, repair, gold and durability wear

> **Status:** approved (owner, 2026-10-16; unattended); [ADR-0017](../adrs/0017-scope-quests-travel-economy.md) accepted 2026-10-16
> **Created:** 2026-10-16
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0017-scope-quests-travel-economy

## TL;DR

**Question:** what does an item cost to buy, sell, gamble and repair, and how is that computed from its base, its
quality, its affixes and stats, the NPC and the difficulty; what do hiring and resurrecting cost; how much gold drops
from a monster, an object or a quest event, and what does a player lose on death; and how do items lose durability,
quantity and charges in use, and get them back? When it is done:
- the price, cost and durability columns of the item and NPC tables are documented;
- `docs/findings/items/0011-economy.md` names the price function and its per-stat terms, repair, the hire and
  resurrect costs, the gold amounts and caps, and the wear events;
- `tools/economy.py` reproduces prices, repair costs and gold amounts as one-shot functions, and wear events per event;
- `docs/specs/items/economy.md` is drafted and reviewed.

## Context

- Scope comes from ADR-0017 (accepted 2026-10-16). Research map: a new row `items/economy` in the **Game rules (ADR-0017)** band,
  added when this plan starts.
- **Named, not specified:** [items/vendors § I](../specs/items/vendors.md) (`sub_0062FDC0_ItemTradePrice`,
  `sub_00656900_NpcGetByClass`, `sub_00578050_NpcRepair`, `sub_0062FE60_RepairCost` (L)); hirelings (the hire and
  resurrect costs, `sub_00576D90_PayGold`); [items/quest-drops](../specs/items/quest-drops.md) open question:
  `sub_0055A090_DropGoldAmount` and Baal's, Wirt's (`sub_00594630_A1Q4_WirtGold`) and the quest chests' gold;
  [items/tc](../specs/items/tc.md) (the gold `mul=` and gold find, `sub_005589A0_DropGoldFind`);
  `sub_00559300_DropGoldPile`, `sub_0055B030_DropGold`, `OBJINIT_GoldPiles` (C); combat/0001 (`COMBAT_DurabilityLoss`,
  `ITEMS_DurabilityLossRoll`); repairs by quest and cube (`sub_005761C0_ItemRepairAll`, `sub_0055F900_ItemRepairBroken`);
  `sub_00625E00_ItemMaxDurability` (I), `sub_00629930_ItemHasDurability` (C).
- **Plan 0038** files vendors row 35 (prices and repair) as d-sim; this plan is where it goes.
- **Tooling:** `tools/vendors.py` and the `d2pilot.py npc` action (plan 0031) open stores and gamble windows; the item
  chain (`tools/items_chain.py`) gives the items' stats a price reads.
- Leads: search for and register price and repair formula documentation, gold-drop and death-penalty pages.

## Phases

### Phase 0 — Price, cost and durability columns
- **Owner skill:** archivist
- **What:** document the columns the economy code is expected to read.
- **Outputs:** [Weapons](../tables/Weapons.md), [Armor](../tables/Armor.md), [Misc](../tables/Misc.md) § Economy (the
  cost, gamble cost, durability, quantity, stack and repair columns); [ItemStatCost](../tables/ItemStatCost.md) § Price
  (the per-stat price columns); [MagicPrefix](../tables/MagicPrefix.md), [MagicSuffix](../tables/MagicSuffix.md),
  [UniqueItems](../tables/UniqueItems.md), [SetItems](../tables/SetItems.md) § Price (the cost multiply and add
  columns); [Npc](../tables/Npc.md) § Multipliers (buy, sell, repair, the quest multipliers, max buy);
  [ItemTypes](../tables/ItemTypes.md) § Repair and throwing columns; [Hireling](../tables/Hireling.md) § Costs;
  [Skills](../tables/Skills.md) § Charge cost columns if any row uses them; `tools/economy_survey.py` (gate survey
  `economy`).
- **Done when:** each named section lists its columns with offsets and ranges; the survey's `SURVEY` line matches the
  docs; meanings stay `[L]` unless a finding anchors them; the gate is green.

### Phase 1 — Read prices, costs, gold and wear
- **Owner skill:** reverser
- **What:** read the price function and everything it calls, repair, the hire and resurrect costs, the gold paths,
  and the wear and refill events.
- **Outputs:** `docs/findings/items/0011-economy.md`; `re/symbols.csv` rows (subsystem `items/economy`).
- **Done when:** the finding states, each with addresses and `[I]` or better:
  - **prices:** `ItemTradePrice` per mode (buy, sell, gamble, repair), the base cost, quality and affix terms, the
    per-stat terms, sockets and their contents, charges, durability and quantity, the NPC and quest multipliers, the
    difficulty, the clamps, rounding and widths; the client copy told apart;
  - **repair:** `NpcRepair`, `RepairCost`, repair all, the quest and cube repairs, what is restored (durability,
    quantity, charges);
  - **costs:** hiring and resurrecting a mercenary (with the plan 0033 tables), and any other gold sink;
  - **gold:** the gold pile amount (the TC entry, `ilvl`, the difficulty, gold find), `DropGoldAmount` and its draws,
    Baal's, Wirt's and the quest chests' gold, the object gold piles, the gold caps of the inventory and the stash per
    level, and the player's death loss (amount, corpse, hardcore);
  - **wear:** the durability-loss chance on attack and on being hit, which item loses it, ethereal and indestructible
    items, a broken item; quantity loss for thrown weapons and ammunition; charges used; the self-repair and replenish
    stats' ticks; each with its draws and seeds;
  - for each event kind, the inputs, outputs and the chaining reading;
  - **the boundary recommendation** for Phase 2. The architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch and register price, repair, gold and durability documentation; compare blind.
- **Outputs:** `docs/sources.md` entries; verdicts in the finding's *Leads used*.
- **Done when:** each compared claim carries one verdict; every `contradicted` claim reachable on stock data is a
  required case of Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven; **1 slot**, given in the prompt)
- **What:** write `tools/economy.py` (model and `check`), `tools/gdb/economy.gdb` and its handler, and steps files that
  price store and inventory items, repair, hire, and fight for wear; log a run.
- **Evidence:** prices, costs and gold amounts are one-shot functions (ADR-0004, the item's stats as logged inputs or
  chained to the item chain); wear and ticks are per-event (ADR-0014 as ADR-0017 applies it).
- **Done when:** `run:YYYY-MM-DD-economy` reproduces with **0 mismatches** over at least:
  - 3 000 price evaluations: buy, sell and gamble, every item quality, in all three difficulties, with and without the
    quest multipliers, including socketed items, charged items, damaged items and stacks;
  - 150 repair costs and repairs (NPC, repair all, and a quest repair);
  - 20 hires and 10 resurrections;
  - 400 gold amounts from monsters (all three difficulties, with and without gold find), 30 from objects, and Wirt's
    gold;
  - 20 death losses (softcore), with the corpse's gold;
  - 300 durability-loss events and 100 quantity-loss events, each with at least 20 chained pairs; 50 self-repair or
    replenish ticks;
  - the Phase 1b cases.

  Rare branches (an indestructible item, a broken item, Baal's gold, the stash cap) may fall short, named in the record;
  they stay `[I]`.

### Phase 3 — Spec: items/economy
- **Owner skill:** spec-writer
- **What:** write `docs/specs/items/economy.md`; replace the named-only text of items/vendors § I, hirelings and
  items/quest-drops' gold question with links.
- **Done when:** the spec follows the template; every statement is tagged; the price function is pseudocode with its
  arithmetic and a table of its per-stat terms; gold and wear as pseudocode with their draws; worked examples from the
  run. The architect's review passes.

## Open questions

- **Two clients.** Trading between players and shared gold in a party stay `[I]` here; plan 0044 (two clients, ADR-0008
  accepted 2026-10-16) can stage them.
- **Stat inputs.** A price that reads a stat through the aggregation uses plan 0041's model if it has landed, and a
  value oracle otherwise.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-16 — Drafted (architect, `lane/plans39`).** Status `proposed`; gated on ADR-0017.
- **2026-10-16 — Approved (owner, via the main session).** Plans 0039–0044 approved to run unattended, like 0027–0038. ADR-0017 accepted the same day.
