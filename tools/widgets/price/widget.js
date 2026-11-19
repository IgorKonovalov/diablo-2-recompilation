// widget-only/1
// Price stepper. A small tool of our own that restates the buy and sell values of the economy page for a toy item:
// the value starts at the first cost; an identified item adds its terms (the automagic affix's and one by quality),
// each (multiplier x value) / 1024 plus an add, with the division first when the buy value is above 65535; the
// sockets add half their cost each; an ethereal item and a class item divide the sell value by 4; the buyer's
// multipliers scale each value over 1024; the sell value is capped and both are at least 1.
// Every value shown is computed by our model in this page, from the numbers typed here; none is observed in the
// game, and the numbers offered are illustrative.

const NAME = "price";

function toInt(value, lo, hi, fallback) {
  const v = Math.trunc(Number(value));
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, v));
}

function tdiv(a, b) {
  return Math.trunc(a / b);
}

// the signed multiply-divide of the page (a guarded product over a divisor), in 32-bit integers
function muldiv(a, b, c) {
  a |= 0;
  b |= 0;
  c |= 0;
  if (c === 0) return 0;
  if (a > 0x100000) {
    if (c > a >> 4) return tdiv(a * b, c) | 0;
    return (tdiv(a, c) * b) | 0;
  }
  if (b > 0x10000) {
    if (c > b >> 4) return tdiv(a * b, c) | 0;
    return (tdiv(b, c) * a) | 0;
  }
  return tdiv(Math.imul(a, b), c);
}

// one term added to the two running sums: the large form tests the buy value for both
function addTerm(rule, buyV, sellV, m, a, dp, ds) {
  if (buyV > rule.large && m !== 0) {
    return {
      dp: (dp + Math.imul(tdiv(buyV, rule.unit), m) + a) | 0,
      ds: (ds + Math.imul(tdiv(sellV, rule.unit), m) + a) | 0,
    };
  }
  return {
    dp: (dp + tdiv(Math.imul(m, buyV), rule.unit) + a) | 0,
    ds: (ds + tdiv(Math.imul(m, sellV), rule.unit) + a) | 0,
  };
}

// the buyer's step: the test of the large form is on the multiplier named, which is the sell multiplier for the sell value
function scale(rule, v, m, test) {
  if (v > rule.large && test !== 0) return Math.imul(tdiv(v, rule.unit), m);
  return tdiv(Math.imul(m, v), rule.unit);
}

// The pure part: no page access. The inputs are the numbers of widget.json's `inputs`; the parsed widget.json is the second argument.
export function compute(inputs, data) {
  const lim = data.inputs;
  const rule = data.rule;
  const cost = toInt(inputs.cost, lim.cost.min, lim.cost.max, lim.cost.default);
  const grade0 = toInt(inputs.grade, lim.grade.min, lim.grade.max, lim.grade.default);
  const ident = toInt(inputs.ident, lim.ident.min, lim.ident.max, lim.ident.default);
  const recMult = toInt(inputs.recMult, lim.recMult.min, lim.recMult.max, lim.recMult.default);
  const recAdd = toInt(inputs.recAdd, lim.recAdd.min, lim.recAdd.max, lim.recAdd.default);
  const auto = toInt(inputs.auto, lim.auto.min, lim.auto.max, lim.auto.default);
  const autoMult = toInt(inputs.autoMult, lim.autoMult.min, lim.autoMult.max, lim.autoMult.default);
  const autoAdd = toInt(inputs.autoAdd, lim.autoAdd.min, lim.autoAdd.max, lim.autoAdd.default);
  const sockets = toInt(inputs.sockets, lim.sockets.min, lim.sockets.max, lim.sockets.default);
  const gem = toInt(inputs.gem, lim.gem.min, lim.gem.max, lim.gem.default);
  const eth = toInt(inputs.eth, lim.eth.min, lim.eth.max, lim.eth.default);
  const kind = toInt(inputs.kind, lim.kind.min, lim.kind.max, lim.kind.default);
  const sell = toInt(inputs.sell, lim.sell.min, lim.sell.max, lim.sell.default);
  const buy = toInt(inputs.buy, lim.buy.min, lim.buy.max, lim.buy.default);
  const maxbuy = toInt(inputs.maxbuy, lim.maxbuy.min, lim.maxbuy.max, lim.maxbuy.default);
  const reduce = toInt(inputs.reduce, lim.reduce.min, lim.reduce.max, lim.reduce.default);
  const grade = grade0 === 1 || grade0 === 5 || grade0 === 7 ? grade0 : 2;
  let bv = cost;
  let sv = cost;
  const first = [bv, sv];
  let dp = 0;
  let ds = 0;
  if (ident !== 0) {
    if (auto !== 0) {
      const t = addTerm(rule, bv, sv, autoMult, autoAdd, 0, 0);
      dp = t.dp;
      ds = t.ds;
    }
    if (grade === 1) {
      dp = -tdiv(bv, rule.half);
      ds = -tdiv(sv, rule.half);
    } else if (grade === 5 || grade === 7) {
      const t = addTerm(rule, bv, sv, recMult, recAdd, dp, ds);
      dp = t.dp;
      ds = t.ds;
    }
    bv = (bv + dp) | 0;
    sv = (sv + ds) | 0;
  }
  const added = [bv, sv];
  for (let i = 0; i < sockets; i++) {
    const half = tdiv(gem, rule.half);
    bv = (bv + half) | 0;
    sv = (sv + half) | 0;
  }
  const withSockets = [bv, sv];
  if (eth !== 0) sv = tdiv(sv, rule.quarter);
  const afterEth = [bv, sv];
  if (kind !== 0) sv = tdiv(sv, rule.quarter);
  const value = [bv, sv];
  bv = scale(rule, bv, sell, sell);
  sv = scale(rule, sv, buy, sell);
  const npc = [bv, sv];
  const ceiling = sv > maxbuy ? maxbuy : sv;
  let pb = bv;
  if (reduce !== 0) pb = (pb - muldiv(pb, reduce, rule.pct)) | 0;
  return {
    cost,
    first,
    terms: [dp, ds],
    added,
    sockets: withSockets,
    ethereal: afterEth,
    value,
    npc,
    ceiling,
    buy: pb >= rule.floor ? pb : rule.floor,
    sell: ceiling >= rule.floor ? ceiling : rule.floor,
  };
}

