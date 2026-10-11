# String tables (`.tbl`)

Owned by `archivist`. Localised strings: `data/local/lng/<lang>/string.tbl`, `patchstring.tbl` and
(for `eng`) `expansionstring.tbl`, in `workspace/merged/`. Documented here only as far as the excel
`.bin` files need it: several columns store a **string index** that is resolved through these files
([excel-bin.md § String-table keys](excel-bin.md#string-table-keys)). Parser: `tools/tbl.py`.

## Layout

Little-endian, offsets from the start of the file.

| offset | size | type | name | meaning | tag |
|---|---|---|---|---|---|
| `0x00` | 2 | u16 | `crc` | unchecked here | `[C]` field / unknown meaning |
| `0x02` | 2 | u16 | `count` | number of entries | `[C]` |
| `0x04` | 4 | u32 | `hash_size` | number of hash nodes | `[C]` |
| `0x08` | 1 | u8 | `version` | 1 in every file | `[C]` |
| `0x09` | 4 | u32 | `string_start` | offset of the string area | `[C]` field / not used by the parser |
| `0x0D` | 4 | u32 | `max_probes` | unchecked here | unknown |
| `0x11` | 4 | u32 | `file_size` | equals the file size in every file | `[C]` |
| `0x15` | `2 × count` | u16[] | `index` | entry → hash node number | `[C]` |
| after | `17 × hash_size` | node[] | nodes | see below | `[C]` |

Hash node (17 bytes): `u8 used`, `u16 entry` (back-pointer to the entry number), `u32 hash`,
`u32 key_offset`, `u32 string_offset`, `u16 string_length`. Keys and strings are NUL-terminated.

- `[C]` `tools/tbl.py` reads all 20 `.tbl` files under `data/local/lng/*/` without error: for every entry
  `e`, `index[e]` points at a used node whose `entry` is `e`, and `file_size` equals the real size.
  (`por` ships only a 17-entry `patchstring.tbl`; `deu` and `fra` `string.tbl` have 5322 entries, the
  other languages 5391.)
- `[L]` The hash function, the probing scheme and the `crc` are not needed to resolve keys and are not
  documented yet.

## Key → index (as the excel `.bin` files store it)

- `[C]` index = **base + entry**, with base 0 for `string.tbl`, 10000 for `patchstring.tbl`, 20000 for
  `expansionstring.tbl`. A key present in several files resolves to **patchstring, then
  expansionstring, then string**. A blank key, or one found nowhere, gives **5382** (`string.tbl`
  entry 5382, key `dummy`). Checked over every `namestr`/`spelldescstr` cell of weapons, armor, misc
  and every `NameStr`/`DescStr` cell of monstats (2 278 cells with the English tables): all match but one.
- `[C]` The exception: monstats `uberandariel` has `NameStr = Lilith`; its `.bin` stores 5382 (not
  found) although the shipped `eng/patchstring.tbl` has `Lilith` at entry 1154 (→ 11154). `[L]` The
  `.bin` was compiled against an earlier `patchstring.tbl` without that key.
- `[I]` Inside one file a duplicated key resolves to its first entry (`tools/tbl.py` does this; no item
  or monster cell depends on it).
- `[L]` Whether the game resolves the stored index through the same three-file scheme at run time is a
  loader question (backlog).
