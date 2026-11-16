// Draw Mermaid blocks to SVG for tools/site_build.py (ADR-0034). Same bundle and browser as the gate's
// tools/mermaid_render.mjs (E17): the pinned Mermaid in <dir>/mermaid-<version>.min.js, run in the system's
// Chromium-family browser that may resolve nothing but the loopback server. This helper never fetches
// anything: no bundle or no browser means {"skip": reason} and the builder shows the block's source.
//
// Usage: node tools/site_mermaid.mjs --dir <cache-dir> [--browser <path>] < blocks.json
// stdin:  {"blocks": [{"id": "<unique id>", "text": "<block body>"}, ...]}
// stdout: one JSON line: {"skip": reason} or {"svgs": {"<id>": "<svg>"}, "errors": {"<id>": "<message>"}}
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";

const VERSION = "12.2.0";
const BROWSERS = ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "brave", "brave-browser"];
const TIMEOUT_MS = Number(process.env.MERMAID_RENDER_TIMEOUT_MS || 240000);
const out = (o) => process.stdout.write(JSON.stringify(o) + "\n");
const DECODE = { "&quot;": '"', "&lt;": "<", "&gt;": ">", "&amp;": "&", "&apos;": "'", "&#39;": "'" };
const githubText = (t) => t.replace(/&(?:quot|lt|gt|amp|apos|#39);/g, (m) => DECODE[m]);

function findBrowser() {
  for (const n of BROWSERS) for (const d of (process.env.PATH || "").split(path.delimiter)) {
    const p = path.join(d, n);
    try { fs.accessSync(p, fs.constants.X_OK); return p; } catch {}
  }
  return null;
}

const PAGE = `<!doctype html><meta charset="utf-8"><body><div id="host" style="width:1200px"></div><script src="/mermaid.js"></script><script type="module">
const report = (o) => fetch("/results", { method: "POST", body: JSON.stringify(o) });
try {
  const mermaid = globalThis.mermaid;
  mermaid.initialize({ startOnLoad: false, securityLevel: "strict", suppressErrorRendering: true, theme: "neutral" });
  const blocks = await (await fetch("/blocks")).json();
  const host = document.getElementById("host");
  const svgs = {}, errors = {};
  for (const b of blocks) {
    try {
      const { svg } = await mermaid.render("m" + b.id, b.text);
      svgs[b.id] = svg;
    } catch (e) {
      errors[b.id] = String((e && (e.message || e.str)) || e).split("\\n").filter(Boolean).slice(0, 2).join(" | ");
    }
    host.innerHTML = "";
    document.getElementById("dm" + b.id)?.remove();
  }
  await report({ svgs, errors });
} catch (e) { await report({ fatal: String(e && e.message || e) }); }
</script>`;

function drawAll(bundle, browser, blocks) {
  return new Promise((resolve, reject) => {
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "site-mermaid-"));
    let child = null;
    const done = (f, v) => { clearTimeout(timer); child?.kill("SIGKILL"); server.close(); fs.rmSync(tmp, { recursive: true, force: true }); f(v); };
    const timer = setTimeout(() => done(reject, new Error(`no result in ${TIMEOUT_MS} ms`)), TIMEOUT_MS);
    const server = http.createServer((req, res) => {
      if (req.url === "/") res.writeHead(200, { "content-type": "text/html" }).end(PAGE);
      else if (req.url === "/blocks") res.writeHead(200, { "content-type": "application/json" }).end(JSON.stringify(blocks.map((b) => ({ id: b.id, text: githubText(b.text) }))));
      else if (req.url === "/results" && req.method === "POST") {
        let body = "";
        req.on("data", (d) => (body += d));
        req.on("end", () => { res.writeHead(204).end(); const o = JSON.parse(body); o.fatal ? done(reject, new Error(o.fatal)) : done(resolve, o); });
      } else if (req.url === "/mermaid.js") res.writeHead(200, { "content-type": "text/javascript" }).end(fs.readFileSync(bundle));
      else res.writeHead(404).end();
    });
    server.listen(0, "127.0.0.1", () => {
      child = spawn(browser, ["--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
        "--disable-background-networking", "--disable-sync", "--window-size=1400,1000", `--user-data-dir=${tmp}`,
        "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1", `http://127.0.0.1:${server.address().port}/`], { stdio: "ignore" });
      child.on("error", (e) => done(reject, e));
      child.on("exit", (code) => { if (server.listening) done(reject, new Error(`browser exited with ${code} before reporting`)); });
    });
  });
}

async function main() {
  const a = {};
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i += 2) a[argv[i].replace(/^--/, "")] = argv[i + 1];
  const input = JSON.parse(fs.readFileSync(0, "utf8") || '{"blocks":[]}');
  const bundle = a.dir && path.join(a.dir, `mermaid-${VERSION}.min.js`);
  if (!bundle || !fs.existsSync(bundle)) return out({ skip: `Mermaid ${VERSION} bundle not found in ${a.dir} (the gate's E17 fetches it once)` });
  const browser = a.browser || process.env.GATE_BROWSER || findBrowser();
  if (!browser) return out({ skip: `no browser found (tried ${BROWSERS.join(", ")}; set $GATE_BROWSER)` });
  try { out(await drawAll(bundle, browser, input.blocks)); } catch (e) { out({ skip: `browser run failed: ${e.message}` }); }
}
// no process.exit(): a large result written to a pipe must drain before the process ends
main().catch((e) => out({ skip: `helper crashed: ${e && e.message}` }));
