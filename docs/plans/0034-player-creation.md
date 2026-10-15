# 0034 — Player: new character, starting items, experience and level-up

> **Status:** in-progress (approved 2026-10-15)
> **Created:** 2026-10-15
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0011-harness-slots

## TL;DR

**Question:** what does a new character of each class start with (stats, skills, items, with their seeds), how does
experience turn into a level, and what does a level-up change? When it is done:
- `CharStats`, `Experience` and `CharTemplate` have table docs;
- `docs/findings/player/0001-creation.md` names the new-character path from the client's stub to the first save, the
  starting items' creation (through the item model), the experience table lookup, and the level-up;
- `tools/player.py` predicts a new character's save and a level-up, and reproduces a run;
- `docs/specs/player/creation.md` is drafted.

## Context

- Research-map row `player/creation`: `not started`. Dependency `items/properties` reviewed; `save/d2s` reviewed (the
  layout this path writes).
- Code already named ([save/d2s](../specs/save/d2s.md), [save/0001](../findings/save/0001-d2s-io.md), all `[I]`): the
  client builds a 335-byte stub (`sub_0043C540_StubBuild`, `StubWrite` `0x0043C6B0`), and the server calls
  `sub_00569F80_NewCharFromStub` when the file ends at the header; `sub_0043CAA0_ConvertToExpansion`;
  `sub_005345A0_PlayerLoad`. `sub_00573910_PlayerXpPct` is the player-count experience share of monsters
  ([monsters/stats](../specs/monsters/stats.md)), not the level table.
- Data: `charstats` (196 B, `0x00613D07`) and `chartemplate` (240 B, `0x0066571A`) have no doc and no layout;
  `experience` is not in data/0001's loader list. Phase 0 finds it.
