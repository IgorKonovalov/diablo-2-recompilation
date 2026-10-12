/* Server game and unit objects (partial: only the fields findings cite). Field names are ours.
 * Evidence: docs/findings/items/0001-tc-resolution.md, docs/findings/rng/0002-seed-tree.md,
 * docs/findings/monsters/0001-level-pool.md. [I] unless noted. */
#include <stdint.h>

typedef struct Game { /* server game object, passed in ECX */
    uint8_t  _pad0000[0x6A];
    uint8_t  gameType;            /* +0x06A game type; /players applies for 1..3 (items/0001 §6) */
    uint8_t  _pad006B[0x2];
    uint8_t  difficulty;          /* +0x06D 0..2 ([C], items/0001 summary) */
    uint8_t  _pad006E[0x2];
    uint32_t expansion;           /* +0x070 non-zero in an expansion game ([C], items/0001 summary) */
    uint8_t  _pad0074[0x4];
    uint16_t unk78;               /* +0x078 copied into the item creation record +0x2A (items/0001 §8); width as copied */
    uint8_t  _pad007A[0x56];
    uint32_t seed[2];             /* +0x0D0 game seed (rng/0002) */
    uint8_t  _pad00D8[0x14];
    uint32_t monRegionSeedLow;    /* +0x0EC low word of the game seed's draw that seeds the monster regions ([C], monsters/0001) */
    struct MonRegion * pMonRegions[137]; /* +0x0F0 one per level id, [0] unused, filled at game creation (monsters/0001, re/types/monregion.h); length = the levels count, 137 stock */
    uint8_t  _pad0314[0xE0C];
    void    * playerLists[128];   /* +0x1120 player unit hash lists, next = unit+0xE4 (items/0001 §6) */
    uint8_t  _pad1320[0xA0C];
    void    * pParties;           /* +0x1D2C party list (items/0001 §6) */
} Game;

typedef struct Unit { /* any unit; type-specific data at +0x14 */
    uint32_t type;                /* +0x000 0 player, 1 monster, 4 item (items/0001) */
    uint32_t classId;             /* +0x004 record index in the type's table (items/0001) */
    uint8_t  _pad0008[0xC];
    void    * pTypeData;          /* +0x014 monster data: +0x16 u16 type flags (0x02 superunique, 0x04 champion, 0x08 unique), +0x26 superunique id (items/0001 §3) */
    uint8_t  _pad0018[0x8];
    uint32_t seed[2];             /* +0x020 unit seed (rng/0002, items/0001 §5) */
    uint8_t  _pad0028[0x9C];
    uint32_t flagsC4;             /* +0x0C4 bit 17 skips the death drop (items/0001 §3); byte +0xC6 bit 0 = dead flag (items/0001 §6) */
    uint8_t  _pad00C8[0x1C];
    struct Unit * pListNext;      /* +0x0E4 next in the game player hash list (items/0001 §6) */
} Unit;
