// Smoke test (APP_STANDARD §5): open demo companies, sectors and products; click every tab; open the watchlist; fail on console errors.
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
await page.click('.pages button[data-page="watchlist"]');
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
await page.goto(BASE + "#watchlist");
await page.waitForSelector(".wl-page[data-wl]", { timeout: 15000 });
await page.setViewportSize({ width: 390, height: 800 });
await page.waitForTimeout(200);
const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
if (overflow) errors.push("watchlist overflows horizontally at 390px");
await page.screenshot({ path: process.env.SHOT_WL || "smoke-watchlist.png", fullPage: true });
await page.setViewportSize({ width: 1440, height: 900 });
await page.screenshot({ path: process.env.SHOT || "smoke.png" });
await browser.close();
if (errors.length) { console.error("CONSOLE ERRORS:\n" + errors.join("\n")); process.exit(1); }
console.log("SMOKE OK");
