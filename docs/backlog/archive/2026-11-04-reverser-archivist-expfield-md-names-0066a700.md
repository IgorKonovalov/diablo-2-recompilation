---
from: reverser
to: archivist
date: 2026-11-04
status: done
context:
  - ../../formats/expfield.md
  - ../../findings/items/0014-ground-items.md
resolution: "Done on lane/a70: formats/expfield.md names sub_0066A700_FieldLoadFile and its one direct caller DATATBLS_LoadAll at 0x00619462 [I] as items/0014 tags them; the caller question is no longer open, whether anything else opens the file by name stays [L] [expfield](../../formats/expfield.md)."
---

From lane/r70. The function at 0x0066A700 is named sub_0066A700_FieldLoadFile in re/symbols.csv (I): it formats DATA\GLOBAL\expfield.d2, reads it through 0x00517079 and calls sub_0066A2B0_FieldLoad; one direct caller, DATATBLS_LoadAll at 0x00619462, and no other reference to the address in the image (tools/xrefscan.py, one hit). formats/expfield.md line 20 says 'no symbol row yet' and line 68 '[L] Who calls 0x0066A700 ... not followed': both are answered in items/0014 Functions. Not blocking.
