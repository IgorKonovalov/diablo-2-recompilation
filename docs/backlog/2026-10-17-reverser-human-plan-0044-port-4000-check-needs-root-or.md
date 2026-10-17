---
from: reverser
to: human
date: 2026-10-17
status: open
context:
  - ../findings/multiplayer/0001-cases.md#5-the-hosts-binding-and-the-port-4000-precondition
  - ../plans/0044-multiplayer-branches.md#implementation-log
resolution: ""
---

Plan 0044 Phase 2 cannot start a hosting session until the run record shows TCP 4000 unreachable from outside loopback (your condition on ADR-0008). The ufw configuration already drops it (active, default input DROP, no 4000 rule, `lo` accepted first), but the loaded ruleset needs root to list, and the lane has none. Once, before the Phase 2 run's first hosting session, either (1) run `sudo ufw status verbose` and give the lane its output (it must show `Status: active`, `Default: deny (incoming)` and no ALLOW IN rule covering 4000/tcp), or (2) if it does not show that, run `sudo ufw deny proto tcp from any to any port 4000` and give the lane the output. Nothing else is asked: no probe, no second machine. The lane re-checks the ufw files' hashes without root before each later session and comes back only if they changed. Nothing was changed. Details: [multiplayer/0001 § 5](../findings/multiplayer/0001-cases.md#5-the-hosts-binding-and-the-port-4000-precondition). (Reworded at the architect's Phase 1 review, 2026-10-17: the probe option and the reboot repeat were dropped, and the nft listing is not needed.)
