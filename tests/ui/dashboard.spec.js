const { expect, test } = require("@playwright/test");

const DASHBOARD_TABS = [
  { label: "Prefab", tab: "prefab", src: "prefab/app.html" },
  { label: "ggsql + Vega-Lite", tab: "ggsql", src: "ggsql/index.html" },
  { label: "mviz", tab: "mviz", src: "mviz/index.html" },
  { label: "MDV", tab: "mdv", src: "mdv/index.html" },
  { label: "Observable", tab: "observable", src: "observable/dist/" },
  { label: "Evidence.dev", tab: "evidence", src: "evidence/build/" },
  { label: "Marimo", tab: "marimo", src: "marimo.html" },
  { label: "Quarto", tab: "quarto", src: "quarto/index.html" },
  { label: "DAC", tab: "dac", src: "dac/build/" },
  { label: "Shaper", tab: "shaper", src: "shaper/index.html" },
  { label: "DuckDB WASM", tab: "duckdb-wasm", src: "duckdb-wasm/index.html" },
  { label: "Mosaic", tab: "mosaic", src: "mosaic/dist/" },
  { label: "Observable (live)", tab: "observable-live", src: "observable/dist/live.html" },
  { label: "About", tab: "about", src: "about.html" },
];

const PREFAB_THEMES = [
  { label: "Vanilla", theme: "vanilla", src: "prefab/app.html" },
  { label: "Reactive", theme: "reactive", src: "prefab/app_reactive.html" },
  { label: "MySpace", theme: "myspace", src: "prefab/app_myspace.html" },
  { label: "Windows 2000", theme: "windows-2000", src: "prefab/app_windows_2000.html" },
];

const requireBuiltArtifacts = process.env.CI || process.env.UI_TEST_REQUIRE_BUILDS === "1";

async function expectRouteToExist(request, path) {
  const response = await request.get(path);
  if (!response.ok() && !requireBuiltArtifacts) {
    test.skip(true, `Missing generated artifact ${path}; run make build or set UI_TEST_REQUIRE_BUILDS=1.`);
  }
  expect(response.status(), `${path} should load`).toBeLessThan(400);
}

