# 0021 — Items: affix level, magic and rare affixes, automagic

> **Status:** in-progress (approved 2026-10-14)
> **Created:** 2026-10-14
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** once an item's quality is 4 (magic) or 6 (rare), or a unique or set build has fallen back to one of
them, which `MagicPrefix`, `MagicSuffix`, `RarePrefix` and `RareSuffix` rows does it get, and in which draw order?
And which `AutoMagic` row does an expansion item get after the quality switch?
[items/0004](../findings/items/0004-uniques-sets.md) § 5 and § 8 name the entry points only:
- the magic builder `sub_005565E0_ItemBuildMagic` (pick at `0x005C18E0`, or the record's forced affixes at
  `+0x68`/`+0x74`);
- the rare builder `sub_005C21A0_ItemBuildRare` → `0x005C1BF0`;
- the superior builder `sub_005C2AD0_ItemBuildSuperior` and the normal builders, not read;
- the automagic step after the switch (base group `+0xF8`, `0x005C1940`).

Plan 0019 takes these builders as ADR-0004 oracles, with the item seed asserted at each entry. This plan reads them,
models the affix level (alvl), the candidate filter, the weighted picks, the rare affix count and name rolls, and
the automagic pick in `tools/affixes.py`, and replaces those oracles. When it is done:
- `docs/findings/items/0005-affixes.md` has the selection at `[C]` for the logged cases;
- `docs/specs/items/affixes.md` is drafted.

The *values* of an affix's properties (`mod1code`..`mod3code` with their min/max) are `items/properties`: the
boundary is the chosen row ids, and the property roll stays an oracle with the item seed asserted.

## Context

- Research-map row `items/affixes`, `not started`. Dependencies:
  - `rng` reviewed, `items/tc` reviewed, `items/quality` reviewed (C 61 / I 36 / L 4);
  - `items/uniques-sets` findings `[I]` (items/0004, Phase 1 and 1b accepted); its Phase 2 is running and logs each
    fallback builder's entry and exit seed. Phase 3 here waits for the `items/uniques-sets` spec (plan 0019 Phase 3).
- Code already named, all `[I]` from the decompile:
  - `sub_00558D90_ItemCreate` → `sub_00557450_ItemCreateByQuality` (cases 3, 4, 6; the fallback chain);
  - `sub_005565E0_ItemBuildMagic`, `sub_005C21A0_ItemBuildRare`, `sub_005C2AD0_ItemBuildSuperior`,
    `sub_00557250_ItemClearAffixes` (3 prefixes, 3 suffixes, two rare names, file index);
  - the fallback helpers `sub_005573F0_ItemFallbackRare`, `sub_00557380_ItemFallbackMagic`,
    `sub_00557320_ItemFallbackSuperior`, `sub_005572A0_ItemFallbackNormal`, each reseeding `{S, 666}`;
  - the pre-switch helpers `sub_0062E9E0_ItemTypeMagic`, `sub_0062E990_ItemTypeRare`, `sub_0062A0F0_ItemQualityMagicPlus`;
  - unread: `0x005C18E0` (magic pick), `0x005C1BF0` (rare builder), `0x005C1940` (automagic);
  - from other subsystems: `ITEMS_SetAutoAffix` 0x00627F50 and `g_MagicAffixInfo` 0x0096CA7C (save/0001),
    `sub_00633EE0_MagicAffixRecord` (items/0003).
- Item seed: on a drop the builder entry seed is `{ItemData+0x10, 666}` (items/0004 § 5), a value rng/0002 models.
  So every affix draw sits on a seed whose state the model already knows.
