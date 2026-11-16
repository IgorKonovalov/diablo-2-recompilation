# Combat — runtime experiments

Runs of plan 0037 Phase 2 (per-event reproduction, ADR-0014). Harness and evidence rules: ADR-0003, ADR-0004,
ADR-0011, ADR-0014; [tooling](../../../.claude/skills/reverser/references/tooling.md),
[harness-play](../../../.claude/skills/reverser/references/harness-play.md).

## run:2026-10-16-combat

- **Question:** plan 0037 Phase 2. Does `tools/combat.py`, the model of [combat/0001](0001-formulas.md), reproduce
  every logged attack event draw for draw: the to-hit roll, the defence rolls, the damage build, the reductions, the
  delivery with crushing blow, open wounds, leech, cold and the life change, the missile hits, the El draws of
  `MonAttackStats` and the stat-74 tick, with every logged seed asserted? Boundary (Phase 1 review rulings 3, 5, 6):
  stat values are value oracles (ADR-0014); a skill's or missile's packet is an input; the handlers other than
  crushing blow and open wounds, `COMBAT_DurabilityLoss`, the knockback, `COMBAT_GetHit` and the monster on-hit skill
  `0x005A4390` are boundary oracles (ADR-0004: entry seeds asserted, exits taken); events with a progressive-charge
  hook (`PRG`) are dropped (none occurred).
