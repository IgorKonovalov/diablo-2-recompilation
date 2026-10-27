/* Server game and unit objects (partial: only the fields findings cite). Field names are ours.
 * Evidence: docs/findings/items/0001-tc-resolution.md, docs/findings/rng/0002-seed-tree.md,
 * docs/findings/save/0001-d2s-io.md, docs/findings/monsters/0001-level-pool.md, docs/findings/items/0009-vendors.md,
 * docs/findings/combat/0001-formulas.md, docs/findings/anim/0001-modes-frames.md. [I] unless noted. */
#include <stdint.h>

typedef struct Game { /* server game object, passed in ECX */
    uint8_t  _pad0000[0x6A];
    uint8_t  gameType;            /* +0x06A game type; /players applies for 1..3 (items/0001 §6) */
    uint8_t  _pad006B[0x2];
    uint8_t  difficulty;          /* +0x06D 0..2 ([C], items/0001 summary) */
    uint8_t  _pad006E[0x2];
    uint32_t expansion;           /* +0x070 non-zero in an expansion game ([C], items/0001 summary) */
    uint32_t ladder;              /* +0x074 non-zero in a ladder game; ORed into the save status as bit 6 (save/0001) */
    uint16_t itemVersion;         /* +0x078 copied into the item creation record +0x2A (items/0001 §8); 101 in an expansion game, 2 in classic; saved as the item version (save/0001) */
    uint8_t  _pad007A[0x2];
    uint32_t mapSeed;             /* +0x07C map seed (rng/0002); written to and, in single player, read from save 0xAB (save/0001) */
    uint8_t  _pad0080[0x4];
    uint32_t seedOverride;        /* +0x084 1 when -seed N is applied (rng/0002); blocks the save map-seed reuse (save/0001) */
    void    * pClients;           /* +0x088 client list, next = client+0x4A8 (save/0001) */
    uint8_t  _pad008C[0x1C];
    uint32_t frame;               /* +0x0A8 server game frame; timed states expire at frame + length (combat/0001) */
    uint8_t  _pad00AC[0xC];
    void    * pEventCtl;          /* +0x0B8 unit event lists: +0x00 frame & 63; per unit-type list L (0x006E0B9C: player 0,
                                     monster 1, missile 2, object 3, item 4) the oldest-first slot heads at +0x004 + 4 (64 L + slot),
                                     the newest at +0x504 + ..., the every-frame list at +0xA04 + 4 L (anim/0001 § 6) */
    void    * pActs[5];           /* +0x0BC server acts, created on demand with mapSeed (rng/0002, save/0001) */
    uint32_t seed[2];             /* +0x0D0 game seed (rng/0002) */
    uint8_t  _pad00D8[0x14];
    uint32_t monRegionSeedLow;    /* +0x0EC low word of the game seed's draw that seeds the monster regions ([C], monsters/0001) */
    struct MonRegion * pMonRegions[137]; /* +0x0F0 one per level id, [0] unused, filled at game creation (monsters/0001, re/types/monregion.h); length = the levels count, 137 stock */
    uint8_t  _pad0314[0xE0C];
    void    * playerLists[128];   /* +0x1120 player unit hash lists, next = unit+0xE4 (items/0001 §6) */
    uint8_t  _pad1320[0x804];
    uint32_t uniqueMade[128];     /* +0x1B24 bit per uniqueitems row built in this game, cleared at game creation (items/0004 §3.3) */
    struct NpcStoreCtl * pNpcStore;/* +0x1D24 NPC store control: records and the store seed (items/0009, re/types/vendors.h) */
    uint8_t  _pad1D28[0x4];
    void    * pParties;           /* +0x1D2C party list (items/0001 §6) */
} Game;

