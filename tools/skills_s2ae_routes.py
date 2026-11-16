#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S2ae (`lane/n66sa`): the route reads behind the batch's rows (ruling R2, ADR-0021,
ADR-0029). For each root, the direct-call graph under it (tools/sweep2_s7e_routes.py's walker over
tools/sweep_s4b.py's objdump bodies; indirect calls counted, not followed), cut at the pool allocator and free entries
and the fatal handlers, to a depth bound; printed per root: the first path to each allocator entry reached with the
call site, every import call (`call [slot]` with the slot in the import address table) with its site, and the number
of other indirect calls. A root's listing says which callees a route reaches; whether a given case reaches them is the
branch's reading, cited per row in the finding.

    python3 -I tools/skills_s2ae_routes.py [--depth N] > workspace/logs/n66sa/s2ae/routes.txt

Stdlib only, plus the objdump binary. Read-only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep_s4b as W  # noqa: E402
import sweep2_s7e_routes as R  # noqa: E402

ROOTS = [   # (label, entry, rows: d = skills/dispatch, m = skills/missiles inventory rows)
    ("SKILLS_CanUse", 0x00647960, "d3, d32, d33, d63r"),
    ("SkillAmmoOk", 0x00647640, "d34"),
    ("SKILLS_WeaponTypeOk", 0x00643F80, "d35"),
    ("SKILLS_ManaOk", 0x00647540, "d36, d37"),
    ("SKILLS_RestrictOk", 0x00644060, "d38"),
    ("SKILLS_StartManaOk", 0x006440F0, "d39"),
    ("SKILLS_ItemChargesOk", 0x00647840, "d40"),
    ("SKILLS_GetRangeType", 0x00645460, "d30"),
    ("DualAttackAlternate", 0x00549960, "d31r"),
    ("SKILLS_TargetCheck", 0x0056CC60, "d47"),
    ("SKILLS_SrvManaCheck", 0x0056C160, "d49"),
    ("SKILLS_DelayOk", 0x006478F0, "d69"),
    ("ITEMSKILL_Cast", 0x005FDA80, "d79r"),
    ("ItemTargetRandomPoint", 0x005FD850, "d83"),
    ("ItemTargetCorpse", 0x005FD9C0, "d84"),
    ("ItemTargetStoredUnit", 0x005FDA10, "d84"),
    ("SkillSt06Hit", 0x005DA940, "d89"),
    ("SkillKickDamage", 0x00644C20, "d91"),
    ("SKILLS_GetPhysMin", 0x00647BC0, "d92"),
    ("SkillSrcDamWeapon", 0x00623990, "d92"),
    ("SkillSt02Kick", 0x0056CAF0, "d93"),
    ("KickItemDamage", 0x00646280, "d96"),
    ("StatEv01MissileAtSource", 0x005CAB40, "d110"),
    ("StatEv02CalcHitAttacker", 0x005CAC50, "d111"),
    ("StatEv03ElemHitAttacker", 0x005CAD40, "d112"),
    ("StatEv07Knockback", 0x005BF960, "d135"),
    ("StatEv08Howl", 0x005BFA10, "d117, d135"),
    ("StatEv09Stupidity", 0x005BFAA0, "d135"),
    ("StatEv10ThornsLightning", 0x005BF720, "d119"),
    ("STATEVENT_Freeze", 0x005BFC60, "d122"),
    ("StatEv18HealAfterDemonKill", 0x005C0260, "d124"),
    ("StatEv23BloodGolemHit", 0x005C6530, "d127"),
    ("StatEv24EnergyShield", 0x005CA6C0, "d128"),
    ("StatEv25CycloneArmor", 0x005C87A0, "d129"),
    ("StatEv26BloodGolemDamaged", 0x005C6690, "d130"),
    ("StatEv27ClayGolemSlow", 0x005C6760, "d131"),
    ("STATEVENT_Reanimate", 0x005C09E0, "d133"),
    ("StatEv11ThornsFire", 0x005BF7D0, "d135"),
    ("StatEv12ThornsCold", 0x005BF880, "d135"),
    ("StatEv30SkillOnDeathOrLevel", 0x005C0670, "d135"),
    ("PreventHealHook", 0x0057D810, "d138"),
    ("SummonSetLevel", 0x005C49E0, "d142, d143"),
    ("SummonInitStats", 0x005C4470, "d144"),
    ("SkeletonParam1Roll", 0x005C4300, "d149"),
    ("MonAttackStats", 0x005A4F50, "d152"),
    ("MonOwnerSkillDamage", 0x0056E050, "d153, d154"),
    ("SkillWeaponWear", 0x005DAA40, "d156, d181"),
    ("SkillDo146Armageddon", 0x005C8520, "d182, d184"),
    ("SorSkillStaticMin", 0x005C9800, "d164r"),
    ("SkillDo117Firestorm", 0x005C7160, "d172r"),
    ("MissileCreate", 0x0059FA30, "m14, m16, m17, m18, m19"),
    ("MissileOwnerUModEvent", 0x005A43B0, "m21"),
    ("MissileDamageBlock", 0x0064B860, "m26, m29"),
    ("MissileDamageToStats", 0x0064AC60, "m27, m95"),
    ("MissileCritRoll", 0x0064A850, "m28"),
    ("PathVelocityStep", 0x006502D0, "m35"),
    ("PathDirection", 0x0064FC60, "m38, m98"),
    ("CollidePlayerOrAlly", 0x005A87F0, "m40"),
    ("CollideMonster", 0x005A87B0, "m41"),
    ("CollideUnit", 0x005A8850, "m42, m46"),
    ("CollideMissile", 0x005A8890, "m45"),
    ("CollideUnitFilter", 0x005A8730, "m47"),
    ("MissDo02SubMissile", 0x005AE400, "m49"),
    ("MissileElemRoll", 0x005A8910, "m60-62, m65, m66"),
    ("MISSILE_BuildDamage", 0x005A89A0, "m63"),
    ("CallDoFunc", 0x0056D810, "m69"),
    ("MissDo03CloudMark", 0x005AE480, "m71"),
    ("MissDo05Loop", 0x005AE520, "m72"),
    ("MissHit27End", 0x005ABA00, "m73"),
    ("AreaHitUnit", 0x0056B9C0, "m74"),
    ("MissHit14AreaHitSub", 0x005AABB0, "m74"),
    ("MissCbReseedFromArg", 0x005D40F0, "m75, m85"),
    ("MissCbReseedZigzag", 0x005D4680, "m76"),
    ("MissCbReseedRoll", 0x005CD110, "m77"),
    ("MissSubNearReseed", 0x005A9820, "m78"),
    ("MissDo28Reseed", 0x005AFB80, "m79"),
    ("MissDo34Reseed", 0x005B04A0, "m80"),
    ("MissDo35Reseed", 0x005B0640, "m81"),
    ("MissHit58Reseed", 0x005ACDF0, "m85"),
    ("MissScatterAtTarget", 0x005D5BF0, "m85"),
]


def main(argv):
    depth = int(argv[argv.index("--depth") + 1]) if "--depth" in argv else 4
    A = W.asm()
    print("S2AE-ROUTES depth=%d roots=%d" % (depth, len(ROOTS)))
    for label, root, rows in ROOTS:
        seen, pool, imports, icalls, fatal = R.walk(A, root, depth)
        print("ROOT %s %08X (%s): functions=%d pool=%d imports=%d indirect=%d fatal=%d"
              % (label, root, rows, len(seen), len(pool), len(imports), icalls, len(fatal)))
        for t, (site, p) in sorted(pool.items()):
            print("  POOL %s at %08X via %s" % (R.POOL[t], site, p))
        for va, slot, e in imports:
            print("  IMPORT slot %08X at %08X in %08X" % (slot, va, e))
        direct = sorted(t for t, parent in seen.items() if parent == root)
        print("  CALLS " + " ".join("%08X" % t for t in direct))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
