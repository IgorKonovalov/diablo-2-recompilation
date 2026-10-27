/* Animation: the animdata record, the sequence tables, the monster mode records and the unit event record
 * (plan 0050 Phase 1, batch P1.1). Field names are ours. Evidence: docs/findings/anim/0001-modes-frames.md.
 * [I] unless noted. The unit's own animation fields (+0x30 .. +0x50) are in re/types/game.h (struct Unit). */
#include <stdint.h>

/* One animdata.d2 record, 160 bytes. The file is 256 blocks { uint32 count; AnimDataRec rec[count]; }, block b
 * holding the names whose uppercase byte sum & 0xFF is b (ANIMDATA_Load 0x0066A770, ANIMDATA_Find 0x0066A8F0). */
typedef struct AnimDataRec {
    char     cofName[8];          /* +0x00 token + mode token + weapon class, compared as two dwords after uppercasing */
    uint32_t framesPerDir;        /* +0x08 -> Unit.animLength = framesPerDir << 8 */
    uint32_t speed;               /* +0x0C the base rate the rate function scales (P1.2) */
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
    uint16_t flags;               /* +0x02 bit 0 running, bit 2 every frame, bit 3 (every-frame list only) free after running; a slot event is always freed */
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
    void    (*pfnCallback)(void); /* +0x2C 0: the unit type's dispatch */
} UnitEvent;
