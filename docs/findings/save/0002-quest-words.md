# 0002 — Quest words of the `Woo!` section and the act-travel gates

> **Subsystem:** save/d2s
> **Question:** Which quest words and bits must a save carry, per difficulty, so that a loaded character can open the
> waypoint tabs of Acts II–V (and counts as having completed each act and quest), and does anything else gate act travel?
> **Date:** 2026-10-13   **Plan:** none (backlog 2026-10-12, archivist → reverser)   **Status:** open (static reading; the
> difficulty slot and the act-travel words `[C]` from two owner-played saves, the tab gate `[I]`; 2026-10-15, plan 0027
> Phase 2: § 5 the Arcane Sanctuary waypoint, § 6 the Pandemonium portal stubs)

Static reading of the pinned `Game.exe`; no game run. Names are ours. "Block *d*" is the *d*-th 96-byte quest block of
the `Woo!` section ([save/0001](0001-d2s-io.md) § 3, [d2s.md § Quests](../../formats/d2s.md#quests-waypoints-npcs-0x14f0x2fc)),
which starts at file offset `0x159 + 0x60·d`. "Word *q*" is the little-endian u16 at block offset `2q`.

## Answer (summary)

- [I] **A quest record is a 768-bit field addressed as `16·q + s`**: quest *q*, state bit *s*. The getter
  `fn:QUESTRECORD_GetState@0x0065C310`, setter `fn:QUESTRECORD_SetState@0x0065C360` and clearer
  `fn:QUESTRECORD_ClearState@0x0065C3A0` pass `q·16 + s` to the bit-field helpers `fn:BITFIELD_Get@0x00410B30` /
  `fn:BITFIELD_Set@0x00410B10` / `fn:BITFIELD_Clear@0x00410B50`, which address byte `i >> 3`, mask `1 << (i & 7)`
  (mask table `0x006CE268` = `01 02 04 08 …`). So state bit *s* of quest *q* is bit *s* of word *q*, LSB first.
- [C] **Block *d* is difficulty *d*** (0 Normal, 1 Nightmare, 2 Hell). Every reader and writer of a player's quest
  record takes player data `+0x10 + 4·game[+0x6D]` (the game's difficulty byte, the same one that selects header byte
  `0x0A8 + d`); the waypoint record is `+0x1C + 4·game[+0x6D]` (`fn:sub_00547F50_PlayerWaypointRecord@0x00547F50`).
  Data: in the two owner-played Nightmare saves below, only block 1 carries progress.
  (0x005467F3, 0x00546AE0, 0x0058478A, fn:sub_00546270_QuestsPlayerJoin@0x00546270, run:2026-10-12-tc-champion,
  run:2026-10-12-quality)
- [C] **Act-travel words.** Bit 0 of word 7, 15, 23 and 28 records that the character crossed to Act II, III, IV and V.
  The game sets bit 0 and bit 13 together (`0x2001`) and nothing else writes those bits: words 7 and 15 in the Warriv
  and Meshif branches of `fn:sub_005467E0_NpcActTravel@0x005467E0`, word 28 in its Tyrael branch (expansion games
  only) and in `0x005B5880`, word 23 in `fn:sub_00546AC0_DuranceActTravel@0x00546AC0`. Both owner-played saves hold
  word 7 = `0x2001` in block 1, and the one that reached Act III also holds word 15 = `0x2001`.
  (setter calls 0x00546997, 0x005469A1, 0x0054692B, 0x00546935, 0x0054685D, 0x00546867, 0x00546BCC, 0x00546BD6,
  0x005B590F, 0x005B5919; run:2026-10-12-tc-champion, run:2026-10-12-quality)
- [I] **The waypoint menu's act tabs are the only quest gate on travel.** The client draws tab *i* (Act *i*+1) when it
  is the current tab or when bit 0 of word 7 (*i* = 1), 15 (2), 23 (3) or 26 (4, expansion only) is set in the client's
  copy of the current difficulty's record (`fn:sub_0049C9C0_WpMenuDraw@0x0049C9C0`). On open and on a tab click the
  selected act is clamped down until it is allowed: act 4 needs word 28 bit 0, act 3 word 23, act 2 word 15, act 1
  word 7, otherwise act 0 (`fn:sub_0049C760_WpTabClamp@0x0049C760`). So the Act V tab needs **both** word 26 bit 0
  (to be drawn) and word 28 bit 0 (to be selected).
- [I] **The server checks only the waypoint bit.** `fn:sub_00584F60_WaypointTravel@0x00584F60` moves the player when
  the target level's waypoint index is set in the current difficulty's waypoint record; it reads no quest word.
  The act change `fn:sub_0053AEC0_PlayerChangeLevel@0x0053AEC0` → `fn:sub_0053ACC0_PlayerChangeAct@0x0053ACC0` creates
  the act if needed and reads no quest word either. The progression bits of the header status word gate only the
  difficulty ([save/0001](0001-d2s-io.md) § 2).
- [I] **The client's copy** (`fn:sub_004B32D0_ClientQuestRecord@0x004B32D0`, global `0x007C0D43`) is the player's
  record for the game's difficulty: on join `sub_00546270_QuestsPlayerJoin` sends it (96 bytes,
  `fn:sub_0053D670_SendQuestRecord@0x0053D670`) from `+0x10 + 4·game[+0x6D]`.
- [I] **Arcane Sanctuary (74) has no gate of its own** (plan 0027 Phase 2, § 5). The client's list of a tab
  (`fn:sub_0049C7F0_WpMenuListBuild@0x0049C7F0`) enables every waypoint index of the act whose bit is set and whose level
  is not the current one, and the server (`sub_00584F60_WaypointTravel`) tests only that bit. Neither tests a level id
  except to choose the arrival point: 74, like 46 and 133–136, arrives at point type 13. Level 74 is waypoint index 16
  (`Levels.txt` `Waypoint`), row 8 of the Act II tab; a save with waypoint bits 0–38 and word 7 opens it.
  (fn:sub_0049C7F0_WpMenuListBuild@0x0049C7F0, fn:WAYPOINT_LevelFromIndex@0x00660D90, 0x00585023, tbl:Levels.txt:Waypoint)
- [C] **The Pandemonium portals cannot open in this `Game.exe`** (plan 0027 Phase 2, § 6). The cube's output dispatch
  (`0x00565D1E`, in `sub_00565AB0_RecipeOutputCreate`) calls `g_CubePortalFns[t]` for the output type *t* that the
  `cubemain` loader gives `"Cow Portal"` (1), `"Pandemonium Portal"` (2) and `"Pandemonium Finale Portal"` (3). Entries
  2 and 3 are thunks to two-instruction stubs that return 0 (`xor eax, eax; ret`). With nothing created, the recipe
  returns before it consumes the inputs. There is no test of game type, difficulty or player count: the code that would
  open them is not in this binary. Corroborated by session k1 of run:2026-10-15-drlg-outdoor (single-player Hell,
  Harrogath: three transmutes with the three keys, no portal, the keys stayed). So levels 133–136 cannot be reached
  through the cube. (data:g_CubePortalFns@0x006E11C8, fn:CUBE_PandemoniumPortalStub@0x00594270,
  fn:CUBE_PandemoniumFinalePortalStub@0x00594280, fn:CUBEMAIN_OutputTypeParse@0x00668A90, run:2026-10-15-drlg-outdoor)

## Recipe for `tools/d2s.py build`

For each difficulty *d* to open (0 Normal, 1 Nightmare, 2 Hell), with `B = 0x159 + 0x60·d` the block's file offset
and "set word *q*" meaning `u16[B + 2q] |= 0x0001` (equivalently byte `B + 2q` `|= 0x01`):

| goal | words (bit 0) | file offsets of the low byte, Normal / Nightmare / Hell | tag |
|---|---|---|---|
| Act II tab | 7 | `0x167` / `0x1C7` / `0x227` | `[I]` (gate), `[C]` (word written on travel); fn:sub_0049C9C0_WpMenuDraw@0x0049C9C0, run:2026-10-12-tc-champion |
| Act III tab | 15 | `0x177` / `0x1D7` / `0x237` | `[I]` / `[C]`; fn:sub_0049C9C0_WpMenuDraw@0x0049C9C0, run:2026-10-12-quality |
| Act IV tab | 23 | `0x187` / `0x1E7` / `0x247` | `[I]` fn:sub_0049C9C0_WpMenuDraw@0x0049C9C0 |
| Act V tab drawn (expansion) | 26 | `0x18D` / `0x1ED` / `0x24D` | `[I]` fn:sub_0049C9C0_WpMenuDraw@0x0049C9C0 |
| Act V tab selectable | 28 | `0x191` / `0x1F1` / `0x251` | `[I]` fn:sub_0049C760_WpTabClamp@0x0049C760 |

- [I] **"All acts open"** in difficulty *d* = set words 7, 15, 23, 26, 28 of block *d*, plus waypoint bits 0–38 in
  `WS` block *d* (field bytes `FF FF FF FF 7F`, as `setwp … all` writes), plus the status word's progression high
  enough for *d* (≥ 5 Nightmare, ≥ 10 Hell in an expansion save; 15 for all) and the expansion bit for Act V. Bit 0
  alone suffices: the loader clears bits 13 and 14 of every word anyway ([save/0001](0001-d2s-io.md) § 3), so the
  game's own `0x2001` and `0x0001` load the same. The game sets word 26 bit 0 in `0x005B4D20` (with bits 13, 6 and 7);
  that this is Diablo's death is `[L]`, so setting it may mark Diablo dead in that difficulty.
- [I] **"All quests completed"** = the above plus bit 0 of the quest words of the quest objects in
  `data:g_QuestDescs@0x00731510` grouped by act: Act I 1–6, Act II 9–14, Act III 17–22, Act IV 25–27,
  Act V 35–40. Bit 0 is the bit every gate above and the join pass test (see below); it grants no reward: skill points,
  stat points, resistances and life of quest rewards live in the stat list, and some consumable rewards are gated on
  other bits (word 9 bit 5, word 20 bit 5, word 37 bits 7–8 in `0x00483F80`). Leave words 0, 8, 16, 24, 29–34 and 41
  at 0 (their meaning is open).
- [I] On join, every quest object with flag byte 0 whose record word has bit 0 or bit 15 set marks the game-wide record's word bit 15
  (fn:sub_00546270_QuestsPlayerJoin@0x00546270, the loop over `g_QuestDescs`); nothing there rejects a save.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x00410B10` | `BITFIELD_Set` | `(bytes, i)`: byte `i >> 3` `\|=` `1 << (i & 7)` | I |
| `0x00410B30` | `BITFIELD_Get` | the same bit, tested | I |
| `0x00410B50` | `BITFIELD_Clear` | the same bit, cleared | I |
| `0x0065C310` | `QUESTRECORD_GetState` | `(rec, q, s)` → bit `16q + s` | I |
| `0x0065C360` | `QUESTRECORD_SetState` | sets bit `16q + s` | I |
| `0x0065C3A0` | `QUESTRECORD_ClearState` | clears bit `16q + s` | I |
| `0x0065C430` | `QUESTRECORD_Alloc` | 96 zero bytes behind a bit-buffer header (`.\QuestRecord\QuestRecord.cpp`) | I |
| `0x0065C4D0` | `QUESTRECORD_LoadBytes` | 96 bytes in; with the flag, per word 0–41: clear bits 13, 14; bit 1 → set bit 15 | I |
| `0x0065C560` | `QUESTRECORD_SaveBytes` | 96 bytes out, as they are | I |
| `0x00660E00` | `WAYPOINT_IndexFromLevel` | `levels.txt` `Waypoint` (`+0xE4`) of a level; 255 = none | I |
| `0x00660E50` | `WAYPOINT_IsSet` | `(rec, n)` → word `g_WaypointBits[n]`, mask | I |
| `0x00660EC0` | `WAYPOINT_Set` | sets waypoint *n* | I |
| `0x00547F50` | `sub_00547F50_PlayerWaypointRecord` | player data `+0x1C + 4·game[+0x6D]` | I |
| `0x00546270` | `sub_00546270_QuestsPlayerJoin` | join: quest objects, game record bit 15, sends the player record | I |
| `0x0053D670` | `sub_0053D670_SendQuestRecord` | 103-byte message with the 96 record bytes | I |
| `0x005467E0` | `sub_005467E0_NpcActTravel` | NPC 155 (Warriv) sets word 7, 210 (Meshif) words 15 and 10, 367 (Tyrael, expansion) word 28 | I |
| `0x00546AC0` | `sub_00546AC0_DuranceActTravel` | from level 102: sets word 23 (and word 18, removing its quest items) | I |
| `0x00584750` | `sub_00584750_DurancePortalOperate` | portal operate: needs word 22 bit 13 or bit 0, then `sub_00546AC0`; marks waypoint of level 103 | I |
| `0x00584E30` | `sub_00584E30_WaypointOperate` | marks the level's waypoint, sends the record (`WAYPOINT_Save`) | I |
| `0x00584F60` | `sub_00584F60_WaypointTravel` | target waypoint bit set → change level; no quest test | I |
| `0x0053AEC0` | `sub_0053AEC0_PlayerChangeLevel` | other act → `sub_0053ACC0`; no quest test | I |
| `0x0053ACC0` | `sub_0053ACC0_PlayerChangeAct` | creates the act if absent and moves the player | I |
| `0x004B32D0` | `sub_004B32D0_ClientQuestRecord` | client: returns the received player record (`0x007C0D43`) | I |
| `0x0049C760` | `sub_0049C760_WpTabClamp` | clamps the selected act tab by words 28, 23, 15, 7 | I |
| `0x0049C9C0` | `sub_0049C9C0_WpMenuDraw` | draws tab *i* if current or word 7/15/23/26 bit 0 | I |
| `0x0049CF90` | `sub_0049CF90_WpMenuOpen` | waypoint message: tab = act of the player's level, clamped; loads the 16-byte record | I |
| `0x0049D160` | `sub_0049D160_WpMenuClick` | tab click → clamp, rebuild the list | I |
| `0x0049C7F0` | `sub_0049C7F0_WpMenuListBuild` | the tab's rows: waypoint indices of the act's level range; a row is enabled when its bit is set and its level is not the current one (§ 5) | I |
| `0x00660D90` | `WAYPOINT_LevelFromIndex` | waypoint index → level id (the inverse of `WAYPOINT_IndexFromLevel`) | I |
| `0x00668A90` | `CUBEMAIN_OutputTypeParse` | `cubemain` output string: `"Cow Portal"` → type 1, `"Pandemonium Portal"` → 2, `"Pandemonium Finale Portal"` → 3, `usetype`/… otherwise (§ 6) | I |
| `0x006E11C8` | `g_CubePortalFns` | data: `{0, 0x00565A80, 0x00565A90, 0x00565AA0}`, thunks to `0x00594140`, `0x00594270`, `0x00594280` | C |
| `0x00565A80` / `0x00565A90` / `0x00565AA0` | `thunk_CUBE_CowPortalOpen` / `thunk_CUBE_PandemoniumPortalStub` / `thunk_CUBE_PandemoniumFinalePortalStub` | `jmp` thunks, the three non-null entries of `g_CubePortalFns` | C |
| `0x00594140` | `CUBE_CowPortalOpen` | cow portal: event flag 11 clear, quest-word tests, level 1 (Rogue Encampment), then the class-60 portal to level 39 | I |
| `0x00594270` | `CUBE_PandemoniumPortalStub` | `xor eax, eax; ret`: no portal | C |
| `0x00594280` | `CUBE_PandemoniumFinalePortalStub` | `xor eax, eax; ret`: no portal | C |

Data: `data:g_QuestDescs@0x00731510`: 37 records of 0x18 bytes (count at `0x00731888`): `+0x00` init function,
`+0x04` act (0–4), `+0x0C` a flag byte, `+0x10` quest object id, `+0x14` record word. Words by act field: act 0: 0–6, 29, 41;
act 1: 8–14, 30, 31; act 2: 16–22, 32; act 3: 24–27, 33; act 4: 35–40. Words 7, 15, 23, 28 and 34 belong to no record.

## Walkthrough

### 1. The record

- [I] `QUESTRECORD_LoadBytes` (stdcall `(rec, src, 0x60, flag)`) copies 24 dwords, then with the flag set loops
  `i = 14, 30, …, 670` (`cmp esi, 0x2AE`, 42 iterations): clear bits `i − 1` and `i`, and if bit `i − 13` is set, set
  bit `i + 1`. Per word *k* = 0–41: clear bits 13 and 14, set bit 15 if bit 1 is set. Bytes `0x54`–`0x5F` (words
  42–47) are only copied. (0x0065C50E–0x0065C54D)
- [I] `D2S_ReadQuests` and `D2S_WriteQuests` move the three records at player data `+0x10`, `+0x14`, `+0x18` in that
  order, so block *d* is the record at `+0x10 + 4d`. (fn:D2S_ReadQuests@0x0056A370, fn:D2S_WriteQuests@0x00569320)
- [I] Every gameplay access found takes `+0x10 + 4·game[+0x6D]`: `movzx ecx, byte [ebx+0x6D]` at 0x005467F3 and
  0x00546AE0, `byte [edi+0x6D]` at 0x0058478A, and the join pass in `sub_00546270_QuestsPlayerJoin`.

### 2. Who writes the act-travel words

- [I] `sub_005467E0_NpcActTravel` (ECX = game, arg = `{1, npc id}`): npc 155 (`sub eax, 0x9B` at 0x00546820): if word 7
  bit 0 is clear, set bits 0 and 13, send the record, change act. npc 210: if word 15 bit 0 is clear, set word 10 bits 0
  and 13 if word 10 bit 0 was clear (removing items `msf ` and `vip `), then word 15 bits 0 and 13. npc 367, only when
  `game+0x70` (expansion) is non-zero (`cmp [ebx+0x70], eax` at 0x00546850): word 28 bits 0 and 13. The npc ids are
  `monstats` rows; that 155, 210 and 367 are Warriv, Meshif and Tyrael is `[L]` (row names not checked here).
- [I] fn:sub_00546AC0_DuranceActTravel@0x00546AC0 (level 102 = `0x66`): if word 23 bit 0 is clear, set word 18 bits 0 and 13 when
  clear (removing `qey `, `qhr `, `qbr `, `qf1 `, `qf2 `), then word 23 bits 0 and 13, send the record. It is reached
  from `sub_00584750_DurancePortalOperate`, which first needs word 22 bit 13 or bit 0.
- [I] A full list of setter calls with a constant word (Ghidra call-argument dump of `0x0065C360`) gives no other writer
  of words 7, 15, 23 or 28; word 26 is set in `0x005B4670` (bit 8) and `0x005B4D20` (bits 13, 0, 6, 7).

### 3. The waypoint menu (client)

- [I] `sub_0049C9C0_WpMenuDraw`: for each tab *i* < 4 (classic) or < 5 (expansion: `0x00408F20` and `0x0044DCC0`
  both non-zero), draw it if *i* is the selected tab, else test bit 0 of word 7, 15, 23 (`push 7/0xF/0x17` at
  0x0049CBB8, 0x0049CBCD, 0x0049CBD3) or 26 (`push 0x1A`, 0x0049CBD9, expansion only) in the client record and draw it
  if set. (0x0049CB9A–0x0049CC00)
- [I] `sub_0049C760_WpTabClamp` (EAX = act): a switch that falls through: act 4 → 3 if word 28 bit 0 is clear;
  act 3 → 2 if word 23's is clear; act 2 → 1 if word 15's is clear; act 1 → 0 if word 7's is clear.
  (0x0049C77E–0x0049C7C8)
- [I] `sub_0049CF90_WpMenuOpen` sets the tab from the act of the player's level through the clamp, then loads the
  16-byte waypoint record from the message (`WAYPOINT_Load`). The list of a tab is built by `0x0049C7F0` from the
  received record (`WAYPOINT_IsSet`) and the level range of the act.

### 4. Server-side travel

- [I] `sub_00584F60_WaypointTravel` (the waypoint object's operate state, `0x00732D18` table entry =
  `sub_00584E30_WaypointOperate`): target level ≠ current level, `WAYPOINT_IndexFromLevel(target)` valid,
  `WAYPOINT_IsSet(PlayerWaypointRecord, n)`; then `sub_0053AEC0_PlayerChangeLevel`. No call to
  `QUESTRECORD_GetState` in the function (r2: 0 references to `0x0065C310`).
- [I] `sub_0053AEC0_PlayerChangeLevel` compares the target's act with the current one and goes through `0x00537340`
  (act-entry hooks per town level 1, 40, 75, 103, 109) and `sub_0053ACC0_PlayerChangeAct`; neither reads a quest word.

### 5. Arcane Sanctuary (74) in the waypoint menu (plan 0027 Phase 2, 2026-10-15)

The backlog entry of 2026-10-14 asked which quest word or waypoint bit gates 74 and 46. Canyon of the Magi (46) opened
by waypoint in four sessions of run:2026-10-15-drlg-outdoor; 74 was not tried.

```text
WpMenuListBuild (0x0049C7F0), tab t:                                   [I]
  once per act: [lo, hi] = the min and max WAYPOINT_IndexFromLevel over the act's level range (table 0x007224AC, 11 bytes per act)
  for n in lo..hi:
    if WAYPOINT_IsSet(record, n): level = WAYPOINT_LevelFromIndex(n); row enabled unless level = the player's level
    else: row shown disabled
WaypointTravel (0x00584F60), server:                                   [I]
  the operated object's OperateFn is WaypointOperate; target ≠ current level; WAYPOINT_IndexFromLevel(target) valid;
  WAYPOINT_IsSet(PlayerWaypointRecord, n); arrival point type 13 if target is 46, 74, 133–136 or FUN_0061AAF0(target),
  else 0; PlayerChangeLevel(target, type)
```

- [I] Neither function tests a quest word or a level id before travel. Level 74 is index 16 (`Levels.txt` `Waypoint`),
  between Palace Cellar 1 (52, index 15) and Canyon of the Magi (46, index 17), so it is row 8 of the Act II tab. The
  `quests: all` save with waypoint bits 0–38 that opened row 9 (46) has bit 16 set. (fn:sub_0049C7F0_WpMenuListBuild@0x0049C7F0,
  fn:sub_00584F60_WaypointTravel@0x00584F60, tbl:Levels.txt:Waypoint)
- A run needs no recipe change: click row 8 of the Act II tab with the run:2026-10-15-drlg-outdoor `UniqNova` or
  `UniqClassic` save (backlog → Phase 3).

### 6. The Pandemonium key transmute (level 134) (plan 0027 Phase 2, 2026-10-15)

```text
cubemain load, output column (CUBEMAIN_OutputTypeParse 0x00668A90): record +8 ← 1 "Cow Portal", 2 "Pandemonium Portal",
  3 "Pandemonium Finale Portal" (case-insensitive), 0xFF "usetype", …        [I] (fn:CUBEMAIN_OutputTypeParse@0x00668A90)
transmute (sub_00565AB0_RecipeOutputCreate, 0x00565D1E):                                                        [C]
  t = record +8; if 1 ≤ t ≤ 3 and g_CubePortalFns[t] ≠ 0: made = g_CubePortalFns[t]()
  … per output slot: an item made sets made = 1
  if made = 0: return                                ; 0x00566400: the inputs stay in the cube
g_CubePortalFns (0x006E11C8) = {0, 0x00565A80 → CUBE_CowPortalOpen 0x00594140,
                                   0x00565A90 → 0x00594270, 0x00565AA0 → 0x00594280}
0x00594270, 0x00594280: xor eax, eax ; ret
```

- [C] The two Pandemonium outputs are stubs that return 0, in every game type: single player, TCP/IP or open
  Battle.net games run this `Game.exe`, and none of them can open these portals. Session k1 of run:2026-10-15-drlg-outdoor
  (single-player Hell, Harrogath, the three keys `pk1`/`pk2`/`pk3`) saw three transmutes with no portal and the keys left
  in the cube, as the code says. (data:g_CubePortalFns@0x006E11C8, fn:CUBE_PandemoniumPortalStub@0x00594270, run:2026-10-15-drlg-outdoor)
- [I] The portal creator `sub_0056D130_PortalObjectCreate` refuses class 60 in a level whose `FUN_0061AB00` is set unless
  the destination is 39 or 133–136, but no caller in this binary passes 133–136. Level 134 can be reached only by a
  forced path that makes some reachable warp or waypoint lead there (ADR-0010), which is the architect's call
  (backlog). (fn:sub_0056D130_PortalObjectCreate@0x0056D130)

## Corroboration (data)

- [C] `workspace/runtime/saves-backup/p0011c/LightSorc-after.d2s` (run:2026-10-12-tc-champion) and
  `…/p0010q/LightSorc-after.d2s` (run:2026-10-12-quality, session B): the installed tool-built input
  `LightSorc.d2s` has all 288 quest bytes zero; the owner played Nightmare (header `0x0A8`–`0x0AA` = `00 81 00` and
  `00 82 00`, Nightmare act 1 and act 2). After play only block 1 is non-zero: word 6 = `0x2019`, word 7 = `0x2001`
  in both, and in the one that reached Act III also words 8, 10–14 and word 15 = `0x2001`. Blocks 0 and 2 stay zero.
  This pins block 1 = Nightmare and the travel words written as bits 0 + 13. Bit 13 is still in the file because the
  writer copies the record as it is; the next load clears it.
- The 21 survey samples of the d2s gate set are level-1/2 characters with all quest blocks zero; `seedtest`
  (level 71) has only word 1 = `0x0004` in block 1. None of them tests a gate.
- Consistent, not a test: run:2026-10-11-d2s-waypoints loaded a save with waypoint bits 9–38 and no quest bit and
  showed no Act II–V tab ([d2s.md § Waypoints](../../formats/d2s.md#waypoints-ws)).

## Leads used

- `src:d2s-community-format` lists per-difficulty quest words with act-intro and "traveled to" words; not compared
  claim by claim here (the code was read first). No verdict recorded.

## Open questions

- [L] Run case for `[C]` on the tab gate: a Normal save with only word 7 bit 0 set (and waypoints 0–38) shows the
  Act II tab and no other; adding 15, 23 shows III, IV; in an expansion game, 26 without 28 draws the Act V tab but a
  click falls back to Act IV; 26 + 28 opens it.
- What the NPC menus test before offering travel (Warriv's "go east" etc.) was not traced; `0x0058FB50` tests word 0
  bit 0 for npc 155. Not needed for waypoint travel.
- The meaning of the other state bits (1, 12–15 beyond the loader rule) and of words 0, 8, 16, 24, 29–34, 41.
- Quest names per word (Andariel = word 6, Diablo = word 26, …) are `[L]`; the code shows only the act grouping.
