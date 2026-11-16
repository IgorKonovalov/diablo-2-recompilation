# Skills experiments

Runtime records for [skills/0001](0001-dispatch.md) and the later skills findings (plan 0045 Phase 2). Harness and
evidence rules: ADR-0003, ADR-0004, ADR-0011, ADR-0013, ADR-0014;
[tooling](../../../.claude/skills/reverser/references/tooling.md),
[harness-play](../../../.claude/skills/reverser/references/harness-play.md).

Plan 0045 Phase 2's harness runs come first (part 2, run:2026-10-27-skills, then part 1, run:2026-10-25-skills); plan
0046's emulated runs (ADR-0015) follow.

## run:2026-10-30-skills-catalogue

Plan 0046 **Phase 2** (harness sample): for each skill family with no tier-A member, one representative logged on the
machinery of `tools/skills.py`, so the catalogue's draws and outputs are checked in the game and not only under
emulation. The families are the plan's batches with no tier-A entry: the monster skills **8a** (Skills rows 156–189),
**8b** (190–289) and **8c** (290–338), and the **item** casts (batch 10; `ItemEffect` 53 Chain Lightning, do 151 and the
stat-event handler 20 path of skills/0003 § 2). The Baal Tentacle item carried from batch 8c is under *Shortfalls*.

- **Question:** does `tools/skills.py` reproduce sessions in which monsters of each family use their skills and a
  player's item casts Chain Lightning, with 0 mismatches, and does one member of each family reach 30 events?
- **Setup:** 12 agent-driven sessions on harness slot 2 only (display `:9`, prefix `workspace/wineprefix-2`; slot 1
  held by another lane), single player, the pinned `game.exe` in `workspace/runtime/game` (stock data), gdb by
  `tools/d2run.py` with `-seed` per session. Logger `tools/gdb/skills.gdb` and `tools/gdb/skills.py` **rev 5**
  (unchanged from run:2026-10-27-skills; `sha256sum` of the `SKILLSLOG` revision line in each log), driver
  `tools/skills_catalogue_sessions.py` over `tools/skills_sessions.py` (its `until` step and `last_level` are this
  run's addition: a pilot command repeated until the player's level is the target) over `tools/d2pilot.py`
  (unchanged). Per session: `saves.py --slot 2 restore`/`aside p46h`, `d2run.py --install`, the steps, `slots.py stop
  2`; `saves.py --slot 2 restore p46h` at the end (aside empty, slot idle). The pilot only decides where to click.