- Data: none of the five affix tables has a doc. [tables/README](../tables/README.md) lists them:
  - `magicprefix` (669 rows) and `magicsuffix` (747 rows), `.txt` and `.bin` both from patch_d2;
  - `automagic` (36), `RarePrefix` (46) and `RareSuffix` (155) are **mixed-archive tables**: the `.txt` is from d2exp and
    the `.bin` from patch_d2. A stock run loads the `.bin` ([excel-bin § Mixed-archive tables](../formats/excel-bin.md#mixed-archive-tables-automagic-rareprefix-raresuffix)).
  - [ItemTypes](../tables/ItemTypes.md) gives the `Equiv1`/`Equiv2` chains that `itype`/`etype` test, and the `Magic`,
    `Rare` and `MaxSock*` columns; [Weapons](../tables/Weapons.md), [Armor](../tables/Armor.md) and
    [Misc](../tables/Misc.md) give `level` (qlvl), `magic lvl` and `auto prefix`.
- Harness: `tools/gdb/tc-drops.gdb`, `tools/quality.py` and the `tools/uniques.py` of plan 0019 Phase 2. Magic and
  rare drops are by far the most common qualities, so a short run yields hundreds of builds.
- Why now: this is the next link of the item chain after quality and uniques/sets, and it removes the largest
  remaining oracle on the drop path. `items/vendors` and `items/cube` depend on it.
- Leads: `src:d2dfg-blizzard` (registered; it describes D2R, so its claims are later-build claims). Item affixes have
  the widest community coverage of any subsystem (alvl formula, the 3+3 rare cap, `group` exclusivity), so Phase 1b is
  required.

## Phases

### Phase 0 — Affix tables
- **Owner skill:** archivist
- **What:** document the five affix tables and their `.bin` layouts, and survey the candidates per item type.
- **Outputs:**
  - `docs/tables/MagicPrefix.md`, `MagicSuffix.md` (one shared schema doc is fine if the layouts agree),
    `RarePrefix.md`, `RareSuffix.md`, `AutoMagic.md`: column schema, `.bin` field offsets, value ranges, label and
    blank rows. The generation columns at least: `spawnable`, `rare`, `level`, `maxlevel`, `levelreq`,
    `classspecific`, `class`, `classlevelreq`, `frequency`, `group`, `itype1..7`, `etype1..5`, `version`. The `mod*`
    columns are noted as `items/properties`;
  - for the mixed-archive tables, which columns differ between the d2exp `.txt` and the patch_d2 `.bin`;
  - `tools/excel_layouts.py` entries and the `excel_layout` gate baseline regenerated by rerunning its survey;
  - a `tools/` survey command.
- **Done when:** `excel_bin.py diff` passes on all five tables, and one command prints, for a given item type and
  level, the candidate rows of each table (row, `level`, `maxlevel`, `frequency`, `group`, `version`, `spawnable`,
  `rare`) after expanding the `itype`/`etype` lists through the ItemTypes equivalence chains. Meanings stay `[L]`.

### Phase 1 — Read the affix builders
- **Owner skill:** reverser
- **What:** read the magic, rare, superior and normal builders and the automagic step, then choose the boundary for
  Phase 2.
- **Outputs:** `docs/findings/items/0005-affixes.md`, `re/symbols.csv` rows (subsystem `items/affixes`, giving
  `ITEMS_` names to the `sub_` ones it settles), `re/types/` additions if an affix record is recovered.
- **Done when:** the finding states, with addresses and `[I]` or better:
  - **alvl:** how the affix level is derived from ilvl, the base's qlvl and `magic lvl`, with the exact integer
    arithmetic (clamps, rounding, the order of the tests);
  - **the candidate filter** of each table: `spawnable`, `rare`, `version` against the item version, `level` and
    `maxlevel` against alvl, `itype`/`etype` through the type chains, `classspecific`/`class`, `group`
    exclusivity with affixes already on the item, and the order of the tests;
  - **the weighted pick:** the seed, the range (sum of `frequency`, or otherwise), and the draw count per affix;
  - **magic:** how the prefix/suffix/both choice is drawn, and the forced-affix path (`+0x68`/`+0x74`);
  - **rare:** the affix count draw (how many prefixes and suffixes, the caps), the order of prefix and suffix picks,
    retries on a failed pick, and the two name rolls (`RarePrefix`, `RareSuffix`) with their filter;
  - **superior and normal (and low):** whatever they draw on the item seed;
  - **automagic:** the group at the base's `+0xF8`, the pick, its seed, and which qualities and versions get it
    (items/0004 § 8 says all but 5 and 7 in expansion);
  - where each builder's draws sit relative to `sub_0065FEC0_ItemApplyProps` and the post-switch ethereal and
    socket rolls;
  - **the boundary decision** for Phase 2: which callees (the property roll above all) are ADR-0004 oracles.
    Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch `src:d2dfg-blizzard` (§ MagicPrefix.txt, § MagicSuffix.txt, § RarePrefix.txt, § RareSuffix.txt,
  § AutoMagic.txt), and search for and register community documents on affix generation (alvl, rare affix counts,
  `group`). Compare blind, per `evidence-rules.md` § Community cross-checks. Downloads go to the scratchpad only.
- **Outputs:** `docs/sources.md` entries or a "none found" note with the searches made; verdicts in the finding's
  *Leads used*.
- **Done when:** each claim about alvl, the filter, the weighting, the magic choice, the rare counts and caps, the
  rare names and automagic carries a verdict with a `src:` id or `not covered`. Every `contradicted` claim is a
  required case of Phase 2, unless the architect rules it unreachable with stock data.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md);
  a human may play)
