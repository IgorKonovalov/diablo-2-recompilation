// Draw Mermaid blocks as GitHub draws them, for the docs gate (tools/gate.py, rule E17) and
// tools/mermaid_lint.py. E9 only parses, with another Mermaid; this finds what a reader of the pushed
// page would meet: a block GitHub refuses, a layout error, an empty drawing, and label text lost on
// the way to the page (a <word> taken for an HTML tag, a node id given a second label).
//
// Usage: node tools/mermaid_render.mjs --dir <cache-dir> [--browser <path>] [--redraw 1]  < blocks.json
//
// stdin:  {"blocks": [{"id": <any>, "text": "<block body>"}, ...]}
// stdout: one JSON line, {"skip": "<reason>"} (no browser or bundle: the caller warns once and goes
//         on) or {"rendered": n, "cached": n, "results": [{"id", "ok", "message"}]}.
// Exit 0 in both cases; anything else (a crash) is treated as a skip by the caller.
//
// The two things that make this GitHub's drawing and not just any drawing:
// - MERMAID_VERSION is what GitHub's diagram frame ran on 2026-11-04 (a refused block's error text
//   prints it: "mermaid version 12.2.0"). The one file used is fetched once from the npm registry into
//   <cache-dir>, its tarball checked against MERMAID_INTEGRITY. Bump both when GitHub moves on.
// - GITHUB_DECODE: GitHub decodes HTML entities before Mermaid sees the text, so &quot; closes a
//   quoted label. Mermaid's own #quot; #lt; #gt; are what survive.
//
// The bundle runs in the system's Chromium-family browser, which may resolve nothing but the loopback
// server that hands it the page and takes back the results. Blocks that drew clean are remembered by
// sha256 of their text in <cache-dir>, stamped with the version and this script, so a commit only
// draws what changed. A failure is never remembered.
import { execFileSync, spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";

const MERMAID_VERSION = "12.2.0";
const MERMAID_INTEGRITY = "sha512-w7nr/SFrLO7BaVTs3dQTvYSV6nYSBj0Yy9DjBhsIJtAcHqRzXSq4Pg32ujHZ/AdWsAMNEvvhbm5dt9E2tOiHzw==";
const BROWSERS = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "brave", "brave-browser"];
const TIMEOUT_MS = Number(process.env.MERMAID_RENDER_TIMEOUT_MS || 240000);

const out = (o) => process.stdout.write(JSON.stringify(o) + "\n");

function args(argv) {
  const a = {};
  for (let i = 0; i < argv.length; i += 2) a[argv[i].replace(/^--/, "")] = argv[i + 1];
  return a;
}

function findBrowser() {
  for (const name of BROWSERS) {
    for (const dir of (process.env.PATH || "").split(path.delimiter)) {
      const p = path.join(dir, name);
      try {
        fs.accessSync(p, fs.constants.X_OK);
        return p;
      } catch {}
    }
  }
  return null;
}

// ---- the labels a block's source promises, to be found again in the drawing

const HTML_TAGS = /<\/?(?:a|abbr|b|big|br|code|div|em|font|i|kbd|mark|p|pre|s|small|span|strong|sub|sup|u)\b[^<>]*>/gi;
const ENTITY = { quot: '"', amp: "&", lt: "<", gt: ">", apos: "'", nbsp: " ", num: "#" };

function decode(s) {
  return s.replace(/[#&](#?)(x?)([0-9a-z]+);/gi, (m, h, x, v) => {
    if (/^\d+$/.test(v)) return String.fromCodePoint(Number(v));
    if (x && /^[0-9a-f]+$/i.test(v)) return String.fromCodePoint(parseInt(v, 16));
    return ENTITY[v.toLowerCase()] ?? m;
  });
}

// What a label reads as, letters and digits only: spacing, wrapping and punctuation are the
// renderer's business. Tags the sanitizer keeps are dropped first, so <b>x</b> expects x; any other
// <word> stays in, and if the drawing lost it the comparison says so.
function normal(s) {
  return decode(s.replace(HTML_TAGS, " ")).toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "");
}

