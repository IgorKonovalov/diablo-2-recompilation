# 0010 — Quest drops, quest rewards and special drops

> **Subsystem:** items/quest-drops
> **Question:** How does quest state change what a kill drops (the MonStats quest TC), which items do the quest
> scripts create outside the treasure-class path (quest items, special drops, NPC rewards), with which draws, and does
> an act boss keep its MonStats level in an expansion Nightmare or Hell game?
> **Date:** 2026-10-15 (Phase 2: 2026-10-16)   **Plan:** 0032 (Phase 1, Phase 1b, Phase 2)   **Status:** open (Phase 1 read from the decompile and the
> disassembly of the pinned `Game.exe`. Phase 1b cross-check in *Leads used*: 17 verdict lines, 1 contradicted,
> the Act I `TCQuestId` labels of src:d2dfg-blizzard, settled by Phase 2. Phase 2 runtime results in
> § Phase 2, run:2026-10-16-quest-drops; review requested)

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

- [C] **B6, the quest TC switch** (run:2026-10-16-quest-drops, single player; the pet, hireling and `exp`-state resolution and "no other party member's record is read" stay `[I]`: no party was run). `MONSTER_DropItems` replaces the chosen TC with `TreasureClass4` of the difficulty
  when the class's `TCQuestId` (`+0x9E`) is non-zero, that column is set, the kill context has a killer, the killer
  resolves to a **player** (§ 2), and that player's own record has **bit 15, bit 1 and bit `TCQuestCP` of word
  `TCQuestId` all clear**. No other party member's record is read. (fn:MONSTER_DropItems@0x005A6600 0x005A6705–0x005A67F1,
  fn:QUESTS_PlayerRecord@0x00543520, fn:QUESTRECORD_GetState@0x0065C310, tbl:MonStats.txt:TCQuestId, tbl:MonStats.txt:TCQuestCP)
- [C] **The drop runs before the quest scripts see the death** (run:2026-10-16-quest-drops). The kill handler sets the monster's death mode
  (`sub_005A7C20_MonSetMode`, call at 0x0057CDC4), whose start function `sub_005A6FF0_MonDeathEvent` drops the items
  at once (0x005A7D67), and only then dispatches the quest death event (0x0057CDD9). So the three tests read the
  killer's bits **before** the boss's own quest script sets them for this kill. (fn:sub_0057CCB0_UnitKilled@0x0057CCB0,
  fn:sub_005A7C20_MonSetMode@0x005A7C20, fn:QUESTS_MonsterDeathEvent@0x00543A30)
