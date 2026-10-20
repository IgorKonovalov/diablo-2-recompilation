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
    uint8_t  unk10[0x14];         /* +0x10 */
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
