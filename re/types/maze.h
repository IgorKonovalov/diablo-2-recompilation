/* DRLG maze rooms, room adjacency, level links and the act link builder (plan 0022 Phase 1).
 * Field names are ours. Evidence: docs/findings/drlg/0006-maze.md, docs/findings/drlg/0007-warps.md.
 * [I] unless noted; only the fields the maze and link code touch are listed. */
#include <stdint.h>

typedef struct DrlgRect { int32_t x, y, w, h; } DrlgRect;  /* tiles */

typedef struct RoomAdj {          /* 0x18, sub_0066B560_RoomAdjAdd (.\DRLG\DrlgRoom.cpp line 0xD4) */
    struct DrlgRoom * pRoom;      /* +0x00 the other room */
    int32_t  dir;                 /* +0x04 0 W, 1 N, 2 E, 3 S (4..7 diagonals, sub_00671320 only) */
    int32_t  unk08;               /* +0x08 0 */
    int32_t  type;                /* +0x0C 1 = maze link (RoomFree unlinks type 1 both ways) */
    DrlgRect * pRect;             /* +0x10 &pRoom->rect */
    struct RoomAdj * pNext;       /* +0x14 prepended */
} RoomAdj;

typedef struct MazeRoomData {     /* room +0x20 of a type-2 (preset/maze) room, sub_00666630_PresetRoomAlloc */
    int32_t  def;                 /* +0x00 LvlPrest Def; 0 until sub_006709B0 or a special sets it */
    int32_t  fileIndex;           /* +0x04 forced index for MazePresetFile, -1 = none */
    void   * pInstance;           /* +0x08 PresetInstance (preset rooms only) */
    uint32_t flags;               /* +0x0C bit 1 (0x2): Def fixed ("locked"): no growth from it, no merge, no theme */
} MazeRoomData;

typedef struct DrlgRoomMaze {     /* the DRLG room (0xEC, DRLG_RoomCreate), fields used by the maze code */
    RoomAdj * pAdj;               /* +0x00 adjacency list */
    int32_t  seedLo04;            /* +0x04 */
    uint8_t  _pad08[0x0C];
    uint32_t seed[2];             /* +0x14 room seed; the maze steps it for growth directions and merges */
    uint8_t  _pad1C[0x04];
    MazeRoomData * pData;         /* +0x20 */
    struct DrlgRoomMaze * pNext;  /* +0x24 level list, newest first */
    uint32_t flags;               /* +0x28 bits 0x10<<m: holds a warp tile of slot m; 0x30000: holds a waypoint */
    uint8_t  _pad2C[0x08];
    DrlgRect rect;                /* +0x34 */
    int32_t  type;                /* +0x48 1 outdoor, 2 preset/maze */
    uint8_t  _pad4C[0x0C];
    void   * pLevel;              /* +0x58 */
} DrlgRoomMaze;

typedef struct MazeSpecial {      /* 0x10, tables 0x006EF8A8..0x006F05D8, read by sub_006724E0_MazeSpecialPlace */
    int32_t  matchDef;            /* +0x00 dead-end Def to replace (base + one exit bit) */
    int32_t  def;                 /* +0x04 special Def (Prev/Next/Down/Waypoint/quest room) */
    int32_t  fileIndex;           /* +0x08 forced index, -1 in every stock entry */
    int32_t  dir;                 /* +0x0C fallback: attach a new room in this direction */
} MazeSpecial;

typedef struct LevelLinks {       /* 0x48, act +0x90 list, sub_00642860_ActLevelLinksCopy (.\DRLG\Drlg.cpp line 0x3E0) */
    int32_t  levelId;             /* +0x00 */
    int32_t  vis[8];              /* +0x04 copy of Levels Vis0..7 (leveldefs +0x48) */
    int32_t  warp[8];             /* +0x24 copy of Levels Warp0..7 (leveldefs +0x68) */
    struct LevelLinks * pNext;    /* +0x44 */
} LevelLinks;

typedef struct LinkEntry {        /* 0x10, the act link tables 0x006F0750..0x006F0ED0, zero-terminated */
    int32_t (*pick)(void);        /* +0x00 ECX = LinkBuild*: place rect[i]; 0 = exhausted */
    int32_t  levelId;             /* +0x04 0 ends the table */
    int32_t  anchor;              /* +0x08 index of the entry it is placed against, -1 none */
    int32_t  unk0C;               /* +0x0C -1 in every stock entry */
} LinkEntry;

typedef struct LinkBuild {        /* 0x1F4 on the stack of sub_006772C0_LevelLinkBuild (memset 500) */
    uint32_t seed[2];             /* +0x000 copy of the act seed */
    DrlgRect rect[15];            /* +0x008 per entry: position from the pick, size from Levels SizeX/SizeY[diff] */
    LinkEntry * pTable;           /* +0x0F8 */
    int32_t  dir[15];             /* +0x0FC current choice per entry (the "link value" levels 1/40/6 read) */
    int32_t  dir0[15];            /* +0x138 first choice, -1 = not drawn yet */
    int32_t  step[15];            /* +0x174 second-axis choice of the two-draw picks */
    int32_t  flip0[15];           /* +0x1B0 its first value */
    int32_t  i;                   /* +0x1EC current entry */
} LinkBuild;
