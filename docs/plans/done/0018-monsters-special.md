# 0018 — Monsters: champions, uniques and superuniques (mods, minions, names)

> **Status:** done (approved 2026-10-14, closed 2026-10-14)
> **Created:** 2026-10-14
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only

## TL;DR

**Question:** once the population pass has decided that a monster is special, what makes it the champion or unique it
becomes? This covers which mods it gets, its minions, and the name it shows. It also covers how a superunique is built
from its `SuperUniques` row. [monsters/0002](../../findings/monsters/0002-room-population.md) § 5 already has the
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
  `data/strings` findings `[I]` ([data/0003](../../findings/data/0003-string-tables.md)), enough to resolve a name index to a
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
  table doc yet (backlog, plan 0014). `superuniques` has a layout doc ([SuperUniques](../../tables/SuperUniques.md), semantics
  `[L]` except the TC columns). `uniqueprefix`, `uniquesuffix`, `uniqueappellation` and `uniquetitle` are in the
  inventory with no doc.
- Harness and logs: `tools/gdb/mon-spawn.gdb` with `tools/monspawn.py`. The three logs of run:2026-10-13-mon-spawn hold
  24 special-mod rolls, 24 + 6 mod-handler windows (boss and pack members), 4 champion packs and 20 unique groups,
  in Normal and Hell (corrected 2026-10-14; the draft said Normal and Nightmare). They are the first test set and need no new run. Nightmare and Hell saves can be built
  with `tools/d2s.py build` (`acts_open`, [save/0002](../../findings/save/0002-quest-words.md)).
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
  - [SuperUniques](../../tables/SuperUniques.md): `Class`, `Mod1`–`Mod3`, `MinGrp`/`MaxGrp`, `AutoPos`, `Stacks`,
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
  Point the special branch and the *Inputs and oracles* rows of [monsters/spawn](../../specs/monsters/spawn.md) at it, and
  add the row to [monsters/README](../../specs/monsters/README.md).
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
- **2026-10-14 — Approved (human).** No changes to the draft. Phase 0 (archivist) is next.
- **2026-10-14 — Phase 0 landed (archivist).** New table docs [MonUMod](../../tables/MonUMod.md),
  [UniquePrefix](../../tables/UniquePrefix.md), [UniqueSuffix](../../tables/UniqueSuffix.md),
  [UniqueAppellation](../../tables/UniqueAppellation.md), [UniqueTitle](../../tables/UniqueTitle.md); generation columns added to
  [SuperUniques](../../tables/SuperUniques.md). Layouts in `tools/excel_layouts.py`: `excel_bin.py diff` passes on all five
  new tables (MonUMod 688 cells, the name tables 53 + 69 + 25 + 16, 0 mismatches; the `excel_layout` gate baseline goes
  from 30 to 35 tables). Survey commands: `python3 -I tools/mon_survey.py umod <excel-dir>` prints every record and the
  pick weights per difficulty with the `exclude` pairs; `… superuniques <excel-dir>` the SuperUniques generation columns.
  Meanings stay `[L]` except row 0 `constants` = 20 (`[C]`, monsters/0002 § 5), the `cpick` order (`[I]`, by the
  `+0x0E + 2·difficulty` reader) and SuperUniques `Stacks` = record `+0x26`, which `SuperUniqueSpawn` reads (`[I]`,
  monsters/0002 § 7). Surprises: the champion weights are five 1s (`champion` and the four expansion-only mods
  `ghostly`/`fanatic`/`possessed`/`berserk`); the unique weights are 6 each on 12 mods (13 from Nightmare, `resist`
  added); the only `exclude` pair is `lightning` ↛ MonType `sandleaper`; `constants` is a list indexed by row, not a
  property of the row's mod; `uniquesuffix` skips the string `raven` (2790); every UniqueTitle record is the index of
  `unused`. Superunique fixed mods include `rndname`, `poisonhit` and the disabled `thief` (Lord De Seis), none of which
  has a unique pick weight. Backlog: plan 0014 follow-ups (b) and the MonUMod half of the Levels `umon` entry marked
  done; one new archivist → reverser entry (UniqueTitle reader, `fInit`/`exclude2`/`upick` order, superunique minion
  source, the other constants).
