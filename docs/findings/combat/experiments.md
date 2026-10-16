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
| mercenary attack `ha` | 1 259 | 993 | 265 | 588 / 350 / 321 | 1 005 / 254 |
| missile on the player or the mercenary `md` | 1 957 | 1 957 | 0 | 375 / 396 / 1 186 | |
| the player's Nova missile `pm` | 519 | 519 | 0 | 0 / 219 / 300 | |
| `MonAttackStats` | 5 060 | 5 060 | 0 | | 167 with an El applied |

Resynchronisations inside events (named, entry taken as logged): a delivery on a later frame than the hit test (362
at `COMBAT_ApplyDamage` entry, 112 at the exit with no delivery, 1 early return whose reason is not logged; the AI drew
on both seeds in between; 216 of those queued packets were changed by the mercenary's skill before delivery, taken as
input), and 7 monster skill do-functions that drew between the hit test and the build (seed taken at the build).

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

**Shortfalls** (named, not blocking; their claims stay `[I]`): the **hireling boss percent in Hell** (25, against
`MonsterCEDamagePercent` 20): Andariel was not reached in Hell in two attempts; two further sessions
(`sor-h-andariel-nova2`, `-nova3` in `SESSIONS`) were not run for lack of time. **Open wounds on an act boss**: none
(the two Andariel kills had no open-wounds hit on her). **Crushing blow on an act boss** 1 event, **on a superunique**
5, **on a champion** 0 as labelled (the checker labels a unit with the unique bit first). **Evade, weapon block,
dodge, avoid**: 0 (no character had those stats). **Conversion, freeze and the freeze handler, pierce, flat absorb,
the PvP 17 % and the hireling-against-hireling 25 %, magic at or above the cap, magic immunity**: not reached. **The
player's stat-74 tick** (`0x00580610`): no window on the player. `MonAttackStats`: 167 El applications, but only
its draws are modelled, not the stats it writes, so monsters/stats § H stays `[I]` for its outputs.

- **Conclusion:** the claims of [combat/0001](0001-formulas.md) reproduced here move to `[C]` (§ 15 of the finding),
  each naming its value oracles; the shortfalls above keep theirs at `[I]`.
