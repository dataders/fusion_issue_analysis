const { test, expect } = require("@playwright/test");
const fs = require("fs/promises");
const path = require("path");
const LIVE = !!process.env.MOTHERDUCK_READ_TOKEN;

test.skip(!LIVE, "MOTHERDUCK_READ_TOKEN not set");
test("mosaic loads live data with charts", async ({ page }) => {
  test.setTimeout(60000);
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });

  // Match deployment's token injection without writing a credential into a file.
  const body = await fs.readFile(path.resolve(__dirname, "../../dashboard/mosaic/index.html"), "utf8");
  await page.route("**/mosaic/index.html", (route) => route.fulfill({
    contentType: "text/html",
    body: body.replaceAll("__MOTHERDUCK_READ_TOKEN__", process.env.MOTHERDUCK_READ_TOKEN),
  }));

  await page.goto("/mosaic/index.html");

  // Wait for status to reach final state
  await page.waitForFunction(
    () => {
      const s = document.getElementById("status")?.textContent ?? "";
      return s.length > 0 && s !== "Connecting…" && !s.includes("Rendering");
    },
    null,
    { timeout: 35000 }
  );

  const status = await page.locator("#status").textContent();
  expect(status, "loaded successfully").toContain("MotherDuck");
  await expect.poll(() => page.locator("#app .tile:has(svg)").count(), { timeout: 20000 }).toBe(7);
  expect(errors.filter(e => /Catalog Error|IPC data batch/.test(e)), "no chart query errors").toHaveLength(0);
  await expect(page.locator("#header .asof strong")).toHaveText(/^\d{4}-\d{2}-\d{2}$/);
});
