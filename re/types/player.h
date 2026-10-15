/* Player creation, experience and level-up tables (partial: the fields the creation, experience and level-up code
 * reads). Field names are ours, column names in comments are the .txt headers. Offsets from the field descriptors of
 * CHARSTATS_LoadTable (0x00613260) and EXP_LoadTable (0x00613D30), matched against charstats.bin / experience.bin.
 * Evidence: docs/findings/player/0001-creation.md. [I] unless noted. */
#include <stdint.h>

typedef struct CharStatsStartItem { /* 8 bytes, CharStatsRec.items[10] at +0x5C */
    uint32_t code;                /* +0x0 itemN: item code, 4 chars, space padded ("jav "); "0   " = none */
    uint8_t  loc;                 /* +0x4 itemNloc: body location index (bodylocs), 0 = none */
    uint8_t  count;               /* +0x5 itemNcount */
    uint8_t  _pad6[2];
} CharStatsStartItem;

typedef struct CharStatsRec {     /* 0xC4, DataTables+0xBC4 = g_pCharStats (0x0096C7F4), count +0xBC8 (0x0096C7F8);
                                     record = class id 0..6 (the .txt "Expansion" separator row is not compiled) */
    uint16_t wszClass[16];        /* +0x00 not in the descriptor (filled elsewhere) */
    char     szClass[16];         /* +0x20 class (string, 15 chars) */
    uint8_t  str;                 /* +0x30 str */
    uint8_t  dex;                 /* +0x31 dex */
    uint8_t  energy;              /* +0x32 int */
    uint8_t  vit;                 /* +0x33 vit */
    uint8_t  stamina;             /* +0x34 stamina */
    uint8_t  hpadd;               /* +0x35 hpadd */
    uint8_t  percentStr;          /* +0x36 PercentStr */
    uint8_t  percentInt;          /* +0x37 PercentInt */
    uint8_t  percentDex;          /* +0x38 PercentDex */
    uint8_t  percentVit;          /* +0x39 PercentVit */
    uint8_t  manaRegen;           /* +0x3A ManaRegen */
    uint8_t  _pad3B;
    int32_t  toHitFactor;         /* +0x3C ToHitFactor */
    uint8_t  walkVelocity;        /* +0x40 WalkVelocity */
    uint8_t  runVelocity;         /* +0x41 RunVelocity */
    uint8_t  runDrain;            /* +0x42 RunDrain */
    uint8_t  lifePerLevel;        /* +0x43 LifePerLevel, quarter points */
    uint8_t  staminaPerLevel;     /* +0x44 StaminaPerLevel, quarter points */
    uint8_t  manaPerLevel;        /* +0x45 ManaPerLevel, quarter points */
    uint8_t  lifePerVitality;     /* +0x46 LifePerVitality, quarter points */
    uint8_t  staminaPerVitality;  /* +0x47 StaminaPerVitality, quarter points */
    uint8_t  manaPerMagic;        /* +0x48 ManaPerMagic, quarter points */
    uint8_t  blockFactor;         /* +0x49 BlockFactor */
    uint8_t  _pad4A[2];
    uint32_t baseWClass;          /* +0x4C baseWClass, 4-char code ("hth ") */
    int8_t   statPerLevel;        /* +0x50 StatPerLevel (read signed) */
    uint8_t  _pad51;
    uint16_t strAllSkills;        /* +0x52 StrAllSkills, string-table index */
    uint16_t strSkillTab[3];      /* +0x54 StrSkillTab1..3 */
    uint16_t strClassOnly;        /* +0x5A StrClassOnly */
    CharStatsStartItem items[10]; /* +0x5C item1..item10 with itemNloc, itemNcount */
    int16_t  startSkill;          /* +0xAC StartSkill, skill id, -1 = blank */
    int16_t  skills[10];          /* +0xAE Skill 1..Skill 10, skill ids, -1 = blank */
    uint8_t  _padC2[2];
} CharStatsRec;

typedef struct ExperienceRec {    /* 0x20, g_pExperience (0x0096C8A8); record 0 = the MaxLvl row, record L+1 = Level L;
                                     101 records, count not kept by the loader */
    uint32_t perClass[7];         /* +0x00 Amazon, Sorceress, Necromancer, Paladin, Barbarian, Druid, Assassin */
    uint32_t expRatio;            /* +0x1C ExpRatio (record 0: the shift, 10) */
} ExperienceRec;
