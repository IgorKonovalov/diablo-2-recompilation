# 0010 — Quest drops, quest rewards and special drops

> **Subsystem:** items/quest-drops
> **Question:** How does quest state change what a kill drops (the MonStats quest TC), which items do the quest
> scripts create outside the treasure-class path (quest items, special drops, NPC rewards), with which draws, and does
> an act boss keep its MonStats level in an expansion Nightmare or Hell game?
> **Date:** 2026-10-15   **Plan:** 0032 (Phase 1, Phase 1b)   **Status:** open (Phase 1 read from the decompile and the
> disassembly of the pinned `Game.exe`; no game run. Phase 1b cross-check in *Leads used*)

Names are ours. "Record" of a player is the player's quest record for the game's difficulty (`PlayerData+0x10 +
4·Game+0x6D`, [save/0002](../save/0002-quest-words.md)); "word *q*, bit *s*" is bit `16q + s` of it. Word numbers are
the quest ids of `data:g_QuestDescs@0x00731510`; the source file each quest's code names (`…\Quests\a1q6.cpp`) gives
the act and the quest's place in it. NPC, monster and object ids are `monstats`, `objects` rows; the names given for
them come from the row names of the `.txt` tables and are not used as evidence. "Quest seed" is the 8-byte seed at
`QuestControl+0x18` (§ 1). "Creation record" is the 0x84-byte `struct:ItemCreateRec` ([items/0001 § 8](0001-tc-resolution.md)).
Item flags are `ItemData+0x18` (`0x10` identified, `0x800` socketed, `0x400000` ethereal, `0x1000000` personalized).
Phase 0 (the archivist's quest bits in saves) had not landed, so no `tbl:` anchor below rests on a Phase 0 survey.
Phase 1 was written from the code only; no community text had been read when it was written.

## Answer (summary)

- [I] **B6, the quest TC switch.** `MONSTER_DropItems` replaces the chosen TC with `TreasureClass4` of the difficulty
  when the class's `TCQuestId` (`+0x9E`) is non-zero, that column is set, the kill context has a killer, the killer
  resolves to a **player** (§ 2), and that player's own record has **bit 15, bit 1 and bit `TCQuestCP` of word
  `TCQuestId` all clear**. No other party member's record is read. (fn:MONSTER_DropItems@0x005A6600 0x005A6705–0x005A67F1,
  fn:QUESTS_PlayerRecord@0x00543520, fn:QUESTRECORD_GetState@0x0065C310, tbl:MonStats.txt:TCQuestId, tbl:MonStats.txt:TCQuestCP)
- [I] **The drop runs before the quest scripts see the death.** The kill handler sets the monster's death mode
  (`sub_005A7C20_MonSetMode`, call at 0x0057CDC4), whose start function `sub_005A6FF0_MonDeathEvent` drops the items
  at once (0x005A7D67), and only then dispatches the quest death event (0x0057CDD9). So the three tests read the
  killer's bits **before** the boss's own quest script sets them for this kill. (fn:sub_0057CCB0_UnitKilled@0x0057CCB0,
  fn:sub_005A7C20_MonSetMode@0x005A7C20, fn:QUESTS_MonsterDeathEvent@0x00543A30)
- [I] **What the three bits mean per boss** (the five classes with a `TCQuestId`, `TCQuestCP` from the data):
  bit 1 is "done in a game, reward not yet taken", bit 15 is set by the save loader when bit 1 was saved
  ([save/0002 § 1](../save/0002-quest-words.md)) and never cleared, and bit `TCQuestCP` is each script's own marker.
  Andariel (word 6, CP 1): her script sets bit 1 at the kill and Warriv's talk turns bit 1 into bit 0, so the quest TC
  is used again in every later game **once the quest is reported in the game it was done in**, and never again if the
  game was saved before the report. Duriel (14, CP 5): bit 5 is set at the kill and never cleared, so the quest TC is
  used until the first kill. Mephisto (22), Diablo (26) and Baal (40) (CP 0): the kill sets bit 0, so the quest TC is
  used until the first kill. (§ 3; fn:sub_00596210_A1Q6_SetKilled@0x00596210, fn:sub_00595C60_A1Q6_NpcMessage@0x00595C60,
  fn:sub_0059D050_A2Q6_DurielDeath@0x0059D050, fn:sub_005BC140_A3Q6_SetDone@0x005BC140, fn:QUESTRECORD_LoadBytes@0x0065C4D0)
- [I] **Killer resolution.** A non-player killer becomes the player that owns it: a monster's owner (summons,
  hirelings: `sub_0058F0D0_MonsterOwner`), overridden by the caster of a state whose `States.txt` `exp` column is set
  (conversion, attract, confuse in the shipped data) when the killer carries one. A killer that still is not a player
  (a wild monster, a missile with no owner) keeps the normal TC. (fn:sub_0063A690_UnitHasExpState@0x0063A690,
  fn:sub_00625760_StatListFindFlag@0x00625760, `states.txt` column `exp`)
- [I] **Special drops are scripted, with their own draws on the quest seed.** Andariel's death drops two chipped gems
  or skulls and one standard gem or skull for a killer with bits 0 and 1 clear; the Cow King's death drops eight
  stamina potions (`vps`); the Hellforge drops four waves of gems (perfect, flawless, flawless, standard) and, in an
  expansion game, one rune of `r01`–`r11` / `r12`–`r22` / `r15`–`r25` by difficulty (`Range(11)`); Baal's first kill
  drops a gold pile per qualifying player. Each draw is one step of the quest seed. The Countess has **no quest
  dependence** in her drop: her class has no `TCQuestId`, and her quest script creates no item. (§ 4;
  fn:sub_005965A0_A1Q6_AndarielDeath@0x005965A0, fn:sub_00593E70_A1Q4_CowKingDeath@0x00593E70,
  fn:sub_005B6710_A4Q3_ForgeWave@0x005B6710, fn:sub_0058DF20_A5Q6_BaalDeath@0x0058DF20, fn:QUESTS_GetSeed@0x005438B0)
- [I] **Quest items** come from the quest scripts through two creators: `sub_00559A30_DropItemAtUnit` (the code in
  the source unit's `+0xB8`, normal or unique quality, ilvl from the source unit) and `QUESTS_GiveItem` (into the
  inventory, or dropped when it is full). A script counts the players that still need the item and creates that many
  copies. "Needs" is `sub_00558110_PlayerFindItemByCode`, which ignores a quest item with `questdiffcheck` whose stat
  356 (set to the game difficulty when the item is created) is below the current difficulty. (§ 5, tbl:Misc.txt:questdiffcheck)
- [I] **Rewards.** All three NPC item services live in `sub_00579D60_NpcItemReward`: Charsi's imbue creates a
  **new** rare (quality 6) of the same base with **ilvl = clvl, +4 when clvl > 5**, on fresh seeds; Larzuk's socket
  copies the item and requests `max` sockets (low, normal, superior), `1 + RangeB(item seed, min(max, 2))` (magic) or 1
  (set, rare, unique, crafted, 9); Anya copies the item and writes the player's name (flag `0x1000000`), nothing else.
  Akara, Ormus, Malah, Anya (Prison of Ice) and Qual-Kehk give fixed or difficulty-tiered items; the Ancients and Nihlathak
  create none. (§ 6; fn:sub_00579D60_NpcItemReward@0x00579D60, fn:QUESTS_GiveItem@0x005466B0)
