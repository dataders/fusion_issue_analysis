const { test, expect } = require("@playwright/test");

test("mosaic loads live data with charts", async ({ page }) => {
  const errors = [];
  const logs = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => logs.push(`[${m.type()}] ${m.text()}`));

  await page.goto("/mosaic/index.html");

  // Wait for status to reach final state
  await page.waitForFunction(
    () => {
      const s = document.getElementById("status")?.textContent ?? "";
      return s.length > 0 && s !== "Connecting…" && !s.includes("Rendering");
    },
    { timeout: 35000 }
  );

  // Mosaic renders SVGs asynchronously after status updates — wait for them
  await page.waitForSelector("#app svg", { timeout: 15000 }).catch(() => {});

  const status = await page.locator("#status").textContent();
  const svgCount = await page.locator("#app svg").count();
  const appHTML = await page.locator("#app").innerHTML().catch(() => "").then(h => h.slice(0, 500));

  console.log("STATUS:", status);
  console.log("SVG count:", svgCount);
  console.log("APP HTML (500 chars):", appHTML);
  const errLogs = logs.filter(l => l.toLowerCase().includes("error") || l.toLowerCase().includes("warn"));
  if (errLogs.length) console.log("ERRORS/WARNINGS:", errLogs.slice(0, 5));
  if (errors.length) console.log("PAGE ERRORS:", errors.slice(0, 3));

  expect(errors, "no JS errors").toHaveLength(0);
  expect(status, "loaded successfully").toContain("MotherDuck");
  expect(svgCount, "charts rendered").toBeGreaterThanOrEqual(2);
});
