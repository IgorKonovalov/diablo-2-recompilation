#!/usr/bin/env node
// PreToolUse hook: run the docs gate (fast tier) before a commit that touches
// docs/ or re/, and deny the commit when the gate is red.
//
// Rationale: ADR-0006 makes the fast tier of tools/gate.py the mechanical part
// of every docs review. Running it at commit time catches a broken anchor, tag
// count or link before it lands, in whatever worktree is being committed.
// See CLAUDE.md -> "Commit hygiene" and docs/plans/0007-docs-gate.md Phase 3.
//
// Wired up in .claude/settings.json under hooks.PreToolUse with matcher
// "Bash". The matcher only filters by tool name; this script decides whether to
// run the gate (see the pass-through early returns below).
//
// Repository root: the `git -C <dir>` path when given, else the hook input's
// cwd, else $CLAUDE_PROJECT_DIR, resolved with `git rev-parse --show-toplevel`.
// Paths considered: the staged paths, plus the paths of any `git add` in the
// same command line (not staged yet when the hook fires), plus modified tracked
// paths for `git commit -a`. The gate runs only if one is under docs/ or re/.
//
// A broken gate never blocks work: gate.py missing in that root (an older
// branch) passes silently; python missing, a timeout or an unexpected exit code
// passes with a one-line warning on stderr.

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

// Minimal shell tokenizer: words, quotes, and the separators && || ; | newline.
// Good enough for the command lines agents write; anything odd just yields
// extra words, which at worst runs the gate when it was not needed.
function tokenize(s) {
  const toks = [];
  let cur = null;
  let i = 0;
  const flush = () => {
    if (cur !== null) toks.push({ w: cur });
    cur = null;
  };
  while (i < s.length) {
    const c = s[i];
    if (c === "'" ) {
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
    } else if (/\s/.test(c) && c !== "\n") {
      flush();
      i++;
    } else if (c === "\n" || c === ";" || c === "|" || c === "&") {
      flush();
      if ((c === "&" || c === "|") && s[i + 1] === c) i++;
      toks.push({ sep: true });
      i++;
    } else {
      cur = (cur || "") + c;
      i++;
    }
  }
  flush();
  return toks;
}

// Split into simple commands, then pick out the git invocations.
const commands = [[]];
for (const t of tokenize(cmd)) {
  if (t.sep) commands.push([]);
  else commands[commands.length - 1].push(t.w);
}

// Parse `git [-C dir] [-c k=v] [--opt] <sub> args…`; skip leading env assignments.
function parseGit(words) {
  let k = 0;
  while (k < words.length && /^[A-Za-z_][A-Za-z0-9_]*=/.test(words[k])) k++;
  if (words[k] !== "git") return null;
  k++;
  let dir = null;
  while (k < words.length && words[k].startsWith("-")) {
    const w = words[k];
    if (w === "-C") {
      dir = dir ? path.resolve(dir, words[k + 1] || ".") : words[k + 1] || ".";
      k += 2;
    } else if (w === "-c" || w === "--git-dir" || w === "--work-tree" || w === "--namespace") {
      k += 2;
    } else k++;
  }
  return { dir, sub: words[k], args: words.slice(k + 1) };
}

const gits = commands.map(parseGit).filter(Boolean);
const commits = gits.filter((g) => g.sub === "commit");
if (commits.length === 0) pass();

const baseCwd = input.cwd || process.env.CLAUDE_PROJECT_DIR || process.cwd();

function git(dir, args) {
  const r = spawnSync("git", ["-C", dir, ...args], { encoding: "utf8", timeout: 10000 });
  if (r.error || r.status !== 0) return null;
  return r.stdout;
}

const commit = commits[0];
const commitDir = commit.dir ? path.resolve(baseCwd, commit.dir) : baseCwd;
const top = git(commitDir, ["rev-parse", "--show-toplevel"]);
if (top === null) pass(); // not a git repo: let git report it
const root = top.trim();

const paths = new Set();
const addLines = (out) => {
  if (out) for (const p of out.split("\n")) if (p) paths.add(p);
};
addLines(git(root, ["diff", "--cached", "--name-only"]));

// `git commit -a` / `-am` / `--all` also commits modified tracked files.
if (commit.args.some((a) => a === "--all" || /^-[A-Za-z]*a[A-Za-z]*$/.test(a))) {
  addLines(git(root, ["diff", "--name-only"]));
}
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
    paths.add(path.relative(root, abs).split(path.sep).join("/"));
  }
}
for (const g of gits) {
  const dir = g.dir ? path.resolve(baseCwd, g.dir) : baseCwd;
  if (g.sub === "add") addArgPaths(dir, g.args, ["--chmod", "--pathspec-from-file"]);
}
// Commit pathspecs only when no message-bearing flag swallows them as values.
addArgPaths(
  commitDir,
  commit.args,
  ["-m", "--message", "-F", "--file", "-C", "-c", "--reuse-message", "--reedit-message",
   "--author", "--date", "-t", "--template", "--fixup", "--squash", "--cleanup", "-S"],
);

const touchesDocs = [...paths].some(
  (p) => p === "docs" || p === "re" || p.startsWith("docs/") || p.startsWith("re/"),
);
if (!touchesDocs) pass();

const gate = path.join(root, "tools", "gate.py");
if (!existsSync(gate)) pass(); // older branch without the gate

const r = spawnSync("python3", ["-I", gate, "--no-warnings", "--root", root], {
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

// Red: carry the error lines and the summary line in the reason.
const out = r.stdout || "";
const errLines = [];
let inErrors = false;
for (const line of out.split("\n")) {
  if (line.startsWith("Errors:")) inErrors = true;
  else if (inErrors && line.startsWith("  ")) errLines.push(line.trim());
  else if (inErrors && line.trim() === "") inErrors = false;
}
const summary = out.split("\n").filter((l) => l.startsWith("gate fast tier:")).pop() || "";
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
        (summary ? `\n${summary}` : ""),
    },
  }),
);
process.exit(0);
