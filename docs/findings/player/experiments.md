# Player — runtime experiments

Run records for the player subsystem (ADR-0003). Each record states the question, the setup, the procedure and the
result; the findings cite them by `run:<id>`.

## run:2026-10-16-player

- **Question:** plan 0034 Phase 2. Do the level-up saves of `tools/levelup_saves.py` (Phase 0) load and come back
  unchanged through *Save and Exit*; and does `tools/player.py`, the model of
  [player/0001](0001-creation.md) chained to the item model as `tools/cube.py` is (`tools/props.py` `check_iis` and
  `check_ic`, `tools/items_chain.py` `check_creation`), reproduce every logged new character (the stub,
  `NewCharFromStub` step by step, every game-seed step, every starting item's creation, stat lists and placement, the
  skill list, the first save field by field), every kill's experience (`XP_Compute` with its level-difference factor
  and `ExpRatio`, `PLAYER_AddExperience`) and every level-up (`PLAYER_LevelUp`, with every RNG call and LCG step
  inside it listed)?
- **Setup:** agent-driven sessions on slot 3 (display `:10`, prefix `workspace/wineprefix-3`), single player, game
  directory `workspace/runtime/game` (stock, no `-direct`), gdb by `tools/d2run.py`. One slot throughout: no case
  needed two clients (party share not run, see *Not covered*). Slot 3's saves directory was empty; every session
  started with `tools/saves.py --slot 3 aside h34p2` and ended with `restore h34p2` (empty again), so only the
  files a session created were removed. Session driver `tools/player_sessions.py` (`bd9eff0f…`), with three
  commands:
  - `load` (the save-load step): one game per save, `tools/gdb/d2s-io.gdb` (unchanged since plan 0013) and
    `tools/gdb/levelup-load.steps` (Single Player, OK, wait, Escape, *Save and Exit*);
  - `newchar`: one game process per batch, characters created through the menu (Create New, class, the expansion
    and hardcore boxes, name, OK, the hardcore warning's OK, in town, *Save and Exit*), coordinates in
    `.claude/skills/reverser/references/tooling.md` § New characters and level-ups; `--game-args "-act N"` for the
    act starts;
  - `levelup`: one game per save, `enter-normal.steps` or `enter-hell.steps`, then `tools/d2pilot.py explore
    --any-level` (Nova with the F1/F2 hotkeys for the Sorceress; `--walk --melee`, added for this run, for the
    Barbarian and the Paladin: walk, and left-click the nearest live monster outside town) until the log has a
    `LUX` line, then *Save and Exit*.
- **Logger:** `tools/gdb/player.gdb` sourcing `tools/gdb/pilot.py`, `uniques.py`, `props.py` and `d2s-io.py`
  (unchanged) and `tools/gdb/player.py` in two revisions: r1 as committed in f37baf2 (`efdf01eb…`) for the new
  character sessions 34101–34108; r2 (`18f3d6b3…`, b6b8800) for 34109 and the level-up sessions, which adds the
  LCG breakpoints inside `NewCharFromStub` as a control (no line of r1 changed). The LCG lines come from the 852
  instruction sites of `tools/gdb/lcg-sites.txt` (every `mov ecx|edx, 0x6AC690C5` in `.text`), armed only
  between `LU0` and `LUX` (and, r2, between `NC0` and `NCX`).
- **Characters.** New characters: created by the game (no built save). Level-up characters: built with `tools/d2s.py
  build` from `tools/d2s_recipes/lv{sor,bar,pal}{a,b,c,d}.json` on the expansion samples `smpsor`, `smpbar`,
  `smppal`: level 1, 9, 49 or 97 with experience one point below the next level's threshold (as the Phase 0 saves),
  8 000 life, all waypoints and progression 15, Act 1; the Sorceress with the Nova gear of `keynova.json`, the
  Barbarian and Paladin with *Messerschmidt's Reaver* and melee gear. Built states (a built save, not an ADR-0010 forced-path run: no table is edited; review ruling in plan 0034's log): the attributes and
  life are not a level-*N* character's; the level-up arithmetic adds to whatever base it finds (player/0001 § 7), and
  the refill maxima with item bonuses are logged (LUM) and taken as inputs where they differ from the base maximum.
