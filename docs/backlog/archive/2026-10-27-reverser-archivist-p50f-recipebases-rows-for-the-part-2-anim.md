---
from: reverser
to: archivist
date: 2026-10-27
status: done
context: []
resolution: "49 RECIPE_BASES rows added to tools/test_d2s.py, pinned to the saves of run:2026-10-27-anim-p2 (manifest ckpt2); sp-pal-chg2 and sp-ass-bos2 reuse the existing anim-pal-chg and anim-ass-bos saves (hashes equal), so no row; test_d2s.py 60 tests OK [test_d2s](../../../tools/test_d2s.py)"
---

Plan 0050 Phase 2 part 2 added recipes anim-<cls>-t<k>-gh9 and -gh10 (21 each), anim-sor-t0-gh5, -gh6, -gh7, anim-bar-t0-gh7, -gh8, anim-dru-th, anim-pal-slow (and sp-pal-chg2, sp-ass-bos2 saves). Their RECIPE_BASES rows in tools/test_d2s.py are not added; pins are the saves-2026-10-27-anim-p2/ manifest lines (workspace/logs/anim/2026-10-27-anim-p2-manifest-ckpt2.sha256). Names from tools/anim_sessions.py SAVES.
