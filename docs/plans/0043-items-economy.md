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

### Phase 2b — Shortfall remainder (added at the Phase 2 review, 2026-10-19)
- **Owner skill:** reverser (harness, **1 slot**)
- **What:** the stock-reachable items of Phase 2's *Done when* that the run missed and that are not rare branches,
  listed in backlog [2026-10-19-architect-reverser-plan-0043-p2b-economy-remainder](../backlog/2026-10-19-architect-reverser-plan-0043-p2b-economy-remainder.md):
  crafted prices, the Hell repair price, the gamble at clvl 3, partial/ethereal/broken repairs, the quest repair (or
  its absence shown), Wirt's gold, question 9 with a control live to the session's end, the two unchanged-seed sales.
- **Done when:** each listed item reproduces with 0 mismatches on the same manifest, or is named again as a shortfall
  with its reason. Phase 3 does not wait for it; the spec is updated when it lands.

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
- **2026-10-17 — Phase 1 and Phase 1b done (reverser, `lane/p43r`, static).** No game run, no slot; Ghidra on the lane's
  copy (`ghidra-p43r`, `-Xmx3G`, own log), objdump for the instruction-level reads; `main` `419929a` merged in. Finding:
  [items/0011](../findings/items/0011-economy.md) (66 `[I]`, 22 `[L]` lead verdicts, 0 `[C]`). 46 symbols added (44
  functions, 2 data; subsystem `items/economy`), no address or name clash with `main` or `lane/p42r`'s committed CSV.
  New tool `tools/economy_scan.py` (call sites, Books readers, draws in the 37 functions read, 4-byte pointer search,
  store-record byte reads); its output is `workspace/logs/economy-scan/economy-scan.out`, sha256 in
  `workspace/logs/economy-scan-manifest.txt` (`SCAN calls … sites=129`, `books calls=10 tablerefs=6`, `draws funcs=37
  hits=5`, `pointers hits=0`, `storerec hits=0`).

  | Done-when item | Answer | Anchor |
  |---|---|---|
  | prices | one function, `ITEMS_TradePriceCore` (modes 0 buy, 1 sell, 2 gamble, 3 repair), three running values `P`/`S`/`R`; base by kind (ear, body part `+8·mlvl`, tome `CostPerCharge·q + cost`, quiver, stack divisor `maxstack`), armour `cost·def/maxac`; identified only: automagic, quality (low −½; magic, rare, crafted affix `multiply/1024 + add`; set and unique `cost mult/1024 + cost add`), per-stat ISC terms (superior, magic, rare, crafted, tempered; `ValShift` first; Encode 1–3 use Skills costs and `S/4096`), staff mods; sockets `cost/2`; ethereal and class items `S/4`; Npc and quest multipliers (`v·m/1024`, large form above `0xFFFF`); quantity; `max buy`; stat 87 via `MulDiv`; floor 1. Gamble price computed from clvl and the three tiers' `cost`/`level` (rings, amulets and version-0 items: `gamble cost`). No difficulty term except `max buy` and the body-part level. Client: same functions, client inputs | 0011 § 1–5 `[I]` |
  | repair | mode 3 (durability fraction, `M − 1` rule with stat 252, recharge cost added after the Npc step); repair-all over the 13 body slots; one item: stack to max, charges refilled, broken cleared, durability max; the partial repair takes all gold; the test reads the item's own type's `Repair` | 0011 § 4–5 `[I]` |
  | costs | `PayGold` gold then stash; resurrect `min(50 000, (L²/2)·15)` with the mercenary's level; hire from hirelings/0001; Cain 100 per unidentified item until quest word 4; a dead heal-for-gold function | 0011 § 6 `[I]` |
  | gold | caps `clvl·10 000` and 2 500 000 (overflow writes 0; give and pickup clip and drop); pile amounts from items/0006 and items/0001; object, Wirt and chest ilvl by creator; `DropGoldAmount` splits; death `min(L,20)%` of gold + stash, single player keeps `500·L` and only carried gold, rest dropped, PvP drops the loss | 0011 § 6 `[I]` |
  | wear | melee only: attacker weapon 4 % (throwing 10 %, classic none) on the attacker's seed; defender armour `RangeB(7)`, `RangeB(W)` over `g_ArmorWearSlots` then 10 %; break at 0 (armour), stack −1 (throwing); ammunition and thrown −1 per use; charges −1 per cast; replenish every `max(125, 2500/r + 1)` frames, durability before quantity | 0011 § 7 `[I]` |
  | event kinds | table with inputs, outputs, draws; only the wear kinds draw (and item creation for gold piles) | 0011 § 8 `[I]` |
  | boundary | below | 0011 § 8 |
  | Phase 0 (a)–(j), review (a)–(f), `NpcStoreRec` | each answered in the finding's table; the store record bytes are read by none of the economy functions, the image-wide reader stays open (P2 question 9) | 0011 § Phase 0 surprises `[I]` |

  **Surprises.** (1) The table divisors (ISC `Divide`, affix `divide`) are never read; the skill-based terms divide
  `S` by 4096. (2) An ethereal item sells for a quarter, a class item for a quarter again. (3) Unique and set items
  get no per-stat terms; superior and tempered items do. (4) The gamble price ignores `gamble cost` for every
  version ≥ 1 item but rings and amulets. (5) The recharge cost is not scaled by `rep mult` or the quest groups.
  (6) A gold add over a cap writes 0, not the cap (`UnitAddGoldStat`); the callers clip first. (7) The sell takes the
  lower of the item's price and its repaired store copy's. (8) `sub_005761C0_ItemRepairAll` repairs one item (name
  kept). (9) A melee weapon reaching durability 0 gets `D = 0` and quantity 0 without `ItemBreak` (open).

  **Phase 1b.** Re-fetched `src:arreat-summit-vendors`, `src:arreat-summit-gambling`,
  `src:arreat-summit-character-basics`, `src:maxroll-d2r-items` ("Durability & Quantity") and `src:d2dfg-blizzard`
  (price columns); no new source (the Arreat Summit death page is gone). 22 verdicts: 10 held, 5 held with
  refinement, 6 **contradicted**, 1 not covered. Contradicted: the armour slot weights, ethereal "25 % less", ethereal
  throwing weapons "always 1 gold", affix `multiply` "4096ths for sell", `gamble cost` as the gamble price (all
  reachable on stock data: P2 required cases, backlog), and Books `BaseCost` as the tome base (equal to the Misc
  `cost` on stock data, no stock case; the spec states it).

  **P2 harness questions** (1 slot; every line also logs the game seed and the acting units' seeds on entry and exit,
  so that each kind that does not draw shows them unchanged over ≥ 20 events, as the 0041 P1 review asked):
  1. *Prices* — break at `ITEMS_TradePriceCore` (`0x0062EFB0`) entry and its four `ret 0x10` exits: mode,
     difficulty, npc class, the quest record words 4, 9, 17, 35, 41 (bits 0, 1), player stats 12 and 87; the item's
     class, quality, `ItemData+0x18` flags, `+0x30` version, `+0x36`, prefixes and suffixes, file index, stats
     70/72/73/252/253, the full-stat cache (list `+0x48`, count `+0x4C`), base stat 31, the socketed children's
     classes; the result. **No draw.** Checker: `tools/economy.py price` from the tables. Boundaries: `P > 0xFFFF`
     (an expensive unique armour), a magic javelin stack (`n = maxstack`, unsigned stat-term division), a damaged
     throwing stack (`S = M·S − R·(M − q)`), ethereal, a class item, a starting item (1), low quality, an
     unidentified magic item, a tome at several `q`, a quiver, an ear, a body part, `max buy` reached, stat 87
     (Gheed's Fortune), a broken ethereal item (1), all-resistance prefixes (`multiply` 1280), a charged item, a
     staff with stat 107, Act V NPCs with both quest groups. ≥ 3 000 calls over modes 0/1/3 in all three difficulties.
  2. *Gamble* — the same breakpoint, mode 2, at clvl 1–5 (`L′ = 5`), ~30 and ≥ 60 (negative `10000 − e − x`),
     rings and amulets, a version-0 item if one exists (none expected). **No draw** in the price; the window build
     draws (`GAMBLE_BuildInv`, plan 0031) and is the existing model's.
  3. *Repair* — `RepairCost` (`0x0062FE60`) result; `NpcRepair` (`0x00578050`) in/out: gold, stash, each item's
     D/M, quantity, charges, broken flag. Cases: one damaged item, repair all, an item with stat 252 at `D < M − 1`
     and at `M − 1`, a charged item with missing charges (recharge term), a throwing stack below max, an ethereal
     item (refused), a crossbow with `nodurability`, the partial repair (gold short; a broken item refused). **No
     draw** reachable within depth 6, except a broken item's repair (`ItemRepairBroken`): include one paid repair of a
     broken item and log the player's and game seeds. ≥ 150, and one quest repair (`sub_005761C0` from Charsi's reward path, items/0010).
  4. *Buy and sell* — `NPC_BuyItem` (`0x00577830`), `NPC_SellItem` (`0x00579510`): the price, the multi-buy count of a
     permanent stack, the sale's store-copy price and the paid minimum, `PlayerGiveGold` overflow drops. **No draw in
     the body**; the store copy's `ItemCopy` reaches `UnitSeedInit` and `UNIT_SetMode` (economy-scan `REACH`): log the
     game seed, the player's, the NPC's and the copy's seeds on entry and exit, and the copy's seed after creation.
  5. *Gold caps* — `UnitAddGoldStat` (`0x0053FF00`), `StashGoldMove` (`0x00564D50`), `GoldPickup` (`0x0055C850`):
     gold and stash before and after, at and near `clvl·10 000` and 2 500 000 (tool-built save with gold set).
     **No draw** except the re-drop's item creation.
  6. *Hire and resurrect* — `HIRE_Hire` price (already C) and `MERC_Resurrect` (`0x00579C00`): mercenary stat 12,
     price, gold/stash. ≥ 20 hires, 10 resurrections; a mercenary of level ≥ 82 for the 50 000 cap. **No draw** in
     the price; the revive (`MercRevive`) reaches drawing code: log the mercenary's and the game seeds.
  7. *Death* — `PLAYER_DeathGoldLoss` (`0x005357D0`) entry/exit: L, gold, stash, `game+0x6A`, killer type and owner;
     stat 175; the `DropGoldAmount` calls (amount, piles); `PLAYER_CorpseCreate`'s corpse gold. Cases: total above and
     below `500·L` (single player), gold < loss. ≥ 20 softcore deaths. **Draws:** one item creation per dropped pile
     (log the game seed around each).
  8. *Gold amounts* — `sub_005589A0_DropGoldFind` in/out (gold, both GF stats), `sub_00559300_DropGoldPile` (ilvl,
     resulting stat 14), Wirt's piles, a quest chest's piles: the item-creation draws (item seed) as items/0006's
     model. ≥ 400 monster piles in three difficulties with and without gold find, ≥ 30 object piles.
  9. *`NpcStoreRec` readers* — a read watchpoint (`rwatch`, 4 bytes) on Charsi's record `+0x24` during a store,
     sell, repair, gamble (Gheed) and hire session: any reader's pc and caller. Closes the plan 0039 Q23 question.
  10. *Weapon and armour wear* — `ITEMS_DurabilityLossRoll` (`0x00559E30`) entry/exit: game `+0x70`, the seed owner
      and its seed before/after, the item's class, chance, D/q before/after; `COMBAT_DurabilityLoss` (`0x0057D3D0`):
      both `RangeB` results and the occupied slots. **Draws:** one LCG step per roll (attacker's seed), `RangeB` ×2 +
      one step (defender's seed). Checker predicts each event and the chained pairs on one seed (≥ 300 events, ≥ 20
      chained pairs). Boundaries: an indestructible item (no draw), armour reaching 0 (broken), a throwing stack at
      D = 1 (quantity −1, D = M), a melee weapon reaching 0 (which code sets broken: open question), no armour worn
      (`W = 0`, no draw), a shield in the right hand; a classic-game throwable (no draw) if a classic character fits the
      slot time (may fall short).
  11. *Quantity and charges* — `sub_0056C310_ItemConsumeOne` (`0x0056C310`) and `sub_0056BEC0_UseCharge`
      (`0x0056BEC0`) in/out: q, D, charges. **No draw** in the bodies (ammunition use reaches `UNIT_SetMode` through
      `HandsRefresh`: log the player's seed). ≥ 100 quantity events (arrows, javelins), charges cast to 0.
  12. *Replenish* — `ITEMEVENT_Replenish` (`0x00562D30`): frame, r, D/q before/after, the requeue frame; ≥ 50 ticks
      for stat 252 and 253 items (`of Self-Repair`, `of Replenishing`, tool-built), one item with both (durability
      only). **No draw** in the body (only `UnitQueueEvent`'s dispatch reaches drawing code).
  13. *Cain* — `NPC_CainIdentify` (`0x00578460`): count, cost, quest word 4 state. **No draw.**

  **Boundary recommendation.** One-shot functions: the price core, the gamble price, the recharge cost, the
  resurrect cost and the death loss (inputs logged as above, ADR-0004); per-event with seeds: the two wear functions
  and the replenish tick; value oracles: the item's full-stat cache as logged (plan 0041's model may replace it), the
  hire price (`HIRELING_RollEntry`, `[C]` in hirelings/0001) and the gold pile amounts (items/0006's model). Slot
  need: **1 slot** (an expansion character with tool-built items and gold for questions 1–13; a classic character
  only for question 10's classic case).

  **Points for the review.** (a) All behaviour `[I]`; the draw table rests on a one-level scan (callees not scanned;
  item creation is the only drawing callee named). (b) The `S/4096` asymmetry and the never-read divisors.
  (c) The ethereal `S/4` against the lead's 25 %. (d) The game-type-3 reading of the single-player death rule rests on
  monsters/0001's logged value, not on the writer of `game+0x6A`. (e) The store-record reader question moved to a P2
  watchpoint instead of an image-wide static scan. (f) The melee weapon at durability 0 (open).
- **2026-10-17 — Phase 1 and Phase 1b reviewed (architect, `lane/p43r`): accept with fixes**, applied on the lane
  (`main` `419929a` already merged; nothing new to merge). Re-runs: `economy_scan.py` over the pinned image gives
  `economy-scan.out` with the manifest's sha256 (`85dd1d44…`), byte for byte. Spot-checks with objdump (16): the
  ethereal `sar 2` on `S` (0x0062F88E, `S` identified by the mode-1 return at 0x0062FD75) and the class-item quarter
  (0x0062F99C); the stat terms' `and 0xfff; sar 0xc` on the first stack argument only (`&S`, from the call at
  0x0062F80C–0x0062F81A) in the Encode 1–3 branches and `0x3ff`/`sar 10` everywhere else, with no `+0x0C` read; the
  set/unique term (0x0062F8A4–0x0062F96B) and the low-quality halving; the quantity and `max buy` steps and the three
  returns (0x0062FC59–0x0062FD8B); `PLAYER_GoldCap` (`imul 0x2710`) and `PLAYER_StashGoldCap` (`0x2625A0`);
  `UnitAddGoldStat`'s zero-on-overflow; `PLAYER_DeathGoldLoss` whole (the `0x51EB851F` /100, `imul 0x1F4`, the
  `game+0x6A == 3` branch, the PvP test, stat 175); `PlayerDropGold`; `g_ArmorWearSlots` bytes (1,3)(3,5)(4,4)(5,4)(8,2)(9,2)(10,2),
  count 7 at `0x00732BC8`, and `COMBAT_DurabilityLoss` (the first `RangeB` takes `edx` = 7 left by the slot loop);
  `ITEMS_DurabilityLossRoll` (4/10, the classic return, the LCG, the break and stack branches); `ItemCanRepair` (own
  type through `ITEMS_GetBaseType` → `ITEMTYPES_GetRecord` `+0x08`, no `Equiv` walk); `MERC_ResurrectCost`; the
  gamble `rin `/`amu ` compares; Cain's `imul 0x64`; the sell's lower-of-two (0x005798D2); `ITEMEVENT_Replenish`;
  the Books readers (the 10 `BOOKS_GetRecord` sites, the iterator `0x006374A0` used only by 0x005C2540 for `+0x18`/`+0x1C`,
  and `0x00637490` the unload). All match. Tags: 66 `[I]`, 22 `[L]` (all under *Leads used*, 22 verdicts), 0 `[C]`;
  symbols: 46 rows, all `[I]`, subsystem `items/economy`, no address or name duplicate in the CSV, every row of the
  finding's table present; every `src:` id in `docs/sources.md`.

  Fixes:
  - **Draws reached through callees (overclaim).** A new `reach` section of `economy_scan.py` (not in `all`, so the
    lane's hash stands; output `workspace/logs/economy-scan/economy-reach.out`, sha256 `9310600a…` in the manifest)
    walks direct callees to depth 6. The price core and terms, gamble, recharge, `RepairCost`, `NpcRepair`,
    `ItemRepairAll`, `ItemRefillCharges`, Cain, `PayGold`, `UnitAddGoldStat`, `UseCharge` and `MERC_ResurrectCost`
    reach no drawing code within that depth (`ItemRepairBroken` does, from itself, so a broken item's repair is
    P2's: question 3 logs the seeds for it); buy and sell (the store copy's `ItemCopy` → `UnitSeedInit`, and `UNIT_SetMode`), resurrect
    (`MercRevive`), ammunition use (`HandsRefresh` → `UNIT_SetMode`) and the replenish tick (`UnitQueueEvent`'s
    dispatch) do. items/0011 § 8 and its table now say "none in the body; reachable: P2 decides" for those kinds, and
    P2 questions 4, 6, 11 and 12 name the extra seeds to log. Question 4's "the store copy's `ItemCopy` makes none"
    is removed.
  - **"The table divisors are never read" (overclaim):** scoped to the price path (§ 1–§ 4); no image-wide reader scan
    was made.
  - **The death drop (omission):** § 6 now states what `PlayerDropGold` does (nothing when the amount is above carried
    gold or its cap; else at most 2 000 000 000 in at most 32 piles, each taken from carried gold) and that every
    stat write in the death path goes through the cap test, so the PvP `gold = loss` write is 0 above `L × 10 000`
    and that loss then drops nothing.
  - **The melee weapon at 0 (omission):** the open question now carries the `HandsRefresh` → 0x00580030 reading
    (`ItemBreak` only for a magic-or-better stackable or throwable weapon at quantity 0 without stat 125; a plain melee
    weapon untouched), so P2 knows which flag to log.
  - **Verdict count (miscount):** "21 verdicts" in this log → 22 (10 + 5 + 6 + 1).

  Rulings:
  - (a) **The draw table may state "none" before P2 only where the callee walk is clean** (fix above). It stays `[I]`
    either way; P2's seed logging on entry and exit decides each kind, and the kinds with reachable draws must log
    the extra seeds named in their questions.
  - (b) **Verified.** `S/4096` occurs only in the skill-based branches (Encode 1–3, the staff-mod term, `S` alone);
    `P` and `R` are always over 1024. No read of ItemStatCost `+0x0C` or affix `+0x84` in the price functions; scoped.
  - (c) **Verified: a quarter**, so the lead's "25 % less" is contradicted (the item sells for 25 % of the non-ethereal
    value, 75 % less). A P2 required case.
  - (d) **Accepted as `[I]` with the open question.** The rule's arithmetic is read; only the meaning of value 3 rests
    on monsters/0001's logged runs. Follow-up filed to find the writer of `game+0x6A` (not blocking).
  - (e) **Accepted.** A byte-read scan cannot be exhaustive for a record pointer held in any register, and a read
    watchpoint over a full store, repair, gamble and hire session answers the question with a `run:`. Question 9 is
    required in P2, not a "may fall short" item. The plan 0039 Q23 entry is closed as moved to P2 question 9.
  - (f) **Stays open**, with the review's reading added; P2 question 10's boundary case answers it.
  - Also checked as asked: the gold caps; the death loss `min(L,20)%` and the type-3 floor `500·L` (the loss is
    lowered to `T − 500·L`, floored at 0, then capped at carried gold); the armour pick `RangeB(7)` then `RangeB(W)`
    over the weights 3/5/4/4/2/2/2; the Books readers; the repair test's own type. All as the finding states.

  Done when: Phase 1's list is met (prices per mode with every term, rounding and width; repair; costs; gold; wear;
  the event-kind table; the boundary recommendation; the client copy told apart); Phase 1b's (one verdict per claim;
  the five stock-reachable contradicted claims are P2 required cases in the backlog). Pre-existing fix on this lane:
  `re/symbols.csv`'s `CRT_alldiv` signature `__int64` → `longlong` (Ghidra's built-in name, which
  `ImportSymbols.java`'s `FunctionSignatureParser` accepts; no other 64-bit signature is in the CSV). Research map:
  the `items/economy` row added under *Game rules (ADR-0017)*. Backlog: the review request, the architect → reverser
  Phase 1 inputs entry (answered) and the plan 0039 Q23 entry (moved to P2 question 9) closed; filed architect →
  reverser `game-type-writer`. **Phase 2 may start** (harness lane H1, 1 slot).