- **Characters** (ADR-0013 § Neutral: tool-built, stock items and skill points, no test-state key), into
  `workspace/logs/skills/2026-10-30-skills-catalogue-saves/`: `SkillsSor` (`tools/d2s_recipes/skills-sor.json`, the
  run:2026-10-27-skills save byte for byte, sha256 `d033b674…`: Nova F1, Frost Nova F2, Static Field F3, Fire Bolt F4,
  Meteor F5, Blaze F6, Teleport on Shift + left) for the monster sessions, and the new **`SkillsChain`**
  (`tools/d2s_recipes/skills-chain.json`, sha256 `94f0b491…`, pinned in `tools/test_d2s.py` `RECIPE_BASES`; Barbarian
  clvl 85 on the stock `smpbar` base: two short swords, two rings and an amulet, each a magic item with the suffix
  record 443 *of Chain Lightning* (MagicSuffix `att-skill` 53, 8 % at skill level 5), Howltusk, Corpsemourn and
  Nosferatu's Coil at `roll: max`; Attack F1, Bash F2) for the item family. The monster sessions send the Sorceress
  with `farm --wp TAB,ROW` and `explore --melee --melee-button 3 --curse-keys F1…F6 --keys-cycle` (skills_sessions'
  `cast_explore`), 200 hops; the monsters act on their own. The item sessions walk the Barbarian with Attack.

### Sessions

| session | save | difficulty | seed | waypoint, area | what |
|---|---|---|---:|---|---|
| cat-a1-1 | SkillsSor | Normal | 5101 | 1,3 Stony Field | 8a (Nest only) |
| cat-a1-3, cat-a1-4 | SkillsSor | Normal | 5109, 5110 | 1,2 Cold Plains | 8a: fallen shamans (ShamanFire 160, Resurrect 181) |
| cat-a3-1, cat-a3-2 | SkillsSor | Normal | 5103, 5104 | 3,4 · 3,3 (Flayer Jungle, Great Marsh) | 8a: Submerge 176, FetishInferno 178; 8b: MonFrenzy 215 |
| cat-a5-1, cat-a5-2 | SkillsSor | Normal | 5105, 5106 | 5,2 Frigid Highlands · 5,3 Arreat Plateau | 8b: Imp Inferno 282, Imp Fireball 283; 8c: Imp Fire Missile 299, Imp Teleport 330, Overseer Whip 295, Cry Help 290, Healing Vortex 291 |
| cat-a5-3 | SkillsSor | Nightmare | 5107 | 5,2 | 8c: Overseer Whip, Healing Vortex |
| cat-baal-1 | SkillsSor | Normal | 5121 | 5,9, two Baal Temple Down warps, Throne of Destruction (131) | Baal route of tools/h6d_sessions.py `baal()`; Baal never reached (Shortfalls); BloodLordFrenzy 328 |
| cat-chain-1 … 3 | SkillsChain | Normal | 5111–5113 | 1,2 · 1,3 · 1,4 | item: Chain Lightning cast by the *of Chain Lightning* items on strike |

No session was aborted for the kept set. Logs `workspace/logs/skills/2026-10-30-skills-catalogue-<session>.log`
with `.pilot.txt` and `-shots/`. Two development logs, `dev-p46h-cat-a1-1` (a 50-hop first try that finished in 86 s)
and `dev-p46h-cat-baal-1` (the same Baal route started with `wpchain 5,9`, whose waypoint list did not open on this map
seed), are kept under `dev-p46h-manifest.sha256`; no claim rests on them. One first Baal try was killed by the lane
after that `wpchain` failure, before any result.

- **Procedure** (from the worktree; the check under a 4 GB scope; kept outputs by `systemd-run --user --scope -p
  MemoryMax=4G python3 -I <worktree>/tools/skills.py …` from `workspace/logs/skills`):
  ```
  python3 -I tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/skills-chain.json \
      workspace/runtime/saves-backup/p0005/smpbar.d2s workspace/logs/skills/2026-10-30-skills-catalogue-saves/SkillsChain.d2s
  python3 -I tools/saves.py --slot 2 aside p46h
  python3 -I tools/skills_catalogue_sessions.py run --slot 2 --tag p46h \
      --saves workspace/logs/skills/2026-10-30-skills-catalogue-saves --run 2026-10-30-skills-catalogue \
      cat-a1-1 cat-a3-1 cat-a5-1 cat-chain-1 cat-chain-2 cat-chain-3 cat-a1-3 cat-a1-4 cat-a5-2 cat-a3-2 cat-a5-3 cat-baal-1
  cd workspace/logs/skills
  skills.py check 2026-10-30-skills-catalogue-cat-*.log --json …-check.json --gaps …-gaps.txt > …-check.txt
  skills.py tally 2026-10-30-skills-catalogue-cat-*.log > …-tally.txt
  skills_catalogue_tally.py 2026-10-30-skills-catalogue-cat-*.log > …-families.txt
  ```
  (the sessions ran in four `run` calls, in this order of sets: a1-1, a3-1, a5-1; chain-1; chain-2, chain-3, a1-3,
  a1-4, a5-2, a3-2, a5-3; baal-1).
- **Tool revisions** (all in this commit): `tools/skills.py` `f8a2f6e0…`, `tools/test_skills.py` `85d963eb…` (15 tests,
  passing: the 13 of run:2026-10-27-skills and two new, each both ways), `tools/skills_sessions.py` `f230e15a…`,
  `tools/skills_catalogue_sessions.py` `6d964045…`, `tools/skills_catalogue_tally.py` `c059f0a7…`. The checker's two
  additions (both found by this run): the creation callback `0x005AC040` (§ Result) and `ReturnDamage` when the
  returned damage kills the cursed unit.
- **Kept:** `workspace/logs/skills/2026-10-30-skills-catalogue-manifest.sha256` (`dc673ebd…`, 81 files: the 12 logs and
  their pilot files and screenshots, the two saves, `check.txt` `2bd2b4fb…`, `check.json`, `gaps.txt`, `tally.txt`,
  `families.txt`); `sha256sum -c` from that directory passes.

### Result

**0 mismatches** over the 12 logs (`check.txt`: every row 0; `mismatches: 0`). Counts: 44 773 missile creations
(`MC.gameseed`, `MC.seed` 44 737 and `MC.cbseed2` 36, `MC.range`, `MC.vel`, `MC.accel` each 44 773), 13 576 hit ends
(`MH.end`), 2 612 `SDO.seed` and 2 616 `SST.seed` (the modelled player rows), 13 671 `CHAIN.caster` and 36 540
`CHAIN.gameseed` chained pairs, 20 `CHAIN.caster+logged`, 13 881 `BD.seed` builds, 4 813 `PAY`, 22 751 `MAS.seed` and 22 484 `MAS.stats`
calls. The two additions the run forced:

- **12 `MC.seed` mismatches in the first check** (cat-a5-1, before the checker was changed): a class-408 missile
  (`catapultchargedballbolt`) created by a catapult spotter (class 516, the skills of rows 287 and 288) whose seed
  was not the creation seed `Init(step(game).low)`. Its parameter block's `+0x54` word is `0x005AC040`
  (`sub_005AC040_MissCbReseedPathX`), a creation callback no logger line covers. Reading it with `r2` (`pD` at
  `0x005AC040`): `0x0064A300` clamps the range to 255, `0x00648A00(path)` gives the word that `0x00650E40` takes as
  the new seed's low (high `0x029A`) at `0x005AC073`, then `0x00648CF0(path, 10)`, `0x00648E70` and `0x00649970(path,
  missile, 0)` follow, the same three path calls as `0x005C9290`'s. `skills.py` now checks that the creation seed lies on the
  stream from `Init(path word +0x10, 0x029A)` (`MC.cbseed2`): **36 of 36 creations at 10 steps** (24 in cat-a5-2,
  12 in cat-a5-1), and the unmodelled steps are reported (`0x005AC040 steps after the Init`).
- **1 `EVH.seed` mismatch** (cat-chain-3, `n=1802`): `ReturnDamage` (`0x005C5F50`, Iron Maiden 76, event 5) is a
  no-draw handler in the table, and the cursed monster's seed stepped once. Its life went from 1 173 to 0 in the
  handler (EVR `st` has no stat 6), the next events being the player's kill events. The checker now reports, and does
  not check, the steps of a `ReturnDamage` call that kills the cursed unit (one case, 1 step); the same handler where
  the unit survives stays a no-draw check.

Coverage (`families.txt`, `tally.txt`; the do events of a monster mode that repeats per frame are many more than its
starts, both are given):

| family | member logged | SrvStart | SrvDo | floor |
|---|---|---:|---:|---|
| 8a | 181 Resurrect (do 97) | 66 | 66 | met (≥ 30) |
| 8a | 160 ShamanFire (do 85) | 39 | 37 | met |
| 8a | 176 Submerge (st 51, do 94) | 58 | 4 971 | met; 178 FetishInferno 12 · 14, 167 Nest 11 |
| 8b | 282 Imp Inferno (st 59, do 126) | 33 | 1 004 | met; 283 Imp Fireball 48 · 43, 215 MonFrenzy 26 · 15 |
| 8c | 299 Imp Fire Missile (do 132) | 213 | 198 | met |
| 8c | 330 Imp Teleport (do 129) | 354 | 347 | met |
| 8c | 295 Overseer Whip (do 131) | 61 | 61 | met; 328 BloodLordFrenzy 538 · 980 (do 109, shared with 8b), 291 Healing Vortex 22 · 21, 290 Cry Help 17 · 14 |
| item | 53 Chain Lightning, cast by the *of Chain Lightning* items (do 26 with the item argument; `ItemEffect` 53) | 0 (item casts skip `SKILLS_SrvStart`) | 64 | met |

The 64 item casts are the 64 `EVH SkillOnEvent roll succeeded (cast: a boundary)` fires of event 7 (`EVH.seed1`: at
least the one roll draw, 64 of 64, the steps after the first reported: 1 in each, as in the 28 casts of
run:2026-10-27-skills); 102 more fires failed the roll with exactly one draw (`EVH.seed`).

Draws of the logged monster rows (caster's seed steps from `SDO` entry to exit, from `check.txt`; reported, the
rows are not in `SDO.seed`'s modelled list): 0 in every do event of 160 (37), 176 (4 971), 178 (14), 181 (66), 282
(1 004), 283 (43), 290 (14), 291 (21); 1 in all 61 of 295 and 198 of 299; 0 in 285 and 1 in 62 of 330's 347 (the
nested missile creation's or the delivery's, listed with the lines between in `gaps.txt`); 1 in 11 and 4 in 4 of
215's, 1 in 350 and 4 in 630 of 328's (do 109's restart and hit, which the batch left `[I]`); one 9-step Nest event
(10 of 11 with 0). `MC owner draws` give 1 305 critical rolls and 43 468 creations with none (run:2026-10-30-skills-catalogue).

### Shortfalls

- **Baal Tentacle (do 140, the stale-word question of skills/0018 § 7): not reached.** `cat-baal-1` followed
  tools/h6d_sessions.py's route: the Worldstone Keep 2 waypoint, the two Baal Temple Down warps (levels 130 and 131),
  a 421 s sweep of the Throne of Destruction (456 hops, 7 Nova casts), the
  Worldstone Chamber portal step (`objop` 563: 0 of 1 in 100 s, no portal) and a 420 s hunt for class 544 ("class
  544 never seen"), the player at 2 % life after Blood Lord Frenzy hits. No `baalcrab` (class 544) line, so no do 140
  event: the arm's two-or-three draw question stays `[I]`, to the monster-AI plan or a session that gets the waves
  started (fn:sub_005D2C20_SkillDo140BaalTentacle@0x005D2C20, run:2026-10-30-skills-catalogue). Why they did not start is not established: this session differs from h6d's `baal-fresh` in the save (here
  `SkillsSor`, every quest done, no Energy Shield key) and the map seed.
- **Item family: only the `att-skill` Chain Lightning cast.** The scroll and book rows (do 113) and the `charged`
  suffixes (records 529, 530, casting through the item's charges) were not attempted: no session step uses an
  inventory item. The 64 casts are `SKILLS_SrvDo` calls of skill 53 at level 5 with the item argument set and the
  effect argument 1 in all 64 (the argument that selects the `ItemEffect` entry, skills/0015 § 4); the logger does not
  record which do function ran, so do 151 itself is not shown, and the checker has no model of its outputs: the
  caster's steps are reported (`SDO skill 53 caster steps: 0 x64`), not checked. Two Iron Maiden casts (76, level 2,
  effect 0) came from another proc source of the recipe (Corpsemourn), not from the suffix.
- **Per-family chained pairs:** the checker counts `CHAIN.gameseed` (36 540) and `CHAIN.caster` (13 671) over the
  whole run, not per family. Missile creations by monster casters are 44 773 − the player's; a per-family split was
  not made. The monster-caster resyncs are plan 0052's, as in run:2026-10-27-skills (`gaps.txt`: 2 059 lines).
- **8a is mostly Act 1 and Act 3:** no Act 2 monster of rows 156–168 (sand raiders 156, unravelers 157, maggots)
  was logged.

*2026-11-10:* plan 0066 batch S2a re-checked this run's logs with `tools/skills_s2a.py` (0 breaks); the counts are in [run:2026-10-27-skills § Addendum 2026-11-10](#addendum-2026-11-10-plan-0066-batch-s2a-new-checks-over-the-three-kept-skills-runs-lanen66b).

*2026-11-15:* plan 0066 batch S2b checked the missile lines of this run's logs with `tools/skills_s2b.py` (0 breaks); the counts are in [run:2026-10-27-skills § Addendum 2026-11-15](#addendum-2026-11-15-plan-0066-batch-s2b-the-missile-lines-of-the-three-kept-skills-runs-lanen66f).

## run:2026-10-27-skills

Plan 0045 Phase 2 **part 2** (ruled at the part 1 review, 2026-10-27): the models and sessions part 1 lacked. Part 1's
logs (run:2026-10-25-skills, below) are kept unchanged and re-checked here with part 2's checker; the floors count both.

- **Question:** with a `SKILLS_CanUse` breakpoint, models of `MonAttackStats`, the stat-event handlers, the state-52
  hook, the summoned unit's seed and stats and the end of a damaging hit, and the caster's own logged draws added to
  the chaining, does `tools/skills.py` reproduce part 2's sessions with 0 mismatches, and do both parts together meet
  plan 0045 Phase 2's floors?
- **Setup:** 15 agent-driven sessions on harness slot 2 only (display `:9`, prefix `workspace/wineprefix-2`; slot 1
  held by another lane), single player, the pinned `game.exe` in `workspace/runtime/game` (stock data), gdb by
  `tools/d2run.py` with `-seed` per session; Normal, and Nightmare for `spike-1`/`spike-2`. Logger
  `tools/gdb/skills.gdb` (`92420a1c…`, unchanged) sourcing `tools/gdb/pilot.py` (`1ad48a4c…`, unchanged) and
  `tools/gdb/skills.py` **rev 4** (`5459da8a…`, commit `3b5b843`) for `barh-1`, `ref-sor-1`, `ref-low-1`, **rev 5**
  (`e28d1344…`, commit `a06e825`) for the other 12 (each log's `SKILLSLOG` line names its revision). Rev 4 adds to
  rev 3: `CU0`/`CUL`/`CU1` (`SKILLS_CanUse` `0x00647960` entered from the four request call sites, return addresses
  `0x00549B0F`, `0x00549B49`, `0x00549BC6`, `0x00549C11`, and its ten `ret 8`s; `CUL` the level bonus `EAX` and base
  `EDI` at `0x00647589` inside `SKILLS_ManaOk`); on `EVH` the handler's own stat value (`sv`, the record's
  `stat << 16 | layer`), the other unit's type, stats and MonsterData `+0x16` flags, the packet's first 0x70 bytes; on
  `MAS0`/`MAS1` the elemental stats 48–66 and 315–317 and the game's `+0x6A/+0x6D/+0x70/+0x74`; `SP1` with stats 6–9,
  12, 19, 21, 22, 31, 36, 37, 39, 41, 43, 45, 100; `THR`/`DRR` written outside the logged spans too (capped at 20 000
  each). Rev 5 adds the client's per-frame check of a skill button (`SKILLS_CanUse` returning to `0x004D9FCA`), written
  (`"cl": 1`) only when that skill's code differs from the last one written for it, and keys the pending calls by ESP.
  Driver `tools/skills_sessions.py` (`97c0820f…`) over `tools/d2pilot.py` (`3ccabe20…`, main's, unchanged by this
  lane): `saves.py --slot 2 aside p45k` before each `run`, per session `restore`/`aside p45k`, `d2run.py --install
  p45k`, then the steps of `SESSIONS` (the waypoint, `cast` presses with a right-click beside the player, `explore
  --melee --melee-button 3 --curse-keys … --keys-cycle`, the Necromancer's `corpse` step); `slots.py stop 2` after
  each session, `saves.py --slot 2 restore p45k` at the end (aside empty, slot idle). The pilot only decides where to
  click.
- **Characters** (ADR-0013 § Neutral: tool-built by `skills_sessions.py build` from the recipes on the stock `p0005`
  base saves, stock items and skill points, no test-state key), into `workspace/logs/skills/2026-10-27-skills-saves/`:
  the eight part 1 saves, byte for byte part 1's (`cmp`), and two new recipes. `SkillsBarH`
  (`tools/d2s_recipes/skills-barh.json`, clvl 85; Bash F1, Kick F2, Left Hand Throw F3, Attack F4, Howl F5; dual
  wielding *Fleshripper* and *Lacerator*; *Howltusk*, *Corpsemourn*, *Dracul's Grasp*, *Nosferatu's Coil*,
  *Gorefoot*, *Nagelring*, *Nature's Peace*, *Atma's Scarab*, all `roll: max`): the handler stats (prevent heal,
  crushing blow, open wounds, slow, knockback, howl, thorns, damage to mana, skill on attack and on get-hit, mana and
  life after a kill, rest in peace) and Left Hand Swing through the dual-wield Attack alternation. `SkillsSorLow`
  (`skills-sorlow.json`: `SkillsSor` with energy 10, mana 30 and a belt of `hp5`): the mana refusals.

### Sessions

| session | save | difficulty | seed | what |
|---|---|---|---:|---|
| barh-1 … barh-3 | SkillsBarH | Normal | 4611–4613 | waypoint 1,2 · 1,3 · 1,4; the ten-key cycle `F1 F2 F3 F4 F4 F5 F2 F3 F4 F4` walking |
| ref-sor-1, ref-sor-2 | SkillsSor | Normal | 4601, 4602 | 20 casts in the Rogue Encampment, waypoint 1,2 · 1,3, 40 Meteor and 20 Static Field presses, then explore |
| ref-low-1, ref-low-2 | SkillsSorLow | Normal | 4603, 4604 | (ref-low-1: 20 town casts) waypoint, Nova, Fire Bolt, Meteor, Frost Nova presses |
| amaj-3 | SkillsAmaJ | Normal | 4621 | waypoint 1,4; Plague Javelin twice in the four-key cycle |
| nec-3 | SkillsNec | Normal | 4622 | waypoint 1,3; `corpse` (420 s, 60 corpses), then Amplify Damage and Bone Armor |
| ass-3 | SkillsAss | Normal | 4623 | waypoint 1,4; Fire Trauma twice in the cycle |
| pal-3 | SkillsPal | Normal | 4624 | waypoint 1,3; 25 Holy Shield casts, then explore |
| blaze-1 | SkillsSor | Normal | 4625 | waypoint 1,2; Blaze twice and Nova, **walking** (C4) |
| spike-1, spike-2 | SkillsSor | Nightmare | 4626, 4627 | waypoint 1,4 (Dark Wood) · 1,5 (Black Marsh), the quill-rat areas (C2) |
| spike-3 | SkillsSor | Normal | 4628 | waypoint 1,4 |

No session was relaunched, aborted or died. Logs `workspace/logs/skills/2026-10-27-skills-<session>.log` (49 MB),
with their `.pilot.txt` and `-shots/`. Two development sessions before the run, `dev-p45k-dev-barh` (rev 4 before
the request filter: its `CU` lines include the client's per-frame calls, which a gdb condition on `[esp]` failed to
exclude; the filter moved into Python) and `dev-p45k-dev-barh2` (rev 4 with the filter; Left Hand Swing on F4, which
the request handlers never received: the run uses the Attack alternation), are kept under
`dev-p45k-manifest.sha256` (`0450c0c9…`); no claim rests on them.

- **Procedure** (from the worktree; checks under a 4 GB scope; the kept outputs by
  `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/skills.py …` from `workspace/logs/skills`):
  ```
  python3 -I tools/skills_sessions.py build --saves workspace/logs/skills/2026-10-27-skills-saves
  python3 -I tools/saves.py --slot 2 aside p45k
  python3 -I tools/skills_sessions.py run --slot 2 --tag p45k --saves workspace/logs/skills/2026-10-27-skills-saves \
      --run 2026-10-27-skills barh-1 ref-sor-1 ref-low-1 blaze-1 spike-1 nec-3 amaj-3 ass-3 pal-3 barh-2 ref-sor-2 \
      ref-low-2 spike-2 spike-3 barh-3
  cd workspace/logs/skills
  skills.py check 2026-10-27-skills-*.log --json 2026-10-27-skills-check.json --gaps 2026-10-27-skills-gaps.txt \
      > 2026-10-27-skills-check.txt
  skills.py tally 2026-10-27-skills-*.log > 2026-10-27-skills-tally.txt
  skills.py check 2026-10-25-skills-*.log --json 2026-10-27-skills-part1-check.json \
      --gaps 2026-10-27-skills-part1-gaps.txt > 2026-10-27-skills-part1-check.txt     # part 1's logs, unchanged
  skills.py tally 2026-10-25-skills-*.log 2026-10-27-skills-*.log > 2026-10-27-skills-tally-both.txt
  skills.py audit $(cat workspace/logs/combat/c37p2-run.lst) $(awk '{print $4}' workspace/logs/stats/s1017-manifest.txt) \
      workspace/logs/combat/p47h-owf-n-andariel-p8.log > workspace/logs/skills/2026-10-27-skills-audit.txt   # from the root
  ```
  Checker `tools/skills.py` `c09f9419…` (it gives every kept output); its tests `tools/test_skills.py` (`89f4d098…`, 12
  tests, passing: part 1's 8 and MonAttackStats, a handler, `SKILLS_CanUse` and the summon's seed, each both ways).
- **Kept:** `workspace/logs/skills/2026-10-27-skills-manifest.sha256` (`08b79a9b…`, 49 files: the 15 logs and their
  pilot files, `check.txt` `f6e4df6c…`, `check.json` `a9e72b5e…`, `gaps.txt` `6843be4a…`, `tally.txt` `41f45171…`,
  `part1-check.txt` `82688917…`, `part1-check.json` `5df6ffee…`, `part1-gaps.txt` `5f43d175…`, `tally-both.txt`
  `48561615…`, `audit.txt` `28f85c9a…`, the 10 saves); `sha256sum -c` from that directory passes.

### Result

**0 mismatches** over part 2's 15 logs and over part 1's 18 logs re-checked (`check.txt`, `part1-check.txt`: every
row 0). The new checks, part 2 and the re-check of part 1:

| check | part 2 | part 1 re-checked | what it asserts |
|---|---:|---:|---|
| `MAS.seed`, `MAS.stats` | 13 905, 13 693 | 13 050, 12 732 | `MonAttackStats`: the unit's seed steps by the `El<e>` rolls only (21 one-draw calls, all `El1`), and stats 21, 22, 19 are MonLvlStats by the mode's `A1`/`A2`/`S1` columns (the other column sets would give other values in 13 683 and 12 700 of them); a summon's other-list offset learned at its first call (4 and 10 summons, 3 061 and 2 632 later calls checked through it); 2 218 calls of the Raven class (419), which has a `SkillDamage` owner pair, and 208 + 308 calls with no stat list yet, reported |
| `MAS.elem` | 2 | — | an applied `El1` (cold, type 4; poison, type 5): its stats as written (the poison 10 × and 2 × scalings) |
| `EVH.seed`, `EVH.seed1` | 991, 28 | 284, 0 | the handler unit's seed steps by the handler's own draws: 0, or 1 for knockback, howl (gated on a plain monster), stupidity, open wounds, crushing blow; at least 1 for the casts of 20 and 21 |
| `EVH.mana`, `EVH.life` | 78, 78 | — | mana and life after a kill: `+= sv << 8`, capped at stat 9 / 7 |
| `EVH.ow` | 120 | — | open wounds' roll `low % 100 < sv` against its `STA` state 62 (82 hits, 38 misses) |
| `PH.state52`, `PH.seed` | 333, 333 | 585, 585 | the prevent-heal hook: state 52 for 120 000 frames with stat 31 = 0 exactly when the player attacker's stat 117 ≠ 0 (86 applies, 247 without), no draw |
| `CU.code` | 1 340 | — | `SKILLS_CanUse`'s code: 1 126 request calls (all code 0) and 214 client changes of code (129 to 0, 8 to 1, 76 to 8, 1 to 6) |
| `SP.seed`, `.gameseed`, `.stats` | 4 each | 215 each | the summon's seed `Init(step(game).low)` in its `SUnitCreate`; its life (stat 6 = 7) and AC (31) from `tools/monstats.py`'s appearance and HP draws on that seed (207 Ravens with a 20–32 HP range) |
| `MH.end` | 3 166 | 710 | a damaging hit of a row with no hit function: the result and stat 328 (137 + 139 ends at the unit, 12 + 118 pierce uses, 3 017 + 453 continuing rows with no `CollideKill`) |
| `CHAIN.caster+logged` | 45 | 90 | a caster resync attributed by the unit's own logged draws and the logged exits of the spans and boundaries between |

Part 1's other checks re-run unchanged in value (`MC`, `MF`, `BD`, `PAY`, `SL`, `RSK`, `SST.seed`, `SDO.seed`,
`CHAIN`): `part1-check.txt` repeats part 1's counts row for row.

Coverage against the *Done when* of part 2 (part 1 and part 2 together, `tally-both.txt` unless named):

- **Skill uses: met.** 3 183 do events (1 840 + 1 343) and 2 985 start events (1 688 + 1 297); 2 375 do events in the
  26 tier-A rows. Every tier-A row at ≥ 30 except **70 Raise Skeleton, 12** (8 + 4: the Necromancer's `corpse` step
  raises few; short): 0 Attack 188, 1 Kick 32, 2 Throw 53, 4 Left Hand Throw 36, 5 Left Hand Swing 30, 10 Jab 108,
  12 Multiple Shot 36, 25 Plague Javelin 45, 36 Fire Bolt 89, 42 Static Field 104, 44 Frost Nova 71, 48 Nova 93,
  54 Teleport 378, 56 Meteor 117, 66 Amplify Damage 61, 68 Bone Armor 34, 98 Might 90, 102 Holy Fire 35, 117 Holy
  Shield 65, 126 Bash 82, 130 Howl 74, 221 Raven 207, 225 Firestorm 221, 251 Fire Trauma 61, 259 Fists of Fire 53.
  Kick and Left Hand Throw are cast from a hotkey bound by the recipe; Left Hand Swing only through the dual-wield
  alternation of Attack (skills/0001 § 1), the F4 binding of the development session reaching no request handler.
- **Refusals, with `CanUse`'s code: named short.** The request handlers received no refused request: the client runs
  the same `SKILLS_CanUse` on its own copy of the player every frame (`0x004D9FC5`) and sends no request for a refused
  skill, so all 1 126 request calls return 0. The refusals are the client check's: **delay** (code 8) 76 changes,
  **mana** (code 1) 8, an aura (code 6) 1; the **town** refusal is `SKILLS_SrvStart`'s `InTown` test, not a `CanUse`
  code, and the 60 town casts of `ref-sor-1`, `ref-sor-2` and `ref-low-1` reached no request (none sent): 0. Delay at about 30, mana and town short (rare-branch).
- **Handlers: met.** 1 303 `EVH` fires (284 + 1 019) over six event kinds (1, 2, 5, 6, 9, 11), event 9 (kill) 328;
  every fire checked for its seed effect (`EVH.seed`/`.seed1` 1 303 = 284 + 991 + 28); state 52 applied 86 times.
- **Summons: met.** 219 (215 + 4), each with its seed, level and stats predicted to the monsters/stats boundary.
- **`MonAttackStats`: met.** 26 425 calls predicted (12 732 + 13 693), 13 050 + 13 905 seeds.
- **Hit ends and pierce uses: met.** 276 ends of a missile at a unit it damages (139 + 137) and 130 pierce uses at a hit
  (118 + 12), besides part 1's 105 missed to-hits.
- **Re-seeds at the Q15 sites other than `0x005C9290`: named unreached.** No breakpoint sits on them and no session's
  row reaches them by skills/0003 § 9's *Reached by* column: `0x005ACDF0` (hit 58, Missiles row 654), `0x005D40F0`
  (do 37), `0x005D5BF0` (a catalogue hit function, skills/0007), the call at `0x005AC073` (in `0x005AC040`, reached from the hit functions at
  `0x005AC14B` and `0x005AC525`), and `0x00645390` (no reference in the image). `0x005C9290`: 168 more (`MC.cbseed`, 38 steps
  after the Init each, a monster's class-195 missiles).
  *2026-10-30:* the call at `0x005AC073` is reached, in 36 creations ([run:2026-10-30-skills-catalogue](#run2026-10-30-skills-catalogue)).
- **C2: short.** 22 `spike2` creations (Normal Dark Wood's quill rats, `amaj-3` and `ass-3`), all at level 1, where
  `(VelLev · 1) / 8` is 0 and so does not separate the `VelLev` term; the Nightmare sessions met no quill rat.
  **C4: met.** 271 `blaze` creations (`LevRange` 25) at Blaze level 2 while walking, every range checked (`MC.range`).
- **The 304 caster resyncs of part 1, re-checked** (`part1-gaps.txt`): of the 133 player resyncs, **90 are attributed**
  by the unit's own logged draws (the `THR` rolls, with the delivery boundaries' logged exits), and 43 are listed with
  their lines: 31 with the player a hit's defender between (its defence rolls, combat/0001, which part 1's logger
  wrote only inside an open span), 11 with no logged line naming the player, 1 other. The 171 monster resyncs are
  left to plan 0052 (monster AI): 131 where the walk reaches a logged observation of the monster's seed (a
  `MonAttackStats` entry, mostly) that its logged draws do not explain, the AI's draws among the candidates, 33 with no line naming the monster, 7 as a defender. Part 2's own 308 resyncs: 45 attributed; 103
  player resyncs listed (60 as a defender, 17 nested in a span that opened before the first event's exit, 11 off the
  stream within 4 096 steps, 2 with no line, 13 other); 160 monster resyncs left to plan 0052 (`gaps.txt`).
- **The handler audit** (`audit.txt`): the 3 461 handler fires of run:2026-10-16-combat, run:2026-10-17-stats and the
  *Fleshripper* log are all replaced by the handler model for their seed effects (0 mismatches): crushing blow 1 637,
  open wounds 1 637, slow 59, heal after kill 57, skill on attack 59 (at least one draw: the cast is a boundary), life
  tap 12. Their outcomes (the crushing-blow life, the open-wounds state) stay combat.py's checks; the 59 heal-after-kill
  fires carry no handler stat value in those logs, so their life effect is not replaced. The missile-packet and
  aura-run oracles stay as part 1 named (ruling (b)).

Readings the run adds or changes, in the findings: `MonAttackStats` clears its list first and gives every `El<e>` El1's
bounds (skills/0001 § 18, monsters/0004 § 9); the delay state ends at frame `set + d` (§ 18); the client's own
`CanUse` filters refusals before any request (§ 18).

### Addendum 2026-11-10: plan 0066 batch S2a, new checks over the three kept skills runs (`lane/n66b`)

Plan 0066 Phase 1 batch S2a (a-logs; [inventory § 4](../../plans/0066-inventory/README.md#4-batch-list)): new checks
over the kept logs of this run, run:2026-10-25-skills and run:2026-10-30-skills-catalogue, unchanged. No session.

- **Procedure** (from `workspace/logs/skills`, under a 4 GB scope):
  `python3 -I <worktree>/tools/skills_s2a.py check 2026-10-25-skills-*.log 2026-10-27-skills-*.log
  2026-10-30-skills-catalogue-cat-*.log > 2026-11-10-s2a-check.txt` (45 logs; exit 0, `SURVEY s2a breaks=0`).
  Tool `tools/skills_s2a.py` `f3084824…` (it reads the logs with `tools/skills.py`'s parser, unchanged); output
  `2026-11-10-s2a-check.txt` `f69b8ec8…` (680 lines), kept under `2026-11-10-s2a-manifest.sha256`; `sha256sum -c`
  from that directory passes. A first form of the start/do check (no "return 0 before the payment" case) gave 6
  breaks on monster do events of row 181 that return 0; the kept revision models E4's `r = 0` return, and the
  development outputs were not kept.
- **What the logs hold** (rev 3 logs have no `CU` line, so the request checks cover the rev 4 and 5 logs of this run
  and of run:2026-10-30-skills-catalogue; `SrvDo`'s and `SrvStart`'s callers are told apart by the logged return
  address):

| check | count | result |
|---|---:|---|
| request calls of `SKILLS_CanUse` from the four request sites | 4 367 (2 825 location form, 1 542 unit form) | every one returns 0 and leaves the caster's seed unchanged (CU1 `s` = CU0's) |
| code-0 request then the player's `SrvStart` (from `StartUsedSkill`, `0x0056FC27`) of the same skill in the same frame, before the next request | 4 344 (2 823 + 1 521) | 0 breaks; 12 unit-form Kick requests start in a later frame (B3's run, the run itself not logged); 11 code-0 requests (9 unit, 2 location) have no start before the next request |
| player starts from `StartUsedSkill` in the rev 4/5 logs | 4 356 | 4 344 with a code-0 request in their frame, the other 12 the Kick starts above |
| stat 328 (`b328` of MC0's player owner) between two observations | 61 025 pairs, 1 660 with ≥ 1 request between | the rise equals the number of request calls between, 0 breaks |
| dual-wield alternation (barh, requests of skills 0 and 5) | 59 requests, 56 consecutive pairs | 56 of 56 alternate |
| `SrvStart`: a row with no start function | 6 216 | returns 1 |
| `SrvStart`: direct `PAY` | 1 602 with one (808 player, 794 monster: a start function returning non-zero, not `usemanaondo`, `noCost` 0); 6 267 with none (no start function 6 216, `usemanaondo` 45, a start function returning 0 6) | as D3, 0 breaks; PAY's `(id, lvl)` the start's in 1 602 |
| `SrvStart` callers | 7 827 from `StartUsedSkill` (5 843 player, 1 984 monster), 42 from `0x005CDF75` inside do 109 | `noCost` 0 in all 7 869 |
| `SrvDo` callers and `(pay, item, effect)` | `DoUsedSkill` 14 168, all (1, 0, 0); `EVENT_SelectedAuraTick` (`0x0056FD39`) 119 and the aura select (`0x0056FFB9`) 6, (1, 0, 0); `ITEMSKILL_Cast` (`0x005FDC34`) 86, (0, 1, 1) 83 and (0, 1, 0) 3 | — |
| `SrvDo`: direct `PAY` | 6 295 with one (no start function 6 250 incl. 119 ticks and 6 selects, `usemanaondo` 45); none in 8 084 (a start function, not `usemanaondo`, 7 974; no start function but `r = 0` and no `srvmissile` 24; the 86 item casts); of the 59 do events returning 0 with no `srvmissile`, none pays | as E4, 0 breaks; PAY's `(id, lvl)` the do's in 6 295 |
| `SrvDo`: direct `DLY` | 613, all players: Firestorm 221 (`d` 15), Meteor 347 (30), Plague Javelin 45 (100) | one exactly when pay, a player, the row's `delay` set and the do goes on; none in the 13 766 others (the 8 266 monster do events from `DoUsedSkill` among them); DLY's frame = the do's in 613; PAY before DLY in 613; the `srvmissile` creations before PAY/DLY in 487 |
| do events from `DoUsedSkill` per player mode start | 5 843 starts | one in 5 794; 3 in each of 36 Jab (sequence) starts; 0 in 13 (the mode ended first) |
| monster starts by mode and bit 6 of `Unit+0xC4` at the entry | 2 026 (1 984 from `StartUsedSkill`, 42 do-109 restarts) | modes 4, 5, 7, 8, 9: bit 6 set in 1 460 of 1 460; **mode 14: bit 6 clear in 566 of 566** (skills 158, 160, 167, 176, 181, 327) |
| player start modes | 5 843 | 7, 10, 11, 12, 14, 15, 16, 18 |
| aura ticks (`SelectedAuraTick`) | Might 84, Holy Fire 35 | every tick on frame `≡ 1 (mod 50)` (`perdelay` 50 for both); from one call to the next 50 frames in 114 of 117; the other three run from a Might select at frame `≡ 18, 24, 36 (mod 50)` to the first tick 33, 27 and 15 frames later, the next grid frame `((f − 1 + 50) ÷ 50) · 50 + 1`; the caster's seed unchanged from a tick's exit to the next tick's entry in 89 pairs |
| aura select `SrvDo` | 6 (5 player Might, `immediate` 1) | none for Holy Fire (`immediate` 0) |
| item casts | 86 (64 skill 53 by handler 20 on event 7, 11 + 7 by handler 20 on events 5/6, 3 by handler 21 on events 1/2) | no `PAY`, no `DLY`, no `SrvStart`; the caster steps once from the handler's entry to the cast (the handler's roll) and not at all from the cast's exit to the handler's return, in 86 of 86 |
| Skills `ItemEffect` over every row | 357 | 0 in 285, 1 in 69, 36 in 2, 151 in 1 |
| finisher calls (`PF0`) | 329 (run:2026-10-25-skills 56), all inside a `SrvDo` of Attack (210) or Left Hand Swing (119) | 311 run no entry and leave the seed unchanged; 18 (Fists of Fire charges) run `143` (7), `143 38` (7), `143 38 39` (4); the seed at the first entry call is the entry's in 18 of 18, at the exit the last entry's return in 18 |
| finisher entries' own steps | 143: 18; 38: 11; 39: 4 | 143 one step (18 of 18, no missile); 39 one step before its creations, the 48 creations' owner seed unchanged (a local seed); 38: the queued hit delivered first (DQ0), then one step, the elemental roll (REL), the rest boundaries |
| summon do events | Raven 207, Raise Skeleton 12 | lines `SP0 PA0 PA1 SP1 SL0 SL1` (+ `RSK0 RSK1` for 70) in every one; block words class, 0, mode 8, …, `pettype`, `petmax`, mode (Raven `1a3 0 8 0 0 a 5 8`); `PetAdd(type, max)` (10, 5) and (4, 8) = `pettype`, `petmax` (Raven `petmax` at level 20: 5; Raise Skeleton's: 8); `SummonSetLevel` lvl 104 = `calc2` at owner level 86 and skill level 20 (Raven, 207), 0 (Raise Skeleton, 12); the owner's seed unchanged across `SpawnOwnedMonster` in 219; bit 6 set at the do's exit for Raven (207), clear for Raise Skeleton (12) |
| stat events dispatched inside `COMBAT_ApplyDamage` spans | 548 kill (9) handler calls | all 548 inside an AD span; the attacker's event 5/6 before the defender's 1/2 in the 2 spans holding both; no killed (10) handler fired |
| tier-A rows (§ O): lines per event and own caster steps | — | Throw (53) and Left Hand Throw (36): one MC per do, own 0; Plague Javelin 45, Fire Bolt 317, Fire Trauma 61, Meteor 347: one MC per do, own 0; Multiple Shot 36: 21 MC = `calc1` at level 20, own 0; Nova 465, Frost Nova 279, Howl 74: 64 MC per do, own 0; Firestorm 221: 3 MC and 2 MCB = `calc1` 3 at level 20, own 0; Holy Shield 65: STA 101 for `auralencalc` (13 250 at level 21, 14 500 at 23); Bone Armor 34: STA 14, length 0 (`auralencalc` blank); Might 79: STA 33; Holy Fire 35: one REL per run and one AD per unit (0 to 15); Amplify Damage 61: STA 9 on 0 to 6 units; Teleport 1 951 and Static Field 303: own 0; Jab 108: start no line, do to-hit, hit test, REL and delivery (95), own 3 in 95; Bash 86 starts: hit test and to-hit in the start (82), REL in 73 of them, delivery in the do (DQ in 82) |

- **Separations and limits.** The request pairing, the stat-328 rise, the payment and delay placement, the caller
  arguments and the finisher's entry sequences are equalities over the logged lines; the 1 660 stat-328 pairs with a
  request between, the 59 `r = 0` do events with no payment, the 11 multi-entry finisher calls (against "only the
  current count's entry runs") and the 2 attacker-first spans separate their readings. Not separated by these logs:
  the refusal branches of B2, B3, D1 to D3 and E4 (no refused request reaches the server, § Result), the `+0x24` word
  of B4, the peek and the client message of J3, the charge state of J1/J2, Claws of Thunder, Blades of Ice and Royal
  Strike (no session), entry 38's physical draw (Fists of Fire's physical range draws nothing here), killed (10)
  handlers, `SummonInitStats`, `PetLimitRefresh`, the state id 121 (no line names it) and the event-9 item aura tick.
- **Contradicted in part:** dispatch's entry table lists monster skill modes 4, 5, 7, 8, 9, and README § C says a
  monster reaches the start and do "through its AI with bit 6 set"; 566 monster starts in mode 14 (six sequence
  skills) enter `SrvStart` from `StartUsedSkill` with bit 6 clear, while every start in modes 4 to 9 has it set
  (fn:SKILLS_StartUsedSkill@0x0056FAF0, run:2026-10-27-skills, run:2026-10-30-skills-catalogue). Routed to Phase 3
  (the mode list and the bit-6 sentence) and to a reverser read of the mode-14 start path (plan 0066 log).

### Addendum 2026-11-10: plan 0066 batch S2a part 2, handler effects, the AI command, ammunition (`lane/n66b`)

The last 20 rows of batch S2a: new checks over the same 45 kept logs, the 86 ai.gdb logs of run:2026-11-03-ai (with
its `-2` and `-3` launches) and the 35 economy.gdb logs of run:2026-10-17-economy, all unchanged. No session.

- **Procedure** (under a 4 GB scope; tool `tools/skills_s2a.py` revision 2, `a7395fa3…`, which adds the commands
  `check2`, `ai` and `ua` and leaves `check` as it was: rerun, it gives `2026-11-10-s2a-check.txt` `f69b8ec8…` again):
  from `workspace/logs/skills`, `skills_s2a.py check2 2026-10-25-skills-*.log 2026-10-27-skills-*.log
  2026-10-30-skills-catalogue-cat-*.log > 2026-11-10-s2a-check2.txt`; from `workspace/logs/ai`, `skills_s2a.py ai`
  over the `.log` lines of `manifest-run-2026-11-03-ai.sha256`, `-ai-2` and `-ai-3` (86 logs) `>
  ../skills/2026-11-10-s2a-ai.txt`; from `workspace/logs`, `skills_s2a.py ua economy-s1-*.log >
  skills/2026-11-10-s2a-ua.txt` (35 logs, each listed in `economy-run-manifest.txt`). Exit 0 each, breaks 0. Outputs
  `2026-11-10-s2a-check2.txt` `29ad2680…` (142 lines), `2026-11-10-s2a-ai.txt` `8816d536…` (56 lines),
  `2026-11-10-s2a-ua.txt` `3c3c8c6c…` (7 lines), under `2026-11-10-s2a-part2-manifest.sha256`; `sha256sum -c` from
  `workspace/logs/skills` passes. The handler reads behind the checks (0x005BF960, 0x005BF670, 0x005C0310,
  0x005C0770, 0x005BFAA0, 0x0056CDA0, 0x0056FCB0) were Ghidra decompiles, not kept.

| check | count | result |
|---|---:|---|
| `MonAiUseSkill` (AIB `0x005DEAD0`) to its return or the decision's end | 1 088 calls (mode 14 486, 8 444, 4 68, 7 62, 9 16, 5 12) | one `SrvStart` of the unit inside each, with the call's skill, mode and frame |
| bit 6 of `Unit+0xC4` at a logged return (AIR) | 350 | set in all 174 of modes 4, 5, 7, 8, 9; **clear in all 176 of mode 14** (set at the call in 70 of them) |
| handler 7, knockback | 246 calls | one step; returns 1 exactly when `low & 0x7F < c`, `c` 32 for a MonStats2 `large` class (22 calls), 128 for `small` (136), else 64 (88); `c` = 64 for every class fails 63, mask `0xFF` 98; packet `+0x04` bit 3 clear at the entry with a later handler on the same packet: 66, set after in the 50 passing rolls, clear in the 16 others |
| handler 6, thorns | 23 calls | the attacker loses `stat << 8`: 14 at stat 3 (768) and alive after; 8 attackers killed held at most `stat << 8`; 1 without the life |
| handler 19, slow | 246 calls | `STATE_ApplyTimed` on the other unit: state 24, 750 frames, the block's stat 67 = −v (v 10 ×187, 30 ×59) |
| handlers 5, 13, 22, 29, 9 | 2, 25, 2, 78, 65 calls | Life Tap: attacker at its maximum life both times; damage to mana: mana at its maximum in all 25, no change; Bone Armor, rest in peace: no line inside; stupidity: rev 3 logs, no handler stat or unit level |
| handler calls by function | 2 167 | each handler only on its K1 table events; `p0C` = `stat << 16 \| layer` of its ItemStatCost stat for the item handlers, the skill (68, 76, 82) for the auraevent ones |
| `PreventHealHook` | 2 583 `PH0` | 2 372 right after their attacker's `THR` with the seed unchanged (the other 211 in rev 3 logs with no `THR` outside spans); every `THR` with roll < chance (2 372) is followed at once by `PH0`, none of the 2 221 failed ones; no seed moves inside; the defender's `DRR` is the next draw line in 257 |
| `REL` | 866 | `n` ≥ 1 in all; 11 with no other line of the unit before the event's exit, the exit seed one step on (60 two, 13 four: other draws follow) |
| finisher entry 39 | 4 calls | 48 creations, all class 557 (Fists of Fire's `srvmissilec`; its `a`, `b` blank) |
| item casts | 86 | skills 53, 66, 76, 82: none has a `srvmissile` |
| `MISSILE_HitUnit` of rows with a hit function | 6 822 | 547 reached the build; no line holds the hit function's return |
| `PLAYER_UseAmmo` (economy) | 142 | 12 for the mercenary from `SrvDo` (`0x0056FA93`): return 0, no `ItemConsumeOne`; 130 for the player from the skill missile creation (`0x0056EDB5`): one `ItemConsumeOne` of the thrown weapon (class 44), quantity 130 → 0 by one, the return the quantity before; the player's and game seeds unchanged in 142 |

- **Separations and limits.** Knockback's `c` per class and its mask are separated by the 63 and 98 calls named;
  the hook's place by 2 372 against 2 221; the AI command's start by its 1 088 calls. Not separated: the effects of
  Life Tap, damage to mana, Bone Armor, rest in peace (`0x00639DB0` is not `STATE_ApplyTimed`, the only state call
  STA logs) and stupidity; slow's stats 68 and 69 (added after the call) and its caps; thorns' damage type; the
  elemental value and packet field; charges 1 and 2 of the finisher entries; the item-cast creation (E4); the bow path
  of `PLAYER_UseAmmo`.
- **For Phase 3.** Slow's logged block carries stat 67 = −v, which dispatch § K's row 19 does not name. Mode 14:
  bit 6 is clear at the AI command's return as at the start's entry (part 1), against dispatch § E2, § M1 and the
  entry table; backlog `2026-11-10-reverser-reverser-skills-mode-14-start-bit-6.md` asked for the read (answered: skills/0002 § 16).

### Addendum 2026-11-15: plan 0066 batch S2b, the missile lines of the three kept skills runs (`lane/n66f`)

Plan 0066 Phase 1 batch S2b (a-logs; [inventory § 4](../../plans/0066-inventory/README.md#4-batch-list)): new checks
over the missile lines of the same 45 kept logs (this run, run:2026-10-25-skills and run:2026-10-30-skills-catalogue),
unchanged. No session, no Ghidra.

- **Procedure** (from `workspace/logs/skills`, under a 4 GB scope): `python3 -I <worktree>/tools/skills_s2b.py check
  2026-10-25-skills-*.log 2026-10-27-skills-*.log 2026-10-30-skills-catalogue-cat-*.log > 2026-11-15-s2b-check.txt`
  (exit 0, `SURVEY s2b breaks=0`). Tool `tools/skills_s2b.py` `114b0f7d…` (it reads the logs with `tools/skills.py`'s
  parser, unchanged; its docstring names the sections FRAME, MH, DMG, MA, BDO, MC, SKL, OWN). Output
  `2026-11-15-s2b-check.txt` `180157a2…` (218 lines). The state census `cat <the 45 logs> | grep '^STA ' | grep -o
  '"state":[0-9]*' | sort | uniq -c | sort -k2 > 2026-11-15-s2b-sta-states.txt` (`d11872d5…`, 1 406 lines in 13
  states). Both under `2026-11-15-s2b-manifest.sha256`; `sha256sum -c` from that directory passes. One development pass
  (`workspace/logs/n66f/s2b-dev1.txt`, the same tool revision) is byte-identical to the kept output; earlier passes of
  the paused lane (before the FRAME end-call split) were not kept.
- **What the logs hold** (every count from `2026-11-15-s2b-check.txt`, section in the first column):

| check | count | result |
|---|---:|---|
| FRAME: `MF0`'s row number (0x005ADC97, before the indexed do call) against Missiles `pSrvDoFunc` | 33 041 windowed frames (do 1 20 860, 3 4 605, 5 7 096, 23 480) | equal in all |
| FRAME: a frame returning 1, the missile's next frame | 31 804 | at frame + 1 in all |
| FRAME: do-1 end calls (no unit, `end` 1) nested in a frame | 888 | 823 at frames left 0 after the decrement (range spent), 65 before it (the step's end); the frame returns the end call's 2 in all 888 |
| FRAME: do-1 missiles ending at range spent | 823 | frames run = frames left at creation in all; 257 others ended earlier |
| FRAME: unit hits in do-1 frames | 230 | all at frames left < the activate mark (none at =) |
| FRAME: do-1 frames returning 2 with no hit call | 0 | — |
| MH: end calls of rows without a hit function | 80 600 | no build, the missile's seed unchanged, result 2 |
| MH: end calls of rows with a hit function | 5 610 | result 2; the seed moved in 419; 386 builds inside, none naming a unit |
| MH: unit calls of rows without a hit function, `THR`/`BD0`/`MA0` directly in order | 18 170 | `BD0 MA0` 16 858, `THR BD0 MA0` 594, `THR` (missed) 718; none returned before them |
| MH: a pierce used by a `CollideKill` row | 130 | result 1 (kept) in all |
| MH: hit-function unit calls with the to-hit passed, the table-only result (no hit function) against a logged build | 1 209 | the table predicts a build in all; a build logged in 161, none in 1 048 |
| MH: `AlwaysExplode` rows | 709 calls | end calls 2 (662); unit calls 1 (31) or 2 (13) after a passed or absent roll, 2 after a missed roll (3) |
| MH: the missile's stat 19 at the hit | 105 592 | player-owned 0 of 101 777; monster-owned 1 601 of 3 815 |
| DMG: the missile's seed from `BD1` to `MA0` by `pSrvDmgFunc` | 17 613 | function 3: one step in 13 486 of 13 486; none: 0 in 4 118; function 1: 0 in 9 |
| MA: the missile's seed across `MISSILE_ApplyDamage` by `KnockBack` | 17 613 | 0 → no step (17 608); 33 → one step (5) |
| MA: the knockback roll against packet `+0x04` bit 3 at the `AD0` inside | 5 | bit set exactly when roll < 33 (rolls 4, 25 set; 33, 48, 86 clear) |
| MA: `DRR` lines inside | 85 | all the defender's |
| BDO: builds with two draws | 143 (run25 19, run27 43, catalogue 81) | pairs (phys, fire) 108, (phys, poison) 34, (fire, cold) 1; every one separates its pair's order, and each is in F1's order |
| MC: `srvmissile` creations of rows with no `srvdofunc` | 579 | line player `0x21` 362, line monster with stat 19 `0x1021` 113 (block `+0x48` and the missile's stat 19 = the owner's stat 19), lob monster `0x420` 43, lob player `0x420` 61; flags, class, skill and level as B2/B3 in all |
| MC: flag `0x1000` by owner type, every creation | 95 833 | player 0 of 92 094; monster 1 622 of 3 739 |
| MC: callback lines (`MCB0`) | 618 | `+0x54` = `0x005C9290`, `EDX` = `+0x58`, `ECX` = the missile `MC1` returns, in all; after `SU0 SU1` (602) or `SU0 SU1 MON` (16) |
| MC: Firestorm do events | 221 | one plain creation of class 458, then class 458 with callback `0x005C9290` and arguments 0, 1, in all |
| MC: Meteor do events | 347 | flags 1, no target unit, target words 0 (no return address on `MC0`) |
| MC: Multiple Shot do events | 36 | 21 creations; groups 9 (`0x10820`), 2 (`0x820`), 10 (`0x10820`); targets stepped by one `(sx, sy)`, `sx² + sy² ≤ 3`, eight vectors |
| MC: class-408 creations, the innermost enclosing span | 36 | inside an `end` 1 call of class 407 with hit function 38: 24; after `cat-a5-1`'s `MH` cap: 12 |
| MC: creations inside a missile's hit call | 7 975 | 961 name the hitting missile as source |
| SKL: Amplify Damage do events | 61 | `STA` lines 0 (37) or 1 to 6 (24), each state 9 = `auratargetstate`, one per unit, one length, the caster as applier |
| SKL: Holy Fire do events | 35 | one `REL` on the caster, no caster step before it; 17 with 2 to 15 units, one fire value across their packets |
| SKL: Bash starts (st 32) | 86 | one `REL` on the caster in 73, none in 13 |
| SKL: monster do events, caster steps (R4) | 7 899 | do 131 (row 295) 1 in 61 of 61; do 132 (row 299) 1 in 198 of 198, inside its `MC0`; do 129 (row 330) 1 in 62 of 347, no logged line; do 109 (rows 215, 328) 1 in 361, inside `MHT0`, and 4 in 634 (`MHT0` 1, `REL` 1, unlogged 2); **rows 339, 340, 342, 345 (do 0) 1 in 92 of 92, inside their `MC0`; row 167 (do 91) 9 in 1 of 11, no logged line**; the 14 other rows 0 |
| OWN: a missile's creation (`MC1`) to its hit's to-hit roll (`THR`), the owner's logged seeds | 1 356 | the attacker is the owner in all; the seeds chain forward in all (1 079 with no owner line between, 277 with); with none between, the roll is the next draw in 1 023, 56 show unlogged owner draws |
| state census (`2026-11-15-s2b-sta-states.txt`) | 1 406 `STA` lines | 13 states (9, 13, 14, 24, 33, 35, 52, 55, 56, 58, 62, 101, 141); no state 86 |

- **Separations and limits.** Separating: the frame's end-call split (823 against 65), the 230 hits all below the
  mark, the knockback rolls 33 and 48 against `≤`, the 143 two-draw builds (one per pair order), the 113 monster
  creations with stat 19 against the 43 without, the Firestorm arguments' order, the 1 048 hit-function calls with no
  build against an OR of the table result. Not separated: the own-cell and crossed-cell branches of D3 (no frame
  returned 2 without a hit), the town frees of D2, the boundary frames left = the activate mark, the filters of E1
  (no refusal logged), a hit function's result as a replacement or an AND, state 54 and stat 120 in E3, the to-hit
  chance's terms (`THR` logs the chance), state 86, the order of the magic, lightning and burn pairs, stat 180, the
  callback's place before the damage block, the 12 class-408 creations after the cap, and Meteor's creator.
- **Contradicted in part (catalogue § R4).** "the other logged monster rows none" fails: the `srvmissile` rows 339,
  340, 342, 345 step their caster once in 92 of 92 do events, inside the creation, and row 167 nine times in 1 of 11
  with no logged line inside (fn:SKILLS_SrvDo@0x0056F7F0, run:2026-10-30-skills-catalogue). The run's own
  `2026-10-30-skills-catalogue-check.txt` (`2bd2b4fb…`) prints these counts (lines 215 and 234–237); R4 left them out.
  Routed to Phase 3 (the rewording); the steps' sources stay `[I]` (b, H2a).

## run:2026-10-25-skills

- **Question:** (plan 0045 Phase 2) Does `tools/skills.py`, the model of [skills/0001](0001-dispatch.md),
  [skills/0002](0002-missiles.md) and [skills/0003](0003-handlers.md), reproduce the logged skill and missile events
  of tier-A characters draw for draw: the payment, the missile creation (velocity, acceleration and maximum, range,
  frames left, activate mark, skill and level, the missile's seed from the game seed or a creation callback, the
  owner's critical draws, the pierce count), every logged frame of a followed missile (the velocity step, the position
  step, the seed), the packet a missile builds at a hit (`MISSILE_BuildDamage`'s draws on the missile's seed and the
  drawn fields), a missed to-hit, a summon's level, and the caster's seed across the skill events of the rows whose
  functions draw nothing of their own, with the game and caster seeds chained across events?
- **Setup:** 18 agent-driven sessions on harness slot 2 (display `:9`, prefix `workspace/wineprefix-2`), single
  player, pinned `game.exe` in `workspace/runtime/game` (stock data), gdb by `tools/d2run.py` with `-seed` per
  session, all in Normal. Logger `tools/gdb/skills.gdb` (`92420a1c…`) sourcing `tools/gdb/pilot.py` (`1ad48a4c…`,
  unchanged) and `tools/gdb/skills.py` **rev 3** (`12e30fe5…`: rev 2 with the `RSK0`/`RSK1` lines around do 31's call
  of `0x005C4430` at `0x005C4C7A`/`0x005C4C7F`); breakpoints only print and continue. Driver
  `tools/skills_sessions.py` (`f5777a25…`, unchanged from the development runs) over `tools/d2pilot.py` (`b1db3063…`):
  each session `saves.py --slot 2 restore`/`aside p45h`, `d2run.py --install p45h`, the waypoint, then `explore
  --melee --melee-button 3 --curse-keys … --keys-cycle` (the next skill hotkey and a right-click at the nearest live
  monster; Teleport on Shift + left), the Necromancer's `corpse` step first, the Paladin's two aura walks after;
  `slots.py stop 2` after each session, `saves.py --slot 2 restore p45h` at the end (aside empty, slot idle). The
  pilot only decides where to click.
- **Characters** (ADR-0013 § Neutral: tool-built by `skills_sessions.py build` from the recipes
  `tools/d2s_recipes/skills-{sor,ama,amaj,nec,dru,bar,pal,ass}.json` on the stock `p0005` base saves, stock items,
  skill points from the recipe; no test-state key), into `workspace/logs/skills/2026-10-25-skills-saves/`, byte for
  byte the development saves of `dev-p45h-manifest.sha256`: `SkillsSor` (clvl 80; Nova F1, Frost Nova F2, Static Field
  F3, Fire Bolt F4, Meteor F5, Blaze F6, Teleport), `SkillsAma` (85, *Pluckeye* and arrows: Multiple Shot, Attack),
  `SkillsAmaJ` (85, *Titan's Revenge*: Jab, Plague Javelin, Throw), `SkillsNec` (85, *The Gnasher*: Poison Nova, Raise
  Skeleton, Amplify Damage, Bone Armor), `SkillsDru` (Firestorm, Raven), `SkillsBar` (Bash, Howl), `SkillsPal`
  (*Steelclash*: Holy Shield, Attack, Might, Holy Fire), `SkillsAss` (*Cutthroat*: Fists of Fire, Attack, Fire
  Trauma).

### Sessions

| session | save | seed | waypoint (act, row) |
|---|---|---:|---|
| sor-1 … sor-4 | SkillsSor | 4521–4524 | 1,2 · 1,3 · 1,4 · 1,5 |
| ama-1, ama-2 | SkillsAma | 4531, 4532 | 1,2 · 1,3 |
| amaj-1, amaj-2 | SkillsAmaJ | 4541, 4542 | 1,2 · 1,3 |
| nec-1, nec-2 | SkillsNec | 4551, 4552 | 1,2 · 1,3 |
| dru-1, dru-2 | SkillsDru | 4561, 4562 | 1,2 · 1,3 |
| bar-1, bar-2 | SkillsBar | 4571, 4572 | 1,2 · 1,3 |
| pal-1, pal-2 | SkillsPal | 4581, 4582 | 1,2 · 1,3 |
| ass-1, ass-2 | SkillsAss | 4591, 4592 | 1,2 · 1,3 |

No session was relaunched, aborted or died. Logs `workspace/logs/skills/2026-10-25-skills-<session>.log` (65 MB),
with their `.pilot.txt` and `-shots/`.

- **Procedure** (from the worktree; the checks under a 4 GB scope):
  ```
  python3 -I tools/skills_sessions.py build --saves workspace/logs/skills/2026-10-25-skills-saves
  python3 -I tools/saves.py --slot 2 aside p45h
  python3 -I tools/skills_sessions.py run --slot 2 --tag p45h --saves workspace/logs/skills/2026-10-25-skills-saves \
      --run 2026-10-25-skills sor-1 sor-2 sor-3 sor-4 ama-1 ama-2 amaj-1 amaj-2 nec-1 nec-2 dru-1 dru-2 bar-1 bar-2 \
      pal-1 pal-2 ass-1 ass-2
  cd workspace/logs/skills
  python3 -I ../../../tools/skills.py check 2026-10-25-skills-*.log --json 2026-10-25-skills-check.json \
      > 2026-10-25-skills-check.txt
  python3 -I ../../../tools/skills.py tally 2026-10-25-skills-*.log > 2026-10-25-skills-tally.txt
  python3 -I tools/skills.py audit $(cat workspace/logs/combat/c37p2-run.lst) \
      $(awk '{print $4}' workspace/logs/stats/s1017-manifest.txt) workspace/logs/combat/p47h-owf-n-andariel-p8.log \
      > workspace/logs/skills/2026-10-25-skills-audit.txt                      # from the worktree root
  ```
  Checker `tools/skills.py` `1b297c24…` (it gives the kept `check.txt`, `tally.txt` and `audit.txt`); its tests
  `tools/test_skills.py` (8 tests, passing). Against the development revision (`7d7417a2…`) it adds: `MF.seed` with
  the draws of a hit nested in the frame (the `BD` draws, then the `MISSILE_ApplyDamage` boundary's exit, the frame
  exiting with the last hit's seed: `MF.hitseed`); do 31's class draw (`RSK.seed`, and the rows 70 and 80 in
  `SDO.seed`); the `0x005C9290` callback check as "the exit seed lies on the stream of `Init(path x + arg)`", the
  steps after the Init reported; the `tally` and `audit` commands; counters only otherwise. A first check of
  `sor-1`…`sor-4` with the callback check as written (the exit seed equal to the Init) gave 8 `MC.cbseed` mismatches,
  each 38 steps past the Init (not kept as a file; the cause is in the result below).
- **Kept:** `workspace/logs/skills/2026-10-25-skills-manifest.sha256` (`8b01d216…`, 48 files: the 18 logs and their
  pilot files, `check.txt` `17555e43…`, `check.json` `5619ca23…`, `tally.txt` `b82c4040…`, `audit.txt` `96816fa4…`,
  the 8 saves); `sha256sum -c` from that directory passes.

### Result

**0 mismatches** over 335 618 checks (the checker's table; every row 0). Counts below are `check.txt` and
`tally.txt`.

| check | ok | what it asserts |
|---|---:|---|
| `PAY` | 1 798 | 1 334 player payments of a cost row (258 with a `lvlmana` term at level > 1; `manashift` 5, 6, 7, 8 in 19, 21, 117, 1 177), 259 result-0 calls of a row with no cost, 205 non-player calls returning 1 |
| `MC.vel`, `.accel`, `.range`, `.left`, `.skill`, `.owner`, `.seed`, `.gameseed` | 31 391 each (`.range` 30 941, `.left` 30 922) | every creation; 450 ranges taken after a creation callback and 19 lob frame counts are oracles |
| `MC.cbseed` | 450 | the `0x005C9290` re-seed: 442 Firestorm sub-missiles (20 steps after the Init each), 8 of a monster's class-195 missiles (38 each) |
| `MC.crit`, `MC.pierce` | 984, 1 066 | 984 owner critical draws (1 draw each; none of 2 or 3), 856 pierce counts drawn from the local seed |
| `MF.vel`, `.pos` | 11 413 | 1 657 accelerating steps, 278 fifth steps, 60 capped at `MaxVel`; none floored at 0 |
| `MF.left`, `.seed`, `.still`, `.hitseed` | 13 335, 13 335, 1 922, 110 | 37 frames with a nested hit; the boundary moved the missile's seed in none of 36 |
| `BD.seed`, `.elem`, `.phys`, `.len` | 778, 594, 164, 24 | builds with 0, 1, 2 draws: 39, 720, 19 |
| `THR.roll`, `MH.missed` | 269, 105 | 105 missed to-hits ending the missile, 7 of them with a pierce left (C5) |
| `SL.level` | 215 | 8 Raise Skeleton summons from the owner's level (C1: L 86, skill level 20, 84 each), 207 Raven summons at the given level |
| `RSK.seed` | 8 | do 31's class draw, 8 class-363 summons at skill level 20, one caster step each |
| `SST.seed`, `SDO.seed` | 1 142, 1 269 | the rows with no own draws (17 rows of the checker's `NO_OWN_DRAWS`, Raise Skeleton's 8 do events too), the nested events' draws added; not the run's skill-use totals (*2026-10-27*) |
| `CHAIN.gameseed`, `CHAIN.caster` | 21 860, 3 155 | chained pairs; 304 caster resyncs between skill events (steps in `check.txt`'s distribution) |

Coverage against the plan's *Done when* (`tally.txt`):

- **Skill uses:** 1 840 do events and 1 688 start events (the logs' `SDO0` and `SST0` lines, the tally's rows
  summed; 2 708 and 2 508 before the review's correction), 1 409 of the do events in tier-A rows: **short** of the
  2 000 skill uses the plan asks. Tier-A rows at ≥ 30 do events: 0 Attack 116, 2 Throw 35,
  10 Jab 63, 12 Multiple Shot 36, 36 Fire Bolt 32, 44 Frost Nova 33, 48 Nova 33, 54 Teleport 182, 56 Meteor 30,
  98 Might 84, 102 Holy Fire 35, 126 Bash 67, 130 Howl 54, 221 Raven 207, 225 Firestorm 221, 259 Fists of Fire 41.
  **Short:** 25 Plague Javelin 26, 42 Static Field 26, 66 Amplify Damage 25, 68 Bone Armor 23, 251 Fire Trauma 19,
  117 Holy Shield 13, 70 Raise Skeleton 8; 1 Kick, 4 Left Hand Throw, 5 Left Hand Swing 0 (no session). Others: 46
  Blaze 29, 92 Poison Nova 208, the monster rows 160 (82), 181 (106), 167 (6). Refusals: 2 start functions returning
  0 (rows 10, 259), 21 do events of row 0 returning 0; **no** payment refused for its cost (every result-0 payment is
  a no-cost row), no delay refusal and no town refusal logged (277 delay states set, `DLY`, an oracle).
- **Missiles:** 31 391 creations; 493 windowed missiles followed from creation to their removal frame; 778 hit
  packets predicted; 450 sub-missiles (the callback's). **Short:** the end of a missile at a hit is an oracle except
  the 105 missed to-hits (31 257 hit calls returned 2, 1 536 hit calls had a unit); pierce uses at a hit are not
  modelled (7 cases of C5).
- **Handlers:** 284 `EVH` fires (event 5: `0x005BFAA0` 65, `0x005BFE60` 62, `0x005BFFC0` 62; event 9 `0x005C0130`
  94; event 11 `0x005C6370` 1), all oracles: **short** (no handler model); state 52 never applied.
- **Summons:** 215 (`SP0`), each level predicted; the created unit's seed and stats not predicted: **short in part**.
- **Monster skill uses:** 15 268 `MonAttackStats` calls, all oracles: **short** (no `MonAttackStats` model).
- **Re-seeds:** 450 at `0x005C9290`; the other sites of skills/0003 § 9 not reached: **short in part**.
- **Chaining:** the game seed across creations of one do event (21 860 pairs) and the caster's seed across skill
  events (3 155); the missile's seed across the hits of one frame (`MF.hitseed`, 110). The 304 caster resyncs are sorted by the
  lines between at the review (skills/0001 § 17: 87 match the unit's own `THR` rolls, which `CHAIN.caster` does not
  add).
- **The oracle replacement:** `audit.txt` over the 19 logs of run:2026-10-16-combat, the 18 of run:2026-10-17-stats
  and the *Fleshripper* log: 2 554 missile-packet oracle events, 3 461 handler fires and 3 646 aura runs, **none
  replaceable**: those loggers wrote no missile stat list at the hit and no `MISSILE_BuildDamage` line with the
  missile's seed, no creation, no `RollElemDamage` line in an aura run, and the handler fires need a handler model
  this tool does not have. Their checks stand as kept.
- **The Phase 1b cases:** C1 8 (above); C3 278 fifth steps and 60 caps; C5 7. **Short:** C2 0 (no `spike1`–`spike4`
  monster met: no `VelLev` row created), C4 0 (Blaze cast 29 times, but its `blaze` missiles, `LevRange` 25, come
  from walking and the pilot teleports: no `LevRange` row created at all).

Two readings changed by the run, both recorded in the findings: do 31's caster draw (skills/0003 § 5, found in the
development logs and located statically: `0x005C4300`'s inline step at `0x005C4384`), and the `0x005C9290` re-seed,
whose new seed the callback's own path calls then step 20 or 38 times (skills/0003 § 9, the "none" corrected).

The raises are in [skills/0001 § 17](0001-dispatch.md#17-plan-0045-phase-2-the-run-run2026-10-25-skills) (the
payment, the cost and delay steps' draws, the caster's chaining), [skills/0002 § 11](0002-missiles.md#11-plan-0045-phase-2-the-run-run2026-10-25-skills)
and [skills/0003 § 15](0003-handlers.md#15-plan-0045-phase-2-the-run-run2026-10-25-skills).


*2026-11-10:* plan 0066 batch S2a re-checked this run's logs with `tools/skills_s2a.py` (0 breaks); the counts are in [run:2026-10-27-skills § Addendum 2026-11-10](#addendum-2026-11-10-plan-0066-batch-s2a-new-checks-over-the-three-kept-skills-runs-lanen66b).

*2026-11-15:* plan 0066 batch S2b checked the missile lines of this run's logs with `tools/skills_s2b.py` (0 breaks); the counts are in [run:2026-10-27-skills § Addendum 2026-11-15](#addendum-2026-11-15-plan-0066-batch-s2b-the-missile-lines-of-the-three-kept-skills-runs-lanen66f).

## run:2026-10-20-cat-emu-9a

- **Question:** (plan 0046 Phase 1, batch 9a) Do the missile server do functions 2, 6–12 and 14–18 map their inputs
  (the missile's record, `MissileData` words, owner, path and seed) to the arguments of the calls they end in, and to
  the bytes and seed they write before them, exactly as [skills/0004](0004-missile-do-1-18.md) §§ 3–11 say?
- **Setup:** Ghidra 12.1.2 p-code emulator (`EmulatorHelper`) on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m1`, symbols replayed from `re/symbols.csv`, heap 3 GB, under
  `systemd-run --user --scope -p MemoryMax=4G`). No wine, nothing runs natively, no slot. New script
  `re/ghidra_scripts/EmuBoundary.java` (`286393aa…`, `tools/ghidra.sh emuboundary`): `EmuTrace.java` plus `observe
  <addr>` lines in the memory spec; a case that reaches one ends there and prints its registers and the 64 bytes at
  ESP (skills/0004 § 2). Models, case writers and checks: `tools/skills_catalogue_emu.py` (`b2a6afd8…`, which uses
  `tools/rng.py` and `tools/sweep_s4b.py`'s image reader). All inputs synthetic (stock parameter values among them);
  every case-writer draw from `random.Random("cat9a-<family>")`. Files in `workspace/logs/skills-cat-9a/`,
  `manifest.sha256` `58e190a9…` (48 files: cases, memory specs, expected inputs, outputs, the empty `.err` logs,
  `check.txt` `3e1f2587…`, `static.txt` `e2b2f9a1…`, `rows.txt` `6cfad638…`); `sha256sum -c manifest.sha256` from that
  directory passes.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-9a
  python3 -I tools/skills_catalogue_emu.py cases
  for f in cellsub orb spiral scatter chest homing periodic sublob guided; do
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m1 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -q -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read, names the nine
  boundaries (`observe`) and guards the allocator and fatal-path entries; each case writes only the fields its
  function reads, so any other read is traced.
- **Observed** (`check.txt`):
  ```
  CAT9A cellsub  cases=1800 match=1800 bad=0 neg=173 traced=2   undeclared=0 stopped=0
  CAT9A orb      cases=1500 match=1500 bad=0 neg=266 traced=130 undeclared=0 stopped=0
  CAT9A spiral   cases=1500 match=1500 bad=0 neg=223 traced=0   undeclared=0 stopped=0
  CAT9A scatter  cases=2400 match=2400 bad=0 neg=394 traced=4   undeclared=0 stopped=0
  CAT9A chest    cases=1500 match=1500 bad=0 neg=247 traced=1   undeclared=0 stopped=0
  CAT9A homing   cases=1500 match=1500 bad=0 neg=22  traced=3   undeclared=0 stopped=0
  CAT9A periodic cases=1200 match=1200 bad=0 neg=149 traced=0   undeclared=0 stopped=0
  CAT9A sublob   cases=1200 match=1200 bad=0 neg=187 traced=4   undeclared=0 stopped=0
  CAT9A guided   cases=1200 match=1200 bad=0 neg=128 traced=79  undeclared=0 stopped=0
  CAT9A static   data_stores=0 pins=18 pins_ok=18 ro_reads=3
  ```
  (`traced` counts aggregated rows of declared image reads; the branches reached are on each family's `outcomes`
  line.) Development runs before the final declared sets: the first `check` listed three undeclared image reads (the
  `CALC_Eval` jump table, `UNIT_GetSizeX`'s jump table, a target's `+0xC6`), each then declared or written by the case
  writer; the outputs above are from the final case files.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015, ADR-0021) of the 13 functions' maps up to their boundary
  calls, 13 800 cases, 0 mismatches; raises skills/0004 §§ 3–11's `[C]` statements up to their boundaries (do 7's re-plan and do 13 not covered).
  *Architect ruling (`lane/p46m1` review, 2026-10-20):* the `observe` boundary does not meet ADR-0015 (1) and (3) as
  written; the proposed [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md) admits it. Until the owner
  accepts it, the statements that rest on cases ending at a boundary are `[I]`; the refusal paths that return are `[C]`
  (skills/0004 § 2). *ADR-0021 accepted by the owner (2026-10-20):* those statements are `[C]` without a re-run, each
  up to its boundary, covering nothing after it (skills/0004 § 2). The review checked the call site of every observed boundary from the kept outputs
  (`workspace/logs/skills-cat-9a-review/callsites.txt` `8ea8058b…`: one site per function and boundary). Not covered: what any
  boundary callee does; faults (§ 1); when the game runs these functions or with which seed.
  (fn:sub_005A9820_MissSubNearReseed@0x005A9820, fn:sub_005AF030_MissDo15OrbBolts@0x005AF030)

