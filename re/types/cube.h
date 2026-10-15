/* CubeMain records as loaded (the compiled input and output cells). Field names are ours.
 * Evidence: docs/findings/items/0008-cube.md ([I] unless noted). Offsets come from the loader's field descriptor
 * (0x00669130) and the cell parsers (0x00668600 inputs, 0x00668A90 outputs); the readers are the transmute
 * functions 0x005665F0, 0x00565010 and 0x00565AB0. */
#include <stdint.h>

typedef struct CubeInput {        /* 8 bytes, CubeMainRec.inputs[7], parsed from `input 1..7` */
    uint16_t flags;               /* +0x0 0x001 item (code, `any`, unique or set name), 0x002 item type, 0x004 nos,
                                     0x008 sock, 0x010 eth, 0x020 noe, 0x040 a given unique/set row, 0x080 upg,
                                     0x100 bas, 0x200 exc, 0x400 eli, 0x800 nru; 0 = empty slot (always matches) */
    uint16_t index;               /* +0x2 item record (flag 0x001) or ItemTypes record (0x002); 0xFFFF = `any` */
    uint16_t rowPlus1;            /* +0x4 unique or set row + 1 (flag 0x040) */
    uint8_t  quality;             /* +0x6 1 low .. 9 (`tmp`); 0 = any quality */
    uint8_t  qty;                 /* +0x7 `qty=`; 0 is read as 1 */
} CubeInput;

typedef struct CubeMod {          /* 12 bytes, CubeOutput.mods[5], from `mod N`, `mod N param/min/max/chance` */
    int32_t  prop;                /* +0x0 properties row (g_PropertiesLink); < 0 = blank */
    int16_t  param;               /* +0x4 */
    int16_t  min;                 /* +0x6 */
    int16_t  max;                 /* +0x8 */
    uint8_t  chance;              /* +0xA 1..99 = one draw on the output's unit seed; 0 or >= 100 = always */
    uint8_t  _pad0B;
} CubeMod;

typedef struct CubeOutput {       /* 0x54 bytes, CubeMainRec.outputs[3], from `output`, `output b`, `output c` */
    uint16_t flags;               /* +0x00 0x001 mod, 0x002 sock, 0x004 eth, 0x008 parser: named unique/set,
                                     0x010 uns, 0x020 rem, 0x040 reg, 0x080 exc, 0x100 eli, 0x200 rep, 0x400 rch */
    uint16_t index;               /* +0x02 item record (kind 0xFC) or ItemTypes record (kind 0xFD) */
    uint16_t rowPlus1;            /* +0x04 unique or set row + 1 (named output) */
    uint8_t  quality;             /* +0x06 forced quality 1..9; 0 = the builder's own roll */
    uint8_t  qty;                 /* +0x07 `qty=` or `sock=` (one byte for both) */
    uint8_t  kind;                /* +0x08 0 none, 1 Cow Portal, 2 Pandemonium Portal, 3 Pandemonium Finale Portal,
                                     0xFC item code, 0xFD item type, 0xFE useitem, 0xFF usetype */
    uint8_t  lvl;                 /* +0x09 `lvl` (fixed ilvl) */
    uint8_t  plvl;                /* +0x0A `plvl` (percent of the player's level) */
    uint8_t  ilvl;                /* +0x0B `ilvl` (percent of input 1's ilvl) */
    uint16_t pre[3];              /* +0x0C `pre=` values, copied to the creation record's forced prefixes */
    uint16_t suf[3];              /* +0x12 `suf=` values, copied to the forced suffixes */
    CubeMod  mods[5];             /* +0x18 */
} CubeOutput;

typedef struct CubeMainRec {      /* 0x148, g_pCubeMain (0x0096D628), count g_nCubeMain (0x0096D62C) */
    uint8_t  enabled;             /* +0x000 0 = skipped unless g_CubeAllRows (0x0088CAC0) is non-zero */
    uint8_t  ladder;              /* +0x001 */
    uint8_t  minDiff;             /* +0x002 `min diff`, compared with Game+0x6D */
    uint8_t  classId;             /* +0x003 `class`; 0xFF = any class */
    uint8_t  op;                  /* +0x004 1..14 player tests, 15..27 input-1 tests, 28 quest-item difficulty */
    uint8_t  _pad005[3];
    int32_t  param;               /* +0x008 */
    int32_t  value;               /* +0x00C */
    uint8_t  numInputs;           /* +0x010 must equal the number of items in the cube */
    uint8_t  _pad011;
    uint16_t version;             /* +0x012 >= 100 = expansion game only */
    CubeInput  inputs[7];         /* +0x014 */
    CubeOutput outputs[3];        /* +0x04C, +0x0A0, +0x0F4 */
} CubeMainRec;
