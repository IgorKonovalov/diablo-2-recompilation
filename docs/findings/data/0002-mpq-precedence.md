# 0002 — MPQ open order and precedence, loose files and `-direct`, the `data\local\use` byte

> **Subsystem:** data/excel (file layer under the excel loader)
> **Question:** In which order does 1.14d open its MPQs, which archive wins when several hold the same file, when
> does it read loose files from disk, and what does `data\local\use` select?
> **Date:** 2026-10-11   **Plan:** 0002 (Phase 2)   **Status:** answered (inferred, runtime check open)

## Answer (summary)

- [I] **Open order** (`MPQ_OpenCoreArchives`): `d2data` (priority 1000), `d2sfx` (1000), `d2speech` (1000),
  `d2delta` (1000), `d2kfixup` (1000), `patch_d2` (**5000**), `d2exp` (**3000**). Then `MPQ_OpenGameArchives` opens
  `d2char` (1000), `d2music` (1000) and, for an expansion game, `d2Xmusic`, `d2Xtalk`, `d2Xvideo` (3000 each).
  `d2video` (1000) is opened on demand. (fn:MPQ_OpenCoreArchives@0x004FAB90, fn:MPQ_OpenGameArchives@0x004FAEC0,
  fn:MPQ_OpenVideoArchives@0x004FAD10)
- [I] **Priority:** the archive list is kept sorted by descending priority. A new archive goes in front of the
  first one whose priority is ≤ its own, so **among equal priorities the later-opened archive is searched
  first**. A file lookup walks the list from the front and takes the first archive whose hash table has the name.
  (fn:STORM_LinkArchive@0x0041B6B0, fn:STORM_FindFile@0x00417F10)
- [I] **Effective precedence for `data\global\…`:** `patch_d2` > `d2exp` > `d2kfixup` > `d2delta` > `d2data`
  (`d2speech`/`d2sfx`/`d2char`/`d2music`/`d2X*` sit in the same bands but hold no excel data). This is the
  `workspace/merged/` order (d2data → d2exp → patch_d2, later wins), so the merged tree matches the game.
  (fn:MPQ_OpenCoreArchives@0x004FAB90, fn:STORM_LinkArchive@0x0041B6B0)
- [I] **`d2kfixup.mpq` and `d2delta.mpq` are opened whenever present** (failure is tolerated; neither is required).
  At priority 1000 and opened after `d2data`, each overrides `d2data` but loses to `d2exp` and `patch_d2`. They don't
  ship in our set, so they change nothing here. (fn:MPQ_OpenCoreArchives@0x004FAB90)
- [I] **`d2exp.mpq` is opened unconditionally** (if the file exists), also for a classic game, and its excel tables
  outrank `d2data`'s. So classic and expansion games read the same excel data. (fn:MPQ_OpenCoreArchives@0x004FAB90,
  fn:STORM_LinkArchive@0x0041B6B0)
- [I] **Loose files are read only under `-direct`.** `-direct` (`FILEIO`/`DIRECT`, `config+0x204`) sets Storm's
  direct-access flags (`0x00779058`) and the game's `g_bDirect` (`0x0074C82C`). With the flag set, every file open
  first tries the path on disk (relative path as given) and only then the archives, so **a loose file beats every
  MPQ**. Without it, the disk is never consulted while at least one archive is open. `-direct` also lets startup
  continue when `d2data`/`d2sfx`/`d2speech` are missing. (fn:sub_00406870_InitFileIO@0x00406870,
  fn:STORM_GetDirectFlags@0x00418B50, fn:STORM_DiskPath@0x00415B00)
