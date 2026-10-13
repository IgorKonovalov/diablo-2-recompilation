/* DRLG preset instances and preset units (plan 0016 Phase 1). Field names are ours.
 * Evidence: docs/findings/drlg/0004-preset-units.md. [I] unless noted. */
#include <stdint.h>

typedef struct PresetPath {       /* 0x08, copied by sub_006660B0_PresetPathCopy */
    uint32_t nPoints;             /* +0x00 */
    int32_t  (*points)[3];        /* +0x04 12-byte points: action, x, y (DS1_Parse; x/y offset by the copy) */
} PresetPath;

typedef struct PresetUnit {       /* 0x20, sub_0066BF30_PresetUnitCreate / sub_00667510_PresetUnitCopy */
    int32_t  mode;                /* +0x00 0 object, 1 monster, 3 item */
    int32_t  id;                  /* +0x04 monster: MonStats | nMonStats+SU row | nMonStats+nSU+MonPlace row; object row */
    int32_t  x;                   /* +0x08 subtiles: in the DS1, + instance origin x5 in the instance list, room-relative in the room list */
    struct PresetUnit * pNext;    /* +0x0C */
    PresetPath * pPath;           /* +0x10 */
    int32_t  type;                /* +0x14 1 monster, 2 object, 4 item */
    int32_t  y;                   /* +0x18 subtiles, as x */
    uint32_t flags;               /* +0x1C bit 0: the server's sub_005559A0_RoomPresetUnits skips the unit */
} PresetUnit;

typedef struct PresetInstance {   /* 0x58, sub_00666ED0_PresetInstanceCreate (.\DRLG\Preset.cpp) */
    int32_t  def;                 /* +0x00 LvlPrest Def */
    int32_t  fileIndex;           /* +0x04 File(idx+1) */
    void   * pRecord;             /* +0x08 LvlPrest record (0x1B0) */
    void   * pDs1;                /* +0x0C cached DS1, set by DS1_LoadCached; 0 until the first load (rolls run then) */
    int32_t  x, y;                /* +0x10, +0x14 origin, tiles */
    int32_t  w, h;                /* +0x18, +0x1C size, tiles (SizeX/SizeY when both non-zero) */
    int32_t  unk20;               /* +0x20 non-zero: PresetRoomsCreate reads a second grid cell per room */
    uint8_t  _pad24[0x14];
    PresetUnit * pUnits;          /* +0x38 kept units (sub_00667620_PresetUnitDropRolls), drained by sub_00666710_PresetUnitsToRoom */
    int32_t  pending;             /* +0x3C 1 at create; cleared by PresetRoomLoadDs1 after the centre monster / client objects */
    int32_t  nPops;               /* +0x40 */
    int32_t * popIndex;           /* +0x44 style/4 - 1 */
    int32_t * popMain;            /* +0x48 main index */
    uint32_t * popTimer;          /* +0x4C client tick deadline */
    int32_t  (*popRect)[4];       /* +0x50 x, y, w, h tiles */
    struct PresetInstance * pNext;/* +0x54 level +0x1B0 list */
} PresetInstance;
