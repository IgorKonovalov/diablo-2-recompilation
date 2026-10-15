/* NPC stores: vendor stock, gambling, the per-game store control. Field names are ours.
 * Evidence: docs/findings/items/0009-vendors.md (plan 0031 Phase 1, static reading). [I] unless noted. */
#include <stdint.h>

typedef struct NpcStoreSlot {     /* 8, g_NpcStoreTable entries at 0x00731188 (count 43 at 0x00731184) */
    uint32_t classId;             /* +0x0 MonStats row of the NPC */
    uint8_t  hasStore;            /* +0x4 copied to NpcStoreRec.hasStore */
    uint8_t  act;                 /* +0x5 0..4, copied to NpcStoreRec.act */
    uint8_t  flag6;               /* +0x6 copied to NpcStoreRec+0x26; not followed */
    uint8_t  _pad7;
} NpcStoreSlot;

typedef struct VendorStockEntry { /* 0xC, one per base a vendor can stock (VENDOR_BuildList) */
    uint8_t  min;                 /* +0x0 items +0x146+v  <Vendor>Min */
    uint8_t  max;                 /* +0x1 items +0x157+v  <Vendor>Max */
    uint8_t  magicMin;            /* +0x2 items +0x168+v  <Vendor>MagicMin */
    uint8_t  magicMax;            /* +0x3 items +0x179+v  <Vendor>MagicMax */
    uint32_t code;                /* +0x4 items +0x080    code */
    uint8_t  magicLvl;            /* +0x8 items +0x18A+v  <Vendor>MagicLvl */
    uint8_t  _pad9[3];
} VendorStockEntry;

typedef struct VendorList {       /* 0x10, g_VendorLists[17] at 0x00883D78, built once per process (VENDOR_BuildAllLists) */
    VendorStockEntry * entries;   /* +0x0 bases with PermStoreItem = 0, item-index order */
    int32_t  nEntries;            /* +0x4 */
    uint32_t * permCodes;         /* +0x8 codes of bases with PermStoreItem != 0, item-index order */
    int32_t  nPerm;               /* +0xC */
} VendorList;

typedef struct GambleInvNode {    /* 0xC, one per player with a gamble window (GAMBLE_BuildInv) */
    void    * pInventory;         /* +0x0 the player's gamble inventory */
    uint32_t playerId;            /* +0x4 player unit id */
    struct GambleInvNode * next;  /* +0x8 */
} GambleInvNode;

typedef struct NpcStoreRec {      /* 0x44, one per MonStats row with the `interact` flag, in row order (NPCSTORE_CtlCreate) */
    uint32_t classId;             /* +0x00 MonStats row */
    void    * pInventory;         /* +0x04 the shared stock inventory (also the NPC unit's +0x60) */
    GambleInvNode * gambleInvs;   /* +0x08 per-player gamble inventories */
    uint32_t isGambler;           /* +0x0C 1 for classes 147, 199, 254, 405, 512, 514 */
    void    * pHirelings;         /* +0x10 hireling list (HIRE_BuildStock) */
    void    * pPending;           /* +0x14 pending-item list; its consumer has no caller */
    void    * pProxies;           /* +0x18 per-player proxy nodes (+0x4 byte: 0 trade, 1 gamble) */
    uint32_t opened;              /* +0x1C set to 1 by NPC_TradeOpen (trade or gamble) */
    uint8_t  built;               /* +0x20 the stock has been built */
    uint8_t  hirelingsBuilt;      /* +0x21 */
    uint8_t  act;                 /* +0x22 0..4: Normal ilvl cap index, stale-check filter */
    uint8_t  hasStore;            /* +0x23 */
    uint8_t  flag24, flag25, flag26; /* +0x24..+0x26 not followed */
    uint8_t  stale;               /* +0x27 rebuild on the next trade open (NPCSTORE_ActStale) */
    uint32_t buildTick;           /* +0x28 GetTickCount at the last build or stale mark */
    VendorStockEntry * entries;   /* +0x2C copied from g_VendorLists[v] */
    int32_t  nEntries;            /* +0x30 */
    uint32_t * permCodes;         /* +0x34 */
    int32_t  nPerm;               /* +0x38 */
    uint8_t  _pad3C[0x4];
    uint32_t npcUnitId;           /* +0x40 unit id of the NPC at the last open */
} NpcStoreRec;

typedef struct NpcStoreCtl {      /* 0x14, Game+0x1D24, allocated at game creation (NPCSTORE_CtlCreate) */
    int32_t  nRecs;               /* +0x00 records in use (at most 64) */
    NpcStoreRec * recs;           /* +0x04 64 records, 0x1100 bytes */
    uint32_t seed[2];             /* +0x08 the store seed: init(low of one game-seed step) */
    int32_t  nInteract;           /* +0x10 count of interact rows */
} NpcStoreCtl;

typedef struct GambleList {       /* g_GambleList at 0x0096CAB0, filled by GAMBLE_LoadTable */
    int32_t  nRows;               /* +0x000 Gamble.txt rows */
    int32_t  * items;             /* +0x004 item indices sorted by base `level` (qsort, comparator 0x00638AC0) */
    int32_t  countUpTo[100];      /* +0x008 [L] = rows with base level <= L for L >= 1; [0] = 2 */
} GambleList;
