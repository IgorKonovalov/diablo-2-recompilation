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

Plan 0044 Phase 2 cannot start a hosting session until the run record shows TCP 4000 unreachable from outside loopback (your condition on ADR-0008). The ufw configuration already drops it (active, default input DROP, no 4000 rule, `lo` accepted first), but the loaded ruleset needs root to list, and the lane has none. One of these is needed before the first session, and after any reboot: (1) paste the output of `sudo ufw status verbose` (and `sudo nft list ruleset | grep -n 4000`) into the run record; or (2) approve a probe from a container on the Docker bridge (or another LAN host) to 172.17.0.1:4000 and 192.168.0.12:4000 against a stand-in listener on 0.0.0.0:4000 (this session's permission check refused the lane's look into a local image); or (3) add `sudo ufw deny proto tcp from any to any port 4000` yourself. Nothing was changed. Details: [multiplayer/0001 § 5](../findings/multiplayer/0001-cases.md#5-the-hosts-binding-and-the-port-4000-precondition).
