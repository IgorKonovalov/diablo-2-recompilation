/* DRLG outdoor levels: the outdoor record, its grids, the level outline and the border-adjacency nodes
 * (plan 0026 Phase 1). Field names are ours. Evidence: docs/findings/drlg/0008-outdoor.md.
 * [I] unless noted; only the fields the outdoor generators touch are listed. Uses DrlgRect from maze.h. */
#include <stdint.h>

typedef struct DrlgGrid {         /* 0x14, sub_0067CB80_GridAlloc (.\DRLG\DrlgGrid.cpp) */
    uint32_t * pCells;            /* +0x00 cells, row-major */
    int32_t  * pRowOffs;          /* +0x04 per-row offsets (y * w) */
    int32_t  w;                   /* +0x08 */
    int32_t  h;                   /* +0x0C */
    int32_t  isView;              /* +0x10 1 when the cells are not owned */
} DrlgGrid;

/* Cell grid bits (OutdoorData.cells): 0x1 border/seam, 0x2 typed (cliff) seam or border, 0x80 road,
 * 0x100 covered (no room), 0x200 preset footprint, 0x400 seam opening, 0x800 waypoint, 0x1000 shrine,
 * 0xF0000 preset file index (bits 16-19). Occupied mask for placement: 0x1B81.
 * grid0 bits (OutdoorData.grid0 -> out room +0x28): 0x10<<k warp slot k, 0x1000<<r shrine record r,
 * 0x10000 / 0x20000 waypoint record 0 / 1. */

typedef struct OutdoorVertex {    /* 0x14, sub_0067CDD0_VertexAlloc (.\DRLG\DrlgVer.cpp line 0x13) */
    int32_t  x;                   /* +0x00 tiles while built, cells after sub_00675080_OutVertsToCells */
    int32_t  y;                   /* +0x04 */
    uint8_t  type;                /* +0x08 0; 1 = cliff run (sub_00680070_A1CliffMark) */
    uint8_t  _pad09[3];
    uint32_t flags;               /* +0x0C bit 0: segment to next is a seam with a walkable neighbour; bit 1: that neighbour is a preset level */
    struct OutdoorVertex * pNext; /* +0x10 ring: v0 bottom-left, v1 top-left, v2 top-right, v3 bottom-right */
} OutdoorVertex;

typedef struct LevelAdjNode {     /* 0x18, sub_0066B790_LevelAdjAdd, list OutdoorData+0x264 */
    void   * pNeighbour;          /* +0x00 the neighbour level */
    int32_t  side;                /* +0x04 0 W, 1 N, 2 E, 3 S (sub_00642240_RectAdjDir) */
    int32_t  isPreset;            /* +0x08 neighbour DrlgType == 2 */
    int32_t  unk0C;               /* +0x0C 0 at creation; non-zero would suppress the seam warp flag (no writer found) */
    DrlgRect * pRect;             /* +0x10 &neighbour->rect (level +0x1C) */
    struct LevelAdjNode * pNext;  /* +0x14 sorted by sub_0066B6A0_LevelAdjLess */
} LevelAdjNode;

typedef struct OutdoorRoadEnd {   /* 0x14, Act I road endpoint arrays at +0x80/+0xF8/+0x170/+0x1E8 (6 entries each) */
    int32_t  x, y;                /* +0x00 tiles */
    int32_t  dir;                 /* +0x08 0..3 side, 4 = hub */
    int32_t  unk0C, unk10;
} OutdoorRoadEnd;

typedef struct OutdoorData {      /* 0x268, level +0x14 of a DrlgType 3 level, sub_00675320_OutdoorLevelCreate */
    uint32_t flags;               /* +0x00 link inputs: 0x4..0x400 (Act I, sub_00677180_LinkOutdoorFlags), 0x400000/0x800000 (Act IV);
                                     set by Act I: 0x20 cliff run, 0x40 cave placed */
    DrlgGrid defs;                /* +0x04 preset Def at its anchor cell */
    DrlgGrid grid0;               /* +0x18 out room +0x28 flags, embedded preset flags */
    DrlgGrid cells;               /* +0x2C cell bits (above) */
    DrlgGrid grid3;               /* +0x40 passed to OutRoomCreate, not written by the generators */
    void   * sizeCells;           /* +0x54 a grid header used only for its size: 0 */
    void   * sizeRows;            /* +0x58 0 */
    int32_t  cw;                  /* +0x5C cells across, L.w / 8 */
    int32_t  ch;                  /* +0x60 cells down, L.h / 8 */
    OutdoorVertex * pRing;        /* +0x64 the level outline */
    OutdoorVertex * pRoads[6];    /* +0x68 Act I road polylines */
    OutdoorRoadEnd ends[4][6];    /* +0x80, +0xF8, +0x170, +0x1E8 */
    int32_t  nEnds;               /* +0x260 */
    LevelAdjNode * pAdj;          /* +0x264 border-adjacency list */
} OutdoorData;
