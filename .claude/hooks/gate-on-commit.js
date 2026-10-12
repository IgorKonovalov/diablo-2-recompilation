#!/usr/bin/env node
// PreToolUse hook: run the docs gate (fast tier) before a commit that touches
// docs/ or re/, and deny the commit when the gate is red.
//
// Rationale: ADR-0006 makes the fast tier of tools/gate.py the mechanical part
// of every docs review. Running it at commit time catches a broken anchor, tag
// count or link before it lands, in whatever worktree is being committed.
// See CLAUDE.md -> "Commit hygiene" and docs/plans/done/0007-docs-gate.md Phase 3.
//
// Wired up in .claude/settings.json under hooks.PreToolUse with matcher
// "Bash". The matcher only filters by tool name; this script decides whether to
// run the gate (see the pass-through early returns below).
//
// Repository root: the `git -C <dir>` path when given, else the hook input's
// cwd, else $CLAUDE_PROJECT_DIR, resolved with `git rev-parse --show-toplevel`.
// A `cd <dir>` earlier on the same command line moves that cwd, for the commit
// root and for the `git add` paths alike.
// Paths considered: the staged paths, plus the paths of any `git add` in the
// same command line (not staged yet when the hook fires), plus modified tracked
// paths for `git commit -a` and `git add -u`/`-A`. The gate runs only if one
// is under docs/ or re/.
//
// What the gate checks: the git index (`gate.py --staged`), with the not-yet-
// staged paths above overlaid from the working tree (`--also`), so it sees what
// the commit will contain and not another lane's uncommitted edits. A gate.py
// without `--staged` (an older branch) is run on the working tree as before.
//
// A broken gate never blocks work: gate.py missing in that root (an older
// branch) passes silently; python missing, a timeout, a crash (exit 1 without
// the summary line) or an unexpected exit code passes with a one-line warning
// on stderr.

const { readFileSync, existsSync } = require("fs");
const { spawnSync } = require("child_process");
const path = require("path");

const GATE_TIMEOUT_MS = 20000;

function pass() {
  process.stdout.write("{}");
  process.exit(0);
}

function warn(msg) {
  process.stderr.write(`gate-on-commit: ${msg}; commit allowed without the docs gate\n`);
  pass();
}

let input;
try {
  input = JSON.parse(readFileSync(0, "utf8"));
} catch (e) {
  pass();
}
const cmd = (input.tool_input && input.tool_input.command) || "";

// Cheap pre-filter before any tokenizing.
if (!/\bgit\b[^\n]*\bcommit\b/.test(cmd)) pass();

// Simple commands come from the push hook's splitter: heredoc bodies dropped,
// split on separators outside quotes, `bash -c "…"` wrappers unwrapped. So a
// commit message body that mentions `git add docs/…` is never read as a command.
const { simpleCommands } = require(path.join(__dirname, "block-push-and-history-rewrite.js"));

// Word tokenizer for one simple command: quotes and backslashes. Stops at a
// leftover redirection-ish separator (`2>&1`), which carries no paths we need.
function words(s) {
  const out = [];
  let cur = null;
  let i = 0;
  while (i < s.length) {
    const c = s[i];
    if (c === "'") {
      const j = s.indexOf("'", i + 1);
      const end = j < 0 ? s.length : j;
      cur = (cur || "") + s.slice(i + 1, end);
      i = end + 1;
    } else if (c === '"') {
      let j = i + 1;
      let buf = "";
      while (j < s.length && s[j] !== '"') {
        if (s[j] === "\\" && j + 1 < s.length) {
          buf += s[j + 1];
          j += 2;
        } else buf += s[j++];
      }
      cur = (cur || "") + buf;
      i = j + 1;
    } else if (c === "\\" && i + 1 < s.length) {
      cur = (cur || "") + s[i + 1];
      i += 2;
    } else if (/\s/.test(c)) {
      if (cur !== null) out.push(cur);
      cur = null;
      i++;
    } else if (c === "&" || c === "|" || c === ";") {
      break;
    } else {
      cur = (cur || "") + c;
      i++;
    }
  }
  if (cur !== null) out.push(cur);
  return out;
}

// Parse `git [-C dir] [-c k=v] [--opt] <sub> args…`; skip leading env assignments.
function parseGit(w) {
  let k = 0;
  while (k < w.length && /^[A-Za-z_][A-Za-z0-9_]*=/.test(w[k])) k++;
  if (w[k] !== "git" && w[k] !== "git.exe") return null;
  k++;
  const dirs = []; // repeated -C options apply in order
  while (k < w.length && w[k].startsWith("-")) {
    const x = w[k];
    if (x === "-C") {
      dirs.push(w[k + 1] || ".");
      k += 2;
    } else if (x === "-c" || x === "--git-dir" || x === "--work-tree" || x === "--namespace") {
      k += 2;
    } else k++;
  }
  return { dirs, sub: w[k], args: w.slice(k + 1) };
}

// Walk the simple commands in order, tracking `cd`/`pushd` so later git
// commands (their -C, the commit root, the `git add` paths) resolve against it.
const home = process.env.HOME || "/";
let cwd = input.cwd || process.env.CLAUDE_PROJECT_DIR || process.cwd();
const gits = [];
for (const seg of simpleCommands(cmd)) {
  const w = words(seg);
  if ((w[0] === "cd" || w[0] === "pushd") && w[1] !== "-") {
    const target = (w[1] || home).replace(/^~(?=\/|$)/, home);
    cwd = path.resolve(cwd, target);
    continue;
  }
  const g = parseGit(w);
  if (g) gits.push({ sub: g.sub, args: g.args, dir: path.resolve(cwd, ...g.dirs) });
}
const commit = gits.find((g) => g.sub === "commit");
if (!commit) pass();