- [I] **`data\local\use`:** read once through the same file API (MPQ, or disk under `-direct`). Its first byte is a
  language id: values > 13 become 0, and it is matched against the id column of the 13-entry language table at
  `0x007303DC` (0 `ENG`, 1 `ESP`, 2 `DEU`, 3 `FRA`, 4 `POR`, 5 `ITA`, 6 `JPN`, 7 `KOR`, 8 `SIN`, 9 `CHI`,
  10 `POL`, 11 `RUS`, 12 `ENG`/`HAN`). The resulting code fills the `%s` in `data\local\lng\%s\string.tbl`,
  `…\expansionstring.tbl`, `…\patchstring.tbl` and `data\local\font\%s\default.map`, and picks a font charset
  (`JPN`, `KOR`, `POL` → `LATIN2`, `RUS` → `CYR`…). `0x0B` = `RUS`, `0x00` = `ENG`. It touches localisation only,
  not `data\global\` or any excel table. (fn:LNG_GetLanguageIndex@0x00525150, fn:LNG_GetLanguageCode@0x00525260,
  0x005259C0)

## Leads used

- None. The "patch_d2 > d2exp > d2data" order in `docs/formats/mpq.md` was `[L]` and is now anchored.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00405C30` | `sub_00405C30_InitGame` | file-I/O init, then `MPQ_OpenCoreArchives`, `MPQ_OpenGameArchives`, `LNG_GetLanguageIndex` | I |
| `0x00406870` | `sub_00406870_InitFileIO` | `ECX` = `cfg[0x204]` (`-direct`): `STORM_SetDirectFlags(ECX)`, `g_bDirect = ECX` | I |
| `0x00406D20` | `FILEIO_IsDirect` | returns `g_bDirect` | I |
| `0x004FAB90` | `MPQ_OpenCoreArchives` | opens the 7 core archives (order above) | I |
| `0x004FAEC0` | `MPQ_OpenGameArchives` | `d2char`, `d2music`; expansion: `d2Xmusic`, `d2Xtalk`, `d2Xvideo` | I |
| `0x004FAD10` | `MPQ_OpenVideoArchives` | `d2video` or `d2Xvideo` on demand | I |
| `0x00517332` | `MPQ_OpenArchive` | `__fastcall(name, flags; retryCb, priority)`: retries via callback with `Sleep(100)` | I |
| `0x00517299` | `sub_00517299_MpqOpenFromPaths` | tries name as given, then `<exe dir>\name`, then `0x00517128` | I |
| `0x0041BA60` | `STORM_OpenArchive` | Storm archive open: record 0x25C bytes, priority at `+0x118` | I |
| `0x0041B6B0` | `STORM_LinkArchive` | reads the MPQ header (`0x1A51504D`) and tables, inserts into the sorted list | I |
| `0x00419980` | `STORM_OpenFile` | `STORM_OpenFileEx(0, name, STORM_GetDirectFlags(), &h)` | I |
| `0x004192F0` | `STORM_OpenFileEx` | `STORM_FindFile`; 2 → `CreateFileA` on disk, 1 → archive file handle | I |
| `0x00417F10` | `STORM_FindFile` | walks the archive list; disk check first when flags & 3 | I |
| `0x00415B00` | `STORM_DiskPath` | builds and tests the on-disk path for flag bits 1/2 | I |
| `0x00418B50` | `STORM_GetDirectFlags` | bit 0 = `g_StormDirectFlags & 1` (or no archive open), bit 1 = `& 2` | I |
| `0x00415F70` | `STORM_SetDirectFlags` | `g_StormDirectFlags = arg` | I |
| `0x004155D0` | `STORM_HashLookup` | hash-table probe with (locale, platform) and neutral fallback | I |
| `0x00517079` | `FILE_LoadWhole` | game file API: open, size, alloc, read, close; fatal on a short read | I |
| `0x00525150` | `LNG_GetLanguageIndex` | first byte of `data\local\use`, cached, > 13 → 0 | I |
| `0x00525260` | `LNG_GetLanguageCode` | language table lookup, returns one of 4 fields | I |

## Walkthrough

### 1. Startup

```c
// fn:sub_00405C30_InitGame@0x00405C30 (trimmed)
sub_00406870_InitFileIO(/*ECX*/ cfg->direct /*+0x204*/, /*EDX*/ 0);
...
if (mode != 2) {
    if (!MPQ_OpenCoreArchives() || !MPQ_OpenGameArchives(0, cfg)) { MPQ_CloseAll(); return 0; }
    *cfg = sub_00408F20();            // d2exp.mpq present on disk → expansion installed
}
LNG_GetLanguageIndex();
```

