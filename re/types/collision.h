/* Server room collision grid, the active (dungeon) room that owns it, the room tile entries it is stamped
 * from, and the unit path fields that mark it (plan 0017 Phase 1). Field names are ours.
 * Evidence: docs/findings/drlg/0005-collision.md. [I] unless noted. Coordinates are subtiles unless noted. */
#include <stdint.h>

typedef struct CollMap {          /* 0x24 header + w*h u16 cells + 2*h u16 slack; .\COLLISN\Collisn.cpp line 0x185 (0x0064C900) */
    int32_t  x0, y0;              /* +0x00, +0x04 subtile origin = DungeonRoom +0x4C/+0x50 */
    int32_t  w, h;                /* +0x08 stride (cells per row), +0x0C rows */
    int32_t  tx, ty, tw, th;      /* +0x10..+0x1C the same rectangle in tiles; +0x10/+0x14 give a tile entry's origin */
    uint16_t * cells;             /* +0x20 = &data, cell (x, y) at cells[(y - y0) * w + (x - x0)] */
    uint16_t data[1];             /* +0x24 zeroed at build */
} CollMap;

typedef struct RoomTileEntry {    /* 0x30, wall/floor/shadow entry of a DRLG room (sub_0066DC50_RoomTileAdd) */
    int32_t  screenX;             /* +0x00 */
    int32_t  screenY;             /* +0x04 */
    int32_t  x, y;                /* +0x08, +0x0C tile position relative to the owning DRLG room (may equal its w or h: the border column/row) */
    void   * pLogicBox;           /* +0x10 wall entries: the logic box of the cell (sub_0066C9C0_LogicWallBoxes) */
    uint32_t flags;               /* +0x14 sub_0066DB20_RoomTileSetFlags: 0x02 orientation 8..11 or cell bit 28 -> grid 0x10; 0x40 cell bit 17 -> grid 0x01;
                                     0x80 cell bit 16 -> grid 0x04; 0x08 hidden; 0x4000*(layer+1) layer bits (not on orientation 13) */
    void   * pTile;               /* +0x18 DT1 tile record; its +0x28 holds the 25 sub-tile bytes (TILE_GetSubtileFlags) */
    int32_t  orientation;         /* +0x1C */
    struct RoomTileEntry * pNext; /* +0x20 merge-node chain (bit-2 path) */
} RoomTileEntry;

typedef struct DungeonTileLists { /* view at DRLG RoomTile +0x14, stored in DungeonRoom +0x08 (DRLG_RoomActivate) */
    RoomTileEntry * walls;  int32_t nWalls;     /* +0x00, +0x04 (0x006196A0) */
    RoomTileEntry * floors; int32_t nFloors;    /* +0x08, +0x0C (0x00619660) */
    RoomTileEntry * shadows; int32_t nShadows;  /* +0x10, +0x14 (0x006196E0) */
} DungeonTileLists;

typedef struct DungeonRoom {      /* 0x80, the active room, DUNGEON_RoomCreate (.\DUNGEON\Dungeon.cpp) */
    struct DungeonRoom ** ppNear; /* +0x00 active rooms of the DRLG near list, self included (0x00619800) */
    uint8_t  _pad04[0x4];
    DungeonTileLists * pTiles;    /* +0x08 */
    uint8_t  _pad0C[0x4];
    void   * pDrlgRoom;           /* +0x10 DRLG room; its +0x30 points back here */
    uint8_t  _pad14[0xC];
    CollMap * pColl;              /* +0x20 (0x0061A010 get, 0x0061A040 set) */
    int32_t  nNear;               /* +0x24 */
    uint8_t  _pad28[0x4];
    void   * pAct;                /* +0x2C */
    uint8_t  _pad30[0x4];
    int32_t  roomFlags;           /* +0x34 DUNGEON_RoomCreate argument: 4 outdoor-flagged, 1 or 0 */
    uint8_t  _pad38[0x14];
    int32_t  x0, y0, w, h;        /* +0x4C subtile rectangle (sub_00463740_RoomAtSubtile, sub_00619730_RoomRectGet copies 8 dwords) */
    int32_t  tx, ty, tw, th;      /* +0x5C tile rectangle */
    uint32_t seed[2];             /* +0x6C active-room seed (rng/0002) */
    uint8_t  _pad74[0x8];
    struct DungeonRoom * pNext;   /* +0x7C act room list */
} DungeonRoom;

typedef struct DynPathColl {      /* collision fields of a dynamic path (unit +0x2C), PATH_DynamicCreate 0x00649D00 */
    uint16_t xFrac; uint16_t x;   /* +0x00, +0x02 x = subtile */
    uint16_t yFrac; uint16_t y;   /* +0x04, +0x06 */
    uint8_t  _pad08[0x14];
    DungeonRoom * pRoom;          /* +0x1C */
    uint8_t  _pad20[0x10];
    void   * pUnit;               /* +0x30 */
    uint32_t pathFlags;           /* +0x34 */
    uint8_t  _pad38[0xC];
    int32_t  size;                /* +0x44 UNIT_GetSizeX at creation (scheme A size, used when the unit is a missile) */
    int32_t  pattern;             /* +0x48 0..5 footprint pattern (PATH_PatternFromSize) */
    uint32_t markMask;            /* +0x4C bits OR-ed into the grid: player 0x80, monster 0x100, missile 0, dead 0x8000 */
    uint32_t testMask;            /* +0x50 bits that block a move: player 0x1C09, monster PATH_MonTestMask, missile 0 */
    uint16_t lastHit;             /* +0x54 */
} DynPathColl;
