/* Magic and rare affix records as loaded, and the two merged affix arrays (partial: only the fields findings cite).
 * Field names are ours. Evidence: docs/findings/items/0005-affixes.md ([I] unless noted), docs/tables/MagicPrefix.md,
 * RarePrefix.md, AutoMagic.md (file layout). Fields marked "load" are written by the loader and are 0 in the .bin. */
#include <stdint.h>

typedef struct MagicAffixRec {    /* 0x90: magicsuffix, magicprefix and automagic records, merged in that order */
    char     name[32];            /* +0x000 `Name` */
    uint16_t nameKey;             /* +0x020 load: string key of `Name` (STRTABLE_GetByKey) */
    uint16_t version;             /* +0x022 `version`; >= 100 needs item version >= 100 */
    uint8_t  mods[0x30];          /* +0x024 three property slots {code, param, min, max}; mod1code (+0x024) read by the type test */
    uint16_t spawnable;           /* +0x054 tested as a byte when the caller asks for it */
    uint8_t  transformColor;      /* +0x056 */
    uint8_t  _pad057;
    int32_t  level;               /* +0x058 must be <= alvl (signed); also the weight factor when the base has `magic lvl` */
    int32_t  group;               /* +0x05C exclusion group; also the automagic group key */
    int32_t  maxLevel;            /* +0x060 0 = none, else must be >= alvl */
    uint8_t  rare;                /* +0x064 0 excludes the row on quality 6, 8 and 9 items */
    uint8_t  levelReq;            /* +0x065 not read by the pick */
    uint8_t  classSpecific;       /* +0x066 0xFF none; else must equal the item's type class unless that is 7 */
    uint8_t  classLevelClass;     /* +0x067 `class`, not read by the pick */
    uint16_t classLevelReq;       /* +0x068 not read by the pick */
    int16_t  itype[7];            /* +0x06A ItemTypes rows, list ends at the first value < 1 */
    int16_t  etype[5];            /* +0x078 ItemTypes rows, list ends at the first value < 1 (0xFFFF = -1 ends it) */
    uint16_t frequency;           /* +0x082 weight; read as a byte; 0 excludes the row */
    uint32_t divide, multiply, add; /* +0x084 price columns, not read by the pick */
} MagicAffixRec;

typedef struct MagicAffixInfo {   /* g_MagicAffixInfo (0x0096CA7C), returned by 0x00633ED0 */
    int32_t  count;               /* +0x00 suffixes + prefixes + automagic */
    MagicAffixRec * base;         /* +0x04 first record (= first suffix); id n is base[n - 1] */
    MagicAffixRec * suffixes;     /* +0x08 magicsuffix records, ids 1..nSuffix */
    MagicAffixRec * prefixes;     /* +0x0C magicprefix records */
    MagicAffixRec * autoMagic;    /* +0x10 automagic records, to base + count */
} MagicAffixInfo;

typedef struct RareAffixRec {     /* 0x48: raresuffix and rareprefix records, merged in that order */
    uint8_t  _pad000[0xC];
    uint16_t nameKey;             /* +0x00C load: string key of `name` */
    uint16_t version;             /* +0x00E `version` (0 in every stock row); >= 100 needs item version >= 100 */
    int16_t  itype[7];            /* +0x010 list ends at the first value < 1 */
    int16_t  etype[4];            /* +0x01E list ends at the first value < 1 */
    char     name[32];            /* +0x026 `name` (descriptor length 31) */
    uint8_t  _pad046[2];
} RareAffixRec;

typedef struct RareAffixInfo {    /* g_RareAffixInfo (0x0096CAA0), returned by 0x00634250 */
    int32_t  count;               /* +0x00 suffixes + prefixes */
    RareAffixRec * base;          /* +0x04 first record (= first suffix); id n is base[n - 1] */
    RareAffixRec * suffixes;      /* +0x08 raresuffix records, ids 1..nSuffix */
    RareAffixRec * prefixes;      /* +0x0C rareprefix records, to base + count */
} RareAffixInfo;
