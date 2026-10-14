# 0005 — Affixes: alvl, magic and rare affix picks, automagic, the other builders

> **Subsystem:** items/affixes
> **Question:** Once an item's quality is settled (or a builder has fallen back), which `MagicPrefix`, `MagicSuffix`, `RarePrefix`, `RareSuffix` and `AutoMagic` rows does it get, and in which draw order on the item seed?
> **Date:** 2026-10-14   **Plan:** 0021 (Phase 1)   **Status:** open (Phase 1 in progress)

## Functions

| Address | Name | Role | Tag |
|---|---|---|---|
| `0x005565E0` | `ITEMS_BuildMagic` | magic builder: one prefix pick, one suffix pick | I |
| `0x00556A60` | `sub_00556A60_CharmForcedAffixes` | normal-quality charm: the record's forced prefix or suffix | I |
| `0x00556E80` | `ITEMS_BuildNormal` | normal builder (expansion) | I |
| `0x005C0D00` | `sub_005C0D00_AffixCandAdd` | appends `{id, record}` to the candidate list, cap 511 | I |
| `0x005C0D70` | `sub_005C0D70_StaffModsRollV0` | staff mods, classic | I |
| `0x005C0F90` | `sub_005C0F90_StaffModsRoll` | staff mods, expansion | I |
| `0x005C1260` | `ITEMS_RollStaffMods` | class skill bonuses of a class item type | I |
| `0x005C12F0` | `sub_005C12F0_PickMagicAffixV0` | magic affix pick, classic (uniform) | I |
| `0x005C1500` | `sub_005C1500_AffixGroupTaken` | group already used by a prefix or suffix on the item | I |
| `0x005C1560` | `ITEMS_PickMagicAffix` | magic affix pick, expansion (alvl, filter, weighted draw) | I |
| `0x005C18E0` | `sub_005C18E0_PickMagicAffixByVersion` | version dispatch, no automagic group | I |
| `0x005C1940` | `sub_005C1940_PickAutoAffixByVersion` | version dispatch with an automagic group | I |
| `0x005C19A0` | `sub_005C19A0_PickRareNameV0` | rare name pick, classic | I |
| `0x005C1AB0` | `ITEMS_PickRareName` | rare name pick (uniform over the type-eligible rows) | I |
| `0x005C1BC0` | `sub_005C1BC0_PickRareNameByVersion` | version dispatch for the quality 9 name pair | I |
| `0x005C1BF0` | `ITEMS_BuildRareAffixes` | rare builder body (expansion) | I |
| `0x005C1E80` | `sub_005C1E80_ItemBuildRareV0` | rare builder body (classic) | I |
| `0x005C21A0` | `ITEMS_BuildRare` | type test, then the rare body by version | I |
| `0x005C21D0` | `sub_005C21D0_ItemBuildCrafted` | quality 8 builder | I |
| `0x005C2970` | `ITEMS_BuildSuperiorPick` | superior row pick (`QualityItems`) | I |
| `0x005C2AD0` | `ITEMS_BuildSuperior` | superior builder | I |
| `0x005C2AF0` | `sub_005C2AF0_ItemBuildLowV0` | low-quality builder, classic | I |
| `0x005C2D40` | `ITEMS_BuildLowPick` | low-quality builder, expansion | I |
| `0x005C2FB0` | `ITEMS_BuildLow` | version dispatch for the low builders | I |
| `0x00627EC0` | `ITEMS_GetPrefix` | item data `+0x38 + 2i` | I |
| `0x00627EF0` | `ITEMS_SetPrefix` | | I |
| `0x00627F80` | `ITEMS_GetSuffix` | item data `+0x3E + 2i` | I |
| `0x00627FB0` | `ITEMS_SetSuffix` | | I |
| `0x00627FE0` | `ITEMS_GetRareName1` | item data `+0x32` | I |
| `0x00628010` | `ITEMS_SetRareName1` | | I |
| `0x00628070` | `ITEMS_SetRareName2` | item data `+0x34` | I |
| `0x00628740` | `ITEMS_GetQLvl` | base `level` (`+0x0FD`) | I |
| `0x006289F0` | `sub_006289F0_ItemBaseStackable` | base `stackable` (`+0x132`) | I |
| `0x00629900` | `sub_00629900_ItemBaseHasInv` | base `hasinv` (`+0x137`) | I |
| `0x0062B400` | `ITEMS_GetBaseType` | the base's `type` (ItemTypes row) | I |
| `0x0062BA80` | `sub_0062BA80_ItemTypeThrowable` | ItemTypes `Throwable` (`+0x10`) | I |
| `0x0062BBD0` | `sub_0062BBD0_ItemTypeStaffMods` | ItemTypes `StaffMods` (`+0x1F`), 7 = none | I |
| `0x0062C0B0` | `sub_0062C0B0_ItemTypeClass` | ItemTypes `Class` (`+0x21`), 7 = none | I |
| `0x00633730` | `sub_00633730_LoadMagicAffixes` | loads and merges suffix, prefix, automagic | I |
| `0x00633ED0` | `sub_00633ED0_GetMagicAffixInfo` | returns `&g_MagicAffixInfo` | I |
| `0x00633EE0` | `MAGICAFFIX_GetRecord` | merged id → record | I |
| `0x00633F40` | `sub_00633F40_LoadRareAffixes` | loads and merges raresuffix, rareprefix | I |
| `0x00634250` | `sub_00634250_GetRareAffixInfo` | returns `&g_RareAffixInfo` | I |
| `0x00634260` | `RAREAFFIX_GetRecord` | merged id → record | I |
| `0x00636B10` | `sub_00636B10_GetQualityItemsInfo` | returns `&g_QualityItemsInfo` | I |
| `0x00636B20` | `QUALITYITEMS_GetRecord` | row → `0x70`-byte record | I |
| `0x006375B0` | `sub_006375B0_GetLowQualityInfo` | returns `&g_LowQualityItemsInfo` | I |
| `0x0065E620` | `ITEMS_MagicAffixTypeOk` | magic affix type test | I |
| `0x0065E710` | `ITEMS_RareNameTypeOk` | rare name type test | I |
| `0x0065E7D0` | `sub_0065E7D0_QualityItemTypeOk` | superior row type test | I |
| `0x006E3014` | `g_RareAffixCountTable` | `int[8]` = 3,4,4,5,5,5,6,6 | I |
| `0x0096CAA0` | `g_RareAffixInfo` | merged rare name array | I |
| `0x0096CC50` | `g_QualityItemsInfo` | `{count, records}` | I |
| `0x0096CC58` | `g_LowQualityItemsInfo` | `{count, records}` | I |
