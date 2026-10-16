# 0033 — Hirelings: stock, names, stats and the saved mercenary

> **Status:** in-progress (approved 2026-10-15)
> **Created:** 2026-10-15
> **Owner skill(s):** archivist, reverser, spec-writer
> **Related ADRs:** 0001-target-toolchain-evidence-sources, 0002-scope-creation-paths-and-enablers, 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0007-fetched-leads-only, 0011-harness-slots

## TL;DR

**Question:** which hirelings does a town's hire list offer, with which names, levels, skills and prices, and how
does a hired mercenary's state follow from `Hireling.txt`, its experience and its saved seed? When it is done:
- `Hireling` and `HireDesc` have table docs;
- `docs/findings/hirelings/0001-hirelings.md` names the stock builder (count, row pick, name roll, level), the hire, the
  stats per level, and the mercenary's creation from a save;
- `tools/hirelings.py` predicts a hire list and a mercenary's stats, and reproduces a run;
- `docs/specs/hirelings/README.md` is drafted;
- monsters/pool's last hireling question is closed: the four hireling classes that are not yet logged (338, 359,
  560, 561) and the classic case.

## Context

- Research-map row `hirelings`: `not started`. Dependencies: `rng` reviewed; `monsters/stats` reviewed (hirelings have
  `Align` 1, so no player-count bonus, [stats.md](../specs/monsters/stats.md)); `data/strings` (for the name text) is
  [plan 0028](done/0028-data-strings.md). The name roll stops at a string index, so this plan doesn't wait for 0028; only the
  spec links it.
- What exists:
  - [monsters/pool](../specs/monsters/pool.md) § Constants and § E: the five hireling classes 271, 338, 359, 560 and 561
    are recognised by `sub_0063EE90_HirelingType`, and step E2 forces the normal `Level`. That is `[C]` for 271 only
    (run:2026-10-12-mon-pool-p2), `[I]` for the other four. The *Open questions* entry asks for the other four, classic
    normal, and the no-level-record fallback.
  - [monsters/experiments](../findings/monsters/experiments.md): the `exphellmerc` run injected a merc header (seed
    12345, hireling id 4, experience 500 000). MonStatsInit made the merc at level 1, and the screen showed level 15,
    so the level comes from experience and is applied later.
  - [save/d2s](../specs/save/d2s.md) § D (`[I]`, `D2S_WriteMercHeader` `0x00568E60`, `D2S_ReadMercHeader`
    `0x0056AA50`): flags (bit 16 = dead), seed, name id (stored minus Hireling `+0x114`, reset if above `+0x116`),
    hireling id (looked up by `0x006562F0`), experience. The merc items follow `jf` in expansion saves (§ C3i, § H3).
    `d2s.md` lists the merc section as not verified by a run.
  - [items/quality](../specs/items/quality.md): whether a hireling's kill uses the owner's magic find is `[L]`.
- Data: `hireling` (280 B per record, loaded at `0x0065616B`) and `hiredesc` (4 B, `0x00612AE8`) have no doc and no
  layout.
- Harness: `tools/d2s.py` parses the merc header but `build` has no merc key (`tools/monpool_saves.py` injected one
  with `struct.pack_into`). Opening a hire list needs NPC dialogue: the `tools/d2pilot.py npc` action of
  [plan 0031](done/0031-items-vendors.md). So this plan's Phase 2 runs after 0031's Phase 2.
- Leads: none registered for hirelings. Phase 1b searches (the Arreat Summit hireling pages, Phrozen Keep
  `hireling.txt` guides, `src:d2dfg-blizzard` § Hireling.txt).

## Phases

