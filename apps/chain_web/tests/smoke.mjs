// Smoke test (APP_STANDARD §5): open demo companies, sectors and products; click every tab; open the watchlist, factor monitor and holdings pages; fail on console errors.
import { chromium } from "playwright-core";

const BASE = process.env.APP_URL || "http://127.0.0.1:8787/";
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const companies = ["002714.SZ", "300750.SZ", "002475.SZ", "600519.SH", "601318.SH"];
const sectors = ["270000", "630000", "110000"];
const nodes = ["PROD_PWR_EV_BATTERY", "SEG_FOOD_BAIJIU", "MKT_EV"];

const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
// "no synthesized view" is a documented 404 (openapi.yaml); every other failed response is an error
page.on("response", (r) => { if (r.status() >= 400 && !(r.status() === 404 && r.url().includes("/api/views/"))) errors.push(`${r.status()} ${r.url()}`); });
page.on("console", (m) => { if (m.type() === "error" && !m.text().startsWith("Failed to load resource")) errors.push(m.text()); });
page.on("pageerror", (e) => errors.push(e.message));

async function visit(hash, label, id) {
  await page.goto(BASE + hash);
  await page.waitForSelector(`.dossier[data-sel="${id}"] .head h2`, { timeout: 15000 });
  const title = await page.textContent(".head h2");
  const tabs = await page.$$eval(".tabs button", (bs) => bs.map((b) => b.dataset.tab));
  for (const t of tabs) {
    await page.click(`.tabs button[data-tab="${t}"]`);
    await page.waitForTimeout(150);
  }
  const nodesDrawn = await page.evaluate(() => document.querySelectorAll(".cy canvas").length);
  console.log(`${label}: ${title} · ${tabs.length} tabs · canvas ${nodesDrawn > 0 ? "ok" : "missing"}`);
}

for (const c of companies) await visit(`#co=${c}`, "company " + c, c);
for (const s of sectors) await visit(`#sector=${s}`, "sector " + s, s);
for (const n of nodes) await visit(`#node=${n}`, "node " + n, n);
// search box: type, pick with Enter
await page.goto(BASE);
await page.waitForSelector(".head h2");
await page.fill(".search input", "茅台");
await page.waitForSelector(".results button");
await page.keyboard.press("Enter");
await page.waitForFunction(() => document.querySelector(".head h2")?.textContent === "贵州茅台");
console.log("search: 茅台 → 贵州茅台");
// watchlist page (plan 15 phase 7): header chip, cards, charts with hover, table, back to the graph
await page.click('.side-nav button[data-page="watchlist"]');
await page.waitForSelector(".wl-page[data-wl]", { timeout: 15000 });
const cards = await page.$$eval(".wl-card", (cs) => cs.map((c) => [c.querySelector(".wl-name")?.textContent, c.querySelector(".wl-big")?.textContent, c.querySelector(".wl-gap")?.textContent,
  [...c.querySelectorAll(".wl-kv .wl-v")].slice(1, 3).map((v) => v.textContent).join(" / ")].join(" ")));
