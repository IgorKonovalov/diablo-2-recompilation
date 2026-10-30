#!/usr/bin/env bash
# Wrapper around Ghidra's analyzeHeadless for the pinned Game.exe (Plan 0001 phase 4).
#
# Usage: tools/ghidra.sh <command> [args]
#   build                       import + auto-analyse Game.exe into workspace/ghidra/, then replay
#                               re/symbols.csv. Refuses if the project exists (use rebuild).
#   rebuild                     delete workspace/ghidra/ and build again
#   import-symbols              replay re/symbols.csv into the existing project
#   export-symbols              write user-defined symbols back to re/symbols.csv (merging tags)
#   decompile <addr|name>...    print C for the function(s) containing each address / with each name
#   xrefs <addr|name>...        references to each target, plus callees for functions
#   findstring <text>...        defined strings containing <text> (case-insensitive) and their xrefs
#   findscalar <value>...       functions whose instructions use an immediate (dec or 0x-hex)
#   findptr <addr>...           every way the image reaches an address: references of any type, VA/RVA bytes in
#                               every initialized block, immediates, raw relative branches, exports, fall-through
#                               (FindPointer.java)
#   instrat <addr-file>         per address: instruction / data / undefined, containing function
#   emu <fn addr> <cases>       emulate a __fastcall(u32 *seed, u32 edx) per case line (EmuFastcall.java)
#   emucalc <fn addr> <cases>   emulate a calc-formula function (a, b, c, ctx) per case line (EmuCalcFunc.java)
#   emucall <fn addr> <cases> <mem>  emulate any call (ecx edx args...) with a memory spec (EmuCall.java)
#   emutrace <cases> <mem>      emulate calls with per-case memory, dumps and a trace of every access outside the
#                               stack, the spec and the case memory (EmuTrace.java)
#   emuboundary <cases> <mem>   emutrace plus `observe <addr>` lines in <mem>: a case ends at that call and its
#                               registers and stack arguments are printed (EmuBoundary.java, plan 0046 batch 9a)
#   strings <addr|name>...      strings each function references (source paths tell the module)
#   decompile-range <out> <lo> <hi>
#                               C of every function with entry in [lo, hi) into <out> (slow: grep it after)
#   rngcallgraph <class-file|-> <root>...
#                               call graph under the roots; every function with an LCG step or an
#                               RNG call, matched against a classification file (RngCallGraph.java)
#   callersup <max-depth> <root:0xADDR=LABEL|0xADDR>...
#                               referrers of each target walked upward (calls and table pointers) to the declared
#                               roots; per target every root reached with a shortest path (CallersUp.java, plan 0055)
#
# Run from the repo root. Logs: workspace/logs/ghidra-build-<UTC stamp>.log (build) and
# $GHIDRA_LOG (the most recent other command; see GHIDRA_LOG below), each with a .stderr next to it. Query commands open
# the project read-only. Headless runs lock the project: never run two at once or with the GUI open.
# Env: GHIDRA_HOME (default /opt/ghidra), GHIDRA_HEADLESS_MAXMEM (default 8G), SYMBOLS_CSV (default
# re/symbols.csv; point it at a scratch copy to test a round trip), GHIDRA_PROJ_DIR (default workspace/ghidra;
# point it at a per-worktree copy of the project so parallel lanes don't share the lock), GHIDRA_LOG (log of every
# non-build command; default workspace/logs/ghidra-last.log when the project dir is named `ghidra`, else
# workspace/logs/ghidra-last-<basename of GHIDRA_PROJ_DIR>.log, so lanes on project copies never share a log).
set -euo pipefail

GHIDRA_HOME=${GHIDRA_HOME:-/opt/ghidra}
export GHIDRA_HEADLESS_MAXMEM=${GHIDRA_HEADLESS_MAXMEM:-8G}
HEADLESS="$GHIDRA_HOME/support/analyzeHeadless"
ROOT=$(cd "$(dirname "$0")/.." && pwd)
EXE="$ROOT/workspace/install/app/game.exe"
PINNED=631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf
PROJ_DIR=${GHIDRA_PROJ_DIR:-"$ROOT/workspace/ghidra"}
PROJ=d2
PROGRAM=game.exe
SCRIPTS="$ROOT/re/ghidra_scripts"
CSV=${SYMBOLS_CSV:-"$ROOT/re/symbols.csv"}
LOGS="$ROOT/workspace/logs"
if [ -z "${GHIDRA_LOG:-}" ]; then
	proj_base=$(basename "$PROJ_DIR")
	if [ "$proj_base" = ghidra ]; then
		GHIDRA_LOG="$LOGS/ghidra-last.log"
	else
		GHIDRA_LOG="$LOGS/ghidra-last-$proj_base.log"
	fi