- [I] **The `boss` exception of monsters/pool E4** is the byte test `MonStats+0x00C & 0x40` next to `& 0x04`
  (`noRatio`) at 0x00573E32–0x00573E40: a `boss` class keeps `Level(N)`/`Level(H)` in an expansion Nightmare or Hell
  game. The 25 `boss` classes and the Phase 2 case set are in § 7. (fn:sub_00573CB0_MonStatsInit@0x00573CB0, tbl:MonStats.txt:boss)

## Leads used

The lead pages were fetched and read **after** the walkthrough below was written. One verdict per compared claim.

_(filled in by Phase 1b, below)_

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005A6600` | `MONSTER_DropItems` | TC column choice; B6 quest switch (existing row) | I |
| `0x00543520` | `QUESTS_PlayerRecord` | `(game, player)` → `PlayerData+0x10 + 4·Game+0x6D` | I |
| `0x006221A0` | `sub_006221A0_PlayerData` | `Unit+0x14` of a player unit (asserts type 0) | I |
| `0x0063A690` | `sub_0063A690_UnitHasExpState` | unit carries a state of the `exp` state mask (`DataTables+0x144`) | I |
| `0x0063A130` | `sub_0063A130_UnitHasStateInMask` | any bit of the unit's state mask in a state bit-set (EAX unit, EBX set) | I |
| `0x00611D60` | `sub_00611D60_StatesMaskBuild` | states loader: bit-set *i* = states whose flag bit *i* is set | I |
| `0x00625760` | `sub_00625760_StatListFindFlag` | the unit's first stat list with a flag (`0x800` here) | I |
| `0x00625250` | `sub_00625250_StatListOwnerType` | stat list `+0x08` (6 if none) | I |
| `0x006252B0` | `sub_006252B0_StatListOwnerGuid` | stat list `+0x0C` | I |
| `0x0057CCB0` | `sub_0057CCB0_UnitKilled` | kill: death mode (drop) first, then the quest death event | I |
| `0x005A7C20` | `sub_005A7C20_MonSetMode` | sets a monster mode and calls the mode's start function | I |
| `0x005A78A0` | `sub_005A78A0_MonModeRecord` | the mode's function record (table `0x006E2260`) | I |
| `0x00545D80` | `QUESTS_InitGame` | one quest object per `g_QuestDescs` row, the quest seed, the game record | I |
| `0x005438B0` | `QUESTS_GetSeed` | `QuestControl+0x18` | I |
| `0x00543640` | `QUESTS_FindById` | quest object by id (`Quest+0x00`) | I |
| `0x005436B0` | `QUESTS_HookMonster` | the "quest hook" of special monsters: registers a monster with a quest | I |
| `0x005438E0` | `QUESTS_DispatchEvent` | calls `Quest+0xA0 + 4·event` of every quest object | I |
| `0x005439A0` | `QUESTS_DispatchUnitEvent` | same, for the quests registered on a unit (`Unit+0x74`) | I |
| `0x00543A30` | `QUESTS_MonsterDeathEvent` | event 8 for a dying monster, killer resolved to a player | I |
| `0x005449E0` | `QUESTS_ObjectOperate` | quest objects' operate dispatch by object class | I |
| `0x005537D0` | `sub_005537D0_GameForEachUnit` | calls a function on each unit of a type in the game (skips state 7 `playerbody`) | I |
| `0x00540510` | `sub_00540510_PartyForEach` | calls a function on each member of a party | I |
| `0x00559A30` | `sub_00559A30_DropItemAtUnit` | creates the item coded at `source+0xB8` (or a random base) at the source, quality given | I |
| `0x00559CE0` | `sub_00559CE0_ItemCreateSimple` | creation record for an item index, quality, ilvl; ItemCreate | I |
| `0x005466B0` | `QUESTS_GiveItem` | item by code into the player's inventory, or dropped at the player | I |
| `0x00558110` | `sub_00558110_PlayerFindItemByCode` | cursor or inventory item with a code; quest items with `questdiffcheck` count only at stat 356 ≥ difficulty | I |
| `0x00544160` | `sub_00544160_PlayerRemoveItemByCode` | removes that item | I |
| `0x00585970` | `sub_00585970_DropItemCodeAt` | creates an item by code at a unit (used for `gld`) | I |
| `0x0055A090` | `sub_0055A090_DropGoldAmount` | gold piles of a given amount at a unit | I |
| `0x0055B030` | `sub_0055B030_DropGold` | `DropGoldAmount(amount, max 32 piles)` | I |
| `0x00579D60` | `sub_00579D60_NpcItemReward` | NPC menu actions: imbue (154), socket (511), personalize (512), act travel | I |
| `0x00558270` | `sub_00558270_ItemCreateRecFromItem` | fills a creation record from an existing item | I |
| `0x0055EEA0` | `sub_0055EEA0_CursorItemConsume` | removes the item on the player's cursor | I |
| `0x0062C590` | `sub_0062C590_ItemCanImbue` | imbue test | I |
| `0x0062C6A0` | `sub_0062C6A0_ItemCanPersonalize` | personalize test | I |
| `0x0062C770` | `sub_0062C770_ItemCanQuestSocket` | Larzuk test | I |
| `0x00629C80` | `sub_00629C80_ItemBitfield1Bit0` | `bitfield1` (`+0xDC`) bit 0 of the item record | I |
| `0x00628370` | `sub_00628370_ItemSetPersonalName` | copies a name to `ItemData+0x4A` | I |
| `0x00591790` | `sub_00591790_A1Q3_ImbueDone` | word 3: set bit 0, clear bit 1 | I |
| `0x005877C0` | `sub_005877C0_A5Q1_SocketDone` | word 35: set bit 0, clear bit 1 | I |
| `0x0058BC00` | `sub_0058BC00_A5Q4_PersonalizeDone` | word 38: set bit 0, clear bit 1 | I |
| `0x00591AC0` | `sub_00591AC0_A1Q3_MalusDrop` | Malus (`hdm`) from its object | I |
| `0x005965A0` | `sub_005965A0_A1Q6_AndarielDeath` | Andariel's death: bits, three gems | I |
| `0x00596210` | `sub_00596210_A1Q6_SetKilled` | word 6 bits 13 and 1 | I |
| `0x00595C60` | `sub_00595C60_A1Q6_NpcMessage` | Warriv: word 6 bit 1 → bit 0 | I |
| `0x00595710` | `sub_00595710_A1Q5_CountessDeath` | the Countess's death: word 5 bits, no item | I |
| `0x00593E70` | `sub_00593E70_A1Q4_CowKingDeath` | the Cow King's death: word 4 bit 10, eight `vps` | I |
| `0x00593AF0` | `sub_00593AF0_A1Q4_InifussDrop` | Scroll of Inifuss (`bks`) from the tree | I |
| `0x00594630` | `sub_00594630_A1Q4_WirtGold` | Wirt's body: 10–19 gold piles | I |
| `0x00592250` | `sub_00592250_A1Q4_NpcMessage` | Akara's ring, the deciphered scroll | I |
| `0x00583E70` | `sub_00583E70_WirtLegDrop` | `leg` from its object | I |
| `0x00599020` | `sub_00599020_A2Q1_RadamentDeath` | Book of Skill (`ass`) per qualifying player | I |
| `0x00599C10` | `sub_00599C10_A2Q2_ScrollChest` | `tr1` chest | I |
| `0x00599CF0` | `sub_00599CF0_A2Q2_StaffChest` | `msf` chest | I |
| `0x00599DF0` | `sub_00599DF0_A2Q2_CubeChest` | `box` chest | I |
| `0x0059A7E0` | `sub_0059A7E0_A2Q3_ViperChest` | `vip` chest | I |
| `0x0059D050` | `sub_0059D050_A2Q6_DurielDeath` | Duriel's death: word 14 bit 5 | I |
| `0x005B7A60` | `sub_005B7A60_A3Q1_TomeDrop` | `bbb` from its object | I |
| `0x005B8860` | `sub_005B8860_A3Q2_HeartChest` | `qhr` chest | I |
| `0x005B8940` | `sub_005B8940_A3Q2_EyeChest` | `qey` chest | I |
| `0x005B8A20` | `sub_005B8A20_A3Q2_BrainChest` | `qbr` chest | I |
| `0x005B9980` | `sub_005B9980_A3Q3_GidbinnDrop` | `g33` from a dying monster | I |
| `0x005B9240` | `sub_005B9240_A3Q3_NpcMessage` | Ormus's rare ring | I |
| `0x005BAB60` | `sub_005BAB60_A3Q4_FigurineDrop` | `j34` from a dying monster | I |
| `0x005BA320` | `sub_005BA320_A3Q4_NpcMessage` | `g34`, `xyz` | I |
| `0x005BBC00` | `sub_005BBC00_A3Q5_CouncilDeath` | `qf1`, then `box` | I |
| `0x005BC8B0` | `sub_005BC8B0_A3Q6_MephistoDeath` | Mephisto's death: soulstones | I |
| `0x005BC140` | `sub_005BC140_A3Q6_SetDone` | word 22 bits 13, 0, 11 | I |
| `0x005B52E0` | `sub_005B52E0_A4Q2_DiabloDeath` | Diablo's death: bits, no item | I |
| `0x005B5C10` | `sub_005B5C10_A4Q3_ForgeOperate` | Hellforge: soulstone, three hammer strikes | I |
| `0x005B6710` | `sub_005B6710_A4Q3_ForgeWave` | Hellforge: a gem wave per event, then the rune | I |
| `0x005B65D0` | `sub_005B65D0_A4Q3_HammerDrop` | `hfh`, unique | I |
| `0x00587B00` | `sub_00587B00_A5Q2_NpcMessage` | Qual-Kehk's runes | I |
| `0x00589580` | `sub_00589580_A5Q3_NpcMessage` | Malah's `ice`/`tr2`, Anya's class item | I |
| `0x0058DF20` | `sub_0058DF20_A5Q6_BaalDeath` | Baal's death: gold per qualifying player | I |
| `0x005E0070` | `sub_005E0070_UberTristramDrop` | after three uber deaths: `cm2` unique and `std` per player | I |

Data: `data:g_AndarielChippedGems@0x007361DC`, `data:g_AndarielStdGems@0x00736444`,
`data:g_ForgeGemsPerfect@0x0073E56C`, `data:g_ForgeGemsFlawless@0x0073E588`, `data:g_ForgeGemsStandard@0x0073E5A4`,
`data:g_ForgeRunesNormal@0x0073E114`, `data:g_ForgeRunesNightmare@0x0073E514`, `data:g_ForgeRunesHell@0x0073E540`,
`data:g_QualKehkRunes@0x00732FEC`, `data:g_AnyaRewardsNormal@0x00735F6C`, `data:g_AnyaRewardsNightmare@0x00735EFC`,
`data:g_AnyaRewardsHell@0x00735F34` (§ 4–6).

## Walkthrough

### 1. Quest objects, events and the quest seed

- [I] `QUESTS_InitGame` (game in ECX) allocates one 0xF8-byte quest object per `g_QuestDescs` row (and per row of a
  second table at `0x0073188C`, count `0x007318AC`): `+0x00` quest object id, `+0x04` game, `+0x08` act, `+0x09`
  active, `+0xF4` next, then calls the row's init function, which fills the callbacks at `+0xA0 + 4·event`, the record
  word at `+0xE0` and private data at `+0x18`. Then the quest control (`Game+0x10F4`): `+0x00` list head, `+0x0C` the
  game-wide record (`QUESTRECORD_Alloc`), `+0x18` the **quest seed**, seeded by `RNG_SeedInit(seed, low dword of one
  LCG step of the game seed Game+0xD0)` (the game seed is advanced). (fn:QUESTS_InitGame@0x00545D80 0x00545F10–0x00545F3E,
  fn:QUESTS_GetSeed@0x005438B0, struct:Game+0xD0)
- [I] Every quest-seed draw in this finding is the LCG step `s ← lo·0x6AC690C5 + hi` inlined, then `low32(s) mod n`
  (unsigned; the compiler's multiply-shift for 7 and 5) or `RNG_Range`/`RNG_RandLoHi` on the same seed. The quest seed
  is also drawn by quest code that creates no item (0x0058E830, 0x00592E90, 0x0059B1C0, 0x0059EDC0, 0x005BD390), so
  its state at a drop depends on the game's quest history. (fn:QUESTS_GetSeed@0x005438B0, fn:RNG_Range@0x0045C390,
  fn:RNG_RandLoHi@0x004BC500)
- [I] Events: `QUESTS_DispatchEvent` calls `Quest+0xA0 + 4·event` of each quest object (of the event unit's act, when
  asked). Monsters registered with a quest (`QUESTS_HookMonster`, the "quest hook N" of
  [monsters/0003](../monsters/0003-special-monsters.md)) carry a list at `Unit+0x74`, and
  `QUESTS_MonsterDeathEvent` sends **event 8** (`Quest+0xC0`) to those quests with an event block `{game, 8,
  monster, killer player}`; a pet's or hireling's kill is resolved to its owner first (`0x0058F090`). (fn:QUESTS_DispatchEvent@0x005438E0,
  fn:QUESTS_DispatchUnitEvent@0x005439A0, fn:QUESTS_MonsterDeathEvent@0x00543A30 0x00543A6B, fn:QUESTS_HookMonster@0x005436B0)

### 2. B6: the quest TC switch and the killer

```c
// fn:MONSTER_DropItems@0x005A6600, 0x005A6705–0x005A67F1 (trimmed; ECX game, ctx = arg 4)
tc = <TreasureClass1..3 or the superunique TC, items/0001 §3>;
if (mon->TCQuestId /*+0x9E u8*/ && mon->tc[diff][3] /*+0x8C + 8·diff u16*/ && ctx && (k = ctx->killer /*+8*/)) {
    if (k->type != 0) {                                          // not a player
        p = sub_0058F0D0_MonsterOwner(k);                         // monster → its owner unit, else 0
        if (sub_0063A690_UnitHasExpState(k)                       // state of the `exp` mask
            && (sl = sub_00625760_StatListFindFlag(k, 0x800)))
            p = sub_00552F60_GameFindUnit(game, OwnerType(sl) /*+8*/, OwnerGuid(sl) /*+0xC*/);
        if (p) k = p;
    }
    if (k->type == 0 && (r = QUESTS_PlayerRecord(game, k))
        && GetState(r, TCQuestId, 15) != 1 && GetState(r, TCQuestId, 1) != 1
        && GetState(r, TCQuestId, TCQuestCP /*+0x9F u8*/) != 1)
        tc = mon->tc[diff][3];                                    // TreasureClass4 / (N) / (H)
}
TC_DropByIndex(game, mon, ctx->killer, tc, ...);                  // the original killer, not k
```

- [I] The record read is the resolved player's own (`QUESTS_PlayerRecord(game, k)` = `sub_006221A0_PlayerData(k) +
  0x10 + 4·Game+0x6D`). The party is not consulted; in a party only the player credited with the kill decides. The
  TC walk itself still receives the **unresolved** killer (`ctx+8`), as before. (fn:QUESTS_PlayerRecord@0x00543520,
  fn:sub_006221A0_PlayerData@0x006221A0, fn:MONSTER_DropItems@0x005A6600 0x005A6817)
- [I] The state test: `sub_0063A690_UnitHasExpState` loads the bit-set at `DataTables+0x144` and calls
  `sub_0063A130_UnitHasStateInMask`, which ANDs it with the unit's state mask (`statlist+0x58`) word by word over
  `(nStates + 31) / 32` words. The states loader builds 40 bit-sets at `DataTables+0xCC + 4i`, set *i* holding the
  states whose flag bit *i* is set (`sub_00611D60_StatesMaskBuild`); set 30 (`0x144`) is the flag bit the loader's
  descriptor gives the column `exp`. In the shipped `states.txt` that column is 1 on rows 53 `conversion`, 57
  `attract` and 59 `confuse`. (fn:sub_0063A690_UnitHasExpState@0x0063A690, fn:sub_0063A130_UnitHasStateInMask@0x0063A130,
  fn:sub_00611D60_StatesMaskBuild@0x00611D60, 0x00618B77, `states.txt` column `exp`)
- [I] The owner of the flagged stat list is found by its stored type and GUID (`sub_00625250_StatListOwnerType`,
  `sub_006252B0_StatListOwnerGuid`, then `sub_00552F60_GameFindUnit`); the flag `0x800` is the stat-list flag of
  those states' lists, read here only. (fn:sub_00625250_StatListOwnerType@0x00625250, fn:sub_006252B0_StatListOwnerGuid@0x006252B0,
  fn:sub_00552F60_GameFindUnit@0x00552F60)
- [I] A missile is never resolved here: `sub_0058F0D0_MonsterOwner` answers only for unit type 1 (monsters). Whether
  the kill context's killer is ever a missile rather than its owner is left open. (fn:sub_0058F0D0_MonsterOwner@0x0058F0D0)

**Order of the drop and the quest scripts.**

```text
sub_0057CCB0_UnitKilled (monster):                     [I] (fn:sub_0057CCB0_UnitKilled@0x0057CCB0)
  0x0057CDC4  sub_005A7C20_MonSetMode(game, {mode 0 …}, 1)
                └ 0x005A7D4C sub_005A78A0_MonModeRecord → record of mode 0 (table 0x006E2260: start = sub_005A6FF0_MonDeathEvent)
                └ 0x005A7D67 call start → MonDeathDrop → MONSTER_DropItems (B6 reads the killer's bits)
  0x0057CDD9  QUESTS_MonsterDeathEvent → each registered quest's Quest+0xC0 (the script sets this kill's bits)
