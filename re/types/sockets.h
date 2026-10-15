/* Gems and Runes records as loaded (partial where the loader descriptor or the code does not pin a field).
 * Field names are ours. Evidence: docs/findings/items/0007-sockets-runewords.md ([I] unless noted): the loader
 * descriptors of GEMS_Load (0x00636B70) and RUNES_Load (0x006394A0), and the readers RUNEWORD_Match (0x0062BED0),
 * RUNEWORD_Apply (0x006600A0) and sub_0065C6D0_PropBlock3x3. PropBlock is in properties.h. */
#include <stdint.h>
#include "properties.h"

typedef struct GemsRec {          /* 0xC0, g_pGems (0x0096CA94), count g_nGems (0x0096CA90) */
    char     name[32];            /* +0x000 `name` (descriptor type 1, 0x1F) */
    char     letter[8];           /* +0x020 `letter` (type 5) */
    int32_t  item;                /* +0x028 `code`, through g_ItemCodeLink (type 0x0B): the base item index; GEMS_Load
                                   * writes this row's index into that item record's gemoffset (+0x0F0) */
    uint16_t nameKey;             /* +0x02C load: STRTABLE_GetByKey of the bytes at +0x028 (not followed) */
    uint8_t  nummods;             /* +0x02E `nummods`; not read by the socket path */
    uint8_t  transform;           /* +0x02F `transform` (colour, items/0003) */
    PropBlock weaponMod[3];       /* +0x030 gemapplytype 0 */
    PropBlock helmMod[3];         /* +0x060 gemapplytype 1 */
    PropBlock shieldMod[3];       /* +0x090 gemapplytype 2 */
} GemsRec;

typedef struct RunesRec {         /* 0x120, g_pRunes (0x0096CA9C), count g_nRunes (0x0096CA98) */
    char     name[64];            /* +0x000 `Name` (Runeword1..); the key of nameStr */
    char     runeName[64];        /* +0x040 `Rune Name` */
    uint8_t  complete;            /* +0x080 0 = the row never matches */
    uint8_t  server;              /* +0x081 non-zero = applied only in a ladder game (Game+0x74) */
    uint16_t nameStr;             /* +0x082 load: STRTABLE_GetByKey(name); saved as the 16-bit runeword field */
    uint16_t _pad084;
    int16_t  itype[6];            /* +0x086 itype1..6 (ItemTypes index, 0 ends the list) */
    int16_t  etype[3];            /* +0x092 etype1..3 (ItemTypes index, 0 ends the list) */
    int32_t  rune[6];             /* +0x098 Rune1..6 (item index through g_ItemCodeLink, < 1 ends the list) */
    PropBlock t1[7];              /* +0x0B0 T1Code1/T1Param1/T1Min1/T1Max1 .. 7; code < 0 ends the list */
} RunesRec;
