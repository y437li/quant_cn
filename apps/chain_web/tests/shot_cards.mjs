// Screenshots of app cards for phone alerts (plan 22, D-153).
// Usage: node shot_cards.mjs <base_url> <json [{page, selector, out, title}]>; prints one line per saved file.
// A phone style is injected: bigger figures, the small range / rule line hidden.
import { chromium } from "playwright-core";
const [, , base, spec] = process.argv;
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PHONE_CSS = [
  ".mc-card > div.mc-month { display: none } .mc-figs b { font-size: 34px } .mc-name { font-size: 18px }",
  // watchlist card: name, price, status, the buy conditions and the price chart with the buy band
  ".wl-card > :not(.wl-row):not(.wl-chart):not(.cd-box) { display: none } .wl-code { display: none }",
].join(" ");
const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage({ viewport: { width: 420, height: 900 }, deviceScaleFactor: 3 });
for (const s of JSON.parse(spec)) {
  try {
    await page.goto(base + s.page);
    await page.waitForSelector(s.selector, { timeout: 15000 });
    await page.addStyleTag({ content: PHONE_CSS });
    if (s.title) {
      // plain-language title, no percentile figure (plan 22: no jargon for the recipient)
      await page.$eval(s.selector, (el, t) => {
        const n = el.querySelector(".mc-name");
        if (n) n.textContent = t;
        el.querySelectorAll(".mc-pct").forEach((p) => (p.style.display = "none"));
      }, s.title);
    }
    await page.waitForTimeout(400);
    await (await page.$(s.selector)).screenshot({ path: s.out });
    console.log("saved " + s.out);
  } catch (e) {
    console.log("failed " + s.out + " " + String(e).slice(0, 120));
  }
}
await browser.close();
