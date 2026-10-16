/* Combat: the damage packet, the reduction context and the resistance table (plan 0037 Phase 1).
 * Field names are ours. Evidence: docs/findings/combat/0001-formulas.md. [I] unless noted.
 * Units: damage fields are in 1/256 life (a stat value << 8) except where noted; percents are whole numbers.
 * The packet is 0x70 bytes: callers memset 0x70 on the stack (0x005A5490, 0x0056F070) and the hit queue copies
 * 0x1C dwords (0x0057CA80, 0x0057D4F0). */
#include <stdint.h>

typedef struct DamagePacket {     /* 0x70 */
    uint32_t flags;               /* +0x00 input flags: 0x1 physical already set (skip the roll), 0x2 already built
                                     (COMBAT_ResolveAndQueue skips the builder), 0x4/0x8/0x10 no life/mana/stamina
                                     steal from stats, 0x20 set by the builder (and forced by the queue delivery),
                                     0x80 missile without the "domissiledamage" event, 0x100/0x200/0x400 bypass
                                     undead/demons/beasts (stats 103/104/106), 0x1000 hits non-hostile targets */
    uint16_t result;              /* +0x04 outcome: 0x1 hit, 0x2 killed, 0x4 get-hit, 0x8 knockback, 0x10 blocked,
                                     0x20 no events, 0x80 dodged, 0x100 avoided, 0x200 evaded (missiles),
                                     0x2000 critical / deadly strike (doubled), 0x4000 missile pass, 0x8000 weapon block */
    uint16_t pad06;
    int32_t  phys;                /* +0x08 "Dam" */
    int32_t  edPct;               /* +0x0C enhanced-damage percent added to stat 25 by the physical roll */
    int32_t  fire;                /* +0x10 "Fire" */
    int32_t  burn;                /* +0x14 burning damage per frame (see the 316 + RangeB(1) quirk) */
    int32_t  burnLen;             /* +0x18 burning length, frames */
    int32_t  light;               /* +0x1C "Ligt" */
    int32_t  magic;               /* +0x20 "Magc" */
    int32_t  cold;                /* +0x24 "Cold" */
    int32_t  poison;              /* +0x28 "Pois", per frame */
    int32_t  poisonLen;           /* +0x2C "PLen", frames */
    int32_t  coldLen;             /* +0x30 "CLen", frames */
    int32_t  freezeLen;           /* +0x34 "FLen", frames */
    int32_t  lifeSteal;           /* +0x38 "Life": percent (players, hirelings) or rolled drain (monsters) */
    int32_t  manaSteal;           /* +0x3C "Mana" */
    int32_t  stamSteal;           /* +0x40 "Stam" */
    int32_t  stunLen;             /* +0x44 frames */
    int32_t  absorbHeal;          /* +0x48 life returned to the defender by absorb */
    int32_t  total;               /* +0x4C life removed: phys+fire+light+magic+cold+poison (+lifeSteal, monster attacker) */
    int32_t  unk50;               /* +0x50 */
    int32_t  frameRate;           /* +0x54 missile stat 327 damage_framerate; scales DR and MDR when > 0 */
    int32_t  unk58;               /* +0x58 */
    int32_t  unk5C;               /* +0x5C */
    uint32_t hitClass;            /* +0x60 */
    uint8_t  hitClassSet;         /* +0x64 */
    uint8_t  convType;            /* +0x65 element the physical share converts to: 1 fire, 2 light, 3 magic, 4 cold,
                                     5 poison, 10 random 1..5, 11 fire+burn, 12 cold+freeze */
    uint8_t  pad66[2];
    int32_t  convPct;             /* +0x68 percent of physical moved to convType */
    int32_t  overlay;             /* +0x6C overlay put on the defender after delivery */
} DamagePacket;

typedef struct ReduceCtx {        /* 0x34, on the stack of COMBAT_ApplyReductions (0x0057C1E0) */
    void    *game;                /* +0x00 */
    void    *diffRec;             /* +0x04 DifficultyLevels record of game+0x6D (ResistPenalty +0x00,
                                     HireableBossDamagePercent +0x38) */
    void    *attacker;            /* +0x08 */
    void    *defender;            /* +0x0C */
    int32_t  attackerIsMonster;   /* +0x10 monster and not a hireling */
    int32_t  defenderIsMonster;   /* +0x14 monster and not a hireling */
    DamagePacket *pkt;            /* +0x18 */
    int32_t  reduce[3];           /* +0x1C slot 0: 0; slot 1: DR = stat34 << 8; slot 2: MDR = stat35 << 8
                                     (each MulDiv(x, pkt->frameRate, 1024) when frameRate > 0) */
    int32_t  unk28, unk2C;        /* +0x28 */
    int32_t  pct;                 /* +0x30 COMBAT_DamagePercent result */
} ReduceCtx;

typedef struct ResistRow {        /* 0x2C, g_DamageResistTable (0x00732980), 12 rows */
    int32_t  pktOffset;           /* +0x00 field of DamagePacket */
    int32_t  resStat;             /* +0x04 defender's resist stat, -1 none */
    int32_t  maxStat;             /* +0x08 defender's max-resist stat, -1 none */
    int32_t  pierceStat;          /* +0x0C attacker's pierce stat, -1 none */
    int32_t  absorbPctStat;       /* +0x10 defender's absorb percent stat, -1 none */
    int32_t  absorbStat;          /* +0x14 defender's flat absorb stat */
    int32_t  reduceSlot;          /* +0x18 index into ReduceCtx.reduce */
    int32_t  monsterOnly;         /* +0x1C row processed only for a monster attacker (the steal rows) */
    int32_t  scaled;              /* +0x20 scaled by ReduceCtx.pct */
    const char *name;             /* +0x24 debug name ("Dam", "Fire", ...) */
    int32_t  nameArg;             /* +0x28 */
} ResistRow;
