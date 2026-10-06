import { lineChart, sparkline, shortDate } from "./charts.js";

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const state = { dash: null, model: {}, bucket: "all", window: "all", per: 100, open: new Set(), openFilter: "all" };

// ------------------------------------------------------------------ formatting
const pct = (v, digits = 1) => v == null ? "–" : `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(v * 100).toFixed(digits)}%`;
const plainPct = (v) => v == null ? "–" : `${Math.round(v * 100)}%`;
const cls = (v) => v == null ? "" : v > 0 ? "up" : v < 0 ? "down" : "";
const k = () => state.per / 100;
const usd = (v) => v == null ? "–" : `${v < 0 ? "−" : v > 0 ? "+" : ""}$${Math.abs(v * k()).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const price = (v) => v == null ? "–" : v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const longDate = (iso) => iso ? new Date(iso + "T12:00:00").toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" }) : "";
const model = (key) => state.dash.meta.models.find((m) => m.key === key) || { display_name: key, color: "#888" };
const bucketLabel = (b) => ({ moonshot: "Moonshot", catalyst: "Catalyst", compounder: "Compounder" }[b] || b);
const EXIT = { target: "Hit target", stop: "Stopped out", time: "Time's up", model_sell: "Model sold", no_data: "No data" };

async function getJSON(path) {
  const r = await fetch(path, { cache: "no-cache" });
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

// ------------------------------------------------------------------ boot
async function load() {
  state.dash = await getJSON("data/dashboard.json");
  const m = state.dash.meta;
  $("#repo-link").href = `https://github.com/${m.repo}`;
  const updated = new Date(m.generated_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  $("#status").textContent = `Next picks are due by 11:59 PM ET on ${longDate(m.next_night.run_date)} for ${longDate(m.next_night.session)}. Updated ${updated}.`;
  render();
}