### Phase 0 — Hireling and HireDesc, and merc saves
- **Owner skill:** archivist
- **What:** document both tables with `.bin` layouts, and add a `merc` key to `tools/d2s.py build`.
- **Outputs:**
  - `docs/tables/Hireling.md` (`Hireling`, `Version`, `Id`, `Class`, `Act`, `Difficulty`, `Level`, `Seller`,
    `NameFirst`/`NameLast`, `Gold`, `Exp/Lvl`, `HP`/`HP/Lvl`, `Defense`/`Def/Lvl`, `Str`/`Dex` and per-level,
    `AR`/`AR/Lvl`, damage and per-level, the resistances and per-level, `Skill1..6` with `Mode`, `Chance`,
    `ChancePerLvl`, `Level`, `LvlPerLvl`, `HireDesc`, `DefaultChance`, `Head`, `Torso`, `Weapon`, `Shield`), the record
    fields `+0x114`/`+0x116` that save/d2s cites, and a survey by act, difficulty and version;
    `docs/tables/HireDesc.md`;
  - `tools/excel_layouts.py` entries and the regenerated baseline;
  - `tools/d2s.py build`: a recipe key `merc: {id, name, seed, exp, dead, items}` with a round-trip test;
  - recipes `mercnova.json` (expansion, gold, every act open) and `mercclassic.json`, plus a set of merc saves, one per
    hireling class and difficulty, for the monsters/pool case.
- **Done when:** `excel_bin.py diff` passes on both tables with 0 mismatches and no uncovered bytes; the survey prints
  each act's hireling rows per difficulty; each recipe builds, loads, and shows its merc in game.

### Phase 1 — Read the hire list and the mercenary
- **Owner skill:** reverser
- **What:** read the stock builder (from the trigger to the list), the hire, the mercenary's creation in the world
  (fresh hire and from a save), and the stat arithmetic per level.
- **Outputs:** `docs/findings/hirelings/0001-hirelings.md` (new subsystem directory); `re/symbols.csv` rows (subsystem
  `hirelings`); `re/types/` additions (the Hireling record, the merc info block).