- [I] `-direct` is the command-line entry `FILEIO`/`DIRECT`/`direct` at `0x00706124` (type 0 = flag,
  `cfgOffset 0x204`; table layout in [0001](0001-excel-loader.md) §2). `sub_00406870_InitFileIO` is called with
  `movzx ecx, byte [esi+0x204]` (`0x00405C55`).

### 2. Archive open and the sorted list

```c
// fn:MPQ_OpenCoreArchives@0x004FAB90
h_d2data   = MPQ_OpenArchive("d2data.mpq",   0, NULL, 1000);
h_d2sfx    = MPQ_OpenArchive("d2sfx.mpq",    0, NULL, 1000);
h_d2speech = MPQ_OpenArchive("d2speech.mpq", 0, NULL, 1000);
h_d2delta  = MPQ_OpenArchive("d2delta.mpq",  0, NULL, 1000);
h_d2kfixup = MPQ_OpenArchive("d2kfixup.mpq", 0, NULL, 1000);
h_patch    = MPQ_OpenArchive("patch_d2.mpq", 0, NULL, 5000);
h_d2exp    = MPQ_OpenArchive("d2exp.mpq",    0, NULL, 3000);
if (FILEIO_IsDirect()) return 1;
if (h_d2data && h_d2sfx && h_d2speech) { if (!sub_00408F20()) return 1; if (h_d2exp) return 1; }
return 0;
```

- [I] Handle globals: `d2data 0x007D561C`, `d2sfx 0x007D5608`, `d2speech 0x007D5624`, `d2delta 0x007D560C`,
  `d2kfixup 0x007D5620`, `patch_d2 0x007D5630`, `d2exp 0x007D5634`, `d2char 0x007D5610`, `d2music 0x007D5628`,
  `d2Xmusic 0x007D5604`, `d2Xtalk 0x007D5618`, `d2Xvideo 0x007D562C`, `d2video 0x007D5614`.
- [I] `MPQ_OpenArchive` → `sub_00517299_MpqOpenFromPaths` passes Storm open flags 2 (3 when `EDX` ≠ 0; always 0 at
  these call sites) and tries the name relative to the working directory, then next to `Game.exe`, then a third
  location (`0x00517128`, not followed).
- [I] `STORM_OpenArchive` stores the priority at record `+0x118` and the flag bit 2 at `+0x114` (0 for every game
  archive). `STORM_LinkArchive` then inserts (fn:STORM_OpenArchive@0x0041BA60, fn:STORM_LinkArchive@0x0041B6B0):
  ```asm
  0x0041B946  mov eax,[g_StormArchiveList]          ; head (0x0070835C)
  0x0041B955  cmp [eax+0x118], ecx                  ; node.prio vs new.prio
  0x0041B95B  jle insert_before_eax                 ; stop at first node with prio <= new
  0x0041B95D  mov eax,[eax+4] ...                   ; else next
  ```
  so the list is descending by priority, and a tie goes in front of the older archive.
- Resulting search order with every archive present (expansion): `patch_d2`, `d2Xvideo`, `d2Xtalk`, `d2Xmusic`,
  `d2exp`, `d2music`, `d2char`, `d2kfixup`, `d2delta`, `d2speech`, `d2sfx`, `d2data` (then `d2video` goes to the
  front of the 1000 band when it is opened).

### 3. File lookup and loose files

```c
// fn:STORM_FindFile@0x00417F10 (trimmed). flags = STORM_GetDirectFlags()
for (a = g_StormArchiveList; ; a = a->next) {
    if (a == NULL || a->disabled /*+0x258*/ < 1) {
        if ((flags & 3) && (a == NULL || a->+0x114 == 0) && STORM_DiskPath(flags))
            return 2;                                   // loose file on disk wins
        if (a == NULL) return not_found;
        i = STORM_HashLookup(a, locale, platform);
        if (i != -1) return (block[i].flags & 0x80000000) ? 1 : error;  // first archive that has it
    }
}
```

- [I] The disk test sits inside the loop, before the first archive's hash lookup, so with the flag it runs before
  any archive is searched. (fn:STORM_FindFile@0x00417F10)
