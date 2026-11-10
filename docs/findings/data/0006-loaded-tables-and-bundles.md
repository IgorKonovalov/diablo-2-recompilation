# 0006 — The last loaded tables, their readers, and the COF bundles

> **Subsystem:** data/excel
> **Question:** Who reads `MonItemPercent`, `BodyLocs`, `PlayerClass`, `Events`, `Sounds`, `Composit`, `Overlay`, `SkillDesc` and `Arena`, does 1.14d open the COF bundles, `lut.dn1`, the colour `.dat` and the `.key` files, and does any of them feed a game rule?
> **Date:** 2026-11-10   **Plan:** [0068](../../plans/done/0068-game-files-coverage.md) Phase 2   **Status:** answered (items 1–5; the run-time absences and the skill-level bonus routed as harness pieces)

Static reading of the pinned `Game.exe` (objdump/r2 listing, `tools/xrefscan.py` raw scan, `tools/ghidra.sh xrefs` and
`decompile` on the lane's project copy), with the kept loader logs of [data/0001 § Plan 0038 batch H3b](0001-excel-loader.md#plan-0038-batch-h3b-run2026-10-27-sweep-data-load)
(run:2026-10-27-sweep-data-load) as the run-time side. The kept check outputs are under `workspace/logs/n68r/check/`
(`check-item1.txt`, `check-items2-5.txt`, `check-cul.txt`, `bundles.txt` from `python3 -I tools/n68r_bundles.py workspace/merged --list`;
hashes in `workspace/logs/n68r/n68r-manifest.sha256`, which passes `sha256sum -c` from `workspace/logs/n68r/`).

Every table global below is also reachable as `g_DataTables` (0x0096BC30, the value of `g_pDataTables` 0x00744304)
plus an offset, the form most readers use; each reader search covers both forms (absolute operand and
`[reg + offset]`).

## Answer (summary)

- [C] **`MonItemPercent` is loaded in every run** (the logs below). [I] **Nothing references it but its loader, its free and two getters that have no caller** (a static scan; no read has been watched). `sub_00654F20_MonItemPctLoad`, called
  unconditionally from `DATATBLS_LoadAll` at 0x00619470, loads the 2 records into `g_pMonItemPercent` (0x0096D484,
  `g_DataTables + 0x1854`) and the count into `g_nMonItemPercent` (0x0096D480, `+0x1850`); the six kept H3b runs that
  reach the loader (`workspace/logs/h3b/h3b-s2-3101-stock`, `3102-txt`, `3103-loose`, `3104-direct`, `3105-dtxt`, `3107-clamp`, `.log`) log the call (`XTBL` return 0x00654FAD, count 2, the archive `.bin`). The only other code that touches
  either global is the free at the excel unload and a bounds-checked record getter,
  `sub_00654FE0_MonItemPctGetRecord`, which has **no caller**: no `call`, `jmp` or `jcc` rel32 and no absolute pointer
  to it anywhere in the image (`tools/xrefscan.py`), and no reference in Ghidra. The table address getter at
  0x00654FD0 has none either, and no instruction uses `+0x1850` or `+0x1854` off a base register. (§ 1;
  fn:sub_00654F20_MonItemPctLoad@0x00654F20, fn:sub_00654FE0_MonItemPctGetRecord@0x00654FE0, 0x00619470,
  0x006192A1, run:2026-10-27-sweep-data-load)
- [I] **So no `MonItemPercent` column changes a drop, and no draw comes from it.** No row is chosen (neither
  `Composited` nor `NonComposited`), and the death drop chain `sub_005A6830_MonDeathDrop` → `MONSTER_DropItems` →
  `TC_ResolveDrops` has nothing to add for it: the items/tc draw order is complete as far as this table goes. The `[I]`
  is the static scan's limit (§ 1.3); a harness read watch is routed (§ 1.4). (fn:MONSTER_DropItems@0x005A6600,
  fn:TC_ResolveDrops@0x0055A6D0)
- **`MonItemPercent` field widths, raised in part.** [C] `TreasureClassPercent` is the u8 at `+0x2`: the loader's
  descriptor gives it type 4 (u8) and offset 2, and the data's only non-zero byte is `+0x2` (20, both records).
  [I] `HeartPercent` `+0x0`, `BodyPartPercent` `+0x1`, `ComponentPercent` `+0x3`, each a u8 (type 4): the descriptor
  alone, since the data is 0. (§ 1.5; 0x00654F64–0x00654FA1)
- [I] **`BodyLocs`, `PlayerClass` and `Events` are index spaces, not loaded tables.** Every stored reference is the
  row index, compared or used as a number: body location 0..10 (ItemTypes `BodyLoc1/2`, CharStats `itemNloc`,
  MonEquip `loc1..3`), class 0..6 against the unit's class word (ItemTypes `Class`, `StaffMods`, the affixes'
  `classspecific`/`class`, Skills `charclass`, CubeMain `class`, CharTemplate `Class`), event id 0..12 (ItemStatCost
  `itemevent1/2`, Skills `auraevent1..3`). The readers are already in findings; § 2 lists them. New here (§ 2.3): the
  17 `UNIT_DispatchEvent` calls pass the ids 0, 1, 2, 3, 5, 6, 7, 9, 10, 11, 12 and 13 as constants, so **events 4
  (`doactive`) and 8 (`domissileattack`) are never dispatched**, and stat 195's `itemevent2` handler never runs; the
  item-stat registrars skip an event ≤ 0 (so `hitbymissile` can never be an item event), the skill registrars only
  one < 0. (fn:UNIT_DispatchEvent@0x005C0C30, fn:sub_0056E740_AddStatEvent@0x0056E740, 0x0055B867, 0x005C95D8)