## run:2026-10-20-cat-emu-9b

- **Question:** (plan 0046 Phase 1, batch 9b) Do the missile server do functions 19–23 and 25–36 and the damage
  functions 1–5 and 7–14 map their inputs (the missile's record, `MissileData` words, owner, target, path, stat lists,
  Skills, MonStats and MonStats2 records, the packet and the seeds) to the arguments of the calls they end in, the bytes
  and seeds they write, and (damage functions) the packet they return, exactly as
  [skills/0005](0005-missile-do-19-36-damage.md) §§ 3–18 say?
- **Setup:** as run:2026-10-20-cat-emu-9a: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m2`, symbols replayed from `re/symbols.csv`, heap 3 GB, under
  `systemd-run --user --scope -p MemoryMax=4G`), `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine,
  nothing runs natively, no slot. Models, case writers and checks: the 9b families of `tools/skills_catalogue_emu.py`
  (`540cf98e…`; `tools/rng.py`, `tools/sweep_s4b.py`), which now assert the **return address** of every observed
  boundary (ADR-0021 (b)) and run a site control and two negative controls per family. All inputs synthetic (stock
  parameter values among them); every case-writer draw from `random.Random("cat9b-<family>")`. Files in
  `workspace/logs/skills-cat-9b/`, `manifest.sha256` `cda8abef…` (68 files: cases, memory specs, expected inputs,
  outputs, the empty `.err` logs, `check.txt` `7b5c1f6f…`, `static.txt` `16672f27…`, `rows.txt` `9152e7da…`);
  `sha256sum -c manifest.sha256` from that directory passes. The same tool revision reproduces 9a's `check.txt` and
  `static.txt` byte for byte from 9a's kept outputs, and its 9a `cases` regenerate 9a's case files byte for byte.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-9b
  python3 -I tools/skills_catalogue_emu.py cases --batch 9b
  for f in create9b vines rabies reseed9b scatter25 wake regen tornado fx dmgconv dmgelem dmgpkt knock; do
    systemd-run --user --scope -q -p MemoryMax=4G env GHIDRA_PROJ_DIR=workspace/ghidra-p46m2 GHIDRA_HEADLESS_MAXMEM=3G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch 9b > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 9b > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 9b --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read, names the
  boundaries (`observe`: 9a's nine and twelve more, plus do 20's entry in `create9b` only) and guards the allocator and
  fatal-path entries; the damage cases pass `(unit, packet)` on the stack and dump the packet.
- **Observed** (`check.txt`):
  ```
  CAT9B create9b  cases=1500 match=1500 bad=0 neg=299 traced=2  undeclared=0 stopped=0
  CAT9B vines     cases=1200 match=1200 bad=0 neg=497 traced=3  undeclared=0 stopped=0
  CAT9B rabies    cases=1200 match=1200 bad=0 neg=242 traced=5  undeclared=0 stopped=0
  CAT9B reseed9b  cases=1500 match=1500 bad=0 neg=347 traced=4  undeclared=0 stopped=0
  CAT9B scatter25 cases=900  match=900  bad=0 neg=297 traced=4  undeclared=0 stopped=0
  CAT9B wake      cases=1200 match=1200 bad=0 neg=503 traced=4  undeclared=0 stopped=0
  CAT9B regen     cases=1200 match=1200 bad=0 neg=184 traced=5  undeclared=0 stopped=0
  CAT9B tornado   cases=900  match=900  bad=0 neg=365 traced=4  undeclared=0 stopped=0
  CAT9B fx        cases=1200 match=1200 bad=0 neg=180 traced=0  undeclared=0 stopped=0
  CAT9B dmgconv   cases=1500 match=1500 bad=0 neg=421 traced=43 undeclared=0 stopped=0
  CAT9B dmgelem   cases=1200 match=1200 bad=0 neg=137 traced=32 undeclared=0 stopped=0
  CAT9B dmgpkt    cases=2400 match=2400 bad=0 neg=70  traced=5  undeclared=0 stopped=0
  CAT9B knock     cases=1200 match=1200 bad=0 neg=62  traced=2  undeclared=0 stopped=0
  CAT9B static data_stores=0 pins=26 pins_ok=26 ro_reads=4 table_entries=30
  ```
  17 100 cases. Every family's two negative controls fail (counts per control on its `negative control` lines); the
  site control fails on all 8 762 matched boundary cases (40 `site` lines: function, boundary, return address).
  Development runs before these files: the first check found do 28's point in the block's target words (the model
  had the start words; corrected), two controls that could not fail (do 31's `Explosion`, damage 3's `≤`; replaced),
  and undeclared reads of the three `EType` jump tables and of `MissileData+0x0C` by `MISS_EvalCalc` (declared, and
  written by the case writer); the outputs above are from the final case files.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the damage functions' maps on returning
  cases (`[C]`), of the do functions' refusal paths that return (`[C]`), and of the do functions' maps up to their
  boundary calls with the call site asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md), accepted by the owner 2026-10-20 and applied at the
  `lane/p46m2` review; skills/0005 names each claim's boundary). Not covered:
  what any boundary callee does and everything after it; the `fMin` floor of `StatListGetValue`; faults
  (`GameFindUnit` with a type above 5); when the game runs these functions or with which seed.
  (fn:sub_005AD050_MissDmg01ConvertPct@0x005AD050, fn:sub_005B0010_MissDo30Contagion@0x005B0010)
- **Review checks** (`lane/p46m2` review, 2026-10-20; `workspace/logs/skills-cat-9b-review/`, `manifest.sha256`
  `02466fbf…`, 9 files): `sha256sum -c` of the run's manifest passes (68 files); `check rabies reseed9b` from the kept
  outputs gives `check.txt`'s lines; `cases --batch 9a` and `cases --batch 9b` regenerate every kept case, memory and
  expectation file byte for byte (27 and 39); `check --batch 9a` and `static --batch 9a` reproduce 9a's kept files byte
  for byte (tool `540cf98e…`; `EmuBoundary.java` `286393aa…`); do 30's 90 creation cases leave the missile's, the
  owner's and the decoy's seeds unchanged (270 of 270, `seeds-do30.txt`, from the kept `rabies.out`); objdump of do 28
  (0x005AFCAA–0x005AFD50), do 30 (0x005B0140–0x005B0187), damage 14 (0x005AD67C–0x005AD69E) and do 31's end code
  (0x005B0289–0x005B0336) in `objdump-spot.txt`. (fn:sub_005B0010_MissDo30Contagion@0x005B0010)

## run:2026-10-20-cat-emu-9c