- Harness: no steps file creates a character; [run:2026-10-11-d2s-samples](../formats/experiments.md#run2026-10-11-d2s-samples) did it
  by hand and kept no coordinates. `tools/d2s.py build` writes characters from a base save, never a stub. Two ways
  reach `NewCharFromStub`: the menu (a steps file), or a stub file the client would have written. Phase 2 uses the
  menu (it is the real path), and the stub only as a cross-check.
- Leads: `src:d2s-community-format` (header), `src:maxroll-player-settings` (experience share); search for
  `charstats.txt` / `experience.txt` guides and the Arreat Summit class pages.

## Phases

### Phase 0 — CharStats, Experience, CharTemplate
- **Owner skill:** archivist
- **What:** document the three tables with `.bin` layouts; locate `experience`'s form (`.bin` or `.txt`).
- **Outputs:**
  - `docs/tables/CharStats.md` (`str`/`dex`/`int`/`vit`, `tot`, `stamina`, `hpadd`, `LifePerLevel`,
    `StaminaPerLevel`, `ManaPerLevel`, `LifePerVitality`, `StaminaPerVitality`, `ManaPerMagic`, `StatPerLevel`,
    `SkillsPerLevel`, the walk and run columns, `ToHitFactor`, `BlockFactor`, `MinimumCastingDelay`, `StartSkill`,
    `Skill 1..10`, `item1..10` with `item1loc`, `item1count`, `StrAllSkills`/`StrSkillTab*`, `baseWClass`) with their
    fixed-point units marked as `[L]` until Phase 1; `docs/tables/Experience.md` (`Level`, the per-class columns,
    `ExpRatio`, the `MaxLvl` row); `docs/tables/CharTemplate.md` (and whether stock play reads it at all);
  - `tools/excel_layouts.py` entries and the regenerated baseline;
  - a `tools/d2s.py build` recipe set for level-up: each class one experience point below a level threshold
    (levels 2, 10, 50 and 98) in an expansion and a classic save.
- **Done when:** `excel_bin.py diff` passes on the tables with 0 mismatches and no uncovered bytes; the survey prints
  each class's start block; the level-up saves load.

### Phase 1 — Read creation and level-up
- **Owner skill:** reverser
- **What:** read `NewCharFromStub` and what it calls, the experience-to-level code, and the level-up handler.
- **Outputs:** `docs/findings/player/0001-creation.md` (new subsystem directory); `re/symbols.csv` rows (subsystem
  `player/creation`); `re/types/` additions.
- **Done when:** the finding states, with addresses and `[I]` or better:
  - **the stub:** what the client sends (class, name, flags: hardcore, expansion, ladder) and what the server checks;
  - **the start:** base attributes, life/mana/stamina with their fixed-point arithmetic, the starting skills
    (`StartSkill`, the class skills at level 0), and the starting items: each `itemN` created through which entry of
    the item model, its quality, its seed source (the character's seed, the game seed), the order, the belt and
    inventory placement, and the class weapon;
  - **the character seed:** where the save's seed field comes from at creation;
  - **experience:** the table lookup (per class or shared), the `ExpRatio` penalty (if experience gain is in scope, the
    share formula is monsters/stats'), and the level cap;
  - **level-up:** the stat and skill points added, the life/mana/stamina gain per level, and whether anything is
    drawn;
  - **the boundary decision** for Phase 2. Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** search for and register class starting-stat and per-level gain documentation; compare blind.
- **Outputs:** `docs/sources.md` entries; verdicts in the finding's *Leads used*.
- **Done when:** each claim carries a verdict; every `contradicted` claim reachable on stock data is a required case of
  Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md);
  at most two slots)
- **What:** write `tools/player.py`, a `tools/gdb/player.gdb` logger, and `tools/gdb/newchar-<class>.steps` steps
  files that create a character through the menu (the coordinates measured once and recorded in `tooling.md`); then
  log a run. New characters land in the slot's saves directory: set the slot's saves aside first, restore them after
  (`tools/saves.py`), and delete only the files this run created.
- **Logging:** the stub received, every draw from `NewCharFromStub` to the first save, each starting item's lines;
  each level-up's before and after.
- **Done when:** a run `run:YYYY-MM-DD-player` reproduces with 0 mismatches:
  - at least 3 new characters of each of the seven classes, expansion, and one of each of the five classic classes,
    hardcore at least once; the saved file after the first game exit predicted by `tools/player.py` field by field
    (the starting items through the item chain);
  - level-ups at levels 2, 10, 50 and 98 for at least three classes, reproduced;
  - the Phase 1b cases;
  - first, the level-up saves of `tools/levelup_saves.py` loaded (at least one per class, expansion and classic, the
    four classic bases made by `d2s.py classic` among them), each written back by *Save and Exit* and compared field
    by field, their hashes recorded in `test_d2s.py` or the run record (moved from Phase 0 at its review).

  In-scope claims go to `[C]`, citing the run.

### Phase 3 — Spec: player/creation
- **Owner skill:** spec-writer
- **What:** write `docs/specs/player/creation.md`; link it from save/d2s (§ D1, the new-character path) and the
  research map row.
- **Done when:** the spec follows the template, and every statement is tagged. It has the starting values per class as
  a table (from CharStats, with the arithmetic), the starting items' creation order with its draws, the level-up as
  pseudocode, and a worked example from the run. The architect's review passes.

## Open questions

- Skill effects, synergies and the skill tree are out of scope (ADR-0002); only which skills a new character has.
- Battle.net and ladder character rules are out of scope (ADR-0009 § no auth topics).

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-15 — Drafted and approved.** The owner asked for a queue of plans to run unattended, and approved all of
  them in advance. Written in the architect worktree `lane/plans0028`.
- **2026-10-15 — Phases 1 and 1b (reverser, `lane/r34p1`).** [player/0001](../findings/player/0001-creation.md): the
  stub and the server's checks, `NewCharFromStub` step by step, starting stats (`<< 8` of the CharStats bytes, no
  per-point factors at creation), skill list (Attack + `Skill 1..10`, `StartSkill` via `item_singleskill` on `item1`
  and as right skill), starting items (creation record quality 2, flags no-socket/no-ethereal, ilvl = level, game-seed
  steps per item, belt/equip/inventory placement, starter flag `[C]`), the seeds, the experience table and
  `ExpRatio`, the kill-experience chain (clamp, level-difference /256 tables, ratio, party share), death loss, the
  level-up and stat spending. Surprises: `-act N` gives a new character `Exp[lvl]` so it starts at level 16/21/27/33
  and its starting items get that ilvl; class byte 7 passes the header check; only the class of CharTemplate is read
  (template games). Cross-check: one contradiction (`ToHitFactor`, combat, out of scope). 3 `[C]`, 41 `[I]`, 14 `[L]`.
  Phase 0 has not landed: the finding anchors columns by `struct:` offsets in `re/types/player.h`.
- **2026-10-15 — Phase 1 and Phase 1b accepted with fixes, boundary ruled (architect).** player/0001 meets every
  Phase 1 *Done when* item and Phase 1b gives each compared claim a verdict. Six anchors re-read with r2, all agree;
  the CharStats and Experience data checks rerun in review (0 mismatches) and written into the finding; the level-up
  "no RNG" claim scoped to the handler and its direct callees, with a Phase 2 question for the deeper callbacks;
  `0x00559CE0` keeps main's name `ITEMS_CreateForStore` after the merge. **Phase 2 boundary:** `tools/player.py`
  models the player code and the two game-seed steps per item copy; each item's own creation chains to the
  normal-quality path of `tools/props.py` (exit seed compared), and a creation it cannot cover is a logged
  `ItemCreate` boundary oracle (ADR-0004), named in the run record. The ToHitFactor contradiction (combat) is not a
  Phase 2 case.
