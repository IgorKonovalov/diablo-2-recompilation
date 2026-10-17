/* Stat lists, the run-time tail of the ItemStatCost record, the timed-state request and the shrine effect table
 * (plan 0041 Phase 1). Field names are ours. Evidence: docs/findings/stats/0001-aggregate.md and
 * docs/findings/stats/0002-states.md. [I] unless noted.
 * Keys: a stat entry's key is (stat id << 16) | param (u16 param), compared as a signed 32-bit int. */
#include <stdint.h>

typedef struct StatEntry {        /* 8 bytes; arrays are sorted by key ascending (binary search 0x00624B90) */
    int32_t  key;                 /* +0x0 stat << 16 | param */
    int32_t  value;               /* +0x4 stored value (already << ValShift) */
} StatEntry;

typedef struct StatArray {        /* 8 bytes */
    StatEntry * entries;          /* +0x0 */
    int16_t  count;               /* +0x4 */
    int16_t  capacity;            /* +0x6 grows and shrinks by 4 (0x00624C80, 0x00624D10) */
} StatArray;

/* A stat list. Plain lists are 0x3C bytes (STATLIST_Alloc 0x006251F0); a unit's own list is "extended", 0x64 bytes
 * (sub_00626D40_UnitStatListCreate), with flag 0x80000000 and the fields from +0x3C on. */
typedef struct StatList {
    void    * pMemPool;           /* +0x00 */
    struct Unit * pUnit;          /* +0x04 the unit this list is linked to (set by STATLIST_LinkToUnit) */
    uint32_t ownerType;           /* +0x08 type of the unit that made the list (unit list: its own unit's type) */
    uint32_t ownerGuid;           /* +0x0C guid of that unit */
    uint32_t flags;               /* +0x10 see STATLIST_F_* */
    int32_t  state;               /* +0x14 States row, 0 = none */
    int32_t  expireFrame;         /* +0x18 timed lists: the frame at which UNIT_ExpireTimedLists frees it */
    int32_t  skill;               /* +0x1C skill that made a timed state (STATE_ApplyTimed) */
    int32_t  skillLevel;          /* +0x20 its level */
    StatArray base;               /* +0x24 the list's own entries ("base" for a unit list) */
    struct StatList * pNext;      /* +0x2C next sibling in the parent's chain */
    struct StatList * pPrev;      /* +0x30 */
    struct StatList * pParent;    /* +0x34 the unit list this list is attached under */
    void    (*pfnRemove)(struct StatList *); /* +0x38 called by STATLIST_Unlink when the list leaves a unit */
    /* extended (unit) lists only: */
    struct StatList * pChildren;  /* +0x3C attached lists that count (summed by STATLIST_SumOwnAndChildren) */
    struct StatList * pChildrenOff;/* +0x40 attached lists with flag 0x2000: kept but not summed, not propagated */
    struct Unit * pOwner;         /* +0x44 the unit whose list this is */
    StatArray full;               /* +0x48 cached full values, read by every full accessor */
    StatArray clientDirty;        /* +0x50 4-byte keys of changed stats to send (0x00624DD0) */
    uint32_t * pStateBits;        /* +0x58 two bit-sets of ceil(nStates/32) dwords: the states on, then the changed ones */
    void    (*pfnStatChanged)(void *arg, int32_t key, int32_t oldv, int32_t newv); /* +0x5C 0x0055B800 for players and monsters */
    void    * pCallbackArg;       /* +0x60 the game */
} StatList;

/* StatList.flags */
#define STATLIST_F_TIMED        0x00000002u /* has an expiry frame at +0x18 (STATE_ApplyTimed, 0x00625310) */
#define STATLIST_F_DROP_ON_MODE 0x00000004u /* freed with its state on a mode change (0x006272E0); sets 0x2 on the unit list */
#define STATLIST_F_AURA         0x00000008u /* the state's States `aura` bit */
#define STATLIST_F_CURSE        0x00000020u /* a curse list: one per unit, found by this flag */
#define STATLIST_F_ITEMPROPS    0x00000040u /* an item's property list (items/0006) */
#define STATLIST_F_EXP          0x00000800u /* the state's States `exp` bit */
#define STATLIST_F_OFF          0x00002000u /* kept on the +0x40 chain: does not count (set bonus lists until active) */
#define STATLIST_F_HAS_OPLVL    0x20000000u /* holds a stat with ISC +0x53 (op 4/5 source) */
#define STATLIST_F_NODAMAGE     0x40000000u /* linked "inactive": damage-related stats stop here */
#define STATLIST_F_EXTENDED     0x80000000u /* a unit's own list */

/* Run-time tail of struct:ItemStatCostRec (0x144 bytes, save.h), filled by ITEMSTATCOST_Load (0x00637A00).
 * The file holds 0 in all of +0x51..+0x53 and +0x5E..+0x13F. */
typedef struct StatOpIn {         /* 6 bytes, the inverse of `op stat1..3`, in source-row order */
    uint16_t opBase;              /* +0x0 the source row's `op base` */
    uint16_t source;              /* +0x2 the source stat */
    uint8_t  op;                  /* +0x4 the source row's `op` (0 ends the table) */
    uint8_t  opParam;             /* +0x5 the source row's `op param` */
} StatOpIn;

typedef struct ItemStatCostOps {  /* view of the record from +0x050 */
    uint8_t  keepZero;            /* +0x050 `keepzero`: an entry at 0 stays in the full cache */
    uint8_t  hasDependents;       /* +0x051 set on a row with an op target, and on every row named as an `op base` */
    uint8_t  hasOpIn;             /* +0x052 set on a target row */
    uint8_t  opNeedsOwnerLevel;   /* +0x053 set on a row with op 4 or 5 */
    uint8_t  op;                  /* +0x054 `op`, 0 when outside 1..13 */
    uint8_t  opParam;             /* +0x055 */
    uint16_t opBase;              /* +0x056 */
    uint16_t opStat[3];           /* +0x058 */
    uint16_t dependents[64];      /* +0x05E rows whose `op base` is this row, 0xFFFF-terminated */
    StatOpIn opIn[16];            /* +0x0DE */
} ItemStatCostOps;

/* The request STATE_ApplyTimed (0x0056E970) reads through ECX. */
typedef struct TimedStateReq {
    struct Unit * pSource;        /* +0x00 copied to the list's ownerType / ownerGuid (none: type 6, guid -1) */
    struct Unit * pTarget;        /* +0x04 */
    int32_t  skill;               /* +0x08 */
    int32_t  skillLevel;          /* +0x0C */
    int32_t  duration;            /* +0x10 frames; 0 = no expiry */
    int32_t  stat;                /* +0x14 one stat to set, -1 none */
    int32_t  statValue;           /* +0x18 */
    int32_t  state;               /* +0x1C States row */
    void    (*pfnRemove)(struct StatList *); /* +0x20 0 = STATE_DefaultRemoveCB (0x0056E900) */
} TimedStateReq;

typedef struct ShrineEffect {     /* g_ShrineEffects 0x006E1850, 24 entries by Shrines `Code` */
    void    (*pfnOperate)(void);  /* +0x0 */
    int32_t  stat;                /* +0x4 -1 none */
    int32_t  state;               /* +0x8 */
} ShrineEffect;