- **2026-10-17 — Phase 2 started; rotation checkpoint (reverser, `lane/p43h`, harness slot 1).** Not done; no review
  request yet. Record: [run:2026-10-17-economy](../findings/items/experiments.md#run2026-10-17-economy) (status in
  progress); finding section [items/0011 § Phase 2](../findings/items/0011-economy.md#phase-2-runtime-results-run2026-10-17-economy).
  Tools: logger `tools/gdb/economy.py` (+ `economy.gdb`, `economy-hire.gdb`), checker `tools/economy.py` (test
  `tools/test_economy.py`), driver `tools/economy_sessions.py` (`act`, `tour`, `die`), `d2s.py` key `"dur"`,
  `d2pilot.py` NPC rows `cain2`/`cain5`/`cain6`/`tyrael` and the `identify`/`resurrect` confirmations (untested),
  recipes `econ*.json` (pinned in `test_d2s.py` without hashes).

  **Done so far (0 mismatches):** 968 distinct price inputs over 6 949 calls (mode 0 683, 1 159, 2 70, 3 56), Normal
  only, 14 NPCs; 60 repair-all sums; 71 replenish ticks (gaps 501 and 834 frames seen); 10 gold amounts at creation and
  10 gold-find scalings (gold find 0); seeds unchanged for price, repair, `PayGold`, `UnitAddGoldStat`, give-gold and
  replenish; buy and sell move the game seed by 2 steps per created item. Required cases 2–5 reproduced (ethereal
  `S/4`, the ethereal throwing stack 1 040, the all-resistance `S` over 1024, the computed gamble price); case 1 (slot
  weights) not yet.

  **Resume note.** Saves built in `workspace/scratch-p43h/saves/` (rebuild with `d2s.py build … <recipe>`; base
  `workspace/samples/d2s-owner/smpsor-l50.d2s`, Barbarians on `workspace/samples/d2s/smpbar.d2s`): EconA (damaged
  equipment, ethereal, stacks, tome, quiver, staff mod, replenish items), EconB (set, socketed sword, rare and
  unidentified rings, crossbow, class shield, Gheed's Fortune for `r ≠ 0`, Darksight Helm charges), EconC (EconA with
  quest words 4, 9, 17, 35, 41 bits 0–1 cleared: quest-off multipliers, and Cain's paid identify), EconD (40 one-cell
  rings, amulets, charms: about 40 sale prices per NPC), EconDL3 / EconDL75 (EconD at clvl 3 and 75, for the gamble
  `L′ = 5` and high-level cases), EconK1..K10 (deaths: level, gold and stash vary, 5 hit points, a dead mercenary of
  level 10..99 for resurrection, Act IV start: Tyrael), EconW / EconT (Barbarian wear and throwing), EconG / EconN
  (Nova with and without gold find). Left, by question:
  1–2. Nightmare and Hell tours (EconD and EconB), a quest-off tour (EconC), gamble refresh runs with EconDL3 and
  EconDL75 (`4:jamella:gamble:grid` repeated). A tour of 20 stops takes ~50 min (walks dominate): prefer Acts IV, V
  and II. 3. Repair cases: a single-item repair (`repair` token then a click), the partial repair (gold short), an
  ethereal item refused, a broken item (needs an armour broken by wear) and the quest repair. 4. Sales and purchases
  with the new `ra2` cross-check (≥ 20 each). 5. Pickup of an overflow pile and the stash move (UI not scripted).
  6. Hires: `economy-hire.gdb`, `d2pilot.py npc <log> kashya hire --repeat 20 --buy 1`; resurrections: EconK saves,
  `npc tyrael resurrect` (menu line unverified). 7. Deaths: `economy_sessions.py die --save EconK<n>.d2s --wp 4,2`
  (Hell) — not yet run. 8. Gold: longer Nova farms (EconG, EconN; the 4322 farm left the level after 45 s). 9. The
  store-record watch: session 4311 logged no read of Charsi's `+0x24` in a full Act I visit, but had no control; the
  control watch `SWC` (`+0x00`) is now in the logger: rerun an Act I visit and require `SWC` hits. 10. Wear: the
  Barbarian cannot use the pilot's Teleport hops (4321: 0 melee hits); drive the melee with walking clicks
  (`explore --any-level --walk --melee`, as `player_sessions.py levelup` does) or let a Nova sorceress stand in a
  melee pack without Energy Shield. 11–13. Quantity (EconT, Throw on the right button), charges, Cain (EconC).
  Gotchas: `--save` is `action=append` (one per flag); store cells are skipped when empty by a brightness test (26);
  Escape after a sale may need a second press; `d2pilot.py npc` stops when a trade window is still open.
- **2026-10-19 — Phase 2 done (reverser, `lane/p43h`, harness slot 1).** Record:
  [run:2026-10-17-economy](../findings/items/experiments.md#run2026-10-17-economy) (status done; 33 claim logs and 7
  development logs, sha256 in `workspace/logs/economy-run-manifest.txt`); finding
  [items/0011 § Phase 2](../findings/items/0011-economy.md#phase-2-runtime-results-run2026-10-17-economy).
  `tools/economy.py check`: **0 mismatches** — 26 525 price calls (3 762 distinct inputs, all three difficulties,
  quest groups A and B on and off, set, rare, socketed, charged, ethereal, stacks, `item_reducedprices`), 138 repair-all
  sums, 54 `PayGold`, 43 sales and 14 purchases checked, 22 hires, 14 resurrections (10 paid, 4 refused), 20 death
  losses, 545 gold amounts at creation and 433 gold-find scalings (Normal 228, Nightmare 140, Hell 65), 102 object
  piles, 1 061 durability rolls and 1 412 melee wear events (964 armour picks, 1 878 chained draw pairs), 130 quantity
  uses, 287 replenish ticks; the five Phase 1b required cases (case 1, the slot weights, settled). Question 9 answered
  with a control (one read, `NPC_TradeOpen`'s byte `+0x27`). New reading: a refused resurrection pays nothing and
  revives nothing (0x00579CAE). **Shortfalls** (named in the record, left `[I]`): quest, partial, ethereal and broken
  repairs; Wirt's and Baal's gold, the caps, pickup and stash move; the Hell repair price; crafted items, ears, Encode
  4, the recharge cost; charges and skill wear; gamble at clvl 3; Cain one case. Tools: `tools/economy.py` (checker
  additions), `tools/economy_sessions.py` (`die --resurrect`, retries, walking deaths), `tools/gdb/economy.py` (watch pc
  fix), `tools/d2pilot.py` (`qualres`, Tyrael's menu order). Review request
  [2026-10-19-reverser-architect-plan-0043-p2-review](../backlog/2026-10-19-reverser-architect-plan-0043-p2-review.md);
  spec-writer entry [2026-10-19-reverser-spec-writer-plan-0043-p3-economy-inputs](../backlog/2026-10-19-reverser-spec-writer-plan-0043-p3-economy-inputs.md);
  the required-cases entry closed.
- **2026-10-19 — Phase 2 review (architect, `lane/p43h` at `50a0eaf`, `main` `02d790d` merged): accept with fixes.**
  Read: [items/0011 § Phase 2](../findings/items/0011-economy.md#phase-2-runtime-results-run2026-10-17-economy) and its
  open questions, the [run record](../findings/items/experiments.md#run2026-10-17-economy), the manifest, the review
  request, the spec-writer entry and the tool diffs (`tools/economy.py`, `economy_sessions.py`, `gdb/economy.py`,
  `d2pilot.py`). Re-run: `tools/economy.py check` over the 33 claim logs gives a byte-identical `check-run.txt`
  (0 mismatches); `tools/test_economy.py` 9 tests OK. Anchors checked in the pinned `Game.exe` with r2:
  0x00579C9E–0x00579D5D (`MERC_ResurrectCost`, `PayGold`, the test at 0x00579CAE, the revive only on the non-zero
  path), 0x00576D90–0x00576DDC (`PayGold` refuses when gold + stash < amount, signed), 0x00732B90 (seven pairs: slots
  1/3/4/5/8/9/10, weights 3/5/4/4/2/2/2, count 7 at 0x00732BC8), 0x0057D41A–0x0057D4B4 (weights summed over slots whose
  item passes the type test, `RangeB(7)` then `RangeB(W)` on the unit's `+0x20` seed, the cyclic pick),
  0x0057949E–0x005794B3 (`cmp byte [edi+0x27]`, the clear at `[edi+0x20+7]`, the call 0x00536D10).
  - **Ruling (b), the resurrection refinement: rests on the code, not fitted.** The branch is direct (0x00579CAE
    `test eax, eax; jne 0x00579CC8`, else the common exit), and the four refused cases are told by the logged
    `PayGold` exit `v = 0` in sessions 4352, 4354, 4359 and 4360, independent of the checker's `gold + stash < cost`
    test, which is `PayGold`'s own condition (0x00576DB3). Scoped: "pays nothing" is `[C]`; "revives nothing" is `[I]`,
    since the logger does not record the mercenary after the call (fix 3).
  - **Ruling (c), question 9 and the pre-4335 watch data.** No claim rests on sessions 4311–4334's watch hits: the
    question-9 statements cite 4335, 4401 and 4403 only; the hire check on 4334 counts its 41 `LOGERR` lines as the
    broken handler's and rests on no watch line. The `+0x27` read at 0x0057949E is `[C]` (the watch hit at 0x005794A2,
    the next instruction, and the code). The absence of other reads is **not** controlled: the control's 40-line cap was
    reached within two frames of the watch being set in all three sessions, so nothing shows the watchpoint armed during
    the later repair, repair-all and other NPCs' windows; the raise is "in part" and the absence an observation (fix 5),
    with a rerun in P2b.
  - **Required case 1, the slot weights: verified.** The table holds 3/5/4/4/2/2/2 and the logged `W` 18 (left hand
    empty: 22 − 4) and 10 (head 3 + body 5 + belt 2) are separated from the lead's 2/3/2/1/1/1 (10 and 6); 964 of 964
    picks name the slot whose item is then rolled. A wrong table could not match by chance.
  - **Seed movement: accepted with one scoping.** The step counts are the kept output's. The three `+4` sales each hold
    one `DropGoldAmount` beside the copy; the 2 unchanged sales (4311 line 29206, 4332 line 5963) hold none and are not
    explained, so "sell draws only through its item creations" is `[I]`; buy (15 of 15 `+2`) and death (`+2` exactly in
    the 7 that dropped a pile) stand `[C]` (fix 4). The wear kinds' `ps` steps (3 = two picks and a roll, 2 = picks and an
    item without durability, 1 = the attacker's weapon roll) agree with the code read above.
  - **Ruling (a), the shortfalls: Phase 3 may start; a Phase 2b is filed.** The run clears every numeric floor of the
    *Done when* by a wide margin, and the single-case branches (broken armour, weapon to 0, Cain) are rightly `[I]`
    (one case decides nothing here). But three named items are not rare branches and the *Done when* lists them: a
    quest repair (items/0011 names no such path, so P2b first shows whether 1.14d has one), Wirt's gold, and "every
    item quality" (crafted). With the cheap stock cases (the Hell repair price, the clvl 3 gamble with the save already
    built, the partial, ethereal and broken repairs) and the two follow-ups above they form Phase 2b (one slot). None
    blocks the spec: each stays `[I]` and goes under the spec's *Open questions*. Charges, skill wear, ears, Encode 4,
    the recharge cost, version-0 items, Baal's gold, the caps, pickup and the stash move are accepted as shortfalls.
  - **Ruling (e), gold per difficulty: accepted.** Hell 65 of 433 covers both gold-find states (4393/4395 with, 4397
    without); the scaling has no difficulty term to separate.
  - **Fixes (made here):** (1) *miscount:* eight counts in items/0011, the record and this log were one off the kept
    `check-run.txt` (armour picks 963 → 964, W 18 801 → 802, events with the slot list 974 → 975, wear rolls 1 060 →
    1 061, armour rolls 913 → 914, melee wear events 1 411 → 1 412, DL `+1` 1 010 → 1 011, resurrect-cost calls 35 → 34,
    the player's seed logged in 20 of them); corrected to the output. (2) *other:* the manifest mixed two path bases
    (46 lines relative to `workspace/logs/`, 6 tool lines to the repository root), so `sha256sum -c` failed from either;
    normalised to the root, 52 of 52 OK, new hash `addf7737…` in the record. (3) *overclaim:* the refused resurrection's
    "revives nothing" scoped to `[I]`. (4) *overclaim:* sell's seed scoped to `[I]`, the two unexplained sales added to
    items/0011's open questions. (5) *overclaim:* question 9 raised in part; the absence uncontrolled; the record carries
    the review note and the open question the rerun.
  - **Ledger:** 5 fixes: overclaim 3, miscount 1, other 1. Promoted in the reverser's review-fixes: rule 2 gains "copy a
    run's counts from the kept output" (fix 1), rule 4 gains "an absence counts only with a control live over the whole
    window" (fixes 4–5), rule 6's one-path-base manifest recurred (fix 2, after H7a).
  - **Backlog:** review request closed; the spec-writer entry
    [2026-10-19-reverser-spec-writer-plan-0043-p3-economy-inputs](../backlog/2026-10-19-reverser-spec-writer-plan-0043-p3-economy-inputs.md)
    released with the three scopings; filed
    [2026-10-19-architect-reverser-plan-0043-p2b-economy-remainder](../backlog/2026-10-19-architect-reverser-plan-0043-p2b-economy-remainder.md).
  - **Next:** merge `lane/p43h`; Phase 3 (spec-writer) from the released entry; Phase 2b when harness slot 1 frees.
- **2026-10-19 — Phase 3 written (spec-writer, `lane/p43s`, from `main` `7aeeafd`), review requested.** New
  [items/economy](../specs/items/economy.md), draft, {C 106, I 81, L 12}: the `Scale` primitive, the price core
  (early returns and base, value terms with the per-stat table by `Encode`, mode steps, NPC row and quest groups,
  quantity, recharge, `max buy`, result), the gamble price, buy, sell and repair, gold (payment, caps, pile amount,
  `DropGoldAmount`, the death loss with the `game+0x6A` writer of rbs2 (b), corpse, hire, resurrect and Cain costs),
  wear (armour pick, rolls, quantity, charges, replenish) and a draws-per-event table; eight worked examples from
  run:2026-10-17-economy. The three released scopings are applied; Phase 2b's items and the accepted shortfalls are
  `[I]` in the body and listed under *Open questions* (6 `[L]` items plus 6 community differences). Cross-links:
  items/vendors § I (renamed "Prices and repair", now a link), hirelings § K and F3 (`PayGold` and resurrection
  raised to `[C]` from the run), items/quest-drops D6 and its `DropGoldAmount` question (struck), the items README
  Files row, two glossary terms, and the two inbound links the § I rename broke. Research map: `items/economy` →
  `draft spec` (the architect's row, proposed in the review request). Backlog: the inputs entry closed, the rbs2
  readings entry annotated (part (b) folded), review request
  [2026-10-19-spec-writer-architect-plan-0043-p3-economy-spec-review](../backlog/2026-10-19-spec-writer-architect-plan-0043-p3-economy-spec-review.md).
- **2026-10-19 — Phase 3 review (architect, `lane/p43s` at `6607069`, from `main` `7aeeafd`): accept with fixes.**
  [items/economy](../specs/items/economy.md) is `reviewed`, {C 109, I 80, L 12} after the fixes. Read: the spec whole,
  [items/0011](../findings/items/0011-economy.md) § 1–§ 8 and § Phase 2, the
  [run record](../findings/items/experiments.md#run2026-10-17-economy), the Phase 2 rulings above, the review request
  and the cross-link diffs. Re-run: `tools/economy.py check` over the 33 claim logs gives an output byte-identical to
  `check-run.txt` (0 mismatches). Worked examples recomputed with `tools/economy.py price` against the logged results:
  1 (11 442), 2 (1040), 3 (5278 and 80) and 4 (52 943); 5–8 by hand from the logged seeds and values (EconK1/K9,
  18 750, 24 → 129, `u` 4, `w` 0, rolls 80 and 51): all agree. Anchors checked with r2 in the pinned `Game.exe`:
  0x00559E30–0x0055A07A (`ITEMS_DurabilityLossRoll`: the `IsType(50)`/`IsType(45)` gate, the chances, the inline
  step, the branch order), 0x00629044/0x0062904E and 0x00628D6A (the param shift and mask), 0x0062FAAC–0x0062FAF2 (the
  NPC step and `S`'s `sell mult` test), 0x005782C0–0x00578370 (the partial repair pays stat 14 through `PayGold`),
  0x0057F72D (the corpse cap). The three released scopings are applied: the refused resurrection "pays nothing" `[C]`
  and "revives nothing" `[I]` (G13); sell's seed movement `[I]` (§ I); question 9 only as the `+0x27` read, in the
  vendors open question. The six community differences each cite a registered source (`maxroll-d2r-items`,
  `d2dfg-blizzard`, both with plan 0043 notes in `docs/sources.md`); no transliterated code.
  - **Ruling 1, the indestructible item: holds; the record is amended and the clause raised.** All 50 of the run's
    "no durability" rolls are on two items of session 4381 with stat 152 = 1 in the full cache (a set `xtb`, 12 rolls,
    first at frame 791; a unique `uit`, 38), whose bases have `nodurability` 0, `durability` 18 and 86 and a non-zero
    maximum; every roll on an item without stat 152 drew (counted from the `DL0`/`DL1` pairs of the 33 logs). Only
    stat 152 explains the 50, so the clause is `[C]` (H2's new note); the record's *Limits* carries a review note and
    items/0011's Phase 2 remainder is corrected. `ItemHasDurability`'s other terms (F2) stay `[I]`.
  - **Ruling 2, the param packing: holds, re-anchored.** The shift and mask are not the checker's: the code reads them
    from the data tables' `+0xC6C` and `+0xC70` (0x00629044, 0x0062904E; `RechargeCost` 0x00628D6A), and the logger's
    `ECON` line reads 6 and 63 in all 8 games. The Encode 2/3 row now says so (items/0011 § 3 notes it); the term stays
    `[C]`, the recharge cost `[I]`.
  - **Ruling 3, the last wear branches: the checker's order is the code's.** The break branch tests "not `weap`"
    (0x00559F15) and "not broken", so a broken `armo` item falls to the version test; the two version-≠-0 branches
    then arm the durability timer when `ITEMS_GetMaxStack` > 0 (0x0055A031–0x0055A040), which neither items/0011 nor
    the spec stated. H2 rewritten and items/0011 § 7 noted; the branches stay `[I]` (single cases or none).
  - **Ruling 4, branches at `[I]` under a `[C]` parent.** The large form of `Scale` is separated at the NPC step and
    in the stat terms: a copy of `tools/economy.py` with the `0xFFFF` test made false reports 1 846 (line 491) and
    2 737 (line 295) mismatch lines on the claim logs, so those two and the `LARGE` constant are `[C]`. The same edit
    in `AddTerm` (line 417) reports 0, so the affix/set/unique large form is not separated (the request's "50 inputs
    above 0xFFFF at the affix step" counts base values) and stays `[I]` with the staff-mod and recharge forms. The
    writer's scratch count (`workspace/scratch-p43s/cov.py`, re-run here) shows zero cases of B1–B3, D1, the stat-252
    and full-durability repair branches, `r` on a repair and `L2 = 5`: those stay `[I]`, correctly. The mutation
    commands are in the record's review note.
  - **Ruling 5, the combat/delivery link: made.** One sentence in [combat/delivery § F](../specs/combat/delivery.md#f-the-boundary-at-delivery)
    links items/economy § H (no claim, no tag); `consumed_by` gains `items/economy`; the combat wiki's `based_on`
    date follows (its text is unchanged and still true).
  - **Cross-links.** items/vendors § I `[C]`: the routing is logged in the run, kept. quest-drops D6 and its struck
    question: kept. hirelings F3 `[C]`: 10 `PayGold` calls in the run took the rest from the stash (gold short, stash
    enough), kept; § K `[C]` covered the four other resurrection NPCs read from the code only: scoped (fix 5). The
    0038 inventory row 35's anchor fix resolves (E8). The wiki's stale-page warnings are cleared, not left: see fix 6.
  - **Fixes (made here):** (1) *under-claim:* the indestructible clause `[C]`, the record and items/0011 corrected.
    (2) *under-claim:* `Scale`'s large form `[C]` at the NPC step and in the stat terms, `LARGE` `[C]`. (3) *wrong
    anchor:* the Encode 2/3 packing cited the checker's decoder; now the code's two globals. (4) *miscount:* "22 claims:
    10 held, 5 with refinement, 6 contradicted" left out the 1 not covered. (5) *overclaim:* hirelings § K's `[C]`
    named five NPCs; the run resurrected at Qual-Kehk only. (6) *stale cross-reference:* the wiki kept "how Baal's
    gold is split into piles is unknown" twice (items-other-paths) and the stash payment and resurrection as
    code-only or named-only (characters); rewritten, and the `based_on` dates of items-other-paths, characters and
    saves moved to 2026-10-19 (saves: § H unchanged); "not yet reviewed" dropped now that the spec is. (7)
    *omission:* the combat/delivery link (the writer's point 5) and the H2 timer arm. Not the lane's: items/0011's
    Leads-used detail said the partial repair "takes all carried and stashed gold"; the code passes stat 14 to
    `PayGold` (0x005782C0–0x0057832F), so § 5 and the spec are right and the detail is corrected.
  - **Ledger:** 7 fixes: under-claim 2, overclaim 1, wrong anchor 1, miscount 1, stale cross-reference 1, omission 1.
    Spec-writer review-fixes: rules 2, 5, 7 and 8 recurred (fixes 5, 4, 6 and 1–2) and gain this review as a
    citation; rule 9 gains fix 3.
  - **Backlog:** review request closed; filed
    [2026-10-19-architect-spec-writer-plan-0043-economy-wiki](../backlog/2026-10-19-architect-spec-writer-plan-0043-economy-wiki.md)
    (wiki owner, architect rule 8). Phase 2b (`lane/p43b`) runs on; its items stay `[I]` in the spec and under
    *Open questions* until it lands, and the spec is re-tagged then.
  - **Research map:** `items/economy` → `reviewed`. Plan stays open for Phase 2b.
  - **Next:** merge `lane/p43s`; Phase 2b review when `lane/p43b` reports; then the spec re-tag and the wiki entry.
- **2026-10-19 — Phase 2b started; resume note (reverser, `lane/p43b`, harness slot 1).** Not done. Run id
  run:2026-10-19-economy2. Tools: logger `tools/gdb/economy.py` (+ `economy2.gdb` = `economy.gdb` with `quests.py`;
  new lines `NSX` sale copy decision, `WG0/WG1/WGS/WGN` Wirt's gold, `DUL`, the control watch `SWC` rate-limited to
  one line per 10 frames with no cap, item `id` and `ind`), checker `tools/economy.py` (NpcRepair one item and the
  partial repair, `ItemRepairAll` by caller, `ItemRepairBroken`, the sale copy decision, Wirt's piles, the watch span),
  `tools/economy_scan.py qrepair`, driver `tools/economy_sessions.py` (`--watchdog`, `fix:` with the repair confirm
  box, service stops `imbue@inv=c,r`, `wirt`), `tools/d2s.py` keys `crafted` and `broken`, recipes `econq.json`,
  `econh.json`. Sessions so far: 4501 (quest services, sales, question 9), 4503 (partial repairs, sales, question 9),
  dev 4502 (repair box measured); 4504 (Hell, crafted) running. Left: gamble at clvl 3 (EconDL3), Wirt (`wirt`
  with EconN), the record and finding. Saves in `workspace/scratch-p43b/saves/` (rebuild from the recipes).
- **2026-10-19 — Phase 2b done (reverser, `lane/p43b`, harness slot 1).** Record:
  [run:2026-10-19-economy2](../findings/items/experiments.md#run2026-10-19-economy2) (5 claim logs, 1 development log;
  manifest `workspace/logs/economy2-run-manifest.txt`, repository-root paths); finding
  [items/0011 § Phase 2b](../findings/items/0011-economy.md#phase-2b-runtime-results-run2026-10-19-economy2).
  `tools/economy.py check`: **0 mismatches** — 7 376 price calls (distinct: mode 0 542, mode 1 79, mode 2 153, mode 3
  59), counts from `check-run.txt`. By item: (1) quest repair: no quest script repairs (`economy_scan.py qrepair`);
  the socket and personalize services repaired their result (1 case each), the imbue's call is a no-op on the
  unidentified new item; (2) Wirt's gold: 18 piles, the count and the 18 ilvls reproduce (one game); (3) crafted: 55
  distinct inputs (sale 35, repair 17, purchase 3), tool-built items; (4) Hell repair: 25 distinct mode-3 inputs;
  (5) gamble at clvl 3: 125 distinct; (6) 4 single-item repairs: 2 partial, 1 refused at gold 0, 1 broken (paid);
  ethereal refused by the client (no call), `[I]`; (7) question 9: control live to each log's end in 4 sessions, the
  watch fired only at the `+0x27` read (5), no `+0x24..+0x26` reader in the windows played; (8) the two P2 sales: no
  store copy (ethereal; `carry1` unique, `sub_00575FA0_ItemIsCarry1Unique`); 11 sales separate copied (+2, 6) from
  refused (+0, 5). **Shortfalls:** single cases (broken repair, each service repair, one Wirt game); the ethereal server
  refusal and the `Cracked`/`0x0055F590` copy refusals not reached. Tools: `tools/economy.py`, `economy_scan.py`
  (`qrepair`), `economy_sessions.py` (`--watchdog`, `fix:`, service stops, `wirt`), `gdb/economy.py`, `gdb/economy2.gdb`,
  `d2s.py` (`crafted`, `broken`), recipes `econq`, `econh`. Symbols +2. Review request
  [2026-10-19-reverser-architect-plan-0043-p2b-review](../backlog/2026-10-19-reverser-architect-plan-0043-p2b-review.md);
  spec-writer entry [2026-10-19-reverser-spec-writer-plan-0043-p2b-economy-inputs](../backlog/2026-10-19-reverser-spec-writer-plan-0043-p2b-economy-inputs.md).
  Game stopped, slot 1 saves restored (empty), no background process.
- **2026-10-19 — Phase 2b review (architect, `lane/p43b` at `22ea490`, from `main` `7aeeafd`; `main` not merged in):
  accept with fixes. Phase 2 is closed.** Read: [items/0011 § Phase 2b](../findings/items/0011-economy.md#phase-2b-runtime-results-run2026-10-19-economy2),
  the [run record](../findings/items/experiments.md#run2026-10-19-economy2), the manifest, the kept `check-run.txt`, the
  review request, the spec-writer entry, the Phase 2b definition and the Phase 2 review above. Re-run:
  `sha256sum -c workspace/logs/economy2-run-manifest.txt` from the repository root, 20 of 20 OK (manifest
  `cb72ac21…`); `tools/economy.py check` over the five claim logs gives an output byte-identical to `check-run.txt`
  (`4cb39d92…30b4`, 0 mismatches); `tools/test_economy.py` 9 tests OK. Anchors checked with r2 in the pinned `Game.exe`:
  `ItemRepairAll` returns at once when `ItemCanRepair` fails (0x005761CB), and `ItemCanRepair` needs an item unit with
  flag `0x10` (identified) and not `0x400000` (0x0062E66B–0x0062E691); the imbue calls `ItemRepairAll` at 0x0057A0F9
  and `ItemIdentifyAttach` after it at 0x0057A103; the socket call at 0x0057A3ED; `A1Q4_WirtGold` draws
  `RNG_RandLoHi(QUESTS_GetSeed(…), 10, 20)` once (0x00594651–0x00594664, `+0x90` latch) and makes one `DropItemAtUnit`
  pile per event (0x00594695, `+0x8C` decremented); `DropItemAtUnit` takes ilvl from `LevelMonLvl`, at least 1
  (0x00559AE3–0x00559AF8); `NPC_SellItem`'s copy tests 0x0057962B–0x0057971B; `sub_00575FA0` (type 4, quality 7,
  file index ≥ 0, UniqueItems `+0x2C` AND 0x006CE270 = 4, the `carry1` bit of UniqueItems.md); the thunk 0x005762B0
  (frame and `jmp 0x005761C0`); the partial repair's unsigned `div` for `k` and signed `idiv` for the gain
  (0x005782DA–0x00578309).
  - **Ruling 1, the quest repair: accepted as written.** No quest script repairs (`[I]`, the scan; no second source),
    and the repair is the services' shared `ItemRepairAll` step. Larzuk's socket and Anya's personalization each took
    a cap from durability 1 to 12 (`[C]`, one case each: a wrong reading leaves 1, reverser rule 10). The imbue's call
    is a no-op `[C]`: the code refuses an unidentified item and identifies after the call, and the run shows flags
    `0x82000` (no `0x10`) and 10 of 12 unchanged, which the alternative (a repair) could not give.
  - **Ruling 2, Wirt's gold: `[C]`, as scoped.** The count draw is matched by the logged quest seed's step (a
    32-bit match, not a one-in-ten chance) and the range is the code's immediates, so one game suffices for the draw;
    10..19 piles; the 18 piles' ilvl 6 and their amounts (among the 40 gold creations checked) reproduce. Which Levels column `LevelMonLvl` read here stays
    unseparated (both 6), stated.
  - **Ruling 3, question 9: `[C]` for the windows played; not raised further.** The control (uncapped, rate-limited)
    wrote 66 lines and a line after the last window of each log, so the P2 objection (a cap reached in two frames) is
    met. One scoping: in 4505 the watch was set at frame 1769 as the first Gheed gamble window opened and the control's
    first line is at 2729, so that window is bracketed by the setting and the next control line rather than holding
    one (fix 4). A reader of `+0x24..+0x26` outside the played windows cannot be excluded by a run; that remainder is
    out of this plan (the open question stays in items/0011).
  - **Ruling 4, the sales and sell's seed: raised in part to `[C]`.** The 11 logged decisions give 6 copies (`+2`
    each; 3 placed, 3 freed) and 5 refusals (`+0`: ethereal 2, broken 2, `carry1` 1), the check output's counts; the
    two P2 sales are of the refused kinds (flags `0xC00010`; *Annihilus*). But the copy decision runs **every** test
    (eight, each clearing `[ebp-4]`), not "the first matching" one (fix 1), and five refusal tests were not reached
    (fix 3); sell's seed is `[C]` for the copy and the three reached refusals and `[I]` for the five others (fix 2,
    reverser rule 8).
  - **Ruling 5, the single cases: accepted as `[I]` where stated.** The broken repair (one case, its `IB` line misread
    by the earlier logger) keeps "no draw" `[I]`; its `ItemRepairAll` lines and the paid amount reproduce. The two
    partial repairs are `[C]` (code and two cases; the arithmetic's rounding rests on the code). The ethereal server
    refusal stays `[I]` (client-side in practice). Each service repair is one case and decides (ruling 1).
  - **Symbols:** both new rows checked; neither address is named on `main` (4af9f86); names, kinds and `[I]` fit.
  - **`tools/test_d2s.py`:** confirmed on `main` (4af9f86): `test_every_recipe_has_a_base` fails on twelve plan 0042
    recipes with no `RECIPE_BASES` row (`quest-tpc`, `quest-death`, `quest-orbwill`, `quest-talk1`..`5`,
    `quest-talk1c`..`4c`); not this lane's. Filed to the archivist.
  - **Fixes (made here):** (1) *misread:* "refuses the store copy at its first matching test": every test runs; the
    eight listed in order. (2) *overclaim:* "sell's seed reading is raised" (untagged, covering unreached refusals):
    now "raised in part", `[C]` with a remainder, and Phase 2's § 8 remainder points to it. (3) *omission:* the
    not-reached list lacked base type 7, flag `0x1000000` and the store record's byte `+4`. (4) *overclaim:* question
    9's control "from the frame the watch was set" in all four logs; 4505 scoped (finding and record). (5) *overclaim:*
    the spec-writer entry's "each now `[C]` unless noted" carried the scan (`[I]`), the unreached refusals ("…") and
    Wirt's ilvl column unscoped; corrected. (6) *omission:* `sub_00575FA0`'s description lacked its unit-type and
    file-index tests. (7) *other:* the record's *Observed* block, labelled "trimmed from", is a summary; relabelled,
    the exact lines being in the hashed output.
  - **Ledger:** 7 fixes: overclaim 3, omission 2, misread 1, other 1. Reverser review-fixes: rule 4 (a control live
    over the whole window) recurred (fix 4, after the P2 review) and rule 8 (split a raise) recurred (fix 2); both gain
    this review as a citation.
  - **Backlog:** review request and the P2b remainder entry closed; the spec-writer entry
    [2026-10-19-reverser-spec-writer-plan-0043-p2b-economy-inputs](../backlog/2026-10-19-reverser-spec-writer-plan-0043-p2b-economy-inputs.md)
    corrected and **released** for a re-tag pass of the reviewed items/economy; filed
    [2026-10-19-architect-archivist-register-the-plan-0042-quest-recipes-in-test](../backlog/2026-10-19-architect-archivist-register-the-plan-0042-quest-recipes-in-test.md)
    and [2026-10-19-architect-archivist-unique-items-carry1-has-a-reader](../backlog/2026-10-19-architect-archivist-unique-items-carry1-has-a-reader.md).
  - **Close:** Phase 2 is done for good (no Phase 2c: the remainders are single cases or unreachable by a run). Plan
    0043 closes at the review of the items/economy re-tag pass; the wiki entry
    (`2026-10-19-architect-spec-writer-plan-0043-economy-wiki`) may ride the same spec-writer pass or follow the close.
  - **Merge note:** this branch's plan log conflicts with `main`'s (the P3 entries of `lane/p43s`, appended after
    `7aeeafd`): keep both sides, in either order; the ledger rows likewise.
  - **Next:** merge `lane/p43b`; the spec-writer re-tag pass; harness slot 1 to the next H2 batch (plan 0038 H5b).
- **2026-10-19 — Phase 2b re-tag and economy wiki (spec-writer, `lane/p43t`, from `main` `cf617f0`), review
  requested.** [items/economy](../specs/items/economy.md) re-tagged from
  [run:2026-10-19-economy2](../findings/items/experiments.md#run2026-10-19-economy2): {C 109, I 80, L 12} →
  {C 125, I 83, L 12}. Changed: Entry points (quest services' repair, Wirt's body), C4 crafted, D2 Hell repair, E2
  `L2 = 5`, F4 (the eight copy tests, all evaluated; three reached `[C]`, five `[I]`), F6 single-item and partial
  repairs `[C]` (ethereal server refusal `[I]`), F7 (the quest repair: socket and personalize `[C]`, the imbue no-op
  `[C]`, no quest script repairs `[I]`; the broken repair's draws `[I]`), a § F note on the store record (`[C]` for
  the windows played), G8/G8a Wirt's gold `[C]` (ilvl column unseparated), § I (sell split, Wirt row), a
  reimplementation note, Evidence, *Open questions* (Phase 2b struck; its remainder one `[L]` bullet). Stale text
  closed: [items/quest-drops](../specs/items/quest-drops.md) F0, F1, Outputs and the Wirt row ({C 81, I 88, L 2} →
  {C 84, I 87, L 2}), [items/vendors](../specs/items/vendors.md)' store-record question (tags unchanged). Wiki: new
  [economy](../wiki/economy.md) page, index row 8, items-other-paths' vendor link and services paragraph. Gate green.
  Backlog: the P2b inputs and the wiki entries closed; review request
  [2026-10-19-spec-writer-architect-plan-0043-economy-retag-and-wiki-review](../backlog/2026-10-19-spec-writer-architect-plan-0043-economy-retag-and-wiki-review.md),
  which notes that the plan can close at this review. Research map: no status change (`reviewed`); the tag counts
  for the architect.
