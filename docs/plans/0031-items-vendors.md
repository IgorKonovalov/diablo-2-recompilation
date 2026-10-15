# 0031 — Items: vendor stock and gambling

> **Status:** in-progress (approved 2026-10-15)
> **Created:** 2026-10-15
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0011-harness-slots

## TL;DR

**Question:** when a player opens a vendor's trade or gamble window, which items does the game create, with which
ilvl, quality and seed, and when is the stock rebuilt? Vendor stock and gambling never reach `TC_ResolveDrops`
([items/README](../specs/items/README.md)); they are their own callers of item creation (ADR-0002). When it is done:
- `Npc`, `Gamble` and `StorePage` have table docs, and the per-vendor columns of Weapons/Armor/Misc are documented;
- `docs/findings/items/0009-vendors.md` names the stock builder, its triggers, the per-vendor item picks, the vendor
  ilvl, the magic-item rolls and the gamble roll (item pick, ilvl, quality, the exceptional/elite upgrade);
- `tools/vendors.py` predicts a vendor's stock and a gamble window from the seeds, chained into the item model;
- `docs/specs/items/vendors.md` is drafted.

## Context

- Research-map row `items/vendors`: `not started`. Dependencies `items/quality` and `items/affixes` reviewed.
- Code already named: `sub_00557450_ItemCreateByQuality` (C) → `sub_00556F60_ItemRollQualityCreate` (I), whose
  other callers ([items/0002](../findings/items/0002-quality-roll.md)) are "vendors, gambling, cube, quest items";
  `sub_00558D90_ItemCreate` (I); `sub_005467E0_NpcActTravel` (I, the travel branches only). There is no store, vendor
  or gamble symbol yet.
- Data:
  - `npc` (17 rows, stride 76), `gamble` (125 rows, stride 12) and `storepage` (4 rows, stride 4) have no table doc
    and no layout;
  - the item layout already places `StorePage` (`+0x022`), `gamble cost` (`+0x0D4`), `PermStoreItem` and `multibuy`
    (`+0x1A4`/`+0x1A5`). The per-vendor columns (`<Vendor>Min`, `<Vendor>Max`, `<Vendor>MagicMin`, `<Vendor>MagicMax`,
    `<Vendor>MagicLvl` for each store NPC) and `NightmareUpgrade`/`HellUpgrade` are in the layouts by stride, but not
    documented.
- Harness: `tools/d2s.py build` can set gold (any ItemStatCost stat through `stats`). `tools/d2pilot.py` has no NPC
  actions. `tools/xdrive.py` can click; NPCs are monster units whose positions the existing loggers already print.
  NPC dialogue menus are fixed-position text, so a click table per NPC menu is enough.
- Leads: `src:arreat-summit-magic-items` (§ Gambling), `src:fandom-d2-unique-set` (gambling and the unique limit),
  `src:d2dfg-blizzard` (§ Npc.txt, § Gamble.txt, the vendor columns of Weapons/Armor/Misc). Gambling odds are widely
  documented, so Phase 1b is required.

## Phases

### Phase 0 — Npc, Gamble, StorePage and the vendor columns
- **Owner skill:** archivist
- **What:** document the three tables with `.bin` layouts and the vendor columns of Weapons, Armor and Misc; build
  the vendor saves.
- **Outputs:**
  - `docs/tables/Npc.md`, `docs/tables/Gamble.md`, `docs/tables/StorePage.md`;
  - [Weapons](../tables/Weapons.md), [Armor](../tables/Armor.md), [Misc](../tables/Misc.md): a § Vendor columns with
    each vendor's column group, the upgrade columns, `PermStoreItem` and `multibuy`; a survey command that prints, for
    one vendor and difficulty, every base it can stock with its min/max and magic columns;
  - `tools/excel_layouts.py` entries and the regenerated baseline;
  - recipes `vendornova.json` (expansion, clvl 30 and clvl 75 variants, plenty of gold, quest state with every act
    open, so every vendor is reachable) and `vendorclassic.json`.