- **2026-10-15 — Phase 0 landed (archivist, `lane/a34p0`), review requested.** [CharStats](../tables/CharStats.md)
  (196-byte record: 32 zero bytes, `class` char[16], the attributes and growth as u8, `ToHitFactor` s32, the five
  string keys as u16 string indices, ten 8-byte item slots, `StartSkill` and `Skill 1..10` as u16 skills rows),
  [Experience](../tables/Experience.md) (32-byte record: seven u32 class columns and `ExpRatio`; record 0 is the
  `MaxLvl` row, `Level` not compiled; it is a `.bin` loaded at `0x00613E41`, not `.txt` only) and
  [CharTemplate](../tables/CharTemplate.md) (240-byte record: `Name`, `Class`, `Level`, attributes, life, mana, nine
  skills with levels, fifteen item slots; loaded, use unknown): `excel_bin.py diff` 0 mismatches on all three, every
  byte mapped; `excel_layout` baseline regenerated (53 tables on this branch). `tools/player_survey.py` (`start
  [class]` prints each class's start block, `xp`, `templates`, `summary`; gate survey `player`). `tools/d2s.py
  classic` (expansion save → classic, reproduces the existing classic base byte for byte) and
  `tools/levelup_saves.py` (48 saves: 7 expansion and 5 classic classes × levels 2, 10, 50, 98, one experience point
  short; `ClassicTest`) ([d2s.md § Level-up saves](../formats/d2s.md#level-up-saves)). Surprises: `SkillsPerLevel`
  and `MinimumCastingDelay` are not in this `charstats.txt`; the seven experience columns are identical; values above
  2³¹ from label 93; the fresh samples hold every class skill at 0 and the `StartSkill` on the right mouse button,
  and life `vit + hpadd`, mana `int`, stamina `stamina` (observed, `[L]`); two column pairs hold equal cells, so their
  slots are `.txt` order (`StaminaPerLevel`/`StaminaPerVitality`; CharTemplate's three rates). **Not done:** no save
  was loaded in the game (no harness slot); proposed for Phase 2, which loads them to level up.
- **2026-10-15 — Phase 0 accepted with fixes (architect review, `lane/a34p0`).** `excel_bin.py diff` rerun on
  charstats, experience and chartemplate (497, 808 and 2 280 cells, 0 mismatches, every byte mapped); `player_survey.py
  start` prints each class's start block; `ClassicTest` and the rest of `test_d2s` pass; gate green with `--full`
  for `excel_layout` (regenerated after merging main: 62 tables) and `player`. No table doc contradicts player/0001:
  the CharStats offsets agree with its descriptor reading, and its `[L]` are open questions the finding now answers
  (follow-up to the archivist, backlog). Fix: the `chartemplate` layout comment said `Hitpoints` u16 (the field is
  u8). Rulings: (1) the unloaded level-up saves do not block, as for plans 0031/0033 Phase 0: loading them is the
  first step of Phase 2 (added to its *Done when*), which loads them anyway to level them up; a save that fails to
  load goes back to the archivist as a blocking entry for that run. (2) The converted classic bases stay unverified
  until that load; (3) the level-1 attributes on a high-level character are acceptable for a level-up run (the
  arithmetic is player/0001 § 7's, not the builder's).
- **2026-10-16 — Phase 2 (reverser, `lane/h34p2`), review requested.**
  [run:2026-10-16-player](../findings/player/experiments.md#run2026-10-16-player), slot 3. First the save-load step:
  the 48 level-up saves (classic ones on the five `d2s.py classic` bases) load and come back unchanged but for the
  time, checksum, map seed and item flag `0x2000` (`tools/player.py loadcheck`, `tools/d2sio.py`; hashes in the
  record). Then `tools/player.py` (the player code; each item copy chained to the item model as `tools/cube.py` does)
  reproduces 35 new characters (7 × 3 expansion, 5 classic, 3 hardcore, 6 `-act N`), their stubs and first saves field
  by field, 269 item copies (11 staff/wand creations are the named `ITEMS_RollStaffMods` boundary oracle), 32 kills
  and 20 level-ups (2, 10, 50, 98 for the Sorceress, Barbarian, Paladin), 0 mismatches. Answers: only
  `PlayerUnitInit` steps the game seed before the items; a level-up draws nothing (no RNG call, no LCG site). New:
  the equip flag `0x1`, the level-0 start-skill entry, the inventory spot score and the belt slot search (player/0001
  § 11). Not run: party share, death loss, the cap. Menu coordinates in `tooling.md`.
- **2026-10-16 — Phase 2 accepted with fixes (architect review, `lane/h34p2`).** Every *Done when* item is met: the 48
  level-up saves load and come back unchanged but for time, checksum, map seed and item flag `0x2000` (the five
  converted classic bases among them, so Phase 0's ruling (2) is settled); 35 new characters (3 per class in the
  expansion, the five classic classes, 3 hardcore) with first saves predicted field by field, starting items through
  the item chain; level-ups at 2, 10, 50 and 98 for the Sorceress, Barbarian and Paladin; the Phase 1b cases (the
  game-seed question and the level-up draw question) answered. Checked in review: `tools/player.py check` rerun
  (35 / 20, 0 failed), the run manifest (71 files) verifies, `tools/d2sio.py check` rerun on four load logs (0
  mismatches, the built hashes as recorded), six anchors read with r2, symbols.csv free of duplicate addresses and
  names, every `[C]` cites the run (bit-exact reproduction) as its second source. **Fixes:** the summary's `[C]`
  bullets claimed branches the run never reached; split so the stub's failure codes, the belt and equip fallbacks,
  the quiver quantity, the class clamp and the experience cap stay `[I]`; the Functions table tags now follow the 19
  rows raised in symbols.csv; the refill statement names the LUM inputs; the record no longer calls built saves
  "forced". **Rulings:** (a) the refill maxima with item bonuses (7 level-ups) are named value inputs: the `[C]` is
  that the refill reads `UnitGetMaxHp/Mana/Stamina`, and equals the base maximum without items (13 level-ups); the
  bonus sum is not claimed. (b) The level-up characters are built saves on stock tables, not ADR-0010 forced-path
  runs (no decision table edited), so no `-forced` id; as with plan 0030's cow saves, they carry `[C]` only for what
  does not depend on the built values (the per-level arithmetic, `XP_Compute`, the no-draw result), never for a
  natural level-*N* character's attributes or life; the six `-act` grants run the same handler on game-made
  characters. (c) Both `d2sio.py` fixes stand: comparing modulo the field width still fails on a saturating writer,
  so it checks truncation rather than hiding it; reader code 2 for a stub is player/0001 § 1. (d) `d2pilot.py explore
  --walk --melee` stands (tool change in the harness lane, plan 0029 precedent). Not covered and not blocking:
  party share, death loss, the cap, class 7 (all `[I]`). The branch is based on `edf5abd`; `main` (`de29693`) must
  be merged into it before it lands. **For Phase 3:** player/0001 summary and § 11, the record's *Answers* and
  *Observed* bullets; the worked example can take one expansion Sorceress (staff oracle) and one Barbarian
  (no oracle) from the run; the Hell life-stat checker note is a save/d2s backlog item, not a spec claim.
- **2026-10-16 — Phase 3 (spec-writer, `lane/s34p3`), review requested.** New
  [player/creation](../specs/player/creation.md) (draft) and the subsystem map [player/README](../specs/player/README.md):
  § A the stub and the server's checks, § B `NewCharFromStub` in order with its game-seed budget (`1 + 2 × copies`) and
  a sequence diagram, § C the starting values per class as a table (CharStats, `<< 8`, the per-level quarter points),
  § D the skill list, § E the starting items (creation record, the draws per copy, belt / equip / inventory placement),
  § F the experience table, § G `XP_Compute`, § H `PLAYER_AddExperience`, § I `PLAYER_LevelUp` as pseudocode, § J the
  `-act` grant, the capped grant, death loss, party share and spending. Worked examples from run:2026-10-16-player:
  an expansion Sorceress (the staff ends at the `ITEMS_RollStaffMods` oracle), an expansion Barbarian (no oracle), a
  Barbarian level-up 9 → 10 and a Sorceress level-up 97 → 98 in Hell (refill from the logged maxima). Tags
  **{C: 77, I: 41, L: 6}**; 6 open questions. Kept `[I]` as the Phase 2 review left them: the stub's failure codes,
  the belt and equip fallbacks, the quiver quantity, the class clamp, the experience cap, party share, death loss,
  class 7; the built level-up characters back `[C]` only for the arithmetic, `XP_Compute` and the no-draw result; the
  refill maxima with item bonuses are named value inputs. Linked from [save/d2s § D1](../specs/save/d2s.md); glossary:
  stub, starter item, ExpRatio. The research-map row is the architect's (backlog). Noticed: player/0001 § 1 and
  save/d2s § D read a class byte above 7 differently (fail 4 vs read as 4); an open question and a reverser entry.
