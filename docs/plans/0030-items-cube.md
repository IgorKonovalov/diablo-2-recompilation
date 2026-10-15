# 0030 — Items: the Horadric Cube (recipe matching, input checks, output construction)

> **Status:** in-progress (approved 2026-10-15)
> **Created:** 2026-10-15
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0010-forced-path-runs, 0011-harness-slots

## TL;DR

**Question:** when the player presses Transmute, which CubeMain row matches the cube's contents, and what item (or
portal) comes out, with which ilvl, quality, affixes, sockets and seed? Recipes are an item creation path (ADR-0002):
crafted items (quality 8), rerolled magic and rare items, rune and gem upgrades, socket recipes, the uniques made by
recipe, and the portals (the cow level; the Pandemonium portals). When it is done:
- `docs/tables/CubeMain.md` is a table doc, with the compiled input and output encoding;
- `docs/findings/items/0008-cube.md` names the transmute handler, the match, the input checks, the output builder per
  output kind and the special outputs;
- `tools/cube.py` predicts a transmute's output from the cube's contents and the seeds, chained into the item model
  (`tools/items_chain.py`);
- `docs/specs/items/cube.md` is drafted.

## Context

- Research-map row `items/cube`: `not started`. Dependencies: `items/properties` and `items/affixes` reviewed;
  `data/excel` reviewed. [Plan 0029](0029-items-sockets-runewords.md) (sockets) runs first: socket recipes and
  runeword bases read its model.
- Code already named:
  - the CubeMain loader `0x00669130` (cubemain 328 B per record, loaded at `0x0066A184`); it aborts with a fatal error
    if a `cubeserver` table exists (`0x0066A110`, `0x0066A164`). **cubemod and cubetype are never loaded**
    ([data/0001](../findings/data/0001-excel-loader.md)), so this row has one table.
  - `sub_00565AB0_RecipeOutputCreate` (`[L]`) clears a unique's made bit after creating it
    ([items/0004](../findings/items/0004-uniques-sets.md)).
  - `sub_005C21D0_ItemBuildCrafted` and `sub_005C1BC0_PickRareNameByVersion`
    ([items/0005 § 11](../findings/items/0005-affixes.md), qualities 8 and 9: "items/cube material").
  - Cube outputs are created into an inventory, so they are in no room list ([save/0001](../findings/save/0001-d2s-io.md)).
- Open runtime issue: the Pandemonium key transmute did nothing in single-player Hell
  ([drlg/experiments](../findings/drlg/experiments.md), [drlg/0008](../findings/drlg/0008-outdoor.md)).
  [Plan 0027](0027-backlog-sweep-3.md) Phase 2 reads the refusal. This plan takes its answer and does not repeat it.
- Harness: `tools/d2s.py build` puts items in the cube (`keynova.json` precedent). The `tbk` tome crash is fixed by
  plan 0027 Phase 1; this plan needs that fix for the cow portal recipe. Nothing in `tools/d2pilot.py` opens the cube or
  presses Transmute.
- Leads: `src:d2dfg-blizzard` (§ CubeMain.txt), `src:arreat-summit-magic-items` (crafting is not covered there, so
  search), `src:pd-sockets` (the socket recipes). Cube recipes are thoroughly documented by the community, so Phase 1b
  is required.

## Phases

### Phase 0 — CubeMain, and cube saves
- **Owner skill:** archivist
- **What:** document `cubemain`, its `.bin` layout and how the text input and output cells (`"rin,qty=3"`, `"usetype,
  crf"`, `"Cow Portal"`) compile into the record; build the cube recipe saves.
- **Outputs:**
  - `docs/tables/CubeMain.md`: every column (`enabled`, `ladder`, `min diff`, `version`, `op`/`param`/`value`,
    `class`, `numinputs`, `input 1..7`, `output`, `lvl`, `plvl`, `ilvl`, `mod 1..5` with `chance`/`param`/`min`/`max`,
    and `output b`/`output c`), the compiled input record (item or type code, quantity, the qualifier flags `nos`,
    `sock`, `noe`, `eth`, `upg`, `bas`, `exc`, `eli`, `nru`, quality), the output record (the special codes `useitem`,
    `usetype`, the portal outputs, quality forcing, `pre=`/`suf=`, `sock=`, `rem`, `rep`, `rch`, `reg`, `mod`), and a
    survey: rows by output kind, `enabled`/`ladder`/`version` counts;
  - a note that cubemod and cubetype are not loaded, citing data/0001;
  - `tools/excel_layouts.py` entry and the regenerated baseline;
  - recipes in `tools/d2s_recipes/`, one per recipe class, each with the inputs of several transmutes in the inventory
    and the first transmute's inputs in the cube: `cuberunes.json` (rune and gem upgrades), `cubereroll.json`
    (the 3-perfect-gem magic reroll, the 6-perfect-skull rare reroll), `cubecraft.json` (each of the four crafting
    families with jewels and the required base types), `cubesock.json` (socket recipes), `cubeportal.json` (Wirt's
    Leg and a tome of Town Portal), and `cubeclassic.json`.
