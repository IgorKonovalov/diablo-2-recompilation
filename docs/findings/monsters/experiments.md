# Monster experiments

## run:2026-10-12-mon-pool

- **Question:** (plan 0012 Phase 2) Does the model of [monsters/0001](0001-level-pool.md) predict, from the `-seed N`
  value and the difficulty alone, every level's monster region built at game creation? That means its entries
  (class, rarity), appearance sets, copied Levels fields and the region seed after each level, plus the game-seed draw
  that seeds it. Does it also predict the monster level of the monsters created and the client critter draws?
- **Setup:** the ADR-0003 harness (`workspace/runtime/game/`, prefix `workspace/wineprefix`, display `:7`), wine 11.17,
  GNU gdb 17.2. Logger `tools/gdb/mon-pool.gdb`, which sources `tools/gdb/mon-pool.py`. Model and checker `tools/monpool.py`,
  which reads `levels.bin`, `monstats.bin` and `monstats2.bin` from `workspace/merged/data/global/excel` (the tree of
  the MPQs the harness game loads). Save: the harness character `seedtest`, a fresh expansion Barbarian stub
  (sha256 `cabccb01…`), normal difficulty only, left in place. The saves directory was hashed before the runs and
  restored after them: the game had rewritten `seedtest.ma0` and `seedtest.map` (automap), and both were copied back
  from the pre-run copy. All seven `seedtest.*` sha256 matched the pre-run list afterwards. No walking, no waypoint.
- **Logged** (one JSON line per event, header of `tools/gdb/mon-pool.py`): MPS `0x00547D63` (game seed after its
  step, the low word, difficulty, expansion, game type, `+0x74`, caller, monstats records 722/723); MPR `0x00547B1A` (one
  per level: the whole region as built, and `R` after it); MLV `0x00573E56` (class, chosen level, difficulty index,
  level id); CR0/CRC/CRX `0x0046C460`/`0x0046C548`/`0x0046C56B` (client critters: room seed in, each creation's class
  and seed, seed out).