function git(dir, args) {
  const r = spawnSync("git", ["-C", dir, ...args], { encoding: "utf8", timeout: 10000 });
  if (r.error || r.status !== 0) return null;
  return r.stdout;
}

const top = git(commit.dir, ["rev-parse", "--show-toplevel"]);
if (top === null) pass(); // not a git repo: let git report it
const root = top.trim();

const paths = new Set();
// Paths the commit will contain that are not in the index yet: overlaid from
// the working tree with `--also`.
const pending = new Set();
const addLines = (out, into) => {
  if (out) for (const p of out.split("\n")) if (p) { paths.add(p); if (into) into.add(p); }
};
addLines(git(root, ["diff", "--cached", "--name-only"]));

// Every modified tracked path: `git commit -a`/`-am`/`--all`, and
// `git add -u`/`--update`/`-A`/`--all` earlier on the line.
const ALL_TRACKED = /^(--all|--update|-[A-Za-z]*[uA][A-Za-z]*)$/;
const addsAll =
  commit.args.some((a) => a === "--all" || /^-[A-Za-z]*a[A-Za-z]*$/.test(a)) ||
  gits.some((g) => g.sub === "add" && g.args.some((a) => ALL_TRACKED.test(a)));
if (addsAll) addLines(git(root, ["diff", "--name-only"]), pending);

// `git commit <pathspec>` commits those paths directly.
// `git add <paths>` in the same command line: not staged yet.
function addArgPaths(dir, args, valueFlags) {
  let afterDashDash = false;
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (!afterDashDash && a === "--") {
      afterDashDash = true;
      continue;
    }
    if (!afterDashDash && a.startsWith("-")) {
      // A flag that takes a value, alone or ending a short cluster (`-am msg`).
      if (valueFlags.includes(a) || (/^-[A-Za-z]{2,}$/.test(a) && valueFlags.includes("-" + a.slice(-1)))) i++;
      continue;
    }
    const abs = path.resolve(dir, a);
    const rel = path.relative(root, abs).split(path.sep).join("/");
    paths.add(rel);
    pending.add(rel);
  }
}
for (const g of gits) {
  if (g.sub === "add") addArgPaths(g.dir, g.args, ["--chmod", "--pathspec-from-file"]);
}
// Commit pathspecs only when no message-bearing flag swallows them as values.
// (`-S` is not here: it only takes an attached `-S<keyid>`.)
addArgPaths(
  commit.dir,
  commit.args,
  ["-m", "--message", "-F", "--file", "-C", "-c", "--reuse-message", "--reedit-message",
   "--author", "--date", "-t", "--template", "--fixup", "--squash", "--cleanup"],
);

const touchesDocs = [...paths].some(
  (p) => p === "docs" || p === "re" || p.startsWith("docs/") || p.startsWith("re/"),
);
if (!touchesDocs) pass();

const gate = path.join(root, "tools", "gate.py");
if (!existsSync(gate)) pass(); // older branch without the gate

const gateArgs = ["-I", gate, "--no-warnings", "--root", root];
if (readFileSync(gate, "utf8").includes('"--staged"')) {
  gateArgs.push("--staged");
  if (pending.size) gateArgs.push("--also", ...pending); // nargs="+": keep last
}
const r = spawnSync("python3", gateArgs, {
  encoding: "utf8",
  timeout: GATE_TIMEOUT_MS,
  cwd: root,
});
if (r.error) {
  if (r.error.code === "ETIMEDOUT") warn(`tools/gate.py timed out after ${GATE_TIMEOUT_MS / 1000} s`);
  warn(`could not run python3 (${r.error.code || r.error.message})`);
}
if (r.status === 0) pass();
if (r.status !== 1) warn(`tools/gate.py exited ${r.status === null ? r.signal : r.status}`);

// Exit 1 without the summary line is a crash (a Python traceback also exits 1),
// not a red gate: fail open.
const out = r.stdout || "";
const summary = out.split("\n").filter((l) => l.startsWith("gate fast tier:")).pop() || "";
if (!summary) {
  const last = (r.stderr || "").trim().split("\n").pop() || "no output";
  warn(`tools/gate.py crashed (${last})`);
}

// Red: carry the error lines and the summary line in the reason.
const errLines = [];
let inErrors = false;
for (const line of out.split("\n")) {
  if (line.startsWith("Errors:")) inErrors = true;
  else if (inErrors && line.startsWith("  ")) errLines.push(line.trim());
  else if (inErrors && line.trim() === "") inErrors = false;
}
const MAX = 40;
const shown = errLines.slice(0, MAX);
if (errLines.length > MAX) shown.push(`… and ${errLines.length - MAX} more`);

process.stdout.write(
  JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason:
        `Docs gate is red in ${root} (python3 -I tools/gate.py --no-warnings). ` +
        `Fix these before committing changes under docs/ or re/ (ADR-0006):\n` +
        (shown.length ? shown.join("\n") : out.trim()) +
        `\n${summary}`,
    },
  }),
);
process.exit(0);
