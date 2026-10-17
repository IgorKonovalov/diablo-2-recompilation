# 0004 — Excel cell converters, missing-column defaults, and fields with no `.txt` column

> **Subsystem:** data/excel
> **Question:** What does the `.txt` compiler store for each kind of cell (including a blank cell and a column the `.txt` lacks), and are the record bytes no column fills padding or filled at run time?
> **Date:** 2026-10-12   **Plan:** 0015 (Phase 2)   **Status:** answered (each converter sub-rule `[C]` where a named cell of the laid-out tables exercises it, else `[I]`; no-column fields `[I]`)

Static reading only. This continues [data/0001](0001-excel-loader.md) §1 and §8, which named `EXCEL_ParseTxt` and
`EXCEL_MapColumns` and left the defaults, the key not-found value and the string-key order open. The compiler runs
only under `-txt` (data/0001 §2); what it does is what the shipped `.bin` files hold, so the archivist's cell diff
is the second source for every converter rule. "Descriptor entry" is one 20-byte `{column, type, len, offset, link}`
entry of a table's field descriptor (data/0001 §1).

## Answer (summary)

- [C] **Column lookup.** `EXCEL_MapColumns` matches each `.txt` header against the descriptor by a folded hash
  (`0x00413CE0`) and `_strnicmp` (`0x00413590`), so the match is case-insensitive; an unmatched header maps to `0x7FFF`
  and its cells are skipped. On a match it zeroes the descriptor entry's hash (`0x006BD00F`), so a **header that
  occurs twice feeds the field from its first occurrence** and the second maps to `0x7FFF`. Data: `excel_bin.py
  survey` over all 28 laid-out tables (7 425 records, 555 659 cells, 0 unexplained, 1 explained; run 2026-10-12 on
  the merged excel directory) depends on these rules (`alternateGfx` /
  `alternategfx`, the ignored `HratliMagicLvl`, armor's second `mindam`/`maxdam`). (fn:EXCEL_MapColumns@0x006BCE20)
- **Columns the `.txt` lacks get a per-type default.** `EXCEL_MapColumns` appends every descriptor entry that no
  header matched after the file's columns and returns the total; at the end of each row `EXCEL_ParseTxt` walks those
  entries and stores through the jump table at `0x006BE128` (indexed by type − 1). (0x006BDFA0–0x006BE031)
  - [C] the types an absent column of a laid-out table exercises (23 855 absent cells, every one equal to the
    default): **0** for a string (type 1: misc `setinvfile`), integers (type 2 weapons `minac`/`pSpell`, type 3 misc
    `auto prefix`, type 4 weapons `spelldesc`, type 6 weapons `absorbs`/`spellicon`), a 4-character code (type 9:
    misc `normcode`/`ubercode`/`ultracode`, weapons `BetterGem`; four zero bytes) and a string key (type 0x16:
    weapons/armor `spelldescstr`, word 0, the converter is not called); **−1 at the field's width** for a byte code
    lookup (0x0D: armor/misc `hit class`, automagic `classspecific` → `0xFF`), a word code lookup (0x0F:
    magicsuffix/automagic `etype4`/`etype5` → `0xFFFF`) and a word name lookup (0x14: weapons/armor `state`,
    `cstate1`/`2`, `stat1`–`3` → `0xFFFF`); and the calc callback (type 0x19: weapons/armor `calc1`–`3`, `len`,
    `spelldesccalc`), called with no cell (ECX = 0), which `0x00631530` turns into −1 (0x00631552).
  - [I] the types no absent column exercises, read from the jump table only: 0 for types 5, 7, 8, the registrations
    0x0A/0x0C/0x0E/0x10–0x12 and bit flags 0x1A (untouched); −1 for the dword lookups 0x0B and 0x13 and the byte name
    lookup 0x15 (`0xFF`); callbacks 0x17/0x18 called with ECX = 0 (what each does with it is its own code). (0x006BE128)
- **Integers.** (0x006BDE15–0x006BDE3E)
  - [C] optional leading `-`, then `value = value·10 + (byte − 0x30)` per byte, stored at the field width (every
    integer cell of the survey). (0x006BDE15–0x006BDE3E)
  - [C] **no validation**: misc `TMogMin`/`TMogMax` of the three Khalim parts hold a single space and store −16
    (`0xF0`, 6 cells). (0x006BDE20–0x006BDE29)
  - [C] **truncation to the field width**: misc `rarity` = 999 on 7 rows stores `999 & 0xFF` = 231 (the only
    out-of-range integer cells of the laid-out tables). (0x006BDE56)
  - [I] the byte is sign-extended (`movsx`), so a byte ≥ 0x80 adds a negative digit (no cell has one); type 5 stores
    only a non-empty cell, and type 0x1A sets or clears one bit (both read from the code only; the 0x1A flags of
    monstats diff clean but are not checked here bit by bit against the set/clear path). (0x006BDE20)
- **Key lookups.** A code lookup copies at most 4 bytes of the cell, pads with spaces (blank → `"    "`) and calls
  `EXCEL_FindCode`; a name lookup copies at most 31 bytes and calls `EXCEL_FindName` (blank → `""`); the result (−1
  when absent) is stored at the field width. (0x006BDD82, 0x006BDDE7)
  - [C] **a blank cell is looked up**: it gets the row whose key is blank (itemtypes row 0 `"    "` for weapons/armor/misc
    `type2`, itemtypes `Equiv1`/`Equiv2`/`Shoots`/`Quiver`; the empty-named TC 0 for monstats `TreasureClass*`), or −1
    when the target has no blank key (the `states`, `itemstatcost`, `skills`… refs listed in excel-bin.md). A
    non-blank key that matches nothing would take the same −1 path; no cell has one. (0x006BDD82, 0x006BDDE7)
  - [C] **cut to 4 characters**: magicprefix `itype1` = `staff` (9 cells) finds `staf`; magicsuffix `itype2` =
    `ring ` (trailing space, 3 cells) finds `ring`. (0x006BDD82)
  - [C] **a duplicated key resolves to its first row**: the itemtypes rows with a blank code share the key `"    "` and
    every blank itemtypes reference (15 443 cells: weapons/armor/misc `type2`, itemtypes `Equiv1`/`Equiv2`/`Shoots`/
    `Quiver`, the affix and rare-affix `itype*`/`etype*`) stores row 0, the first of them (code link,
    `EXCEL_AddCode` keeps the first and bumps later duplicates); monstats `NextInClass` = `cr_lancer8` (1 cell) and
    the `Sk*mode` cells naming a `seq_*` value repeated in `monseq.txt` store the first occurrence's ordinal (name
    links, data/0001 §6). (fn:EXCEL_AddCode@0x006BD230, fn:EXCEL_AddNameIfAbsent@0x006BD5A0)