- **Question:** (plan 0046 Phase 1, batch 9c) Do the missile server hit functions 1, 3 (and 44), 4, 7–10, 12–22 and
  24–29 map their inputs (the missile's record, `MissileData` words, owner, hit unit, path, stat lists, state lists,
  Skills and MonStats records and the seeds) to the result they return, or to the arguments, pointed-to bytes and
  seed states at the call they end in, exactly as [skills/0006](0006-missile-hit-1-29.md) §§ 3–16 say, and do they
  leave the owner's and the target's seeds as they were?
- **Setup:** as run:2026-10-20-cat-emu-9b: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m3`, symbols replayed from `re/symbols.csv`, heap 3 GB, under
  `systemd-run --user --scope -p MemoryMax=4G`), `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`;
  `EmuTrace.java` `3255db0c…`). No wine, nothing runs natively, no slot. Models, case writers and checks: the 9c
  families of `tools/skills_catalogue_emu.py` (`412e3e5c…`; `tools/rng.py`, `tools/sweep_s4b.py`), which keep 9b's
  call-site assertion and site control, run two to six negative controls per family, compare the missile's, the
  owner's and the target's seeds in every case (written and dumped by every case; a control moves the missile's draws
  to the owner's seed), and compare the bytes behind a boundary argument that points into the caller's frame (the
  packet of `AreaHitAt` and `MISSILE_BuildDamage`, hit 20's context block). All inputs synthetic (stock parameter
  values among them); every case-writer draw from `random.Random("cat9c-<family>")`. Files in
  `workspace/logs/skills-cat-9c/`, `manifest.sha256` `343ef0d7…` (28 files: cases, memory specs, expected inputs,
  outputs, the empty `.err` logs, `check.txt` `733ad44a…`, `static.txt` `1644c5cb…`, `rows.txt` `eaec0e1a…`);
  `sha256sum -c manifest.sha256` from that directory passes. The same tool revision reproduces 9a's and 9b's
  `check.txt` and `static.txt` byte for byte from their kept outputs, and its `cases --batch 9a` / `--batch 9b`
  regenerate their 27 and 39 case, memory and expectation files byte for byte.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-9c
  python3 -I tools/skills_catalogue_emu.py cases --batch 9c
  for f in area9c holy9c create9c state9c range9c; do
    systemd-run --user --scope -q -p MemoryMax=4G env GHIDRA_PROJ_DIR=workspace/ghidra-p46m3 GHIDRA_HEADLESS_MAXMEM=3G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch 9c > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 9c > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 9c --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, States
  count 190, ItemStatCost, MonStats as each family needs), names the boundaries (`observe`: 9b's and eleven more,
  skills/0006 § 2) and guards the allocator and fatal-path entries; each case passes the hit unit on the stack and
  dumps the three seeds.
- **Observed** (`check.txt`):
  ```
  CAT9C area9c   cases=1800 match=1800 bad=0 neg=829 traced=30 undeclared=0 stopped=0
  CAT9C holy9c   cases=1500 match=1500 bad=0 neg=218 traced=10 undeclared=0 stopped=0
  CAT9C create9c cases=1800 match=1800 bad=0 neg=284 traced=8  undeclared=0 stopped=0
  CAT9C state9c  cases=1800 match=1800 bad=0 neg=153 traced=30 undeclared=0 stopped=0
  CAT9C range9c  cases=1500 match=1500 bad=0 neg=182 traced=74 undeclared=0 stopped=0
  CAT9C static pins=26 pins_ok=26 ro_reads=6 table_entries=25
  ```
  8 400 cases. Every negative control fails (counts per control on its `negative control` lines, the weakest hit
  29's `left > 0` with 4 and hit 7's undead mask with 8, each beside a stronger control on another claim); the site
  control fails on all 3 941 matched boundary cases (27 `site` lines: function, boundary, return address); the
  seed control fails on the 155 and 39 cases whose missile drew. Development runs before these files (outputs in the
  session scratch, not cited): the first check found hit 44's EBX holding the y position (the model had the owner;
  corrected), `0x005A8F20`'s jump table undeclared (declared), the States count missing from `holy9c`'s spec (hit 8's
  `UNIT_HasState` read it; added), keys of JSON-loaded dicts read as integers in two models, and a decoy shared by
  the owner's hash chain and hit 22's stored unit (the writer now keeps them apart); the outputs above are from the
  final case files.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the hit functions' maps on returning cases
  (`[C]`: hit 3 with a unit, 7's type tests, 8, 10, 27 and every refusal path), and of their maps up to their boundary
  calls with the call site, the arguments, the pointed-to packet or context and all three seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0006 names each claim's boundary). The only
  seed any case steps before a boundary is the missile's (hits 1, 9, 13 through the `EType` roll; hit 7's heal); no
  case steps the owner's or the target's. A caller register that is not a boundary argument (the radius of hits 24,
  44 and 14 in EBX, EDI and ESI at `BuildDamage`) is compared but stays `[I]` (`lane/p46m3` review, ruling 1). Not
  covered: what any boundary callee does and everything after it; hit 2 (carried to batch 9d);
  faults (`MonsterOwnerRef` without MonsterData, `GameFindUnit` with a type above 5); when the game runs these
  functions or with which seed. (fn:sub_005A9FB0_MissHit07HolyBolt@0x005A9FB0, fn:sub_005AA650_MissHit10Guided@0x005AA650)

## run:2026-10-20-cat-emu-9d

- **Question:** (plan 0046 Phase 1, batch 9d) Do the missile server hit functions 31–33, 35–40, 43, 45, 47, 48,
  50–59 and the tier-A hit 2 map their inputs (the missile's record, `MissileData` words, owner, hit unit, path, room,
  object, stat lists, the owner's skill list, Skills and MonStats records, the game frame and the seeds) to the result
  they return, or to the arguments, pointed-to bytes and seed states at the call they end in, exactly as
  [skills/0007](0007-missile-hit-31-59.md) §§ 3–10 say, and do they leave the seeds the model leaves alone as they were?
- **Setup:** as run:2026-10-20-cat-emu-9c: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m4`, symbols replayed from `re/symbols.csv`, heap 3 GB),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the 9d families of `tools/skills_catalogue_emu.py` (`da004a4b…`; `tools/rng.py`,
  `tools/sweep_s4b.py`), with 9c's conventions: the call site of every boundary asserted with a site control, the
  missile's, the owner's and the target's seeds written and compared in every case (a control moves the missile's
  draws to the owner's seed in the two families that draw), a boundary's pointer argument into the caller's frame
  compared by content (the `MissileCreate` block, 0x5C bytes; the packet of `MISSILE_BuildDamage`, 0x70 bytes), and
  no model compares a callee-saved register that is not a boundary argument (`lane/p46m3` review, ruling 1). All
  inputs synthetic (stock parameter values among them); every case-writer draw from `random.Random("cat9d-<family>")`.
  Files in `workspace/logs/skills-cat-9d/`, `manifest.sha256` `6fa68cd0…` (29 files: cases, memory specs, expected
  inputs, outputs, the empty `.err` logs, `check.txt` `9ec69cf5…`, `static.txt` `d909b72d…`, `rows.txt`
  `9678d001…`, `repro.txt`); `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the
  same tool revision regenerates every case, memory and expectation file of 9a, 9b and 9c byte for byte and
  reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-9d
  python3 -I tools/skills_catalogue_emu.py cases --batch 9d
  for f in heal9d create9d nova9d area9d event9d; do
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m4 GHIDRA_HEADLESS_MAXMEM=3G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch 9d > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 9d > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 9d --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills,
  ItemStatCost, MonStats, MonStats2), names the boundaries (`observe`: 9c's and nine more, skills/0007 § 2) and
  guards the allocator; each case passes the hit unit on the stack and dumps the three seeds.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CAT9D heal9d   cases=1500 match=1500 bad=0 neg=246 traced=22 undeclared=0 stopped=0
  CAT9D create9d cases=2100 match=2100 bad=0 neg=617 traced=6  undeclared=0 stopped=0
  CAT9D nova9d   cases=1500 match=1500 bad=0 neg=462 traced=4  undeclared=0 stopped=0
  CAT9D area9d   cases=1500 match=1500 bad=0 neg=473 traced=5  undeclared=0 stopped=0
  CAT9D event9d  cases=1800 match=1800 bad=0 neg=211 traced=3  undeclared=0 stopped=0
  CAT9D static pins=50 pins_ok=50 ro_reads=5 table_entries=25 tabreads=4 tabreads_signed=4
  ```
  8 400 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 53 or more cases: `nocap43` 73, `ownseed` 140 and 181, `hp_swap` 344, `unit56` 378, `mode1` 106); the site
  control fails on all 3 796 matched boundary cases (28 `site` lines: function, boundary, return address). Development
  runs before these files (outputs overwritten, not cited): the first check found `event9d`'s object written without
  its type word, so `UnitGetRoom` (`0x00620BB0`) took the path branch for hit 35's object (58 cases observed
  `SetMode` or returned 1 where the model had the room pin; the writer now sets type 2), `area9d`'s `lenlt` control
  failing no case (no case had the rabies end frame at the length; the writer now puts 30 % of the hit-53 cases at
  the length, one under or one over) and no `area9d` control reaching 50 (`unit56` added), and one static pin one
  instruction off (hit 50's `jge` is at 0x005AC856). The outputs above are from the final case files.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the hit functions' maps on returning cases
  (`[C]`: hit 37, hit 50, hit 55's refusals, every refusal path) and of their maps up to their boundary calls with the
  call site, the arguments, the pointed-to block or packet and all three seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0007 names each claim's boundary). The seeds
  any case steps before a boundary are the missile's only: hit 31 (the `EType` roll), hit 43 (one `RNG_RangeB`), hit
  58 (re-seeded from its x, two `RNG_Range`). Row 568's `pSrvHitFunc` 64 948 is a static claim: all four reads of
  the hit table sit behind a signed `test ax, ax; jle`. Not covered: what any boundary callee does and everything
  after it; the fatal path after its first call (`0x00408090`); when the game runs these functions or with which seed.
  (fn:sub_005AC350_MissHit43HealVortex@0x005AC350, fn:sub_005ACDF0_MissHit58Reseed@0x005ACDF0)

## run:2026-10-20-cat-emu-sor

- **Question:** (plan 0046 Phase 1, batch `sor`) Do the sorceress start functions 11–14 and do functions 17–26, 28,
  29 and 144 (with the Inferno helpers `0x005C8CA0` and `0x005C8E30`) map their inputs (the Skills and Missiles
  records, the caster, its path, target link, rooms, stat and state lists, skill list and used skill, the target
  unit and its owner and alignment, the game frame, difficulty and expansion words, and the seeds) to the result they
  return, or to the arguments, pointed-to bytes, written words and seed states at the call they end in, exactly as
  [skills/0008](0008-sorceress.md) §§ 3–8 say, and do they leave the target's seed alone?
- **Setup:** as run:2026-10-20-cat-emu-9d: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m5`, symbols replayed from `re/symbols.csv`, heap 3 GB),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `sor` families of `tools/skills_catalogue_emu.py` (`7525830c…`; `tools/rng.py`,
  `tools/sweep_s4b.py`), with 9d's conventions: the call site of every boundary asserted with a site control, the
  caster's and the target's seeds written and compared in every case (a control moves do 21's draw to the target's
  seed), a boundary's pointer argument into the caller's frame compared by content (the `MissileCreate` blocks, the
  `STATE_ApplyTimed` block at ECX, the `SpawnOwnedMonster` block, do 20's 20-byte block, do 21's zeroed packet), and
  no model compares a callee-saved register that is not a boundary argument. Each case calls the function with
  `ECX` = the game, `EDX` = the caster and `(id, lvl)` on the stack (`(id, lvl, cls)` for the helpers). All inputs
  synthetic (stock parameter values among them); every case-writer draw from `random.Random("catsor-<family>")`.
  Files in `workspace/logs/skills-cat-sor/`, `manifest.sha256` `83d7c0f9…` (35 files: cases, memory specs, expected
  inputs, outputs, the `.err` logs (the scope line only), `cases.txt`, `check.txt` `961ccef7…`, `static.txt`
  `91a6de74…`, `rows.txt` `148cf553…`, `repro.txt` `9a74392b…`); `sha256sum -c manifest.sha256` from that directory
  passes. `repro.txt` records that the same tool revision regenerates every case, memory and expectation file of 9a,
  9b, 9c and 9d byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept
  outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-sor
  python3 -I tools/skills_catalogue_emu.py cases --batch sor > $D/cases.txt
  for f in start_sor inferno_sor create_sor state_sor tk_sor hydra_sor; do
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m5 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch sor > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch sor > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch sor --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills,
  Missiles, ItemStatCost, MonStats, MonStats2, the States and PetType counts), the missile table `0x0096C794` and
  the difficulty table `0x0096C8AC` at scratch tables (inputs of the claims; skills/0008 § 2), names the boundaries
  (`observe`: 9d's less `UnitsSameParty`, and fifteen more, skills/0008 § 2) and guards the allocator.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATSOR start_sor   cases=1500 match=1500 bad=0 neg=220 traced=51 undeclared=0 stopped=0
  CATSOR inferno_sor cases=1200 match=1200 bad=0 neg=246 traced=8  undeclared=0 stopped=0
  CATSOR create_sor  cases=1800 match=1800 bad=0 neg=330 traced=12 undeclared=0 stopped=0
  CATSOR state_sor   cases=1600 match=1600 bad=0 neg=153 traced=32 undeclared=0 stopped=0
  CATSOR tk_sor      cases=1200 match=1200 bad=0 neg=116 traced=65 undeclared=0 stopped=0
  CATSOR hydra_sor   cases=1200 match=1200 bad=0 neg=228 traced=80 undeclared=0 stopped=0
  CATSOR static data_stores=1 pins=35 pins_ok=35 ro_reads=7 table_entries=17
  ```
  8 500 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 60 or more cases: `inv14` 138, `inv18` 141, `c1lvl` 170, `a1_ge0` 79, `tseed` 93, `lvl_p2` 195); the site
  control fails on all 2 977 matched boundary cases (27 `site` lines: function, boundary, return address).
  Development runs before these files (outputs overwritten, not cited): two model slips (the `PlayerPairFlags`
  registers read from the wrong tuple slot; `PartyIdOfUnit`'s likewise), `UnitsSameParty` observed through 9c's
  boundary list (the batch now runs it emulated), do 26's second-argument slot outside the stack dump (now dumped at
  `0x7FF00008`), and three controls failing no case (`dist_ge`, `stun_le`, `charge_a`; the writer now places targets
  at `r`, the draw at `Param2` and charged lists on purpose). The outputs above are from the final case files.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  start 12, 13, 14, do 21's returns, every refusal path) and of their maps up to their boundary calls with the call
  site, the arguments, the pointed-to blocks, the written words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0008 names each claim's boundary). The only
  draw before a boundary is do 21's `RNG_Range(caster seed, 100)`; no case steps the target's seed. Not covered: what
  any boundary callee does and everything after it; do 27; when the game runs these functions or with which seed.
  (fn:sub_005C98F0_SkillDo21Telekinesis@0x005C98F0, fn:sub_00554200_UnitsHostile@0x00554200)

## run:2026-10-20-cat-emu-ama

- **Question:** (plan 0046 Phase 1, batch `ama`) Do the amazon start functions 4–10 and do functions 6, 7, 8 and
  10–16 map their inputs (the Skills, Missiles, MonStats and MonStats2 records, the caster, its path, target link,
  inventory word, skill list and used skill's node, the target unit and its owner and alignment, the units the node
  names, and the seeds) to the result they return, or to the arguments, pointed-to bytes, frame words, written words
  and seed states at the call they end in, exactly as [skills/0009](0009-amazon.md) §§ 3–8 say, and do they leave
  both seeds alone?
- **Setup:** as run:2026-10-20-cat-emu-sor: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m6`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `ama` families of `tools/skills_catalogue_emu.py` (`69c01d13…`), with `sor`'s conventions
  (the call site of every boundary asserted with a site control, the caster's and the target's seeds written and
  compared in every case, a boundary's pointer argument compared by content: the `MissileCreate` blocks, do 6's
  24-byte block, the `SpawnOwnedMonster` blocks, the zeroed hit packets, the counter `n`; no model compares a
  callee-saved register that is not a boundary argument). New: a boundary inside a helper (`0x00623990`,
  `0x00622870`, `0x0056BC80`, `UnitGetWeapon`) also compares the batch function's frame words written before it at
  their absolute stack address (`compare`'s ninth expectation field; every function's `EBP` is `0x7FEFFFFC`). All
  inputs synthetic (stock parameter values among them); every case-writer draw from
  `random.Random("catama-<family>")`. Files in `workspace/logs/skills-cat-ama/`, `manifest.sha256` `6a3181d8…` (37
  files: cases, memory specs, expected inputs, outputs, the `.err` logs (the scope line only), `cases.txt`,
  `check.txt` `03a40fde…`, `static.txt` `b1b51e31…`, `rows.txt` `d441af4c…` with its `rows.sh`, `repro.txt`
  `9b03d065…` with its `repro.sh`, the run script `run_ama.sh`); `sha256sum -c manifest.sha256` from that directory
  passes. `repro.txt` records that the same tool revision regenerates every case, memory and expectation file of 9a,
  9b, 9c, 9d and `sor` byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their
  kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-ama
  python3 -I tools/skills_catalogue_emu.py cases --batch ama > $D/cases.txt
  for f in start_ama hit_ama aura_ama create_ama node_ama summon_ama; do      # one at a time ($D/run_ama.sh)
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m6 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch ama > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch ama > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch ama --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills,
  Missiles, ItemStatCost, MonStats, MonStats2, the calc pool, the States and PetType counts), names the boundaries
  (`observe`: `sor`'s less `0x00623990`, plus `0x0063C9B0`, `0x00580310`, `0x0064F380`, `COMBAT_MeleeHitTest`,
  `MonAttackStats`, `COMBAT_DeliverQueued`, `UnitSetPathTargetUnit`, `InMeleeRange`) and guards the allocator and the
  fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATAMA start_ama  cases=1600 match=1600 bad=0 neg=1030 traced=7 undeclared=0 stopped=0
  CATAMA hit_ama    cases=1600 match=1600 bad=0 neg=385  traced=8 undeclared=0 stopped=0
  CATAMA aura_ama   cases=900  match=900  bad=0 neg=559  traced=2 undeclared=0 stopped=0
  CATAMA create_ama cases=1800 match=1800 bad=0 neg=513  traced=7 undeclared=0 stopped=0
  CATAMA node_ama   cases=1200 match=1200 bad=0 neg=218  traced=7 undeclared=0 stopped=0
  CATAMA summon_ama cases=1200 match=1200 bad=0 neg=915  traced=2 undeclared=0 stopped=0
  CATAMA static data_imms=0 data_stores=0 pins=34 pins_ok=34 ro_reads=4 table_entries=17
  ```
  8 300 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 96 or more cases: `filt_swap` 335, `tohit0` 175, `blk_swap` 295, `src_a` 323, `g_any` 122, `w24_zero` 715;
  the smallest, `nonorm`, 51); the site control fails on all 4 190 matched boundary cases (33 `site` lines: function,
  boundary, return address). The skills calc function count's scan names every operand form (`PTR` and `moffs`
  stores, immediates, reads): 0 stores, 0 immediates, 7 reads. The first session of this lane ran the six families at
  once and was killed by the system's out-of-memory handler before checking; the resumed lane regenerated its case
  files (byte-identical), re-ran the families one at a time and compared the new outputs with that session's before
  replacing them: byte-identical, so nothing of it is lost.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  start 4's and 5's results and every refusal path) and of their maps up to their boundary calls with the call site,
  the arguments, the pointed-to blocks, the frame words, the written words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0009 names each claim's boundary). No
  function draws before its boundary or return; no case steps either seed. Not covered: what any boundary callee does
  and everything after it (start 10's elemental draw among it); when the game runs these functions or with which
  seed. (fn:sub_005DB410_SkillDo08MultiShot@0x005DB410, fn:SKILLS_GetToHit@0x006449F0)

## run:2026-10-20-cat-emu-nec

- **Question:** (plan 0046 Phase 1, batch `nec`) Do the necromancer start functions 15–21 and do functions 30–32 and
  55–63 map their inputs (the Skills, ItemStatCost, MonStats, MonStats2 and item records, the difficulty table, the
  bit-set `DataTables+0x150`, the caster, its path, room and stat list, the target unit, its mode, flags, stat lists,
  state words, item data and room, and the seeds) to the result they return, or to the arguments, pointed-to blocks,
  frame words and seed states at the call they end in, exactly as [skills/0010](0010-necromancer.md) §§ 3–6 say, and
  do they leave both seeds alone?
- **Setup:** as run:2026-10-20-cat-emu-ama: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m7`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `nec` families of `tools/skills_catalogue_emu.py` (`27b93f23…`), with `ama`'s conventions (the call site of
  every boundary asserted with a site control, both seeds written and compared in every case, a boundary's pointer
  argument compared by content: do 30's and do 61's 0x68-byte blocks, the `SpawnOwnedMonster` blocks, the
  `COMBAT_ApplyDamage` packet, the zeroed hit packet; frame words at their absolute stack address; no model compares a
  callee-saved register that is not a boundary argument). New: a boundary inside a helper the batch function called
  (`0x005C2FF0`, `0x005C3300`, `0x005C31F0`, `0x005C5BC0`) also compares the helper's return address into the batch
  function at its absolute stack slot (ruling 1 of the `lane/p46m6` review); `static` lists every call of each helper.
  All inputs synthetic (stock parameter values among them); every case-writer draw from
  `random.Random("catnec-<family>")`. Files in `workspace/logs/skills-cat-nec/`, `manifest.sha256` `792c0cb4…` (28 files: cases, memory
  specs, expected inputs, outputs, the `.err` logs, `cases.txt`, `check.txt` `10fec33a…`, `static.txt` `c8bdc9e9…`,
  `rows.txt` `2e561e99…` with its `rows.sh`, `repro.txt` `387455f3…` with its `repro.sh`, the run script
  `run_nec.sh`); `sha256sum -c
  manifest.sha256` from that directory passes. `repro.txt` records that the same tool revision regenerates every case,
  memory and expectation file of 9a, 9b, 9c, 9d, `sor` and `ama` byte for byte and reproduces their kept `check.txt`
  and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-nec
  python3 -I tools/skills_catalogue_emu.py cases --batch nec > $D/cases.txt
  for f in start_nec curse_nec corpse_nec summon_nec; do      # one at a time ($D/run_nec.sh)
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m7 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch nec > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch nec > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch nec --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles,
  ItemStatCost, MonStats, MonStats2, the calc pool, the States and PetType counts, the bit-set at `+0x150`), sets
  `g_pDifficultyLevels`/`g_nDifficultyLevels` and `ITEMS_GetRecord`'s count and table, names the boundaries
  (`observe`: `ama`'s plus `sub_0056E780_SkillForUnitsNearTarget`, `COMBAT_ApplyDamage`, `0x0061A270`, `STATE_Set`,
  `0x0056E2F0`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATNEC start_nec  cases=1600 match=1600 bad=0 neg=295 traced=84 undeclared=0 stopped=0
  CATNEC curse_nec  cases=1400 match=1400 bad=0 neg=485 traced=4  undeclared=0 stopped=0
  CATNEC corpse_nec cases=1500 match=1500 bad=0 neg=238 traced=8  undeclared=0 stopped=0
  CATNEC summon_nec cases=1600 match=1600 bad=0 neg=1332 traced=90 undeclared=0 stopped=0
  CATNEC static data_imms=0 data_stores=0 helper_sites=8 pins=38 pins_ok=38 ro_reads=5 table_entries=19
  ```
  6 100 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 76 or more cases: `town_inv` 274, `aura1_read` 319, `nomiss0` 80, `w24_zero` 741; the weak ones fail on the
  deciding class skills/0010 § 2 names); the site control fails on all 1 891 matched boundary cases (17 `site` lines:
  function, boundary, return address). The skills calc function count's scan names every operand form (`PTR` and
  `moffs` stores, immediates, reads): 0 stores, 0 immediates, 7 reads. The first runs of the four families found three
  model faults (do 63's range exit returns 1, do 31's `0x0061A270` takes three stack words, the fatal path's return
  address is `0x00629CDA`) and low reach on the corpse and room paths; the models and case writers were fixed and every
  family re-run; the kept outputs are the last runs'.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  start 15's, 17's, 18's, 19's and 20's results and every refusal path) and of their maps up to their boundary calls
  with the call site, the helper return addresses, the arguments, the pointed-to blocks, the frame words, the written
  words and both seeds asserted (`[C]` under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md);
  skills/0010 names each claim's boundary). No function draws before its boundary or return; no case steps either
  seed. Not covered: what any boundary callee does and everything after it (do 55's and do 58's draws on the target's
  seed among it); when the game runs these functions or with which seed. (fn:sub_005C37C0_SkillDo30Curse@0x005C37C0,
  fn:sub_00645510_MonCorpseTest@0x00645510)

## run:2026-10-20-cat-emu-pal

- **Question:** (plan 0046 Phase 1, batch `pal`) Do the paladin start functions 29, 31, 35, 36, 37 and do functions
  64–67, 73, 79–82 and 150 map their inputs (the Skills, CharStats and MonStats records, the caster, its path, used
  skill node, queued hits, stat list and inventory word, the target unit, its stat lists and room, the game frame, and
  the seeds) to the result they return, or to the arguments, pointed-to blocks, node and frame words and seed states at
  the call they end in, exactly as [skills/0011](0011-paladin.md) §§ 3–5 say, and do they leave both seeds alone?
