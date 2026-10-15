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
  `data/excel` reviewed. [Plan 0029](done/0029-items-sockets-runewords.md) (sockets) runs first: socket recipes and
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
- **2026-10-15 — Phases 1 and 1b landed (reverser, branch `lane/r30p1`).** [items/0008](../findings/items/0008-cube.md),
  read blind from the code (commit `a7f0073`) before any community source; column names from the raw `cubemain.txt`
  header (Phase 0 had not landed). The transmute is packet `0x4F` button `0x18` → `CUBE_Transmute`: a first-fit row
  scan (`enabled`, `version`, `ladder`, `min diff`, `class`, `numinputs` = cube item count, ops 1–14 on the player),
  then `CUBE_MatchInput` per input (each input claims every matching item; a stack counts one; ops 15–27 on input 1,
  op 28 on every input). Input 1 alone feeds all three outputs, with output A's flags. Output ilvl = `lvl`, else
  trunc(clvl·plvl/100) + trunc(ilvl·ilvl/100), clamped to [1, MaxLvl]. Created outputs go through `ItemCreate` with
  no socket or ethereal roll unless asked; `useitem`/`mod` copy input 1; `mod` lines draw a chance on the unit seed;
  `ItemBuildCrafted` read in full (count `max(low % 5, tier)`). If anything is produced the whole cube is destroyed and
  the outputs placed identified; otherwise nothing changes. Surprises: the two Pandemonium portal handlers are
  `xor eax, eax; ret` (the plan 0027 refusal; outcome `[C]` by run:2026-10-15-drlg-outdoor); ladder rows match in single
  player; the four rune socket recipes are all `sock` 1–6. Confidence: 2 `[C]` (one claim), 58 `[I]`. 41 symbols,
  `re/types/cube.h`. Phase 1b: `src:d2dfg-blizzard` § cubemain.txt and the new `src:arreat-summit-cube-crafted`; 29
  verdicts, nine contradicted, four reachable on stock data and listed as required Phase 2 cases in § 7 and the
  backlog; `src:pd-sockets` was behind a Cloudflare challenge and not compared. Boundary recommendation in § 7.
  Review requested.
