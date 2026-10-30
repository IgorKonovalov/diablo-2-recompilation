# Save experiments

## run:2026-10-12-d2s-io

- **Question:** (plan 0013 Phase 2) Does the game write and read a `.d2s` the way [save/0001](0001-d2s-io.md) reads
  the code? For a save written by the game, is every header field and every item common-part field the runtime value
  the finding names? Are edited fields read back as logged? What does the reader do with a wrong checksum and a wrong
  size field? Does a game without `-seed` reuse the saved map seed for the act? Is the saved seed of a picked-up drop
  the drop's `unit+0x28`, with its quality and ilvl? Is max mana (stat 9) recomputed at load? Is the `.tbl` crc checked
  ([data/0003](../data/0003-string-tables.md))?
- **Setup:** the ADR-0003 harness (`workspace/runtime/game/`, prefix `workspace/wineprefix`, display `:7`), wine 11.17,
  GNU gdb 17.2. Logger `tools/gdb/d2s-io.gdb`, which sources `tools/gdb/d2s-io.py` (breakpoint list and log format
  in its header). Checker `python3 -I tools/d2sio.py check`, which parses each logged buffer and each file with
  `tools/d2s.py` (layout of [d2s.md](../../formats/d2s.md)) using `workspace/merged/data/global/excel`. Test
  characters built by `python3 -I tools/d2sio_saves.py workspace/merged/data/global/excel workspace/runtime/d2sio`:
  - `rt/qitsor.d2s` (sha256 `809be2e9…9ded`): the sample `qitsor` (expansion Sorceress, level 1, 14 items, qualities
    2, 4 and 7) with stat 9 `maxmana` = `8000 << 8` (one stat), header `unk_2c` = `0x0BADF00D` (one header field) and
    `difficulty` = `00 00 00` (bit 7 clear, so the first load does not reuse the map seed);
  - `badsum/qitsor.d2s` (`30048a9b…f201`): `rt` with the stored checksum + 1;
  - `badsize/qitsor.d2s` (`5e241d14…f3d9`): `rt` with `file_size` + 1 and the checksum recomputed over that;
  - `drop/seedtest.d2s` (`9179ef03…2030`): the strong Barbarian of run:2026-10-11-tc-drops (fifth session; clvl 71,
    War Cry on the right button, progression 5), unchanged.
  The `.tbl` case uses `python3 -I tools/tbl_crc_case.py workspace/runtime/game workspace/merged/data/local/lng/eng/patchstring.tbl workspace/runtime`,
  which makes `workspace/runtime/game-tbl-fixed/` and `game-tbl-bad/` (every entry of `game/` symlinked, plus a loose
  `data/local/lng/eng/patchstring.tbl`): in both, byte `0xCF0E` (the last value character) changed; `fixed` has the
  header crc recomputed (`0x8E1C`), `bad` keeps the stock crc `0xF840`. They differ only in those two header bytes
  (sha256 `ffe2290d…7a23` fixed, `380a9168…f9a2` bad). `tools/d2run.py` got `--game-dir` for these runs, and
  `tools/xdrive.py` got `keydown`/`keyup` (Alt held for the item labels).
  Saves: `python3 -I tools/saves.py aside d2sio` / `install d2sio <file>` before the runs, `restore` after; the swap
  was done three times (tags `d2sio`, `d2sio2`, `d2sio3`) so that each run had only its own character in the
  directory. Every restore matched the manifest, and the directory ends with `seedtest.d2s` sha256 `cabccb01…`.
  Saves written by the game were copied **from** the saves directory to `workspace/runtime/d2sio/written/` before
  the next swap. No memory write, no forced state, no seed used as model input.
- **Procedure** (each run starts with no `tools/d2run.py` left, checked with `pgrep -f 'tools/d2run[.]py'`; menu
  clicks are those of `tools/gdb/d2s-io-enter.steps`, *Save and Exit Game* is `key Escape` then `click 400 262`):
  1. `rt` installed. `python3 -I tools/d2run.py --seed 0 --gdb tools/gdb/d2s-io.gdb --steps tools/gdb/d2s-io-enter.steps --after 600 --log workspace/logs/d2sio-1.log`
     (`-seed 0` sets no override: `game+0x84` = 0, [rng/0002](../rng/0002-seed-tree.md)). In town: `key c`, two
     screenshots of the character screen 5 s apart (`workspace/logs/d2sio-1-charscreen.png`, `-charscreen2.png`),
     `key c`; *Save and Exit*; copy the file as `written/save1-qitsor.d2s`; *Single Player* → *OK* (the same process
     loads the save it just wrote); *Save and Exit*; copy as `written/save2-qitsor.d2s`; *Exit Diablo II*.
  2. `badsum` installed: `--seed 0`, steps = `d2s-io-enter.steps`, `--after 10`, log `workspace/logs/d2sio-2-badsum.log`.
  3. `badsize` installed: the same, log `workspace/logs/d2sio-3-badsize.log`.
  4. Control: `written/save2-qitsor.d2s` (bit 7 set, map seed `1869471365`) installed as `qitsor.d2s`; `--seed 7`,
     log `workspace/logs/d2sio-4-seed7.log`.
  5. `.tbl` fixed: `--seed 7 --game-dir workspace/runtime/game-tbl-fixed --game-args=-direct`, steps
     `d2s-io-enter.steps`, log `workspace/logs/d2sio-5-tblfixed.log`.
  6. `.tbl` bad: the same with `game-tbl-bad`, log `workspace/logs/d2sio-6-tblbad.log`; then once without `--gdb`
     (`--attach-wait 0`, a one-line steps file `shot …`), log `workspace/logs/d2sio-6b-tblbad-nogdb.log`.
  7. Drop: `drop` installed. `python3 -I tools/d2run.py --seed 12345 --gdb tools/gdb/d2s-io.gdb --steps tools/gdb/d2s-io-drop.steps --after 1500 --log workspace/logs/d2sio-7-drop.log`
     (Normal, `/players 8`, out to the Blood Moor). Then, one command at a time: `rclick 478 320` three times and
     `rclick 510 275` (War Cry on the monsters in view), `keydown Alt_L` + `shot`, `click 432 310` on the label
     *Cracked Short Staff* + `keyup Alt_L`, `key i` + `shot` (the staff in the inventory), `key i`, *Save and Exit*,
     copy as `written/save3-seedtest-drop.d2s`; *Single Player* → *OK* → *Normal* (`click 400 280`), *Save and
     Exit*, copy as `written/save4-seedtest-reload.d2s`, *Exit Diablo II*. No walking beyond the steps file.
  Check: `python3 -I tools/d2sio.py check workspace/merged/data/global/excel workspace/logs/d2sio-1.log workspace/runtime/d2sio/written/save1-qitsor.d2s workspace/runtime/d2sio/written/save2-qitsor.d2s`,
  and the same for logs 2, 3, 4 and 7 (log 7 with `save3-…` and `save4-…`).
