---
from: reverser
to: archivist
date: 2026-10-17
status: done
context:
  - ../findings/items/0011-economy.md
resolution: "Done: readers from [items/0011](../findings/items/0011-economy.md) in Books (pSpell s32 in the layout), ItemStatCost § Price, MagicPrefix/MagicSuffix, Npc § Multipliers, ItemTypes, Weapons/Armor/Misc § Economy, UniqueItems/SetItems § Price, Skills § Charge cost columns."
---

plan 0043 Phase 1 readers for the table docs (after the architect's review), from [items/0011](../findings/items/0011-economy.md): Books: `CostPerCharge` (`+0x14`, 32-bit) and the Misc `cost` make the tome price, `BaseCost` (`+0x10`) has no reader, `pSpell` `+0x04` is read 32-bit signed, `SpellIcon` `+0x02` as a byte, the codes by the code match at 0x005C2540; ItemStatCost `Divide` is never read in the price path, `ValShift` shifts first, `Encode` 1–3 switch to the Skills costs; MagicPrefix/MagicSuffix `divide` never read; Npc `sell mult` scales the player's buy price, `max buy` caps the sell value per difficulty; ItemTypes `Repair` read on the item's own type, `StaffMods` (7 skips), `Class` < 7 quarters the sale; Weapons/Armor/Misc `gamble cost` only for `rin`/`amu` and version-0 items, `minac`/`maxac` scale armour prices; UniqueItems/SetItems `cost mult`/`cost add` as `P·m/1024 + add`; Skills `cost mult`/`cost add`/`reqlevel` in the staff-mod, stat and recharge terms. Each `[L]` meaning can link the finding's section.
