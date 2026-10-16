# String tables (`.tbl`)

Owned by `archivist`. Localised strings: `data/local/lng/<lang>/string.tbl`, `patchstring.tbl` and
`expansionstring.tbl`, in `workspace/merged/`. Several excel columns store a **string index** that is
resolved through these files ([excel-bin.md § String-table keys](excel-bin.md#string-table-keys)), and
unique monster names are rolled from `uniqueprefix`/`uniquesuffix`/`uniqueappellation`, whose rows
are string keys. Parser: `tools/tbl.py` (`survey`, `dump`, `lookup`, `--key`, and a bare file list for
the header). Lead for the layout: none (everything below was found from the files).

**Scope.** The `[C]` tags in § Layout and § Hash table describe the **bytes**: they hold by data over
every file, which the evidence rules' data-format clause allows. They don't say how the game *reads*
the files. How the game loads and looks them up is anchored in [data/0003](../findings/data/0003-string-tables.md) (static, `[I]`; the crc check
`[C]` by [run:2026-10-12-d2s-io](../findings/save/experiments.md#run2026-10-12-d2s-io)) and summarised in § Override order, with that finding's tags.

## Files

`python3 -I tools/tbl.py survey workspace/merged` reads every `.tbl` under `data/local/lng/` (exit 0,
`SURVEY tbl` baseline in `tools/gate/baselines/tbl.txt`). Entries per file:

| language dir | `string.tbl` | `patchstring.tbl` | `expansionstring.tbl` |
|---|---|---|---|
| `eng` | 5391 | 1179 | 2818 |
| `chi`, `esp`, `ita`, `jpn`, `kor` | 5391 | 1179 | — |
| `deu`, `fra` | 5322 | 1179 | — |
| `pol` | — | 1179 | — |
| `por` | — | 17 | — |
| `rus` | — | — | — |

Plus `eng/beta/string.tbl` (5390 entries), a path the game doesn't format (it builds
`data\local\lng\%s\<name>.tbl`, [data/0002](../findings/data/0002-mpq-precedence.md)). In all: **20 files,
10 language directories, 61 826 entries** (equal to the sum of the header counts), 2 316 544 value bytes.
The 16 `.tbl` files under `data/local/font/latin/` are a different format (font metrics) and are not
read here.

- `[C]` Only `eng` ships `expansionstring.tbl`; `pol` and `por` ship no `string.tbl`; `rus` ships no
  `.tbl` at all in `merged/`. A missing table crashes the game (§ Override order).
- `[C]` Each language directory also ships UTF-16 source text (`english.txt`, `german.txt`,
  `patch.txt`, `expansioninput.txt`…), lines of `key, identifier, "value"`. They are not the exact
  sources of the shipped tables: for `eng/string.tbl`, 3812 of the 4688 keys found in the source text
  have an identical value; the differences seen are typographic (`…` in the source, `...` in the table).

## Layout

Little-endian, offsets from the start of the file.

| offset | size | type | name | meaning | tag |
|---|---|---|---|---|---|
| `0x00` | 2 | u16 | `crc` | CRC-16/CCITT-FALSE of the bytes from `string_start` to the end of the file (§ Hash table) | `[C]` |
| `0x02` | 2 | u16 | `count` | number of entries | `[C]` |
| `0x04` | 4 | u32 | `hash_size` | number of hash nodes (`count` + 1 to 3 in the shipped files) | `[C]` |
| `0x08` | 1 | u8 | `version` | 1 in every file | `[C]` |
| `0x09` | 4 | u32 | `string_start` | offset of the key/value area; always `0x15 + 2·count + 17·hash_size` | `[C]` |
| `0x0D` | 4 | u32 | `max_probes` | the longest linear-probe count of any entry (§ Hash table) | `[C]` |
| `0x11` | 4 | u32 | `file_size` | equals the file size in every file | `[C]` |
| `0x15` | `2 × count` | u16[] | `index` | entry → hash node number | `[C]` |
| after | `17 × hash_size` | node[] | nodes | see below | `[C]` |
| `string_start` | to the end | bytes | key/value area | NUL-terminated keys and values | `[C]` |

Hash node (17 bytes):

| offset | size | type | name | meaning | tag |
|---|---|---|---|---|---|
| `+0x00` | 1 | u8 | `used` | 1 for a node holding an entry, 0 for an empty slot | `[C]` |
| `+0x01` | 2 | u16 | `entry` | back-pointer: the entry number whose `index` names this node | `[C]` |
| `+0x03` | 4 | u32 | `hash` | the **home slot**: `elf_hash(key) % hash_size`, not the full hash | `[C]` |
| `+0x07` | 4 | u32 | `key_offset` | file offset of the key (NUL-terminated) | `[C]` |
| `+0x0B` | 4 | u32 | `string_offset` | file offset of the value | `[C]` |
| `+0x0F` | 2 | u16 | `string_length` | value length in bytes **including** its NUL | `[C]` |

- `[C]` For every entry `e`, `index[e]` points at a used node whose `entry` is `e`; the number of used
  nodes equals `count`; `file_size` equals the real size (all 20 files).
- `[C]` Every byte of the key/value area belongs to exactly one key or one value (keys with their NUL,
  values over `string_length`): no gaps, no overlaps, nothing shared, in all 20 files.
- `[C]` Values are **UTF-8**: every value of every file decodes (the `chi`, `jpn` and `kor` tables are
  mostly multi-byte), and the byte at `string_offset + string_length − 1` is always the NUL. Values
  hold real newlines (`0x0A`) where the source text writes `\n`. Keys are ASCII in every file.
- `[C]` Keys are not unique inside a file: 3988 duplicate entries in all (292 in each full
  `string.tbl`, 30 in `eng/expansionstring.tbl`, 5–124 per `patchstring.tbl`).

## Hash table

- `[C]` `hash` = `elf_hash(key) % hash_size`, with the classic PJW/ELF hash over the key bytes:

  ```
  h = 0
  for each byte c of key:
      h = (h << 4) + c                     (u32)
      g = h & 0xF0000000
      if g != 0: h = h ^ (g >> 24)
      h = h & ~g
  ```

  It holds for all 61 826 entries. No key has a byte ≥ 0x80, so signed and unsigned `char` give the same
  result on these files.
- `[C]` The node positions are exactly what inserting entries `0, 1, …, count−1` in order gives, each
  at the first free node scanning `home, home+1, …` (wrapping at `hash_size`). `max_probes` is the
  largest number of nodes that insertion examined for one entry (1 = placed at home). Both reproduce
  for all 20 files (`checks()` fields `slot` and `max_probes`).
- `[C]` So a lookup that starts at `elf_hash(key) % hash_size` and steps +1 over at most `max_probes`
  nodes, comparing keys, finds every entry; for a duplicated key it finds the **first** entry, since
  that entry was inserted first along the same probe chain (`find` check, every entry of every file).
  `tools/tbl.py` resolves keys this way.
- `[I]` The game's lookup probes the same way and stops **only** after `max_probes` nodes: an unused node is skipped,
  not a stop. It hashes **signed** chars, which equals the unsigned result on the shipped files (no key byte ≥ 0x80).
  A key matches on an exact, case-sensitive `strcmp`. ([data/0003](../findings/data/0003-string-tables.md), fn:STRTABLE_FindInTable@0x00524C60,
  fn:STRTABLE_Hash@0x005249E0)
- `[C]` `crc` = CRC-16/CCITT-FALSE (polynomial `0x1021`, initial value `0xFFFF`, no reflection, no
  final XOR) of the bytes `[string_start, file_size)`. It matches in all 20 files.
- `[C]` The game checks it: `STRTABLE_LoadFile` recomputes the CRC over `[string_start, file_size)` and stops the game
  with a fatal error when it differs from `crc`. A loose `patchstring.tbl` with a changed value byte and its `crc`
  recomputed with this model loaded (logged computed crc = the model's `0x8E1C`); the same file with the stock `crc`
  halted the game at start-up ("failed at (206)"). ([data/0003](../findings/data/0003-string-tables.md), fn:STRTABLE_LoadFile@0x00525920,
  fn:STRTABLE_Crc16@0x00525020, [run:2026-10-12-d2s-io](../findings/save/experiments.md#run2026-10-12-d2s-io))
- `[I]` It also stops the game when any node's `key_offset` or `string_offset` is ≥ `file_size` (not exercised).
  ([data/0003](../findings/data/0003-string-tables.md))

## Key → index (as the excel `.bin` files store it)

- `[C]` index = **base + entry**, with base 0 for `string.tbl`, 10000 for `patchstring.tbl`, 20000 for
  `expansionstring.tbl`. A key present in several files resolves to **patchstring, then
  expansionstring, then string**. A blank key, or one found nowhere, gives **5382** (`string.tbl`
  entry 5382, key `dummy`). Checked over every `namestr`/`spelldescstr` cell of weapons, armor, misc
  and every `NameStr`/`DescStr` cell of monstats (2 278 cells with the English tables): all match but one.
- `[I]` The game's converter that compiles a key cell into a `.bin` index is `fn:STRTABLE_KeyToIndex@0x006117B0`: it
  calls the run-time key lookup (patchstring → expansionstring → string, below) and turns a result of 0 (blank key
  or key not found) into `0x1506` = 5382. The data check above is the corroboration the finding names for `[C]`.
  ([data/0003](../findings/data/0003-string-tables.md))
- `[C]` The exception: monstats `uberandariel` has `NameStr = Lilith`; its `.bin` stores 5382 (not
  found) although the shipped `eng/patchstring.tbl` has `Lilith` at entry 1154 (→ 11154). `[C]` **The converter
  explains it (plan 0039 A3):** the pinned game's own `-direct -txt` compile, given this install's string tables,
  stores 11154 in that cell, and it is the only cell of the written `monstats.bin` that differs from the shipped one
  ([experiments § run:2026-10-15-cube-saves, addendum 2026-10-16](experiments.md#addendum-2026-10-16-the-whole-bin-set-the-compile-wrote-plan-0039-a3),
  [data/0004 § S1b](../findings/data/0004-cell-converters.md#plan-0038-batch-s1b-2026-10-16), fn:STRTABLE_KeyToIndex@0x006117B0).
  `[L]` The shipped `.bin` was compiled against an earlier `patchstring.tbl` without that key (how the file was made
  is not observable in our binary).
- `[C]` Inside one file a duplicated key resolves to its first entry, both through the hash table
  (above) and in `tools/tbl.py`'s compiled indices, which reproduce every checked cell.

### Unique monster name tables

`uniqueprefix.bin` (53 records), `uniquesuffix.bin` (69) and `uniqueappellation.bin` (25) are a u32
record count followed by one u16 per record ([excel-bin.md](excel-bin.md)). `survey` checks every row:

- `[C]` For all **147** rows, the English key lookup of the `.txt` `Name` cell (`GloomUM`, `the Hammer`…)
  gives exactly the u16 the `.bin` stores (2702–2849, all in `string.tbl`), and the value at that index
  equals the value the `english.txt` source text gives for the key (147/147; e.g. `GloomUM` → 2702 →
  `Gloom`).
- `[C]` The same 147 keys resolve in every language that ships a `string.tbl` (`chi`, `deu`, `esp`,
  `fra`, `ita`, `jpn`, `kor`: 147/147 each, e.g. `deu` `the Hammer` → `der Hammer`), and in neither
  `pol` nor `por`, which ship only `patchstring.tbl`. The index is the stored one in the 5391-entry
  tables (147/147) and different for all 147 in the 5322-entry `deu`/`fra` tables, so a stored index
  read against `deu`/`fra` names other strings (the `[I]` in excel-bin.md, now by data for these rows).

## Override order

From [data/0003](../findings/data/0003-string-tables.md) (static reading, then run:2026-10-15-strings; the tag is on
each bullet). The data-side order of § Key → index is the same order the code uses.

- `[I]` **Loading.** `fn:STRTABLE_LoadAll@0x005259C0` loads `data\local\lng\<lang>\string.tbl`, then `patchstring.tbl`,
  then `expansionstring.tbl`, each through `fn:STRTABLE_LoadFile@0x00525920` (crc and offset checks above). Every
  node's value is converted to a 16-bit-per-character string once, at load.
- `[C]` **`expansionstring.tbl` loads whenever `d2exp.mpq` exists**, classic games included: the three callers pass
  `HasExpansionMpq()` as the flag and run at program level, before any game
  ([data/0003 § Answer](../findings/data/0003-string-tables.md#answer-summary), run:2026-10-15-strings).
- `[C]` **Index → text** (`fn:STRTABLE_GetByIndex@0x00524A30`, run:2026-10-15-strings; the two fallbacks stay `[I]`): index ≥ 20000 → `expansionstring` entry
  `index − 20000` if that table is loaded, else the index becomes **11078** and goes on as below; index ≥ 10000 (with
  `patchstring` loaded) → `patchstring` entry `index − 10000`; else `string` entry `index`. Inside a table an entry
  ≥ `count` is replaced by entry **500**, and the entry must name a used node (fatal otherwise). So the bases are the
  0 / 10000 / 20000 of § Key → index, with two fallbacks the data cannot show. `[C]` The 11078 fallback is unreachable
  on a stock install, since `expansionstring` is always loaded while `d2exp.mpq` exists; an install without it would
  land on `patchstring` entry 1078 (that table has 1179 entries in every shipped language but `por`) `[I]`.
- `[C]` **Key → index** (`fn:STRTABLE_GetByKey@0x00524D30`, run:2026-10-15-strings): searches **`patchstring`, then `expansionstring` (if
  loaded), then `string`**, and returns `10000 + entry`, `20000 + entry` or `entry`. An empty key returns 0. A key
  found nowhere returns 0 with a placeholder text: the key followed by `" -not xlated call ken w"` minus its last
  character, so `"funeralpire"` gives `"funeralpire -not xlated call ken "`. Within a table a duplicated key gives its
  lowest entry (the probe chain reaches the first-inserted node first). The excel converter
  maps that 0 to 5382 (§ Key → index).
- `[I]` **Missing tables.** A table that cannot be opened is not tested for: the game reads its header through a
  NULL pointer and crashes. There is **no fallback to `eng`**. With the shipped files a `pol`, `por` or `rus` language
  id would crash at the first table, and any language other than `eng` would crash in an expansion game at
  `expansionstring.tbl`. Which language the game uses comes from `data\local\use`
  ([data/0002](../findings/data/0002-mpq-precedence.md)).

## Tooling

- `python3 -I tools/tbl.py survey workspace/merged`: every check above, per-file lines, the unique-name
  check and the `SURVEY tbl` line (about 8 s). Registered in `tools/gate.py` `SURVEYS`.
- `python3 -I tools/tbl.py dump <file.tbl>`: `entry  node  key  value` per entry, with `\n`, `\t` and
  `\\` escaped.
- `python3 -I tools/tbl.py lookup <lng-dir> <key>`: index, table, entry and value
  (`--key` prints the index alone; `tools/excel_bin.py` uses the same `Strings` class).

## Open questions

- `[L]` Not run ([data/0003](../findings/data/0003-string-tables.md) § Open questions): the entry-500 and 11078
  fallbacks (the latter unreachable while `d2exp.mpq` exists) and the node offset checks.
- `[L]` `eng/beta/string.tbl` is on no path the game formats; probably a leftover.
