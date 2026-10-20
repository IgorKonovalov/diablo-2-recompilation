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
    and off events; 300 expiries in total with the kept run; 20 different-state `group` clears; open wounds on the
    player; the curse resistance cut;
  - travel (after 0042 closes, if still short): 20 waypoint activations from mode 0, with the object-seed draw
    chained (ADR-0014).

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
    spec-writer ([backlog](../backlog/2026-10-20-reverser-spec-writer-stats-full-set-blocks-and-aura-chaining-checked.md)).
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
    | **attract** | — | **not staged:** no MonStats `Skill` cell names Attract (the name is in `skills.txt` only), so only another player's curse: two clients (plan 0044) |
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
