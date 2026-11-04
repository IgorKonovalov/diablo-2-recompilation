# PathDirTables: the direction and step tables of the path planners (`Game.exe` image)

> **Source:** the pinned `Game.exe` image (no excel file)   **Tables:** 15, 882 elements: 278 listed, 604 by rule   **Records:** dwords, except one byte table
> **Doc status:** every table's address, element width, shape and how it is indexed; four tables' values, and eleven tables' exact rules checked element by element against the image ([ADR-0031](../adrs/0031-constants-of-the-code-image.md)), all by script;
> the width of each table taken from the instructions that read it (65 instructions, 69 table and reader pairs since the four walker reads serve two tables each, checked by script against `objdump`); each index shape from the same instructions (§ Layout);
> the meanings taken from [path/0001](../findings/path/0001-pathplan-register.md), [path/0002](../findings/path/0002-search.md),
> [path/0003](../findings/path/0003-short-planners.md) and [drlg/0008](../findings/drlg/0008-outdoor.md) with their tags and scopes
> (plan 0054, entry `2026-11-04-spec-writer-archivist-path-direction-tables-doc`)

## Purpose

The path planners ([path/search](../specs/path/search.md), [path/overview](../specs/path/README.md)) and the outdoor road search
([drlg/outdoor](../specs/drlg/outdoor.md)) read small constant tables from the image's data. No MPQ file holds them and they are not an excel table:
they are constants of the code. A reimplementation needs their values, so this doc gives every one: as a rule where one is written below, as a short listed table otherwise ([ADR-0031](../adrs/0031-constants-of-the-code-image.md); [plan 0054](../plans/0054-path-search.md)), with where each sits, how wide an element is, its shape
and its index. Generated and checked by `python3 -I tools/path_survey.py dirtables|dirmd|readers|rules <game.exe>` (tests:
`python3 -I tools/test_path_survey.py`; the totals, a checksum per table and the rules' mismatch count are in gate survey `path`). The path types themselves
(`g_PathPlanFuncs`, the flags) are [PathTypes](PathTypes.md); the collision pattern table is [drlg/collision](../specs/drlg/collision.md).

## Layout

`[C]` Addresses are those of `re/symbols.csv`; a centred table starts below its symbol. Values are little-endian two's complement.
"Read as" is the operand size of the instructions that read the table, `[C]` for each listed reader (`path_survey.py readers`): **a table of
dwords is not always read as a dword**. `WORD` means the instruction loads the low 16 bits of the dword (`mov ax, WORD PTR [reg*8+table]`),
so the table's other 16 bits are never read; every dword of those three tables is -1, 0 or 1, so the dword and its low word give the same
signed value. "Via pointer" means the readers dereference a register that holds a pointer into the table (the pointer is built at the
address given in § How each is read).

| Table | Address | Elements | Stored as | Read as | Shape | Index | First address after |
|---|---|---:|---|---|---|---|---|
| `g_DirOctant` | `0x006F1518` | 75 | i32 | DWORD | `[25][3]` | `3 * PathDirCell + column`; the cell is `5 dx' + dy' + 12` | `0x006F1644` |
| `g_PathDirTriples` | `0x006F1648` | 75 | u8 | BYTE | `[25][3]` | `3 * PathDirCell + column` | `0x006F1693` |
| `g_PathDistNear` | `0x006F1698` | 64 | i32 | DWORD | `[8][8]` | `dx + 8 dy`, both below 8 | `0x006F1798` |
| `g_PathStep8Long` | `0x006F1798` | 16 | i32 | WORD | `[8][2]` | `2 * direction + (0: dx, 1: dy)` | `0x006F17D8` |
| `g_PathSearchTurnRows` | `0x006F17D8` | 64 | i32 | DWORD, via pointer | `[8][8]` | row `(want - d) & 7`, entry by try | `0x006F18D8` |
| `g_T15Step` | `0x006F1D98` | 32 | i32 | WORD | `[16][2]` | `2 * direction + (0: dx, 1: dy)`, direction 0..15 | `0x006F1E18` |
| `g_T15DirFromStep` | `0x006F1E18` (symbol `0x006F1E28` is index 0) | 9 | i32 | DWORD | centred, `-4..4` | `3 dy + dx` for a step `(dx, dy)` of -1..1 | `0x006F1E3C` |
| `g_T15TurnB` | `0x006F1E40` | 16 | i32 | DWORD, via pointer | `[16]` | direction 0..15 | `0x006F1E80` |
| `g_T15NextB` | `0x006F1E80` | 16 | i32 | DWORD, via pointer | `[16]` | direction 0..15 | `0x006F1EC0` |
| `g_T15TurnA` | `0x006F1EC0` | 16 | i32 | DWORD, via pointer | `[16]` | direction 0..15 | `0x006F1F00` |
| `g_T15NextA` | `0x006F1F00` | 16 | i32 | DWORD, via pointer | `[16]` | direction 0..15 | `0x006F1F40` |
| `g_PathDir8` | `0x006EB398` | 16 | i32 | WORD | `[8][2]` | `2 * direction + (0: dx, 1: dy)` | `0x006EB3D8` |
| `g_PathSignTable` | `0x006EB3F0` (symbol `0x006EB490` is index 0) | 81 | i32 | DWORD | centred, `-40..40` | `a + 9 b` | `0x006EB534` |
| `g_PathDirTable` | `0x006EB7E0` | 384 | i32 | DWORD | `[128][3]` | `3 q + column`, `q = minor * 127 / major` | `0x006EBDE0` |
| (unnamed) | `0x006EB7D4` | 2 | i32 | DWORD | `[2]` | a zero vector | `0x006EB7DC` |

- `[C]` The element widths come from the instructions: `g_PathStep8Long`, `g_T15Step` and `g_PathDir8` are read with `WORD PTR`; `g_PathDirTriples` with `movzx ... BYTE PTR [eax+eax*2+0x6f1648]`; the rest with `DWORD PTR`.
  All 69 table and reader pairs (65 instructions: `0x0067BC87`, `0x0067BCCB`, `0x0067BD1A` and `0x0067BFFD` read through a walker's pointer and serve two tables each) are in § How each is read; `path_survey.py readers` disassembles them again and compares the size, **and nothing else**: it does not test an index.
- `[C]` **The index form is read from the instructions before each load**, by hand at the `lane/a54` review, not by the script: `g_DirOctant` `lea eax,[eax+eax*2]`, then `*4`, the columns at `+0`, `+4`, `+8` (0x00678D00, 0x00678D03, 0x00678D48-0x00678D5C); `g_PathDirTriples` `[eax+eax*2+base]`, `+1`, `+2` (0x00678DC0-0x00678DD8); `g_PathDistNear` `lea eax,[eax+ecx*8]`, `*4` (0x006793AD, 0x006793B0); `g_PathStep8Long`, `g_T15Step` and `g_PathDir8` `*8` with `dy` at `+4` (0x00679C01, 0x00679C0D; 0x0067BC42, 0x0067BC53; 0x006481C7, 0x006481CF); `g_PathSearchTurnRows` `& 7`, `shl 5`, 4 added per try (0x0067A5D6, 0x0067A5D9, 0x0067A6A6); `g_T15DirFromStep` `3 dy + dx`, `*4`, from `0x006F1E28` (0x0067BBD6-0x0067BBE3, 0x0067BED2-0x0067BEDD); the four `g_T15` lists `[pointer + d*4]` (0x0067BC87, 0x0067BFFD); `g_PathSignTable` `lea ebx,[eax+ecx*8]`, `add ebx,ecx`, `*4` from `0x006EB490` (0x006480AF-0x006480C0); `g_PathDirTable` `lea edx,[eax+eax*2]`, `*4`, the columns at `+0`, `+4`, `+8` (0x0064FCDD-0x0064FCF8).
- **How many rows.** `[C]` Bound by the code: the 25 cells (each term clamped to -2..2, then `+ 12`, 0x00678C63-0x00678C94, the same at 0x00678BC3-0x00678BF4), `g_PathDistNear`'s 8 and 8 (`cmp`, 0x006793A3, 0x006793A8), `g_PathSearchTurnRows`' 8 (`& 7`), `g_PathSignTable`'s -40..40 (the tests at 0x00648089, 0x00648092). `[I]` From the range of the index, not from a test at the load: `g_PathDirTable`'s 128 (`q = minor * 127 / major` with the minor no larger than the major, 0x0064FCB1-0x0064FCD7), the 8 rows of `g_PathStep8Long` and `g_PathDir8` (a direction from `g_DirOctant` or `g_PathDirTriples`), `g_T15DirFromStep`'s -4..4 (a step of -1..1). `[I]` The 16 rows of `g_T15Step` and the 16 entries of each `g_T15` list are the span to the next symbol: on path/0003 § 7's index, at most 14, with `Turn` and `Next` values of 0 to 6, their row 15 is not reached. (0x0067BEE4, 0x0067BC87, 0x0067BFFD)
- `[C]` The tables lie in the file-backed part of a data section; no listed table extends past the next one's start
  (`tools/test_path_survey.py`, `test_neighbours_do_not_overlap`).
- `[C]` By script `g_T15TurnA` and `g_T15NextB` hold the same 16 values; `g_T15TurnB` and `g_T15NextA` differ. A relation of the values only.

## How each is read

Every statement below is the finding's, with the finding's tag; the instruction addresses are in the table at the end of the section.

- **`g_DirOctant`, `g_PathDirTriples`: the cell of a direction pair.** `[C]` `PathDirCell(a, b)` ([path/0001](../findings/path/0001-pathplan-register.md),
  `sub_00678C10_PathDirCell`): `dx = b.x - a.x`, `dy = b.y - a.y`; when `|dx| >= 2|dy|` the y term becomes -1 for a negative `dy`, else `dy & 1`; else
  when `|dy| >= 2|dx|` the x term likewise; both are clamped to -2..2; the cell is `5 dx + dy + 12` (0 to 24, `dx'` and `dy'` being the terms after those
  steps; the `dy & 1`, not a sign, is the code, 0x00678C4C). `[I]` Eight of the 16 readers take the cell from `sub_00678B80_DirOctantIndex` instead (the functions whose first load is 0x00678CC0, 0x00678D03, 0x00678D48 and 0x00678DC0: the same instructions on two words passed apart, drlg/0008). `[C]` `PathDirOctant(a, b)` is `g_DirOctant[PathDirCell(a, b)]`, the first of the cell's
  three values, and `PathDirRow(a, b)` copies the three ([path/0003](../findings/path/0003-short-planners.md) *Functions*, [path/0002](../findings/path/0002-search.md)
  *Functions*). `g_DirOctant` holds 0 to 7 only, `[I]` (path/0003 § 1 on the assert 0x4C; the values below are 0..7 by script, `dirtab_octant_max=7`).
  The outdoor road search reads column 0 only, `[C]` (drlg/0008: `DirOf(p) = g_DirOctant[3 (5 dx' + dy' + 12)] / 2 & 3`, `g_DirOctant` `i32[25][3]`, "only
  column 0 is read here"; drlg/0008 lists that column by cell). `g_PathDirTriples` is `[I]` (path/0001 *Functions*, its data rows): the main direction and two alternates, 255 for none;
  `[C]` every entry is 0, 2, 4, 6 or 255 (path/0001 § 5, `p1-tables.txt` `T1648`; `test_triples_are_axis_directions_or_none` checks it again).
  The free walk (`PathTry3Dirs`, path/0003 § 1) uses the row's three directions in order, `[C]` "each tested at `cur + step`; the first free one".
- **`g_PathDistNear`.** `[C]` (path/0003 § 1, `PathDistNear`, 0x00679380-0x006793D7): with `dx`, `dy` absolute; below 8 on both axes `g_PathDistNear[dx + 8 dy]`, a negative
  entry giving 0 and another `entry + 1`; otherwise `2 max + min` (`dx > dy` strictly picks the first form, which is the same value at equality).
  By script the table is symmetric in `dx`, `dy`, holds -1 in six cells (`(dx,dy)` = `(0,0) (1,0) (0,1) (2,0) (0,2) (1,1)`) and its largest entry is 11.
  `[C]` The image holds the same 64 values a second time at `0x006EB180`, read by `UnitInteractDistance` ([items/inventory](../specs/items/inventory.md) I2; `dirtab_distnear_eq_6eb180=1`).
- **`g_PathStep8Long`, `g_PathDir8`, `g_PathSearchStep8`.** `[C]` `g_PathStep8Long` is the eight compass steps clockwise from `+x`, y down, index = direction, by the rule in [§ The rules](#the-rules)
  (path/0003 *Functions* and path/0002 § 5 for `g_PathSearchStep8`, `0x006F1958`, which this doc does not list). `g_PathDir8` is the free walk's steps
  (path/0001 *Functions*, `[I]`; "the steps of `g_PathDir8` used are rows 0, 2, 4, 6 (axis steps)" `[C]`, path/0001 § 5). By script `g_PathDir8` and `g_PathStep8Long` hold the same 16 values (`dirtab_dir8_eq_step8long=1`).
  The readers add the WORD to a u16 coordinate.
- **`g_PathSearchTurnRows`.** `[C]` (path/0002 § 5) the root's `dir` is `want & 7`, its row 0; each child tries 5 entries of the row chosen by `(want - d) & 7`, `d` the parent's direction
  when the child was made, and the root tries the 8 entries of row 0 (`0, +1, -1, +2, -2, +3, -3, +4`). `PathSearchAdvance` adds the node's next row entry to its `dir`;
  a node is spent when `tries` reaches 5 (a child) or 8 (the root). path/0002 § 5 tabulates the five entries a child uses, per row; the block below lists all 8 entries of each row.
  `[C]` as instruction text: the row pointer is built as `base + ((x - y) & 7) * 32` (0x0067A5D6-0x0067A5DC, 0x0067A963-0x0067A969), the readers load the dword at the pointer (0x0067A665, 0x0067A676, 0x0067A9B1, 0x0067A9BE) and the pointer is advanced by `ebx = 4` (0x0067A697, 0x0067A6A6).
  `[I]` the first try keeps the parent's direction in rows 0, 1, 2, 6 and 7 (path/0002 § 5).
- **`g_T15Step`, `g_T15DirFromStep`, `g_T15Turn*`, `g_T15Next*`.** `[C]` (path/0003 § 7) `T15Follow` starts two followers from `cur` with directions
  `g_T15DirFromStep[3 dy + dx] + 1` and `+ 7`, `(dx, dy)` the step to the block, **not masked**: an index up to 14 into the 16-entry tables. A follower's step tries its direction, then up to three
  turns of its `Turn` table; a free one is its next cell, and on success its direction becomes `Next[d]`. Follower A uses `g_T15TurnA` and `g_T15NextA`, follower B `g_T15TurnB` and `g_T15NextB`
  `[I]` (`re/types/path.h` `T15Walker`: the Next list at the record's `+0x14`, the Turn list at `+0x18`; the records are set at 0x0067BE2D-0x0067BE8A). `g_T15Step` is 8 steps from `(0,-1)` clockwise (screen y down), listed twice, so that direction `d` and `d + 8` give one step
  (by script). `g_T15DirFromStep` is `[I]` (path/0003 *Functions*, its data rows: "centred: index `3 dy + dx`"); its element for the step `(0,0)` is -1 (by script) and for the eight steps it is the `g_T15Step` direction of that step
  (by script, `test_t15_dir_from_step_inverts_t15_step`).
- **`g_PathSignTable`.** `[C]` (path/0001 § 5, `PathTargetExtendPlayer`) with `dx, dy` the moved target minus the start, nothing when `|dx| >= 5`, `|dy| >= 5` or both 0; else the step
  `(g_PathSignTable[dx + 9 dy], g_PathSignTable[dy + 9 dx])`. **The entry at `a + 9 b` is `sign(a)` when
  `|a| >= |b|` and 0 otherwise**, for every `a`, `b` in -4..4 (§ The rules), so the pair is `(sign dx, 0)` when `|dx| > |dy|`, `(0, sign dy)` when `|dy| > |dx|`
  and `(sign dx, sign dy)` only when `|dx| = |dy|`: `x` takes `g_PathSignTable[dx + 9 dy]`, `y` takes `g_PathSignTable[dy + 9 dx]` (0x006480AF-0x006480C7, 0x006480EA, 0x006480ED). path/0001 § 5 and [path/overview § C3](../specs/path/README.md#c3-the-free-target-step) said "the signs of dx and dy" until they were corrected at the `lane/a54` review, 2026-11-04.
  `0x00648020` holds the other two readers (0x00648028, 0x00648039), the same pair written through two pointers; `[I]` no direct `call` reaches it (byte scan of `.text`) and no operand names it, and a table pointer to it was not looked for.
- **`g_PathDirTable`.** `[C]` (path/0001 § 9, `PathDirection`, 0x0064FC60-0x0064FD69, 16.16 positions): the major axis is y when `dx <= dy`; `q = minor * 127 / major` (signed `idiv`, 0 for a zero major) indexes
  the table (128 rows of three dwords); the row's vector is swapped and signed by octant and its third dword gives the 64-step direction (`(-1 - t) & 15` swapped, `& 31` for a decreasing y, `& 63` for an increasing x, then `+ 8`).
  The 128 rows are given by the rule in § The rules; the rule is a statement about the values, not about the code.
  The two dwords at `0x006EB7D4` and `0x006EB7D8` are 0, 0: `[C]` (path/0001 § 9) `PathAimNextPoint` takes the vector and step from them past the last point (0x0064FF33, 0x006507D6).

Readers, by table (`WORD` and `BYTE` are the size of the memory operand, `[C]` by `objdump` of the pinned image; the address is the instruction):

| Table | Reading instructions |
|---|---|
| `g_DirOctant` | `0x00678D03`, `0x00678D23`, `0x00678D48`, `0x00678D53`, `0x00678D5C`, `0x00678D88`, `0x00678D93`, `0x00678D9C` (DWORD) |
| `g_PathDirTriples` | `0x00678CC0`, `0x00678CE0`, `0x00678DC0`, `0x00678DCD`, `0x00678DD8`, `0x00678E03`, `0x00678E0D`, `0x00678E18` (BYTE) |
| `g_PathDistNear` | `0x006793B0` (DWORD) |
| `g_PathStep8Long` | `0x0067942C`, `0x00679434`, `0x00679477`, `0x0067947F`, `0x006794D3`, `0x006794DB`, `0x00679C01`, `0x00679C0D`, `0x00679DBE`, `0x00679DC6`, `0x0067A33F`, `0x0067A347` (WORD) |
| `g_PathSearchTurnRows` | `0x0067A665`, `0x0067A676`, `0x0067A9B1`, `0x0067A9BE` (DWORD through the row pointer) |
| `g_T15Step` | `0x0067BC42`, `0x0067BC53`, `0x0067BC8C`, `0x0067BC9E`, `0x0067BCD3`, `0x0067BCE5`, `0x0067BD1F`, `0x0067BD31` (WORD) |
| `g_T15DirFromStep` | `0x0067BBE3`, `0x0067BEDD` (DWORD) |
| `g_T15TurnA`, `g_T15TurnB` | `0x0067BC87`, `0x0067BCCB`, `0x0067BD1A` (DWORD through the walker's `+0x18` pointer) |
| `g_T15NextA`, `g_T15NextB` | `0x0067BFFD` (DWORD through the walker's `+0x14` pointer) |
| `g_PathDir8` | `0x006481C7`, `0x006481CF`, `0x00648207`, `0x00648213`, `0x0064824E`, `0x0064825A` (WORD) |
| `g_PathSignTable` | `0x00648028`, `0x00648039`, `0x006480B4`, `0x006480C0` (DWORD) |
| `g_PathDirTable` | `0x0064FCE0`, `0x0064FCE7`, `0x0064FCF8`, `0x0064FD0F` (DWORD) |
| the two zero dwords | `0x0064FF33`, `0x0064FF38`, `0x006507D6`, `0x006507DB` (DWORD) |

Scope of the reader list: a scan of the `objdump -d` listing of the whole image for any operand (displacement or immediate, not a `call` or `jmp` target) inside a table's span
found these instructions and no other. The sites that take a table's address rather than read it are `g_PathSearchTurnRows` at 0x0067A5DC, 0x0067A969 and 0x0067AC41, and the four `g_T15` lists at
0x0067BE2D, 0x0067BE37, 0x0067BE80 and 0x0067BE8A. A reader that forms its address by arithmetic from another symbol, or a listing that `objdump` desynchronised, is not covered. The lane kept no scan; the `lane/a54` review wrote its own and it finds the same sites (`workspace/logs/a54/review/reader_scan.py`, its output beside it).

## Values

`[C]` Every element of all 15 tables is given here, 882 in all: **278 listed** in 4 tables and **604 by rule** in 11 tables. For `g_PathDistNear` and `g_PathSearchTurnRows` no exact rule is known. `g_DirOctant` and `g_PathDirTriples` stay listed as the owner's ruling named them; each equals a description by cases, and whether that counts as a rule is the owner's open choice ([ADR-0031](../adrs/0031-constants-of-the-code-image.md)). `g_PathDirZero` is the tool's label for the two dwords at `0x006EB7D4`, which have no symbol.
Checksum: `zlib`'s CRC-32 of the table's elements in listed order, each packed as a little-endian i32 (the `u8` table too, widened), the same numbers as gate survey `path` holds, `[C]` read from the pinned image (sha256 in [inventory](../inventory.md)).

| Table | Elements | Given by | crc32 |
|---|---:|---|---:|
| `g_DirOctant` | 75 | listed | 3474250297 |
| `g_PathDirTriples` | 75 | listed | 2984211674 |
| `g_PathDistNear` | 64 | listed | 2545762225 |
| `g_PathStep8Long` | 16 | rule | 4218449362 |
| `g_PathSearchTurnRows` | 64 | listed | 1736307774 |
| `g_T15Step` | 32 | rule | 2096992061 |
| `g_T15DirFromStep` | 9 | rule | 4267223524 |
| `g_T15TurnB` | 16 | rule | 1590483018 |
| `g_T15NextB` | 16 | rule | 636168578 |
| `g_T15TurnA` | 16 | rule | 636168578 |
| `g_T15NextA` | 16 | rule | 3641255487 |
| `g_PathDir8` | 16 | rule | 4218449362 |
| `g_PathSignTable` | 81 | rule | 2847324179 |
| `g_PathDirTable` | 384 | rule | 3523208887 |
| `g_PathDirZero` | 2 | rule | 1696784233 |

### The rules

`[C]` **`path_survey.py rules` computes each rule's values and compares them with the pinned image element by element: 604 of 604 bit-identical, 0 mismatches**, and a mismatch fails gate survey `path` (`dirtab_rule_mismatches=0`). Each rule is `[C]` as an equality on the pinned image's elements. **It was found by matching the data and is no claim about how the table was generated**, nor about any other build. The survey holds the rules as its own code and the gate checks that code against the image; it doesn't read the block below. The block's words were checked once, at the `lane/a54b` review, by an implementation written from them alone: 604 of 604 (`workspace/logs/a54b/review/indep.py`). An edit to the block needs that check again.

Every result is stored as a signed 32-bit little-endian element. Below, arithmetic is on exact integers unless a line says otherwise, `&` is on two's complement, `sign(x)` is -1, 0 or 1, `/` between integers is exact where it is used, and `mod` gives 0 to the modulus minus one.

```
stepDx(d):  e = d & 7;  return sign(2 - min(e, 8 - e))

g_PathStep8Long, g_PathDir8     d 0..7    element [2 d] = stepDx(d)       element [2 d + 1] = stepDx(d - 2)
g_T15Step                       d 0..15   element [2 d] = stepDx(d - 2)   element [2 d + 1] = stepDx(d - 4)

g_T15DirFromStep                k 0..8, listed from 0x006F1E18:  i = k - 4
                                dx = ((i + 1) mod 3) - 1;  dy = (i - dx) / 3
                                element [k] = -1 when i = 0, else the one d in 0..7 with stepDx(d - 2) = dx and stepDx(d - 4) = dy

g_T15TurnA, g_T15NextB          d 0..15   element [d] = ((d & 6) + 2) & 7
g_T15NextA                      d 0..15   element [d] = ((d & 6) + 6) & 7
g_T15TurnB                      d 0..15   element [d] = (((d + 1) & 6) + 6) & 7

g_PathSignTable                 k 0..80, listed from 0x006EB3F0:  i = k - 40
                                a = ((i + 4) mod 9) - 4;  b = (i - a) / 9
                                element [k] = sign(a) when |a| >= |b|, else 0

g_PathDirTable                  q 0..127, row of three:  den = q * q + 127 * 127
                                element [3 q]     = the largest integer x >= 0 with x * x * den <= 4096 * 4096 * q * q
                                element [3 q + 1] = the largest integer y >= 0 with y * y * den <= 4096 * 4096 * 127 * 127
                                element [3 q + 2] = min(7, trunc(atan(q / 127.0) / (pi / 32.0)))

g_PathDirZero                   element [0] = 0, element [1] = 0
```

- **`g_PathDirTable`, widths and rounding.** Columns 0 and 1 are exact integers, every product below 2^63, so no floating point enters them; they are `trunc(4096 sin a)` and `trunc(4096 cos a)` for `a = atan(q / 127)` (`test_dirtable_relations`). Column 2 is IEEE-754 binary64: `q / 127.0` and the outer quotient round to nearest, `pi` is the double nearest to it, `atan` is the double function, and `trunc` goes toward zero. It has room: for `q` 1 to 126 the outer quotient is at least 0.0073 from any integer (`dirtab_z_margin_micro=7301`), so a double `atan` a few units in the last place out gives the same result; `q = 0` gives exactly 0; at `q = 127` the quotient is 8 within rounding and the `min` gives 7 on either side. Rows 0 and 127, as a check of a reimplementation: `0 4096 0`, `2896 2896 7`.
- **`g_T15TurnA`, `g_T15NextB`** share one rule; so do **`g_PathStep8Long`, `g_PathDir8`**. From the two lines above, `g_T15Step` row `d` is `g_PathStep8Long` row `(d - 2) & 7`, so it starts at `(0, -1)` and repeats at `d + 8`.
- **`g_PathSignTable`**, worked: `a = 3`, `b = 1` is index 12, entry `1`; `a = 1`, `b = 3` is index 28, entry `0`; so a target at `(3, 1)` steps `(1, 0)`.

### The listed tables

Generated by `python3 -I tools/path_survey.py dirmd <game.exe>`; one line per row of the shape, every entry the stored value (an `i32` shown signed; `g_PathDirTriples` is `u8`). `tools/test_path_survey.py` compares these blocks with the image. `[C]` for each: read from the pinned image at the address. The cell index of `g_DirOctant` and `g_PathDirTriples` is `5 dx' + dy' + 12`, so
line `n` is cell `n` (line 0 is `dx' = -2, dy' = -2`).

#### g_DirOctant  `0x006F1518`

```
5 4 6
4 5 6
4 3 5
4 3 2
3 4 2
6 5 4
5 4 6
4 3 5
3 4 2
2 3 4
6 7 5
6 7 5
6 7 5
2 1 3
2 1 3
6 7 0
7 0 6
0 1 7
1 0 2
2 1 0
7 0 6
0 7 6
0 1 7
0 1 2
1 0 2
```

#### g_PathDirTriples  `0x006F1648`

```
4 6 255
4 6 255
4 2 6
4 2 255
4 2 255
6 4 255
4 6 255
4 2 6
4 2 255
2 4 255
6 0 4
6 0 4
6 0 4
2 0 4
2 0 4
6 0 255
0 6 255
0 2 6
2 0 255
2 0 255
0 6 255
0 6 255
0 2 6
0 2 255
0 2 255
```

#### g_PathDistNear  `0x006F1698`

```
-1 -1 -1 0 2 4 6 8
-1 -1 0 1 2 4 6 8
-1 0 0 2 3 5 7 8
0 1 2 2 4 5 7 8
2 2 3 4 5 6 7 9
4 4 5 5 6 7 8 9
6 6 7 7 7 8 10 10
8 8 8 8 9 9 10 11
```

#### g_PathSearchTurnRows  `0x006F17D8`

```
0 1 6 3 4 5 2 7
0 1 6 3 1 3 6 1
0 1 1 1 1 1 2 7
1 1 1 1 1 3 6 1
6 4 3 6 1 3 2 7
7 7 7 7 7 5 2 7
0 7 7 7 7 5 2 7
0 7 2 5 7 5 2 7
```

## Open questions

- `[L]` Whether the path planners read `g_PathSearchTurnRows` entries 5 to 7 of rows 1 to 7: path/0002 § 5 tabulates the entries a child uses (five per row) and the root uses the eight of row 0;
  this doc lists all 64 values and does not say that the other 21 are never read.
- `[L]` The dword at `0x006F1644` (value 0) lies between `g_DirOctant` and `g_PathDirTriples` and is not listed; its reader, if any, is unknown.
