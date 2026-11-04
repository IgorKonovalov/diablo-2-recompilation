---
from: architect
to: reverser
date: 2026-11-04
status: done
context:
  - ../../findings/archaeology/0001-switches.md
  - ../../findings/path/0003-short-planners.md
  - ../../plans/done/0062-debug-and-cut-content.md
resolution: "Done in lane/r70: the three corrections made as dated notes in archaeology/0001 and path/0003 [../findings/archaeology/0001-switches.md]. path/0003's 618/36 split is the review's, not recounted."
---

From the `lane/s69` Tier A review; the specs are already fixed. Three corrections in your findings. (1) archaeology/0001 § 5 (`-arena` row), § 7 (`-arena` row) and open question 1 call `+0x207` and `+0x209` the create message: they are offsets of the config block `g_ClientConfig` (0x00477D07 loads it). `ClientGameCreateMsg` copies the block's low word at `+0x207` to the message at `+0x25` (0x00477D33, 0x00477D3A; the message starts at `[ebp-0x30]`, 0x00477CB0) and the block's `+0x209` to the message at `+0x27` (0x00477D3E, 0x00477D44). items/economy G10 and its open question now say so. (2) archaeology/0001 § 7's State column still reads "not stated: Phase 3" for `-nosave`, the class rows, `-name`, `-ctemp` and `-arena`, and "to be checked" for `/players`: all are stated now (plan 0062 log). The review verified the "stated" cells for `-seed`, `-act`, `-txt`, `-direct` and `-gametype`; they hold. (3) path/0003 § 10's `[I]` "the range logged before the callback ... in all 654": `h1log` reads it before the callback for the 618 of `0x005C9290` only; the 36 of `0x005AC040` have no logger line and it is read at `MC1`, `MissileCreate`'s exit (that callback writes no range back). skills/missiles H1 says so. Not blocking.
