# 0019 — Items: unique and set selection, and the creation fallbacks

> **Status:** draft
> **Created:** 2026-10-14
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** once a drop has rolled quality 7 (unique) or 5 (set), which `UniqueItems` or `SetItems` row does the
item become? And what happens when no row fits? [items/0002](../findings/items/0002-quality-roll.md) § 8 names the
path only:
- `sub_00557450_ItemCreateByQuality` calls the unique builder `0x005566B0` or the set builder `0x005C2940`;
- on failure, a durability step (stats 72/73), then the fallback chain rare → magic → superior → normal (unique) or
  magic → superior → normal (set);
- six pre-switch helpers that can rewrite the quality to 4, 7 or 2.

This plan reads that code, along with a TC cell that names a unique directly. It models the candidate filter and the
weighted pick in `tools/uniques.py` and reproduces logged drops bit for bit. When it is done:
- `docs/findings/items/0004-uniques-sets.md` has the selection and the fallbacks at `[C]` for the logged cases;
- `docs/specs/items/uniques-sets.md` is drafted.

The unique and set *properties* (`prop1..12`, the set bonuses) are `items/properties`. The affixes of a rare or magic
fallback are `items/affixes`. Both are only named here.

## Context

- Research-map row `items/uniques-sets`, `not started`. Dependencies:
  - `rng` reviewed, `items/tc` reviewed;
  - `items/quality` findings `[C]` (items/0002, 1916 rolls with no oracle). Its spec is plan 0010 Phase 3, which is
    still to come, so Phase 3 here waits for it.
- Code already named, all `[I]` from the decompile:
  - `sub_00558D90_ItemCreate` → `0x00557AB0` → `sub_00557450_ItemCreateByQuality`;
  - the builders `0x005566B0` (unique) and `0x005C2940` (set);
  - `sub_005573F0_ItemFallbackRare`;
  - the pre-switch helpers `0x0062E9E0`, `0x00628CD0`, `0x0062A0F0`, `0x0062E990`, `0x00628C70`, `0x0062EA30`;
  - the creation-side quality roll `sub_00556F60_ItemRollQualityCreate`, reached from the fallback helpers;
  - `UNIQUEITEMS_GetRecord` 0x00483470 (items/0003);
  - the TC cell that names a unique by `index` (`TC_ParseItemCell` with the `uniqueitems` name link, data/0001 § 7).
- Data: [UniqueItems](../tables/UniqueItems.md) and [SetItems](../tables/SetItems.md) have `.bin` layouts `[C]`
  for the record heads (`version`, `enabled`, `ladder`, `rarity`, `lvl`, `lvl req`, `code`/`item`, `set`), with
  meanings `[L]` except the art columns. `nolimit` is blank in every row. `UniqueItems.index` is not unique (`Rainbow
  Facet` ×8), and 14 rows have a blank `code`. `sets.txt` has no doc.
- Harness: `tools/gdb/tc-drops.gdb` and `tools/quality.py` (plan 0010 Phase 2). The drop path from the resolver
  through the quality roll already runs with no oracle. TCs with a high unique and set ratio (boss and superunique TCs,
  items/0001 § 7) raise the rate of quality 7 and 5. Nightmare and Hell saves come from `tools/d2s.py build`
  (`acts_open`).
- Why now: this is the next step of the item chain after the quality roll. It is smaller than `items/affixes` and
  shares its harness. Item properties and `save/d2s` reviewed also wait on the per-item part of creation.
- Leads: `src:d2dfg-blizzard` (registered; its UniqueItems, SetItems and Sets sections are not yet read). Items have
  wide community coverage, so Phase 1b is required, not optional.

## Phases

### Phase 0 — Unique and set generation columns
- **Owner skill:** archivist
- **What:** survey the generation columns of UniqueItems and SetItems per base item, and document Sets.
- **Outputs:**
  - [UniqueItems](../tables/UniqueItems.md) and [SetItems](../tables/SetItems.md): value ranges of `version`,
    `enabled`, `ladder`, `carry1`, `rarity`, `lvl`, `lvl req` per row class (classic, expansion, disabled, label
    rows), and per base code the number of candidate rows with their `lvl` and `rarity`. Also the label rows and
    blank-code rows a reader must skip;
  - `docs/tables/Sets.md`: layout and identity columns, the `version` and `level` columns, and the link from `SetItems.set`.
    The bonus property columns are noted as `items/properties`;
  - a `tools/` survey command.
- **Done when:** one command prints, for every base code with at least one unique or set row, its candidates
  (row, `lvl`, `rarity`, `version`, `enabled`). It also prints the bases with more than one candidate, and the
  duplicated `index` names. `excel_bin.py diff` passes on Sets. Meanings stay `[L]`.

