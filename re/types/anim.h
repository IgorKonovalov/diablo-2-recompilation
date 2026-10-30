/* Animation: the animdata record, the sequence tables, the monster mode records and the unit event record
 * (plan 0050 Phase 1, batch P1.1). Field names are ours. Evidence: docs/findings/anim/0001-modes-frames.md.
 * [I] unless noted. The unit's own animation fields (+0x30 .. +0x50) are in re/types/game.h (struct Unit). */
#include <stdint.h>

/* One animdata.d2 record, 160 bytes. The file is 256 blocks { uint32 count; AnimDataRec rec[count]; }, block b
 * holding the names whose uppercase byte sum & 0xFF is b (ANIMDATA_Load 0x0066A770, ANIMDATA_Find 0x0066A8F0). */
typedef struct AnimDataRec {
    char     cofName[8];          /* +0x00 token + mode token + weapon class, compared as two dwords after uppercasing */
    uint32_t framesPerDir;        /* +0x08 -> Unit.animLength = framesPerDir << 8 */
    uint32_t speed;               /* +0x0C the base rate UNIT_AnimSetRate scales (anim/0002 § 3) */
    uint8_t  events[0x90];        /* +0x10 event byte per frame; 1..4 are acted on, frames >= 0x90 are never read */
} AnimDataRec;

/* The animdata table object (ANIMDATA_Load): +0x000 the file buffer, +0x004 256 block pointers, +0x404 the fallback
 * record (name 0, framesPerDir 0x800, speed 0x100, no events) that ANIMDATA_Lookup returns when a name is absent. */
typedef struct AnimDataTable {
    void    * pFile;              /* +0x000 */
    uint32_t * pBlock[256];       /* +0x004 */
    AnimDataRec fallback;         /* +0x404 */
} AnimDataTable;                  /* 0x4A4 bytes, zeroed at load */

/* One sequence frame, 6 bytes: monseq.bin records (MonsterTbls loader 0x00659C60) and the player tables in the image
 * (0x007483B8). */
typedef struct SeqFrame {
    uint16_t sequence;            /* +0x0 monseq: the sequence index; player tables: 0 */
    uint8_t  mode;                /* +0x2 the mode the frame shows (MonMode / PlrMode row) -> Unit.seqMode */
    uint8_t  frame;               /* +0x3 the animation frame -> Unit.animFrame = frame << 8 */
    uint8_t  dir;                 /* +0x4 read into a local by UNIT_SeqReadFrame, not stored */
    uint8_t  event;               /* +0x5 event byte -> Unit.animEvent */
} SeqFrame;

/* A sequence: 12 bytes. Monsters: the index built at load (0x0096C7B4, one per sequence index, count 0x0096C7B8);
 * players: 14 per seqnum in the image, one per weapon-class column (0x007483B8[seqnum] + 12 col). */
typedef struct SeqIndex {
    SeqFrame * pFrames;           /* +0x0 first frame; Unit.pSeqFrames */
    int32_t  length;              /* +0x4 frames -> Unit.seqLength = length << 8 */
    int32_t  frames;              /* +0x8 frames -> Unit.animLength = frames << 8 (equal to length in every entry) */
} SeqIndex;

/* The monster mode record, 16 bytes (0x006E2260: 16 by mode, then 5 class-override rows). */
typedef struct MonModeRec {
    int (*pfnStart)(void);        /* +0x0 ECX game, EDX the mode command; 0 refuses the mode */
    int (*pfnFrame)(void);        /* +0x4 unit event 0 (ECX game, EDX unit); its return is not read (anim/0001 § 6) */
    void (*pfnEnd)(void);         /* +0x8 unit event 1 */
    uint32_t schedule;            /* +0xC 0: MonSetMode queues no mode event; else every-frame or scheduled */
} MonModeRec;