- **2026-10-15 — Phase 0 landed (archivist, `lane/a30p0`), review requested.** [CubeMain](../tables/CubeMain.md):
  the 328-byte record (20-byte header, seven 8-byte inputs, three 84-byte outputs with five 12-byte mod lines each),
  0 mismatches over the stock table (24 764 cells) and no uncovered byte; every input and output cell decoded by
  `tools/cubemain.py` (the compiler model the layout check uses through the new `conv=` field option), survey
  `unexplained=0`, gate survey `cubemain`. The columns blank in every stock row and the keywords no stock row uses
  were placed by a **compile probe**: the game compiled a `cubemain.txt` with 81 probe rows under `-direct -txt`,
  and the same layout matches all 232 records ([run:2026-10-15-cube-saves](../formats/experiments.md#run2026-10-15-cube-saves)).
  Surprises: the stock `.txt` compiles to the shipped `.bin` byte for byte; an input head resolves as an item type
  before an item code and an output head the other way round (`axe`, `key`); output `qty=` and `sock=` share one
  byte; a 4th `pre=` spills into `suf1`; `useitem,reg` stores kind usetype; output `useitem,sock` without `=N`
  stops the compile; a skill name in a mod `param` is not looked up. `cubemod`/`cubetype` are not loaded (data/0001).
  Six recipes (`cuberunes`, `cubereroll`, `cubecraft`, `cubesock`, `cubeportal`, `cubeclassic`) build and load,
  and *Save and Exit* writes them back item for item (slot 1). `d2s.py build` gained rare items (`"rare"`) and the
  socket quality clamp (follow-up (b) of plan 0029 P0, opt-out `"unclamped_sockets": true`); SetItems moved to
  `names=` (follow-up (a)). Questions for Phase 1 in the backlog. No transmute was pressed; Phase 2 needs a
  `d2pilot.py cube` action.
- **2026-10-15 — Phase 2 landed (reverser, branch `lane/h30p2`; review requested in the backlog).**
  [run:2026-10-15-cube](../findings/items/experiments.md#run2026-10-15-cube): 29 sessions on slot 1, 182 transmutes,
  `python3 -I tools/cube.py check $(cat workspace/logs/cube-run.lst)` reproduces all with 0 mismatches.
  - Tools: `tools/gdb/cube.gdb` (uniques.py + props.py + the new `tools/gdb/cube.py`), `tools/cube.py` (chained after
    `tools/items_chain.py`), `tools/d2pilot.py cube` (tokens `mv`, `tm`, `out`), `tools/cube_sessions.py` (29 recipes
    `tools/d2s_recipes/cube-*.json`, plans `tools/gdb/cube-*.plan`, entry steps `cube-enter-*.steps`). Library
    additions: `affixes.py` Walk.crafted and forced picks, `uniques.py` hooks for the quality-0 creation roll and
    quality 8, `items_chain.py` forced ids, `d2s.py build` keys `quest_bits`, `item_stats`, `quest_diff` (with a test).
  - Coverage: 51 crafted (four families), 28 magic rerolls, 15 rare rerolls, 27 rune/gem upgrades, 16 socket recipes,
    16 no-row transmutes, the cow portal opened in Normal, Nightmare and Hell and refused by each expansion gate, a
    classic session (row 60 refused), and every output kind (fixed code, item type, usetype, useitem, mod, rep/rch,
    forced `pre=`/`suf=`, cow portal, both Pandemonium rows). No seed oracle between the match and any output; the cow
    portal's spot search and object creation are the only oracles.
  - Phase 1b cases: the ladder rows match in single player; op 28 passes on stat 356 = difficulty; the rune socket
    rows roll 1–6 on every class (capped by the base); the Pandemonium rows match and produce nothing.
  - New readings ([items/0008 § 8](../findings/items/0008-cube.md#8-phase-2-the-reproduction-run2026-10-15-cube)):
    the body of `sub_00556F60_ItemRollQualityCreate` and its second call inside the fallback helpers (the cube's
    quality-0 records draw there); `ItemCopy` takes two game-seed steps and gives the copy a fresh item seed (the open
    question closed); `CubePickItemOfType` re-read; forced ids are block-relative; row 63 refuses rings and amulets
    (socketable first-input test).
  - Tags: items/0008's match, inputs, slots, ilvl, outputs, crafted builder, cow gates and the new readings to `[C]`;
    11 `re/symbols.csv` rows raised to C. Not reached and still `[I]`: outputs B/C, `uns`/`rem`/`reg`/`tmp`, mod
    `chance`, ops 1–27, `eth`/`exc`/`eli` inputs, the classic cow test, the ethereal upgrade question.
- **2026-10-15 — Phase 2 reviewed (architect): accept with fixes**, fixes applied on `lane/h30p2`.
  - Rerun from the worktree: `tools/cube.py check` on the 29 logs of `cube-run.lst`, **182 transmutes, 0 failed**.
    All 29 sha256s match `cube-run-manifest.txt`, and the list equals the manifest's. The earlier models still
    reproduce: `items_chain.py affixes` 3102, `props` 168 (2281 with the forced logs), `sockets.py check` 351,
    `uniques.py check` 304 and 1519, 0 failed each. The model derives its outputs: the rows that reach the matcher, the
    slots, the creation record, both game-seed steps of every creation and copy, the unit, start and item seeds, the
    picks and rolls, and the game seed at CUBX are all predicted and compared. Taken from the log: the cow portal's spot
    search and portal object (declared oracles, which reset the game seed), and the created item's flag word at CRECX
    (now stated in the record's limits; no claim rests on it).
  - Spot-checked with r2 on the pinned `game.exe` (`631066c1…`): `0x00556F60` (the misc test `push 0x34`, table
    `0x006E1138`, six `idiv`s for version ≥ 1 and three for the version-0 body, `RNG_RangeB` `0x0045C3E0`, flag
    `0x40`, `ret 8`); `0x00565930` (`RNG_RangeB` twice, the 256 cap, `ITEMS_IsType`); `0x005652E9`–`0x005652FD`
    (stat 356 against `Game+0x6D` with `jl`: op 28 is ≥); `0x00594270` `xor eax, eax; ret`; and ItemCopy's path
    `0x0055A31C` → `sub_00558CB0_ItemCreateFromSave` → `SUnitCreate` (`0x00558D01`) → `ItemSeedInit` (`0x0055532A`).
  - Rulings: (1) The three logger revisions stand. r1→r3 adds only the UNIT fields `xy` and `seed28`, with no
    breakpoint or address changed, and the logs carry those fields in exactly the sessions the record names. (2) The
    builder-made inputs (name-only rares, uniques at max properties) limit no `[C]`. The match reads class, type,
    quality, socket and ethereal state and stat 356; created outputs read only input 1's class and ilvl; copies are
    compared with their input list by list. (3) The cow saves' quest bits and stat 356 are forced states (ADR-0010):
    they test the gates, not how a game sets them. (4) The `d2s.py` keys stand, as in plan 0029 Phase 2. Merged
    with main's: `quest_bits` keeps main's mapping form and also accepts the list form the cow recipes use; a simple
    `questdiffcheck` item needs `quest_diff` (main's rule). `test_d2s.py`: 42 tests OK, every cube recipe hash
    unchanged. (5) The calibration logs and the first craftgear session are fairly excluded (a pilot fault), and
    they reproduce too (12 transmutes, now in the record).
  - Fixes applied: items/0008's summary `[C]` bullets are scoped to what the run reached: the player ops, ops 15–27,
    `eth`/`exc`/`eli`, the 252-redraw bound, and CubePickItemOfType's skipped record, cap and empty case stay `[I]`.
    § 8.2 (ItemCopy) now anchors the code path, not only the run. Main's `pre=`/`suf=` bullet goes to `[C]` on the
    run's 12 forced picks. items/0005 § 3: a displaced `run:2026-10-14-affixes` anchor is put back on its bullet. The
    record now gives 3102 affix creations (it said 2171), the excluded logs and the CRECX flag limit. `tools/cube.py`
    docstrings no longer call ItemCopy an oracle. The backlog entry on Larzuk's crafted socket cap is closed: no stock
    row can reach it (row 63 is `sock=1` on a `rar` input; rows 123–126 need `nor` inputs).
  - The ItemCopy question is closed with two sources: the code path above, and 18 copies whose start, item and unit
    seeds were predicted. `sub_0055A2A0_ItemCopy` stays `I` in `re/symbols.csv` (save/d2s owns it; its serialise
    path is not what this run tested).
  - Phase 3 (spec-writer) next: items/0008 § 8 and the record.
- **2026-10-15 — Phase 3 drafted (spec-writer, branch `lane/s30p3`), review requested.** [items/cube](../specs/items/cube.md)
  (draft), tags {C: 121, I: 80, L: 8}, 8 open questions. Written from items/0008 (§§ 1–8 and *Leads used*), the run
  record, [CubeMain](../tables/CubeMain.md), items/0002 § 8 and items/0005 §§ 3, 11, with the Phase 2 review rulings.
  The match is pseudocode (§ A, § B), the output kinds with their draws are tabled (§ M), and the worked examples
  are a crafted amulet (row 70) and a magic reroll (row 60) with their draw order, plus the recorded Savage polearm
  (row 19). No per-transmute seeds are published, so the two examples carry no seed values: backlog entry to the
  reverser. Linked from the items README, items/affixes, items/uniques-sets and drlg/outdoor; three glossary terms.
- **2026-10-16 — Phase 3 updated (spec-writer, `lane/s30p3`).** The reverser's test vectors
  ([items/0008 § 8.5](../findings/items/0008-cube.md#85-test-vectors-backlog-2026-10-15-from-run2026-10-15-cube))
  are now Examples 1 and 2 of items/cube (row 70, 20 draws; row 60, 9 draws), and the crafted pick of 0 (§ 4) is a
  § I step note `[I]`. Tags {C: 118, I: 81, L: 6}, 6 open questions.
