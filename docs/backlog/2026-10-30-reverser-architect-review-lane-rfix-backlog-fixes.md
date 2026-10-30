---
from: reverser
to: architect
date: 2026-10-30
status: open
context:
  - ../findings/ai/0001-machinery.md
  - ../findings/ai/0003-pool-b.md
  - ../findings/player/0001-creation.md
resolution: ""
---

Review request, lane/rfix (static, objdump only; main 00b6e760 merged). Five reverser entries worked off, each closed in archive/:
1. ai-0001-frame-corrections: ai/0001 § 1 and § 11 dated correction notes, tags [I] kept; every call site re-read with objdump (0x0052D8DF-0x0052D907, 0x0052FD19, 0x00564603, 0x00564C97; xrefscan 0x00564C70: 0 hits; 0x0064C42D, 0x0064C432). frame/0001 unchanged.
2. ai-0001-state-rows-reusing-a-first-table: ai/0001 § 3 reworded (five reuse; 10 and 17 share 0x005E8020, dword hits 0x0073D400 and 0x0073D470 only).
3. ai-0003-vampire-flee-velocity-guard: confirmed, signed s16 test at 0x005F4BC0-0x005F4BC9, parameter 0 otherwise, signed idiv, clamp by setle/sub/and; one override call in the function (0x005F4BF8). Added to ai/0003 § 2.12 as a dated refinement [I]. Archivist entry filed to drop MonStats.md's 'not in § 2.12' note.
4. s38p-review-player-0001-counts-and-s3b-clamp: player/0001 H6g rows 3/30 read five deaths, four cases (DG0 recounted from the kept h6g logs: 1+1+1+2); S3b row 21 [C] narrowed to classes 0..6, clamp [I]; Open questions annotated (XP_PartyShare still not run).
5. light-radius-server-readers: answered [I], none found server-side. New tools/light_radius_scan.py (objdump-driven, read-only); output workspace/logs/rfix/light-radius-scan.txt with manifest-rfix.txt (sha256 3cb99dbe...). Scope: immediate stat ids at the ten stat getters (1 418 calls, 1 203 immediate, none 89; 215 register ids unresolved), every 0x59 immediate (39, none a stat read), every +0x12f] displacement (4: one item lightradius reader, three Missiles Holy), state 146 tests via UNIT_HasState/HasStateFlag (6). Light radius column reader sub_0063EBD0 feeds client code only; the server's one visibility term is state 146 invis in AiHostileCandidate. Written in ai/0001 § 6 and the Answer summary.
Symbols: 1 new row, sub_0063EBD0_MonComponentLightRadius, I. Ledger usage row appended (tokens 0, unknown). Things to check: whether the 215 register-id getter calls need resolving before the 'none found' stands for the spec, and the § 6 scope wording.