- **Setup:** agent-driven sessions on harness slot 3 (display `:10`, prefix `workspace/wineprefix-3`), single player,
  pinned `game.exe` in `workspace/runtime/game` (stock data), gdb by `tools/d2run.py` with `-seed` per session.
  Logger `tools/gdb/combat.gdb` (`450f36f8…`) sourcing `tools/gdb/pilot.py` (`1ad48a4c…`, unchanged) and
  `tools/gdb/combat.py` in nine revisions, each session's given below; r4 and later write a `COMBATLOG {"rev": N}`
  line. r1 `1e2f23b` (`99301064…`); r2 = r3 without the `c4` unit field, never committed; r3 `b5f5b2d` (`46dfdfa6…`:
  `DRB`/`DRM` inside missile events, unit `+0xC4`); r4 `03dc463` (`c90fd7a9…`); r5 `f9c183b` (`5d3f791a…`); r6
  `fc5d0be` (`942c8e14…`: `MH0`/`MH1`); r7 `ac1038a` (`c4618ea2…`: the monster regeneration event `0x005A6920`); r8
  `d293013` (`782e95dd…`: base stat 74 at the tick); r9 `98426bc` (`82780acc…`: no reverse `COMBAT_ApplyDamage`). r4 and
  r5 tried to open the tick window on `0x00580610` (the player's tick) and wrote no `RGN` line; the monster tick is
  `0x005A6920`, logged from r7, asserted from r8. Breakpoints only print and continue. Per-session caps (ruling 6):
  player attack 800, monster attack 500, hireling attack 300, `MonAttackStats` 300, missile defence 300, player missile
  300; the tick window ≤ 250 frames after an open-wounds or poison application, one at a time, ≤ 30 per session.
  Driver `tools/combat_sessions.py` (sessions, pilot commands and seeds in its `SESSIONS` table) over
  `tools/d2pilot.py farm`/`hunt`/`explore` with the new `--melee-button 3` (Attack on the right button, Teleport on
  Shift + left). Each session: `saves.py --slot 3 restore`/`aside c37`, `d2run.py --install c37`, the pilot steps,
  `slots.py stop 3`.
- **Characters** (ADR-0013 § Neutral: tool-built from stock uniques; no test-state key): `CombatSor`
  (`combatsor.json`, expansion Sorceress clvl 85, *Ginther's Rift*, *Steelclash*, *Rockstopper*, *Rockfleece*,
  *Venom Grip*, *Goldwrap*, *Gorerider*, *Nokozan Relic*, *Raven Frost*, *Manald Heal*; Act V Barbarian mercenary
  Id 24, level 80; `1d9de374…`), `CombatSolo` (`combatsolo.json`, the same without the mercenary, `a2a64d72…`),
  `CombatBar` (`combatbar.json`, Barbarian on `smpbar.d2s`, same items, `107f3ac1…`), `CombatCls`
  (`combatclassic.json`, classic Sorceress: *Blood Crescent*, *Steelclash*, *Tarnhelm*, *Rockfleece*, *Magefist*,
  *Goldwrap*, *Goblin Toe*, *Nokozan Relic*, *Manald Heal*, *The Stone of Jordan*; `8e1625b2…`). The items carry
  crushing blow, deadly strike, open wounds, life and mana leech, fire, cold, lightning, poison and magic damage, DR,
  MDR, physical resist, cold % absorb and fire maximum resist; none carries a stat-event handler outside 14–16.

### Sessions

| session | seed | save | difficulty | where | logger | pa | ma | ha | md | pm | MAS |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| sor-n-plains | 3711 | CombatSor | Normal | Cold Plains | r1 | 81 | 36 | 160 | 10 | 0 | 300 |
| sor-n-andariel | 3712 | CombatSor | Normal | Catacombs 2–4, Andariel killed | r2 | 47 | 38 | 116 | 15 | 0 | 277 |
| solo-h-p3 | 3734 | CombatSolo | Hell, /players 3 | Cold Plains | r3 | 187 | 500 | 0 | 56 | 0 | 300 |
| sor-h-andariel | 3732 | CombatSor | Hell | Catacombs 2–3 (Andariel not reached) | r4 | 130 | 500 | 61 | 203 | 0 | 300 |
| solo-nm-p8 | 3723 | CombatSolo | Nightmare, /players 8 | Cold Plains | r6 | 246 | 500 | 0 | 81 | 0 | 300 |
| sor-nm-andariel | 3722 | CombatSor | Nightmare | Catacombs 2–3 (not reached) | r7 | 125 | 89 | 186 | 74 | 0 | 300 |
| solo-h2-p3 | 3735 | CombatSolo | Hell, /players 3 | Stony Field | r8 | 130 | 428 | 0 | 300 | 0 | 300 |
| solo-n-p8 | 3713 | CombatSolo | Normal, /players 8 | Cold Plains | r9 | 105 | 249 | 0 | 20 | 0 | 300 |
| nova-h-immune | 3751 | CombatSor | Hell | Frigid Highlands, Nova | r9 | 0 | 500 | 157 | 261 | 300 | 300 |
| cls-nm-plains | 3761 | CombatCls | classic Nightmare | Cold Plains | r9 | 196 | 420 | 0 | 97 | 0 | 300 |
| cls-h-plains | 3762 | CombatCls | classic Hell | Cold Plains | r9 | 169 | 500 | 0 | 66 | 0 | 300 |
| solo-nm2-p8 | 3724 | CombatSolo | Nightmare, /players 8 | Stony Field | r9 | 220 | 394 | 0 | 37 | 0 | 300 |
| solo-h3 | 3736 | CombatSolo | Hell | Dark Wood | r9 | 142 | 21 | 0 | 300 | 0 | 300 |
| sor-n-p2 | 3742 | CombatSor | Normal, /players 2 | Stony Field | r9 | 40 | 18 | 103 | 1 | 0 | 178 |
| sor-nm-andariel-nova | 3727 | CombatSor | Nightmare | Catacombs 2–4, Nova, Andariel killed | r9 | 0 | 43 | 164 | 107 | 219 | 300 |
| sor-h-andariel-nova | 3737 | CombatSor | Hell | Catacombs 2–3, Nova (no way down found) | r9 | 0 | 30 | 103 | 0 | 0 | 122 |
| sor-n-highlands | 3715 | CombatSor | Normal, /players 8 | Frigid Highlands | r9 | 127 | 71 | 209 | 300 | 0 | 300 |
| sor-nm-highlands | 3725 | CombatSor | Nightmare, /players 4 | (no event: the session never left town) | r9 | 0 | 0 | 0 | 0 | 0 | 0 |
| bar-n-plains | 3771 | CombatBar | Normal | Cold Plains, walking | r9 | 85 | 196 | 0 | 29 | 0 | 283 |

`bar-n-plains` ran twice; the first log (40 player attacks, 0 mismatches; its explore stopped on a missing screenshot
directory) was overwritten by the second, which is the one kept. Not part of the run: the calibration log
`workspace/logs/combat/smoke-s3-3701-normal.log` (the first logger, whose `THV` pct read `EDX` before its load).
Run list `workspace/logs/combat/c37p2-run.lst` (`9eb62a78…`, 19 logs, 46 MB), per-file sha256 in
`workspace/logs/combat/c37p2-manifest.txt` (`e7dff751…`); checker output `c37p2-check.txt` (`d1c34b1a…`) and
`c37p2-check.json` (`c4695a49…`), from `tools/combat.py` at `9d91e1d` (`2eb46ee6…`).

### Procedure and result

1. `python3 -I tools/combat_sessions.py run --slot 3 --tag c37 --saves <dir> --run c37p2 <sessions>` (three batches).
2. `python3 -I tools/combat.py check $(cat workspace/logs/combat/c37p2-run.lst) --json …/c37p2-check.json` (under
   `systemd-run --user --scope -p MemoryMax=4G`): **0 mismatches over 15 358 events**.

| kind | events | checked to exit | checked to the last line (deferred delivery overtaken) | N / NM / H | hits / misses |
|---|---:|---:|---:|---|---|
| player attack `pa` | 2 030 | 2 030 | 0 | 485 / 787 / 758 | 1 644 / 386 |
| monster attack on the player or the mercenary `ma` | 4 533 | 4 505 | 28 | 608 / 1 446 / 2 479 | 697 / 3 836 |
| mercenary attack `ha` | 1 259 | 994 | 265 | 588 / 350 / 321 | 1 005 / 254 |
| missile on the player or the mercenary `md` | 1 957 | 1 957 | 0 | 375 / 396 / 1 186 | |
| the player's Nova missile `pm` | 519 | 519 | 0 | 0 / 219 / 300 | |
| `MonAttackStats` | 5 060 | 5 060 | 0 | | 167 with an El applied |

Resynchronisations inside events (named, entry taken as logged): a delivery on a later frame than the hit test (362
at `COMBAT_ApplyDamage` entry, 112 at the exit with no delivery, 1 early return whose reason is not logged; the AI drew
on both seeds in between; 216 of those queued packets were changed by the mercenary's skill before delivery, taken as
input), and 7 monster skill do-functions that drew between the hit test and the build (seed taken at the build). In the
sessions logged before r6 (no `MH0`/`MH1`), the monster on-hit skill `0x005A4390` is crossed by taking the attacker's
seed at `AD1` (630 events); from r6 it is a boundary oracle with its entry seed asserted (2 132).

Chained pairs (ruling 5; the second event's entry seed equal to the first's predicted exit) on the player's seed, as
first / as second: `pa` 1 796 / 1 808 (213 resynchronised), `ma` 4 235 / 4 226 (51), `md` 1 505 / 1 503 (196), `pm`
519 / 518 (0). On a monster's seed, `MonAttackStats` → its attack: 2 237 (`ma`) and 558 (`ha`), 96 resynchronised.
Every kind passes the floor of 20 on both ends.

Cases (checker counts): to-hit with `ToHitFactor` 1 889 Sorceress (−15) and 85 Barbarian (+20) attacks, AR and DEF
checked at `THB`; block 2 243 (divided by 3 for a moving player 26; the player's chance against its formula 2 523
expansion, 395 classic); the builder's `RangeB(1)` in all 3 732 builds, the build on 386 misses; deadly strike 250;
resistance applications fire 2 803 (381 at the cap, 268 immune), cold 1 386 (15 / 158), lightning 930 (17 / 72),
poison 1 374 (2 / 73), magic 1 340 (0 / 0), physical 3 544; DR, MDR or absorb non-zero 1 747; percent absorb healing
the player 32; leech 364 / 681 / 455 (N / NM / H) with 1 500 `Range(2)` overlay draws; monster drain 7; crushing blow
on normal monsters 247, uniques 63, superuniques 5, an act boss 1, at /players 1, 2, 3, 8: 147, 5, 40, 124; open
wounds 246 applications, the bleed ending at application frame + 200 in all 11 windows logged across their end; the
stat-74 tick 6 181 checked (233 before r8 not asserted), 5 881 without natural regeneration under a life-flag state;
the hireling boss percent 50 (Normal, 2 events) and 35 (Nightmare, 78); the prime-evil percent 200 once; classic
events 616 (Nightmare) and 669 (Hell), the classic penalty on the player 138 / 208; stun rolls on uniques 17; the
monster `Crit` doubling 89; running player hit without a roll 26.

**Shortfalls** (named, not blocking; their claims stay `[I]`; completed by the architect review below): the **hireling boss percent in Hell** (25, against
`MonsterCEDamagePercent` 20): Andariel was not reached in Hell in two attempts; two further sessions
(`sor-h-andariel-nova2`, `-nova3` in `SESSIONS`) were not run for lack of time. **Open wounds on an act boss**: none
(the two Andariel kills had no open-wounds hit on her). **Crushing blow on an act boss** 1 event, **on a superunique**
5, **on a champion** 0 as labelled (the checker labels a unit with the unique bit first). **Evade, weapon block,
dodge, avoid**: 0 (no character had those stats). **Conversion, freeze and the freeze handler, pierce, flat absorb,
the PvP 17 % and the hireling-against-hireling 25 %, magic at or above the cap, magic immunity**: not reached. **The
player's stat-74 tick** (`0x00580610`): no window on the player. `MonAttackStats`: 167 El applications, but only
its draws are modelled, not the stats it writes, so monsters/stats § H stays `[I]` for its outputs.

- **Conclusion:** the claims of [combat/0001](0001-formulas.md) reproduced here move to `[C]` (§ 15 of the finding),
  each naming its value oracles; the shortfalls above keep theirs at `[I]` (run:2026-10-16-combat).

#### Architect review, 2026-10-16

Re-run read-only in the lane worktree after merging `main`: the 19 logs match `c37p2-manifest.txt` (sha256 and size);
`python3 -I tools/combat.py check $(cat workspace/logs/combat/c37p2-run.lst) --json …` under `systemd-run --user
--scope -p MemoryMax=4G` prints `SUMMARY mismatches=0 events=15358`, and its text and JSON output are identical to
`c37p2-check.txt` and `c37p2-check.json`; `tools/combat.py`, `tools/gdb/combat.gdb` and `tools/gdb/combat.py` hash as
recorded. Corrections: `ha` checked to exit is 994 (not 993); the logs hold 7 669 to-hit rolls (`THR`) in 7 822 melee
events. Branches that reproduced but stay under the plan's rare-branch floor of about 30, so stay `[I]` (finding
§ 15, last bullet): crushing blow on an act boss (1) and a superunique (5), the prime-evil percent 200 (1), the
negative absorbed amount (4), the monster drain branch (7), the stun draw on a unique (17), and the resistance cap
reached for cold (15), lightning (17) and poison (2); fire reaches it 381 times and the cap is one path over the
table rows (run:2026-10-16-combat). Verdict in the [plan log](../../plans/done/0037-combat-formulas.md#implementation-log).

#### Resume lane addendum, 2026-10-16

Phase 2 review ruling (c) ([plan 0037](../../plans/done/0037-combat-formulas.md#implementation-log)): the shortfalls of
Hell's hireling boss percent, open wounds on an act boss and crushing blow on act bosses and superuniques. Same run id,
same harness rules, on slot 2 (display `:9`, `workspace/wineprefix-2`), logger r9 unchanged (`tools/gdb/combat.gdb`
`450f36f8…`, `tools/gdb/combat.py` `82780acc…`). Driver `tools/combat_sessions.py` (`a140aecb…`) with new sessions
and two pilot changes in `tools/d2pilot.py` (`95dd71c5…`): `descend` stays on its breadth-first path once it has one
(a path step away from the warp followed by a greedy hop back had shuttled between two cells for a whole search), and
`--merc-drink F` gives the mercenary a belt potion (Shift + column key) when its `MON` life falls below F of the most
seen. A descend step of an Andariel session is skipped once the player stands in level 37, and up to four descend
steps run, so one failed search no longer leaves the hunt a level short. Nothing the pilot computes feeds a model.

- **Characters** (tool-built on `smpsor-l50.d2s`, stock uniques, no test-state key): `CombatSorH`
  (`combatsorh.json`, `CombatSor` with *Venomsward*, *The Ward*, *Mara's Kaleidoscope*; Act V Barbarian mercenary
  in unique gear) in three revisions of the mercenary's gear: rev1 *Shadowfang*, *Duriel's Shell*, *Vampiregaze*
  (`5a8f4677…`, session `sorh-h-andariel`); rev2 *Shadowfang*, *Venomsward*, *Wormskull* (`ac12b7b4…`, sessions 2–5);
  rev3 *The Atlantian*, *Venomsward*, *Wormskull* (`210b2c0c…`, sessions 6–10; the recipe file holds rev3).
  `CombatOW` (`combatow.json`, `CombatSolo` with *The Gnasher*, *Boneflesh*, *Steelrend*: open wounds 85 %, crushing
  blow 40 %; `b07db91b…`). Each log's header names the installed save's sha256.
- **Seeds:** every Hell Andariel session uses map seed 3738 (the layout `sor-h-andariel-nova2` had already crossed;
  3791 put the player in a pack at the waypoint twice); the Normal Andariel sessions 3712 (as `sor-n-andariel`), the
  Nightmare one 3727, Frigid Highlands 3783 and 3785. /players 8 for every `CombatOW` session, 1 for the Hell ones.

| session | seed | save | difficulty | where | pa | ma | ha | md | pm | MAS | target counts |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| sor-h-andariel-nova2 | 3738 | CombatSor | Hell | Catacombs 2–4, Nova; the mercenary died before Andariel, the player at her | 0 | 408 | 58 | 232 | 300 | 300 | — |
| sorh-h-andariel | 3738 | CombatSorH rev1 | Hell | Catacombs 4, Andariel | 0 | 309 | 177 | 300 | 300 | 300 | hireling boss 4 |
| sorh-h-andariel2 | 3738 | CombatSorH rev2 | Hell | died in level 36 | 0 | 185 | 91 | 300 | 300 | 300 | — |
| sorh-h-andariel3 | 3738 | rev2 | Hell | Catacombs 4, Andariel | 0 | 500 | 85 | 221 | 300 | 300 | 0 |
| sorh-h-andariel4 | 3738 | rev2 | Hell | Catacombs 4, Andariel | 0 | 442 | 122 | 300 | 300 | 300 | 6 |
| sorh-h-andariel5 | 3738 | rev2 | Hell | Catacombs 4, Andariel | 0 | 500 | 109 | 266 | 300 | 300 | 0 |
| sorh-h-andariel6 | 3738 | rev3 | Hell | Catacombs 4, Andariel | 0 | 162 | 76 | 294 | 300 | 300 | 0 |
| sorh-h-andariel7 | 3738 | rev3 | Hell | Catacombs 4, Andariel | 0 | 411 | 30 | 117 | 94 | 300 | 3 |
| sorh-h-andariel8 | 3738 | rev3 | Hell | Catacombs 4, Andariel | 0 | 182 | 125 | 176 | 300 | 300 | 1 |
| sorh-h-andariel9 | 3738 | rev3 | Hell | Catacombs 4, Andariel | 0 | 462 | 102 | 300 | 300 | 300 | 3 |
| sorh-h-andariel10 | 3738 | rev3 | Hell | Catacombs 4, Andariel | 0 | 265 | 215 | 232 | 300 | 300 | 16 |
| ow-n-andariel-p8 | 3712 | CombatOW | Normal, /players 8 | Andariel killed | 132 | 309 | 0 | 113 | 0 | 300 | OW boss 15, CB boss 11 |
| ow-n-andariel2-p8 | 3712 | CombatOW | Normal, /players 8 | Andariel killed | 257 | 500 | 0 | 182 | 0 | 300 | OW boss 9, CB boss 3 |
| ow-n-andariel3-p8 | 3712 | CombatOW | Normal, /players 8 | Andariel killed | 254 | 500 | 0 | 300 | 0 | 300 | OW boss 12, CB boss 5 |
| ow-n-andariel4-p8 | 3712 | CombatOW | Normal, /players 8 | Andariel killed | 262 | 500 | 0 | 247 | 0 | 300 | OW boss 15, CB boss 8 |
| ow-nm-andariel-p8 | 3727 | CombatOW | Nightmare, /players 8 | Catacombs 2–3 (not reached) | 510 | 500 | 0 | 223 | 0 | 300 | — |
| ow-n-highlands-p8 | 3783 | CombatOW | Normal, /players 8 | Frigid Highlands, Eldritch | 163 | 255 | 0 | 300 | 0 | 300 | CB superunique 12 |
| ow-n-highlands2-p8 | 3785 | CombatOW | Normal, /players 8 | Frigid Highlands | 213 | 160 | 0 | 300 | 0 | 300 | CB superunique 5 |

"Hireling boss" counts the mercenary's hits on Andariel that reach `COMBAT_ApplyReductions` (`RDP` P = 25); its
attacks on her were about three times as many (misses and blocks). In Hell the mercenary (life about 1 400) usually
reached Andariel after fights on the way and lasted seconds against her; the potion option helped from session 4 on.

**Not part of the run** (set aside under the lane's scratch, with the reason): two `CombatSorH` attempts at seed 3791
(an Energy Shield build that drained the mana Teleport needed, and a build whose shield had been put in the glove
slot; the player died at the waypoint both times); a `CombatOW` revision with *Fleshripper* and *Dracul's Grasp*
(`5f440622…`) whose Normal Andariel session gave 133 mismatches, all "expected `DRB`": *Fleshripper*'s prevent-heal
applies state 52 between the to-hit roll and the block roll, which the checker does not model (open question in
[combat/0001](0001-formulas.md#open-questions)); its first session at seed 3781 was overwritten by the rerun of the
same name; and a Nightmare Frigid Highlands session stopped one minute in by the lane.

**Checker change** (`tools/combat.py` `77c63ef5…`): a state applied by a third unit (a monster's curse on the
mercenary, state 9) between a deferred hit test and its delivery is dropped as foreign, like the other foreign lines
of that gap (one event in `sorh-h-andariel5`). Re-run over the first run's 19 logs: output identical to
`c37p2-check.txt` (`SUMMARY mismatches=0 events=15358`).

**Result.** Run list `workspace/logs/combat/c37r-run.lst` (`644074fd…`, the 19 logs of `c37p2-run.lst` and the 18
above, 37 logs); new logs' sha256 in `c37r-manifest.txt` (`5a8217d3…`, 68 MB). `python3 -I tools/combat.py check
$(cat workspace/logs/combat/c37r-run.lst) --json …/c37r-check.json` under `systemd-run --user --scope -p
MemoryMax=4G`: **`SUMMARY mismatches=0 events=37786`** (`c37r-check.txt` `0fc6ec35…`, `c37r-check.json` `24de2285…`):
player attacks 3 821, monster attacks 11 083, mercenary 2 449, missile defence 6 360, Nova 3 613, `MonAttackStats`
10 460. Chained pairs on the player's seed (first / second): `pa` 3 446 / 3 462, `ma` 10 510 / 10 487, `md` 5 386 /
5 392, `pm` 3 608 / 3 609; on a monster's seed `MonAttackStats` → `ma` 4 263, → `ha` 1 035.

| target (floor about 30) | first run | whole run list now | |
|---|---:|---:|---|
| hireling boss percent, Hell (P 25) | 0 | **33** | met |
| open wounds on an act boss | 0 | **51** | met |
| crushing blow `k` = 8 on an act boss | 1 | 28 | short |
| crushing blow on a superunique | 5 | 22 | short |
| crushing blow on a champion (labelled) | 0 | 0 | not reached |
| prime-evil percent 200 | 1 | **154** | met |
| monster drain branch | 7 | **80** | met |
| stun draw on a unique | 17 | **34** | met |
| resistance at the cap: cold / lightning / poison | 15 / 17 / 2 | 27 / 17 / **692** | poison met |
| negative absorbed amount | 4 | 4 | short |

*Fire at the cap, added 2026-10-17 (`lane/rbs`, plan 0037 close follow-up (a)):* `python3 -I tools/combat.py check
$(cat workspace/logs/combat/c37r-run2.lst)` re-run (tool sha256 `d4dfed41…22c53b43c`; output
`workspace/logs/combat/c37r-run2-check-rbs-2026-10-17.txt`, `dc63aab8…f17f5b983`): `SUMMARY mismatches=0
events=40655`, `resist application fire at cap: 2115` (cold 27, light 17, poison 692, as above).

- **Conclusion:** the branches marked met move to `[C]` in [combat/0001 § 15](0001-formulas.md) (bullet *Resume
  lane*); crushing blow on an act boss (28) and a superunique (22), cold and lightning at the cap and the negative
  absorbed amount stay `[I]` with their counts. One more Normal Andariel session (about 8 crushing blows on her) and
  one more Frigid Highlands session would close the crushing-blow pair; the lane stopped at the owner's deadline for
  the machine. (run:2026-10-16-combat)

#### Resume lane, second sessions, 2026-10-17

The crushing-blow pair left short above. Same run id, slot 2, logger r9 unchanged (`tools/gdb/combat.gdb`
`450f36f8…`, `tools/gdb/combat.py` `82780acc…`), `tools/d2pilot.py` unchanged (`95dd71c5…`); driver
`tools/combat_sessions.py` `54984ffc…` (two more Andariel rows and one Frigid Highlands row, same steps as their
predecessors). Save `CombatOW` (`b07db91b…`, the recipe revision of the addendum above), /players 8, Normal.

| session | seed | where | pa | ma | md | MAS | target counts |
|---|---:|---|---:|---:|---:|---:|---|
| ow-n-andariel5-p8 | 3712 | Catacombs 4; Andariel seen about 50 cells away, never reached (the hunt timed out) | 147 | 206 | 99 | 300 | — |
| ow-n-highlands3-p8 | 3786 | Frigid Highlands; boss class 453 killed, class 481 seen | 265 | 209 | 219 | 300 | CB superunique 33 |
| ow-n-andariel6-p8 | 3712 | Andariel killed | 189 | 438 | 197 | 300 | CB boss 6, OW boss 12 |

`ow-n-andariel5-p8` has no event on Andariel but checks with 0 mismatches, so it stays in the run list.

**Checker change** (`tools/combat.py` `d4dfed41…`): a state-52 (`preventheal`) `STA` line of the attacker between
the to-hit and the defence rolls is skipped without a draw, and the defence line after it is no longer dropped as
foreign. No log of the run list has such a line (the case counter is absent from the output), so the run's output
is unchanged by it. On the set-aside *Fleshripper* session (above) it removes all 133 "expected `DRB`" mismatches;
101 remain, all "expected `AD1`, got `EVH`" at an event-9 handler `0x005C01D0` (open question in
[combat/0001](0001-formulas.md#open-questions)). That session stays out of the run.

**Result.** Run list `workspace/logs/combat/c37r-run2.lst` (`12d53ed1…`, `c37r-run.lst` plus the three logs above,
40 logs); the new logs' sha256 in `c37r2-manifest.txt`. `python3 -I tools/combat.py check $(cat …/c37r-run2.lst)
--json …/c37r2-check.json` under `systemd-run --user --scope -p MemoryMax=4G`: **`SUMMARY mismatches=0
events=40655`** (`c37r2-check.txt` `dc63aab8…`, `c37r2-check.json` `25f5f1bd…`): player attacks 4 422, monster
attacks 11 936, mercenary 2 449, missile defence 6 875, Nova 3 613, `MonAttackStats` 11 360. Chained pairs on the
player's seed (first / second): `pa` 4 045 / 4 063, `ma` 11 362 / 11 337, `md` 5 901 / 5 907, `pm` 3 608 / 3 609; on
a monster's seed `MonAttackStats` → `ma` 4 655, → `ha` 1 035.

| target (floor about 30) | after the first addendum | whole run list now | |
|---|---:|---:|---|
| crushing blow `k` = 8 on an act boss | 28 | **34** | met |
| crushing blow on a superunique | 22 | **55** | met |
| crushing blow on a champion (labelled) | 0 | 0 | not reached |
| open wounds on an act boss | 51 | 63 | met (already) |
| block `/3`, player moving and not walking | 43 | **48** | met |
| running player hit without a to-hit roll | 42 | **47** | met |
| resistance at the cap: cold / lightning | 27 / 17 | 27 / 17 | short |
| resistance at the cap: fire (added at the plan 0037 close, 2026-10-17) | — | **2 115** | met |
| negative absorbed amount | 4 | 4 | short |

- **Conclusion:** crushing blow `k` = 8 on an act boss and on superuniques moves to `[C]` in
  [combat/0001 § 15](0001-formulas.md) (bullet *Resume lane, second sessions*). The block `/3` and the running
  player's hit without a roll were already above the floor after the first addendum (43, 42) but were not raised
  there; they move to `[C]` in the same bullet. Champions, cold and lightning at the cap, the negative absorbed
  amount and a total ≤ 0 stay `[I]`. Slot 2 stopped, its saves restored empty. (run:2026-10-16-combat)

#### Architect review of the resume lane, 2026-10-17

Re-run read-only in the lane worktree after merging `main`. The 40 logs of `c37r-run2.lst` (`12d53ed1…`) match the
three manifests (`c37p2-manifest.txt` 19, `c37r-manifest.txt` 18, `c37r2-manifest.txt` 3: sha256, size and line
count); every `CombatOW` log header names save `b07db91b…`, and the `CombatSorH` logs name the three revisions as the
addendum lists them. `python3 -I tools/combat.py check $(cat workspace/logs/combat/c37r-run2.lst) --json …` with
`tools/combat.py` `d4dfed41…` under `systemd-run --user --scope -p MemoryMax=4G`: `SUMMARY mismatches=0
events=40655`, text and JSON output byte-identical to `c37r2-check.txt` and `c37r2-check.json`. The checker has no
unit tests (`tools/test_*.py` has no combat module); the run list is its test.

Counts read at the review (the same checker, with a scratch counter wrapped around `openwounds` and `resist_for`,
and a scan of the `EV0`/`DRM` lines; no new run):

- **Running player.** Monster attacks on a player in mode 3: 47 with a `DRB` and no `THR`, 0 with a `THR`, 30 that
  ended before any defence line. `DRM` `mv` was set in mode 3 only (47 melee, 1 missile), never in another mode, and
  no attack on a walking player (mode 2) was logged. All 48 `/3` events divide the capped chance: 45 expansion at
  75 → 25, 3 classic at 53 → 17.
- **Open wounds.** 1 880 applications: 383 on monsters with type flag `0x08` (Andariel 63 with `f` = `0x08`; other
  uniques 320, 87 of them with `0x04` as well), all at half the band; 1 497 on monsters without `0x0C`, at the full
  band; 0 on a monster with `0x04` and not `0x08`; 0 on a player.
- **Resistance floor.** 214 resistance applications on the player at exactly −100 before the floor, none below.
- **Set-aside *Fleshripper* session** (lane scratch, sha256 `e001b03e…`, not in the run): 861 events, 133 state-52
  `STA` lines skipped, 101 mismatches, the first 60 printed all "expected `AD1`, got `EVH`". *2026-10-20 (plan 0047
  Phase 1):* the log is lost with the lane's scratch (`workspace/logs/combat/p47r-fleshripper-search.txt`,
  `aef49a11…`); the session is re-staged as `owf-n-andariel-p8` on the same recipe ([combat/0001 *Open
  questions*](0001-formulas.md#open-questions)).

- **Conclusion:** the lane's raises hold, scoped in [combat/0001 § 15](0001-formulas.md) to what the logs show: the
  `/3` and the automatic hit are `[C]` for a running player; the mode-2 exception stays `[I]`. Open wounds on
  Andariel are halved, by her unique flag, not taken in full as the finding had said; the unique half of the `0x0C`
  test is `[C]` (383), the champion half `[I]` (0); the −100 floor changed no logged value and stays `[I]`.
  Verdict in the [plan log](../../plans/done/0037-combat-formulas.md#implementation-log). (run:2026-10-16-combat)

#### Addendum 2026-11-15: plan 0066 batch S5a, part 1 (new checks over the kept combat and skills logs, `lane/n66j`)

A new check over the kept logs, no game. Tool `tools/sweep2_s5a.py` (`104ce037…`): its `combat` section reruns
`tools/combat.py`'s `Checker` unchanged over `c37r-run2.lst` (40 logs, c37p2 and c37r), `p47h-run.lst` (31, with the
recorded `--no-shield-log`) and `p47b-run.lst` (3), and on every event the Checker accepts adds the S5a counters and
nine new checks; `skills` counts the owner-seed steps of each `MC0`/`MC1` creation of run:2026-10-25-skills; `handlers`
counts each outermost `EVH`..`EVR` handler call's unit-seed steps in run:2026-10-25-skills and run:2026-10-27-skills.
Outputs under `workspace/logs/n66j/`: `check-combat.txt` (`8301a8c5…`, 422 lines), `check-skills.txt` (`c17d62f4…`),
`check-handlers.txt` (`f51b54c2…`), `manifest.sha256` (`f7ddd85e…`, passes `sha256sum -c` from that directory);
development outputs in `dev/` with `manifest-dev.sha256`. Static reads with r2 (the second tool after Ghidra) on the
pinned image.

- **The Checker on the union:** 0 mismatches over 74 logs (pa 6 901, ma 19 017, ha 3 174, md 8 638, pm 4 409, MAS 19 780
  events). **The nine new checks: 0 bad** (`S5a total bad=0 checker=0`): `burn-plain` 10 951 builds with `burnLen` 0
  at `BD1` and no state-115 `STA`; `conv-zero` 10 951 `BD0` packets with byte `+0x65` and dword `+0x68` at 0;
  `evh-order` 5 540 (no delivery held both a hit and a get-hit handler, so the order itself is not separated); `md-block` 10 387 missile events with physical 0 and no block draw, 6 838 of them in the 30 logs
  where another missile was blocked; `miss-nodef` 12 161 missed to-hit rolls with no defence roll after them;
  `mon-leech-strict` 8 876 monster attacks whose `LE1` attacker seed equals the `AD0` one (the Checker's own drain
  model met 276 monster drains, Nightmare 19 and Hell 257); `sta-52` 509 state-52 `STA` lines with length 120 000, stat 31, value 0, all from a
  player attacker; `steal` 462 deliveries whose defender mana at `AD1` is the `AD0` mana minus the packet's mana steal,
  0 below 256 (226 on the player, 236 on monsters; no stamina steal logged). [C] (run:2026-10-16-combat,
  run:2026-10-20-shortfalls, run:2026-10-21-shortfalls2)
- **Entry points.** `EV0` return addresses (`check-combat.txt`, `ev0-ret`): `SKILL_AttackDo` 0x0056F156 (pa 6 901),
  `MON_MeleeHit` 0x005A54C8 (ma 18 735, ha 1 318), `sub_005D7EA0_SkillSt32Hit` 0x005D7F42 (ha 1 068),
  `sub_005DB2D0_SkillDo07MeleeHit` 0x005DB371 (231), `sub_005CAE40_SkillSt42FireHit` 0x005CAED8 (3),
  `sub_005DA940_SkillSt06Hit` 0x005DA9B4 (1). No return lies in `sub_005D9C80_MonSkillAttackDo`, which reaches the hit
  test through `MON_MeleeHit`: r2 reads its calls, in order, `sub_005A4F50_MonAttackStats` (0x005D9C95),
  `MON_MeleeHit` (0x005D9C9F), `COMBAT_DeliverQueued` (0x005D9CAC), then 0x006445E0 and 0x00644620. [C] for the call
  order (fn:sub_005D9C80_MonSkillAttackDo@0x005D9C80, r2 and Ghidra)
- **The packet copy.** `COMBAT_QueueHit` copies the packet with `mov ecx, 0x1C; rep movsd` (0x0057CAE1–0x0057CAE6):
  28 dwords, 0x70 bytes, the size the logger reads and the Checker compares at `BD1` and `AD0`. [C] for the size and
  the whole copy (fn:COMBAT_QueueHit@0x0057CA80, r2 and Ghidra); the callers' zeroing was not read here. [I]
- **Late deliveries:** 789, queued by `SkillSt32Hit` (788) and `SkillSt42FireHit` (1), delivered 6 frames (787) or 9
  (2) after the hit test, resynchronised at `AD0`. [C] (run:2026-10-16-combat, run:2026-10-20-shortfalls)
- **No difficulty term in the chance to hit, the block, crushing blow or open wounds.** `THR` per difficulty and game
  type: Normal 12 019, Nightmare 4 940 + 607 classic, Hell 9 211 + 664 classic, with the chance strictly between 5
  and 95 in 1 502, 3 546 and 9 814 of them; block rolls 2 204, 1 678 and 7 869; crushing-blow and open-wounds handler
  calls 3 102, 1 662 (160 classic) and 675 (126 classic). Every chance and every handler's life result is asserted by
  a model with no difficulty term. [C] (fn:COMBAT_ToHitRoll@0x0057D9B0, fn:STATEVENT_CrushingBlow@0x005BFFC0,
  run:2026-10-16-combat)
- **The result word at delivery** (`AD0 result word`): melee 0x1, 0x3, 0x5, 0x7, 0x9, 0xB, 0xD, 0xF, 0x2005, 0x2007;
  missile 0x1, 0x5, 0xD and **0x4001 (537)**, a bit the to-hit spec's list does not name. Blocked, dodged, avoided,
  evaded and weapon-blocked hits deliver nothing, so 0x10, 0x80, 0x100, 0x200 and 0x8000 are not in any logged
  packet. Each `DRR` line is a roll, not a success: the one missile evade roll with a delivery (`p47h-ama-n-walk`,
  frame 2549) failed and delivered 0x5. [C] for the bits listed (run:2026-10-16-combat); [I] for the others
- **Defence rolls per event:** the defender 0 (29 243), 1 (12 000) or 2 (61); the attacker's `THR` 0 or 1; no event
  drew three times. A running player defender drew the block without a to-hit roll in 135 events. [C]
  (fn:COMBAT_DefenceRoll@0x0057DFB0, run:2026-10-16-combat)
- **The builder.** 10 951 builds (player 6 901, hireling 1 787, monster 2 263) with `BD1` asserted whole. The
  mastery crit and stat 141 both above 0 in 144 builds (the mastery drawn first). 981 doublings, every one with an
  element field non-zero and left undoubled. No monster build had stat 21 below 1 or 22 below 2 and every player held
  a weapon, so the unarmed clamp is not reached; no build carried an event-3 handler. [C] for the counts
  (run:2026-10-16-combat)
- **A monster's missile and the crit doubling:** 7 734 md events from monsters with MonStats `Crit` above 0, the
  owner's step asserted at `MSX`. [C] (0x005AD884, run:2026-10-16-combat)
- **Mercenaries:** 519 Hell `ha` leeches with steal fields checked by the model without the divisors (`LE1`); 79 hits
  on Andariel at P 35 (53) and 25 (26) with the steal fields unscaled; 191 hits on champions, uniques and superuniques
  that are not MonStats `boss` at P 100; 1 787 builds with no drain draw (the build's seeds asserted). [C]
  (fn:sub_0063EE90_HirelingType@0x0063EE90, fn:MONSTATS_IsBoss@0x0063E9F0, run:2026-10-16-combat)
- **Absorb and the zero floor:** 794 absorb heals on the player asserted at `AD1` (flat fire 372, lightning 51, cold 1;
  percent 371); 635 negative and 864 zero totals leaving life unchanged. [C] (fn:COMBAT_Absorb@0x0057BF10,
  fn:COMBAT_ApplyReductions@0x0057C1E0, run:2026-10-16-combat, run:2026-10-21-shortfalls2)
- **Not in the logs.** `STA` is logged at `STATE_ApplyTimed` (0x0056E970) only: the logs hold states 9, 24, 28, 35,
  40, 43, 44, 46, 49, 52, 62 and 159, and none of the stun (21), cold (11), freeze (1), poison (2), shatter (107) or
  burning (115) states. The missile's stat 327 is not in `MS0`. No delivery had both a hit event and a get-hit event
  handler, nor a kill or killed handler. Those rows return to (b), H5b.
- **Skills runs.** `check-skills.txt`: weapon-share creations stepped the owner's seed once, 856 by a player and 128 by
  a monster (classes 160, 161 and 170 with missiles 13, 14 and 196); none twice. `check-handlers.txt`: handlers 7, 8,
  20 (attacker) and 21 (the player defender) stepped their unit's seed once per call, 9 once on a monster attacker;
  5, 6, 13, 17, 19, 22, 28 and 29 not at all; handlers 3, 30 and 31 never fired. [C] (run:2026-10-25-skills,
  run:2026-10-27-skills)
- **Skills.txt:** `srvprgfunc1`–`3` are set on four rows: 259 (143, 38, 39), 269 (–, 36, 37) and 274 (–, 38, 39) with
  `prgstack`, 280 (40, 143, 41) without. [C] (tbl:Skills.txt:srvprgfunc1, full table)

#### Addendum 2026-11-15: plan 0066 batch S5a, part 2 (the `MonAttackStats` output model and the delivery's boundary draws, `lane/n66j`)

A new check over the same kept logs, no game. Tool `tools/sweep2_s5a2.py` (`946081ff…`), which runs part 1's
`sweep2_s5a.py` (`104ce037…`, unchanged) as its base, so the Checker and the nine part-1 checks run again (0
mismatches, 0 bad), and adds the models below. Command, from the repository root: `python3 -I tools/sweep2_s5a2.py
workspace/logs/combat/c37r-run2.lst workspace/logs/combat/p47h-run.lst workspace/logs/combat/p47b-run.lst
--no-shield-log` with the nine logs recorded above for `p47h-run.lst`. Output `workspace/logs/n66j/check-combat-p2.txt`
(`d5a594af…`, 214 lines, `S5a2 total bad=0 checker=0 part1-bad=0`); the r2 reads it rests on are kept beside it
(`p2/mas-disasm.txt`, `p2/mas-disasm2.txt`, `p2/gethit-disasm.txt`); `manifest-p2.sha256` (`77a83aae…`) passes
`sha256sum -c` from `workspace/logs/n66j`. Six development outputs of earlier revisions are in `p2/dev/` with
`manifest-dev-p2.sha256`. r2 is the second tool after Ghidra for the readings below.

- **`MonAttackStats`' stats reproduce in all 19 780 logged calls.** The model (module docstring; r2 0x005A4F50–0x005A5443):
  MonLvlStats cells by the mode's column set, then in a classic game (`game+0x70` = 0) with `d` > 0 and `Align` ≠ 1
  damage `tdiv(10x, 12)` and to-hit `tdiv(10x, 15)`; in an expansion game, when `sub_006259B0_UnitAlignGet` returns 0,
  `x += tdiv(x·b, 128)` on 21, 22, 19 and on the `El` block's minimum, maximum and length, with
  `b = sub_005A4F20_PlayerDmgBonus(game, max(stat 100, 1))` (r2: 0 for `game+0x6D` = 0 or `n` < 2, the dword table
  0x006E21F4 = 0, 0, 8, 16, 24, 32, 40, 48, 56 for `n` < 9, `lea eax, [edx·8 − 0x10]` above). `mas-stats` 19 750 of 19 750
  (the 30 others are each hireling's first call, where its offset is learned), `mas-el` 1 030 of 1 030 `El` applications
  compared (types 1 fire 308, 2 lightning 611, 4 cold 108 with stat 56, 5 poison 298 with `× 10` and `× 2`; `El1` 1 228,
  `El2` 97). [C] (fn:sub_005A4F50_MonAttackStats@0x005A4F50, fn:sub_005A4F20_PlayerDmgBonus@0x005A4F20,
  data:g_PlayerDmgBonus@0x006E21F4, run:2026-10-16-combat, run:2026-10-20-shortfalls)
  - **What separates** (each reading reversed alone, `check-combat-p2.txt`): the classic factors in 562 of the 600
    classic Nightmare and Hell calls (no factor, or the two divisors swapped, gives other stats); `b` = 16 at
    `/players 3` in 600 of 600 Hell calls and `b` = 56 at `/players 8` in 1 679 of 1 798 Nightmare calls (against
    `b` = 0), the table step in 2 279 (`n − 1`) and 600 (`n + 1`); the `d = 0` test in 5 216 of 6 444 Normal calls at
    `n` ≥ 2 (the bonus of `n` would change them); `b` on the `El` stats in 154 of 154 applications compared under
    `b` > 0 (13 at 16, 141 at 56), the length included; the mode's column set in 18 081 calls; an `El` group of another
    mode left unwritten in 3 929 calls; `El2` applied with `El1`'s minimum, maximum and length (the mask `0x40 + e`)
    in 57 compared applications whose own `El2` cells differ from `El1`'s (97 applied, 40 on units with another `El`
    list). [C] (0x005A5252–0x005A527A, run:2026-10-16-combat)
  - **Not separated or not met.** The `L` columns (the plain cells give the same 17 714 values); the `8n − 16` branch
    (`n` ≥ 9 never logged; at `n` = 9 it equals the table's 56); `Align` = 1 (2 classic calls, not counted for
    separation); `UnitAlignGet` ≠ 0: the 2 066 hireling calls (class 561) are checked against an offset learned at each
    one's first call, since their MonStats cells give 0 and their Hireling list adds the rest, so the alignment test is
    not separated; types 3, 6–11 and 12 never applied, nor any `El3`; the skill-damage pair (no logged class has one). 295 `El`
    writes on units already holding `El` stats from another list (classes 9, 10, 19, 20, 30, 80, 85, 135: enchanted
    uniques' minions) are not compared. [I] (fn:sub_005A4F50_MonAttackStats@0x005A4F50)
  - **The mode passed.** At the attacker's next `EV0` its mode equals the last `MAS0` mode in 10 842 of 10 979 pairs;
    the 137 others (8 → 14 in 53, 4 → 14 in 25 among them) can have mode changes between, so this is a counter, not a
    test of "the new mode". [I] (fn:sub_005A7C20_MonSetMode@0x005A7C20, 0x005A7D34)
- **The durability draws match `items/economy` H1–H2 by seed steps.** On every one of 9 680 `DU0`/`DU1` pairs but
  one: a player attacker's seed steps once and a monster's or a hireling's never (5 668 player hits, 4 012 others);
  a player defender's seed steps three times (`RangeB(7)`, `RangeB(W)`, the roll; 2 045), a monster's or a hireling's
  never (1 749 hireling hits on monsters, 218 monster hits on hirelings). The exception: the one `0x005CAED8` (mode-14)
  attack on the player stepped neither seed, not explained. [C] for the step counts (fn:COMBAT_DurabilityLoss@0x0057D3D0,
  fn:ITEMS_DurabilityLossRoll@0x00559E30, run:2026-10-16-combat); [I] the roll values (the equipment is not logged)
  and the `0x005CAED8` case.
- **The get-hit draws on a player defender are `GetHitRoll`'s** (anim/timing M1–M2): `gh-steps` 25 669 of 25 669, i.e.
  18 072 events with no delivery and 875 with a result that returns first (0x1 without 0x4, or 0x7 killed) step
  nothing, and 6 722 reach `GetHitRoll` with the bands by `hp ÷ D` (stat 7 at the outer `AD1`; `D` 16 in 6 547,
  8 in 175 from a missile's hit class), 8 of them drawing (one draw 5, two 3); another divisor would give other steps
  in 169. [C] (fn:COMBAT_GetHit@0x0057CEE0, fn:sub_0057CB00_GetHitRoll@0x0057CB00, run:2026-10-16-combat)
- **On a monster or hireling defender the model is an upper bound only.** `COMBAT_GetHit` first calls 0x005A54F0
  (unread) for such a defender and tests states 54 and 21 and, in `GetHitRoll`, state 1, none of which these logs
  hold. Logged steps never exceed the model (`gh-steps-monster-not-more`, 9 509 of 9 509): equal in 7 969 (2 085 of
  them drawing), fewer in 406 (163 with a logged stun packet still running, 125 with a cold length running), 0 in all
  1 134 results that return before `GetHitRoll`; 2 of 1 696 GetHits with no delivery stepped once (0x005A54F0's part,
  presumably). A kill runs `UnitKilled` (3 652, 2 364 stepping: the drop). [I] (0x0057CF65, 0x0057CFF8, 0x0057D0B9,
  run:2026-10-16-combat)
- **Flags and result bits** (`check-combat-p2.txt`, with part 1's counters): flag `0x2` is set at the builder's entry
  in all 6 901 player attacks, which build once (`build-once` 10 951 of 10 951), and clear in the 4 050 monster and
  hireling attacks, which build once inside the resolve; result `0x1` is set exactly when the melee `THR` roll is below
  its chance (9 594 of 9 594, hits and misses); `0x2` exactly when the defender's life is 0 at the outer `AD1` (3 665
  set, 17 141 clear); `0x4` only with `0x1` (20 806); `0x2000` with the doubling (the Checker's build). Flag `0x1`
  never occurs; `0x300` (bypass undead and demons) occurs at 7 `AD0` lines, not tested; the other flags and result
  bits are not in any logged packet (part 1). [C] for the bits named as tested (run:2026-10-16-combat); [I] for the
  rest.
- **A `manahit` attacker's drain.** 262 hits by monsters with stat 62 ≥ 256 (`v` = stat ÷ 256 from 10..16 to 60..91);
  on the player, with no handler in the delivery, mana at `AD1` = `AD0` mana − the packet's mana field, 0 below 256,
  in 226 of 226 (`manahit-loss`); every one took all the mana held, and in 138 the `v` reading (the field ÷ 256)
  would have left mana. With the Checker's `BD1` (the field rolled from stats 62/63 and shifted) this composes B4's
  `256·v`. [C] (fn:sub_005A1F90_UModManaHit@0x005A1F90, fn:COMBAT_ApplyDamage@0x0057C6C0, run:2026-10-16-combat,
  run:2026-10-20-shortfalls) The `El` type 7 half (no logged `El` 7) and the `v << 22` wrap (`v` ≤ 91 here) stay [I].

## run:2026-10-20-shortfalls

One run under two checkers: this section holds the combat sessions; the stats sessions are in
[stats/experiments](../stats/experiments.md#the-stats-sessions-of-run2026-10-20-shortfalls), the travel sessions in
[quests/experiments](../quests/experiments.md#the-travel-sessions-of-run2026-10-20-shortfalls).

- **Question:** plan [0047](../../plans/done/0047-simulation-shortfalls.md) Phase 2. Do the branches that
  run:2026-10-16-combat left under the rare-branch floor of about 30 (combat/0001 § 15, last bullets) reproduce event
  for event when sessions are built for them: crushing blow on champions, the resistance caps, magic immunity, the
  negative absorbed amount, the negative total, evade, weapon block, dodge, avoid, freeze, flat absorb, a walking
  player's block? Boundary as in run:2026-10-16-combat (value oracles, boundary oracles, inputs); no new oracle.
- **Setup:** agent-driven sessions on harness slot 2 (display `:9`, prefix `workspace/wineprefix-2`), saves set aside
  under tag `p47h`, pinned `game.exe`, stock data. Logger `tools/gdb/combat.gdb` (`450f36f8…`) with
  `tools/gdb/combat.py` r9 (`82780acc…`, commit `98426bc`, unchanged) and `tools/gdb/pilot.py` (`1ad48a4c…`); every log
  writes `COMBATLOG {"rev": 9}`. Driver `tools/combat_sessions.py run --slot 2 --tag p47h --saves
  workspace/scratch-p47h/saves --run p47h …` (final revision `89444dbb…`; the sessions, seeds and pilot commands are its
  `SESSIONS` rows), `tools/d2pilot.py` `c2b3257f…`. Five batches: A and B (the first lane, killed with every agent by
  systemd-oomd at 20:12 while `ama-n-idle1`'s and `ass-n-plains2`'s checks started; both re-checked by this lane), C, D.
  Per-session caps as before (player attack 800, monster attack 500, `MonAttackStats` 300, missile defence 300).
- **Characters** (ADR-0013 § Neutral, tool-built from stock uniques, pinned in `tools/test_d2s.py` except the two
  plan 0037 recipes): `CombatOW` (`b07db91b…`), `CombatSorH` (`210b2c0c…`), `CombatDR` (`639afd6a…`), `CombatAbs`
  (`05f4741c…`), `CombatFrz` (`c1ed1c39…`), `CombatAma` (`5b694383…`), `CombatAss` (`e0ea31a2…`), `CombatAssO`
  (`c4dc7172…`), `CombatOWF` (`77807e00…`: commit `5871b00`'s `CombatOW` recipe with only the name changed, so not
  the lost log's `5f440622…` byte for byte; the item list and rolls are that recipe's), and two new ones on
  `smpama.d2s`: **`CombatAmaD`** (`d4572d07…`: level 5, dexterity 15, Dodge, Avoid and Evade 20, *The Gnasher*,
  *Goldwrap*, *Nokozan Relic*, *Raven Frost*, *Manald Heal*; no shield, no armour) and **`CombatAmaW`** (`fa9c4162…`:
  the same with dexterity 60 and *Pelta Lunata*). Why the new ones: `CombatAma` (level 85, dexterity 400) was hit at
  the to-hit floor, `c` = 5 in every logged roll of `ama-n-stand`, `ama-n-walk` and `ama-n-idle1`, and every defence
  roll needs a hit first; with its shield the block roll also comes before dodge.

### Sessions

| session | seed | save | difficulty | where (waypoint) | pa | ma | ha | md | pm | MAS |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| ow-nm-champs1 | 4701 | CombatOW | Nightmare, /players 8 | Cold Plains (1,2) | 103 | 297 | 0 | 1 | 0 | 300 |
| ow-nm-champs2 | 4702 | CombatOW | Nightmare, /players 8 | Stony Field (1,3), `--sweep` | 195 | 500 | 0 | 18 | 0 | 300 |
| ow-nm-champs3 | 4703 | CombatOW | Nightmare, /players 8 | Dark Wood (1,4), `--sweep` | 205 | 279 | 0 | 19 | 0 | 300 |
| sorh-n-darkwood | 4711 | CombatSorH | Normal, /players 8 | Dark Wood (1,4) | 90 | 38 | 169 | 23 | 0 | 300 |
| sorh-n-lostcity | 4712 | CombatSorH | Normal, /players 8 | Lost City (2,6) | 25 | 12 | 49 | 190 | 0 | 156 |
| sorh-n-marsh | 4713 | CombatSorH | Normal, /players 8 | Black Marsh (1,5) | 68 | 34 | 122 | 6 | 0 | 218 |
| sorh-n-cityd | 4719 | CombatSorH | Normal, /players 8 | City of the Damned (4,2) | 73 | 37 | 82 | 34 | 0 | 220 |
| sorh-n-travincal2 | 4791 | CombatSorH | Normal, /players 8 | Travincal (3,8) | 29 | 7 | 38 | 187 | 0 | 300 |
| sorh-n-travincal3 | 4792 | CombatSorH | Normal, /players 8 | Travincal (3,8) | 31 | 3 | 31 | 300 | 0 | 300 |
| sorh-n-catacombs2 | 4793 | CombatSorH | Normal, /players 8 | Catacombs Level 2 (1,9) | 14 | 10 | 47 | 7 | 0 | 88 |
| sorh-h-lostcity1 | 4721 | CombatSorH | Hell | Lost City (2,6) | 30 | 500 | 51 | 0 | 0 | 300 |
| sorh-h-lostcity2 | 4722 | CombatSorH | Hell | (left the level after 11 s: no event) | 0 | 0 | 0 | 0 | 0 | 0 |
| sorh-h-lostcity3 | 4723 | CombatSorH | Hell | Lost City (2,6) | 117 | 500 | 122 | 2 | 0 | 300 |
| sorh-h-lostcity4 | 4724 | CombatSorH | Hell | Lost City (2,6) | 101 | 500 | 14 | 0 | 0 | 300 |
| dr-n-plains | 4731 | CombatDR | Normal | Cold Plains (1,2) | 78 | 206 | 0 | 3 | 0 | 242 |
| dr-n-darkwood | 4732 | CombatDR | Normal | Dark Wood (1,4) | 104 | 65 | 0 | 2 | 0 | 171 |
| dr-n-travincal | 4734 | CombatDR | Normal | Travincal (3,8) | 38 | 8 | 0 | 232 | 0 | 300 |
| abs-n-plains | 4741 | CombatAbs | Normal | Cold Plains (1,2) | 95 | 87 | 0 | 18 | 62 | 236 |
| abs-n-darkwood | 4742 | CombatAbs | Normal | Dark Wood (1,4) | 109 | 361 | 0 | 19 | 198 | 300 |
| abs-n-marsh | 4743 | CombatAbs | Normal | Black Marsh (1,5) | 111 | 148 | 0 | 77 | 212 | 300 |
| frz-n-plains | 4751 | CombatFrz | Normal | Cold Plains (1,2) | 97 | 115 | 0 | 60 | 0 | 210 |
| ama-n-stand | 4761 | CombatAma | Normal, /players 8 | Cold Plains, walking explore with Attack | 109 | 349 | 0 | 9 | 0 | 300 |
| ama-n-walk | 4763 | CombatAma | Normal, /players 8 | Cold Plains, walk toggle (`r`) | 56 | 260 | 0 | 55 | 0 | 300 |
| ama-n-idle1 | 4765 | CombatAma | Normal, /players 8 | Stony Field, walk in, stand 3 × 90 s | 49 | 500 | 0 | 6 | 0 | 300 |
| amad-n-idle1 | 4795 | CombatAmaD | Normal, /players 8 | Cold Plains, walk in, stand 3 × 90 s | 63 | 500 | 0 | 15 | 0 | 300 |
| amad-n-run | 4798 | CombatAmaD | Normal, /players 8 | Cold Plains, running explore | 41 | 135 | 0 | 5 | 0 | 193 |
| amaw-n-walk | 4799 | CombatAmaW | Normal, /players 8 | Stony Field, walk toggle (`r`) | 38 | 123 | 0 | 81 | 0 | 300 |
| ass-n-plains | 4771 | CombatAss | Normal, /players 8 | Cold Plains | 63 | 229 | 0 | 1 | 0 | 253 |
| ass-n-plains2 | 4772 | CombatAss | Normal, /players 8 | Stony Field | 38 | 500 | 0 | 8 | 0 | 300 |
| ass-n-plains3 | 4774 | CombatAss | Normal, /players 8 | Dark Wood (explore stopped after 5 hops) | 0 | 6 | 0 | 0 | 0 | 7 |
| asso-n-plains | 4773 | CombatAssO | Normal, /players 8 | Cold Plains | 43 | 120 | 0 | 0 | 0 | 126 |

`ass-n-plains2`'s pilot was killed by the OOM at hop 30; the game ran on under its driver's `--after` with the
Assassin standing (the log ends at 20:34 with gdb's `exited normally`), so its later events are a standing player's.
`sorh-h-lostcity2` and `ass-n-plains3` are in the run list with 0 and 13 events. Staged but not run, as their cases
were met or capped first: `ow-nm-champs4`…`6`, `sorh-n-oasis`, `sorh-n-catacombs`, `sorh-n-upperk`,
`sorh-n-travincal`, `sorh-n-spider`, `sorh-n-catacombs3`, `sorh-h-lostcity5`/`6`, `abs-nm-marsh`, `frz-nm-plains`,
`ama-n-run`, `ama-n-walk2`, `ama-n-idle2`/`3`, `amad-n-idle2`/`3`.

Not part of the run: `owf-n-andariel-p8` (seed 3712, `CombatOWF`; below) and the development log
`dev-p47h-amaw-n-walk-steelclash.log` (the first `amaw-n-walk`, with *Steelclash*, whose level 17 left it unusable at
level 5: all 225 player `DRB` lines read 0, the shield test of `UnitBlockChance`; the recipe was changed to *Pelta
Lunata* and the session re-run).

### Log manifest

| file (under `workspace/logs/combat/`) | sha256 | what |
|---|---|---|
| `p47h-run.lst` | `89fce594…` | the 31 logs of the run, in check order |
| `p47h-manifest.txt` | `04dadb8c…` | per log: sha256, size, line count (`tools/combat.py manifest`), the 31, `owf-n-andariel-p8` and the dev log |
| `p47h-logs.sha256` | `7211a9b4…` | `sha256sum -c` from this directory: every log and output of this table |
| `p47h-check.json`, `p47h-check.txt` | `4e7ee7a7…`, `e748e625…` | the checker over the run list |
| `p47h-owf-check.json`, `p47h-owf-check.txt` | `5db67372…`, `3ccb063d…` | the checker over `p47h-owf-n-andariel-p8.log` |
| `p47h-mode2-hits.py`, `.txt` | `cf2c105f…`, `23f3a7d2…` | events on a player in mode 2 per log (the walking block) |
| `p47h-mode14.py`, `.txt` | `b76b02da…`, `65348be0…` | monster attacks in mode 14 by return address and class, with or without their own `MAS` (the 40 logs of `c37r-run2.lst` and the 31) |
| `p47h-defrolls.py`, `.txt` | `c535f3d1…`, `06e7e82a…` | player defence rolls by label, defender mode and outcome, over the run list |
| `p47h-monflags.py`, `.txt` | `6223837f…`, `9c795179…` | the type flags `0x0C` of every monster first seen in a `MON` line, over the 74 combat logs on disk |
| `p47h-<session>.pilot.txt`, `-shots/` | — | the driver's output and screenshots |

### Procedure and result

1. The sessions, five batches (above).
2. `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/combat.py check $(cat
   workspace/logs/combat/p47h-run.lst) --no-shield-log p47h-ass-n-plains,p47h-ass-n-plains2,p47h-ass-n-plains3,p47h-asso-n-plains,p47h-dr-n-plains,p47h-dr-n-darkwood,p47h-dr-n-travincal,p47h-amad-n-idle1,p47h-amad-n-run
   --json workspace/logs/combat/p47h-check.json`, `tools/combat.py` at `9d8a1fa` (`bd80126a…`): **0 mismatches over
   18 737 events** (pa 2 213, ma 6 429 of which 8 dropped, ha 725, md 1 378, pm 472, MAS 7 520).
   `--no-shield-log` (new) names the logs whose player holds no usable shield (the claws, `CombatAmaD`, and
   `CombatDR`, whose two-handed *Spellsteel* leaves *Kerke's Sanctuary* with block chance 0 in all 18 of its player `DRB` lines,
   12 + 4 + 2): `UnitBlockChance`'s shield test is a value oracle, as before; the logs carry no equipment.
   *Review 2026-10-21:* the same call without `--no-shield-log` gives `SUMMARY mismatches=88 events=18737`, every one
   `DRB block chance (player formula, shield held)` with 0 logged: 66 on `CombatAss` (28, 37 and 1 in
   `ass-n-plains`, `-plains2`, `-plains3`), 4 on `CombatAssO`, 18 on `CombatDR` (12, 4, 2); the `CombatAmaD` logs
   pass either way (dexterity 15 makes the expansion formula 0). The claw recipes hold no shield, so their 70 are a
   prediction from the recipe; `CombatDR`'s 18 are the logged 0 taken as the input (its refusal is unread,
   combat/0001 § 16). The flag only sets the expected chance to 0: a logged chance above 0 still fails.
3. The same checker over `c37r-run2.lst` (the kept run): `SUMMARY mismatches=0 events=40655`, unchanged except two
   counters: `defence roll block` 9 288 is new, and the crushing-blow label `champion (0x04)` takes 72 of the 163
   events labelled `unique` (below). *Review 2026-10-21:* against the kept output
   `c37r-run2-check-rbs-2026-10-17.txt` there are also the three new `≤ 0` delivery counters (147 negative on the
   player, 4 and 444 at zero on the player and on a monster); no other line differs.

**Checker changes** (`tools/combat.py`, commits `157e502`…`9d8a1fa` on `lane/p47h`): the `≤ 0` delivery counter
(`delivery total negative/zero (life unchanged)`, backlog resume-lane follow (b)); the dead-defender test from
`sub_005541B0_UnitIsDead`; `STATEVENT_Freeze` up to its nested delivery; flat absorb per element; defence rolls
counted per label and the undivided mode-2 block; `--no-shield-log`; the crushing-blow label tests `0x04` before
`0x08`; an attacker's own `MonAttackStats` inside its event (`sandraider2` in mode 14, return `0x005CAED8`: 6 of the 14 such
events before a `MAS` cap call it, over the 71 logs of `p47h-mode14.txt`) gives the build its stats (`MAS1`, a value oracle as at `EV0`) and
must enter on the attacker's running seed (5 events, asserted); past a log's `MAS` cap such an event has no stats
input and is dropped with a count (8, one log).

| case (plan 0047 Phase 2) | count, this run | label in `p47h-check.txt` | met |
|---|---:|---|---|
| crushing blow on champions (Nightmare) | 40 (52 in all) | `crushing blow on champion (0x04)` | yes |
| cold resistance at the cap | 4 (31 with the kept run's 27) | `resist application cold at cap` | over the two runs (review ruling 2) |
| lightning resistance at the cap | 42 | `resist application light at cap` | yes |
| magic immunity | 36 | `resist application magic immune` | yes |
| negative absorbed amount | 186 | `negative absorbed amount (no heal)` | yes |
| negative total, life unchanged (player) | 488 (+ 113 at 0; 32 at 0 on a monster) | `delivery total negative/zero (life unchanged)` | yes |
| evade | 31 of 46 rolls | `evade`, `defence roll evade` | yes |
| weapon block | 30 of 50 rolls | `weapon block`, `defence roll wblock` | yes |
| dodge | 109 of 172 rolls | `dodge`, `defence roll dodge` | yes |
| avoid | 68 of 103 rolls | `avoid`, `defence roll avoid` | yes |
| freeze | 81 | `freeze handler: freeze delivered` | yes |
| flat absorb | 113 (fire; cold 0, lightning 0) | `flat absorb fire on the player (amount > 0)` | yes (fire) |
| a walking player's block | 6 | `block not divided: moving player in mode 2 (walk)` | **no** |

- **Champions carry `0x08`.** No monster of the 74 combat logs on disk has type flag `0x04` without `0x08`: 6 982
  with neither, 328 with `0x08` only, 164 with both (`p47h-monflags.txt`). A champion is a special monster on which
  `SpecialModsRoll`'s champion roll set `0x04` (monsters/0003 § 2), so "`0x04` and not `0x08`", the label the
  checker used, is empty on stock spawns; the 72 kept-run and 52 new crushing blows on `0x0C` defenders are the
  champion case, all at `k` = 4 raised by the player count. `STATEVENT_CrushingBlow` tests neither flag
  (combat/0001 § 10), so the reading needs no split.
- **Weapon block and the skill check.** `WBS` = 13 in all 50 rolls of the two-claw `CombatAss` (15, 34, 1 per log);
  `CombatAssO` (one claw, empty left hand) logged `WBS` 12 once and rolled no weapon block. So 13 is what the two-claw
  layout gives and 12 the one-claw layout (Phase 1 review ruling 3 (b)); what the value is (a weapon class row) stays
  unread.
- **The walking block.** 48 events on a player in mode 2 over `ama-n-walk` and `amaw-n-walk`, 6 of them hits that
  reached the block roll, all with `DRM` `mv` = 1 and the chance not divided (`p47h-mode2-hits.txt`): the
  exception holds where seen, under the floor. Ruling 3 (a)'s one more session was `amaw-n-walk` (`ama-n-walk2`
  replaced by it, since the cause was the to-hit floor, not the mode).
- **Cold at the cap.** 4: in Normal (no penalty) a cold hit on the player needs a cold El row that rolls (the Dark Wood's
  cold rows `fallen2` and `quillrat2` have an empty `El1Pct`) or a cold-enchanted special; Travincal's cantors and vampires
  (`El1Pct` 65) were rarely in melee range of `CombatSorH`, and the Lost City drew no cold row on seed 4712. With the
  kept run's 27 it is 31 over two runs.
- **Prevent-heal (state 52) needs no draw, in a run log.** `abs-n-plains` (`CombatAbs`, *Blackhorn's Face*,
  `noheal`) has 81 and the run 271 state-52 `STA` lines between the to-hit and the defence rolls, each skipped with no
  draw and every seed after it asserted, 0 mismatches.
- **`owf-n-andariel-p8`** (`CombatOWF`, seed 3712, Normal Andariel; not in the run): 633 events, 68 state-52 lines
  skipped, **57 mismatches, all "expected `AD1`, got `EVH`"** (the event-9 handler `0x005C01D0`, function 28
  `item_healafterkill`, not modelled: plan 0045 Phase 2). It is the kept replacement of the lost `e001b03e…` log
  (backlog resume-lane follow (a)): `p47h-owf-n-andariel-p8.log` `a411b34d…` in `p47h-manifest.txt`.
- **Conclusion:** every case but two passes the floor with 0 mismatches; cold at the cap (4) and the walking block (6)
  are named again with these counts (*review 2026-10-21:* the cold cap is met over the two runs, 31, both re-checked
  by this checker revision; the walking block is final); the magic cap stays unstaged (Phase 1 ruling 2). Raises in
  [combat/0001 § 16](0001-formulas.md#16-plan-0047-phase-2-the-shortfalls-run2026-10-20-shortfalls). (run:2026-10-20-shortfalls)

## run:2026-10-21-shortfalls2

The run is defined in [stats/experiments § The stats sessions of run:2026-10-21-shortfalls2](../stats/experiments.md#the-stats-sessions-of-run2026-10-21-shortfalls2)
(plan [0047](../../plans/done/0047-simulation-shortfalls.md) Phase 2b); this section holds its combat sessions, the cold and
lightning flat absorb that `abs-nm-marsh` was to reach.

- **Setup:** slot 2, tag `p47b`, saves `workspace/scratch-p47b/saves` (`CombatAbs` `05f4741c…`, pinned). Logger
  `tools/gdb/combat.gdb` (`450f36f8…`) with `tools/gdb/combat.py` r9 (`82780acc…`, unchanged). Driver
  `tools/combat_sessions.py run --slot 2 --tag p47b --saves workspace/scratch-p47b/saves --run p47b abs-nm-marsh
  abs-n-travincal abs-n-cityd` (`f2539a81…`; the two new rows: the fields whose every row adds the element, Travincal
  for cold and the City of the Damned for lightning, since the Act I fields' cold and lightning rows have an empty
  `El1Pct`), `tools/d2pilot.py` `114a7003…`.

| session | seed | save | difficulty | where (waypoint) | events | flat absorb fire / cold / lightning |
|---|---|---|---|---|---:|---|
| abs-nm-marsh | 4744 | CombatAbs | Nightmare | Black Marsh (1,5) | 1 276 | 31 / 0 / 13 |
| abs-n-travincal | 4745 | CombatAbs | Normal | Travincal (3,8) | 598 | 193 / 1 / 25 |
| abs-n-cityd | 4746 | CombatAbs | Normal | City of the Damned (4,2) | 653 | 35 / 0 / 13 |

- **Check:** `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/combat.py check $(cat
  workspace/logs/combat/p47b-run.lst) --json workspace/logs/combat/p47b-check.json`, `tools/combat.py` `ee628bbe…`
  (commit `600f2ca`): **0 mismatches over 2 527 events** (`p47b-run.lst` `0632742b…`, `p47b-check.json` `f61d3b5f…`,
  `p47b-check.txt` `aedd5766…`). Logs, pilot outputs and outputs in `p47b-logs.sha256` (`d5b96337…`, `sha256sum -c`
  from `workspace/logs/combat/`).
- **Checker change** (`600f2ca`): `abs-nm-marsh` gave one mismatch with the previous revision, `LE1 attacker life:
  logged 26279, model 32679` (line 6 763): a monster draining the player (its stat 74 at −2 449) was hit by *Blackhorn's
  Face*'s lightning thorns (handler `0x005BF720`, the defender's event 1) for 25 life before its drain, and the checker
  started the drain from the attacker's `AD0` life. It now takes the attacker's life from the defender handler's `EVR`
  (`lo`), on both the plain and the nested-line path, counted as `attacker life taken from a defender handler's EVR`
  (22 + 7 events here; *review 2026-10-21:* 8 of them have a leech after the handler and one, line 6 763, separates
  the two readings, the previous revision's only mismatch). Re-checks with this revision: `p47h-run.lst` (with its recorded `--no-shield-log`) 0 / 18 737,
  its JSON equal to `p47h-check.json` but for that counter (30); `c37r-run2.lst` 0 / 40 655, its report equal to the
  one of the Phase 2 re-check (no such event). Outputs `p47b-recheck-p47h.json` (`212c0557…`)/`.txt`, `p47b-recheck-c37r.json`/`.txt` (`0fd905d4…`).
- **Result:** lightning flat absorb **51** (met); cold flat absorb **1** (named again, final: Travincal's cold rows
  gave 13 melee attacks, all misses; *review 2026-10-21:* final under the Done-when's own condition, `abs-nm-marsh`
  run, not as a stock-data limit, since Nightmare and Hell cold rows were not tried). (run:2026-10-21-shortfalls2)

## run:2026-11-15-sweep2-s5b

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S5b (`lane/n66j`): static second
sources for the 24 class-c rows of the combat specs. No game, no wine, no Ghidra. The claims are in
[combat/0001 § 18](0001-formulas.md#18-plan-0066-batch-s5b-static-second-sources-run2026-11-15-sweep2-s5b).

- **Question:** do a second tool's call, pointer, push and store scans of the pinned `Game.exe`, and full-table
  checks of the excel `.txt` tables, give the callers, stat ids, packet writers, event registrations and draw-free
  closures the combat specs state (at `b5999f5e`) as inferred?
- **Setup:** `tools/sweep2_s5b.py` (sha256 `4ad860dd…`), stdlib only. Its tools: the raw-byte scan of
  `tools/xrefscan.py` (every rel32 call/jmp and abs32 reference to a target), radare2 (`r2 -q`, linear `pd`/`pD`,
  `pxw`, its own `/x` byte search for the LCG multiplier) for every decoded instruction the checks assert, and the
  objdump listing of `.text` (`tools/sweep_s4b.py`) for function bodies, the call graph and the store scans; plus
  `re/symbols.csv` for names only. Sections `callers`, `stats`, `stores`, `tables`, `closures` (the docstring says
  which row each serves).
- **Procedure** (from the worktree root; `L=workspace/logs/n66j/s5b`):
  ```
  systemd-run --user --scope -p MemoryMax=4G python3 -I tools/sweep2_s5b.py all > $L/check-s5b.txt
  (cd $L && sha256sum -c manifest-s5b.sha256)
  ```
- **Outputs:** `check-s5b.txt` (`3b8c2822…`, 2 517 lines, last line `S5b total bad=0`) and `totals-s5b.txt` (the
  inventory's class totals after merging `main` `c48797e7`), listed in `manifest-s5b.sha256` (`30f6ea65…`), which
  passes from `workspace/logs/n66j/s5b`. Fourteen development outputs of
  earlier tool revisions (a stat-id window that kept the layer push, a misaligned read of the reduction table, a
  missing entry for the helper `0x005D8B10`, a looser `rep movsd` decoding) are kept in `dev/` with their own
  `dev/manifest-dev.sha256`, passing from `dev/`; none is cited.
- **Result:** 29 checks, 0 bad. Row outcomes and their counts are in combat/0001 § 18 and in each inventory row's
  *Route* cell.

## run:2026-11-16-sweep2-s5e

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S5e part 1 (`lane/n66t`): the combat
reduction and to-hit leaf functions run under Ghidra's p-code emulator on the pinned image (ADR-0015, ADR-0021),
compared with `tools/` models. No game, no wine. The claims are in
[combat/0001 § 19](0001-formulas.md#19-plan-0066-batch-s5e-part-1-emulated-reduction-and-to-hit-leaves-run2026-11-16-sweep2-s5e).

- **Question:** do `COMBAT_ResistFor`, `COMBAT_Absorb`, `COMBAT_DamagePercent`, `COMBAT_LengthImmunities`,
  `COMBAT_ToHitTargetMods`, `sub_0057D810_PreventHealHook`, `0x00621190`, `COMBAT_AvoidRoll` and
  `sub_005A5560_MonCritDouble`, run on declared inputs, give the outputs the combat specs (at `b5999f5e`) state as
  inferred, including the branches no logged event reached?
- **Setup:** `tools/combat_s5e_emu.py` (sha256 `a783622e…`, stdlib), `re/ghidra_scripts/EmuBoundary.java` unchanged,
  Ghidra 12.1.2, project `workspace/ghidra-n66t` (`-Xmx3G`) after `import-symbols`. One kept launch of
  `tools/ghidra.sh emuboundary`, 9 families, 17 300 cases, seeds `random.Random("n66t-s5e-<family>")` and the image
  `random.Random("n66t-s5e-image")`.
- **Memory spec** (`s5e.mem`): `g_pDataTables` 0x00744304 → a scratch DataTables (`dt.bin`: state count `+0xC4` = 192,
  MonStats `+0xA78`/`+0xA80` = 0x240 records of seeded random bytes, `monstats.bin`; ItemStatCost `+0xBCC`/`+0xBD4` =
  0x200 zero records, `isc.bin`, so no stat floor applies). Each case writes its units (random bytes, then type,
  class, mode, MonsterData `+0x14` with flags `+0x16`, seed `+0x20`, `+0x30`, `+0x40`, stat list `+0x5C`, inventory
  `+0x60` = 0, game `+0x80`, flags `+0xC4`), the stat list (live array at `+0x48`/`+0x4C` when `+0x10` bit 31 is set,
  else `+0x24`/`+0x28`, sorted keys `stat << 16 | layer`, decoys at layer 1 and in the other array, state bits at
  `+0x58`), the context, the packet and the reduction row, and the MonStats bytes it uses (`+0x0C`, `+0x0D`, `+0xA6`).
  Guards: the fatal path 0x00408090, 0x00408A60, 0x00681E09 and the allocator 0x0040B4B0, 0x0040B430, 0x0040B480.
  **Observed boundaries (ADR-0021):** `STATE_ApplyTimed` 0x0056E970 (`phh`; site 0x0057D891, return 0x0057D896),
  0x0064F380 (`avoid`, the weapon-block check, which runs `COMPOSIT_WeaponClass`; sites 0x0057DDAB, return 0x0057DDB0,
  local `ebp − 4`, for a player and 0x0057DEEA, return 0x0057DEEF, local `ebp − 8`, for any other type),
  `sub_00621E40_UnitSetOverlayStat` (`crit`; return 0x005A5641). Every other callee runs whole (the list is in the
  tool's docstring); none allocates, and no import is reached.
- **Read set (ADR-0015 (2)):** the 9 traced read sites all fall in `g_BitMask32` 0x006CE268 (128 bytes, `.rdata`,
  read by `UNIT_TestStateBit`, the `MONSTATS_Is*` tests and `sub_00624F60_StatListGetValue`), the constant table
  run:2026-11-16-sweep2-s6f also declared; no traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66t/s5e/run`):
  ```
  python3 -I tools/combat_s5e_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66t GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s5e.cases $D/s5e.mem > $D/s5e.out
  python3 -I tools/combat_s5e_emu.py check --dir $D > $D/check.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`100ff7eb…`, 137 lines, last line `S5E total cases=17300 mismatches=0 stops=0
  controls=127 unseparated=9 controls_passed=0 unaccounted=0`), `s5e.out` (`5600bf1c…`), `s5e.cases` (`dd76a35d…`,
  regenerated byte for byte by `cases`), listed in `manifest.sha256` (`44d94245…`, 8 lines), which passes from `$D`.
  Development outputs (a 40-case-per-family run with `--limit 40`, two checks of the kept run by earlier tool
  revisions: the `phh` and `avoid` sites, a null-unit control crash, the state record's last three words not yet
  compared) are in `workspace/logs/n66t/s5e/dev1/` with `manifest-dev.sha256`, passing from there; none is cited.
- **Result:** 0 mismatches over 17 300 cases; every observed case reached its predicted boundary from its predicted
  site. Per family (cases; outcomes): `resist` 3 000; `absorb` 2 000; `pct` 2 500 (100: 1 891, 17: 416, 400: 111,
  25: 40, 200: 16, the difficulty column's value: the rest); `len` 1 500; `thm` 2 500; `phh` 1 200 (156 at
  `STATE_ApplyTimed`); `mode` 600; `avoid` 2 500 (32 at the weapon-block check); `crit` 1 500 (245 at
  `UnitSetOverlayStat`). 127 controls (each named test reversed alone, each ordered compare's strictness switched
  alone, and two spec-reading controls): 118 separate with `passed` 0. The 9 that change no case are strictness
  switches at a boundary where both sides give the same output: `r_ltcap~` (`r = cap`), `absorb` `p_ge40~`,
  `p_gt0~`, `d_le_f~` (40, 0 and `d = f` give the same result), `len` `pois_gt0~`, `burn_gt0~` (zeroing a 0), `thm`
  `p_gt0~`, `p_le0~`, `p_ge100~` (a 0 or 100 percent gives the same `DEF`).
- **Not covered:** the callees after each observed boundary (`STATE_ApplyTimed`, the weapon-block check and its
  draw, `UnitSetOverlayStat`), x87 (none in these functions), who calls these functions and with which units in play,
  and the meaning of every offset read (each keeps its own tag: the MonsterData `+0x16` bits, the MonStats bytes,
  the context fields).

## run:2026-11-16-sweep2-s5e2

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S5e part 2 (`lane/n66t`): the stat
events, the player's life tick and `COMBAT_BuildDamage` under Ghidra's p-code emulator on the pinned image (ADR-0015,
ADR-0021), compared with `tools/` models. No game, no wine. The claims are in
[combat/0001 § 20](0001-formulas.md#20-plan-0066-batch-s5e-part-2-stat-events-life-tick-and-the-damage-builder-run2026-11-16-sweep2-s5e2).

- **Question:** do `STATEVENT_CrushingBlow`, `STATEVENT_OpenWounds`, `STATEVENT_Freeze`, `sub_00580610_LifeRegenTick`
  and `COMBAT_BuildDamage` (attacker without an inventory), run on declared inputs, give the outputs the combat specs
  (at `b5999f5e`) state as inferred, including the branches no logged event reached?
- **Setup:** `tools/combat_s5e2_emu.py` (sha256 `156dae37…`, stdlib; imports `tools/combat_s5e_emu.py` unchanged for
  its unit, stat-list, MonStats and arithmetic builders), `re/ghidra_scripts/EmuBoundary.java` unchanged, Ghidra
  12.1.2, project `workspace/ghidra-n66t` (`-Xmx3G`, symbols imported in part 1). One kept launch of
  `tools/ghidra.sh emuboundary`, 5 families, 11 200 cases, seeds `random.Random("n66t-s5e2-<family>")`, part 1's
  MonStats image `random.Random("n66t-s5e-image")` and a MonType table `random.Random("n66t-s5e2-montype")`.
- **Memory spec** (`s5e2.mem`): part 1's scratch DataTables (state count, MonStats 0x240 random records, ItemStatCost
  0x200 zero records) plus the MonType table at `+0xC40` (count 40), `+0xC44` (`montype.bin`), `+0xC48` (stride 2).
  Units as part 1, plus each list's state chain (`+0x14` state, `+0x2C` next = 0, `+0x3C` the list itself or 0,
  `+0x40` = 0) so `UNIT_FindStatListByState` walks only case memory, and the `bd` attacker's inventory `+0x60` = 0.
  Guards: the fatal path 0x00408090, 0x00408A60, 0x00681E09 and the allocator 0x0040B4B0, 0x0040B430, 0x0040B480.
  **Observed boundaries (ADR-0021)**, return addresses checked per case: `sub_00627260_UnitSetStat` (`cb` 0x005C00FB,
  `regen` 0x00580673, `bd` the stat-120 write 0x0057B857), `STATE_ApplyTimed` (`ow` 0x005BFFA7),
  `COMBAT_ApplyDamage` (`frz` 0x005BFD7A), `UNIT_UnlinkStatList` 0x006277E0 (`regen` 0x00580655),
  `UNIT_DispatchEvent` (`bd` step 8, 0x0057BCB2), `sub_00621E40_UnitSetOverlayStat` (`bd` through
  `MonCritDouble`, 0x005A5641). Every other callee runs whole (the list is in the tool's docstring); no guard was
  reached and no import is on these paths (`STATLIST_FreeIfPlain` 0x00626CD0, the tick's only free, lies after the
  unlink boundary). The CRT `memset` 0x00681EF0 runs whole on 0x70 bytes, below its 0x100 test, so the SSE flag
  0x00994C88 is not read.
- **Read set (ADR-0015 (2)):** every traced read falls in `g_BitMask32` 0x006CE268 (`.rdata`), the PlayerHpPct table
  0x006E1590 (9 dwords, `.rdata`, read by `sub_005738F0_PlayerHpPct`) or the conversion switch table 0x0057BD94
  (12 dwords, `.text`); no traced write. The tool reads both tables from the pinned image for its model.
- **Procedure** (worktree root; `D=workspace/logs/n66t/s5e/run2`):
  ```
  python3 -I tools/combat_s5e2_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66t GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s5e2.cases $D/s5e2.mem > $D/s5e2.out
  python3 -I tools/combat_s5e2_emu.py check --dir $D > $D/check.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`03b6603a…`, 234 lines, last line `S5E2 total cases=11200 mismatches=0 stops=0
  controls=227 unseparated=53 controls_passed=0 unaccounted=0`; its `ROWS` line tallies the named points the matched
  cases reach), `s5e2.out` (`1bd848fc…`), `s5e2.cases` (`2ea8c7a2…`, regenerated byte for byte by `cases`), listed in
  `manifest.sha256` (`a5a0335d…`, 9 lines), which passes from `$D`. `check.txt` was written by the final tool
  revision; the revisions before it changed only the model's controls and tallies, not the cases (the regenerated
  case file has the kept hash). A development launch (`--limit 60`, 300 cases; its check found the `bd` overlay site
  written as 0x005A5646 for the return 0x005A5641, and null-unit controls that matched by a free seed) is in
  `workspace/logs/n66t/s5e/dev2/` with `manifest-dev.sha256`, passing from there; it is not cited.
- **Result:** 0 mismatches over 11 200 cases; every observed case reached its predicted boundary from its predicted
  site. Per family (cases; outcomes): `cb` 2 000 (837 at `UnitSetStat`, 1 163 returned 0); `ow` 1 500 (543 at
  `STATE_ApplyTimed`); `frz` 1 500 (443 at `COMBAT_ApplyDamage`); `regen` 1 200 (949 at `UnitSetStat`, 65 at the
  unlink, 186 returned at stat 74 = 0); `bd` 5 000 (2 682 returned, 1 307 at `DispatchEvent`, 598 at the stat-120
  write, 413 at the overlay). 227 controls (each named test reversed alone, each ordered compare's strictness switched
  alone, and spec-reading controls): 174 separate with `passed` 0. The 53 that change no case are strictness switches
  where both sides give the same output or the boundary value cannot occur: the clamps and floors at their own value
  (`cb` `n_ge1~`, `new_le0~`, `r36_ge100~`, `r36_gt0~`; `ow` `L_gt1~` and the five band edges, which the band
  formula joins continuously; `frz` `x_ge0~`, `ch_gt0~`, `ch_ge100~`, `ln_le25~`, `ln_ge250~`; `regen` `hp_lt256~`;
  `bd` `burn_ge0~`, `ph_gt0~`, `s31_ge0~`, `s121_gt0~`, `s122_gt0~`, `s326_gt1~`, `rp_b_le_m90~`, the four
  `t*_ge50~`), the draw tests at `hi = lo` (`RangeB` of 0 draws nothing: the seven `*_hi_gt_lo~` and
  `rp_hi_gt_lo~`), and values a multiple of 256 cannot take (`*_mx_ge8~`, `*_hi_gt0~` of the elements and drains,
  `rp_mn_lt1~`, `rp_mx_gt0~`; `s58_gt0~`, where `hi` = 0 returns the field whatever the percent).
- **Not covered:** the callees after each observed boundary (what `UnitSetStat`, `STATE_ApplyTimed`,
  `COMBAT_ApplyDamage`, `UNIT_DispatchEvent` and `UnitSetOverlayStat` do, and the caller's code after them: crushing
  blow's packet flag and overlay 147, the tick's life-percent message), the weapon paths of `COMBAT_BuildDamage`
  (`UnitGetWeapon` returns 0 in every case: the blunt bonus, the mastery crit, the two-handed test and the
  Weapons bonuses), x87 (none in these functions), who calls these functions and with which units in play, and the
  meaning of every offset read (each keeps its own tag).

## run:2026-11-16-sweep2-s5e3

Plan [0066](../../plans/0066-simulation-inferred-claims-sweep.md) Phase 1, batch S5e part 3 (`lane/n66t`): the
defence roll with a player's shield, `UNIT_GetDefense` and the `COMBAT_ApplyDamage` prologue under Ghidra's p-code
emulator on the pinned image (ADR-0015, ADR-0021), compared with `tools/` models, plus one recount of a kept log check.
No game, no wine. The claims are in
[combat/0001 § 21](0001-formulas.md#21-plan-0066-batch-s5e-part-3-the-defence-roll-with-a-shield-unit_getdefense-and-the-delivery-prologue-run2026-11-16-sweep2-s5e3).

- **Question:** do `COMBAT_DefenceRoll` (a player defender with an inventory), `UNIT_GetDefense` and the
  `COMBAT_ApplyDamage` prologue, run on declared inputs, give the outputs to-hit B1 and C2 and delivery B1 (at
  `b5999f5e`) state as inferred, including the walking exception and the three-draw path no logged event reached?
- **Setup:** `tools/combat_s5e3_emu.py` (sha256 `5f7cb4a6…`, stdlib; imports `tools/combat_s5e_emu.py`,
  `tools/combat_s5e2_emu.py` and `tools/anim_s6f_emu.py` unchanged), `re/ghidra_scripts/EmuBoundary.java` unchanged,
  Ghidra 12.1.2, project `workspace/ghidra-n66t` (`-Xmx3G`). One kept launch of `tools/ghidra.sh emuboundary`, 3
  families (`blk` 6 000, `def` 3 000, `adp` 3 000), seeds `random.Random("n66t-s5e3-<family>")`, part 1's MonStats
  image, S6f's item image (`random.Random("n66s-s6f-image")`) and this file's CharStats BlockFactor bytes and Skills
  calc words (`random.Random("n66t-s5e3-image")`).
- **Memory spec** (`s5e3.mem`): one scratch DataTables at 0x21000000 holding part 1's state count, MonStats and
  ItemStatCost, S6f's CharStats layout (`+0xBC4`, 7 records, `+0x49` BlockFactor and `+0x4C` code), ItemTypes bits
  (`+0xBFC`–`+0xC04`) and a Skills table (`+0xB98`, 64 records of 0x23C, `+0x138` the calc word); the items table
  pointer pair 0x0096CA58 (32 records) and `g_ItemWeaponClassIndex` 0x007446A0 as S6f declared them, and the page
  descriptor 0x0074479C = `0d 01`. Each case writes its units (part 1's builder), the defender's inventory (magic,
  page 0 at 13 × 1, so `sub_0063ADD0_InvPageGet` allocates nothing), two hand items with their data, the stat-348
  entries, the `def` state list (a second list at `+0x3C` or `+0x40` with base stats 350, 351) and the `adp` path,
  room, DRLG room and level, and PlayerData nodes. Guards: the fatal path 0x00408090, 0x00408A60, 0x00681E09 and the
  allocator 0x0040B4B0, 0x0040B430, 0x0040B480. **Observed boundaries (ADR-0021)**, return addresses checked per
  case: `SKILLS_EvalCalc` 0x00646CA0 (`def`, 0x006224BF) and 0x00621D50 (`adp`, 0x0057C793). Every other callee runs
  whole (the tool's docstring lists them); no allocator entry and no import is on these paths; `GameFindUnit` and
  `UNIT_AnimTransform` are not reached (the inputs keep their gates closed).
- **Read set (ADR-0015 (2)):** every traced read falls in `g_BitMask32` 0x006CE268 (`.rdata`), `g_WeaponClassTokens`
  0x006EB748 (13 pairs, `.rdata`) or `sub_006426A0_LevelIsTown`'s switch tables in `.text`: the index bytes 0x006426C8
  (109, the `cmp eax, 0x6C` at 0x006426A3 bounds the index) and the jump table 0x006426C0 (2 dwords, 0x006426AF); no
  traced write.
- **Procedure** (worktree root; `D=workspace/logs/n66t/s5e/run3`):
  ```
  python3 -I tools/combat_s5e3_emu.py cases --dir $D
  GHIDRA_PROJ_DIR=workspace/ghidra-n66t GHIDRA_HEADLESS_MAXMEM=3G systemd-run --user --scope -p MemoryMax=4G \
      tools/ghidra.sh emuboundary $D/s5e3.cases $D/s5e3.mem > $D/s5e3.out
  python3 -I tools/combat_s5e3_emu.py check --dir $D > $D/check.txt
  python3 -I tools/combat_s5e3_mas.py workspace/logs/combat/c37r-run2.lst workspace/logs/combat/p47h-run.lst \
      workspace/logs/combat/p47b-run.lst --no-shield-log <the nine p47h logs of the S5a part 1 record> > $D/mas-recount.txt
  (cd $D && sha256sum -c manifest.sha256)
  ```
- **Outputs:** `check.txt` (`ddbca2be…`, 112 lines, last line `S5E3 total cases=12000 mismatches=0 stops=0
  controls=107 unseparated=11 controls_passed=0 unaccounted=0`), `s5e3.out` (`43db2f08…`), `s5e3.cases`
  (`fbb5c9b4…`, regenerated byte for byte by `cases`), `mas-recount.txt` (`97495c77…`, 219 lines, `S5a2 total bad=0
  checker=0 part1-bad=0`; `tools/combat_s5e3_mas.py` `71109513…`), listed in `manifest.sha256` (`03b20edd…`, 16
  lines), which passes from `$D`. A development launch (`--limit 80`, 240 cases; its check found the room's
  `+0x10` hop and the switch tables undeclared) is in `workspace/logs/n66t/s5e/dev3/` with `manifest-dev.sha256`; it
  is not cited.
- **Result:** 0 mismatches over 12 000 cases; every observed case reached its predicted boundary from its predicted
  site. Per family: `blk` 6 000 (5 859 returned, 141 at the fatal path of `ITEMS_GetType` for an item class with no
  record, predicted; 2 113 with `b` ≥ 1, 608 divided, 295 moving at mode 2 undivided, draws 0/1/2/3 in 1 970 / 3 394 /
  490 / 5); `def` 3 000 (2 861 returned, 137 at `EvalCalc`, 2 fatal, predicted); `adp` 3 000 (2 706 returned, 216 at
  0x00621D50, 78 at the fatal path of `UnitGetRoom` for a null defender). 107 controls, 96 separating with `passed` 0.
  The 11 that change no case: `b_lt75~` and `wb_lt~` (equal values give equal outputs), and nine of S6f's
  `COMPOSIT_WeaponClass` tests (`f62`, `r2`, `s1is2`, `s1is3`, `s2is2`, `s2is3`, `s2is3b`, `swap`, `twoh`), whose
  outputs matter here only through index 13, which those branches do not change; S6f's own run separates them. The
  spec-reading controls: `spec_b_gt0_after` (C2's order) 2 and `spec_def_plain` (B1 for every `d`) 648, each
  `passed` 0.
- **Recount (README 35):** the two classic Nightmare/Hell calls of an `Align` = 1 class (257 `d1`, 405 `d2`) logged
  stats 19, 21, 22 all 0 and give 0 without the exception too, so they do not separate; 562 of the 598 others do.
- **Not covered:** `EvalCalc`'s value and the defence after it, the delivery after 0x00621D50, `UnitIsMoving`'s
  monster branch, a monster defender's block and three draws, `MonsterOwner`'s redirect (`GameFindUnit`), who calls
  these functions with which units, and the meaning of every offset read (each keeps its own tag).