typedef struct Unit { /* any unit; type-specific data at +0x14 */
    uint32_t type;                /* +0x000 0 player, 1 monster, 4 item (items/0001) */
    uint32_t classId;             /* +0x004 record index in the type's table (items/0001) */
    uint8_t  _pad0008[0x4];
    uint32_t guid;                /* +0x00C unit id; with type, names a unit in the hit queue and event records (combat/0001) */
    uint32_t mode;                /* +0x010 animation mode; for items the item mode saved as `location` (save/0001) */
    void    * pTypeData;          /* +0x014 monster data: +0x16 u16 type flags (0x02 superunique, 0x04 champion, 0x08 unique), +0x26 superunique id (items/0001 §3) */
    uint8_t  _pad0018[0x8];
    uint32_t seed[2];             /* +0x020 unit seed (rng/0002, items/0001 §5) */
    uint32_t initSeed;            /* +0x028 value the unit seed was initialised from (rng/0002); the saved item seed (save/0001) */
    void    * pPath;              /* +0x02C path (PathSetTargetPoint, PathSetSpeed; skills/0002, anim/0001) */
    /* Animation fields (anim/0001 § 2, re/types/anim.h). 8.8 means frames x 256. */
    void    * pSeqFrames;         /* +0x030 the sequence's 6-byte frame records (SeqFrame); 0 outside a sequence */
    int32_t  seqLength;           /* +0x034 sequence length, frames << 8 */
    int32_t  seqPos;              /* +0x038 sequence position, 8.8 */
    int32_t  seqRate;             /* +0x03C sequence step per tick, 8.8; 0x100 at the sequence start; UNIT_AnimSetRate writes
                                     it only in its cast and attack branches (anim/0002 § 3.8) */
    int32_t  seqMode;             /* +0x040 the mode byte of the current sequence frame */
    int32_t  animFrame;           /* +0x044 current frame, 8.8; in a server-scheduled mode the game frame the schedule was made at, << 8 */
    int32_t  animLength;          /* +0x048 frames << 8 (animdata FramesPerDir); objects: Objects FrameCnt[mode] unshifted;
                                     sequences: the frames still to run, << 8, counted down by seqRate */
    int16_t  animRate;            /* +0x04C frame step per tick, 8.8, clamped to [0, 0x7FFF]; UNIT_AnimSetRate (anim/0002) */
    uint8_t  animEvent;           /* +0x04E event byte (1..4) of the frames the last advance crossed, 0 if none */
    uint8_t  _pad004F;
    struct AnimDataRec * pAnimData; /* +0x050 the animdata record of the unit's token, mode and weapon class */
    uint8_t  _pad0054[0x8];
    void    * pStatList;          /* +0x05C stat list; base stats saved in the gf section (save/0001) */
    void    * pInventory;         /* +0x060 inventory (save/0001) */
    uint8_t  _pad0064[0x1C];
    struct Game * pGame;          /* +0x080 (combat/0001: sub_00554010_UnitGetGame) */
    uint8_t  _pad0084[0xC];
    void    * pEvents;            /* +0x090 stat-event list: u8 event, +0x0C/+0x10 args, +0x14 handler, +0x1C next (combat/0001) */
    uint8_t  _pad0094[0x18];
    void    * pHitQueue;          /* +0x0AC queued hits of this attacker, next = +0x84 (combat/0001) */
    uint32_t hitClass;            /* +0x0B0 last hit class received (combat/0001) */
    uint8_t  _pad00B4[0x10];
    uint32_t flagsC4;             /* +0x0C4 bit 17 skips the death drop (items/0001 §3); byte +0xC6 bit 0 = dead flag (items/0001 §6);
                                     bit 0 set by UNIT_SetMode; bit 14 (0x4000) the sequence frame's mode changed (anim/0001 § 5);
                                     bit 19 (0x80000) set by the monster mode command (anim/0001 § 10) */
    uint32_t flagsC8;             /* +0x0C8 bit 3: the unit may have a display-transform state (UNIT_AnimTransform; anim/0001 § 2) */
    uint8_t  _pad00CC[0x10];
    struct UnitEvent * pEventChain; /* +0x0DC the unit's queued events, linked by UnitEvent +0x24 (re/types/anim.h; anim/0001 § 6) */
    uint8_t  _pad00E0[0x4];
    struct Unit * pListNext;      /* +0x0E4 next in the game player hash list (items/0001 §6) */
} Unit;