/* Per monster mode (0x006E23D0, 12 bytes): does the mode run every frame (sub_005A6B10_MonModeEveryFrame)? */
typedef struct MonModePerFrame {
    uint32_t always;              /* +0x0 every frame */
    uint32_t never;               /* +0x4 scheduled */
    uint32_t byMoveBit;           /* +0x8 every frame when MonStats2 +0x104 bit[mode] (the `*mv` columns) is set */
} MonModePerFrame;

/* A queued unit event (sub_005417D0_UnitQueueEvent -> 0x005416B0; items/0010 § 9). Fields the animation reads. */
typedef struct UnitEvent {
    uint8_t  kind;                /* +0x00 0 mode frame, 1 mode end, 2 monster AI, ... (< 15) */
    uint8_t  _pad01;
    uint16_t flags;               /* +0x02 bit 0 running, bit 1 on the free list (set to exactly 2 by 0x00540CD0), bit 2 every frame, bit 3 free asked while running (the runner frees it after the run; a slot event is always freed) (frame/0002 § 2) */
    int32_t  frame;               /* +0x04 game frame it runs at; -1 every frame; never <= the current frame */
    struct Unit * pUnit;          /* +0x08 passed in EDX to the dispatch */
    uint32_t unitGuid;            /* +0x0C the unit's guid, -1 without a unit (0x00540DF0) */
    uint32_t unitType;            /* +0x10 selects the list through 0x006E0B9C */
    int32_t  a;                   /* +0x14 kind 0: the event byte (1..4) */
    int32_t  b;                   /* +0x18 kind 0: the index of this code-1/2/4 event in the mode, 0 for code 3 */
    struct UnitEvent * pNext;     /* +0x1C the next one to run */
    struct UnitEvent * pPrev;     /* +0x20 */
    struct UnitEvent * pUnitNext; /* +0x24 the unit's own chain from Unit+0xDC (0x00540DF0; UNIT_CancelEvents walks it) */
    struct UnitEvent * pUnitPrev; /* +0x28 */
    void    (*pfnCallback)(void); /* +0x2C 0: the unit type's dispatch; else called (ECX game, EDX unit; kind, a, b) */
} UnitEvent;                      /* 0x30 bytes; 600 to a block (0x00540BB0) */

/* The game's event control, Game+0xB8 (0xA20 bytes, zeroed at game create, 0x00541470; freed by 0x00541400).
 * List index L from g_UnitTypeEventList (0x006E0B9C): player 0, monster 1, object 3, missile 2, item 4.
 * Evidence: docs/findings/frame/0002-unit-events-queue.md § 1-2 (run:2026-10-30-frame-emu-2). */
typedef struct EventCtl {
    int32_t  curSlot;                     /* +0x000 Game+0xA8 % 64 (signed remainder), written by GameRunUnitEvents */
    struct UnitEvent * slotHead[5][64];   /* +0x004 [L][frame % 64]: the oldest queued record of the slot */
    struct UnitEvent * slotTail[5][64];   /* +0x504 the newest; EventQueueAt appends here */
    struct UnitEvent * everyHead[5];      /* +0xA04 the every-frame list: newest first (pushed on the front) */
    struct UnitEvent * walkNext;          /* +0xA18 the runner's saved next; EventFree moves it past a freed record */
    struct EventBlock * pBlocks;          /* +0xA1C the first record block (free records go back to this one) */
} EventCtl;

typedef struct EventBlock {
    struct UnitEvent recs[600];           /* +0x0000 */
    struct UnitEvent * pFree;             /* +0x7080 free list, linked by UnitEvent +0x1C, last freed first */
    struct EventBlock * pNext;            /* +0x7084 a new block is linked second, after the first */
} EventBlock;                             /* 0x7088 */

/* The rate bonus table g_AnimRateBonus (0x006E8E24, 6 entries), read by sub_00621740_AnimRateBonus (EAX the entry):
 * B = (type == 1 && s != 0) ? k*s/(k+s) (imul, idiv) : s, s the unit's full stat. Entries 0..4: (120, 93 IAS),
 * (120, 99 FHR), (120, 105 FCR), (120, 102 FBR), (150, 96 FRW); 5: (1, 0), not used by the rate. Evidence:
 * docs/findings/anim/0002-rates.md § 2. */
