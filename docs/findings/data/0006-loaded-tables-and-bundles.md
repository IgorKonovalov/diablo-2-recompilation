# 0006 — The last loaded tables, their readers, and the COF bundles

> **Subsystem:** data/excel
> **Question:** Who reads `MonItemPercent`, `BodyLocs`, `PlayerClass`, `Events`, `Sounds`, `Composit`, `Overlay`, `SkillDesc` and `Arena`, does 1.14d open the COF bundles, `lut.dn1`, the colour `.dat` and the `.key` files, and does any of them feed a game rule?
> **Date:** 2026-11-10   **Plan:** [0068](../../plans/0068-game-files-coverage.md) Phase 2   **Status:** open (item 1 answered)

Static reading of the pinned `Game.exe` (objdump/r2 listing, `tools/xrefscan.py` raw scan, `tools/ghidra.sh xrefs` on
the lane's project copy), with the kept loader logs of [data/0001 § Plan 0038 batch H3b](0001-excel-loader.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load)
(run:2026-10-27-sweep-data-load) as the run-time side. The kept check outputs are under `workspace/logs/n68r/check/`
(`check-item1.txt`; hashes in `workspace/logs/n68r/n68r-manifest.sha256`, which passes `sha256sum -c` from
`workspace/logs/n68r/`).

## Answer (summary)

- [C] **`MonItemPercent` is loaded in every run and read by nothing.** `sub_00654F20_MonItemPctLoad`, called
  unconditionally from `DATATBLS_LoadAll` at 0x00619470, loads the 2 records into `g_pMonItemPercent` (0x0096D484) and
  the count into `g_nMonItemPercent` (0x0096D480); the six kept H3b runs that reach the loader log the call (return
  0x00654FAD, count 2, the archive `.bin`). The only other code that touches either global is the free at the excel
  unload and a bounds-checked record getter, `sub_00654FE0_MonItemPctGetRecord`, which has **no caller**: no `call`,
  `jmp` or `jcc` rel32 and no absolute pointer to it anywhere in the image (`tools/xrefscan.py`), and no reference in
  Ghidra. The table address getter at 0x00654FD0 has none either. Two independent tools agree on all six addresses.
  (fn:sub_00654F20_MonItemPctLoad@0x00654F20, fn:sub_00654FE0_MonItemPctGetRecord@0x00654FE0, 0x00619470,
  0x006192A1, run:2026-10-27-sweep-data-load)
- [I] **So no column changes a drop, and no draw comes from it.** No row is chosen (neither `Composited` nor
  `NonComposited`), and the death drop chain `sub_005A6830_MonDeathDrop` → `MONSTER_DropItems` →
  `TC_ResolveDrops` has nothing to add for it: the items/tc spec's draw order is complete as far as this table goes.
  The `[I]` is the scan's one blind spot, an address computed at run time (§ 1.3); a harness watch on the records is
  routed in a backlog entry (§ 1.4).
  (fn:MONSTER_DropItems@0x005A6600, fn:TC_ResolveDrops@0x0055A6D0)
- [C] **Field widths: four `u8` at `+0x0..+0x3`, in column order.** The loader's descriptor gives each of the four
  columns type 4 (u8, [data/0001 § 1](0001-excel-loader.md#1-load-path-of-one-table)) and offsets 0, 1, 2, 3, in
  `.txt` order; `TreasureClassPercent`'s offset 2 is tied by the data (byte `+0x2` = 20 in both records, the kept
  `XFLW` head `02000000 00001400 00001400`). The widths of the three zero columns rest on the descriptor alone, `[I]`.
  (0x00654F64–0x00654FA1)

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00654F20` | `sub_00654F20_MonItemPctLoad` | builds the 4-column descriptor, `DATATBLS_LoadTable("monitempercent", …, &g_nMonItemPercent, 4)`, stores the records | C |
| `0x00654FC0` | `sub_00654FC0_MonItemPctFree` | `DATATBLS_FreeTable(g_pMonItemPercent)` at the excel unload (called from 0x006192A1) | I |
| `0x00654FD0` | `sub_00654FD0_MonItemPctTable` | returns `&g_nMonItemPercent` (count, then records); no caller | I |
| `0x00654FE0` | `sub_00654FE0_MonItemPctGetRecord` | `stdcall(idx)`: `&g_pMonItemPercent[idx]` if `0 ≤ idx < count` and `idx ≠ −1`, else 0; fatal on a null table; no caller | I |
| `0x0096D480` | `g_nMonItemPercent` | record count (2) | C |
| `0x0096D484` | `g_pMonItemPercent` | the 4-byte records | C |

## 1. `MonItemPercent` (plan item 1)

### 1.1 The loader

```asm
; sub_00654F20_MonItemPctLoad (trimmed). ECX = the pool; EDX = 4 for every field's type.
0x00654F28  mov edx, 4
0x00654F2D  push edx                       ; recSize 4
0x00654F2E  push 0x0096D480                ; &g_nMonItemPercent
0x00654F5D  push eax                       ; descriptor at [ebp-0x64]
0x00654F5E  push "monitempercent"
0x00654F64  {"HeartPercent",         type 4, len 0, off 0}
0x00654F6E  {"BodyPartPercent",      type 4, len 0, off 1}
0x00654F7F  {"TreasureClassPercent", type 4, len 0, off 2}
0x00654F90  {"ComponentPercent",     type 4, len 0, off 3}
0x00654FA1  {"end"}
0x00654FA8  call DATATBLS_LoadTable
0x00654FAD  mov [0x0096D484], eax          ; g_pMonItemPercent
```

- [I] Each descriptor entry is the 20-byte `{column, type, len, offset, link}` of data/0001 § 1; the stack slots are
  zeroed first, so `len` and `link` are 0. Type 4 is a u8 cell. (0x00654F26–0x00654FA1)
- [C] The call runs in every run that reaches the table load: `DATATBLS_LoadAll` calls the loader in its straight
  sequence (0x00619470, no branch around it), and the kept H3b logs show the `DATATBLS_LoadTable` call returning to
  0x00654FAD with `count` 2 in all six runs that reach it (stock, loose, direct, clamp at sequence 71; txt and dtxt at
  89, after the `.txt` was compiled). The stock run reads the archive `.bin` (sha256 `01bfe3f2…`, the table doc's).
  (fn:DATATBLS_LoadAll@0x00619300, 0x00619470, run:2026-10-27-sweep-data-load; `check-item1.txt`)

### 1.2 Every reader

The table's records are reachable only through `g_pMonItemPercent` (0x0096D484), and its count only through
`g_nMonItemPercent` (0x0096D480).

| Reference | Function | What it does | Ghidra | raw scan |
|---|---|---|---|---|
| 0x00654F2E | `MonItemPctLoad` | pushes `&g_nMonItemPercent` as the count out-pointer | DATA | abs32 0x00654F2F |
| 0x00654FAD | `MonItemPctLoad` | stores the record pointer | WRITE | abs32 0x00654FAE |
| 0x00654FC0 | `MonItemPctFree` | loads the pointer to free it | READ | abs32 0x00654FC1 |
| 0x00654FD0 | `MonItemPctTable` | `mov eax, 0x0096D480; ret` | not disassembled | abs32 0x00654FD1 |
| 0x00654FE6 | `MonItemPctGetRecord` | bounds test against the count | READ | abs32 0x00654FE8 |
| 0x00654FF3 | `MonItemPctGetRecord` | loads the pointer, returns `&rec[idx]` | READ | abs32 0x00654FF4 |

- [C] No other instruction or data word names either global: `tools/xrefscan.py` finds 3 absolute hits for each, all
  listed above, and Ghidra lists the same references (it has no function at 0x00654FD0). (`check-item1.txt`)
- [C] The two getters are dead code. `tools/xrefscan.py 0x00654FD0 0x00654FE0`: 0 hits each (no `E8`/`E9`/`0F 8x`
  rel32 to them in an executable section, no 4-byte pointer to them in any section, so no vtable or callback table
  holds them). Ghidra's `xrefs 0x00654FE0` lists only the getter's own callees (the error reporter at 0x00408090,
  0x00408A60, 0x00681E09). `MonItemPctLoad` and `MonItemPctFree` have one caller each, 0x00619470 and 0x006192A1.
  (`check-item1.txt`)
- [I] The getter itself, for a reimplementer who wants its contract: `stdcall(int idx)`, returns 0 when
  `idx ≥ count` (signed `jge`) or `idx = −1`, else `g_pMonItemPercent + 4·idx`; a null table pointer or a null result
  goes to the fatal reporter with source lines `0x6DC` and `0x6DD`. (0x00654FE0–0x0065502C)

### 1.3 What that means for the drop chain

- [I] No code reads a percentage, so no code picks a row, makes a draw on it, or skips a drop because of it. A
  monster's death drop runs `sub_005A6830_MonDeathDrop` → `MONSTER_DropItems` → `TC_DropByIndex` →
  `TC_ResolveDrops` with no `MonItemPercent` step anywhere (none of them, and no other function, calls the getter);
  the draw order in items/0001 and the items/tc spec stands as written.
  (fn:sub_005A6830_MonDeathDrop@0x005A6830, fn:MONSTER_DropItems@0x005A6600, fn:TC_ResolveDrops@0x0055A6D0)
- [I] Why `[I]` and not `[C]`: a raw scan under-approximates an address computed at run time (base plus offset). No
  instruction forms 0x0096D480/0x0096D484 from a nearby base: the closest absolute operands, 0x0096D47C (a store at
  0x00640F12) and 0x0096D488 (0x0065A463), belong to other tables' loaders. That is a reading, not a run.

### 1.4 Kept-log check, and what is routed

- [C] The kept logs hold the load (above), not a read. No kept log holds a value of this table being used: the H2a
  drop logs (run:2026-10-20-sweep-items-tc) log `MDD0` → `MDDX` → `MDI` → `TCR` per death, with the monster seed at
  `TCR`, but not at the death, so they cannot show that nothing drew in between. (`workspace/logs/h2a/`)
- The run-time absence is routed as a harness piece:
  [backlog entry](../../backlog/2026-11-10-reverser-reverser-plan-0068-monitempercent-read-watch.md) (an `rwatch` on
  the 8 record bytes over a session with kills, with a control watch on a table the death path does read). It would
  raise § 1.3's `[I]`. It does not block Phase 4: with no reader there is nothing to carry.

### 1.5 Layout, for the table doc

- [C] `TreasureClassPercent` is the u8 at `+0x2`: descriptor offset 2, and the data's only non-zero byte (20, both
  records). (0x00654F7F–0x00654F89, `XFLW` head in run:2026-10-27-sweep-data-load)
- [I] `HeartPercent` `+0x0`, `BodyPartPercent` `+0x1`, `ComponentPercent` `+0x3`, all u8: the descriptor, which
  settles the probe's alternative fits (a `u16` at `+0x0` or `+0x2`): every field is type 4 at its own byte. The data
  cannot test them (all 0). (0x00654F64–0x00654F9A)

## Data touched

`tbl:MonItemPercent.txt:HeartPercent`, `tbl:MonItemPercent.txt:BodyPartPercent`,
`tbl:MonItemPercent.txt:TreasureClassPercent`, `tbl:MonItemPercent.txt:ComponentPercent` (loaded only).

## Dead ends

- Looking for the reader near the TC code: the loader sits between `TC_GetChestTC` (0x00654E80) and the superunique
  getter, which only reflects the source file order of the table loaders.

## Open questions

- `[L]` Whether any 1.14d code path reaches `MonItemPercent` through a computed address: the harness watch of § 1.4
  resolves it.
