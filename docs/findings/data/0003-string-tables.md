# 0003 — String tables at run time

> **Subsystem:** data/strings
> **Question:** How does the game load the `.tbl` string tables, turn a stored string index into text, look a key up, and react to a bad or missing table?
> **Date:** 2026-10-12, run 2026-10-15   **Plan:** none at first (backlog archivist → reverser 2026-10-12, "run-time `.tbl` use"; static read alongside plan 0013 Phase 1); [plan 0028](../../plans/done/0028-data-strings.md) Phase 1 for the run   **Status:** open (the lookups `[C]` by [run:2026-10-15-strings](experiments.md#run2026-10-15-strings); the crc check `[C]` by [run:2026-10-12-d2s-io](../save/experiments.md#run2026-10-12-d2s-io); the 5382 rule `[C]` by data, plan 0015 Phase 2; the fallbacks and fatal paths `[I]`)

Static reading, then [run:2026-10-15-strings](experiments.md#run2026-10-15-strings): `tools/tbl.py` (`GameStrings`, `check`)
models the lookups below and reproduces 336 logged index lookups and 3 928 logged key lookups, expansion and classic,
with 0 mismatches (§ Run). Module `.\StrTable\strtable.cpp` (string `0x006E0334`); the byte layout is
[tbl.md](../../formats/tbl.md) and is not repeated. "Entry" is a position in a file's `index` array, "node" a hash node.
Names are ours.

## Answer (summary)

- [I] **Loading.** `fn:STRTABLE_LoadAll@0x005259C0` (EDX = language code or NULL for the configured one, and one stack
  argument, `ret 4`) loads `data\local\lng\<lang>\string.tbl`, then `patchstring.tbl`, then `expansionstring.tbl`
  **when the stack argument is non-zero** (0x00525E11), each through `fn:STRTABLE_LoadFile@0x00525920`. It is
  reference-counted (`0x008829D8`): a second call only increments the count. Before the tables it loads the font map
  `data\local\font\<charset>\default.map` (`fn:UNICODE_LoadFontMap@0x00527790`, § Text conversion). For every hash node it converts
  the node's value into a 16-bit-per-character string (`fn:UNICODE_Utf8ToUtf16@0x00526320`, § Text conversion) and keeps one pointer
  per node. (0x00525AF5, 0x00525B05–0x00525F5C)
- [C] **`expansionstring.tbl` loads whenever `d2exp.mpq` exists, also for a classic game.** The three callers
  (0x004359F2, 0x00441B91, 0x0044B911) push `sub_00408F20_HasExpansionMpq()` as that stack argument (the
  `call 0x004FAC80` between the push and the call is a stub returning 0, which becomes ECX), and they run at program
  level, before any game. Run: every line of both sessions, the classic one included, has the three tables loaded
  (`ld = "spx"`) from the main menu on, and the classic session resolved 21796, 22730 and 22732 through
  `expansionstring` (character-select text). (0x00408F20, 0x00525E11,
  [run:2026-10-15-strings](experiments.md#run2026-10-15-strings))
- [C] **`crc` is checked.** `STRTABLE_LoadFile` recomputes `fn:STRTABLE_Crc16@0x00525020` over
  `[string_start, file_size)` (init `0xFFFF`, table at `data:g_Crc16Table@0x007301D8`, `table[1]` = `0x1021`, MSB first)
  and stops the game with a fatal error when it differs from header `+0x00`. Run: the three stock tables check at
  every game entry; a loose `patchstring.tbl` (under `-direct`) with one value byte changed and its crc recomputed
  by the CRC-16/CCITT-FALSE model loaded with the logged computed crc equal to the model's `0x8E1C`; the same file
  with the stock crc halted the game at start-up ("Unrecoverable internal error … failed at (206)", stack from
  `0x0052596E`, the fatal call after the compare). (0x0052594B–0x00525973, run:2026-10-12-d2s-io)
- [I] It also fatals when any node's `key_offset` or `string_offset` is ≥ `file_size` (not exercised).
  (0x00525978–0x005259B0)
- [C] **Index → text** (`fn:STRTABLE_GetByIndex@0x00524A30`, u16 index in CX): index ≥ 20000 → entry `index − 20000`
  of `expansionstring` if it is loaded, else the index is replaced by 11078 and handled as below; index ≥ 10000 with
  `patchstring` loaded → entry `index − 10000` of `patchstring`; otherwise entry `index` of `string`. Inside a file
  (`fn:STRTABLE_EntryToString@0x00524930`) an entry ≥ `count` is replaced by entry **500**, then `index[entry]` must
  name a used node (fatal otherwise) and that node's converted value is returned. So the bases are 0 / 10000 / 20000 as
  tbl.md found, with two fallbacks the data cannot show (11078, entry 500). Run: 336 index lookups (201 distinct
  indices: 269 in `string`, 38 in `patchstring`, 29 in `expansionstring`), table, entry, node and text as modelled.
  The two fallbacks and the fatal checks were not reached and stay `[I]`. ([run:2026-10-15-strings](experiments.md#run2026-10-15-strings))
- [C] **Key → index** (`fn:STRTABLE_GetByKey@0x00524D30`, stdcall: key, out text): requires `string` and
  `patchstring` loaded (fatal 0x2BA / 0x2BB otherwise, `[I]`) and a non-NULL key (fatal 0x2C0, `[I]`). An empty key
  returns 0 and the empty text `data:g_EmptyText@0x008829E8` without a search. Otherwise it searches **`patchstring`,
  then `expansionstring` (if loaded), then `string`**, returning `10000 + entry`, `20000 + entry` or `entry`. A key
  found nowhere returns **0** and a placeholder text cached per key (`fn:sub_00524AC0_NotXlated@0x00524AC0`, a list at
  `0x008829B0`): the key followed by `data:g_szNotXlatedSuffix@0x00730520` = `" -not xlated call ken w"`, converted
  with a limit that drops its last character (§ Text conversion), so `"funeralpire"` gives `"funeralpire -not xlated call ken "`.
  Run: 3 928 key lookups (1 964 distinct keys per session, 79 found nowhere, 1 empty), index, every table searched
  and the text as modelled. ([run:2026-10-15-strings](experiments.md#run2026-10-15-strings))
- [C] **The excel `.bin` value 5382** comes from the excel field converter `fn:STRTABLE_KeyToIndex@0x006117B0`: it
  calls `STRTABLE_GetByKey` and replaces a result of 0 (empty key or key not found) by `0x1506` = 5382. Corroborated
  by data behaviour (evidence rule 2): `tools/excel_bin.py survey` reproduces every string-key cell of the laid-out
  tables with patch → expansion → string and blank/unknown → 5382 (2 344 present cells: 776 blank and 15 non-blank
  keys found in no table store 5382, and each precedence pair is exercised; the one explained exception, monstats
  `Lilith`, is entry 1154 of `patchstring.tbl`, not entry 0, and stays `[L]` in [data/0004](0004-cell-converters.md)). How the compiler calls it (type 0x16,
  ECX = the cell, a missing column stores 0 without the call) is in data/0004. (0x006117B9–0x006117C6; registered as
  a field callback at 0x006134CD, 0x00613F96, 0x00614467)
- [C] **Hash lookup** (`fn:STRTABLE_FindInTable@0x00524C60`; EDI = table file, stack: text array, key, out): home slot = `fn:STRTABLE_Hash@0x005249E0`(key) %
  `hash_size`, the PJW/ELF hash of tbl.md computed on **signed** chars (`movsx`); then it examines at most
  `max_probes` (`+0x0D`) nodes, stepping `slot = (slot + 1) % hash_size`. An unused node is **skipped, not a stop**;
  only `max_probes` ends the search. A used node matches on an exact, case-sensitive `strcmp` of the key and returns
  the node's `entry` (`+0x01`); a NULL converted text there is fatal (0x296, `[I]`). The give-up return is `0xFFFF`.
  Run: every search's home slot, node count and result as modelled (9 456 searches: 1 770 hits after more than one
  node, the longest 5 159 nodes, `"not used"` in `string`; 5 688 misses, each over all `max_probes` nodes, through
  unused ones); the signed hash shows on three keys with a byte ≥ 0x80 (`"\x80\x02"`: patchstring home 361, unsigned
  869). (0x00524C7D–0x00524CDC, [run:2026-10-15-strings](experiments.md#run2026-10-15-strings))
- [I] **Missing tables.** `FILE_LoadWhole` returns NULL for a file it cannot open (after logging
  `"Error opening file: %s"`), and `STRTABLE_LoadFile` reads the header through that pointer without a test, so a
  missing `string.tbl`, `patchstring.tbl`, or, with `d2exp.mpq` present, `expansionstring.tbl` ends in an access
  violation at 0x0052593E. There is no fallback to `eng`. The fatal paths after a NULL return in `STRTABLE_LoadAll`
  (0x1C3, 0x1F6) are unreachable for that reason. With the shipped files, a `pol`/`por`/`rus` language id would crash
  at the first table, and any non-`eng` language at `expansionstring.tbl` (§ Language). (0x00516E5F–0x00516E7D, 0x0052593E)

## Leads used

- None outside our docs. [tbl.md](../../formats/tbl.md) (archivist, data only) gave the layout and the questions; each
  claim above was read from the code.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00524930` | `STRTABLE_EntryToString` | entry → converted value (entry ≥ count → 500) | C |
| `0x005249E0` | `STRTABLE_Hash` | `elf_hash(key) % size`, signed chars | C |
| `0x00524A30` | `STRTABLE_GetByIndex` | stored u16 index → text | C |
| `0x00524AC0` | `sub_00524AC0_NotXlated` | cached `"<key> -not xlated call ken"` + space placeholder | C |
| `0x00524C60` | `STRTABLE_FindInTable` | probe ≤ `max_probes` nodes, skip unused | C |
| `0x00524D30` | `STRTABLE_GetByKey` | key → index (patch, expansion, string) | C |
| `0x00524E20` | `STRTABLE_GetStringByKey` | key → converted value | I |
| `0x00524E40` | `STRTABLE_Unload` | reference count; frees on 0 | I |
| `0x00525020` | `STRTABLE_Crc16` | CRC-16, init `0xFFFF`, table-driven | C |
| `0x00525920` | `STRTABLE_LoadFile` | load, CRC check, offset checks | C |
| `0x005259C0` | `STRTABLE_LoadAll` | the three files, value conversion | I |
| `0x006117B0` | `STRTABLE_KeyToIndex` | excel converter: 0 → 5382 | C |
| `0x00526100` | `UNICODE_Utf8DecodeOne` | one UTF-8 sequence → u16, table-driven, −1 when bad or cut | C |
| `0x00526320` | `UNICODE_Utf8ToUtf16` | UTF-8 → at most limit − 1 units | C |
| `0x005276E0` | `UNICODE_IsWideByte` | byte ≥ 0x20 outside every font-map range → 1 | C |
| `0x00527790` | `UNICODE_LoadFontMap` | `default.map` (`KAMAP`) → ranges and tables | I |
| `0x00527D50` | `UNICODE_CharCount` | characters in a byte string under the font map | C |

Data: `data:g_pStringTbl@0x008829B4`, `data:g_pPatchStringTbl@0x008829D0`, `data:g_pExpStringTbl@0x008829D4` (file
buffers); `data:g_StringTblText@0x008829B8`, `data:g_PatchStringTblText@0x008829BC`,
`data:g_ExpStringTblText@0x008829C0` (per-node pointers to converted values); `data:g_Crc16Table@0x007301D8`;
`data:g_Utf8DecodeTable@0x007309B8`, `data:g_szNotXlatedSuffix@0x00730520`, `data:g_EmptyText@0x008829E8`;
`data:g_FontMapRangeCount@0x00882B22`, `data:g_pFontMapRanges@0x00882B28`, `data:g_pFontMapTable@0x00882B2C`.

## Walkthrough

```c
// fn:STRTABLE_GetByIndex@0x00524A30 (CX = index)
if (index >= 20000) {
    if (!g_pExpStringTbl) index = 11078;
    else return EntryToString(g_pExpStringTbl, g_ExpStringTblText, index - 20000);
}
if (g_pPatchStringTbl && index >= 10000)
    return EntryToString(g_pPatchStringTbl, g_PatchStringTblText, index - 10000);  // never returns NULL
if (!g_pStringTbl) fatal(0x246);
return EntryToString(g_pStringTbl, g_StringTblText, index);

// fn:STRTABLE_EntryToString@0x00524930
if (entry >= tbl->count) entry = 500;
node = tbl->index[entry];
if (node >= tbl->hash_size || !nodes[node].used || !text[node]) fatal();
return text[node];

// fn:STRTABLE_FindInTable@0x00524C60
slot = STRTABLE_Hash(key, tbl->hash_size);
for (n = 0; n < tbl->max_probes; n++) {
    if (nodes[slot].used == 1 && strcmp(file + nodes[slot].key_offset, key) == 0)
        { *out = text[slot]; return nodes[slot].entry; }
    slot = (slot + 1) % tbl->hash_size;
}
return 0xFFFF;
```

- [I] The 11078 fallback of an expansion index without `expansionstring` lands in `patchstring` entry 1078 when
  `patchstring` has more entries, else (entry ≥ count) on `patchstring` entry 500. (0x00524A33–0x00524A49)
- [C] **On a stock LoD install the 11078 path is unreachable**: `expansionstring` is loaded whenever `d2exp.mpq`
  exists (§ Answer, Loading), classic games included. Only an install without `d2exp.mpq` would take it (data/0002:
  the archive is opened only if the file exists). The classic session's indices ≥ 20000 went to
  `expansionstring`. ([run:2026-10-15-strings](experiments.md#run2026-10-15-strings))
- [C] Duplicated keys: the search returns the first used node on the probe chain, which tbl.md shows is the first
  entry inserted, so `GetByKey` returns the lowest entry number of a duplicated key. Run: three logged keys are
  duplicated in the table that has them and returned the lower entry: `Berserker's` (string 1826, not 2507),
  `Eschuta's temper` (expansionstring 1586, not 1620), `fire` (string 3272, not 3328).
  (fn:STRTABLE_FindInTable@0x00524C60, fmt:tbl#hash-table, [run:2026-10-15-strings](experiments.md#run2026-10-15-strings))

## Text conversion

Every text the lookups return is a UTF-16 copy made by `fn:UNICODE_Utf8ToUtf16@0x00526320` (`.\Unicode\UNISYS.CPP`
module, string `0x006E03C8`), at load for every node and once per not-found key for the placeholder.

- [C] **Decode.** `fn:UNICODE_Utf8DecodeOne@0x00526100` decodes one UTF-8 sequence with the six-row table
  `data:g_Utf8DecodeTable@0x007309B8` (rows {mask, value, result mask, minimum}: `80/00/7F/0`, `E0/C0/7FF/80`,
  `F0/E0/FFFF/800`, `F8/F0/1FFFFF/10000`, `FC/F8/3FFFFFF/200000`, `FE/FC/7FFFFFFF/4000000`): the first byte selects the
  row, each continuation byte must be `10xxxxxx`, an over-long result (below the row's minimum), a cut sequence or a
  bad byte returns −1, and the code point is stored as a u16 (truncated above U+FFFF, no surrogates). The first byte
  is sign-extended (`movsx`) before masking, which the mask makes harmless.
  (0x00526115–0x00526181, [run:2026-10-15-strings](experiments.md#run2026-10-15-strings))
- [C] **Limit.** `UNICODE_Utf8ToUtf16(dst, src, limit)` writes at most `limit − 1` units and a terminator. It stops
  at the end of `src`; at a bad sequence it counts the unit without writing it and terminates after it, so one unit of
  the buffer's old content survives. (0x00526363–0x005263C8)
- [C] **Character count.** The limit comes from `fn:UNICODE_CharCount@0x00527D50(str, max_bytes)`. With a font map
  loaded (`data:g_pFontMapTable@0x00882B2C` non-NULL) it walks at most `max_bytes` bytes up to the NUL and counts one
  character per byte, or per two bytes when `fn:UNICODE_IsWideByte@0x005276E0` says so: a byte ≥ 0x20 that lies in
  none of the `data:g_FontMapRangeCount@0x00882B22` (lo, hi) ranges at `data:g_pFontMapRanges@0x00882B28`. Without a
  map it is `strlen` (not exercised: the map is always loaded before the tables). (0x00527D54–0x00527DA4,
  0x005276E0–0x0052771C, [run:2026-10-15-strings](experiments.md#run2026-10-15-strings))
- [I] **The font map.** `fn:UNICODE_LoadFontMap@0x00527790`, called from `STRTABLE_LoadAll` (0x00525AF5), reads
  `data\local\font\<charset>\default.map`: `"KAMAP\n"`, a name ended by 0x1A, then at name end + 5 a u16 `n`, a u8
  range count `r`, `r` (lo, hi) byte pairs, `n` 4-byte pairs and `n` u16. The shipped `font/latin/default.map` (the
  `eng` charset) has `n` = 191 and the ranges (0x20–0x7E) and (0xA0–0xFF), so 0x7F–0x9F count as two-byte characters.
  (0x005277A1–0x00527A1F)
- [C] **At load** the limit is `count(value, string_length) + 1`, so a value converts whole; over all 9 388 entries of
  the three `eng` tables the result equals a plain UTF-8 decode (model check). **For a not-found key** the
  placeholder is `key + " -not xlated call ken w"` converted with `limit = count(...)`, which loses the last
  character: `"funeralpire -not xlated call ken "`. A key byte in 0x7F–0x9F loses one more (`"\x7f\x02"` →
  `"\x7f\x02 -not xlated call ken"`), and a key starting with a bad sequence leaves a single unwritten unit.
  (0x00525C49–0x00525C64, 0x00524BEF–0x00524C28, [run:2026-10-15-strings](experiments.md#run2026-10-15-strings))

## Language

- [I] Answered statically for plan 0028 (data/0002 § 4 for the mechanism): the language byte is the first byte of
  `data\local\use`. The MPQ copy (`d2data.mpq`) and the loose `data\local\Use` and `Use_eng` of the install hold
  **0x00** (`ENG`); the loose `Use_rus` holds **0x0B** (`RUS`) and is read only when copied over `Use` and the game runs
  with `-direct`. No shipped file holds any other value, so `pol`, `por` and the other languages are never selected
  by the shipped files; `RUS`, the one other reachable value, has no `.tbl` file in any archive or loose in the
  install, so `STRTABLE_LoadAll` would crash at `string.tbl` (§ Answer, Missing tables). Not run, per the plan.
  (fn:LNG_GetLanguageIndex@0x00525150, data/0002)

## Run

[run:2026-10-15-strings](experiments.md#run2026-10-15-strings), plan 0028 Phase 1: `tools/gdb/strings.gdb` logs
`GetByIndex` (index, tables loaded, table, entry, node, text), `GetByKey` (key, index, text) with each
`FindInTable` inside it (table, home slot, nodes examined, result), one line per distinct index or key.
`python3 -I tools/tbl.py check <eng> <logs>` compares them with `GameStrings`:

| session | index lookups (distinct) | key lookups (distinct) | hits after > 1 node | misses (all `max_probes`) | mismatches |
|---|---|---|---|---|---|
| expansion, seed 2802 | 187 | 1 964 | 885 | 2 844 | 0 |
| classic, seed 2803 | 149 | 1 964 | 885 | 2 844 | 0 |

Worked example (key lookup, chain longer than one): `of Amianthus` → patchstring home 961, all 1 179 nodes, miss →
expansionstring home 34, nodes 34, 35, 36, match at 36 = entry 925 → index 20925.

Seen on the way, for other findings: `GEMS_Load` calls `GetByKey` at 0x00637217 with 68 two-byte keys it builds on
its stack (`"-\x02"` … `"\x82\x02"`); none is found and the 0 goes to gems `+0x2C` (0x00637225).

- [I] **The gems key** (backlog 2026-10-15) is bytes `+0x28..+0x2A` of the gems record, a space read as 0, then a
  NUL: the loop treats `+0x28` as the gem's 4-character `code`, but in 1.14d that field holds the item index the
  `code` column compiles to (557..642 for the 69 rows), which is where the two-byte keys come from. So the lookup that
  was meant to give the gem's name string by its code finds nothing and every gem stores 0; details and the
  missing reader in [items/0007 § 9](../items/0007-sockets-runewords.md). (fn:GEMS_Load@0x00636B70 0x006371D6–0x00637225)
- [I] **Rare names** (backlog 2026-10-15). `sub_00633F40_LoadRareAffixes` fills `+0x0C` of each merged rare-name
  record (0x48 bytes: the suffix and prefix tables together) with `STRTABLE_GetByKey(record + 0x26)`, the row's
  `name` (0x006341E0–0x0063420B); the `.bin` holds 0 there. The client's item-name builder takes the two merged ids
  of a rare item (`ITEMS_GetRareName1`, item data `+0x32`, and `0x00628040`, `+0x34`), resolves each through
  `RAREAFFIX_GetRecord`, and shows `STRTABLE_GetByIndex(record + 0x0C)` for each; when that index is 0 it shows the
  raw `name` between `(` and `)` instead. The two texts go to two separate buffers (0x0048C5C1–0x0048C726); how the
  line joins them (order, separator) is not read. (fn:sub_00633F40_LoadRareAffixes@0x00633F40,
  fn:RAREAFFIX_GetRecord@0x00634260, fn:ITEMS_GetRareName1@0x00627FE0, fn:STRTABLE_GetByIndex@0x00524A30)

## Data touched

- fmt:tbl#layout fields `crc`, `count`, `hash_size`, `string_start`, `max_probes`, `file_size`, `index`, nodes.

## Open questions

- Not reached by a stock case, so `[I]`: the entry-500 fallback, the 11078 fallback (unreachable while `d2exp.mpq`
  exists, § Walkthrough), the node and offset fatal checks of `EntryToString` and `LoadFile`, and the NULL-text fatal
  of `FindInTable`. Forcing them means editing a `.tbl` file, which the crc check already makes fatal (plan 0028).
  (The crc case ran in run:2026-10-12-d2s-io.)
- The language question is answered statically (§ Language): only `ENG` (and `RUS` through a loose `Use_rus` under
  `-direct`, which would crash) can be selected by the shipped files. The other charsets' `default.map` files and the
  map's two other tables (`n` pairs and `n` u16, presentation) are not read here.
- ~~`GEMS_Load`'s 68 not-found two-byte keys (§ Run): what field it means to look up.~~ The gem's `code` text, read
  from a field that now holds the item index (§ Run, 2026-10-15).
- How the item-name line joins a rare item's two names (§ Run): the client builder after 0x0048C726.
