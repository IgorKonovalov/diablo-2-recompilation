/* Monster stats at creation (plan 0025 Phase 1). Field names are ours.
 * Evidence: docs/findings/monsters/0004-stats.md. [I] unless noted; [C] layouts are fixed by the loader descriptor
 * and the archivist's excel_bin diff of every record.
 * Tables: MonLvl at DataTables+0xB70 (records) / +0xB74 (count); MonProp at DataTables+0xC30 / +0xC34
 * (g_pMonProp 0x0096C860, g_nMonProp 0x0096C864); DifficultyLevels at g_pDifficultyLevels 0x0096C8AC /
 * g_nDifficultyLevels 0x0096C8B0 (read only through sub_00611D30_DifficultyRec). */
#include <stdint.h>

typedef struct MonLvlRec {        /* 0x78, MonLvl.txt; column c, difficulty d, L = 0 classic columns / 1 "L-" columns */
    uint32_t ac[2][3];            /* +0x00  AC: +0x00 + 0xC*L + 4*d */
    uint32_t th[2][3];            /* +0x18  TH */
    uint32_t hp[2][3];            /* +0x30  HP */
    uint32_t dm[2][3];            /* +0x48  DM (also the enchant handlers' base) */
    uint32_t xp[2][3];            /* +0x60  XP */
} MonLvlRec;

typedef struct MonLvlStatsOut {   /* 0x38, filled by sub_006538A0_MonLvlStats by mask bits */
    int32_t  minHp, maxHp;        /* +0x00 +0x04 mask 0x01 */
    int32_t  ac;                  /* +0x08 mask 0x02 */
    int32_t  toHit;               /* +0x0C mask 0x08 (A1TH), 0x10 (A2TH), 0x20 (S1TH) */
    int32_t  exp;                 /* +0x10 mask 0x04 */
    int32_t  a1Min, a1Max;        /* +0x14 +0x18 mask 0x08 */
    int32_t  a2Min, a2Max;        /* +0x1C +0x20 mask 0x10 */
    int32_t  s1Min, s1Max;        /* +0x24 +0x28 mask 0x20; also the noRatio El<e> min/max (masks 0x40/0x80/0x100) */
    int32_t  elMin, elMax;        /* +0x2C +0x30 masks 0x40/0x80/0x100, ratio classes only */
    int32_t  elDur;               /* +0x34 masks 0x40/0x80/0x100: MonStats El<e>Dur, never scaled */
} MonLvlStatsOut;

typedef struct MonPlayerBonus {   /* 0x14, filled by sub_00573930_MonPlayerBonus */
    int32_t  hpPct;               /* +0x00 g_PlayerHpPct[n] (0 when MonStats Align != 0) */
    int32_t  xpPct;               /* +0x04 g_PlayerXpPct[n] (0 when Align != 0) */
    int32_t  skillBonus;          /* +0x08 DifficultyLevels MonsterSkillBonus (+0x10) */
    int32_t  difficulty;          /* +0x0C game+0x6D after the clamp to 2 */
    int32_t  players;             /* +0x10 max(1, PlayerCount) when Align == 0, else 1 */
} MonPlayerBonus;

typedef struct MonPropSlot {      /* 0x10, layout [C] (descriptor of sub_00658720_MonPropLoad) */
    int32_t  prop;                /* +0x00 Properties row, -1 blank: the slot walk stops */
    int32_t  par;                 /* +0x04 */
    int32_t  min;                 /* +0x08 */
    int32_t  max;                 /* +0x0C */
} MonPropSlot;

typedef struct MonPropRec {       /* 0x138, monprop.bin; layout [C] */
    uint32_t id;                  /* +0x000 row index (name link g_MonPropLink 0x0096C85C) */
    MonPropSlot slot[3][6];       /* +0x004 difficulty-major: +0x004 + 0x60*d + 0x10*k */
    uint8_t  chance[3][6];        /* +0x124 u8; 0 = apply with no draw */
    uint16_t _pad136;
} MonPropRec;

typedef struct DifficultyLevelsRec { /* 0x58, difficultylevels.bin; offsets [C] (descriptor of sub_00617D90_DifficultyLevelsLoad) */
    int32_t  resistPenalty;       /* +0x00 */
    int32_t  deathExpPenalty;     /* +0x04 */
    int32_t  uberCodeOddsNormal;  /* +0x08 */
    int32_t  uberCodeOddsGood;    /* +0x0C */
    int32_t  monsterSkillBonus;   /* +0x10 read by sub_00573930_MonPlayerBonus: monster skill levels */
    int32_t  monsterFreezeDivisor;/* +0x14 */
    int32_t  monsterColdDivisor;  /* +0x18 */
    int32_t  aiCurseDivisor;      /* +0x1C */
    int32_t  ultraCodeOddsNormal; /* +0x20 */
    int32_t  ultraCodeOddsGood;   /* +0x24 */
    int32_t  lifeStealDivisor;    /* +0x28 */
    int32_t  manaStealDivisor;    /* +0x2C */
    int32_t  uniqueDamageBonus;   /* +0x30 no reader found */
    int32_t  championDamageBonus; /* +0x34 read by the champion, berserk and strong handlers (uniques too) */
    int32_t  hireableBossDamagePercent; /* +0x38 */
    int32_t  monsterCEDamagePercent;    /* +0x3C */
    int32_t  staticFieldMin;      /* +0x40 */
    int32_t  gambleRare, gambleSet, gambleUnique, gambleUber, gambleUltra; /* +0x44..+0x54 */
} DifficultyLevelsRec;

typedef struct ClassicDiffAdjustRow { /* 0x14, 3 rows at g_ClassicDiffAdjust 0x006EA9F0 (sub_0063EEF0_MonClassicDiffAdjust) */
    int32_t  stat;                /* +0x00 7 maxhp, 31 armorclass, 13 experience */
    int32_t  nmMul, nmDiv;        /* +0x04 +0x08 nightmare: 1/2, 10/12, 10/17 */
    int32_t  hellMul, hellDiv;    /* +0x0C +0x10 hell: 1/2, 10/12, 10/26 */
} ClassicDiffAdjustRow;
