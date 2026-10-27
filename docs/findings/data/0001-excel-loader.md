# 0001 — Excel loader: `.bin` vs `.txt`, registered tables, code→index lookup, live TC table

> **Subsystem:** data/excel
> **Question:** Which form of each excel table does 1.14d load, through which code, into which globals, and how
> are codes and names turned into record indices?
> **Date:** 2026-10-11   **Plan:** 0002 (Phase 2)   **Status:** answered

## Answer (summary)

- [C] **The game reads the `.bin`.** Every excel table goes through `DATATBLS_LoadTable`, which loads
  `DATA\GLOBAL\EXCEL\<name>.bin` and returns `data + 4` as the record array and the u32 at `+0` as the count. The
  branch that would parse `<name>.txt` at load time is gated by `g_DataTblsLoadBin` (`0x00744308`), which is
  initialised to 1 and never written (30 references, all `cmp`). Corroborated by data behaviour: the record size each
  call site passes matches the `.bin` record size for all 86 loaded tables (see *Record sizes*).
  (fn:DATATBLS_LoadTable@0x006122F0, 0x00744308)
- [I] **The one switch is `-txt`** (`TXT`/`TXT`/`txt` in the command-line table, flag at `config+0x215`). Its apply
  handler sets `g_DataTblsCompileTxt` (`0x0096C8B4`). In that mode each table's `.txt` is parsed with the table's
  field descriptor and written to disk as `DATA\GLOBAL\EXCEL\<name>.bin` (`fopen "wb"`, relative path), and **then
  the `.bin` is loaded through the normal file API anyway**. Without `-direct` that file API never looks at loose
  files ([0002](0002-mpq-precedence.md)), so `-txt` alone still loads the MPQ `.bin`. Only `-direct -txt` makes the
  game run on `.txt` content. (fn:sub_0044D9C0_ApplyTxtOption@0x0044D9C0, fn:DATATBLS_SetCompileTxt@0x006125A0,
  0x007063A8)
- [I] **Mixed-archive tables: the `.bin` is authoritative in a stock run.** `automagic`, `RarePrefix`, `RareSuffix`:
  the patch_d2 `.bin` (the patch's update is live; the stale d2exp `.txt` is ignored). `inventory`, `PlrMode`: the
  d2exp `.bin` (the patch_d2 `.txt` edit is **not** live unless the game runs with `-direct -txt`). Follows from the two
  claims above plus the archive order in [0002](0002-mpq-precedence.md). (fn:DATATBLS_LoadTable@0x006122F0, 0x00744308,
  fn:DATATBLS_SetCompileTxt@0x006125A0)
- [C] **The live TC table is `treasureclassex`.** `TreasureClass.txt` is never loaded: the string `treasureclass`
  (`0x006EA76C`) is only the name of the `itemtypes` column `TreasureClass` in the itemtypes descriptor.
  `TC_LoadTreasureClassEx` copies the `treasureclassex.bin` records into the runtime TC array `g_pTreasureClasses`
  (`0x0096C5EC`, 0x2C-byte entries), which the getters `TC_GetByIndex`/`TC_GetByName` read. Corroborated by data
  behaviour: the TC index space (0 = empty name, 1–160 = auto-generated item TCs, then the 853 TCEx rows in file order)
  reproduces all 4362 non-blank `TreasureClass*` cells of `monstats.bin` exactly. (fn:TC_LoadAll@0x0065A390,
  fn:TC_LoadTreasureClassEx@0x006547D0, fn:TC_GetByIndex@0x00654E00, tbl:monstats.txt:TreasureClass1)
- [C] **Record sizes:** 86/88 `.bin` tables are registered, and for every one the call site's record size equals the
  `.bin` record size in `docs/tables/README.md`. The other two, `cubemod` and `cubetype`, are never loaded: their
  names do not occur in `Game.exe`. (fn:DATATBLS_LoadAll@0x00619300, fn:DATATBLS_LoadTable@0x006122F0; § 4)
- [I] **Code→index:** `EXCEL_FindCode` (`0x006BD130`) binary-searches a sorted `{u32 code, s32 index}` array
  (unsigned compare) and returns the index or −1. Item codes go through `ITEMS_GetByCode` (`0x00633640`) on
  `g_ItemCodeLink`; the index is the position in the combined items array (weapons, then armor, then misc).
  **Collision:** `EXCEL_AddCode` never stores a duplicate key. When the code is already present it increments the
  u32 code by 1 and retries, so the **first** record keeps the code and later duplicates become unreachable under
  their written code. The shipped weapons/armor/misc have no duplicate codes (659 records, data check).
- [I] **Name→index** (TC names, monster `Id`s): `EXCEL_FindName` (`0x006BD3C0`) lowercases the key (first 31
  characters), then walks a binary search tree ordered by byte `strcmp`. Returns the node index or −1.
  `EXCEL_AddName` frees a duplicate node but still increments the count, so **first match wins** and the duplicate's
  index is left without a name. Item codes are **case-sensitive** (no folding); names are not.
- [C] **`leveldefs` `+0x30` is `Levels.txt:DrlgType`, `+0x34` is `Levels.txt:LevelType`.** `leveldefs` has its own
  field descriptor, and under `-txt` it is compiled from `levels.txt`. Data check: both columns match all 137
  records of `leveldefs.bin` (as do 13 other columns tried). (fn:DRLG_LoadLevelDefs@0x0061DE00)

## Leads used

- None. `[L]` statements in `docs/formats/excel-bin.md` (`leveldefs` = compiled half of Levels) and in the tooling
  notes (`-direct -txt` is the modding switch) are confirmed here from our binary.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x006122F0` | `DATATBLS_LoadTable` | `void* __stdcall (pool, name, fields, int *pCount, int recSize)`: (compile) + load one table | C |
| `0x00612280` | `DATATBLS_OpenExcelFile` | `__fastcall(pool, name, ext, &size, file, line)`: `DATA\GLOBAL\EXCEL\<name><ext>` into memory | I |
| `0x006121F0` | `DATATBLS_WriteBin` | writes `u32 count` + records to `DATA\GLOBAL\EXCEL\<name>.bin` (compile mode only) | I |
| `0x006125A0` | `DATATBLS_SetCompileTxt` | `g_DataTblsCompileTxt = (arg == 0)` | I |
| `0x006125C0` | `DATATBLS_FreeTable` | frees `ptr − 4` (bin) or `ptr` | I |
| `0x00613E90` | `DATATBLS_LoadCodeBin` | loads a header-less `*code.bin` whole (`itemscode`, `misscode`, `skillscode`, `skilldesccode`) | I |
| `0x00612750` | `DATATBLS_LoadCodeLists` | `compcode` always; 15 code-list tables only under `-txt` | C (H3b) |
| `0x00619300` | `DATATBLS_LoadAll` | the fixed call sequence of every table loader (the "registration list") | C (H3b) |
| `0x0044D9C0` | `sub_0044D9C0_ApplyTxtOption` | `DATATBLS_SetCompileTxt(cfg[0x215] == 0)` | C (H3b) |
| `0x0044D9F0` | `sub_0044D9F0_ApplyOptions` | calls the 52 option handlers at `g_OptionApplyTable` (`0x0070F488`) | I |
| `0x006BD040` | `EXCEL_LinkCreate` | 16-byte link `{count, capacity, codeArray, nameTreeRoot}` | I |
| `0x006BD0B0` | `EXCEL_LinkFree` | | I |
| `0x006BD130` | `EXCEL_FindCode` | code → index, binary search, −1 if absent | I |
| `0x006BD230` | `EXCEL_AddCode` | sorted insert; duplicate code → code+1, retry; returns index | I |
| `0x006BD3C0` | `EXCEL_FindName` | lowercased name → index via BST, −1 if absent | I |
| `0x006BD500` | `EXCEL_AddName` | BST insert, index = count++; duplicate node freed | I |
| `0x006BD5A0` | `EXCEL_AddNameIfAbsent` | as above, but only when `EXCEL_FindName` < 0 | I |
| `0x006BCE20` | `EXCEL_MapColumns` | `.txt` header → descriptor index per column (hash + `_strnicmp`), `0x7FFF` = unknown | I |
| `0x006BD780` | `EXCEL_ParseTxt` | `.txt` cells → records by field descriptor (compile path only) | I |
| `0x004113C0` | `STR_ToLowerN` | in-place map through the table at `0x006CEB98` (ASCII lowercase) | I |
| `0x00633640` | `ITEMS_GetByCode` | `EXCEL_FindCode(g_ItemCodeLink, code)` → `&g_pItems[i]` (0x1A8 stride), index out | I |
| `0x006315D0` | `ITEMS_LoadItemTables` | weapons/armor/misc → one combined array; fills `g_ItemCodeLink` | I |
| `0x00638D80` | `ITEMS_LoadItemTypes` | | I |
| `0x00637620` | `ITEMS_LoadItemRatio` | | I |
| `0x00651210` | `MONSTATS_Load` | | I |
| `0x0061C540` | `DRLG_LoadLevels` | | I |
| `0x0061DE00` | `DRLG_LoadLevelDefs` | | I |
| `0x0065A390` | `TC_LoadAll` | create `g_TCLink`, empty TC, auto TCs, TCEx | I |
| `0x006541C0` | `TC_BuildAutoTCs` | `"<itemtype code><3..96 step 3>"` TCs for item types with `TreasureClass` ≠ 0 | I |
| `0x006547D0` | `TC_LoadTreasureClassEx` | `treasureclassex.bin` → runtime TC entries | I |
| `0x00653F90` | `TC_Alloc` | `EXCEL_AddName(g_TCLink, name)`; grows `g_pTreasureClasses` by 16 entries of 0x2C | I |
| `0x00654440` | `TC_ParseItemCell` | resolves one `ItemN` cell (item code / TC / unique / set) + `mul=`, `cu=`… modifiers | I |
| `0x00650EB0` | `STR_ToItemCode` | first 4 chars, space-padded, to a u32 code | I |
| `0x00654DD0` | `TC_GetByName` | `EXCEL_FindName(g_TCLink)` → entry; no reference in the image, no hit (H3b) | I |
| `0x00654E00` | `TC_GetByIndex` | index → entry, with the `group`/`level` upgrade walk | I |

## Walkthrough

### 1. Load path of one table

```c
// fn:DATATBLS_LoadTable@0x006122F0 (trimmed, renamed). stdcall, ret 0x14.
void *DATATBLS_LoadTable(void *pool, const char *name, ExcelField *fields, int *pCount, int recSize) {
    if (g_DataTblsCompileTxt) {                       // 0x0096C8B4, set only by -txt
        txt = DATATBLS_OpenExcelFile(pool, stricmp(name,"leveldefs") ? name : "levels", ".txt", &size);
        if (!txt) fatal();
        n = rows(txt); recs = alloc(n*recSize); memset 0;
        EXCEL_ParseTxt(txt, fields, recs, n, recSize);
        DATATBLS_WriteBin("<name>.bin", recs, n*recSize, n);   // fopen "DATA\GLOBAL\EXCEL\<name>.bin","wb"
        free(recs);
    }
    if (g_DataTblsLoadBin) {                          // 0x00744308 == 1, never written
        p = DATATBLS_OpenExcelFile(pool, name, ".bin", &size);
        if (!p) fatal();
        n = p[0]; recs = p + 4;                       // recSize is NOT used on this path
    } else {                                          // dead: parse .txt in place, no write
        ...
    }
    if (pCount) *pCount = n;
    return recs;
}
```

- [I] `DATATBLS_OpenExcelFile` builds `DATA\GLOBAL\EXCEL\<name><ext>` with `wsprintf("%s\\%s%s")` and reads it
  whole through the game's file API (`0x00517079`), which searches the open MPQs and, only under `-direct`, the disk
  ([0002](0002-mpq-precedence.md)). (0x00612280)
- [C] `.bin` layout as the loader reads it: u32 count at `+0`, records from `+4`; the block is freed as `ptr − 4`
  (`DATATBLS_FreeTable`, and the unload loop at `0x00612EA0`). Agrees with `fmt:excel-bin#bin`.
- [I] The `.txt` parser is a straight descriptor walk (`EXCEL_ParseTxt`). Field descriptor = 20-byte entries
  `{char *column; u32 type; u32 len; u32 offset; void *link}`, terminated by the column name `"end"`. Types seen:
  1 string (`len` bytes), 2/8 s32, 3 s16, 4/6 u8, 5 u8 if the cell is non-empty, 9-like 4-char code (blank → four
  spaces), 0x0A/0x0C/0x0E code registered in a link (stored as code / byte / word), 0x10 string registered as a name,
  0x11/0x12 name lookup-or-add (word / dword index), 0x14 name → index through another table's link (e.g. monstats
  `TreasureClass*` → `g_TCLink`), 0x16 callback, 0x1A bit flag. Number cells are summed digit by digit with an
  optional leading `-`, no validation. This only matters for how the shipped `.bin` files were produced (and for
  `-direct -txt` runs); it is not executed in a stock run. Type semantics beyond these are `[I]` from one read of the
  switch and are left to the archivist's data diff. (0x006BD780)

