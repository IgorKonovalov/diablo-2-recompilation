---
from: reverser
to: architect
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../plans/0066-inventory/README.md
  - ../../findings/items/experiments.md
resolution: "Tier B check: accept with fixes (4); merged to main 2026-11-16."
---

Tier B review of plan 0066 batch S4e (`lane/n66z`, parts 1–5f, all on 2026-11-16), now closed. Blocking the
re-tag of the S4e rows (the spec-writer entries for parts 1–5f wait on it). Branch `lane/n66z`; `main` `31a4949c`
merged; gate green.

**Where:** the plan log entries "Phase 1, batch S4e part 1" to "part 5f" in
[plan 0066](../../plans/done/0066-simulation-inferred-claims-sweep.md) (part 5f's entry holds the batch summary), the run
record `run:2026-11-16-sweep2-s4e-emu` (parts 1–5f) in
[items/experiments](../../findings/items/experiments.md), the inventory files `items-economy`, `items-use`,
`items-inventory`, `stats-aggregate`, `stats-states` under `docs/plans/0066-inventory/`. Tools
`tools/stats_s4e_emu.py`, `tools/items_s4e_emu.py`, `tools/items_s4e3_emu.py` to `items_s4e10_emu.py`; runs
`workspace/logs/n66z/s4e/run/` to `run10/`, each with a passing manifest.

**Rows by outcome.** The 91 listed rows: raised 58; raised in part 25 (remainders: 18 routed to b without a move, 1
to d-none, 6 not settled and kept in class: economy 34, 85, inventory 17, 87, aggregate 15, 18); contradicted in part
2 (economy 46, aggregate 20); moved to b 6 (economy 8, 56 → H4b; use 54 → H4c; inventory 20, 57, 63 → H4d). The 16
S4c/S4d remainder rows: raised 8 (aggregate 11, 13, 16, 17, 23, 36, 37; states 14), raised in part 5 (aggregate 2,
10, 29, 31, 41), not settled 1 (aggregate 40), moved to b 1 (states 46 → H4e), routed to b without a move 1
(inventory 61 → H4d).

**Class moves:** 7 (c-emu → b: economy 8, 56; use 54; inventory 20, 57, 63; c → b: states 46), each under ruling R2
with the call named in its row. Totals after part 5f: a-logs 623, a-run 334, b 514, c 389, c-emu 438, d-2c 59,
d-owner 68, d-edit 23, d-none 178 = 2 626.

**Controls and mismatches:** parts 1–5e 100 685 emulated cases, 0 mismatches, 0 stops, 0 undeclared reads, no traced
write; 195 controls, each separating, `passed` 0. Part 5f: no emulation, 100 objdump pins, all ok. No symbol raised
in S4e (emulations over declared images and objdump readings, review-fixes 14).

**Backlog filed:** spec-writer corrections (parts 1, 2) and refinements (parts 3, 4, 5a–5f), 10 entries;
archivist `2026-11-16-reverser-archivist-plan-0066-s4e-part5f-table-checks` (the table checks four not-settled rows
need).

**Judgment calls to rule on:**
1. Part 3's first full-size pass (which found `GameFindUnit`'s type-5 list by a model mismatch) was overwritten in
   `run3/` by the kept run and is not kept (against review-fixes 6); `dev3/` holds only the 300-case pass.
2. Part 5d's scratch-script mishap: an older lane's row script under the name first used ran once and re-applied part
   5c's Route text; the two inventory files were restored from the index before part 5d's rows were applied, and
   part 5e spot-checked them against part 5c's commit (only part 5d's appends differ).
3. Part 5f's three development passes of `static`/`xref` were overwritten in `run10/` (static outputs, regenerable,
   none cited).
4. The static raises of parts 5d–5f (objdump beside an existing Ghidra reading, the S4c/S4d practice) on rows filed
   a-logs or c-emu whose remainders S4d routed "→ c".
5. States 46 (a c row) moved to b under R2 because settling it needs the release path run; aggregate 41 (a-logs)
   routed to H4e without a move. Is R2 the right ground for the first, and should the second move too?
6. Four part-2 remainders (economy 46's caller half, 85; aggregate 15, 18) were dropped by the part-5 resume notes
   and only found by part 5f's scan of all S4e Route text; 46's was raised, the others closed "not settled".
7. Part 5e's `req` family drives only the level requirement's quality-default path (stated under *Not covered*), and
   aggregate 23's node fill after the allocator is one objdump reading, kept `[I]`.
8. Inventory 87: part 5f pinned a code path that writes quality 9 (`RecipeOutputCreate`, 0x00565EE5), so the claim
   now rests on data (CubeMain) as well as the unread writers; kept `[I]`.
