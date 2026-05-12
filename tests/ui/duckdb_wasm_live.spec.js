const { test, expect } = require("@playwright/test");

test("duckdb-wasm loads live data from MotherDuck", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));

  await page.goto("/duckdb-wasm/index.html");

  // Wait for connection + data load (up to 25s — WASM init is slow)
  await expect(page.locator("#status")).not.toContainText("Connecting", { timeout: 25000 });
  await expect(page.locator("#status")).not.toContainText("Loading", { timeout: 5000 });

  const status = await page.locator("#status").textContent();
  const kpis = await page.locator(".kpi-value").allTextContents();

  console.log("STATUS:", status);
  console.log("KPI VALUES:", kpis);
  if (errors.length) console.log("PAGE ERRORS:", errors);

  expect(errors, "no JS errors").toHaveLength(0);
  expect(kpis.length, "6 KPI cards").toBe(6);
  expect(kpis.some((v) => /\d+/.test(v)), "at least one numeric KPI").toBe(true);
});
