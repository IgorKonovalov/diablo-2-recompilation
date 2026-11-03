/* The path request as PathPlan builds it, and the path record fields the request reads and writes (plan 0054 P1.1,
 * docs/findings/path/0001-pathplan-register.md) and the search's store (plan 0054 P1.2, docs/findings/path/0002-search.md).
 * Field names are ours. [I] unless the finding says [C] (by emulation,
 * run:2026-11-03-path-emu-1). The movement fields are re/types/anim.h PathMove, the collision fields
 * re/types/collision.h DynPathColl. Coordinates are subtiles; a point is a u16 pair (x | y << 16). */
#include <stdint.h>

/* The request context: a 0x34-byte local of sub_00649970_PathPlan at EBP-0x34, passed to the planner in ECX
 * (g_PathPlanFuncs[type]) and to its helpers in EBX (0x006498A0), EAX (0x00648120) and ESI (0x006483A0, 0x00648050). */
typedef struct PathPlanCtx {
    uint16_t sx, sy;              /* +0x00 the start: path +0x02, +0x06 */
    uint16_t tx, ty;              /* +0x04 the target point: path +0x10, +0x12 after the target refresh; moved by 0x00648120 */
    void   * pRoom;               /* +0x08 the unit's room: path +0x1C */
    void   * pTargetRoom;         /* +0x0C RoomAtSubtile(pRoom, tx, ty) */
    uint32_t unset10;             /* +0x10 not written by PathPlan */
    uint8_t  refresh;             /* +0x14 0x006498A0's result: 1 (no target unit, a player, monster, missile or tile), 2 (an
                                     object or item; an object of +0x13A, Objects IsDoor, moves the target 2 subtiles), 0 (no
                                     position). Doubled by PathPlanSearch (0x0067AD15), then the search's stop radius */
    uint8_t  _pad15[3];
    uint32_t limit;               /* +0x18 path +0x91 (movzx): PathSetByte90's value, at most 77; the search does not read it */
    uint8_t  b1C;                 /* +0x1C path +0x92: the search's last bound for types 0 and 16 (PathSearchRun 0x0067AC69) */
    uint8_t  _pad1D[3];
    int32_t  type;                /* +0x20 path +0x3C */
    int32_t  size;                /* +0x24 path +0x44 (UNIT_GetSizeX at creation) */
    int32_t  pattern;             /* +0x28 path +0x48 (PATH_PatternFromSize) */
    uint32_t testMask;            /* +0x2C path +0x50 */
    void   * pPath;               /* +0x30 the path record */
} PathPlanCtx;

/* The fields of the 0x200-byte dynamic path record (PATH_DynamicCreate 0x00649D00 allocates 0x200 and zeroes it) that
 * PathPlan, its helpers and setters read or write, beyond PathMove and DynPathColl. */
typedef struct PathRequestFields {
    uint8_t  _pad00[0x10];
    uint16_t tx, ty;              /* +0x10 the target point (PathSetTargetPoint 0x00648AD0; refreshed from the target
                                     unit; set to the last point after a plan without target unit and flag 0x10) */
    uint16_t px, py;              /* +0x14 the planned target, copied from +0x10 after a plan (0x00649C14) */
    uint16_t fx, fy;              /* +0x18 the target the request used (after 0x00648120), written before the slot call */
    uint8_t  _pad1C[0x38];
    uint16_t w54;                 /* +0x54 zeroed by PathPlan (0x006499CB) */
    uint8_t  _pad56[0x0E];
    uint8_t  face;                /* +0x64 the facing direction 0..63 (0x006485F0) */
    uint8_t  faceTo;              /* +0x65 the direction to turn to */
    uint8_t  faceStep;            /* +0x66 g_PathFaceStep[(faceTo - face) & 63] */
    uint8_t  b67, b68;            /* +0x67, +0x68 set by 0x006490C0; +0x68 != 0 sends a player or monster target through
                                     0x00679190 (an x87 offset of the target point) */
    uint8_t  _pad69[0x27];
    uint8_t  knockDist;           /* +0x90 countdown (PathSetByte90, PathSetKnockDist, PathStepMove) */
    uint8_t  limit;               /* +0x91 PathSetByte90 (min(v, 77)); 73 a player, 14 a monster at creation */
    uint8_t  b92;                 /* +0x92 0x00648F00 (asserts an untyped path); 70 a player at creation */
    uint8_t  stopRange;           /* +0x93 PathSetStopDist: v - 1 for v in 1..19, else 0 */
    uint8_t  budget94;            /* +0x94 PathSetByte94 (<= 255); 0x00649140 adds, clamped to 0..255; PathReplan
                                     takes the next point index off it and refuses a monster at 0 */
    uint8_t  _pad95[3];
    int32_t  typeParam;           /* +0x98 g_PathTypeParam98[type] (PathSetType): 2 for type 5, -2 for 6, -4 for 12 */
    uint32_t points[78];          /* +0x9C the point list, 78 slots to +0x1D3 (+0x1D4 is the crossed-subtile count) */
} PathRequestFields;

/* PathSearchRun's store: its 0x36FF8-byte frame from EBP-0x36FF8 (sub_0067AAA0_PathSearchRun), passed in EDI to
 * sub_0067A740_PathSearchWalk. Compared as scratch by run:2026-11-03-path-emu-2. */
typedef struct PathSearchNode {   /* 0x1C */
    int16_t  f;                   /* +0x00 g + h */
    uint16_t h;                   /* +0x02 2 max(|dx|, |dy|) + min(|dx|, |dy|) to the target */
    uint16_t g;                   /* +0x04 the cost from the start: 2 a straight step, 3 a diagonal one */
    int16_t  tries;               /* +0x06 -3 the root, 0 a child; a node is spent at 5 (8 and 5 directions) */
    uint16_t x, y;                /* +0x08 */
    const int32_t * turn;         /* +0x0C the next entry of g_PathSearchTurnRows */
    int32_t  dir;                 /* +0x10 the direction of the try, 0..7 (g_PathSearchStep8) */
    struct PathSearchNode * parent; /* +0x14 */
    struct PathSearchNode * child;  /* +0x18 one slot, reused after a backtrack */
} PathSearchNode;

typedef struct PathSearchStore {
    PathSearchNode * root;        /* +0x00 = &nodes[0] */
    PathSearchNode nodes[900];    /* +0x04 */
    int32_t  nNodes;              /* +0x6274 */
    uint16_t x0, y0, x1, y1;      /* +0x6278 the rectangle (x1 = x0 + w, y1 = y0 + h: both ends inside) */
    uint16_t w, h;                /* +0x6280 */
    int32_t  stride;              /* +0x6284 w + 6 */
    int32_t  offX, offY;          /* +0x6288 3 - x0, 3 - y0: cell (x, y) = (y + offY) * stride + offX + x */
    uint32_t cells[50000];        /* +0x6290 0 unseen, 1 blocked, else the least g written; cleared (w + 6)(h + 6) cells */
    int32_t  drawing;             /* +0x36FD0 1 under type 16 */
    uint32_t * seed;              /* +0x36FD4 the unit's seed (unit +0x20) under type 16 */
    PathSearchNode rootInit;      /* +0x36FD8 copied to nodes[0] before each pass */
    int32_t  lastBound;           /* +0x36FF4 at EBP-4 */
} PathSearchStore;
