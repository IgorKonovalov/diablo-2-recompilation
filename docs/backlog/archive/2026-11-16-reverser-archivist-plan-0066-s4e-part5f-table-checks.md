---
from: reverser
to: archivist
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../findings/items/0013-grids-belts-stacks.md
  - ../../findings/stats/0001-aggregate.md
resolution: "All four checks run 2026-11-17. (1) CubeMain: quality token tmp in rows 142-145 only, all disabled; no enabled row gives quality 9 [../tables/CubeMain.md]. (2) Rows 338/339: 0 units in all 2274 DS1 files, in no ObjGroup row, and no 338/339 dword in 8 KB of Game.exe data from 0x00731EA0 [../tables/Objects.md]. (3) Skills 127-129: no Hireling or MonStats skill cell and no aura property names them; only two uniqueitems skill-property cells (Bloodtree Stump par6 129, Bloodletter par7 127) [../tables/Skills.md]. (4) The 36 /time codes: only ac/time, on magicsuffix of Dawn and of Sunlight, spawnable blank [../tables/Properties.md]. The findings' rows (items/0013 87 and 17, stats/aggregate 40 and 15) stay with their owners to raise."
---

Plan 0066 batch S4e closed with these rows "not settled; stays `[I]`" for want of table checks the reverser lane
does not own. Not blocking. Each answer lets a later sweep raise the row (inventory files under
`docs/plans/0066-inventory/`).

1. **items/inventory 87** (no stock path makes quality 9): which stock CubeMain rows, if any, give an output whose
   quality byte (the output block's `+0x06`, read at 0x00565EB6) is 9, and whether those rows are enabled.
2. **items/inventory 17** (types `0x152`, `0x153`): where objects.txt rows 338 (Guild Vault) and 339 (Trophy Case) can
   be placed: the DS1 object presets that map to them (through obj.txt) and the level population tables
   (ObjGroup, the `OBJPOP_*` lists at 0x00731EA0). `tools/ds1.py units` gives ranges only.
3. **stats/aggregate 40** (skills 127–129 and the `aura` bit): whether any stock row gives a hireling (Hireling.txt
   skill columns), a monster or summon (MonStats skill columns) or an item aura property (affix, unique, set and
   runeword tables) one of skills 127, 128, 129.
4. **stats/aggregate 15** (op 6/7 stats): that the 36 rows with an op-6/7 (`…/time`) property sit only on *of Dawn*
   and *of Sunlight*, both with `spawnable` 0.
