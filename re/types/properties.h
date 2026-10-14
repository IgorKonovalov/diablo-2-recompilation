/* Property records, the property block of the item tables, and the item-record fields the base-stat and property
 * code reads (partial: only the fields findings cite). Field names are ours.
 * Evidence: docs/findings/items/0006-properties.md ([I] unless noted); file layouts docs/tables/Properties.md,
 * Weapons.md, Armor.md, Misc.md. */
#include <stdint.h>

typedef struct PropertiesRec {    /* 0x2E, DataTables+0xA4 (g_pProperties 0x0096BCD4), count DataTables+0xAC */
    uint16_t code;                /* +0x000 the row's own index; `code` is registered lower-cased in g_PropertiesLink */
    uint8_t  set[7];              /* +0x002 set1..7: non-zero = the slot's stat is set (STATLIST_SetStat), else added */
    uint8_t  _pad009;
    int16_t  val[7];              /* +0x00A val1..7: passed to the handler (param of func 21, value of func 36) */
    uint8_t  func[7];             /* +0x018 func1..7: index into g_PropFuncTable (0x007462F8); 0 ends the slot walk */
    uint8_t  _pad01F;
    uint16_t stat[7];             /* +0x020 stat1..7: ItemStatCost row, 0xFFFF blank */
} PropertiesRec;

typedef struct PropBlock {        /* 0x10, one (code, par, min, max) block of an item table row */
    int32_t  code;                /* +0x00 properties row; -1 = blank or a code that names no row */
    int32_t  par;                 /* +0x04 */
    int32_t  min;                 /* +0x08 */
    int32_t  max;                 /* +0x0C */
} PropBlock;
/* Where the blocks are: UniqueItemsRec +0x08C (12 blocks, mode 3); SetItemsRec +0x088 (prop1..9, mode 4) and +0x118
 * (aprop1a, aprop1b, ..., aprop5b, mode 4); MagicAffixRec +0x024 (3 blocks, mode 0); QualityItems record +0x00C
 * (2 blocks, mode 1); a 3x3 group at +0x030/+0x060/+0x090 (modes 2 and 5, sub_0065C6D0_PropBlock3x3). */

typedef struct ItemsRecStats {    /* view of the 0x1A8-byte weapons/armor/misc record (g_pItems) */
    uint8_t  _pad000[0x80];
    uint32_t code;                /* +0x080 */
    uint8_t  _pad084[0x48];
    int32_t  minac;               /* +0x0CC defense draw low end (armor) */
    int32_t  maxac;               /* +0x0D0 defense draw high end; ac% resets defense to maxac + 1 */
    uint32_t gambleCost;          /* +0x0D4 */
    int32_t  speed;               /* +0x0D8 negated into stat 67 (armor) or 68 (weapons) */
    uint8_t  _pad0DC[0x8];
    int32_t  minstack;            /* +0x0E4 */
    int32_t  maxstack;            /* +0x0E8 (+ stat 254, capped at 511, by ITEMS_GetMaxStack) */
    int32_t  spawnstack;          /* +0x0EC misc only */
    uint8_t  _pad0F0[0x8];
    uint16_t autoPrefix;          /* +0x0F8 automagic group (items/0005) */
    uint8_t  _pad0FA[0x4];
    uint8_t  mindam;              /* +0x0FE stat 21 */
    uint8_t  maxdam;              /* +0x0FF stat 22 */
    uint8_t  minmisdam;           /* +0x100 stat 159 */
    uint8_t  maxmisdam;           /* +0x101 stat 160; non-zero enables both throw stats in ItemInitStats */
    uint8_t  twoHandMindam;       /* +0x102 stat 23 */
    uint8_t  twoHandMaxdam;       /* +0x103 stat 24 */
    uint8_t  _pad104[0xB];
    uint8_t  invwidth;            /* +0x10F socket cap invwidth * invheight (max 6) */
    uint8_t  invheight;           /* +0x110 */
    uint8_t  block;               /* +0x111 stat 20 (armor) */
    uint8_t  durability;          /* +0x112 stat 73; current durability drawn in [d/2, d/2 + d/2 - 1] */
    uint8_t  nodurability;        /* +0x113 tested by sub_00629930_ItemHasDurability, not by the durability draw */
    uint8_t  _pad114[0x1E];
    uint8_t  stackable;           /* +0x132 */
    uint8_t  _pad133[0x4];
    uint8_t  hasinv;              /* +0x137 the socket roll needs it */
    uint8_t  gemsockets;          /* +0x138 cap of sub_0062BC20_ItemMaxSockets */
    uint8_t  _pad139[0x6F];
} ItemsRecStats;
