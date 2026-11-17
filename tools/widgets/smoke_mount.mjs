// Imports one widget module the way the page does and lets it mount into a minimal stand-in for the page (no browser) and reports what it built.
// Usage: node smoke_mount.mjs <widget.mjs> <widget.json>
// Prints JSON {nodes, text, inputs, live}; used by tools/test_widgets.py to catch a widget whose mount fails.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

class Node_ {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.attrs = {};
    this.listeners = {};
    this.value = "";
    this.dataset = {};
    this._text = "";
  }
  append(...kids) { for (const k of kids) this.children.push(k); }
  replaceChildren(...kids) { this.children = [...kids]; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  setAttribute(k, v) { this.attrs[k] = v; }
  set textContent(v) { this._text = String(v); this.children = []; }
  get textContent() { return this._text + this.children.map((c) => c.textContent).join(""); }
  fire(type) { for (const f of this.listeners[type] || []) f({ preventDefault() {} }); }
}
const all = [];
const walkAll = (n, f) => { f(n); for (const c of n.children) walkAll(c, f); };
const [mod, dataPath] = process.argv.slice(2);
const host = new Node_("figure");
host.dataset.widgetData = readFileSync(dataPath, "utf8");
// the host page gives the module its figure; importing the module mounts it, as the browser's script tag does
globalThis.document = {
  createElement: (tag) => { const n = new Node_(tag); all.push(n); return n; },
  querySelectorAll: () => [host],
};
await import(pathToFileURL(mod).href);
if (!host.dataset.mounted) throw new Error("the module did not mount into its figure");
const found = [];
walkAll(host, (n) => found.push(n));
const inputs = found.filter((n) => n.tag === "input");
inputs[0].value = "12345";
inputs[1].value = "100";
inputs[2].value = "2";
for (const i of inputs) i.fire("input");
const rows = [];
walkAll(host, (n) => { if (n.tag === "tr") rows.push(n.textContent); });
const live = found.find((n) => n.attrs["aria-live"] === "polite");
process.stdout.write(JSON.stringify({ nodes: found.length, inputs: inputs.length, rows, live: live ? live.textContent : null }));
