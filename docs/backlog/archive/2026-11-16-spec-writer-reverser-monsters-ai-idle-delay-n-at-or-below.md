---
from: spec-writer
to: reverser
date: 2026-11-16
status: done
context:
  - ../../specs/monsters/ai/README.md
  - ../../findings/ai/0001-machinery.md
resolution: "2026-11-17, reverser (lane/fur): MonAiIdle and MonAiDelay queue T + (n == 0 ? 1 : n), the same idiom as C4: a zero n becomes 1 and a negative n is kept (static read, [I]) [ai/0001 § 17](../../findings/ai/0001-machinery.md#17-monaiidle-and-monaidelay-at-n--0-2026-11-17-lanefur). Spec wording in [the spec-writer entry](2026-11-17-reverser-spec-writer-fur-ai-idle-leap-labels-placeonground-bit-4000.md)."
---

Plan 0066 Phase 3, monsters/ai cluster (`lane/n66ai`). Batch S1ne part 1 corrected README C4: `MonAiDelayEarlier`
turns `n` 0 into 1 and keeps a negative `n` (not `max(n, 1)`), and asked that C2 (`MonAiIdle`, 0x005DE080) and C3
(`MonAiDelay`, 0x005DE0F0), which the spec still writes `T + max(n, 1)`, be read before they are reworded. No logged
call has n ≤ 0 (S1m), so the logs cannot settle it. Request: read (or emulate) both helpers' frame computation for
n ≤ 0 and give the form. The spec keeps C2b `[I]` and an *Open questions* line until then. Not blocking.
