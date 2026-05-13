const { test, expect } = require("@playwright/test");
const LIVE = !!process.env.MOTHERDUCK_READ_TOKEN;

test.skip(!LIVE, "MOTHERDUCK_READ_TOKEN not set");
test("duckdb-wasm loads live data with all charts", async ({ page }) => {
  const errors = [];
  const consoleLogs = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => consoleLogs.push(`[${m.type()}] ${m.text()}`));

  await page.goto("/duckdb-wasm/index.html");

  // Wait for any non-initial status (done or error)
  await page.waitForFunction(
    () => {
      const s = document.getElementById("status")?.textContent ?? "";
      return !s.includes("Connecting") && !s.includes("Loading");
    },
    { timeout: 30000 }
  );

  const status = await page.locator("#status").textContent();
  const kpis = await page.locator(".kpi-value").allTextContents();
  const svgCount = await page.locator("svg").count();

  console.log("STATUS:", status);
  console.log("KPI VALUES:", kpis);
  console.log("SVG charts:", svgCount);
  if (errors.length) console.log("PAGE ERRORS:", errors);
  if (consoleLogs.some(l => l.includes("error") || l.includes("Error")))
    console.log("CONSOLE ERRORS:", consoleLogs.filter(l => l.toLowerCase().includes("error")));

  expect(errors, "no JS errors").toHaveLength(0);
  expect(kpis.length, "6 KPI cards").toBe(6);
  expect(kpis.some((v) => /\d+/.test(v)), "at least one numeric KPI").toBe(true);
  expect(svgCount, "3 charts rendered").toBeGreaterThanOrEqual(3);
});