- **Observed:**
  - **Writes.** Every *Save and Exit* wrote the file **twice**, byte-identical: `PLRSAVE_Save` called from
    `0x0052CA5F` (`sub_0052CA10_SaveGameClients`, every client of the game) and then from `0x0052C940`
    (`sub_0052C900_SaveClients`), each time `PLRSAVE_WriteFile` from `0x005324F0` (`PLRSAVE_Save`, the
    no-host-callback branch), path `C:\users\<user>\Saved Games\Diablo II\<name>.d2s`. 8 writes in runs 1 and 7. The
    checker: logs 1 and 7, **1492 comparisons, 0 mismatches** (828 + 664, reads included). Per write: magic,
    version 96, `file_size` = bytes written, checksum = the model over the buffer, weapon set, name, status u32
    (client `+0x0A` | `0x20`), class, `0x29` = 16, `0x2A` = 30, level = the writer's stat-12 read, `unk_2c` = client
    `+0x488` (`0x0BADF00D`, carried from the edited file), `last_played` = the writer's `time()`, `unk_34` =
    `0xFFFFFFFF`, the four mouse skills against player data `+0x70`–`+0x8C`, `difficulty` = `act | 0x80` in the game's
    difficulty byte and 0 elsewhere, `map_seed` = `game+0x7C`, `0xCF` = client `+0x480`, the other `unk_bf` bytes 0,
    the `gf` list = the unit's base stat list (11 and 13 stats). Per item, 14 and 11 items per write, the item at the
    logged offset of the final pass: flags = item-data flags with bit 19 cleared and bit 23 set (bit 21 set on the
    simple items), version = item data `+0x30` (101), location = unit mode, body, store = page + 1, code, and for the
    extended items seed = `unit+0x28`, ilvl, quality, gfx. Each saved file hashes to its logged buffer.
  - **Reads (runs 1, 4, 7).** 5 loads, all `D2S_ReadHeader` code 0; the stats read (`RSTAT`, 11 or 13) equal the file's
    `gf` list in order, including stat 9 = `2048000` (the edit) and the items read (`RITEM`, 14, 10 or 11) equal the file's
    items in order: extended items get `+0x28` = the saved seed and `RNG_SeedInit` gives `{seed, 666}` at `+0x20`;
    simple items get seed 0, ilvl 1, quality 2. Client `+0x488` = the file's `unk_2c` (`0x0BADF00D`) after each load.
  - **Item flags bit 13.** The flags read keep bit 13 (`0x822010` at `RITEM`), and every write after a load has it
    clear (`0x00822010` in `rt` → `0x00820010` in `save1`). The staff dropped in run 7 had bit 13 **set** at its creation
    (`CPOST` flags `0x82010`), **clear** at the first save after the pickup (final-pass `SBIT` `0x80010`, file
    `0x00800010`) and on the reload (`RITEM` `0x800010`). So something between the drop and the write cleared it; the
    writer masks only bit 19. The run does not show which step (the pickup is the only action in between).
  - **Map seed (case 4).** Run 1, first load: `GAME` clock path, map `1869471365`; file bit 7 clear → no copy; both
    `ACT` lines `map=1869471365 seed=b9950ef3:2e79ec20`; the first save wrote `map_seed` `1869471365` and `difficulty`
    `80 00 00`. Second load in the same process: clock map `1282649071`, `RMAP` g6a 3, g84 0, bit7 `0x80` →
    `RMAP2` `game+0x7C` = `1869471365`, and both `ACT` lines `map=1869471365 seed=b9950ef3:2e79ec20`, the act seed of
    the first game. Control (run 4, `-seed 7`, same bit-7 save): `GAME` override path, g84 1, `RMAP2` stays 7,
    `ACT map=7 seed=eb6df7fd:00000002`.
  - **Bad checksum (run 2):** `RSUM computed=2096918441 stored=2096918442`, `D2S_ReadHeader` returned **6**, the
    failure exit mapped it to **14** (`g_D2sLoadErrorMap[6]`); no section read, no `RMAP`; the game was back at the main
    menu (`workspace/logs/d2sio-2-badsum.png`). **Bad size (run 3):** checksum equal (`2097180585`),
    `size_field=1180`, `len=1179`, return **5**, mapped to **14**, main menu again. The checker predicts each load's code from the file alone (6 if the model checksum differs from the stored one, else 5 if the size field differs from the length, else 0) and asserts it against `D2S_ReadHeader`'s return and the failure exit's internal code, with mapped code 14 (4 comparisons per bad load, 0 mismatches; the bad-size file passes the checksum test). Return codes 2–4, 7–18 were not seen.
  - **Stat 9 (case 6).** `LFIN`/`LFIN2` (entry and exit of `D2S_LoadFinish`): stat 9 = `2048000` (`8000 << 8`) in
    both the base and full lists, stat 7 = `10240`, unchanged; stat 8 = the value read. In town the character screen
    showed Mana **8000** / **2485**, then 8000 / 3482 five seconds later: the left box (max) is stat 9 as saved, the
    right box (current) rises. At the second save stat 9 was still `2048000`.
  - **Drop (case 5).** `CPOST` (after `sub_0055A550_DropCreateItem`): unit id 11, `sst `, mode 3, `+0x28` =
    `2728687498`, quality 1, ilvl 1, flags `0x82010`. After the pickup the final-pass `SBIT` of the same unit and id:
    mode 0, the same `+0x28`, quality and ilvl; the file item at `0x403`: seed `2728687498`, quality 1, ilvl 1
    (checker: 6 comparisons over the two writes, 0 mismatches). On reload (`save3` read) `RITEM` gave `+0x28` =
    `2728687498`, quality 1, ilvl 1, flags `0x800010`.
  - **`.tbl` (case 7).** Every game entry logged three `STRTABLE_LoadFile` crc checks (sizes 390570, 53008, 173234:
    `string`, `patchstring`, `expansionstring`), computed = stored. Run 5 (`fixed`, loose file under `-direct`):
    `patchstring` computed = stored = **36380** (`0x8E1C`), the value of `tools/tbl.py`'s CRC-16/CCITT-FALSE for the
    modified file and not the stock `63552`, so the loose file was the one read; the game entered normally. Run 6
    (`bad`): the game process ended before the debugger attached, with no window. Its crash report
    (`workspace/runtime/game-tbl-bad/BlizzardError/2026-10-12 12.09.15/Crash.txt`) reads
    `[Halt] (Unrecoverable internal error …) failed at (206)` with the stack starting at `0x0052596E`, the fatal call
    after the crc compare (`push 0xCE` = 206 at `0x00525959`), called from `0x00525CCA` (`STRTABLE_LoadAll`). The
    second launch without gdb also showed no window (`no window named 'Diablo II'`) and wrote a second report.
- **Raw logs:** `workspace/logs/d2sio-1.log` (sha256 `8f9a0568…5858`), `d2sio-2-badsum.log` (`1c561ffe…4616`),
  `d2sio-3-badsize.log` (`63c93e0f…adf3`), `d2sio-4-seed7.log` (`edcad6c4…e273`), `d2sio-5-tblfixed.log`
  (`45ba0b94…1650`), `d2sio-6-tblbad.log` (`4342a2d3…3c0c`), `d2sio-6b-tblbad-nogdb.log` (`ec0f297f…b7aa`),
  `d2sio-7-drop.log` (`53bd5ed6…e866`); written saves in `workspace/runtime/d2sio/written/`: `save1-qitsor.d2s`
  (`614fceee…69fe`), `save2-qitsor.d2s` (`9a3e0f5b…fde7`), `save3-seedtest-drop.d2s` (`2dad064f…16e8`),
  `save4-seedtest-reload.d2s` (`94fe5930…6156`); screenshots `workspace/logs/d2sio-*.png` (workspace, not in git).