- [I] `STORM_GetDirectFlags`: bit 0 if `g_StormDirectFlags & 1`, **or** if no archive is open and the flags are 0;
  bit 1 if `g_StormDirectFlags & 2`. The game writes `g_StormDirectFlags` only from `sub_00406870_InitFileIO`, with
  the `-direct` byte (0 or 1). So in a stock run (archives open, no `-direct`) the disk is never read.
  (fn:STORM_GetDirectFlags@0x00418B50, fn:sub_00406870_InitFileIO@0x00406870)
- [I] The game's whole-file loader `FILE_LoadWhole` (`0x00517079`, used by the excel loader and for `data\local\use`)
  goes `0x004068E0` → `STORM_OpenFile` with archive 0 (global search), so the rule above covers every excel table.

### 4. The language byte

```c
// fn:LNG_GetLanguageIndex@0x00525150
if (!g_lngLoaded) { g_lngLoaded = 1;
    p = FILE_LoadWhole("data\\local\\use");
    if (p) { g_lng = p[0]; free(p); } }
if (g_lng > 13) g_lng = 0;
return g_lng;
```

- [I] `LNG_GetLanguageCode(out, field)` looks `g_lng` up in the id column (`+0x10`) of 13 entries of 0x18 bytes
  at `0x007303DC` (falls back to entry 0), and copies field 0 (`ENG`…), 1, 2 (`USA`, `ESP`…) or 3 (a 4-character
  tag, `enUS` for entry 0). `0x005259C0` uses the code for the string-table and font paths and the charset.
- [I] The 1.14d install's launcher scripts copy `Use_rus` (0x0B) over `data\local\Use` and pass `-direct`; in that
  launch path the loose byte is read and selects `RUS`. Without `-direct`, the byte comes from the MPQ copy.
  (fn:LNG_GetLanguageIndex@0x00525150, fn:STORM_FindFile@0x00417F10)

## Plan 0038 batch S1b (2026-10-16)