- **Setup:** as run:2026-10-20-cat-emu-nec: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m8`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `pal` families of `tools/skills_catalogue_emu.py` (`c1630af4…`), with `nec`'s conventions (the
  call site of every boundary asserted with a site control, both seeds written and compared in every case, a
  boundary's pointer argument compared by content: the aura functions' 0x50-byte blocks and their 16-byte context
  passed in `ECX`, the `COMBAT_ApplyDamage` packet, the zeroed hit packet, the `MissileCreate` blocks; the used skill's
  node words dumped and compared; no model compares a callee-saved register that is not a boundary argument; a boundary
  inside a helper compares the helper's return address at its stack slot, or the helper's single call site is listed by
  `static`). New: `0x0056B740` runs emulated, so the aura boundary is `AURA_ApplyToTarget` entered through an indirect
  call. All inputs synthetic (stock parameter values among them); every case-writer draw from
  `random.Random("catpal-<family>")`. Files in `workspace/logs/skills-cat-pal/`, `manifest.sha256` `12c8d5c0…` (23
  files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`, `check.txt` `989e5367…`,
  `static.txt` `5fd43532…`, `rows.txt` `dc96db87…` with its `rows.sh`, `repro.txt` `daf042cc…` with its `repro.sh`, the
  run script `run_pal.sh`); `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the
  same tool revision regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama` and `nec` byte
  for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-pal
  python3 -I tools/skills_catalogue_emu.py cases --batch pal > $D/cases.txt
  for f in aura_pal melee_pal move_pal; do      # one at a time ($D/run_pal.sh)
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m8 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch pal > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch pal > $D/static.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch pal --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles,
  ItemStatCost, MonStats, MonStats2, CharStats, the calc pool, the States and PetType counts), names the boundaries
  (`observe`: `nec`'s plus `AURA_ApplyToTarget`, `0x0063C8F0`, `0x006633B0`, `sub_00648690_PathSetSpeed`,
  `0x00649050`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATPAL aura_pal  cases=1600 match=1600 bad=0 neg=907 traced=3 undeclared=0 stopped=0
  CATPAL melee_pal cases=1750 match=1750 bad=0 neg=213 traced=9 undeclared=0 stopped=0
  CATPAL move_pal  cases=1600 match=1600 bad=0 neg=381 traced=8 undeclared=0 stopped=0
  CATPAL static data_imms=0 data_stores=0 helper_sites=16 pins=40 pins_ok=40 ro_reads=4 table_entries=15
  ```
  4 950 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 134 or more cases: `npf6` 552, `inv_any` 134, `xy73` 153; the weak ones fail on the deciding class
  skills/0011 § 2 names); the site control fails on all 2 615 matched boundary cases (21 `site` lines: function,
  boundary, return address). The skills calc function count's scan names every operand form (`PTR` and `moffs` stores,
  immediates, reads): 0 stores, 0 immediates, 7 reads. Every family matched on its first emulation; one tool fault (a
  pal model helper that shadowed a `sor` helper of the same name) was caught by `repro.sh` before the kept files were
  written and renamed; the case files did not change.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  start 36's and start 37's results, do 64's and do 65's 1, every refusal path) and of their maps up to their boundary
  calls with the call site, the helper return addresses, the arguments, the pointed-to blocks and context, the node and
  frame words and both seeds asserted (`[C]` under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md);
  skills/0011 names each claim's boundary). No function draws before its boundary or return; no case steps either
  seed. Not covered: what any boundary callee does and everything after it (the aura target passes and their draws on
  the caster's and the units' seeds, start 35's and do 79's draws on the caster's seed among it); when the game runs
  these functions or with which seed. (fn:sub_005CF010_PalAuraDo@0x005CF010, fn:sub_005CE8E0_SkillDo64SacrificeSelfHit@0x005CE8E0)

## run:2026-10-21-cat-emu-bar

- **Question:** (plan 0046 Phase 1, batch `bar`) Do the barbarian start functions 32–34 and 38–41 and do functions 2,
  9, 68–72 and 74–78 map their inputs (the Skills and MonStats2 records, the caster, its path, used-skill node, unit
  skill chain, queued hits, stat lists, `+0x38` word and inventory word, the target unit, its stat lists, room and
  position, the rooms, the game frame and pool word, and the seeds) to the result they return, or to the arguments,
  pointed-to blocks, node, path and frame words and seed states at the call they end in, exactly as
  [skills/0012](0012-barbarian.md) §§ 3–6 say, and do they leave both seeds alone?
- **Setup:** as run:2026-10-20-cat-emu-pal: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m9`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `bar` families of `tools/skills_catalogue_emu.py` (`613471e3…`), with `pal`'s conventions
  (the call site of every boundary asserted with a site control, both seeds written and compared in every case, a
  boundary's pointer argument compared by content: the hit packet, do 75's and start 40's points, `NovaAtUnit`'s block,
  do 71's search context; the node, path and list words dumped and compared; register arguments compared only where the
  callee reads them before writing them; no model compares a callee-saved register that is not a boundary argument; a
  boundary inside a helper compares the helper's return address at its absolute stack slot, the helpers' call sites
  listed by `static`). All inputs synthetic (stock parameter values among them); every case-writer draw from
  `random.Random("catbar-<family>")`. Files in `workspace/logs/skills-cat-bar/`, `manifest.sha256` `737c8b4f…` (28
  files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`, `check.txt` `13b1a4d2…`,
  `static.txt` `4808f177…`, `rows.txt` `9646927a…` with its `rows.sh`, `repro.txt` `65c7b964…` with its `repro.sh`, the
  run script `run_bar.sh`); `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the
  same tool revision regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec` and
  `pal` byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-bar
  python3 -I tools/skills_catalogue_emu.py cases --batch bar > $D/cases.txt
  for f in cry_bar hit_bar corpse_bar move_bar; do      # one at a time ($D/run_bar.sh)
    GHIDRA_PROJ_DIR=workspace/ghidra-p46m9 GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_catalogue_emu.py check  --batch bar > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch bar > $D/static.txt
  $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch bar --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles,
  ItemStatCost, MonStats, MonStats2, the calc pool, the States, PetType and overlay counts, the `+0x150` state set),
  names the boundaries (`observe`: `pal`'s plus `0x0056E520`, `UnitQueueEvent`, `FreeNearFallback`, `PathSetType`,
  `MonSkillAttackDo`, `COLL_PatternTestBool`, `0x005D9460`, `0x00553DC0`, `0x006212C0`, `0x005DA120`, `0x005D9F70`,
  `0x005DA660`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATBAR hit_bar    cases=1750 match=1750 bad=0 neg=357 traced=67 undeclared=0 stopped=0
  CATBAR corpse_bar cases=2500 match=2500 bad=0 neg=233 traced=7 undeclared=0 stopped=0
  CATBAR cry_bar    cases=800 match=800 bad=0 neg=542 traced=9 undeclared=0 stopped=0
  CATBAR move_bar   cases=1750 match=1750 bad=0 neg=236 traced=21 undeclared=0 stopped=0
  CATBAR static data_imms=0 data_stores=0 helper_sites=49 pins=45 pins_ok=45 ro_reads=6 table_entries=19
  ```
  6 800 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more cases: `par_low` 224, `no12` 109, `vel1` 257, `x1` 90; the weak ones fail on the deciding class
  skills/0012 § 2 names); the site control fails on all 2 397 matched boundary cases (39 `site` lines: function,
  boundary, return address). The skills calc function count's scan names every operand form (`PTR` and `moffs` stores,
  immediates, reads): 0 stores, 0 immediates, 7 reads. `hit_bar` and `cry_bar` matched on their first emulation (one
  fix to the declared read set: `NovaAtUnit`'s offsets); the first `corpse_bar` and `move_bar` runs mismatched on tool
  faults (missing dumps of the compared node, path and list words; do 76's `+0xC6` byte written over the compared
  `+0xC4` word; too few points inside rooms to reach two free-spot calls), fixed in the case writers before the kept
  run; those first outputs were overwritten by the kept run of the same file names.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  start 33's and start 34's results, do 78's 1 with its node word, every refusal path) and of their maps up to their
  boundary calls with the call site, the helper return addresses, the arguments (register arguments where the callee
  reads them first), the pointed-to blocks, the node, path and frame words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0012 names each claim's boundary). No function
  draws before its boundary or return; no case steps either seed. Not covered: what any boundary callee does and
  everything after it (do 69's and do 72's draws on the caster's seed, do 69's inline step, the hits' elemental rolls
  among it); when the game runs these functions or with which seed. (fn:sub_005D81C0_SkillDo69FindPotion@0x005D81C0,
  fn:sub_005D9A10_LeapPoint@0x005D9A10)

## run:2026-10-21-cat-emu-dru

- **Question:** (plan 0046 Phase 1, batch `dru`) Do the druid start functions 56–58, do functions 114–124 and do-table
  entries 145 and 146 map their inputs (the Skills and Missiles records, the caster, its path, used-skill node, unit
  skill chain, stat lists and state words, the target unit and its position, the rooms and their collision maps, the
  state list at `DataTables+0x17C`, the game frame and pool word, and the seeds) to the result they return, or to the
  arguments, pointed-to blocks, node, frame and argument-slot words and seed states at the call they end in, exactly
  as [skills/0013](0013-druid.md) §§ 3–7 say, and which seed does each draw before its boundary step?
- **Setup:** as run:2026-10-21-cat-emu-bar: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m10`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged (`286393aa…`). No wine, nothing runs natively, no slot. Models, case
  writers and checks: the `dru` families of `tools/skills_catalogue_emu.py` (`11b763dd…`; the kept outputs were
  emulated from case files that this revision regenerates byte for byte, and it reproduces the kept `check.txt` byte
  for byte), with `bar`'s conventions (the call site of every boundary asserted with a site control, both seeds written
  and compared in every case, a boundary's pointer argument compared by content: the spawn blocks, the hit packets,
  the `MissileCreate` blocks, `COLL_RectTest`'s rectangle; the node and argument-slot words dumped and compared;
  register arguments compared only where the callee reads them before writing them; no model compares a callee-saved
  register that is not a boundary argument; a boundary inside a helper compares the helper's return address at its
  absolute stack slot, the helpers' call sites listed by `static`). All inputs synthetic (stock parameter values among
  them); every case-writer draw from `random.Random("catdru-<family>")`. Files in `workspace/logs/skills-cat-dru/`,
  `manifest.sha256` `d1a77e1f…` (69 files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`,
  `check.txt` `592baf51…`, `static.txt` `d2c98496…`, `rows.txt` `fba56eef…` with its `rows.sh`, `repro.txt`
  `c6f4b37b…` with its `repro.sh`, the run script `run_dru.sh`, and the two development runs under `dev/` with
  `dev/notes.txt`); `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the same tool
  revision regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal` and `bar`
  byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-dru
  python3 -I tools/skills_catalogue_emu.py cases --batch dru > $D/cases.txt
  $D/run_dru.sh $D summon_dru shape_dru melee_dru miss_dru     # one EmuBoundary instance at a time, each in a 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch dru > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch dru > $D/static.txt
  $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch dru --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles,
  ItemStatCost, MonStats, MonStats2, the calc pool, the States, PetType counts and the States record base), names the
  boundaries (`observe`: `bar`'s less `COLL_WHTest`, which runs here, plus `COMBAT_BuildDamage`, `StatListSetEnd`,
  `UNIT_UnlinkStatList`, `COLL_RectTest`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATDRU summon_dru cases=1500 match=1500 bad=0 neg=1622 traced=7 undeclared=0 stopped=0
  CATDRU shape_dru  cases=2500 match=2500 bad=0 neg=620 traced=84 undeclared=0 stopped=0
  CATDRU melee_dru  cases=2400 match=2400 bad=0 neg=438 traced=41 undeclared=0 stopped=0
  CATDRU miss_dru   cases=2000 match=2000 bad=0 neg=441 traced=9 undeclared=0 stopped=0
  CATDRU static data_imms=0 data_stores=0 helper_sites=25 pins=43 pins_ok=43 ro_reads=4 table_entries=16
  ```
  8 400 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more cases: `w24_zero` 735, `notown` 134, `rf_ignored` 171, `c1_ge0` 156; the weak ones fail on the
  deciding class skills/0013 § 2 names); the site control fails on all 3 967 matched boundary cases (33 `site` lines:
  function, boundary, return address; 747 + 1 694 + 931 + 595). The skills calc function count's scan names every
  operand form: 0 stores, 0 immediates, 7 reads. Two development runs came first and are kept under their own names in
  `dev/` (`dev/notes.txt`): the first mismatched on 3 do 121 cases (the model walked the whole state list where the
  case wrote a count of 0) and had one control that did not fail (no class past the Missiles count); the second matched
  in full; the writers were re-weighted between them and one control added before the kept run.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, do 119's and do 123's 0, do 118's and do 120's 1) and of their maps up to their boundary calls
  with the call site, the helper return addresses, the arguments (register arguments where the callee reads them
  first), the pointed-to blocks, the node, frame and argument-slot words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0013 names each claim's boundary). Two
  functions draw before their boundary, each one `RNG_Range` on the caster's seed: do 124 (`0x10000`, the value at
  `ebp−0xC`) and do 123 (`0x100`, the low byte at `[ebp+0x8]`); no case steps the target's seed. Not covered: what any
  boundary callee does and everything after it (entry 146's re-seed of the caster's seed and its free-point draws,
  entry 145's damage rolls, the hits' elemental rolls among it); when the game runs these functions or with which seed.
  (fn:sub_005C8190_SkillDo124PeriodicState@0x005C8190, fn:sub_005C8080_SkillDo123Volcano@0x005C8080)

## run:2026-10-21-cat-emu-ass

- **Question:** (plan 0046 Phase 1, batch `ass`) Do the assassin start functions 22–28, do functions 33–52 and 54 and
  the progressive entries 36–41 and 143 map their inputs (the Skills, Missiles and Levels records, the caster, its
  path, used-skill node, unit skill chain, stat lists, state words, inventory word and queued hits, the target unit and
  its position, the rooms, a monster caster's owner, the game frame and pool word, and the seeds) to the result they
  return, or to the arguments, pointed-to blocks, node, frame, argument-slot and stack-seed words and seed states at the
  call they end in, exactly as [skills/0014](0014-assassin.md) §§ 3–6 say, and which seed does each draw before its
  boundary step?
- **Setup:** as run:2026-10-21-cat-emu-dru: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m11`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged. No wine, nothing runs natively, no slot. Models, case writers and
  checks: the `ass` families of `tools/skills_catalogue_emu.py` (`b38bba31…`; the kept outputs were emulated from case
  files this revision regenerates byte for byte, and it reproduces the kept `check.txt` byte for byte), with `dru`'s
  conventions (the call site of every boundary asserted with a site control, both seeds written and compared in every
  case, a boundary's pointer argument compared by content: the hit packets, the `MissileCreate`, spawn and
  `ApplyTimed` blocks; the node, argument-slot, frame and stack-seed words dumped and compared; register arguments
  compared only where the callee reads them before writing them; no model compares a callee-saved register that is not
  a boundary argument; a boundary inside a helper compares the helper's return address at its absolute stack slot, the
  helpers' call sites listed by `static`). All inputs synthetic (stock parameter values among them); every case-writer
  draw from `random.Random("catass-<family>")`. Files in `workspace/logs/skills-cat-ass/`, `manifest.sha256`
  `04f487b6…` (70 files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`, `check.txt`
  `dd6ed294…`, `static.txt` `fcf4be4f…`, `rows.txt` `3f8ff8a8…` with its `rows.sh`, `repro.txt` `43e65419…` with its
  `repro.sh`, the run script `run_ass.sh`, and the two development runs under `dev/` with `dev/notes.txt`);
  `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the same tool revision
  regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal`, `bar` and `dru`
  byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-ass
  python3 -I tools/skills_catalogue_emu.py cases --batch ass > $D/cases.txt
  $D/run_ass.sh $D start_ass hit_ass prg_ass trap_ass     # one EmuBoundary instance at a time, each in a 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch ass > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch ass > $D/static.txt
  $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch ass --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles,
  ItemStatCost, MonStats, MonStats2, the calc pool, the States, PetType counts and the Levels records at `+0xC58`/
  `+0xC5C`), sets the missile table and count `MissileSpeedAtLevel` reads (`0x0096C794`/`0x0096C79C`, as in `sor`),
  names the boundaries (`observe`: `dru`'s plus `COMBAT_PrgFinisher`, `InvGetBodyLocItem`, `UnitTeleport`,
  `0x006229F0`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATASS start_ass cases=2100 match=2100 bad=0 neg=507 traced=64 undeclared=0 stopped=0
  CATASS hit_ass   cases=2100 match=2100 bad=0 neg=632 traced=63 undeclared=0 stopped=0
  CATASS prg_ass   cases=2100 match=2100 bad=0 neg=1559 traced=12 undeclared=0 stopped=0
  CATASS trap_ass  cases=2400 match=2400 bad=0 neg=511 traced=97 undeclared=0 stopped=0
  CATASS static data_imms=0 data_stores=0 helper_sites=22 pins=66 pins_ok=66 ro_reads=5 table_entries=29
  ```
  8 700 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more cases: `st25_inv` 300, `parity_inv` 350, `noseed` 1 200, `pet_keep` 165; the weak ones fail on
  the deciding class skills/0014 § 2 names); the site control fails on all 3 020 matched boundary cases (37 `site`
  lines: function, boundary, return address; 685 + 753 + 674 + 908). The skills calc function count's scan names every
  operand form: 0 stores, 0 immediates, 7 reads. Two development runs came first and are kept under their own names in
  `dev/` (`dev/notes.txt`): the first mismatched on 131 do 46 and do 52 cases and one start 26 case (the model read the
  json row's stat values by integer key; the keys are strings) and had two controls that did not fail; the second
  matched in full; the writers were re-weighted between them and before the kept run.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, start 22's and 25's results, do 35's 1, entry 39's and 41's 1, do 54's town 1) and of their maps
  up to their boundary calls with the call site, the helper return addresses, the arguments (register arguments where
  the callee reads them first), the pointed-to blocks, the node, frame, argument-slot and stack-seed words and both
  seeds asserted (`[C]` under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0014 names each
  claim's boundary). Four entries draw before their boundary, each one inline step of the caster's seed at entry before
  the record test: 37 and 143 (then one step of the ring's stack seed), 39 (then two `RNG_Range` of its stack seed per
  try) and 41 (then two steps of its stack seed); no case steps the target's seed. Not covered: what any boundary
  callee does and everything after it (do 33's knock step and do 42's `RNG_Range(100)` on the caster's seed, the
  physical and elemental rolls, the finisher, the rings' later creations among it); when the game runs these functions
  or with which seed. (fn:sub_005D4E70_SkillPrgDo37Ring@0x005D4E70, fn:sub_005D3F90_SkillPrgDo39Scatter@0x005D3F90,
  fn:sub_005D5080_SkillPrgDo41Scatter@0x005D5080)

## run:2026-10-21-cat-emu-item

- **Question:** (plan 0046 Phase 1, batch 10 `item`) Do Unsummon's start 3 and do 4, do 113, do 151, `ITEMSKILL_Cast`
  with its `ItemTarget` helpers and its two callers `ItemCastAtUnit` / `ItemCastAtXY`, the stat-event handlers 20, 21
  and 30, the shrine functions 19, 21 and 22 and `SKILLS_PayCost` map their inputs (the Skills, PetType, Books, Shrines
  and item records, the item-type equivalence words, the caster, its path, used node, pet lists, inventory and items,
  stat lists and state words, the target, the stored unit, the event packet, the shrine and its context, and the
  seeds) to the result they return, or to the arguments, pointed-to blocks, path, node, frame and out words and seed
  states at the call they end in, exactly as [skills/0015](0015-item.md) §§ 3–8 say, and which seed does each draw
  before its boundary step?
- **Setup:** as run:2026-10-21-cat-emu-ass: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m12`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged. No wine, nothing runs natively, no slot. Models, case writers and
  checks: the `item` families of `tools/skills_catalogue_emu.py` (`904fe25e…`; the kept outputs were emulated from case
  files this revision regenerates byte for byte, written by `fc207804…`, which differs only in the `CLASS` lines of
  `check`), with `ass`'s conventions (the call site of every boundary asserted with a site control; the caster's, the
  target's and the shrine's seeds written and compared in every case; a boundary's pointer argument compared by
  content: the `MissileCreate` blocks and shrine 19's search block; the node, path, out, argument-slot and frame words
  dumped and compared; register arguments compared only where the callee reads them before writing them, `EAX`
  among them for `UseCharge`; a boundary inside a helper or inside `ITEMSKILL_Cast` called by its callers compares the
  return address at its absolute stack slot). All inputs synthetic (stock parameter values among them); every
  case-writer draw from `random.Random("catitem-<family>")`. Files in `workspace/logs/skills-cat-item/`,
  `manifest.sha256` `3e974e32…` (118 files: cases, memory specs, expected inputs, outputs, the `.err` logs,
  `cases.txt`, `check.txt` `22402718…`, `static.txt` `55299029…`, `rows.txt` `a9e0cb25…` with its `rows.sh`, `repro.txt`
  `41e54f5b…` with its `repro.sh`, `cg.txt` `42b678eb…` with `cg.sh` and the five call-graph files, the run script
  `run_item.sh`, and the three development runs under `dev/` with `dev/notes.txt`); `sha256sum -c manifest.sha256`
  from that directory passes. `repro.txt` records that the same tool revision regenerates every case, memory and
  expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal`, `bar`, `dru` and `ass` byte for byte and reproduces
  their kept `check.txt` and `static.txt` byte for byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-item
  python3 -I tools/skills_catalogue_emu.py cases --batch item > $D/cases.txt
  $D/run_item.sh $D use_item cast_item event_item shrine_item cost_item   # one EmuBoundary instance at a time, 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch item > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch item > $D/static.txt
  $D/rows.sh > $D/rows.txt; $D/cg.sh > $D/cg.txt; $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch item --write
  ```
  Each memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, the calc
  pool, ItemStatCost, the States, PetType counts and records, the item-type count, stride and equivalence words, the
  item-skill layer shift 6 and mask 0x3F), sets `ITEMS_GetRecord`'s and `BOOKS_GetRecord`'s counts and tables
  (`0x0096CA58`/`0x0096CA5C`, `0x0096CC60`/`0x0096CC64`) and the cookie, names the family's boundaries (`observe`) and
  guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CATITEM use_item    cases=2400 match=2400 bad=0 neg=1069 traced=13 undeclared=0 stopped=0
  CATITEM cast_item   cases=3000 match=3000 bad=0 neg=1701 traced=11 undeclared=0 stopped=0
  CATITEM event_item  cases=3000 match=3000 bad=0 neg=1757 traced=2 undeclared=0 stopped=0
  CATITEM shrine_item cases=1800 match=1800 bad=0 neg=2474 traced=1 undeclared=0 stopped=0
  CATITEM cost_item   cases=1800 match=1800 bad=0 neg=597 traced=2 undeclared=0 stopped=0
  CATITEM static data_imms=0 data_stores=0 helper_sites=72 pins=74 pins_ok=74 ro_reads=4 table_entries=12
  ```
  12 000 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more: `flag0` 531, `aim_none` 471, `layer_full` 1 037, `sh_noseed` 784, `no_min` 241; the thinner ones
  equal their deciding classes on the `CLASS` lines); the site control fails on all 4 936 matched boundary cases (31
  `site` lines: function, boundary, return address; 934 + 1 317 + 386 + 1 800 + 499). The skills calc function count's
  scan names every operand form: 0 stores, 0 immediates, 7 reads. The static call graphs (`cg.txt`): helpers 3 and 4
  and `0x0056E390` hold no LCG step or RNG call (586, 554, 578 functions; 56, 54, 56 indirect calls not followed),
  helper 2 only its own (564), `SKILLS_PayCost` none (619; 57). Three development runs came first and are kept in
  `dev/` (`dev/notes.txt`): the first mismatched on 61 `cast_item` cases (the writer left the caster's hash slot
  unwritten and the emulator, which keeps memory between cases, read an earlier case's slot); the second and third
  matched in full; the writers were re-weighted between them.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, start 3's mark and 1, the cast's restore, `ItemTgtDo`'s 1 with no other unit, the cost's 0s)
  and of their maps up to their boundary calls with the call site, the nested return addresses, the arguments
  (register arguments where the callee reads them first), the pointed-to blocks, the path, node, out and frame words
  and the three seeds asserted (`[C]` under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md);
  skills/0015 names each claim's boundary). Draws before the boundaries: handlers 20 (packet condition) and 30 one
  inline step of the unit's seed, handler 21 `RNG_RangeB(unit, 100)`, `ITEMSKILL_Cast`'s helper 2 two steps of the
  cast's caster's seed, shrines 21 and 22 `RNG_RangeB(shrine, Arg1 − Arg0)` on the shrine's seed; no other case steps a
  seed. Not covered: what any boundary callee does and everything after it (the casts' do functions, helper 2's later
  tries, the potions and missiles of the shrines, `UseCharge`); when the game runs these functions or with which
  seed. (fn:ITEMSKILL_Cast@0x005FDA80, fn:sub_005FD850_ItemTargetRandomPoint@0x005FD850,
  fn:sub_005C0470_StatEv20SkillOnEvent@0x005C0470, fn:SHRINE_Exploding@0x005830E0)

## run:2026-10-21-cat-emu-8a

- **Question:** (plan 0046 Phase 1, batch 8a) Do the monster start functions 42–53 and do functions 83–98, 110 and 111
  map their inputs (the Skills, Missiles, MonStats and MonStats2 records, the caster, its path, used node, stat lists,
  state words, frame words and owner link, the target, its path, stat list and state words, the rooms, the game frame
  and pool word, and the seeds) to the result they return, or to the arguments, pointed-to blocks, node, path, frame and
  argument-slot words and seed states at the call they end in, exactly as [skills/0016](0016-monster-8a.md) §§ 3–6
  say, and which seed does each draw before its boundary step?
- **Setup:** as run:2026-10-21-cat-emu-item: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m13`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged. No wine, nothing runs natively, no slot. Models, case writers and
  checks: the `8a` families of `tools/skills_catalogue_emu.py` (`e2f67728…`; the kept outputs were emulated from case
  files this revision regenerates byte for byte, and it reproduces the kept `check.txt` and `static.txt` byte for byte),
  with `item`'s conventions (the call site of every boundary asserted with a site control; the caster's and the target's
  seeds written and compared in every case; a boundary's pointer argument compared by content: the hit packets and the
  `MissileCreate` blocks; the node, path, frame and both argument-slot words dumped and compared, each dumped byte
  written by the case; register arguments compared only where the callee reads them before writing them; a boundary
  inside a helper compares the helper's return address at its absolute stack slot). All inputs synthetic (stock
  parameter values among them); every case-writer draw from `random.Random("cat8a-<family>")`. Files in
  `workspace/logs/skills-cat-8a/`, `manifest.sha256` `10a8ce1f…` (106 files: cases, memory specs, expected inputs, outputs, the `.err` logs,
  `cases.txt`, `check.txt` `b06f25a1…`, `static.txt` `f4ed00d9…`, `rows.txt` `d842e64a…` with its `rows.sh`, `repro.txt`
  `485fdbef…` with its `repro.sh`, the run script `run_8a.sh`, and the three development runs under `dev/` with `dev/notes.txt`);
  `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the same tool revision
  regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal`, `bar`, `dru`,
  `ass` and `item` byte for byte and reproduces their kept `check.txt` and `static.txt` byte for byte from their kept
  outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-8a
  python3 -I tools/skills_catalogue_emu.py cases --batch 8a > $D/cases.txt
  $D/run_8a.sh $D hit_8a move_8a summon_8a miss_8a aura_8a   # one EmuBoundary instance at a time, 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch 8a > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 8a > $D/static.txt
  $D/rows.sh > $D/rows.txt; $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 8a --write
  ```
  The memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills, Missiles
  with count 48, ItemStatCost, MonStats, MonStats2, the calc pool, the States and PetType counts, the state set at
  `+0xD4`, the overlay count), sets `MONSTATS_GetClassChainPos`'s table and count (`0x0096C6A8`/`0x0096C6B0`) and the
  cookie, names the boundaries (`observe`; the allocator `0x0040B430` in `aura_8a` only) and guards the allocator and
  the fatal path elsewhere.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CAT8A hit_8a    cases=2400 match=2400 bad=0 neg=679 traced=31 undeclared=0 stopped=0
  CAT8A move_8a   cases=2600 match=2600 bad=0 neg=953 traced=7 undeclared=0 stopped=0
  CAT8A summon_8a cases=2500 match=2500 bad=0 neg=795 traced=346 undeclared=0 stopped=0
  CAT8A miss_8a   cases=2500 match=2500 bad=0 neg=432 traced=434 undeclared=0 stopped=0
  CAT8A aura_8a   cases=600 match=600 bad=0 neg=409 traced=5 undeclared=0 stopped=0
  CAT8A static data_imms=0 data_stores=0 entry_words=30 helper_sites=51 pins=52 pins_ok=52 ro_reads=8 table_entries=30
  ```
  12 600 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more: `q40` 249, `f_le1` 200, `keep3c` 251, `axis_swap` 162, `r_lvl1` 409; the thinner ones equal their
  deciding classes on the nine `CLASS` lines); the site control fails on all 5 135 matched boundary cases (31 `site`
  lines: function, boundary, return address; 1 041 + 1 459 + 970 + 1 159 + 506). The `.data` reads have no writer in
  `.text`: the skills calc function count (0 stores, 0 immediates, 7 reads) and the byte map `0x00745600` (three reads
  in `0x007455C0`–`0x007456FF`, no store, no immediate). Three development runs came first and are kept in `dev/`
  (`dev/notes.txt`): the start 32 return slot guessed, do 98 modelled after an id test it does not make, `PathDirection`'s
  ratio leaving its table for far points (the writer now keeps do 87's and do 88's points within 250 subtiles), and do
  93's target words read as a point (they are offsets).
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, start 46's node words, start 51's and 52's flag words, do 94's frame test, start 53's state-12
  return, do 86's `n ≤ 0` return) and of their maps up to their boundary calls with the call site, the nested return
  addresses, the arguments (register arguments where the callee reads them first), the pointed-to blocks and packets,
  the node, path, argument-slot and frame words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0016 names each claim's boundary). One draw
  before a boundary: do 96's `RNG_RangeB(caster, hi − lo)`; no other case steps a seed. Not covered: what any boundary
  callee does and everything after it (the spawns, the hits' delivery, the missiles, the continuations after
  `CancelEvents`, do 111's loop); when the game runs these functions or with which seed.
  (fn:sub_005CC840_SkillDo96Heal@0x005CC840, fn:sub_0064FC60_PathDirection@0x0064FC60,
  fn:sub_005CAE40_SkillSt42FireHit@0x005CAE40)

## run:2026-10-21-cat-emu-8b

- **Question:** (plan 0046 Phase 1, batch 8b) Do the monster start functions 54, 55, 59, 60, 64 and do functions
  99–109, 112, 125–127, 141 and 152 map their inputs (the Skills, Missiles, MonStats and MonStats2 records, the caster,
  its path, used node, stat lists, state words, frame words, queued hits and owner link, the target, its path and stat
  list, the rooms, the game frame and the seeds) to the result they return, or to the arguments, pointed-to blocks and
  packets, node, path and argument-slot words and seed states at the call they end in, exactly as
  [skills/0017](0017-monster-8b.md) §§ 3–5 say, and which seed does each draw before its boundary step?
- **Setup:** as run:2026-10-21-cat-emu-8a: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m14`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged. No wine, nothing runs natively, no slot. Models, case writers and
  checks: the `8b` families of `tools/skills_catalogue_emu.py` (`ba63f2a8…`; the kept outputs were emulated from case
  files this revision regenerates byte for byte, and it reproduces the kept `check.txt` and `static.txt` byte for byte),
  with 8a's conventions (the call site of every boundary asserted with a site control; the caster's and the target's
  seeds written and compared in every case; a boundary's pointer argument compared by content: the `MissileCreate`
  blocks, the hit packets, do 112's curse block, do 141's area block; the node, path, frame and argument-slot words
  dumped and compared, each dumped byte written by the case; register arguments compared only where the callee reads
  them before writing them; a boundary inside a helper compares the helper's return address at its absolute stack
  slot). All inputs synthetic (stock parameter values among them); every case-writer draw from
  `random.Random("cat8b-<family>")`. Files in `workspace/logs/skills-cat-8b/`, `manifest.sha256` `1c9c42ff…` (118
  files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`, `check.txt` `2f000a04…`,
  `static.txt` `4c181a27…`, `rows.txt` `46d85e01…` with its `rows.sh`, `repro.txt` `948be1e1…` with its `repro.sh`, the run
  script `run_8b.sh`, and the four development runs under `dev/` with `dev/notes.txt` and the first repro
  `dev/repro-dev1.txt`); `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the same
  tool revision regenerates every case, memory and expectation file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal`,
  `bar`, `dru`, `ass`, `item` and 8a byte for byte and reproduces their kept `check.txt` and `static.txt` byte for
  byte from their kept outputs.
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-8b
  python3 -I tools/skills_catalogue_emu.py cases --batch 8b > $D/cases.txt
  $D/run_8b.sh $D curse_8b move_8b hit_8b miss_8b   # one EmuBoundary instance at a time, 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch 8b > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 8b > $D/static.txt
  $D/rows.sh > $D/rows.txt; $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 8b --write
  ```
  The memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills with count 3,
  or 92 for `curse_8b` so that do 112's curse rows exist; Missiles with count 48; ItemStatCost, MonStats, MonStats2,
  the calc pool, the States and PetType counts, the state set at `+0xD4`, the overlay count), sets
  `MONSTATS_GetClassChainPos`'s table and count, `sub_00663270_MissileSpeedAtLevel`'s missile table and count
  (`0x0096C794`/`0x0096C79C`) and the cookie, names the boundaries (`observe`) and guards the allocator and the fatal
  path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CAT8B miss_8b  cases=3200 match=3200 bad=0 neg=1088 traced=11 undeclared=0 stopped=0
  CAT8B hit_8b   cases=2800 match=2800 bad=0 neg=374 traced=10 undeclared=0 stopped=0
  CAT8B move_8b  cases=2400 match=2400 bad=0 neg=1129 traced=48 undeclared=0 stopped=0
  CAT8B curse_8b cases=800 match=800 bad=0 neg=1158 traced=12 undeclared=0 stopped=0
  CAT8B static d152_differ=0 data_imms=0 data_stores=0 entry_words=22 helper_sites=11 pins=64 pins_ok=64 ro_reads=6 table_entries=22
  ```
  9 200 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 90 or more: `speed0` 265, `rf_ignored` 152, `t64_inv` 400, `k_mod4` 578; every control equals its deciding
  class on the 24 `CLASS` lines); the site control fails on all 3 698 matched boundary cases (27 `site` lines:
  function, boundary, return address; 1 296 + 1 172 + 703 + 527). The one `.data` read, the skills calc function count,
  has no writer in `.text` (0 stores, 0 immediates, 7 reads). `static.txt` also finds do 152's 147 instructions equal
  to do 95's, start 59's 63 equal to start 53's but one, and computes the two shift bounds (`wrap` lines). Four
  development runs came first and are kept in `dev/` (`dev/notes.txt`): the stale target link's `+0x58` clearing and
  `0x0061A270`'s three stack words modelled wrong, one control that failed on no case, then the deciding classes and
  the writer's tuning; and a first repro whose `ass` static step ended with no output under one shared 4 GB scope.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, start 54's node and path words, start 55's count on its local seed, start 64's result, do 102's
  and do 105's `n ≤ 0` returns, do 103's last return, do 100's no-target 1) and of their maps up to their boundary
  calls with the call site, the nested return addresses, the arguments (register arguments where the callee reads them
  first), the pointed-to blocks and packets, the node, path and argument-slot words and both seeds asserted (`[C]`
  under [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0017 names each claim's boundary). One
  draw on a unit's seed before a boundary: do 112's inline step of the caster's seed; start 55 draws on a local seed. Not
  covered: what any boundary callee does and everything after it (the further creations, the damage rolls, the leech
  and corpse heals after their calls, the inferno repeats); when the game runs these functions or with which seed.
  (fn:sub_005CE2B0_SkillDo112MonCurse@0x005CE2B0, fn:sub_005CD910_SkillSt55LocalSeed@0x005CD910,
  fn:sub_005CC690_SkillDo152DiabLight@0x005CC690)

## run:2026-10-21-cat-emu-8c

- **Question:** (plan 0046 Phase 1, batch 8c) Do the monster start functions 61–63 and do functions 128–137, 139, 140
  and 147–149 map their inputs (the Skills, Missiles, MonStats and MonStats2 records, the caster, its path, used node,
  stat list, monster data, owner links and `+0xC4`, the target, its path, stat list, state words, alignment list and
  owner link, the rooms, the game's frame and difficulty bytes, and the seeds) to the result they return, or to the
  arguments, pointed-to blocks and packets, node, frame and argument-slot words and seed states at the call they end
  in, exactly as [skills/0018](0018-monster-8c.md) §§ 3–5 say, and which seed does each draw before its boundary step?
- **Setup:** as run:2026-10-21-cat-emu-8b: Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p46m15`, heap 3 GB, one instance at a time, each under a 4 GB scope),
  `re/ghidra_scripts/EmuBoundary.java` unchanged. No wine, nothing runs natively, no slot. Models, case writers and
  checks: the `8c` families of `tools/skills_catalogue_emu.py` (`8911d02a…`; the kept outputs were emulated from case
  files this revision writes, and it gives the kept `check.txt` and `static.txt`), with 8a's and 8b's conventions (the
  call site of every boundary asserted with a site control; the caster's and the target's seeds written and compared
  in every case; a boundary's pointer argument compared by content: the `MissileCreate` block, the hit packet, the
  timed-state blocks; the node, frame and argument-slot words dumped and compared, each dumped byte written by the case;
  register arguments compared only where the callee reads them before writing them; a boundary inside a helper compares
  the helper's return address at its absolute stack slot). All inputs synthetic (stock parameter values among them);
  every case-writer draw from `random.Random("cat8c-<family>")`. Files in `workspace/logs/skills-cat-8c/`,
  `manifest.sha256` `9dc63588…` (92 files: cases, memory specs, expected inputs, outputs, the `.err` logs, `cases.txt`,
  `check.txt` `500b673c…`, `static.txt` `873640da…`, `rows.txt` `21a02907…` with its `rows.sh`, `repro.txt` `2a44bd63…`
  with its `repro.sh`, the run script `run_8c.sh`, and the three development runs under `dev/` with `dev/notes.txt`);
  `sha256sum -c manifest.sha256` from that directory passes. `repro.txt` records that the same tool revision (which also
  carries the `near8` docstring fix of the `lane/p46m13` review, fix 2) regenerates every case, memory and expectation
  file of 9a, 9b, 9c, 9d, `sor`, `ama`, `nec`, `pal`, `bar`, `dru`, `ass`, `item`, 8a and 8b byte for byte and
  reproduces their kept `check.txt` and `static.txt` byte for byte from their kept outputs (14 `REPRO` lines, each
  `differ=0 check=same static=same`).
- **Procedure:**
  ```
  D=workspace/logs/skills-cat-8c
  python3 -I tools/skills_catalogue_emu.py cases --batch 8c > $D/cases.txt
  $D/run_8c.sh $D miss_8c hit_8c curse_8c move_8c   # one EmuBoundary instance at a time, 4 GB scope
  python3 -I tools/skills_catalogue_emu.py check  --batch 8c > $D/check.txt
  python3 -I tools/skills_catalogue_emu.py static --batch 8c > $D/static.txt
  $D/rows.sh > $D/rows.txt; $D/repro.sh <scratch dir> > $D/repro.txt
  python3 -I tools/skills_catalogue_emu.py manifest --batch 8c --write
  ```
  The memory spec points `g_pDataTables` at a scratch DataTables written one field per field read (Skills with count
  3; Missiles with count 48; ItemStatCost, MonStats with count 4, or 600 for `curse_8c` so that `MonClassCheck` admits
  the bases 453, 546 and 551; MonStats2, the calc pool, the States and PetType counts, the state sets at `+0xD4` and
  `+0x150`, the overlay count), sets `MONSTATS_GetClassChainPos`'s table and count, `MissileSpeedAtLevel`'s missile
  table and count and the cookie, names the boundaries (`observe`) and guards the allocator and the fatal path.
- **Observed** (`check.txt`, `static.txt`):
  ```
  CAT8C miss_8c  cases=3200 match=3200 bad=0 neg=605 traced=12 undeclared=0 stopped=0
  CAT8C hit_8c   cases=1200 match=1200 bad=0 neg=260 traced=9 undeclared=0 stopped=0
  CAT8C curse_8c cases=2000 match=2000 bad=0 neg=204 traced=29 undeclared=0 stopped=0
  CAT8C move_8c  cases=2400 match=2400 bad=0 neg=1109 traced=6 undeclared=0 stopped=0
  CAT8C static d148_differ=1 entry_words=18 helper_sites=29 pins=68 pins_ok=68 rng_calls=1 rng_mult=3 ro_reads=5 table_entries=18
  ```
  8 800 cases. Every negative control fails (per-control counts on the `negative control` lines; each family has one
  failing 75 or more: `lob_inv` 271, `corpse_any` 100, `base_any` 75, `mode_x` 359; every control equals its deciding
  class on the 18 `CLASS` lines); the site control fails on all 2 376 matched boundary cases (23 `site` lines: function,
  boundary, return address; 892 + 370 + 227 + 887). `static.txt` also finds do 148's and do 149's 101 instructions equal
  but one, scans the batch's bodies and helpers for the RNG functions and the multiplier (one `RNG_Range` call in do
  131, the multiplier three times in do 140, nothing else), prints `0x0063EFA0`'s first switch table and do 130's
  offsets, and computes do 128's frame-sum wrap (`wrap` line). Three development runs came first and are kept in `dev/`
  (`dev/notes.txt`): one case-writer error (two owners written as one unit) and two classes too wide, then the writer's
  tuning for the thin controls.
