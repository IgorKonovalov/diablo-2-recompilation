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

### Addendum 2026-11-15: plan 0066 batch S4d, part 1 of 2: static second sources and full-table checks (`lane/n66i`)

- **Question.** Which of the S4d `[I]` rows of class (c) in [stats/aggregate](../../specs/stats/aggregate.md) and
  [stats/states](../../specs/stats/states.md) does a second tool on the code or a full-table check raise? Inventory rows:
  [stats-aggregate](../../plans/0066-inventory/stats-aggregate.md), [stats-states](../../plans/0066-inventory/stats-states.md).
  Part 2 (the a-logs rows over this run's and the shortfalls logs, and aggregate rows 5 and 40) is not done here.
  (data:g_ShrineEffects@0x006E1850, fn:STATE_GroupClear@0x0056C740, fn:STATE_ApplyTimed@0x0056E970)
- **Setup and procedure.** As [items/experiments § Addendum 2026-11-15 (S4c)](../items/experiments.md#addendum-2026-11-15-plan-0066-batch-s4c-new-checks-over-the-kept-inventory-logs-and-static-second-sources-lanen66i):
  `tools/sweep2_s4cd.py` (`271e96c8…`), sections `ststatic` and `tables`, in the one kept run
  `workspace/logs/n66i/check.txt` (`fdf66219…`, `S4 total bad=0`, `manifest.sha256`). Second tools: objdump (the States
  loader, `PlayerSwapWeapons`, the walker), r2 (`g_ShrineEffects`, `PlayerSwapWeapons`, the LCG sites), the raw-byte scan
  (call sites). Tables: `states.txt`, `pettype.txt`, `skills.txt`, `sets.txt`, `montype.txt`.
- **Observed** (`check.txt`):
  - `states5`: objdump reads `STATES_Load` (0x00618100 up to `DATATBLS_LoadAll`): 91 field descriptors built on the
    stack (name, type, bit), constants tracked through registers. 46 have type `0x1A`; 40 of them are States.txt columns,
    with bits 0..39 each once (`curse` 11, `plrstaydeath` 13, `monstaydeath` 14, `exp` 30, `life` 32); the other 6
    (`warp`, `range`, `partysend`, `unsummon`, `automap`, `drawhp`, bits 0..5) are PetType.txt columns built in the same
    range.
  - `states16_51`: `STATE_GroupClear` has 9 rel32 call sites, no abs32: `MonStatCallback` 0x0055BDA3, 0x0055BDB6;
    `ItemUseTimedState` 0x005BEE15 (the only one in 0x005BE130..0x005BF3D0); `ShapeRemoveCb` 0x005C6C5B, 0x005C6CB2;
    `SkillDo116Shapeshift` 0x005C6F20; `SkillDo18TimedSelfState` 0x005C94F4; `SkillSt28BladeShield` 0x005D7A9C;
    `SkillSt38Whirlwind` 0x005D9195. `STATE_ApplyTimed`'s direct closure (1 999 functions, objdump) does not hold it.
  - `states14`: `STATE_ApplyTimed` has 25 rel32 call sites in 25 functions, no abs32: its own (0x0056EC9E),
    `PreventHealHook`, `SHRINE_ApplyState`, `SHRINE_Skill`, `STATEVENT_OpenWounds`, `AURA_ApplyToTarget`, and 19 more:
    `UModElemDamage`, `MissHit21BattleCry`, `StatEv19Slow`, `CurseApplyCb`, `SkillDo59Attract`, `ConfuseApplyCb`,
    `StatEv27ClayGolemSlow`, `SkillDo18TimedSelfState`, `SkillDo23TimedState`, `SkillDo25Enchant`,
    `SkillDo29ThunderStorm`, `WhipApplyState`, `SkillDo133Impregnate`, `CloakAreaCb`, `SkillDo47Cloak`,
    `SkillSt28BladeShield`, `SkillSt38Whirlwind`, `SkillDo06UnitCb`, `MonFleeFrom`.
  - `states34_42`: r2 reads `g_ShrineEffects` as 24 entries of {fn, stat, state}: codes 6..15 give the spec's G2 pairs
    (6 → 171, 128; 7 → state 129; 8 → 39, 131; 9 → 43, 132; 10 → 41, 130; 11 → 45, 133; 12 → 11, 134; 13 → 27, 135;
    14 → 162, 136; 15 → 85, 137), no other code a state. States row 128 (`shrine_armor`) names `armorclass`.
  - `agg34`: `PlayerSwapWeapons` (395 instructions, 52 direct calls, none indirect) has one caller, `SwapWeaponsReq`
    0x0054CEB0; it calls `ITEMS_DetachFromOwner` at 0x005617C4 and 0x005617D8, each behind its own `test edx, edx`, and
    `ITEMS_AttachToOwner` at 0x0056192B (objdump and r2 alike).
  - `states46`: closures (objdump walker) and r2's LCG sites: `STATE_GroupClear` 463 functions, `StatListsPurgeOnDeath`
    447, `StatListsDropOnMode` 457, none with a draw. `STATE_DefaultRemoveCB`: 1 996 functions, 122 with a draw, all
    under its call of `PetLimitRefresh` (0x0056E960); the shortest path is `PetLimitRefresh` → `PetLimit` → `PetRemove` →
    `PetUnitRelease` → `MonSetMode` → `MonAttackStats` (draw). Its other 8 call sites (7 functions) reach none.
  - `states31` (table): 79 Skills rows with an `aurastat` or `aurastatcalc`: no `aurastat` after a blank one; 6 stats with
    no calc (`Tiger Strike`, `Fists of Fire`, `Cobra Strike`, `Claws of Thunder`, `Blades of Ice`, `Royal Strike`, the
    `progressive_*` stats); 1 calc with no stat (`Holy Shield`).
  - `agg38` (table): 10 named Sets param cells: 4 first hit in skills (Trang-Oul's `Fire Ball`, `Fire Wall`, `Meteor`,
    `Fire Mastery`), 6 in states (`fullsetgeneric` ×5, `monsterset`); none named in two of the three tables.
- **Outcome by row:** raised 4 (states 16, 34, 42, 51), raised in part 5 (aggregate 34, 38; states 5, 14, 31), raised in
  part and contradicted in part 1 (states 46: the remove callback). Part 2 holds the other 34 S4d rows.
- **Contradicted in part, states 46.** stats/states' draw table says "none found in the code" for the remove callback.
  Its direct-call closure reaches 122 drawing functions through `PetLimitRefresh` (a player's pet limits; a pet over a
  lowered limit is released, its mode set). Whether an expiry ever takes that path on stock (a state whose end lowers a
  summon limit) is not read; the run's 2 749 expiries left the seeds unchanged (§ Results). A static reading of one tool
  (the walker) with r2's sites agreeing, no case. Backlog as for S4c.

### Addendum 2026-11-15: plan 0066 batch S4d, part 2 of 2: new checks over the kept stats logs and static second sources (`lane/n66i`)

- **Question.** Which of the other 34 S4d rows (aggregate 2–4, 6, 8–13, 16–17, 19, 23–26, 29, 31–32, 36–37, 39, 41–42,
  and 5, 40; stats/README 1; states 13, 17, 23, 32, 37, 41) and the part-1 remainders (aggregate 34, states 5, 14, 46)
  do a new check over the kept logs, or a second tool on the code, raise? Inventory rows:
  [stats-aggregate](../../plans/0066-inventory/stats-aggregate.md), [stats-README](../../plans/0066-inventory/stats-README.md),
  [stats-states](../../plans/0066-inventory/stats-states.md). (fn:STATLIST_LinkToUnit@0x00626E10, fn:STATE_ApplyTimed@0x0056E970)
- **Setup and procedure.** No game, no Ghidra. `tools/sweep2_s4cd.py` (`59d67950…`), new sections `ststatic2` and
  `stlogs`, `tools/test_sweep2_s4cd.py` (13 tests). One kept run, `python3 -I tools/sweep2_s4cd.py ststatic2 stlogs`
  under `systemd-run --user --scope -p MemoryMax=4G` (57 s): `workspace/logs/n66i/check-part2.txt` (`a2cbf09c…`,
  105 lines, `S4 total bad=0`), `manifest-part2.sha256` passing from `workspace/logs/n66i`; development outputs in `dev/`
  under `manifest-dev-part2.sha256`. `all` still reproduces part 1's `check.txt` byte for byte. `stlogs` reads each log
  of `workspace/logs/stats/s1017-run.lst` (run:2026-10-17-stats, 18 logs) and `p47h-run.lst` (run:2026-10-20-shortfalls,
  10 logs) once, through `tools/stats.py`'s checker (`85e14b94…`; 0 mismatches in both runs, as kept) with observers on
  its lines and two model controls computed beside each predicted write (`op11_running`: op 11 a percentage of the
  running total; `op89_full`: op 8/9 add the source's full value). `ststatic2` reads the code with objdump next to r2
  or the raw bytes, the closures with the objdump walker next to r2's own LCG-multiplier sites.
- **Observed** (`check-part2.txt`; s1017 / p47h counts):
  - Fields and flags. Every unlinked list's logged `+0x34` equals its parent in the mirrored tree (13 039 / 524 ULK),
    every child's `+0x04` equals the unit of the extended list it hangs under (2 745 / 663 distinct tree nodes), and
    every new player state list's `+0x34` is the unit list (20 / 90). 4 228 / 826 `STATE_ApplyTimed` returns give state,
    skill, level and end frame `= frame + duration` as requested (4 203 / 623 durations not a multiple of 25), and 20 / 85
    new lists show `+0x08` = the source's type. List flags, on lists the apply made (a refresh returns the list it
    found, 0x0056EACC, whatever made it; 2 610 / 383 such returns are not counted): `0x2` with a duration 20 / 90,
    `0x8` exactly on the States `aura` rows (states 28, 47, 33, 37, 157: 58 lists; 52 lists of other states, none with
    it), `0x800` on none (no logged state has `exp`), `0x22` on the six shrine lists of states 128, 130, 131, 136 (all
    `curse` = 1). In the trees, `0x40` is on every non-extended child of an item list (329 / 89) and on nothing else.
    `0x2` without an end frame: the player's unit list (state 0, extended; 9 / 10 nodes, the drop-on-mode marker
    `STATLIST_LinkToUnit` sets, below), and the potion lists of states 178–180 dumped between their link and their end
    write (84 seen with the end later; 2 never dumped again).
  - Entries. 1 582 / 316 own and 201 / 113 cache arrays of two or more entries, all strictly ascending; no own entry of
    value 0; 162 / 36 entries a writer emptied (`SetStatEx` 56 / 44, the clear at 0x006273D3 524 / 53; `AddStat` none)
    absent from the next tree. 6 007 / 37 extended lists linked or unlinked with cache ≠ own: the checker's predicted
    propagations of the cache matched each.
  - Controls. `op11_running` predicts another value for 74 / 12 of the 5 827 / 125 checked writes (stats 7 and 9);
    `op89_full` for all of them. The stock model matched every one.
  - ISC. In all 28 dumps the 97 `opIn` edges are the table's `op stat` cells as written, including 273
    (`item_maxdamage_percent_bytime`) → 22, 23, 159 and 237, 291 → 147 (`item_absorbmagic`).
  - Callers. Item-list links: 5 973 through `ITEMS_AttachToOwner`, 70 / 39 through `sub_00627910_StatListLinkOwner`
    alone. Item-list unlinks: 5 695 through `ITEMS_DetachFromOwner`; **278 through `sub_0063AAF0_InvItemRemove` →
    `UNIT_UnlinkItemStatList` (the body-to-cursor pickup, `Pkt1CBodyToCursor`), 260 of them with no detach of that item
    in the frame**; 60 / 39 under `sub_0055F140_KeyConsume`; 10 unattributed. Set items: a `SETS_UpdateOnEquip` mode 0
    before each attach (5 749), mode 1 before each detach's unlink (5 593). Without damage: 32 links, all of `bl` 5.
    Through `StatListLinkOwner`, no item of `bl` 11 or 12 linked or unlinked; no `DMG` line in either run.
  - The weapon switch (76): its direct detaches and attaches touch `bl` 4 and 5 only: 4+5 → 4+5 (24), 4+5 → 4 (26),
    4 → 4+5 (26); the rest under it (336 each) belong to the refresh it runs.
  - Catch-up. Inside the link of an item list holding an op-4/5 source, 2 361 changed writes during a refresh, 337
    outside one, 2 594 unchanged.
  - Sets. Swapping add func 1 and 2 predicts other toggles in 2 039 of the 3 905 `TIP` calls with func 1 or 2. 2 850 trees
    with two or more set lists: the unit list's stat 71 equals the sum of its children's stat 71 in all 4 996 trees with one.
  - Passives. 7 848 / 52 `SKILLS_RefreshPassive` calls returned the list's 351 (the equal branch) and changed nothing;
    984 / 4 returned another value and rebuilt, each with a new 351. objdump and r2 read the test: `push 0x15F`;
    `call 0x625D00`; `cmp eax, [ebp−4]` (`SKILLS_GetSkillLevel`'s value); `je 0x646F0A`; and the two free paths (no
    unit skill, `aurastate` on the unit).
  - The stat callback: a zero-crossing write of 98 is followed in its frame by a group clear (360); of 83, 97, 127, 188 by
    `SKILLS_RefreshPassive` (180, 1 920, 48, 2 006 / 2+2); 151's ten by unlinks; a non-crossing write of 204 by a link
    and an unlink (4 / 4). Keys
    107 and 126 were not written; the item-event registration is not logged.
  - The refresh's frames: the commonest gap is 136 in 12 of the 18 s1017 logs and all 10 p47h logs (1 in the other six:
    refresh bursts after actions); all gaps: 136 651 / 157, 1 569 / 13; the top 136-residue class is unbroken in 10 / 10
    logs and has holes in 8.
  - Seeds: 972 refresh windows with two or more seed-carrying lines (115 634), no seed moved; 119 / 30 expiry runs that
    freed a list, seeds equal at entry and exit.
  - States. Stamina ticks: all 54 719 / 27 192 equal E3; with `staminarecoverybonus` ≥ 1000, mode 3 gained in 4 326 ticks
    where a no-bonus reading writes nothing; mode 4 with the bonus was not reached. Item aura restarts (5): the first item
    tick fell on `NextPeriodicFrame(restart)`, not `restart + p`, and no frame had two item ticks. The stamina shrine's
    two applies: remove callback 0x00583A40, the list holding stat 28 = 1 000 alone at its first dump. Expiries: the freed
    state's bit was off at the next states line 147 times, on once (s1017). Elemental lists: poison only (17), plain, `0x2`,
    an end frame, `+0x08` 1.
  - Static. `StatListsDropOnMode` (callers `UNIT_SetMode` 0x006246BE and the client's 0x004B0D5A) acts only when the unit
    list has `0x2`, frees every `+0x3C` child with `0x4` (clearing its state, freeing a plain one) and clears the `0x2`;
    `STATLIST_LinkToUnit` sets the unit list's `0x2` on a flag-4 link. `STATLIST_Alloc`'s 71 calls: flag bit 2 as an
    immediate at 7 (`SkillAttackRateList`, `SKILL_MeleeDeliverDo`, `MonModeVelocity` 0x4004, `SkillSt32Hit`,
    `RunVelocityStat`, two client ones), a register at 7. `UNIT_HasState` (0x00639DF0) answers only for unit types 0, 1
    and 3 and 0 otherwise; `UNIT_TestStateBit` has no type test; `UNIT_SetStateBit` sets `+0xC8` bit 3 when the States
    record's `+0x12` bit 0 (`disguise`, loader bit 16) is set and clears it only when `UNIT_HasStateFlag(unit, 16)` finds
    none left. The monster gate is at 0x0056E9C7–0x0056EA08: type 1, MonStats (`0x1A8` rows) `+0x0D` & 1 refuses,
    MonStats2 `+0x05` & 2 clear refuses (objdump; the raw bytes agree at 6 sites). `STATE_DefaultRemoveCB` calls, in order,
    0x005C0B50 (nearest symbol `UNIT_AddEvent`), `UnitIsDead`, `STATES_StaysOnDeath`, `STATE_Set(…, 0)`,
    `UNIT_AnimSetRate`, `SKILLS_RefreshPassivesInState`, and for a type-0 unit `PetLimitRefresh`. The mask byte
    0x006CE27C (`0x20`) is referenced 39 times; 9 sites test a record's `+0x04` with it (`EVENT_SelectedAuraTick`,
    `AuraSelect`, `PlayerSetSkill` ×2, `MissileCreate`, `ITEMAURA_Start`, `ITEMAURA_Stop`, `SummonInitStats`,
    `MERCAI_PickSkill`). Closures: `SetBonusApply` 433 functions and `SKILLS_RefreshPassive` 480, no draw;
    `EquipReqRefresh` 1 993 functions, 122 drawing, the shortest path through `PlayerSkillReselect` → `PlayerSetSkill` →
    `AuraSelect` → `SKILLS_SrvDo` → `PlayerModeCmd` → `PlayerModeAllowed`, and through its attach and detach calls.