- **2026-10-14 — Phase 0 accepted (architect).** Reran `tools/mon_survey.py umod` (champion weights: 5 mods at 1, 4 expansion-only; unique weights: 12 mods at 6 in Normal, 13 in Nightmare and Hell; one exclusion) and `excel_bin.py diff` on `monumod` and `uniqueprefix` (exit 0). SuperUniques `Stacks` tagged `[I]` from the monsters/0002 § 7 anchor: accepted, a table doc may restate a finding's tag with its citation. The archivist → reverser questions (UniqueTitle readers, `fInit`/`exclude2`, `Mod1`–`Mod3` indexing, superunique minions without `minion1`) are Phase 1 inputs. Phase 1 (reverser) is next.
- **2026-10-14 — Phase 1 landed (reverser).** [monsters/0003](../../findings/monsters/0003-special-monsters.md), 58 new
  `re/symbols.csv` rows (subsystem `monsters/special`; `SpecialModsRoll`, `ChampionModPick`, `SpecialModsApply` and
  `SuperUniqueSpawn` moved to this subsystem and finding, names unchanged because specs cite them), `re/types/monspecial.h`
  (`MonsterData`, `MonUModRec`, `SuperUniqueRec`, `UModAuraRow`). Done-when: `ChampionModPick` and the unique loop § 2–3
  (filter `enabled` / `version` vs `game+0x70` / `champion` byte / `exclude1`+`exclude2` by MonType is-a / `fPick` / present
  mods for uniques only; one `Range(unit.seed, Σw)`; no candidate → no draw, 0; count `Range(1)+1+d`, total capped at 9,
  roll skipped at ≥ 8); handlers and per-handler draw table § 4 (only `rndname` steps the unit seed, once; `aura` draws on a
  local seed from the name seed; pack members: mod 16 + one `rndname`); `xfer` § 5 (copied into minion lists at creation;
  every boss mod also applied to the group with flag 0); superuniques § 6 (fixed mods, `thief` skipped, `d` extra unique
  picks, minions `MinGrp+d..MaxGrp+d` of `minion1` or own class, `AutoPos`, placed bit/`Stacks`, 15 hard-coded tails,
  Radament `Range(5)`, mod 22 appended); names § 8 (server sends a 16-bit name seed; the client rolls suffix, prefix, then
  50 % appellation/suffix/prefix; superunique `Name`; champion "<mod word> <NameStr>"; UniqueTitle unread); MonPlace 2, 3
  and `0x11`–`0x20` with `0x0054E2A0` § 7. The run:2026-10-13-mon-spawn logs were re-read: step counts of all 24 rolls and
  67 handler windows and 6 superuniques match the reading (`[C]` where stated), and a scratch replay gives the logged mods
  and exit seeds in 24 of 24 rolls (not kept; Phase 2 writes `tools/monspecial.py`). **Boundary recommendation (§ 9):**
  no new oracle; model every draw incl. the aura index and the client name roll; handler effects and their deep callees
  out of scope as seed-asserted calls; the MonType matrix builder unread (read it or log `MonTypeIsA` as a value oracle).
  Surprises: MonPlace 2 ignores the preset point and never rolls champion; preset champions and every pack member get mod
  16 only; `fPick` 1/3 are mode tests (`A1`/`WL`); superuniques skip `ModEligible`; names are client-side. Backlog: the
  archivist → reverser entry (a)–(c) answered, (d) named only; one reverser → archivist entry for the table docs. Ready
  for the architect's review; Phase 1b next.