function make(el, text, cls) {
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}

function td(text) {
  return make(document.createElement("td"), text);
}

function field(form, id, label, spec, value) {
  const wrap = make(document.createElement("div"), undefined, "widget-field");
  const lab = make(document.createElement("label"), label);
  lab.htmlFor = id;
  const inp = document.createElement("input");
  inp.type = "number";
  inp.id = id;
  inp.min = String(spec.min);
  inp.max = String(spec.max);
  inp.step = "1";
  inp.value = String(value);
  wrap.append(lab, inp);
  form.append(wrap);
  return inp;
}

export function mount(element, data) {
  const t = data.text;
  const uid = "w-" + NAME + "-" + Math.floor(Math.random() * 1e9);
  const root = make(document.createElement("div"), undefined, "widget-body");
  root.append(make(document.createElement("p"), t.intro));
  const form = make(document.createElement("form"), undefined, "widget-form");
  form.addEventListener("submit", (e) => e.preventDefault());
  const lim = data.inputs;
  const ins = {
    cost: field(form, uid + "-cost", t.caps.cost, lim.cost, lim.cost.default),
    grade: field(form, uid + "-grade", t.caps.grade, lim.grade, lim.grade.default),
    ident: field(form, uid + "-ident", t.caps.ident, lim.ident, lim.ident.default),
    recMult: field(form, uid + "-recMult", t.caps.recMult, lim.recMult, lim.recMult.default),
    recAdd: field(form, uid + "-recAdd", t.caps.recAdd, lim.recAdd, lim.recAdd.default),
    auto: field(form, uid + "-auto", t.caps.auto, lim.auto, lim.auto.default),
    autoMult: field(form, uid + "-autoMult", t.caps.autoMult, lim.autoMult, lim.autoMult.default),
    autoAdd: field(form, uid + "-autoAdd", t.caps.autoAdd, lim.autoAdd, lim.autoAdd.default),
    sockets: field(form, uid + "-sockets", t.caps.sockets, lim.sockets, lim.sockets.default),
    gem: field(form, uid + "-gem", t.caps.gem, lim.gem, lim.gem.default),
    eth: field(form, uid + "-eth", t.caps.eth, lim.eth, lim.eth.default),
    kind: field(form, uid + "-kind", t.caps.kind, lim.kind, lim.kind.default),
    sell: field(form, uid + "-sell", t.caps.sell, lim.sell, lim.sell.default),
    buy: field(form, uid + "-buy", t.caps.buy, lim.buy, lim.buy.default),
    maxbuy: field(form, uid + "-maxbuy", t.caps.maxbuy, lim.maxbuy, lim.maxbuy.default),
    reduce: field(form, uid + "-reduce", t.caps.reduce, lim.reduce, lim.reduce.default),
  };
  const all = [ins.cost, ins.grade, ins.ident, ins.recMult, ins.recAdd, ins.auto, ins.autoMult, ins.autoAdd, ins.sockets, ins.gem, ins.eth, ins.kind, ins.sell, ins.buy, ins.maxbuy, ins.reduce];
  const presetWrap = make(document.createElement("div"), undefined, "widget-field");
  const presetLab = make(document.createElement("label"), t.presetLabel);
  presetLab.htmlFor = uid + "-preset";
  const preset = document.createElement("select");
  preset.id = uid + "-preset";
  const none = document.createElement("option");
  none.value = "";
  none.textContent = t.presetNone;
  preset.append(none);
  data.presets.items.forEach((p, i) => {
    const o = document.createElement("option");
    o.value = String(i);
    o.textContent = p.name;
    preset.append(o);
  });
  presetWrap.append(presetLab, preset);
  form.append(presetWrap);
  const table = make(document.createElement("table"), undefined, "widget-table");
  const live = make(document.createElement("p"), undefined, "widget-live");
  live.setAttribute("aria-live", "polite");
  const note = make(document.createElement("p"), t.note, "widget-note");
  root.append(form, table, live, note);
  element.replaceChildren(root);

  function render() {
    const o = compute(
      {
        cost: ins.cost.value,
        grade: ins.grade.value,
        ident: ins.ident.value,
        recMult: ins.recMult.value,
        recAdd: ins.recAdd.value,
        auto: ins.auto.value,
        autoMult: ins.autoMult.value,
        autoAdd: ins.autoAdd.value,
        sockets: ins.sockets.value,
        gem: ins.gem.value,
        eth: ins.eth.value,
        kind: ins.kind.value,
        sell: ins.sell.value,
        buy: ins.buy.value,
        maxbuy: ins.maxbuy.value,
        reduce: ins.reduce.value,
      },
      data,
    );
    const lines = [
      [t.steps.first, t.calc.first, String(o.first.at(0)), String(o.first.at(1))],
      [t.steps.terms, t.calc.terms, String(o.terms.at(0)), String(o.terms.at(1))],
      [t.steps.added, t.calc.added, String(o.added.at(0)), String(o.added.at(1))],
      [t.steps.sockets, t.calc.sockets, String(o.sockets.at(0)), String(o.sockets.at(1))],
      [t.steps.ethereal, t.calc.ethereal, String(o.ethereal.at(0)), String(o.ethereal.at(1))],
      [t.steps.value, t.calc.value, String(o.value.at(0)), String(o.value.at(1))],
      [t.steps.npc, t.calc.npc, String(o.npc.at(0)), String(o.npc.at(1))],
      [t.steps.ceiling, t.calc.ceiling, "-", String(o.ceiling)],
      [t.steps.price, t.calc.price, String(o.buy), String(o.sell)],
    ];
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    for (const l of lines) {
      const tr = document.createElement("tr");
      tr.append(td(l.at(0)), td(l.at(1)), td(l.at(2)), td(l.at(3)));
      body.append(tr);
    }
    table.append(thead, body);
    live.textContent = t.liveBuy + " " + o.buy + ", " + t.liveSell + " " + o.sell + ".";
  }

  for (const el of all) el.addEventListener("input", render);
  preset.addEventListener("change", () => {
    if (preset.value !== "") {
      const p = data.presets.items.at(Number(preset.value));
      ins.cost.value = String(p.cost);
      ins.grade.value = String(p.grade);
      ins.ident.value = String(p.ident);
      ins.recMult.value = String(p.recMult);
      ins.recAdd.value = String(p.recAdd);
      ins.auto.value = String(p.auto);
      ins.autoMult.value = String(p.autoMult);
      ins.autoAdd.value = String(p.autoAdd);
      ins.sockets.value = String(p.sockets);
      ins.gem.value = String(p.gem);
      ins.eth.value = String(p.eth);
      ins.kind.value = String(p.kind);
      ins.sell.value = String(p.sell);
      ins.buy.value = String(p.buy);
      ins.maxbuy.value = String(p.maxbuy);
      ins.reduce.value = String(p.reduce);
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
