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
- **2026-10-17 — Phase 0 landed (archivist, `lane/p43a`), review requested.** Gate survey `economy`
  (`tools/economy_survey.py`, sections `items`, `types`, `stats`, `affixes`, `npc`, `hireling`, `skills`, `books`;
  baseline `tools/gate/baselines/economy.txt`); every count in the sections below is a key of its `SURVEY` line.
  - [Weapons § Economy](../tables/Weapons.md#economy-plan-0043-phase-0) (the shared table of `cost`, `gamble cost`,
    `durability`, `nodurability`, `durwarning`, `qntwarning`, `stackable`, `minstack`/`maxstack`/`spawnstack`,
    `multibuy`, `quest` with offsets and per-file ranges), [Armor § Economy](../tables/Armor.md#economy-plan-0043-phase-0),
    [Misc § Economy](../tables/Misc.md#economy-plan-0043-phase-0).
  - [ItemTypes § Repair and throwing columns](../tables/ItemTypes.md#repair-and-throwing-columns-plan-0043-phase-0):
    `Repair` (32 types), `Throwable`, `Reload`, `ReEquip`, `AutoStack`, `Shoots`, `Quiver`, `CostFormula`, with the
    item bases' own type against `nodurability`.
  - [ItemStatCost § Price](../tables/ItemStatCost.md#price-plan-0043-phase-0) (`Divide`/`Multiply`/`Add`, 190 priced
    rows, cross-checked with `prop_survey.py`'s stat use); [MagicPrefix § Price](../tables/MagicPrefix.md#price-plan-0043-phase-0)
    (with MagicSuffix, AutoMagic, and the uncompiled QualityItems and RareSuffix price cells),
    [UniqueItems § Price](../tables/UniqueItems.md#price-plan-0043-phase-0), [SetItems § Price](../tables/SetItems.md#price-plan-0043-phase-0);
    [Npc § Multipliers](../tables/Npc.md#multipliers-plan-0043-phase-0) (every row);
    [Hireling § Costs](../tables/Hireling.md#costs-plan-0043-phase-0); [Skills § Charge cost columns](../tables/Skills.md#charge-cost-columns-plan-0043-phase-0).
  - **New table: [Books](../tables/Books.md)** (`BaseCost`, `CostPerCharge`, the tome and scroll codes and skills): a
    price table the plan did not name, found by a header scan of every `.txt` for cost, price, gold, repair and charge
    columns (the only other hits are MonStats' `El*Dur` and QualityItems' `Dur%`, not prices). New `books` layout in
    `tools/excel_layouts.py` (3 × 9 cells, 0 mismatches); `excel_layout` baseline regenerated: tables 66 → 67,
    cells 850 401 → 850 428, `books_cells` 27, `books_bad` 0, nothing else moved.

  Confidence: layouts and counts `[C]` (diff and survey); meanings `[L]` (the price, repair and wear code is named
  only), except the creation-side readers already anchored (`stackable`/stack bounds and `durability` `[I]` from
  items/0006, `ItemHasDurability` `[C]` from items/0004, the hire price `[C]` from hirelings/0001, the Npc scaling
  `[I]` from items/0009, `Throwable` `[I]` from items/0001 and 0005). Surprises, for Phase 1:
  (a) every item-side price input is present on every base except where it is 0 by design (`cost` 0 on gold, the ear
  and five quest items; `gamble cost` 0 on the throwing potions and the nine quest weapons), but 5 armors
  (`pac`..`paf`, `nef`) have `cost` above `gamble cost`; (b) the 13 `nodurability` weapons whose own type has
  `Repair` (12 crossbows, `7cr`), and the bows/`tpot` with no `Repair` type: the repair test's type read decides
  them; (c) MagicPrefix `divide` is 0 on the 21 priced rows (all-resistance prefixes are the only affixes with a
  price term), so the affix term must guard a 0 divisor or skip; (d) QualityItems and RarePrefix/RareSuffix price
  cells have no field, so a superior or rare price term, if any, is code; (e) ItemStatCost stats with no price term
  that a used property reaches (27, 28, 151, 155, 268), and `ValShift` 8 on three priced saved stats (raw or
  shifted value?); (f) UniqueItems `cost mult` 3 on 81 expansion rows against 5 elsewhere, SetItems `cost add` by
  the set's version (2500 classic, 5000 expansion); (g) Skills `cost mult` is 256 + 128·tier of `reqlevel`, and 13
  rows break the `cost add` tier pattern; every skill a `charged` property names (112) has a cost; (h) Npc: the Act V
  rows' `sell mult` 2048 and quest B 512 compose to the same 922/1024 as Acts I–IV with quest A; (i) Books
  `BaseCost` equals the tomes' Misc `cost`, and `CostPerCharge` is a fifth of it, not the scroll's `cost`;
  (j) resurrection has no column in 1.14d (constants in code, hirelings/0001). Gate green (fast tier;
  `--full=economy,excel_layout`).
- **2026-10-17 — Phase 0 reviewed (architect, `lane/p43a`): accept with fixes**, applied on the lane (`main` `8f8c0bc`
  was already merged; nothing to merge). Re-runs: `gate.py` fast tier green (0 errors, 120 warnings, none on a file
  of this phase) and `--full=economy,excel_layout` green (both surveys equal to their baselines); the `excel_layout`
  baseline diff adds only `tables` +1, `records` +3, `cells` +27 and `books_cells`/`books_bad`. `economy_survey.py`
  has no test (survey only, like `stats_survey.py`). Spot-checks of every section against `economy_survey.py <section>`
  (QualityItems and the ItemTypes `Equiv` closure also recomputed from the `.txt` apart from the survey): the 17 Npc rows (multipliers, quest flags,
  `max buy`), the three Books rows and the tome/scroll Misc `cost`, the 60 Hireling groups (`Gold`, `Exp/Lvl`, the
  Act III split), the 21 all-resistance prefixes (records 316..336, the tier counts 10/3/4/2/2 and the three
  illustrated `add`s), the five armors with `cost` above `gamble cost`, the Misc `cost` 0 and stack rows, the 13
  Skills `cost add` exceptions (6 + 4 + 2 + 1), the 13 `nodurability` weapons with a `Repair` type, and the
  QualityItems cells. All match. Tags: data counts `[C]`, the readers already anchored `[I]`/`[C]` with their
  findings, unread meanings `[L]` (table docs, allowed). Fixes:
  - Hireling § Costs: the resurrection bullet was `[L]`, but hirelings/0001 § 10 states the price as `[I]` with
    addresses (`MERC_ResurrectCost` 0x006637B0, `min(50000, (L²/2)·15)`, unsigned compare). Now the missing column
    is `[C]` (header and layout) and the constants are `[I]`, anchored to § 10.
  - Npc § Multipliers: the composed bullet now quotes items/0009's whole scaling rule (the `(v / 1024) · m` form for
    `v ≥ 0x10000`), not only `v · m / 1024`.
  - Skills § Charge cost columns: "13 rows carry the value of the tier below" was wrong for *Find Potion* (tier
    above); now 1 above and 12 below.
  - MagicPrefix § Price, QualityItems: the example ("*improved damage* 3 / 250 and 5 / 350 for its two rows") is
    replaced by the pattern the cells show: one-modifier rows 2/100, 3/250, 2/200; every two-modifier row 5/350.
  - ItemTypes § Repair and throwing columns: point 3's question has no effect on stock data (below), stated.

  Rulings on the six points:
  1. **Books: accepted in Phase 0.** It holds item price columns the plan's *What* covers ("the columns the economy
     code is expected to read") and was found by a scan the plan would have asked for. The doc follows the table
     template and its layout is in the gate; a separate request would only add a hop.
  2. **Books widths: accepted as `[I]` by stride**, with the open question. Phase 1 settles them when it names a reader
     of `+0x004`/`+0x010`/`+0x014` (follow-up below).
  3. **Repair by own type: accepted, and it doesn't matter on stock data.** Recomputed at the review from
     `itemtypes.txt`: walking `Equiv1`/`Equiv2` to the root gives the same 270 weapons, 202 armors and 0 misc, with no
     item differing. Phase 1 still names which one the code reads, for the spec. The archivist adds the closure
     counts as survey keys at the next `economy` touch (not blocking).
  4. **Npc composition `[I]`: accepted.** Both inputs are `[I]` (items/0009 § 9) or `[C]` data, and the bullet says it
     is derived, not observed. Fixed to quote the whole rule.
  5. **Resurrect constants: not `[L]`, raised to `[I]`** (fix above). The Phase 1b verdict line is `[L]` only as
     the lead's own tag; the finding's § 10 states the code read with addresses.
  6. **Surprises in the plan log: accepted** (plan 0041 review rule). Because the archivist filed no Phase 1 request,
     the reverser follow-up below points at (a)–(j) and adds the review's questions.

  Done when: each named section lists its columns with offsets and ranges (met; Books too); the `SURVEY` line matches
  the docs (met; one count is a review recomputation, flagged as not yet a key); meanings `[L]` unless anchored (met,
  except the resurrection line, now fixed); gate green (met). Phase 1/1b may start (static lane B's queue).
