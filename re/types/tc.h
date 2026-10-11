/* Runtime treasure class, built at load by TC_LoadTreasureClassEx / TC_BuildAutoTCs.
 * Evidence: docs/findings/items/0001-tc-resolution.md §1 ([C] layout by writer/reader agreement). */
#include <stdint.h>

#define TCE_UNIQUE   0x01   /* entry is a uniqueitems reference, aux = record index */
#define TCE_SET      0x02   /* entry is a setitems reference, aux = record index */
#define TCE_TC       0x04   /* entry is a sub-TC, index = TC index */
#define TCE_EXPONLY  0x10   /* excluded from totalClassic */

typedef struct TCEntry {          /* 0x1C */
    int32_t  cumClassic;          /* +0x00 totalClassic before this entry */
    int32_t  cumExp;              /* +0x04 totalExp before this entry */
    uint16_t index;               /* +0x08 item record or TC index; 0xFFFF = none */
    uint16_t aux;                 /* +0x0A unique/set index, or mul=/ma=/mg= */
    uint8_t  flags;               /* +0x0C TCE_* */
    uint8_t  _pad0D;
    uint16_t mod[6];              /* +0x0E cm, cr, cs, cu, ce, cg */
} TCEntry;

typedef struct TreasureClass {    /* 0x2C, g_pTreasureClasses[] */
    int16_t  group;               /* +0x00 group + nAutoTypes, or 0 */
    uint16_t level;               /* +0x02 */
    int32_t  nEntries;            /* +0x04 */
    int32_t  totalClassic;        /* +0x08 */
    int32_t  totalExp;            /* +0x0C */
    int32_t  picks;               /* +0x10 0 stored as 1 */
    int32_t  noDrop;              /* +0x14 */
    uint16_t _unk18;              /* +0x18 */
    uint16_t ratio[6];            /* +0x1A Magic, Rare, Set, Unique, record +0x30, record +0x32 */
    uint16_t _pad26;
    TCEntry *entries;             /* +0x28 */
} TreasureClass;
