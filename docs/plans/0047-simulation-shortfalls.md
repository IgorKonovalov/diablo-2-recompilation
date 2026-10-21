# 0047 — Simulation shortfalls: the named remainders of the combat, stats and travel runs

> **Status:** approved 2026-10-20 (owner)
> **Created:** 2026-10-20
> **Owner skill(s):** reverser, spec-writer
> **Related ADRs:** 0003-runtime-experiments, 0004-boundary-oracles-in-reproduction, 0011-harness-slots, 0013-forced-path-runs-cell-level, 0014-scope-game-simulation, 0017-scope-quests-travel-economy

## TL;DR

**Question:** do the branches that the reviewed combat, stats and travel specs read from the code, but whose runs fell
short of their minimums, behave as read? This is not a new subsystem: it reaches the **named shortfalls** of
run:2026-10-16-combat, run:2026-10-17-stats and plan 0042's travel runs with sessions built for them, on the existing
loggers and checkers, and re-tags the specs. When it is done, each shortfall below is reproduced to its minimum, or
named again with the reason it cannot be staged on stock data.

## Context

- **Why now.** The combat and stats specs are reviewed and their loggers and checkers are kept
  (`tools/combat.py`, `tools/gdb/combat.gdb`, `tools/stats.py`, `tools/gdb/stats.gdb`). Each shortfall is a missing
  *case*, not a missing reading: one harness slot closes them while plan 0045 is in its static phases, and the
  checkers' outstanding tool items land first.
- **The shortfalls**, as the specs name them:
  - [combat § Open questions](../specs/combat/README.md) (run:2026-10-16-combat, 40 655 events): crushing blow on a
    champion (0 labelled; the community "1/8 on champions" lead is contradicted in
    [combat/0001](../findings/combat/0001-formulas.md)); the resistance cap for cold (27), lightning (17), magic (0);
    magic immunity (0); the negative absorbed amount (4); evade, weapon block, dodge, avoid (0); freeze and flat
    absorb (0); the negative total that leaves life unchanged (25, under the floor of about 30); the mode-2 (walking)
    exception of the block `÷ 3` (no walking player attacked). **Conversion and pierce** are skill and missile
    effects: they move to plan [0045](0045-skills-missiles-machinery.md) Phase 2, not here.
  - [stats/states § Open questions](../specs/stats/states.md) (run:2026-10-17-stats): shrines and wells (12 operates
    against 50: the combat and stamina shrines, the re-arm, a cure by a well); an aura state's end (9 on and off
    events against 50); a different-state `group` clear; the 256 floor; open wounds on the player; the curse
    resistance cut and `attract`. The research map adds the expiries (123 of 300).
  - Plan [0042](done/0042-quests-travel.md) Phase 2 part 3 (run:2026-10-19-quests3, accepted with fixes 2026-10-20 at the
    `lane/p42r` review, its shortfalls final): **waypoint activation from mode 0** (0 of 20; the walk never reached an unvisited field
    waypoint, and field waypoints were first logged in mode 1 or 2 after a waypoint arrival), with the `Sync` 0
    object-seed draw. This plan takes it only **after 0042 closes**, and only if that close leaves it a shortfall.
