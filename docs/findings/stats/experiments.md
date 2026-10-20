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
