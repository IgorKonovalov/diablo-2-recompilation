/* Room lifecycle: the fields of the active (dungeon) room, the DRLG room and the DRLG act that activation and
 * release touch, and the inactive-unit records a released room leaves behind (plan 0040 Phase 1).
 * Views over structs declared elsewhere (DungeonRoom in collision.h, DrlgRoomMaze in maze.h) carry only the
 * fields cited here. Field names are ours. Evidence: docs/findings/drlg/0009-room-lifecycle.md. [I] unless noted. */
#include <stdint.h>

typedef struct DungeonRoomLife {  /* view of DungeonRoom (0x80, DUNGEON_RoomCreate) */
    void   ** ppNear;             /* +0x00 active rooms of the near list, self included */
    uint8_t  _pad04[0x8];
    uint32_t idleCount;           /* +0x0C passes of sub_0052D240_RoomsDeactivate with no client (sub_0061A790_RoomIdleCount) */
    void   * pDrlgRoom;           /* +0x10 DRLG room */
    uint8_t  deadIdx;             /* +0x14 next slot of +0x38, (i + 1) & 3 (sub_0061AFA0_RoomRecordDeath; ai/0002 § 4) */
    uint8_t  _pad15[0x3];
    void   * pRemovals;           /* +0x18 removal notes {type, guid, next} (sub_0061A270_RoomUnitOp), sent by the client
                                     room sync, freed by sub_0053A820_ActsRoomRemovalsClear (frame/0001 § 3.4) */
    void   * pUpdated;            /* +0x1C units marked updated this frame, newest first, next = unit+0xE0, bit 0x2000 of
                                     unit+0xC4 (sub_0064C040_UnitMarkUpdated; frame/0001 § 3.3) */
    uint8_t  _pad20[0x4];
    int32_t  nNear;               /* +0x24 */
    uint8_t  _pad28[0x4];
    void   * pAct;                /* +0x2C DUNGEON act */
    uint8_t  _pad30[0x4];
    uint32_t flags;               /* +0x34 bit 0 populated, bit 1 inactive units restored, 4 client copy */
    uint32_t deadGuid[4];         /* +0x38 guids of the last four monsters whose death event ran here (sub_005A6FF0_MonDeathEvent
                                     -> sub_0061AFA0_RoomRecordDeath); row 6 Fallen scans them (ai/0002 § 2.5) */
    void   ** ppClients;          /* +0x48 clients whose room's near list holds this room, sorted by pointer */
    uint8_t  _pad4C[0x20];
    uint32_t seed[2];             /* +0x6C active-room seed */
    void   * pUnits;              /* +0x74 unit list, newest first, next = unit+0xE8 */
    uint32_t nClients;            /* +0x78 entries of +0x48 */
    struct DungeonRoomLife * pNext; /* +0x7C act room list, newest first */
} DungeonRoomLife;

typedef struct DrlgRoomLife {     /* view of the DRLG room (0xEC, DRLG_RoomCreate) */
    uint8_t  _pad00[0x8];
    void   ** ppNear;             /* +0x08 near list (sub_0066C370_RoomNeighboursEnsure) */
    uint16_t refs[4];             /* +0x0C references at near-list distance 0..3 (sub_0061B490_DrlgRefAdd) */
    uint8_t  _pad14[0x8];
    struct DrlgRoomLife * pRingPrev; /* +0x1C status ring links (sub_0061B210_DrlgStatusSet) */
    uint8_t  _pad20[0x8];
    uint32_t flags;               /* +0x28 0x100000 built, 0x200000 tiles freed with the active room, 0x400000 pinned (portal) */
    int32_t  nNear;               /* +0x2C */
    void   * pActive;             /* +0x30 active room, 0 while released */
    uint8_t  _pad34[0x10];
    uint8_t  status;              /* +0x44 lowest distance with a reference, 4 = none */
    uint8_t  _pad45[0x13];
    void   * pLevel;              /* +0x58 */
    uint8_t  _pad5C[0x4];
    uint32_t populated;           /* +0x60 the active room's flags bit 0, kept across a release */
    uint8_t  _pad64[0x84];
    struct DrlgRoomLife * pRingNext; /* +0xE8 */
} DrlgRoomLife;

typedef struct InactiveRoomRec {  /* 0x18, .\UNIT\SUnitInactive.cpp; one per released room, in the act list at game +0xD8 + 4*act */
    int32_t  x, y;                /* +0x00 room subtile origin (the key) */
    void   * pItems;              /* +0x08 InactiveItemRec list */
    struct InactiveMonRec * pMonsters; /* +0x0C */
    struct InactiveUnitRec * pUnits;   /* +0x10 objects, warps, kept players */
    struct InactiveRoomRec * pNext;    /* +0x14 list ordered by x descending */
} InactiveRoomRec;

