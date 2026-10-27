---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0050-animation-frame-timing.md#implementation-log
  - ../../findings/anim/leads.md
  - ../../findings/anim/0001-modes-frames.md#leads-used
  - ../../findings/anim/0002-rates.md#leads-used
  - ../../findings/anim/0003-movement-gates.md#leads-used
  - ../2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md
resolution: "Reviewed 2026-10-27 (architect, lane/p50v review): accept with fixes (4). P1b-1 ruled a counting difference: A1, C1, H1, B1 to held with refinement, A2 stays contradicted, P1b-1 required with the fields that settle it; counts held 7, refined 33, contradicted 19 (9, D2R 7, 1.09 3), not covered 2; P1b-10 not conditional (Blood Raven, Hell); 28 verdicts given anchors. Phase 1b done. Plan 0050 log."
---

Review `lane/p50v`: plan 0050 Phase 1b part 2, one verdict per [anim/leads](../../findings/anim/leads.md) claim (61)
against anim/0001–0003 and the P0 data, in the findings' *Leads used* and the leads' Verdict column and § 12; the
contradicted claims written into Phase 2's *Done when* as P1b-1 … P1b-15
([entry](../2026-10-27-reverser-reverser-plan-0050-p1b-contradicted-cases.md)). Static, no Ghidra, no harness.

What to check:
- the counts (held 7, held with refinement 29, contradicted 23 = 9 + 11 `(version: D2R)` + 3 `(version: 1.09)`, not
  covered 2), with the greps of leads § 12; one verdict per Id across the three findings;
- `python3 -I tools/anim_leads_check.py code workspace/merged workspace/logs/anim/p50a-anim-scan.txt` against
  `workspace/logs/anim-leads/p50v-code.txt` (`sha256sum -c p50v-manifest.sha256` from `workspace/logs/anim-leads/`), and
  the default run still equal to `p50c-leads-check.txt`; `SUMMARY anim_leads_code tab=78 thresholds_equal=78
  table_minus_n_is_-1=76 table_minus_n_is_0=2 basin=69 basin_match=69 delay_rows=23 delay_match=23`;
- the reading behind P1b-1 (the scheduled length `⌈256 (F − S) / r⌉`, anim/0001 § 7) against the sources' one fewer,
  with Lightning (a sequence) as the one place they agree: the verdict files the record-mode formulas (A1, A2, C1, H1,
  B1) as contradicted and the table rows (C3, H3, B3) as held with refinement, the offset carried by the formula rows;
- the verdict calls that lean on other findings' `[I]` readings: M6–M8 on skills/0003's handler 19 (stats 68/69 only),
  M12/M13 on skills/0011 § 5 (Charge's start), H9 on combat/0001 § 9, A11 and D5 as not covered;
- the one objdump read (0x0062449F, `RunVelocityStat`'s real class) in M14's detail;
- the reachability of P1b-10 (a stock knockback on a player; monprop has one `knock` row) and P1b-14 (a moving factor
  below 25).

Nothing is promoted and no tag changed; `re/symbols.csv` untouched. Ledger row added with "—" usage. Not blocking
Phase 2's first sessions (Phase 1b lands before its last session batch).