- **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the functions' maps on returning cases (`[C]`:
  every refusal path, start 62's node words from `SkillSummonClass`, do 140's no-room return with the seed stepped
  `1 + 2n` times, do 147's no-owner 1) and of their maps up to their boundary calls with the call site, the nested
  return addresses, the arguments (register arguments where the callee reads them first), the pointed-to blocks and
  packets, the node, frame and argument-slot words and both seeds asserted (`[C]` under
  [ADR-0021](../../adrs/0021-observed-boundaries-in-emulation.md); skills/0018 names each claim's boundary). Draws on a
  unit's seed before a boundary: do 131's `RNG_Range(caster, 100)` and do 140's inline steps of the caster's seed. Not
  covered: what any boundary callee does and everything after it, `0x0063EFA0`'s arms other than the default one (Baal's
  among them); when the game runs these functions or with which seed. (fn:sub_005D1F70_SkillDo131OverseerWhip@0x005D1F70,
  fn:sub_005D2C20_SkillDo140BaalTentacle@0x005D2C20, fn:sub_005D1AB0_SkillDo129ImpTeleport@0x005D1AB0)

## run:2026-11-16-sweep2-s2ae

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2ae (`lane/n66sa`), part 1: skills and
missile leaf functions under Ghidra's p-code emulator on the pinned image (ADR-0015, ADR-0021), compared with a `tools/`
model, plus objdump reads and a call-graph route listing. No game, no wine. The claims are in
[skills/0002 § 17](0002-missiles.md#17-plan-0066-batch-s2ae-part-1-leaf-functions-emulated-earlier-runs-re-read-the-routes-2026-11-16-lanen66sa).

- **Question:** do `PathVelocityStep`, `PathDirection`, `MissileElemRoll`, `SKILLS_StartManaOk`, `SKILLS_RestrictOk`,
  `SKILLS_DelayOk` (to its first call), `SkillKickDamage` and `SummonClassRoll` (with `SkeletonParam1Roll`, `0x005C43D0`
  and `SummonSetDataBytes`), run on declared inputs, give what skills/dispatch and skills/missiles (at `b5999f5e`) state
  as inferred, and which batch routes cross a pool allocator or an import?
- **Setup:** `tools/skills_s2ae_emu.py` (sha256 `d35f9f74…`, stdlib and objdump; imports `tools/combat_s5e_emu.py` and
  `tools/sweep_s4b.py` unchanged), `tools/skills_s2ae_routes.py` (`ee45d8f1…`; imports `tools/sweep2_s7e_routes.py`
  unchanged), `re/ghidra_scripts/EmuBoundary.java` unchanged, Ghidra 12.1.2, project `workspace/ghidra-n66sa`
  (`-Xmx3G`, `MemoryMax=4G`; `import-symbols` run first). One kept launch of `tools/ghidra.sh emuboundary`, 8 families
  (`pvs` 1 500, `pdir` 3 000, `elem` 2 500, `smana` 1 200, `rst` 2 000, `dly` 1 200, `kick` 1 200, `skel` 1 500), seeds
  `random.Random("n66sa-s2ae-<family>")`.
- **Memory spec** (`s2ae.mem`): a scratch DataTables at 0x21000000 (`dt.bin`: states 0xC0 at `+0xC4`, the restricted-state
  mask words at `+0x110` → 0x21400000 (`rmask.bin`, seeded), MonStats and ItemStatCost as S5e part 1 (`monstats.bin`,
  zero `isc.bin`), 32 seeded Skills records of 0x23C bytes at `+0xB98`/`+0xBA0` (`skills.bin`)); each case writes its
  unit (S5e part 1's builder), path block, entry and record, or summon with MonsterData. Guards: the fatal path
  0x00408090, 0x00408A60, 0x00681E09 and the allocator 0x0040B4B0, 0x0040B430, 0x0040B480 (never reached). **Observed
  boundaries (ADR-0021):** `SKILLS_GetSkillLevel` 0x006442A0 (`dly`, return address 0x00647936) and 0x005B0D70 (`skel`,
  0x005C42CE), both checked per case. Every other callee runs whole: `STATS_GetUnitStat`, `UNIT_HasState`,
  `sub_00483360_MulDiv`, `RNG_RangeB`, 0x0063A510, 0x0063A130, 0x00625BB0, `SkeletonParam1Roll`, 0x005C43D0,
  `SummonSetDataBytes`; no import is reached.
- **Read set (ADR-0015 (2)):** every traced read falls in `g_BitMask32` 0x006CE268 (`.rdata`; 0x00624F9F, 0x00625BA1),
  `g_PathDirTable` 0x006EB7E0 (`.rdata`, 128 rows of 12 bytes; 0x0064FCE0, 0x0064FCE7, 0x0064FCF8, 0x0064FD0F) or the
  9-byte rows at 0x00741940 (`.data`, nine reads 0x005C418F–0x005C42D5); `static.txt` `SDB-REF` lists every `.text`
  operand inside those rows: 9, all `mov` loads, no store. No traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66sa/s2ae/run`):
  ```
  python3 -I tools/skills_s2ae_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66sa GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s2ae.cases $D/s2ae.mem > $D/s2ae.out 2> $D/s2ae.err
  python3 -I tools/skills_s2ae_emu.py check --dir $D > $D/check.txt
  python3 -I tools/skills_s2ae_emu.py static > $D/static.txt
  python3 -I tools/skills_s2ae_routes.py --depth 4 > $D/routes.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`1b264a66…`, 73 lines, last line `S2AE total cases=14100 mismatches=0 stops=0 controls=62
  unseparated=5 controls_passed=0 unaccounted=0`), `static.txt` (`2a020d10…`, 859 lines), `routes.txt` (`c78b8b93…`,
  80 roots), `s2ae.out` (`b0bff78e…`), `s2ae.cases` (`0643f011…`, regenerated byte for byte by `cases`), listed in
  `manifest.sha256` (`83a5755f…`, 12 lines), which passes from `$D`. `check` with the committed revision reproduces
  `check.txt` byte for byte. Development: two launches (`--limit 40`, `--limit 60`; `dev1/`, `dev2/`, 0 mismatches on
  their own case files), the first route listing and decompiles in `dev/`, all under
  `workspace/logs/n66sa/s2ae/manifest-dev.sha256` (`46bcc2c2…`, 23 lines, passes from `workspace/logs/n66sa/s2ae/`),
  not cited.
- **Controls:** 62, 57 separating, each `passed` 0. The 5 that separate nothing are inherent: `pvs v_lt0~` (a sum of 0
  is 0 either way), `elem inverted~` (an equal pair swapped is the same pair), `kick x_lt1~` (1 floors to 1),
  `skel idx_gt10~` (the index is 1 on every path run: state 97 is off), `rst st_neg~` (no case lists state 0 and has
  it). Spec-reading controls: `pvs spec_two_ifs` 111, `elem spec_no_swap` 1 172, `smana spec_unsigned` 12.
- **Not covered:** the callees after each observed boundary; `SKILLS_EvalCalc` in `SKILLS_DelayOk`; state 97's path in
  `SkeletonParam1Roll`; what any offset means (each keeps its own tag); faults; when and on which live seed the game
  runs these functions. **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015, ADR-0021) of the eight
  maps above; the claims and the rows they settle are in skills/0002 § 17.