- [I] **`Sounds`: a stock run loads no `sounds.bin`.** The table name `sounds` (0x006ED50C) has one reference, the
  `-txt`-only call 0x00659C16; the only other `sounds` file read is `sub_00481950_SoundTablesLoad`'s text read of
  `sounds.txt` (0x0048203A), which runs only when the sound device is up (0x0048226A). None of the four stock-mode H3b
  runs (all `-ns`) reads any `sounds` file [C] (run:2026-10-27-sweep-data-load). data/0001's two sentences that said
  otherwise are corrected there. (§ 2.4)
- [I] **`SkillDesc` is rule-bearing in two places, both server-side.** `sub_00644180_SkillLevelBonus`, the bonus
  every effective skill level adds to the base (`SKILLS_ManaOk`, the skill-level reads), adds stat 188
  `item_addskill_tab` with param `8·class + SkillPage − 1` when the skill's SkillDesc `SkillPage` (`+0x2`) is non-zero;
  and `sub_00627AF0_SkillHasDesc` (the skill's `skilldesc` index below the SkillDesc count) gates a legacy save's stat
  107 (save/0001). The rest of its readers are the client's skill tree. The bonus function's whole formula is in
  § 3.2; no spec states it. (fn:sub_00644180_SkillLevelBonus@0x00644180, fn:sub_00627AF0_SkillHasDesc@0x00627AF0)
- [I] **`Overlay`, `Composit`, `MonSounds`, `AutoMap`: client only.** No server code reads a record; the server reads
  only `Overlay`'s count, as the bound on an overlay id before it sets one. **`Arena` is read by the server** at
  every kill and player death in every game (`sub_0053F720_ArenaScoreKill`, from `sub_0057CCB0_UnitKilled` and
  `sub_00580EC0_PlayerDeath`), into a per-player score that no core-area rule reads in this lane's reading. (§ 3; fn:sub_00621E40_UnitSetOverlayStat@0x00621E40,
  fn:sub_0053F720_ArenaScoreKill@0x0053F720)
- [I] **The COF bundles feed the client's COF cache only.** At an act load the client opens `cmncof_a1..a4.d2` and
  `cmncof_a6.d2` (one per act, a name table at 0x006D6C30) and hashes their records into `g_ClientCofCache`
  (0x007A78F0), which only the client's drawing code reads. `chars_cof.d2`, `cmncof_a5.d2` and `cmncof_a7.d2` are
  named nowhere in the image. The loader's record layout parses all eight files to the byte with 0 errors (6 726
  COFs) [C] (`bundles.txt`); 11 of them differ from `animdata.d2` in frames per direction and 2 in event frames, none
  of which reaches the server's mode lengths. (§ 4)
