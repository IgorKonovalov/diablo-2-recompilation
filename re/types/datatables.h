/* Excel data-tables block (partial: only the fields findings cite).
 * Evidence: docs/findings/data/0001-excel-loader.md §5 ([I] unless the finding says otherwise). */
#include <stdint.h>

typedef struct DataTables { /* one block at 0x0096BC30; g_pDataTables (0x00744304) points at it; size unknown */
    uint8_t  _pad0000[0x94];
    void    * pItemCodeLink;      /* +0x094 g_ItemCodeLink 0x0096BCC4 */
    void    * pItemsCode;         /* +0x098 itemscode.bin buffer 0x0096BCC8 (§3) */
    uint8_t  _pad009C[0x91C];
    void    * pTCLink;            /* +0x9B8 g_TCLink 0x0096C5E8 */
    struct TreasureClass * pTreasureClasses;/* +0x9BC g_pTreasureClasses 0x0096C5EC (tc.h) */
    int32_t  nTreasureClasses;    /* +0x9C0 g_nTreasureClasses 0x0096C5F0 */
    uint8_t  _pad09C4[0xB4];
    void    * pMonStats;          /* +0xA78 g_pMonStats 0x0096C6A8, 0x1A8-byte records */
    void    * pMonStatsLink;      /* +0xA7C g_MonStatsLink 0x0096C6AC */
    int32_t  nMonStats;           /* +0xA80 0x0096C6B0 */
    uint8_t  _pad0A84[0x174];
    void    * pItemTypes;         /* +0xBF8 g_pItemTypes 0x0096C828 */
    int32_t  nItemTypes;          /* +0xBFC 0x0096C82C */
    uint8_t  _pad0C00[0x58];
    void    * pLevels;            /* +0xC58 g_pLevels 0x0096C888 */
    int32_t  nLevels;             /* +0xC5C 0x0096C88C */
    void    * pLevelDefs;         /* +0xC60 g_pLevelDefs 0x0096C890 (count = nLevels) */
    uint8_t  _pad0C64[0x1C4];
    int32_t  nItems;              /* +0xE28 g_nItems 0x0096CA58 (weapons+armor+misc) */
    void    * pItems;             /* +0xE2C g_pItems 0x0096CA5C, 0x1A8-byte records */
    void    * pWeapons;           /* +0xE30 g_pWeapons 0x0096CA60 (sub-range of pItems) */
    int32_t  nWeapons;            /* +0xE34 0x0096CA64 */
    void    * pArmor;             /* +0xE38 g_pArmor 0x0096CA68 (sub-range of pItems) */
    int32_t  nArmor;              /* +0xE3C 0x0096CA6C */
    void    * pMisc;              /* +0xE40 g_pMisc 0x0096CA70 (sub-range of pItems) */
    int32_t  nMisc;               /* +0xE44 0x0096CA74 */
    uint8_t  _pad0E48[0x1D0];
    int32_t  nItemRatio;          /* +0x1018 0x0096CC48 */
    void    * pItemRatio;         /* +0x101C g_pItemRatio 0x0096CC4C */
} DataTables;
