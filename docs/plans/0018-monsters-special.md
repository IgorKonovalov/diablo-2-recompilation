# 0018 — Monsters: champions, uniques and superuniques (mods, minions, names)

> **Status:** draft
> **Created:** 2026-10-14
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** once the population pass has decided that a monster is special, what makes it the champion or unique it
becomes? This covers which mods it gets, its minions, and the name it shows. It also covers how a superunique is built
from its `SuperUniques` row. [monsters/0002](../findings/monsters/0002-room-population.md) § 5 already has the
champion-or-unique split (`Range(boss.seed, 100) <` MonUMod row 0 `constants`, 20) and the pack and minion counts at
`[C]`. Everything after that split is still unread. That means `ChampionModPick`, the unique mod picks
(`1 + difficulty` of them), the mod handlers, the superunique builder and the name rolls. Plan 0014 took the mod
handlers' unit-seed draws as ADR-0004 seed oracles. This plan reads that code and models it in `tools/monspecial.py`.
It reruns the plan 0014 logs with those oracles replaced, then logs a new run in all three difficulties. When it is
done:
- `docs/findings/monsters/0003-special-monsters.md` has the mod selection, the superunique build and the name roll at
  `[C]` for the logged cases;
- `docs/specs/monsters/special.md` is drafted;
- the *Inputs and oracles* table of monsters/spawn lists the special-mod draws as `monsters/special` behaviour, not
  as oracles.

What the mods *do* (HP, damage, auras, resistances) is `monsters/stats` and is only named here.

## Context

- Research-map row `monsters/special`, `not started`. Dependencies: `rng` reviewed; `monsters/pool` reviewed;
  `monsters/spawn` reviewed (plan 0014, closed 2026-10-14), with the special branch `[C]` up to the split;
  `data/strings` findings `[I]` ([data/0003](../findings/data/0003-string-tables.md)), enough to resolve a name index to a
  key.
- Code already named (monsters/0002 § 5 and § 7):
  - `sub_005A0760_SpecialModsRoll` and `sub_005A0500_ChampionModPick` (`[I]`; the champion weights are the u16 at MonUMod
    `+0x0E + 2·difficulty`, and the pick is the only spawn-side reader of the expansion flag);
  - `sub_005A2120_SpecialModsApply` (`[I]`);
  - `sub_005A0C00_UniqueMinions` and `sub_005A0BB0_UniqueMinionClass`, `sub_0054E1E0_ChampionPack` and
    `sub_005A48C0_ChampionMemberMark` (`[C]`);
  - `sub_005A49B0_SuperUniqueSpawn` with the placed bit in `game+0x1D30` and record `+0x26` (`[I]`);
  - `sub_006556E0_SuperUniqueGet` and `sub_005A03A0_MonSuperUniqueId` (`[I]`, items/0001);
  - the preset path `sub_0054E600_PresetMonSpawn`, with its MonPlace cases 2 (a unique, champions disallowed) and 3 (a
    champion with its pack), and the class helper `0x0054E2A0` for `0x11`–`0x20` (not read).
- Data: `monumod.txt`/`.bin` (43 records of `0x20`, `DataTables+0xC50`), with columns `uniquemod`, `id`, `enabled`,
  `version`, `xfer`, `champion`, `fPick`, `exclude1`, `exclude2`, `cpick` ×3, `upick` ×3, `fInit` and `constants`. It has no
  table doc yet (backlog, plan 0014). `superuniques` has a layout doc ([SuperUniques](../tables/SuperUniques.md), semantics
  `[L]` except the TC columns). `uniqueprefix`, `uniquesuffix`, `uniqueappellation` and `uniquetitle` are in the
  inventory with no doc.
- Harness and logs: `tools/gdb/mon-spawn.gdb` with `tools/monspawn.py`. The three logs of run:2026-10-13-mon-spawn hold
  24 special-mod rolls, 24 + 6 mod-handler windows (boss and pack members), 4 champion packs and 20 unique groups,
  all in Normal and Nightmare. They are the first test set and need no new run. Nightmare and Hell saves can be built
  with `tools/d2s.py build` (`acts_open`, [save/0002](../findings/save/0002-quest-words.md)).
- Why now: this is the last core monsters row without a plan, and `monsters/stats` and `hirelings` wait on it. The
  reverser can start from logs that already exist.
- Leads: `src:arreat-summit-bonuses` (registered; its champion and unique counts were compared in plan 0014, but not
  "which champion mod each pack member gets"), and `src:d2dfg-blizzard` (registered; its MonUMod, SuperUniques and
  unique-name table sections are not yet read). Phase 1b fetches both again, as ADR-0007 requires.

## Phases

### Phase 0 — Mod, superunique and name tables
- **Owner skill:** archivist
- **What:** document the MonUMod table and the four unique-name tables, and complete the generation columns of
  SuperUniques.
- **Outputs:**
  - `docs/tables/MonUMod.md`: layout `[C]` by `excel_bin.py diff`, every column including `fInit` and `constants`,
    and a survey per difficulty of which mods have a non-zero `cpick`/`upick` and which `exclude` pairs occur;
  - `docs/tables/UniquePrefix.md`, `UniqueSuffix.md`, `UniqueAppellation.md`, `UniqueTitle.md`: rows, string keys,
    and any version or class columns;
  - [SuperUniques](../tables/SuperUniques.md): `Class`, `Mod1`–`Mod3`, `MinGrp`/`MaxGrp`, `AutoPos`, `Stacks`,
    `Replaceable`, `Utrans` and the other non-TC columns, with value ranges;
  - the backlog follow-ups for the MonStats and Levels links (plan 0014) that touch these tables;
  - the `tools/` survey commands.
