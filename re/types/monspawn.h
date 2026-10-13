/* Server random population of a room (plan 0014 Phase 1). Field names are ours.
 * Evidence: docs/findings/monsters/0002-room-population.md. [I] unless noted.
 * LogicBox/LogicRecord were SpawnBox/SpawnBoxes until 2026-10-13: they are the DRLG logic regions
 * (.\DRLG\DrlgLogic.cpp), which the client wall cut-away also reads (docs/findings/drlg/0004-preset-units.md). */
#include <stdint.h>

typedef struct LogicBox {         /* 0x30, one area of a DRLG room; list from DRLG room +0x64 -> +0x30 (0x0066CF30) */
    int32_t  rect0[4];            /* +0x00 left, top, right, bottom in tiles; not read by the population pass */
    int32_t  rect[4];             /* +0x10 left, top, right, bottom in tiles; x5 gives subtiles (0x00643560) */
    int32_t  kind;                /* +0x20 populated only when 0 (0x0054ED0D); merges require equal kinds (0x0066CF60) */
    int32_t  unk24;               /* +0x24 */
    int32_t  regionId;            /* +0x28 level-wide area id from level +0x1DC (0x0066CCB0); 0 = not populated (0x0054ED03) */
    struct LogicBox * pNext;      /* +0x2C (0x0054EEC3) */
} LogicBox;

typedef struct LogicRecord {       /* 0x34, DRLG room +0x64, allocated in .\DRLG\DrlgLogic.cpp (0x0066CCB0) */
    uint32_t flags;               /* +0x00 bit 0: one box covers the whole room (0x0066CCB0); else a tile grid maps to boxes (0x0066CE30) */
    int32_t  nBoxes;              /* +0x04 1 in the single-box case */
    uint8_t  _pad08[0x28];
    LogicBox * pFirst;            /* +0x30 */
} LogicRecord;

typedef struct MonSpawnReq {      /* 0x28, built on the stack by the wrappers 0x005B2F20/0x005B2F70/0x005B3040/0x005B23C0, read by sub_005B2A00_MonSpawnTry */
    void    * pGame;              /* +0x00 server game */
    void    * pRoom;              /* +0x04 active room whose seed (+0x6C) the position search draws from */
    LogicBox * pBox;              /* +0x08 0 = bound by the room rectangle instead of a box */
    int32_t  classId;             /* +0x0C MonStats record */
    int32_t  arg10;               /* +0x10 passed to SUnitCreate as its 8th argument (always 1 on this path) */
    int32_t  arg14;               /* +0x14 passed to SUnitCreate as its 9th argument (0 on this path) */
    int32_t  x;                   /* +0x18 search centre, subtiles */
    int32_t  y;                   /* +0x1C */
    int32_t  radius;              /* +0x20 < 0: test the centre only; n >= 1: rings 3, 6, .. 3n */
    uint16_t flags;               /* +0x24 0x01 probe only, 0x02 skip 0x005B21B0, 0x08 region count flag, 0x20 create arg 3 not 1, 0x40 no minions, 0x80 ignore collision */
    uint16_t _pad26;
} MonSpawnReq;
