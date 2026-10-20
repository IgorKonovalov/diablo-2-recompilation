/* Skills: a unit's skill list and its skill entries, the dispatch fields of the Skills record (plan 0045 Phase 1,
 * batch P1.1). Field names are ours. Evidence: docs/findings/skills/0001-dispatch.md. [I] unless noted.
 * The Skills record itself (572 bytes) is laid out in docs/tables/Skills.md; only the fields the dispatch reads are
 * repeated here, by offset. */
#include <stdint.h>

/* One skill a unit has. 0x40 bytes, zeroed and appended to the list by SKILLS_AddSkill (0x00647110). */
typedef struct SkillEntry {
    void    * pRecord;            /* +0x00 Skills record (DataTables+0xB98 + id*0x23C); *(int16*)pRecord = skill id */
    struct SkillEntry * pNext;    /* +0x04 */
    int32_t  mode;                /* +0x08 the mode the skill runs in: Skills `monanim` (+0x11) for a monster, 16 for the
                                     assassin's Left Hand Swing (class 6, skill 5), else Skills `anim` (+0x10) */
    uint32_t flags;               /* +0x0C bit 0: move to the target first, do on arrival; bit 1: arrived (set by the
                                     frame functions when the move step returns 2) */
    uint8_t  unk10[0x08];         /* +0x10 */
    int32_t  state18;             /* +0x18 per-skill state word of the do functions (0x006444A0 get, 0x00644560 set;
                                     skills/0003): Blade Fury's next fragment frame, Frenzy's last hit (1/0),
                                     Armageddon's re-seed value (do 146), start 55's rolled value */
    int32_t  unk1C;               /* +0x1C also a re-seed word for 0x00645390 (+7 per repeat), and set by start 55 */
    int32_t  unk20;               /* +0x20 */
    int32_t  altHand;             /* +0x24 dual-wield Attack alternation: 0 or 5 (sub_00549960_DualAttackAlternate) */
    int32_t  baseLevel;           /* +0x28 hard points; 1 when added */
    int32_t  unk2C;               /* +0x2C */
    int32_t  quantity;            /* +0x30 scroll and book uses (Skills `scroll` rows), tested > 0 */
    int32_t  ownerItem;           /* +0x34 guid of the item that grants it, -1 for a skill of the unit's own */
    int32_t  charges;             /* +0x38 an item skill's charges left, tested > 0 */
    int32_t  unk3C;               /* +0x3C */
} SkillEntry;

/* The unit's skill list, Unit+0xA8. */
typedef struct SkillList {
    void    * unk00;              /* +0x00 */
    SkillEntry * pFirst;          /* +0x04 head of the entry chain */
    SkillEntry * pLeft;           /* +0x08 left skill (UNIT_GetLeftSkill 0x00620190) */
    SkillEntry * pRight;          /* +0x0C right skill (UNIT_GetRightSkill 0x006201D0) */
    SkillEntry * pUsed;           /* +0x10 the skill of the current mode (UNIT_GetUsedSkill / UNIT_SetUsedSkill) */
} SkillList;

/* Unit fields the dispatch reads (the full Unit layout lives in other headers' comments; these are by offset).
 *   Unit+0x00 type (0 player, 1 monster), Unit+0x10 mode, Unit+0x20/+0x24 the unit seed (low, high),
 *   Unit+0x4E monster frame-event byte (1, 2 action; 4 sequence), Unit+0xA8 SkillList *,
 *   Unit+0xC4 bit 6 (0x40): "the action of this mode has run" (cleared by the player skill mode starts, set by most
 *   do functions and by SKILLS_SrvDo when it creates the skill's srvmissile). */

