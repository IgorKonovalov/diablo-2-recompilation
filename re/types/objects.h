/* Server object population: the object region (one per game), its per-level counters, the object unit data and the
 * handler context, plus the ObjGroup record. Field names are ours. Evidence: docs/findings/objects/0001-object-population.md
 * ([I] unless noted), docs/tables/ObjGroup.md and Objects.md (file layout). */
#include <stdint.h>

typedef struct ObjGroupRec {      /* 0x34, objgroup.bin; OBJGROUP_GetRecord (0x006412F0) returns NULL past the count */
    int32_t  id[8];               /* +0x00 Objects record index of member k; the member walk stops at the first 0 [C] */
    uint8_t  density[8];          /* +0x20 passed to the PopulateFn; must be < 0x80 */
    uint8_t  prob[8];             /* +0x28 cumulative-percent weights against one draw mod 100 [C] */
    uint8_t  shrines;             /* +0x30 not read by the populate pass */
    uint8_t  wells;               /* +0x31 not read by the populate pass */
    uint16_t _pad32;
} ObjGroupRec;

typedef struct ObjRgnLevel {      /* 0x90, one per level id >= 1, allocated by OBJRGN_Create (.\OBJECTS\objrgn.cpp) */
    uint8_t  act;                 /* +0x00 Levels Act */
    uint8_t  _pad01[3];
    int32_t  roomsVisited;        /* +0x04 +1 per room that passes the populate gate */
    int32_t  roomCount;           /* +0x08 0x7FFFFFFF until the first gated room, then LevelRoomCount */
    int32_t  unk0C;               /* +0x0C theme gate needs roomCount >= 10 * this; no writer found (0) */
    int32_t  healthShrines;       /* +0x10 shrines of code 2 placed by the shrine PopulateFn */
    int32_t  nShrinePos;          /* +0x14 shrine-handler objects placed, capped at 10 */
    int32_t  nWellPos;            /* +0x18 wells placed, capped at 4 */
    int32_t  _unk1C;              /* +0x1C set to -1 at creation */
    int32_t  wellPos[4][2];       /* +0x20 (x, y) of each well */
    int32_t  shrinePos[10][2];    /* +0x40 (x, y) of each shrine-handler object; ends at 0x90 */
} ObjRgnLevel;

typedef struct ObjRgn {           /* game +0x10F0, built at game creation (OBJRGN_Create, game-seed draw 2) */
    uint32_t seedLow, seedHigh;   /* +0x000 the object-region seed: Init(low of one game-seed step) */
    int32_t  nShrines[8];         /* +0x008 per Shrines effectclass: number of codes in the list */
    int32_t *shrines[8];          /* +0x028 per effectclass: Shrines codes in record order */
    ObjRgnLevel *level[0x400];    /* +0x048 by level id; [0] is NULL */
    /* +0x1048 debug counters (200 B), +0x1110 a list used by the waypoint InitFn (17) */
} ObjRgn;

typedef struct ObjectData {       /* 0x38, unit +0x14 for unit type 2, allocated in SUnitCreate */
    void    *objRec;              /* +0x00 Objects record (OBJECTS_GetRecord(class), class = record index) */
    uint8_t  interact;            /* +0x04 shrine code; for containers the trap type (bits 0-6) and locked (bit 7) */
} ObjectData;

typedef struct ObjCtx {           /* stack context passed in ECX to an InitFn (OBJ_ServerInit) */
    void    *game;                /* +0x00 */
    void    *unit;                /* +0x04 the object */
    void    *room;                /* +0x08 */
    uint32_t *seed;               /* +0x0C the object-region seed (ObjRgn +0x00) */
    void    *objRec;              /* +0x10 Objects record */
    int32_t  x, y;                /* +0x14, +0x18 position in subtiles */
} ObjCtx;

typedef struct ObjOpCtx {         /* stack context passed in ECX to an OperateFn (OBJ_OperateDispatch) */
    void    *game;                /* +0x00 */
    void    *unit;                /* +0x04 the object */
    void    *player;              /* +0x08 the operating unit */
    uint32_t *seed;               /* +0x0C the object-region seed */
    int32_t  objClass;            /* +0x10 */
} ObjOpCtx;
