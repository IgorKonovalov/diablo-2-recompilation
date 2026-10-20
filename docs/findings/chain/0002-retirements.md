# 0002 — The in-chain oracles retired, and the composition checked with them modelled

> **Subsystem:** chain (seed to world, plan 0048)
> **Question:** can each oracle the Phase 0 review assigned (chain/0001 § 4: 2, 14, 16, 17, 22, 19, 21, 20, 7, 6, 13) be replaced by a model from code the specs already cite, and does `tools/chain.py check` pass on the kept logs with those callees predicted?
> **Date:** 2026-10-20   **Plan:** 0048 (Phase 1)   **Status:** open (Phase 1 in progress)

Phase 1 runs no harness session. Each model is checked on kept logs of earlier runs (re-analysis); the logs are named
per oracle with their manifests. `tools/chain.py` is the composition: `gen` builds what the game seed alone fixes,
`check` replays a log through the reviewed checkers with every retired oracle switched to its model and counts the
oracles still taken from the log.

## Answer (summary)

- [C] **Oracle 2 (`ITEMS_RollStaffMods`) is retired**: the staff-mods model is the default of `tools/affixes.py`,
  `tools/items_chain.py` and `tools/chain.py`; 3 991 + 3 170 creations of the 133 kept item logs reproduce with no
  staff-mods seed from a log, 99 exit seeds and 64 skill entries predicted (§ 2). (fn:ITEMS_RollStaffMods@0x005C1260,
  run:2026-10-14-affixes, run:2026-10-15-items-chain)
- [C] **`tools/chain.py gen`** reproduces the seed tree the rng/seeds worked example logged from `-seed N` alone (game
  seed, the four game-creation draws, act bases, Act II tombs, level seeds) (§ 1). (fn:GAME_InitSeeds@0x0052C280,
  fn:DRLG_ActCreate@0x00642DA0, fn:DRLG_LevelCreate@0x00642AE0, run:2026-10-11-seed-tree)

## 1. `tools/chain.py`

- [C] `gen --seed N` gives, under the override branch of rng/seeds step 1: the game seed `Init(N)` and map seed `N`; the
  four game-creation draws in order, each seeding its object with `Init(low)`: monster regions (draw 1, then
  `tools/monpool.py build_all` for the difficulty and game type), the object-region seed (draw 2), the store seed
  (draw 3), the quest seed (draw 4); each act's `levelSeedBase` and its act-specific draws (`tools/rng.py act_seeds`);
  each level's create seed `Init(levelSeedBase + id)`. On `-seed 12345` it prints the worked example of
  [rng/seeds](../../specs/rng/seeds.md#worked-example): level 1 `015B2E78:0000029A`, Act II tombs 72 and 71, act seed
  `B7A5C418:63A93A78`; on `-seed 34844169`, level 134 `0000000D:0000029A`. `tools/test_chain.py` holds these cases.
  (fn:GAME_InitSeeds@0x0052C280, fn:sub_00547D20_MonRegionsInit@0x00547D20, fn:OBJRGN_Create@0x00546C60,
  fn:NPCSTORE_CtlCreate@0x00536070, fn:QUESTS_InitGame@0x00545D80, fn:DRLG_ActCreate@0x00642DA0,
  run:2026-10-11-seed-tree, run:2026-10-15-objects, run:2026-10-16-quest-drops)
- [I] What `gen` stops at is what needs an input of chain/0001 § 3.3: the level layouts are built when a level is
  first needed and the rooms activate in the player's order (§ 3.2 there), so `check` replays them on logs that carry
  that order.
- `check <log>...` runs, per log, the line sets it carries: item lines through `tools/items_chain.py` (affixes, props
  or both, split as in the items experiments record of 2026-10-15), and the summary counts every oracle still taken.

## 2. Oracle 2: the staff mods

- [C] With `--staff model` the default, `tools/chain.py check` over the 133 kept item logs (51 of
  run:2026-10-14-affixes, 50 of run:2026-10-14-props and -props-forced, 32 of run:2026-10-15-items-chain; each manifest
  `sha256sum -c` clean) reproduces 3 991 creations from the affix lines (the property roll and the staff mods
  modelled) and 3 170 from the property lines (the builders and the staff mods modelled), 0 failed; it predicts 99
  `STF1` exit seeds and the 64 `item_singleskill` entries of the final lists, and takes no staff-mods seed from a log
  (the former "exit not checkable" count of the props pass is 0). 14 logs carry no creation (sessions that never
  dropped an item). (fn:ITEMS_RollStaffMods@0x005C1260, fn:sub_005C0F90_StaffModsRoll@0x005C0F90,
  run:2026-10-14-affixes, run:2026-10-14-props-forced, run:2026-10-15-items-chain)
- [I] The classic body `sub_005C0D70_StaffModsRollV0` is not modelled; it runs only for an item of version 0, which no
  created item has (items/0005 § 10). (fn:sub_005C0D70_StaffModsRollV0@0x005C0D70)

## Kept outputs

`workspace/logs/chain-p1/`, one path base, `manifest.txt` (`sha256sum -c manifest.txt` from that directory):
`o2-items-check.txt` (`tools/chain.py check` over the 133 item logs; `tools/chain.py` `f69b7f02…`,
`tools/items_chain.py` `f72af367…`, `tools/affixes.py` `44c1faf9…`).

## Open questions

- None yet for the retired oracles; the remaining assignment is in the plan 0048 log.
