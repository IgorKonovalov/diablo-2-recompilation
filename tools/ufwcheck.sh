#!/bin/bash
# No-root re-read of the host's ufw state before a two-client hosting session (ADR-0008's port-4000
# condition; docs/findings/multiplayer/0001-cases.md § 5). Fixed successor of the run copy
# workspace/logs/p44h-run/drivers/ufwcheck.sh (run:2026-10-20-two-clients), which always exited 0
# and whose 'Policy="ACCEPT"' pattern could not match the upper-case DEFAULT_INPUT_POLICY line.
#
# Usage: tools/ufwcheck.sh <session> <baseline.sha256> <log>
#   Appends the re-read to <log>, prints UFW-OK and exits 0 only when every test holds:
#   ufw active and enabled, DEFAULT_INPUT_POLICY="DROP", ENABLED=yes, every baseline hash OK.
#   Otherwise prints UFW-CHANGED with the failed tests and exits 1, so a driver's
#   `tools/ufwcheck.sh ... || exit 1` stops before hosting. A missing argument or file exits 2.
# UFW_DEFAULT and UFW_CONF override /etc/default/ufw and /etc/ufw/ufw.conf (for the self-test only).
set -u
if [ $# -ne 3 ]; then echo "usage: $0 <session> <baseline.sha256> <log>" >&2; exit 2; fi
SESSION=$1 BASE=$2 LOG=$3
DEF=${UFW_DEFAULT:-/etc/default/ufw} CONF=${UFW_CONF:-/etc/ufw/ufw.conf}
[ -r "$BASE" ] || { echo "ufwcheck: baseline $BASE not readable" >&2; exit 2; }
fail=()
act=$(systemctl is-active ufw 2>&1); ena=$(systemctl is-enabled ufw 2>&1)
[ "$act" = active ] || fail+=("is-active=$act")
[ "$ena" = enabled ] || fail+=("is-enabled=$ena")
pol=$(grep -E '^[[:space:]]*DEFAULT_INPUT_POLICY=' "$DEF" 2>&1 | tail -1)
[ "$pol" = 'DEFAULT_INPUT_POLICY="DROP"' ] || fail+=("policy: ${pol:-missing}")
en=$(grep -E '^[[:space:]]*ENABLED=' "$CONF" 2>&1 | tail -1)
[ "$en" = 'ENABLED=yes' ] || fail+=("ufw.conf: ${en:-missing}")
sums=$(sha256sum -c "$BASE" 2>&1); rc=$?
[ $rc -eq 0 ] || fail+=("sha256sum -c exit $rc")
{ echo "== $(date -Is) session $SESSION"; echo "is-active $act is-enabled $ena"
  echo "$pol"; echo "$en"; echo "$sums"
  if [ ${#fail[@]} -eq 0 ]; then echo "UFW-OK"; else echo "UFW-CHANGED: ${fail[*]}"; fi; } >> "$LOG"
if [ ${#fail[@]} -eq 0 ]; then echo UFW-OK; exit 0; fi
echo "UFW-CHANGED: ${fail[*]}"; exit 1
