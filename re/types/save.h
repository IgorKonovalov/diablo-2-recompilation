/* Objects the .d2s writer and reader copy fields from and into (partial: only what the save code touches).
 * Field names are ours. Evidence: docs/findings/save/0001-d2s-io.md. [I] unless noted. */
#include <stdint.h>

typedef struct Client { /* server per-connection client (.\GAME\Clients.cpp); accessors 0x005385xx-0x005392xx */
    uint8_t  _pad0000[0x8];
    uint8_t  classId;             /* +0x008 character class; save 0x28 */
    uint8_t  _pad0009;
    uint16_t status;              /* +0x00A save status word: bit0 new, bit2 hardcore, bit3 dead, bit5 expansion, bit6 ladder, bits 8-12 progression; save 0x24 */
    uint8_t  _pad000C;
    char     name[16];            /* +0x00D character name; save 0x14 */
    uint8_t  _pad001D[0x18B];
    uint32_t _unk1A8;             /* +0x1A8 passed to 0x00571F90 after the player unit is created */
    uint8_t  act;                 /* +0x1AC current act 0..4; save 0xA8+difficulty bits 0-6 */
    uint8_t  _pad01AD[0x2AF];
    uint8_t  weaponSwitch;        /* +0x45C non-zero = swap set active; save 0x10 bit 0 */
    uint8_t  _pad045D[0x23];
    uint8_t  _unk480[3];          /* +0x480 only [0] is saved (0xCF); meaning unknown */
    uint8_t  _pad0483[0x5];
    uint32_t _unk488;             /* +0x488 pass-through of save 0x2C (unk_2c) */
    uint8_t  _pad048C[0x1C];
    struct Client * pNext;        /* +0x4A8 next client of the game (Game+0x088) */
} Client;

typedef struct PlayerData { /* unit+0x14 of a player unit (0x006221A0) */
    uint8_t  _pad0000[0x10];
    void    * pQuests[3];         /* +0x010 96-byte quest records, saved in index order (Woo!) */
    void    * pWaypoints[3];      /* +0x01C 16-byte waypoint records, saved in index order (WS) */
    uint8_t  _pad0028[0x38];
    void    * pNpc[3];            /* +0x060 two 8-byte NPC records each (01 77 section) */
    uint8_t  _pad006C[0x4];
    uint32_t rightSkill;          /* +0x070 from save 0x7C */
    uint32_t leftSkill;           /* +0x074 from save 0x78 */
    uint32_t rightSkillItem;      /* +0x078 item ref from save 0x7E, resolved to a unit id on load */
    uint32_t leftSkillItem;       /* +0x07C item ref from save 0x7A */
    uint32_t swapSkillB;          /* +0x080 from save 0x84 */
    uint32_t swapSkillA;          /* +0x084 from save 0x80 */
    uint32_t swapSkillBItem;      /* +0x088 from save 0x86 */
    uint32_t swapSkillAItem;      /* +0x08C from save 0x82 */
} PlayerData;

typedef struct ItemData { /* unit+0x14 of an item unit, 0x74 bytes (rng/0002) */
    uint32_t quality;             /* +0x000 1..9; saved 4 bits */
    uint32_t seed[2];             /* +0x004 item-data seed (rng/0002); not saved */
    uint8_t  _pad000C[0xC];
    uint32_t flags;               /* +0x018 item flags; saved 32 bits (bit 4 identified, 11 socketed, 13 new, 16 ear, 21 simple, 22 ethereal, 24 personalized, 26 runeword) */
    uint8_t  _pad001C[0x10];
    int32_t  ilvl;                /* +0x02C item level, 1..99; saved 7 bits */
    uint16_t version;             /* +0x030 item version (Game+0x078 at creation); saved 10 bits */
    uint16_t _unk32;              /* +0x032 cleared by the reader */
    uint16_t _unk34;              /* +0x034 cleared by the reader */
    uint16_t autoAffix;           /* +0x036 automagic affix id; saved as class_affix */
    uint16_t prefix[3];           /* +0x038 prefix ids; [0] also receives the runeword u16 on load */
    uint16_t suffix[3];           /* +0x03E suffix ids */
    uint8_t  bodyLoc;             /* +0x044 equip slot; saved `body` */
    int8_t   invPage;             /* +0x045 inventory page; saved `store` = invPage + 1 */
    uint8_t  _pad0046[0x2];
    uint8_t  earLevel;            /* +0x048 */
    uint8_t  gfx;                 /* +0x049 picture variant; saved 3 bits */
    char     name[16];            /* +0x04A ear or personalized name, 7 bits per char in the save */
} ItemData;

typedef struct ItemStatCostRec { /* DataTables+0xBCC + 0x144*id, count DataTables+0xBD4 */
    uint8_t  _pad0000[0x5];
    uint8_t  flags05;             /* +0x005 bit 5 = CSvSigned */
    uint8_t  _pad0006[0x4];
    uint8_t  csvBits;             /* +0x00A CSvBits (character stats) */
    uint8_t  csvParam;            /* +0x00B CSvParam */
    uint8_t  _pad000C[0xC];
    uint8_t  valShift;            /* +0x018 ValShift */
    uint8_t  saveBits;            /* +0x019 Save Bits */
    uint8_t  saveBits109;         /* +0x01A 1.09-Save Bits (saves older than version 93) */
    uint8_t  _pad001B;
    int32_t  saveAdd;             /* +0x01C Save Add */
    int32_t  saveAdd109;          /* +0x020 1.09-Save Add */
    uint32_t saveParamBits;       /* +0x024 Save Param Bits */
} ItemStatCostRec;