## run:2026-11-16-sweep2-s2ae2

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2ae (`lane/n66sa`), part 2: the two
mana checks and the missile collide filters under Ghidra's p-code emulator on the pinned image (ADR-0015), compared
with a `tools/` model. No game, no wine. The claims are in
[skills/0002 § 18](0002-missiles.md#18-plan-0066-batch-s2ae-part-2-the-mana-checks-and-the-collide-filters-emulated-2026-11-16-lanen66sa).

- **Question:** do `SKILLS_ManaOk`, `SKILLS_SrvManaCheck` (each with `SkillLevelBonus` and `ExpMaxLevel`) and
  `CollideUnitFilter` with its four collide-type callers and `CollideMissile`, run whole on declared inputs, give what
  skills/dispatch C4 and D3 and skills/missiles D6 (at `b5999f5e`) state as inferred?
- **Setup:** `tools/skills_s2ae2_emu.py` (sha256 `ac1bae1a…`, stdlib and objdump; imports `tools/skills_s2ae_emu.py`
  (part 1, unchanged: its build, predict and check machinery, pointed at this part's families in its module state only)
  and `tools/combat_s5e_emu.py` unchanged), `re/ghidra_scripts/EmuBoundary.java` unchanged, Ghidra 12.1.2, project
  `workspace/ghidra-n66sa` (`-Xmx3G`, `MemoryMax=4G`). One kept launch of `tools/ghidra.sh emuboundary`, 7 families
  (`mana` 2 500, `srvm` 1 500, `filt` 3 000, `cpa` 1 200, `cmon` 800, `cun` 1 200, `cmis` 800), seeds
  `random.Random("n66sa-s2ae2-<family>")`, tables `random.Random("n66sa-s2ae2-tables")`.
- **Memory spec** (`s2ae.mem`): a scratch DataTables at 0x21000000 (`dt.bin`: states 0xC0 at `+0xC4`; 16 seeded Missiles
  rows of 0x1A4 at `+0xB64`/`+0xB6C` (`missiles.bin`); 12 seeded SkillDesc rows of 0x120 at `+0xB8C`/`+0xB94`
  (`skilldesc.bin`); 24 Skills records of 0x23C at `+0xB98`/`+0xBA0` (`skills.bin`, seeded, with the cost words,
  class byte, desc index, `+0x1DC` and `srvdofunc` drawn from short lists); zero ItemStatCost at `+0xBCC`/`+0xBD4`); the
  pointer 0x0096C8A8 that `ExpMaxLevel` reads (runtime data) declared as 0x20004800, whose first word each case writes
  (0, 1, 20, 50 or 99). Each case writes its units (S5e part 1's builder; the stat array rewritten with layered keys,
  the state stat-list chains at `+0x3C`/`+0x40`, `MonsterOwner`'s chain ending in 0, a player's relation list at data
  `+0x38`), entry, record, missile unit and context. Guards: the fatal path 0x00408090, 0x00408A60, 0x00681E09, the
  allocator 0x0040B4B0, 0x0040B430, 0x0040B480 and the game lookup 0x00552F60 (never reached). No observed boundary:
  every callee runs whole (`STATS_GetUnitStat`, `UNIT_HasState`, `SkillLevelBonus`, `ShrineSkillBonus`, `SkillDescRec`,
  `ExpMaxLevel`, `SKILLS_GetSkillLevel`, `UNIT_GetUsedSkill`, 0x006439A0, 0x00643AD0, 0x00644140, 0x0063A400,
  `MISSDATA_IsLastHit`, `UnitsHostile`, `MonsterOwner`, `PlayerPairFlags`, 0x006221A0, `AlignSame02`, `UnitAlignGet`,
  `UNIT_FindStatListByState`, `StatListFindByState`, `StatListGetStat`); no import is reached.
- **Read set (ADR-0015 (2)):** every traced read falls in `g_BitMask32` 0x006CE268 (`.rdata`; 0x005A88BE 195,
  0x00624F9F 5 138, 0x00625BA1 2 881, 0x0064A4AC 1 196). No traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66sa/s2ae/run2`):
  ```
  python3 -I tools/skills_s2ae2_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66sa GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s2ae.cases $D/s2ae.mem > $D/s2ae.out 2> $D/s2ae.err
  python3 -I tools/skills_s2ae2_emu.py check --dir $D > $D/check.txt
  python3 -I tools/skills_s2ae2_emu.py reach > $D/reach.txt
  python3 -I tools/skills_s2ae2_emu.py static > $D/static.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`4aa76a41…`, 141 lines, last line `S2AE total cases=11000 mismatches=0 stops=0
  controls=131 unseparated=10 controls_passed=0 unaccounted=0`), `reach.txt` (`0001c1a2…`, 114 lines: each family's
  predicted outcomes and every named test's true/false count), `static.txt` (`42c76d27…`, 1 029 lines: the objdump of every function run, the nine `(filter, mask)` pairs of `g_MissileCollideTypes` read from the image (`GCT`, `.data`), and the four `.text` operands inside them (`GCT-REF`: 0x0059FD73, 0x005AE303 reads; 0x005AE30B, 0x005AE355 `lea`s, whose uses were not followed)), `s2ae.out`
  (`9e165c70…`), `s2ae.cases` (`8faafb24…`, regenerated byte for byte by `cases`), listed in `manifest.sha256`
  (`1edb5bbd…`, 12 lines), which passes from `$D`. `check`, `reach` and `static` with the committed revision reproduce
  their files byte for byte; part 1's `check` still reproduces its `run/check.txt`. Development: three launches
  (`dev3/` `--limit 60`; `dev4/`, `dev5/` full, before the cost targeting and before `PlayerPairFlags` ran whole), all
  under `workspace/logs/n66sa/s2ae/manifest-dev-p2.sha256` (31 lines, passes from `workspace/logs/n66sa/s2ae/`), not
  cited.
- **Outcomes:** `mana` 902 × 0, 1 598 × 1; `srvm` 377, 1 123; `filt` 1 631, 1 369; `cpa` 1 079, 121; `cmon` 715, 85;
  `cun` 999, 201; `cmis` 691, 109. The mana families set stats 6 and 8 at the model's cost or one off it in about two
  cases of three, so a wrong level term changes the returned bit.
- **Controls:** 131, 121 separating, each `passed` 0. The 10 that separate nothing: nine strictness switches at an
  equality that gives the same value both ways (`lvl_le0~`, `lvl_lt0~`, `lvl_lt_max~`, `b_cap3~` in `mana` and `srvm`,
  `b_cap3n~` in `mana`), and `cun spec_any_flag` (separated by `filt` 5 and `cpa` 1 on the same code). Spec-reading
  controls: `mana spec_no_minus1` 428, `srvm spec_st114` 56, `spec_any_flag` 5 and 1. `srvm b_player` is true in every
  case that reaches it (the function returns 1 for a non-player first).
- **Not covered:** `MonsterOwner`'s game lookup (0x00552F60) and a type-3 owner with `+0xC8` bit 10 in `UnitsHostile`;
  what any offset means (each keeps its own tag); the collide-type masks of `g_MissileCollideTypes`; faults; who calls
  these functions and when. **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the maps above; the
  claims and the rows they settle are in skills/0002 § 18.

## run:2026-11-16-sweep2-s2ae3

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2ae (`lane/n66sa`), part 3: hit
function 27, `CallDoFunc` and the unique-mod-29 missile hook under Ghidra's p-code emulator on the pinned image
(ADR-0015), compared with a `tools/` model, and a static read of the two `g_MissileCollideTypes` `lea`s. No game, no
wine. The claims are in
[skills/0002 § 19](0002-missiles.md#19-plan-0066-batch-s2ae-part-3-the-mask-uses-read-calldofunc-hit-27-and-unique-mod-29-emulated-2026-11-16-lanen66sa).

- **Question:** do hit 27 (0x005ABA00), `CallDoFunc` and `MissileOwnerUModEvent` (through `UModEventRun` and mod 29's
  slot-5 function, to its first creation), run on declared inputs, give what skills/missiles B1, G1 and G2 (at
  `b5999f5e`) state as inferred; and is any store made through the two `lea`s into `g_MissileCollideTypes`?
- **Setup:** `tools/skills_s2ae3_emu.py` (sha256 `d173233c…`, stdlib and objdump; imports `tools/skills_s2ae_emu.py`
  (part 1, unchanged: its build, predict and check machinery, pointed at this part's families in its module state only)
  and `tools/combat_s5e_emu.py` unchanged), `re/ghidra_scripts/EmuBoundary.java` unchanged, Ghidra 12.1.2, project
  `workspace/ghidra-n66sa` (`-Xmx3G`, `MemoryMax=4G`). One kept launch of `tools/ghidra.sh emuboundary`, 3 families
  (`h27` 300, `cdo` 1 500, `uev` 3 000), seeds `random.Random("n66sa-s2ae3-<family>")`, Missiles rows
  `random.Random("n66sa-s2ae3-tables")`.
- **Memory spec** (`s2ae.mem`): a scratch DataTables at 0x21000000 (`dt.bin`: 80 seeded Missiles rows of 0x1A4 at
  `+0xB64`/`+0xB6C`, `missiles.bin`, byte `+5` bit 4 cleared in about four rows of five). Each case writes its units
  (the monster, the owner, the target and decoys as nodes of 0x100 bytes with data at `+0x200` and a path at `+0x300`),
  the missile with its data and path, and the game's bucket heads that its lookups read (the rest unwritten). Guards:
  the fatal path 0x00408090, 0x00408A60, 0x00681E09 and the allocator 0x0040B4B0, 0x0040B430, 0x0040B480. Observed
  boundaries: the 152 distinct non-null `g_SkillDoFuncs` entries, `sub_0056ECB0_SkillMissileCreate`, 0x005A2E00
  (mod 19) and 0x005A30B0 (mod 27). Every other callee runs whole.
- **Read set (ADR-0015 (2)):** every traced read falls in a declared constant range: `g_UModEventFns` (0x005A4317,
  7 024), `g_SkillDoFuncs` (0x0056D81D, 943), the bucket offsets 0x006E10E0 (`.rdata`; 0x00552F9C, 2 496) and
  `g_BitMask32` (0x005A367F, 1 204). The two `.data` tables are read from the image: `static.txt` lists their entries and
  every `.text` operand naming them (`DOF-REF` 5, `UMF-REF` 2, all reads). No traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66sa/s2ae/run3`):
  ```
  python3 -I tools/skills_s2ae3_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66sa GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s2ae.cases $D/s2ae.mem > $D/s2ae.out 2> $D/s2ae.err
  python3 -I tools/skills_s2ae3_emu.py check --dir $D > $D/check.txt
  python3 -I tools/skills_s2ae3_emu.py reach > $D/reach.txt
  python3 -I tools/skills_s2ae3_emu.py static > $D/static.txt
  python3 -I tools/skills_s2ae3_emu.py masks > $D/masks.txt
  python3 -I tools/skills_s2ae3_emu.py sites > $D/sites.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`bad4fdbf…`, 41 lines, last line `S2AE total cases=4800 mismatches=0 stops=0 controls=35
  unseparated=0 controls_passed=0 unaccounted=0`), `reach.txt` (`21dfdffa…`, 29 lines), `static.txt` (`0ecfbce8…`,
  1 051 lines), `masks.txt` (`d7cc31cc…`, 25 lines: the def-use of the two `lea`s, `stores-through=0`), `sites.txt`
  (`4d3253be…`, 28 lines: mod 29's and do 30's direct call sites with their allocator and import reach), `s2ae.out`
  (`0f99daa0…`), `s2ae.cases` (`5d5473fc…`, regenerated byte for byte by `cases`), listed in `manifest.sha256`
  (`5612f356…`, 11 lines), which passes from `$D`. `check`, `reach`, `static`, `masks` and `sites` with the committed
  revision reproduce their files byte for byte; parts 1 and 2's `check` still reproduce `run/check.txt` and
  `run2/check.txt`. Development: four launches (`dev6/` `--limit 40`; `dev7/`, `dev8/` `--limit 300`, before the
  Missiles bit and unique-mod draws were tuned; `dev9/` full, before `CallDoFunc`'s `ECX` and `EDX` were compared),
  all under `workspace/logs/n66sa/s2ae/manifest-dev-p3.sha256` (32 lines, passes from `workspace/logs/n66sa/s2ae/`),
  not cited.
- **Outcomes:** `h27` 300 × 1; `cdo` 474 calls (132 distinct entries; entry 30, 0x005C37C0, 172 times), 469 returns
  at a null entry, 557 past the bound; `uev` 939 first creations, 624 and 617 calls of mods 19 and 27, 820 returns
  without a call.
- **Controls:** 35, all separating, each `passed` 0, among them the spec-reading controls `cdo spec_signed` 268, `uev
  spec_no_zero` 230, `uev spec_same_side` 709 and `h27 spec_ret0` 300.
- **Not covered:** a monster owner without data, unique-mod bytes above 42, owner or target types above 5; what do 30
  does past `CallDoFunc`; mod 29's second creation (past the first creation's allocation, `sites.txt`); what any
  offset means. **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the maps above, and a static
  def-use of the mask table's `lea`s with no store through them; the claims and the rows they settle are in skills/0002
  § 19.

## run:2026-11-16-sweep2-s2ae4

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2ae (`lane/n66sa`), part 4: the
zig-zag re-seed callback and `MissileCreate` up to its `SUnitCreate` call under Ghidra's p-code emulator on the pinned
image (ADR-0015), compared with a `tools/` model, and the per-call-site allocator reach of the batch's remaining roots.
No game, no wine. The claims are in
[skills/0002 § 20](0002-missiles.md#20-plan-0066-batch-s2ae-part-4-the-zig-zag-callback-and-missilecreate-to-its-allocation-emulated-2026-11-16-lanen66sa).

- **Question:** do `sub_005D4680_MissCbReseedZigzag` (whole) and `sub_0059FA30_MissileCreate` (to its first
  allocation), run on declared inputs, give what skills/missiles B1 and H (at `b5999f5e`) state as inferred?
- **Setup:** `tools/skills_s2ae4_emu.py` (sha256 `f481fed7…`, stdlib and objdump; imports `tools/skills_s2ae_emu.py`
  (part 1: its build, predict and check machinery and its `PathDirection` model) and `tools/skills_s2ae3_emu.py`
  (part 3: its memory view, objdump, reference scan and site walk), both unchanged and pointed at this part's families
  in their module state only), `re/ghidra_scripts/EmuBoundary.java` unchanged, Ghidra 12.1.2, project
  `workspace/ghidra-n66sa` (`-Xmx3G`, `MemoryMax=4G`). One kept launch of `tools/ghidra.sh emuboundary`, 2 families
  (`zz` 2 500, `mcr` 4 000), seeds `random.Random("n66sa-s2ae4-<family>")`, Missiles rows
  `random.Random("n66sa-s2ae4-tables")`.
- **Memory spec** (`s2ae.mem`): a scratch DataTables at 0x21000000 (`dt.bin`: 192 states at `+0xC4`; 80 seeded
  Missiles rows of 0x1A4 at `+0xB64`/`+0xB6C`, `missiles.bin`, `CanSlow` set in about half; 512 zero ItemStatCost
  records at `+0xBCC`/`+0xBD4`, `isc.bin`). Each `zz` case writes the unit (0x100 bytes), its missile data and its path
  through the point list (0x1D0 bytes); each `mcr` case the parameter block, the owner, source and target (each with a
  path; the owner with a stat list, its state bits and at most one state-list node with a base-stat array), the room and
  up to four neighbours. Guards: the fatal path 0x00408090, 0x00408A60, 0x00681E09 and the allocator 0x0040B4B0,
  0x0040B430, 0x0040B480. Observed boundary: `sub_00555230_SUnitCreate`. Every other callee runs whole.
- **Domain:** `zz` unit-to-target differences of at most 250 sub-tiles (see skills/0002 § 20, *Not covered*).
- **Read set (ADR-0015 (2)):** every traced read falls in a declared constant range: the 8-way steps 0x006E32AC and
  0x006E328C (0x005D47E4, 0x005D47EB, 166 731 each), the 64-to-8 direction bytes 0x00745600 (0x0063E7A7, 55 577), the
  zig-zag words 0x00741B0C (0x005D480C, 55 577) and 0x00741B10 (0x005D47AB 6 249, 0x005D4845 13 254),
  `g_PathDirTable` (0x0064FCE0, 0x0064FCE7 2 083 each; 0x0064FCF8 699; 0x0064FD0F 1 384), `PathSetType`'s tables
  0x006EB690 and 0x006EB648 (0x00648D29, 0x00648D73, 2 452 each) and `g_BitMask32` (0x0059FB3E 1 960, 0x00625BA1 940,
  0x00624EFC 289). The three `.data` ranges are read from the image: `static.txt` lists their values and every `.text`
  operand naming them (`DIR64-REF` 2, `ZZW-REF` 3, all reads; the scan also splits the `ds:` form, and part 3's
  `DOF-REF` 5 and `UMF-REF` 2 are unchanged under it). No traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66sa/s2ae/run4`):
  ```
  python3 -I tools/skills_s2ae4_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66sa GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s2ae.cases $D/s2ae.mem > $D/s2ae.out 2> $D/s2ae.err
  python3 -I tools/skills_s2ae4_emu.py check --dir $D > $D/check.txt
  python3 -I tools/skills_s2ae4_emu.py reach > $D/reach.txt
  python3 -I tools/skills_s2ae4_emu.py static > $D/static.txt
  python3 -I tools/skills_s2ae4_emu.py sites > $D/sites.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`5d0dead9…`, 77 lines, last line `S2AE total cases=6500 mismatches=0 stops=369
  controls=72 unseparated=3 controls_passed=0 unaccounted=0`), `reach.txt` (`83bda362…`, 51 lines), `static.txt`
  (`02daa52f…`, 1 110 lines), `sites.txt` (`58ac68de…`, 124 lines: the direct call sites of eight roots with their
  allocator and import reach), `s2ae.out` (`c8ce12fe…`), `s2ae.cases` (`4cec9e5b…`, regenerated byte for byte by
  `cases`), listed in `manifest.sha256` (`ce7ed80a…`, 11 lines), which passes from `$D`. The committed revision's
  `check`, `reach`, `static` and `sites` reproduce their files byte for byte; it adds three spec controls
  (`spec_udiv8`, `spec_floor100_slow`, `spec_floor100_75`) and the `ds:` split of `static`'s reference scan to the
  revision that ran the emulation, whose cases file is the same. Parts 1 to 3's `check` still reproduce `run/check.txt`, `run2/check.txt` and `run3/check.txt`.
  Development: one launch (`dev10/`, `--limit 200`, 0 mismatches) under
  `workspace/logs/n66sa/s2ae/manifest-dev-p4.sha256` (7 lines, passes from `workspace/logs/n66sa/s2ae/`), not cited.
- **Outcomes:** `zz` 2 131 returns, 369 fatal-path stops (path `+0x40` = 0xB or 8, predicted); `mcr` 1 577 calls of
  `SUnitCreate` from 0x0059FC75, 2 423 refusals.
- **Controls:** 72, 69 separating, each `passed` 0. Not separating: `zz b_lt_4d~` (a byte of 77 gives 77 either way),
  `mcr r_x1~` and `nb_x1~` (no point drawn on a room's right edge). The spec-reading controls: `zz spec_no_flip` 938,
  `mcr spec_lvl_m1` 853, `spec_floor8` 112, `spec_udiv8` 112, `spec_floor100_75` 96, `spec_floor100_slow` 25,
  `spec_abs` 2.
- **Not covered:** room bounds that wrap and the right-edge strictness; `zz` differences past 250 sub-tiles;
  `ItemStatCost` flags on stat 161; everything past `SUnitCreate` (the pool allocation, `sites.txt`); what any offset
  means. **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the maps above; the claims and the rows
  they settle are in skills/0002 § 20.

## run:2026-11-16-sweep2-s2ae5

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2ae (`lane/n66sa`), part 5:
`SKILLS_TargetCheck` whole and the re-seed callbacks `0x005D40F0` and `0x005CD110` to their `PathPlan` call under
Ghidra's p-code emulator on the pinned image (ADR-0015, ADR-0021), compared with a `tools/` model, and the per-call-site
allocator reach of the batch's open roots. No game, no wine. The claims are in
[skills/0002 § 21](0002-missiles.md#21-plan-0066-batch-s2ae-part-5-skills_targetcheck-and-two-re-seed-callbacks-emulated-2026-11-16-lanen66sa).

- **Question:** do `SKILLS_TargetCheck`, `sub_005D40F0_MissCbReseedFromArg` and `sub_005CD110_MissCbReseedRoll`, run on
  declared inputs, give what skills/dispatch D2 and skills/missiles H (at `b5999f5e`) state as inferred? In
  particular, which targets does `TargetCheck` clear at 0x0056CCF0–0x0056CD35 (the part 4 resume note's question)?
- **Setup:** `tools/skills_s2ae5_emu.py` (sha256 `0490ce73…`, stdlib and objdump; imports parts 1, 3 and 4's tools,
  unchanged, pointed at this part's families in their module state only: part 1's build, predict and check machinery,
  part 3's memory view, objdump and site walk, part 4's zig-zag case writer and path-type pieces),
  `re/ghidra_scripts/EmuBoundary.java` unchanged, Ghidra 12.1.2, project `workspace/ghidra-n66sa` (`-Xmx3G`,
  `MemoryMax=4G`). One kept launch of `tools/ghidra.sh emuboundary`, 3 families (`tc` 4 000, `rfa` 1 500, `rro`
  2 000), seeds `random.Random("n66sa-s2ae5-<family>")`, Skills rows `random.Random("n66sa-s2ae5-tables")`.
- **Memory spec** (`s2ae.mem`): a scratch DataTables at 0x21000000 (`dt.bin`: 192 states at `+0xC4`; 48 seeded Skills
  rows of 0x23C at `+0xB98`/`+0xBA0`, `skills.bin`, `+6` bit 0x10 in about half, `+7` bits 1, 2, 4 at 0.5, 0.4, 0.4;
  512 zero ItemStatCost records at `+0xBCC`/`+0xBD4`, `isc.bin`). Each `tc` case writes five units (caster, target,
  two owners or decoys, a player; 0x100 bytes each with monster/player data, an owner record, a stat list with a
  state-105 node and two stat arrays, players' pair lists), the caster's path, the game's bucket heads for every
  (type, guid) the code can look up, the party list and some client records; each `rfa`/`rro` case is part 4's `zz`
  case writer's unit, data and path. Guards: the fatal path 0x00408090, 0x00408A60, 0x00681E09 and the allocator
  0x0040B4B0, 0x0040B430, 0x0040B480. Observed boundary: `PathPlan` 0x00649970. Every other callee runs whole.
- **Domain:** `tc` lookups of types 0 to 5 only (a type above 5 makes `GameFindUnit` read address 0); every type-1
  unit has monster data and an owner record (`MonsterOwnerRef` reads both without a null test); no owner cycle
  (`UnitsHostile`'s owner loop stops only at a unit that is its own owner).
- **Read set (ADR-0015 (2)):** every traced read falls in a declared constant range: `GameFindUnit`'s bucket offsets
  0x006E10E0 (0x00552F9C, 3 873), `g_BitMask32` (0x00554301 347, 0x00554D62 202, 0x0056CCA5 2 133, 0x0056CD08 171,
  0x0056CD27 787, 0x00624F9F 229) and `PathSetType`'s tables 0x006EB690, 0x006EB648 (0x00648D29, 0x00648D73, 3 030
  each), all `.rdata`. No traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66sa/s2ae/run5`):
  ```
  python3 -I tools/skills_s2ae5_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66sa GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s2ae.cases $D/s2ae.mem > $D/s2ae.out 2> $D/s2ae.err
  python3 -I tools/skills_s2ae5_emu.py check --dir $D > $D/check.txt
  python3 -I tools/skills_s2ae5_emu.py split --dir $D > $D/split.txt
  python3 -I tools/skills_s2ae5_emu.py reach > $D/reach.txt
  python3 -I tools/skills_s2ae5_emu.py static > $D/static.txt
  python3 -I tools/skills_s2ae5_emu.py sites > $D/sites.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`78107755…`, 84 lines, last line `S2AE total cases=7500 mismatches=0 stops=655
  controls=78 unseparated=4 controls_passed=0 unaccounted=0`), `split.txt` (`f2f57100…`, 10 lines: the `tc` cases
  that reach the `+0xC4` bit test by cell, with the emulator's outcome read from its own dump, each cell asserted
  equal to the model), `reach.txt` (`cbd40329…`, 70 lines), `static.txt` (`05fc2d2e…`, 1 167 lines), `sites.txt`
  (`9255ebd1…`, 527 lines: the direct call sites of 39 roots, every open S2ae row's function, with their allocator
  and import reach), `s2ae.out` (`4fe3d183…`), `s2ae.cases` (`7ed835b4…`, regenerated byte for byte by `cases`),
  listed in `manifest.sha256` (`0f6933ff…`, 12 lines), which passes from `$D`. The committed revision's `check`,
  `reach`, `static` and `sites` reproduce their files byte for byte; it adds `split` (and two format fixes to it) to
  the revision that ran the emulation, whose cases file is the same. Parts 1 to 4's `check` still reproduce `run/`
  to `run4/` `check.txt`. Development: one launch (`dev11/`, `--limit 150`, 450 cases, 0 mismatches) under
  `workspace/logs/n66sa/s2ae/manifest-dev-p5.sha256` (8 lines, passes from `workspace/logs/n66sa/s2ae/`), not cited.
- **Outcomes:** `tc` 1 028 returns of 0, 2 731 of 1, 241 fatal-path stops (a null caster path, or a clear on a
  caster of type 2 or 4; predicted); `rfa` 1 284 `PathPlan` calls from 0x005D4141, 37 returns (null unit), 179 stops
  (path `+0x40` = 0xB or 8); `rro` 1 332 `PathPlan` calls from 0x005CD1AE, 433 returns (null unit, or the roll below
  20), 235 stops.
- **Controls:** 78, 74 separating, each `passed` 0. Not separating: `tc pet_u0` and `pet_t1` (`SkillPetTest`'s first
  test: a target that is not type 1 fails its owner test anyway), `rfa b_lt_4d~` and `rro b_lt_4d~` (a byte of 77
  gives 77 either way). The spec-reading controls: `tc spec_d2` (D2's dead-target rule) 1 564, `rfa spec_plus_x`
  1 284, `rro spec_no_step` 1 775, `rro spec_smod` 766.
- **Not covered:** see skills/0002 § 21, *Not covered*; everything past `PathPlan`'s entry; what `+0xC4` bit 1 or any
  other offset means. **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the maps above; spec D2's
  dead-target rule is contradicted in three of five cells (`split.txt`); the claims and the rows they settle are in
  skills/0002 § 21.

## run:2026-11-16-sweep2-s2ae6

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2ae (`lane/n66sa`), part 6: stat-event
handlers 7, 8, 9, 10, 18 and 31 and Kick's start function 2 under Ghidra's p-code emulator on the pinned image
(ADR-0015, ADR-0021), compared with a `tools/` model, and the objdump reads behind part 6's route decisions. No game,
no wine. The claims are in
[skills/0002 § 22](0002-missiles.md#22-plan-0066-batch-s2ae-part-6-six-stat-event-handlers-and-kicks-start-emulated-the-open-routes-read-2026-11-16-lanen66sa).

- **Question:** do the six handlers and `sub_0056CAF0_SkillSt02Kick`, run on declared inputs, give what skills/dispatch
  K and I4 (at `b5999f5e`) state as inferred, up to the first call on each route that reaches the allocator?
- **Setup:** `tools/skills_s2ae6_emu.py` (sha256 `74a04489…`, stdlib and objdump; imports `tools/combat_s5e_emu.py`
  and parts 1, 3 and 5's tools, unchanged, pointed at this part's families in their module state only: part 1's
  case, check and manifest machinery, S5e part 1's unit builder `put_unit`, part 3's memory view, part 5's
  `GameFindUnit`, `MonsterOwner`, `UNIT_GetTargetUnit` and stat-list models), `re/ghidra_scripts/EmuBoundary.java`
  unchanged, Ghidra 12.1.2, project `workspace/ghidra-n66sa` (`-Xmx3G`, `MemoryMax=4G`). One kept launch of
  `tools/ghidra.sh emuboundary`, 7 families (`h7` 2 000, `h8` 3 000, `h9` 2 500, `h10` 1 500, `h18` 4 000, `h31` 4 000,
  `st2` 1 500), seeds `random.Random("n66sa-s2ae6-<family>")`, tables `random.Random("n66sa-s2ae6-tables")`.
- **Memory spec** (`s2ae.mem`): a scratch DataTables at 0x21000000 (`dt.bin`: 192 states; 576 seeded MonStats rows
  of 0x1A8 at `+0xA78`/`+0xA80`, `monstats.bin`, `+0x18` a valid MonStats2 index in 8 of 12 draws and −1, the count,
  the count + 7 or −0x8000 otherwise; 128 seeded MonStats2 rows of 0x134 at `+0xA90`/`+0xA98`, `monstats2.bin`; 48
  seeded Skills rows of 0x23C at `+0xB98`/`+0xBA0`, `skills.bin`; 512 zero ItemStatCost records, `isc.bin`), a zero
  game image of 0x2000 bytes at 0x20010000 (`game.bin`, the bucket heads a case does not write). Each case writes its
  units (0x100 bytes each with monster data, a sorted stat list with layer-1 decoys and state bits, as S5e part 1),
  owner records and bucket heads (`h31`, `st2`), the unit's path (`st2`) and `h7`'s packet. Guards: the fatal path
  0x00408090, 0x00408A60, 0x00681E09 and the allocator 0x0040B4B0, 0x0040B430, 0x0040B480. Observed boundaries:
  `sub_005DDD00_MonFleeFrom`, `0x005C39C0`, `COMBAT_ApplyDamage` 0x0057C6C0, `sub_00627260_UnitSetStat`,
  `UNIT_AddEvent` 0x005C0AD0, `COMBAT_ResolveAndQueue` 0x0057DBF0; at each the call's `ECX`/`EDX` (where the code
  sets them), its stack arguments and the dumps (the unit's seed; `h10`'s and `st2`'s stack packet at 0x7FEFFF88, 0x70
  bytes) are compared. Every other callee runs whole.
- **Domain:** the handlers' units are non-null where `UnitGetStat` is reached (it does not test the unit); owner
  chains end within two links, types 0 to 5; Kick's skill id is inside the table and its unit has a path.
- **Read set (ADR-0015 (2)):** every traced read falls in a declared constant range: `g_BitMask32` (0x005BF9B0 215,
  0x005BF9BF 112, 0x00624F9F 8 509, 0x0063E97D 2 332) and `GameFindUnit`'s bucket offsets 0x006E10E0 (0x00552F9C
  1 569), both `.rdata`. No traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66sa/s2ae/run6`):
  ```
  python3 -I tools/skills_s2ae6_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66sa GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s2ae.cases $D/s2ae.mem > $D/s2ae.out 2> $D/s2ae.err
  python3 -I tools/skills_s2ae6_emu.py check --dir $D > $D/check.txt
  python3 -I tools/skills_s2ae6_emu.py reach > $D/reach.txt
  python3 -I tools/skills_s2ae6_emu.py static > $D/static.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`276b3a96…`, 85 lines, last line `S2AE total cases=18500 mismatches=0 stops=0
  controls=75 unseparated=6 controls_passed=0 unaccounted=0`), `reach.txt` (`a3ae2ace…`, 15 lines), `static.txt`
  (`f6b1716e…`, 2 532 lines: the functions run and the triage reads, each with its direct-call count), `s2ae.out`
  (`c2a8f092…`), `s2ae.cases` (`280579e7…`, regenerated byte for byte by `cases`), listed in `manifest.sha256`
  (`d5ce3bdc…`, 13 lines), which passes from `$D`. The committed revision adds `reach` to the revision that ran the
  emulation (same cases; `check` and `static` reproduce their files byte for byte). Parts 4 and 5's `check` still
  reproduce `run4/` and `run5/` `check.txt`. Development: three launches (`dev12/`, `--limit 40`, the first revision;
  `dev13/`, full counts, before `h31`'s stat values were narrowed to separate `roll_lt_v~`; `dev14/`, the kept
  revision, whose `check.txt` equals `run6/`'s) under `workspace/logs/n66sa/s2ae/manifest-dev-p6.sha256` (passes from
  `workspace/logs/n66sa/s2ae/`), not cited.
- **Outcomes** (`reach.txt`): `h7` 355 returns of 1, 1 645 of 0; `h8` 296 `MonFleeFrom` calls, 2 704 returns; `h9` 571
  calls of `0x005C39C0`, 1 929 returns; `h10` 474 `ApplyDamage` calls, 1 026 returns; `h18` 319 `UnitSetStat` calls
  (101 sums, 89 at the maximum, 129 at 0), 3 681 returns; `h31` 299 `UNIT_AddEvent` calls, 3 701 returns; `st2` 648
  `ResolveAndQueue` calls, 852 returns of 0.
- **Controls:** 75, 69 separating, each `passed` 0. Not separating, inherent: the strictness of a clamp at its own
  bound (`h9 ch_gt0~`, `ch_gt1~`, `ch_lt99~`, `n_gt1~`, `n_lt20~`, `h18 nl_lt_max~`: the bound gives the bound either
  way). The spec-reading and alternative controls: `h7 spec_mask_ff` 164, `h8 spec_mask_4` 132, `h9 spec_no_third` 56,
  `h10 spec_no_shift` 474, `h18 spec_no_floor` 108, `st2 spec_maxdam` 648, `st2 spec_shift_full` 77.
- **Not covered:** see skills/0002 § 22, *Not covered*; everything past the observed calls; what the packet fields,
  `+0xC4` bit 2 or the `UNIT_AddEvent` arguments mean. **Conclusion:** bit-exact reproduction (evidence rule 4,
  ADR-0015) of the maps above; the claims and the rows they settle are in skills/0002 § 22.

## run:2026-11-16-sweep2-s2ae7

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2ae (`lane/n66sa`), part 7:
`SKILLS_ItemChargesOk`, `sub_005DAA40_SkillWeaponWear` and stat-event handlers 26 and 27 under Ghidra's p-code
emulator on the pinned image (ADR-0015, ADR-0021), compared with a `tools/` model. No game, no wine. The claims are in
[skills/0002 § 23](0002-missiles.md#23-plan-0066-batch-s2ae-part-7-skills_itemchargesok-skillweaponwear-and-handlers-26-and-27-emulated-2026-11-16-lanen66sa).

- **Question:** do the four functions, run on declared inputs, give what skills/dispatch C7, N2, P and K (at
  `b5999f5e`) state as inferred, up to the first call on each route that reaches the allocator?
- **Setup:** `tools/skills_s2ae7_emu.py` (sha256 `6a383a11…`, stdlib and objdump; imports `tools/combat_s5e_emu.py`
  and parts 1, 3, 5 and 6's tools, unchanged, pointed at this part's families in their module state only: part 1's
  case, check and manifest machinery, S5e part 1's unit builder, part 3's memory view, part 5's `GameFindUnit`,
  `MonsterOwner` and stat-list models, part 6's unit, owner-link and seed helpers), `re/ghidra_scripts/EmuBoundary.java`
  unchanged, project `workspace/ghidra-n66sa` (`-Xmx3G`, `MemoryMax=4G`). One kept launch of `tools/ghidra.sh
  emuboundary`, 4 families (`chg` 3 000, `wear` 4 000, `h26` 4 000, `h27` 2 500), seeds
  `random.Random("n66sa-s2ae7-<family>")`, tables `random.Random("n66sa-s2ae7-tables")`.
- **Memory spec** (`s2ae.mem`): a scratch DataTables at 0x21000000 (`dt.bin`: 576 seeded MonStats rows, `+0x170` a
  valid Skills row in 7 of 12 draws, else −1, 48, 51, 0x7FFF or −0x8000; 48 seeded Skills rows, `+0x158` 0, 100, 1–99,
  101–400, −50…−1 or a random word; 512 zero ItemStatCost records; 64 ItemTypes rows of two equivalence words at
  `+0xBFC`/`+0xC00`/`+0xC04`, `itemtypes-eq.bin`, type 45's bit set in about 45 %), and, set on purpose as inputs of the
  claims, `ExpMaxLevel`'s table pointer 0x0096C8A8 (a case-written word) and the items count and records
  0x0096CA58/0x0096CA5C (64 seeded records of 0x1A8, `items.bin`: `+0x11E` a declared type, `+0x120` 0, −1, a type,
  64 or 0x7FFF, `+0x132`, `+0x112`, `+0x113` varied); a zero game image at 0x20010000 (`game.bin`). Each case writes
  its units, items with stat lists (live and base arrays), inventory chain, skill entry and record, owner records and
  bucket heads. Guards: 0x00408090, 0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480. Observed
  boundaries: `PLAYER_UseAmmo` 0x0056C3F0, `sub_00627260_UnitSetStat`, `sub_0055F850_ItemBreak`, `STATE_ApplyTimed`
  0x0056E970; at each the registers the code sets, the stack arguments and the dumps (`wear`'s unit seed, `h26`'s
  packet word `+0x4C`, `h27`'s parameter block at 0x7FEFFFD8, 0x24 bytes) are compared. Every other callee runs
  whole.
- **Domain:** `chg`'s entry has a skill record; `wear`'s item class is below the items count and its record's first
  type a declared row (0x00628700 does not range-test it); `h26`'s owner chains one link; the handlers' units are
  non-null where `UnitGetStat` reads them.
- **Read set (ADR-0015 (2)):** every traced read falls in a declared constant range: `g_BitMask32` (0x00624EFC 1 558,
  0x00624F9F 6 627, 0x00629C0B 3 885, 0x00629C64 130) and `GameFindUnit`'s bucket offsets 0x006E10E0 (0x00552F9C
  1 698), both `.rdata`. No traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66sa/s2ae/run7`):
  ```
  python3 -I tools/skills_s2ae7_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66sa GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s2ae.cases $D/s2ae.mem > $D/s2ae.out 2> $D/s2ae.err
  python3 -I tools/skills_s2ae7_emu.py check --dir $D > $D/check.txt
  python3 -I tools/skills_s2ae7_emu.py reach > $D/reach.txt
  python3 -I tools/skills_s2ae7_emu.py static > $D/static.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`1baf4dc6…`, 76 lines, last line `S2AE total cases=13500 mismatches=0 stops=0
  controls=69 unseparated=4 controls_passed=0 unaccounted=0`), `reach.txt` (`32353c4a…`, 8 lines), `static.txt`
  (`27991a14…`, 997 lines: the functions run, each with its direct-call count), `s2ae.out` (`60f3e25c…`), `s2ae.cases`
  (`c4d4ac5d…`, regenerated byte for byte by `cases`), listed in `manifest.sha256` (`60c01ec1…`, 14 lines), which
  passes from `$D`. The committed revision ran the emulation; `check` reproduces `check.txt` byte for byte, and parts 5
  and 6's `check` still reproduce `run5/` and `run6/` `check.txt`. Development: two launches (`dev15/`, `--limit 150`;
  `dev16/`, full counts, before `wear`'s chance was set at the roll in 12 % of the cases to separate `ra_lt_ch~`)
  under `workspace/logs/n66sa/s2ae/manifest-dev-p7.sha256` (24 lines, passes from `workspace/logs/n66sa/s2ae/`), not
  cited.
- **Outcomes** (`reach.txt`): `chg` 676 returns of 0, 2 324 of 1; `wear` 189 `PLAYER_UseAmmo`, 209 `ItemBreak`, 137
  `UnitSetStat` calls, 3 465 returns; `h26` 407 `UnitSetStat` calls, 3 593 returns of 0; `h27` 1 294
  `STATE_ApplyTimed` calls, 1 206 returns of 0.
- **Controls:** 69, 65 separating, each `passed` 0. Not separating, inherent: the strictness of a clamp at its own
  bound (`chg lvl_gt0~`, `lvl_lt_max~`, `h26 nv_lt256~`, `h27 v_ge_cap~`). The spec-reading and alternative controls:
  `chg spec_full_value` 358, `spec_no_mask` 215; `wear spec_math_le0` 58; `h26 spec_pct` 31, `spec_no_floor` 116;
  `h27 spec_cap_swap` 720.
- **Not covered:** see skills/0002 § 23, *Not covered*; everything past the observed calls. **Conclusion:** bit-exact
  reproduction (evidence rule 4, ADR-0015) of the maps above; the claims and the rows they settle are in skills/0002
  § 23.

## run:2026-11-16-sweep2-s2ae8

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2ae (`lane/n66sa`), part 8:
`sub_00627260_UnitSetStat` run whole on a declared stat-list world, alone, behind handlers 18 and 26 and
`SkillWeaponWear`, and inside `sub_0064AC60_MissileDamageToStats`, under Ghidra's p-code emulator on the pinned image
(ADR-0015, ADR-0021), compared with a `tools/` model. No game, no wine. The claims are in
[skills/0002 § 24](0002-missiles.md#24-plan-0066-batch-s2ae-part-8-the-stat-setter-run-whole-behind-handlers-18-26-skillweaponwear-and-in-missiledamagetostats-2026-11-16-lanen66sa).

- **Question:** does the setter, run on a declared list, write what skills/dispatch K 18, K 26, N2 and skills/missiles
  C1 (at `b5999f5e`) state as inferred, up to the first call on each route that allocates?
- **Setup:** `tools/skills_s2ae8_emu.py` (sha256 `8af90127…`, stdlib and objdump; imports `tools/combat_s5e_emu.py`
  and parts 1, 5, 6 and 7's tools, unchanged, in their module state only: part 1's case, check and manifest
  machinery, part 6's `h18` and part 7's `h26` and `wear` generators and models, their MonStats and Skills images
  merged: part 6's rows with part 7's `+0x170` and `+0x158` columns), `re/ghidra_scripts/EmuBoundary.java` unchanged,
  project `workspace/ghidra-n66sa` (`-Xmx3G`, `MemoryMax=4G`). The world follows batch S4e part 5d's `addst`
  (`lane/n66z`, `tools/items_s4e8_emu.py`, read on its branch, not imported). One kept launch of `tools/ghidra.sh
  emuboundary`, 5 families (`set` 6 000, `h18w` 3 000, `h26w` 3 000, `wearw` 3 000, `mdts` 3 000), seeds
  `random.Random("n66sa-s2ae8-<family>")`, ItemStatCost rows `random.Random("n66sa-s2ae8-isc")`.
- **Memory spec** (`s2ae.mem`): part 6's DataTables at 0x21000000 (`dt.bin`) with the merged MonStats, MonStats2 and
  Skills images, part 7's items count and records and ItemTypes words; 512 ItemStatCost rows (`isc.bin`): `+0x04`
  random, `+0x05` random with bit 2 clear, `+0x50` 1 in 4, `+0x51` non-zero in 15 %, `+0x52` in 10 %, `+0x53` 1 in 3,
  and for the 37 stats of the handlers and `MissileDamageToStats` (6, 12, 72, 180 and C1's) the shipped
  `itemstatcost.bin` bytes at those six offsets, read from `workspace/merged` at case time; the CRT copy-path flag
  0x00994C88 = 1 (set on purpose: memmove reads it for 256 bytes or more); a zero game image (`game.bin`). Each case
  writes its unit, the list header, base and cache arrays with spare slots (`0xEE`), the changed-key array, the
  callback word (0, or 0x0055B800) and up to two parent lists. Guards: 0x00408090, 0x00408A60, 0x00681E09,
  0x0040B430, 0x0040B480. Observed: `STATLIST_InsertEntry` 0x00624C80, 0x0040B4B0, 0x0055B800,
  `sub_006266C0_StatRecompute`, `sub_00621E40_UnitSetOverlayStat`, 0x005531C0, `PLAYER_UseAmmo`,
  `sub_0055F850_ItemBreak`; at each the registers the code sets, the stack arguments, the return address and the
  dumps (the list header, every array, the parents' flags and caches, the missile data word) are compared.
- **Read set (ADR-0015 (2)):** every traced read falls in a declared constant range: `g_BitMask32` (0x00624E2E
  39 554, 0x00625120 41 038, 0x00626974 54 293, 0x00624EFC 2 678, 0x00624F9F 15 961, 0x00629C0B 2 984, 0x00629C64 57,
  0x0063E97D 2 801), `GameFindUnit`'s bucket offsets (0x00552F9C 2 754), `MarkClientDirty`'s switch tables
  0x00624EB0/0x00624EB8 (0x00624DF6, 0x00624DFD, 4 958 each) and the memmove's jump tables (0x0068389C 4 053,
  0x006838C4 1 787, 0x006839AB 1 787, 0x00683A2E 183, 0x00683B47 183). No traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66sa/s2ae/run8`):
  ```
  python3 -I tools/skills_s2ae8_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66sa GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s2ae.cases $D/s2ae.mem > $D/s2ae.out 2> $D/s2ae.err
  python3 -I tools/skills_s2ae8_emu.py check --dir $D > $D/check.txt
  python3 -I tools/skills_s2ae8_emu.py reach > $D/reach.txt
  python3 -I tools/skills_s2ae8_emu.py static > $D/static.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`2a37b7c0…`, 249 lines, last line `S2AE total cases=18000 mismatches=0 stops=0
  controls=241 unseparated=42 controls_passed=0 unaccounted=0`), `reach.txt` (`fe367583…`, 10 lines), `static.txt`
  (`24013e3c…`, 467 lines: the setter's functions and the three handler tails, each with its direct-call count),
  `s2ae.out` (`aeb075e2…`), `s2ae.cases` (`c68738a3…`, regenerated byte for byte by `cases`), listed in
  `manifest.sha256` (`45f538e0…`, 15 lines), which passes from `$D`. The emulation ran on the revision before the
  `spec_sorted` control was added (a model-side control: cases and `reach.txt` unchanged); the committed revision
  reproduces `check.txt`. Part 7's `check` still reproduces `run7/check.txt`. Development: three launches (`dev17/`,
  `dev18/`, `dev19/`, `--limit 300`: the dumps' address order, the `mdts` family, the copy-path flag) under
  `workspace/logs/n66sa/s2ae/manifest-dev-p8.sha256` (40 lines, passes from `workspace/logs/n66sa/s2ae/`), not cited.
- **Outcomes** (`check.txt`): `set` 3 831 returns, 848 `InsertEntry`, 405 resize, 447 callback, 469 `StatRecompute`;
  `h18w` 1 876 overlay calls, 440 returns, 317 `InsertEntry`, 367 resize; `h26w` 2 633 returns, 364 `InsertEntry`, 3
  resize; `wearw` 2 091 client calls, 446 returns, 26 `UseAmmo`, 24 `ItemBreak`, 398 `InsertEntry`, 15 resize; `mdts`
  1 648 returns, 360 `InsertEntry`, 992 resize.
- **Controls:** 241, 199 separating, each `passed` 0. Not separating: `rm_mid~` (a last entry moves 0 bytes) and
  `ge_max~` (at most 8 entries declared), and in `h18w`, `h26w`, `wearw`, `mdts` the reversals the shipped rows make
  inert (`ca_cb`, `ca_pos`, `md_ext`, `sx_ext`, `sx_8`, `us_player`, `us_ret` and the like: rows 6 and 72 have no
  callback bit, stat 6 stops at the switch, row 72 sends nothing), plus the parts' own clamp strictness
  (`nl_lt_max~`, `nv_lt256~`, `pk_pos~`). The spec-reading and alternative controls: `spec_add` (set 4 539, h18w
  1 968, h26w 2 347, wearw 2 200, mdts 2 744), `spec_md_all` (set 43, h18w 328, h26w 517), `spec_no_zero_floor` 281,
  `spec_315_once` 1 123, `spec_sorted` 977, and parts 6 and 7's `spec_no_floor`, `spec_pct`, `spec_math_le0`.
- **Not covered:** see skills/0002 § 24, *Not covered*; everything past the observed calls. **Conclusion:** bit-exact
  reproduction (evidence rule 4, ADR-0015) of the maps above; the claims and the rows they settle are in skills/0002
  § 24.

## run:2026-11-16-sweep2-s2ae9

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2ae (`lane/n66sa`), part 9 (the
closing part): `sub_005C49E0_SummonSetLevel` whole and `sub_005C87A0_StatEv25CycloneArmor` to its boundaries, both
with part 8's stat setter run whole, under Ghidra's p-code emulator on the pinned image (ADR-0015, ADR-0021),
compared with a `tools/` model. No game, no wine. The claims are in
[skills/0002 § 25](0002-missiles.md#25-plan-0066-batch-s2ae-part-9-summonsetlevel-and-handler-25-emulated-with-the-setter-whole-the-batch-closed-2026-11-16-lanen66sa).

- **Question:** do `SummonSetLevel` and handler 25 do what skills/dispatch L2 (the summon level, no `noRatio` test)
  and K 25 (at `b5999f5e`) state as inferred, up to the first call on each route that leaves the claim?
- **Setup:** `tools/skills_s2ae9_emu.py` (sha256 `e5d88bb6…`, stdlib and objdump; imports `tools/combat_s5e_emu.py`
  and parts 1, 6, 7 and 8's tools, unchanged, in their module state only: part 1's case, check and manifest
  machinery, part 8's setter model, world builder and ItemStatCost rows), `re/ghidra_scripts/EmuBoundary.java`
  unchanged, project `workspace/ghidra-n66sa` (`-Xmx3G`, `MemoryMax=4G`). One kept launch of `tools/ghidra.sh
  emuboundary`, 2 families (`ssl` 6 000, `h25` 8 000), seeds `random.Random("n66sa-s2ae9-<family>")`.
- **Memory spec** (`s2ae.mem`): a DataTables image at 0x21000000 (`dt.bin`: states 192, part 6's Skills image of 48
  rows with part 7's column merged (`skills.bin`), part 8's 512 ItemStatCost rows (`isc.bin`, the same bytes as
  `run8/isc.bin`); no MonStats image, `+0xA78` 0); the CRT copy-path flag 0x00994C88 = 1. Each case writes only:
  `ssl` the summon's `+0x00` and `+0x5C`, its list (part 8's world: header, base and cache arrays, changed-key array,
  up to two parents) holding keys 12, 31 and 19 or not, the owner's `+0x5C` and list with stat 12, the game's
  `+0x6A`, `+0x6D`, `+0x74`, the data table's `+0xB70`/`+0xB74` and the MonLvl rows (0x78 bytes) the level can
  index; `h25` the unit's `+0x5C`, its list's `+0x10`, `+0x3C`, `+0x40`, `+0x58` and bit sets, decoy lists' `+0x14`
  and `+0x2C`, the target state list (part 8's world), the Skills record's `+0x54`, `+0x56`, `+0x80` and a 0x40-byte
  packet. Guards: 0x00408090, 0x00408A60, 0x00681E09, 0x0040B430, 0x0040B480. Observed: `STATLIST_InsertEntry`
  0x00624C80, 0x0040B4B0, 0x0055B800, `sub_006266C0_StatRecompute`, `sub_0064C040_UnitMarkUpdated`, `STATE_Set`
  0x00639DB0; at each the registers the code sets, the stack arguments, the return address and the dumps (list
  headers, arrays, parents, the packet, the state bit sets) are compared.
- **Read set (ADR-0015 (2)):** every traced read falls in a declared constant range: `g_BitMask32` (0x00624E2E 6 941,
  0x00624EFC 12 488, 0x00624F9F 3 990, 0x00625120 7 157, 0x00626974 10 680, 0x00639E67 743), `MarkClientDirty`'s
  switch tables (0x00624DF6, 0x00624DFD, 3 026 each) and the memmove's jump tables (0x0068389C 451, 0x006838C4 2 177,
  0x006839AB 2 177, 0x00683A2E 275, 0x00683B47 275). No traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66sa/s2ae/run9`):
  ```
  python3 -I tools/skills_s2ae9_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66sa GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s2ae.cases $D/s2ae.mem > $D/s2ae.out 2> $D/s2ae.err
  python3 -I tools/skills_s2ae9_emu.py check --dir $D > $D/check.txt
  python3 -I tools/skills_s2ae9_emu.py reach > $D/reach.txt
  python3 -I tools/skills_s2ae9_emu.py static > $D/static.txt
  python3 -I tools/skills_s2ae9_emu.py wrap > $D/wrap.txt
  python3 -I tools/skills_s2ae6_emu.py check --dir workspace/logs/n66sa/s2ae/run6 > $D/check6-rerun.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`40230f8d…`, 154 lines, last line `S2AE total cases=14000 mismatches=0 stops=0
  controls=149 unseparated=22 controls_passed=0 unaccounted=0`), `reach.txt` (`b776807a…`, 4 lines), `static.txt`
  (`bf2c02a2…`, 862 lines: 19 functions or ranges with their direct-call counts), `wrap.txt` (`8ec21331…`, 4 lines),
  `s2ae.out` (`e8688f7f…`), `s2ae.cases` (`0f12d5dc…`), and `check6-rerun.txt` (`276b3a96…`, byte-identical to
  `run6/check.txt`: part 6's check reproduces), and `batch-totals.txt` (`fb605ba9…`, the nine parts' kept `check.txt`
  last lines and their sums), listed in `manifest.sha256` (`5089fa8d…`, 13 lines), which passes from `$D`. The emulation, `check`, `reach` and `static` ran on the revision before the `wrap` command was added; the
  committed revision reproduces all three byte for byte. Development: one launch (`dev20/`, the same cases; its
  `check.txt` equals the kept one) and the session's objdump listings (`scratch9/`) under
  `workspace/logs/n66sa/s2ae/manifest-dev-p9.sha256` (15 lines, passes from `workspace/logs/n66sa/s2ae/`), not cited.
- **Outcomes** (`reach.txt`): `ssl` 3 711 return 1, 648 return 0, 1 413 `InsertEntry` (466 from `CacheAdd`, 547 from
  `UnitAddStat`, 400 from `SetStatEx`), 228 resize; `h25` 312 return 1, 2 409 return 0, 2 473 `STATE_Set`, 743
  `UnitMarkUpdated`, 138 `InsertEntry`, 1 134 resize, 339 callback, 452 `StatRecompute`.
- **Controls:** 149, 127 separating, each `passed` 0. Not separating (22): the strictness of clamps and compares at
  bounds that give the same result (`cap_ge~`, `n_gt1~`, `n_gt1b~`, `ml_lt~`, `ml_ltn~`, `df_ge2~`, `ab10~`, `ab24~`,
  `ab1c~`, `rm_mid~`, `s54_ge0~`, `s54_ltn~`, `s56_ge0~`, `s56_ltn~`, `st_ge0~`, `sb_ge0~`, `sb_ltn~`), the reversals
  rows 19 and 31 make inert (`ax_8`, `ax_ext`, `ca_cb`) and `spec_md_all` in `ssl`. The spec-reading and alternative
  controls: `spec_floor` 2, `spec_ceil` 1 422, `spec_cells` 4 011, `spec_order` 556, `spec_add` (`ssl` 3 816, `h25`
  4 668), `spec_md_all` (`h25` 3).
- **Not covered:** see skills/0002 § 25, *Not covered*; everything past the observed calls. **Conclusion:** bit-exact
  reproduction (evidence rule 4, ADR-0015) of the maps above; the claims and the rows they settle are in skills/0002
  § 25.

## run:2026-11-16-sweep2-s2be2

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2be (`lane/n66sb`), part 2: do 6's
per-unit callback 0x005DB150 to `STATE_ApplyTimed`, and `sub_005D4DB0_SkillPrgDo36NovaAtTarget` whole to
`SkillNovaAtUnit` on Skills rows 44 and 48, under Ghidra's p-code emulator on the pinned image (ADR-0015, ADR-0021),
compared with a `tools/` model; plus do 13's single return read with objdump over `.text` and with radare2. No game,
no wine. The claims are in
[skills/0003 § 19](0003-handlers.md#19-plan-0066-batch-s2be-part-2-do-13s-return-do-6s-per-unit-callback-and-prg-36-on-skills-rows-44-and-48-2026-11-16-lanen66sb).

- **Question:** do the callback and prg 36 do what skills/catalogue H5's `after:` line and M5 (at `b5999f5e`) state
  as inferred, up to the first call that leaves the claim? Does do 13 return 0 on every path (the catalogue's
  reimplementation notes)?
- **Setup:** `tools/skills_s2be2_emu.py` (sha256 `e5bb4844…`, stdlib, objdump and r2; imports
  `tools/combat_s5e_emu.py`, `tools/skills_s2ae_emu.py` (the case, check and manifest machinery) and
  `tools/skills_s2ae5_emu.py` (the `UNIT_GetTargetUnit` model and bucket layout), unchanged, in their module state
  only), `re/ghidra_scripts/EmuBoundary.java` unchanged, project `workspace/ghidra-n66sb` (a copy of
  `workspace/ghidra`, `import-symbols` run first; `-Xmx3G`, `MemoryMax=4G`). One kept launch of `tools/ghidra.sh
  emuboundary`, 2 families (`cb43` 1 500, `p36` 5 000), seeds `random.Random("n66sb-s2be2-<family>")`.
- **Memory spec** (`s2ae.mem`): a DataTables image at 0x21000000 (`dt.bin`: calc pool 0x21900000 of 0x40 bytes,
  states 192, 64 Skills rows at 0x21300000, stats 512); the Skills image (`skills.bin`) and a Missiles image of 0x200
  rows at 0x21800000 (`missiles.bin`, with 0x0096C794 and 0x0096C79C pointing at it), random from
  `random.Random("n66sb-s2be2-tables")` except Skills rows 44, 48 and Missiles rows 90, 119, which carry the shipped
  `.bin` bytes read from `workspace/merged` at case time. Each case writes only: `cb43` the context (0x20 bytes, `+0x0C`
  the block) and the block (0x20 bytes); `p36` the caster, the target and a decoy unit (0x100 bytes each; type, guid,
  mode, bucket link), the caster's path (0x70 bytes, `+0x58` the stored target, type and guid) and the bucket heads.
  Guards: 0x00408090, 0x00408A60, 0x00681E09, 0x0040B4B0, 0x0040B430, 0x0040B480. Observed: `STATE_ApplyTimed`
  0x0056E970, `SkillNovaAtUnit` 0x0056D400. At each, the run compares the registers the code sets, the stack arguments
  and the return address (`cb43`: `ECX` = `ESP + 8` and the nine dwords there; `p36`: `ECX`, `EDX`, the five
  arguments and the path's target words).
- **Read set (ADR-0015 (2)):** every traced read falls in a declared constant range: `g_BitMask32` (0x005D3D1A
  1 943) and GameFindUnit's bucket offsets (0x00552F9C 4 058). No traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66sb/s2be/run2`):
  ```
  python3 -I tools/skills_s2be2_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66sb GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s2ae.cases $D/s2ae.mem > $D/s2ae.out 2> $D/ghidra.err
  python3 -I tools/skills_s2be2_emu.py check --dir $D > $D/check.txt
  python3 -I tools/skills_s2be2_emu.py rows > $D/rows.txt
  python3 -I tools/skills_s2be2_emu.py static > $D/static.txt
  systemd-run --user --scope -p MemoryMax=4G python3 -I tools/skills_s2be2_emu.py tail > $D/tail.txt
  python3 -I tools/skills_s2be2_emu.py manifest --dir $D --write
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`2030c929…`, last line `S2AE total cases=6500 mismatches=0 stops=0 controls=35
  unseparated=5 controls_passed=0 unaccounted=0`), `rows.txt` (`b8547594…`, the outcome per case kind and the shipped
  rows' bytes), `tail.txt` (`ec66e116…`, last line `TAIL verdict single-ret-after-xor`), `static.txt` (`dc526bbe…`,
  249 lines), `s2ae.out` (`2ceb453c…`), `tool.sha256` (`63154aa7…`), listed in `manifest.sha256` (`0dc5df57…`, 12
  lines), which passes from `$D`. The emulation ran on an earlier revision of the tool that differed in `tail` and
  `rows` only. The committed revision reproduces `check.txt` byte for byte, and wrote `rows.txt` and `tail.txt`.
  Development: one launch of 400 cases (`dev1/`, the same families) under
  `workspace/logs/n66sb/s2be/manifest-dev-p2.sha256` (7 lines, passes from `workspace/logs/n66sb/s2be/`), not cited.
- **Outcomes** (`check.txt`, `rows.txt`): `cb43` 1 500 at `STATE_ApplyTimed`; `p36` 1 808 at `SkillNovaAtUnit`
  (row 44 735 with `m` 119 and `v` 24, row 48 688 with `m` 90 and `v` 24, 385 on random rows) and 3 192 returns of 0
  (on rows 44 and 48: 587 refused by the target alone, 1 201 by `lvl ≤ 0`).
- **Controls:** 35, 30 separating, each `passed` 0. Not separating (5): the charge-path tests `charge_flag`,
  `cst_ge0`, `cst_ge0~` and `cstat_ge0~` (the declared rows keep the path closed) and `m_ge0~`. The spec-reading
  controls: `spec_block_order` 1 500, `spec_unit_first` 1 500, `spec_caster_centre` 1 808, `spec_floor` 52.
- **Not covered:** everything past the observed calls; the charge path of `SrvMissileByCharge` (0x006256B0); a calc
  inside the pool; how an item cast reaches prg 36. **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015)
  of the two maps above, and a two-tool read of do 13's return; the claims and the rows they settle are in skills/0003
  § 19.

## run:2026-11-16-sweep2-s2be3

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S2be (`lane/n66sb`), part 3 (the
closing part): do 140 on the catalogue's worked example, and do 137 with `STATE_Set` and `UnitMarkUpdated` run whole
up to 0x00570590, under Ghidra's p-code emulator on the pinned image (ADR-0015, ADR-0021), compared with a `tools/`
model. No game, no wine. The claims are in
[skills/0003 § 20](0003-handlers.md#20-plan-0066-batch-s2be-part-3-closing-the-worked-example-of-do-140-and-do-137-past-state_set-2026-11-16-lanen66sb).

- **Question:** does do 140 on the worked example's inputs give the spec's table (skills/catalogue *Worked example*
  at `b5999f5e`)? Does do 137 reach 0x0064C040 and 0x00570590 after `STATE_Set` as the catalogue's Q4 `after:` line
  states, and with what?
- **Setup:** `tools/skills_s2be3_emu.py` (sha256 `d14b1781…`, stdlib; imports `tools/skills_catalogue_emu.py` (plan
  0046's batch 8c worlds, models, `check9b` and `cmd_cases`/`cmd_check`) and `tools/rng.py`, unchanged, in their
  module state only), `re/ghidra_scripts/EmuBoundary.java` unchanged, project `workspace/ghidra-n66sb` (symbols
  imported in part 2; `-Xmx3G`, `MemoryMax=4G`). Two kept launches of `tools/ghidra.sh emuboundary`, one per family
  (`tent140` 1 200, `d137` 1 500), seeds `random.Random("cat8c-<family>")`. Two earlier `d137` launches (a key error
  in the generator fixed; then a revision with the state bit set in only 1 of 221 reaching cases, changed to half)
  were overwritten by the kept one and are not cited.
- **Memory spec** (`<family>.mem`): batch 8c's (`mem_8c`: the scratch DataTables at 0x12000000, Skills, MonStats,
  MonStats2, ItemStatCost, the states count 190 and the set at `+0x150`), with, for `d137`, DataTables `+0xBC` →
  0x12670000 (the States records; record 104's byte `+0x12` written per case), `STATE_Set` 0x00639DB0 no longer
  observed and 0x00570590 observed. Each `d137` case also writes the target's 12 state words, its `+0xC4`, `+0xC8`,
  `+0xE0`, and each room's `+0x1C`, `+0x2C` (→ a flag dword at the room's `+0xE0`) and `+0x34`; all of them are
  dumped and compared. `tent140`'s first two cases are the worked example (W1 a room `(90, 190, 20 × 20)` holding
  `(100, 199)`; W2 a room at `(5000, 5000)` and no near rooms).
- **Read set (ADR-0015 (2)):** every traced read falls in a declared constant range: GameFindUnit's bucket offsets
  0x006E10E0 and `g_BitMask32` 0x006CE268 (.rdata). `undeclared=0` for both families.
- **Procedure** (worktree root; `D=workspace/logs/n66sb/s2be/run3`):
  ```
  python3 -I tools/skills_s2be3_emu.py cases tent140 d137 --dir $D
  for f in tent140 d137; do
    GHIDRA_PROJ_DIR=workspace/ghidra-n66sb GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
        tools/ghidra.sh emuboundary $D/$f.cases $D/$f.mem > $D/$f.out 2> $D/$f.err
  done
  python3 -I tools/skills_s2be3_emu.py check --dir $D > $D/check.txt
  python3 -I tools/skills_s2be3_emu.py worked --dir $D > $D/worked.txt
  python3 -I tools/skills_s2be3_emu.py manifest --dir $D --write
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`dde8acec…`, 16 lines: `tent140 cases=1200 match=1200 bad=0` and `d137 cases=1500
  match=1500 bad=0`, both `undeclared=0 stopped=0`), `worked.txt` (`2ed96de9…`: the nine steps from `(1, 666)` and the
  model's W1 and W2), `tool.sha256` (`d14b1781…`), listed with the `.cases`, `.mem`, `.json`, `.out` and `.err` files in
  `manifest.sha256` (`3f8db4aa…`, 13 lines), which passes from `$D`.
- **Outcomes:** `tent140` 433 at `SpawnAtPos` (from 0x005D2E07), 767 returns of 1, W1 and W2 among them as the
  spec's table gives them; `d137` 221 at 0x00570590 (from 0x005D2793; 104 bit new, 86 bit already set, 31 no list;
  70 no room and 33 refused by the room's `+0x34` bit 2 at the first `UnitMarkUpdated`; the other 118 cases make two
  calls each, of which 89 link and 147 find the target marked), 1 279 returns of 0 (327 bad
  id, 193 bad aurastate, 363 no target, 396 refused by 0x00645590).
- **Controls:** 5, each failing (`tent140`: `n_mod4` 913, `xy_swap140` 433; `d137`: `old_inv` 157, `chg_nsw` 100,
  `f34_any` 23); the site control fails every boundary case (433 and 221) with its return address changed.
- **Not covered:** what follows `SpawnAtPos` and 0x00570590; 0x00625A70's clear path (`STATE_Set` is called with 1);
  0x0063EFA0's Baal arm. **Conclusion:** bit-exact reproduction (evidence rule 4, ADR-0015) of the two maps above; the
  claims and the rows they settle are in skills/0003 § 20.