- **Done when:** `excel_bin.py diff` passes with 0 mismatches and no uncovered bytes; every input and output cell of
  the stock table is decoded by the survey with no unexplained form; each recipe builds and its save loads.

### Phase 1 — Read the transmute
- **Owner skill:** reverser
- **What:** read the server's transmute handler from the client packet to the outputs, and the output builder.
- **Outputs:** `docs/findings/items/0008-cube.md`; `re/symbols.csv` rows (subsystem `items/cube`,
  `RecipeOutputCreate` re-read); `re/types/` additions (the compiled CubeMain record).
- **Done when:** the finding states, with addresses and `[I]` or better:
  - **the match:** the row scan order, how `enabled`, `ladder`, `min diff`, `version` and `op`/`param`/`value` (the
    stat conditions) filter, how the cube's items are matched against inputs (item vs type, quantity, the qualifier
    flags, a stack counted as one or many), whether extra items in the cube refuse a match, and what happens when no
    row matches;
  - **the outputs, per kind:** `useitem` (the input item kept and modified), `usetype`, a fixed code, quality forcing
    (magic, rare, crafted, unique by name, set by name), `lvl`/`plvl`/`ilvl` (the output's ilvl arithmetic from the
    player's level and the inputs' ilvls), the `mod` lines with their `chance` draws, `sock=`, `pre=`/`suf=`, `rem`
    (remove sockets or affixes), `rep`/`rch` (repair, recharge), `reg`, ethereal, and the inputs destroyed or kept;
  - **the draws:** for each output kind, which seeds are drawn (the game seed for the new item's seed, the item's own
    seed for its rolls), in order, and where the existing item model (quality, affixes, uniques-sets, properties) is
    entered; `sub_005C21D0_ItemBuildCrafted` in full;
  - **the special outputs:** the cow portal, the Pandemonium and Uber portals (with plan 0027's refusal answer), and any
    other non-item output, named with their preconditions;
  - **`RecipeOutputCreate`'s** made-bit clear moves off `[L]`;
  - **the boundary decision** for Phase 2. Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch `src:d2dfg-blizzard` § CubeMain.txt and search for and register crafting and recipe documentation
  (crafted item ilvl formula, crafted affix counts, the reroll recipes' ilvl, socket recipe socket counts, the cow
  portal conditions). Compare blind.
- **Outputs:** `docs/sources.md` entries; verdicts in the finding's *Leads used*.
- **Done when:** each claim carries a verdict; every `contradicted` claim reachable on stock data is a required case
  of Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md);
  at most two slots)
- **What:** write `tools/cube.py`, chained after `tools/items_chain.py`; a `tools/gdb/cube.gdb` logger; and a
  `tools/d2pilot.py cube` action (open the cube from the inventory, press Transmute, move the next inputs from the
  inventory into the cube, repeat). Then log a run.
- **Logging:** per transmute: the cube's contents (class, quality, ilvl, seed, flags), the row matched or none, every
  draw on every seed from the packet to the end, and each output's full item lines (with `affixes.gdb` and
  `props.gdb`, so `items_chain.py` checks the output end to end).
- **Done when:** a run `run:YYYY-MM-DD-cube` reproduces with 0 mismatches:
  - at least 150 transmutes, among them at least 40 crafted items (all four families), 20 magic rerolls, 10 rare
    rerolls, 20 rune or gem upgrades, 10 socket recipes, and 10 transmutes that match no row;
  - every output's item reproduced from the cube contents and the game seed at the packet, with no seed oracle
    between the match and the output;
  - the cow portal opened at least once (it needs plan 0027's tome fix; the Cow King must not be killed on the save, so
    the recipe sets the quest state accordingly), or named as a boundary with the reason;
  - a classic session, where the expansion rows are refused;
  - the Phase 1b cases.

  In-scope claims go to `[C]`, citing the run.

### Phase 3 — Spec: items/cube
- **Owner skill:** spec-writer
- **What:** write `docs/specs/items/cube.md`; link it from the items README, items/affixes § (qualities 8 and 9),
  items/uniques-sets (made bit), and drlg/outdoor (the cow level entry).
- **Done when:** the spec follows the template, and every statement is tagged. It has the match as pseudocode, a table
  of output kinds with their draws, and two worked examples from the run (a crafted item and a reroll). The
  architect's review passes.

## Open questions

- Ladder-only rows are refused offline (`ladder`); named, not forced.
- The Uber portals and Tristram need multiplayer or a realm in 1.14d, presumably. If Phase 1 confirms it, they are
  named boundaries (no multiplayer harness beyond ADR-0008).

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-15 — Drafted and approved.** The owner asked for a queue of plans to run unattended, and approved all of
  them in advance. Written in the architect worktree `lane/plans0028`.
