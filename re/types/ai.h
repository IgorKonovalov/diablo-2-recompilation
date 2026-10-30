/* Monster AI machinery (plan 0052 phase 1.1): the AI table row, the per-monster AI control and path control blocks,
 * the AI event's context and the monster mode command. Field names are ours. Evidence:
 * docs/findings/ai/0001-machinery.md, docs/findings/ai/0002-pool-a.md. [I] unless noted; the AI table's row selection and five helper maps are [C]
 * by emulation (run:2026-10-27-ai-emu), which covers the code's map only. */
#include <stdint.h>

typedef struct MonAiRow {         /* 16 bytes; g_MonAiTable (0x0073CA18), 148 rows indexed by MonStats `AI` (+0x1E),
                                     then 18 state rows g_MonAiStateRows (0x0073D358) indexed by AiCtl.state */
    uint32_t searchKind;          /* +0x0 target search before the think function (sub_005B1650_MonAiTargetByKind):
                                     0 none, 1 search or idle, 2 search, 4 search or wait 20, 5 search; 3 and > 5 skip
                                     the think function (no stock row) */
    void    (*init)(void *blk);   /* +0x4 called by sub_005B0E00_MonAiInit with {ctl, 0 x6, MonStats, MonStats2} */
    void    (*think)(void *ctx);  /* +0x8 copied to AiCtl.think; NULL -> 0x005B0CD0 */
    void    (*alt)(void *ctx);    /* +0xC used instead when AiCtl.think already equals +0x8 */
} MonAiRow;

typedef struct AiCtl {            /* 0x40, MonsterData+0x28, sub_0058EBC0_AiCtlAlloc (.\Ai\AiGeneral.cpp) */
    uint32_t state;               /* +0x00 AI state 0..17: 0 = the MonStats row, else state row `state` */
    void    (*think)(void *ctx);  /* +0x04 the function the AI event calls */
    uint16_t flags;               /* +0x08 0x08 a target was found; 0x40 one-shot "search without the line test";
                                     0x20 teleport flag (sub_005DD250_AiCtlTeleportFlagSet); bit 0 set by
                                     sub_005DEB60_MonAiMove's flag 1 (sub_005DD230_AiCtlFlagSet takes the bit in DX) */
    uint8_t  _pad0A[0x2];
    uint32_t followGuid;          /* +0x0C unit to keep near (-1 none; sub_005DD330_AiCtlFollowSet) */
    uint32_t followType;          /* +0x10 its unit type (1 at allocation) */
    uint32_t aiVar14;             /* +0x14 first AI variable, cleared by MonAiInit with +0x18, +0x1C */
    uint32_t aiVar18;             /* +0x18 */
    uint32_t aiVar1C;             /* +0x1C */
    void    *pParams;             /* +0x20 circular list of parameter records (sub_0058EFA0, kind 10 = a saved point
                                     the inactive save keeps) */
    void    *pParamsHead;         /* +0x24 */
    uint32_t hasOwner;            /* +0x28 non-zero: +0x2C/+0x30 name the owner (sub_0058F030_MonSetOwner) */
    uint32_t ownerGuid;           /* +0x2C -1 at allocation */
    uint32_t ownerType;           /* +0x30 1 at allocation */
    void    *pMinions;            /* +0x34 minion list {guid, next} (sub_0058F380_MonGroupForEach) */
    uint8_t  _pad38[0x8];
} AiCtl;

typedef struct MonPathCtl {       /* 0x24, MonsterData+0x2C, sub_005A6490_MonPathCtlAlloc (.\MONSTER\MonsterMode.cpp) */
    uint8_t  _pad00[0x10];
    int32_t  stepParam;           /* +0x10 the command's +0x18, or the override's +0x1C (sub_005A63F0_MonMovePlan) */
    int32_t  followTicks;         /* +0x14 10 when the plan is not type 1 and the path has a target unit, else -1 */
    uint32_t overrideType;        /* +0x18 one-shot path type override (sub_005A6260_AiPathOverrideSet) */
    int32_t  overrideParam;       /* +0x1C one-shot stepParam override, -126..126 (sub_005DE190_MonAiPathOverride) */
    uint8_t  overrideByte;        /* +0x20 one-shot path +0x90 byte, capped at 77; default 5 */
    uint8_t  _pad21[0x3];
} MonPathCtl;

typedef struct AiCtx {            /* 0x24, on the stack of sub_005B1740_MonAiEvent, passed to every AI function */
    struct AiCtl *ctl;            /* +0x00 MonsterData+0x28 */
    uint32_t _zero04;             /* +0x04 0 */
    void    *target;              /* +0x08 the unit the target search returned (0 none) */
    uint32_t _zero0C;             /* +0x0C 0 */
    uint32_t _zero10;             /* +0x10 0 */
    int32_t  targetDist;          /* +0x14 the AI distance to it; with no target, the nearest checked player head's */
    uint32_t inMelee;             /* +0x18 sub_00622C40_InMeleeRange(unit, target, 0) */
    void    *pMonStats;           /* +0x1C MonStats record (0x1A8): aip1..8 at +0x56 + 6k + 2*difficulty */
    void    *pMonStats2;          /* +0x20 MonStats2 record (0x134) of MonStats +0x18 */
} AiCtx;

typedef struct AiParam {          /* 0x1C, a record of the circular list at AiCtl+0x20 (head) / +0x24
                                     (.\Ai\AiGeneral.cpp; docs/findings/ai/0002-pool-a.md § 4). sub_0058EC90_AiParamsAlloc,
                                     sub_0058EF40_AiParamsPush (copies +0x08..+0x18 of a block and makes it the head),
                                     sub_0058EE80_AiParamsHead, sub_0058ED10_AiParamsPop, sub_0058EEF0_AiParamsFind */
    struct AiParam *next;         /* +0x00 */
    struct AiParam *prev;         /* +0x04 */
    uint32_t kind;                /* +0x08 1 = a group call (sub_0058F730_MonHelpBlock from rows 6 and 13), 10 = a saved
                                     point (ai/0001 § 4), 14 = row 15's alt; 3, 4, 5, 7 by other AIs (later batches) */
    uint32_t w0C;                 /* +0x0C row 14 reads a unit type here; row 30 a guid (ai/0005 2.18) */
    uint32_t w10;                 /* +0x10 row 14 reads a unit guid here; row 30 a type */
    uint32_t w14;                 /* +0x14 */
    uint32_t w18;                 /* +0x18 row 15's alt tests 1 */
} AiParam;

typedef struct MonCmd {           /* 0x20, built by sub_005A7E60_MonCmdInit(unit, mode, cmd), run by sub_005A7C20_MonSetMode */
    uint32_t mode;                /* +0x00 monster mode, < 16 */
    void    *unit;                /* +0x04 */
    void    *target;              /* +0x08 target unit (the path heads for it), or 0 */
    int32_t  x;                   /* +0x0C target point when target is 0 */
    int32_t  y;                   /* +0x10 */
    uint8_t  _pad14;
    uint8_t  pathType;            /* +0x15 path type: MonCmdInit writes 101 (planned as type 13) for an every-frame mode, else 100 (no plan) */
    uint8_t  _pad16[0x2];
    int32_t  stepParam;           /* +0x18 -> MonPathCtl.stepParam */
    uint8_t  pathByte;            /* +0x1C -> path +0x90 when no override byte */
    uint8_t  _pad1D[0x3];
} MonCmd;
