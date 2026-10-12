// Parse Mermaid blocks headlessly for the docs gate (tools/gate.py, rule E9).
//
// Usage: node tools/mermaid_check.mjs --src <bundle-dir> --cache <cache-dir>  < blocks.json
//
// stdin:  {"blocks": [{"id": <any>, "text": "<block body>"}, ...]}
// stdout: one JSON line, either {"skip": "<reason>"} (no parser available: the gate warns once and
//         goes on) or {"version": "<mermaid version>", "results": [{"id", "ok", "line", "message"}]}
//         where line is the 1-based line inside the block named by the error, or null.
// Exit 0 in both cases; anything else (a crash) is treated as a skip by the gate.
//
// No download: the parser is the Mermaid build VS Code ships (markdown-language-features
// markdown-editor-out/, ES modules with hashed chunk names). It is copied to <cache-dir> (re-copied
// when the source listing changes), given a {"type":"module"} package.json, and patched so that it
// loads without a DOM: the DOMPurify instance has no addHook/sanitize outside a browser, so the
// function that registers the "data-temp-href-target" hooks gets no-op stand-ins, and every
// `<purify>.sanitize(` call falls back to the identity. Chunks and patch points are found by pattern;
// when one is missing the result is a skip, never a parse error.
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const out = (o) => process.stdout.write(JSON.stringify(o) + "\n");
const log = (...a) => process.stderr.write(a.map(String).join(" ") + "\n");

function args(argv) {
  const a = {};
  for (let i = 0; i < argv.length; i += 2) a[argv[i].replace(/^--/, "")] = argv[i + 1];
  return a;
}

function stampOf(src) {
  const names = fs.readdirSync(src).filter((n) => n.endsWith(".js")).sort();
  return names.map((n) => {
    const st = fs.statSync(path.join(src, n));
    return `${n}:${st.size}:${Math.floor(st.mtimeMs)}`;
  }).join("\n");
}

// Copy and patch src into cache unless the cache already holds this source. Returns the core
// module path, or throws Error("skip: ...").
function prepare(src, cache) {
  if (!src || !fs.existsSync(src) || !fs.statSync(src).isDirectory()) throw new Error(`skip: bundle dir not found (${src})`);
  const core = fs.readdirSync(src).filter((n) => /^mermaid\.core-[A-Za-z0-9]+\.js$/.test(n));
  if (core.length !== 1) throw new Error(`skip: ${core.length} mermaid.core-*.js files in ${src}`);
  const stamp = `${fs.realpathSync(src)}\n${stampOf(src)}`;
  const stampFile = path.join(cache, "stamp.txt");
  if (fs.existsSync(stampFile) && fs.readFileSync(stampFile, "utf8") === stamp) return path.join(cache, core[0]);

  const tmp = `${cache}.tmp-${process.pid}`;
  fs.rmSync(tmp, { recursive: true, force: true });
  fs.mkdirSync(tmp, { recursive: true });
  for (const n of fs.readdirSync(src)) if (n.endsWith(".js")) fs.copyFileSync(path.join(src, n), path.join(tmp, n));
  fs.writeFileSync(path.join(tmp, "package.json"), '{"type":"module"}\n');

  const hookRe = /function [A-Za-z_$][\w$]*\(\)\{let t="data-temp-href-target";/;
  const hits = fs.readdirSync(tmp).filter((n) => n.endsWith(".js") && hookRe.test(fs.readFileSync(path.join(tmp, n), "utf8")));
  if (hits.length !== 1) {
    fs.rmSync(tmp, { recursive: true, force: true });
    throw new Error(`skip: patch point "data-temp-href-target" found in ${hits.length} chunks`);
  }
  const f = path.join(tmp, hits[0]);
  let js = fs.readFileSync(f, "utf8");
  const purify = [...new Set([...js.matchAll(/([A-Za-z_$][\w$]*)\.sanitize\(/g)].map((m) => m[1]))];
  if (purify.length !== 1) {
    fs.rmSync(tmp, { recursive: true, force: true });
    throw new Error(`skip: ${purify.length} distinct *.sanitize( receivers in ${hits[0]}`);
  }
  const P = purify[0];
  js = js.replace(hookRe, (m) => m + `if(!${P}.addHook){${P}.addHook=()=>{};${P}.sanitize=x=>x;${P}.removeHook=()=>{};${P}.removeHooks=()=>{};}`);
  js = js.split(`${P}.sanitize(`).join(`(${P}.sanitize||(x=>x))(`);
  fs.writeFileSync(f, js);
  fs.writeFileSync(path.join(tmp, "stamp.txt"), stamp);
  // swap in atomically enough for parallel worktrees: the loser of a rename race just reuses the winner
  fs.rmSync(cache, { recursive: true, force: true });
  fs.mkdirSync(path.dirname(cache), { recursive: true });
  try {
    fs.renameSync(tmp, cache);
  } catch (e) {
    fs.rmSync(tmp, { recursive: true, force: true });
    if (!fs.existsSync(stampFile)) throw e;
  }
  return path.join(cache, core[0]);
}

async function main() {
  const a = args(process.argv.slice(2));
  const input = JSON.parse(fs.readFileSync(0, "utf8") || '{"blocks":[]}');
  let mermaid;
  try {
    const core = prepare(a.src, a.cache);
    globalThis.window = globalThis;
    globalThis.addEventListener = () => {};
    // keep stdout for the JSON result: Mermaid logs through console
    for (const k of ["log", "info", "warn", "error", "debug", "trace"]) console[k] = log;
    mermaid = (await import(pathToFileURL(core).href)).default;
    if (!mermaid || typeof mermaid.parse !== "function") throw new Error("skip: default export has no parse()");
  } catch (e) {
    out({ skip: String(e.message || e).replace(/^skip: /, "") });
    return;
  }
  const results = [];
  for (const b of input.blocks) {
    try {
      await mermaid.parse(b.text, { suppressErrors: false });
      results.push({ id: b.id, ok: true, line: null, message: "" });
    } catch (e) {
      const msg = String((e && (e.message || e.str)) || e);
      const m = /line[ :]+(\d+)/i.exec(msg);
      results.push({ id: b.id, ok: false, line: m ? Number(m[1]) : null, message: msg.split("\n").filter(Boolean).slice(0, 3).join(" | ") });
    }
  }
  out({ version: mermaid.version || null, results });
}

main().then(() => process.exit(0), (e) => { out({ skip: `helper crashed: ${e && e.message}` }); process.exit(0); });