```

- [I] So for Andariel and Duriel the bits their scripts set at the kill (bit 1, bit 5) cannot hide the quest TC of the
  kill that sets them. `sub_005A78A0_MonModeRecord` also reads `MonStats+0x1A5` and may pick another table; that the
  five quest-TC classes use the standard table is not checked. (fn:sub_0057CCB0_UnitKilled@0x0057CCB0,
  fn:sub_005A7C20_MonSetMode@0x005A7C20, fn:sub_005A78A0_MonModeRecord@0x005A78A0, fn:sub_005A6FF0_MonDeathEvent@0x005A6FF0)

### 3. The three bits for the five quest-TC classes

`TCQuestId`/`TCQuestCP` in the merged `monstats.txt` (the only non-zero `TCQuestId` rows):

| class | `hcIdx` | `TCQuestId` | `TCQuestCP` | `TreasureClass4` / (N) / (H) |
|---|---|---|---|---|
| `andariel` | 156 | 6 | 1 | `Andarielq` / `Andarielq (N)` / `Andarielq (H)` |
| `duriel` | 211 | 14 | 5 | `Durielq` … |
| `mephisto` | 242 | 22 | 0 | `Mephistoq` … |
| `diablo` | 243 | 26 | 0 | `Diabloq` … |
| `baalcrab` | 544 | 40 | 0 | `Baalq` … |

- [I] **Bit 15.** No code sets bit 15 of a player record except the save loader (`QUESTRECORD_LoadBytes`: bit 1 → bit
  15 for words 0–41) and nothing clears it except one call for word 9 (0x00599293); the setter dump of
  `QUESTRECORD_SetState` with constant arguments shows bit 15 only in `sub_00546270_QuestsPlayerJoin` (the game-wide
  record). So bit 15 means "this character saved the game with bit 1 set". (fn:QUESTRECORD_LoadBytes@0x0065C4D0,
  fn:sub_00546270_QuestsPlayerJoin@0x00546270, fn:QUESTRECORD_SetState@0x0065C360)
- [I] **Andariel (word 6).** Her death callback (`Quest+0xC0` = `sub_005965A0_A1Q6_AndarielDeath`) sets bits 13 and 1
  of the killer when bits 0 and 1 are clear, and later per-player callbacks do the same for players in level 37 with
  bits 0 and 15 clear and for the killer's party in Act I. Warriv (npc 155, message `0xB7`) with bit 1 set clears bit
  1 and sets bit 0. Nothing else writes bits 0, 1 or 15 of word 6. With `TCQuestCP` = 1, the test is "bits 1 and 15
  clear", so: **first kill → quest TC; a later kill in the same game before the report → normal TC; after the report
  (bit 0, bit 1 clear) → quest TC in every later game; a save between the kill and the report → bit 15 → normal TC for
  good.** (fn:sub_005965A0_A1Q6_AndarielDeath@0x005965A0, fn:sub_00596210_A1Q6_SetKilled@0x00596210,
  fn:sub_00595C60_A1Q6_NpcMessage@0x00595C60 0x00595D92, 0x00595D9C)
- [I] **Duriel (word 14).** `sub_0059D050_A2Q6_DurielDeath` sets bit 5 of the killer (and of players in level 73 and of
  the killer's party in Act II) when bits 0, 3, 4 and 5 are clear. The NPC script later sets bits 4, 0, 6–11 and clears
  3 and 4; bit 5 is never cleared and bit 1 is never set. So the quest TC is used until the first Duriel kill in that
  difficulty, then never. (fn:sub_0059D050_A2Q6_DurielDeath@0x0059D050, 0x0059CD2F–0x0059CEA5)
- [I] **Mephisto (22), Diablo (26), Baal (40)** (`TCQuestCP` = 0, the test is bits 0, 1, 15): the death scripts set
  bit 0 (with 13 and others) on the killer and qualifying players: Mephisto `sub_005BC140_A3Q6_SetDone` (bits 13, 0,
  11); Diablo through `0x005B4D20` (13, 0, 6, 7); Baal through `0x0058DC60`/`0x0058DD30` (0, 13). So the quest TC is
  used until the first kill. (fn:sub_005BC8B0_A3Q6_MephistoDeath@0x005BC8B0, fn:sub_005BC140_A3Q6_SetDone@0x005BC140,
  fn:sub_005B52E0_A4Q2_DiabloDeath@0x005B52E0, fn:sub_0058DF20_A5Q6_BaalDeath@0x0058DF20)
- Phase 2 cases (B6 taken and not taken): Andariel fresh (quest TC), Andariel again in the same game (normal), Andariel
  after the report in a new game (quest TC), Andariel with bit 15 (normal); Duriel fresh and with bit 5; Mephisto fresh
  and with bit 0; a kill by a hireling or a Necromancer's golem with the owner fresh (quest TC); a party kill where only
  the non-killer is fresh (normal).

### 4. Special drops

**Andariel's gems** (`sub_005965A0_A1Q6_AndarielDeath`, event 8, quest active, the killer present with word 6 bits 0
and 1 clear):

```text
SetKilled(killer record)                                   ; bits 13, 1
repeat 2: s ← LCG(quest seed); monster+0xB8 ← g_AndarielChippedGems[low32(s) mod 7]   ; gcv gcr gcb gcy gcg gcw skc
          DropItemAtUnit(quality 2, source = Andariel)