- [C] **What the three bits mean per boss** (`[C]` for the states run:2026-10-16-quest-drops tested: Andariel with the word clear or bit 0 only, taken, and bits 1 and 15, not taken; Duriel clear or bit 0 only, taken, and bit 5, not taken; Mephisto clear, taken; and the kill-time writes of Andariel's bit 1 and Duriel's bit 5. Warriv's turn of bit 1 into bit 0, "never cleared", and Mephisto, Diablo and Baal done stay `[I]`) (the five classes with a `TCQuestId`, `TCQuestCP` from the data):
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
- [I] **Rewards.** All three NPC item services live in `NPC_MenuAction`: Charsi's imbue creates a
  **new** rare (quality 6) of the same base with **ilvl = clvl, +4 when clvl > 5**, on fresh seeds; Larzuk's socket
  copies the item and requests `max` sockets (low, normal, superior), `1 + RangeB(item seed, min(max, 2))` (magic) or 1
  (set, rare, unique, crafted, 9); Anya copies the item and writes the player's name (flag `0x1000000`); all three repair and recharge the result.
  Akara, Ormus, Malah, Anya (Prison of Ice) and Qual-Kehk give fixed or difficulty-tiered items; the Ancients and Nihlathak
  create none. (§ 6; fn:NPC_MenuAction@0x00579D60, fn:QUESTS_GiveItem@0x005466B0)
- [C] **The `boss` exception of monsters/pool E4** (run:2026-10-16-quest-drops: Andariel in Nightmare and Hell) is the byte test `MonStats+0x00C & 0x40` next to `& 0x04`
  (`noRatio`) at 0x00573E32–0x00573E40: a `boss` class keeps `Level(N)`/`Level(H)` in an expansion Nightmare or Hell
  game. The 25 `boss` classes and the Phase 2 case set are in § 7. (fn:sub_00573CB0_MonStatsInit@0x00573CB0, tbl:MonStats.txt:boss)

## Leads used

The lead pages were fetched and read **after** the walkthrough below was written (Phase 1 was committed first). One
verdict per compared claim.

- [L] src:pd-item-generation: a quest boss drops from `TreasureClass4` the first time it is killed in a difficulty and
  from `TreasureClass3` after that. **held with refinement**
  Detail: true for Duriel, Mephisto, Diablo and Baal (§ 3); Andariel differs, next line. The switch also replaces a
  champion or superunique TC, whichever was chosen ([items/0001](0001-tc-resolution.md) § 3).
- [L] src:pd-item-generation: after Andariel is killed and the player talks to an NPC, she drops from her quest TC
  after every following kill. **held**
  Detail: `TCQuestCP` = 1 makes the test "bits 1 and 15 clear"; Warriv's message turns bit 1 into bit 0 (§ 3).
- [L] src:almars-andariel-farming: kill Andariel, take the town portal, talk to Warriv and Go East, save and exit at once:
  the quest drop stays; "any improper action" spoils it. **held with refinement**
  Detail: by the code the report alone does it (bit 0 set, bit 1 cleared); what spoils it is a save while bit 1 is
  still set (bit 15 for good). The first kill gives the quest TC in any case (§ 2, order).
- [L] src:d2dfg-blizzard: `TCQuestId`: `TreasureClass4` is used when the player does not have the quest progress;
  `TCQuestCP` names the checkpoint. **held with refinement**
  Detail: three fixed tests, bits 15 and 1 always and `TCQuestCP`; the record is the resolved killer's (§ 2).
- [L] src:d2dfg-blizzard: checkpoint codes 0 "History Success", 1 "History Earned Reward", 13 "Current Game Success",
  14 "Current Game Failure", 15 "Previous Game". **held with refinement**
  Detail: bit 15 is the loader's copy of a saved bit 1 (§ 3); bits 13 and 14 are cleared on load.
- [L] src:d2dfg-blizzard: the `TCQuestId` value list: 6 "The Forgotten Tower", 7 "Sisters to the Slaughter", 13 "The
  Summoner", 14 "The Seven Tombs". **contradicted** (Act I)
  Detail: word 6 is `a1q6.cpp` (Andariel's level 37, Warriv's report), word 5 `a1q5.cpp` (the Countess's hook 5), and
  the data gives `andariel` `TCQuestId` 6. The guide's Act I labels are one higher, like Misc `quest` (quest object id + 1,
  which equals word + 1 only in Act I, § 5 "What Misc/Weapons `quest` indexes"); its Act II labels match. Backlog 2026-10-15; settled by the Andariel B6 case of Phase 2.
- [L] src:d2dfg-blizzard: `questdiffcheck` ties a quest item to the current difficulty. **held**
  Detail: stat 356 = difficulty at creation, compared in `sub_00558110_PlayerFindItemByCode` (§ 5).
- [L] src:arreat-summit-quest-pages: imbue makes a new rare from the base; the character level decides its properties.
  **held** Detail: `rec.ilvl` from clvl, fresh seeds (§ 6).
- [L] src:wikiwiki-d2r-imbue: the affix level is "clvl+4 or qlvl, whichever is higher". **held with refinement**
  Detail: the imbue sets ilvl = clvl + 4 only when clvl > 5 (else clvl); the "qlvl" part is the rare build's affix
  level ([items/0005](0005-affixes.md)), not this function. clvl ≤ 5 cannot reach the imbue on stock data (the Malus
  needs clvl ≥ 8, § 5). The page describes D2R.
- [L] src:wikiwiki-d2r-imbue: only normal items, never socketed ones; ethereal is kept. **held with refinement**
  Detail: low and superior bases pass too (qualities 1–3); ethereal is forced by record flag `0x04` and flag word `+0x44`.
- [L] src:arreat-summit-quest-pages: Larzuk gives regular items their maximum sockets, magic items 1 or 2, set, rare,
  unique and crafted items 1. **held**
  Detail: `1 + RangeB(item seed, min(max, 2))` for magic, then `ITEMS_SetSockets`' caps (§ 6).
- [L] src:arreat-summit-quest-pages: personalization adds the name, and the item is also repaired and recharged; only
  armor and weapons, not quest items or throwing potions. **held**
  Detail: Phase 1 had written "nothing else"; re-reading the shared tail of the three services shows
  `sub_005761C0_ItemRepairAll` (stack, charges, durability, broken flag) and `sub_0055FE00_ItemIdentifyAttach` on the
  result of all three. Corrected in § 6. Bases 5–7 and `Nameable` 0 are refused.
- [L] src:arreat-summit-quest-pages, src:gamebanshee-d2-quests: the Hellforge gives four random gems from normal to
  perfect and, in the expansion, one rune: El–Amn, Sol–Um, Hel–Gul. **held with refinement**
  Detail: one perfect, two flawless and one standard **per counted player**, then one rune per game (§ 4).
- [L] src:arreat-summit-quest-pages: the cow portal needs Eve of Destruction on the same difficulty; a cow-quester who
  kills the King loses the recipe; the King "always drops 8 x Stamina Potion" for the quest. **held with refinement**
  Detail: a classic game tests Terror's End (word 26) instead; the potions drop only when the killer qualifies (§ 4).
- [L] src:gamebanshee-d2-quests: Qual-Kehk gives three runes, Ral, Ort and Tal. **held with refinement**
  Detail: `r07 r08 r09`, but only the first 1 or 2 when word 36 bit 7 or bit 6 is set (§ 6).
- [L] src:gamebanshee-d2-quests: a ring from Akara; a rare ring from Ormus; a class-specific item from Anya. **held with
  refinement** Detail: Akara's ring is magic in Normal; both rings have a fixed ilvl per difficulty; Anya's item is rare
  at clvl from a per-class table (§ 6).
- [L] src:pd-item-generation: the Countess drops from `Countess Item` and `Countess Rune`. **not covered**
  Detail: the TC walk is items/0001's; this finding claims only that no quest state enters her drop, which the page
  does not contradict.
- **Not covered** by any source read: Andariel's three gems, Baal's first-kill gold, the quest chests' gold, the
  killer resolution through `exp` states, and the drop-before-script order.

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005A6600` | `MONSTER_DropItems` | TC column choice; B6 quest switch (existing row) | I |
| `0x00543520` | `QUESTS_PlayerRecord` | `(game, player)` → `PlayerData+0x10 + 4·Game+0x6D` | I |
| `0x006221A0` | `UNIT_GetPlayerData` | `Unit+0x14` of a player unit (asserts type 0) (existing row, player/0001) | I |
| `0x0063A690` | `sub_0063A690_UnitHasExpState` | unit carries a state of the `exp` state mask (`DataTables+0x144`) | I |
| `0x0063A130` | `sub_0063A130_UnitHasStateInMask` | any bit of the unit's state mask in a state bit-set (EAX unit, EBX set) | I |
| `0x00611D60` | `sub_00611D60_StatesMaskBuild` | states loader: bit-set *i* = states whose flag bit *i* is set | I |
| `0x00625760` | `sub_00625760_StatListFindFlag` | the unit's first stat list with a flag (`0x800` here) | I |
| `0x00625250` | `sub_00625250_StatListOwnerType` | stat list `+0x08` (6 if none) | I |
| `0x006252B0` | `sub_006252B0_StatListOwnerGuid` | stat list `+0x0C` | I |
| `0x0057CCB0` | `sub_0057CCB0_UnitKilled` | kill: death mode (drop) first, then the quest death event | C |
| `0x005A7C20` | `sub_005A7C20_MonSetMode` | sets a monster mode and calls the mode's start function | I |
| `0x005A78A0` | `sub_005A78A0_MonModeRecord` | the mode's function record (table `0x006E2260`) | I |
| `0x00545D80` | `QUESTS_InitGame` | one quest object per `g_QuestDescs` row, the quest seed, the game record | C |
| `0x005438B0` | `QUESTS_GetSeed` | `QuestControl+0x18` | I |
| `0x00543640` | `QUESTS_FindById` | quest object by id (`Quest+0x00`) | I |
| `0x005436B0` | `QUESTS_HookMonster` | the "quest hook" of special monsters: registers a monster with a quest | I |
| `0x005438E0` | `QUESTS_DispatchEvent` | calls `Quest+0xA0 + 4·event` of every quest object | I |
| `0x005439A0` | `QUESTS_DispatchUnitEvent` | same, for the quests registered on a unit (`Unit+0x74`) | I |
| `0x00543A30` | `QUESTS_MonsterDeathEvent` | event 8 for a dying monster, killer resolved to a player | I |
| `0x00543BD0` | `sub_00543BD0_QuestsInvItemEvent` | each inventory item with `quest` ≠ 0: event 9 (`Quest+0xC4`) of quest object `quest − 1`; then event 1 (§ 5) | I |
| `0x00555D20` | `sub_00555D20_ItemQuestHook` | sets identified; an item with `quest` ≠ 0 is registered with quest object `quest − 1` (`QUESTS_HookMonster`) (§ 5) | I |
| `0x0055CC90` | `sub_0055CC90_ItemQuestGate` | per-code and per-`quest` refusals of a quest item for a player, four item-move callers (§ 5) | I |
| `0x005449E0` | `QUESTS_ObjectOperate` | quest objects' operate dispatch by object class | I |
| `0x005537D0` | `sub_005537D0_GameForEachUnit` | calls a function on each unit of a type in the game (skips state 7 `playerbody`) | I |
| `0x00540510` | `sub_00540510_PartyForEach` | calls a function on each member of a party | I |
| `0x00559A30` | `sub_00559A30_DropItemAtUnit` | creates the item coded at `source+0xB8` (or a random base) at the source, quality given | I |
| `0x00559CE0` | `ITEMS_CreateForStore` | creation record for an item index, quality, ilvl; ItemCreate (existing row, items/0009) | I |
| `0x005466B0` | `QUESTS_GiveItem` | item by code into the player's inventory, or dropped at the player | I |
| `0x00558110` | `sub_00558110_PlayerFindItemByCode` | cursor or inventory item with a code; quest items with `questdiffcheck` count only at stat 356 ≥ difficulty | I |
| `0x00544160` | `sub_00544160_PlayerRemoveItemByCode` | removes that item | I |
| `0x00585970` | `sub_00585970_DropItemCodeAt` | creates an item by code at a unit (used for `gld`) | I |
| `0x0055A090` | `sub_0055A090_DropGoldAmount` | gold piles of a given amount at a unit | I |
| `0x0055B030` | `sub_0055B030_DropGold` | `DropGoldAmount(amount, max 32 piles)` | I |
| `0x00579D60` | `NPC_MenuAction` | NPC menu actions: imbue (154), socket (511), personalize (512), act travel (existing row, items/0009) | I |
| `0x00558270` | `sub_00558270_ItemCreateRecFromItem` | fills a creation record from an existing item | I |
| `0x0055EEA0` | `sub_0055EEA0_CursorItemConsume` | removes the item on the player's cursor | I |
| `0x0062C590` | `sub_0062C590_ItemCanImbue` | imbue test | I |
| `0x0062C6A0` | `sub_0062C6A0_ItemCanPersonalize` | personalize test | I |
| `0x0062C770` | `sub_0062C770_ItemCanQuestSocket` | Larzuk test | I |
| `0x00629C80` | `sub_00629C80_ItemMagicStockable` | `bitfield1` (`+0xDC`) bit 0 of the item record (existing row, items/0009) | I |
| `0x00628370` | `sub_00628370_ItemSetPersonalName` | copies a name to `ItemData+0x4A` | C |
| `0x005761C0` | `sub_005761C0_ItemRepairAll` | stack, charges, broken flag, durability to maximum | I |
| `0x0055FE00` | `sub_0055FE00_ItemIdentifyAttach` | identified flag; attach socketed items | I |
| `0x00591790` | `sub_00591790_A1Q3_ImbueDone` | word 3: set bit 0, clear bit 1 | I |
| `0x005877C0` | `sub_005877C0_A5Q1_SocketDone` | word 35: set bit 0, clear bit 1 | I |
| `0x0058BC00` | `sub_0058BC00_A5Q4_PersonalizeDone` | word 38: set bit 0, clear bit 1 | I |
| `0x00591AC0` | `sub_00591AC0_A1Q3_MalusDrop` | Malus (`hdm`) from its object | I |
| `0x005965A0` | `sub_005965A0_A1Q6_AndarielDeath` | Andariel's death: bits, three gems | C |
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
| `0x005B5C10` | `sub_005B5C10_A4Q3_ForgeOperate` | Hellforge: soulstone, three hammer strikes | C |
| `0x005B6710` | `sub_005B6710_A4Q3_ForgeWave` | Hellforge: a gem wave per event, then the rune | C |
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
  LCG step of the game seed Game+0xD0)` (the game seed is advanced). (fn:QUESTS_InitGame@0x00545D80 0x00545F10–0x00545F5F,
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

- [I] The record read is the resolved player's own (`QUESTS_PlayerRecord(game, k)` = `UNIT_GetPlayerData(k) +
  0x10 + 4·Game+0x6D`). The party is not consulted; in a party only the player credited with the kill decides. The
  TC walk itself still receives the **unresolved** killer (`ctx+8`), as before. (fn:QUESTS_PlayerRecord@0x00543520,
  fn:UNIT_GetPlayerData@0x006221A0, fn:MONSTER_DropItems@0x005A6600 0x005A6817)
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
level; `ITEMS_CreateForStore`; durability set to max; into the inventory, or dropped at the player.
(fn:sub_00559A30_DropItemAtUnit@0x00559A30, fn:QUESTS_GiveItem@0x005466B0, fn:ITEMS_CreateForStore@0x00559CE0)

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

**What Misc/Weapons `quest` indexes** (backlog 2026-10-15, static; replaces the earlier "quest word + 1"):

- [C] **`quest` − 1 is a quest object id** (`g_QuestDescs` `+0x10`, copied to `Quest+0x00` by `QUESTS_InitGame`),
  **not a record word**. Every reader that uses the value subtracts 1 and either looks the object up by id or keys a
  table with it: `sub_00543BD0_QuestsInvItemEvent` walks the quest list for `Quest+0x00 = quest − 1` and calls that
  object's event 9 (`Quest+0xC4`); `sub_00555D20_ItemQuestHook` registers the item with quest object `quest − 1`
  through `QUESTS_HookMonster` (the same hook the special monsters use, whose `QUESTS_FindById` compares `Quest+0x00`).
  Corroboration (second code path): the gate `sub_0055CC90_ItemQuestGate` carries its own pair table
  `{word, quest}` at `0x00731FEC` (4 pairs: 3 ↔ 4, 18 ↔ 17, 19 ↔ 18, 27 ↔ 25), and every pair is the record word
  that `g_QuestDescs` gives object `quest − 1`; "word + 1" fits only the first. (0x00543C26–0x00543C5C,
  0x00555D6D–0x00555D82, 0x0055CE90–0x0055CEC6, 0x00545DC7–0x00545DED, fn:QUESTS_FindById@0x00543640,
  fn:QUESTS_HookMonster@0x005436B0, data:g_QuestDescs@0x00731510, data:g_QuestItemWordGate@0x00731FEC,
  tbl:Misc.txt:quest, tbl:Weapons.txt:quest)
- [I] `g_QuestDescs` maps object id to record word as id = word for objects 0–6 (Act I) and then 7 → 8 … 13 → 14,
  14 → 16 … 20 → 22, 21 → 24 … 24 → 27, 25 → 29, 26 → 30, 27 → 31, 28 → 32, 29 → 33, 30 → 41, 31 → 35 … 36 → 40.
  So the stock values point at: `leg` 1 → object 0 (word 0); `hdm` 4 → 3 (word 3); `bks`/`bkd` 5 → 4 (word 4); `vip`,
  `box`, `tr1`, `hst`, `msf` 10 → 9 (word 10); `ass` 15 → 14 (word 16); `bbb` 16 → 15 (word 17); `qey`, `qhr`, `qbr`,
  `qf1`, `qf2` 17 → 16 (word 18); `d33`, `g33` 18 → 17 (word 19); `xyz`, `j34`, `g34` 19 → 18 (word 20); `luv` 20 → 19
  (word 21); `mss` 23 → 22 (word 25); `hfh` 25 → 24 (word 27); `ice`, `tr2` 32 → 31 (word 35). Three of these are not
  the object of the script that creates the item (§ 5 table): `ass` (Radament's death, word 9), `mss` (Mephisto's
  death, word 22) and `ice`/`tr2` (Malah, word 37); the code uses the value as written. (data:g_QuestDescs@0x00731510)
- [I] **`sub_0055CC90_ItemQuestGate`** returns 0 (refuse) for: a unique quest item whose unique row has `+0x2C` bit 2
  for which `0x0055CA40` (not read) returns non-zero; `ass` while word 9 bit 5 is clear; `j34` once word 20 bit 0 is set;
  `xyz` while word 20 bit 5 is clear; `g33` once word 19 bit 7 or bit 8 is set; `tr2` while word 37 bit 8 is clear or
  once bit 7 is set. Then by `quest − 1`: object 9 (word 10 bit 0 set, unless the code is `box`); object 4 (word 4 bit 0
  set, unless the code is `leg`, which has object 0 and so never reaches this branch); otherwise the pair table above
  (word bit 0 set). Finally it refuses when `0x0055CA40` returns non-zero for the player, or for any other player of the game
  (by its use, a holder test; not read). All tests read the player's record for the game's difficulty. Its callers (0x0055D011, 0x005631DE,
  0x00563631, 0x00567304) are item-move paths not read here. (fn:sub_0055CC90_ItemQuestGate@0x0055CC90,
  fn:QUESTRECORD_GetState@0x0065C310)

### 6. NPC rewards

`NPC_MenuAction(game, action, npcGuid, itemGuid)`, player in EDX; the item is the player's cursor item
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
  superior bases only. (fn:sub_0062C590_ItemCanImbue@0x0062C590, fn:sub_00629C80_ItemMagicStockable@0x00629C80,
  tbl:Weapons.txt:bitfield1)
- [I] The new item is a fresh creation (`restore` `+0x2C` = 0), so its seeds come from the game seed through
  `sub_00555230_SUnitCreate`, and the rare build is `items/affixes`' ordinary rare path with that ilvl; the old item's
  seeds copied into the record (`+0x48`, `+0x4C`) are not used. (fn:NPC_MenuAction@0x00579D60 0x0057A020–0x0057A0CB,
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
  so Larzuk does **not** reach items/0007's crafted-above-1 case. (fn:NPC_MenuAction@0x00579D60
  0x0057A3A0–0x0057A3E0, fn:sub_0062C770_ItemCanQuestSocket@0x0062C770, fn:RNG_RangeB@0x0045C3E0,
  fn:sub_0062BC20_ItemMaxSockets@0x0062BC20, fn:ITEMS_SetSockets@0x0062BCB0, fn:sub_005877C0_A5Q1_SocketDone@0x005877C0)

**Anya's personalization** (npc 512 `drehya`, word 38 bit 1 set):

- [I] `sub_0062C6A0_ItemCanPersonalize` needs: not flag `0x1000`; base type not 5, 6 or 7; flag `0x100` clear; not
  already personalized; record `compactsave` (`+0x143`) 0 and `Nameable` (`+0x145`) ≠ 0. The item is copied
  (`sub_0055A2A0_ItemCopy`), the original consumed, flag `0x1000000` set and the player's name copied to
  `ItemData+0x4A`; no affix or seed is touched. Then `PersonalizeDone` (word 38: set bit 0, clear bit 1).
  (fn:sub_0062C6A0_ItemCanPersonalize@0x0062C6A0, fn:sub_00628370_ItemSetPersonalName@0x00628370,
  fn:sub_0055A2A0_ItemCopy@0x0055A2A0, fn:sub_0058BC00_A5Q4_PersonalizeDone@0x0058BC00, tbl:Armor.txt:nameable)
  The order here is corrected by Phase 2: the repair and attach run first, the copy is placed, and only then are the flag
  and the name written ([§ Phase 2](#phase-2-runtime-results-run2026-10-16-quest-drops), 0x0057A610–0x0057A625).

- [I] **The shared tail of the three services.** Before the result is placed, each path calls
  `sub_005761C0_ItemRepairAll` (refills a throwable stack to its maximum, refills charges, repairs a broken item, sets
  durability to its maximum) and `sub_0055FE00_ItemIdentifyAttach` (sets identified, attaches socketed items). So an
  imbued, socketed or personalized item comes back repaired and recharged. Re-read for Phase 1b.
  (fn:sub_005761C0_ItemRepairAll@0x005761C0, fn:sub_0055FE00_ItemIdentifyAttach@0x0055FE00, 0x0057A0F9, 0x0057A3ED, 0x0057A581)

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

## Phase 2: runtime results (run:2026-10-16-quest-drops)

Logger `tools/gdb/quests.gdb` (`tools/gdb/quests.py` beside the pilot, item, vendor and monster-pool loggers and
`tools/gdb/tc-drops.gdb`); checks `tools/questdrops.py check` (quest seed, quest-bit writes, the scripted draws, the
three services), `tools/tc.py replay` (B6 through `b6_model`, tied to the `DROP` base of the same kill),
`tools/items_chain.py affixes` (every created item, the imbued rares among them) and `tools/monpool.py check` (every
monster level). Boundary as ruled: quest bits and per-player counts are inputs; each scripted drop takes the quest
seed it finds (`QGS`), and the start value is checked at `QUESTS_InitGame`. Agent-driven sessions on slots 3 and 4,
stock data, no forced path. Counts, sessions and shortfalls: [experiments](experiments.md#run2026-10-16-quest-drops).

- [C] **The quest seed** (§ 1): in every game `QUESTS_InitGame` stepped the game seed once and seeded the quest seed
  with `{low, 666}` of that step; every scripted drop of the run found the quest seed where the model left it (no
  non-item quest code drew in between in these games). (run:2026-10-16-quest-drops, fn:QUESTS_InitGame@0x00545D80)
- [C] **B6** (§ 2–3), 8 boss kills, each with the logged killer chain and the resolved player's word: Andariel (word 6,
  CP 1) taken with the word clear, taken again with bit 0 set and bit 1 clear (the "reported" state, Normal and Hell),
  not taken with bits 1 and 15 set (the test stops at bit 15); Duriel (word 14, CP 5) taken with the word clear, taken
  with only bit 0 set (a `quests: all` save: bit 0 is not one of the three tested bits), not taken with bit 5 set;
  Mephisto (word 22, CP 0) taken with the word clear. The `GetState` calls are made in the order 15, 1, `TCQuestCP`
  and stop at the first set bit; the TC passed to `TC_DropByIndex` is the model's in every case and is the `DROP` base.
  So `TCQuestId` 6 is record word 6 (the Act I label of src:d2dfg-blizzard is one off, as Phase 1b said).
  (run:2026-10-16-quest-drops, fn:MONSTER_DropItems@0x005A6600, tbl:MonStats.txt:TCQuestId, tbl:MonStats.txt:TCQuestCP)
- [C] **The drop runs before the quest scripts** (§ 2): in every boss kill the `B6X`/`DROP`/`TCR` lines come before
  the death script's quest-bit writes (Andariel `SetKilled` at 0x0059621D, Duriel bit 5 at 0x0059D0F5). (run:2026-10-16-quest-drops, fn:sub_0057CCB0_UnitKilled@0x0057CCB0)
- [I] **A Nova kill's killer is the player**: in all 8 kills (and every other monster kill of the run) the kill
  context's killer was the player unit, not a missile, so no resolution step ran. The pet, hireling and `exp`-state
  paths were not exercised and stay `[I]`. (run:2026-10-16-quest-drops, fn:MONSTER_DropItems@0x005A6600)
- [C] **Andariel's gems** (§ 4): one kill with bits 0 and 1 clear drew two chipped picks and one standard pick, one
  LCG step each, `low mod 7` into the two tables (`gcy`, `skc`, `gsg`); the kills with bit 0 or bit 1 set drew nothing. (run:2026-10-16-quest-drops, fn:sub_005965A0_A1Q6_AndarielDeath@0x005965A0)
- [C] **The Hellforge** (§ 4), 5 operations (3 Normal, 2 Nightmare, one player): 20 gem waves (perfect, flawless,
  flawless, standard, one LCG step and `low mod 7` each) and 5 runes (`RNG_Range(quest seed, 11)` into the
  difficulty's table: `r03 r07 r10` Normal, `r13 r19` Nightmare), quality 2, the gems' ilvl the forge's area level.
  Hell is a shortfall (three scripted attempts died on the way). Hephasto's death dropped `hfh` (quality 7, no draw) 11
  times. (run:2026-10-16-quest-drops, fn:sub_005B6710_A4Q3_ForgeWave@0x005B6710, data:g_ForgeRunesNormal@0x0073E114,
  data:g_ForgeRunesNightmare@0x0073E514)
- [C] **The forge's operate tests** (§ 4, read again at runtime): the first click needs the soulstone (`mss` held,
  `questdiffcheck` rule) and sets the object to mode 1, a timer brings it to mode 2, and each later click counts a
  strike only when `PlayerFindItemByCode('hfh ')` finds a hammer **and** the equipped right-hand weapon is `hfh`
  (`0x0063BEF0`). `hfh` has `questdiffcheck` 1, so a hammer without stat 356 ≥ the difficulty is not found: in the
  Nightmare games with a stat-356-0 hammer equipped no strike counted (3321–3324; in 3323 and 3324, which have the `FOP`
  line, every strike click reached the function with mode 2 and left the count at 0); with stat 356 = 2 it counted. Only
  356 = 0 and 356 = 2 in Nightmare were run, so the comparison at the boundary (356 equal to the difficulty) stays `[I]`. (run:2026-10-16-quest-drops, fn:sub_005B5C10_A4Q3_ForgeOperate@0x005B5C10,
  fn:sub_00558110_PlayerFindItemByCode@0x00558110, tbl:Weapons.txt:questdiffcheck)
- [C] **Charsi's imbue** (§ 6), 17 imbues (Normal 8, Nightmare 6, Hell 3) of a normal `cap` at clvl 80: the record has
  the same item index, quality 6, ilvl 84 (clvl + 4), flags `0x22` (no ethereal roll); the new item takes fresh seeds
  from the game seed and its rare build reproduces in the item chain. Only clvl 80 was run, so the `clvl ≤ 5` branch
  stays `[I]`. (run:2026-10-16-quest-drops, fn:NPC_MenuAction@0x00579D60)
- [C] **Larzuk's socket** (§ 6), 15 sockets of magic caps (max 2): one `RNG_RangeB(item seed, 2)` each on the copy's
  seed `{start seed, 666}`, `n = 1 + r` (1 ×8, 2 ×7), the stat 194 count after `ITEMS_SetSockets` equal to `n`. The
  other quality branches (low/normal/superior: max; 5–9: 1) were not run and stay `[I]`. (run:2026-10-16-quest-drops, fn:RNG_RangeB@0x0045C3E0, fn:ITEMS_SetSockets@0x0062BCB0)
- [C] **Anya's personalization** (§ 6), 15 times: the copy gets flag `0x1000000` and the player's name. Correction to
  § 6 order: the repair (`sub_005761C0_ItemRepairAll`, 0x0057A581) and the attach run before the copy is placed, and
  the flag and the name are written after the placement (0x0057A610–0x0057A625). (run:2026-10-16-quest-drops, fn:sub_00628370_ItemSetPersonalName@0x00628370)
- [C] **The `boss` exception** (§ 7): Andariel created in an expansion Nightmare game at level 49 (`Level(N)`, not
  `MonLvl2Ex` 43 of level 37) and in Hell at 75 (`Level(H)`, not 73); `tools/monpool.py` reproduces both with every
  other monster level of those games. (run:2026-10-16-quest-drops, fn:sub_00573CB0_MonStatsInit@0x00573CB0,
  tbl:MonStats.txt:boss)
- [C] **The cow level**: the cube opened the portal in the Rogue Encampment and 565 hell bovines were killed with
  their drops reproduced by `tc.py`; the Cow King was not met, so his eight `vps` stay `[I]`. (run:2026-10-16-quest-drops, fn:CUBE_CowPortalOpen@0x00594140)
- Shortfalls (stay `[I]`): Mephisto with his quest done (4 attempts), the Countess in any state (10 attempts; the
  scripted route through the five tower cellars stalled, or reached her room without reaching her), the Hell Hellforge (3 attempts, deaths),
  the Cow King. They are listed in the run record as an owner-played addendum. (run:2026-10-16-quest-drops)
- Join-time bits seen in the logs: `sub_0058E430_A5Q6_PlayerJoin` sets word 40 bit 10 when word 40 bit 0 or 15 is set
  (every `quests: all` save loaded in its played difficulty got it, the `0x1AA` byte of earlier runs); the orifice
  operate `sub_0059DC70_A2Q6_OrificeOperate` opens the one-item box when the player holds `hst`, and
  `sub_0059DD80_A2Q6_StaffPlaced` sets word 10 bits 0 and 13 (and calls `sub_0059DBD0_A2Q6_StaffPartyCredit` for the
  party). Placing the staff worked in a game whose word 14 bit 0 was already set. `[I]` (read once, seen once each). (run:2026-10-16-quest-drops, fn:sub_0058E430_A5Q6_PlayerJoin@0x0058E430, fn:sub_0059DC70_A2Q6_OrificeOperate@0x0059DC70, fn:sub_0059DD80_A2Q6_StaffPlaced@0x0059DD80, fn:sub_0059DBD0_A2Q6_StaffPartyCredit@0x0059DBD0)

## Data touched

- `tbl:MonStats.txt:TCQuestId` (`+0x9E` u8), `tbl:MonStats.txt:TCQuestCP` (`+0x9F` u8), `tbl:MonStats.txt:TreasureClass4`
  (`+0x8C + 8·diff`), `tbl:MonStats.txt:boss` (`+0x00C` bit 6), `tbl:MonStats.txt:noRatio` (bit 2).
- `states.txt` column `exp` (flag bit 30 → `DataTables+0x144`).
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

- ~~Whether `sub_005A78A0_MonModeRecord` gives any of the five quest-TC classes a mode table other than
  `0x006E2260`.~~ Answered by run:2026-10-16-quest-drops (§ Phase 2): for Andariel, Duriel and Mephisto the drop came
  before the death scripts' bit writes in every kill. Diablo and Baal were not killed.
- ~~Whether the kill context's killer can be a missile.~~ Answered for Nova (§ Phase 2): the killer of every Nova kill
  was the player unit. Other missile skills were not run.
- [L] The meaning of `ITEMS_GetType` = 4 and item flag `0x1000` in the imbue, socket and personalize tests. Flag
  `0x100` is the broken flag (`sub_005761C0_ItemRepairAll` repairs on it), so Larzuk and Anya refuse a broken item.
- [L] The ilvl that `DropItemAtUnit` gives a scripted drop from an object in a level without a `Levels` record, and
  quality 0 in the Cow King's call (which `ItemCreateByQuality` case takes it).
- [L] The record's `+0x40` (`ITEMS_GetFileIndex` of the old item) in the imbue: whether a non-zero value can reach the
  rare build.
