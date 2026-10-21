---
from: reverser
to: archivist
date: 2026-10-21
status: open
context:
  - ../findings/skills/0015-item.md
  - ../tables/Skills.md
  - ../tables/PetType.md
  - ../tables/Books.md
  - ../tables/Shrines.md
  - ../tables/Misc.md
resolution: ""
---

Not blocking. Plan 0046 batch `item` ([skills/0015](../findings/skills/0015-item.md)) settles code readers for these
columns; please link them from the table docs.

- [Skills](../tables/Skills.md) `ItemEffect` (`+0x16A`), `ItemTarget` (`+0x120`), `ItemTgtDo` (`+0x007` bit 5),
  `ItemCheckStart` (`+0x008` bit 1): `ITEMSKILL_Cast` refuses `ItemEffect` 0, reads **only the low byte** of
  `ItemTarget` (values 1–4 switch, any other keeps the aim), and runs `SKILLS_SrvStart(…, 1)` first with
  `ItemCheckStart` (§ 5, `[C]` as the map); handler 20 reads `ItemTgtDo` and with it makes the event's other unit the
  cast's caster and target, effect 0 (§ 6, `[C]`). The effect flag that lets `ItemEffect` replace `srvdofunc` is 1
  only from handler 20 without `ItemTgtDo` (§ 6, `[I]`).
- [Skills](../tables/Skills.md) `mana` (`+0x18A`), `lvlmana` (`+0x18C`), `minmana` (`+0x186`), `manashift`
  (`+0x188`, the byte) through `SKILLS_PayCost`: `(mana + lvlmana · max(lvl − 1, 0)) << (manashift & 31)`, raised to
  `minmana << 8` (signed), both `mana` and `lvlmana` 0 → the payment returns 0 (§ 7, `[C]` as the map; the table's
  "the payment's floor" `[I]` becomes `[C]` for the formula).
- [Skills](../tables/Skills.md) `srvmissilea` (`+0x048`) and `calc1` (`+0x138`) for do 151: the missile of the item
  Chain Lightning and the word written by `MISSDATA_SetSeedLow` (§ 4).
- [PetType](../tables/PetType.md) `unsummon` (`+0x004` bit 3): start 3 refuses a pet whose type lacks it (§ 3, `[C]`);
  `basemax` (`+0x00A`, read as s16): the limit `sub_00575900_PetLimitRefresh` gives a type no skill of the player
  raises (§ 10, `[I]`); `+0x0BC`/`+0x0C0` (zero in the file): a runtime list of the type's skills,
  `sub_0056BD90_PetLimitForSkill` reads the count and s16 ids (§ 10, `[I]`, the loader not followed).
- [Books](../tables/Books.md) `ScrollSkill` (`+0x008`) and `BookSkill` (`+0x00C`): do 113 takes an item of type 22
  whose suffix's Books row has `ScrollSkill` = the skill (no quantity test) or of type 18 with `BookSkill` = the skill
  and stat 70 above 0 (§ 4, `[C]`).
- [Shrines](../tables/Shrines.md) `Arg0`/`Arg1` of codes 19, 21, 22: 19's search radius is `Arg1` and its life loss
  `Arg0` percent (`[C]` for the radius argument, `[I]` for the loss); 21's and 22's count is `Arg0 + RNG_RangeB(Arg1 −
  Arg0)`, so **5 to 9** for the stock 5 and 10, not the `Effect` text's 5–10 (§ 8, `[C]` for the count); the count is
  of potion tries, a try with no free spot making none (`[I]`, after the boundary; `lane/p46m12` review).
- [Misc](../tables/Misc.md) `pSpell` 10 and 11: `g_ItemUseFns[10]`/`[11]` cast skill 47 at level 1 (§ 1); no stock row
  uses them (`rows.txt` `PSPELL`).