- **What:** write `tools/affixes.py` and chain it after `tools/uniques.py`, replacing plan 0019's builder oracles; log a
  new run and rerun the run:…-uniques logs of plan 0019 Phase 2 with the oracles replaced.
- **Logging:** extend `tools/gdb/tc-drops.gdb`: on entry to each builder, the item's base, ilvl, alvl inputs, version
  and seed state; each candidate the filter keeps with its weight; each pick draw; the rows chosen; the rare count
  draws and the name rows; the automagic pick; the seed at each property-roll entry and exit.
- **Done when:** a run `run:YYYY-MM-DD-affixes` shows, with 0 mismatches against the model:
  - at least 200 magic and 100 rare builds from drops, over classic and expansion and over at least two difficulties;
  - every rare affix count the code can draw, and at least one rare with a failed or retried pick if the code has one;
  - at least one base whose type has no eligible affix for a slot, and what follows;
  - at least one `classspecific` affix on a class item, and automagic on a class item (expansion);
  - the forced-affix path if a drop reaches it, or a statement that the drop path cannot;
  - the Phase 1b cases.

  The item seed after each builder matches the log. Any boundary that remains (the property roll) is named in the
  record. In-scope claims go to `[C]` citing the run.

### Phase 3 — Spec: items/affixes
- **Owner skill:** spec-writer
- **What:** write `docs/specs/items/affixes.md` and link it from the items README chain after `items/uniques-sets`.
- **Done when:**
  - the spec follows the template and every statement is tagged;
  - it gives alvl as exact integer arithmetic, the filter as an ordered test list, and the RNG call sequence of a
    magic build, a rare build and the automagic step;
  - it has worked examples of one magic item, one rare item and one automagic pick, all taken from the run;
  - it starts after the items/uniques-sets spec (plan 0019 Phase 3) is drafted;
  - the architect's review passes.

## Open questions

- Affix property values (`mod*code`, `mod*min`, `mod*max`) are `items/properties`. Only which rows are chosen is in
  scope; the property roll is an oracle until that row exists.
- Vendors, gambling, the cube (rerolls, crafted items) and imbue reach the same builders by other paths
  (`items/vendors`, `items/cube`). This plan specifies the builders as reached from a drop.
- Crafted (quality 8) and the `tempered` quality 9 builders: items/0004 names their chains only. Phase 1 says whether
  a drop can reach them; if only the cube can, they are named and deferred to `items/cube`.