/* Skills record fields the dispatch reads (docs/tables/Skills.md gives the layout [C]; the readings are ours).
 *   +0x004 bit 0 decquant (ammunition), bit 1 lob, bit 4 passive (CanUse 5), bit 5 aura (CanUse 6), bit 6 periodic,
 *          bit 7 prgstack
 *   +0x005 bit 0 InTown, bit 2 InGame (CanUse 3 when clear), bit 7 immediate
 *   +0x006 bit 4 TargetableOnly
 *   +0x007 bit 0 TargetCorpse, bit 2 TargetAlly, bit 3 TargetItem, bit 4 AttackNoMana
 *   +0x008 bit 1 ItemCheckStart, bit 4 scroll, bit 5 usemanaondo
 *   +0x010 anim, +0x011 monanim, +0x014 range (0 none, 1 h2h, 2 rng, 3 both)
 *   +0x018 itypea1, +0x024 etypea1 (the weapon test runs when either is set)
 *   +0x02C srvstfunc (g_SkillStartFuncs, < 0x5B), +0x02E srvdofunc (g_SkillDoFuncs, < 0xBF), +0x030..+0x034 srvprgfunc1..3
 *   +0x046 srvmissile, +0x04E srvoverlay, +0x054 aurastat1 (the progressive charge stat), +0x060 auralencalc,
 *   +0x080 aurastate, +0x082 auratargetstate
 *   +0x120 ItemTarget, +0x128 perdelay calc, +0x12E ResultFlags, +0x130 HitFlags, +0x134 HitClass
 *   +0x138..+0x144 calc1..calc4, +0x16A ItemEffect
 *   +0x184 startmana, +0x186 minmana, +0x188 manashift (low byte), +0x18A mana (s16), +0x18C lvlmana (s16)
 *   +0x18F LineOfSight (1..5), +0x190 delay calc, +0x1A5 SrcDam (0 read as 128), +0x1DC EType
 *   +0x228 restrict, +0x22A..+0x22E State1..3 */

/* ---- Missiles (plan 0045 Phase 1, batch P1.2). Evidence: docs/findings/skills/0002-missiles.md. [I] unless noted. ---- */

/* The request sub_0059FA30_MissileCreate reads (ECX game, EDX = this). 0x5C bytes, zeroed by every caller. */
typedef struct MissileParams {
    uint32_t flags;               /* +0x00 0x1 start given, 0x2 target = start + offset, 0x4 velocity given,
                                     0x8 add loops, 0x10 velocity already in 1/256, 0x20 target absolute,
                                     0x200 frames already run, 0x400 lob (frames left from the distance),
                                     0x800 activate override, 0x1000 to-hit, 0x8000 range override,
                                     0x10000 MissileData flag bit 1 */
    void    * pOwner;             /* +0x04 player or monster (else no missile) */
    void    * pSource;            /* +0x08 start position when flag 0x1 is clear; the SrcMissDmg source */
    void    * pTarget;            /* +0x0C target unit, or 0 */
    int32_t  missile;             /* +0x10 Missiles row */
    int32_t  x, y;                /* +0x14, +0x18 start (flag 0x1) */
    int32_t  tx, ty;              /* +0x1C, +0x20 target point or offset (flags 0x20, 0x2) */
    uint32_t unk24;               /* +0x24 */
    int32_t  velocity;            /* +0x28 flag 0x4 */
    int32_t  skill;               /* +0x2C */
    int32_t  level;               /* +0x30 */
    int32_t  loops;               /* +0x34 flag 0x8, times (SubStop - SubStart) */
    uint8_t  unk38[8];            /* +0x38 */
    int32_t  framesRun;           /* +0x40 flag 0x200: range -= it, Unit+0x44 = it << 8 */
    int32_t  activate;            /* +0x44 flag 0x800 */
    int32_t  toHit;               /* +0x48 flag 0x1000: missile stat 19 */
    int32_t  range;               /* +0x4C flag 0x8000 */
    uint32_t unk50;               /* +0x50 */
    void   (*pfnInit)(void);      /* +0x54 ECX missile, EDX cbArg; runs before the damage block */
    uint32_t cbArg;               /* +0x58 */
} MissileParams;

/* The missile unit's data, Unit+0x14 (0x34 bytes, sub_0064A100_MissileDataAlloc). Accessors MISSDATA_* clamp s16. */
typedef struct MissileData {
    uint8_t  unk00[8];            /* +0x00 */
    int16_t  activateMark;        /* +0x08 range - Activate: unit collision once frames left <= it */
    int16_t  skill;               /* +0x0A */
    int16_t  level;               /* +0x0C */
    int16_t  range;               /* +0x0E total frames */
    int16_t  remaining;           /* +0x10 frames left, decremented by do function 1 before its tests */
    uint16_t unk12;               /* +0x12 */
    uint32_t flags;               /* +0x14 bit 0 weapon damage (packet 0x20), bit 1 (packet 0x80) */
    int32_t  lastHitType;         /* +0x18 LastCollide rows: the last unit hit (the owner at creation) */
    int32_t  lastHitGuid;         /* +0x1C -1 when none */
    int32_t  refType, refGuid;    /* +0x20, +0x24 a second unit reference (0x0064A7B0) */
    uint32_t seedLow;             /* +0x28 a stored seed low word (MISSDATA_SetSeedLow / GetSeedLow): written at creation
                                     by the progressive rings (Param2 + 1), do 41, hit 36 and after the draws of do 28
                                     and 35, read back by them to re-seed Unit+0x20 (skills/0003 § 9) */
    uint32_t param2C;             /* +0x2C a packed (dy << 16 | dx) offset, or a unit guid (hit 22) */
    int32_t  unk30;               /* +0x30 used by numbered functions (plan 0046) */
} MissileData;