fi

die() { echo "ghidra.sh: $*" >&2; exit 1; }
usage() { sed -n '2,/^set -euo/{/^set/!p}' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

[ -x "$HEADLESS" ] || die "analyzeHeadless not found at $HEADLESS"
mkdir -p "$LOGS"

check_pinned() {
	[ -f "$EXE" ] || die "missing $EXE"
	local h
	h=$(sha256sum "$EXE" | cut -d' ' -f1)
	[ "$h" = "$PINNED" ] || die "game.exe sha256 $h != PINNED $PINNED (docs/inventory.md); stop and tell the architect"
}

# Script println output and script errors land in the -log file (-scriptlog stays empty in 12.1).
# A failing script does not make analyzeHeadless exit non-zero, so the log is the only signal.
check_log() {
	if grep -qE 'ERROR|SCRIPT ERROR' "$1"; then
		grep -E -A3 'ERROR' "$1" | cut -c1-300 >&2
		die "Ghidra reported an error; see $1"
	fi
}

have_project() { [ -f "$PROJ_DIR/$PROJ.gpr" ]; }

build() {
	have_project && die "project exists at $PROJ_DIR (use rebuild, or import-symbols)"
	check_pinned
	mkdir -p "$PROJ_DIR"
	local stamp log
	stamp=$(date -u +%Y%m%dT%H%M%SZ)
	log="$LOGS/ghidra-build-$stamp.log"
	echo "ghidra.sh: import + analysis, log $log (this takes a while)"
	"$HEADLESS" "$PROJ_DIR" "$PROJ" \
		-import "$EXE" -processor x86:LE:32:default -cspec windows \
		-scriptPath "$SCRIPTS" -postScript ImportSymbols.java "$CSV" \
		-log "$log" >/dev/null 2>"$log.stderr"
	check_log "$log"
	grep -oE 'ImportSymbols: .*' "$log" || die "symbol replay did not run; see $log"
	echo "ghidra.sh: built $PROJ_DIR/$PROJ.gpr"
}

# run_script <readonly 0|1> <script> [args...]
run_script() {
	have_project || die "no project at $PROJ_DIR (run build)"
	local ro=() log="$GHIDRA_LOG"
	: >"$log"
	[ "$1" = 1 ] && ro=(-readOnly)
	shift
	"$HEADLESS" "$PROJ_DIR" "$PROJ" -process "$PROGRAM" -noanalysis "${ro[@]}" \
		-scriptPath "$SCRIPTS" -postScript "$@" \
		-log "$log" >/dev/null 2>"$log.stderr" \
		|| die "analyzeHeadless failed; see $log"
	check_log "$log"
}

# query <script> <targets...>: run a read-only script that writes to an out file, then print it
query() {
	local script=$1; shift
	[ $# -ge 1 ] || usage
	local out
	out=$(mktemp "$LOGS/ghidra-out.XXXXXX")
	trap 'rm -f "$out"' RETURN
	run_script 1 "$script" "$out" "$@"
	cat "$out"
}

cmd=${1:-}; shift || true
case "$cmd" in
	build) build ;;
	rebuild) rm -rf "$PROJ_DIR"; build ;;
	import-symbols)
		run_script 0 ImportSymbols.java "$CSV"
		grep -oE 'ImportSymbols: .*' "$GHIDRA_LOG" ;;
	export-symbols)
		run_script 1 ExportSymbols.java "$CSV"
		grep -oE 'ExportSymbols: .*' "$GHIDRA_LOG" ;;
	decompile) query Decompile.java "$@" ;;
	xrefs) query Xrefs.java "$@" ;;
	findstring) query FindString.java "$@" ;;
	findscalar) query FindScalar.java "$@" ;;
	findptr) query FindPointer.java "$@" ;;
	instrat) query InstrAt.java "$@" ;;
	emu) query EmuFastcall.java "$@" ;;
	emucalc) query EmuCalcFunc.java "$@" ;;
	emucall) query EmuCall.java "$@" ;;
	emutrace) query EmuTrace.java "$@" ;;
	emuboundary) query EmuBoundary.java "$@" ;;
	strings) query StringsIn.java "$@" ;;
	decompile-range)
		[ $# -eq 3 ] || usage
		run_script 1 DecompileRange.java "$@"
		grep -oE 'DecompileRange: .*' "$GHIDRA_LOG" ;;
	rngcallgraph) query RngCallGraph.java "$@" ;;
	callersup) query CallersUp.java "$@" ;;
	*) usage ;;
esac