- [C] **String keys** (type 0x16, `namestr`, `NameStr`…): the cell (≤ 256 bytes) goes to `fn:STRTABLE_KeyToIndex@0x006117B0`
  (ECX = key), which searches patchstring → expansionstring → string ([data/0003](0003-string-tables.md)) and maps a
  result of 0 to **5382**. (0x006BDEE5–0x006BDEED) Each part is exercised by named cells of the 2 344 present ones:
  - the order: keys in two tables resolve to the earlier one, patchstring over string (12 cells, e.g. weapons
    `namestr` `9bl`), patchstring over expansionstring (4, e.g. `7wa`), expansionstring over string (77, e.g. `ob1`);
  - 0 → 5382: every blank cell (776) and the 15 non-blank keys found in no table (misc `namestr` `hpo`, `mpo`,
    `hpf`, `mpf`, `rps`, `rpl`, `bps`, `bpl`; monstats `NameStr` `Bunny`, `Act 5 Hireling 1hs`/`2hs`, `Injured
    Barbarian 1`–`3`, `Worldstone Effect`);
  - one explained exception: monstats `uberandariel` `NameStr = Lilith` stores 5382, but `Lilith` is **entry 1154 of
    the shipped `eng` `patchstring.tbl`** (index 11154), reached by the game's probe at step 28 of 1179, and is in
    neither `expansionstring.tbl` nor `string.tbl`. It is not entry 0, so the rule does not explain it (Open
    questions).
  - [I] `STRTABLE_GetByKey` also returns 0 for entry 0 of `string.tbl` (key `WarrivAct1IntroGossip1`), so that key
    would compile to 5382; no cell uses it. (fn:STRTABLE_GetByKey@0x00524D30)
- [I] **Fields with no `.txt` column** (archivist backlog 2026-10-11), all seen 0 in every record:
  - items `+0x0F0` is **`gemoffset`** (s32 descriptor entry, every cell `0`); `GEMS_Load` then overwrites it at run
    time: records 0 … nGems−1 get −1 and each gem's item gets its `gems` row (§3). `+0x114` is **`missile`** and
    `+0x122` **`subtype`** (u8 each), descriptor entries whose columns no shipped `.txt` has; `subtype` is read at
    `0x005853D6`. `+0x12E` and `+0x123` have no descriptor entry and no reader or writer was found: padding.
  - monstats `+0x02A` (s16) = first `MonEquip` row of the class, −1 if none (`MONEQUIP_Load`); `+0x036`/`+0x038`
    (s16 each) = walk/run values derived at load (`sub_00650F00_MonStatsSpeeds`); `+0x04A`/`+0x04B` (u8 each) = length
    of the class chain and the record's position in it (`sub_00651040_MonClassChain`). `+0x00A` (u16) and `+0x00F`
    bits 5–7 (bits 29–31 of the `+0x00C` flags) have no descriptor entry and no writer was found: padding.
  - levels `+0x16E` and `+0x1BE` are two `wchar[40]` buffers, the localised `LevelName` and `LevelWarp` text written
    by `DRLG_LoadLevels` after the load; `+0x16D` and `+0x20E..+0x20F` are alignment. `+0x00A` has no descriptor
    entry and no writer was found: padding. (TCEx `+0x030` and levels `+0x033..+0x035` were already answered:
    [items/0001 §1](../items/0001-tc-resolution.md), [monsters/0001 §3](../monsters/0001-level-pool.md).)