function render() {
  const route = location.hash.match(/^#\/model\/(\w+)/);
  if (route) return renderModel(route[1]);
  const d = state.dash;
  const view = $("#view");
  if (!d.latest.target_date && !d.session.date) {
    view.innerHTML = `<div class="empty"><h2>The first picks haven't arrived</h2>
      <p class="lede">Each AI uploads its picks every trading night. They'll show up here a minute after the first upload.</p></div>${rulesSection()}`;
    return;
  }
  view.innerHTML = [raceSection(), standingsSection(), tonightSection(), resultsSection(), openSection(),
    closedSection(), ideasSection(), rulesSection()].join("");
  bind();
}

// ------------------------------------------------------------------ race (hero)
function raceSection() {
  const s = state.dash.session;
  if (!s.date) return "";
  const rows = s.standings.filter((r) => r.positions);
  const maxAbs = Math.max(1, ...rows.map((r) => Math.abs(r.pnl)));
  const lanes = rows.map((r, i) => {
    const w = (Math.abs(r.pnl) / maxAbs) * 50;
    const m = model(r.model);
    const parts = Object.entries(r.by_bucket).filter(([, v]) => v).map(([b, v]) => `${bucketLabel(b)} <span class="${cls(v)}">${usd(v)}</span>`).join(", ");
    return `<div class="lane">
      <span class="place">${i + 1}</span>
      <span class="who"><a href="#/model/${r.model}">${esc(m.display_name)}</a><small>${parts || "no positions"}</small></span>
      <span class="track" aria-hidden="true"><span class="bar" style="left:${r.pnl >= 0 ? 50 : 50 - w}%;width:${w}%;background:${m.color}"></span></span>
      <span class="num ${cls(r.pnl)}">${usd(r.pnl)}<small>on the session</small></span>
    </div>`;
  }).join("");
  const lead = state.dash.boards.all.all[0];
  const top = s.movers[0];
  const leader = lead && lead.positions ? `<aside class="leader">
      <h3>Overall leader</h3>
      <div class="big">${esc(model(lead.model).display_name)}</div>
      <p><span class="${cls(lead.total_pnl)}">${usd(lead.total_pnl)}</span> across ${lead.positions} positions, ${pct(lead.return_on_capital)} on the money put in.</p>
      <p>Won ${lead.sessions_won} of ${lead.sessions} sessions.</p>
      ${top ? `<p class="best">Biggest move: <a href="#p${top.id}">${esc(top.ticker)}</a> (${esc(model(top.model).display_name)}, ${bucketLabel(top.bucket).toLowerCase()}) <span class="up">${pct(top.ret)}</span> on the day.</p>` : ""}
    </aside>` : "";
  const winner = rows[0];
  return `<section class="race">
    <h2>${winner ? `${esc(model(winner.model).display_name)} won ${longDate(s.date)}` : longDate(s.date)}</h2>
    <p class="lede">Profit or loss on the session across every open position, at ${usd(100).replace("+", "")} per pick.</p>
    <div class="race-grid"><div class="lanes">${lanes}</div>${leader}</div>
  </section>`;
}

// ------------------------------------------------------------------ standings
function standingsSection() {
  const rows = state.dash.boards[state.window][state.bucket];
  const tab = (attr, val, label, cur) => `<button type="button" data-${attr}="${val}" aria-pressed="${cur === val}">${label}</button>`;
  const d1 = state.bucket === "moonshot" || state.bucket === "catalyst";
  const body = rows.map((r) => {
    const m = model(r.model);
    return `<tr>
      <td class="model"><span class="swatch" style="background:${m.color}"></span><a href="#/model/${r.model}">${esc(m.display_name)}</a></td>
      <td class="${cls(r.total_pnl)}"><strong>${r.positions ? usd(r.total_pnl) : "–"}</strong></td>
      <td class="${cls(r.return_on_capital)}">${pct(r.return_on_capital)}</td>
      <td>${plainPct(r.win_rate)}</td>
      <td class="${cls(r.avg_return)}">${pct(r.avg_return)}</td>
      <td class="${cls(r.avg_alpha)}">${pct(r.avg_alpha)}</td>
      <td>${plainPct(r.target_rate)}</td>
      <td>${plainPct(r.stop_rate)}</td>
      ${d1 || state.bucket === "all" ? `<td>${r.booms}</td>` : ""}
      ${state.bucket === "moonshot" ? `<td class="${cls(r.d1_avg_to_close)}">${pct(r.d1_avg_to_close)}</td>` : ""}
      <td>${r.best ? `${esc(r.best.ticker)} <span class="${cls(r.best.ret)}">${pct(r.best.ret)}</span>` : "–"}</td>
      <td>${r.worst ? `${esc(r.worst.ticker)} <span class="${cls(r.worst.ret)}">${pct(r.worst.ret)}</span>` : "–"}</td>
      <td>${r.closed} / ${r.open}</td>
      <td>${r.sessions_won} / ${r.sessions}</td>
    </tr>`;
  }).join("");
  const series = rows.filter((r) => r.equity.length).map((r) => ({ name: model(r.model).display_name, color: model(r.model).color,
    points: r.equity.map((p) => ({ x: p.date, y: p.pnl * k() })) }));
  const about = state.bucket === "all" ? "All three books together." : state.dash.meta.buckets[state.bucket].about;
  return `<section id="standings">
    <h2>Standings</h2>
    <p class="lede">${esc(about)} Profit includes open positions at their latest price.</p>
    <div class="toolbar">
      <div class="tabs" role="group" aria-label="Book">${tab("bucket", "all", "All books", state.bucket)}${tab("bucket", "moonshot", "Moonshots", state.bucket)}${tab("bucket", "catalyst", "Catalyst", state.bucket)}${tab("bucket", "compounder", "Compounders", state.bucket)}</div>
      <div class="tabs" role="group" aria-label="Time window">${tab("window", "all", "All time", state.window)}${tab("window", "30d", "30 days", state.window)}${tab("window", "7d", "7 days", state.window)}</div>
      <label class="amount">Put <input id="per" type="number" min="1" step="50" value="${state.per}" inputmode="decimal" /> in every pick</label>
    </div>
    <div class="table-wrap"><table>
      <thead><tr><th>Model</th><th>Profit</th><th>Return</th><th>Win rate</th><th>Avg trade</th><th>vs S&amp;P 500</th>
        <th>Hit target</th><th>Stopped</th>${d1 || state.bucket === "all" ? "<th>Booms</th>" : ""}${state.bucket === "moonshot" ? "<th>Avg day 1</th>" : ""}
        <th>Best</th><th>Worst</th><th>Closed / open</th><th>Days won</th></tr></thead>
      <tbody>${body}</tbody></table></div>
    ${series.length ? `<div class="chart-box">${lineChart(series, { baseline: 0, label: "Cumulative profit by model", fmt: (v) => `${v < 0 ? "−" : ""}$${Math.abs(Math.round(v)).toLocaleString()}` })}
      <div class="legend">${series.map((s) => `<span><span class="swatch" style="background:${s.color}"></span>${esc(s.name)}</span>`).join("")}<span>Cumulative profit, dashed line is break-even</span></div></div>` : ""}
  </section>`;
}

// ------------------------------------------------------------------ tonight's picks
function tonightSection() {
  const L = state.dash.latest;
  if (!L.target_date) return "";
  const cols = state.dash.meta.models.map((m) => {
    const s = L.submissions[m.key];
    if (!s) return `<div class="col" style="--c:${m.color}"><div class="col-head"><h3>${esc(m.display_name)}</h3><p>No upload yet.</p></div></div>`;
    const books = Object.keys(state.dash.meta.buckets).map((b) => {
      const picks = s.picks.filter((p) => p.bucket === b);
      if (!picks.length) return "";
      return `<h4 class="book">${bucketLabel(b)}s</h4><ul class="picklist">${picks.map((p) => pickRow(p, `t${p.id}`)).join("")}</ul>`;
    }).join("");
    const sells = s.reviews.filter((r) => r.action === "SELL");
    const moved = s.reviews.filter((r) => r.action === "HOLD" && (r.new_stop || r.new_target));
    const holds = s.reviews.filter((r) => r.action === "HOLD").length;
    return `<div class="col" style="--c:${m.color}">
      <div class="col-head"><h3><a href="#/model/${m.key}">${esc(m.display_name)}</a></h3>
        <p>${esc(s.model_version || m.maker)}, uploaded ${new Date(s.received_at).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}${s.status !== "ok" ? `, <span class="down">${esc(s.status)}</span>` : ""}</p></div>
      ${s.market_view ? `<blockquote class="view">${esc(s.market_view)}</blockquote>` : ""}
      ${s.reviews.length ? `<div class="calls"><h4 class="book">Calls on open positions</h4>
        ${sells.map((r) => `<p><span class="chip stop">Sell</span> <strong>${esc(r.ticker)}</strong> <span class="serif">${esc(r.reason)}</span></p>`).join("")}
        ${moved.map((r) => `<p><span class="chip target">Hold</span> <strong>${esc(r.ticker)}</strong> ${r.new_stop ? `stop to ${price(r.new_stop)}` : ""}${r.new_stop && r.new_target ? ", " : ""}${r.new_target ? `target to ${price(r.new_target)}` : ""}</p>`).join("")}
        <p class="muted">${holds} held${sells.length ? `, ${sells.length} sold at the next open` : ""}.</p></div>` : ""}
      ${books || '<p class="muted">No new picks.</p>'}
      ${s.errors.length ? `<details class="audit"><summary>${s.errors.length} problem${s.errors.length > 1 ? "s" : ""} with this upload</summary><ul>${s.errors.map((e) => `<li>${esc(e)}</li>`).join("")}</ul></details>` : ""}
      <p class="audit"><a href="data/raw/${s.id}.txt" target="_blank" rel="noopener">See the raw upload</a></p>
    </div>`;
  }).join("");
  const scored = L.target_date === state.dash.session.date;
  return `<section id="tonight"><h2>Picks for ${longDate(L.target_date)}</h2>
    <p class="lede">${scored ? "Scored against that session. Open a pick for its thesis, sources and price path." :
      "Locked in and waiting for the session. Entry is the last close; results appear after 4:15 PM ET."}</p>
    <div class="columns">${cols}</div></section>`;
}

function pickRow(p, id) {
  const ref = p.entry_price;
  const tgt = ref ? p.orig_target / ref - 1 : null;
  const stp = ref ? p.orig_stop / ref - 1 : null;
  const d1 = p.d1 || {};
  const live = p.status !== "void" && p.ret != null && p.sessions_held > 0;
  const chips = [d1.boom ? '<span class="chip boom">Boom</span>' : "",
    p.exit_reason === "target" ? '<span class="chip target">Target</span>' : "",
    p.exit_reason === "stop" ? '<span class="chip stop">Stopped</span>' : "",
    p.exit_reason === "model_sell" ? '<span class="chip">Sold</span>' : "",
    p.status === "void" ? '<span class="chip stop">Void</span>' : ""].join("");
  const move = live
    ? `<span class="move ${cls(p.ret)}">${pct(p.ret)}${p.intraday ? sparkline(p.intraday, { ref, mini: true, width: 72, height: 22 }) : ""}<small>${p.status === "open" ? `day ${p.sessions_held} of ${p.horizon_days}` : EXIT[p.exit_reason] || ""}</small></span>`
    : `<span class="move">${tgt != null ? `${pct(tgt)}<small>to target</small>` : ""}</span>`;
  const open = state.open.has(id);
  return `<li class="pick" id="p${p.id}">
    <button type="button" data-pick="${id}" aria-expanded="${open}">
      <span><span class="ticker">${esc(p.ticker)}</span><br><span class="conf" data-c="${esc(p.confidence)}">${esc(p.confidence)}</span></span>
      <span class="catalyst">${esc(p.thesis)}</span>
      ${move}
      <span class="levels">${ref ? `Entry ${price(ref)}&ensp;` : ""}Target ${price(p.orig_target)}${tgt != null ? ` (${pct(tgt)})` : ""}&ensp;Stop ${price(p.orig_stop)}${stp != null ? ` (${pct(stp)})` : ""}${p.bucket !== "moonshot" ? `&ensp;${p.horizon_days}-day limit` : ""}<span class="chips">${chips}</span></span>
    </button>
    ${open ? pickDetail(p) : ""}
  </li>`;
}

function pickDetail(p) {
  const d1 = p.d1 || {};
  return `<div class="detail">
    ${p.intraday ? sparkline(p.intraday, { ref: p.entry_price, target: p.orig_target, stop: p.orig_stop }) : ""}
    ${p.flags.length ? `<p class="down">${esc(p.flags.join("; "))}</p>` : ""}
    ${d1.pct_to_close != null ? `<p>First session: high ${pct(d1.pct_to_high)}, low ${pct(d1.pct_to_low)}, close ${pct(d1.pct_to_close)}.</p>` : ""}
    ${p.status === "closed" ? `<p>${EXIT[p.exit_reason] || "Closed"} on ${shortDate(p.exit_date)} at ${price(p.exit_price)} after ${p.sessions_held} session${p.sessions_held === 1 ? "" : "s"}: ${usd(p.pnl)}${p.bench_ret != null ? ` (S&amp;P 500 ${pct(p.bench_ret)} over the same days)` : ""}.</p>` : ""}
    ${p.status === "open" && p.sessions_held ? `<p>Now ${price(p.last_price)}, ${usd(p.pnl)}. Stop ${price(p.stop)}, target ${price(p.target)}.${p.sell_at_open_on ? ` Selling at the open on ${shortDate(p.sell_at_open_on)}.` : ""}</p>` : ""}
    ${p.last_review ? `<p>Latest call: <strong>${esc(p.last_review.action)}</strong> <span class="serif">${esc(p.last_review.reason)}</span></p>` : ""}
    <p>Catalyst timing: ${esc(p.catalyst_time || "not given")}.${p.entry_zone[0] ? ` Entry zone ${price(p.entry_zone[0])} to ${price(p.entry_zone[1])}.` : ""}</p>
    <p class="serif">Main risk: ${esc(p.main_risk || "not given")}</p>
    ${p.sources.length ? `<p>Sources: ${p.sources.map((u, i) => `<a href="${esc(u)}" target="_blank" rel="noopener nofollow">${esc(hostname(u) || `link ${i + 1}`)}</a>`).join(", ")}</p>` : ""}
  </div>`;
}
const hostname = (u) => { try { return new URL(u).hostname.replace(/^www\./, ""); } catch { return ""; } };

// ------------------------------------------------------------------ last session results
function resultsSection() {
  const s = state.dash.session;
  if (!s.date || s.date === state.dash.latest.target_date) return "";
  const subs = Object.values(s.picks || {}).filter(Boolean);
  if (!subs.length) return "";
  const cols = subs.map((sub) => {
    const m = model(sub.model);
    const fresh = sub.picks.filter((p) => p.bucket !== "compounder" && p.status !== "void");
    const avg = fresh.length ? fresh.reduce((a, p) => a + (p.d1?.pct_to_close || 0), 0) / fresh.length : null;
    return `<div class="col" style="--c:${m.color}"><div class="col-head"><h3>${esc(m.display_name)}</h3>
      <p>First-day average for new moonshots and catalyst plays</p><div class="avg ${cls(avg)}">${pct(avg, 2)}</div></div>
      <ul class="picklist">${fresh.map((p) => pickRow(p, `r${p.id}`)).join("")}</ul></div>`;
  }).join("");
  return `<section id="results"><h2>How the ${longDate(s.date)} picks did</h2>
    <p class="lede">Each line is the session's price path against the entry price. Open a pick for target and stop.</p>
    <div class="columns">${cols}</div></section>`;
}

// ------------------------------------------------------------------ open positions
function positionTable(rows, withModel = true) {
  return `<div class="table-wrap"><table class="positions">
    <thead><tr><th>Ticker</th>${withModel ? "<th>Model</th>" : ""}<th>Book</th><th>Held</th><th>Entry</th><th>Last</th><th>Return</th><th>Profit</th><th>Stop / target</th><th>Latest call</th></tr></thead>
    <tbody>${rows.map((p) => `<tr>
      <td><strong>${esc(p.ticker)}</strong></td>
      ${withModel ? `<td><span class="swatch" style="background:${model(p.model).color}"></span>${esc(model(p.model).display_name)}</td>` : ""}
      <td>${bucketLabel(p.bucket)}</td>
      <td>${p.sessions_held} / ${p.horizon_days}</td>
      <td>${price(p.entry_price)}</td><td>${price(p.status === "closed" ? p.exit_price : p.last_price)}</td>
      <td class="${cls(p.ret)}">${pct(p.ret)}</td><td class="${cls(p.pnl)}">${usd(p.pnl)}</td>
      <td>${price(p.stop)} / ${price(p.target)}</td>
      <td class="call">${p.status === "closed" ? esc(EXIT[p.exit_reason] || "") : p.sell_at_open_on ? '<span class="down">Selling at open</span>' : p.last_review ? `<span title="${esc(p.last_review.reason)}">${esc(p.last_review.action === "HOLD" ? "Hold" : "Sell")}</span>` : "–"}</td>
    </tr>`).join("")}</tbody></table></div>`;
}

function openSection() {
  const all = state.dash.open.filter((p) => p.entry_price && p.sessions_held > 0);
  if (!all.length) return "";
  const f = state.openFilter;
  const rows = all.filter((p) => f === "all" || p.model === f).sort((a, b) => (b.ret ?? 0) - (a.ret ?? 0));
  const tab = (val, label) => `<button type="button" data-openfilter="${val}" aria-pressed="${f === val}">${esc(label)}</button>`;
  return `<section id="open"><h2>Open positions</h2>
    <p class="lede">Still in play. Each model reviews these every night and says hold or sell.</p>
    <div class="toolbar"><div class="tabs" role="group" aria-label="Model">${tab("all", "All")}${state.dash.meta.models.map((m) => tab(m.key, m.display_name)).join("")}</div></div>
    ${positionTable(rows)}</section>`;
}

function closedSection() {
  const rows = state.dash.closed.slice(0, 30);
  if (!rows.length) return "";
  return `<section id="closed"><h2>Recently closed</h2>
    <p class="lede">The last ${rows.length} trades to finish, newest first.</p>${positionTable(rows)}</section>`;
}

// ------------------------------------------------------------------ idea board
function ideasSection() {
  const byModel = {};
  state.dash.ideas.forEach((r) => (byModel[r.model] ||= []).push(r));
  const cols = state.dash.meta.models.filter((m) => byModel[m.key]).map((m) => {
    const [latest, prev] = byModel[m.key];
    return `<div><div class="col-head" style="--c:${m.color}"><h3>${esc(m.display_name)}</h3><p>${longDate(latest.date)}</p></div>
      ${latest.market_view ? `<blockquote class="view">${esc(latest.market_view)}</blockquote>` : ""}
      <ul>${(latest.lessons || []).map((l) => `<li>${esc(l)}</li>`).join("")}</ul>
      ${prev?.lessons?.length ? `<p class="when">The night before:</p><ul>${prev.lessons.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>` : ""}</div>`;
  }).join("");
  if (!cols) return "";
  return `<section id="ideas"><h2>Idea board</h2>
    <p class="lede">Before picking, each model reads its own results and writes down what it learned. Those lessons go into its next night's briefing.</p>
    <div class="ideas">${cols}</div></section>`;
}

// ------------------------------------------------------------------ rules
function rulesSection() {
  const m = state.dash.meta;
  const b = m.buckets;
  const inbox = state.dash.inbox.slice(0, 8);
  return `<section id="rules"><h2>How it works</h2>
    <div class="rules">
      <div>
        <p>Every trading night, Claude, ChatGPT and Grok each read a briefing with their open positions and last results,
          research the market, and upload one file of picks to this site's GitHub repository. A GitHub Action checks
          the file, records when it arrived, and opens the positions.</p>
        <ul>
          <li><strong>${esc(b.moonshot.label)}:</strong> ${esc(b.moonshot.about)} Five a night.</li>
          <li><strong>${esc(b.catalyst.label)}:</strong> ${esc(b.catalyst.about)} Five a night.</li>
          <li><strong>${esc(b.compounder.label)}:</strong> ${esc(b.compounder.about)}</li>
        </ul>
        <p>Each pick is a simulated $100 buy at the last close. It's sold when the price touches the stop or target
          (if both happen the same day it counts as the stop), when its time limit runs out, or at the next open
          when the model says sell. Picks under $1, under 500K average volume, or not on NYSE/Nasdaq are voided.
          Uploads after 11:59 PM ET don't count.</p>
      </div>
      <div>
        <h3>Latest uploads</h3>
        <ul class="inbox">${inbox.map((u) => `<li><span class="chip ${u.status === "ok" ? "target" : u.status === "partial" ? "" : "stop"}">${esc(u.status)}</span>
          ${esc(model(u.model).display_name)} <span class="muted">${new Date(u.received_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</span>
          ${u.errors.length ? `<br><small class="muted">${esc(u.errors[0])}${u.errors.length > 1 ? ` (+${u.errors.length - 1} more)` : ""}</small>` : ""}</li>`).join("") || "<li>None yet.</li>"}</ul>
        <p class="muted">Bots read their briefing at <code>data/brief/&lt;model&gt;.json</code>.</p>
      </div>
    </div></section>`;
}

// ------------------------------------------------------------------ model page
async function renderModel(key) {
  const view = $("#view");
  if (!state.model[key]) {
    view.innerHTML = `<p class="lede">Loading…</p>`;
    state.model[key] = await getJSON(`data/models/${key}.json`);
  }
  const h = state.model[key];
  const m = model(key);
  const rows = Object.fromEntries(Object.keys(state.dash.meta.buckets).map((b) => [b, state.dash.boards.all[b].find((r) => r.model === key)]));
  const all = state.dash.boards.all.all.find((r) => r.model === key);
  const series = Object.entries(rows).filter(([, r]) => r?.equity.length).map(([b, r], i) => ({
    name: bucketLabel(b), color: ["#C2410C", "#2B59C3", "#0F8A6A"][i], points: r.equity.map((p) => ({ x: p.date, y: p.pnl * k() })) }));
  const subs = h.submissions.slice(0, 20).map((s) => `<div class="run-row">
      <header><h3>${longDate(s.target_date)}</h3><span class="${s.status === "ok" ? "" : "down"}">${esc(s.status)}</span></header>
      ${s.market_view ? `<blockquote class="view">${esc(s.market_view)}</blockquote>` : ""}
      ${s.reviews.filter((r) => r.action === "SELL").map((r) => `<p><span class="chip stop">Sell</span> <strong>${esc(r.ticker)}</strong> <span class="serif">${esc(r.reason)}</span></p>`).join("")}
      <ul class="picklist">${s.picks.map((p) => pickRow(p, `h${p.id}`)).join("")}</ul>
      ${s.errors.length ? `<details class="audit"><summary>${s.errors.length} problems</summary><ul>${s.errors.map((e) => `<li>${esc(e)}</li>`).join("")}</ul></details>` : ""}
      <p class="audit"><a href="data/raw/${s.id}.txt" target="_blank" rel="noopener">Raw upload</a></p>
    </div>`).join("");
  view.innerHTML = `<a class="back" href="#/">Back to the arena</a>
    <section><h2>${esc(m.display_name)}</h2>
      <p class="lede">${all && all.positions ? `${all.positions} positions, ${usd(all.total_pnl)} profit, ${plainPct(all.win_rate)} of closed trades won, ${pct(all.avg_alpha)} average vs the S&amp;P 500.` : "No scored positions yet."}</p>
      ${series.length ? `<div class="chart-box">${lineChart(series, { baseline: 0, height: 260, label: "Cumulative profit by book", fmt: (v) => `${v < 0 ? "−" : ""}$${Math.abs(Math.round(v))}` })}
        <div class="legend">${series.map((s) => `<span><span class="swatch" style="background:${s.color}"></span>${esc(s.name)}</span>`).join("")}</div></div>` : ""}
    </section>
    <section><h2>Open positions</h2>${positionTable(h.positions.filter((p) => p.status === "open" && p.sessions_held > 0), false)}</section>
    <section><h2>Nightly uploads</h2><div class="history-runs">${subs || '<p class="lede">None yet.</p>'}</div></section>`;
}

// ------------------------------------------------------------------ events
function bind() {
  const per = $("#per");
  if (per) per.addEventListener("change", () => {
    const v = parseFloat(per.value);
    if (v > 0) { state.per = v; keepScroll(render); $("#per")?.focus(); }
  });
}

function keepScroll(fn) {
  const y = window.scrollY;
  fn();
  window.scrollTo(0, y);
}

document.addEventListener("click", (e) => {
  const t = e.target.closest("[data-pick],[data-bucket],[data-window],[data-openfilter]");
  if (!t) return;
  if (t.dataset.pick) {
    const id = t.dataset.pick;
    state.open.has(id) ? state.open.delete(id) : state.open.add(id);
    keepScroll(render);
    document.querySelector(`[data-pick="${id}"]`)?.focus({ preventScroll: true });
    return;
  }
  const [attr] = Object.keys(t.dataset);
  state[attr === "openfilter" ? "openFilter" : attr] = t.dataset[attr];
  keepScroll(render);
  document.querySelector(`[data-${attr}="${t.dataset[attr]}"]`)?.focus({ preventScroll: true });
});

window.addEventListener("hashchange", () => {
  if (location.hash.startsWith("#/")) { render(); window.scrollTo(0, 0); }
});

load().catch((err) => {
  $("#view").innerHTML = `<div class="empty"><h2>Couldn't load the data</h2><p class="lede">${esc(err.message)}. Reload in a minute; the site updates after each upload and after the close.</p></div>`;
  $("#status").textContent = "";
});
