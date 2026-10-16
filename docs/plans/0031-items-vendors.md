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
  - the Phase 1b cases;
  - first, the three vendor saves loaded and written back item for item, their `test_d2s.py` hashes pinned (moved
    from Phase 0 at its review).

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
- **2026-10-15 — Phase 0 landed (archivist, `lane/a31p0`), review requested.** [Npc](../tables/Npc.md) (76-byte
  record, 19 u32 fields), [Gamble](../tables/Gamble.md) (12-byte record: the code and 8 zero bytes) and
  [StorePage](../tables/StorePage.md) (4-byte code list): `excel_bin.py diff` 0 mismatches on all three, every byte
  mapped; `excel_layout` baseline regenerated (53 tables). § Vendor columns in [Weapons](../tables/Weapons.md#vendor-columns-plan-0031-phase-0),
  [Armor](../tables/Armor.md#vendor-columns-plan-0031-phase-0) and [Misc](../tables/Misc.md#vendor-columns-plan-0031-phase-0);
  `tools/vendor_survey.py` (`bases <vendor> <difficulty>`, `gamble`, `npc`, `summary`; gate survey `vendors`) runs
  for all 17 vendor column groups and the 17 Npc rows in each difficulty. Recipes `vendornova.json` (clvl 30),
  `vendornova75.json` (clvl 75) and `vendorclassic.json` build and parse ([d2s.md § Vendor saves](../formats/d2s.md#vendor-saves)).
  Surprises: the Npc rows and the item column groups differ (`nihlathak` has no group, `Cain` has a group and no
  row, `hratli`/`Hralti`); Npc stores sell before buy, and `questbuymult`/`questrepmult` hold the same values, so
  which slot is which is `[L]`; StorePage is loaded only under `-txt` (data/0001) and its `mag` page is named by no
  item type; every `NightmareUpgrade`/`HellUpgrade` target is a normal-tier base (a step along the same type, never
  the exceptional code); Hralti's `MagicLvl` is 0 on all weapon and armor bases (the dead `HratliMagicLvl` header);
  staves, wands, sceptres, orbs and class items are not in Gamble. **Not done:** the saves were not loaded in the
  game, because no harness slot was assigned to this lane; the `questbuymult`/`questrepmult` order could be settled
  by a `-txt` compile probe in the same session. Both are in the review entry.
- **2026-10-15 — Phase 1 and Phase 1b (reverser, `lane/r31p1`).** [items/0009](../findings/items/0009-vendors.md)
  read before Phase 0 landed (raw `.txt` headers). The store seed (`Game+0x1D24` → `+0x08`, seeded once per game from
  one game-seed draw) drives every stock, upgrade and gamble draw, and the hireling lists share it. Stock is built on
  the first trade open and rebuilt only after a leave-town reset or a stale mark (240 000 ms with players left in
  town); a level-up rebuilds nothing. Stock level is `clvl + 5`, capped per act in Normal; no normal copies from 25.
  Gambling: 14 slots, `lvl` in `clvl − 5 .. clvl + 4`, slots 0/1 ring and amulet, upgrade then quality on the store
  seed. 41 functions and 4 globals named; tags 1 `[C]`, 42 `[I]`, 22 `[L]`. Phase 1b: three contradictions
  (`<Vendor>MagicLvl` is a minimum, the upgrade constant is 1/10 000, the gambled affix window), all Phase 2 required
  cases. Surprise: a classic Nightmare/Hell store may hit a fatal assert on an expansion `ubercode` (open question).
- **2026-10-15 — Phase 1/1b accepted (architect review).** Ten anchors re-read in `game.exe` (store seed, stock level
  caps, normal-quality pick, `MagicLvl` test, stock upgrade bounds, gamble `lvl`/pick, `GAMBLE_Upgrade`, the NPC slot
  table); all agree. Boundary ruling for Phase 2: model the store seed end to end; `HIRE_BuildStock` is a logged
  oracle until plan 0033; the `g_GambleList` order is dumped per run and the spec carries it as a table. The classic
  Nightmare `ubercode` assert joins the Phase 2 required cases. Phase 0 (archivist) is still to land; Phase 2 waits
  for it.
- **2026-10-15 — Phase 0 accepted (architect review).** `excel_bin.py diff` rerun on the three tables, 0 mismatches; the vendor survey runs for every group and difficulty; gate (with the `excel_layout`, `vendors` and `hireling` baselines) and `test_d2s` green after merging main. No table doc contradicts items/0009; the `[L]` the finding settles go to an archivist follow-up (backlog). Rulings: the unloaded vendor saves do not block; **Phase 2's first harness step loads `vendornova`, `vendornova75` and `vendorclassic`** (enter, *Save and Exit*, compare item for item) and pins their `test_d2s.py` hashes, before any store is opened. No `-txt` compile probe for `questbuymult`/`questrepmult`: prices are named only and Npc.txt is off the creation path; the npc field descriptor would settle it statically if ever needed.
- **2026-10-16 — Phase 2 (reverser, `lane/h31p2`), review requested.** run:2026-10-15-vendors. The three vendor saves
  load and come back item for item (hashes pinned). `tools/vendors.py` (store seed end to end, items handed to the
  item chain; `HIRE_BuildStock` oracle; `g_GambleList` dumped) reproduces 7 games with 0 mismatches: 94 stock builds of
  every store NPC in two or three difficulties, 4656 stock items, 325 gamble windows (4550 items) at clvl 30 and 75,
  9206 creations, 13 rebuilds in one game; a classic Normal and Nightmare pair. Phase 1b cases settled; the classic
  `ubercode` assert is unreachable on stock data. Surprise: in single player an act change by waypoint does not reset
  the act's stores (stale only after 240 s), a level change within the act does, so items/0009 § 3 is corrected. The
  `d2pilot.py npc` action (trade, gamble, hire) is in [tooling § NPC actions](../../.claude/skills/reverser/references/tooling.md#npc-actions-plan-0031-run2026-10-15-vendors).
- **2026-10-16 — Phase 2 accepted with fixes (architect review).** Rerun, no game launched: `tools/vendors.py check`
  on the 7 logs of `vendors-run.lst` exits 0 with every reported count (94 builds, 4656 stock items, 325 windows /
  4550 slots, 7513 + 16 130 store-seed draws, 9206 item seeds, 8787 + 419 chained), `items_chain.py props` on 3207
  419 / 0 failed, `sha256sum -c` of the manifest all OK, `test_d2s.py` 41 OK, `symbols.csv` no duplicate address or
  name. r2 re-read four anchors: `NPCSTORE_ActStale` (the `townEmpty` branch, `buildTick + 0x3A980` unsigned),
  the `TownLevelLeave` call (`sete` on the count, return 0x00537402), the gamble `lvl` and pick (0x00578877–0x005788C3)
  and the `MagicLvl` `jg` (0x00576AEA); all agree. The model asserts S at the `HIRE_BuildStock` entry and checks the
  `VGL` dump (members, `countUpTo`, level sort, same order each run), so the oracles are as ruled (ADR-0004).
  Done-when met in full: every store NPC in two difficulties (three in expansion), ≥ 1 000 stock items, ≥ 300 gambled
  items over ≥ 50 windows at two levels with `GFREE` as the refresh trigger, rebuilds in one game, classic, the
  Phase 1b cases and the three saves first. **Rulings:** (1) the vendor saves are tool-built characters, ADR-0003
  inputs on stock data with no table edit, so not ADR-0010 forced runs; they carry `[C]` for code that reads clvl,
  difficulty, act and expansion as inputs, and nothing about how a character reaches that state. (2) The 24 `[I]` →
  `[C]` stand: each is reproduced draw for draw (or by the trigger state at each open), and every raised bullet names
  the run (two did not; fixed). (3) The town-leave correction is accepted as `[C]` for waypoints only; a walk out of
  town is `[I]` (not run), and why an act change still counts the player is an open question, not a blocker. (4) The
  240 s threshold is `[C]` from the code plus the marking side (7 marks, all > 240 s, none sooner); the logs hold no
  current tick for the stores kept, which the run's limits now say; a later logger adds the tick to `STALE`.
  (5) The classic `ubercode` assert is settled by data (972 cells, no expansion target) plus 28 classic Nightmare
  upgrades reproduced. (6) Commit 1e81f01 joined `git add` and `git commit` in one call: process note only, no rewrite.
  **Fixes made:** run anchors on the gamble `ilvl` and ring/amulet bullets; the same-act reset scoped to waypoints;
  the run's limits extended. **`d2pilot.py npc`** is fit for plans 0033 and 0032 Phase 2: documented in tooling
  § NPC actions with the menu table, a pause guard on the `TICK` heartbeat (so the logger must source
  `tools/gdb/vendors.py`), stops with a screenshot after eight unmoving clicks; the menu table assumes the
  every-quest-done state of the vendor saves (the option-count shift covers a talk line; other quest states may
  need rows), and `wpchain` must be capped with `timeout`. Phase 3 (spec-writer) next.