### 2. The `-txt` switch

- [I] The command-line table at `0x00705040` has 0x5C-byte entries `{section[0x1B], key[0x1B], switch[0x1A], u32
  type @+0x50, u32 cfgOffset @+0x54}`. Entry `0x007063A8` is `TXT`/`TXT`/`txt`, type 0 (flag), `cfgOffset 0x215`.
  (The seed entry at `0x00705EFC` gives `0x21A`, matching [rng/0002](../rng/0002-seed-tree.md).)
- [I] `sub_0044D9F0_ApplyOptions` walks the 52 handler pointers at `0x0070F488` and calls each non-null one with the
  config (`0x0044DA00` loop). Entry `0x0070F550` is `0x0044D9C0`:
  ```asm
  0x0044D9C0  xor eax,eax ; cmp byte [ecx+0x215],al ; sete al ; push eax ; call DATATBLS_SetCompileTxt ; ret
  ```
  and `DATATBLS_SetCompileTxt(x)` stores `x == 0`, so `g_DataTblsCompileTxt = (cfg.txt != 0)`. The only caller of
  the apply loop is `0x0044B6B0` (config setup), which runs before `DATATBLS_LoadAll` (`0x0044B937`).
- Ghidra had no function at `0x0044D9C0` and showed no caller of `0x006125A0`; the call was found with a raw `E8`
  rel32 scan of `.text` (one hit, `0x0044D9CC`).

### 3. What is registered: `DATATBLS_LoadAll` (`0x00619300`)

There is no data-driven registration list. `DATATBLS_LoadAll` calls one loader per table (or group) in a fixed
order; each loader builds its descriptor on the stack and calls `DATATBLS_LoadTable` once per table. All 92 call sites
were listed with `re/ghidra_scripts/CallArgs.java` (name, descriptor, count pointer, record size, return
destination).

- [I] `DATATBLS_LoadCodeLists` (`0x00612750`) always loads `compcode`. The other 15 calls in it (`playerclass`,
  `bodylocs`, `storepage`, `elemtypes`, `hitclass`, `colors`, `hiredesc`, `monmode` (4 B), `plrmode` (4 B), `monai`,
  `monplace`, `skillcalc`, `misscalc`, `skills` (2 B), `events`) are skipped unless `-txt` (`0x006127DF je`). They
  exist to fill code links used while compiling `.txt`; a stock run never loads them. *(2026-10-27, plan 0038 H3b:
  true of `DATATBLS_LoadTable`; `hitclass.bin` is read whole at every start by the character-graphics loader, return
  0x0050448A, and a 2-byte `sounds` call is `-txt`-only too: § Plan 0038 batch H3b, run:2026-10-27-sweep-data-load.)* Same for the 2-byte
  `monstats`/`skilldesc` calls in `0x00613F80` (`0x00617745 je`).
- [I] So `monmode`, `plrmode`, `skills`, `skilldesc`, `monstats` each have two call sites. In a stock run only the
  full-record one executes. (0x006127DF, 0x00617745)
- [I] Four header-less `*code.bin` files are loaded raw by `DATATBLS_LoadCodeBin` (buffer, size, capacity triple),
  not through `DATATBLS_LoadTable`: `itemscode` (`0x00633478`, into `0x0096BCC8`), `skillscode`, `skilldesccode`
  (`0x00617946`/`0x00617961`), `misscode` (`0x006631F5`). Under `-txt` they are written out after the tables that
  feed them are parsed, so formula columns (`itemstatcost`, `skills`, `skilldesc`, `missiles`) are compiled to
  offsets into these buffers at `.txt`-compile time. The bytecode itself is `data/calc`, not followed.
- [I] Other excel-directory readers, outside `DATATBLS_LoadTable` (0x00481950, 0x00504430, 0x00669130, 0x00639420):
  - `sounds.txt` and `soundenviron.txt` are read as text by `0x00481950` (client sound). `sounds.bin` is also loaded
    through the table loader (`0x00659C16`).
  - `D2Comp.cpp` (`0x00504430`) is a second copy of the loader, used for `weapons`/`armor`/`misc`/`itemtypes` by the
    character-graphics code (`0x00506000`). Its own bin/txt switch `0x0072EF2C` is also initialised to 1 and never
    written, so it reads `.bin` too.
  - The `cubemain` loader (`0x00669130`) aborts with a fatal error if `DATA\GLOBAL\EXCEL\cubeserver.bin` or
    `cubeserver.txt` can be opened (`0x0066A110`, `0x0066A164`), then loads `cubemain` normally.
  - `runessrv` (`0x00639420`, called from the Runes loader): probed through the same API, not followed.
- [I] `.txt`-only tables (`Aiparms`, `MonName`, `TreasureClass`, `WeaponClass`) have no loader. Only
  `SoundEnviron` is read (above). (fn:DATATBLS_LoadAll@0x00619300, 0x00481950)

### 4. Record-size corroboration (all 88 `.bin` tables)

Method: every `DATATBLS_LoadTable` call site's `recSize` argument (CallArgs output) against the **Rec** column of
`docs/tables/README.md`, and against `(size − 4) / count` recomputed from the merged `.bin` files. All three agree
for every row, so only one size column is shown.