s ← LCG(quest seed); monster+0xB8 ← g_AndarielStdGems[low32(s) mod 7]                 ; gsv gsr gsb gsy gsg gsw sku
DropItemAtUnit(quality 2); monster+0xB8 ← 0
```

- [I] Every difficulty, every game type. The ilvl is Andariel's level (stat 12). No gem drops for a killer who already
  has bit 0 or bit 1. (0x00596639–0x00596730, data:g_AndarielChippedGems@0x007361DC, data:g_AndarielStdGems@0x00736444,
  fn:sub_00559A30_DropItemAtUnit@0x00559A30)

**The Countess** (quest hook 5): her death callback `sub_00595710_A1Q5_CountessDeath` sets word 5 bits for the
players and arms a timer; it creates no item.

- [I] Her drop is her superunique TC (`Countess`, `Countess (N)`, `Countess (H)`); her class `corruptrogue3` has
  `TCQuestId` 0, so B6 never applies and her drop has no quest dependence in this binary. The rune picks are inside
  that TC tree ([TreasureClassEx](../../tables/TreasureClassEx.md)). (fn:sub_00595710_A1Q5_CountessDeath@0x00595710,
  fn:MONSTER_DropItems@0x005A6600, tbl:SuperUniques.txt:TC, tbl:MonStats.txt:TCQuestId)

**The Cow King** (quest hook 4, `sub_00593E70_A1Q4_CowKingDeath`):

```text
if killer: if killer word 4 bit 10: return                                  ; already credited: nothing at all
           if not (classic ? word 26 bit 0 : word 40 bit 0): return         ; Diablo (classic) / Baal (expansion) not done
           set killer word 4 bit 10