- **Done when:** `excel_bin.py diff` passes on all five new tables, and one survey command prints the MonUMod pick
  weights per difficulty with the `exclude` pairs. Meanings stay `[L]`, except the row 0 `constants` value, which
  cites monsters/0002 § 5.

### Phase 1 — Read the mod selection, the superunique build and the name roll
- **Owner skill:** reverser
- **What:** read the code from the champion-or-unique split to the finished special monster, and choose the
  boundary for Phase 2.
- **Outputs:** `docs/findings/monsters/0003-special-monsters.md`, `re/symbols.csv` rows (subsystem
  `monsters/special`, renaming the `sub_` ones it settles), `re/types/` additions (the monster mod array, the
  superunique record).
- **Done when:** the finding states, with addresses and `[I]` or better:
  - `ChampionModPick`: the candidate filter (`enabled`, `version` against the expansion flag, `champion`, `exclude`
    pairs, mods already present) and the weighted draw (seed, range, order);
  - the unique mod loop of `SpecialModsRoll`: its count `1 + difficulty`, the filter (`upick`, `fPick`, `exclude`,
    duplicates), what happens when no candidate is left, and the cap at 8 or 9 mods;
  - `SpecialModsApply` and the mod handlers: for each handler, **which draws it makes on which seed** and in which
    order. That includes the handlers that run on each champion-pack member. Their effects on stats are only named
    (`monsters/stats`);
  - which mods pass to minions (`xfer`), and how a minion gets them;
  - the superunique build: `SuperUniqueSpawn` from record to unit (class, fixed mods `Mod1`–`Mod3`, the extra random
    mods in Nightmare and Hell if any, minions from `MinGrp`/`MaxGrp`, `AutoPos`, the placed bit and `+0x26`), and the
    hardcoded per-superunique cases it contains;
  - the name roll: where it happens (on the server from the unit seed, or on the client from a value sent with the
    unit), which tables and draws it uses, and how a superunique takes its fixed name;
  - the MonPlace preset specials 2 and 3, and the class helper `0x0054E2A0` for `0x11`–`0x20` (backlog, plan 0014
    Phase 1);
  - **the boundary decision** for Phase 2: which handler effects stay out of scope, and which inputs (if any) are
    still oracles. Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** fetch `src:arreat-summit-bonuses` and `src:d2dfg-blizzard` (§ MonUMod, § SuperUniques, the unique-name
  sections) again and compare blind, per `evidence-rules.md` § Community cross-checks. Register any other document
  found, or record "none found" with the searches made.
- **Outputs:** `docs/sources.md` updates; verdicts in the finding's *Leads used*.
- **Done when:** each claim about mod counts, mod exclusions, champion mod choice, superunique minions and name
  structure carries a verdict with a `src:` id or `not covered`. Every `contradicted` claim is a required case of
  Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (a human may play, as in plan 0014)
- **What:** write `tools/monspecial.py` and plug it into `tools/monspawn.py` in place of the special-mod seed oracles.
  Then log a new run.
- **Logging:** extend `tools/gdb/mon-spawn.gdb` with every mod pick (candidate weights, draw, result), every
  handler's draws, the minion mods and the name indexes. Where the name is rolled on the client, also log what the
  client shows.
- **Done when:**
  - the three plan 0014 logs are rerun with the special mods and handler draws predicted by the model: 0 mismatches,
    and the unit-seed state after each special matches the log;
  - a run `run:YYYY-MM-DD-mon-special` covers Normal, Nightmare and Hell, classic and expansion. It has at least 20
    champion packs, 40 unique groups, and 5 superuniques, at least one of them in Nightmare or Hell. It includes one
    MonPlace preset special of each of cases 2 and 3, and a minion that takes a transferred mod. All of these
    reproduce with 0 mismatches;
  - every mod with a non-zero pick weight in the difficulties played is drawn at least once, or listed as unreached;
  - the Phase 1b cases are covered;
  - any boundary that remains is named in the record.

  In-scope claims go to `[C]` citing the run. monsters/0002 § 9 notes which oracles are now replaced.

### Phase 3 — Spec: monsters/special, and monsters/spawn updated
- **Owner skill:** spec-writer
- **What:** write `docs/specs/monsters/special.md` (champion mods, unique mods, minion transfer, superuniques, names).
  Point the special branch and the *Inputs and oracles* rows of [monsters/spawn](../specs/monsters/spawn.md) at it, and
  add the row to [monsters/README](../specs/monsters/README.md).
- **Done when:**
  - the spec follows the template and every statement is tagged;
  - it has the RNG call sequence of one champion pack and one unique group as worked examples (taken from the run);
  - it has a table of per-mod draws;
  - the architect's review passes.

## Open questions

- Mod effects (HP and damage multipliers, auras, enchant damage, resistances) belong to `monsters/stats`. If a handler
  draws a value that it then stores, Phase 1 says whether the draw is specified here and the meaning there.
- A per-superunique hardcoded case may depend on quest state (e.g. a superunique that only appears once). Phase 1 names
  each one; those tied to quest scripts can stay inputs.
- The display text of a name is a `data/strings` lookup. Only the index chosen is in scope. Turning it into text uses
  the `[I]` string lookup.
- Hireling names use separate tables (`hirelings`, not started); they are out of scope.

## Implementation log

_(lanes append dated entries as phases land)_

- **2026-10-14 — Drafted (architect).** Picked from the research-map rows whose dependencies are met. It finishes the
  core monsters band, and its first test set exists already (run:2026-10-13-mon-spawn). Waits for the owner's approval.