- The mixed-archive tables: a game started with `-direct -txt` would load the d2exp `.txt`. Out of scope, since the
  stock run loads the `.bin`.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-14 — Drafted and approved (architect, on the owner's instruction "draft all three then approve").**
  Picked as the next link of the item chain after plans 0010 and 0019. Phase 0 (archivist) can start now; the
  reverser phases wait until plan 0019 Phase 2 releases Ghidra and display :7.
- **2026-10-14 — Phase 0 landed (archivist, branch `lane/a0021p0`).** New table docs: [MagicPrefix](../tables/MagicPrefix.md)
  (one shared schema doc for MagicPrefix and MagicSuffix, whose layouts agree; [MagicSuffix](../tables/MagicSuffix.md)
  points to it), [RarePrefix](../tables/RarePrefix.md) (shared with [RareSuffix](../tables/RareSuffix.md)) and
  [AutoMagic](../tables/AutoMagic.md), with the README rows. `tools/affix_survey.py`: `columns <table>`, `summary`, and
  `candidates <type-or-base> <level>` (expands the type through `Equiv1`/`Equiv2`, keeps rows with an `itype` in the set
  and no `etype`, and for the magic tables `level` ≤ L ≤ `maxlevel`; prints row, `level`, `maxlevel`, `frequency`,
  `group`, `version`, `spawnable`, `rare`, the class columns and `mod1code`; for a base, its `auto prefix`).
  - **Layouts:** `excel_bin.py diff` passes on all five: `magicprefix` 669 × 40 = 26 760 cells, `magicsuffix` 747 × 38 =
    29 880 (+1 494 absent-column cells), `rareprefix` 46 × 12 = 552, `raresuffix` 155 × 12 = 1 860, `automagic` 36 × 37
    = 1 440 (+108), 0 mismatches. Uncovered bytes: `+0x057` (magic record) and `+0x000..+0x00F` (rare record), 0 in
    every record. The layouts were already in `tools/excel_layouts.py` (plan 0002), so neither it nor the
    `excel_layout` baseline changed; `gate.py --full` green.
  - **The two forms:** for `automagic`, `RarePrefix` and `RareSuffix` (d2exp `.txt`, patch_d2 `.bin`) no compiled cell
    differs; the differences are the record format (132/60 → 144/72 bytes, type indices u8 → u16), the columns the
    `.txt` lacks (`automagic` `classspecific`, `etype4`, `etype5`: defaults in the `.bin`) and the `.txt` columns no
    field carries (`transform`; rare `version`, `add`, `multiply`, `divide`).
  - **Surprises:** `magicprefix` record 0 is blank but `magicsuffix` record 0 is a real row, against a save's
    "suffix 0 = none"; a stored rare `name1` of 160 exceeds both rare tables; every `version` 0 magic row has
    `frequency` 0; `classspecific` is used only by prefixes (group 125) and `class`/`classlevelreq` only by suffixes
    (group 44, `charged`); 27 suffix rows and `rareprefix` `Warp`/`Rift` name no `itype`; `magicsuffix` and
    `automagic` carry `0xFFFF` in `etype4`/`etype5`; `automagic` group 301 is named by no base. All meanings stay
    `[L]`; questions in the backlog (archivist → reverser).
- **2026-10-14 — Phase 0 accepted (architect).** Five layouts diff clean (the layouts predate this plan, from plan 0002; the
  excel layout baseline is unchanged); `tools/affix_survey.py candidates` meets the Done-when, and its eligibility rule (itype
  in the `Equiv` closure, no etype, `level`/`maxlevel`) stays `[L]` until Phase 1 reads the filter. Required Phase 1
  questions: how merged affix ids map to records (magicprefix record 0 blank, magicsuffix record 0 a real row), the rare
  `name1` of 160 past both rare tables, whether `frequency` 0 version-0 rows can ever be picked, the `0xFFFF` defaults in
  absent `etype` columns, and automagic group 301. Phase 1 (reverser) is the next Ghidra session after plan 0019 Phase 2.
- **2026-10-14 — Phase 1 and Phase 1b landed (reverser, branch `lane/r0021p1`).** [items/0005](../findings/items/0005-affixes.md),
  all `[I]` from the decompile and the disassembly; 54 `re/symbols.csv` rows under `items/affixes` (the builders get
  `ITEMS_` names: `ITEMS_BuildMagic`, `ITEMS_BuildRare`/`ITEMS_BuildRareAffixes`, `ITEMS_BuildSuperior`,
  `ITEMS_BuildLow`, `ITEMS_BuildNormal`, `ITEMS_PickMagicAffix`, `ITEMS_PickRareName`), `re/types/affixes.h`.
  - **Read:** ids are the merged index + 1 (suffix, prefix, automagic; rare suffix, rare prefix). alvl =
    `max(ilvl, qlvl)` then `+ magic lvl`, or `− qlvl/2` below `99 − qlvl/2`, else `2·i − 99`; clamp 1..99. One pick =
    a step whose bit 0 decides "roll" (unless forced to), the ordered filter, then `low % (W + 1)` over `frequency`
    weights (`× level` on `magic lvl` bases), a draw of W taking the last candidate. Magic: prefix pick, then a suffix
    pick that must roll if no prefix. Rare: two names first, count `{3,4,4,5,5,5,6,6}[low & 7]` (jewels 3–4), one side
    bit per slot, a failed pick closes its side and the slot is retried, 3 per side. Automagic after the ethereal and
    socket rolls, expansion only, not on 5 or 7. Superior: rejection sampling over `QualityItems`; low: one
    `RNG_Range`; staff mods at the end of every builder but normal. Crafted (8) and quality 9 do not occur on drops.
  - **Phase 0 questions** answered in the finding's table; the archivist entry is struck.
  - **Boundary recommended:** model every selection; oracles `sub_0065FEC0_ItemApplyProps` and `ITEMS_RollStaffMods`.
  - **Phase 1b:** `src:d2dfg-blizzard` re-read, new `src:arreat-summit-magic-items`, `src:arreat-summit-item-pages`
    re-read; `src:lurker-affix-threads` refused every fetch. Four `contradicted` (the "qlvl ≤ ilvl + 2" uniform rule,
    "2 to 6" rare properties, rare names tied to affixes, automagic `spawnable`), backlog reverser → architect; the
    rest held or held with refinement.
  - **Merge note:** `docs/specs/items/uniques-sets.md` on `main` cites four of the renamed builders; see the review
    entry in the backlog.