typedef struct InactiveUnitRec {  /* 0x34, objects (type 2), type-5 units, kept player corpses (type 0) */
    int32_t  x, y;                /* +0x00 */
    int32_t  type, classId;       /* +0x08 */
    int32_t  mode;                /* +0x10 objects: mode 1 saved as 2 when Objects +0x109 = 0 and +0x141 != 0 */
    int32_t  frame;               /* +0x14 game frame at the save */
    uint32_t flagsC4, flagsC8;    /* +0x18 unit +0xC4, +0x1C unit +0xC8 (0x100: unit kept alive) */
    int32_t  aux20;               /* +0x20 unit id (types 0, objects 59/60/100) or shrine timer high half */
    int32_t  aux24;               /* +0x24 sparkle byte or shrine timer low half */
    uint8_t  interact;            /* +0x28 object interact byte */
    uint8_t  _pad29[0x3];
    int32_t  unitB8;              /* +0x2C unit +0xB8 */
    struct InactiveUnitRec * pNext; /* +0x30 */
} InactiveUnitRec;

typedef struct InactiveMonRec {   /* 0x5C, sub_005421A0_InactiveMonsterSave */
    int32_t  x, y;                /* +0x00 */
    int32_t  classId;             /* +0x08 */
    int32_t  unitId;              /* +0x0C reused at the restore */
    uint32_t flagsC4, flagsC8;    /* +0x10, +0x14 (0x100 in +0x14: unit kept alive) */
    uint32_t recFlags;            /* +0x18 0x1 SpecialMonPlace, 0x2 champion, 0x4 dying or dead, 0x8/0x10 group-link flags,
                                     0x20 minion, 0x40 monster data +0x5C bit 1, 0x80/0x100/0x200 alignment 1/2/0,
                                     0x400 in a target list (unit +0xD0 != 11), 0x800 superunique */
    int32_t  leaderId;            /* +0x1C group leader id (AI control +0x2C when +0x30 = 1), else -1 */
    int32_t  ai34;                /* +0x20 AI control +0x34 */
    void   * pPath;               /* +0x24 preset path moved out of the monster's AI control +0x38 */
    int32_t  aiState;             /* +0x28 first dword of the AI record */
    int32_t  mon58;               /* +0x2C monster data +0x58 */
    uint16_t nameSeed;            /* +0x30 */
    uint8_t  mods[9];             /* +0x32 */
    uint8_t  _pad3B;
    uint16_t superUniqueId;       /* +0x3C */
    uint8_t  _pad3E[0x2];
    int32_t  stat13;              /* +0x40 */
    int32_t  maxHp;               /* +0x44 written back as stat 7 */
    int32_t  hp;                  /* +0x48 stat 6 at the save */
    int32_t  ai4C, ai50;          /* +0x4C, +0x50 AI parameters (sub_00541FE0_InactiveMonAiSave) */
    int32_t  frame;               /* +0x54 game frame at the save */
    struct InactiveMonRec * pNext; /* +0x58 */
} InactiveMonRec;

typedef struct InactiveItemRec {  /* 0x0F + n bytes, sub_00541B10_InactiveItemSave */
    struct InactiveItemRec * pNext; /* +0x00 */
    int32_t  expiry;              /* +0x04 frame after which the item is dropped, 0 = never */
    int32_t  rec08;               /* +0x08 0x00629F20(item) */
    uint16_t nBytes;              /* +0x0C */
    uint8_t  bytes[1];            /* +0x0E ITEMS_Serialize(item, .., 0x400, 1, 1, 0), socketed children included */
} InactiveItemRec;

typedef struct DungeonActFrame {  /* view of the DUNGEON act (Game+0xBC + 4*act, DungeonRoomLife+0x2C): the fields the
                                     server frame touches (frame/0001 §§ 3.1, 3.3, 3.4) */
    uint32_t updatedDirty;        /* +0x00 set by sub_00619F90_RoomUpdatedList with EDX != 0; walked and cleared by
                                     sub_0053B000_ActUnitsFrameReset */
    struct ActClock * pClock;     /* +0x04 the act light clock (sub_0061AA60_ActClockPtr) */
    uint8_t  _pad08[0x50];
    uint32_t removalsDirty;       /* +0x58 set by sub_0061A270_RoomUnitOp, cleared by sub_0053A820_ActsRoomRemovalsClear */
} DungeonActFrame;

typedef struct ActClock {         /* the act's light clock, stepped once a frame by sub_0061C040_ActClockTick */
    int32_t  period;              /* +0x00 0..5, row of g_ActClockTable0/1/2 */
    int32_t  value;               /* +0x04 the row's second dword */
    int32_t  counter;             /* +0x08 +1 a frame (act index 3: +16; act index 2 in a type-2 row: +10; other type-2: +2) */
    uint8_t  _pad0C[0xC];
    uint8_t  colour[3];           /* +0x18..+0x1A written by 0x0061BCE0 */
    uint8_t  _pad1B[0xD];
    int32_t  scale;               /* +0x28 k: the period starts are start * k, the wrap k * 360 */
    uint8_t  _pad2C[0x4];
    int32_t  tableFlag;           /* +0x30 0: g_ActClockTable0; else g_ActClockTable2 (act index 3 compares against Table1) */
    int32_t  lastBucket;          /* +0x34 counter / scale at the last reported change */
} ActClock;