- [I] **Two descriptor facts the data cannot show:** `levels.txt` `camt1`..`camt4` are four descriptor entries that
  all write `+0x0DC` (s16), so the compiler stores the last `camt` column present in `+0x0DC` and never writes
  `+0x0DE..+0x0E3`, while the critter code reads `+0x0DC + 2k` (`0x0046C524`); the stock cells are all blank, so
  nothing differs in a stock run. `levels` `Id` is compiled as a u8 (type 4); `+0x001` is never written.
- [I] **`LvlTypes` `Expansion`** is compiled as an s32 (type 2, `+0x784`) and read as a dword
  (`cmp dword [rec + 0x784], 0` at `0x0061FB97`); `Act` is a u8 (type 4, `+0x780`), read as a byte at `0x0061EB19`
  and `0x006429EC`.
- [I] **MonStats2 `+0x025`** is computed by the compiler, not a column: the component-list callback
  `sub_00657010_MonStats2CompList`, when it handles list 15 (`S8v`), stores Σ over the 16 lists of
  `count − 1` for each count ≥ 2, capped at 254. `[C]` for the stock values by the archivist's diff of all 609 records
  ([MonStats2](../../tables/MonStats2.md)). (fn:sub_00657010_MonStats2CompList@0x00657010)

## Leads used

