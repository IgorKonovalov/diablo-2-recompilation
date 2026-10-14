/* Unique and set item records as loaded, and the item creation record (partial: only the fields findings cite).
 * Field names are ours. Evidence: docs/findings/items/0004-uniques-sets.md ([I] unless noted),
 * docs/findings/items/0001-tc-resolution.md §8 (creation record), docs/tables/UniqueItems.md, SetItems.md, Sets.md
 * (file layout). Fields marked "load" are written by the loader and are 0 in the .bin. */
#include <stdint.h>

typedef struct UniqueItemsRec {   /* 0x14C, g_pUniqueItems (0x0096C854) */
    uint16_t rowIndex;            /* +0x000 load: the row's own index */
    char     name[32];            /* +0x002 `index`, added to g_UniqueItemsLink in row order */
    uint16_t nameKey;             /* +0x022 load: string key of `index` (0x1507 when missing) */
    uint16_t version;             /* +0x024 `version`; >= 100 needs item version >= 100 */
    uint16_t _pad026;
    uint32_t code;                /* +0x028 `code`, compared with the base record +0x80 */
    uint8_t  flags;               /* +0x02C bit 0 enabled, bit 1 nolimit, bit 2 carry1, bit 3 ladder */
    uint8_t  _pad02D[3];
    int32_t  rarity;              /* +0x030 pick weight, raised to 1 when < 1 */
    int16_t  lvl;                 /* +0x034 must be <= the item's ilvl (signed compare) */
    uint16_t lvlReq;              /* +0x036 not read by the builder */
    uint8_t  _rest038[0x114];     /* art columns, sounds, cost, property block (tables/UniqueItems.md) */
} UniqueItemsRec;

typedef struct SetItemsRec {      /* 0x1B8, g_pSetItems (0x0096C848) */
    uint16_t rowIndex;            /* +0x000 load: the row's own index */
    char     name[32];            /* +0x002 `index`, added to g_SetItemsLink in row order */
    uint16_t setVersion;          /* +0x022 load: copied from the set's `version` (SetsRec+0x04); tested by the set builder */
    uint16_t nameKey;             /* +0x024 load: string key of `index` (0x1507 when missing) */
    uint16_t _pad026;
    uint32_t code;                /* +0x028 `item` */
    int16_t  set;                 /* +0x02C `set`, row of sets; set 29 needs a hellbovine source */
    uint16_t memberSlot;          /* +0x02E load: position in SetsRec.members */
    int16_t  lvl;                 /* +0x030 must be <= the item's ilvl (signed compare) */
    uint16_t lvlReq;              /* +0x032 */
    int32_t  rarity;              /* +0x034 pick weight, 0 raised to 1 */
    uint8_t  _rest038[0x4F];      /* cost, art, sounds */
    uint8_t  addFunc;             /* +0x087 `add func`, read by the set property code */
    uint8_t  _props088[0x130];    /* property block (items/properties) */
} SetItemsRec;

typedef struct SetsRec {          /* 0x128, g_pSets (0x0096C83C) */
    uint16_t rowIndex;            /* +0x000 `index` stored as the row index */
    uint16_t nameKey;             /* +0x002 `name` string key */
    uint32_t version;             /* +0x004 `version`, copied into each member's SetItemsRec.setVersion */
    uint32_t _unk008;             /* +0x008 0 in the file; no writer or reader found */
    int32_t  nMembers;            /* +0x00C load: member count, at most 6 ([C] writer/reader agreement) */
    uint8_t  bonuses[0x100];      /* +0x010 partial (8) and full (8) bonus quads, items/properties */
    struct SetItemsRec * members[6]; /* +0x110 load: member records in setitems row order ([C]) */
} SetsRec;

typedef struct ItemCreateRec {    /* 0x84, built zeroed by sub_0055A550_DropCreateItem (items/0001 §8) */
    void    * pSource;            /* +0x00 source unit */
    uint8_t  _pad04[0x4];
    void    * pGame;              /* +0x08 */
    int32_t  ilvl;                /* +0x0C */
    uint8_t  _pad10[0x4];
    int32_t  itemIndex;           /* +0x14 item record */
    uint8_t  _pad18[0x14];
    int32_t  restore;             /* +0x2C non-zero: seeds from +0x48/+0x4C, unique row taken from +0x40 as is; 0 for drops */
    int32_t  quality;             /* +0x30 requested quality; the fallback steps overwrite it */
    uint8_t  _pad34[0xC];
    int32_t  rowPlus1;            /* +0x40 unique or set row + 1 (0 none) from a TC entry; the row itself when restore */
    uint32_t flags44;             /* +0x44 bit 0x400000 forces ethereal */
    uint32_t unitSeed;            /* +0x48 used when restore */
    uint32_t itemSeed;            /* +0x4C used when restore */
    uint8_t  _pad50[0x18];
    int32_t  forcedPrefix[3];     /* +0x68 affix ids relative to the prefix block (row + 1); [0] read by the magic builder, [i] by the rare builder's i-th prefix pick; < 0 in [0] = no prefix (magic); 0 on drops (items/0005) */
    int32_t  forcedSuffix[3];     /* +0x74 same for suffixes */
    uint32_t flags;               /* +0x80 0x01 hellbovine source, 0x02 no ethereal roll, 0x04 force ethereal, 0x08 no socket roll, 0x10 sockets always, 0x20 staff-mod bonus = ilvl (items/0005 §9); 0x04/0x10 are the resolver's upgrade bits (items/0001 §8) */
} ItemCreateRec;
