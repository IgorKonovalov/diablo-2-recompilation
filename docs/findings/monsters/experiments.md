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
  3. Check: `python3 -I tools/monpool.py check workspace/merged/data/global/excel workspace/logs/monpool-*.log`.
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