function expectedLabels(text) {
  const lines = text.split("\n");
  let start = 0;
  if (lines[0]?.trim() === "---") {
    start = lines.indexOf("---", 1) + 1;
  }
  const body = lines.slice(start).filter((l) => l.trim() && !l.trim().startsWith("%%"));
  const kind = (body[0] || "").trim().split(/\s+/)[0];
  const labels = [];
  const skip = /^\s*(style|classDef|class|click|linkStyle|accTitle|accDescr|title)\b/;
  for (const l of body.slice(1)) {
    if (skip.test(l)) continue;
    if (kind === "flowchart" || kind === "graph" || kind.startsWith("packet") || kind.startsWith("block")) {
      for (const m of l.matchAll(/"([^"]*)"/g)) labels.push(m[1]);
      for (const m of l.matchAll(/\|([^|"]+)\|/g)) labels.push(m[1]);
    } else if (kind === "sequenceDiagram") {
      const msg = /^\s*(?:[^:]*?(?:-->>|->>|-->|->|--x|-x|--\)|-\))[+-]?[^:]*|[Nn]ote\s[^:]*):(.*)$/.exec(l);
      if (msg) labels.push(msg[1]);
    } else if (kind.startsWith("stateDiagram")) {
      const msg = /^\s*\S+\s*-->\s*\S+\s*:(.*)$/.exec(l);
      if (msg) labels.push(msg[1]);
    }
  }
  return labels.map((s) => s.trim()).filter((s) => s && !s.includes("$$"));
}

const GITHUB_DECODE = { "&quot;": '"', "&lt;": "<", "&gt;": ">", "&amp;": "&", "&apos;": "'", "&#39;": "'" };
const githubText = (text) => text.replace(/&(?:quot|lt|gt|amp|apos|#39);/g, (m) => GITHUB_DECODE[m]);

function verdict(block, r) {
  if (r.error) return `does not draw: ${r.error}`;
  if (!r.shapes || !r.width || !r.height) return `draws nothing visible (${r.shapes} shapes, ${r.width}x${r.height})`;
  const seen = normal(r.text);
  const lost = expectedLabels(githubText(block.text)).filter((s) => normal(s) && !seen.includes(normal(s)));
  if (lost.length) return `label text missing from the drawing: ${lost.slice(0, 3).map((s) => JSON.stringify(s)).join(", ")}`;
  return null;
}

// ---- the page: runs in the browser, draws one block at a time, posts everything back

const PAGE = `<!doctype html><meta charset="utf-8"><body><div id="host" style="width:1200px"></div><script src="/mermaid.js"></script><script type="module">
const report = (o) => fetch("/results", { method: "POST", body: JSON.stringify(o) });
try {
  const mermaid = globalThis.mermaid;
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict", suppressErrorRendering: true });
  const blocks = await (await fetch("/blocks")).json();
  const host = document.getElementById("host");
  const results = [];
  for (let i = 0; i < blocks.length; i++) {
    const r = { i };
    try {
      const { svg } = await mermaid.render("d" + i, blocks[i]);
      host.innerHTML = svg;
      const el = host.querySelector("svg");
      el.querySelectorAll("style").forEach((s) => s.remove());
      const box = el.getBBox();
      r.width = Math.round(box.width);
      r.height = Math.round(box.height);
      r.shapes = el.querySelectorAll("path,rect,polygon,circle,ellipse,line,text,foreignObject").length;
      r.text = el.textContent || "";
    } catch (e) {
      r.error = String((e && (e.message || e.str)) || e).split("\\n").filter(Boolean).slice(0, 3).join(" | ");
    }
    results.push(r);
    host.innerHTML = "";
    document.getElementById("d" + i)?.remove();
    document.getElementById("dd" + i)?.remove();
  }
  await report({ results });
} catch (e) {
  await report({ fatal: String(e && e.message || e) });
}
</script>`;

function drawAll(bundle, browser, blocks) {
  return new Promise((resolve, reject) => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "mermaid-render-"));
    let child = null;
    const done = (f, v) => {
      clearTimeout(timer);
      child?.kill("SIGKILL");
      server.close();
      fs.rmSync(tmp, { recursive: true, force: true });
      f(v);
    };
    const timer = setTimeout(() => done(reject, new Error(`no result in ${TIMEOUT_MS} ms`)), TIMEOUT_MS);
    const server = http.createServer((req, res) => {
      if (req.url === "/") {
        res.writeHead(200, { "content-type": "text/html" }).end(PAGE);
      } else if (req.url === "/blocks") {
        res.writeHead(200, { "content-type": "application/json" }).end(JSON.stringify(blocks.map((b) => githubText(b.text))));
      } else if (req.url === "/results" && req.method === "POST") {
        let body = "";
        req.on("data", (d) => (body += d));
        req.on("end", () => {
          res.writeHead(204).end();
          const o = JSON.parse(body);
          if (o.fatal) done(reject, new Error(o.fatal));
          else done(resolve, o);
        });
      } else if (req.url === "/mermaid.js") {
        res.writeHead(200, { "content-type": "text/javascript" }).end(fs.readFileSync(bundle));
      } else {
        res.writeHead(404).end();
      }
    });
    server.listen(0, "127.0.0.1", () => {
      const url = `http://127.0.0.1:${server.address().port}/`;
      child = spawn(browser, ["--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
        "--disable-background-networking", "--disable-sync", "--window-size=1400,1000", `--user-data-dir=${tmp}`,
        "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1", url], { stdio: "ignore" });
      child.on("error", (e) => done(reject, e));
      child.on("exit", (code) => { if (server.listening) done(reject, new Error(`browser exited with ${code} before reporting`)); });
    });
  });
}

// The bundle, fetched once. Throws on a network failure or a tarball that is not the pinned one.
async function ensureBundle(dir) {
  const file = path.join(dir, `mermaid-${MERMAID_VERSION}.min.js`);
  if (fs.existsSync(file)) return file;
  const url = `https://registry.npmjs.org/mermaid/-/mermaid-${MERMAID_VERSION}.tgz`;
  const res = await fetch(url, { signal: AbortSignal.timeout(60000) });
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  const tgz = Buffer.from(await res.arrayBuffer());
  const got = "sha512-" + crypto.createHash("sha512").update(tgz).digest("base64");
  if (got !== MERMAID_INTEGRITY) throw new Error(`${url}: integrity mismatch`);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "mermaid-bundle-"));
  try {
    fs.writeFileSync(path.join(tmp, "m.tgz"), tgz);
    execFileSync("tar", ["-xzf", "m.tgz", "package/dist/mermaid.min.js"], { cwd: tmp, stdio: "ignore" });
    fs.mkdirSync(dir, { recursive: true });
    const part = `${file}.tmp-${process.pid}`;
    fs.copyFileSync(path.join(tmp, "package/dist/mermaid.min.js"), part);
    fs.renameSync(part, file);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
  return file;
}