### Phase 1 — Read the builders and the fallbacks
- **Owner skill:** reverser
- **What:** read the unique and set builders, the pre-switch overrides and the fallback chain. Then choose the
  boundary for Phase 2.
- **Outputs:** `docs/findings/items/0004-uniques-sets.md`, `re/symbols.csv` rows (subsystem `items/uniques-sets`,
  giving `ITEMS_` names to the `sub_` ones it settles), `re/types/` additions if a record is recovered.
- **Done when:** the finding states, with addresses and `[I]` or better:
  - the candidate filter of each builder: base code match, `enabled`, `version` against the item version, `lvl` against
    ilvl, `ladder`, any once-per-game record of an item already made, and the order of the tests;
  - the weighted pick: which seed (item seed or other), the range (sum of `rarity`, or otherwise), the draw count,
    and where it sits relative to the quality roll and the item seed initialisation;
  - the no-candidate exits, the durability step (stats 72/73, ×3 for unique, ×2 for set, cap 255), and each step of the
    fallback chain, up to where the affix or property code takes over;
  - the six pre-switch helpers: the condition under which each one rewrites the quality, and the value it writes;
  - the TC-named unique: how a pick of a unique `index` reaches the builder, and which of two equal `index` rows it gets;
  - whether `sub_00556F60_ItemRollQualityCreate` is reachable from the drop path. If it is reached only from vendors,
    gambling, the cube or quests, it is named only;
  - **the boundary decision** for Phase 2: which draws after the pick (property rolls, the affixes of a fallback)
    are ADR-0004 oracles. Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch `src:d2dfg-blizzard` (§ UniqueItems.txt, § SetItems.txt, § Sets.txt), and search for and register any
  community document on unique and set selection. Compare blind, per `evidence-rules.md` § Community cross-checks.
- **Outputs:** `docs/sources.md` entries or a "none found" note with the searches made; verdicts in the finding's
  *Leads used*.
- **Done when:** each claim about candidate filtering, the role of `rarity` and `lvl`, the no-candidate result and
  repeated uniques carries a verdict with a `src:` id or `not covered`. Every `contradicted` claim is a required case of
  Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (a human may play, as in plans 0004 and 0010)
- **What:** write `tools/uniques.py`, chain it after `tools/quality.py`, and log a new run.
- **Logging:** extend `tools/gdb/tc-drops.gdb`: on entry to each builder, the item's base, ilvl, version and seed
  state; each candidate the filter keeps; the pick draw; the row chosen or the failure; each fallback step taken.
- **Done when:** a run `run:YYYY-MM-DD-uniques` shows, with 0 mismatches against the model:
  - at least 30 unique builds and 30 set builds from drops, over classic and expansion and over at least two
    difficulties;
  - at least one base with several candidates (rings, amulets or jewels), and a duplicated `index` if a TC-named
    pick reaches one;
  - at least one failure of each builder, with its fallback chain, as far as the boundary of Phase 1;
  - every pre-switch override the drop path can reach, or a statement that the drop path cannot reach it;
  - the Phase 1b cases.

  The seed state after each builder matches the log. Any boundary that remains is named in the record. In-scope
  claims go to `[C]` citing the run.

### Phase 3 — Spec: items/uniques-sets
- **Owner skill:** spec-writer
- **What:** write `docs/specs/items/uniques-sets.md` and link it from the items README chain after the quality spec.
- **Done when:**
  - the spec follows the template and every statement is tagged;
  - it gives the RNG call sequence from the quality code to the chosen row, and the fallback chain as a decision
    order;
  - it has worked examples of one unique pick, one set pick and one failure, all taken from the run;
  - it starts after the items/quality spec (plan 0010 Phase 3) is drafted;
  - the architect's review passes.

## Open questions

- The `prop` blocks of UniqueItems and SetItems, and the partial and full set bonuses in Sets, are `items/properties`.
  Only which row is chosen is in scope.
- The rare and magic fallbacks draw affixes (`items/affixes`, not started). Phase 2 takes them as oracles if the
  boundary decision says so, and `items/affixes` replaces them later.
- Vendors, gambling, the cube and quest items call the same builders through other paths (`items/vendors`, `items/cube`,
  `items/quest-drops`). This plan specifies the shared builder only as reached from a drop.
- `ladder` rows in a single-player or offline game: Phase 1 says how the flag is tested. A ladder realm is out of reach.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-14 — Drafted (architect).** Picked from the research-map rows whose dependencies are met. It is the next
  item step after plan 0010 and reuses its harness. Waits for the owner's approval.