for each player: 0x00593E30 ; then
monster+0xB8 ← 'vps '; repeat 8: DropItemAtUnit(quality 0, source = Cow King)
```

- [I] The Cow King's own TC (`Cow King`, superunique) drops as usual before this (§ 2). The eight stamina potions drop
  when the kill has no killer or the killer qualifies; a killer that already has bit 10, or has not finished
  Diablo/Baal, gets none (the function returns before the drop). Bit 10 is what `CUBE_CowPortalOpen` refuses on. The
  hellbovine set-29 flag of cow drops is [items/0004](0004-uniques-sets.md)'s. (fn:sub_00593E70_A1Q4_CowKingDeath@0x00593E70,
  fn:CUBE_CowPortalOpen@0x00594140)

**The Hellforge** (word 27; object operate `sub_005B5C10_A4Q3_ForgeOperate`, timer `sub_005B6710_A4Q3_ForgeWave`):

```text
operate, word 27 bits 0 and 1 clear:
  forge state 0 and the player has 'mss ' : place it (remove the soulstone), state 2
  forge state 2, the player holds 'hfh ' : strikes += 1; at the 3rd strike:
      remove 'hfh'; player word 27 bits 13, 1; waves ← 4; per wave n ← 1
      each other player in Act IV with bits 0 and 1 clear: bits 13, 1, n += 1
      timer 7 after Objects+0xE4 >> 8 frames
timer (ForgeWave), forge active:
  repeat n: s ← LCG(quest seed); table ← waves = 4: g_ForgeGemsPerfect, 3 or 2: g_ForgeGemsFlawless, 1: g_ForgeGemsStandard
            forge+0xB8 ← table[low32(s) mod 7]; DropItemAtUnit(quality 2, source = the forge)
  if any created: waves -= 1
     if waves < 1: forge inactive; if expansion:
         r ← RNG_Range(quest seed, 11); forge+0xB8 ← runes[difficulty][r]; DropItemAtUnit(quality 2)
     else timer 7 after 20 frames
