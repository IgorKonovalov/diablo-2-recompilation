// widget-only/1
// Checksum stepper. A small tool of our own that restates the checksum step of the saves page: the sum
// starts at 0; for each byte, the 32-bit sum is rotated left by one bit and the byte is added, modulo
// 2 to the power 32; the four bytes at offsets 12 to 15 (the checksum field) count as 0.
// The bytes are typed here as toy bytes; nothing is read from a save. Every value shown is computed by
// our model, not observed in the game.

const NAME = "checksum";

// One or two hex digits per token; returns { octets, fault } with fault 0 none, 1 a bad token, 2 too many bytes
function parseBytes(text, maxBytes) {
  const octets = [];
  let token = [];
  let fault = 0;
  const flush = () => {
    if (token.length === 0) return;
    if (token.length > 2) fault = 1;
    else octets.push(token.reduce((acc, v) => acc * 16 + v, 0));
    token = [];
  };
  for (const raw of text) {
    const v = parseInt(raw, 16);
    if (raw === " " || raw === ",") flush();
    else if (isNaN(v)) {
      fault = 1;
      token = [];
    } else token.push(v);
  }
  flush();
  if (fault === 0 && octets.length > maxBytes) fault = 2;
  return { octets: fault === 0 ? octets : [], fault };
}

// The pure part: no page access. inputs: { typed } (a string of hex bytes); the parsed widget.json is the second argument.
export function compute(inputs, data) {
  const rule = data.rule;
  const parsed = parseBytes(String(inputs.typed), rule.maxBytes);
  const steps = [];
  let sum = 0;
  parsed.octets.forEach((b, i) => {
    const used = i >= rule.skipFrom && i < rule.skipTo ? 0 : b;
    const rot = ((sum << 1) | (sum >>> 31)) >>> 0;
    sum = (rot + used) >>> 0;
    steps.push({ i, byte: b, used, rot, sum });
  });
  return { fault: parsed.fault, tally: parsed.octets.length, steps, whole: sum };
}

function hex(v, width) {
  return v.toString(16).toUpperCase().padStart(width, "0");
}

function make(el, text, cls) {
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}

function td(text) {
  return make(document.createElement("td"), text);
}

export function mount(element, data) {
  const t = data.text;
  const uid = "w-" + NAME + "-" + Math.floor(Math.random() * 1e9);
  const root = make(document.createElement("div"), undefined, "widget-body");
  root.append(make(document.createElement("p"), t.intro));
  const form = make(document.createElement("form"), undefined, "widget-form");
  form.addEventListener("submit", (e) => e.preventDefault());
  const wrap = make(document.createElement("div"), undefined, "widget-field");
  const lab = make(document.createElement("label"), t.bytesLabel);
  lab.htmlFor = uid + "-b";
  const bytesIn = document.createElement("input");
  bytesIn.type = "text";
  bytesIn.id = uid + "-b";
  bytesIn.value = data.inputs.typed.default;
  wrap.append(lab, bytesIn);
  form.append(wrap);
  const presetWrap = make(document.createElement("div"), undefined, "widget-field");
  const presetLab = make(document.createElement("label"), t.presetLabel);
  presetLab.htmlFor = uid + "-p";
  const preset = document.createElement("select");
  preset.id = uid + "-p";
  const none = document.createElement("option");
  none.value = "";
  none.textContent = t.presetNone;
  preset.append(none);
  for (const s of data.presets.items) {
    const o = document.createElement("option");
    o.value = s;
    o.textContent = s;
    preset.append(o);
  }
  presetWrap.append(presetLab, preset);
  form.append(presetWrap);
  const table = make(document.createElement("table"), undefined, "widget-table");
  const skip = make(document.createElement("p"), t.skipNote, "widget-note");
  const live = make(document.createElement("p"), undefined, "widget-live");
  live.setAttribute("aria-live", "polite");
  const note = make(document.createElement("p"), t.note, "widget-note");
  root.append(form, table, skip, live, note);
  element.replaceChildren(root);

  function render() {
    const out = compute({ typed: bytesIn.value }, data);
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    const first = document.createElement("tr");
    first.append(td("-"), td("-"), td("-"), td("-"), td(hex(0, 8) + " (" + t.start + ")"));
    body.append(first);
    for (const s of out.steps) {
      const tr = document.createElement("tr");
      tr.append(td(String(s.i)), td(hex(s.byte, 2)), td(hex(s.used, 2)), td(hex(s.rot, 8)), td(hex(s.sum, 8)));
      body.append(tr);
    }
    table.append(thead, body);
    if (out.fault === 1) live.textContent = t.errBad + " " + bytesIn.value;
    else if (out.fault === 2) live.textContent = t.errLong;
    else live.textContent = t.totalHead + " " + hex(out.whole, 8) + " (" + out.tally + " " + t.liveCount + ").";
  }

  bytesIn.addEventListener("input", render);
  preset.addEventListener("change", () => {
    if (preset.value !== "") {
      bytesIn.value = preset.value;
      render();
    }
  });
  render();
}

if (typeof document !== "undefined") {
  for (const el of document.querySelectorAll('figure[data-widget-name="' + NAME + '"]')) {
    if (!el.dataset.mounted) {
      el.dataset.mounted = "1";
      mount(el, JSON.parse(el.dataset.widgetData));
    }
  }
}
