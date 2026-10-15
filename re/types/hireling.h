/* Hireling.txt records, the hire list, the mercenary's pet info and the NPC records that hold the list.
 * Field names are ours. Evidence: docs/findings/hirelings/0001-hirelings.md ([I] unless noted).
 * HirelingRec offsets come from the loader's field descriptor (0x00655720) and are [C] against every row of
 * hireling.bin (all 120 records, every loaded column). */
#include <stdint.h>

typedef struct HirelingRec {      /* 0x118 bytes; g_pHirelingTxt, count g_nHirelingTxt */
    uint16_t version;             /* +0x000 `Version`: 0 classic, 100 expansion; matched against game+0x70 */
    uint16_t _pad002;
    int32_t  id;                  /* +0x004 `Id` 0..29 (fatal above 255 in an expansion install) */
    int32_t  classId;             /* +0x008 `Class`: MonStats row of the mercenary */
    int32_t  act;                 /* +0x00C `Act` 1..5 */
    int32_t  difficulty;          /* +0x010 `Difficulty` 1..3 */
    int32_t  seller;              /* +0x014 `Seller`: MonStats row of the NPC who hires out the row */
    int32_t  gold;                /* +0x018 `Gold` */
    int32_t  level;               /* +0x01C `Level`: the band start of this row */
    int32_t  expPerLvl;           /* +0x020 `Exp/Lvl` */
    int32_t  hp, hpPerLvl;        /* +0x024 `HP`, +0x028 `HP/Lvl` */
    int32_t  defense, defPerLvl;  /* +0x02C `Defense`, +0x030 `Def/Lvl` */
    int32_t  str, strPerLvl;      /* +0x034 `Str`, +0x038 `Str/Lvl` (eighths) */
    int32_t  dex, dexPerLvl;      /* +0x03C `Dex`, +0x040 `Dex/Lvl` (eighths) */
    int32_t  ar, arPerLvl;        /* +0x044 `AR`, +0x048 `AR/Lvl` */
    int32_t  share;               /* +0x04C `Share` */
    int32_t  dmgMin, dmgMax;      /* +0x050 `Dmg-Min`, +0x054 `Dmg-Max` */
    int32_t  dmgPerLvl;           /* +0x058 `Dmg/Lvl` (eighths) */
    int32_t  resist, resistPerLvl;/* +0x05C `Resist`, +0x060 `Resist/Lvl` (quarters) */
    int32_t  defaultChance;       /* +0x064 `DefaultChance` (AI only) */
    int32_t  head, torso, weapon, shield; /* +0x068..+0x074 */
    int32_t  skill[6];            /* +0x078 `Skill1..6`: Skills row, -1 empty */
    int32_t  chance[6];           /* +0x090 `Chance1..6` (AI only) */
    int32_t  chancePerLvl[6];     /* +0x0A8 `ChancePerLvl1..6` (AI only) */
    int8_t   mode[6];             /* +0x0C0 `Mode1..6` */
    int8_t   skLevel[6];          /* +0x0C6 `Level1..6` */
    int8_t   skLvlPerLvl[6];      /* +0x0CC `LvlPerLvl1..6` (32nds) */
    uint8_t  hireDesc;            /* +0x0D2 `HireDesc`: HireDesc row */
    char     nameFirst[32];       /* +0x0D3 `NameFirst` string key */
    char     nameLast[32];        /* +0x0F3 `NameLast` string key */
    uint8_t  _pad113;
    uint16_t nameFirstIdx;        /* +0x114 string index of nameFirst (filled at load, 0 in the .bin) */
    uint16_t nameLastIdx;         /* +0x116 string index of nameLast (filled at load) */
} HirelingRec;

typedef struct HireEntry {        /* 16 bytes; NpcRecord.pHireTable holds one per name index */
    uint16_t nameIdx;             /* +0x0 string index (nameFirstIdx + position) */
    uint16_t _pad2;
    uint32_t seed;                /* +0x4 low word of one NPC-seed step */
    uint32_t hired;               /* +0x8 1 once hired (or given) */
    uint32_t listed;              /* +0xC 1 when picked into the list */
} HireEntry;

typedef struct MercInfo {         /* 12 bytes; pet-list node +0x08 for pet type 7; the save header copies it */
    uint32_t seed;                /* +0x0 the hire entry's seed; save 0xB3 */
    uint16_t nameIdx;             /* +0x4 save 0xB7 (minus nameFirstIdx) */
    uint16_t _pad6;
    uint32_t hirelingId;          /* +0x8 Hireling `Id`; save 0xB9 (u16) */
} MercInfo;

typedef struct PetNode {          /* 0x18 bytes, .\PLAYER\PlayerPets.cpp; lists at PlayerData+0x44, 12 bytes per pet type */
    uint32_t flags;               /* +0x00 bit 0: dead */
    uint32_t unitId;              /* +0x04 */
    MercInfo info;                /* +0x08 */
    struct PetNode * pNext;       /* +0x14 */
} PetNode;

typedef struct NpcRecord {        /* 0x44 bytes; NpcControl.pRecords[64], keyed by MonStats row */
    int32_t  classId;             /* +0x00 MonStats row of the NPC */
    uint8_t  _pad04[0xC];
    HireEntry * pHireTable;       /* +0x10 0x450 bytes (69 entries), allocated by HIRE_BuildStock */
    uint8_t  _pad14[0xC];
    uint8_t  tradeBuilt;          /* +0x20 vendor stock built */
    uint8_t  hireBuilt;           /* +0x21 hire table built */
    uint8_t  act;                 /* +0x22 act index 0..4 (table at 0x00731188) */
    uint8_t  trader;              /* +0x23 (table at 0x00731188) */
    uint8_t  _pad24[0x20];
} NpcRecord;

typedef struct NpcControl {       /* game+0x1D24, .\UNIT\sunitproxy.cpp */
    int32_t  count;               /* +0x00 */
    NpcRecord * pRecords;         /* +0x04 */
    uint32_t seed[2];             /* +0x08 the NPC seed: Init(low of one game-seed step) at game creation */
    int32_t  count2;              /* +0x10 */
} NpcControl;