typedef struct AnimRateBonus {
    int32_t  type;                /* +0x0 1: diminishing */
    int32_t  k;                   /* +0x4 */
    int32_t  stat;                /* +0x8 ItemStatCost row */
} AnimRateBonus;

/* Per mode, the branch UNIT_AnimSetRate takes (g_PlrModeRateClass 0x006E8A00, 20 modes; g_MonModeRateClass
 * 0x006E8B90, monster class < 410; g_MonXModeRateClass 0x006E8CD0, class >= 410; 16 modes each). anim/0002 § 3. */
typedef struct ModeRateClass {
    uint32_t skillMove;           /* +0x00 moving when the used skill's entry flags have bit 0 and not bit 12 */
    uint32_t move;                /* +0x04 moving */
    uint32_t skillAttack;         /* +0x08 attack when the used skill has Skills UseAttackRate (+0x006 bit 3) */
    uint32_t attack;              /* +0x0C attack */
    uint32_t fixed;               /* +0x10 the record's speed unscaled */
} ModeRateClass;

/* The movement fields of a unit's dynamic path (Unit+0x2C), as the per-frame step reads them (plan 0050 P1.3,
 * docs/findings/anim/0003-movement-gates.md §§ 2 and 4; the collision fields are re/types/collision.h DynPathColl).
 * Positions are 16.16 subtiles; points are subtile words, taken at the subtile centre ((w << 16) + 0x8000).
 * One step per game frame: sub_00554CA0_UnitMoveStep -> sub_00650840_PathStep(unit, 0x400) ->
 * sub_006502D0_PathVelocityStep: step = (dir * ((speed * 0x400) >> 6)) >> 12 per axis (imul, sar). */
#pragma pack(push, 1)                 /* dirX/dirY sit at +0x6A, unaligned */
typedef struct PathMove {
    uint32_t x;                   /* +0x00 16.16 */
    uint32_t y;                   /* +0x04 16.16 */
    uint8_t  _pad08[0x1C];
    int32_t  iPoint;              /* +0x24 index of the next point */
    int32_t  nPoints;             /* +0x28 point count (0: no path) */
    uint8_t  _pad2C[0x08];
    uint32_t flags;               /* +0x34 0x20 moving, 0x10 re-plan when blocked (monster), 0x8000 speed from +0x80,
                                     0x40000 straight (no target check) */
    int32_t  changed;             /* +0x38 15 when PathSetSpeed changed the speed */
    int32_t  type;                /* +0x3C planner index into g_PathPlanFuncs (0x006EB6D8); 8 knockback */
    uint8_t  _pad40[0x18];
    void   * pTargetUnit;         /* +0x58 */
    uint8_t  _pad5C[0x0E];
    int32_t  dirX;                /* +0x6A unit vector x 4096 (g_PathDirTable), unaligned */
    int32_t  dirY;                /* +0x6E */
    int32_t  stepX;               /* +0x72 1/65536 subtile per frame */
    int32_t  stepY;               /* +0x76 */
    uint8_t  _pad7A[0x02];
    int32_t  speed;               /* +0x7C v: v/16 subtiles per frame on an axis */
    int32_t  speedSaved;          /* +0x80 restored into +0x7C by sub_00648DC0_PathMoveReset under flag 0x8000 */
    int32_t  speedMax;            /* +0x84 */
    int32_t  accel;               /* +0x88 added every fifth step; set only for missiles */
    int32_t  accelCount;          /* +0x8C */
    uint8_t  knockDist;           /* +0x90 knockback: the point is (knockDist >> 1) + 1 subtiles away; decremented per
                                     subtile crossed for other path types than 8 and 11 */
    uint8_t  _pad91[0x02];
    uint8_t  stopRange;           /* +0x93 the target-check distance at or below which the path ends */
    uint8_t  _pad94[0x08];
    uint32_t points[1];           /* +0x9C word pairs (x, y), nPoints of them */
} PathMove;
#pragma pack(pop)