async function expectFrameToHaveText(page) {
  await expect
    .poll(
      async () =>
        page.locator("#frame").evaluate((frame) => {
          const text = frame.contentDocument?.body?.innerText || "";
          return text.replace(/\s+/g, " ").trim().length;
        }),
      { message: "active dashboard iframe should render visible text" },
    )
    .toBeGreaterThan(20);
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

test.describe("dashboard bakeoff shell", () => {
  test("shows refresh metadata and source repository link in the chrome", async ({ page }) => {
    await page.goto("/index.html");

    const refreshLabel = page.locator("#data-refreshed");
    await expect(refreshLabel).toHaveText(/^Data refreshed: .+/);
    await expect(refreshLabel).not.toHaveText(/Invalid Date/);

    const repoLink = page.getByRole("link", { name: "Open source repository" });
    await expect(repoLink).toHaveAttribute("href", "https://github.com/dataders/fusion_issue_analysis");
    await expect(repoLink.locator("img")).toHaveAttribute(
      "src",
      "https://github.githubassets.com/favicons/favicon.svg",
    );
  });

  test("keeps one shared tab contract and active style across dashboards", async ({ page, request }) => {
    await page.goto("/index.html");

    await expect(page.locator(".header-title")).toHaveText(
      "dbt-fusion Issue Analysis — Visualization Framework Bakeoff",
    );
    await expect(page.locator("nav.main-tabs")).toHaveAttribute("aria-label", "Dashboard framework");

    const labels = await page.locator(".main-tabs button").evaluateAll((buttons) =>
      buttons.map((button) => ({
        label: button.textContent.trim(),
        tab: button.dataset.tab,
        src: button.dataset.src,
      })),
    );
    expect(labels).toEqual(DASHBOARD_TABS);

    for (const dashboard of DASHBOARD_TABS) {
      await expectRouteToExist(request, dashboard.src);

      const tab = page.locator(`.main-tabs button[data-tab="${dashboard.tab}"]`);
      await tab.click();

      await expect(tab).toHaveClass(/active/);
      await expect(page.locator('#frame')).toHaveAttribute("src", new RegExp(escapeRegExp(dashboard.src)));
      await expect(page).toHaveURL(new RegExp(`[?&]tab=${dashboard.tab}(?:&|#|$)`));
      await expect(page).toHaveURL(new RegExp(`#${dashboard.tab}$`));
      await expectFrameToHaveText(page);

      const styles = await tab.evaluate((button) => {
        const computed = getComputedStyle(button);
        return {
          backgroundColor: computed.backgroundColor,
          borderTopLeftRadius: computed.borderTopLeftRadius,
          color: computed.color,
          fontFamily: computed.fontFamily,
          fontWeight: Number(computed.fontWeight),
          whiteSpace: computed.whiteSpace,
        };
      });
      expect(styles.backgroundColor).toBe("rgb(255, 255, 255)");
      expect(styles.borderTopLeftRadius).toBe("5px");
      expect(styles.fontFamily).toContain("Segoe UI");
      expect(styles.fontWeight).toBeGreaterThanOrEqual(600);
      expect(styles.whiteSpace).toBe("nowrap");

      if (dashboard.tab === "prefab") {
        await expect(page.locator("#prefab-themes")).toBeVisible();
      } else {
        await expect(page.locator("#prefab-themes")).toBeHidden();
      }
    }
  });

  test("keeps the shared shell usable on mobile widths", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/index.html?tab=quarto#quarto");

    await expect(page.locator(".main-tabs")).toBeVisible();
    await expect(page.locator(".main-tabs button[data-tab='quarto']")).toHaveClass(/active/);
    await expect(page.locator("#frame")).toBeVisible();

    const shellMetrics = await page.evaluate(() => ({
      bodyOverflow: getComputedStyle(document.body).overflow,
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    expect(shellMetrics.bodyOverflow).toBe("hidden");
    expect(shellMetrics.documentWidth).toBeLessThanOrEqual(shellMetrics.viewportWidth + 1);
  });
});

test.describe("dashboard UI controls", () => {
  test("switches Prefab themes through the shared selector and deep links", async ({ page, request }) => {
    for (const theme of PREFAB_THEMES) {
      await expectRouteToExist(request, theme.src);
    }

    await page.goto("/index.html?tab=prefab&theme=windows-2000#prefab");

    await expect(page.locator("#prefab-themes")).toBeVisible();
    await expect(page.locator('.main-tabs button[data-tab="prefab"]')).toHaveClass(/active/);
    await expect(page.locator('#prefab-themes button[data-theme="windows-2000"]')).toHaveClass(/active/);
    await expect(page.locator("#frame")).toHaveAttribute("src", /prefab\/app_windows_2000\.html$/);
    await expect(page.locator("#frame")).toHaveAttribute("title", "Prefab Windows 2000");

    await page.locator('#prefab-themes button[data-theme="reactive"]').click();
    await expect(page.locator('#prefab-themes button[data-theme="reactive"]')).toHaveClass(/active/);
    await expect(page.locator("#frame")).toHaveAttribute("src", /prefab\/app_reactive\.html$/);
    await expect(page).toHaveURL(/[?&]tab=prefab/);
    await expect(page).toHaveURL(/[?&]theme=reactive/);

    await page.locator('.main-tabs button[data-tab="mviz"]').click();
    await expect(page.locator("#prefab-themes")).toBeHidden();
    await expect(page.locator("#frame")).toHaveAttribute("src", /mviz\/index\.html$/);
    await expect(page).not.toHaveURL(/theme=/);

    await page.goto("/index.html?tab=prefab-windows-2000");
    await expect(page.locator('#prefab-themes button[data-theme="windows-2000"]')).toHaveClass(/active/);
    await expect(page.locator("#frame")).toHaveAttribute("src", /prefab\/app_windows_2000\.html$/);
  });

  test("opens generated dashboard dropdowns and filters without leaving the bakeoff shell", async ({
    page,
    request,
  }) => {
    await expectRouteToExist(request, "prefab/app_reactive.html");
    await page.goto("/index.html?tab=prefab&theme=reactive#prefab");
    await expectFrameToHaveText(page);

    const frame = page.frameLocator("#frame");
    await expect(frame.getByText("Quick filter:")).toBeVisible();

    const categoryDropdown = frame.getByRole("combobox").filter({ hasText: "Category" });
    await categoryDropdown.click();
    await expect(categoryDropdown).toHaveAttribute("aria-expanded", "true");
    await page.keyboard.press("Escape");
    await expect(frame.getByText(/Showing \d+ of \d+/).first()).toBeVisible();

    await expectRouteToExist(request, "evidence/build/");
    await page.locator('.main-tabs button[data-tab="evidence"]').click();
    await expectFrameToHaveText(page);

    const evidence = page.frameLocator("#frame");
    const menu = evidence.getByLabel("Menu");
    await expect(menu).toBeVisible();
    await menu.click();
    await expect(
      evidence.getByRole("link", { name: "Built with Evidence" }),
    ).toBeVisible();
    await expect(page.locator("#frame")).toHaveAttribute("src", /evidence\/build\/$/);
  });
});