- **The backlog it absorbs:**
  `2026-10-17-architect-reverser-stats-shrine-well-and-aura-end-addendum.md` (the stats addendum),
  `2026-10-17-architect-reverser-stats-checker-chaining-and-tests.md` (tool items for `tools/stats.py`, no game),
  `2026-10-17-architect-reverser-plan-0037-resume-lane-review-follow.md` ((a) the *Fleshripper* log copy into
  `workspace/logs/combat/` with a manifest hash, which plan 0045's oracle replacement needs; (b) the ≤ 0 counter).
- **Not here:** the event-9 handler and the state-52 call (read by plan 0045 Phase 1); objects' trap fires of types
  5, 7, 8 and 9 and the `fire` count (plan 0038's H5b and H5d batches, which load the objects logger); two-client
  cases (plan 0044).

## Phases

### Phase 1 — Tools and staging
- **Owner skill:** reverser
- **What:** land the checker items, copy the set-aside log, and write the session recipes.
- **Outputs:** `tools/stats.py` with the chaining and test items of the backlog entry and its tests; the *Fleshripper*
  log under `workspace/logs/combat/` with its manifest; `tools/combat_sessions.py` and `tools/stats_sessions.py`
  sessions for the cases below, with tool-built saves (stock items, ADR-0013 § Neutral) where a stat is needed
  (cold, lightning and magic resistances at the cap, a magic-immune target, dodge, avoid and evade on an Amazon, a
  weapon-blocking Assassin or a shield-less two-weapon character, a freeze item, flat absorb items); for the
  waypoint case (if it applies), a static reading of how `InitFn` 17 creates a waypoint in mode 0 and a route a
  fresh character can walk.
- **Done when:** the stats checker's tests pass (`python3 -I tools/test_stats.py` or its successor) and its chaining
  report matches the 18 kept logs; the log copy is hashed in the manifest; every case below has a session or a written
  reason it cannot be staged; the architect's review accepts the case list.

### Phase 2 — The runs
- **Owner skill:** reverser (agent-driven; **one slot**, given in the prompt)
- **What:** run the sessions on the existing loggers and checkers.
- **Done when:** `run:YYYY-MM-DD-shortfalls` reproduces with **0 mismatches** under `tools/combat.py` and
  `tools/stats.py`, and reaches, each to **30** unless stated or named again as a shortfall with its count and reason:
  - combat: crushing blow on champions (Nightmare or Hell); the resistance caps for cold, lightning and magic; magic
    immunity; the negative absorbed amount; evade, weapon block, dodge and avoid; freeze; flat absorb; the negative
    total that leaves life unchanged; a walking player's block;
  - stats: 50 shrine or well operates over the combat and stamina shrines, the re-arm and a well's cure; 50 aura on
    and off events; 300 expiries in total with the kept run; 20 different-state `group` clears; the curse resistance
    cut; 30 curses refused on a target in `attract` (Phase 1 review: a Necromancer's own Attract, then another curse on
    the same monster; open wounds on the player moved to plan [0044](done/0044-multiplayer-branches.md));
  - travel (after 0042 closes, if still short): 20 waypoint activations from mode 0, with the object-seed draw
    chained (ADR-0014).

### Phase 2b — The staging-limited cases (added at the Phase 2 review, 2026-10-21)
- **Owner skill:** reverser (agent-driven; **one slot**, given in the prompt)
- **What:** the stats and travel cases Phase 2 named again for staging reasons, not for stock data: fix the
  staging, run the sessions Phase 2 left unrun, add them to the same checkers.
- **Done when:** a run `run:YYYY-MM-DD-shortfalls2` (its own record, 0 mismatches under `tools/stats.py`,
  `tools/combat.py` and `tools/quests.py`) reaches, with Phase 2's and the kept runs' counts: 50 shrine or well
  operates over the combat and stamina shrines, the re-arm and a well's cure (`sor-shrines1`…`10`, `palc-wells2`);
  300 expiries (the potion plan's failure found and fixed first, in a dev session); 20 group-3 clears checked (the
  stats logger writes the exit line of the nested `STATE_GroupClear` call, or the checker reads the nested call's
  result; a tool change, its tests); the 256 floor and the curse resistance cut to 30 each (`ass-curses2` and a route
  that reaches the Worldstone Keep Level 1's witches; a field whose monsters poison `StatsFloor`); 20 waypoint
  activations from mode 0 (the pilot's warp search fixed, `x-wpact5r-1`…`5`); cold and lightning flat absorb to 30
  if `abs-nm-marsh` reaches them. Each case it cannot reach is named again with its count and a stock-data reason, or
  a tool reason with the fix tried; those are then final.

### Phase 3 — Re-tag
- **Owner skill:** spec-writer
- **What:** re-tag combat, stats/states and (if run) quests/travel from the run; narrow their open questions.
- **Done when:** each raised statement cites the run; the shortfall bullets are rewritten with the new counts; the
  wiki pages' `based_on` dates are refreshed if a page states a changed count; the gate is green; the architect's
  review passes.

## Resources and limits

- **Static:** Phase 1 needs no Ghidra for the tools; the waypoint reading takes a static lane for under an hour.
- **Harness:** Phase 2 takes **one slot from 1–2**; at most two games at once across all plans; not while plan 0045·P2
  or plan 0044·P2 holds both slots.
- **Character risk.** A death ends a session (ADR-0003): Hell champion sessions use the harness-play survival rules.
- **Rotation:** past about 4 h the lane checkpoints and a fresh lane resumes.
- **Estimate** (an estimate): one Phase 1 lane, one or two Phase 2 lane runs.

## Open questions

- **Magic cap and immunity.** Whether a stock monster or item set reaches the magic-resistance cap without a skill
  (phase 3) is part of Phase 1's case list.
- **Walking player's block.** It needs a player hit while in mode 2; the pilot may not be able to hold that mode
  under attack, in which case it stays `[I]`.

## Implementation log

_(lanes append dated entries as phases land: what was found, the confidence reached, surprises)_

- **2026-10-20 — Drafted (architect, `lane/plans45`).** Status `proposed`.
- **2026-10-20 — Approved (owner, via the orchestrator).** Plans 0045–0049 and ADR-0020 approved as proposed; the run
  order of the [plans index](README.md#run-order-unattended-queue-set-2026-10-20-plans-00380049) is the current queue.
- **2026-10-20 — Phase 1 landed (reverser, `lane/p47r`; static, no game, no slot, no Ghidra).** Review requested.
  - **Stats checker items** (backlog entry closed): `tools/stats.py` (`98538acf…`) reports the ADR-0014 aura chained
    pairs (the caster's next run entering on a drawing run's exit, keyed by the caster unit), keys the aura grid's
    gaps per log, builds every Sets block (values `<< ValShift`, the `state` block by func 24 with the compiled param,
    `tools/stats.py` `Tables.par_value` after `sub_006336A0_PropParamCell`), and `oracle-player` prints a consistency
    count. `tools/test_stats.py` (`d7d6b0c6…`): 15 tests pass (the well and recharge-shrine predictions, the negative
    stat-74 tick and the 256 floor, the full Trang-Oul's blocks, two written logs for the per-log reset, the per-log
    gaps and the chained pairs). **Chaining report vs the 18 kept logs:** 0 mismatches; 865 drawing aura runs, 746
    chained pairs (the review's scratch count), 115 breaks, 4 with no next run; aura gaps all 50 within a log; all
    5 749 wearer set lists predicted, the 180 full Trang-Oul's included (the *unchecked remainder* is gone, so no
    property block is left unchecked: the request allowed two). Output `workspace/logs/stats/s1017-check-p47r.json`
    (`4b94c8ef…`); the reversed order differs only in the 20 wells listed. Carried into
    [stats/0001](../findings/stats/0001-aggregate.md) (the full-block statement raised to `[C]`) and the
    [stats experiments](../findings/stats/experiments.md#run2026-10-17-stats) record; specs and wiki to the
    spec-writer ([backlog](../backlog/archive/2026-10-20-reverser-spec-writer-stats-full-set-blocks-and-aura-chaining-checked.md)).
  - **The *Fleshripper* log: not copied, re-staged.** The lane's scratch is gone; a scan of the 307 harness logs on
    the machine found none with `e001b03e…` or save `5f440622…` (`workspace/logs/combat/p47r-fleshripper-search.txt`,
    `aef49a11…`, which also holds the rebuild: commit `5871b00`'s recipe still builds `5f440622…`). Session
    `owf-n-andariel-p8` (save `CombatOWF`, that recipe renamed, seed 3712) replaces it; combat/0001 and the combat
    record say so. The resume-lane entry stays open for (b).
  - **Session tools.** `tools/combat_sessions.py`, `tools/stats_sessions.py` and `tools/quest_sessions.py` gain the
    plan's sessions and a `check` command (`tools/session_check.py`: each save built from its recipe into a temporary
    directory and compared with the sha256 pinned in `tools/test_d2s.py`, the case's stats summed over the built
    save's equipped items, the steps file, every `d2pilot.py` option). New tool-built saves on stock rows (ADR-0013
    § Neutral): `CombatDR`, `CombatAbs`, `CombatFrz`, `CombatOWF`, `CombatAma`, `CombatAss`, `CombatAssO`, `StatsSor`,
    `StatsPalD`, `StatsAss`, `StatsDru`, `StatsFloor`, `StatsPot`, `TravelWpArreat`. Dry checks (`SUMMARY` lines; a session serving two cases is
    counted under each): combat 14 cases staged in 31 distinct sessions (36 case entries), 1 not staged, 0 problems (`workspace/logs/combat/p47r-sessions-check.txt`, `6aacdf45…`); stats 6
    staged in 25 sessions, 2 not staged, 0 problems (`workspace/logs/stats/p47r-sessions-check.txt`, `b6a7e854…`);
    travel 1 in 6 sessions, 0 problems (`workspace/logs/quests/p47r-sessions-check.txt`, `a5726f20…`).
  - **Case list** (session, or the reason it cannot be staged):

    | case | sessions | staged by |
    |---|---|---|
    | crushing blow on champions | `ow-nm-champs1`…`6` | `CombatOW` (crushing blow 45) in Nightmare, `farm` bosses first (the champion flag), `/players 8` |
    | cold cap | `sorh-n-darkwood`, `sorh-n-lostcity` | `CombatSorH` (cold and lightning resistance 120 each) in Normal (no penalty); cold attackers by MonStats `El*Type` and missiles |
    | lightning cap | `sorh-n-marsh`, `sorh-n-oasis`, `sorh-n-catacombs` | as above, lightning attackers |
    | **magic cap** | — | **not staged:** no stock source of player magic resistance (stat 37) reaches 75. No unique, set item, affix, runeword, gem, skill or state writes it (`grep -l -w` over the excel tables: only `itemstatcost`, `properties` and `cubemain`); the one writer is the crafted Safety Shield recipe (`res-mag` 5–10), which `tools/d2s.py` cannot build with its recipe mods |
    | magic immunity | `sorh-h-lostcity1`…`3` | `CombatSorH`'s Ginther's Rift (magic damage) on the Hell Lost City's Plague Bearers (`zombie5`, `ResMa(H)` 100) |
    | negative absorbed amount | `dr-n-plains`, `dr-n-darkwood` | `CombatDR`: MDR 108 above every Normal field, then percent absorb (Dwarf Star fire 15, Raven Frost cold 20) on the negative field |
    | negative total, life unchanged | `dr-n-plains`, `dr-n-darkwood`, `dr-n-marsh` | `CombatDR`: DR 36, MDR 108 |
    | evade | `ama-n-run`, `ama-n-walk`, `ama-n-walk2` | `CombatAma` (Evade 20) moving: running, then walking after the run/walk key |
    | weapon block | `ass-n-plains`, `ass-n-plains2`, `asso-n-plains` | `CombatAss` (Weapon Block 20, two claws) and `CombatAssO` (one claw): `0x0057DD60` (0x0057DDAB–0x0057DDB4) rolls only when `0x0064F380` gives 13 for the current mode; what 13 stands for is unread (if a weapon class: WeaponClass row 13 is `ht1`, one claw, or `ht2`, two, without the "None" row), so both are staged and the run's `WBS` oracle tells |
    | dodge, avoid | `ama-n-stand` | `CombatAma` (Dodge 20, Avoid 20) standing in melee and under missiles |
    | freeze | `frz-n-plains`, `frz-nm-plains` | `CombatFrz`: Frostwind (stat 134 = 4) |
    | flat absorb | `abs-n-plains`, `abs-n-darkwood`, `abs-n-marsh`, `abs-nm-marsh` | `CombatAbs`: fire 15, cold 11, lightning 40 flat; Nightmare for fields above the absorb |
    | a walking player's block | `ama-n-walk`, `ama-n-walk2` | `CombatAma` with a shield after the run/walk key (mode 2); whether the key holds mode 2 under attack shows in the `DRM` lines |
    | the *Fleshripper* session | `owf-n-andariel-p8` | `CombatOWF`, above |
    | shrines and wells | `sor-shrines1`…`10`, `palc-wells1`, `palc-wells2` | `StatsSor` (life 1 500 of 6 000, mana 500 of 3 000) over ten field waypoints, a wait past the re-arm, the shrines again; `StatsPalC` poisoned at wells (the cure). Which shrine types appear is the map's draw |
    | an aura state's end | `pald-auras1`, `pald-auras2` | `StatsPalD`: Might, Defiance, Prayer switched by key, 30 switches a session |
    | 300 expiries | `pot-town1`…`4` | `StatsPot`: 56 potions a session drunk so each timed state ends before the next of its kind (about 55 freed lists a session) |
    | different-state group clears | `sor-armours`, `ass-fade`, `dru-shapes` | the Sorceress armours (group 1), Fade and Quickness (group 2), the Druid's shapes (group 3); whether the skill path calls `STATE_GroupClear` is phase 3's, the `GRP` lines tell |
    | the 256 floor | `floor-poison1`, `floor-poison2` | `StatsFloor`: life 30 of 3 000, DR 58 (Normal hits take nothing), poisoned in the Spider Forest and the Far Oasis, no potion |
    | **open wounds on the player** | — | **not staged:** stat 135 is written only by item properties (gems, runes, sets, cube recipes); no MonStats, MonProp or MonUMod cell names it, so only another player wounds a player: two clients (plan 0044) |
    | the curse resistance cut | `ass-curses1`, `ass-curses2` | `StatsAss` under Fade 20 (`curse_resistance`, `aurastat5`, the only stock writer) among the Worldstone Keep 1's witches (`succubuswitch2`: Amplify Damage, Weaken), Normal |
    | **attract** | — | **not staged:** no MonStats `Skill` cell names Attract (the name is in `skills.txt` only), so only another player's curse: two clients (plan 0044). *Review 2026-10-20: reason refused;* Attract is a Necromancer curse (skills.txt Id 86, `charclass` nec), and the refusal tests the target (`STATE_ApplyTimed`, stats/0002 § 1), so a Necromancer staged single-client reaches it on a monster: Phase 2's first step |
    | waypoint activation from mode 0 | `x-wpact5r-0`…`5` (`tools/quest_sessions.py`) | the reading and the route below |

  - **`InitFn` 17 and the route** ([quests/0002 § 2](../findings/quests/0002-travel.md#2-waypoint-activation), `[I]`,
    static): a preset waypoint is created with its preset's mode, 0 for every object (`PresetUnitSpawn` →
    `PresetUnitDispatch` → `SUnitCreate`'s mode argument, stored at unit `+0x10` before `OBJ_ServerInit`), and
    `OBJINIT_Waypoint` changes it only for a room the arrival list names (mode 1) or a town room (mode 2); it never
    reads the waypoint record. So a waypoint whose room is built on foot or through a warp stays in mode 0, held or not.
    Route: `TravelWpArreat` (towns and the Arreat Plateau) arrives at the Plateau by waypoint, then LvlWarp 71, 74, 74,
    71 down through the Crystalline Passage, the Glacial Trail, the Frozen Tundra and the Ancients' Way, four Act V
    waypoints (rows with `Sync` 0) per map seed; six seeds.
  - **Not done here:** no session was run (slots 1 and 2 are plan 0044's); the `≤ 0` delivery counter is Phase 2's.
    `tools/test_d2s.py` has one failure that predates this lane (`h2afind`, plan 0038 H2a's recipe, has no
    `RECIPE_BASES` row); the 14 new recipes are pinned there.
- **2026-10-20 — Phase 1 review (architect, `lane/p47r` at `0678bc3`, `main` merged): accept with fixes (2).**
  Re-run on the review's side: `tools/test_stats.py` 15 tests OK (`tools/stats.py` `98538acf…`, `tools/test_stats.py`
  `d7d6b0c6…` as cited); `tools/stats.py check` over the 18 logs of `s1017-run.lst` gives a JSON byte-identical to
  `s1017-check-p47r.json` (`4b94c8ef…`; 0 mismatches, `aura_chained_pairs` 746, `aura_chain_breaks` 115,
  `aura_drawing_runs_without_next_run` 4; the printed report differs from `s1017-check-p47r.txt` only by the
  `systemd-run` scope line); the three dry checks give outputs byte-identical to the kept ones (`6aacdf45…`,
  `b6a7e854…`, `a5726f20…`; combat 14 staged / 1 unstaged / 36 session entries, stats 6 / 2 / 25, travel 1 / 0 / 6,
  0 problems each); `tools/test_d2s.py` 45 tests OK after fix 3. Anchors spot-checked in `re/symbols.csv`
  (`OBJINIT_Waypoint`, `PresetUnitSpawn`, `PresetUnitDispatch`, `SUnitCreate`, `OBJ_ServerInit`, `g_ObjInitFns`,
  `RoomIsTown`, `PROP_Func24_ParParam`, `PropParamCell`, `PROP_WriteStat`, `SetBonusApply`, `COMBAT_AvoidRoll`); the
  skill check `0x0064F380` is unnamed (an `[L]` in combat/0001, the staging names it as unread: correct).
  - **Fixes:** (1) *misread*: the `attract` reason is refused (case table row above): Attract is a Necromancer curse,
    and `STATE_ApplyTimed` refuses a curse on any target in state 57, so a Necromancer casting Attract on a monster and
    then another curse on it reaches the refusal in one client; it is Phase 2's (Phase 2 *Done when* updated, ruling 2).
    (2) *stale cross-reference*: the stats run record's *Results* still said the 180 full Trang-Oul's lists were taken
    as logged; it now points at the re-check. (3) not the lane's (pre-existing, counted for no lane): `h2afind` pinned
    in `tools/test_d2s.py` from the H2a run record (base `smpbar.d2s`, recipe `d8115721…` as recorded, save
    `38f0fc57…` from `items-tc-saves.sha256`); the build reproduces it.
  - **Ruling 1 (the *Fleshripper* log).** Yes, the case still needs a run, and the new log replaces the lost one.
    skills/0003 answers *which call* applies state 52 (`PreventHealHook` inside `COMBAT_ToHitRoll`), statically, `[I]`;
    the no-draw claim and the event-9 (function 28) modelling need a kept log, and a log nobody can open backs nothing
    (reverser review-fixes 6). `owf-n-andariel-p8` on the byte-identical save is accepted in place of `e001b03e…`
    (the lost log is history, not evidence); with it under `workspace/logs/combat/` and hashed in Phase 2's manifest,
    backlog (a) of the resume-lane entry closes, (b) stays with Phase 2's counter. Plan 0045 Phase 2's oracle
    replacement takes this log whichever lands later: if plan 0045 Phase 2 runs first, its re-check of event 9 and
    state 52 on this session is done by the later lane on the kept log. The combat/0001 bullet stays `[I]` until then;
    the run plus `PreventHealHook` are the two sources that may raise it.
  - **Ruling 2 (the case list).** Accepted with the `attract` change. *Magic cap*: a final shortfall reason (the
    review's `grep -l -w -i 'res-mag\|magicresist'` over the excel tables gives only `itemstatcost`, `properties`
    and `cubemain`, and the one cube row is the Safety Shield craft's `res-mag` 5–10): the cap stays `[I]`, named in
    Phase 3 as unreachable on stock data, homed nowhere. *Open wounds on the player*: accepted, moved to plan
    [0044](done/0044-multiplayer-branches.md) (log entry there; it needs hostility, as plan 0044's hostility case from plan 0042 does).
    *Attract*: not a shortfall; Phase 2's first step, before its first game, adds a Necromancer recipe with Attract
    and one other curse (tool-built, ADR-0013 § Neutral, pinned in `tools/test_d2s.py`), a session that casts Attract
    and then the other curse on the same Normal monster, the `stats_sessions.py check` dry run, and counts the `STA`
    refusals to 30.
  - **Ruling 3 (Phase 2 risks).** (a) *Run/walk key under attack*: the `DRM` mode decides; if no hit lands in mode 2
    in `ama-n-walk`/`-walk2`, one more session at most (a held walk toggle with a ranged attacker), then the walking
    block and the mode-2 evade are named again with the mode-2 hit count; the `÷ 3` exception stays `[I]`. (b)
    *`0x0064F380` = 13*: Phase 2 logs the WBS value per layout; whichever of `CombatAss`/`CombatAssO` rolls weapon
    block decides the case, and the other layout's value is recorded as what 13 is not; if neither rolls, weapon block
    is named again with both layouts' WBS values and the skill check goes to the reverser as a static read (a backlog
    entry, not a third layout). (c) *`STATE_GroupClear` reach*: if the `GRP` lines show none for a group, that group
    is named with its apply count and the claim that the skill path reaches it is withdrawn to `[L]` under *Open
    questions* for Phase 3; no extra session. (d) *Plague Bearers*: a seed whose Hell Lost City holds no `zombie5`
    is replaced, up to six seeds; if none holds them, move to a Hell level with `unraveler*` (ResMa(H) 100, the
    review's MonStats scan: `zombie5`, `brute5`, `unraveler2`–`9`, `megademon6`) before naming magic immunity again.
  - **Ruling 4 (the stats/0001 raise).** Accepted at `[C]`: the code reading (`SetBonusApply`, `PROP_Func24_ParParam`,
    `PropParamCell`) and a full reproduction of the 180 logged lists by the kept checker are two sources, and the
    values are exact (`<< ValShift`, param 176, the `oskill` id and level), so a wrong reading cannot match by chance
    (the review checked the full block holds both `state` `monsterset` and `oskill` Fire Mastery). The broken-member
    bullet stays `[I]`. The specs and wiki are the spec-writer's backlog entry.
  - **Ruling 5 (`InitFn` 17 and the route).** Accepted at `[I]`: a static reading with every hop addressed and the
    preset mode tied to drlg/0004; the route matches Levels' warps. It is raised only by Phase 2's activations from
    mode 0 with the `Sync` 0 draw chained. Plan 0042 closed with this shortfall final, so the travel case applies.
  - **Ruling 6 (`h2afind`).** Fixed here (fix 3); nothing to the archivist.
  - **Phase 2 may start** in the next free harness slot (slot 1: plan 0048 Phase 2; slot 2: plan 0038 H2b), with the
    `attract` staging as its first, static step.
- **2026-10-20 — Phase 1 specs and wiki (spec-writer, `lane/stw`; no game, no Ghidra).** Review requested
  ([backlog](../backlog/archive/2026-10-20-spec-writer-architect-review-lane-stw-stats-full-set-blocks-and.md)). Ruling 4 and
  the re-check's chaining counts carried into the stats specs: [stats/README](../specs/stats/README.md) (boundary row
  *no remainder*, `[I]` → `[C]`; the 746 chained pairs as `tools/stats.py`'s, 115 breaks, 4 with no next run; tags
  C 13 → 14, I 4 → 2, L 3), [stats/aggregate](../specs/stats/aggregate.md) (J4 full Trang-Oul's `[C]`, the
  broken-member set split out `[I]`, the full-block open question struck; tags C 64 → 65, I 42, L 5 → 4),
  [stats/states](../specs/stats/states.md) (§ H note; tags unchanged) and
  [wiki/stats-and-states](../wiki/stats-and-states.md) (`based_on` aggregate 2026-10-20). Open questions: aggregate 5 → 4,
  README 3, states 6. The reverser's entry is closed.
- **2026-10-20 — Phase 1 specs and wiki review (architect, `lane/stw` at `503e72c`, `main` merged: up to date):
  accept with fixes (1, plus 1 not the lane's).** Checked against [stats/0001](../findings/stats/0001-aggregate.md)
  *Answer (summary)* (the raised full-block bullet) and § 9, the [stats experiments](../findings/stats/experiments.md#run2026-10-17-stats)
  *Re-check 2026-10-20* (0 mismatches; `aura_chained_pairs` 746, `aura_chain_breaks` 115,
  `aura_drawing_runs_without_next_run` 4; 746 + 115 + 4 = 865) and ruling 4 above: the J4 full Trang-Oul's bullet and
  the README boundary row are `[C]` on its two sources (the code reading, the checker's reproduction of the 180
  lists), the broken-member set is split out at `[I]`, and the struck open question carries no live tag. Tags
  recounted by script against `main`: README `{C: 13, I: 4, L: 3}` → `{C: 14, I: 2, L: 3}` (the old row held the
  tag cell's `[I]` and a backticked `` `[I]` `` in its text, both counted, both gone), aggregate
  `{C: 64, I: 42, L: 5}` → `{C: 65, I: 42, L: 4}`, states unchanged `{C: 44, I: 47, L: 6}`. Anchors spot-checked in
  `re/symbols.csv`: `SetBonusApply` 0x00660120, `PROP_Func24_ParParam` 0x0065F390, `PropParamCell` 0x006336A0,
  `SKILLS_RollElemDamage` 0x0056E0C0, `RNG_RangeB` 0x0045C3E0. The three stats specs stay `reviewed`.
  - **Fixes:** (1) *overclaim*: the wiki said the 115 next runs "started from a different seed"; the record counts the
    breaks and gives no cause, so the page now says the next run did not start where the last one left the seed and
    that the record does not say why. (2) not the lane's (pre-existing, flagged by the lane): [how-we-know](../wiki/how-we-know.md)
    said plan 0041's specs were not reviewed and no wiki page restated them; it now says they are reviewed and points at
    [stats and states](../wiki/stats-and-states.md).
- **2026-10-21 — Phase 2 landed (reverser, `lane/p47h`; slot 2 only; no Ghidra).** Review requested. The first
  lane ran batches A and B and was killed with every agent by systemd-oomd at 20:12 (no resume note); this lane kept its
  uncommitted `combat_sessions.py` edit (Travincal and Catacombs Level 2 seeds, checked against Levels' rows), re-ran
  the two killed checks and ran the rest. **run:2026-10-20-shortfalls**, one run under three checkers:
  [combat](../findings/combat/experiments.md#run2026-10-20-shortfalls) (31 logs, **0 mismatches over 18 737 events**),
  [stats](../findings/stats/experiments.md#the-stats-sessions-of-run2026-10-20-shortfalls) (10 logs, **0 mismatches**)
  and [travel](../findings/quests/experiments.md#the-travel-sessions-of-run2026-10-20-shortfalls) (1 log, **0
  mismatches over 2 625 checks**); the kept runs re-check unchanged (combat `c37r-run2.lst` 0 / 40 655, stats
  `s1017-check-p47r.json` byte-identical, `tools/test_stats.py` and `tools/test_d2s.py` pass).
  - **Reached** (each ≥ 30, this run): crushing blow on champions 52 (40 in Nightmare; champions carry `0x08` with
    `0x04`, so the checker's "`0x04` and not `0x08`" label was empty on stock spawns and is fixed); the lightning cap
    42; magic immunity 36; the negative absorbed amount 186; the total ≤ 0 with life unchanged 488 (+ 113 at 0; the
    resume-lane counter (b)); evade 31 (46 rolls); weapon block 30 (50 rolls; `WBS` 13 with two claws, 12 with one,
    ruling 3 (b)); dodge 109; avoid 68; freeze 81; flat absorb 113 (fire only; cold and lightning 0); stats: 71 curses
    refused in `attract` (151 made outside it); 120 aura on and off events (61 + 59, the ends by the skill switch);
    43 different-state group clears (groups 1 and 2).
  - **Named again:** the cold cap 4 (27 kept, 31 over the two runs); the walking block 6 in 48 mode-2 events (ruling
    3 (a)'s extra session spent on `amaw-n-walk`); group 3 (12 unchecked clears, no exit line; the skill path's reach
    stays `[I]`; *review 2026-10-21:* not withdrawn to `[L]`, since ruling 3 (c) applies when no call is seen and these
    12 reached `STATE_GroupClear`); the 256 floor 0 (no poison taken);
    the curse resistance cut 0 (no witch curse); expiries 30 (153 with the kept 123, of 300: the potion plan drank no
    inventory potion in three attempts, dev logs kept); shrines and wells 3 (15 with the kept 12, of 50); waypoint
    activation from mode 0: 1 of 20 (the Act V route's warp search fails on most seeds). The magic cap stays
    unstaged (ruling 2).
  - **The *Fleshripper* log** is kept (`workspace/logs/combat/p47h-owf-n-andariel-p8.log`, `a411b34d…`, outside the
    run: 57 mismatches, all the unmodelled event-9 handler, plan 0045 Phase 2); backlog entry
    [resume-lane follow](../backlog/archive/2026-10-17-architect-reverser-plan-0037-resume-lane-review-follow.md)
    closed with (a) and (b).
  - **Tools:** `tools/combat.py` (`--no-shield-log`, the champion label, an attacker's own `MonAttackStats` inside its
    event, the per-label defence-roll counters), `tools/stats.py` (the `Expansion` row of `itemtypes` skipped: the
    claw-mastery param was one high), `tools/d2pilot.py --dead-below`, `tools/stats_sessions.py` (the potion plan's
    inventory key), recipes `CombatAmaD` and `CombatAmaW` (level 5, to-hit above the floor), pinned.
  - **Findings:** [combat/0001 § 16](../findings/combat/0001-formulas.md#16-plan-0047-phase-2-the-shortfalls-run2026-10-20-shortfalls)
    (evade, weapon block, dodge, avoid, crushing blow on champions, the lightning cap, magic immunity, the negative
    field, flat absorb, freeze, prevent-heal's no draw raised to `[C]`; the unusable shield and the in-event
    `MonAttackStats` read `[I]`), [stats/0002 § 9](../findings/stats/0002-states.md#9-plan-0047-phase-2-the-shortfalls-run2026-10-20-shortfalls)
    (the `attract` refusal on monsters, the different-state group clear for groups 1–2, the aura end by the skill
    switch, `[C]`), [quests/0002](../findings/quests/0002-travel.md) (one mode-0 activation, stays `[I]`). Phase 3 may
    start on the counts above.
- **2026-10-21 — Phase 2 review (architect, `lane/p47h` at `2d116b3`, `main` merged at `75ff308`): accept with fixes
  (6, plus 1 not the lane's).** Re-run on the review's side under `systemd-run --user --scope -p MemoryMax=4G`, tools
  as recorded (`tools/combat.py` `bd80126a…`, `tools/stats.py` `23f34c4d…`, `tools/quests.py` `b6dfb1a3…`): the three
  `sha256sum -c` lists (`p47h-logs.sha256` for combat and stats, `p47h-manifest.sha256` for quests) pass; the combat
  check over `p47h-run.lst` with the recorded `--no-shield-log` gives a JSON byte-identical to `p47h-check.json`
  (`4e7ee7a7…`) and the same report (0 / 18 737); the stats check over its `p47h-run.lst` gives `p47h-check.json`
  (`63892df3…`) byte for byte; `tools/quests.py check` on `p47h-x-wpact5r-0.log` gives `p47h-check.txt` byte for
  byte (0 / 2 625); `p47h-owf-n-andariel-p8.log` (`a411b34d…`) gives `p47h-owf-check.json` (`5db67372…`), 57
  mismatches, all `expected AD1, got EVH`, and its 57 `EVH` lines with `fn` `0x005C01D0` are exactly those events;
  `c37r-run2.lst` 0 / 40 655; `s1017-run.lst` byte-identical to `s1017-check-p47r.json`; `tools/test_stats.py` OK;
  `tools/test_d2s.py` 45 OK after fix 7. Spot-read on `Game.exe` (objdump): `0x0057DDAB` calls `0x0064F380` and
  `0x0057DDB0` compares its out-word with 13; `UnitBlockChance`'s player branch (`0x00622791`) returns 0 when
  `sub_0063C8F0_InvItemQuery` gives 0; `0x005CAED3` calls `COMBAT_MeleeHitTest`, so `0x005CAED8` is the attack's
  return; `PreventHealHook` ends at `0x0057D899` with no RNG call (`STATE_ApplyTimed` and stat reads only);
  `0x005702DC` calls `UNIT_UnlinkStatList` (return `0x005702E1`); `STATE_ApplyTimed` pushes 57 at `0x0056EA40`; the
  `Expansion` row is data row 58 of `itemtypes.txt`, so `h2h` is 67 (ItemTypes.md's `[C]` marker rule). Symbols of
  § 16 and § 9 resolve in `re/symbols.csv`.
  - **Fixes:** (1) *omission*: the stats record now says which sessions met the machine suspend (23:17–06:25): no
    run-list log; a first `floor-poison1` launch at 23:15:33 spanned it with no event and is kept as the dev log
    `p47h-floor-poison1.log.failed1` (`06b1601b…`), which the record did not name; `dev-p47h-pot-town2-keyi`'s game
    ended before it. (2) *omission*: the combat record and combat/0001 § 16 state what `--no-shield-log` changes:
    without it, 88 mismatches, all the shield-held block chance against a logged 0 (66 `CombatAss`, 4 `CombatAssO`,
    18 `CombatDR`; `CombatAmaD` passes either way), so the lane's "37 on an Assassin log" was one log of three
    Assassin and three `CombatDR` logs; the claws' 70 are predicted from the recipe, `CombatDR`'s 18 are the logged 0
    taken as input. (3) *miscount*: the kept run's re-check differs from its kept output by five counters, not two
    (the three `≤ 0` delivery counters). (4) *misread*: group 3's reach is not withdrawn to `[L]` (above): ruling 3 (c)
    is for a group with no call, and 12 calls reached `STATE_GroupClear`. (5) *omission*: commit `b7dec78`'s message
    gives a cause (the Pandemonium floor) that the run refuted; the stats record now says so and names `3236965`'s.
    (6) *other*: combat/0001 § 16 cites `0x0063C8F0` by its existing name `sub_0063C8F0_InvItemQuery`. (7) not the
    lane's (pre-existing on `main`, counted for no lane): `h2bjewel` and `h2bthrow` pinned in `tools/test_d2s.py` from
    the H2b record (bases `samples/d2s/smpsor.d2s` and the classic `smpsor.d2s`; saves `03afa56f…` and `b965d6b9…`,
    both rebuilt byte for byte).
  - **Ruling 1 (`--no-shield-log`): a model input, not a mask.** It sets the predicted chance to 0 for a named log and
    nothing else, so a logged chance above 0 still fails and a block roll the game made would break the seed chain; it
    cannot hide a roll. For a recipe with no shield in either hand it is a recipe fact (the code's `0x0063C8F0` test,
    read at `[I]`); for `CombatDR` it takes the logged 0 as given, so those 18 events check nothing about the refusal,
    which stays `[I]` in § 16. A later run list declares the flag from the recipes before the check and names any log
    whose shield the code refuses.
  - **Ruling 2 (the cold cap): met over the two runs.** 4 here and 27 in `c37r-run2.lst`, both re-checked by the same
    checker revision with 0 mismatches, on the one table-row path the fire, lightning and poison caps take: 31, so
    combat/0001 § 16 now raises it to `[C]` (done in this review). The plan's floor is per case, not per run (the
    expiries and shrines already count with the kept run).
  - **Ruling 3 (`CombatAmaD`, `CombatAmaW`, `amaw-n-walk`).** Accepted: stock uniques at their maximum rolls, pinned;
    the stat totals at level 5 are a built state (as `CombatAma`'s), harmless since every stat the model uses is
    logged. `amaw-n-walk` as ruling 3 (a)'s one extra session is accepted (the cause was the to-hit floor, not the
    mode); with 6 the walking block is **final** at `[I]`.
  - **Ruling 4 (the in-event `MonAttackStats`, the drop past the cap).** Accepted at `[I]`: the inner call is checked
    as its own `mas` event, its exit stats feed the build as a value oracle (as at `EV0`), its entry seed is asserted
    (5 in this run, 6 over the 71 logs); the 8 dropped events are counted in `ma` and checked nothing. Which events
    call it is unread: carried to plan [0045](0045-skills-missiles-machinery.md) (its monster skill uses with
    `MonAttackStats` predicted; log entry there).
  - **Ruling 5 (the stats checker's item-type fix, `--dead-below`, the potion key).** The index fix follows
    ItemTypes.md's `[C]` marker rule and moves no kept-run value (byte-identical re-check). `--dead-below` changes the
    pilot only (its default stays 0.05); with 0 the death stop is off, so a session using it must find a death in its
    log: neither `floor-poison` session died (80 hops each, the character moving). The potion plan's one key press
    is a staging change behind dev logs only.
  - **Ruling 6 (the *Fleshripper* log).** Accepted outside the run: it is the kept replacement (Phase 1 ruling 1),
    hashed in `p47h-manifest.txt`; its 57 mismatches are one cause, the unmodelled event-9 handler, each located by its
    `EVH` line. Plan 0045 Phase 2's oracle replacement takes it (log entry there); combat/0001's event-9 bullet stays
    `[I]`.
  - **Ruling 7 (the raises).** combat/0001 § 16: evade, weapon block, dodge and avoid, crushing blow on champions, the
    lightning cap and magic immunity, the negative field and the total ≤ 0, fire flat absorb, freeze and prevent-heal's
    no draw stand at `[C]` (code reading plus a 0-mismatch reproduction, every case above 30; the evade-by-mode
    "never" is separated by the same characters rolling dodge and avoid in other modes); the cold cap added by ruling
    2; the weapon-block skill value, open wounds' `0x0C`, the unusable shield and the in-event `MonAttackStats` stay
    `[I]`. stats/0002 § 9: the `attract` refusal on monsters (71 of 71 refused, 151 of 151 made), groups 1–2 (43) and
    the aura end by the skill switch (59, return `0x005702E1` read) stand at `[C]`, each split from its remainder.
    quests/0002: one activation, stays `[I]`.
  - **Ruling 8 (Done-when and what carries forward).** Phase 2 meets its *Done when* for every combat case and for
    `attract`, the aura end and groups 1–2. The cases named again for staging reasons (shrines and wells with ten
    staged sessions unrun, the expiries behind an unexplained potion-plan failure, the 256 floor and the curse cut with
    one of two sessions run, group 3's missing exit line, the travel route's warp search) do not give the stock-data
    reason the TL;DR asks for, so they are not final: they move to **Phase 2b** of this plan (added above), with cold
    and lightning flat absorb (`abs-nm-marsh` unrun). Final now: the walking block (6), the magic cap (unstaged).
    **Phase 3 may start** on combat and on the stats cases reached here; the Phase 2b counts reach the specs after it.
- **2026-10-21 — Phase 3 landed for combat and the reached stats cases (spec-writer, `lane/s47p3`; static, no game,
  no Ghidra).** Review requested ([backlog](../backlog/archive/2026-10-21-spec-writer-architect-review-lane-s47p3-plan-0047-phase-3-re.md)).
  Re-tagged from run:2026-10-20-shortfalls per rulings 1, 2, 7 and 8, each raised statement citing the run:
  [combat/to-hit](../specs/combat/to-hit.md) (C3's four rolls on a player defender, prevent-heal's no draw, the
  `--no-shield-log` scope; the walking block 6 final at `[I]`, the unusable shield and the skill check 13/12 `[I]`;
  tags `{C: 33, I: 27, L: 3}` → `{C: 39, I: 30, L: 5}`), [combat/reductions](../specs/combat/reductions.md) (magic
  immunity, the lightning cap, the cold cap over two runs, fire flat absorb, the negative absorbed amount; the magic
  cap final at `[I]`; `{C: 40, I: 25, L: 4}` → `{C: 45, I: 24, L: 5}`), [combat/delivery](../specs/combat/delivery.md)
  (the total ≤ 0, crushing blow on champions, freeze on a melee hit; `{C: 52, I: 54, L: 4}` → `{C: 59, I: 49, L: 3}`),
  [combat/damage](../specs/combat/damage.md) (the in-event `MonAttackStats`, `[I]`; `{C: 34, I: 29, L: 4}` →
  `{C: 34, I: 30, L: 5}`), [combat/README](../specs/combat/README.md) (the run's boundary paragraph, the champion
  1/8, the shortfall bullet rewritten; `{C: 36, I: 42, L: 5}` → `{C: 38, I: 42, L: 5}`),
  [stats/states](../specs/stats/states.md) (`attract` on a monster target, groups 1–2, the aura end by the skill
  switch; group 3, the curse cut, the 256 floor, expiries 153, shrines and wells 15 named for Phase 2b;
  `{C: 44, I: 51, L: 6}` → `{C: 47, I: 52, L: 6}`), [stats/README](../specs/stats/README.md) (`{C: 14, I: 3, L: 3}` →
  `{C: 15, I: 3, L: 3}`), [quests/travel](../specs/quests/travel.md) (one dated `[I]` note, 1 of 20; `{C: 74, I: 84,
  L: 4}` → `{C: 74, I: 86, L: 4}`). Open questions (live `[L]`): to-hit 3 → 5, reductions 4 → 5, delivery 4 → 3,
  damage 4 → 5, README 5, states 6, stats/README 3, travel 4. Wiki: [combat](../wiki/combat.md),
  [stats and states](../wiki/stats-and-states.md), [quests](../wiki/quests.md) (`based_on` 2026-10-21) and
  [how we know](../wiki/how-we-know.md). The research map rows are asked of the architect in the review request.
  The Phase 2b counts reach the specs after Phase 2b.
- **2026-10-21 — Phase 3 review (architect, `lane/s47p3` at `0a9a615`, `main` merged at `c70ef30`): accept with fixes
  (3: overclaim 2, misread 1).** Every raised `[C]` checked against combat/0001 § 16, stats/0002 § 9, the two run
  records and the Phase 2 review: evade 46 (31), weapon block 50 (30), dodge 172 (109), avoid 103 (68), the moving
  player's evade-only rolls scoped to the run's modes; prevent-heal's no draw 271; magic immunity 36; the lightning cap
  42; the cold cap 4 + 27 = 31 over the two runs (ruling 2); fire flat absorb 113; the negative absorbed amount 186;
  the total ≤ 0 488 + 113 + 32 = 633; crushing blow `k` = 4 on champions 52; freeze 81 up to the nested delivery;
  `attract` 71/71 and 151/151 with 239 requests draw-free; groups 1–2 43 (20 + 23); the aura end 59 of 61, 120 on and
  off events. Each cites run:2026-10-20-shortfalls and is split from what stays `[I]` (the mode-2 exception, the
  skill value 13/12, a monster defender's modes, the shield test's "usable" in the pseudocode, the missile terms of
  E3, D3 inside the nested delivery, the curse cut, group 3 at `[I]` not `[L]`). `--no-shield-log`'s 88 (70 claws,
  18 `CombatDR` taken from the logs) is stated as ruling 1 has it, and its `[C]` in to-hit C2 is a run-scope note
  like the boundary paragraphs. The community 1/8 on champions is refuted by the run plus the code, as the evidence
  rules allow for a contradiction; both pages are registered (`purediablo-mechanics` 1.10-era,
  `fextralife-d2r-crushing-blow` D2R) and combat/0001 § 13 already records them `contradicted`, so `docs/sources.md`
  needs no change. The final shortfalls (walking block 6, magic cap) and the Phase 2b items are named; `[L]` only
  under *Open questions* (E5 green); the Mermaid edges ("aura skill switch") restate F4. Wiki pages: no claim of their
  own beyond the fixes below, `based_on` dates equal the specs' `updated:` (no W4). The lane's two notes are upheld:
  flat absorb's heal stays `[I]` (but see fix 1) and D3's freezing stays `[I]`. Tag counts recounted with the gate
  (E6 green).
  - **Fixes:** (1) *overclaim*: reductions B3 dropped the `[I]` that scoped "both the percent and the flat amounts are
    healed" to the percent, leaving the flat heal under a `[C]` that 32 percent heals carry; the 113 flat hits assert
    the field, not the heal (as the lane's own delivery note and the wiki say). An `[I]` sentence restores the split
    (`{C: 45, I: 25, L: 5}`). (2) *misread*: the new `[C]` E1 bullet called `0x08` "the unique flag"; it is the
    special flag that `MonMarkSpecial` sets on every champion-pack member before the champion roll sets `0x04`
    ([monsters/spawn § G](../specs/monsters/spawn.md#g-the-special-group-boss-champion-or-unique)), which is why no
    stock champion has `0x04` alone. The bullet now cites `sub_005A0320_MonMarkSpecial`, and the label is corrected in
    delivery's state table, D1 (the stun test therefore covers champions), E2, its Mermaid line and the wiki's
    crushing-blow, open-wounds and stun text; no tag changes. (3) *overclaim*: combat/README's struck shortfall bullet
    said "Reached …" after a struck list that holds the walking block and the magic cap; it now says which were not
    reached.
  - **Bookkeeping (the reviewer's):** research map rows for `combat/formulas` (C 215 / I 176 / L 23 summed),
    `stats/states` (C 47 / I 52 / L 6; stats/0002 {C 19, I 55, L 8}) and `quests/travel` (C 74 / I 86 / L 4, a stale
    C 73 / I 82 corrected) rewritten whole; the 2026-10-17 shrine, well and aura-end addendum entry closed as moved
    (its (b) and groups 1–2 of (c) reached here, (a) and group 3 carried by Phase 2b); the review request closed.
  - **Can the plan close?** Not yet, and only for Phase 2b: Phases 1, 2 and 3 (for Phase 2's counts) meet their
    *Done when*; Phase 2b and the re-tag of its counts remain, after which the plan closes.
- **2026-10-21 — Phase 2b landed (reverser, `lane/p47b`; slot 2 only; no Ghidra).** Review requested.
  **run:2026-10-21-shortfalls2**, one run under three checkers, each **0 mismatches**:
  [stats](../findings/stats/experiments.md#the-stats-sessions-of-run2026-10-21-shortfalls2) (14 logs, `tools/stats.py`
  `85e14b94…`), [combat](../findings/combat/experiments.md#run2026-10-21-shortfalls2) (3 logs, 2 527 events,
  `tools/combat.py` `ee628bbe…`), [travel](../findings/quests/experiments.md#the-travel-sessions-of-run2026-10-21-shortfalls2)
  (8 logs, 9 300 checks, `tools/quests.py` unchanged). The kept runs re-check unchanged: stats `s1017-run.lst` and
  `p47h-run.lst` byte-identical JSONs; combat `p47h-run.lst` 0 / 18 737 (one new counter, 30) and `c37r-run2.lst`
  0 / 40 655; `tools/test_stats.py` (18) and `tools/test_d2s.py` (45) pass.
  - **The Done-when items** (this run, and with Phase 2's and the kept runs' counts):

    | item | this run | in all | |
    |---|---:|---:|---|
    | 300 expiries | 296 | 449 | met; the potion plan fixed first (dev session `dev-p47b-pot1`) |
    | 20 group-3 clears checked | 24 | 24 (67 over groups 1–3) | met; stats logger rev 10 writes the nested call's exit, checker and tests |
    | the curse resistance cut | 54 | 54 | met (Crystalline Passage succubi, Defense Curse; Fade's 84) |
    | the 256 floor | 0 | 0 | **final**: stock data (below) |
    | 50 shrine or well operates | 6 | 21 | **final**: tool reason, fix tried |
    | 20 waypoint activations from mode 0 | 6 | 7 | **final**: tool reason, fixes tried |
    | lightning flat absorb | 51 | 51 | met |
    | cold flat absorb | 1 | 1 | **final**: the Done-when's condition (`abs-nm-marsh` run), not stock data (review) |

  - **Fixes, each found in a log:** the potion plan did drink; its 8 s waits were sized at 25 frames a second and the
    game runs at about 17 under the stats logger, so each healing potion refreshed the last one's list instead of
    linking a new one (the cube token `frames:N` waits on the log's frame). `STATE_GroupClear` is re-entered (Werebear's
    clear of Werewolf calls it for 139), and the rev 9 logger's single open call lost the outer exit (rev 10 keeps a
    stack with the depth). The Act V route named LvlWarp ids where the WRP lines number records (id 71 = records 71/72,
    id 74 = 76/77; record 74 is Ice Caves Up, which took `x-wpact5r-0` back to the Plateau); `descend` gains a
    breadth-first path before skipping a room; `activate`'s Escape opened the game menu when no waypoint list was up
    (its Save and Exit ended two games). `StatsAss` has no Teleport, so the Worldstone Keep route cannot go up; the
    Crystalline Passage's succubi curse instead. `StatsFloor`'s experience is level 86's threshold (any experience
    levels it up and fills life: all five floor logs of both phases), hence `StatsFloorB`. The shrine hunt explored
    nothing between its operates. The combat checker started a draining monster's drain from its `AD0` life after the
    player's lightning thorns had cut it (one mismatch in `abs-nm-marsh`): it now takes the defender handler's `EVR`.
  - **Final, with reasons** (Phase 2b's rule: named again with a stock-data or a tool reason, the fix tried):
    the 256 floor 0: the only stock items that keep a 30-life Paladin alive in a poisoner's field (flat damage
    reduction 58) also carry `regen` (*Kerke's Sanctuary*), poison length (*The Gladiator's Bane*) and poison resistance
    (*Nature's Peace*); the stock items with flat reduction and none of these reach about 50 (the record's scan), below
    the 58 the recipe uses so that Normal hits take nothing; regeneration raised life to 267 before the first poison
    (`floorb-poison2`). Not tried: a character without those items at more life, where poison alone would have to
    drain it to the floor. Cold flat absorb 1: the cold rows that roll their
    element (Travincal's `cantor3`, `vampire2`) gave 13 melee attacks, all misses; the Act I cold rows have an empty
    `El1Pct`. Shrines and wells 21 of 50: about one operate per 12-minute explore-and-operate session in the Act I
    fields; the re-arm and a well's cure unreached. Waypoint activations 7 of 20: about one per 5–15 minutes once the
    route was fixed; the Passage's maze stops the four-waypoint route after its first waypoint.
  - **Tools:** `tools/gdb/stats.py` rev 10, `tools/stats.py` (nested group-clear pairing, `apply_curse_cut`),
    `tools/test_stats.py` (18 tests), `tools/combat.py` (the attacker's life after a defender handler),
    `tools/d2pilot.py` (`frames:N`, `--done` with several tags, `descend`'s path), `tools/stats_sessions.py`,
    `tools/combat_sessions.py` and `tools/quest_sessions.py` (the sessions above), recipe `statsfloorb.json` pinned
    in `tools/test_d2s.py`.
  - **Findings:** [stats/0002 § 10](../findings/stats/0002-states.md#10-plan-0047-phase-2b-the-staging-limited-cases-run2026-10-21-shortfalls2)
    (the curse cut on the player, group 3, the 300 expiries `[C]`; the floor and shrines `[I]`, final),
    [combat/0001 § 17](../findings/combat/0001-formulas.md#17-plan-0047-phase-2b-flat-absorb-by-element-run2026-10-21-shortfalls2)
    (lightning flat absorb `[C]`; the leech after a defender handler `[I]` at the review, one separating event; cold `[I]`, final),
    [quests/0002](../findings/quests/0002-travel.md) (7 activations, the operate stays `[I]`; the warp ids and records).
    Phase 3 may re-tag on these counts.
- **2026-10-21 — Phase 2b review (architect, `lane/p47b` at `6cf1ec2`; `main` not merged): accept with fixes (5:
  overclaim 3, misread 1, omission 1).** Re-checked with the lane's tools (hashes as recorded: `tools/stats.py`
  `85e14b94…`, `tools/combat.py` `ee628bbe…`, `tools/quests.py` `b6dfb1a3…` unchanged) under `MemoryMax=4G`: stats
  `p47b-run.lst` 0 mismatches, its JSON byte-identical to `p47b-check.json`; combat 0 / 2 527, JSON byte-identical;
  quests `SUMMARY mismatches=0 checks=9300 logs=8`, the text equal but for systemd's scope line; the three `p47b-*`
  manifests pass `sha256sum -c`. Kept runs: stats `s1017-run.lst` and `p47h-run.lst` byte-identical to
  `s1017-check-p47r.json` and `p47h-check.json`; combat `p47h-run.lst` (its recorded `--no-shield-log`) differs from
  `p47h-check.json` in the one new counter (30) only, `c37r-run2.lst` 0 / 40 655 with no new counter, its text equal
  to `c37r-run2-check-rbs-2026-10-17.txt` but for the label and `≤ 0` counters the Phase 2 review already recorded.
  `tools/test_stats.py` (18) and `tools/test_d2s.py` pass. Counts recomputed from the kept outputs: expiries 296
  (`expired_lists`), 449 with 153; group 3 24 at depth 1 with 24 nested (`p47b-grpclear.txt`), 67 with 43; curse
  cuts 54 (`apply_curse_cut`; 52 + 1 + 1 in `p47b-cursecut.txt`); shrines 6 (`shrine` 6: 4 applied, 2 refills), 21
  with 15; lightning flat absorb 13 + 25 + 13 = 51, cold 1; activations 1 + 0 + 1 + 1 + 1 + 1 + 1 + 0 = 6, 7 with
  Phase 2's.
  - **Fixes:** (1) *overclaim*: stats/0002 § 10 said the three curse lengths rule out "another rounding"; `len · 84`
    is a multiple of 100 for 275, 3 600 and 2 400 (cuts 231, 3 024, 2 016 exactly), so no case separates `MulDiv`'s
    rounding from truncation: the `[C]` is the cut, the rounding stays `[I]`. (2) *overclaim*: combat/0001 § 17
    raised "the leech after a defender's handler" to `[C]` on "29 events here and 30 in `p47h-run.lst`, each `LE1`
    equal to `EVR` plus the drain"; the counter counts events whose `EVR` life differs from the model's, and an
    instrumented copy of the checker (scratch, not kept) shows only 8 of the 59 followed by a leech, all in this run,
    of which the previous revision's single mismatch (line 6 763) is the only one that separates the readings. `[I]`,
    the checker's correction kept (a value oracle as the handler is, firing only when the logged life differs; it
    cannot hide a mismatch elsewhere). (3) *overclaim*: the 256 floor's "stock data" reason holds for the staged route
    only (a 30-life character kept alive by flat reduction); the lane itself names a route not tried (more life,
    poison alone): scoped in § 10 and the stats record. (4) *misread*: the plan table gave cold flat absorb's reason
    as stock data; Travincal's cold rows gave 13 attacks, all misses, and Nightmare/Hell cold rows were untried; it is
    final under the Done-when's own condition (`abs-nm-marsh` run). (5) *omission*: the shrine and well "tool reason"
    did not say the yield rests on one session (`sor-shrines2`) and that `palc-wells2` was not run, so the well's cure
    was not tried in this phase: stated in § 10 and the record.
  - **Rulings on the final items.** (a) *The 256 floor, 0*: final at `[I]` on the code reading and the checker's
    test; the fixes tried (poisoner fields, `StatsFloorB` after the level-86 experience bug) each found the next
    obstacle; the untried higher-life route is out of this plan, not a stock-data limit. (b) *Shrines and wells, 21 of
    50*: final at `[I]` as a slot-time ruling: the staging fault (no exploration) is fixed and shown working, and at
    about one operate per 12 minutes the 29 missing cost about six slot hours for a draw-free path that 21 operates
    already check with 0 mismatches; the re-arm and a well's cure leave this plan unreached (out of this plan). (c)
    *Waypoint activations from mode 0, 7 of 20*: final at `[I]`, a tool reason with the fixes tried (the LvlWarp id vs
    WRP record numbering, `activate`'s Escape, the Highlands route), the yield measured over eight sessions. (d)
    *Cold flat absorb, 1*: final at `[I]` (fix 4); `COMBAT_Absorb` is the one table-row path, but one case is under
    the floor.
  - **The checker and route changes.** `tools/combat.py`'s change is a model correction with a value oracle, not an
    oracle that takes the checked value: it replaces the attacker's starting life only where the defender handler's
    logged `EVR` life differs, and the leech's gain, the cap and the `LE1` life are still predicted. The quest route's
    record numbering and `activate`'s Escape are pilot changes; `tools/quests.py` is unchanged, so Phase 2's one
    activation (checked under the same revision) stands, and the travel finding's ids-vs-records note corrects only
    the sessions' description. The stats rev 10 pairing leaves the rev 9 logs' reports byte-identical.
  - **Raises upheld:** stats/0002 § 10 the curse cut on a player (r 1..99, rounding `[I]`), group 3 (24, the nested
    call's caller unfollowed), the 300 expiries; combat/0001 § 17 lightning flat absorb (51); quests/0002 stays `[I]`.
  - **Phase 2b closes.** Every Done-when item is met or named again, final, with a reason the review accepts above.
    Spec-writer entry filed for the Phase 3 re-tag of the 2b counts
    ([backlog](../backlog/archive/2026-10-21-architect-spec-writer-plan-0047-phase-3-re-tag-the-phase.md)); the review request
    closed. **Can the plan close?** After that re-tag's review: Phases 1, 2, 2b and 3 (for Phase 2's counts) meet
    their *Done when*.
- **2026-10-21 — Phase 3 landed for the Phase 2b counts (spec-writer, `lane/s47p3b`; static, no game, no Ghidra).**
  Review requested ([backlog](../backlog/2026-10-21-spec-writer-architect-review-lane-s47p3b-plan-0047-phase-3-re.md));
  the re-tag entry closed ([backlog](../backlog/archive/2026-10-21-architect-spec-writer-plan-0047-phase-3-re-tag-the-phase.md)).
  Re-tagged from run:2026-10-21-shortfalls2 as the Phase 2b review rules, each raised statement citing the run:
  [stats/states](../specs/stats/states.md) (B1 the curse resistance cut on a player target, `r` 1..99, 54, with
  `MulDiv`'s rounding, the refusal at 100 and a negative `r` split out at `[I]`; D1 group 3, 24, 67 over groups 1–3,
  the nested call's caller `[I]`; C1 the 300 expiries, 449 over three runs; the 256 floor (0) and shrines and wells
  (21 of 50) final at `[I]`, out of the plan; G6's stale "stamina shrine not reached" corrected, code 14 was operated
  twice in run:2026-10-20-shortfalls; `{C: 47, I: 52, L: 6}` → `{C: 51, I: 53, L: 6}`),
  [stats/README](../specs/stats/README.md) (the run's boundary paragraph; `{C: 15, I: 3, L: 3}` → `{C: 16, I: 3, L: 3}`),
  [combat/reductions](../specs/combat/reductions.md) (B3 lightning flat absorb 51 `[C]`; cold 1, final at `[I]`;
  `{C: 45, I: 25, L: 5}` → `{C: 46, I: 25, L: 5}`), [combat/delivery](../specs/combat/delivery.md) (C1 the leech
  after a defender's event 1/5 handler, `[I]` on one separating event; E4's floor count; `{C: 80, I: 63, L: 3}` →
  `{C: 80, I: 64, L: 4}`), [combat/README](../specs/combat/README.md) (the run's boundary paragraph with the
  checker's value oracle, the named-again bullet rewritten whole; `{C: 38, I: 42, L: 5}` → `{C: 39, I: 42, L: 5}`),
  [quests/travel](../specs/quests/travel.md) (C1's note rewritten: 7 of 20 activations from mode 0, final, `[I]`;
  the spec names no Act V LvlWarp id, so no id/record note; tags unchanged `{C: 74, I: 86, L: 4}`). Open questions
  (live `[L]`): states 6, stats/README 3, reductions 5, delivery 3 → 4, combat/README 5, travel 4. Wiki:
  [stats and states](../wiki/stats-and-states.md), [combat](../wiki/combat.md), [quests](../wiki/quests.md)
  (`based_on` already 2026-10-21, the specs' `updated:`), [how we know](../wiki/how-we-know.md) (the further pass and
  its final shortfalls). The research map rows are asked of the architect in the review request.