- **Done when:** `excel_bin.py diff` passes on the three tables with 0 mismatches and no uncovered bytes; the vendor
  survey runs for every store NPC and difficulty; the saves load. Meanings stay `[L]`.

### Phase 1 — Read the stock builder and gambling
- **Owner skill:** reverser
- **What:** read what happens on the server when a player opens a vendor's trade window and gamble window.
- **Outputs:** `docs/findings/items/0009-vendors.md`; `re/symbols.csv` rows (subsystem `items/vendors`); `re/types/`
  additions (the store and the Npc record).
- **Done when:** the finding states, with addresses and `[I]` or better:
  - **when** stock is built and rebuilt: first open in a game, entering town, a quest event, each open, a timer, the
    player's level changing;
  - **which bases:** how a vendor's candidate list is made from the vendor columns and `PermStoreItem`, the count per
    store page, the draws per pick, and the order;
  - **the vendor ilvl:** its arithmetic (from the player's level, difficulty, the act), and the magic rolls (the magic
    and rare share, the affix ilvl from `<Vendor>MagicLvl`), entering the existing item model where it can;
  - **gambling:** the list built from `Gamble.txt`, the ilvl window around the player's level, the quality roll (the
    unique, set and rare chances, through `ItemRollQualityCreate` or its own code), the exceptional/elite upgrade, and
    the refresh;
  - **the seeds:** which seed is drawn for the picks (the game seed, the NPC's unit seed, the store's own), and each
    item's seed;
  - prices and repair costs are named only;
  - **the boundary decision** for Phase 2. Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch the leads above, search for and register vendor and gambling documentation (vendor ilvl, the
  gambling quality odds, the gambled ilvl window, the upgrade thresholds). Compare blind.
- **Outputs:** `docs/sources.md` entries; verdicts in the finding's *Leads used*.
- **Done when:** each claim carries a verdict; every `contradicted` claim reachable on stock data is a required case
  of Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md);
  at most two slots)
- **What:** write `tools/vendors.py` (chained into `tools/items_chain.py`), a `tools/gdb/vendors.gdb` logger, and
  `tools/d2pilot.py npc <name> trade|gamble` (walk to the NPC by its logged position, click it, click the menu line;
  the menu click table goes in `tooling.md`). Then log a run.
- **Logging:** each stock build or gamble refresh with its trigger, every draw on every seed, and each created item's
  full lines (with `affixes.gdb` and `props.gdb`).
- **Done when:** a run `run:YYYY-MM-DD-vendors` reproduces with 0 mismatches:
  - every store NPC of Acts I–V opened at least once in at least two difficulties, with at least 1 000 stock items in
    total, each reproduced from the seed at the build;
  - at least 300 gambled items over at least 50 gamble refreshes, at two player levels, with the refresh trigger
    shown;
  - at least one rebuild of the same vendor's stock in one game, so the trigger is `[C]`;
  - a classic session;
  - the Phase 1b cases.

  No odds claim is made from frequencies; the odds are stated from the code, `[C]` by the reproduced draws.

### Phase 3 — Spec: items/vendors
- **Owner skill:** spec-writer
- **What:** write `docs/specs/items/vendors.md`; link it from the items README and items/quality (gambling's quality
  path).
- **Done when:** the spec follows the template, and every statement is tagged. It has the triggers, the stock build as
  pseudocode with its RNG call order, the gamble roll, and worked examples from the run (one stock build, one gamble
  window). The architect's review passes.

## Open questions

- Multiplayer stock (per player or shared) is named only if the code is not clear.
- Prices and the buy/sell/repair formulas are game economy, not item creation; deferred under ADR-0002 unless the
  owner extends scope.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-15 — Drafted and approved.** The owner asked for a queue of plans to run unattended, and approved all of
  them in advance. Written in the architect worktree `lane/plans0028`.