```

- [I] Gem tables (7 entries each): perfect `gpv gpr gpb gpy gpg gpw skz`, flawless `gzv glr glb gly glg glw skl`,
  standard `gsv gsr gsb gsy gsg gsw sku`. Rune tables (11 each): Normal `r01`–`r11`, Nightmare `r12`–`r22`, Hell
  `r15`–`r25`. A classic game gets no rune. The gems' ilvl is the forge's area level (`sub_00559A30` for an object:
  `Levels` monster level of its level, difficulty and expansion). (fn:sub_005B5C10_A4Q3_ForgeOperate@0x005B5C10,
  fn:sub_005B6710_A4Q3_ForgeWave@0x005B6710, data:g_ForgeGemsPerfect@0x0073E56C, data:g_ForgeGemsFlawless@0x0073E588,
  data:g_ForgeGemsStandard@0x0073E5A4, data:g_ForgeRunesNormal@0x0073E114, data:g_ForgeRunesNightmare@0x0073E514,
  data:g_ForgeRunesHell@0x0073E540)
- [I] The hammer itself: `sub_005B65D0_A4Q3_HammerDrop` (a death callback, quest active) drops `hfh` with quality 7
  (unique). (fn:sub_005B65D0_A4Q3_HammerDrop@0x005B65D0)

**Baal's first kill** (`sub_0058DF20_A5Q6_BaalDeath`, killer present, killer word 40 bit 0 clear):

- [I] For each qualifying player counted by the per-player callbacks (`+0x88`): `amount = RandLoHi(quest seed, 6000·d +
  1500, min(6000·d + 3000, 0xFFFF))` and `sub_0055B030_DropGold(amount)` at Baal. *d* = difficulty.
  (0x0058E002–0x0058E079, fn:sub_0058DF20_A5Q6_BaalDeath@0x0058DF20, fn:sub_0055A090_DropGoldAmount@0x0055A090)

**Diablo, Nihlathak, the Ancients.**

- [I] Diablo's death script (`sub_005B52E0_A4Q2_DiabloDeath`) and the Nihlathak and Ancients scripts (a5q4, a5q5)
  create no item: no call of `sub_00559A30_DropItemAtUnit`, `QUESTS_GiveItem` or the item creators lies in them. Their
  drops are their TCs (Diablo's B6 above; Nihlathak's class `nihlathakboss` has `TCQuestId` 0).
  (fn:sub_005B52E0_A4Q2_DiabloDeath@0x005B52E0)

**Uber Tristram** (`sub_005E0070_UberTristramDrop`, reached from the death handlers of classes 704 `ubermephisto`, 705 `uberdiablo` and 709 `uberbaal`):

- [I] When all three have died: `cm2` with quality 7 (charges refilled), then `Game+0x8C` copies of `std` with
  quality 2. The portals to these levels cannot open in this `Game.exe` ([save/0002 § 6](../save/0002-quest-words.md)), so
  stock play cannot reach it. (fn:sub_005E0070_UberTristramDrop@0x005E0070)

### 5. Quest items

`sub_00559A30_DropItemAtUnit(game, source, quality, &ilvl, …)`: ilvl = monster stat 12, player base stat 12, or the
area level of an object's level (minimum 1); the item index is `source+0xB8`'s code (`ITEMS_GetByCode`), or a random
base when `+0xB8` is 0; a free cell near the source; creation record `+0x0C` ilvl, `+0x14` index, `+0x30` quality;
`sub_00558D90_ItemCreate`. `QUESTS_GiveItem(game, player, code, ilvl, quality, dropIfFull)`: ilvl 0 → the player's
level; `sub_00559CE0_ItemCreateSimple`; durability set to max; into the inventory, or dropped at the player.
(fn:sub_00559A30_DropItemAtUnit@0x00559A30, fn:QUESTS_GiveItem@0x005466B0, fn:sub_00559CE0_ItemCreateSimple@0x00559CE0)

| item | source | gate | count | quality | anchor |
|---|---|---|---|---|---|
| `leg` | its object's operate | object not yet used | 1 | 2 | 0x00583E70 |
| gold | Wirt's body (object 268) | first operate | `RandLoHi(quest seed, 10, 20)` piles, one per timer | 2 | 0x00594630 |
| `bks` | Inifuss tree | word 4 bits 0, 1 clear, no `bks`/`bkd` | 1 | 2 | 0x00593AF0 |
| `bkd` | Akara (npc 148), for `bks` | — | 1 (`GiveItem`) | 2 | 0x00592313 |
| `hdm` | Malus object | word 3 bits 0, 1 clear, clvl ≥ 8 | 1 | 2 | 0x00591AC0 |
| `ass` | Radament's death | per player with word 9 bit 5 and no `ass` | per player | 2 | 0x00599020 |
| `tr1` | its chest | per player with word 10 bits 0, 3 clear | per player (identified) | 7 | 0x00599C10 |
| `msf` | its chest | per player with word 10 bit 0 clear, no `msf`/`hst` | per player (identified) | 7 | 0x00599CF0 |
| `box` | its chest | per player without `box` | per player | 2 | 0x00599DF0 |
| `vip` | its chest | not (word 11 done and (word 10 done or `vip`/`hst` held)) | per player (identified) | 7 | 0x0059A7E0 |
| `bbb` | its object | word 17 bit 0 clear | 1 | 2 | 0x005B7A60 |
| `qhr`, `qey`, `qbr` | their chests | per player | per player | 2 | 0x005B8860, 0x005B8940, 0x005B8A20 |
| `g33` | a dying monster (unique or flagged) | quest flag armed | 1 | 2 | 0x005B9980 |
| `j34` | a dying monster | killer word 19 bit 0 clear | 1 | 2 | 0x005BAB60 |
| `qf1`, then `box` | council deaths | counted players | per player | 7, 2 | 0x005BBC00 |
| `mss` | Mephisto's death | killer word 22 bit 0 clear (+ counted players) | per player | 2 | 0x005BC8B0 |
| `hfh` | its death callback | quest active | 1 | 7 | 0x005B65D0 |
| `ice`, `tr2` | Malah (messages) | word 37 states; no `ice` held | 1 each | 2 | 0x0058964F, 0x005896DF |

- [I] The chest functions (`tr1`, `msf`, `box`, `vip`, the Khalim chests) also run the chest's normal TC drop
  (`sub_00585B90_ObjectChestDrop`) and then `5 + low32(LCG(quest seed)) mod 5` gold piles (`sub_00585970_DropItemCodeAt`
  with `gld`, quality 2). (fn:sub_00599C10_A2Q2_ScrollChest@0x00599C10, fn:sub_00599CF0_A2Q2_StaffChest@0x00599CF0,
  fn:sub_00599DF0_A2Q2_CubeChest@0x00599DF0, fn:sub_0059A7E0_A2Q3_ViperChest@0x0059A7E0,
  fn:sub_005B8860_A3Q2_HeartChest@0x005B8860, fn:sub_005B8940_A3Q2_EyeChest@0x005B8940,
  fn:sub_005B8A20_A3Q2_BrainChest@0x005B8A20, fn:sub_00585B90_ObjectChestDrop@0x00585B90, fn:sub_00585970_DropItemCodeAt@0x00585970)
- [I] **Duplicates.** A script refuses a duplicate only through its own test: the quest bits, or "the player already
  has the item". `sub_00558110_PlayerFindItemByCode` looks at the cursor item and the inventory (not page 1); a quest
  item (`quest` ≠ 0) whose record has `questdiffcheck` counts only when its stat 356 is ≥ the game's difficulty.
  `sub_00557AB0_ItemInitStats` gives every created item with `quest` ≠ 0 and `questdiffcheck` ≠ 0 stat 356 = the game
  difficulty. So a Normal-difficulty staff does not stop a Nightmare chest from making a new one; the cube (`box`,
  `questdiffcheck` blank) does. (fn:sub_00558110_PlayerFindItemByCode@0x00558110 0x0055815E,
  fn:sub_00557AB0_ItemInitStats@0x00557AB0 0x00557E61–0x00557EC3, tbl:Misc.txt:quest, tbl:Misc.txt:questdiffcheck)
- [I] Per-player loops (`sub_005537D0_GameForEachUnit`) visit every player unit in the game except those in state 7
  (`playerbody`), wherever they are; the party loops (`sub_00540510_PartyForEach`) visit the members of one party.
  (fn:sub_005537D0_GameForEachUnit@0x005537D0, fn:sub_00540510_PartyForEach@0x00540510)

### 6. NPC rewards

`sub_00579D60_NpcItemReward(game, action, npcGuid, itemGuid)`, player in EDX; the item is the player's cursor item
(`0x00578610`), consumed by `sub_0055EEA0_CursorItemConsume`.

**Charsi's imbue** (npc 154 `charsi`, word 3 bit 1 set):

```text
if not ItemCanImbue(item): refuse (message 7), item back
rec ← ItemCreateRecFromItem(item)                 ; game, index (same base), quality, flags +0x44, seeds, durability, …
rec.flags80 |= 0x20 | (ethereal(item) ? 0x04 : 0x02)   ; force ethereal / no ethereal roll; staff-mod bonus = ilvl
keep the personalized name if flag 0x1000000
CursorItemConsume(item)
rec.quality ← 6; rec.ilvl ← clvl (base stat 12, min 1); if rec.ilvl > 5: rec.ilvl += 4
new ← ItemCreate(rec)                             ; restore = 0: fresh seeds from the game seed
place in the inventory or drop; ImbueDone (word 3: set bit 0, clear bit 1)
```

- [I] `sub_0062C590_ItemCanImbue` refuses: an item whose `ITEMS_GetType` is 4, item flag `0x1000` in `ItemData+0x18`,
  a record without `bitfield1` bit 0, a throwable (unless the unit flag bit 25 at `Unit+0xC8`), a quest item other
  than `leg`, an item holding socketed items, a socketed item (`0x800`), and qualities 4–9. So low, normal and
  superior bases only. (fn:sub_0062C590_ItemCanImbue@0x0062C590, fn:sub_00629C80_ItemBitfield1Bit0@0x00629C80,
  tbl:Weapons.txt:bitfield1)
- [I] The new item is a fresh creation (`restore` `+0x2C` = 0), so its seeds come from the game seed through
  `sub_00555230_SUnitCreate`, and the rare build is `items/affixes`' ordinary rare path with that ilvl; the old item's
  seeds copied into the record (`+0x48`, `+0x4C`) are not used. (fn:sub_00579D60_NpcItemReward@0x00579D60 0x0057A020–0x0057A0CB,
  fn:sub_00558270_ItemCreateRecFromItem@0x00558270, fn:sub_00591790_A1Q3_ImbueDone@0x00591790, fn:sub_00558D90_ItemCreate@0x00558D90)

**Larzuk's socket** (npc 511 `larzuk`, word 35 bit 1 set):

```text
if not ItemCanQuestSocket(item): refuse
copy ← ItemCopy(item); CursorItemConsume(item); set flag 0x800 on the copy
max ← ItemMaxSockets(copy)            ; items/0007
q ← quality(copy)
n ← q = 4      ? 1 + RangeB(ItemSeed(copy), min(max, 2))    ; one draw even when the bound is 1
  : 5 ≤ q ≤ 9  ? 1                                          ; set, rare, unique, crafted, 9 (when max > 0)
  :              max                                        ; low, normal, superior
