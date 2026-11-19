// widget-only/1
// Regeneration ticker. A small tool of our own that restates the regeneration tick of the states page: each frame the
// life takes its stat 74 (kept between 256 and the maximum), the stamina gains a share of its maximum by the unit's
// mode, and the mana gains a share of its maximum plus the flat recovery, kept between 0 and the maximum.
// Every value shown is computed by our model in this page, from the numbers typed here; none is observed in the
// game, and the numbers offered are illustrative.

const NAME = "regen";

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

// The pure part: no page access. The inputs are the numbers of widget.json's `inputs`; the parsed widget.json is the second argument.
export function compute(inputs, data) {
  const lim = data.inputs;
  const rule = data.rule;
  const life0 = toInt(inputs.life, lim.life.min, lim.life.max, lim.life.default);
  const lifeMax = toInt(inputs.lifeMax, lim.lifeMax.min, lim.lifeMax.max, lim.lifeMax.default);
  const lifeReg = toInt(inputs.lifeReg, lim.lifeReg.min, lim.lifeReg.max, lim.lifeReg.default);
  const stam0 = toInt(inputs.stam, lim.stam.min, lim.stam.max, lim.stam.default);
  const stamMax = toInt(inputs.stamMax, lim.stamMax.min, lim.stamMax.max, lim.stamMax.default);
  const stamBonus = toInt(inputs.stamBonus, lim.stamBonus.min, lim.stamBonus.max, lim.stamBonus.default);
  const mode = toInt(inputs.mode, lim.mode.min, lim.mode.max, lim.mode.default);
  const mana0 = toInt(inputs.mana, lim.mana.min, lim.mana.max, lim.mana.default);
  const manaMax = toInt(inputs.manaMax, lim.manaMax.min, lim.manaMax.max, lim.manaMax.default);
  const manaK = toInt(inputs.manaK, lim.manaK.min, lim.manaK.max, lim.manaK.default);
  const manaBonus = toInt(inputs.manaBonus, lim.manaBonus.min, lim.manaBonus.max, lim.manaBonus.default);
  const manaFlat = toInt(inputs.manaFlat, lim.manaFlat.min, lim.manaFlat.max, lim.manaFlat.default);
  const noMana = toInt(inputs.noMana, lim.noMana.min, lim.noMana.max, lim.noMana.default);
  const ticks = toInt(inputs.ticks, lim.ticks.min, lim.ticks.max, lim.ticks.default);
  let life = life0;
  let stam = stam0;
  let mana = mana0;
  const rows = [{ tick: 0, life, lifeWhy: "start", stam, stamWhy: "start", mana, manaWhy: "start" }];
  for (let tick = 1; tick <= ticks; tick++) {
    // life: stat 74 is added whatever its sign, held at the maximum, then at the floor
    let lifeWhy = "none";
    if (lifeReg !== 0) {
      let n = (life + lifeReg) | 0;
      lifeWhy = lifeReg > 0 ? "up" : "down";
      if (n > lifeMax) {
        n = lifeMax;
        lifeWhy = "cap";
      }
      if (n < rule.lifeFloor) {
        n = rule.lifeFloor;
        lifeWhy = "floor";
      }
      life = n;
    }
    // stamina: a shift of the maximum by the unit's mode
    let shift = rule.shiftSlow;
    let go = true;
    if (mode === 1 || mode === 5) {
      shift = rule.shiftSlow;
    } else if (mode === 6) {
      shift = rule.shiftFast;
    } else if (mode === 2) {
      shift = rule.shiftFast;
      if (stam < rule.walkMin) go = false;
    } else {
      go = stamBonus >= rule.bonusLimit;
    }
    let stamWhy = "none";
    if (go) {
      if (stam < stamMax) {
        let d = stamMax >> shift;
        if (stamBonus !== 0) d = (d + tdiv(Math.imul(d, stamBonus), rule.percentBase)) | 0;
        stam = Math.min((stam + d) | 0, stamMax);
        stamWhy = "gain";
      } else {
        stamWhy = "full";
      }
    }
    // mana: a share of the maximum scaled by the recovery bonus, plus the flat recovery, kept inside 0 and the maximum
    let d = 0;
    let manaWhy = "state";
    if (noMana === 0) {
      const k = manaK * rule.manaUnit === 0 ? rule.manaDefault : manaK * rule.manaUnit;
      d = tdiv(manaMax, k);
      if (d < 1) d = 1;
      d = muldiv(d, (manaBonus + rule.percentBase) | 0, rule.percentBase);
      manaWhy = "regen";
    }
    d = (d + manaFlat) | 0;
    d = Math.min(d, (manaMax - mana) | 0);
    d = Math.max(d, -mana);
    mana = (mana + d) | 0;
    rows.push({ tick, life, lifeWhy, stam, stamWhy, mana, manaWhy });
  }
  return { rows };
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

function why(list, code) {
  const hit = list.items.find((x) => x.cause === code);
  return hit === undefined || hit.text === "" ? "" : " (" + hit.text + ")";
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
    life: field(form, uid + "-life", t.caps.life, lim.life, lim.life.default),
    lifeMax: field(form, uid + "-lifeMax", t.caps.lifeMax, lim.lifeMax, lim.lifeMax.default),
    lifeReg: field(form, uid + "-lifeReg", t.caps.lifeReg, lim.lifeReg, lim.lifeReg.default),
    stam: field(form, uid + "-stam", t.caps.stam, lim.stam, lim.stam.default),
    stamMax: field(form, uid + "-stamMax", t.caps.stamMax, lim.stamMax, lim.stamMax.default),
    stamBonus: field(form, uid + "-stamBonus", t.caps.stamBonus, lim.stamBonus, lim.stamBonus.default),
    mode: field(form, uid + "-mode", t.caps.mode, lim.mode, lim.mode.default),
    mana: field(form, uid + "-mana", t.caps.mana, lim.mana, lim.mana.default),
    manaMax: field(form, uid + "-manaMax", t.caps.manaMax, lim.manaMax, lim.manaMax.default),
    manaK: field(form, uid + "-manaK", t.caps.manaK, lim.manaK, lim.manaK.default),
    manaBonus: field(form, uid + "-manaBonus", t.caps.manaBonus, lim.manaBonus, lim.manaBonus.default),
    manaFlat: field(form, uid + "-manaFlat", t.caps.manaFlat, lim.manaFlat, lim.manaFlat.default),
    noMana: field(form, uid + "-noMana", t.caps.noMana, lim.noMana, lim.noMana.default),
    ticks: field(form, uid + "-ticks", t.caps.ticks, lim.ticks, lim.ticks.default),
  };
  const all = [ins.life, ins.lifeMax, ins.lifeReg, ins.stam, ins.stamMax, ins.stamBonus, ins.mode, ins.mana, ins.manaMax, ins.manaK, ins.manaBonus, ins.manaFlat, ins.noMana, ins.ticks];
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
        life: ins.life.value,
        lifeMax: ins.lifeMax.value,
        lifeReg: ins.lifeReg.value,
        stam: ins.stam.value,
        stamMax: ins.stamMax.value,
        stamBonus: ins.stamBonus.value,
        mode: ins.mode.value,
        mana: ins.mana.value,
        manaMax: ins.manaMax.value,
        manaK: ins.manaK.value,
        manaBonus: ins.manaBonus.value,
        manaFlat: ins.manaFlat.value,
        noMana: ins.noMana.value,
        ticks: ins.ticks.value,
      },
      data,
    );
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    for (const r of o.rows) {
      const tr = document.createElement("tr");
      tr.append(
        td(String(r.tick)),
        td(String(r.life) + why(t.whyLife, r.lifeWhy)),
        td(String(r.stam) + why(t.whyStam, r.stamWhy)),
        td(String(r.mana) + why(t.whyMana, r.manaWhy)),
      );
      body.append(tr);
    }
    table.append(thead, body);
    const last = o.rows.at(-1);
    live.textContent = t.liveHead + " " + (o.rows.length - 1) + " " + t.liveFrames + " " + last.life + ", " + t.liveStam + " " + last.stam + ", " + t.liveMana + " " + last.mana + ".";
  }

  for (const el of all) el.addEventListener("input", render);
  preset.addEventListener("change", () => {
    if (preset.value !== "") {
      const p = data.presets.items.at(Number(preset.value));
      ins.life.value = String(p.life);
      ins.lifeMax.value = String(p.lifeMax);
      ins.lifeReg.value = String(p.lifeReg);
      ins.stam.value = String(p.stam);
      ins.stamMax.value = String(p.stamMax);
      ins.stamBonus.value = String(p.stamBonus);
      ins.mode.value = String(p.mode);
      ins.mana.value = String(p.mana);
      ins.manaMax.value = String(p.manaMax);
      ins.manaK.value = String(p.manaK);
      ins.manaBonus.value = String(p.manaBonus);
      ins.manaFlat.value = String(p.manaFlat);
      ins.noMana.value = String(p.noMana);
      ins.ticks.value = String(p.ticks);
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