function readCache(file, stamp) {
  try {
    const c = JSON.parse(fs.readFileSync(file, "utf8"));
    if (c.stamp === stamp) return c;
  } catch {}
  return { stamp, ok: {} };
}

function writeCache(file, cache) {
  const tmp = `${file}.tmp-${process.pid}`;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(tmp, JSON.stringify(cache));
  fs.renameSync(tmp, file); // parallel worktrees: the last writer wins, a lost entry is drawn again
}

async function main() {
  const a = args(process.argv.slice(2));
  const input = JSON.parse(fs.readFileSync(0, "utf8") || '{"blocks":[]}');
  if (!a.dir) return out({ skip: "no cache dir" });
  let bundle;
  try {
    bundle = await ensureBundle(a.dir);
  } catch (e) {
    return out({ skip: `Mermaid ${MERMAID_VERSION} not available: ${e.message}` });
  }
  const browser = a.browser || process.env.GATE_BROWSER || findBrowser();
  if (!browser) return out({ skip: `no browser found (tried ${BROWSERS.join(", ")}; set $GATE_BROWSER)` });

  const self = crypto.createHash("sha256").update(fs.readFileSync(new URL(import.meta.url))).digest("hex");
  const stamp = `${MERMAID_VERSION}:${self}`;
  const cacheFile = path.join(a.dir, "drawn-clean.json");
  const cache = a.redraw ? { stamp, ok: {} } : readCache(cacheFile, stamp);
  const key = (b) => crypto.createHash("sha256").update(b.text).digest("hex").slice(0, 24);
  const todo = input.blocks.filter((b) => !cache.ok[key(b)]);
  const seen = new Set();
  const uniq = todo.filter((b) => !seen.has(key(b)) && seen.add(key(b)));
  const messages = new Map();
  if (uniq.length) {
    let res;
    try {
      res = await drawAll(bundle, browser, uniq);
    } catch (e) {
      return out({ skip: `browser run failed: ${e.message}` });
    }
    for (const r of res.results) {
      const b = uniq[r.i];
      const m = verdict(b, r);
      if (m) messages.set(key(b), m);
      else cache.ok[key(b)] = 1;
    }
    if (!a.redraw) writeCache(cacheFile, cache);
  }
  out({
    rendered: uniq.length, cached: input.blocks.length - todo.length,
    results: input.blocks.map((b) => ({ id: b.id, ok: !messages.has(key(b)), message: messages.get(key(b)) || "" })),
  });
}

main().then(() => process.exit(0), (e) => { out({ skip: `helper crashed: ${e && e.message}` }); process.exit(0); });