for (const c of cards) console.log("watchlist card: " + c);
if (cards.length) {
  const chart = await page.$(".wl-chart svg rect[fill=transparent]");
  if (chart) { const b = await chart.boundingBox(); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2); await page.waitForSelector(".wl-tip"); }
  await page.click(".wl-card .wl-name");
  await page.waitForSelector(".dossier .head h2");
}
console.log(`watchlist: ${cards.length} cards · head "${cards.length ? "ok" : "empty state"}"`);
// structured conditions (plan 15 ph7f): one box per entry with conditions, one chip per condition
await page.goto(BASE + "#watchlist");
await page.waitForSelector(".wl-page[data-wl]", { timeout: 15000 });
const cdBoxes = await page.$$eval(".cd-box", (bs) => bs.map((b) => b.getAttribute("data-condition-status")));
const cdChips = await page.$$eval(".wl-card .cd-chip", (cs) => cs.length);
console.log(`watchlist conditions: ${cdBoxes.length} entries (${cdBoxes.join(", ")}) · ${cdChips} chips`);
// ETF rows (ph7p): tagged, no company link, only the 买入价 field, not in the valuation table
const etfCards = await page.$$eval(".wl-card", (cs) => cs.filter((c) => c.querySelector(".wl-tag")).map((c) => [c.dataset.code, c.querySelector("button.wl-name") ? "link" : "plain", c.querySelectorAll(".wl-kv .wl-v").length, c.querySelector(".wl-big")?.textContent, c.querySelector(".wl-name")?.textContent]));
const etfInTable = await page.$$eval(".wl-section td", (ts, codes) => ts.filter((t) => codes.some((c) => t.textContent === c)).length, etfCards.map((c) => c[4]));
if (etfInTable) throw new Error("ETF rows leaked into the valuation table");
if (etfCards.some(([, link, n]) => link !== "plain" || n !== 1)) throw new Error("ETF card shows stock fields: " + JSON.stringify(etfCards));
console.log(`watchlist ETF rows: ${etfCards.map((c) => c.join(" ")).join(", ") || "none"} · in valuation table ${etfInTable}`);
// 国家队 ETF panel (plan 15 phase 7b), its own page since ph7j: headline, index table rows
await page.goto(BASE + "#etf");
await page.waitForSelector(".ep[data-ep]", { timeout: 15000 });
const ep = await page.$eval(".ep", (e) => [e.getAttribute("data-ep"), e.querySelector(".ep-head")?.textContent ?? "", e.querySelectorAll(".wl-table tbody tr").length]);
const es = await page.$$eval(".es-card", (cs) => cs.map((c) => c.getAttribute("data-style") + ":" + (c.querySelector(".es-status")?.textContent ?? "")));
console.log(`etf styles: ${es.join(", ") || "none"}`);
console.log(`etf proxy: ${ep[0]} indices · ${ep[2]} rows · ${String(ep[1]).slice(0, 40)}`);
const rhythm = await page.$$eval("[data-ep-rhythm] tbody tr", (rs) => rs.map((r) => r.querySelectorAll("td").length));
if (rhythm.length && rhythm.some((n) => n !== 12)) errors.push(`etf rhythm rows have ${rhythm.join("/")} cells, expected 12`);
console.log(`etf rhythm: ${rhythm.length} indices`);
// ph7o: 近3月 line and the weekly flow matrix (one column per index, at most matrix_weeks rows)
const win = await page.$eval(".ep", (e) => e.querySelector("[data-ep-window]")?.textContent ?? "");
const mx = await page.$$eval("[data-ep-matrix] tbody tr", (rs) => rs.map((r) => r.querySelectorAll("td").length));
if (rhythm.length && !win.startsWith("近3月分位")) errors.push("etf 近3月 line missing");
if (rhythm.length && (!mx.length || mx.some((n) => n !== rhythm.length + 1))) errors.push(`etf matrix rows ${mx.join("/")}, expected ${rhythm.length + 1} cells`);
console.log(`etf matrix: ${mx.length} weeks · ${win.slice(0, 40)}`);
await page.goto(BASE + "#watchlist");
await page.waitForSelector(".wl-page[data-wl]", { timeout: 15000 });
await page.setViewportSize({ width: 390, height: 800 });
await page.waitForTimeout(200);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
if (overflow) errors.push("watchlist overflows horizontally at 390px");
await page.screenshot({ path: process.env.SHOT_WL || "smoke-watchlist.png", fullPage: true });
await page.setViewportSize({ width: 1440, height: 900 });
// 因子监控 (plan 15 phase 7c) and 持仓 (phase 7d): open from the chips, pick a factor, hover a chart; no overflow at 390px
await page.goto(BASE + "#watchlist");
await page.click('.side-nav button[data-page="factors"]');
await page.waitForSelector(".fm-page, [data-empty=factors]", { timeout: 15000 });
const fm = await page.$$eval(".fm-table tbody tr", (rs) => rs.length);
if (fm) {
  await page.click(".fm-table tbody tr[data-factor]:nth-child(2)");
  const svg = await page.$(".fm-chart svg rect[fill=transparent]");
  if (svg) { const b = await svg.boundingBox(); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2); await page.waitForSelector(".fm-chart .wl-tip"); }
}
console.log(`factors: ${fm} rows · ${fm ? "ok" : "empty state"}`);
await page.click('.side-nav button[data-page="holdings"]');
await page.waitForSelector(".hr-page, [data-empty=holdings]", { timeout: 15000 });
const hr = await page.$$eval(".hr-page .wl-section:not([data-section=notes]) .fm-table tbody tr[data-code]", (rs) => rs.length);
console.log(`holdings: ${hr} positions · ${hr ? "ok" : "empty state"}`);
// position notes, flags and chips (plan 15 ph7f)
const notes = await page.$$eval("[data-section=notes] tbody tr[data-code]", (rs) => rs.length);
const alerts = await page.$$eval(".pn-alerts li", (ls) => ls.length);
if (hr && !notes) errors.push("holdings: notes section missing");
const firstNote = await page.$(".pn-note summary");
if (firstNote) { await firstNote.click(); await page.waitForSelector(".pn-note[open]"); }
console.log(`holdings notes: ${notes} rows · ${alerts} alerts · ${await page.$$eval(".pn-note .cd-chip", (cs) => cs.length)} condition chips`);
// 宏观监测 (plan 15 ph7h): open from the chip, count cards, hover one chart
await page.click('.side-nav button[data-page="macro"]');
await page.waitForSelector(".mc-page, [data-empty=macro]", { timeout: 15000 });
const mc = await page.$$eval(".mc-card", (cs) => cs.length);
if (mc) {
  const r = await page.$(".mc-chart svg rect[fill=transparent]");
  if (r) { const b = await r.boundingBox(); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2); await page.waitForSelector(".mc-chart .wl-tip"); }
}
console.log(`macro: ${mc} cards · ${mc ? "ok" : "empty state"}`);
// 期货监测 (plan 15 ph7i): open from the sidebar, pick a family, hover a chart, pick a spread
await page.click('.side-nav button[data-page="futures"]');
await page.waitForSelector(".fu-page, [data-empty=futures]", { timeout: 15000 });
const fu = await page.$$eval(".fu-table tbody tr[data-family]", (rs) => rs.length);
if (fu) {
  await page.click(".fu-table tbody tr[data-family]:nth-child(3)");
  const r = await page.$(".fu-charts .mc-chart svg rect[fill=transparent]");
  if (r) { await r.scrollIntoViewIfNeeded(); const b = await r.boundingBox(); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2); await page.waitForSelector(".fu-charts .wl-tip"); }
  const sp = await page.$("[data-section=spreads] tr[data-spread]:nth-child(2)");
  if (sp) await sp.click();
}
// the signal list folds on a click of its summary
const flagsBox = await page.$(".fu-flags summary");
let folded = "none";
if (flagsBox) {
  await flagsBox.scrollIntoViewIfNeeded();
  await flagsBox.click();
  folded = (await page.$eval(".fu-flags", (d) => d.open)) ? "still open" : "folds";
  if (folded !== "folds") errors.push("futures: signal list does not fold");
  await flagsBox.click();
}
console.log(`futures: ${fu} families · ${await page.$$eval(".fu-flags li", (ls) => ls.length)} signals (${folded}) · ${fu ? "ok" : "empty state"}`);
// 波动率监测 (plan 03 ph6): open from the sidebar, count cards, hover one chart
await page.click('.side-nav button[data-page="rates"]');
await page.waitForSelector(".wl-page[data-page=rates], [data-empty=rates]", { timeout: 15000 });
if (await page.$(".wl-page[data-page=rates]")) {
  const bondRows = await page.$$eval(".wl-page[data-page=rates] .rf-table tbody tr", (rs) => rs.length);
  if (bondRows < 5) throw new Error(`rates: ${bondRows} bond rows`);
  await page.click('.wl-page[data-page=rates] button[data-group="汇率"]');
  await page.waitForSelector('.wl-page[data-page=rates] tr[data-row="usdcnh"]', { timeout: 5000 });
  console.log(`rates: ${bondRows} bond rows, FX view ok`);
}
await page.click('.side-nav button[data-page="buyback"]');
await page.waitForSelector(".wl-page[data-page=buyback], [data-empty=buyback]", { timeout: 15000 });
if (await page.$(".wl-page[data-page=buyback]")) {
  const live = await page.$$eval(".wl-page[data-page=buyback] .bb-table tbody tr", (rs) => rs.length);
  if (live < 20) throw new Error(`buyback: ${live} rows`);
  await page.click('.wl-page[data-page=buyback] button[data-kind="increase"]');
  await page.click('.wl-page[data-page=buyback] button[data-loan]');
  const loans = await page.$$eval(".wl-page[data-page=buyback] .bb-table:last-of-type tbody td.bb-loan", (cs) => cs.length);
  console.log(`buyback: ${live} buyback rows; 增持 with loans ${loans}`);
} else console.log("buyback: no document (empty state ok)");
await page.click('.side-nav button[data-page="tasks"]');
await page.waitForSelector(".wl-page[data-page=tasks], [data-empty=tasks]", { timeout: 15000 });
if (await page.$(".wl-page[data-page=tasks]")) {
  const steps = await page.$$eval(".wl-page[data-page=tasks] .tk-table tbody tr", (rs) => rs.length);
  if (steps < 10) throw new Error(`tasks: ${steps} steps`);
  console.log(`tasks: ${steps} steps; ${await page.$eval(".wl-page[data-page=tasks] .wl-head p", (p) => p.textContent)}`);
} else console.log("tasks: no document (empty state ok)");
await page.click('.side-nav button[data-page="opportunities"]');
await page.waitForSelector(".wl-page[data-page=opportunities], [data-empty=opportunities]", { timeout: 15000 });
if (await page.$(".wl-page[data-page=opportunities]")) {
  const picks = await page.$$eval(".wl-page[data-page=opportunities] .op-table tbody tr", (rs) => rs.length);
  if (picks > 15) throw new Error(`opportunities: ${picks} rows > 15`);
  console.log(`opportunities: ${picks} rows; ${await page.$eval(".wl-page[data-page=opportunities] .wl-head p", (p) => p.textContent)}`);
} else console.log("opportunities: no document (empty state ok)");
await page.click('.side-nav button[data-page="volatility"]');
await page.waitForSelector(".wl-page[data-page=volatility], [data-empty=volatility]", { timeout: 15000 });
const vo = await page.$$eval(".wl-page[data-page=volatility] .mc-card", (cs) => cs.length);
if (vo) {
  const r = await page.$(".wl-page[data-page=volatility] .mc-chart svg rect[fill=transparent]");
  if (r) { const b = await r.boundingBox(); await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2); await page.waitForSelector(".wl-page[data-page=volatility] .mc-chart .wl-tip"); }
}
console.log(`volatility: ${vo} cards · ${vo ? "ok" : "empty state"}`);
// 小盘观察 panel (plan 30 ph2): rows present, triggered rows first
const sc = await page.$$eval(".sc-panel .sc-table tbody tr", (rs) => rs.map((r) => r.className));
if (sc.length) {
  const firstOff = sc.findIndex((c) => c !== "sc-on");
  if (firstOff >= 0 && sc.slice(firstOff).includes("sc-on")) errors.push("smallcap: triggered rows are not first");
}
console.log(`smallcap: ${sc.length} rows · ${sc.filter((c) => c === "sc-on").length} triggered`);
// plan 30 ph4: 杠杆 rows and the two margin charts when the watch has margin data
const scMargin = await page.$$eval('[data-panel="smallcap"] tr[data-row^="margin_"]', (rs) => rs.map((r) => r.getAttribute("data-row")));
const mgCharts = await page.$$eval('[data-chart^="margin"] svg', (xs) => xs.length);
if (scMargin.length && (scMargin.length !== 3 || mgCharts !== 2)) errors.push(`smallcap margin: ${scMargin.length} rows, ${mgCharts} charts`);
console.log(`smallcap margin: ${scMargin.join(", ") || "none"} · ${mgCharts} charts`);
// 行业监控 (plan 31 ph5): page renders; with data the sector switch, table and charts are there.
await page.click('.side-nav button[data-page="sector-monitor"]');
await page.waitForSelector(".wl-page[data-page=sector-monitor], [data-empty=sector-monitor]", { timeout: 15000 });
const smTabs = await page.$$eval(".sm-switch button", (bs) => bs.length);
const smCharts = await page.$$eval(".wl-page[data-page=sector-monitor] .sm-card", (cs) => cs.length);
const smRows = await page.$$eval(".sm-table tbody tr", (rs) => rs.length);
if (smTabs && (!smCharts || !smRows)) errors.push("sector-monitor: sectors without charts or table rows");
if (smTabs > 1) { await page.click(".sm-switch button:nth-child(2)"); await page.waitForSelector(".sm-switch button:nth-child(2).on"); }
console.log(`sector-monitor: ${smTabs} sectors · ${smCharts} charts · ${smRows} rows`);
await page.waitForSelector("[data-panel=sector-earnings], [data-empty=sector-earnings]", { timeout: 15000 }).catch(() => null);
const seRows = await page.$$eval("[data-panel=sector-earnings] .se-table tbody tr", (rs) => rs.length).catch(() => 0);
const seEmpty = await page.$("[data-empty=sector-earnings]");
if (!seRows && !seEmpty) errors.push("sector-monitor: 财报季信号 neither rows nor the empty hint");
console.log(`sector earnings: ${seRows} rows`);
for (const [hash, name] of [["#factors", "factors"], ["#macro", "macro"], ["#futures", "futures"], ["#volatility", "volatility"], ["#sector-monitor", "sector-monitor"], ["#holdings", "holdings"]]) {
  await page.goto(BASE + hash);
  await page.waitForSelector(".wl-page", { timeout: 15000 });
  await page.setViewportSize({ width: 390, height: 800 });
  await page.waitForTimeout(200);
  if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1)) errors.push(`${name} overflows horizontally at 390px`);
  if (process.env.SHOT_DIR) await page.screenshot({ path: `${process.env.SHOT_DIR}/smoke-${name}-390.png`, fullPage: true });
  await page.setViewportSize({ width: 1440, height: 900 });
}
// 融资融券 tab (plan 15 ph7m): opens and shows the ladder for a margin stock
await page.goto(BASE + "#co=301358.SZ");
await page.waitForSelector(".dossier .head h2", { timeout: 15000 });
await page.click('.tabs button[data-tab="margin"]');
await page.waitForSelector(".mg-tab, [data-margin-empty]", { timeout: 15000 });
const mg = await page.$$eval(".mg-ladder tbody tr", (rs) => rs.length);
console.log(`margin tab: ${mg} ladder rows · ${mg ? "ok" : "no data"}`);
if (process.env.SHOT_DIR) await page.screenshot({ path: `${process.env.SHOT_DIR}/smoke-margin.png` });
await page.goto(BASE + "#co=002714.SZ");
await page.waitForSelector(".dossier .head h2");
await page.screenshot({ path: process.env.SHOT || "smoke.png" });
await browser.close();
if (errors.length) { console.error("CONSOLE ERRORS:\n" + errors.join("\n")); process.exit(1); }
console.log("SMOKE OK");
