# 0019 — Items: unique and set selection, and the creation fallbacks

> **Status:** in-progress (approved 2026-10-14)
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
- **2026-10-14 — Approved (human).** No changes to the draft. Phase 0 (archivist) is next.
- **2026-10-14 — Phase 0 landed (archivist).** `python3 -I tools/unique_survey.py workspace/merged/data/global/excel`
  prints the UniqueItems row classes with the ranges of `version`, `enabled`, `ladder`, `carry1`, `rarity`, `lvl`,
  `lvl req`; the rows to skip; every base code with its unique and set candidates (record, `lvl`, `rarity`,
  `version`, `enabled`); the bases with more than one candidate; and the duplicated `index` names. New
  [Sets](../tables/Sets.md) doc and a partial `sets` layout in `tools/excel_layouts.py`: `excel_bin.py diff … sets`
  0 mismatches over 96 cells (`excel_layout` gate baseline updated). Generation sections added to
  [UniqueItems](../tables/UniqueItems.md#generation-columns) and [SetItems](../tables/SetItems.md#generation-columns).
  All counts `[C]` by script, meanings `[L]`. Surprises: `sets.bin` has no `level` field (every `SetItems.lvl`
  equals its set's `level`, 127/127); `setitems` has no version column, so a set item's version is only its set's;
  `Darkfear` (346, `ulm`) has a base code but blank `enabled` and `lvl`; the six classic quest uniques (123..128)
  have `lvl` 0. Multi-candidate bases: uniques `amu` 12, `rin` 10 (9 enabled), `jew` 8 (all `Rainbow Facet`),
  eight more with 2; sets `amu` 9, seven more with 2. Backlog: `sets.bin` zero slots and the missing `level`
  (→ reverser, Phase 1).
- **2026-10-14 — Phase 0 accepted (architect).** Reran `tools/unique_survey.py` (bases with several candidates: `amu` 12 + 9 set, `rin` 10 (9 enabled) + 2, `jew` 8; duplicated `Rainbow Facet` ×8 and `Azurewrath` ×2) and `excel_bin.py diff … sets` (96 cells, 0 mismatches). Note for Phase 1: a set item has no version, enabled or level of its own in the data, and `sets.bin` has no `level` field; the backlog entry on the zero slots goes with Phase 1. Phase 1 (reverser) is next.
- **2026-10-14 — Phase 1 landed (reverser).** [items/0004](../findings/items/0004-uniques-sets.md), all `[I]` from
  Ghidra decompiles checked against r2 disassembly, except the `sets.bin` member count and pointers, which are `[C]` by
  writer/reader agreement. 51 `re/symbols.csv` rows (`items/uniques-sets`). New `re/types/uniquesets.h` (unique, set
  item and set records as loaded, the creation record); `Game+0x1B24`, `ItemData+0x10`/`+0x28` and the DataTables
  set/unique pointers added. Done-when, by bullet: the candidate filters and their test order (§§ 3.2, 4); the pick
  is one draw on the **item** seed (`low % Σrarity`), the first draw on that seed for a drop, with no draw when a
  TC-named row passes the filter (§§ 1, 3.2, 4); the exits, the durability step and the chain, each step reseeding
  `{S, 666}` (§§ 3.3, 5); the six pre-switch helpers (§ 2); the TC-named unique and its duplicate rule (§ 6);
  `sub_00556F60_ItemRollQualityCreate` runs on every drop but returns without drawing (§ 1); the boundary, recommended
  in § *Boundary for Phase 2*: model up to the builder chain's return, with `sub_0065FEC0_ItemApplyProps` and the
  rare, magic, superior and normal builders as ADR-0004 oracles; the post-switch ethereal, socket and automagic steps
  lie outside. Surprises: a unique row already built in the game (bit set at `Game+0x1B24`) fails the build after the
  pick, with no re-pick, so the item falls back to rare. Ladder-only uniques are candidates in single player and
  TCP/IP (`Game+0x6A` ≠ 0). A TC-named unique is only a preference that must pass the `lvl` ≤ ilvl filter. Set
  items have no once-per-game, `enabled` or ladder test, and the version they are tested on is their set's, copied in
  at load. Set 29 (Cow King) needs a `hellbovine` source. A unique can be ethereal, a set item cannot. Backlog:
  answered the archivist's `sets.bin` entry; new entries → archivist (table-doc slots and tests) and → spec-writer
  (quality § F refinement). Phase 1 goes to the architect for review and the boundary ruling.
- **2026-10-14 — Phase 1 accepted, boundary ruled (architect).** items/0004 meets every *Done when* bullet: 2 `[C]` (the `sets` member count and member pointers: a loader write and two readers, second code path per evidence-rules), 49 `[I]`, 3 `[L]`. **Ruling: the boundary as recommended.** Modelled: from the entry of `ItemCreateByQuality` to the return of the builder chain, covering the overrides, the filter, the pick draw on the item seed, the made-uniques bitset at `Game+0x1B24`, the durability step and the `{S, 666}` reseeds. ADR-0004 oracles: `sub_0065FEC0_ItemApplyProps` (`items/properties`) and the rare, magic, superior and normal builders (`items/affixes`), with the item seed asserted at each oracle entry. The ethereal, socket and automagic steps after the switch are out of scope. Required Phase 2 cases, in addition to the *Done when*:
  - **(a)** a unique already made in this game, which fails after the pick and falls back to rare;
  - **(b)** a TC-named unique, if any TC the run reaches names one: it must pass `lvl` ≤ ilvl;
  - **(c)** a ladder-flagged unique picked in a single-player game, since `Game+0x6A` ≠ 0.

  The scratch-read list of stock rows reaching the overrides stays `[L]` until a committed survey or the run covers it. Phase 1b (reverser, web only) is next.
- **2026-10-14 — Phase 1b landed (reverser).** [items/0004 § Leads used](../findings/items/0004-uniques-sets.md#leads-used): 30 verdicts, written after the finding (blind first). Sources: `src:d2dfg-blizzard` re-fetched (§ UniqueItems.txt, § SetItems.txt, § Sets.txt; its season and Diablo-clone columns show it describes D2R), and new `src:pk-uniqueitems-guide`, `src:pk-setitems-guide`, `src:pk-sets-guide`, `src:arreat-summit-item-pages`, `src:maxroll-d2r-items` (D2R) and `src:fandom-d2-unique-set`. `src:pd-item-generation-tutorial` (PureDiablo tutorial and wikis) was not read: HTTP 403 on every fetch. No page had game code, and none was rejected. Results: 8 `held`, 16 `held with refinement`, 3 `not covered`, 3 `contradicted`. No source covers the pick's seed and single draw, the TC-named preference, the pre-switch overrides or the `{S, 666}` reseed. The once-per-game rule, the ×3/×2 durability (cap 255), failed unique → rare, failed set → magic, ladder rows in single player and TCP/IP, `lvl` against ilvl, the weighting by `rarity` and the absent set `level` all held, some with refinements (no re-pick after a marked row, the chain past rare, set 29 tested by the source monster). **Contradicted, all required Phase 2 cases** (backlog 2026-10-14 reverser → reverser):
  - **(c)** the D2R ladder-season columns: 1.14d has one `ladder` bit, ignored when `Game+0x6A` ≠ 0. This is the case (c) already ruled at the Phase 1 review;
  - **(d)** a TC-named row with `enabled` 0 "can still drop": in 1.14d it must pass `enabled` before it is preferred. No stock TC names a disabled row, so a TC edited to name `Azurewrath` (row 29) on a modded data set, or a second code path, settles it;
  - **(e)** "`rarity` only works in Expansion mode": 1.14d weights classic games too. Log a classic-game unique on `rin` (15/15/1) or `amu` (20/5/10).

  (d) and (e) were re-read with r2 (`0x00556878`–`0x005569A0`), with no change: nothing in the finding is corrected and every tag stays as it was. One gap was added under *Open questions*: whether a `nolimit` or quest unique is identified after the builder (no stock row reaches it). Phase 1b goes to the architect for review.
- **2026-10-14 — Phase 1b accepted (architect).** 30 verdicts: 8 held, 16 held with refinement, 3 not covered, 3 contradicted, none of them an error in the finding (cases (d) and (e) re-read with r2). `src:d2dfg-blizzard` is now identified as describing D2R (its ladder-season and `diablocloneweight` columns), so its claims are later-build claims, not 1.14d. The PureDiablo 1.11 tutorial could not be fetched (HTTP 403, no archive); the searches are recorded. Rulings on the contradicted claims:
  - **(c) ladder:** the same as case (c) of the Phase 1 ruling; required.
  - **(d) a TC-named `enabled` = 0 row:** unreachable with stock data. Not a Phase 2 case, stays `[I]`, goes under the spec's *Open questions*.
  - **(e) `rarity` weighting in a classic game:** required. Needs a classic-game unique on a base with several candidates (`rin` or `amu`).

  Process note: the lane wrote downloads into the main checkout (`pk/`) through a relative path. It moved them to its scratchpad on request, and nothing was committed. Phase 2 (reverser, harness) is next, after plan 0017 Phase 2 releases display :7.
- **2026-10-14 — Phase 2 ruling (architect, owner-approved): forced-path run.** The stock Eldritch run (31 Hell sessions,
  MF 458, 304 creations, 0 mismatches) gave 1 unique and 3 set builds, about 0.13 per session. Under
  [ADR-0010](../adrs/0010-forced-path-runs.md) Phase 2 adds `run:YYYY-MM-DD-uniques-forced`: a loose ItemRatio `.bin` under
  `-direct` (no `-txt`) raises the unique and set outcomes; UniqueItems, SetItems, the bases and every other table stay
  stock and are shown so in the record. First show from the Phase 1 reads that the builders and fallbacks never read
  ItemRatio. The Done-when counts (≥30 unique and ≥30 set builds, the failures and fallback chains, cases (a), (c), (e))
  may come from the forced run; the stock run stays in the record as the stock-data corroboration, and any claim about
  how often a quality comes up keeps citing stock runs only. Case (e) (`rarity` in classic) needs a classic forced
  session too.
- **2026-10-14 — Phase 2 landed (reverser).** Two runs, both with 0 mismatches against `tools/uniques.py`, the model
  of `ItemCreateByQuality` up to the builder chain's return with the ruled ADR-0004 oracles:
  - [run:2026-10-14-uniques](../findings/items/experiments.md#run2026-10-14-uniques), stock: 30 Eldritch sessions,
    expansion Hell, 304 creations, 1 unique and 3 set builds;
  - [run:2026-10-14-uniques-forced](../findings/items/experiments.md#run2026-10-14-uniques-forced), ADR-0010, only
    `itemratio.bin` edited: 54 sessions, 1 519 creations, 115 unique and 72 set builds over expansion Hell,
    Nightmare and Normal and classic Nightmare.

  The same logs replay through `tools/tc.py` and `tools/quality.py`. The quality roll reproduces only with the
  edited ItemRatio loaded, which shows that the game loaded it and that the TC, item and type tables are stock.
  [items/0004](../findings/items/0004-uniques-sets.md) § 9 states the precondition: nothing on the builder path reads
  ItemRatio. § 10 gives the results.

  Done-when, by bullet:
  - ≥ 30 unique and ≥ 30 set builds, classic and expansion, ≥ 2 difficulties: met;
  - multi-candidate bases: unique `rin` in classic and expansion, set `amu` (9 candidates);
  - no TC-named pick, so no duplicated `index` either;
  - each builder failed with its fallback: unique → rare 39 times (38 no candidate, 1 already made), set → magic
    47 times, each with the durability step and the `{S, 666}` reseed. The fallback builders always succeeded, so the
    chain past the first step was not reached;
  - overrides: on drops through the quality roll none changes the quality. Only `Normal` → 2 wrote, always over 2;
  - the seed after each builder matched.

  Cases:
  - (a) a repeated unique in one game (classic `brs`, row 86) failed and fell back to rare;
  - (b) out of reach: the only TC cells naming a unique are `Annihilus` in `ROP (N)`/`ROP (H)`;
  - (c) ladder rows 290 and 317 were picked in single player;
  - (e) classic `rin` 120/121/122 at 15/15/1, r = 20 of 31 → 121.

  Promoted to `[C]`: the item-seed placement, the filters, the pick, the made-uniques set, the durability step and the
  fallback reseeds. 12 `re/symbols.csv` rows. Still `[I]`: the forced row, set 29, a quest base, a `unique`-flag base
  with no candidate, the chain past the first fallback, the override order.

  Remaining oracles: `ItemApplyProps` (`items/properties`) and the rare, magic, superior, low and normal builders
  (`items/affixes`).

  Tooling:
  - `tools/excel_edit.py`: writes a forced table, edited through the excel layout;
  - `tools/d2s.py build`: magic-suffix items, a belt fill per column, hotkeys;
  - `tools/d2pilot.py farm`: the Eldritch loop. The earlier agent's warp, findwarp and fight commands are gone. The
    Mephisto attempts were stopped by the owner and are not in the record.

  Phase 2 goes to the architect for review.