- **2026-10-14 — Phase 1 review fix F1 (reverser).** The 24-of-24 replay in [monsters/0003](../../findings/monsters/0003-special-monsters.md)
  (§ Answer, § 9) is reworded as an informal, uncommitted check that supports no tag; the `[C]` bullets rest only on what the
  run:2026-10-13-mon-spawn logs show directly (`SMR1` → `SMRX` step counts, the 67 handler windows, the superunique minion
  counts). Architect's boundary ruling, recorded as given: "No new oracle" is accepted. Phase 2 models every draw: the mod
  picks, `Range(1)`, the extra superunique picks, the minion counts, Radament's `Range(5)`, the aura index on its local seed,
  and the client name roll. The handler effects stay out of scope; their deep callees are seed-asserted calls (any seed
  change is a failure). `MonTypeIsA`: log it as a named ADR-0004 value oracle in Phase 2, unless its builder turns out to be
  a short read. The `lightning` × `sandleaper` exclusion is a required case only if the run reaches one; otherwise list it
  as unreached. Phase 1b (the community cross-check against `src:arreat-summit-bonuses` and `src:d2dfg-blizzard`) is next.
- **2026-10-14 — Phase 1 accepted with fix F1 (architect).** monsters/0003 meets every *Done when* bullet: 8 `[C]` (step and minion counts read from the run:2026-10-13-mon-spawn logs), 41 `[I]`, 5 `[L]` under *Open questions*. F1 (99e883a): the uncommitted 24/24 replay supports no tag. Boundary as ruled in the reverser's log entry: no new oracle; `MonTypeIsA` is a named value oracle unless its builder is a short read. Correction: the plan 0014 logs cover Normal and **Hell**, not Nightmare, so Phase 2's new run must add Nightmare and classic. Phase 1b (reverser, no Ghidra needed) is next.
- **2026-10-14 — Phase 1b landed (reverser).** Cross-check in [monsters/0003 § Leads used](../../findings/monsters/0003-special-monsters.md#leads-used),
  written after the Phase 1 finding (blind first). Sources fetched and read in this session (raw HTML or wikitext, saved only in a
  scratch directory, nothing run): `src:arreat-summit-bonuses` and `src:d2dfg-blizzard` (§ monumod.txt, § SuperUniques.txt,
  § UniqueAppellation/UniquePrefix/UniqueSuffix; the guide has no UniqueTitle section) again, and new `src:arreat-summit-monster-pages`
  (basics, super and the five act superunique pages) and `src:fandom-d2-elite-monsters` (Unique, Super Unique, Champion
  Monsters, Minions). `src:pk-monumod-guide` was searched for and not found. No page had game code. 37 verdicts on 36 claims (10 held, 18 held with refinement, 6 not covered, 3 contradicted): mod counts
  (`1 + d` uniques, superunique `d` extras and `+d` minions) held with refinement; exclusions, `fPick`, weights, the champion
  pack ("pack members get mod 16 only" agrees with the Arreat Summit's "all but one are always Champion"), `xfer`, the aura
  table and the name structure held or held with refinement; 6 not covered (Spectral Hit's element, Cursed, `SpawnUniqueMod`
  of a later build, `Utrans` 0, UniqueTitle, the champion name). **Contradicted, required Phase 2 cases:** (1)
  src:d2dfg-blizzard `champion` = 0 "can be used by any type of special monster", while the code limits the champion pick to
  `champion` = 1; stock data cannot show the difference, so the case needs an edited MonUMod run or an "unreachable" ruling;
  (2) src:d2dfg-blizzard `AutoPos` "within a radius of its designated position", while the code draws a point anywhere in the
  room; log and reproduce one `AutoPos` superunique's position; (3) src:fandom-d2-elite-monsters "always have 3-6 minions"
  and one/two/three bonuses for superuniques, already contradicted by run:2026-10-13-mon-spawn (Rakanishu 10) and kept as a
  checked case. (1) and (2) were re-read with r2 (`0x005A056F`, `0x005A4A2B`, `0x005A09EF`): no finding error, no tag
  changed. New *Open question*: where a unique's random colour is drawn (display only, client). Backlog: reverser → reverser
  (the three cases) and reverser → architect (review). Ready for the architect's review; Phase 2 next.
- **2026-10-14 — Phase 1b accepted (architect).** 37 verdicts on 36 claims: 10 held, 18 held with refinement, 6 not covered, 3 contradicted, none of them an error in the finding. New sources: `src:arreat-summit-monster-pages` and `src:fandom-d2-elite-monsters` (documentation, read in-session). `src:pk-monumod-guide` is recorded as not found. Nothing was rejected. Rulings on the contradicted claims:
  - **(1)** `champion` = 0 rows in the champion pick: unreachable with stock data. Not a Phase 2 case, no edited-data run, stays `[I]` and goes under the spec's *Open questions* (precedent: `sparsePopulate`, plan 0014).
  - **(2)** An `AutoPos` superunique's position (any point in the room via `SpawnPosPick`, on the room seed) is a required Phase 2 case.
  - **(3)** Superunique minion counts `MinGrp + d .. MaxGrp + d` are a required Phase 2 case; run:2026-10-13-mon-spawn already shows Rakanishu with 10.

  Phase 2 (reverser, harness) is next, after plan 0017 Phase 2 releases display :7. Its new run must add Nightmare and classic (Phase 1 acceptance).
- **2026-10-14 — Phase 2 landed (reverser).** [run:2026-10-14-mon-special](../../findings/monsters/experiments.md#run2026-10-14-mon-special),
  agent-driven (scripted Teleport/Nova through `tools/xdrive.py`, steered by the new `tools/d2pilot.py` from the live log), twelve
  sessions over normal, nightmare and hell, classic and expansion. New: `tools/monspecial.py` (the model of monsters/0003) wired into
  `tools/monspawn.py` in place of the special-mod and mod-handler seed oracles; logger `tools/gdb/mon-special.gdb` /
  `mon-special.py` (MTI, MPK, HD0/HDX, TH0/TH1, AUR, XF, SU0..SUX, PM0..PMX, CN0/CNR/CNH, PLR), the `SNP` snapshot in
  `tools/gdb/collision.py`, recipes `tools/d2s_recipes/specnova.json` and `specclassic.json`. Done-when: the plan 0014 logs
  rerun with the oracles replaced (24 rolls, 30 handler windows, 114 363 checks, 0 mismatches) and the run:2026-10-14-collision
  logs too (7 rolls, 14 windows, 75 812 checks, 0 mismatches); the new run has 20 champion packs, 54 unique groups, 11
  superuniques (7 in nightmare or hell), MonPlace 2 and 3 four times each (Tristram), 277 minions with a transferred mod, 94
  client name rolls, `monspawn: 390144 checks, 0 mismatches`. All 5 champion mods and all 13 unique mods were drawn
  (normal: only 4 unique mods, and no pass champion); Phase 1b cases (2) `AutoPos` position (6 superuniques) and (3) superunique
  minion counts reproduced; the `lightning` × `sandleaper` exclusion, Radament and the other superunique tails, `thief` and
  aura superuniques are unreached and listed. No oracle is left on the special path: `MonTypeIsA` is modelled after reading its
  builder (`sub_00658460_MonTypeReachable`). **Correction:** the client keeps only the low byte of the name seed
  (`sub_0045F190_ClientMonAssign`, `0x0045F387`); the name roll runs on `Init(nameSeed & 0xFF)` (monsters/0003 § 8). The monster
  post-create mods (`MonPostCreateMods`) are now modelled (no draw). Surprise for `monsters/stats`: the level the aura handler
  reads lacked the `leveladd` + 3 in two classic-nightmare cases. monsters/0003 claims reproduced go to `[C]` (§ 10); monsters/0002
  § 9 notes the replaced oracles; 5 new symbols, 13 raised to `C`. Side fix: the run:2026-10-14-collision *Conclusion* anchor
  (drlg experiments, W1). Backlog: reverser → reverser cases (2) and (3) done; reverser → architect (review); reverser →
  archivist (a MonType table doc). Ready for the architect's review; Phase 3 (spec-writer) next.
- **2026-10-14 — Phase 2 accepted (architect).** Spot-checked `0x0045F382`–`0x0045F387` (a 16-bit `BITBUF_ReadUnsigned`, then
  `movzx cx, al`) and `0x005A0777` (`xor edx, edx`) in the pinned binary; the unreached cases stay `[I]` in § 10. Rulings:
  - **(a)** The low-byte name seed is accepted as a correction at `[C]` (code plus 94 client rolls). Phase 3 states the name roll
    on `Init(nameSeed & 0xFF)` and that only 256 random-unique names exist.
  - **(b)** The aura level in classic stays under *Open questions* as an `[L]` for `monsters/stats`; the spec states the aura
    draw at `[C]` and the level threshold (`≥ 20`) at the tag of its own anchor.
  - **(c)** The unreached cases are accepted as `[I]` and are no blocker: none is reachable on demand without edited data or a
    quest state the recipes don't build. Phase 3 lists them under *Open questions* or keeps them `[I]` in the body.
  - **(d)** The presets/restore/objects window stays an oracle and is named in the spec's *Inputs and oracles*.
  Phase 3 (spec-writer) is next; plan 0019 Phase 2 can take display :7.
- **2026-10-14 — Phase 3 landed (spec-writer).** New [specs/monsters/special](../../specs/monsters/special.md) (draft, C 102 / I 85 /
  L 7): §§ A–J (champion or unique, the weighted picks with `ModEligible` and the MonType matrix, the handlers incl. `rndname`
  and the local aura draw, the per-mod draw table over all 43 MonUMod rows, unique minions and `xfer`, pack members and preset
  champions, superuniques with the tails, MonPlace 2/3 and `0x11`–`0x20`, the client name roll) and the draw order on the unit
  seed, with five Mermaid diagrams. Rulings applied: (a) the name roll on `Init(nameSeed & 0xFF)` at `[C]`, 256 names; (b) the
  aura draw `[C]`, the `≥ 20` threshold `[I]` by its table anchor, the classic aura level an `[L]` under *Open questions*; (c)
  the unreached cases `[I]` in the body and listed under *Open questions*; (d) the presets/restore/objects window named in
  *Inputs and oracles*; the `champion` = 0 case (Phase 1b ruling 1) under *Open questions*. Worked examples, all from
  run:2026-10-14-mon-special and re-derived with `tools/rng.py`: a champion pack (`monspecial-s6-2106-nightmare.log` line
  3700, berserk boss and two mod-16 members), a unique group with its minions, transfer, aura and client name
  (same log, line 9960), the superunique Rakanishu in hell (`monspecial-s11-2111-hell.log` line 3855), and a name with an
  appellation (line 6512). [specs/monsters/spawn](../../specs/monsters/spawn.md) (stays reviewed; C 107 → 108, I 61, L 6): the
  special branch and the *Inputs and oracles* rows point at special.md, the MonUMod anchor replaces "no table doc yet", and
  the "not logged" open question is narrowed to multiplayer. [specs/monsters/README](../../specs/monsters/README.md) (C 11 → 12):
  the `special.md` row (draft), a superunique entry point, the open question narrowed to `monsters/stats`. Glossary: Mod,
  Superunique, Name seed. Open questions in special.md: 7 (all `[L]`). Backlog: spec-writer → archivist (the name-table docs
  still say "16-bit"), spec-writer → reverser (the aura guards of the model), spec-writer → architect (review). Ready for the
  architect's review; the research-map row is the architect's.
- **2026-10-14 — Phase 3 accepted, plan closed (architect).** [specs/monsters/special](../../specs/monsters/special.md)
  reviewed (C 102 / I 85 / L 7); monsters/spawn stays reviewed (C 108 / I 61 / L 6). Checked: the § D table covers all
  43 MonUMod rows with run-backed `[C]` only for mods in a logged list; the four worked examples come from the run (example 1's
  four unit-seed steps re-derived: `F89D25DB:13AF665B` … `394C9678:2EE42422`, `Range(100)` = 11, pack `mod 3` = 1); every `[L]`
  is under *Open questions*; rulings (a)–(d) applied. Non-blocking follow-ups stay in the backlog: the unique-name table docs
  (16-bit wording, archivist) and the aura-handler guards (reverser). Research map row `monsters/special` → reviewed.
