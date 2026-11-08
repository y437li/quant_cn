// Smoke test (APP_STANDARD §5): open demo companies, sectors and products; click every tab; fail on console errors.
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
await page.screenshot({ path: process.env.SHOT || "smoke.png" });
await browser.close();
if (errors.length) { console.error("CONSOLE ERRORS:\n" + errors.join("\n")); process.exit(1); }
console.log("SMOKE OK");