- None outside our docs. [excel-bin.md § Cell encoding rules](../../formats/excel-bin.md#cell-encoding-rules) (the
  archivist's data rules) gave the questions; every claim above was read from the code, then checked against
  `excel_bin.py survey`.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x006BCE20` | `EXCEL_MapColumns` | header → descriptor index; appends unmatched entries; returns the total | C |
| `0x006BD780` | `EXCEL_ParseTxt` | two passes: link registrations, then cells; then the missing-column defaults | C |
| `0x006117B0` | `STRTABLE_KeyToIndex` | type 0x16 converter: `STRTABLE_GetByKey`, 0 → 5382 | C |
| `0x00631530` | `sub_00631530_ItemCalcCell` | item calc callback (type 0x19): no cell or an empty expression → −1, else the offset of the compiled expression | I |
| `0x00636B70` | `GEMS_Load` | `gems` table; fills items `+0x0F0` | I |
| `0x006372C0` | `GEMS_GetRecord` | `gems` row by index, NULL for −1 or out of range | I |
| `0x00650F00` | `sub_00650F00_MonStatsSpeeds` | monstats `+0x036`/`+0x038` at load | I |
| `0x00651040` | `sub_00651040_MonClassChain` | monstats `+0x04A`/`+0x04B` at load | I |
| `0x006510C0` | `MONSTATS_GetClassChainPos` | `(id, &count, &pos)` → pos, from `+0x04A`/`+0x04B` | I |
| `0x00657010` | `sub_00657010_MonStats2CompList` | monstats2 list column callback (type 0x17): count, `compcode` rows, and `+0x025` | I |
| `0x00659E60` | `MONEQUIP_Load` | `monequip` table; fills monstats `+0x02A` | I |

## Walkthrough

### 1. Column map and the defaults pass

```c
// fn:EXCEL_MapColumns@0x006BCE20 (trimmed): map[] gets one entry per .txt column, then the unmatched descriptor entries
for each descriptor entry e (until type 0): bucket[hash(e.column)] += {hash, e}      // 0x00413CE0
for each .txt header h, col = 0..:
    for each candidate c in bucket[hash(h)]:
        if c.hash == hash(h) && _strnicmp(h, c.e.column) == 0:
            c.hash = 0;  map[col] = index(c.e);  goto next     // 0x006BD00F: a second h finds nothing
    map[col] = 0x7FFF
next:
n = nColumns; for each candidate c with c.hash != 0: map[n++] = index(c.e)
return n
```

```c
// fn:EXCEL_ParseTxt@0x006BD780, per row, after the row's cells (0x006BDFA0–0x006BE031)
for (k = nColumns; k < n; k++) {
    e = &desc[map[k]]; p = record + e->offset;
    switch (e->type) {                         // jump table 0x006BE128, index type − 1
      case 1,4,5,6,7,0x0C,0x10:  *(u8 *)p  = 0;    break;   // string: first byte; u8 fields
      case 2,8,9,0x0A,0x12:      *(u32 *)p = 0;    break;   // s32; 4-char code; code register (dword)
      case 3,0x0E,0x11,0x16:     *(u16 *)p = 0;    break;   // s16; registers (word); string key
      case 0x0B,0x13:            *(u32 *)p = -1;   break;   // code / name lookup, dword
      case 0x0D,0x15:            *(u8 *)p  = 0xFF; break;   // code / name lookup, byte
      case 0x0F,0x14:            *(u16 *)p = 0xFFFF; break; // code / name lookup, word
      case 0x17,0x18,0x19:       if (e->link) e->link(/*ECX*/ NULL, /*EDX*/ record, e->offset, e->len, row, k); break;
      case 0x1A:                 break;                      // bit flag: the record was memset 0
    }
}
```

- [I] The record buffer is `memset` 0 before parsing (data/0001 §1), so a 0 default and "not written" give the same
  byte. The −1 defaults are real writes. The calc callback `0x00631530` writes −1 when ECX is NULL (`0x00631552`) and
  when the expression compiler `0x006C1AE0` returns ≤ 0, so a blank calc cell and a missing calc column are both −1.

### 2. Cell types (second pass, `0x006BDB50` loop)

The pass dispatches on a byte class at `0x006BE0D7 + type`:

| class | types | conversion |
|---|---|---|
| 0 | 1, 7 | string: copy up to `len` bytes, NUL-terminate (the field is `len + 1` bytes) |
| 1 | 2–6, 8, 0x1A | integer, as in the summary |
| 2 | 9 | 4-character code: first 4 bytes, missing ones spaces, blank `"    "` |
| 3 | 0x0A, 0x0C, 0x0E, 0x10–0x12 | skipped here (registered in the first pass) |
| 4 | 0x0B, 0x0D, 0x0F | code lookup: 4-byte space-padded key → `EXCEL_FindCode(link)` → dword / byte / word |
| 5 | 0x13, 0x14, 0x15 | name lookup: ≤ 31 bytes → `EXCEL_FindName(link)` (lower-cased) → dword / word / byte |
| 6 | 0x16 | string key: ≤ 256 bytes → `link(ECX = key)` → word |
| 7 | 0x17, 0x18, 0x19 | callback `link(ECX = cell, EDX = record, offset, len, row, col)` |

- [I] The first pass (only when a mapped column has a registration type 0x0A/0x0C/0x0E/0x10–0x12) registers keys
  in the links before any lookup: codes through `EXCEL_AddCode` (stored as the code, or as the u8/u16 index, fatal
  above 255/65535), names through `EXCEL_AddName` (type 0x10, the string is also stored) or `EXCEL_AddNameIfAbsent`
  (0x11/0x12, index stored as word/dword). (0x006BD99F, 0x006BDA34, 0x006BDA74)
- [I] Callbacks run in `.txt` column order. `sub_00657010_MonStats2CompList` computes `+0x025` while it handles
  list 15, so the sum covers the lists already parsed; in `monstats2.txt` `S8v` is the last of the sixteen. (fn:sub_00657010_MonStats2CompList@0x00657010)

### 3. Runtime fillers of no-column fields

```c
// fn:GEMS_Load@0x00636B70, after DATATBLS_LoadTable("gems", 0xC0) (0x00637245–0x00637295)
for (g = 0; g < nGems; g++) {
    g_pItems[g].gemoffset = -1;                 // item record g, not the gem's item: the first nGems item records
    if (gems[g].item >= 0)                      // gems +0x28: `code` resolved through g_ItemCodeLink (type 0x0B)
        g_pItems[gems[g].item].gemoffset = g;   // items +0x0F0
}
```

- [I] Readers take `+0x0F0` only after an item-type test (`ITEMS_UnitIsType`, e.g. `0x004866CF`, `0x0055C2FE`) and
  pass it to `GEMS_GetRecord`, so the −1 written on the first nGems records (weapons) is never used.
  (0x004866E1, 0x0055C321, 0x0062C4C0)
- [I] `MONEQUIP_Load` (`0x0065A070`–`0x0065A0F7`): every monstats `+0x02A` = −1, then for each `monequip` row r whose
  `monster` is a valid record and whose class still has −1, `+0x02A` = r.
- [I] `sub_00650F00_MonStatsSpeeds` (from `MONSTATS_Load` at `0x00653890`): a `BaseId` outside the table is replaced by
  the record itself; `+0x036` = a value from the animation lookup `0x0066A9B0` (mode argument 2) scaled by
  `Velocity`/the base record's `Velocity`, clamped to 0x7FFF; `+0x038` likewise with mode argument 15 and `Run`
  (records below 410 start from half the base record's `+0x036`). Its meaning belongs to `monsters/*`.
- [I] `sub_00651040_MonClassChain` (from `0x00653884`): walks `BaseId` → `NextInClass` (≤ 256 steps) and stores the
  chain length at `+0x04A` and the record's position at `+0x04B`; `MONSTATS_GetClassChainPos` reads them.
- [I] `DRLG_LoadLevels` (`0x0061DA70`–`0x0061DAD4`): per record, `memset(+0x16E, 0, 80)`, `memset(+0x1BE, 0, 80)`, copy
  `STRTABLE_GetStringByKey(LevelName)` (`+0x0F5`) into `+0x16E` and of `LevelWarp` (`+0x11D`) into `+0x1BE` (40
  characters each, `+0x1BC`/`+0x20C` forced 0). Then the `+0x033..+0x035` counts.
- [I] `subtype` (`+0x122`) is read at `0x005853D6` as an index into a 21-entry table at `0x00732EB0` (12 bytes each:
  handler, percent, argument): the handler runs when `rand % 100` (draw from the seed at `+0x20` of the object in
  EDI) is below the percent. Every shipped item has `subtype` 0, so entry 0 is used. Not followed further.

### 4. Searches behind "padding"

- Descriptor coverage: every descriptor entry of items (`0x006315D0`–`0x00633357`), monstats (`0x00651210`–
  `0x0065384C`) and levels (`0x0061C540`–`0x0061DA25`) was listed from the disassembly, with widths by type; the bytes
  named padding above are covered by no entry.
- Writers: no `mov` store with displacement `+0x12E`, `+0x122` or `+0x123` exists in `.text`; stores with `+0x00A`,
  `+0x02A`, `+0x036`… within 30 instructions after a load of `g_pMonStats` or a call to `MONSTATS_GetRecord` are
  only the fillers above; for levels the same search (`+0x00A`, `+0x16D..+0x20F`) after `g_pLevels` /
  `LEVELS_GetRecord` finds only `DRLG_LoadLevels` (one other hit, `0x0054FCDE`, reads another structure).
- Readers: the same window after `ITEMS_GetRecord`/`ITEMS_GetByCode`/`g_pItems` finds no access to `+0x12E` or
  `+0x114`; no `test byte [r + 0xF], 0x20/0x40/0x80` exists in `.text`, and the 14 `test dword [r + 0xC], 0x40000000`
  sites sit in client code on other structures. Records reached through a cached pointer (unit → monster data →
  record) are not covered by this window: that is the limit of the padding claims.

## Plan 0038 batch S1b (2026-10-16)

Static batch S1b of [plan 0038](../../plans/0038-inferred-claims-sweep.md), the compiler rows of
[inventory data-excel](../../plans/0038-inventory/data-excel.md). No session was played; method and log manifest as in
[data/0001 § Plan 0038 batch S1b](0001-excel-loader.md#plan-0038-batch-s1b-2026-10-16). The checks are
`python3 -I tools/sweep_s1b.py compile` and `survey`. Where a statement above is tagged inferred and this section
raises it, the tag and the second source given here are the current ones.

**The compiler's own output.** In run:2026-10-15-cube-saves the pinned game compiled every table under `-direct -txt`.
88 of the 90 `.bin` it wrote are byte-identical to the shipped files; `cubemain.bin` is the probe's own table and
`monstats.bin` differs in two bytes. `excel_bin.py survey` explains every cell of the shipped tables (66 laid-out
tables, 11 434 records, 848 353 cells, 0 unexplained, 2 explained) and of the game-compiled ones (0 unexplained, 1
explained). So the survey's cell rules are now checked against this binary's compile, not only against files someone
else compiled.

- **The `Lilith` question (Open questions) answered.** The two differing `monstats.bin` bytes are record 707
  (`uberandariel`) `NameStr` at `+0x006`: the game compiled 11154 (`patchstring` entry 1154, `Lilith`), the shipped
  file holds 5382. So the converter rule holds for this cell too: the pinned compiler, given this install's string
  tables, stores the key's index. The shipped `monstats.bin` was compiled against string tables without `Lilith`; that
  part stays an inference about how the file was made. [C] for the converter on this cell
  (fn:STRTABLE_KeyToIndex@0x006117B0, run:2026-10-15-cube-saves). The survey's one explained exception is gone on the
  compiled tables.
- **data/excel row 55** (spec L571, the `deu`/`fra` `string.tbl` have fewer entries; the stored indices are the English
  ones) **raised.** [C] `deu` and `fra` `string.tbl` hold 5 322 entries, `eng` 5 391. With the `deu` (or `fra`) tables
  in place of `eng`, 1 505 (1 506) of the 4 548 string-key cells of the laid-out tables would compile to another index,
  while the `eng` tables explain all of them: rule 2. (fn:STRTABLE_KeyToIndex@0x006117B0)
- **data/excel row 61** (spec L620, J2c: a code lookup takes ≤ 4 bytes, pads with spaces, stores `FindCode` at the field
  width) **raised in part.** [C] for the word code lookups, the only width with present cells: 4 549 cells, 475 shorter
  than 4 characters (padded), 12 longer (cut), all equal in the game-compiled tables. **Remainder d-edit:** the byte
  (`0x0D`) and dword (`0x0B`) conversions of a present cell; no stock cell has one (their absent-column defaults are J3,
  `[C]`). (fn:EXCEL_FindCode@0x006BD130)
- **data/excel row 62** (spec L624, J2d: a name lookup takes ≤ 31 bytes, stores `FindName` at the field width)
  **raised in part.** [C] for the dword (610 cells) and word (126) name lookups, 11 of them in another case than their
  key. **Remainder:** the byte width (`0x15`) has no present cell (d-edit); the 31-byte cut has no cell over 31 (S1e's
  c-emu data-excel row 16). (fn:EXCEL_FindName@0x006BD3C0)
- **data/excel row 63** (spec L628, J2f: callbacks get `(cell, record, offset, len, row, col)`) **raised in part.** [C]
  what the callbacks write: the game-compiled records and the four `*code.bin` pools that the calc callbacks build are
  byte-identical to the shipped ones, so the cell and the record offset reach the callback as the shipped data needs.
  **Remainder d-none:** the `row` and `col` arguments; no stock output depends on them. (fn:EXCEL_ParseTxt@0x006BD780)
- **data/excel row 67** (spec L672: the first pass registers keys before any lookup; overflow is fatal; callbacks run in
  `.txt` column order) **raised in part.** [C] registration before lookup: 442 `monstats` `NextInClass` cells name a
  later row and resolve, in the game-compiled table. **Remainder d-none:** the overflow fatal (no stock table reaches
  255/65535), and the callback order (spec J2f–J3: no stock row distinguishes the two orders). (fn:EXCEL_ParseTxt@0x006BD780)
- **data/excel row 68** (spec L675: the record is zeroed before the parse; the −1 defaults are real writes) **raised.**
  [C] The no-column and padding bytes listed in § Answer are 0 in every record of the game-compiled files (they are the
  shipped bytes), and the absent-column −1 defaults (J3, 23 855 cells) are present in them: a write. (fn:EXCEL_ParseTxt@0x006BD780)

## Plan 0038 batch S1e (2026-10-17)

Static batch S1e of [plan 0038](../../plans/0038-inferred-claims-sweep.md), rows 56, 60, 64 and 66 of
[inventory data-excel](../../plans/0038-inventory/data-excel.md). No session was played. Method: the converters under
Ghidra's p-code emulator against `tools/sweep_s1e.py`'s models ([ADR-0015](../../adrs/0015-emulated-reproduction.md)),
[run:2026-10-17-sweep-emu](experiments.md#run2026-10-17-sweep-emu). `EXCEL_ParseTxt` (family `parsetxt`, 400 calls)
ran on a synthetic parsed `.txt` (header and NUL-separated cells, rows ended by `\n`; the columns shuffled against the
descriptor) and a 13-entry descriptor of the integer (2, 3, 4, 5, 8, 0x1A), code-lookup (0x0B, 0x0D, 0x0F) and
name-lookup (0x13, 0x14, 0x15) types, with a scratch code link and name tree; no registration type, so the first pass
and its allocations do not run, and every descriptor entry has a column, so the defaults pass does not run. Read set:
the descriptor, text, links and records (spec and case memory); the type → class bytes and jump tables
(0x006BE08C–0x006BE13F, `.text`); `FUN_00413CE0`'s name-hash table 0x006CEE30, `STR_ToLowerN`'s table and
`BITFIELD_Set`/`Clear`'s mask tables 0x006CE274–0x006CE2FF (all `.rdata`); `__locale_changed` and the SSE2 flag (spec;
both flag values run, identical output); `strncpy`'s write-only store to 0x007788D8. Where a statement above is tagged
inferred and this section raises it, the tag and the second source given here are the current ones.

- **Row 60** (spec L618, J2b: the integer converter sign-extends each byte, so a byte ≥ 0x80 adds a negative digit)
  **raised.** [C] 2 312 integer cells with bytes ≥ 0x80 among digits, signs, spaces and letters, stored at every
  width; `value·10 + (s8 byte − 0x30)` per byte after an optional leading `-`, no validation, truncation to the field;
  type 5 skips an empty cell (60 cases) and type 0x1A sets or clears its bit. The negative control (bytes read
  unsigned, 0 for a lookup miss) differs in 399 of 400 calls. The `movsx` is cited from the disassembly (0x006BDE20, ADR-0015 condition 5).
  (fn:EXCEL_ParseTxt@0x006BD780, 0x006BDE20, fn:BITFIELD_Set@0x00410B10, run:2026-10-17-sweep-emu)
- **Row 66** (spec L665, a non-blank key that matches nothing stores −1) **raised.** [C] 1 931 code-lookup cells and
  1 258 name-lookup cells that match nothing store −1 at the field width (`0xFFFFFFFF`, `0xFFFF`, `0xFF`); blank code
  cells find the `"    "` key (378), and longer keys are cut to 4 (codes) and 31 (names; 1 058 cells over 31 bytes)
  before the lookup. (0x006BDD82, 0x006BDDE7, run:2026-10-17-sweep-emu)
- **Row 64** (spec L629, the item calc callback stores −1 for a blank cell or an expression that fails to compile)
  **raised.** [C] 420 calls of `sub_00631530_ItemCalcCell` (ECX = text or NULL, EDX = field offset, stack: record and
  three more arguments; `ret 0x10`): a NULL cell (13) and a failed compile (97) store −1; a compiled one (190) appends
  its bytes to `itemscode` (`g_DataTables + 0x98`, size `+0x9C`) and stores the old size; offset 0 (120) stores
  nothing. Family `compile`, both SSE2 flag values. (fn:sub_00631530_ItemCalcCell@0x00631530,
  fn:sub_006118B0_CalcPoolAppend@0x006118B0, run:2026-10-17-sweep-emu)
  *Review note (architect, 2026-10-17):* the scratch pool's capacity (0x10000) is above every append, so the growth
  loop of `CalcPoolAppend` (0x006118D0–0x006118FE: capacity + 0x400, then the pool allocator 0x0040B4B0) is not
  reached; the `[C]` covers the append without growth.
- **Row 56** (spec L574, I2: `string.tbl` entry 0's key would compile to 5382) **raised.** [C] `STRTABLE_KeyToIndex`
  on `WarrivAct1IntroGossip1` (and the synthetic `string`'s entry-0 key) returns 5382, as on the empty key and the keys
  found nowhere; every other key returns its index (family `strings`, [data/0003 § S1e](0003-string-tables.md#plan-0038-batch-s1e-2026-10-17)).
  (fn:STRTABLE_KeyToIndex@0x006117B0, run:2026-10-17-sweep-emu)

## Plan 0038 batch S1f (2026-10-17)

Static batch S1f of [plan 0038](../../plans/0038-inferred-claims-sweep.md), the c-emu rows of the
[inventory § 2.6 S1f table](../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews). No session was
played. Method: the function runs under Ghidra's p-code emulator against `tools/sweep_s1f.py`'s models, under
[ADR-0015](../../adrs/0015-emulated-reproduction.md): [run:2026-10-17-sweep-emu2](experiments.md#run2026-10-17-sweep-emu2).
Every memory spec guards the fatal path (0x00408090, 0x00408A60, 0x00681E09) and the pool allocator's entries
(0x0040B4B0, 0x0040B430, 0x0040B480), and no case stopped, so no claimed branch was reached through either (review
condition (a)). Where a statement above is tagged inferred and this section raises it, the tag and the second source
given here are the current ones.

`EXCEL_ParseTxt` (family `parsetxt2`, 300 calls, 618 rows; both values of the CRT SSE2 flag, identical outputs) ran on
a synthetic parsed `.txt` and a 45-entry descriptor (record 0xA0 bytes, random prefill dumped after the call). 17
entries may have a column (the integer, flag, code- and name-lookup types of S1e, plus three type `0x19`, one `0x17`
and one `0x18` entry whose callback is `fn:sub_00631530_ItemCalcCell@0x00631530`, the item calc cell callback S1e
reproduced, used here as an admitted probe: S1e ruling 2); each case keeps about 60 % of them, in a shuffled order,
with unknown headers mixed in (221 cases). 22 entries never have a column: one of every type the parse pass would
convert through a link the run does not build or register (1, 7, 9, 0x0A, 0x0C, 0x0E, 0x10–0x12, 0x16, a second
0x1A) and four groups of absent entries sharing one field (OvA: 2, 0x13, 0x19; OvB: 0x19, 2; OvC: 0x15, 5, 0x17; OvD:
0x14, 3, 0x0B), so the field shows which ran last. Six more form three pairs of a present column and an absent entry
on one field (OvP: column type 2, absent 0x19; OvQ: column 0x19, absent 0x13; OvR: column 0x19, absent 2). Calc cells
hold compiler texts (S1e's random expressions and fixed valid and invalid ones); the itemscode pool
(`g_DataTables + 0x98`, case memory) has capacity 0x10000 and the pool reached 178 bytes at most, so
`CalcPoolAppend`'s growth loop and its allocator call are not reached (and are guarded: no case stopped). No
registration column is present, so the first pass (`EXCEL_AddCode`, which may grow its array) does not run. Read
set: S1e's `parsetxt` and `compile` sets, plus the defaults jump table 0x006BE128 (26 entries, `.text`), which S1e
never reached. Spec writes on image addresses: the security cookie (no output depends on it), `__locale_changed`
(writer scan, S1e) and the SSE2 flag (both values run): S1e ruling 3 (a), (c), (b); the itemstatcost name link
`g_DataTables + 0xBD0` (0x0096C800) and the pool header are arguments.

- **Row 65** (spec J3 table L645–L649, the absent-column defaults no stock column exercises; 5 statements) **raised.**
  [C] After each row's last cell every absent entry is written through the jump table at 0x006BE128 at its exact
  width, the bytes around it unchanged: types 5, 7, 0x0C, 0x10 write the byte 0; 8, 0x0A, 0x12 the dword 0; 0x0E,
  0x11 the word 0 (L645); 0x0B and 0x13 the dword −1 (L646); 0x15 the byte `0xFF` (L647); 0x17 and 0x18 call the
  entry's callback with ECX = 0 (no cell) and the record and field offset in EDX and the first stack argument, so the
  probe writes −1 at record + offset (421 and 120 absent calls; L648); 0x1A leaves the byte untouched, the prefill showing it (409;
  L649). Every type 1–0x1A was absent in 113 to 1 261 rows, and all 618 rows reproduce. The scope of L648 is the
  arguments the probe uses; the length, row and column pushed with them (0x006BE003–0x006BE01A) stay a code reading,
  and L649's "the record was zeroed" is the caller's (data/0001 § 1), not this run's. (fn:EXCEL_ParseTxt@0x006BD780,
  0x006BDFBE, 0x006BE128, run:2026-10-17-sweep-emu2)
- **Row 69** (spec J2f–J3 note L683, callback order: `.txt` columns, then the absent entries) **raised.** [C] In all
  300 calls the present callback columns ran when their column was reached (the pool holds their compiled bytes in
  shuffled header order, 3 092 present calc cells) and the absent entries after the row's last cell, in descriptor
  order: in OvP, OvQ and OvR the absent entry's default overwrote the present cell's value in every row, and in OvA–OvD
  the last absent entry in descriptor order decided the field. Two negative controls fail: absent entries before the
  cells (300 of 300 calls differ) and present cells in descriptor order (290). `EXCEL_MapColumns` appends the
  unmatched entries in descriptor order (0x006BCFB0–0x006BCFDC); a header the descriptor lacks maps to 0x7FFF and its
  cell is skipped. (fn:EXCEL_ParseTxt@0x006BD780, fn:EXCEL_MapColumns@0x006BCE20, run:2026-10-17-sweep-emu2)
- [I] The first pass's gate and loop count only the `.txt` columns (`mov eax, [ebx+0xc]` at 0x006BD7FE, loop to
  0x006BD847), so an absent registration entry (0x0A, 0x0C, 0x0E, 0x10–0x12) is never registered, only defaulted. In
  this run no registration column was present and the pass did not run (the registration entries had no link, and no
  read through one was traced). (0x006BD7FE, 0x006BD85F)

## Data touched

- `fmt:excel-bin#bin` (all laid-out tables), `tbl:Weapons.txt:gemoffset` (`+0x0F0`), `tbl:Levels.txt:LevelName`,
  `tbl:Levels.txt:LevelWarp`, `tbl:Levels.txt:camt1`, `tbl:Levels.txt:Id`, `tbl:LvlTypes.txt:Expansion`,
  `tbl:LvlTypes.txt:Act`, `tbl:MonStats.txt:BaseId`, `tbl:MonStats.txt:NextInClass`, `tbl:MonStats.txt:Velocity`,
  `tbl:MonStats.txt:Run`, `tbl:MonStats2.txt:HDv`…`S8v`, `gems.bin` `+0x28` (item index), `monequip.bin` `+0x00`.

## Dead ends

- The archivist's `+0x122` was read as a u16; the descriptor has a u8 `subtype` at `+0x122` and nothing at `+0x123`.
- Ghidra could not follow the defaults pass (`0x006BDFBE`, "too many branches"); the jump table had to be read from
  the bytes at `0x006BE128`.

## Open questions

- The `Lilith` cell (monstats `uberandariel` `NameStr`): `Lilith` is entry 1154 of the shipped `eng` `patchstring.tbl`
  (index 11154; the game's probe finds it at step 28 of `max_probes` 1179) and in no other table, so the converter
  would store 11154, not 5382. The shipped `.bin` was compiled against string tables that lacked the key `[L]`.
  Nothing in the code explains it; it stays the one explained mismatch of the survey.
- Whether any reader reaches monstats `+0x00A` or bits 29–31 through a cached record pointer. A data breakpoint on
  one record's `+0x00A` during a game would settle it.
- What `subtype`'s 21 handlers do (`0x00732EB0`) and which caller reads it (`0x005853D6`): `items/*` if it matters.
