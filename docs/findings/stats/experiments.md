# Stats experiments

Runtime records for [stats/0001](0001-aggregate.md) and [stats/0002](0002-states.md) (plan 0041 Phase 2). Harness
and evidence rules: ADR-0003, ADR-0004, ADR-0011, ADR-0013, ADR-0014;
[tooling](../../../.claude/skills/reverser/references/tooling.md),
[harness-play](../../../.claude/skills/reverser/references/harness-play.md).

## run:2026-10-17-stats

**In progress** (lane `lane/p41h`, rotated at a checkpoint 2026-10-17; the resume note in the
[plan 0041 log](../../plans/0041-stats-and-states.md#implementation-log) lists what is left). The sessions below are
complete and checked; the record is finished by the resuming lane.

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
  Prayer replaces). Not yet run: `StatsBarD`, `StatsNec`, `StatsPalC` (see the plan log).

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
| **all** | | **17703** | **156683** | **648599** | **3907** | **12895** | **14240** | **6200** | **3226** | **2941** | **2208** | **42794** | **4810** | **0** |

Logs: `workspace/logs/stats/s1017-*.log`, run list `s1017-run.lst` (`14aa1fbb…`, 13 logs), per-file sha256 in
`s1017-manifest.txt` (`82a50af3…`); `python3 -I tools/stats.py check $(cat workspace/logs/stats/s1017-run.lst)
--json …/s1017-check.json` under `systemd-run --user --scope -p MemoryMax=4G`, `tools/stats.py` at the checkpoint
commit: **0 mismatches**. Seeds unchanged at entry and exit: link 8 856, unlink 8 841, own write 67 592, toggle
12 895, apply 4 835, expire 2 208, tick 42 794, shrine 4, well 3, aura 2 064; the aura kind moved the caster's seed in
865 runs, each by exactly the `RNG_RangeB` calls of `SKILLS_RollElemDamage` (Sanctuary's hit), chained.