Static batch S1b of [plan 0038](../../plans/0038-inferred-claims-sweep.md), the archive rows of
[inventory data-excel](../../plans/0038-inventory/data-excel.md) and [data-README](../../plans/0038-inventory/data-README.md).
No session was played; method and log manifest as in [data/0001 § Plan 0038 batch S1b](0001-excel-loader.md#plan-0038-batch-s1b-2026-10-16).
The checks are `python3 -I tools/sweep_s1b.py arch` and `compile`. Where a statement above is tagged inferred and this
section raises it, the tag and the second source given here are the current ones.

**What decides the order.** Three kinds of file are held by more than one archive with different bytes, and a kept
log reads each kind with 0 mismatches on the merged tree (`workspace/merged/`, d2data → d2exp → patch_d2, later wins):
- excel `.bin`: d2data holds none. d2exp and patch_d2 both hold 45; for 41 of them d2exp's copy has another record size
  than the one the loaders' consumers use (data/0001 § 4, all 86 loaded tables equal to the merged copy), and 4 have
  the same size with other bytes. Only patch_d2's copies fit the strides every checker and the game use.
- DS1 maps: `tools/drlg.py gen` over the 33 logs of run:2026-10-13-drlg-preset and run:2026-10-15-acts-3-5 (3 394
  preset rooms) gives 0 mismatches on the merged tree. With d2data's copies of the 89 DS1 files d2data and d2exp both
  hold (patch_d2 holding none of them) it gives 1 751 mismatches; with d2exp's copies of the 10 DS1 files patch_d2
  overrides, 564.
- string tables: with d2exp's `eng\patchstring.tbl` in place of patch_d2's, 3 964 of the 4 264 lines of
  run:2026-10-15-strings no longer reproduce (0 with the merged tables).

- **data/README row 1** (spec L50, `patch_d2` > `d2exp` > `d2data`; loose files only under `-direct`) **raised in part.**
  [C] the order of the three archives, by the counterfactuals above. [C] under `-direct` a loose file beats the
  archives: the loose `data/global/excel/cubemain.txt` was compiled (run:2026-10-15-cube-saves) and loose `.bin`
  files of the forced runs were loaded (data/0001 row 10). **Remainder `[I]`:** "only under `-direct`": no log has a
  loose file without `-direct` (the stock game directory has no `data` tree). As the route says, H3b (with spec A3 and
  data/excel row 24). (fn:MPQ_OpenCoreArchives@0x004FAB90, fn:STORM_FindFile@0x00417F10, fn:sub_00406870_InitFileIO@0x00406870)
- **data/excel row 11** (spec L69, priorities 5000 / 3000 / 3000 / 1000) **raised in part.** [C] the order they give
  (`patch_d2` above `d2exp` above `d2data`), as above. **Remainder d-none:** the numbers themselves, beyond that order.
  (fn:MPQ_OpenCoreArchives@0x004FAB90)
- **data/excel row 19** (spec L130, A2 inserts by descending priority, the later-opened archive first on a tie)
  **raised in part.** [C] descending priority, as above. **Remainder d-none:** the tie rule. No two archives of one
  priority band hold a file with different bytes: of the 6 files shared inside a band (d2music and d2video), 0
  differ. (fn:STORM_LinkArchive@0x0041B6B0)
- **data/excel row 21** (spec L148, `d2kfixup`/`d2delta` optional; `d2exp` opened for a classic game too) **raised.**
  [C] The game directory of every stock run holds neither `d2kfixup.mpq` nor `d2delta.mpq` (`game_dir_has_*=0`) and
  every run started. The classic session of run:2026-10-15-strings resolved three indices ≥ 20000 through
  `expansionstring.tbl`, which only `d2exp.mpq` holds, and d2data holds no excel `.bin` at all, so every table a
  classic game loads comes from d2exp or patch_d2. (fn:MPQ_OpenCoreArchives@0x004FAB90)
- **data/excel row 23** (spec L153, `patch_d2` > `d2exp` > `d2kfixup` > `d2delta` > `d2data`) **raised in part.**
  [C] `patch_d2` > `d2exp` > `d2data`, as above. **Remainder d-edit:** the places of `d2kfixup` and `d2delta`; our
  install ships neither, so only an added archive would show them. (fn:STORM_LinkArchive@0x0041B6B0)
- **data/excel row 28** (spec L195, the `.bin` side of the five mixed-archive tables is authoritative)
  **reclassified d-none.** The pinned game's own compile of the `.txt` the archives rank first gives, for `automagic`,
  `rareprefix`, `raresuffix`, `inventory` and `plrmode`, `.bin` files byte-identical to the shipped ones
  (`sweep_s1b.py compile`, 88 of 90 identical; run:2026-10-15-cube-saves). Whichever side a stock run loads, the records
  are the same, so the claim has no observable. The d2exp copies of `automagic`, `rareprefix` and `raresuffix` `.bin` are
  a different matter: their record sizes (132, 60, 60) do not fit, which is the order above, not this claim.

## Data touched

- Archive names `0x006DC728`…`0x006DC7B4`, `0x006CD3A0`, `0x006D4C78`.
- `data\local\use` (`0x006DF664`), `data\local\lng\%s\*.tbl` (`0x006E028C`, `0x006E02B4`, `0x006E02F8`),
  `data\local\font\%s\default.map` (`0x006E02D8`).
- Config: `+0x204` (`-direct`), `+0x215` (`-txt`).

## Dead ends

- Looked for an MPQ list in a data table; there is none. The order is straight-line code in three functions.
- `0x0051ED00` and `0x0051FAB0` also reference `d2data.mpq`/`patch_d2.mpq`/`data\local\use`; they are the
  Battle.net patch downloader (`BnDownload.cpp`: `Prepatch.lst`, `bnupdate.exe`, ExtraWork DLL), not the open
  sequence.

## Open questions

- Runtime confirmation: a wine run with a loose `DATA\GLOBAL\EXCEL\<table>.bin` that differs from the MPQ copy,
  launched with and without `-direct`, would confirm the loose-file rule. Same for a dummy `d2kfixup.mpq`
  carrying one excel file.
- Storm's lookup also matches a (locale, platform) pair with neutral fallback (`STORM_HashLookup`). Which locale the
  game sets is not followed; excel files are stored neutral in our archives, so it does not affect them.
- `sub_00408F20` (expansion detection by `d2exp.mpq` file presence) and the archive record fields `+0x150`/`+0x258`
  are not fully read.