| table | rec | call site | | table | rec | call site |
|---|---:|---|---|---|---:|---|
| arena | 28 | `0x00664A98` | | monai | 2 | `0x00612C30`ᵗ |
| armor | 424 | `0x00633376` | | monequip | 28 | `0x0065A03B` |
| armtype | 52 | `0x0065B3AE` | | monitempercent | 4 | `0x00654FA8` |
| automagic | 144 | `0x00633D9B` | | monlvl | 120 | `0x00659956` |
| automap | 44 | `0x0061FE62` | | monmode | 52 | `0x0065B18C` (+4 B `0x00612B40`ᵗ) |
| belts | 264 | `0x00660C22` | | monplace | 2 | `0x00612CAA`ᵗ |
| bodylocs | 4 | `0x006128AC`ᵗ | | monpreset | 4 | `0x00659A72` |
| books | 32 | `0x00637475` | | monprop | 312 | `0x006594B3` |
| charstats | 196 | `0x00613D07` | | monseq | 6 | `0x00659D24` |
| chartemplate | 240 | `0x0066571A` | | monsounds | 148 | `0x00656F45` |
| colors | 4 | `0x00612A90`ᵗ | | monstats | 424 | `0x0065384C` (+2 B `0x006177ED`ᵗ) |
| compcode | 4 | `0x006127CF` | | monstats2 | 308 | `0x00658422` |
| composit | 52 | `0x0065B33E` | | montype | 12 | `0x00658615` |
| cubemain | 328 | `0x0066A184` | | monumod | 32 | `0x00655279` |
| **cubemod** | 4 | **not loaded** | | npc | 76 | `0x006568DC` |
| **cubetype** | 4 | **not loaded** | | objects | 448 | `0x00640DDE` |
| difficultylevels | 88 | `0x006180B9` | | objgroup | 52 | `0x006412E0` |
| elemtypes | 4 | `0x0061299E`ᵗ | | objmode | 52 | `0x0065B22E` |
| events | 2 | `0x00612E8E`ᵗ | | objtype | 52 | `0x0065B216` |
| experience | 32 | `0x00613E41` | | overlay | 132 | `0x00664514` |
| gamble | 12 | `0x00638B25` | | pettype | 224 | `0x0061909A` |
| gems | 192 | `0x006371AB` | | playerclass | 4 | `0x00612833`ᵗ |
| hiredesc | 4 | `0x00612AE8`ᵗ | | plrmode | 52 | `0x0065AE3E` (+4 B `0x00612BB6`ᵗ) |
| hireling | 280 | `0x0065616B` | | plrtype | 52 | `0x0065AE26` |
| hitclass | 4 | `0x00612A17`ᵗ | | properties | 46 | `0x00638A84` |
| inventory | 240 | `0x0065C0F7` | | qualityitems | 112 | `0x00636A83` |
| itemratio | 68 | `0x006378E0` | | rareprefix | 72 | `0x0063414C` |
| itemstatcost | 324 | `0x006381D1` | | raresuffix | 72 | `0x00634132` |
| itemtypes | 228 | `0x006392D9` | | runes | 288 | `0x00639C3F` |
| leveldefs | 156 | `0x0061E41F` | | setitems | 440 | `0x00636651` |
| levels | 544 | `0x0061DA25` | | sets | 296 | `0x006357E1` |
| lowqualityitems | 34 | `0x00637549` | | shrines | 184 | `0x00641493` |
| lvlmaze | 28 | `0x0061F46C` | | skillcalc | 4 | `0x00612D23`ᵗ |
| lvlprest | 432 | `0x0061EF23` | | skilldesc | 288 | `0x006178E1` (+2 B `0x00617842`ᵗ) |
| lvlsub | 348 | `0x0061F842` | | skills | 572 | `0x0061787B` (+2 B `0x00612E15`ᵗ) |
| lvltypes | 1928 | `0x0061EA29` | | sounds | 2 | `0x00659C16` |
| lvlwarp | 48 | `0x0061F2E1` | | states | 60 | `0x00618B7D` |
| magicprefix | 144 | `0x00633D7D` | | storepage | 4 | `0x00612925`ᵗ |
| magicsuffix | 144 | `0x00633D60` | | superuniques | 52 | `0x006555F3` |
| misc | 424 | `0x00633395` | | treasureclassex | 736 | `0x00654C29` |
| misscalc | 4 | `0x00612D9C`ᵗ | | uniqueappellation | 2 | `0x0065A51C` |
| missiles | 420 | `0x0066312C` | | uniqueitems | 332 | `0x00634CEA` |
| | | | | uniqueprefix | 2 | `0x0065A492` |
| | | | | uniquesuffix | 2 | `0x0065A4D7` |
| | | | | uniquetitle | 2 | `0x0065A44D` |
| | | | | weapons | 424 | `0x00633357` |

ᵗ = executed only under `-txt` (section 3).