- [I] **`lut.dn1`, `a1npc.txt`..`a5npc.txt`: never opened** (no name in the image). The colour `.dat` files, the
  `.key` maps and `gateways.txt` are opened by client code only. (§ 5; 0x00476EA0, 0x00469650, 0x00518300)

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00654F20` | `sub_00654F20_MonItemPctLoad` | builds the 4-column descriptor, `DATATBLS_LoadTable("monitempercent", …, &g_nMonItemPercent, 4)`, stores the records | C |
| `0x00654FC0` | `sub_00654FC0_MonItemPctFree` | `DATATBLS_FreeTable(g_pMonItemPercent)` at the excel unload (called from 0x006192A1) | I |
| `0x00654FD0` | `sub_00654FD0_MonItemPctTable` | returns `&g_nMonItemPercent` (count, then records); no caller | I |
| `0x00654FE0` | `sub_00654FE0_MonItemPctGetRecord` | `stdcall(idx)`: `&g_pMonItemPercent[idx]` if `0 ≤ idx < count` and `idx ≠ −1`, else 0; fatal on a null table; no caller | I |
| `0x0096D480` | `g_nMonItemPercent` | record count (2) | C |
| `0x0096D484` | `g_pMonItemPercent` | the 4-byte records | C |
| `0x0053F4B0` | `sub_0053F4B0_ArenaCreate` | the game's arena record at `game+0x1D28` (both game creators) | I |
| `0x0053F500` | `sub_0053F500_ArenaFree` | frees it | I |
| `0x0053F530` | `sub_0053F530_ArenaPlayerCreate` | a player's score record at player data `+0x34` | I |
| `0x0053F720` | `sub_0053F720_ArenaScoreKill` | the kill and death scoring from the Arena row | I |
| `0x006649B0` | `sub_006649B0_ArenaLoad` | loads `arena` into `g_pArena` | I |
| `0x00664AB0` | `sub_00664AB0_ArenaGetRecord` | `ECX` the arena type; fatal for ≥ 1 | I |
| `0x0096D608` | `g_pArena` | the Arena records (`g_DataTables + 0x19D8`) | I |
| `0x00644150` | `sub_00644150_ShrineSkillBonus` | 2 when the unit has state 134, else 0 | I |
| `0x00644180` | `sub_00644180_SkillLevelBonus` | the bonus added to a skill's base points (§ 3.2) | I |
| `0x00627AF0` | `sub_00627AF0_SkillHasDesc` | the skill's `skilldesc` index is a SkillDesc row | I |
| `0x0096C7BC` | `g_pSkillDesc` | SkillDesc records (`+0xB8C`) | I |
| `0x0096C7C4` | `g_nSkillDesc` | SkillDesc count (`+0xB94`) | I |
| `0x00664150` | `sub_00664150_OverlayLoad` | loads `overlay` | I |
| `0x0096C7EC` | `g_pOverlay` | Overlay records (`+0xBBC`) | I |
| `0x0096C7F0` | `g_nOverlay` | Overlay count (`+0xBC0`), the server's overlay-id bound | I |
| `0x0096C6B4` | `g_pMonSounds` | MonSounds records (`+0xA84`) | I |
| `0x0096C6BC` | `g_nMonSounds` | MonSounds count | I |
| `0x0046F310` | `sub_0046F310_CofBundleLoadAct` | client: opens `cmncof_a<act>.d2` at an act load | I |
| `0x0046DDF0` | `sub_0046DDF0_CofBundleParse` | client: walks the bundle's records into the COF cache | I |
| `0x006D6C30` | `g_CofBundleNames` | the five bundle names, by act | I |
| `0x007A78F0` | `g_ClientCofCache` | client COF cache (512 hash buckets at `+0x0C`) | I |
| `0x00476EA0` | `sub_00476EA0_ColorDatLoad` | client: `GreenBlood.dat`, `RandTransforms.dat` | I |
| `0x00477170` | `sub_00477170_MonPalShiftLoad` | client: a monster's `\Cof\palshift.dat` | I |

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

- [I] No other instruction or data word names either global: `tools/xrefscan.py` finds 3 absolute hits for each, all
  listed above, and Ghidra lists the same references; an independent r2 search at the architect check (`/x` of both
  addresses and of the `0x1850`/`0x1854` displacements) found the same hits and no displacement operand (it has no function at 0x00654FD0). (`check-item1.txt`)
- [I] The two getters are dead code, by a static scan (a computed call target is not seen). `tools/xrefscan.py 0x00654FD0 0x00654FE0`: 0 hits each (no `E8`/`E9`/`0F 8x`
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
- [I] Why `[I]` and not `[C]`: the scans cover the two ways the image names a table (the absolute address, and
  `g_DataTables + 0x1850/0x1854` off a base register: `check-items2-5.txt` finds no such operand outside stack
  frames, and Ghidra, which resolves the `g_pDataTables` form for other tables, lists none). Neither sees an address
  built at run time some other way, and no run has watched the records. (0x0096D480, 0x0096D484)

### 1.4 Kept-log check, and what is routed

- [I] The kept logs hold the load (above), not a read. No kept log holds a value of this table being used: the H2a
  drop logs (run:2026-10-20-sweep-items-tc) log `MDD0` → `MDDX` → `MDI` → `TCR` per death, with the monster seed at
  `TCR`, but not at the death, so they cannot show that nothing drew in between. (`workspace/logs/h2a/`)
- The run-time absence is routed as a harness piece:
  [backlog entry](../../backlog/2026-11-10-reverser-reverser-plan-0068-monitempercent-read-watch.md) (an `rwatch` on
  the 8 record bytes over a session with kills, with a control watch on a table the death path does read). It would
  raise § 1.3's `[I]`. It does not block Phase 4: with no reader there is nothing to carry. (0x0096D484)

### 1.5 Layout, for the table doc

- [C] `TreasureClassPercent` is the u8 at `+0x2`: descriptor offset 2, and the data's only non-zero byte (20, both
  records). (0x00654F7F–0x00654F89, `XFLW` head in run:2026-10-27-sweep-data-load)
- [I] `HeartPercent` `+0x0`, `BodyPartPercent` `+0x1`, `ComponentPercent` `+0x3`, all u8: the descriptor, which
  settles the probe's alternative fits (a `u16` at `+0x0` or `+0x2`): every field is type 4 at its own byte. The data
  cannot test them (all 0). (0x00654F64–0x00654F9A)

## 2. `BodyLocs`, `PlayerClass`, `Events` and `Sounds` (plan item 2)

These four `.bin` files load only under `-txt` (data/0001 H3b `[C]`), so a stock run never holds the code lists.
What it holds are the compiled tables' stored row indices, read as plain numbers. The readers below are the ones the
named findings already give; this section collects them per index space and adds what the event dispatch shows.
(fn:DATATBLS_LoadCodeLists@0x00612750, run:2026-10-27-sweep-data-load)

### 2.1 `BodyLocs`: body location 0..10

| Stored in | Offset | Reader | Use | Spec |
|---|---|---|---|---|
| ItemTypes `BodyLoc1`, `BodyLoc2` | `+0xA`, `+0xB` (u8) | `sub_0062EA80_ItemBodyLocs`, `sub_0055D710_ItemAutoEquipSlot` (items/0014) | the auto-equip slot choice | items/inventory (auto-equip) |
| CharStats `item1loc..item10loc` | `+0x60 + 8k` (u8) | `sub_00534D60_StartItemSlot` (player/0001 § 5) | equip a starting item at that location; 0 → inventory | player/creation |
| MonEquip `loc1..loc3` | `+0x14..+0x16` (u8; read signed at 0x005D6C48) | `sub_005D6B60_MonEquipInit` at 0x005D6BF0 and 0x005D6C48, then `sub_0063BDE0_InvGetBodyLocItem` | the monster's equip slot | monsters/stats (MonEquip) |

- [I] The location is the BodyLocs row index (0 `None` .. 10 `Gloves`) and goes straight into the inventory's body
  location calls; no reader translates it through a code. (fn:sub_0062EA80_ItemBodyLocs@0x0062EA80,
  fn:sub_00534D60_StartItemSlot@0x00534D60, fn:sub_005D6B60_MonEquipInit@0x005D6B60, 0x005D6BF0, 0x005D6C48)

### 2.2 `PlayerClass`: class 0..6

| Stored in | Offset | Reader | Compared with | Spec |
|---|---|---|---|---|
| ItemTypes `Class` | `+0x21` | `ITEMS_IsClassSpecific` (items/0002) | 7 = none | items/quality, items/affixes |
| ItemTypes `StaffMods` | `+0x1F` | `sub_0062BBD0_ItemTypeStaffMods`, `ITEMS_RollStaffMods` (items/0005) | Skills `charclass` | items/affixes |
| MagicPrefix/MagicSuffix `classspecific`, `class` | `+0x66`, `+0x67` | the affix filter 0x005C16D3–0x005C17AD (items/0005) | the item type's class | items/affixes |
| Skills `charclass` | `+0x0C` (s8 at 0x006441DD) | `ITEMS_RollStaffMods` (0x005C1285), `sub_00644180_SkillLevelBonus` (0x006441DD, § 3.2) | the staff-mods class; the unit's class word `unit+0x04` | items/affixes; skills (§ 3.2) |
| CubeMain `class` | `+0x03` | the recipe test (items/0008) | 0xFF or the player's class | items/cube |
| CharTemplate `Class` | `+0x1E` | `sub_006657C0_CharTemplateClass` (player/0001) | — (the template game's class) | player/creation |

- [I] Every comparison is with the unit's class word (player `unit+0x04`, 0 Amazon .. 6 Assassin), which is also the
  d2s class byte; the `Expansion` marker row of `PlayerClass.txt` takes no index. (fn:ITEMS_IsClassSpecific@0x00629F70,
  fn:ITEMS_RollStaffMods@0x005C1260, 0x006441DD, fn:sub_006657C0_CharTemplateClass@0x006657C0)

### 2.3 `Events`: event id 0..12, and what is dispatched

Registration (who stores an event id on a unit, `sub_0056E740_AddStatEvent`, 11 calls):

- [I] **Item stats** (ItemStatCost `itemevent1` `+0x48`, `itemevent2` `+0x4A`, each with its `itemeventfunc`
  `+0x4C`/`+0x4E`): `sub_0055B800_MonStatCallback` (0x0055B867, 0x0055B8A3) and `sub_005C4470_SummonInitStats`
  (0x005C453B, 0x005C4589, 0x005C4686, 0x005C46D4) read the id as `s16` and **register only when it is `> 0`**
  (`cmp word, 0; jle` / `test ax, ax; jle`). A blank cell is stored −1 (`0xFFFF`) and skipped; id 0
  (`hitbymissile`) would be skipped too, and no stock stat uses it.
- [I] **Skills** (`auraevent1..3` `+0x84..+0x88`, with `auraeventfunc1..3` `+0x8A..+0x8E`): the three loops at
  0x005C95D2, 0x005C9D42 and 0x005D9273 (and 0x005C48F6 for a summon) read each id as `s16` and register when it is
  **`≥ 0`** (`test ax, ax; jl`), so `hitbymissile` (0) registers for Chilling Armor (skill 60, function 1). The
  fourth caller, 0x005C377B (`sub_005C35C0_CurseApplyCb`), takes the id from a runtime record, not a table.
- Not read by any of the 11 registrar calls: Skills `auratgtevent` (`+0x90`), `passiveevent` (`+0xB8`) and States
  `cltevent` (`+0x30`). The two Skills columns are blank (−1) in every stock row; `cltevent` is set in one state (id 0,
  function 1). Their readers, if any, were not followed.

Dispatch (`UNIT_DispatchEvent`, `EDX` the id; it runs each handler record whose byte `+0x00` equals the id,
0x005C0C69):

| Id | Name (Events row) | Call sites (17 in all, `tools/xrefscan.py 0x005C0C30`) |
|---|---|---|
| 0 | `hitbymissile` | `MISSILE_HitUnit` 0x005AE08A, 0x005AE0FE; `sub_005B01F0_MissDo31SidePair` 0x005B02CA |
| 1 | `damagedinmelee` | `COMBAT_ApplyDamage` 0x0057C7F3 (falling through from 0x0057C7E8) |
| 2 | `damagedbymissile` | `COMBAT_ApplyDamage` 0x0057C7F3 (joined from 0x0057C7D1 via 0x0057C7D6) |
| 3 | `attackedinmelee` | `COMBAT_BuildDamage` 0x0057BCAD; `COMBAT_DeliverQueued` 0x0057D61F |
| 5 | `domeleedamage` | `COMBAT_ApplyDamage` 0x0057C7E3 |
| 6 | `domissiledamage` | `COMBAT_ApplyDamage` 0x0057C7CC |
| 7 | `domeleeattack` | `COMBAT_DeliverQueued` 0x0057D60D |
| 9 | `kill` | `COMBAT_ApplyDamage` 0x0057C970; `sub_005A6920_MonRegenEvent` 0x005A6AFF |
| 10 | `killed` | `COMBAT_ApplyDamage` 0x0057C95E; `sub_005A6920_MonRegenEvent` 0x005A6AEB |
| 11 | `absorbdamage` | `COMBAT_ApplyReductions` 0x0057C2FC |
| 12 | `levelup` | `PLAYER_AddExperience` 0x0057E58A; `MERC_AddExp` 0x0057E979 |
| 13 | (no Events row) | `sub_005A6FF0_MonDeathEvent` 0x005A72CD |

- [I] Each call passes its id as a constant (`mov edx, imm` or `xor edx, edx` before the call); the one join
  (0x0057C7ED) merges the constants 1 and 2. So the ids are the Events row indices, read by name from the sites
  above. (`check-items2-5.txt`)
- [I] **Ids 4 (`doactive`) and 8 (`domissileattack`) are never dispatched**, so a handler registered on them never
  runs. On stock data that is stat 195 `item_skillonattack`'s `itemevent2` (8, function 20); its `itemevent1` (7,
  `domeleeattack`) is dispatched, from `COMBAT_DeliverQueued` only. Whether a missile attack reaches that call was not
  followed. (0x0057D606, fn:COMBAT_DeliverQueued@0x0057D4F0)
- [I] Id 13 is dispatched at a monster's death but no table can register a handler on it (the Events rows end at 12,
  and the runtime registrar 0x005C377B was not followed for its id).

### 2.4 `Sounds`

- [I] The table name string `sounds` (0x006ED50C) has one reference, 0x00659C11, the push for the 2-byte
  `DATATBLS_LoadTable` call 0x00659C16 that the function at 0x00659BB0 runs only under `-txt` (data/0001 H3b). No other
  call loads `sounds.bin`.
- [I] The only other `sounds` read is `sub_00481950_SoundTablesLoad`: `wsprintf("%s\\sounds.txt")` (0x0048203A) and
  `soundenviron.txt` (0x004820E1), read as text. Its one caller, `sub_00482260_ClientSoundInit` (0x0048226C), calls it
  only when `0x00513B50` returns non-zero, the sound device word `0x00881768` (archaeology/0003); under `-ns` the
  device is not started.
- [C] In the four stock-mode H3b runs (stock, loose, direct, clamp; `tools/d2run.py` passes `-ns` by default and the
  driver lines name no `--sound`) no file named `sounds.bin`, `sounds.txt` or `soundenviron.txt` is opened; under
  `-txt` (txt, dtxt) `sounds.txt` and `sounds.bin` are, by the 0x00659C16 path (4 lines each run).
  (`check-items2-5.txt`, run:2026-10-27-sweep-data-load)
- So a stock run with sound on reads `sounds.txt` as text and never `sounds.bin`; with `-ns` it reads neither. The two
  data/0001 sentences that said "`sounds.bin` is also loaded" and "the full `sounds` table loads in every run" carry a
  dated correction pointing here.

## 3. `Composit`, `Overlay`, `SkillDesc`, `Arena` (plan item 3), with `MonSounds` and `AutoMap`

| Table | Records / count | Record readers | Server reads | Verdict |
|---|---|---|---|---|
| `Composit` | `g_pComposit` 0x0096D4EC (`+0x18BC`) | `sub_0065B5E0_CompositRecord` only, called from the client 0x004DA7A5 (in 0x004DA790, called from 0x00470289) | none | presentation |
| `Overlay` | 0x0096C7EC (`+0xBBC`) / count 0x0096C7F0 (`+0xBC0`) | client drawing (0x0046D9DA, 0x0046E262, 0x0046E4B0, `sub_0046EE80_ItemCelDrawUi`, `ITEMGFX_SelectCelName`, `sub_004DB7B0_GfxDescFromUnit`) and the getter 0x00664740 (client callers 0x004D866B, 0x004D99C0..) | the count only | presentation |
| `SkillDesc` | 0x0096C7BC (`+0xB8C`) / count 0x0096C7C4 (`+0xB94`) | the client skill tree (0x004A..0x004E readers); `sub_004A89D0_SkillDescRec` | `SkillPage` in the skill-level bonus; the count in `SkillHasDesc`; the description missiles in `SKILLS_CalcVar` codes 43–48 | **rule-bearing** (§ 3.2) |
| `Arena` | `g_pArena` 0x0096D608 (`+0x19D8`) | `sub_00664AB0_ArenaGetRecord` from `sub_0053F720_ArenaScoreKill` | every column but the name | server state, no core-area rule (§ 3.3) |
| `MonSounds` | 0x0096C6B4 (`+0xA84`) / count 0x0096C6BC | getters 0x00656F90, 0x00656FC0, called from the client 0x004CA410 and 0x004F4F40 | none | presentation |
| `AutoMap` | copied into the client automap cells by `sub_0061FCF0_AutomapTxtLoad` | `sub_0061FFF0_AutomapCellFind` (rng/0002: a client automap tile pick) | none | presentation |

- [I] For each table the record global's base-offset form has no further reader: the raw listing finds `+0x18BC`,
  `+0x19D8` and `+0xA84` nowhere, `+0xBBC` only at the Overlay readers above (and one unrelated
  `[ecx+0xBBC]` store in `sub_006BEAD0_NetQueuePop`), `+0xB8C` only at client sites and `CALC_Compile` (0x006C3271,
  a different struct). (`check-items2-5.txt`)

### 3.1 `Overlay`'s count on the server

- [I] Ghidra lists 41 reads of `g_DataTables + 0xBC0`, Overlay's record count: 15 below 0x00500000 (the client's
  drawing code, by the functions above; not each read), the 8 Overlay getters 0x00664560–0x00664780 (7 of them with no
  caller, 0x00664740 called by the client), and 18 server sites from 0x0056F23A to 0x005DA7A5 plus
  `sub_00621E40_UnitSetOverlayStat` (0x00621E50). The three read here (0x005715CA, 0x005CAD17, 0x00621E50) bound an
  overlay id (`id < 0` or `id ≥ count` → skip) before setting it on a unit or sending it. No server site reads a
  record, so no Overlay column (frames, timing) reaches a server rule; what a reimplementation needs is the row count
  as that bound. (fn:sub_00621E40_UnitSetOverlayStat@0x00621E40, 0x00621E50, 0x005CAD17, `check-items2-5.txt`)

### 3.2 `SkillDesc` on the server: the skill-level bonus

`sub_00644180_SkillLevelBonus(entry)` (stdcall; the unit in `ESI`) is the term `SKILLS_GetSkillLevel(unit, entry, 1)`
adds to the base points, and the bonus `SKILLS_ManaOk` adds (skills/0001). Callers: `SKILLS_GetSkillLevel`
0x006442C3, 0x00644322 (in 0x00644300), `sub_00644AA0_SkillLevelClamped` 0x00644AC7, `SKILLS_ManaOk` 0x00647584.

```c
// fn:sub_00644180_SkillLevelBonus@0x00644180 (from the disassembly; renamed). rec = entry->skill record.
int SkillLevelBonus(SkillEntry *entry /*stack*/, Unit *u /*ESI*/) {
    if (!entry || !entry->rec) return 0;
    int s = (s16)rec->id;                                   // Skills +0x00
    if (s < 0 || s >= g_DataTables.nSkills) return 0;       // +0xBA0
    int b = entry->bonus2C                                   // SkillEntry +0x2C
          + (UNIT_HasState(u, 134 /*shrine_skill*/) ? 2 : 0) // sub_00644150
          + GetStat(u, 127 /*item_allskills*/, 0);
    if (u && u->type == 0 /*player*/) {
        if ((s8)rec->charclass /*+0x0C*/ == u->class /*+0x04*/) {
            b += GetStat(u, 83 /*item_addclassskills*/, u->class);
            u8 page = SkillDescRec(s)->SkillPage;            // SkillDesc +0x02, via Skills +0x194
            if (page) b += GetStat(u, 188 /*item_addskill_tab*/, 8 * u->class + page - 1);
            b += min(GetStat(u, 97 /*item_nonclassskill*/, s), 3);
        } else {
            b += GetStat(u, 97, s);                          // no clamp
        }
    } else {                                                 // no unit, or not a player
        if (entry->base28 > 0) { int v = GetStat(u, 97, s); if (v) b += min(v, 3); }
        else                    b += GetStat(u, 97, s);       // no clamp
    }
    if (rec->EType /*+0x1DC, u8*/ > 0) b += GetStat(u, 126 /*item_elemskill*/, rec->EType);
    return b + GetStat(u, 107 /*item_singleskill*/, s);
}
```

- [I] The whole formula as above, read from 0x00644180–0x00644295 and `sub_00644150` (0x00644150–0x0064416E: 2 when
  the unit has state 134, else 0). Every `GetStat` is `STATS_GetUnitStat` (0x00625480); stat and state names are the
  table rows. The clamp at 3 (`cmp eax, 3; jle`, 0x0064424C) applies to stat 97 for a skill of the player's own class
  and for a non-player whose base points are above 0; a player's skill of another class takes stat 97 unclamped.
  (fn:sub_00644180_SkillLevelBonus@0x00644180, fn:sub_00644150_ShrineSkillBonus@0x00644150,
  tbl:SkillDesc.txt:SkillPage, tbl:Skills.txt:charclass, tbl:Skills.txt:EType)
- [I] So SkillDesc's `SkillPage` is the server's only use of a SkillDesc record column outside the calc
  variables: the tab bonus (stat 188) applies to a class skill only if its SkillDesc row puts it on a page 1–3. (0x006441F5–0x00644217,
  fn:sub_004A89D0_SkillDescRec@0x004A89D0)
- [C] The function runs in play inside `SKILLS_ManaOk`: the `CUL` lines of the 15 run:2026-10-27-skills logs give its
  return 1 339 times, 182 of them non-zero (1 to 4) (`check-cul.txt`). They do not log the unit's stats, so they do
  not separate the formula's terms, which stay `[I]`. Checking them needs each character's item stats at the call:
  routed as a harness piece
  ([backlog entry](../../backlog/2026-11-10-reverser-reverser-plan-0068-skill-level-bonus-check.md)).
  (fn:SKILLS_ManaOk@0x00647540, 0x00647589, run:2026-10-27-skills)
- [I] `sub_00627AF0_SkillHasDesc(skill)` (ECX): 1 iff `0 ≤ skill < nSkills` and `0 ≤ Skills[skill].skilldesc (+0x194,
  s16) < nSkillDesc` (`+0xB94`). Its one caller is `ITEMS_ReadFull`'s legacy branch for stats 107–109 and 181–187
  (save/0001 § the property list, 0x0062E01D), which drops the stat when it fails. (fn:sub_00627AF0_SkillHasDesc@0x00627AF0,
  fn:ITEMS_ReadFull@0x0062CBE0)
- The calc variables 43–48 (`SKILLS_CalcVar`) read a skill's SkillDesc description missiles; that is data/0005 § G,
  `[C]`, and data/calc's spec has it. (fn:SKILLS_CalcVar@0x00646460)

### 3.3 `Arena` on the server

- [I] Every game creates an arena record: `sub_00530930_GameCreateA` (0x00530B50) and `sub_00530BF0_GameCreate`
  (0x00530D75) both call `sub_0053F4B0_ArenaCreate`, which allocates 16 bytes at `game+0x1D28` (`+0x04` the arena
  type, 0; `+0x08` flags `& 0x3179C7`; `+0x0C` a byte). Every player gets an 8-byte score record `{s32 score, s32
  dirty}` at player data `+0x34` (`sub_0053F530_ArenaPlayerCreate`, called from `sub_005348C0_PlayerUnitAlloc`
  0x00534946). (0x0053F4DC, 0x0053F57A)
- [I] `sub_0053F720_ArenaScoreKill(victim)` (ECX game, EDX killer; called from `sub_0057CCB0_UnitKilled` 0x0057CD5B
  and `sub_00580EC0_PlayerDeath` 0x00581009) reads the Arena row of the game's arena type (`sub_00664AB0_ArenaGetRecord`,
  fatal for a type ≥ 1, so only row 0 `Deathmatch`) and, on the score records:
  - player kills itself: its score `+= Suicide` (`+0x00`);
  - player kills player: killer `+= PlayerKill` (`+0x04`), then killer `+= PlayerKillPercent (+0x08) · victim score
    / 100`; victim `+= PlayerDeath` (`+0x10`), then victim `+= PlayerDeathPercent (+0x14) · killer score / 100`
    (the killer's score already updated); `/ 100` is signed, truncating toward zero (`imul 0x51EB851F; sar 5` with the
    sign fix, 0x0053F8F3, 0x0053F9E3);
  - player kills monster: killer `+= MonsterKill` (`+0x0C`);
  - monster kills player: victim `+= MonsterDeath` (`+0x18`);
  each change sets the record's dirty word, the game arena flags `|= 0x400`, and marks the unit updated.
- [I] No core-area rule reads the score in this reading; its readers (the dirty word's consumer, the client message)
  were not followed. The scoring has no draw. It is server state the chain does not model; plan 0062 left `-arena`'s
  server reader to plan 0061 P1, which this section names. (fn:sub_0053F720_ArenaScoreKill@0x0053F720)

## 4. The COF bundles (plan item 4)

- [I] **The open.** `sub_0046F310_CofBundleLoadAct(act)` (`CL` the act 0..4) takes the name from
  `g_CofBundleNames` (0x006D6C30: `cmncof_a1.d2`, `a2`, `a3`, `a4`, `a6`), builds `DATA\GLOBAL\<name>` and calls
  `sub_0046DDF0_CofBundleParse` with `EBX = g_ClientCofCache` (0x007A78F0). Its callers are
  `sub_0044E100_ClientActLoad` (0x0044E1CD) and `sub_0045C8E0_PktLoadAct` (0x0045E989): the client, at an act load.
  So act 5 (index 4) loads `cmncof_a6.d2`; `cmncof_a5.d2`, `cmncof_a7.d2` and `chars_cof.d2` are not named anywhere in
  the image (`check-items2-5.txt`: 0 occurrences of each name, any case).
- [I] **The layout** the parser reads (0x0046DDF0): the file is records back to back with no header; each record is a
  0x18-byte header `{u32 next, u32 flags, u32 size, char name[8], u32 data}` (the parser overwrites `next`, clears
  `flags`, sets `data` to the record `+0x18`) followed by `size` bytes of COF. A name longer than 7 characters is fatal
  (line 0x79), as is a COF byte 2 (directions) above 0x40 (line 0x126). Each record is linked into one of 512 hash
  buckets at cache `+0x0C` by a hash of its name (`0x00413CE0`, folded to 9 bits).
- [C] That layout parses all eight bundles to the end of file with 0 errors: 6 726 COFs (`chars_cof.d2` 754,
  `cmncof_a1..a7` 809, 791, 1 281, 660, 789, 650, 992). 6 597 are byte-identical to the loose `.cof` of the same name,
  93 differ and 36 have no loose file. (fn:sub_0046DDF0_CofBundleParse@0x0046DDF0, `tools/n68r_bundles.py`,
  `bundles.txt`)
- [I] **What they feed.** Only the client's drawing code references `g_ClientCofCache` (9 raw references, all in
  0x0046E866–0x0047030C, in the client functions 0x0046E740, 0x0046F310, 0x0046F440, 0x0046F650, 0x00470200 and
  0x00470290 per Ghidra). The loose `%s\%s\COF\%s%s%s.COF` path is built by client code (0x0046F490, 0x005034B0) and by
  `COMPOSIT_BuildCofName`'s path branch (0x0064F9BC). The server's mode lengths and event frames come from
  `animdata.d2` (anim/0001 § 2), which no bundle feeds.
- [C] The data comparison the plan asked for, for the record: against `animdata.d2`'s record of the same name, 6 715
  bundle COFs have the same frames per direction and 11 differ (`aia1ht1`, `aia1hth` 12/11; `yoophth` 19/10;
  `3dnuhth` 16/1; `yknuhth` 13/20, some in several bundles); 6 724 have the same event frames and 2 differ (`aia12ht`,
  `aia22ht`: animdata has event 1 at frame 10, the COF none). Every bundle COF has an animdata record. These
  differences reach the client's drawing only. (fn:ANIMDATA_Find@0x0066A8F0, `bundles.txt`)

## 5. `lut.dn1`, the colour `.dat` files, the `.key` maps, `gateways.txt`, the NPC dialogue files (plan item 5)

- [I] `lut.dn1` (Act II town tiles): no string `lut.dn1` or `.dn1` in the image, in any case; never opened. (the
  whole image, 0x00400000–0x009BA000, `check-items2-5.txt`)
- [I] `GreenBlood.dat` and `RandTransforms.dat` are loaded by 0x00476EA0 (names at 0x00476F48 and 0x00476F00), called
  once from the client start-up function 0x0044E200 (0x0044E2B9, itself called at 0x0044F4E0 right after
  `sub_00482260_ClientSoundInit`); a second `GreenBlood.dat` loader, 0x00476E30, has no caller (`tools/xrefscan.py`: 0
  hits). `\Cof\palshift.dat` is appended to a monster's directory by 0x00477170 (0x0047735B; callers 0x0045F3F6 and
  four in 0x004774FF–0x0047751F). All client colour transforms: presentation. (`check-items2-5.txt`, Ghidra xrefs)
- [I] The `.key` maps: `%s%s.key`, `default.key` and `%s\CMD\%s\default.key` are used only by the client's key
  configuration (0x00469650, 0x00469780, 0x004698D0). `defaultdebug.key` is not named. Input: out of scope.
- [I] `gateways.txt` (`DATA\GLOBAL\gateways.txt`, 0x00518313, in 0x00518300): Battle.net gateways, client network
  setup. Out.
- [I] `a1npc.txt`..`a5npc.txt`: no `npc.txt` name in the image; never opened by the game. (the whole image,
  0x00400000–0x009BA000, `check-items2-5.txt`)

## Data touched

`tbl:MonItemPercent.txt:HeartPercent`, `tbl:MonItemPercent.txt:BodyPartPercent`,
`tbl:MonItemPercent.txt:TreasureClassPercent`, `tbl:MonItemPercent.txt:ComponentPercent` (loaded only);
`tbl:ItemTypes.txt:BodyLoc1`, `tbl:ItemTypes.txt:BodyLoc2`, `tbl:CharStats.txt:item1loc`, `tbl:MonEquip.txt:loc1`;
`tbl:ItemTypes.txt:Class`, `tbl:ItemTypes.txt:StaffMods`, `tbl:MagicPrefix.txt:classspecific`, `tbl:Skills.txt:charclass`,
`tbl:CubeMain.txt:class`, `tbl:CharTemplate.txt:Class`; `tbl:ItemStatCost.txt:itemevent1`,
`tbl:ItemStatCost.txt:itemevent2`, `tbl:Skills.txt:auraevent1`; `tbl:SkillDesc.txt:SkillPage`,
`tbl:Skills.txt:skilldesc`, `tbl:Skills.txt:EType`; `tbl:Arena.txt:Suicide` .. `tbl:Arena.txt:MonsterDeath`.
`struct:Game+0x1D28` (arena record), `struct:PlayerData+0x34` (arena score), `struct:SkillEntry+0x2C`.

## Dead ends

- Looking for the `MonItemPercent` reader near the TC code: the loader sits between `TC_GetChestTC` (0x00654E80) and
  the superunique getter, which only reflects the source file order of the table loaders.
- A first nearest-symbol pass put `g_DataTables + offset` readers in the wrong functions (the CSV has gaps); the
  function boundaries in § 3 are Ghidra's.

## Open questions

- `[L]` Whether any 1.14d code path reaches `MonItemPercent` through an address built at run time: the harness watch
  of § 1.4 resolves it.
- `[L]` Whether a missile attack ever dispatches event 7 (`COMBAT_DeliverQueued`), which decides whether stat 195
  fires on a ranged attack at all: read `COMBAT_DeliverQueued`'s callers (§ 2.3).
- `[L]` The runtime registrar 0x005C377B's event id, and whether anything registers on id 13 (§ 2.3).
- `[L]` Who reads the arena score at player data `+0x34` (§ 3.3; plan 0061 P1's `-arena` reader).