- **Done when:** the finding states, with addresses and `[I]` or better:
  - **the stock:** when the list is built and rebuilt, how many entries, the row pick (act, difficulty, version,
    player level), the name roll (`NameFirst`..`NameLast`, the seed, uniqueness within the list), the level and
    experience of each entry, the skill choice, and each entry's seed;
  - **the hire:** what the merc header stores and where the seed comes from;
  - **the stats:** HP, defence, attack rating, damage, strength/dexterity and resistances per level from Hireling
    columns, with the integer arithmetic, and how experience gives the level (the `exphellmerc` case);
  - **the creation in the world:** from a save (the seed's role, the items), the MonStats class and the level path of
    monsters/pool § E2 for each of the five classes and the classic case;
  - **magic find on a hireling's kill:** the items/quality `[L]`, read and tagged;
  - resurrection and death costs are named only;
  - **the boundary decision** for Phase 2. Recommend one; the architect rules at the review.

### Phase 1b — Community cross-check
- **Owner skill:** reverser
- **What:** search for and register hireling documentation (stats per level, list size, the name pick, the skill
  choice). Compare blind.
- **Outputs:** `docs/sources.md` entries; verdicts in the finding's *Leads used*.
- **Done when:** each claim carries a verdict; every `contradicted` claim reachable on stock data is a required case of
  Phase 2.

### Phase 2 — Bit-exact reproduction
- **Owner skill:** reverser (agent-driven per [harness-play](../../.claude/skills/reverser/references/harness-play.md),
  after plan 0031 Phase 2 lands the NPC action; at most two slots)
- **What:** write `tools/hirelings.py`, a `tools/gdb/hirelings.gdb` logger, and a hire-list action
  (`tools/d2pilot.py npc <name> hire`). Then log a run.
- **Logging:** each list build with its trigger, every draw, each entry's row, name, level and seed; each merc
  creation's class, level path, stats and seed.
- **Done when:** a run `run:YYYY-MM-DD-hirelings` reproduces with 0 mismatches:
  - the hire lists of Kashya, Greiz, Asheara and Qual-Kehk, in all three difficulties, at least 50 lists in all, with
    at least one rebuild in one game so the trigger is `[C]`;
  - at least 20 hires and their mercenaries' stats in the world;
  - a merc loaded from each of the merc saves: the five classes in Normal, and in Nightmare and Hell where the class
    exists, plus a classic Rogue; the MonStatsInit level reproduced by `tools/monpool.py` (closes the monsters/pool
    entry), and the stats after the level from experience reproduced by `tools/hirelings.py`;
  - a hireling's kill logged with the owner's magic find, so the items/quality `[L]` is settled;
  - the Phase 1b cases;
  - first, `mercnova` (merc shown with its items) and `mercclassic` loaded, their `test_d2s.py` hashes pinned (moved
    from Phase 0 at its review); class 560 recorded as unreachable on stock data (no Hireling row).

  In-scope claims go to `[C]`, citing the run.

### Phase 3 — Spec: hirelings
- **Owner skill:** spec-writer
- **What:** write `docs/specs/hirelings/README.md`; update monsters/pool (§ E2, *Open questions*), items/quality (the
  hireling magic find), save/d2s § D (the merc header now run-checked), and the monsters README.
- **Done when:** the spec follows the template, and every statement is tagged. It has the stock build as pseudocode
  with its RNG call order, the per-level stat arithmetic table, and a worked example from the run. The architect's
  review passes.

## Open questions

- Hireling AI, skill use in combat and auras in effect are out of scope (ADR-0002); only the skills a merc is created
  with are specified.
- Item restrictions on what a merc can equip are inventory rules; named only.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-15 — Drafted and approved.** The owner asked for a queue of plans to run unattended, and approved all of
  them in advance. Written in the architect worktree `lane/plans0028`.
- **2026-10-15 — Phase 0 landed (archivist, `lane/a31p0`, after plan 0031 Phase 0), review requested.**
  [Hireling](../tables/Hireling.md) (280-byte record: 30 s32 fields, six skill slots as parallel arrays, `HireDesc`
  u8, the two name keys, `+0x114`/`+0x116` zero in the file) and [HireDesc](../tables/HireDesc.md) (4-byte code
  list, loaded only under `-txt`): `excel_bin.py diff` 0 mismatches, every byte mapped; `excel_layout` baseline
  regenerated (55 tables). `tools/hireling_survey.py` (`rows [act] [difficulty] [version]`, `summary`; gate survey
  `hireling`) prints each act's rows per difficulty and version. `tools/d2s.py build` gains the `merc` key (`id`,
  `seed`, `name`, `exp`, `dead`, `items`; `MercTest`, round-trip byte for byte); recipes `mercnova.json`,
  `mercclassic.json`; `tools/merc_saves.py` builds 21 merc saves (expansion 4 classes × 3 difficulties, classic
  3 × 3) ([d2s.md § Mercenary saves](../formats/d2s.md#mercenary-saves)). Surprises: `Id` is not unique (60
  (Version, Id) groups of 1–3 level brackets, the 30 Ids identical across versions except the level columns); class
  560 (`act5hire1`) has no row, and Ids 24/25, 26/27, 28/29 are identical; Act V rows exist in `Version` 0;
  `WType1`/`WType2` are not compiled; `Head` and `Weapon` hold the same cells, so their slots are `[L]`; one run
  fits merc level thresholds `Exp/Lvl` × L² × (L + 1) (lead only). **Not done:** no save was loaded in the game
  (the archivist lane has no harness slot, plans README § queue), so "loads and shows its merc" is open.

- **2026-10-15 — Phase 1 and Phase 1b landed (reverser, branch `lane/r33p1`).** [hirelings/0001](../findings/hirelings/0001-hirelings.md)
  (C 11, I 50, L 20; the 20 `[L]` are the *Leads used* verdicts), 46 symbols (subsystem `hirelings`),
  `re/types/hireling.h`. Read blind and committed before any source was opened: the hire table is built once per
  seller per game at the first interaction, from an NPC seed of its own (game draw 3); `n + 10` NPC draws (a seed per
  name, then 10 distinct picks); an entry's seed gives the type (`Range` over the first band's rows) and the level
  offset (`playerLevel − 5 + low mod 5`, min 2); the saved header is `{seed, name, Id, experience}`, and a load takes
  the level from experience (`(L+1)·L²·Exp/Lvl`, `[C]` by the `exphellmerc` save) and the stats from the band row.
  Class 560 has no `hireling.txt` row. A mercenary's kill counts the owner's magic find `[I]`. Corroboration added
  in this pass: for `d ≥ 0` the per-level stat arithmetic (Str, Dex, HP, Def, damage) and the skill level are `[C]`
  by second code paths (`HIRELING_RollEntry`, the client's `sub_004B1090_ClientMercInit`). Phase 1b: three fetched
  sources (`arreat-summit-hirelings`, `rpgkdh-hireling-guide`, `d2dfg-blizzard` § hireling.txt, the last of a later
  build). Contradicted, each re-read with no change: `Resist/Lvl` ÷4 (guide: eighths) and the entry level range
  P−5..P−1 (d2dfg: ± a column) are required Phase 2 cases; the experience formula is settled by the existing run, and
  `HireDesc` (a `hiredesc` row, not a string key) by data. Boundary recommendation for Phase 2: the hire list from the
  NPC seed logged on entry to each `HIRE_BuildStock`, vendor draws as an oracle (finding § 11). Phase 0 (the table
  docs) had not landed, so the finding has no `tbl:` anchors for `Hireling`/`HireDesc`; column names are from the
  `.txt` header.
- **2026-10-15 — Phase 1 and Phase 1b accepted with fixes, boundary ruled (architect).** hirelings/0001 meets every
  *Done when* bullet of both phases: C 11, I 50, L 19 (the 19 `[L]` are the *Leads used* verdicts; the lane's 20th
  was a mention of the items/quality lead in § Answer, reworded). Spot-checked in the pinned `Game.exe` (r2): the
  `ExpForLevel` product `(L+1)·L·L·e` at 0x00663790; the entry level `playerLevel − 5 + low mod 5`, min 2, at
  0x00663874–0x006638BB; `Str/Lvl`/`Dex/Lvl` `sar 3` on `+0x38`/`+0x40` in `RollEntry`; `Resist/Lvl` (`+0x60`)
  `cdq; and edx, 3; add; sar 2` at 0x00572A77–0x00572A83; the client skill level `sar 5`, cap 32, at
  0x004B115A–0x004B1178; the 0x450-byte table and the NPC-seed call in `HIRE_BuildStock`. All hold. The two
  second-code-path `[C]` raises qualify under evidence-rules § Tags (1): `HIRELING_RollEntry` and
  `sub_004B1090_ClientMercInit` are distinct functions (siblings of `MERC_SetLevel` under `MERC_Init`, and client
  code), reading the same `hireling` bytes with the same operation. Fixes applied in review: the raise is scoped to a
  non-negative product `column·d` (floor and truncation differ for a negative per-level column even at `d ≥ 0`; every
  stock per-level column is ≥ 0) and to the column arithmetic only, since `RollEntry` always uses the first band's
  row, so the band choice of `HIRELING_GetRecord` stays `[I]`. Contradictions: (a) `Resist/Lvl` ÷4 and (b) the entry
  level range are required Phase 2 cases; the experience formula (one observation that the d2dfg formula cannot give)
  and `HireDesc` (data) are settled; the backlog entry stays open until Phase 2. **Ruling: the boundary as
  recommended** (§ 11): the model starts from the NPC seed logged on entry to each `HIRE_BuildStock` and asserts it;
  vendor draws on the NPC seed between builds are an ADR-0004 oracle, not modelled; one check per game that the NPC
  seed is `Init(low of game draw 3)`. `HIRELING_RollEntry` is modelled on both sides (client list draw and server
  hire), with the player level logged on entry. Phase 0 still owes the `tbl:` anchors' targets; the spec (Phase 3)
  adds them.
- **2026-10-15 — Phase 0 accepted with fixes (architect review).** `excel_bin.py diff` rerun, 0 mismatches; `MercTest` and the rest of `test_d2s` pass; gate green after merging main. Fixed in review from the descriptor in hirelings/0001 § 1: the `hireling` layout's `Version` is u16 (+0x002 padding) and `Mode`/`Level`/`LvlPerLvl` are s8 (diff still 0, baseline unchanged). Rulings: the unloaded saves do not block; **Phase 2's first harness step loads `mercnova` (merc shown with its three items) and `mercclassic`** and pins their hashes, and the merc-save loads its *Done when* already lists cover the 21-save set. No compile probe: the descriptor settles `Head`/`Weapon` and skill slots 4–6. Class 560 has no row and no save; Phase 2 records it as unreachable on stock data. The `[L]` the finding settles go to an archivist follow-up (backlog).
- **2026-10-16 — Phase 2 landed (reverser, branch `lane/h33p2`), review requested.** run:2026-10-16-hirelings
  ([experiments](../findings/hirelings/experiments.md#run2026-10-16-hirelings)): 48 games on slot 1, `tools/hirelings.py
  check` 0 mismatches, `tools/monpool.py check` 10 788 / 10 788. Done-when coverage: 53 hire lists (Kashya, Greiz,
  Asheara, Qual-Kehk × Normal, Nightmare, Hell; ≥ 50) with one rebuild in one game (the trigger `[C]`); 49 hires with
  their stats in the world (≥ 20); `mercnova` (merc shown with its three items, via the same mercenary block in
  `mercmf`) and `mercclassic` loaded, hashes pinned in `test_d2s.py` (with the new `mercmf.json`); every merc save
  loaded in its difficulty (the four expansion classes × three; the classic three × three, refused in Act IV by
  `MERC_Create`'s act test and created in their own act), MonStatsInit level 1 reproduced by `monpool.py` for every
  class and difficulty (closes monsters/pool's hireling entry; 560 unreachable on stock data, no row); the stats
  after the level from experience reproduced by `hirelings.py`; three mercenary kills with the owner's magic find
  (items/quality `[L]` settled); Phase 1b cases (a) `Resist/Lvl` ÷4 and (b) list level −5 .. −1 settled. NPC seed =
  `Init(low of game draw 3)` in 48 of 48 games; S chained through every build with no vendor draw between, so the
  boundary oracle was never needed. Finding: 13 functions and 21 walkthrough statements to `[C]`; symbols 12 rows I →
  C. Tools: `tools/hirelings.py`, `tools/gdb/hirelings.{gdb,py}`, `tools/hireling_sessions.py`, `d2pilot.py npc …
  hire --buy`. Also fixed first (separate commit): `test_d2s.py` `RECIPE_BASES` lacked the 26 `calc-*`/`lv*` recipes.
  Not reached (stay `[I]`): classic hire lists and hires, Greiz hires, the free mercenary, refused hires, the stash
  payment, `NPC_OpenStore`'s build, `MERC_AddExp`, dead or empty headers, the written header, multiplayer.
- **2026-10-16 — Phase 2 accepted with fixes (architect review).** Rerun read-only: `tools/hirelings.py check` on the
  48 logs of `hire-run.lst` (`79ddb047…`) exits 0 with every count as reported (53 tables, 52 first builds and 1
  rebuild, 2625 draws, 723 `RollEntry`, 49 hires, 33 headers, 72 `MERC_SetLevel`, 3 kills, 0 mismatches);
  `tools/monpool.py check` 10 788 / 10 788; manifest (`4559f158…`) `sha256sum -c` all OK; `test_d2s.py` 43 OK. r2
  re-read: the NPC-seed step and `Init` at 0x005360D2–0x005360FB; `NPCSTORE_GetSeed` returning `[Game+0x1D24] + 8`;
  `HIRE_BuildStock`'s per-name step loop and its 10 `Range(n)` picks stepping past listed (`+0xC`) or hired (`+8`)
  entries with wrap (0x00576120–0x005761B5); the owner's stat-80 read at 0x005585F6 (the r2 breakpoint 0x005585FB is its
  return). All agree. Every new `[C]` names run:2026-10-16-hirelings (the three without it are Phase 1's data-check
  `[C]`); `symbols.csv` has no duplicate address or name, and its 12 promoted rows match the finding's table (the 13th
  row, `NPCSTORE_CtlCreate`, is items/vendors' and already C). Saves: every input is tool-built on stock data
  (ADR-0003: `mercmf.json`, the 21 merc saves, the 9 classic act variants that change only the difficulty bytes);
  no table edit, so ADR-0010 does not apply; the boundary oracle (ADR-0004) was not needed. The screenshot's next
  level 3 075 200 is `ExpForLevel(31)` = 32·31²·100. **Rulings:** (1) `mercnova` "shown with its items" is met
  through `MercMF`, whose `merc` block is byte-identical JSON to `mercnova.json`'s (checked), with MercNova itself
  loaded and reproduced in 3330. (2) Logger r1/r2: accepted; r1 was never committed, so the record now says so, and
  that no r1 `MFK` line is used. (3) Greiz failed in four tours: a pilot issue, not blocking (Greiz lists 10 builds in
  all three difficulties; Greiz hires stay `[I]`, the same code path as the other three sellers). (4) The hire-list
  detector's 1–2-row miss is accepted with the `--buy` fix; 3302/3303's 18 hires and lists stand. (5) The leftover
  MonStatsInit stats stay in *Open questions* as observations (no tag), correct. **NPC seed vs store seed:** the same
  object (`NpcControl+0x08`, returned by `NPCSTORE_GetSeed` to vendor and hire code), seeded once from game-seed draw
  3; items/vendors § A1's store seed is this seed, so there is no conflict. Fixes: hirelings/0001 now says so in the
  conventions, § Answer and § 2, and § 2's interleaving of vendor and hire draws is `[C]` by run:2026-10-15-vendors
  (C 42, I 25, L 19); the experiments record states r1's status; the stale reverser → reverser backlog entry on the
  `HIRE_BuildStock` oracle is struck. *Done when*: met (≥ 50 lists with a rebuild, ≥ 20 hires, every merc save
  loaded, MonStatsInit level by `monpool.py`, the magic-find kill, Phase 1b cases (a) and (b), `mercnova`/
  `mercclassic` pinned, class 560 recorded unreachable); named shortfalls, all `[I]` and none a *Done when* item:
  classic hire lists and hires, Greiz hires, the free mercenary, refused hires, the stash payment, `NPC_OpenStore`'s
  build, `MERC_AddExp`, dead/empty headers, the written header, multiplayer. **Phase 3 (spec-writer) next:** state
  the NPC seed as items/vendors' store seed (link § A1, do not define a second seed); the stock build pseudocode from
  § 3 with the `n + 10` call order; the stats table with the truncation (not floor) for `d < 0` and the clamps (life
  40, AR/defence 0 and absent); `RollEntry`'s first-band row vs `MERC_SetLevel`'s band row; the classic act test; and
  the not-reached list as `[I]`.
- **2026-10-16 — Phase 3 landed (spec-writer, branch `lane/s33p3`), review requested.** New
  [hirelings](../specs/hirelings/README.md) (draft), tags **{C: 89, I: 39, L: 8}**: the store seed linked to
  items/vendors § A1 (no second seed; vendor and hire draws interleave, `[C]` by run:2026-10-15-vendors); the
  triggers; `HIRE_BuildStock` as pseudocode with its `n + 10` call order (a step per name index, then 10 `Range(n)`
  picks probing past listed or hired entries with wrap); `HIRELING_RollEntry` (own seed, draw 1 type over the first
  band's rows, draw 2 level offset, floor eighths, price ≥ `Gold`); the hire and `MERC_Init`; the per-level stat
  table of `MERC_SetLevel` (band row, truncation for `d < 0`, resistances ÷4, clamps life 40 and AR/defence 0 with the
  stat absent); the load with the classic act test; class 560 unreachable; the mercenary's magic find. Two worked
  examples recomputed with `tools/hirelings.py` from the run's logs (read-only): session 3302's Qual-Kehk list (S
  `9c65f9a3:0000029a`, 77 draws, the 10 picks, three entries rolled, one showing floor against truncation) and
  `MercNova`'s load (L 30 from 2 790 000, life 288, resistances 54, next level 3 075 200). The not-reached paths are
  `[I]` and listed under *Open questions* with the MonStatsInit leftovers (observations, untagged in the finding);
  the four Phase 1b contradictions are under *Open questions* § Community sources as 1.14d differences. Updated:
  [monsters/pool](../specs/monsters/pool.md) § E2 and its *Open questions* (271, 338, 359, 561 logged; 560
  unreachable; C 79, I 30, L 4), [items/quality](../specs/items/quality.md) M3 (a mercenary's kill counts its own plus
  its owner's magic find; C 63, I 36, L 4), [save/d2s](../specs/save/d2s.md) § D (the merc header's read side
  run-checked, write side and dead flag still `[I]`; C 88, I 144, L 5), [monsters README](../specs/monsters/README.md)
  (C 14, I 1, L 0); glossary *Hire table*, *Mercenary*. Gate green. The research-map row `hirelings` is the
  architect's.
