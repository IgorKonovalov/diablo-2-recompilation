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
  - the Phase 1b cases.

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