- **Outcome by row (34):** raised 12, raised in part 13, raised in part and contradicted in part 4 (aggregate 2, 4, 41;
  stats/README 1), contradicted in part 2 (aggregate 29, 42), not raised 3 (aggregate 9, 13, 24). Part-1 remainders:
  aggregate 34 now raised whole; states 5 contradicted in part (its other half raised); states 14 and 46 keep a
  remainder. Per row in the inventory notes.
- **Contradicted in part.** (1) aggregate 2, stats/README 1 (and H2's scope): an item taken from the body to the cursor
  is unlinked by `InvItemRemove` → `UNIT_UnlinkItemStatList`, not `ITEMS_DetachFromOwner` (260 cases with no detach).
  (2) aggregate 41: the requirement refresh's code reaches drawing functions (the skill reselect path); 972 logged
  refreshes drew nothing. (3) states 5: `UNIT_HasState` answers for players, monsters and missiles (type 3), not objects
  (type 2 answers 0). (4) aggregate 4: `0x2` on the unit list is the drop-on-mode marker, not "timed". (5) aggregate
  29, 42: 136 is the commonest gap in 22 of the 28 logs, not in every session (six s1017 logs: 1). Backlog
  [`2026-11-15-reverser-spec-writer-plan-0066-s4c-s4d-corrections`](../../backlog/archive/2026-11-15-reverser-spec-writer-plan-0066-s4c-s4d-corrections.md).

## The stats sessions of run:2026-10-20-shortfalls

The run is one run under two checkers; its combat half and its definition are in
[combat/experiments § run:2026-10-20-shortfalls](../combat/experiments.md#run2026-10-20-shortfalls).

- **Question:** plan [0047](../../plans/done/0047-simulation-shortfalls.md) Phase 2, the stats cases: do the shrine and
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

The run is one run under three checkers (plan [0047](../../plans/done/0047-simulation-shortfalls.md) Phase 2b, the
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
- **Named again, final:** the 256 floor: **0** (no tick floored; 1 431 poisoned ticks, none from below 256 life): on
  the staged route (a 30-life character kept alive in Normal by flat damage reduction) the only items that keep it
  alive (flat damage reduction 58) carry `regen` or poison resistance and length, and the stock items without them
  reach 50 at most (above); the floor stays `[I]` on the code reading and `tools/test_stats.py`'s case. *Review
  2026-10-21:* a stock-data limit of that route only; a character with more life drained to the floor by poison
  alone was not tried and is out of this plan. Shrines and wells: **6** shrine operates this run (codes 11 once, 12 three times, two
  recharges on a full player), **21** with the kept 15, against 50: in four explore rounds of 25 hops the Stony Field
  listed one shrine (`sor-shrines2`), so the hunt yields about one operate in 12 minutes of slot time; the 29 missing
  would take about six hours of `sor-shrines` sessions, which this lane did not have (a tool reason: the fix tried is
  the explore rounds; Act I fields list few shrines). The re-arm and a well's cure stay unreached. *Review
  2026-10-21:* the yield is measured on one session (`sor-shrines2`), and `palc-wells2` was not run, so the well's
  cure was not tried in this phase; both are final as a slot-time ruling of the review, out of this plan, not as a
  stock-data limit.
  (fn:sub_00580610_LifeRegenTick@0x00580610, fn:OBJOP_Shrine@0x00583C70, run:2026-10-21-shortfalls2)

## run:2026-10-27-p51s-emu

Static, no game and no slot (plan 0051 Phase 1b, `lane/p51s`). Two items of the backlog sweep, each optional:
the op 6/7 emulation (backlog entry of 2026-10-17, from the plan 0041 P1 review) and the re-run of
run:2026-10-16-calc-emu under `EmuTrace` (the plan 0038 S1e review follow-ups, (b)).

- **Question:** (1) Do `STAT_ByTimeValue` and `sub_00626200_StatEvaluate`'s cases 6 and 7 do what
  [stats/0001](0001-aggregate.md) § 4 reads, on inputs no stock play reaches? (2) Does run:2026-10-16-calc-emu's
  read set, written from a code read in [data/0005](../data/0005-calc.md) § 11, match what the tool traces?
- **Setup:** Ghidra 12.1.2 p-code emulator on the pinned `game.exe`, lane copy
  `GHIDRA_PROJ_DIR=workspace/ghidra-p51s` (symbols replayed from `re/symbols.csv`), heap 3 GB, under
  `systemd-run --user --scope -p MemoryMax=4G`, one headless instance at a time. Script `re/ghidra_scripts/EmuTrace.java`
  (unchanged; its sha256 is in `tools-revisions.txt`). Models, case writers and checks: `tools/sweep_p51s.py`
  (families `bytime`, `op67` seeded `p51s-<family>`; `calcemu-cases`/`calcemu-check` over the kept files of
  `workspace/logs/calc-emu/`, manifest `4ca75152…`, which still checks). It reuses `tools/sweep_s1e.py`'s report and
  read-set accounting, `tools/sweep_s1f.py`'s `MulDiv` model and guards (the allocator and fatal-path entries), and
  `tools/calc_funcs.py`'s checkers unchanged. Files in `workspace/logs/p51s/emu/`: `manifest.txt` `b16c2780…`
  (79 files, `sha256sum -c` passes from that directory), `check.txt` `7ee746af…`, `commands.txt`, `tools-revisions.txt`
  (the sha256 of each tool and script behind the outputs), and the empty stderr of each run in `stderr/`.
- **Procedure:** `commands.txt`: `sweep_p51s.py cases` and `calcemu-cases`; one `tools/ghidra.sh emutrace` per family
  (2) and per kept calc-emu run (11); `check`, `static`, `calcemu-check` into `check.txt`; `manifest --write`.
- **Observed** (`check.txt`; `neg` = the negative control's mismatches or failure, `undeclared` = traced accesses
  outside the declared read set):
  ```
  P51S bytime cases=6000 match=6000 bad=0 neg=3302 traced=0 undeclared=0 stopped=0 neg_floor=2416
  P51S op67 cases=3000 match=3000 bad=0 neg=2110 traced=5 undeclared=0 stopped=0 neg_b0=1103
  P51S static cases=0 match=0 bad=0 neg=0 traced=0 undeclared=0 stopped=0 callers_0061C100=12 callers_00626200=10 callers_0065CA30=8 jt_ok=1 mask_ro=1 pins=43 pins_ok=43 ro_tables=3
  P51S calcemu-skills_min cases=5000 match=5000 bad=0 neg=1 traced=0 undeclared=0 stopped=0 model_check_rc=0 neg_vs_skills_max=4972 pop_ok=5000 same_as_kept=1
  P51S calcemu-skills_max cases=5000 match=5000 bad=0 neg=1 traced=0 undeclared=0 stopped=0 model_check_rc=0 neg_vs_skills_min=4972 pop_ok=5000 same_as_kept=1
  P51S calcemu-skills_rand cases=5000 match=5000 bad=0 neg=1 traced=0 undeclared=0 stopped=0 model_check_rc=0 neg_vs_miss_rand=2913 pop_ok=5000 same_as_kept=1
  P51S calcemu-items_min cases=5000 match=5000 bad=0 neg=1 traced=0 undeclared=0 stopped=0 model_check_rc=0 neg_vs_items_max=4972 pop_ok=5000 same_as_kept=1
  P51S calcemu-items_max cases=5000 match=5000 bad=0 neg=1 traced=0 undeclared=0 stopped=0 model_check_rc=0 neg_vs_items_min=4972 pop_ok=5000 same_as_kept=1
  P51S calcemu-items_rand cases=5000 match=5000 bad=0 neg=1 traced=0 undeclared=0 stopped=0 model_check_rc=0 neg_vs_miss_rand=2913 pop_ok=5000 same_as_kept=1
  P51S calcemu-miss_min cases=5000 match=5000 bad=0 neg=1 traced=0 undeclared=0 stopped=0 model_check_rc=0 neg_vs_miss_max=4972 pop_ok=5000 same_as_kept=1
  P51S calcemu-miss_max cases=5000 match=5000 bad=0 neg=1 traced=0 undeclared=0 stopped=0 model_check_rc=0 neg_vs_miss_min=4972 pop_ok=5000 same_as_kept=1
  P51S calcemu-miss_rand cases=5000 match=5000 bad=0 neg=1 traced=0 undeclared=0 stopped=0 model_check_rc=0 neg_vs_skills_rand=2913 pop_ok=5000 same_as_kept=1
  P51S calcemu-miss cases=5000 match=5000 bad=0 neg=1 traced=34 undeclared=0 stopped=0 model_check_rc=0 same_as_kept=1
  P51S calcemu-eval cases=236 match=236 bad=0 neg=1 traced=6 undeclared=0 stopped=0 model_check_rc=0 same_as_kept=1
  ```
  The `op67` traced reads are `StatEvaluate`'s jump table (4 slots) and the mask 0x006CE270. For the calc-emu
  re-run: the nine calc functions read nothing outside their case memory. `MISS_CalcVar` read 34 slots of its own
  jump table 0x0064B62C (indexed at 0x0064B394, codes 0–42), and `MISS_EvalCalc` 2 of them, 3 slots of `CALC_Eval`'s
  0x006C1164 (at 0x006C0C07) and `g_nMissCalcFuncs` (0x00745848, 234 reads). Every output is byte-identical to the
  kept output of 2026-10-16. The kept checkers pass on it, and fail on it with every EAX + 1 (`neg=1`). The nine calc
  functions also differ from a sibling's kept output on 4 972 (min against max) or 2 913 (one table's `rand` against
  another's) lines.
- **Conclusion:** (1) The op 6/7 arithmetic of stats/0001 § 4 is reproduced bit for bit, with every branch reached,
  as a map from the declared inputs. It raises § 10 of stats/0001 to `[C]` under ADR-0015, run id this record. The
  meaning of `owner +0x1C` and its record stays `[I]`. (2) The calc-emu read set: the tool finds the two `.text`
  switch tables (`MISS_CalcVar`'s 0x0064B62C and `CALC_Eval`'s 0x006C1164), which data/0005 § 11's list omits.
  Both lie in the read-only `.text` (`sweep_p51s.py static`), so no claim changes. The addendum is in
  [data/0005 § 11](../data/0005-calc.md#11-static-emulation-of-the-functions-and-the-missile-context-run2026-10-16-calc-emu).
  (fn:STAT_ByTimeValue@0x0065CA30, fn:sub_00626200_StatEvaluate@0x00626200, fn:MISS_CalcVar@0x0064B340,
  fn:MISS_EvalCalc@0x0064B7C0)

## Pointer: plan 0066 batch S4e part 1, the stats family

Record: run:2026-11-16-sweep2-s4e-emu. Plan 0066 batch S4e (`lane/n66z`), part 1: the stats family (the readers' `fMin` floor, the maxima getters,
`StatEvaluate`'s ops 2, 3, 10 and 12, `StatRecompute`'s take test) under emulation. The record is kept with the
batch's items parts in [items experiments](../items/experiments.md#run2026-11-16-sweep2-s4e-emu); the claims are in
[stats/0001 § 11](0001-aggregate.md#11-plan-0066-batch-s4e-part-1-the-stats-family-under-emulation-run2026-11-16-sweep2-s4e-emu).
(fn:sub_00624F60_StatListGetValue@0x00624F60, fn:sub_006266C0_StatRecompute@0x006266C0)
