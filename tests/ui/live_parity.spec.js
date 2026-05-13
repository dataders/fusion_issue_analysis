/**
 * Parity tests: live tabs should have at least as many charts and tables
 * as their static counterparts. Fails fast when a live tab is visually sparse.
 *
 * Requires the local COEP server (./dev.sh) and token injection to be active.
 * MOTHERDUCK_READ_TOKEN must be present in the environment for live tabs to load data.
 */
const { test, expect } = require("@playwright/test");

const LIVE_TIMEOUT = 35000;
const LIVE = !!process.env.MOTHERDUCK_READ_TOKEN;
const MOTHERDUCK_TOKEN = process.env.MOTHERDUCK_READ_TOKEN || "";

/** Intercept HTML/JS responses and inject the read-scaling token in-memory */
async function injectToken(page) {
  if (!MOTHERDUCK_TOKEN) return;
  await page.route("**/*.{html,js}", async (route) => {
    const resp = await route.fetch();
    const body = await resp.text();
    if (body.includes("__MOTHERDUCK_READ_TOKEN__")) {
      await route.fulfill({
        response: resp,
        body: body.replaceAll("__MOTHERDUCK_READ_TOKEN__", MOTHERDUCK_TOKEN),
      });
    } else {
      await route.continue();
    }
  });
}

/** Count SVG charts and HTML tables inside a page URL */
async function countVisuals(page, url, waitForSelector, timeout = 15000) {
  await injectToken(page);
  await page.goto(url);
  if (waitForSelector) {
    await page.waitForSelector(waitForSelector, { timeout }).catch(() => {});
  } else {
    await page.waitForLoadState("networkidle", { timeout }).catch(() => {});
  }
  const svgs   = await page.locator("svg").count();
  const tables = await page.locator("table").count();
  return { svgs, tables, total: svgs + tables };
}

// ── Static baselines (build-time baked) ─────────────────────────────────────

test.describe("static tab baselines", () => {
  test("Observable static renders charts and tables", async ({ page }) => {
    const { svgs, tables } = await countVisuals(page, "/observable/dist/");
    console.log(`Observable static  →  ${svgs} SVGs, ${tables} tables`);
    expect(svgs + tables, "Observable static has visual content").toBeGreaterThan(0);
  });
});

// ── Live tab parity ──────────────────────────────────────────────────────────

test.describe.configure({ mode: "serial" });
test.describe("live tabs match static visual density", () => {
  test.skip(!LIVE, "MOTHERDUCK_READ_TOKEN not set — skipping live parity tests");
  // Observable (live) vs Observable (static): same framework, should be comparable
  test("Observable live ≥ Observable static chart+table count", async ({ page }) => {
    const ref = await countVisuals(page, "/observable/dist/");
    console.log(`Observable static  →  ${ref.svgs} SVGs, ${ref.tables} tables (total ${ref.total})`);

    // Wait for live data to load
    const live = await countVisuals(
      page, "/observable/dist/live.html",
      null,
      LIVE_TIMEOUT
    );
    console.log(`Observable live    →  ${live.svgs} SVGs, ${live.tables} tables (total ${live.total})`);

    // Allow ±2 for Observable Framework chrome SVGs that differ between pages
    expect(
      live.total,
      `Observable live (${live.total}) should be within 2 of static (${ref.total})`
    ).toBeGreaterThanOrEqual(ref.total - 2);
  });

  // DuckDB WASM: 3 charts (velocity line, age dist bar, assignee workload bar)
  // Each Plot.plot() generates ≥1 SVG; wait for the last chart container to render
  test("DuckDB WASM live renders all 3 chart sections", async ({ page }) => {
    const live = await countVisuals(
      page, "/duckdb-wasm/index.html",
      "#chart-workload svg",
      LIVE_TIMEOUT
    );
    console.log(`DuckDB WASM live   →  ${live.svgs} SVGs, ${live.tables} tables (total ${live.total})`);

    expect(live.svgs, "DuckDB WASM has at least 3 charts").toBeGreaterThanOrEqual(3);
  });

  // Mosaic: interactive charts (SVGs) — at least 2
  test("Mosaic live renders at least 2 charts", async ({ page }) => {
    const live = await countVisuals(
      page, "/mosaic/index.html",
      "#app svg",
      LIVE_TIMEOUT
    );
    console.log(`Mosaic live        →  ${live.svgs} SVGs, ${live.tables} tables`);

    expect(live.svgs, "Mosaic has at least 2 charts").toBeGreaterThanOrEqual(2);
  });
});