ITEMS_SetSockets(copy, n); place; SocketDone (word 35: set bit 0, clear bit 1)
```

- [I] `sub_0062C770_ItemCanQuestSocket` needs: no item flag `0x1000` or `0x100`, a non-quest item (or `leg`), nothing
  socketed in it, flag `0x800` clear, `ItemMaxSockets` ≠ 0 and 0 sockets now. `ITEMS_SetSockets` applies its own caps
  ([items/0007 § 7](0007-sockets-runewords.md)). The draw is on the copy's item seed. A crafted item asks for 1 here,
  so Larzuk does **not** reach items/0007's crafted-above-1 case. (fn:sub_00579D60_NpcItemReward@0x00579D60
  0x0057A3A0–0x0057A3E0, fn:sub_0062C770_ItemCanQuestSocket@0x0062C770, fn:RNG_RangeB@0x0045C3E0,
  fn:sub_0062BC20_ItemMaxSockets@0x0062BC20, fn:ITEMS_SetSockets@0x0062BCB0, fn:sub_005877C0_A5Q1_SocketDone@0x005877C0)

**Anya's personalization** (npc 512 `drehya`, word 38 bit 1 set):

- [I] `sub_0062C6A0_ItemCanPersonalize` needs: not flag `0x1000`; base type not 5, 6 or 7; flag `0x100` clear; not
  already personalized; record `compactsave` (`+0x143`) 0 and `Nameable` (`+0x145`) ≠ 0. The item is copied
  (`sub_0055A2A0_ItemCopy`), the original consumed, flag `0x1000000` set and the player's name copied to
  `ItemData+0x4A`; no stat, affix or seed is touched. Then `PersonalizeDone` (word 38: set bit 0, clear bit 1).
  (fn:sub_0062C6A0_ItemCanPersonalize@0x0062C6A0, fn:sub_00628370_ItemSetPersonalName@0x00628370,
  fn:sub_0055A2A0_ItemCopy@0x0055A2A0, fn:sub_0058BC00_A5Q4_PersonalizeDone@0x0058BC00, tbl:Armor.txt:nameable)

**Other given items** (`QUESTS_GiveItem`):

| NPC (quest) | item | ilvl | quality | draws | anchor |
|---|---|---|---|---|---|
| Akara (npc 148, word 4) | `rin` | 7 / 30 / 60 | 4 / 6 / 6 (Normal / NM / Hell) | — | 0x005923E5–0x00592412 |
| Ormus (npc 255, word 19) | `rin` | 21 / 35 / 75 | 6 | — | 0x005B93F3–0x005B941F |
| npc 264 (word 20), for `j34` | `g34` | clvl | 2 | — | 0x005BA661 |
| Alkor (npc 254, word 20), for `g34` | `xyz` | clvl | 2 | — | 0x005BA587 |
| Qual-Kehk (npc 515, word 36) | `r07`, `r08`, `r09`: the first *n* | clvl | 2 | — | 0x00587C30–0x00587C83 |
| Malah (npc 513, word 37) | `ice`, `tr2` | clvl | 2 | — | 0x0058964F, 0x005896DF |
| Anya (npc 512, word 37) | a class item | clvl | 6 | `RNG_Range(quest seed, count)` | 0x00589580 |

- [I] Qual-Kehk: *n* = 2 when word 36 bit 6 is set, else 1 when bit 7 is set, else 3; given once word 36 bit 1 is set
  (then bit 0 set, bit 1 cleared). (fn:sub_00587B00_A5Q2_NpcMessage@0x00587B00, data:g_QualKehkRunes@0x00732FEC)
- [I] Anya's Prison-of-Ice item: word 37 bit 1 set, bit 0 clear, bit 10 clear. Table = Normal unless (Nightmare and
  (`Game+0x6A` = 3 or clvl > 45)) → Nightmare, or (Hell and (`Game+0x6A` = 3 or clvl > 65)) → Hell; the row is the
  player's class (0–6); the item code is `row[RNG_Range(quest seed, count)]`; quality 6 at clvl. Rows: Normal
  `am1`–`am5`, `ob1`–`ob5`, `ne1`–`ne5`, `pa1`–`pa5`, `ba1`–`ba5`, `dr1`–`dr5`, `ktr wrb axf ces clw btl skr`;
  Nightmare `…6`–`…a` and the `9…` katars; Hell `…b`–`…f` and the `7…` katars. `Game+0x6A` is 3 in every logged
  single-player game ([items/0001](0001-tc-resolution.md)), so single player always takes the difficulty's table.
  (fn:sub_00589580_A5Q3_NpcMessage@0x00589580, data:g_AnyaRewardsNormal@0x00735F6C, data:g_AnyaRewardsNightmare@0x00735EFC,
  data:g_AnyaRewardsHell@0x00735F34, fn:RNG_Range@0x0045C390)
- [I] Akara's ring for word 4 and Ormus's ring are created with a fixed ilvl per difficulty, not the player's level.
  (fn:sub_00592250_A1Q4_NpcMessage@0x00592250, fn:sub_005B9240_A3Q3_NpcMessage@0x005B9240, fn:sub_005BA320_A3Q4_NpcMessage@0x005BA320)

### 7. The `boss` exception of monsters/pool E4

```text
0x00573E18  level ← MonStats.Level[d]                     ; i16 +0xAA + 2d, d = 0..2 after the hireling reset
0x00573E20  if Game+0x70 ≠ 0 and d > 0
0x00573E2E     and not (MonStats+0x00C & [0x006CE270] = 0x04)   ; noRatio
0x00573E3A     and not (MonStats+0x00C & [0x006CE280] = 0x40)   ; boss
0x00573E4E        level ← LevelMonLvl(levelId, d, expansion)    ; MonLvlEx
```

- [I] Read again: the two tests are the masks `g_BitMask32[2]` and `[6]` on the same byte, so a `boss` class keeps
  `Level(N)`/`Level(H)` exactly like `noRatio`. No other caller sets the level of these classes on creation in the
  paths read (the quest hooks register them only). (fn:sub_00573CB0_MonStatsInit@0x00573CB0 0x00573E2E–0x00573E40,
  tbl:MonStats.txt:boss, tbl:MonStats.txt:noRatio)
- Phase 2 case set (expansion; MonStats N/H vs `MonLvl2Ex`/`MonLvl3Ex` of the boss's level, from the merged tables):
  `andariel` in 37: 49/75 vs 43/73; `duriel` in 73: 55/88 vs 49/80; `mephisto` in 102: 59/87 vs 55/83; `diablo` in
  108: 62/94 vs 58/85; `bloodraven` in 17: 43/88 vs 36/80; `griswold` in 38: 39/84 vs 39/76 (Hell only). Any one of
  them created in Nightmare and in Hell, logged at `MonStatsInit`, closes the question; the act bosses are reached
  anyway by the B6 runs.

### 8. Boundary for Phase 2 (recommendation)

- Model (bit-exact, in `tools/`): the B6 test and the killer resolution (inputs: the killer chain and the resolved
  player's word bits, logged at `MONSTER_DropItems`); the scripted drops' draws on the quest seed (Andariel's gems, the
  Hellforge waves and rune, the quest chests' gold count, Wirt's gold count, Anya's class item, Baal's gold); the item
  chain of the imbue (record → `ItemCreate`), Larzuk's socket count and the personalization.
- Inputs, not modelled (ADR-0002, game simulation): when a quest bit is set (dialogue, timers, who is in which level),
  the per-player counts the scripts compute, and the quest-seed state on entry, which non-item quest code also draws.
  The quest seed's start value can be checked once (`QUESTS_InitGame`: one game-seed step), but each scripted drop
  should **assert** the quest seed on entry, like a boundary oracle (ADR-0004).

## Data touched

- `tbl:MonStats.txt:TCQuestId` (`+0x9E` u8), `tbl:MonStats.txt:TCQuestCP` (`+0x9F` u8), `tbl:MonStats.txt:TreasureClass4`
  (`+0x8C + 8·diff`), `tbl:MonStats.txt:boss` (`+0x00C` bit 6), `tbl:MonStats.txt:noRatio` (bit 2).
- ``states.txt` column `exp`` (flag bit 30 → `DataTables+0x144`).
- `tbl:Misc.txt:quest` (`+0x12A`), `tbl:Misc.txt:questdiffcheck` (`+0x12B`), `tbl:Weapons.txt:bitfield1` (`+0xDC`),
  `tbl:Weapons.txt:compactsave` (`+0x143`), `tbl:Armor.txt:nameable` (`+0x145`).
- `tbl:SuperUniques.txt:TC`; `tbl:Levels.txt:MonLvl2Ex`, `tbl:Levels.txt:MonLvl3Ex`.
- `struct:Game+0x10F4` quest control, `+0x6A` game type, `+0x6D` difficulty, `+0x70` expansion, `+0x8C`, `+0xD0`
  game seed; `struct:Unit+0x74` registered quests, `+0xB8` the code a scripted drop creates.

## Dead ends

- `0x00585E00` (three chest drops, then two items each of two codes from `0x00558450`/`0x005584C0`) and
  `OBJOP_Bookshelf` (`tsc`/`isc`/`tbk`/`ibk` on the object's seed) look like quest drops but are object operates with no
  quest test; they belong to `objects`. (fn:OBJOP_Bookshelf@0x00584060)
- The 400 quest-record calls Ghidra listed outside any function are the quest scripts, reached only through the
  callback tables; functions were created at their entries in the lane's Ghidra project for the call-argument dump.

## Open questions

- [L] Whether `sub_005A78A0_MonModeRecord` gives any of the five quest-TC classes a mode table other than
  `0x006E2260`, which would change the order of § 2. A Phase 2 log of B6 with the killer's bits answers it.
- [L] Whether the kill context's killer can be a missile (then B6 would not resolve it): read the damage path or log
  a kill by a missile skill.
- [L] The meaning of `ITEMS_GetType` = 4 and item flags `0x1000` and `0x100` in the imbue, socket and personalize
  tests (the ear and the "starter" flags are candidates).
- [L] The ilvl that `DropItemAtUnit` gives a scripted drop from an object in a level without a `Levels` record, and
  quality 0 in the Cow King's call (which `ItemCreateByQuality` case takes it).
- [L] The record's `+0x40` (`ITEMS_GetFileIndex` of the old item) in the imbue: whether a non-zero value can reach the
  rare build.
