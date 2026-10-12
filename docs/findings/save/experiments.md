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
    clear (`0x00822010` in `rt` → `0x00820010` in `save1`). The staff dropped and picked up in run 7 was saved with
    `0x00800010`: bit 13 **clear** on an item created in that session.
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
    `2728687498`, quality 1, ilvl 1, flags `0x80010`. After the pickup the final-pass `SBIT` of the same unit and id:
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
  become `[C]`. The finding's bit-13 reading ("only items created in the session carry it") is refuted for drops.
  [data/0003](../data/0003-string-tables.md): the crc check, its CRC model and the fatal halt become `[C]`.