- [C] **86 / 88 match, 0 mismatches.** `cubemod` and `cubetype` are shipped but never loaded. A full-record
  call exists for every loaded table, and the extra 2- and 4-byte calls are compile-only code lists. Since the `.bin`
  path ignores `recSize`, this agreement is the evidence that the record strides the consumers use (fixed by each
  table's descriptor) are the `.bin` strides. It takes the "fixed-size records" claim and the name→loader→pointer
  mapping below to `[C]` (code anchor + data behaviour over every file). (fn:DATATBLS_LoadTable@0x006122F0,
  fn:DATATBLS_LoadAll@0x00619300)

### 5. Where the nine Phase-1 tables land

All per-table globals are fields of one data-tables block at `0x0096BC30`, whose address is also held in
`g_pDataTables` (`0x00744304`); offsets are given as `DataTables+off`.

| table | records | count | link / note | loader |
|---|---|---|---|---|
| treasureclassex | (local; freed after conversion) | (local) | runtime TCs: `g_pTreasureClasses` `0x0096C5EC` (+0x9BC), `g_nTreasureClasses` `0x0096C5F0` (+0x9C0), `g_TCLink` `0x0096C5E8` (+0x9B8) | `0x006547D0` |
| itemratio | `g_pItemRatio` `0x0096CC4C` (+0x101C) | `0x0096CC48` (+0x1018) | | `0x00637620` |
| itemtypes | `g_pItemTypes` `0x0096C828` (+0xBF8) | `g_nItemTypes` `0x0096C82C` (+0xBFC) | | `0x00638D80` |
| weapons | `g_pWeapons` `0x0096CA60` (+0xE30) | `g_nWeapons` `0x0096CA64` (+0xE34) | copied into `g_pItems` | `0x006315D0` |
| armor | `g_pArmor` `0x0096CA68` (+0xE38) | `g_nArmor` `0x0096CA6C` (+0xE3C) | copied into `g_pItems` | `0x006315D0` |
| misc | `g_pMisc` `0x0096CA70` (+0xE40) | `g_nMisc` `0x0096CA74` (+0xE44) | copied into `g_pItems` | `0x006315D0` |
| (combined items) | `g_pItems` `0x0096CA5C` (+0xE2C) | `g_nItems` `0x0096CA58` (+0xE28) | `g_ItemCodeLink` `0x0096BCC4` (+0x94) | `0x006315D0` |
| monstats | `g_pMonStats` `0x0096C6A8` (+0xA78) | `0x0096C6B0` (+0xA80) | `g_MonStatsLink` `0x0096C6AC` (+0xA7C) | `0x00651210` |
| levels | `g_pLevels` `0x0096C888` (+0xC58) | `g_nLevels` `0x0096C88C` (+0xC5C) | | `0x0061C540` |
| leveldefs | `g_pLevelDefs` `0x0096C890` (+0xC60) | not stored (count arg = 0) | same count as levels | `0x0061DE00` |

- [I] Items: `ITEMS_LoadItemTables` loads the three `.bin`s, allocates `(nW + nA + nM) × 0x1A8`, `memcpy`s weapons,
  armor, misc in that order, frees the three file buffers, and sets `g_pWeapons/g_pArmor/g_pMisc` to the three
  sub-ranges **of the combined copy** (`0x006333E1`–`0x0063343B`). Then, in a stock run, it calls
  `EXCEL_AddCode(g_ItemCodeLink, item[i]+0x80)` for i = 0…nItems−1 (`0x00633491` loop). So item index = combined
  position, and the code key is the u32 at record `+0x80`.
- [I] It also builds a u16 list at `0x0096CA78` of the indices whose `+0xF6` word is 0 (`0x00633510`): the classic item
  index map of the version-`0x47` item reader ([§ Plan 0039 batch P1b](#plan-0039-batch-p1b-2026-10-17) Q3).

### 6. Code→index and name→index

```c
// fn:EXCEL_FindCode@0x006BD130
int EXCEL_FindCode(ExcelLink *l, u32 code) {           // stdcall, 3rd arg unused
    lo = 0; hi = l->count;
    while (lo < hi) { mid = lo + (hi - lo)/2;          // signed /2 of (hi-lo)
        k = l->codes[mid].code;
        if (code > k) lo = mid + 1; else if (code < k) hi = mid; else return l->codes[mid].index; }
    return -1;
}
// fn:EXCEL_AddCode@0x006BD230
int EXCEL_AddCode(ExcelLink *l, u32 code) {
    grow codes by 64 entries when count >= capacity;
    for (;;) { pos = lower_bound(code); if (pos < count && codes[pos].code == code) { code += 1; continue; } break; }
    memmove up; codes[pos] = { code, l->count }; return l->count++;
}
```

- [I] The link object is 16 bytes: `+0 count`, `+4 capacity`, `+8 code array (8-byte {u32 code, s32 index})`,
  `+0xC name-tree root`. A link is used in one mode only (`EXCEL_AddCode` fatals if the tree root is set,
  `EXCEL_AddName` if the code array is set). (fn:EXCEL_AddCode@0x006BD230, fn:EXCEL_AddName@0x006BD500)
- [I] Name nodes are 0x2C bytes: `char name[32]` (lowercased, truncated to 31), `+0x20 index`, `+0x24 left` (key <
  node), `+0x28 right`. `EXCEL_FindName` copies at most 0x20 bytes of the key, lowercases it with `STR_ToLowerN`
  (table at `0x006CEB98`: `A`–`Z` → `a`–`z`, everything else unchanged), and compares with plain byte `strcmp`.
- [I] There is no hash. Codes are an ordered array, names are an unbalanced BST in insertion order.
  (fn:EXCEL_FindCode@0x006BD130, fn:EXCEL_FindName@0x006BD3C0, fn:EXCEL_AddName@0x006BD500)

### 7. Treasure classes at load time

```c
// fn:TC_LoadAll@0x0065A390
g_TCLink = EXCEL_LinkCreate();
TC_BuildAutoTCs();         // TC_Alloc("") -> index 0 (empty name, ECX=0x006CC837 ""), then the auto TCs
TC_LoadTreasureClassEx(pool);
sub_0065A2C0();            // post-pass, not read
if (g_nTreasureClasses > 0xFFFE) fatal();
```

- [I] `TC_BuildAutoTCs`: for each itemtypes record with `TreasureClass` (`+0x1D`) ≠ 0, in table order, and for
  level = 3, 6, …, 96, it allocates a TC named `sprintf("%s%d", itemtypeCode, level)` (format `0x006EC7D0`) and fills
  it with the items of that type (`0x00629A90`) whose byte `+0xFD` lies in (level−3, level], subject to further
  record flags (`+0x12A` = 0, `+0x133` ≠ 0) not followed here. 5 item types qualify in the shipped data, so
  indices 1–160.
- [I] `TC_LoadTreasureClassEx`: descriptor `treasure class` (string, 32 B, `+0x00`), `picks` (s32, `+0x20`),
  `group` (`+0x24`), `level` (`+0x26`), `magic` (`+0x28`), `rare` (`+0x2A`), `set` (`+0x2C`), `unique` (`+0x2E`),
  `nodrop` (s32, `+0x34`), `item1..10` (64-byte strings from `+0x38`, stride 0x40), `prob1..10` (s32 from `+0x2B8`).
  The loop stops at the **first record with an empty name**. Each record → `TC_Alloc(name)` (index = running count);
  `picks` 0 is stored as 1; a non-zero `group` is stored plus the number of auto-TC item types (`0x0096D4B0`).
  Then `item1`, `item2`, … go to `TC_ParseItemCell` **until the first empty `itemN`** (later columns are not read);
  a cell whose `probN` < 1 is ignored.
- [I] `TC_ParseItemCell` resolution order for one cell: strip `"`, split at the first `,` (the rest is `mul=`, `cu=`,
  `cs=`, `cr=`, `cm=`, `ce=`, `cg=`, `ma=`, `mg=` modifiers). Then (fn:TC_ParseItemCell@0x00654440):
  1. if the name is ≤ 4 characters: `STR_ToItemCode` → `ITEMS_GetByCode`; on a hit, the entry is an item;
  2. else (or on a miss) `EXCEL_FindName(g_TCLink)`; a hit **≥ 1** makes it a TC reference (index 0, the empty TC, is
     treated as a miss);
  3. else `uniqueitems` name link (`0x0096C850`), hit ≥ 1, flag `0x11`;
  4. else `setitems` name link (`0x0096C844`), hit ≥ 0, flag `0x12`;
  5. else the cell is dropped.
  So a 4-character name that is both an item code and a TC name resolves to the **item**.
- [C] The resulting index space (0 empty, 1–160 auto, 161+ = TCEx row order, names case-insensitive) reproduces every
  non-blank `TreasureClass*` cell of `monstats.bin` (12 columns at `+0x86`…`+0x9C`, u16; 4362 cells, 0 mismatches;
  blank cells are 0). This is data-behaviour corroboration that `treasureclassex` is the only TC source. The 707-row
  `TreasureClass.txt` would give a different numbering. (fn:TC_LoadTreasureClassEx@0x006547D0,
  tbl:monstats.txt:TreasureClass1)

### 8. Answers to the archivist's Phase 1 questions

- [C] **The 161 TC slots below the first TCEx row** are index 0 (empty name, `TC_Alloc` with `""`) and indices
  1–160, the auto-generated item-type TCs (section 7). **The `ItemN` text → item/TC resolution** happens at load
  time in `TC_ParseItemCell` (`0x00654440`), called from `TC_LoadTreasureClassEx` (`0x006547D0`).
- [I] **monstats references are used as record positions.** `monstats` field 0 (`Id`, type 0x11) goes through
  `EXCEL_AddNameIfAbsent` at compile time, which does **not** consume an index for a duplicate name, so the stored
  ordinal is the position among distinct Ids, as the archivist observed; `BaseId`/`NextInClass` (type 0x14) resolve
  through the same link. At run time nothing remaps them: the monstats post-passes index records directly with
  these values (`0x00651040`: `g_pMonStats + BaseId*0x1A8`, walk via `NextInClass`; `0x00650F00` likewise), and
  the record getter at `0x006538A0` is `idx*0x1A8 + g_pMonStats` with a `< g_nMonStats` bound. No lookup through
  `+0x000` was seen in the loader. So after the duplicate `cr_lancer8`, every stored monster reference points one
  record early (e.g. Pandemonium 3 `mon1` = 723 = the second `cr_lancer8`). Not checked: every one of the ~189
  readers of `g_pMonStats`; a runtime look at Pandemonium 3's spawn list would settle it. (Every reader checked in
  [§ Plan 0039 batch P1c](#plan-0039-batch-p1c-2026-10-17): all index by position.)
- [I] **Cell converters** (`EXCEL_ParseTxt` and its column mapper `0x006BCE20`, compile path only):
  - Header → descriptor match: a Storm-style string hash (`0x00413CE0`, folds `a`–`z` to upper case and `/` to
    `\`) to find candidates, then `_strnicmp` (`0x00413590`). So the lookup is **case-insensitive**, and a `.txt`
    column that matches no descriptor entry is marked `0x7FFF` and skipped (a misspelled header is silently ignored).
  - Numbers: optional leading `-`, then `value = value*10 + (c - '0')` for every remaining byte, no validation;
    `" "` gives 0x20 − 0x30 = −16. The result is stored at the field's width (s32 / s16 / u8), i.e. truncated.
  - Codes (4-char types): first 4 bytes, missing ones padded with spaces; blank → `"    "`.
  - ~~Not read: the default for a descriptor field that has no `.txt` column, the key-lookup types' not-found value,
    and string-table keys.~~ Read in [data/0004](0004-cell-converters.md) (plan 0015 Phase 2): a per-type defaults
    pass (0, or −1 for lookups and calc fields), −1 for a key not found, patchstring → expansionstring → string with
    0 → 5382; `[C]` for each sub-rule a named cell of the `excel_bin.py survey` exercises, `[I]` for the rest (data/0004 lists which).
    (fn:EXCEL_ParseTxt@0x006BD780, fn:EXCEL_MapColumns@0x006BCE20)

## Plan 0038 batch S1b (2026-10-16)

Static batch S1b of [plan 0038](../../plans/0038-inferred-claims-sweep.md) (Phase 1), the data/excel rows of
[inventory data-excel](../../plans/0038-inventory/data-excel.md) whose finding is this one (the archive rows are in
[data/0002](0002-mpq-precedence.md#plan-0038-batch-s1b-2026-10-16), the string-key and compiler rows in
[data/0003](0003-string-tables.md#plan-0038-batch-s1b-2026-10-16) and [data/0004](0004-cell-converters.md#plan-0038-batch-s1b-2026-10-16)).
No session was played. Every count below is printed by `python3 -I tools/sweep_s1b.py <check>` (report kept as
`workspace/logs/sweep-s1b-all.txt`; logs listed with their sha256 in `workspace/logs/sweep-s1b-manifest.txt`,
`d06d2aac…c9506fb`; the 91 files of the compile directory that `compile` and `survey` read, 90 `.bin` and the probe
`cubemain.txt`, are listed with their sha256 in `workspace/logs/sweep-s1b-cubeprobe-manifest.txt`, `97ca5c7a…098b7caa`,
added at the review). The second tool next to Ghidra is GNU objdump through `tools/sweep_s4b.py` and the raw byte scan
of `tools/xrefscan.py`; the `static` check pins every instruction cited here by address and pattern. Where a statement
above is tagged inferred and this section raises it, the tag and the second source given here are the current ones,
and the wording above is unchanged.

**The pinned game's own compile.** run:2026-10-15-cube-saves ran the game with `-direct -txt` in
`workspace/runtime/game-cubeprobe/`, whose `data/global/excel/` held one loose file, a probe `cubemain.txt`. The game
wrote 90 `.bin` files into that directory. 88 are byte-identical to the shipped ones; `cubemain.bin` is the probe's own
table, and `monstats.bin` differs in two bytes (below and data/0004). `cubemod.bin` and `cubetype.bin` were not written.
So the shipped `.bin` files are, all but one cell, what this binary's compiler makes of the `.txt` files the archives
rank first (`sweep_s1b.py compile`). Several rows below rest on that.

- **Row 9** (spec L36, `TC_GetByIndex` maps a TC index to the TC) **raised.** [C] items/tc § C1–C2 is `[C]` for the
  getter and its walk (run:2026-10-11-tc-drops, run:2026-10-12-tc-champion), and `sweep_s1b.py tc` replays all 9 390
  stock calls of the S2a log set with the model's TC array, 0 failed. (fn:TC_GetByIndex@0x00654E00)
- **Row 10** (spec L68, the directory `DATA\GLOBAL\EXCEL\`) **raised.** [C] Under `-direct -txt` the game read the
  loose `data/global/excel/cubemain.txt` (its rows are in the written `cubemain.bin`) and wrote every compiled table
  into the same directory (run:2026-10-15-cube-saves). Under `-direct` alone the forced runs loaded loose `.bin` files
  from that directory, for example run:2026-10-15-uniques-tcnamed-forced, whose 108 creations reproduce only with the
  edited `treasureclassex.bin`. The claim is about the path, so no edited cell is read for it (ADR-0013); review point.
  (fn:DATATBLS_OpenExcelFile@0x00612280)
- **Row 12** (spec L70, combined item stride `0x1A8`) **raised.** [C] `ITEMS_GetByCode` scales the index by `0x1A8`
  (`imul eax, eax, 0x1a8` at 0x0063366D, pinned). At run time the d2s-io logger read 4 bytes at
  `g_pItems + cls × 0x1A8 + 0x80` for 302 item units, and every one equals the code at that combined position of the
  shipped files (`sweep_s1b.py items`, `pairs_MEM=302`; run:2026-10-12-d2s-io). The three files' record size is
  `0x1A8`. (fn:ITEMS_GetByCode@0x00633640, data:g_pItems@0x0096CA5C)
- **Row 13** (spec L71, runtime TC entry `0x2C`) **raised.** [C] Writer and reader agree: `TC_Alloc` grows the array by
  `0x10` entries of `0x2C` (0x00653FB8, 0x00653FBB) and addresses the new entry with `imul 0x2c` (0x00653FDC);
  `TC_GetByIndex` bounds the index by `g_nTreasureClasses`, scales it by `0x2C` (0x00654E0F, 0x00654E17) and walks
  `+0x2C` (0x00654E4E). The tc-drops logger prints each sub-TC as `(ptr − g_pTreasureClasses) / 0x2C`, and those
  indices are the model's in all 9 390 calls. (fn:TC_Alloc@0x00653F90, fn:TC_GetByIndex@0x00654E00,
  data:g_pTreasureClasses@0x0096C5EC)
- **Row 14** (spec L72, auto-TC levels 3, 6, …, 96) **raised.** [C] The model's 160 auto TCs (5 item types × 32
  levels) put every treasureclassex record at `161 + r`; 369 such TCs were logged at those indices, up to 993
  (`Durielq (N)`), and 55 auto TCs (3 types, 27 levels) were logged with their entries reproduced. A count other than
  32 per type would move every one of the 369. (fn:TC_BuildAutoTCs@0x006541C0, run:2026-10-11-tc-drops)
- **Row 26** (spec L174, `-txt` compiles each table from `.txt` and writes the `.bin` to disk) **raised.** [C] The
  compile wrote 90 `.bin` files, 88 byte-identical to the shipped ones, the probe `cubemain.txt` compiled to its own
  table (run:2026-10-15-cube-saves). The record is the archivist's; the addendum there is requested in the backlog.
  (fn:DATATBLS_LoadTable@0x006122F0)
- **Row 29** (spec L199, no loader for `TreasureClass`, `Aiparms`, `MonName`, `WeaponClass`) **raised.** [C] The
  `-txt` compile writes a `.bin` for every table it loads (B1b), and it wrote none of these four although all four
  `.txt` files are in the archives (`no_loader_bin_written=0`, `no_loader_txt_in_archives=4`). (fn:DATATBLS_LoadTable@0x006122F0)
- **Row 30** (spec L202, the 15 code-list tables load only under `-txt`) **raised in part.** [C] Under `-txt` they
  load: the compile wrote all 15 (and the four `*code.bin`). **Remainder `[I]`:** "a stock run never loads them". The
  route's data premise fails: all 15 `.bin` ship in the stock archives (`playerclass`, `bodylocs`, `storepage`,
  `hitclass`, `colors`, `hiredesc` in d2exp; `elemtypes` in both; `monai`, `monplace`, `skillcalc`, `misscalc`,
  `events` in patch_d2; `monmode`, `plrmode`, `skills` as their full tables), so an absent file proves nothing. Proposed
  class (b), H3b: the startup logger's table names at `DATATBLS_LoadTable` in a stock start. (fn:DATATBLS_LoadCodeLists@0x00612750)
- **Row 31** (spec L204, `*code.bin` loaded whole as raw buffers) **raised.** [C] In all 44 529 evaluations of
  run:2026-10-16-calc, offset + length equals the file size of the pool (`skillscode` 14 658, `skilldesccode` 28 771,
  `misscode` 1 044, `itemscode` 56), the pool's base is constant within each of the 35 (log, pool) pairs, and
  `tools/calc.py check` matched the logged bytes to the file bytes at those offsets. So the pool is the whole file, with
  no header. (fn:DATATBLS_LoadCodeBin@0x00613E90)
- **Row 33** (spec L232, where the items/tc tables land) **raised in part.** [C] for the globals a kept logger
  dereferenced and whose checker matched: `g_pTreasureClasses` (tc-drops `SUB`, 9 390 calls; objects `OCT`),
  `g_pItemRatio` (tc-drops `QROW`, `(row − g_pItemRatio) / 0x44`), `g_pItems`/`g_nItems` (d2s-io, 302 codes) and
  `g_pLevelDefs` (drlg-roomk, `+ lid × 0x9C + 0x68`). **Remainder `[I]`:** `g_pItemTypes`, `g_pMonStats` (see row 46,
  through `DataTables + 0xA78`), `g_pLevels`, the three links and the counts: no logger reads them by address.
  (data:g_pTreasureClasses@0x0096C5EC, data:g_pItemRatio@0x0096CC4C, data:g_pItems@0x0096CA5C,
  data:g_nItems@0x0096CA58, data:g_pLevelDefs@0x0096C890)
- **Row 34** (spec L258, L263, L265, L272: weapons ++ armor ++ misc, `AddCode` of `+0x80` for each index, the code
  lookup, item index = position with 306/202/151) **raised, 4 statements.** [C] 4 999 logged (code, index) pairs, 282
  distinct and in all three ranges (148 weapons, 84 armor, 50 misc), equal the combined position of the code: 4 656
  `CSW` lines of `VENDOR_CreateStockItem` (the code and the index the lookup returned; run:2026-10-15-vendors), 41
  quest drops (`QDI` code, then the created item's class at `IC0`; run:2026-10-16-quest-drops) and the 302 memory reads
  of row 12. 659 distinct codes, so the first-record rule of E2 has no stock case. (fn:ITEMS_LoadItemTables@0x006315D0,
  fn:ITEMS_GetByCode@0x00633640, fn:EXCEL_FindCode@0x006BD130)
- **Row 35** (spec L285, the 16-byte link, codes or names, never both) **raised.** [C] Rule 1, one layout in every
  function that touches a link (20 instructions pinned): `EXCEL_LinkCreate` allocates `0x10` bytes and zeroes the four
  dwords (0x006BD04D–0x006BD063); `EXCEL_FindCode` reads the count at `+0`, the array at `+8` and 8-byte
  `{code, index}` entries (0x006BD138, 0x006BD13F, 0x006BD152, 0x006BD170); `EXCEL_AddCode` checks `+0xC` (fatal when
  set), compares capacity `+4` with count `+0` and grows by `0x40` (0x006BD25C, 0x006BD269, 0x006BD26C, 0x006BD27A);
  `EXCEL_FindName` walks from the root at `+0xC` through node `+0x24`/`+0x28` to the index at `+0x20` (0x006BD3F3,
  0x006BD450, 0x006BD455, 0x006BD473); `EXCEL_AddName` and `EXCEL_AddNameIfAbsent` check `+8` (fatal when set), store
  the count into the node's `+0x20` and insert under `+0xC` (0x006BD52B, 0x006BD579, 0x006BD57E, 0x006BD5C9, 0x006BD625).
  (fn:EXCEL_LinkCreate@0x006BD040, fn:EXCEL_FindCode@0x006BD130, fn:EXCEL_AddCode@0x006BD230,
  fn:EXCEL_FindName@0x006BD3C0, fn:EXCEL_AddName@0x006BD500, fn:EXCEL_AddNameIfAbsent@0x006BD5A0)
- **Row 38** (spec L313, `"hax "` is the u32 `0x20786168`) **raised.** [C] The d2s-io logger read the bytes `hax ` at
  item 0's `+0x80` (18 lines), and the vendor logger prints the code local `[ebp−4]` of `VENDOR_CreateStockItem`, a
  u32, as the four characters in text order (`mpi `, 4 656 lines), so the u32 holds the text little-endian; the save
  writer stores the same bytes (save/d2s I1 `[C]`). `EXCEL_FindCode` compares the codes unsigned (`jbe`/`jae` at
  0x006BD157, 0x006BD15E, pinned). (fn:EXCEL_FindCode@0x006BD130)
- **Row 41** (spec L335, L337, L341, L347, L356, L360: name links) **raised, 5 statements; 1 in part.**
  - F1 (L335) **in part.** [C] lower-casing: 11 name-lookup cells of the laid-out tables differ in case from their key
    and resolve to it, in the shipped and in the game-compiled tables alike (`sweep_s1b.py survey`,
    `name_cells_case_differs_from_key=11`, 0 unexplained). **Remainder:** the 31-byte cut has no stock cell (no
    name-lookup cell is longer than 31); it is S1e's c-emu data-excel row 16. (fn:STR_ToLowerN@0x004113C0)
  - F2 (L337), F3 (L341), F4 (L347), L356 (first record wins), L360 (TC names by `AddName`, monstats `Id` by
    `AddNameIfAbsent`) **raised.** [C] 736 name-lookup cells (610 dword, 126 word) resolve in the survey on the
    game-compiled tables; the duplicated `cr_lancer8` and the repeated `monseq` values store the first occurrence
    (data/0004); the TC numbering of G5 (every TC index of 9 390 replayed calls, `AddName`, one index per TC) and the
    monstats ordinals among distinct `Id`s (H2, `AddNameIfAbsent`, no index for the duplicate) both hold. Rule 2 over
    the compile's own output. (fn:EXCEL_FindName@0x006BD3C0, fn:EXCEL_AddName@0x006BD500,
    fn:EXCEL_AddNameIfAbsent@0x006BD5A0)
- **Row 42** (spec L387, L395, L397, L406, L420, L422, L456, L458: the TC load) **raised, 2 statements; 6 in part.**
  The evidence is `sweep_s1b.py tc`: the model of G1–G4 (`tools/tc.py`) reproduces all 9 390 stock calls (every
  `NDP` total, pick, selected entry and sub-TC index), 425 distinct TC indices logged.
  - G2 (L397) and the index formula (L456) **raised.** [C] 55 auto TCs logged with their entries (type order, the
    `(level − 3, level]` filter, the rarity weights), and the formula puts the next 852 at `161 + r` (row 14).
    (fn:TC_BuildAutoTCs@0x006541C0)
  - G1 (L387) **in part.** [C] index 0 is the empty TC (752 `DROP base=0` lines name no TC), then the auto TCs, then
    treasureclassex. **Remainder d-none:** the `> 0xFFFE` fatal and the post-pass `0x0065A2C0`. (fn:TC_LoadAll@0x0065A390)
  - Alloc (L395) **in part.** [C] one index per name, in allocation order, entries `0x2C` (row 13). **Remainder
    d-none:** the growth by 16 entries has no observable. (fn:TC_Alloc@0x00653F90)
  - G3 (L406) **in part.** [C] `group + autoTypes`: 302 logged TCs have a group and their upgrade walks reproduce.
    **Remainder d-none:** the first empty name ends the table, but it is the last record (852 of 853); `Picks` 0 and
    `Prob` < 1 have no stock cell (items-tc 13 and 15); no stock record has an item cell after an empty one
    (`tcex_item_cells_after_an_empty_one=0`). (fn:TC_LoadTreasureClassEx@0x006547D0)
  - G4 (L420) **in part.** [C] the item-code test first, then the TC name (a hit ≥ 1): every logged entry resolves as
    the model's (items and sub-TCs). **Remainder d-edit:** the unique and set steps (TC-named uniques are reached only by
    edited data, items/uniques-sets § F). (fn:TC_ParseItemCell@0x00654440)
  - Quotes (L422) **in part.** [C] a leading and a trailing `"` do not stop resolution: 81 quoted cells, 23 of them in
    logged TCs, reproduce. **Remainder d-none:** no stock cell has text after an inner quote, so "the name ends at the
    first inner quote" has no case. (fn:TC_ParseItemCell@0x00654440)
  - 852 loaded, 1 013 in all (L458) **in part.** [C] the numbering holds to the highest logged index, 993.
    **Remainder d-none:** the count itself (no logged index above 993; the bound is not logged).
    (fn:TC_LoadTreasureClassEx@0x006547D0, run:2026-10-11-tc-drops)
- **Row 45** (spec L466, the upgrade walk belongs to items/tc) **raised.** [C] items/tc § C1–C2 (run:2026-10-11-tc-drops,
  run:2026-10-12-tc-champion). (fn:TC_GetByIndex@0x00654E00)
- **Row 46** (spec L485, H1: monster records by position, stride `0x1A8`) **raised.** [C] Rule 1: two readers agree,
  the getter 0x006538A0 (`cmp edi, [DataTables + 0xA80]`, `imul edi, edi, 0x1a8`, `add edi, [DataTables + 0xA78]`) and
  the inline read at 0x005A3D3E–0x005A3D4C (same bound, stride and base), both pinned; the getter has 18 raw callers.
  The monster checkers read `monstats.bin` by class position and reproduce the kept monster runs with 0 mismatches
  (monsters/0001 § Plan 0038 batch S3a: 4 568 creations). (data:g_pMonStats@0x0096C6A8)
- **Row 47** (spec L490, H3: the stored reference is the record position) **raised.** [C] The pool `[C]` of spec H
  (*Pandemonium 3*'s region held class 723 in every logged game; run:2026-10-12-mon-pool) and the position reads of
  row 46. (fn:sub_005475E0_MonRegionPool@0x005475E0)
- **Row 48** (spec L498, the three cells that store 723, and the H2/H3 tag) **raised, 2 statements.** [C] as row 47:
  the three `levels` 135 cells store 723 (H2, data) and the game used 723 as the position (run:2026-10-12-mon-pool).
- **Row 49** (spec L504, `g_MonStatsLink` filled at compile only) **raised.** [C] objdump lists 9 operands that name
  `0x0096C6AC` and the raw scan finds the same 9 occurrences: 5 descriptor link fields (0x0061C9DB, 0x00651245,
  0x0065537A, 0x00656650, 0x00659ED9), the store after `EXCEL_LinkCreate` (0x0065382D), two loads before
  `EXCEL_LinkFree` (0x00653D3F, 0x0065A226) and one `EXCEL_FindName` (0x006599CC) in the compile callback 0x00659990,
  whose only reference is a descriptor field (0x00659A55). No game-time lookup. (data:g_MonStatsLink@0x0096C6AC,
  fn:MONSTATS_Load@0x00651210)
- **Row 73** (spec L703, gamble `+0x04` level, `+0x08` item index, sorted by level; finding items/0009) **raised in
  part.** [C] The gamble list built from the records (`g_GambleList`, dumped once per process as `VGL`, the same
  125 entries in every dump of run:2026-10-15-vendors) holds exactly the gamble codes' combined positions, in
  ascending base level (`+0xFD`), and its `countUpTo[L]` is the number of base levels ≤ L for every L. **Remainder
  `[I]`:** the record offsets `+0x04`/`+0x08` themselves; only the list built from them is logged.
  (fn:GAMBLE_LoadTable@0x00638AE0, tbl:Gamble.txt:code)
- **Row 77** (spec L720, one combined array, item index = position) **raised.** [C] As row 34.
  (fn:ITEMS_LoadItemTables@0x006315D0)
- **Row 78** (spec L722, runtime TC array 1 013 × `0x2C`) **raised in part.** [C] the stride (row 13). **Remainder
  d-none:** the count (row 42, L458). (fn:TC_Alloc@0x00653F90)

## Plan 0039 batch P1b (2026-10-17)

Rows Q1, Q2, Q3 and B7 (c) of [plan 0039](../../plans/done/0039-backlog-sweep-4.md). Static: Ghidra on the lane's copy and
objdump. No game run.

### Q1: the auto-TC details (stale)

- The details that the data/excel spec keeps as an `[L]` open question (G2 (a)–(d): the names, `picks` 1, `group` 0,
  `level` L − 3, the item filter, the entry probability and flag `0x10`) are already in a finding:
  [items/0001 § 9](../items/0001-tc-resolution.md#9-auto-item-type-tcs-weapn-armon-bown-melen-abown) states each of them `[I]` with anchors
  (0x0065428B–0x00654361), and § Plan 0038 batch S1b above raised G2 and the index formula to `[C]` (55 auto TCs logged with
  their entries). Nothing new to read; the spec's open question can move into G2 with those anchors.

### Q2: the TC post-pass and the `group`/`level` walk (stale)

- The post-pass `0x0065A2C0` is `TC_BuildChestTable`: for act 1–5, the three difficulty suffixes and the three chest
  kinds it builds the name `"Act %d%s Chest %s"`, looks it up in `g_TCLink` and stores the TC pointer (0 when the name is
  missing) in `g_ChestTCs` ([items/0001](../items/0001-tc-resolution.md), its *Functions* table and the chest bullet,
  `[I]`). Re-read here (0x0065A2C0–0x0065A38F): it reads no TC field and changes none, so § 7's "post-pass, not read" is
  answered by that row. (fn:TC_BuildChestTable@0x0065A2C0, data:g_ChestTCs@0x0096C5F4)
- The walk in `TC_GetByIndex` is [items/0001 § 4](../items/0001-tc-resolution.md#4-level-upgrade--tc_dropbyindex-0x0055afa0-and-tc_getbyindex-0x00654e00),
  `[C]` there (tc 3). Re-read in the disassembly (0x00654E00–0x00654E5E): the index is a `u16` tested `≠ 0` and
  `< g_nTreasureClasses` (signed `jge`), else NULL; the level is a signed `int`, and the walk runs only for `level > 0`,
  `group ≠ 0` and `t[1].group = t.group`; each step compares `t[1].level` (`movsx`, signed) with the level (`jg` stops)
  and continues while `t[2].group = t[1].group`. This agrees with § 4.

### Q3: the u16 list at `0x0096CA78`

- [I] **It maps a classic item index to the current one.** `ITEMS_LoadItemTables` allocates `2 · nItems` bytes, zeroes
  them, and writes, in item order, the combined index of every record whose `version` (`+0xF6`, u16) is 0
  (0x006334C4–0x00633531). The count is not stored: entries past the last version-0 item stay 0.
  (fn:ITEMS_LoadItemTables@0x006315D0, data:g_pClassicItemIndex@0x0096CA78, tbl:Weapons.txt:version)
- [I] **Its one reader is the oldest item record format.** `sub_006335A0_ItemClassicIndexMap(i)` returns
  `list[i]` (u16) for `0 ≤ i < nItems`, −1 otherwise, and is fatal when the list is NULL (0x006335A0–0x006335E6). Its only
  caller is `sub_00532F30_ItemReadV71Record` (0x00533310), which `sub_00533350_ItemListReadV71` calls three times
  ([rng/0002](../rng/0002-seed-tree.md), the version-`0x47` item list). For a record whose flags have neither bit
  `0x100000` nor the ear bit `0x10000`, the item is named by a signed 10-bit index (`BITBUF_ReadSigned(10)`); the reader
  maps it through the list, stores the current index at record `+0x06` and the item's code (`+0x80` of its record) at
  `+0x44`; an index < 0 or a missing record gives index −1 and code 0. So an item saved by a version-0 game is found
  by its position among the version-0 items, whatever the expansion rows inserted since.
  (fn:sub_006335A0_ItemClassicIndexMap@0x006335A0, fn:sub_00532F30_ItemReadV71Record@0x00532F30,
  fn:sub_00533350_ItemListReadV71@0x00533350)
- [C] **Stock counts (data).** In the shipped `weapons.txt`, `armor.txt` and `misc.txt`, 361 of the 659 item rows have
  `version` 0 (175, 92, 94), the rest 100 (one `misc` row 109). A 10-bit signed index reaches 511, so it covers them.
  (tbl:Weapons.txt:version, tbl:Armor.txt:version, tbl:Misc.txt:version)
- `sub_00633540_ItemTablesFree` frees the item code link, the combined table and this list (0x00633540–0x0063358F).

### B7 (c): the States field descriptor

`STATES_Load` (0x00618100) builds the `states` descriptor on its stack at `[ebp−0x580]` and passes it to
`DATATBLS_LoadTable` at 0x00618B7D. Read by replaying the stores (register constants and `[ebp−X]` writes,
0x0061812A–0x00618B59) into 20-byte entries `{column, type, len, offset, link}` (§ 1); 70 entries, the last `end`.
Type `0x1A` is a bit flag: `len` is the bit number, `offset` the flag field.

- [I] **`attred` is flag bit 10** (entry 12: type `0x1A`, bit `0xA`, field `+0x10`). Bit 9 is `attblue`, bit 11 `curse`.
  The data agree: `attred` is blank in all 185 rows and bit 10 is 0 in every record.
  (fn:STATES_Load@0x00618100, tbl:States.txt:attred)
- [I] **`immed` has no descriptor entry**, so the compiler ignores the column (the header maps it to "unknown",
  `EXCEL_MapColumns` § Functions). That is why no byte or bit follows it. (fn:STATES_Load@0x00618100,
  fn:EXCEL_MapColumns@0x006BCE20, tbl:States.txt:immed)
- [I] **The red bits:** `rfred` is bit 26 (`0x1A`), `rcred` bit 27 (`0x1B`), `rlred` bit 28 (`0x1C`), then `rpred` 29.
  The blue run is `rfblue` 20, `rcblue` 21, `rlblue` 22, `rpblue` 23. (tbl:States.txt:rfred, tbl:States.txt:rcred,
  tbl:States.txt:rlred)
- [I] The rest of the descriptor agrees with [States § Columns](../../tables/States.md): `state` (type `0x11`, a word
  index through the name link `0x0096BCF0`, at `+0x00`), `group` (type 3, an s16 at `+0x1E`, so the always-0 byte
  `+0x1F` is its high byte), the 40 flag bits at `+0x10` (`nosend` 0 … `disguise` 16, `restrict` 17
  … `noclear` 36, `bossinv` 37, `meleeonly` 38, `notondead` 39), the overlays (`+0x02..+0x0E`), `stat` `+0x18`,
  `setfunc`/`remfunc` `+0x1A`/`+0x1C`, `missile` `+0x3A`, `skill` `+0x38`, the colour and light bytes `+0x20..+0x24`,
  the sounds `+0x26`/`+0x28`, `itemtype` `+0x2A`, `itemtrans` `+0x2C`, `gfxtype` `+0x2D`, `gfxclass` `+0x2E`, `cltevent`
  `+0x30`, `clteventfunc`, `cltactivefunc`, `srvactivefunc` `+0x32..+0x36`. (0x0061812A–0x00618B59)

## Plan 0038 batch S1e (2026-10-17)

Static batch S1e of [plan 0038](../../plans/0038-inferred-claims-sweep.md), rows 16, 36, 37, 40, 43 and 44 of
[inventory data-excel](../../plans/0038-inventory/data-excel.md). No session was played. Method: the functions under
Ghidra's p-code emulator against models ([ADR-0015](../../adrs/0015-emulated-reproduction.md)),
[run:2026-10-17-sweep-emu](experiments.md#run2026-10-17-sweep-emu) family `excel` (5 500 calls) and, for the 31-byte
cut through the `.txt` converter, family `parsetxt` ([data/0004 § S1e](0004-cell-converters.md#plan-0038-batch-s1e-2026-10-17)).
Read set: the scratch link, its array or name nodes and the key (case memory); `STR_ToLowerN`'s table 0x006CEB18–0x006CEC17
(`.rdata`, indexed by a signed char); `memmove`'s jump tables (`.text`); one write-only store of `strncpy` (0x004135D0)
to 0x007788D8, which none of these functions reads. Where a statement above is tagged inferred and this section raises
it, the tag and the second source given here are the current ones.

- **Row 36** (spec L288, `FindCode`: binary search, unsigned compare) **raised.** [C] 2 500 calls on arrays of 0–300
  entries (336 deliberately unsorted, so the probe path itself is compared), 1 021 probes ≥ 2³¹, 133 negative counts
  (−1 at once): every return equals the model's `lo/hi` search with `mid = (hi − lo)/2 + lo` and an unsigned compare;
  the family's negative controls (a signed compare here, a reused duplicate for `AddCode`, a 32-byte key for `FindName`)
  differ in 1 048 cases. (fn:EXCEL_FindCode@0x006BD130,
  run:2026-10-17-sweep-emu)
- **Row 37** (spec L298, `AddCode` bumps a duplicate code to code + 1) **raised.** [C] 1 500 inserts (capacity above
  the count, so no allocation): 665 bumped, 221 of them through `0xFFFFFFFF` → 0 → … chains, 835 plain; the array,
  count and returned index (the old count) match byte for byte, `memmove` included. (fn:EXCEL_AddCode@0x006BD230,
  run:2026-10-17-sweep-emu)
- **Row 40** (spec L320, item codes are case-sensitive) **raised.** [C] 316 probes that differ from a stored code only in
  letter case find nothing (−1). (fn:EXCEL_FindCode@0x006BD130, run:2026-10-17-sweep-emu)
- **Row 16** (spec L75, name keys are 31 characters) **raised.** [C] 1 500 `FindName` calls on random trees: the key is
  cut to its first 31 bytes and lower-cased through the table (bytes ≥ 0x80 indexed as signed), then walked by unsigned
  `strcmp` (`<` left at `+0x24`, else right at `+0x28`); 435 keys longer than 31 bytes, 57 of them found by their
  first 31; 894 mixed-case keys; an empty link returns −1. `EXCEL_ParseTxt`'s name lookups give the same cut (1 058
  cells over 31 bytes, data/0004 § S1e). (fn:EXCEL_FindName@0x006BD3C0, fn:STR_ToLowerN@0x004113C0, run:2026-10-17-sweep-emu)
- **Rows 43, 44** (spec L461, a short name that is both an item code and a TC resolves to the item; L463, `uniqueitems`
  row 0 cannot be named from a TC, `setitems` row 0 can) **not raised; returned to d-none.** `TC_ParseItemCell` calls
  `TC_AddEntry` on every resolved cell, and `TC_AddEntry` always calls `TC_GrowEntries`, which reallocates through the
  pool allocator 0x0040B4B0 (heap calls outside the image), so no case that reaches either claim runs to completion
  under ADR-0015 condition 1. The lookups they rest on are now `[C]` (`FindCode` case rules above, `FindName` row 16);
  the order of the tests and the `jle`/`jl` that separate unique and set row 0 stay code readings (0x0065450F,
  0x00654569, 0x006545B4). (fn:TC_ParseItemCell@0x00654440, fn:TC_GrowEntries@0x00654010)

## Plan 0039 batch P1c (2026-10-17)

Row Q4 of [plan 0039](../../plans/done/0039-backlog-sweep-4.md). Static: an operand scan of the objdump listing of the
pinned image (scratch script, not kept), with the odd sites read by hand. No game run.

### Q4: every reader of `g_pMonStats` uses the stored value as a position

§ 8 left one thing unchecked: whether any of the ~189 readers of `g_pMonStats` looks a monster up some other way, for
example by matching the `Id` ordinal at `+0x000`.

- [I] **The scan.** It found 194 instructions that use `g_pMonStats` in `.text`: `[reg+0xA78]` with `reg` the table
  block (`g_pDataTables`), or the absolute `0x0096C6A8`. Three are writes: the loader's store and the two clears.
  The 191 reads fall into four shapes:

  | shape | sites | what the index is |
  |---|---:|---|
  | `0 ≤ i < count` test (`+0xA80` or `0x0096C6B0`), then `base + i·0x1A8` | 177 | a position: 175 with the multiply next to the test, 2 (0x00466601, 0x00536174) with it computed earlier |
  | a constant offset after a `count > n` test | 6 | the fixed classes 492–495 (`imp1`–`imp4`; offsets `0x32EE0`…`0x333D8`, 0x005E2DDD–0x005E3090) |
  | loader-side code, 0x00650F00–0x0065111E | 5 | the `BaseId`/`NextInClass` post-passes of § 8, which index by position as well |
  | allocation, free and NULL checks | 3 | 0x00653D30, 0x00653D63, 0x0065A211: no index |

  None of the 191 is part of a search over the records, such as a loop that compares `+0x000` with a value. A record
  is always the base plus a position times `0x1A8`, or a constant multiple of it. So H3 holds for every reader: whatever a table stores as a monster
  reference (`BaseId`, `NextInClass`, `minion1`/`2`, `spawn`, the `levels` `mon`/`nmon`/`umon`/`cmon` lists, the
  SuperUniques and Hireling classes, a MonPreset id) is used directly as the record position. It is never mapped
  back through the ordinal. (data:g_pMonStats@0x0096C6A8, data:g_pDataTables@0x00744304,
  0x0065385D)
- [I] The scan sees only instructions that address `g_pMonStats`. A copy of the base pointer kept in another
  structure would escape it. None was met while reading the 16 odd sites, and the loader stores the pointer only at
  `0x0096C6A8` (0x0065385D).
- Consequence, as before: only the three *Pandemonium 3* cells that store 723 are affected (spec H). Whether a unit of
  class 723 shows in play is still `monsters/spawn`'s question (the region pool already shows it, confirmed).

## Plan 0038 batch H3b (run:2026-10-27-sweep-data-load)

Harness batch H3b of [plan 0038](../../plans/0038-inferred-claims-sweep.md), the loader and lookup rows of
[inventory data-excel](../../plans/0038-inventory/data-excel.md) and [data-README](../../plans/0038-inventory/data-README.md),
and data-excel row 30's remainder (S1b review). Seven program runs on slot 2 with gdb on the game before its startup
code (`tools/d2run.py --early`); sessions, loose files and commands as in
[data/0002 § Plan 0038 batch H3b](0002-mpq-precedence.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load) and the
record [run:2026-10-27-sweep-data-load](experiments.md#run2026-10-27-sweep-data-load). Counts are printed by
`python3 -I tools/sweep_h3b.py check` (`check/check-h3b.txt`) and `txtfiles` (`check/txtfiles-h3b*.txt`). Where a
statement above is tagged inferred and this section raises it, the tag and the run given here are the current ones.

- **data/excel row 5** (spec L31, `-txt` applied through `ApplyOptions` → `ApplyTxtOption`) **raised.** [C] In the six
  runs that reach it, `sub_0044D9C0_ApplyTxtOption` is called once, returning to 0x0044DA0E inside
  `sub_0044D9F0_ApplyOptions`'s handler loop, with the config byte `+0x215` = 1 under `-txt` (txt, dtxt) and 0
  otherwise, and `g_DataTblsCompileTxt` (0x0096C8B4) holds that value after it.
  (fn:sub_0044D9C0_ApplyTxtOption@0x0044D9C0, fn:sub_0044D9F0_ApplyOptions@0x0044D9F0, run:2026-10-27-sweep-data-load)
- **data/README row 3, data/excel row 6** (`DATATBLS_LoadAll` loads every table in a fixed sequence) **raised.** [C]
  Each run that reaches it calls `DATATBLS_LoadAll` once (from 0x0044B937, at startup) and makes, inside it,
  the same 73 `DATATBLS_LoadTable` calls in the same order in the four stock-mode runs (stock, loose, direct, clamp),
  from `compcode` to `difficultylevels`; under `-txt` (txt, dtxt) the 73 come in the same order with 18 more calls
  between them (below). (fn:DATATBLS_LoadAll@0x00619300, fn:DATATBLS_LoadTable@0x006122F0, run:2026-10-27-sweep-data-load)
- **data/excel row 30, remainder** ("a stock run never loads" the 15 code-list tables) **raised in part, with a
  correction.** [C] No `DATATBLS_LoadTable` call names one of them (nor the 2-byte `monstats` and `skilldesc` calls) in
  the four stock-mode runs; under `-txt` all of them are called, with their small record sizes (4 or 2 bytes).
  **Correction:** `hitclass.bin` is read whole in every run, `-txt` or not, by the character-graphics copy of the
  loader (`FILE_LoadWhole` returning to 0x0050448A, with `weapons`, `armor`, `misc`, `itemtypes`; § 3's D2Comp.cpp
  reader at 0x00504430), so "a stock run never loads them" holds for `DATATBLS_LoadTable` only. **Refinement:** a
  2-byte `sounds` call is a further `-txt`-only call (the 18th; the full `sounds` table loads in every run).
  (fn:DATATBLS_LoadCodeLists@0x00612750, 0x006127DF, 0x0050448A, run:2026-10-27-sweep-data-load)
- **data/excel row 27** (spec L191, `-txt` alone changes nothing loaded; `-direct -txt` runs on `.txt`) **raised.** [C]
  Both `-txt` runs compiled and wrote the same 90 `.bin` files (identical hashes); 89 are byte-identical to the
  archive copies and `monstats.bin` is not (two bytes, data/0004 § S1b). In the txt run every one of the 191 excel
  buffers `FILE_LoadWhole` returned is the archive copy, `monstats.bin` included; in the dtxt run every `.bin` read
  after its write came from the disk (95 reads), and the loaded `monstats` records differ from the shipped ones in that
  one record's `+0x006..+0x007` at load and at the excel unload. The 5 reads before a write (the character-graphics
  loader's) went to the archives. (fn:DATATBLS_LoadTable@0x006122F0, fn:DATATBLS_SetCompileTxt@0x006125A0,
  run:2026-10-27-sweep-data-load)
- **data/README row 4, data/excel row 7** (an item code resolved through `ITEMS_GetByCode` → `EXCEL_FindCode`)
  **raised.** [C] 1 147 logged calls (one line per distinct code and caller, over the six runs that load the tables; 29
  of them in play, from 0x004DBAA3 and 0x0063EC32) all return the record `g_pItems + 0x1A8 × i` with `*pIndex` = i, i
  the code's first position in weapons + armor + misc; the 37 calls with a code that is no item (`Ammo`, `bow3`, `lit `,
  `med `…) return 0 with index 0. (fn:ITEMS_GetByCode@0x00633640, fn:EXCEL_FindCode@0x006BD130,
  run:2026-10-27-sweep-data-load)
- **data/README row 5, data/excel row 8** (a TC name resolved through `TC_GetByName` → `EXCEL_FindName`) **raised in
  part, with a correction.** [C] The name → TC map: 3 728 logged `EXCEL_FindName` calls on `g_TCLink` (0x0096C5E8)
  return the TC index of the name (the empty name 0), or −1 for the 6 names that are no TC, from
  `TC_ParseItemCell` (return 0x0065450B), `TC_LoadAll` (0x0065A33B) and, under `-txt`, the `.txt` parser (0x006BDDEC).
  **Correction, the remainder d-none:** `TC_GetByName` itself is never called. It has no reference in the image
  (`tools/xrefscan.py 0x00654DD0`: no rel32 call or jump, no absolute pointer) and its breakpoint had 0 hits in all
  seven runs, while the callers above called `EXCEL_FindName` directly. The entry-point rows that name it describe dead
  code; it has no observable (the `GameCreateA` precedent, H4b). No TC name lookup ran in play: in the stock run the
  count of `EXCEL_FindName` calls on `g_TCLink` stays 2 789 from the first total in game to the last (t = 31.5–91.5 s)
  while `ITEMS_GetByCode`'s rises from 5 098 to 44 886.
  (fn:TC_GetByName@0x00654DD0, fn:EXCEL_FindName@0x006BD3C0, fn:TC_ParseItemCell@0x00654440,
  fn:TC_LoadAll@0x0065A390, run:2026-10-27-sweep-data-load)

## Data touched

- `fmt:excel-bin#bin` count header and record array (all 88 files).
- `tbl:TreasureClassEx.txt:Treasure Class`, `Picks`, `Group`, `Level`, `Magic`, `Rare`, `Set`, `Unique`, `NoDrop`,
  `Item1..10`, `Prob1..10` (descriptor offsets above).
- `tbl:ItemTypes.txt:TreasureClass` (`+0x1D`, u8), `tbl:ItemTypes.txt:Code` (via link `0x0096C824`).
- `tbl:MonStats.txt:TreasureClass1`…`TreasureClass4(H)` (`+0x86`…`+0x9C`, u16 TC index).
- `tbl:Levels.txt:DrlgType` → `leveldefs+0x30`, `tbl:Levels.txt:LevelType` → `leveldefs+0x34` (s32). Full
  `leveldefs` descriptor (all s32 unless noted): `QuestFlag +0x00`, `QuestFlagEx +0x04`, `Layer +0x08`,
  `SizeX/SizeX(N)/SizeX(H) +0x0C/+0x10/+0x14`, `SizeY/SizeY(N)/SizeY(H) +0x18/+0x1C/+0x20`, `OffsetX +0x24`,
  `OffsetY +0x28`, `Depend +0x2C`, `DrlgType +0x30`, `LevelType +0x34`, `SubType +0x38`, `SubTheme +0x3C`,
  `SubWaypoint +0x40`, `SubShrine +0x44`, `Vis0..7 +0x48..+0x64`, `Warp0..7 +0x68..+0x84`, `Intensity/Red/Green/Blue
  +0x88..+0x8B` (u8), `Portal +0x8C`, `Position +0x90`, `SaveMonsters +0x94`, `LOSDraw +0x98`. Checked against
  `levels.txt` over all 137 records for 15 of these columns, 0 mismatches.
- `struct:DataTables` (`0x0096BC30`) offsets in section 5.

## Dead ends

- `r2 izz~txt` found no `txt` switch string: r2's default minimum string length hides 3-character strings. The
  `TXT`/`txt` entry was only found by walking the 0x5C-byte option table. Read the table, don't grep for short strings.
- Ghidra's xrefs showed no caller of `DATATBLS_SetCompileTxt`, which made `-txt` look removed. The caller sits in an
  undefined function reached only through the handler table at `0x0070F488`. A raw `E8`/`E9` scan of `.text` found it.
- The `treasureclass` string (`0x006EA76C`) looked like a loader for `TreasureClass.txt`; it is an itemtypes column name.
- `CallArgs.java` doesn't report the return destination when the value is first stored in a local; the destinations
  in section 5 were read from the disassembly after each call.

## Open questions

- Behaviour under `-direct -txt` is read from code only. A wine run that edits one `.txt` cell and observes the effect
  (and checks that `DATA\GLOBAL\EXCEL\*.bin` files are written) would confirm the `-txt` claims.
- `EXCEL_ParseTxt` type codes are only partly read (section 1). Only relevant if the spec has to describe the
  `.txt` → `.bin` compiler; the archivist's cell diff covers the stock data.
- ~~`TC_GetByIndex`'s group/level walk and `sub_0065A2C0`'s post-pass belong to plan 0004 (items/tc).~~ Stale: both are
  read in items/0001 (§ 4, and `TC_BuildChestTable`); see [§ Plan 0039 batch P1b](#plan-0039-batch-p1b-2026-10-17) Q2.
- `runessrv` probe (`0x00639420`) and the `cubeserver.*` guard: purpose not followed.
