/* Server "monster region": one per level id, built for every level at game creation from the game seed
 * (sub_00547D20_MonRegionsInit -> sub_005479C0_MonRegionsBuild). Holds the level's monster pool.
 * Field names are ours. Evidence: docs/findings/monsters/0001-level-pool.md. [C] = every field the
 * MPR line of run:2026-10-12-mon-pool logs and tools/monpool.py reproduces; [I] otherwise. */
#include <stdint.h>

typedef struct MonRegionEntry {   /* 0x34, region +0x14 + 0x34*i */
    int16_t  classId;             /* +0x00 monstats record position [C] */
    uint8_t  rarity;              /* +0x02 copy of MonStats Rarity (+0x2E) [C] */
    uint8_t  nVariants;           /* +0x03 appearance sets rolled, 0..3 [C] */
    uint8_t  variant[3][16];      /* +0x04 one byte per MonStats2 component (HD..S8), sub_005BDB20_MonVariantRoll [C] */
} MonRegionEntry;

typedef struct MonRegion {        /* 0x2E4, allocated in .\MONSTER\MonsterRegion.cpp line 0x87 */
    uint8_t  act;                 /* +0x000 Levels Act (+0x003) [C] */
    uint8_t  _pad001[3];
    int32_t  nPopulateCalls;      /* +0x004 incremented by sub_0054EBC0_RoomPopulateGate [I] */
    int32_t  nPopulatedRooms;     /* +0x008 incremented when a populate pass placed something [I] */
    int32_t  nRooms;              /* +0x00C -1 until first populate, then the level's room count (0x0061ABF0) [I] */
    uint8_t  nPool;               /* +0x010 entries from the random pick (spawn picks range over these) [C] */
    uint8_t  raritySum;           /* +0x011 sum of the pool entries' rarity (weighted pick) [C] */
    uint8_t  nEntries;            /* +0x012 entries in use, pool + classes added later by sub_00547BC0_MonRegionFindAdd [C] */
    uint8_t  _pad013;
    MonRegionEntry entries[13];   /* +0x014 [C] */
    int32_t  monDen;              /* +0x2B8 Levels MonDen[diff] (clamped to 10000 when populating) [C] */
    uint8_t  monUMin;             /* +0x2BC Levels MonUMin[diff] [C] */
    uint8_t  monUMax;             /* +0x2BD Levels MonUMax[diff] [C] */
    uint8_t  monWndr;             /* +0x2BE Levels MonWndr [C] */
    uint8_t  _pad2BF;
    int32_t  levelId;             /* +0x2C0 [C] */
    int32_t  nWanderers;          /* +0x2C4 wanderers spawned, capped at 3 (0x0054EFF0, 0x0054EF50; monsters/0002) [I] */
    int32_t  nUniques;            /* +0x2C8 special monsters (champions, uniques, pack members): ++ at 0x005A0362, -- at 0x00547F15; its low byte is compared with monUMin/monUMax (0x005BE031; monsters/0002) [I] */
    int32_t  nMonsters;           /* +0x2CC live monster count (0x00547D90..0x00547ED0) [I] */
    int32_t  unk2D0;              /* +0x2D0 [I] */
    int32_t  unk2D4;              /* +0x2D4 -1 at build [C] */
    uint8_t  quest;               /* +0x2D8 Levels Quest (+0x030) [C] */
    uint8_t  _pad2D9[3];
    int32_t  monLvl;              /* +0x2DC Levels MonLvl[diff] (classic) or MonLvlEx[diff] (expansion); written, never read [C written / I unread] */
    int32_t  monLvl2;             /* +0x2E0 same value; written, never read [C written / I unread] */
} MonRegion;