- **Deviations and limits:**
  - Item grid `x`/`y` and the ground position, the property lists, the quality-specific fields (affix, unique and
    set ids) and the mercenary/golem/corpse sections were not compared (no logged runtime source; no mercenary,
    golem or corpse in these saves). Hotkeys were checked only through the file round trip (none set).
  - One drop only, created by a Normal Blood Moor monster; the claim is about `unit+0x28` and the saved fields, not
    about TC behaviour. Its seed was not re-derived from the game seed here; the server-unit draw behind `+0x28` is
    `[C]` in [rng/0002](../rng/0002-seed-tree.md#units) (fn:sub_00552DF0_UnitSeedInit@0x00552DF0).
  - Only reader codes 0, 5 and 6 (and the mapped 14) were seen; the version, name, magic, status and section codes
    were not exercised.
  - The bad `.tbl` was not caught under gdb (the load runs before the harness can attach); the halt is shown by the
    crash report and by the A/B pair, which differs only in the stored crc.
- **Conclusion** (fn:PLRSAVE_WriteFile@0x00532240, fn:D2S_ReadHeader@0x0056A090): [save/0001](0001-d2s-io.md): the writer path for *Save and Exit*, the header field sources, the
  `gf` stream, the item common part and the extended item's seed/ilvl/quality, the checksum and size checks with their
  codes 6 and 5, the map-seed reuse condition, `unit+0x28` ↔ saved seed for a drop, and stat 9 not recomputed at load
  become `[C]`. The finding's bit-13 reading ("items created in the session carry it into the save") does not hold for this drop: set at creation, cleared before the save.
  [data/0003](../data/0003-string-tables.md): the crc check, its CRC model and the fatal halt become `[C]`.

- **Addendum 2026-10-16: plan 0038 batch S1a (static, no new session; `tools/sweep_s1a.py` sha256 `c07086a3…`, log manifest `workspace/logs/sweep-s1a-manifest.txt` `18318973…1676`).** The logs above (hashes as recorded) and the
  71 d2s-io-logged logs of run:2026-10-16-player, re-read together:
  ```
  python3 -I tools/sweep_s1a.py writes
  S1A writes auto_zero=588 bad=0 cf_list_order_hand_first=200 compactsave_0=588 compactsave_1=1372 hand_items=328
      items=1960 unk_bf_rest_zero=200 writes=200 wsw_nonzero=0
  python3 -I tools/sweep_s1a.py reads
  S1A reads bad=0 lfin_after_items=67 loads=104 ritem_auto_zero=252 ritem_nbytes_eq=747 ritem_nbytes_eq_simple=495
      ritems=747 rstat_values=803 stubs=35 stubs_class56_bit5=8
  ```
  Per write: `weapon_set` = client `+0x45C` (0 in all 200), `unk_bf` rest 0 and `0xCF` = client `+0x480`, flags bit 21 =
  `compactsave`, `has_class` = item data `+0x36` ≠ 0, the hand-slot items after every other top-level item while the
  earlier serialiser calls of the same write meet them first. Per load: the order header, stats, items, `LoadFinish`;
  each `RITEM` byte count is the file item's decoded length; `RSTAT` values are the file's. Conclusion:
  [save/0001 § Plan 0038 batch S1a](0001-d2s-io.md#plan-0038-batch-s1a-2026-10-16) (rows 5, 14, 24, 45, 58, 71, 75, 76,
  84, 86, 103, 109, 131).

## run:2026-10-15-acts-3-5-load

- **Question:** (plan 0020 Phase 4, the load test of [save/0002](0002-quest-words.md)) Does a save built with the
  `quests: all` recipe key show the waypoint tabs of Acts II–V after loading, with the Act V tab selectable, and
  does waypoint travel into each act work from it?
- **Setup:** the session of [run:2026-10-15-acts-3-5](../drlg/experiments.md#run2026-10-15-acts-3-5) (harness slot 1,
  display `:8`, prefix `workspace/wineprefix-1`, logger `tools/gdb/drlg-preset-play.gdb`, map seed 21, Normal, an
  expansion game). Character `UniqNova.d2s` (sha256 `2c793a3df3773c0f…`) built with
  `python3 -I tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/uniqnova.json workspace/samples/d2s-owner/smpsor-l50.d2s workspace/runtime/h20p4-chars/UniqNova.d2s`
  (recipe `3c2f57dc8921dc3d…`: `"quests": "all"`, waypoints `all` in the three difficulties, progression 15,
  difficulty bytes `0x83`), installed with `tools/saves.py --slot 1` (tag `h20p4`). Read back before the run: status
  byte `0x20` (expansion), and in each of the three quest blocks words 7, 15, 23, 26 and 28 = `0x0001`.
- **Procedure:** the game loads the character in the Act IV town (difficulty byte `0x83`: act index 3). A scratch
  driver built on `tools/d2pilot.py` (`Pilot.click_at`, `menu_open`, `shot`) clicked the town waypoint where the log's
  `OBJP` line placed it, waited for the list, took a screenshot, then clicked act tabs I to V in turn (tab x = 115 +
  62·(i − 1), y 73) with a screenshot 0.6 s after each click, then pressed Escape. Then `tools/d2pilot.py --slot 1 wpchain`
  travelled `2,8 3,6 3,8 3,9 5,4 5,8 1,1 1,2 1,4 1,5`.
- **Observed:**
  ```
  wptabs-open: five tabs I II III IV V drawn; tab IV selected (the act of the player's level); rows of Act IV
  wptabs-tab1..tab5: each click selected its tab and listed that act's waypoints
    (tab II: Lut Gholein ... Arcane Sanctuary, Canyon of the Magi; tab V: Harrogath ... Worldstone Keep Level 2)
  wpchain: level 103 -> 74 -> 80 -> 83 -> 101 -> 113 -> 118 -> 1 -> 3 -> 5 -> 6, every hop in 0.2-2.4 s
  ```
  The same save travelled to Acts I, II, III and V in five more sessions of that run (seeds 22–26: rows 2,4 2,5 2,6
  3,9 1,1–1,7).
- **Raw data:** screenshots `workspace/logs/acts35/a35-s1-wptabs-open.png`, `-tab1.png` … `-tab5.png`; log
  `workspace/logs/acts35/a35-s1-21-normal.log` (`86e3e40002679d95…`).
- **Deviations and limits:** only a save with **all** five words set was loaded, in Normal; Nightmare and Hell blocks
  were set but not loaded, and the per-word gate (word 7 alone, 26 without 28) was not isolated, so the tab-per-word
  reading stays `[I]` (fn:sub_0049C9C0_WpMenuDraw@0x0049C9C0, fn:sub_0049C760_WpTabClamp@0x0049C760).
- **Conclusion:** the "all acts open" recipe of [save/0002](0002-quest-words.md) works as a whole in an expansion
  Normal game: all five tabs drawn and selectable, travel into every act. Arcane Sanctuary (74) opened by waypoint
  (Act II row 8) from this save.

## run:2026-10-27-sweep-d2s-play

- **Question:** (plan 0038 Phase 2, batch H1b, [inventory § 5](../../plans/0038-inventory/README.md#harness-batches))
  the 48 inferred statements of [inventory save-d2s](../../plans/0038-inventory/save-d2s.md) rows 1–4, 6, 18, 19, 21,
  25, 31, 33–35, 37, 39–43, 48, 55–57, 60, 72, 73, 77, 78, 83, 88, 102, 108, 110–118, 124, 125, 127 and
  [hirelings](../../plans/0038-inventory/hirelings-README.md) row 24: who calls `PLRSAVE_Save` and through which branch
  (single player, a one-client TCP/IP host, Alt+F4, a death), the join load chain, the section writers and readers in
  order, the header's weapon set, swap skills, hotkeys, graphics and mercenary fields, `D2S_LoadFinish`, the corpse,
  mercenary and golem lists, the item writer's runeword, quest and `ValShift` paths, the reader's rebuilt weapon stats,
  and item flag bit 13 on drops.
- **Setup:** the ADR-0003 harness on **slot 1** (display `:8`, prefix `workspace/wineprefix-1`), agent-driven play (no
  owner play), stock data. The slot's empty saves directory set aside as tag `h1b`, restored and set aside again before
  each launch (`tools/h1b_sessions.py` does both), restored after the last session (empty, all sha256 match).
  - **Characters** (`workspace/runtime/h1b-chars/`, hashes in `h1b-manifest-r2.sha256`): `H1bSor` (`116d0f90…`,
    recipe `tools/d2s_recipes/h1bsor.json` `822dc869…`: Sorceress level 80, gold 900 000 and bank 3 000 000 above the
    level-80 maxima, swap skills set, hotkey slot 2 `left:Teleport`, a mercenary of Id 0, seed 12345, name 3, a short
    bow), `H1bDead` (`9ff431ea…`, `h1bdead.json` `0e9d4353…`: the same with a **dead** mercenary of Id 7, seed 54321,
    name 20, experience 3 000 000 above a level threshold, character experience 750 000 000 at level 80), `H1bWeak`
    (`3acba754…`, `h1bweak.json` `8ea93db5…`: 1 life point, for the death), `H1bHire` (`a1313dd0…`, `h1bhire.json`
    `bff69e4f…`: no mercenary), all built on `smpsor-l50.d2s` with `python3 -I tools/d2s.py build`; `QuestRewards`
    (`246515c5…`) and `QuestRewardsH` (`14c28526…`) from the plan 0032 recipes `questrewards.json` (`b6e54e35…`) and
    `questrewardsh.json` (`4fd8d541…`); the sample `qitbarb` (`98042d88…`, run:2026-10-11-d2s-samples, the corpus's one
    runeword). Tool-built inputs (ADR-0003): the gold above the maximum, the dead mercenary's header and its experience
    are values the builder wrote, not states the game made; the hired, the killed-in-play and the swapped cases are
    the game's own.
  - **Logger** `tools/gdb/d2s-h1b.gdb` (`bcd53b34…`; `d2s-h1b-hire.gdb` `05c0b954…` for the hire session adds the
    hirelings loggers) sourcing `tools/gdb/d2s-io.py` (`5a7ad56d…`, unchanged), `pilot.py` and `tools/gdb/d2s-h1b.py`.
    **Two revisions of `d2s-h1b.py` were used.** Revision 2 is the committed file (`8a27dc8c…`). Revision 1 was not
    kept as a file; it is revision 2 less three pieces: the function `h1b_full` (the unit's full stat array, stat list
    `+0x48`/`+0x4C`) and the `"full"` key it adds to the `RIST` and `SBX` lines; the function `h1b_wskl` and its four
    breakpoints (0x0056915B, 0x00569191, 0x005691C2, 0x005691FB: the `WSKL` lines, the mouse and swap skill the header
    writer reads). Every other breakpoint and line is the same. Revision 1 logged dead, tcpip, shut, hell-r3, hire, qr,
    qrh and rw; revision 2 logged rt-r2, qr-r2, qrh-r2, drop and rw-r2. `tools/sweep_h1b.py` skips, on a log without
    `full`, the property checks (stats 7/9 `ValShift`, 326 after group 57, 52/53, 356, and the write-side runeword
    field = `Runes +0x82`), and keeps the two d2sio mouse comparisons only where there are no `WSKL` lines.
  - **Runner** `tools/h1b_sessions.py` (`d11afb5c…`), steps `enter-normal`, `enter-hell`, `d2s-io-enter` and
    `tools/gdb/h1b-tcpip-host.steps` (`9cb8bcc0…`). **Checker** `tools/sweep_h1b.py` (`c0063a8b…`), which runs
    `tools/d2sio.py check` on each log first.
- **Procedure:** `python3 -I tools/h1b_sessions.py run --slot 1 --tag h1b --saves workspace/runtime/h1b-chars --run h1b
  <session>` (each launch is `d2run.py --slot 1 --seed N --gdb … --steps … --after 2400 --install h1b <save> --log …`;
  `slots.py stop 1` after each session). *Save and Exit* is Escape, then (400, 268); a reload is *Single Player*, *OK*
  and the difficulty in the same process. Check: `systemd-run -q --user --scope -p MemoryMax=4G python3 -I
  tools/sweep_h1b.py check workspace/merged/data/global/excel $(ls workspace/logs/h1b/*.log)` →
  `workspace/logs/h1b/check/sweep-h1b-check-r2.txt` (`f44b92e0…`). Manifests, `sha256sum -c` from `workspace/logs/h1b`:
  `h1b-manifest-r2.sha256` (`f0e88782…`: the 13 kept logs, the check output, the seven input saves) supersedes
  `h1b-manifest.sha256` (`18f92562…`: the first 12 logs and `check/sweep-h1b-check.txt`, 2 502 comparisons, the check
  before rw-r2), kept as it was; `h1b-manifest-dev.sha256` (`122aca67…`: the four logs in `dev/`, listed without the
  directory, so it is checked **from `workspace/logs/h1b/dev`**: `cd dev && sha256sum -c ../h1b-manifest-dev.sha256`;
  `lane/h1b` review fix). No log has `internal-error:`.

  | Session | Seed | Save | Logger rev. | What was done | Lines |
  |---|---|---|---|---|---|
  | rt-r2 | 27101 | H1bSor | 2 | 75 s in town (the autosave control), `w` (weapon swap), *Save and Exit*, reload, *Save and Exit* | 1 325 |
  | dead | 27102 | H1bDead | 1 | load, *Save and Exit*, reload, *Save and Exit* | 1 319 |
  | tcpip | 27103 | H1bSor | 1 | TCP/IP *Host Game*, one client, 80 s, *Save and Exit* | 439 |
  | shut | 27104 | H1bSor | 1 | Alt+F4 in game | 668 |
  | hell-r3 | 27105 | H1bWeak | 1 | Hell River of Flame, teleports with no attack until the death (the Rogue killed in play), *Save and Exit*, reload in Hell, *Save and Exit* | 2 834 |
  | hire | 27106 | H1bHire | 1 | Kashya hire, *Save and Exit*, reload, *Save and Exit* | 3 287 |
  | qr, qr-r2 | 27107 | QuestRewards | 1, 2 | load, *Save and Exit* | 988, 995 |
  | qrh, qrh-r2 | 27108 | QuestRewardsH | 1, 2 | load in Hell, *Save and Exit* | 989, 997 |
  | rw, rw-r2 | 27109 | qitbarb | 1, 2 | load, *Save and Exit*, reload, *Save and Exit* | 1 758, 1 774 |
  | drop | 27111 | H1bSor | 2 | Normal City of the Damned, 15 Nova hops, a 240 s hold (no pickup made), *Save and Exit*; `H1B_WATCH=1` | 2 785 |

  Development logs in `dev/`: rt (revision 1: its two d2sio mouse mismatches per swapped write are the d2sio model's,
  see below), hell and hell-r2 (no death: the pilot stood, then stopped at the 1-point life orb), drop 27110
  (waypoint row 1 is the town). rw-r2 was run at the resume (2026-10-27, the same slot and tag) because the revision-1
  rw log skips the write-side runeword check; its `keep` steps overwrote the rw session's copies under
  `workspace/runtime/h1b-chars/h1b-rw/` (not in a manifest; the logs carry the buffers). *(`lane/h1b` review fix:
  rw-r2 was not the only one. The runner keeps copies per session name without the `-r2` suffix, so rt-r2, qr-r2 and
  qrh-r2 also overwrote the copies of dev rt, qr and qrh under `h1b-rt/`, `h1b-qr/` and `h1b-qrh/`, and drop 27111
  overwrote dev drop 27110's under `h1b-drop/` (file times 08:20–08:35). No claim and no check reads a copy:
  `sweep_h1b.py` reads only the logs.)*
- **Observed** (`check/sweep-h1b-check-r2.txt`; counts as printed):
  ```
  ALL 2798 H1B comparisons, 0 failing (mismatches + d2sio failures)
  per log: rt-r2 342, dead 300, tcpip 46, shut 150, hell-r3 353, hire 292, qr 132, qr-r2 148, qrh 132, qrh-r2 148,
           rw 272, rw-r2 296, drop 187
  who: PLRSAVE_Save callers 0052C940 / 0052CA5F in every session; 0057FD88 once (hell-r3, the death);
       branches SAVE in every single-player write, SVCL (0x00532340) 2 in tcpip; host callback 0 at every AUTO line;
       AutosaveTick logged at call 1 and every 500th call (up to 6 500, drop), saves returning into it 0;
       SaveAllOnShutdown entries 1 or 2 per session (ret 0044F2FE single player, 0044D052 tcpip), its saves 0
  join: single player ClientAddPlayerToGame<-005301E9 PlayerLoad<-00539809 PLRSAVE_ReadFile<-005344E0
        D2S_ReadSave<-0053447A (every load); tcpip D2S_ReadSave<-00534563, no PLRSAVE_ReadFile
  mouse rt-r2 writes 1-4: weapon set 1; sources left 42 right 43 swapA 54 swapB 48
  merc: tool-built 12345/3/0 (rt-r2, drop) and 54321/20/7 dead (dead), hired 2573073805/0/1 exp 52424400 (hire),
        killed in play: dead test 1, merc mode 12 (hell-r3); hire read 1: all-zero header -> merc none, 0x005726C0 0
  lfin rt-r2 read 1: gold 900000 (max 800000) -> 0; bank 3000000 (max 2500000) -> 0; stamina 74240;
        stat 30 742730244 = row 80 (742730244), row 81 is 809986056
  lfin hire read 1: gold 500000 (max 800000) -> 500000; dead read 1: experience 750000000, stat 30 742730244
  vshift rt-r2: stat 9 file 5 -> runtime 1280, stat 7 file 5 -> 1280, stat 9 file 1 -> 256
  poison rt-r2, drop: dgr 57/58/59 = [41, 41, 75], 326 = 1; magdmg: 9cr 52/53 = [50, 120]
  rw rw-r2 writes 1-4: lsd field 20639, RWW [20639, 20639]
  corpse hell-r3: 1 corpse, 11 items (location 1, body 1-11), written 5 times, read 1 corpse, 11 items
  bit13 drop: 5 drops (ids 27-31: gld, mp3, hp5, cm3, gld) with 0x2000 at creation, each cleared by the ground pass;
        watch: unit id 27 armed flags 0x82010; 0 writes; GOLD 0; COPY 11 (hell-r3)
  ```
  The d2sio part has 0 mismatches except rt-r2's four mouse words (file 42/43, runtime 0: d2sio compares player data
  `+0x74`/`+0x70`, which a swap leaves 0, where the writer reads the unit's current skill, `0x00620190`/`0x006201D0`;
  the `WSKL` group compares that source) and hell-r3's `RITEM` count (25 = 14 loaded + 11 `ItemCopy` recreations of the
  corpse items at the death, the 11 `COPY` lines). *(2026-10-27, `lane/r1h`: the d2sio model is fixed. `tools/d2sio.py` `29561293…` compares the mouse words
  with `WSKL` and counts a load's items up to `LFIN2`; the wrapper in `tools/sweep_h1b.py` `b2d9ac1a…` is removed. The
  re-check on the 13 logs, `workspace/logs/r1h/sweep-h1b-check-r1h.txt` (`c39fd4bd…`, manifest
  `r1h-manifest.sha256`), gives 2 798 H1B comparisons, 0 failing, and 0 d2sio mismatches. The replaced revisions,
  `2ac6e9f1…` and `c0063a8b…`, made the output above.
  [save/0001 § Plan 0038 r1h](0001-d2s-io.md#plan-0038-r1h-the-host-callback-setter-and-the-d2sio-model-2026-10-27).)*
- **Deviations and limits:** revision 1 (above) leaves the property checks to the four revision-2 logs that hold
  items with those properties (rt-r2, qr-r2, qrh-r2, drop) and the runeword write to rw-r2. The watchpoint armed on
  drop 27 logged no hit, though that drop's bit was cleared (`B13C`): it is no control, so no absence is claimed from
  it. No mode 3/5 item was in any save, no low-quality item, no socketed item copy, no negative gold, no golem item, no
  joiner on the TCP/IP host and no hosted callback (no `SVCB` line).
- **Conclusion:** see [save/0001 § Plan 0038 batch H1b](0001-d2s-io.md#plan-0038-batch-h1b-run2026-10-27-sweep-d2s-play)
  and [hirelings/0001 § Plan 0038 batch H1b](../hirelings/0001-hirelings.md#plan-0038-batch-h1b-run2026-10-27-sweep-d2s-play):
  25 statements raised, 14 raised in part, 7 shortfalls, 2 proposed d-none.

## run:2026-10-27-sweep-d2s-load

- **Question:** (plan 0038 Phase 2, batch H1a, [inventory § 5](../../plans/0038-inventory/README.md#harness-batches))
  the 46 inferred statements of [inventory save-d2s](../../plans/0038-inventory/save-d2s.md) rows 9, 10, 17, 22, 23,
  26–30, 36, 38, 44, 46, 47, 49, 50, 52–54, 59, 62, 65, 68, 80, 90, 91, 105–107, 126, 132, 139, 140,
  [hirelings](../../plans/0038-inventory/hirelings-README.md) 3, 30, 32, 33,
  [player-creation](../../plans/0038-inventory/player-creation.md) 1, 8, 9, 11, 20, 34 and
  [items-uniques-sets](../../plans/0038-inventory/items-uniques-sets.md) 21: what the server's reader does with a
  malformed, edited or old-format save (the codes of `D2S_ReadSave`, `D2S_ReadHeader`, `D2S_CheckStatus` and the
  section readers, the error map, the 8 KiB cap, the header fields not read, the act clamp, the quest and waypoint
  records, the skill count, the old stat form, ears, personalized names, realm data, out-of-range unique and set ids,
  item params, class 7, the mercenary item list). Plus the S1b leftover session the plan 0051 P1a review assigned to
  H1a (CalcSor; data-calc 19, rng-seeds 11; the rows stay S1b).
- **Setup:** the ADR-0003 harness on **slot 2** (display `:9`, prefix `workspace/wineprefix-2`), agent-driven, no
  owner play, stock data, the shared game directory unchanged. The slot's empty saves directory was set aside as tag
  `h1a` and restored before each launch and after the last (empty, all sha256 match).
  - **Saves:** `python3 -I tools/h1a_saves.py workspace/merged/data/global/excel workspace/runtime/h1a`
    (`eebfeba2…`), one directory per case; each file's size, size field, checksum and sha256 are in
    `workspace/logs/h1a/check/h1a-saves-build.txt`. The base is the sample `qitsor.d2s` (`81a75f54…`, expansion
    Sorceress level 1, 14 items); the stubs come from `stub-seedtest.d2s`; `MercMF.d2s` is `mercmf.json` on
    `smpsor-l50.d2s` (`e98a6b9d…`, the `test_d2s.py` pin); `CalcSor.d2s` is `calc-sor.json` on
    `runtime/saves-backup/p0005/smpsor.d2s` (`787a2291…`, the pin). Tool-built, malformed on purpose (ADR-0003 inputs,
    ADR-0013 § Neutral): they back the reader's handling of the built bytes, never how a game makes them.
  - **Logger** `tools/gdb/d2s-h1a.gdb` (`e9b40dcc…`): `pilot.py`, `d2s-io.py` (`5a7ad56d…`, unchanged),
    `d2s-h1b.py` (`8a27dc8c…`, unchanged) and the new `tools/gdb/d2s-h1a.py` (`00d2f737…`; lines `RSV`,
    `LEG`, `LEGR`, `PLD`, `RCST`, `RACT`, `RSKC`, `RSTV`, `RSTL`, `RQW`, `RWP`, `RIX`, addresses in its header).
    Steps `tools/gdb/h1a-menu.steps` (`92c31f98…`: activate the window, stay at the main menu).
  - **Runner** `tools/h1a_sessions.py` (`097a8a77…`). One game process per session; per case: copy the
    listed file over the character's `.d2s`, *Single Player* (the character screen reads the directory), copy the
    case's file over it (**the swap**), OK and the difficulty, wait for `PLD`, then *Save and Exit* (a load that
    passed; the written file kept under `workspace/logs/h1a/<stem>-saves/<case>/`) or back to the menu. Each case's
    first log line is in `<stem>.marks.jsonl`. The copies are made by the runner into slot 2's saves directory only,
    while `h1a` is set aside.
  - **Checker** `tools/sweep_h1a.py` (`bd1a2a9f…`), which runs `tools/d2sio.py check`
    (`523991f2…`) on each log first. `d2sio.py` was extended (the r1h revision was `29561293…`): the code
    predicted from the file in `D2S_ReadHeader`'s order (4 short, 6, 5, 7 version), the mapped code from the table
    `g_D2sLoadErrorMap` (read from the image), the codes that need the client or the game printed as `context=`, and a
    layout `tools/d2s.py` refuses (realm data, version 94, a skill count other than 30) reported as `UNPARSED` instead
    of a crash. Regression: the 13 H1b logs give the r1h output byte for byte once ` context=None` is dropped
    (`check/sweep-h1b-recheck-h1a.txt`, 2 798 comparisons, 0 failing), and the five d2s-io logs of this record's
    first run give the same totals as `main`'s checker (`check/d2sio-runs-2026-10-12-recheck-h1a.txt`).
- **Procedure** (`python3 -I tools/h1a_sessions.py run --slot 2 --tag h1a --cases workspace/runtime/h1a --run h1a NAME`):
  1. `main` (seed 27201, log `h1a-s2-27201-main.log`): 26 cases in one process, in this order: magic, short, v97,
     v91, class8, hcon (listed base, swapped hc), hcsoft (hc / base), hcdead (hc / hcdead), clson (base / classic),
     expon (classic / base), prog4 (prog5 / prog4, Nightmare), prog0 (prog10 / base, Hell), both, wpbad, stubtrail,
     bigbad, setbad (each back to the menu; setbad loaded and was saved and exited), then big8k, fields, skills29,
     items, v94, prog5 (Nightmare), prog10 (Hell), stubok, uniqbad (each loaded, *Save and Exit*, the file kept).
  2. `order` (27204, `h1a-s2-27204-order.log`): hdrshort, v97sum, namehc, class8hc (menu), param, slots8, v94s12,
     act6 (loaded, saved), class7 (the process halted; the runner stopped).
  3. `stub7` (27205, `h1a-s2-27205-stub7.log`): stub7 (the process halted).
  4. `name15` (27202, `h1a-s2-27202-name15.log`): the 15-character character listed and loaded, saved.
  5. `mercmf` (27203, `h1a-s2-27203-mercmf.log`): MercMF in Normal, saved.
  6. S1b (27210, `h1a-s2-27210-s1b.log`): `python3 -I tools/d2run.py --slot 2 --seed 27210 --gdb
     tools/gdb/s1b-pieces.gdb --steps tools/gdb/s1b-pieces.steps --after 30 --install h1a
     workspace/runtime/h1a/s1b/CalcSor.d2s --log workspace/logs/h1a/h1a-s2-27210-s1b.log` (the plan 0051 P1a staging,
     unchanged: hover, three potions drunk, *Save and Exit*, the same character loaded again), the written save copied
     to `h1a-s2-27210-s1b-CalcSor-written.d2s`.
  Crash reports of the two halts (the game writes them under the shared game directory's `BlizzardError/`) were copied
  to `workspace/logs/h1a/class7-crash/` and `stub7-crash/` (`Crash.txt`); nothing in the game directory was changed.
- **Check:** `systemd-run --user --scope -p MemoryMax=4G python3 -I tools/sweep_h1a.py check
  workspace/merged/data/global/excel workspace/runtime/h1a $(ls workspace/logs/h1a/h1a-*.log)` →
  `workspace/logs/h1a/check/sweep-h1a-check.txt`: **410 H1A comparisons over 38 cases, 0 failing**; the `d2sio.py` part of each of the five logs 0 mismatches (5440 comparisons; 6 buffers that `tools/d2s.py` does not parse reported as `UNPARSED`, one read that never returned as `UNTERMINATED`). The S1b log is checked with its own three checkers (`check/s1b-checks.txt`): `rng.py seedtree` 1 884/1 884, `calc.py hover` 7 `CH` lines and 0 hover evaluations, `calc.py check` 52 evaluations, 0 mismatches.
- **Observed:**
  ```
  case       listed / swapped        D2S_ReadSave  ReadHeader  CheckStatus  RERR int->mapped  PLD   outcome
  magic      base / magic             9 (1179 B)   -           -            -                 9     menu
  short      base / short (7 B)       9 (7 B)      -           -            -                 9     menu
  v91        base / v91               legacy 14    -           -            -                 14    menu
  hdrshort   base / first 0x100 B     -            4           -            4 -> 9            9     menu
  v97sum     base / v97 + sum+1       -            6           -            6 -> 14           14    menu
  both       base / sum+1, size+1     -            6           -            6 -> 14           14    menu
  bigbad     base / 8392 B valid      (8192 read)  6           -            6 -> 14           14    menu
  v97        base / v97               -            7           -            7 -> 1            1     menu
  namehc     base / qitsox + hc       -            7           -            7 -> 1            1     menu
  class8hc   base / class 8 + hc      -            11          11           11 -> 20          20    menu
  class8     base / class 8           -            4           0            4 -> 9            9     menu
  hcon       base / hc                -            11          11           11 -> 20          20    menu
  hcsoft     hc / base                -            12          12           12 -> 19          19    menu
  hcdead     hc / hc+dead             -            10          10           10 -> 21          21    menu
  clson      base / classic           -            9           9            9 -> 23           23    menu
  expon      classic / base           -            8           8            8 -> 24           24    menu
  prog4      prog5 / prog4, NM        -            13          13           13 -> 17          17    menu
  prog0      prog10 / prog0, Hell     -            14          14           14 -> 18          18    menu
  prog5      prog5 / prog5, NM        -            0           0            -                 0     saved
  prog10     prog10 / prog10, Hell    -            0           0            -                 0     saved
  stubtrail  base / stub + 10 B       -            2           0            2 -> 9            9     menu
  stubok     base / stub              -            2           0            -                 0     new character, saved
  wpbad      base / marker 0x0303     -            0           0            16 -> 3           3     menu
  setbad     base / set id 4000       -            0           0            -                 0     item dropped, 13 items saved
  class7     base / class 7           -            (none)      0            -                 -     halt 1210 (Crash.txt)
  stub7      base / class-7 stub      -            2           0            -                 -     halt 1210 (Crash.txt)
  big8k fields skills29 items v94 v94s12 slots8 act6 param uniqbad name15 mercmf: header 0, loaded, saved
  big8k     RHDR 8192 of 8392 bytes; written 1179
  fields    RACT 0x85 -> 0; Hell words 1/2/3 0x6002->0x8002, 0x6000->0x0000, 0x0002->0x8002; waypoints Normal
            0x0102/0002 -> 0x0102/0003, NM 0x0101/000F and Hell 0000/000F -> 0000/0001, written 0x0102/0001;
            written last_played = time(), unk_34 FFFFFFFF, 0x88..0xA7 = GFX (base bytes), 0xCF 5A, unk_bf rest 0
  skills29  RSKC 29; item list at skills + 31; written 30 skill bytes, name qitsor
  items     ear: +0x28 3, +0x48 42, +0x4A earname; cap: +0x4A Hoarder; gloves: realm 11223344/55667788;
            15 written records = the read ones, the realm third u32 written 0
  v94       RSTV 94/16, 16 SetStat lines; durabilities 7, 8, 20 (8-bit) written back; v94s12: RSTV 94/12, stat
            12 not set, header level 0 written; slots8: RSTV 96/8, every gf stat read
  act6      RACT 0x86 -> 0          param  stat 107 param 270 read and written
  uniqbad   unique ids read 71, -1; written 71, 0xFFF      name15  loaded; written name 15 chars + 0
  mercmf    MRX mercenary; merc item list at 970; RITEM 4 + 3 in file order; written merc list the same
  ```
- **Raw data:** `workspace/logs/h1a/` (logs, marks, pilot output, screenshots, kept saves), manifest
  `h1a-manifest.sha256` (`dd900aae…`; `sha256sum -c` from `workspace/logs/h1a`). The
  development session `dev-h1a-s2-27201-main` (two cases, before the post-error click was moved to empty background)
  is kept as a development log, listed in `h1a-manifest-dev.sha256`; no claim rests on it.
- **Deviations and limits:** the swap is the runner's, not a game state: the listed file decides the client's name,
  status and difficulty, the swapped file is what the server reads. No legacy save (version < 92 with its own layout)
  was built, so the legacy reader was reached only with a version-96 body labelled 91 (it returned 14). No write above
  8 KiB, no version-92 item list (the 1.09 widths), no ladder or host game, no classic progression bounds.
- **Conclusion:** see [save/0001 § Plan 0038 batch H1a](0001-d2s-io.md#plan-0038-batch-h1a-run2026-10-27-sweep-d2s-load),
  [hirelings/0001 § Plan 0038 batch H1a](../hirelings/0001-hirelings.md#plan-0038-batch-h1a-run2026-10-27-sweep-d2s-load)
  and [player/0001 § Plan 0038 batch H1a](../player/0001-creation.md#plan-0038-batch-h1a-run2026-10-27-sweep-d2s-load).

## run:2026-10-27-sweep-d2s-legacy

- **Question:** (plan 0038 Phase 2, batch H1c, [inventory § 5](../../plans/0038-inventory/README.md#harness-batches))
  the six H1a shortfall rows that waited for a save in the legacy layout: [hirelings](../../plans/0038-inventory/hirelings-README.md)
  3, 30, 33, [player-creation](../../plans/0038-inventory/player-creation.md) 1,
  [items-uniques-sets](../../plans/0038-inventory/items-uniques-sets.md) 21 and
  [save-d2s](../../plans/0038-inventory/save-d2s.md) 126, plus the piece the `lane/h6b` review routed here from
  [items-sockets-runewords](../../plans/0038-inventory/items-sockets-runewords.md) 1 (the version-71 list reader's
  inserts, 0x005311B5 and 0x005313F0). What the legacy reader (`sub_00534020_ReadSaveLegacy`) and the version-92
  reader do with a file in the version 71, 87 and 92 layouts of `lane/a72`'s builder, observed under the rules of the
  `lane/a72` review ruling 3: the reader path and its return logged, and the game's version-96 write-back compared
  field by field with the build.
- **Setup:** the ADR-0003 harness on **slot 1** (display `:8`, prefix `workspace/wineprefix-1`), agent-driven, no owner
  play, stock data, the shared game directory unchanged. The slot's empty saves directory was set aside as tag `h1c`
  and restored before each launch and after the last (empty, all sha256 match).
  - **Builds** (`python3 -I tools/d2s.py build workspace/merged/data/global/excel tools/d2s_recipes/<case>.json
    workspace/samples/d2s-owner/smpsor-l50.d2s workspace/runtime/h1c/<case>/<Name>.d2s`; the base is the owner sample
    `smpsor-l50.d2s`; sha256 of each build in `workspace/logs/h1c/check/builds.sha256`): the five `lane/a72` recipes
    `leg87merc` (`Leg87Merc`, 825 bytes), `leg87new` (718), `leg71merc` (696), `leg71uniq` (835), `leg92props` (964), and
    two added here: `leg71sock` (777: two caps with one socket and one `gsv` child each, version 71, for the insert
    piece) and `leg71act2` (696: `leg71merc` with difficulty byte `0x81`, the header's act II). Tool-built, ADR-0013 §
    Neutral: they back the reader's handling of the built bytes, never how a game makes them.
  - **Logger** `tools/gdb/d2s-h1c.gdb` (`29f38445…`): `pilot.py`, `d2s-io.py`, `d2s-h1b.py` and `d2s-h1a.py` (all
    unchanged) and the new `tools/gdb/d2s-h1c.py` (`2a731e36…`; lines `NCL`, `MOS`, `MXO`, `MCR`, `SEC`, `V71`, `OPL`,
    `OIC`, `INS`, `UB0`, `UBR`, each with a return line `…R` at the caller's return address; addresses in its header).
    The kept logs are from the revision that disables a return breakpoint after it fires; the first revision
    (`dev1/`) logged one return line more per earlier call of the same function and is kept as a development log, no
    claim rests on it.
  - **Runner** `tools/h1c_sessions.py` (`83b37e18…`, `tools/h1a_sessions.py`'s with one build per session): the file
    copied over the character's `.d2s`, *Single Player* (the character screen lists it), the same file again (no swap),
    OK, Normal, wait for `PLD`, *Save and Exit* and the written file kept under `workspace/logs/h1c/<stem>-saves/<case>/`.
    One game process per session; seeds 27301–27307.
  - **Checker** `tools/sweep_h1c.py` (`2d101ea1…`): for each case the log's reader path (`LEG`, `SEC`, `LEGR`, `RSV`,
    `PLD`; for 92 `RHRET`, `RSTV`, `RSKC`) and the kept write-back compared with the build (`tools/d2s.py`'s
    `parse_legacy` or `parse`): header, stats, skills, hotkeys, mouse skills, every item, the mercenary and its items.
- **Procedure** (`python3 -I tools/h1c_sessions.py run --slot 1 --tag h1c --cases workspace/runtime/h1c --run h1c NAME`):
  one session per case: `leg87new` (27302), `leg87merc` (27301), `leg71merc` (27303), `leg71uniq` (27304), `leg92props`
  (27305), `leg71sock` (27306), `leg71act2` (27307). All seven loaded (`PLD` 0) and were saved and exited.
- **Check:** `python3 -I tools/sweep_h1c.py check workspace/merged/data/global/excel workspace/runtime/h1c
  workspace/logs/h1c` → `workspace/logs/h1c/check/sweep-h1c-check.txt` (`3f1894dd…`): **272 comparisons over 7 cases
  (45, 21, 36, 56, 40, 38, 36), 0 failing.** (The unrelated `tools/test_d2s.py` run: 60 tests, the one failure is
  `test_every_recipe_has_a_base` for 49 `anim-*` recipes that are not in `RECIPE_BASES`; the seven `leg*` recipes are.)
- **Observed:**
  ```
  case        file      reader path                                         write-back vs the build
  leg87new    87, 718   LEG 87; header section only (status bit 0); NCL 0   NOT the build: level 1, stats 10/35/25/10, no skills,
                                                                              4 hp1 + tsc + isc + sst; status 0x20; hotkeys none
  leg87merc   87, 825   LEG 87; 8 sections + the mercenary's list + tail 0   stats, skills, hotkeys 0..9, mouse skills L R A B,
                        MOS 87 (record 0x12, then list), MXO (1, 100000)     2 items; merc seed 12345, Id 1, name 3,
                        -> 546210, MCR (3414, 12345, 1, 271, 0), MOSR len 46  exp 546210 = MXOR; merc list: cap, head
  leg71merc   71, 696   LEG 71; V71 1 record (OIC, OPL); MOS 71 ("JM",       stats, skills, hotkeys 0..7, mouse L R only;
                        12345, 3), no MXO, MCR (3, 12345, 0xFFFF, 0, 0),     cap; merc seed 12345, Id 1, name 0, exp 2649150
                        MOSR len 8
  leg71act2   71, 696   as leg71merc, difficulty byte 0x81                    as leg71merc: merc Id 1; written byte 0xA8 = 0x81
  leg71uniq   71, 835   V71 6 records; UB0/UBR twice (rec+0x2C = 1,           uniques rows 0 and 1, set rows 0 and 1, the Ward's
                        rec+0x40 = 0, 1)                                      unit seed 1234567; the jewel written magic (4)
  leg71sock   71, 777   V71 4 records; INS twice from 0x005311BA (child 2,     children at location 6 after each parent
                        parent 1; child 4, parent 3), INSR 1 each; none        (cap, gsv, cap, gsv)
                        from 0x005313F5
  leg92props  92, 964   no LEG; RHRET 0; RSTV 92/16; RSKC 92/30; 3 items       cap's stats 0, 7, 39, 83(1), 107(54), 126(1), 188(8),
                                                                                195(3075) = the build's; the Ward; the potion
  ```
- **Raw data:** `workspace/logs/h1c/` (logs, marks, pilot output, screenshots, kept saves), manifest
  `manifest.sha256` (51 lines, `38aaf22c…`; `sha256sum -c` from `workspace/logs/h1c`). The development logs of the
  first logger revision are in `dev1/` with `dev1/manifest-dev.sha256` (43 lines, `06ec3120…`, from `dev1/`).
- **Deviations and limits:** the builder writes no corpse, so the corpse list's reader (0x005339A0, the second
  version-71 insert site 0x005313F0, `sub_00531390_OldItemPlaceCorpse`) read an empty list and was not exercised. Only
  versions 71, 87 and 92 were loaded (88, 89, 90, 91 are not built). One act in the mercenary cases' game (the
  character loads in the act the unit starts in). The item version the unique builder tested is the return of
  0x0062A670, which was 3 for both uniques.
- **Conclusion:** see [save/0001 § Plan 0038 batch H1c](0001-d2s-io.md#plan-0038-batch-h1c-run2026-10-27-sweep-d2s-legacy),
  [hirelings/0001 § Plan 0038 batch H1c](../hirelings/0001-hirelings.md#plan-0038-batch-h1c-run2026-10-27-sweep-d2s-legacy),
  [player/0001 § Plan 0038 batch H1c](../player/0001-creation.md#plan-0038-batch-h1c-run2026-10-27-sweep-d2s-legacy),
  [items/0004 § Plan 0038 batch H1c](../items/0004-uniques-sets.md#plan-0038-batch-h1c-run2026-10-27-sweep-d2s-legacy)
  and [items/0007 § Plan 0038 batch H1c](../items/0007-sockets-runewords.md#plan-0038-batch-h1c-run2026-10-27-sweep-d2s-legacy).
