/* Special monsters: monster data (partial), the MonUMod and SuperUniques records, the aura table (plan 0018 Phase 1).
 * Field names are ours. Evidence: docs/findings/monsters/0003-special-monsters.md. [I] unless noted.
 * Tables: MonUMod at DataTables+0xC50 (records) / +0xC54 (count); SuperUniques at DataTables+0xAD4 / +0xADC;
 * MonType is-a bit matrix at DataTables+0xC44 (u32 rows of DataTables+0xC48 dwords, DataTables+0xC40 types);
 * unique-name tables: pointers 0x0096D488 (title, prefix, suffix, appellation), counts 0x0096D498 (same order). */
#include <stdint.h>

typedef struct MonsterData {      /* Unit+0x14 of a monster (partial) */
    uint8_t  _pad00[0x14];
    uint16_t nameSeed;            /* +0x14 low 16 bits of the unit-seed step of the rndname handler (sub_005A0CE0_UModRndName); sent to clients; seeds the client name roll and the aura pick */
    uint16_t flags;               /* +0x16 0x01 placed by SpecialMonPlace, 0x02 superunique, 0x04 champion, 0x08 special (counted in region +0x2C8), 0x10 minion, 0x20 possessed, 0x40 ghostly */
    uint8_t  _pad18[0x4];
    uint8_t  mods[9];             /* +0x1C MonUMod row indices, contiguous, 0 = end (sub_005A0260_ModCount) */
    uint8_t  _pad25;
    int16_t  superUniqueId;       /* +0x26 SuperUniques row (sub_005A0200_MonSuperUniqueIdSet); read when flags & 0x02 (items/0001) */
    void    * pAiControl;         /* +0x28 group/leader link: +0x28 != 0, +0x2C/+0x30 leader type/id, +0x34 minion list (sub_0058F380_MonGroupForEach) */
} MonsterData;

typedef struct MonUModRec {       /* 0x20, MonUMod.txt; layout [C] by docs/tables/MonUMod.md */
    uint32_t id;                  /* +0x00 = row index = handler index into g_UModHandlers (0x0073C008) */
    uint16_t version;             /* +0x04 >= 100: refused unless the game is expansion (sub_005A03E0_ModEligible) */
    uint8_t  enabled;             /* +0x06 0: refused */
    uint8_t  xfer;                /* +0x07 copied to unique minions (sub_005A0930_ModsXferCopy) */
    uint8_t  champion;            /* +0x08 1: champion pick only; 0: unique pick only */
    uint8_t  fPick;               /* +0x09 1: needs MonStats2 mode bit 4 (A1); 2: refused to isMelee / nomultishot; 3: needs mode bit 2 (WL) */
    int16_t  exclude[2];          /* +0x0A MonType rows the mod may not go on; the loop stops at the first <= 0 */
    int16_t  cpick[3];            /* +0x0E champion weight per difficulty, read at +0x0E + 2*d (sub_005A0500_ChampionModPick) */
    int16_t  upick[3];            /* +0x14 unique weight per difficulty, read at +0x14 + 2*d (sub_005A0600_UniqueModPick) */
    uint16_t fInit;               /* +0x1A no reader found */
    int32_t  constants;           /* +0x1C a list indexed by row (sub_005A00F0_UModConstant); row 0 = champion chance */
} MonUModRec;

typedef struct SuperUniqueRec {   /* 0x34, SuperUniques.txt; layout [C] by docs/tables/SuperUniques.md */
    uint16_t hcIdx;               /* +0x00 not read by sub_005A49B0_SuperUniqueSpawn */
    uint16_t nameStr;             /* +0x02 string index of Name; the client name (sub_004AC870_ClientMonNameBuild), 0 -> 5382 */
    int32_t  classId;             /* +0x04 MonStats row; < 0: not spawned */
    int32_t  key;                 /* +0x08 own row index; the switch of the hard-coded tails */
    int32_t  mod[3];              /* +0x0C MonUMod rows, stop at 0; 24 (thief) skipped */
    int32_t  monSound;            /* +0x18 */
    int32_t  minGrp, maxGrp;      /* +0x1C, +0x20 minions min..max, + difficulty when both are non-zero */
    uint8_t  autoPos;             /* +0x24 non-zero: the preset point is replaced by a random point in the room */
    uint8_t  eClass;              /* +0x25 */
    uint8_t  stacks;              /* +0x26 non-zero: may be placed again after the placed bit (game+0x1D30) is set */
    uint8_t  replaceable;         /* +0x27 */
    uint8_t  utrans[3];           /* +0x28 */
    uint8_t  _pad2B;
    uint16_t tc[3];               /* +0x2C items/0001 */
    uint16_t _pad32;
} SuperUniqueRec;

typedef struct UModAuraRow {      /* 0x14, 8 rows at 0x0073BF68 (sub_005A1650_UModAura) */
    int32_t  minLevel;            /* +0x00 row is a candidate when minLevel <= monster level */
    int32_t  add;                 /* +0x04 skill level = (add + level) * mul / div, clamped 1..99 */
    int32_t  mul;                 /* +0x08 */
    int32_t  div;                 /* +0x0C */
    int32_t  skill;               /* +0x10 Skills row */
} UModAuraRow;
