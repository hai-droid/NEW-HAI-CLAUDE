// לוח תוצאות הבחירות. קורא את data/results.json ו-data/history.json ומתרענן כל דקה.
(() => {
  "use strict";

  const REFRESH_MS = 30000;
  const STALE_MS = 10 * 60 * 1000;

  // צבעי מפלגות מוכרים לפי מילת מפתח בשם. רשימה שאינה כאן מקבלת צבע קבוע מהפלטה.
  const KNOWN_COLORS = [
    [/ליכוד/, "#1f4e9c"], [/יש עתיד/, "#3aa0d8"], [/ש"ס|שס/, "#2b2b2b"],
    [/יהדות התורה|אגודת|דגל התורה/, "#5b5b5b"], [/הציונות הדתית|ציונות דתית/, "#6b8e23"],
    [/עוצמה/, "#d4a017"], [/ישראל ביתנו/, "#0e6e5c"], [/הדמוקרטים|העבודה|מרצ/, "#c4314b"],
    [/בנט/, "#13294b"], [/המחנה הממלכתי|כחול לבן|גנץ/, "#4b6cb7"], [/איזנקוט|הישר/, "#7c3aed"],
    [/רע"ם|רעם|המשותפת הערבית/, "#1f8f4e"], [/חד"ש|תע"ל|חדש/, "#e0603a"], [/בל"ד|בלד/, "#8a5a2b"],
    [/המילואימניקים/, "#5f7f4f"], [/נעם/, "#a0522d"],
  ];
  const PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"];
  const OTHER = "#9a9993";

  const $ = (id) => document.getElementById(id);
  const fmt = (n) => (n == null ? "—" : Number(n).toLocaleString("he-IL"));
  const fmtPct = (n) => (n == null ? "—" : `${Number(n).toFixed(2)}%`);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);

  const state = { data: null, history: [], coalition: new Set(loadCoalition()), colors: new Map() };

  function loadCoalition() {
    try { return JSON.parse(localStorage.getItem("coalition") || "[]"); } catch { return []; }
  }
  function saveCoalition() {
    try { localStorage.setItem("coalition", JSON.stringify([...state.coalition])); } catch { /* אין אחסון */ }
  }

  function hash(s) { let h = 0; for (const c of s) h = (h * 31 + c.charCodeAt(0)) | 0; return Math.abs(h); }
  function colorOf(p) {
    if (state.colors.has(p.name)) return state.colors.get(p.name);
    const known = KNOWN_COLORS.find(([re]) => re.test(p.name));
    let c = known ? known[1] : PALETTE[hash(p.name) % PALETTE.length];
    if (!p.seats && !known) c = OTHER;
    state.colors.set(p.name, c);
    return c;
  }

  // ------------------------------------------------------------ tooltip
  const tip = $("tooltip");
  function showTip(html, ev) {
    tip.innerHTML = html; tip.hidden = false;
    const x = Math.min(ev.clientX + 12, window.innerWidth - tip.offsetWidth - 8);
    const y = Math.min(ev.clientY + 12, window.innerHeight - tip.offsetHeight - 8);
    tip.style.left = `${Math.max(8, x)}px`; tip.style.top = `${y}px`;
  }
  const hideTip = () => { tip.hidden = true; };
  function partyTip(p) {
    return `<b>${esc(p.name)}</b><br>${p.seats} מנדטים · ${fmtPct(p.percent)}<br>${fmt(p.votes)} קולות`;
  }
  function bindTip(el, p) {
    el.addEventListener("mousemove", (e) => showTip(partyTip(p), e));
    el.addEventListener("mouseleave", hideTip);
  }

  // ------------------------------------------------------------ KPIs
  function renderKpis(d) {
    const s = d.summary || {};
    const seated = d.parties.filter((p) => p.seats > 0).length;
    const tiles = [
      { label: "אחוז הצבעה", value: s.turnout != null ? `${s.turnout}%` : "—",
        sub: s.voters ? `${fmt(s.voters)} מצביעים מתוך ${fmt(s.eligible)}` : "", meter: s.turnout },
      { label: "קלפיות שנספרו", value: s.counted_percent != null ? `${s.counted_percent}%` : "—",
        sub: s.ballots_counted ? `${fmt(s.ballots_counted)} מתוך ${fmt(s.ballots_total)}` : "", meter: s.counted_percent },
      { label: "קולות כשרים", value: fmt(s.valid), sub: s.invalid ? `${fmt(s.invalid)} פסולים` : "" },
      { label: "רשימות שעברו את החסימה", value: seated, sub: `מתוך ${d.parties.length} רשימות` },
      { label: `אחוז החסימה (${d.threshold_percent}%)`, value: fmt(d.threshold_votes), sub: "קולות נדרשים" },
    ];
    $("kpis").innerHTML = tiles.map((t) => `
      <div class="kpi">
        <div class="label">${esc(t.label)}</div>
        <div class="value">${esc(t.value)}</div>
        ${t.sub ? `<div class="sub">${esc(t.sub)}</div>` : ""}
        ${t.meter != null ? `<div class="meter"><b style="width:${Math.min(100, t.meter)}%"></b></div>` : ""}
      </div>`).join("");
  }

  // ------------------------------------------------------------ hemicycle
  function hemicycleSeats(total) {
    // מיקום מושבים בחצי עיגול: שורות קונצנטריות, מספר מושבים יחסי לרדיוס.
    const rows = 7, r0 = 70, r1 = 190;
    const radii = Array.from({ length: rows }, (_, i) => r0 + ((r1 - r0) * i) / (rows - 1));
    const sum = radii.reduce((a, b) => a + b, 0);
    let counts = radii.map((r) => Math.round((total * r) / sum));
    counts[rows - 1] += total - counts.reduce((a, b) => a + b, 0);
    const seats = [];
    radii.forEach((r, i) => {
      const n = counts[i];
      for (let j = 0; j < n; j++) {
        const a = Math.PI - (Math.PI * j) / (n - 1);
        seats.push({ x: 210 + r * Math.cos(a), y: 205 - r * Math.sin(a), a });
      }
    });
    // ממיינים לפי זווית כדי שכל מפלגה תקבל "פלח" רציף מימין לשמאל.
    return seats.sort((p, q) => q.a - p.a || 0);
  }

  function renderHemicycle(d) {
    const seats = hemicycleSeats(d.total_seats);
    const order = d.parties.filter((p) => p.seats > 0);
    const assigned = [];
    order.forEach((p) => { for (let i = 0; i < p.seats; i++) assigned.push(p); });
    // RTL: הפלח הראשון מימין.
    seats.reverse();
    const allocated = assigned.length;
    const dots = seats.map((s, i) => {
      const p = assigned[i];
      return `<circle cx="${s.x.toFixed(1)}" cy="${s.y.toFixed(1)}" r="7.5" data-i="${i}"
        fill="${p ? colorOf(p) : "var(--empty-seat)"}"></circle>`;
    }).join("");
    $("hemicycle").innerHTML = `
      <svg viewBox="0 0 420 222" role="img" aria-label="חלוקת המושבים בכנסת">
        ${dots}
        <text class="big" x="210" y="190" text-anchor="middle">${allocated}</text>
        <text class="majority" x="210" y="210" text-anchor="middle">רוב: ${d.majority} מנדטים</text>
      </svg>`;
    $("hemicycle").querySelectorAll("circle").forEach((c) => {
      const p = assigned[+c.dataset.i];
      if (p) bindTip(c, p);
    });
    $("legend").innerHTML = order.map((p) =>
      `<li><i style="background:${colorOf(p)}"></i>${esc(p.name)} <b>${p.seats}</b></li>`).join("");
  }

  // ------------------------------------------------------------ seat bars
  function renderSeatBars(d) {
    const rows = d.parties.filter((p) => p.seats > 0);
    const max = Math.max(1, ...rows.map((p) => p.seats));
    $("seatBars").innerHTML = rows.map((p, i) => `
      <div class="bar-row" data-i="${i}">
        <span class="name" title="${esc(p.name)}">${esc(p.name)}</span>
        <span class="track"><span class="fill" style="width:${(100 * p.seats) / max}%;background:${colorOf(p)}"></span></span>
        <span class="val">${p.seats}</span>
      </div>`).join("") || `<p class="hint">עדיין אין רשימות מעל אחוז החסימה.</p>`;
    $("seatBars").querySelectorAll(".bar-row").forEach((el) => bindTip(el, rows[+el.dataset.i]));
  }

  // ------------------------------------------------------------ coalition
  function renderCoalition(d) {
    const seated = d.parties.filter((p) => p.seats > 0);
    const names = new Set(seated.map((p) => p.name));
    for (const n of [...state.coalition]) if (!names.has(n)) state.coalition.delete(n);
    const chosen = seated.filter((p) => state.coalition.has(p.name));
    const total = chosen.reduce((a, p) => a + p.seats, 0);
    const ok = total >= d.majority;
    $("coalitionMeter").innerHTML =
      chosen.map((p) => `<span style="width:${(100 * p.seats) / d.total_seats}%;background:${colorOf(p)}"
        title="${esc(p.name)} ${p.seats}"></span>`).join("") +
      `<i class="line" style="right:${(100 * d.majority) / d.total_seats}%"></i>
       <span class="total">${total} מנדטים ${ok ? "✓ יש רוב" : `· חסרים ${d.majority - total} לרוב`}</span>`;
    $("coalitionChips").innerHTML = seated.map((p) => `
      <button type="button" class="chip" aria-pressed="${state.coalition.has(p.name)}" data-name="${esc(p.name)}">
        <i style="background:${colorOf(p)}"></i>${esc(p.name)} · ${p.seats}
      </button>`).join("");
    $("coalitionChips").querySelectorAll(".chip").forEach((b) => b.addEventListener("click", () => {
      const n = b.dataset.name;
      state.coalition.has(n) ? state.coalition.delete(n) : state.coalition.add(n);
      saveCoalition(); renderCoalition(d);
    }));
  }

  // ------------------------------------------------------------ trend
  function renderTrend(d) {
    const h = state.history;
    const el = $("trend");
    const W = 800, H = 260, m = { t: 12, r: 40, b: 28, l: 12 };
    if (h.length < 2) {
      el.innerHTML = `<svg viewBox="0 0 ${W} ${H}"><text class="empty" x="${W / 2}" y="${H / 2}" text-anchor="middle">
        הגרף יופיע אחרי שני עדכוני ספירה לפחות</text></svg>`;
      $("trendLegend").innerHTML = "";
      return;
    }
    const top = d.parties.filter((p) => p.seats > 0).slice(0, 8);
    const maxSeat = Math.max(4, ...h.flatMap((pt) => top.map((p) => pt.seats[p.name] || 0)));
    const x = (i) => W - m.r - ((W - m.l - m.r) * i) / (h.length - 1); // RTL: זמן זורם מימין לשמאל
    const y = (v) => m.t + (H - m.t - m.b) * (1 - v / maxSeat);
    const ticks = [0, Math.round(maxSeat / 2), maxSeat];
    const time = (t) => new Date(t).toLocaleTimeString("he-IL", { hour: "2-digit", minute: "2-digit" });
    const lines = top.map((p) => {
      const pts = h.map((pt, i) => `${x(i).toFixed(1)},${y(pt.seats[p.name] || 0).toFixed(1)}`);
      return `<path d="M${pts.join("L")}" stroke="${colorOf(p)}"></path>`;
    }).join("");
    el.innerHTML = `
      <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="מגמת מנדטים">
        <g class="axis">
          ${ticks.map((t) => `<line x1="${m.l}" x2="${W - m.r}" y1="${y(t)}" y2="${y(t)}"></line>
            <text x="${W - m.r + 6}" y="${y(t) + 4}">${t}</text>`).join("")}
          <text x="${x(0)}" y="${H - 8}" text-anchor="end">${time(h[0].t)}</text>
          <text x="${x(h.length - 1)}" y="${H - 8}" text-anchor="start">${time(h[h.length - 1].t)}</text>
        </g>
        ${lines}
        <line id="crosshair" y1="${m.t}" y2="${H - m.b}" stroke="var(--text-3)" stroke-dasharray="3 3" visibility="hidden"></line>
        <rect x="${m.l}" y="0" width="${W - m.l - m.r}" height="${H}" fill="transparent" id="hit"></rect>
      </svg>`;
    const svg = el.querySelector("svg"), hit = el.querySelector("#hit"), cross = el.querySelector("#crosshair");
    hit.addEventListener("mousemove", (e) => {
      const r = svg.getBoundingClientRect();
      const px = ((e.clientX - r.left) / r.width) * W;
      const i = Math.max(0, Math.min(h.length - 1, Math.round(((W - m.r - px) / (W - m.l - m.r)) * (h.length - 1))));
      cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i)); cross.setAttribute("visibility", "visible");
      const rows = top.map((p) => `<span style="color:${colorOf(p)}">●</span> ${esc(p.name)}: <b>${h[i].seats[p.name] || 0}</b>`);
      showTip(`<b>${time(h[i].t)}</b> · ${fmt(h[i].valid)} קולות<br>${rows.join("<br>")}`, e);
    });
    hit.addEventListener("mouseleave", () => { cross.setAttribute("visibility", "hidden"); hideTip(); });
    $("trendLegend").innerHTML = top.map((p) => `<li><i style="background:${colorOf(p)}"></i>${esc(p.name)}</li>`).join("");
  }

  // ------------------------------------------------------------ table
  function renderTable(d) {
    const prev = state.history.length > 1 ? state.history[state.history.length - 2] : null;
    const maxPct = Math.max(d.threshold_percent * 2, ...d.parties.map((p) => p.percent));
    const thPos = (100 * d.threshold_percent) / maxPct;
    $("table").querySelector("tbody").innerHTML = d.parties.map((p) => {
      const delta = prev && prev.seats[p.name] != null ? p.seats - prev.seats[p.name] : 0;
      const deltaHtml = delta ? `<span class="delta ${delta > 0 ? "up" : "down"}">${delta > 0 ? "▲" : "▼"} ${Math.abs(delta)}</span>` : "";
      return `<tr class="${p.passed_threshold ? "" : "out"}">
        <td><span class="party"><i style="background:${colorOf(p)}"></i>${esc(p.name)}</span></td>
        <td>${esc(p.letters)}</td>
        <td class="num">${fmt(p.votes)}</td>
        <td><div class="pct"><span class="track"><b style="width:${(100 * p.percent) / maxPct}%;background:${colorOf(p)}"></b>
          <i class="th" style="right:${thPos}%" title="אחוז החסימה"></i></span><span>${fmtPct(p.percent)}</span></div></td>
        <td class="num"><b>${p.seats}</b></td>
        <td class="num">${deltaHtml}</td>
      </tr>`;
    }).join("");
    const out = d.parties.filter((p) => !p.passed_threshold).length;
    $("thresholdNote").textContent = `הקו האנכי מסמן את אחוז החסימה (${d.threshold_percent}%). ` +
      (out ? `${out} רשימות מתחת לחסימה מוצגות באפור.` : "");
  }

  // ------------------------------------------------------------ data
  function renderMeta(d) {
    $("title").textContent = `תוצאות ${d.election}`;
    document.title = `תוצאות בחירות 26`;
    const t = new Date(d.updated_at);
    const stale = Date.now() - t.getTime() > STALE_MS;
    $("updated").textContent = `עודכן: ${t.toLocaleString("he-IL", { dateStyle: "short", timeStyle: "medium" })}`;
    $("live").classList.toggle("on", !stale);
    $("liveText").textContent = stale ? "לא עודכן לאחרונה" : "מתעדכן";
    $("seatsSource").textContent = d.seats_source === "official" ? "מנדטים: רשמי" : "מנדטים: חישוב באדר-עופר";
    if (d.source && /^https?:/.test(d.source)) $("sourceLink").href = d.source;
  }

  function render() {
    const d = state.data;
    if (!d) return;
    renderMeta(d); renderKpis(d); renderHemicycle(d); renderSeatBars(d);
    renderCoalition(d); renderTrend(d); renderTable(d);
  }

  async function load() {
    try {
      const bust = `?t=${Date.now()}`;
      const [r, h] = await Promise.all([
        fetch(`data/results.json${bust}`, { cache: "no-store" }),
        fetch(`data/history.json${bust}`, { cache: "no-store" }).catch(() => null),
      ]);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      state.data = await r.json();
      state.history = h && h.ok ? await h.json() : [];
      $("errorBanner").hidden = true;
      render();
    } catch (e) {
      $("errorBanner").hidden = false;
      $("errorBanner").textContent = `לא ניתן לטעון את קובץ התוצאות (${e.message}). ודאו שה-fetcher רץ.`;
      $("live").classList.remove("on");
      $("liveText").textContent = "אין חיבור";
    }
  }

  $("refresh").addEventListener("click", load);
  $("clearCoalition").addEventListener("click", () => { state.coalition.clear(); saveCoalition(); render(); });
  $("theme").addEventListener("click", () => {
    const root = document.documentElement;
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch { /* אין אחסון */ }
  });
  try { const t = localStorage.getItem("theme"); if (t) document.documentElement.dataset.theme = t; } catch { /* אין אחסון */ }

  load();
  setInterval(load, REFRESH_MS);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) load(); });
})();