- **Procedure:**
  1. Before each run `pgrep -af tools/d2run.py` and `pgrep -x game.exe` were empty (a wrapper script waited for both).
  2. `python3 -I tools/d2run.py --seed N --gdb tools/gdb/mon-pool.gdb --steps tools/gdb/enter-sp.steps --after 8 [--game-args "-act A"] --log workspace/logs/monpool-….log`,
     with `MONPOOL_FORCE_DIFF=D` in the environment for every run but the first.
     | log | N | difficulty | act | logger version |
     |---|---|---|---|---|
     | `monpool-1-normal.log` | 1 | normal (natural) | 1 | MPS/MPR/MLV only |
     | `monpool-1-d1.log` | 1 | nightmare (forced) | 1 | + forced field |
     | `monpool-1-d2.log` | 1 | hell (forced) | 1 | + forced field |
     | `monpool-2-d0.log` | 2 | normal (byte rewritten to 0) | 1 | + forced field |
     | `monpool-2-d2.log` | 2 | hell (forced) | 1 | + forced field |
     | `monpool-3-d0-a1.log` … `monpool-5-d0-a5.log` | 3, 3, 4, 4, 5 | normal (rewritten to 0) | 1, 2, 3, 4, 5 | final (+ critters) |
  - **Intervention (ADR-0003, it changes game state):** with `MONPOOL_FORCE_DIFF=D`, the MPS breakpoint at `0x00547D63`
    writes D into the game's difficulty byte `game+0x6D` before the region build reads it at `0x00547D66`. In
    `monpool-1-d1`, `monpool-1-d2` and `monpool-2-d2` this turns a normal game into a nightmare/hell build; in the other
    runs it rewrites 0 over 0. The pool reads difficulty only at that point, so the nightmare/hell region claims rest on
    the forced byte; a natural nightmare/hell game is a required case of the rest of Phase 2.
  3. Check: `python3 -I tools/monpool.py check workspace/merged/data/global/excel workspace/logs/monpool-[1-5]-*.log` (the ten logs of this run; the glob leaves out the `monpool-p2-*` logs of [run:2026-10-12-mon-pool-p2](#run2026-10-12-mon-pool-p2)).
- **Observed:**
  ```
  all ten MPS: game-seed draw = 1 from Init(N), exp=1, gtype=3, caller 0x00530DCF; monstats 722/723 = monstats.bin
  MPR 1360 (136 levels x 10 games), MLV 47, CR0/CRX 130 rooms (critters in 12: Act I chicken, Act II bug), CRC 36
  per game: candidates > picks in 85 (normal) / 104 (nightmare, hell) levels; empty pools 11 (the 10 NumMon-0
    levels and Mountain Top, isSpawn 0); 20 rangedspawn levels built; 6-10 regions with a class twice;
    359 (normal) / 369 (nightmare, hell) entries, 670-709 appearance sets; class 723 in level 135 in every game
  monpool: 1557/1557 match
  ```
  No LOGERR line in the final logs. Development runs of the critter logger (`-act 1..5` logs written before two fixes
  to it) were overwritten by the reruns above and are not part of the record.
- **Raw logs:** `workspace/logs/monpool-1-normal.log` (sha256 `d4cf9a8f…3b3d`), `monpool-1-d1.log` (`eb514885…1360`),
  `monpool-1-d2.log` (`2036a0a6…5f1d`), `monpool-2-d0.log` (`fc6b83a0…2337`), `monpool-2-d2.log` (`e7518763…8cde`),
  `monpool-3-d0-a1.log` (`fc830d30…1a84`), `monpool-3-d0-a2.log` (`8a52c22f…4598`), `monpool-4-d0-a3.log` (`aaed7338…50fe`),
  `monpool-4-d0-a4.log` (`8c811ac4…0fa4`), `monpool-5-d0-a5.log` (`b28a526c…d869`).
- **Deviations and limits:**
  - **Nightmare and hell are forced.** The only character the session could use plays normal. The logger writes the
    difficulty byte `game+0x6D` at `0x00547D63`, before `0x00547D66` reads it, so the region build runs the
    nightmare/hell branch on a game object that is otherwise a normal one. The pool code reads nothing else that
    depends on difficulty (the build's `sub_00611D30_DifficultyRec` check passed). The forced games did not continue into the world,
    so the monster level and critters were logged only in normal games. A save swap that would have loaded a
    nightmare/hell character was refused by the session's permission checks.
  - **No classic game.** All ten games are expansion games (`+0x70` = 1).
  - **Monster level** (fn:sub_00573CB0_MonStatsInit@0x00573CB0): the 47 MLV lines are town NPCs created in normal games (no hireling among them), and all take MonStats `Level`.
    They don't separate MonStats `Level` from `MonLvl1Ex` of the towns (both 0), and the expansion nightmare/hell branch
    was not reached. The claim stays `[I]`.
  - **Critters:** `sub_0046C1A0_ClientCritterCreate` draws from the room seed (several draws per critter), which the model
    doesn't cover. Critter rooms are checked up to their first creation (seed, first slot's class and count).
    Rooms without critters are checked to their seed after.
- **Conclusion** (fn:sub_005479C0_MonRegionsBuild@0x005479C0): the pool build, the variant rolls, the region fields and the game-seed draw that seeds them are
  reproduced bit-exactly in ten games (normal over five seeds, nightmare over one, hell over two), every act,
  with no oracle on the pool side. In-scope claims of monsters/0001 sections 1–4, 7 and 8 go to `[C]`. The monster-level rule
  (section 5) and the classic branch stay `[I]`.

## run:2026-10-12-mon-pool-p2

- **Question:** (plan 0012 Phase 2, rest) Without forcing the difficulty, does `tools/monpool.py` reproduce the
  regions of a natural nightmare and a natural hell game, and of classic (non-expansion) games? Does the monster
  level of monsters created **outside town** follow the rule of [monsters/0001 §5](0001-level-pool.md#5-the-monster-level-sub_00573cb0_monstatsinit):
  `MonLvlEx` in expansion nightmare/hell, MonStats `Level*` in classic games and in normal, and the hireling and
  `noRatio` exceptions?
- **Setup:** as [run:2026-10-12-mon-pool](#run2026-10-12-mon-pool): the ADR-0003 harness (`workspace/runtime/game/`,
  prefix `workspace/wineprefix`, display `:7`), wine 11.17, GNU gdb 17.2, the unchanged logger `tools/gdb/mon-pool.gdb`
  (+ `mon-pool.py`), model and checker `tools/monpool.py` on `workspace/merged/data/global/excel`. `-seed 1` in every
  game. `MONPOOL_FORCE_DIFF` was **not** set in any run (every MPS line logs `"forced":null`). No memory write.
  - **Test characters** (built on copies, never on the samples): `python3 -I tools/monpool_saves.py <dir>` writes
    `expnm/smpsor.d2s` (expansion Sorceress from `samples/d2s-owner/smpsor-l50.d2s`, level 50, Act I waypoints
    0, 2, 6, 8 in every difficulty, header `progression` 5, difficulty bytes `00 80 00`), `exphell/smpsor.d2s`
    (progression 10, `00 00 80`), `exphellmerc/smpsor.d2s` (exphell plus a mercenary in the header: seed 12345,
    hireling id 4 = Rogue Scout *Fire - Hell*, class 271, experience 500000, an empty mercenary item list),
    `cls/smpsor.d2s` (exphell made classic: status bit 5 cleared, the `jf`/`kf` trailer removed, progression 8) and
    `nec/smpnec.d2s` (Necromancer from `samples/d2s/smpnec.d2s`, Hell waypoints 0, 2, 6, 8, Clay Golem at level 1
    on the right button, progression 10). `tools/d2s.py survey` reads all five cleanly. sha256 (first 16 hex):
    expnm `738e5912363bfba7`, exphell `4beb9d411d211931`, exphellmerc `1211b76aa0c3763f`, cls `b29ea52c72d3bd47`,
    nec `0d7201b41225dc4f`.
  - **Saves directory:** only through `tools/saves.py` (owner-approved): `aside p2` before the first run,
    `install p2 <file>` before each run (with `restore p2` + `aside p2` between characters), `restore p2` at the end;
    the final `status` shows the seven `seedtest.*` files (seedtest.d2s `cabccb01…`) and no open aside.
- **Logged:** the MPS, MPR, MLV and CR0/CRC/CRX lines of run:2026-10-12-mon-pool (header of `tools/gdb/mon-pool.py`).
- **Procedure:**
  1. Before each run `pgrep -f 'tools/d2run[.]py'` was empty; after each, the same check (and `wineserver -k`
     for the one interactive run).
  2. `python3 -I tools/d2run.py --seed 1 --gdb tools/gdb/mon-pool.gdb --steps <steps> --after 10 --log workspace/logs/<log>`
     with the character installed:
     | log | character | steps | game | where monsters were created |
     |---|---|---|---|---|
     | `monpool-p2-1-hell-merc-town.log` | exphellmerc | `monpool-hell-town.steps` | expansion hell | Rogue Encampment; the mercenary |
     | `monpool-p2-2-hell-jail.log` | exphell | `monpool-hell-jail.steps` | expansion hell | camp, Jail Level 1 (waypoint) |
     | `monpool-p2-3-nm-jail.log` | expnm | `monpool-nightmare-jail.steps` | expansion nightmare | camp, Jail Level 1 |
     | `monpool-p2-4-classic-hell-jail.log` | cls | `monpool-hell-jail.steps` | classic hell | camp, Jail Level 1 |
     | `monpool-p2-5-classic-nm-jail.log` | cls | `monpool-nightmare-jail.steps` | classic nightmare | camp, Jail Level 1 |
     | `monpool-p2-6-hell-jail-golem.log` | nec | `monpool-hell-route.steps`, `--after 600`, then by hand | expansion hell | camp, Jail Level 1, a Clay Golem |
     | `monpool-p2-7-normal-stony.log` | exphell | `monpool-normal-stony.steps` | expansion normal | camp, Stony Field (waypoint) |
     The steps pick the difficulty in the *Select Difficulty* box (Normal 400,280 / Nightmare 400,323 / Hell 400,366),
     walk the camp route of `d2s-wp-open.steps`, which for these saves ends with the waypoint at the left edge, click
     the pad (15,182) and a row of the Act I tab. Walking is the only way out of town; no other movement.
  3. Run 6: with the Necromancer the route drifted (a first attempt missed the pad and was discarded, its log deleted).
     The run that counts played `monpool-hell-route.steps` (from a scratch copy, so the log header names that path)
     and was then driven by hand through `tools/xdrive.py --display :7 --window "Diablo II"`: `key Tab` (automap),
     `click 280 70`, `click 680 65` (the pad), `click 200 348` (Jail Level 1), `rclick 470 300` (Clay Golem), then
     `wineserver -k`. Screenshots `monpool-p2-6-{town,automap,wpmenu,golem}.png`.
  4. Two exploratory runs (hell, the first route attempt, and an interactive look at the hell camp) logged only the
     camp; their logs were deleted and are not part of the record.
  5. Check: `python3 -I tools/monpool.py check workspace/merged/data/global/excel workspace/logs/monpool-p2-*.log`.
- **Observed:**
  ```
  seven MPS: game-seed draw = 1 from Init(1), forced=None, caller 0x00530DCF, gtype 3
    diff/exp: 2/1, 2/1, 1/1, 2/0, 1/0, 2/1, 0/1
  MPR 952 (136 x 7), MLV 162, critter rooms 355
  monpool: 1483/1483 match
  monster levels outside town (class: logged level; MonStats Level[d]; area MonLvlEx[d]):
    exp hell  Jail 1 (29):  384 x7: 71; 70; 71   57 x2: 71; 70; 71   39 x2: 71; 71; 71
    exp nm    Jail 1:       384 x7: 41; 40; 41   57 x2: 41; 40; 41   39 x2: 41; 41; 41
    cls hell  Jail 1:       384 x7: 70; 70; 71   57 x2: 70; 70; 71   39 x2: 71; 71; 71
    cls nm    Jail 1:       384 x7: 40; 40; 41   57 x2: 40; 40; 41   39 x2: 41; 41; 41
    exp normal Stony Field (4): 6 x14: 2; 2; MonLvl1Ex 4   160 x2: 4; 4; 4
    exp hell  hireling 271 (the mercenary, no room): level 1, d = 0 (MonStats Level; Level(H) is 67)
    exp hell  Jail 1, 289 claygolem (noRatio): level 0, d = 2 (MonStats Level(H) blank = 0; MonLvlEx 71)
  town NPCs (acts I, every game): level 0 (MonStats Level* and the camp's MonLvl*Ex are both 0)
  regions: natural nightmare (p2-3) = forced nightmare (monpool-1-d1) and natural hell (p2-2) = forced hell
    (monpool-1-d2), entry for entry and seed after for seed after, all 136 levels; classic = expansion regions
    (same seed and difficulty) except the copied monLvl fields (classic MonLvl vs MonLvlEx), which the check predicts
  ```
  No LOGERR line. 61 of the creations separate the two sources of the level (MonStats `Level*` vs the area level):
  9 in each of the five Jail games (seven 384, two 57; run 6 has the same nine), 14 class 6 in Stony Field, the
  mercenary and the golem.
- **Raw logs:** `workspace/logs/monpool-p2-1-hell-merc-town.log` (sha256 `a5a6231f…892f`), `monpool-p2-2-hell-jail.log`
  (`6f1986fd…f071`), `monpool-p2-3-nm-jail.log` (`0c4eeac1…1cb3`), `monpool-p2-4-classic-hell-jail.log` (`84d7492a…6144`),
  `monpool-p2-5-classic-nm-jail.log` (`434bb32b…6269`), `monpool-p2-6-hell-jail-golem.log` (`30342d58…2abb`),
  `monpool-p2-7-normal-stony.log` (`f853b6df…07d8`); arrival screenshots `monpool-p2-{2,3,4,5,7}-arrive.png`.
- **Deviations and limits:**
  - One seed (1) and Act I only for the nightmare/hell and classic regions; the forced runs of run:2026-10-12-mon-pool
    cover seed 2 hell. The natural regions match the forced ones exactly for seed 1.
  - No classic **normal** game. No `boss` class was created (act bosses need play). Hirelings: only class 271, in an
    expansion hell game. `noRatio`: only `claygolem`, in an expansion hell game.
  - The test saves are header edits (ADR-0003 input, not a memory write): the game accepted them (difficulty box,
    the waypoint menus, the mercenary shown at level 15 on its screen). The region build and the monster level read the game's difficulty
    and expansion flags, which every MPS/MLV line logs, not the save.
- **Conclusion:** [monsters/0001](0001-level-pool.md): the column set per difficulty and the region build are
  reproduced in natural nightmare and hell games and in classic nightmare and hell games; the monster-level rule
  (§5) goes to `[C]` for the cases logged here (expansion normal, nightmare, hell; classic nightmare, hell; hireling;
  `noRatio`); `boss` and classic normal stay `[I]` (fn:sub_00573CB0_MonStatsInit@0x00573CB0, fn:sub_005479C0_MonRegionsBuild@0x005479C0).

## run:2026-10-13-mon-spawn

- **Question:** (plan 0014 Phase 2) Does the model of [monsters/0002](0002-room-population.md) reproduce, bit for bit,
  the random population of every room the server activates (gate, attempts, density, class picks and the `spawn`
  substitution, the type roll, groups, specials, minions, every position and every draw on the room, game and unit
  seeds), with the active-room seed **predicted from the `-seed` value** rather than read from the log? It also covers
  the Phase 1b required cases: `MonUMax` (the type-roll draws), the live special count `+0x2C8` across a champion pack,
  and every access to `MonWndr` (fix F5).
- **Setup:** the ADR-0003 harness (`workspace/runtime/game/`, prefix `workspace/wineprefix`, display `:7` moved to a
  visible workspace for the owner), wine 11.17, GNU gdb 17.2. Logger `tools/gdb/mon-spawn.gdb` (sha256 `d2a05950…e3b55284`),
  which sources `tools/gdb/drlg-gen.py` (`91feac40…5c970580`), `tools/gdb/drlg-roomk.py` (`d6b2e6e0…6340ce5be`) and
  `tools/gdb/mon-spawn.py` (`6ad436e8…a2438352`). Model and checker `tools/monspawn.py` (`8519cd27…2ca34f1b`), which runs
  `tools/drlg.py` gen and roomk (`eb9fe18b…8a60ee65`, two inert recording hooks added) and `tools/monpool.py` on the same
  log. Tables: `workspace/merged/data/global/excel` (`.bin`, by position).
  - **Characters** (tool-built inputs, ADR-0003; installed and restored only through `tools/saves.py`, tags `s1`..`s3`,
    final `status` shows the seven `seedtest.*` files and no open aside): session 1 `expnm/smpsor.d2s` of
    `tools/monpool_saves.py` (`738e5912…073e271b`); sessions 2 and 3 `NovaSorc.d2s` (`1f8ece31…4165c263`), built with
    `python3 -I tools/d2s.py build <excel> tools/d2s_recipes/novasorc.json samples/d2s-owner/smpsor-l50.d2s NovaSorc.d2s`, where
    `tools/d2s_recipes/novasorc.json` (`e149aaad…c61e4be9`) is `tools/d2s_recipes/lightsorc.json` with name `NovaSorc`,
    Nova 20 and Nova on the right button (owner's request): level 80, every waypoint and Acts II–V open in all
    difficulties, belt of full rejuvenation potions.
- **Logged** (one JSON line per event, header of `tools/gdb/mon-spawn.py`): the DRLG generator and room-k tags (LC0 … AROOM);
  the room driver RW0–RW4 around the wanderer tick, presets, inactive restore and objects; the pass P0/PG/PR/PB/PN/PA/PC/PT/
  PSP/PGR/PGX/PS2/PSB/PCP/PX (PDEAD on the dead type-1 branch); SpawnPosPick SP0/SPW0/SPW/SPR0/SPR/SPX/SPF; every
  MonSpawnTry MT0/MTX with its oracle calls MR0/MR, MC0/MC, MK0/MK (arguments, result, room and game seed on entry and
  exit), the creation MU0/MU/MUP; MinionsSpawn MM0/MMN/MMX; SpawnGroup G1/GK; the special path SMPX, SMR0/SMR1/SMRX,
  SMA0/SMA1/SMAX, UMN/UMX, CP0/CPN/CPM; the special count SCI/SCD; MonWndr access watchpoints WND.
- **Procedure:**
  1. Before each session `pgrep -af 'tools/d2run[.]py'` was empty; afterwards `wineserver -k` and the same check.
  2. `MONSPAWN_WATCH=<l1,l2> python3 -I tools/d2run.py --seed N --sound --gdb tools/gdb/mon-spawn.gdb --after 5400 --log workspace/logs/<log>`,
     no steps file; the owner played:
     | log | N | character | game | owner's route | watched levels |
     |---|---|---|---|---|---|
     | `monspawn-s1-12345-normal-a1.log` | 12345 | expnm | expansion normal | waypoint to Stony Field | 4, 3 |
     | `monspawn-s2-12345-normal-a2-5.log` | 12345 | NovaSorc | expansion normal | waypoints: Far Oasis, Spider Forest, City of the Damned, Frigid Highlands | 43, 76 |
     | `monspawn-s3-1-hell-a1.log` | 1 | NovaSorc | expansion hell | waypoints: Stony Field, Dark Wood, Jail | 4, 5 |
  3. Check: `python3 -I tools/monspawn.py check workspace/logs/monspawn-s1-12345-normal-a1.log workspace/logs/monspawn-s2-12345-normal-a2-5.log workspace/logs/monspawn-s3-1-hell-a1.log`.
- **Observed:**
  ```
  drlg gen 5402 / 31621 / 16077 checks, roomk 3273 / 23244 / 17676 checks: 0 mismatches each
  passes: gate closed 169, empty 178, populated 169
  rooms with the seed predicted from the map seed: 516; from the log only: 0
  seeds [1, 12345], difficulties [0, 2]; levels 3, 4, 5, 29, 30 (Act I), 43 (II), 76, 77, 84 (III), 106 (IV), 111, 125 (V)
  closed MonDen gates on levels 1, 75, 110 (37 passes)
  creations 916; normal groups 257; champion packs 4 (rolls 0, 9, 4, 15); unique groups 20
  type rolls 346, special 29; MonUMax draws 252 (r = 5: 1, r <= 5: 9); MonUMin draws 115
  champion roll Range(boss seed, 100) vs MonUMod rec 0 +0x1C = 20: 24 rolls, champion iff r < 20
  special-count (+0x2C8) increments 30, each checked against the model's count; no decrement inside a pass
  spawn substitution (threshold 20): taken 14, kept 5; special class from umon (normal) 9; MonStats minions 163
  unit-seed steps after Init(step(game).low) at MU: 2 on 914 creations, 6 and 15 on one each (seed oracle, reported)
  oracle calls: CollisionTest 3903, SpawnClassCellTest 3908, LogicRegionIdAt 4823, NearWarpTest 1919,
    presets/restore/objects 516 windows, special mods 24, mod handlers 24 + 6 (pack members)
  MonWndr watch (levels 3, 4, 5, 43, 76): every access is the region build read 0x00547A99
  monspawn: 110302 checks, 0 mismatches
  ```
- **Raw logs:** `workspace/logs/monspawn-s1-12345-normal-a1.log` (sha256 `4dab869e…b0193609`),
  `monspawn-s2-12345-normal-a2-5.log` (`c50778b4…06bb16b3`), `monspawn-s3-1-hell-a1.log` (`c0556ed2…6cd152d8`).
- **Deviations and limits:**
  - Development logs are not part of the record: `monspawn-smoke.log` (scripted Blood Moor walk, 1554 checks, 0 mismatches
    with the final checker), `monspawn-dev-hell-jail.log` (the scripted route stayed in camp) and `monspawn-s2-aborted.log`
    (session 2 restarted at once to switch to the Nova build).
  - Two checker fixes during the run, both from code and data: the `umon` count at Levels `+0x35` is 0 in `levels.bin`
    and filled at load (slots up to the first negative, as `tools/monpool.py` counts `mon`/`nmon`); and
    `sub_005A48C0_ChampionMemberMark` calls `SpecialModsApply` on each pack member (read at `0x005A492C` after the
    session 3 log showed it), so a pack member's mod handlers are a seed oracle like the boss's.
  - The wanderer roll never fired (no WRL line); the tick is checked as one room draw on 516 rooms. No `sparsePopulate`
    roll (stock data, ruling of 2026-10-13), no spawnCol-1 tile placement, no tentaclehead minions, no evilhut object:
    the checker stops on each and none occurred. No classic game, no nightmare game, no multiplayer.
  - Oracles (ADR-0004): the gate's DRLG parts (RoomPopLevelId, the level room count, the Chaos quest test), the logic-box
    list, the four position predicates (value oracles, room and game seed asserted unchanged across every call and the
    arguments asserted), and the seed oracles named above. The game seed at each pass entry is run-time state, taken from
    the log; every game-seed draw inside the pass is predicted.
- **Conclusion:** [monsters/0002](0002-room-population.md) §§ 3–6 are reproduced bit-exactly in 516 rooms, `[C]` under the
  oracles named; the `MonUMax` threshold `≤ 5` is observed at `r = 5`; the special count is the live `+0x2C8`; the
  champion chance is MonUMod row 0 (20); `MonWndr` has no reader beyond the two of the static search on the levels watched.
