---
from: reverser
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../findings/hirelings/experiments.md#run2026-10-27-sweep-hirelings
  - ../findings/hirelings/0001-hirelings.md#plan-0038-batch-h6f-run2026-10-27-sweep-hirelings
resolution: ""
---

Review plan 0038 batch H6f (`hirelings`; hirelings rows 1–2, 5–6, 9–10, 14–18, 20–21, 23, 25, 27–29, 31, 35–37, 23 statements; `lane/h6f`), run:2026-10-27-sweep-hirelings. 19 launches on slot 2 (15 kept, 4 development: the classic Greiz attempts), logger `tools/gdb/h6f.gdb`, checker `tools/sweep_h6f.py check`: 603 comparisons over the 15 kept logs, 0 failing, and `tools/hirelings.py check` on them 0 mismatches (`workspace/logs/h6f/check/check-final.txt` `943f181f…`; `manifest-final.sha256` and `manifest-shots.sha256` pass `sha256sum -c` from `workspace/logs/h6f/`, `dev/manifest-dev.sha256` from `workspace/logs/h6f/dev/`). Ledger: raised 12, raised in part 8, shortfall 1, reclassified 2: 23; totals against `main` `a105ae13`: static 567, harness 511, c-emu 0, blocked 429 (d-none 302), deferred 2, raised 17: 1 526. Points to look at: (1) rows 1 and 9 proposed d-none (the interaction start builds the table before any trade; reach read at 0x00572CFF); (2) the gate refusals of rows 17, 18 and 21 filed as d-none parts because the stock client's menu had no hire line (observed; which client test drops it is unfollowed); (3) row 29 left a shortfall with a d-2c proposal; (4) row 27 rests on the built state `name_unchecked`; (5) the `tools/hirelings.py` change (a hire counted by `MERC_Init`, not by `HIRE_Hire`'s `EAX`; output on the 48 logs of run:2026-10-16-hirelings byte-identical to the `main` revision's); (6) the 9 symbol raises (rule 14). Not blocking.
