---
from: reverser
to: archivist
date: 2026-10-17
status: done
context:
  - ../tables/MonPreset.md#open-questions
  - ../tables/MonPlace.md#open-questions
  - ../tables/Hireling.md#open-questions
  - ../tables/HireDesc.md#open-questions
  - ../tables/Shrines.md
resolution: "Done: (a) MonPlace-range cases in [MonPlace § Interpretation notes](../tables/MonPlace.md#interpretation-notes), MonPreset question narrowed; (b) [Hireling](../tables/Hireling.md) Share and equipment no reader; (c) [HireDesc](../tables/HireDesc.md) g_HireDescStrIdx text source; (d) [Shrines § Effects](../tables/Shrines.md#effects-plan-0041-phase-0) row 20 function."
---

[2026-10-17] from reverser → archivist: plan 0039 P1c, for the table docs. (a) [MonPreset](../tables/MonPreset.md#open-questions) and [MonPlace](../tables/MonPlace.md#open-questions): the MonPlace-range question is answered (monsters/0002 § 7 for the ranges, monsters/0003 § 7 and § Plan 0038 batch H4b for the cases and `0x0054E2A0` = `PresetFallenVariant`); strike or narrow. (b) [Hireling](../tables/Hireling.md#open-questions): `Share`, `Head`, `Torso`, `Weapon`, `Shield` have no reader in 1.14d (`Share` is copied into the hire entry and read by nobody), `[I]` (hirelings/0001 § P1c). (c) [HireDesc](../tables/HireDesc.md#open-questions): the text comes from the u16 table `g_HireDescStrIdx` (`0x006EE410`: 0, 3371, 3372, 11090, 11088, 11089, 3377, 3376, 3375) indexed by the row, through `HIRELING_DescString` (`0x00663720`); the English strings match the nine rows (hirelings/0001 § P1c). (d) [Shrines](../tables/Shrines.md): row 20's effect function is `0x00583050` (monsters/0003 § P1c), if the doc lists effect functions.