/* The creation-time damage block of sub_0064B860_MissileDamageBlock (0x7C bytes), written as missile stats by
 * sub_0064AC60_MissileDamageToStats. */
typedef struct MissileDamageBlock {
    uint32_t flags;               /* +0x00 bit 0 weapon share, bit 1 critical (stat 141), bit 2 (MissileData bit 1),
                                     0x100/0x200/0x400 bypass undead/demon/beast */
    int32_t  min, max;            /* +0x04, +0x08 -> stats 21, 22 */
    int32_t  fireMin, fireMax, fireLen;          /* +0x0C..+0x14 -> 48, 49, 315 */
    int32_t  ltngMin, ltngMax;                   /* +0x18, +0x1C -> 50, 51 */
    int32_t  magicMin, magicMax;                 /* +0x20, +0x24 -> 52, 53 */
    int32_t  coldMin, coldMax, coldLen;          /* +0x28..+0x30 -> 54, 55, 56 */
    int32_t  poisMin, poisMax, poisLen, poisCnt; /* +0x34..+0x40 -> 57, 58, 59, 326 */
    int32_t  steal[6];                           /* +0x44..+0x58 -> 60..65 */
    int32_t  stunLen;                            /* +0x5C -> 66 */
    int32_t  burnMin, burnMax, burnLen;          /* +0x60..+0x68 -> 316, 317, 315 (overwrites fireLen's write) */
    int32_t  demonPct, undeadPct, acDmg;         /* +0x6C..+0x74 -> 121, 122, 120 */
    int32_t  edPct;                              /* +0x78 -> 25, floored at -90 */
} MissileDamageBlock;

/* g_MissileCollideTypes (0x0073C720), by Missiles CollideType (the missile unit's mode, Unit+0x10). */
typedef struct MissileCollideType {
    int (*pfnFilter)(void);       /* +0x00 ECX candidate, EDX {game, missile, owner, record}; 0 = no unit test */
    uint32_t mask;                /* +0x04 CollisionTest mask and the path's collide mask */
} MissileCollideType;

/* Missiles record fields the machinery reads (docs/tables/Missiles.md gives the layout [C]; the readings are ours).
 *   +0x004 bit 0 LastCollide (last unit hit is skipped), bit 1 Explosion (no damage without a hit function),
 *          bit 2 Pierce, bit 3 CanSlow (state 87), bit 4 CanDestroy (Unit+0xC4 |= 4; CollideType 7 target),
 *          bit 6 GetHit, bit 7 SoftHit
 *   +0x005 bit 0 ApplyMastery, bit 2 Town, bit 3 SrcTown (a monster owner in town ends it), bit 6 Half2HSrc,
 *          bit 7 MissileSkill
 *   +0x00C pSrvDoFunc, +0x00E pSrvHitFunc, +0x010 pSrvDmgFunc (each tested > 0 as s16, then < the table's count)
 *   +0x018 SubMissile1 (do function 2), +0x024 HitSubMissile1, +0x038/+0x03C Param1/2, +0x04C sHitPar1
 *   +0x080 SrvCalc1, +0x094 HitClass (byte), +0x096 Range, +0x098 LevRange, +0x09A Vel, +0x09B VelLev, +0x09C MaxVel,
 *   +0x09E Accel, +0x0AE KnockBack (byte), +0x12D SrcDamage (0xFF = none for a skill missile), +0x12E SrcMissDmg,
 *   +0x12F Holy (bits 1, 2, 4), +0x136 Activate, +0x180..+0x182 SubLoop/SubStart/SubStop, +0x183 CollideType,
 *   +0x184 Collision, +0x186 CollideKill, +0x187 CollideFriend, +0x188 NextHit, +0x189 NextDelay, +0x18A Size,
 *   +0x18B ToHit, +0x18C AlwaysExplode, +0x194 Skill, +0x19C DamageRate (stat 327) */
