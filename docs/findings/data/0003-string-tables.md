# 0003 — String tables at run time

> **Subsystem:** data/strings
> **Question:** How does the game load the `.tbl` string tables, turn a stored string index into text, look a key up, and react to a bad or missing table?
> **Date:** 2026-10-12   **Plan:** none (backlog archivist → reverser 2026-10-12, "run-time `.tbl` use"; static read alongside plan 0013 Phase 1)   **Status:** open (static read `[I]`; the crc check `[C]` by [run:2026-10-12-d2s-io](../save/experiments.md#run2026-10-12-d2s-io))

Static reading only. Module `.\StrTable\strtable.cpp` (string `0x006E0334`); the byte layout is
[tbl.md](../../formats/tbl.md) and is not repeated. "Entry" is a position in a file's `index` array, "node" a hash node.
Names are ours.

## Answer (summary)

- [I] **Loading.** `fn:STRTABLE_LoadAll@0x005259C0` (fastcall: ECX = expansion flag, EDX = language code or NULL for
  the configured one) loads `data\local\lng\<lang>\string.tbl`, then `patchstring.tbl`, then, in an expansion game only,
  `expansionstring.tbl`, each through `fn:STRTABLE_LoadFile@0x00525920`. It is reference-counted (`0x008829D8`): a
  second call only increments the count. For every hash node it converts the node's value into a 16-bit-per-character
  string (`0x00526320`) and keeps one pointer per node. (0x00525B05–0x00525F5C)
- [C] **`crc` is checked.** `STRTABLE_LoadFile` recomputes `fn:STRTABLE_Crc16@0x00525020` over
  `[string_start, file_size)` (init `0xFFFF`, table at `data:g_Crc16Table@0x007301D8`, `table[1]` = `0x1021`, MSB first)
  and stops the game with a fatal error when it differs from header `+0x00`. Run: the three stock tables check at
  every game entry; a loose `patchstring.tbl` (under `-direct`) with one value byte changed and its crc recomputed
  by the CRC-16/CCITT-FALSE model loaded with the logged computed crc equal to the model's `0x8E1C`; the same file
  with the stock crc halted the game at start-up ("Unrecoverable internal error … failed at (206)", stack from
  `0x0052596E`, the fatal call after the compare). (0x0052594B–0x00525973, run:2026-10-12-d2s-io)
- [I] It also fatals when any node's `key_offset` or `string_offset` is ≥ `file_size` (not exercised).
  (0x00525978–0x005259B0)
- [I] **Index → text** (`fn:STRTABLE_GetByIndex@0x00524A30`, u16 index in CX): index ≥ 20000 → entry `index − 20000`
  of `expansionstring` if it is loaded, else the index is replaced by 11078 and handled as below; index ≥ 10000 with
  `patchstring` loaded → entry `index − 10000` of `patchstring`; otherwise entry `index` of `string`. Inside a file
  (`fn:STRTABLE_EntryToString@0x00524930`) an entry ≥ `count` is replaced by entry **500**, then `index[entry]` must
  name a used node (fatal otherwise) and that node's converted value is returned. So the bases are 0 / 10000 / 20000 as
  tbl.md found, with two fallbacks the data cannot show (11078, entry 500).
- [I] **Key → index** (`fn:STRTABLE_GetByKey@0x00524D30`): requires `string` and `patchstring` loaded (fatal
  otherwise). An empty key returns 0 and an empty string. Otherwise it searches **`patchstring`, then
  `expansionstring` (if loaded), then `string`**, returning `10000 + entry`, `20000 + entry` or `entry`. A key found
  nowhere returns **0** and a cached placeholder string, the key followed by `" not xlated call ken w"`
  (`0x00524AC0`, string `0x00730520`).
- [I] **The excel `.bin` value 5382** comes from the excel field converter `fn:STRTABLE_KeyToIndex@0x006117B0`: it
  calls `STRTABLE_GetByKey` and replaces a result of 0 (empty key or key not found) by `0x1506` = 5382. The archivist's
  data check (2 278 cells reproduced with patch → expansion → string, blank → 5382) is consistent; with it this claim
  would be `[C]` by data behaviour. (0x006117B9–0x006117C6; registered as a field callback at 0x006134CD,
  0x00613F96, 0x00614467)
- [I] **Hash lookup** (`fn:STRTABLE_FindInTable@0x00524C60`): home slot = `fn:STRTABLE_Hash@0x005249E0`(key) %
  `hash_size`, the PJW/ELF hash of tbl.md computed on **signed** chars (`movsx`); then it examines at most
  `max_probes` (`+0x0D`) nodes, stepping `slot = (slot + 1) % hash_size`. An unused node is **skipped, not a stop**;
  only `max_probes` ends the search. A used node matches on an exact, case-sensitive `strcmp` of the key and returns
  the node's `entry` (`+0x01`). (0x00524C7D–0x00524CDC)
- [I] **Missing tables.** `FILE_LoadWhole` returns NULL for a file it cannot open (after logging
  `"Error opening file: %s"`), and `STRTABLE_LoadFile` reads the header through that pointer without a test, so a
  missing `string.tbl`, `patchstring.tbl`, or, in an expansion game, `expansionstring.tbl` ends in an access violation
  at 0x0052593E. There is no fallback to `eng`. The fatal paths after a NULL return in `STRTABLE_LoadAll` (0x1C3,
  0x1F6) are unreachable for that reason. With the shipped files, a `pol`/`por`/`rus` language id would crash at the
  first table, and any non-`eng` language in an expansion game at `expansionstring.tbl`. (0x00516E5F–0x00516E7D,
  0x0052593E)

## Leads used

- None outside our docs. [tbl.md](../../formats/tbl.md) (archivist, data only) gave the layout and the questions; each
  claim above was read from the code.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00524930` | `STRTABLE_EntryToString` | entry → converted value (entry ≥ count → 500) | I |
| `0x005249E0` | `STRTABLE_Hash` | `elf_hash(key) % size`, signed chars | I |
| `0x00524A30` | `STRTABLE_GetByIndex` | stored u16 index → text | I |
| `0x00524AC0` | `sub_00524AC0_NotXlated` | cached `"<key> not xlated call ken w"` placeholder | I |
| `0x00524C60` | `STRTABLE_FindInTable` | probe ≤ `max_probes` nodes, skip unused | I |
| `0x00524D30` | `STRTABLE_GetByKey` | key → index (patch, expansion, string) | I |
| `0x00524E20` | `STRTABLE_GetStringByKey` | key → converted value | I |
| `0x00524E40` | `STRTABLE_Unload` | reference count; frees on 0 | I |
| `0x00525020` | `STRTABLE_Crc16` | CRC-16, init `0xFFFF`, table-driven | C |
| `0x00525920` | `STRTABLE_LoadFile` | load, CRC check, offset checks | C |
| `0x005259C0` | `STRTABLE_LoadAll` | the three files, value conversion | I |
| `0x006117B0` | `STRTABLE_KeyToIndex` | excel converter: 0 → 5382 | I |

Data: `data:g_pStringTbl@0x008829B4`, `data:g_pPatchStringTbl@0x008829D0`, `data:g_pExpStringTbl@0x008829D4` (file
buffers); `data:g_StringTblText@0x008829B8`, `data:g_PatchStringTblText@0x008829BC`,
`data:g_ExpStringTblText@0x008829C0` (per-node pointers to converted values); `data:g_Crc16Table@0x007301D8`.

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

- [I] The 11078 fallback of an expansion index in a game without `expansionstring` lands in `patchstring` entry 1078
  when `patchstring` has more entries, else (entry ≥ count) on `patchstring` entry 500. (0x00524A33–0x00524A49)
- [I] Duplicated keys: the search returns the first used node on the probe chain, which tbl.md shows is the first
  entry inserted, so `GetByKey` returns the lowest entry number of a duplicated key.
  (fn:STRTABLE_FindInTable@0x00524C60, fmt:tbl#hash-table)

## Data touched

- fmt:tbl#layout fields `crc`, `count`, `hash_size`, `string_start`, `max_probes`, `file_size`, `index`, nodes.

## Open questions

- Not run yet: `STRTABLE_GetByIndex` for an index ≥ 20000 in a classic game (expect the 11078 path), and the node
  offset checks. (The crc case ran in run:2026-10-12-d2s-io.)
- Whether any shipped language actually selects `pol`, `por` or `rus` (data/0002: the language byte comes from
  `data\local\use`); with the shipped files that choice would crash.