- **Sessions:**

  | step | seeds | what | n |
  |---|---|---|---|
  | load | 34200–34247 | the 48 saves of `levelup_saves.py` (7 expansion and 5 classic classes × levels 2, 10, 50, 98; the classic ones on the five `d2s.py classic` bases) | 48 |
  | newchar | 34101–34103 | the seven classes, expansion, three times | 21 |
  | newchar | 34104 | the five classic classes | 5 |
  | newchar | 34109 | hardcore: Barbarian and Assassin expansion, Sorceress classic | 3 |
  | newchar | 34105–34108 | `-act 2` (Amazon exp, Necromancer classic), `-act 3` (Druid), `-act 4` (Paladin), `-act 5` (Sorceress exp, Barbarian classic) | 6 |
  | levelup | 34411–34414, 34441, 34443 | LvSorA–C Normal, LvSorD Hell; LvSorA and LvSorC again in Hell (monster above the player) | 6 |
  | levelup | 34402, 34421–34423 | LvBarA–C Normal, LvBarD Hell (melee) | 4 |
  | levelup | 34431–34434 | LvPalA–C Normal, LvPalD Hell (melee) | 4 |

  Calibration session 34401 (LvBarA, the melee pilot clicked the town's NPCs) logged no kill and is not part of the
  run.
- **Logs** (workspace, not in git): `workspace/scratch-h34p2/player-run.lst` (`fef9a539…`, 23 logs: 9 newchar, 14
  levelup) and the 48 `load/logs/load-*.log`; sha256 per file in `workspace/scratch-h34p2/player-run-manifest.txt`
  (`ee2ce6bf…`).
- **Procedure and result, the save-load step:**
  ```
  python3 -I tools/player.py loadcheck <built> <written> ...      # the 48 pairs
  48 saves loaded and written back, 0 with differences outside last_played/checksum/map_seed/difficulty;
  changed: checksum 48, items whose flag 0x2000 (new) was cleared 368, last_played 48, map_seed 48
  python3 -I tools/d2sio.py check <excel> load/logs/load-<name>.log written/<name>.d2s    # each of the 48
  TOTAL 11152 comparisons, 0 mismatches (sum)
  ```
  9 672 fields compared by `loadcheck` (header, stats, skills, golem, every item field). Every save loads (reader
  code 0); what the write changes is the time, the checksum, the map seed (the game's) and the item flag `0x2000`
  ("new"), which every built item carries and the game clears. The five classic bases converted by `d2s.py classic`
  (Amazon, Sorceress, Necromancer, Paladin, Barbarian; 20 classic saves) load as classic and come back unchanged.
  The hashes (built / written, sha256 prefix):

  <details><summary>48 pairs</summary>

  | save | built | written |
  |---|---|---|
| XpAmaAc | `f2ffd8497ca6213e` | `48580c8f60c2283c` |
| XpAmaAx | `fb92557e3bb26a77` | `9bba00832bf640f8` |
| XpAmaBc | `aba81cc9ca43eed2` | `78a99a7e7716c6a3` |
| XpAmaBx | `600cb09e554ad972` | `d7d93d2d4d458163` |
| XpAmaCc | `e411c6b2015c0931` | `6959d996b2781a94` |
| XpAmaCx | `b13293797ecaf05e` | `2ceadca9f941046d` |
| XpAmaDc | `3ccd815b1d08aa2e` | `a179d6f88d4e2b7a` |
| XpAmaDx | `76580ad65b1a5464` | `5a5809d57b3bb7e3` |
| XpAsnAx | `27bde68f4bf8ea12` | `0e5c7855b8a01c6d` |
| XpAsnBx | `27f9f14c520d27cf` | `b5aa1e4507af031c` |
| XpAsnCx | `2380c67c4044d244` | `48c3b8683819d7f2` |
| XpAsnDx | `f63ca84581d2a5e8` | `0745a3a1d0219041` |
| XpBarAc | `5434f535683518e6` | `df605d10269c5aac` |
| XpBarAx | `fb553da0df3386dd` | `67ed2995ea502f06` |
| XpBarBc | `52028982344598e7` | `3f9049933df1f29c` |
| XpBarBx | `6fda69eccc9aa64e` | `ff5f7889e42ef6a7` |
| XpBarCc | `c6b15397ca3519b5` | `c602eed6382d7192` |
| XpBarCx | `103c86bdaff5a8f9` | `2c70d84bb533c78c` |
| XpBarDc | `ca4ba482db2da50a` | `41952735c753239d` |
| XpBarDx | `ebc39133c24c785d` | `4b74d066a9f62dd2` |
| XpDruAx | `94b726a90be2110e` | `b16bfed6e0cf534b` |
| XpDruBx | `a7b7948f98eea5b8` | `c63a39a342a59f53` |
| XpDruCx | `803c4172ab50a105` | `48441053289531bb` |
| XpDruDx | `c742706d38272668` | `f13a9735690f4118` |
| XpNecAc | `44d333cce5e04564` | `69711488c09968d6` |
| XpNecAx | `9914438f7b8ca017` | `9ba70be6f5f3d235` |
| XpNecBc | `c94e289f39322b54` | `1a716efbf1da11a0` |
| XpNecBx | `29453e015718f8f9` | `b523f7a2dbcf3998` |
| XpNecCc | `3f881f4670d2800b` | `17122e4ed6eacc2a` |
| XpNecCx | `33224b47cd23b9ba` | `b154903669111f6d` |
| XpNecDc | `961a1f2337cc12bf` | `a89478c55331c475` |
| XpNecDx | `329de07e0591563d` | `c19f50702009111b` |
| XpPalAc | `ece597cb8981453a` | `db8e7cf59cb13d4f` |
| XpPalAx | `c09f140f127fc630` | `b3b96613cfdf743e` |
| XpPalBc | `d0dbfcc6fb3621dd` | `f078a027f9f331c6` |
| XpPalBx | `f6089b3f2474168b` | `58dda19bd62512f5` |
| XpPalCc | `dc86ace0a91d54f7` | `24fd9d102f62efb7` |
| XpPalCx | `53fafebc60b0456e` | `02cf92b38c2b019e` |
| XpPalDc | `af5c4da3b0513dc5` | `3883818bf13523a6` |
| XpPalDx | `1831fdb1099ea1ee` | `8ff2a0cf9f02eee3` |
| XpSorAc | `67d3046801ec1331` | `65b3023394d84f53` |
| XpSorAx | `974f118489fe61e1` | `22414c16551584a7` |
| XpSorBc | `dcfa11cff9a2fd79` | `3fb435dde9362772` |
| XpSorBx | `2ed1fbaec6202d1b` | `d951b3c026bb3866` |
| XpSorCc | `25fab4457d0a0968` | `f3cf7062c6a7a045` |
| XpSorCx | `391bea0da1c8d744` | `cb8db711d89ddfac` |
| XpSorDc | `ac37b7020721cacb` | `8e9b5e2b8831423d` |
| XpSorDx | `a08eee7fce11c3c1` | `315216b1206bf8f6` |

  </details>
- **Procedure and result, the model:**
  ```
  python3 -I tools/player.py check $(cat workspace/scratch-h34p2/player-run.lst)
  35 new characters reproduced, 0 failed; 20 level-ups reproduced, 0 experience lines failed
    stubs checked (RHDR: StubBuild layout, ReadHeader 2) 35; PLAYER_InitBaseStats predicted 35; skill lists 35
    ItemInitStats predicted 269; StartItemCreate stat lists 269; builders run by the affix model: normal 269
    join seeds predicted (ICJ) 258; staff mods: exit not checkable 11
    placements predicted: belt 140, equip 59, inv 70; first saves predicted field by field 35, items 269
    quest/waypoint/npc sections identical across new characters: expansion 27, classic 8
    RNG-function calls inside NewCharFromStub on other seeds (item creation): RNG_Range 54, RNG_RangeB 64,
      RNG_RangeOffset 24; LCG multiplier executions inside NewCharFromStub (control) 127
    kills credited 32; XP_Compute, XP_LevelDiffPenalty, XP_ApplyExpRatio predicted 32 each;
      level difference: below[0] 3, below[1] 2, below[8] 3, below[9] 1, below[10] 19, above[10] 1,
      above with clvl >= 25 (exp x clvl / mlvl) 3; ExpRatio 1024 (levels 1-50), 8 (97), 6 (98)
    PLAYER_AddExperience 38 (32 kills, 6 -act grants); PLAYER_LevelUp reproduced 20
      level-ups: 1 level 14, 15 levels 2, 20 levels 1, 26 levels 1, 32 levels 2
      refill maximum = base maximum 13 x 3; with item bonuses (LUM input) 7 x 3
  exit 0
  ```
  `tools/d2sio.py check` on the nine new-character logs: 5 612 comparisons, 0 mismatches (the stub's reader code 2
  added to the checker for this run).
- **Boundary oracles (ADR-0004), named and counted:** `ITEMS_RollStaffMods` (items/0005) at the end of the normal
  builder on the Sorceress's staff and the Necromancer's wand: 11 of the 269 item creations (sst 6, wnd 5); on 4 of
  them the join seed after it is the log's, on 7 the staff-mod `item_singleskill` entries it added (9 entries) are
  the log's. Every other creation (258) is predicted from the game seed to the item seed at `ICX` with no seed taken.
  The refill maxima with item bonuses (`UnitGetMaxHp/Mana/Stamina`, LUM) are value inputs on 7 level-ups (the
  Sorceress's gear). No other value or seed is taken from the log.
- **Answers:**
  - Nothing steps the game seed between `SUnitCreate` and the first starting item except
    `sub_00569F20_PlayerUnitInit`'s one step: the game seed logged after `SUnitCreate`, after the unit is sent to the
    client and after `PLAYER_InitBaseStats` is the model's, on all 35 characters; `QuestsPlayerJoin` after the items
    steps it neither. No RNG-function call in `NewCharFromStub` is on the game seed or the player's seed.
  - Nothing is drawn by a level-up: over 20 `PLAYER_LevelUp` calls no RNG function is called and none of the 852 LCG
    multiplier sites executes between its entry and its return on the thread, while the same breakpoints fired 127
    times inside `NewCharFromStub` (r2 control); the game seed and the player's unit seed are unchanged across it.
  - Within one game process every new character starts from the same game seed (the game is created anew from the
    same `-seed`), so the characters of a batch share item seeds; the three expansion batches and the classic batch
    use different seeds.
- **Observed and modelled from the code (new in this run):** the equip path (`sub_005606B0_ItemEquip`) sets item
  flag `0x1`, mode 1, page `0xFF` and the path cell (body location, 0); the flag is clear again in the first save.
  The skill `item1` grants (`item_singleskill(StartSkill)`) is a last skill-list entry of base level 0, also under
  `-act N`, where the right skill stays Attack. Inventory placement is `sub_0063B490_InvSpotFindRow` (one-row items:
  columns from the right, rows from the bottom) or `sub_0063B620_InvSpotFind`, best `sub_0063B340_InvSpotScore`
  wins; the belt slot is `sub_0063C600_BeltFreeSlot` on the default belt (4 boxes).
- **Not covered:** party share (`XP_PartyShare`, two clients; not run), death experience loss, the experience cap at
  `MaxLvl − 1`, class 7, `sub_0058C5C0_ExpGrantCapped`. The `appearance` bytes of the saved header (the client's
  graphics) are not predicted.
- **Checker observation (not a model mismatch):** on the six Hell level-up sessions `tools/d2sio.py` reports the
  written stat 6 (life) as `0x1FFFFF` while the writer's runtime base entry is lower (the character had taken
  damage): the save path's life value is not the base entry the checker compares (backlog). Two sessions (34401,
  34422) wrote no save at the end (the *Save and Exit* click missed); their files are not compared.
- **Tag changes:** player/0001: the stub, the start values, the starting skills, the starting items (creation
  record, game-seed steps, stat lists, placement, flags), the seeds, the experience table and `ExpRatio`,
  `XP_Compute`, `PLAYER_AddExperience`, `PLAYER_LevelUp` and `PLAYER_GrantLevel` (`-act N`) go from inferred to confirmed (§ 11 of the finding).

### Addendum 2026-10-16: plan 0038 batch S3a

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/mon_sweep.py logs` checks each log's sha256 against `player-run-manifest.txt` and writes the batch manifest
  `workspace/logs/sweep-s3a-manifest.txt` (sha256 `274ed527…f37b`).
- `python3 -I tools/mon_sweep.py player` over the 23 session logs: 35 stubs with the save checksum at `0x0C`, the hardcore
  bit only in the 3 stubs of session 34109, `0x20` in every class 5/6 and expansion stub, act bytes 0 in all 35, client act
  `N − 1` under `-act N`; 32 kills with `XP_Compute`'s return equal to the value after `XP_ApplyExpRatio`.
- Backs the S3a section of [player/0001](0001-creation.md#plan-0038-batch-s3a-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S2c

- Re-analysis of this run's kept logs; no new session (plan 0038 Phase 1, ruling 2026-10-15 (a)). `python3 -I
  tools/sweep_s2c.py props` checks each of the 23 logs of `workspace/scratch-h34p2/player-run.lst` against
  `player-run-manifest.txt` and reads the start items' ethereal and socket rolls (records with flags `0x0A`): 209
  ethereal rolls returned without a draw, and 54 socket rolls drew and then wrote nothing, 21 of them with a draw
  below 33. Backs the plan 0038 S2c rulings in [items/0006 § Plan 0038 batch S2c](../items/0006-properties.md#plan-0038-batch-s2c-2026-10-16).

### Addendum 2026-10-16: plan 0038 batch S1a

- Re-analysis of this run's kept logs and written saves; no new session. `python3 -I tools/sweep_s1a.py logs` checks the
  71 logs against `player-run-manifest.txt`; `writes`, `reads`, `corpus` and `pairs` read the d2s-io lines (192 writes,
  99 loads, 35 stubs), take the 96 written saves whose sha256 is a logged `WDONE` buffer (the files of sessions 34401 and
  34422 are not), and compare the 48 built saves with the files written back (hotkeys, quest blocks, NPC section, skill
  bytes, item cells). `props` re-runs `tools/player.py check` on the nine new-character logs: 269 saved items predicted
  field by field, exit 0.
- Correction to *Checker observation* above: the `gf` value that differs on the Hell level-up saves is stat **8** (mana),
  runtime 2 276 402 written as `2^21 − 1` = 2 097 151 (session 34414): the `gf` writer's unsigned clamp at its top bound.
- Backs [save/0001 § Plan 0038 batch S1a](../save/0001-d2s-io.md#plan-0038-batch-s1a-2026-10-16).

