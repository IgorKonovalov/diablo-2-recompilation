---
from: reverser
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../findings/save/experiments.md#run2026-10-27-sweep-d2s-play
  - ../findings/save/0001-d2s-io.md#plan-0038-batch-h1b-run2026-10-27-sweep-d2s-play
  - ../findings/hirelings/0001-hirelings.md#plan-0038-batch-h1b-run2026-10-27-sweep-d2s-play
resolution: ""
---

Review plan 0038 batch H1b (`d2s-play`; save-d2s rows 1–4, 6, 18, 19, 21, 25, 31, 33–35, 37, 39–43, 48, 55–57, 60, 72,
73, 77, 78, 83, 88, 102, 108, 110–118, 124, 125, 127 and hirelings 24; `lane/h1b`), run:2026-10-27-sweep-d2s-play.
13 kept sessions on slot 1 (expansion; Normal, Hell, one TCP/IP host; agent-driven), four development logs in `dev/`;
no log has `internal-error:`. Manifests `workspace/logs/h1b/h1b-manifest-r2.sha256` (13 logs, `check/sweep-h1b-check-r2.txt`,
the seven input saves; supersedes `h1b-manifest.sha256`, kept) and `h1b-manifest-dev.sha256`, all `sha256sum -c` from
`workspace/logs/h1b`. Check: `systemd-run -q --user --scope -p MemoryMax=4G python3 -I tools/sweep_h1b.py check
workspace/merged/data/global/excel $(ls workspace/logs/h1b/*.log)` → 2 798 comparisons, 0 failing.

Ledger of the 48 statements: **raised 25, raised in part 14, shortfall 7, proposed d-none 2** (inventory § 2.6 H1b block).

Points for the ruling:
- (a) **Two logger revisions.** Revision 1 (not kept as a file; the record gives it as revision 2 less `h1b_full`, the
  `full` key of `RIST`/`SBX`, `h1b_wskl` and its four breakpoints) logged dead, tcpip, shut, hell-r3, hire, qr, qrh and
  rw. Only rw lost a check a row needs (row 88's write half); rw-r2 was rerun under revision 2 at the resume. The
  property rows (102's stats, 125, 127, 83's 356) rest on the four revision-2 logs that hold such items (rt-r2, qr-r2,
  qrh-r2, drop); no in-part remainder depends on the revision. Whether the seven are acceptable as they stand is the
  review's call.
- (b) **The d2sio mismatches in the check** are explained, not failures: rt-r2's four mouse words (d2sio reads player
  data `+0x74`/`+0x70`, the writer the unit's current skill, `0x00620190`/`0x006201D0`, compared by the `WSKL` group) and
  hell-r3's `RITEM` count (25 = 14 + 11 `ItemCopy` recreations at the death). A d2sio model fix for the first is not
  filed; say if it should be.
- (c) **Row 110 shortfall:** the write watchpoint on drop 27's flags armed and logged no hit, though the bit was cleared
  (`B13C`); it is not a control, so nothing is claimed from it.
- (d) **Rows 77 and 78 → d-none** by their own route (no mode 3/5 item record in the run).
- (e) **Row 56 raised** on the all-zero header (hire read 1: `MRX` eax 0, then `D2S_ReadMercItems` and the rest of the
  load run; at 0x0056B32D the return goes into the items call with no error branch).
- (f) **Rule 14:** the six symbols I → C as named in the plan log. `UnitFrameReset`, `ActUnitsFrameReset`,
  `ITEMS_SetFlag` and `ItemCopy` are met as call sites with logged returns-to, not compared returns, so left I.
- (g) **The relayed ledger did not sum:** the rotation note's figures as relayed (28 / 16 / 7 / 2) total 53; the row
  list in the note recounts to 25 / 14 / 7 / 2 = 48, as filed. The note's "three drops" was five.
- (h) **`tools/test_d2s.py`:** the H1b recipe pins (`h1bsor`, `h1bdead`, `h1bweak`, `h1bhire`, `questrewards`,
  `questrewardsh`) pass; two tests fail on `main` too, from other lanes' mp recipes, not touched here:
  `test_every_recipe_has_a_base` and `test_mp_saves_check`.
- (i) **Totals** against `main` `e88e8e2` after merging it: static 567, harness 523, c-emu 0, blocked 417 (d-none 291),
  deferred 2, raised 17: 1 526 (the two proposed moves).

Filed with it: archivist entry `2026-10-27-reverser-archivist-h1b-d2s-build-test-state-keys-for-a.md` (rows 124 and
48's builder refusals); spec-writer entry `2026-10-27-reverser-spec-writer-h1b-save-d2s-and-hirelings-raises.md` (to be
released with the review). Not blocking.
