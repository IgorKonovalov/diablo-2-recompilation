# Stats experiments

Runtime records for [stats/0001](0001-aggregate.md) and [stats/0002](0002-states.md) (plan 0041 Phase 2). Harness
and evidence rules: ADR-0003, ADR-0004, ADR-0011, ADR-0013, ADR-0014;
[tooling](../../../.claude/skills/reverser/references/tooling.md),
[harness-play](../../../.claude/skills/reverser/references/harness-play.md).

## run:2026-10-17-stats

**Complete** (lane `lane/p41h`, 2026-10-17: 13 sessions before the checkpoint, 5 after the resume; the resume
note and its close are in the [plan 0041 log](../../plans/done/0041-stats-and-states.md#implementation-log)). 18 sessions,
**0 mismatches**.

- **Question:** plan 0041 Phase 2. Does `tools/stats.py`, the model of stats/0001 and stats/0002, reproduce every
  logged stat-list event of the player write for write (every Propagate, CacheAdd and CacheWrite a link, an unlink or
  an own write makes; the evaluation with its op terms and the take test), every stat read in a 50-frame window after
  a list change, the stat callback and its rescale, the requirement check, the set mask, the aprop toggles, the
  wearer's set list, the passive lists, every timed-state apply and expiry, the regeneration tick, the aura runs and
  durations and the timed shrines; and does every event kind leave the game seed and the acting unit's seed unchanged
  (the P1 review's draw-freedom amendment)?
- **Boundary** (P1 review): a skill's own `*calc` results with unit-reading variables, the shrine to-hit and damage
  values, monster AI and the combat appliers are value oracles; the passive calcs (`ln`/`dm`) are modelled with the
  level the list records in stat 351 as input; the item's required level (`0x0062B5B0`) and its own strength and
  dexterity contribution (`0x0062B450`) are value oracles of the requirement check.
- **Setup:** agent-driven sessions on harness slots 2 (`:9`, `workspace/wineprefix-2`) and 1 (`:8`,
  `workspace/wineprefix-1`), one session per slot at a time, single player, pinned `game.exe` in
  `workspace/runtime/game` (stock data), gdb by `tools/d2run.py` with `-seed` per session. Logger
  `tools/gdb/stats.gdb` (`d7a5df84…`) sourcing `tools/gdb/pilot.py` (`1ad48a4c…`) and `tools/gdb/stats.py`: r8
  `1872a47` (`40836c4f…`); r7 for `pal-crystal1` and `pal-crystal2` (r8 without the `ra2` caller chains, never
  committed on its own). Each log's first `STATSLOG` line names it. Breakpoints only print and continue. Driver
  `tools/stats_sessions.py` (`SESSIONS`: save, steps, seed, pilot steps) over `tools/d2pilot.py` `cube --plan`
  (inventory clicks; `clickv`/`keyv` repeat until a link or unlink line follows, `inv:open`, `settle:S,B`) and
  `farm`/`explore`/`objop --walk`. Each session: `saves.py --slot N restore`/`aside`, `d2run.py --install`, the
  steps, `slots.py stop N`.
- **Characters** (tool-built with `tools/d2s.py build`, stock rows; recipes in `tools/d2s_recipes/stats*.json`, built
  sha256 pinned in `tools/test_d2s.py`): `StatsBar` (Barbarian 80: Civerb's full set, Immortal King 4 of 6 with the
  Soul Cage failing strength, two Angelic Halo, ethereal War Boots, Headstriker + Bing Sz Wang on the switch,
  Annihilus, a +Masteries grand charm), `StatsBarB` (Paradox breast plate — an unspawnable prefix, a built state —,
  Sandstorm Trek, Highlord's Wrath, Bul-Kathos' ring, an unidentified Nagelring (test-state key `identified: false`),
  Messerschmidt's Reaver on the switch), `StatsBarC` (op coverage: Headstriker/Bing Sz Wang against Messerschmidt's,
  Ironpelt, The Stone of Jordan), `StatsPal` (Paladin 85 one experience point below 86: Prayer 12, *Azurewrath*
  (Sanctuary), an Act II Prayer mercenary), `StatsPalB` (Prayer 1, Doombringer, Ironpelt: the mercenary's higher
  Prayer replaces), `StatsBarD` (as `StatsBar` with strength 85: with the belt and gloves off the strength lands in
  115..124, where the ethereal War Boots (125) pass only with the −10), `StatsNec` (Necromancer: the full Trang-Oul's
  Avatar, whose full block sets the property `state` = `monsterset`), `StatsPalC` (Paladin with a low defence, to be
  poisoned in the Act III and Act II fields). Saves built into `workspace/logs/stats/p41h-saves/` from
  `workspace/samples/d2s/smp{bar,pal,nec}.d2s`.

### Sessions

| session | rev | link/unlink | CA/CW | reads | set lists | aprop toggles | req | passives | rescales | applies | expiry runs | ticks | aura durations | mismatches |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| barb-town1 | r8 | 4006 | 25166 | 91038 | 998 | 2970 | 2252 | 1704 | 500 | 0 | 0 | 79 | 0 | 0 |
| barb-town2 | r8 | 3986 | 25046 | 90541 | 993 | 2955 | 2241 | 1696 | 498 | 0 | 0 | 79 | 0 | 0 |
| barc-town1 | r8 | 1400 | 10350 | 20116 | 306 | 1020 | 1252 | 976 | 272 | 0 | 0 | 79 | 0 | 0 |
| bar-town1 | r8 | 3189 | 18865 | 30465 | 803 | 2965 | 1287 | 912 | 884 | 0 | 0 | 79 | 0 | 0 |
| bar-town3 | r8 | 3204 | 18918 | 30491 | 807 | 2985 | 1287 | 912 | 888 | 0 | 0 | 79 | 0 | 0 |
| palb-crystal | r8 | 462 | 7390 | 101865 | 0 | 0 | 540 | 0 | 17 | 228 | 141 | 5846 | 405 | 0 |
| palb-spider | r8 | 184 | 4621 | 48622 | 0 | 0 | 901 | 0 | 17 | 198 | 207 | 5840 | 334 | 0 |
| pal-crystal1 | r7 | 3 | 285 | 1520 | 0 | 0 | 70 | 0 | 0 | 39 | 40 | 958 | 39 | 0 |
| pal-crystal2 | r7 | 249 | 9938 | 53890 | 0 | 0 | 1120 | 0 | 30 | 643 | 457 | 5951 | 1049 | 0 |
| pal-glacial | r8 | 291 | 9048 | 49407 | 0 | 0 | 900 | 0 | 30 | 503 | 371 | 5951 | 822 | 0 |
| pal-oasis | r8 | 239 | 8365 | 45531 | 0 | 0 | 760 | 0 | 30 | 452 | 318 | 5951 | 746 | 0 |
| pal-spider | r8 | 152 | 6724 | 27647 | 0 | 0 | 850 | 0 | 30 | 425 | 348 | 5951 | 672 | 0 |
| pal-tundra | r8 | 338 | 11967 | 57466 | 0 | 0 | 780 | 0 | 30 | 453 | 326 | 5951 | 743 | 0 |
| bard-town1 | r8 | 2136 | 12792 | 20827 | 538 | 1990 | 858 | 608 | 592 | 0 | 0 | 79 | 0 | 0 |
| bard-town2 | r8 | 4144 | 24023 | 38533 | 1044 | 3860 | 1668 | 1184 | 1152 | 0 | 0 | 79 | 0 | 0 |
| nec-town1 | r8 | 1368 | 14870 | 18709 | 260 | 780 | 388 | 840 | 776 | 0 | 0 | 79 | 0 | 0 |
| palc-spider | r8 | 444 | 13355 | 100124 | 0 | 0 | 246 | 0 | 3 | 250 | 293 | 5860 | 498 | 0 |
| palc-oasis | r8 | 292 | 10319 | 65052 | 0 | 0 | 234 | 0 | 3 | 452 | 248 | 5828 | 899 | 0 |
| **all** | | **26087** | **232042** | **891844** | **5749** | **19525** | **17634** | **8832** | **5752** | **3643** | **2749** | **54719** | **6207** | **0** |

Seeds and sessions after the resume: `bard-town1` 4141 (2 cycles of the `statsbar` plan) and `bard-town2` 4142 (4
cycles, added to reach 30 decisive ethereal checks), `nec-town1` 4151 (4 cycles of `statsnec`; the first attempt
before the checkpoint failed on the dark Act IV town, its log kept as `s1017-nec-town1.log.failed-dark-town` and not
in the run), `palc-spider` 4171 and `palc-oasis` 4172 (`pal_field`, 50 hops). Slot 2 ran the first three, slot 1 the
Paladin sessions, side by side, one session per slot.

### Log manifest

| file | sha256 | what |
|---|---|---|
| `workspace/logs/stats/s1017-run.lst` | `a42758f3…` | the 18 session logs of the run, in check order |
| `workspace/logs/stats/s1017-manifest.txt` | `7fd7a93a…` | per log: sha256, size, line count (`tools/stats.py manifest`) |
| `workspace/logs/stats/s1017-check.json` | `677e12a6…` | the checker's report over the 18 logs |
| `workspace/logs/stats/s1017-check-p47r.json`, `.txt` | `4b94c8ef…`, `bf0d4613…` | the 2026-10-20 re-check (plan 0047 Phase 1) |
| `workspace/logs/stats/s1017-<session>.log` | in the manifest | the logger's output, one per session |
| `workspace/logs/stats/s1017-<session>.plan`, `.pilot.txt`, `-shots/` | — | the click plan, the driver's output, screenshots |
| `workspace/logs/stats/p41h-saves/*.d2s` | `tools/test_d2s.py` | the built characters |

Check: `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/stats.py check $(cat
workspace/logs/stats/s1017-run.lst) --json workspace/logs/stats/s1017-check.json`, `tools/stats.py` at commit
`27f49ad` (`a6f77ece…` before its docstring line; the logic is that commit's): **0 mismatches**. Notes, not
checks: 180 full Trang-Oul's set lists not predicted (the model builds no `state` or `oskill` property list), one
event open at a log's end (the session killed inside it).

- **Not an oracle** (P2 review; *checked since the 2026-10-20 re-check*, below): the 180 full Trang-Oul's lists are not
  an ADR-0004 boundary oracle (the set list is in scope, and ADR-0004 never oracles in-scope code). They were an
  **unchecked remainder** at the run: the model takes each
  logged list as the input of the events after it (its propagation, the `monsterset` clear, the `oskill` passive),
  which are predicted; the seeds are checked at the link around it; the Sets count excludes them (5 569 of 5 749),
  and the content of a full block with a `state` or `oskill` property stayed `[I]` until the 2026-10-20 re-check
  predicted all 180. (fn:sub_00660120_SetBonusApply@0x00660120, run:2026-10-17-stats)
- **Re-check at the review** (2026-10-17, `main` `af90ea8` merged): the manifest re-hashed (18 logs: sha256, size
  and line count equal); `tools/stats.py check` over the 18 logs in this order gives a report byte-identical to
  `s1017-check.json`, and in the reversed order and in a shuffled order (`random.Random(41)`) 0 mismatches with
  identical counts and seed tallies (only the aura grid's cross-log gaps and the first 20 wells of the report differ).
  The pre-fix checker (`27f49ad^`) on the shuffled order fails once (`aura_rng`, `s1017-pal-tundra.log:613`: the
  open aura run at the end of `palc-oasis` carried into the next log), so the per-log reset is the fix.
- **Re-check 2026-10-20** (plan 0047 Phase 1, `lane/p47r`; the checker items of the P2 review's backlog entry):
  `tools/stats.py` `98538acf…` and `tools/test_stats.py` `d7d6b0c6…` (15 tests, the well and recharge-shrine
  predictions, the negative stat-74 tick and the 256 floor, the set blocks, and two written logs for the per-log
  reset, the per-log aura gaps and the chained pairs). The same command, `--json
  workspace/logs/stats/s1017-check-p47r.json` (`4b94c8ef…`; printed report `s1017-check-p47r.txt`, `bf0d4613…`):
  **0 mismatches**. Against `s1017-check.json` only these change: the set-list note is gone (the 180 full
  Trang-Oul's lists are predicted, so all 5 749 wearer lists are checked); the aura grid's gaps are taken within each
  log (`h/sel` 1 014, `p/item` 893, `p/sel` 1 699 gaps, all 50; the negative cross-log gaps are gone); three counts
  are new: `aura_chained_pairs` 746, `aura_chain_breaks` 115 and `aura_drawing_runs_without_next_run` 4 (865 drawing
  runs). In the reversed order the report differs only in the first 20 wells listed. `oracle-player` now prints a
  consistency count, not a replacement: `CONSISTENCY player level-ups=20 consistent=13 not_consistent=7 replaced=0`.
  (fn:sub_00660120_SetBonusApply@0x00660120, fn:PROP_Func24_ParParam@0x0065F390, fn:SKILLS_RollElemDamage@0x0056E0C0,
  run:2026-10-17-stats)

### Results

- **Draw-freedom** (seeds equal at entry and exit, game and acting unit): link 12 868, unlink 12 853, own write
  101 995, toggle 19 525, apply 6 232, expire 2 749, tick 54 719, aura 2 763 — every kind ≥ 20; **shrine 7 and well 5
  fall short** of 20. The aura kind moved the caster's seed in 865 runs, each by exactly the `RNG_RangeB` calls of
  `SKILLS_RollElemDamage` from `sub_005CF3A0_AuraHitDo` (Sanctuary's hit): each such run's exit is asserted
  against its entry advanced by its logged draws (865). Chained pairs in the ADR-0014 sense (the next run of the
  same caster entering on that exit): 746, counted at the review by a scratch pass over the AU0/AU1 lines and, since
  the 2026-10-20 re-check, by the checker (`aura_chained_pairs` 746, keyed by the caster unit; 115 next runs entered
  elsewhere, 4 drawing runs had no next run in their log). The game seed moved in one aura run (a kill dropped an item).
- **Reads:** 891 844 in the 50-frame windows after each list change, 120 stat ids. **Ops** in predicted writes: 1 348,
  2 1 490, 4 2 568, 5 26, 8 919, 9 3 784, 11 92, 13 136 (every stock op ≥ 20). Ops 3, 6, 7, 10, 12: no reachable row.
- **Recomputes:** 26 087 links and unlinks, 232 042 CacheAdd/CacheWrite, 9 level changes. **Sets:** 5 749 wearer
  lists (5 569 predicted at the run, 180 full Trang-Oul's taken as logged; all 5 749 predicted at the *Re-check
  2026-10-20* above), 19 525 aprop toggles by add func 0/1/2.
- **States:** 3 643 applies (refresh 2 608, refuse 1 013, replace 2, new 20), 2 749 expiry runs (123 lists freed,
  lateness 0), 3 629 aura runs on the `≡ 1 (mod 50)` grid, 6 207 aura durations = `perdelay + 1`.
- **Counted shortfalls** (P2 review): the plan's 300 expiries read as freed lists are **123** (potion states 178–180
  79, state 21 18, state 113 11, poison 2 7, 86 5, shrines 130/131 2, Conviction 28 1); the 2 749 event-12 runs each
  check the free set, the 2 630 that freed nothing included. The 50 aura on and off events are **9**: an aura state
  new 6 (47 five, 28 one), replaced 2, ended 1 (28); Prayer's and Sanctuary's states never ended. The rule both
  rest on (the timed expiry, the apply cases) is `[C]` on the counts above; no claim is raised on the shortfall.
  (fn:EVENT_TimedListExpire@0x00580800, fn:STATE_ApplyTimed@0x0056E970, run:2026-10-17-stats)
- **`group`:** 450 `STATE_GroupClear` calls, 180 effective (the full Trang-Oul's `monsterset` cleared when the set
  breaks, self argument 1). A clear of a different state of one group: **not reached**.
- **Ticks:** 54 719, of which 1 082 with a negative stat 74 (poison, `StatsPalC`): the stat-74 tick under poison is
  reproduced. **Not reached:** the floor at 256 life, open wounds.
- **Requirements:** 17 634 checks; the ethereal −10 decided 30 (`bard-town1` 10, `bard-town2` 20); stat 91 decided
  none (814 checks with it); level, class and broken-item branches not reached.
- **Shrines and wells (named shortfall):** 7 shrines (3 timed: codes 8, 10; 4 recharge on a full player) and 5 wells,
  all predicted, 12 against the plan's 50. `objop --walk` operates only what the field explore activated (about one
  per session); raising it would need sessions that only hunt shrines, which this resume did not run.
- **Oracle replacement:** **none replaced** (P2 review). run:2026-10-16-player (`workspace/scratch-h34p2/player-run.lst`,
  `fef9a539…`): `python3 -I tools/stats.py oracle-player $(cat …)` finds 13 of its 20 level-up maxima
  (`UnitGetMaxHp/Mana/Stamina`, value oracles there) equal to the player's own entries and 7 not. That is a
  consistency check, not a replacement: the 14 level-ups of the built characters carry 9 or 10 items each (recipes
  `tools/d2s_recipes/lv*.json`) and the 6 new characters their starting items, the logs hold no child list, and "no linked child adds to 7, 9 or 11" is concluded
  from the equality itself (levels 1 and 9 equal, 49 and 97 differ, consistent with item requirements, not shown).
  The maxima stay value oracles until a run logs the lists. run:2026-10-16-combat logs values, not lists: its stat
  oracles are **not replaceable** from the kept logs.

## The stats sessions of run:2026-10-20-shortfalls

The run is one run under two checkers; its combat half and its definition are in
[combat/experiments § run:2026-10-20-shortfalls](../combat/experiments.md#run2026-10-20-shortfalls).

- **Question:** plan [0047](../../plans/0047-simulation-shortfalls.md) Phase 2, the stats cases: do the shrine and
  well operates, an aura state's end, the expiries, a different-state `group` clear, the 256 floor, the curse
  resistance cut and a curse refused on a monster in `attract` reproduce under `tools/stats.py`, with the boundary of
  run:2026-10-17-stats?
- **Setup:** slot 2 (`:9`, `workspace/wineprefix-2`), tag `p47h`, as the combat record of this run. Logger
  `tools/gdb/stats.gdb` (`d7a5df84…`) with `tools/gdb/stats.py` rev 9 (`1df37219…`, commit `820bdc3`: `STA` on a
  monster target with `STATS_MONSTA`); every log's `STATSLOG` line says rev 9. Driver `tools/stats_sessions.py run
  --slot 2 --tag p47h --saves workspace/scratch-p47h/saves --run p47h …` (final revision `ecd86f9b…`), `tools/d2pilot.py`
  (`--curse-keys`, and `--dead-below`, new). Environment `STATS_TICKS=6000 STATS_OBJS=1` (and `STATS_MONSTA=1` for the
  Necromancer).
- **Characters** (pinned in `tools/test_d2s.py`): `StatsNecA` (`21b42e85…`, new at this phase's first step: a
  Necromancer with Attract and Amplify Damage, ruling 2), `StatsPalD` (`9fd320d2…`), `StatsSor` (`963ed380…`),
  `StatsAss` (`5eb48cc0…`), `StatsDru` (`58cc838b…`), `StatsFloor` (`82db5212…`), `StatsPalC` (`3c3a1fe3…`), `StatsPot`
  (`a18f03a9…`).

### Sessions

| session | seed | save | what | stats checker | the case's count |
|---|---|---|---|---|---|
| nec-attract1 | 4781 | StatsNecA | Cold Plains: Attract (F1), then Amplify Damage (F2) twice on the same monster | 0 mismatches | 71 curses in attract, 71 refused |
| pald-auras1 | 4731 | StatsPalD | Cold Plains: Might, Defiance, Prayer by key, 30 switches | 0 | 31 on, 30 off |
| pald-auras2 | 4732 | StatsPalD | as above | 0 | 30 on, 29 off |
| sor-armours | 4751 | StatsSor | the three armours cast in turn (group 1) | 0 | 20 different-state clears |
| ass-fade | 4752 | StatsAss | Fade and Quickness in turn (group 2) | 0 (after the checker fix below) | 23 |
| dru-shapes | 4753 | StatsDru | Werewolf and Werebear in turn (group 3) | 0 | 0 checked (below) |
| floor-poison1 | 4771 | StatsFloor | Spider Forest, explore 80 hops, no potion | 0 | no poison taken |
| floor-poison2 | 4772 | StatsFloor | Far Oasis, as above | 0 | no poison taken |
| ass-curses1 | 4761 | StatsAss | Worldstone Keep (the walk stayed in Level 2) | 0 | no curse on the player |
| palc-wells1 | 4721 | StatsPalC | Far Oasis (2,5): the field steps, then `objop --walk` for wells and shrines (no well of the 6 asked) | 0 | 2 shrines (code 14), no well |

Not part of the run (development logs under `workspace/logs/stats/`, kept, no claim on them):
`dev-p47h-pot-town1-act4`, `dev-p47h-pot-town2-act4` (the potion plan's `inv:open` failed four presses; in
`pot-town1` the potion clicks then walked the character out of the Pandemonium Fortress to her death),
`dev-p47h-pot-town1-invopen`, `dev-p47h-pot-town2-invopen` (Rogue Encampment waypoint first: `inv:open` failed again;
the 40 potions fill the grid that the dark-centre test reads), `dev-p47h-pot-town1-keyi`, `dev-p47h-pot-town2-keyi`
(one key press instead: still no inventory potion drunk, 4 lists freed by belt potions the waypoint step's pilot drank;
the cause was not found in this lane), `dev-p47h-floor-poison1-orb` (the pilot read the 1 % life orb as a death and
stopped at the first hop; `--dead-below 0` since). Not run: `pot-town3`/`4`, `ass-curses2`, `palc-wells2`,
`sor-shrines1`…`10` (`sor-shrines1` stopped by the lane before its game started: no log), `nec-attract2`/`3` (attract met
on the first). `floor-poison1` also operated one shrine (code 6).

*Review 2026-10-21 (the machine suspend, 23:17 to 06:25).* No log of the run list spans it: the last session before it,
`dev-p47h-pot-town2-keyi`, ended at 23:15:25 (gdb's `exited normally`; its driver's output was written after the
resume and ends in a screenshot-path traceback), and the first after it, `floor-poison1`, was launched at 06:19:27. A
first `floor-poison1` launch at 23:15:33 ran across the suspend and logged no event (its game exited on resume); it is
kept as `workspace/logs/stats/p47h-floor-poison1.log.failed1` (`06b1601b…`), a development log outside the run, not
in `p47h-manifest.txt`. The potion plan's cause: commit `b7dec78`'s message (and its code comment) blamed the
Pandemonium Fortress's dark floor for `inv:open`'s failure; the Rogue Encampment sessions failed the same way, and
commit `3236965` gives the cause found, the 40 potions filling the grid that `inv:open`'s dark-centre test reads (its
comment replaces the earlier one). With the one key press still no inventory potion was drunk, for a cause not found (above).

### Results

Check: `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/stats.py check $(cat
workspace/logs/stats/p47h-run.lst) --json workspace/logs/stats/p47h-check.json`, `tools/stats.py` `23f34c4d…` (commit `121233e`): **0 mismatches** over the 10 logs (`p47h-run.lst`,
`044518a7…`; per-log sha256, size and lines in `p47h-manifest.txt`, `6acd5060…`, with the 9 dev logs; report
`p47h-check.json` `63892df3…`, `p47h-check.txt` `08c102f7…`). Seeds equal at entry and exit: apply 658, monster apply
239, aura 383, expire 455, link 526, unlink 524, propagate 549, own write 22 784, tick 27 192, shrine 3. Scripts and
outputs: `p47h-auraonoff.py`/`.txt` (`a3bb65b2…`, `67eaaa99…`), `p47h-grpclear.py`/`.txt` (`3fbd6f5f…`, `333738ca…`); `p47h-logs.sha256` (`16574241…`) checks
every log and output with `sha256sum -c` from `workspace/logs/stats/`.
`tools/d2pilot.py` `f8164f3d…` for the sessions after its `--dead-below` change (`floor-poison1`, `floor-poison2`,
`ass-curses1`, `palc-wells1`). The same checker over `s1017-run.lst` gives a JSON byte-identical to `s1017-check-p47r.json`, and
`tools/test_stats.py` passes.

**Checker fix** (`tools/stats.py`, commit `121233e`): the item-type index skipped no row, while the loaded
`itemtypes` table has no record for the `Expansion` separator row (index 58 of the `.txt`), so every expansion type
was one high; the Assassin's claw-mastery passive (skill 252, param `h2h`, 67 in all 23 logged lists) was predicted
68 in `ass-fade`. The kept run's passives (Barbarian masteries, types below row 58) are unchanged.

- **Attract** (`nec-attract1`): 71 curse requests (Amplify Damage) on monsters in state 57, all refused (no list), and
  151 curses on monsters not in it, all made, in the same window; 16 Attract casts made. Both seeds equal at the entry
  and exit of all 239 monster requests. The refusal test of `STATE_ApplyTimed` on a monster target holds as read
  (stats/0002 § 2). (fn:STATE_ApplyTimed@0x0056E970, run:2026-10-20-shortfalls)
- **An aura state's end** (`pald-auras1`/`2`, `p47h-auraonoff.py`): 61 aura lists made (states 33, 34, 37) and 59
  unlinked when the next aura key switched the skill, 120 events. All 59 ends are unlinks called from
  `sub_005701B0_PlayerSetSkill` (return `0x005702E1`) before the state's timed expiry freed it (no aura list was
  freed by event 12 in either log), each an emulated `ULK` checked write for write; each aura duration as predicted
  (109). (fn:sub_005701B0_PlayerSetSkill@0x005701B0, fn:UNIT_UnlinkStatList@0x006277E0, fn:STATLIST_Unlink@0x006269F0,
  run:2026-10-20-shortfalls)
- **Different-state `group` clears** (`p47h-grpclear.py`): 43 calls of `STATE_GroupClear` cleared a state of the same
  group other than the one applied (group 1: frozen 10, chilling 20, shiver 88 armour, 20; group 2: Fade 159 and
  Quickness 157, 23), each `GRX` bit set as predicted. Group 3 (`dru-shapes`): 12 calls for Werebear (140) found
  Werewolf (139) set, and Werewolf's bit was gone at the nested call that followed, but these 12 calls log no exit
  line of their own (`GRX`), so the checker does not check them and they are not counted.
  (fn:STATE_GroupClear@0x0056C740, run:2026-10-20-shortfalls)
- **Named again:** the 256 floor (0: neither field poisoned `StatsFloor`); the curse resistance cut (0: no witch
  cursed `StatsAss`); the expiries: 30 lists freed this run (the shapes 24, the armours 3, `palc-wells1` 3; lateness 0
  in all), 153 with the kept run's 123, against 300: the potion plan that was to give about 220 drank nothing
  (above); shrines and wells: 3 shrines (codes 14 twice, 6 once; draw-free, the timed state as predicted) and no well,
  15 with the kept 12, against 50. *2026-10-21 (Phase 2b):* the potion plan did drink; its waits were too short for the
  logger's frame rate, so each healing potion refreshed the last one's list ([the Phase 2b record](#staging-fixes-each-found-in-a-log-of-this-lane)).
  The floor sessions' character levelled up at its first experience and refilled its life (both logs, frames 498 and
  678).

## The stats sessions of run:2026-10-21-shortfalls2

The run is one run under three checkers (plan [0047](../../plans/0047-simulation-shortfalls.md) Phase 2b, the
staging-limited cases of Phase 2): this section holds its stats sessions and its definition; the combat sessions are in
[combat/experiments § run:2026-10-21-shortfalls2](../combat/experiments.md#run2026-10-21-shortfalls2), the travel
sessions in [quests/experiments § The travel sessions of run:2026-10-21-shortfalls2](../quests/experiments.md#the-travel-sessions-of-run2026-10-21-shortfalls2).

- **Question:** do the stats cases Phase 2 named again for staging reasons (the expiries, group 3's clears, the curse
  resistance cut, the 256 floor, shrines and wells) reproduce under `tools/stats.py` once the staging is fixed, with
  the boundary of run:2026-10-17-stats?
- **Setup:** slot 2 (`:9`, `workspace/wineprefix-2`), tag `p47b` (an empty aside, restored at the end). Logger
  `tools/gdb/stats.gdb` (`d7a5df84…`) with `tools/gdb/stats.py` **rev 10** (`2dc46547…`, commit `22c856d`: the
  `GRP`/`GRX` calls kept on a stack with their depth `dp`, below); `pot-town1` was launched before that change and
  logs rev 9 (its `STATSLOG` line; it has no `GRP` line). Driver `tools/stats_sessions.py run --slot 2 --tag p47b
  --saves workspace/scratch-p47b/saves --run p47b …` (final revision `dcbd27f8…`, commit `600f2ca`; the sessions'
  rows are its `SESSIONS`), `tools/d2pilot.py` `114a7003…` (the edits during the run, the `frames:` token, `--done`
  with several tags and the `descend` path search, touch commands other sessions did not use before their change).
  Environment `STATS_TICKS=6000 STATS_OBJS=1`, and `STATS_TICKS=40000` for the potion sessions (ticks, and with them
  the `fr` the `frames:` token reads, all session).
- **Characters** (pinned in `tools/test_d2s.py`): `StatsPot` (`a18f03a9…`), `StatsDru` (`58cc838b…`), `StatsFloor`
  (`82db5212…`), **`StatsFloorB`** (`f52e4148…`, new: `statsfloor.json` with the experience at level 85's start,
  below), `StatsAss` (`5eb48cc0…`), `StatsSor` (`963ed380…`).

### Staging fixes (each found in a log of this lane)

- **The potion plan (the expiries).** The dev session `dev-p47b-pot1` (`ef20d3cf…`; seed 4741, `StatsPot`, Pandemonium Fortress,
  then the Rogue Encampment) showed the right clicks drink: every clicked cell emptied and the first potion of each
  kind linked a list (the screenshots). What failed was the timing: the plan's waits were wall-clock seconds sized at
  25 frames a second (a healing potion every 8 s against `healthpot`'s 192 frames), but the game runs at about 17 under
  the stats logger (173 frames in 10 s, measured in that log), so each healing potion was drunk while the last one's
  list was still linked and `STATE`'s refresh moved its expiry instead of linking a new list (`EXP0` at frame 1 222:
  the `healthpot` list's expiry 1 606). No list was freed while the drinking went on, which Phase 2 read as "drank
  nothing". Fix: the cube token `frames:N` (waits on the log's server frame), 210 frames between healing potions and
  840 between the three timed potions (750 frames).
- **Group 3 (the exit line).** `STATE_GroupClear` is re-entered: Werebear's clear of Werewolf calls it again for 139
  before it returns. Logger rev 9 kept one open call, so the nested call's exit cleared it and the outer call wrote no
  `GRX`. Rev 10 keeps a stack and writes the depth (`dp`) on both lines; `tools/stats.py` (`85e14b94…`) pairs them by
  depth (rev 9 lines, without `dp`, as before) and counts `group_clear_nested` and `group_clear_holding_nested`;
  `tools/test_stats.py` (`d35d9b42…`, 18 tests) adds the nested pair, a wrong outer exit and the rev 9 pairing.
- **The curse resistance cut.** `StatsAss` has no Teleport, so `ass-curses`' route (waypoint to the Worldstone Keep
  Level 2, `farm --descend 81` up to Level 1, which Teleports) cannot leave Level 2 (`ass-curses2`: "12 hops without
  moving"). A field with a stock curse-caster on the player's own waypoint: the Crystalline Passage (5,4), whose
  Levels row 113 lists `succubus3`, skill `Defense Curse` (309), state 113 `defense_curse` with States `curse` 1 (the
  kept run's 11 state-113 expiries came from there). `tools/stats.py` counts each player curse request whose
  `curse_resistance` is 1..99 (`apply_curse_cut`); a test covers the cut, a non-curse state and the refusal at 100.
- **The 256 floor.** Three causes, in turn: (1) neither Phase 2 field has a Normal poisoner (MonStats `El*Type`
  `pois` with Normal damage, against Levels' `mon1`..`mon10`/`umon` columns): the Halls of the Dead Level 2 (2,4) and
  the Lost City (2,6) do; (2) `StatsFloor`'s recipe experience, 1 145 236 814, is `experience.txt` row 85, the
  experience at which level **86** begins (row N is level N+1's start: row 1 is 500), so the first experience the
  character gets (a melee kill, or *The Gladiator's Bane*'s attacker damage) levels it up and the level-up fills life
  to the maximum: `floor-poison3`, `-4` and `-5` at frames 436, 512 and 1 080 (14 175 → 780 032 in 1/256 units, max
  life +2), as were both Phase 2 floor logs (frames 498 and 678); **`StatsFloorB`** is the same character at row 84's
  1 050 299 747; (3) left at 30 life, the character's own items work against the case: *Kerke's Sanctuary*'s `regen`
  15 (stat 74 +15 a frame, the logged `TK0` value) raised life from 30 to 267 before the first Plague Bearer's poison
  at frame ~4 000 (`floorb-poison2`), *The Gladiator's Bane* halves poison length (`res-pois-len` 50) and two
  *Nature's Peace* add `res-pois` 20–30 each. Those items also give the damage reduction (58 flat) that keeps the
  30-life character alive against Normal hits (`zombie5` A1 55–137), and the stock items with flat damage reduction
  and none of these properties (*Arkaine's Valor* 15, *Rockfleece* 5, *Goblin Toe* 1, *The Patriarch* 3,
  *Lazarus Spire* 5, *Steel Carapice* 14, *Ironward* 7: the `uniqueitems.txt` scan of this lane) do not reach it.
- **Shrines and wells.** `shrine_hunt` went from the waypoint straight to `objop`, which explores nothing (it
  operates only objects already listed): now rounds of `explore` (25 hops) and `objop --obj-mem --done SHR1,WEL1`
  (`--done` takes several tags), a wait past the re-arm, the shrines again. The pilot read `StatsSor`'s life orb
  (1 500 of 6 000) as empty and stopped each `explore` after one hop (`dev-p47b-sor-shrines1`): `--dead-below 0`.

### Sessions

| session | seed | save | what | stats checker | the case's count |
|---|---|---|---|---|---|
| pot-town1 | 4741 | StatsPot | Rogue Encampment, 40 inventory and 16 belt potions on `frames:` waits (logger rev 9) | 0 mismatches | 52 lists freed |
| pot-town2 | 4742 | StatsPot | as above | 0 | 47 |
| pot-town3 | 4743 | StatsPot | as above | 0 | 52 |
| dru-shapes2 | 4754 | StatsDru | Werewolf and Werebear in turn, 12 rounds | 0 | 12 group-3 clears, each with its nested call |
| dru-shapes3 | 4755 | StatsDru | as above | 0 | 12 |
| ass-curses3 | 4763 | StatsAss | Crystalline Passage (5,4), Fade, walking melee explore | 0 | 24 curses cut |
| ass-curses4 | 4764 | StatsAss | as above | 0 | 28 |
| ass-curses2 | 4762 | StatsAss | Worldstone Keep Level 2 (the warp up not reached, no Teleport) | 0 | 2 (shrine curses 133, 134) |
| floor-poison3 | 4773 | StatsFloor | Halls of the Dead Level 2, melee explore | 0 | 0 (levelled up at frame 436; no poison) |
| floor-poison4 | 4774 | StatsFloor | Lost City, melee explore | 0 | 0 (levelled up at 512; 808 poisoned ticks at full life) |
| floor-poison5 | 4775 | StatsFloor | Halls of the Dead Level 2, walk and stand, no melee | 0 | 0 (levelled up at 1 080) |
| floorb-poison1 | 4791 | StatsFloorB | Halls of the Dead Level 2, walk and stand | 0 | 0 (no poison) |
| floorb-poison2 | 4792 | StatsFloorB | Lost City, walk and stand | 0 | 0 (567 poisoned ticks from life 267) |
| sor-shrines2 | 4702 | StatsSor | Stony Field (1,3): four explore and operate rounds, the re-arm wait, again | 0 | 1 shrine (one listed in the whole session) |

Not part of the run (development logs under `workspace/logs/stats/`, kept, no claim on them): `dev-p47b-pot1` (the
potion diagnosis above), `dev-p47b-sor-shrines1` (the one-hop explores; stopped by the lane), `dev-p47b-floor-poison6`
(stopped by the lane at its start once floor-poison5 showed the level-up), `dev-p47b-floorb-poison3` (the game stopped
at frame 1 859 with gdb holding it, state `t`, no `internal-error` line; stopped by the lane). Staged, not run:
`floorb-poison4`, `sor-shrines3`…`10`, `palc-wells2`, `pot-town4`.

### Results

Check: `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/stats.py check $(cat
workspace/logs/stats/p47b-run.lst) --json workspace/logs/stats/p47b-check.json`, `tools/stats.py` `85e14b94…`: **0
mismatches** over the 14 logs (`p47b-run.lst` `1ce4d0b9…`; report `p47b-check.json` `30641747…`, `p47b-check.txt`
`0d6ca631…`; `p47b-logs.sha256` `db24c111…` lists every run log, dev log, plan, pilot output, script and output, and
passes `sha256sum -c` from `workspace/logs/stats/`). Seeds equal at entry and exit: apply 606, aura 544, expire 1 401, link 940, unlink 945, propagate 1 485, own
write 66 458, tick 81 448, shrine 6. Scripts and outputs: `p47b-grpclear.py`/`.txt` (group clears by depth),
`p47b-cursecut.py`/`.txt` (curse durations asked and given), `p47b-expiries.py`/`.txt` (lists freed by state):
`2e6eacf4…`, `9d6b6489…`, `48a47d6f…`. The same checker over `s1017-run.lst` and `p47h-run.lst` gives JSONs
byte-identical to `s1017-check-p47r.json` and `p47h-check.json` (`p47b-recheck-s1017.json` `4b94c8ef…`,
`p47b-recheck-p47h.json` `63892df3…`): the rev 10 pairing leaves rev 9 logs as they were. `tools/test_stats.py` passes
(18 tests).

- **Expiries:** 296 lists freed (`expired_lists`; the free set of each of the 1 401 event-12 runs as predicted,
  lateness 0): `healthpot` 106, `antidote` 16, `thawing` 15, `staminapot` 15, `manapot` 1, `poison` 49, `skilldelay`
  48, `defense_curse` 42, the shrine states 133 and 134 4. **449** with the 153 of run:2026-10-17-stats and
  run:2026-10-20-shortfalls: the 300 are met. (fn:EVENT_TimedListExpire@0x00580800, run:2026-10-21-shortfalls2)
- **Group 3:** 24 `STATE_GroupClear` calls for `bear` (140) cleared `wolf` (139), each with the nested call for 139
  (depth 2, 24) inside it and both exits' bits as predicted (`group_clear` 124, of which nested 24, holding a nested
  call 24, effective 27). With groups 1 and 2's 43 (run:2026-10-20-shortfalls), 67 different-state clears.
  (fn:STATE_GroupClear@0x0056C740, tbl:States.txt:group, run:2026-10-21-shortfalls2)
- **The curse resistance cut:** 54 player curse requests with `curse_resistance` 84 (Fade level 20): 52
  `defense_curse` (42 new, 10 refreshes) asked 275 frames and got 44, the two shrine curses asked 3 600 and 2 400 and
  got 576 and 384 (`p47b-cursecut.txt`): `len - MulDiv(len, 84, 100)` in all three lengths, each list's expiry as
  predicted. (fn:STATE_ApplyTimed@0x0056E970, 0x0056E9C9–0x0056EA4A, run:2026-10-21-shortfalls2)
- **Named again, final:** the 256 floor: **0** (no tick floored; 1 431 poisoned ticks, none from below 256 life): the
  stock data gives no character that is poisoned at the floor and survives Normal hits there, since the only items
  that keep a 30-life character alive (flat damage reduction 58) carry `regen` or poison resistance and length, and
  the stock items without them reach 50 at most (above); the floor stays `[I]` on the code reading and
  `tools/test_stats.py`'s case. Shrines and wells: **6** shrine operates this run (codes 11 once, 12 three times, two
  recharges on a full player), **21** with the kept 15, against 50: in four explore rounds of 25 hops the Stony Field
  listed one shrine (`sor-shrines2`), so the hunt yields about one operate in 12 minutes of slot time; the 29 missing
  would take about six hours of `sor-shrines` sessions, which this lane did not have (a tool reason: the fix tried is
  the explore rounds; Act I fields list few shrines). The re-arm and a well's cure stay unreached.
  (fn:sub_00580610_LifeRegenTick@0x00580610, fn:OBJOP_Shrine@0x00583C70, run:2026-10-21-shortfalls2)
