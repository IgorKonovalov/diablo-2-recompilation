---
from: reverser
to: archivist
date: 2026-10-30
status: done
context:
  - ../../findings/ai/0006-summons.md
resolution: "MonStats aip8, SkillDamage and the Skills Param2, calc4, aitype, aibonus readers of ai/0006 linked from tables/MonStats.md and tables/Skills.md with the finding's tags [tables/MonStats.md](../../tables/MonStats.md)"
---

Link the readers found by [ai/0006](../../findings/ai/0006-summons.md) from the table docs: MonStats aip8 (rows 105 ShadowWarrior and 106/143 ShadowMaster read its three cells at fixed offsets as three parameters, aip8[n] a Skills row id whose owner level the init keeps, aip8[m]/aip8[h] the bounds of row 105's counter; § 2.10, § 2.11, [I]); MonStats SkillDamage (+0xA8: MonOwnerSkillDamage reads it for a summon with an owner and evaluates PhysMin, PhysMax and ToHit at the owner's level in that skill, 0 < s <= Skills count; Answer H3 bullet, [I]); Skills Param2 (+0x14C: row 84's bone wall life, v14 = T + Param2; [C] by emulation, § 2.1), Skills calc4 (+0x144: the sentries' shot count and the blade creeper's life; § 2.4, § 2.5, [I]), Skills aitype/aibonus (+0x230/+0x232: row 106's skill scoring; § 2.11, [I]). No column meaning changes; links only.
