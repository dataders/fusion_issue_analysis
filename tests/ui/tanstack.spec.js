const { expect, test } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const dataPath = path.resolve(__dirname, '../../dashboard/tanstack/data/tiles.json');
const payload = fs.existsSync(dataPath) ? JSON.parse(fs.readFileSync(dataPath, 'utf8')) : null;
const requireBuild = process.env.CI || process.env.UI_TEST_REQUIRE_BUILDS === '1';
const format = (value) => value == null ? '—' : typeof value === 'number'
  ? new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value) : String(value);

test.beforeEach(async ({ page, request }) => {
  const response = await request.get('/tanstack/dist/');
  if (!requireBuild && (!payload || !response.ok())) test.skip(true, 'Run make tanstack first.');
  expect(payload).not.toBeNull();
  expect(response.ok()).toBeTruthy();
  await page.goto('/index.html?tab=tanstack#tanstack');
});

test('TanStack renders every shared tile, KPI, table row, and chart without runtime errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.reload();
  const frame = page.frameLocator('#frame');
  await expect(page.locator('[data-tab="tanstack"]')).toHaveClass(/active/);
  await expect(frame.getByRole('heading', { level: 1 })).toHaveText(payload.manifest.title);
  await expect(frame.locator('.freshness')).toHaveText(payload.freshness);
  await expect(frame.locator('.kpis strong')).toHaveText(payload.kpis.map((item) => item.value));
  const tiles = payload.manifest.sections.flatMap((section) => section.tiles);
  await expect(frame.locator('[data-tile]')).toHaveCount(tiles.length);
  for (const tile of tiles.filter((tile) => tile.form !== 'kpi_row')) {
    const card = frame.locator(`[data-tile="${tile.id}"]`);
    await expect(card.getByRole('heading', { level: 3 })).toHaveText(tile.title);
    const rows = payload.rows[tile.id];
    if (!rows.length) {
      await expect(card.getByText('No data available.')).toBeVisible();
    } else if (tile.form.startsWith('table')) {
      await expect(card.locator('tbody tr')).toHaveCount(rows.length);
      // Compare displayed values with the dbt snapshot, including issue links.
      const first = card.locator('tbody tr').first();
      for (const [index, column] of tile.columns.entries()) {
        await expect(first.locator('td').nth(index)).toHaveText(
          format(rows[0][column]) + (tile.form === 'table_with_bar' && column === 'pct_complete' && rows[0][column] != null ? '%' : ''),
        );
      }
      await expect(first.locator('a')).toHaveAttribute('href', rows[0][tile.link]);
    } else {
      const svg = card.locator('.chart svg').first();
      await expect(svg).toBeVisible();
      expect(await svg.locator('path, rect, circle').count()).toBeGreaterThan(0);
      const invalid = await svg.evaluate((node) => [...node.querySelectorAll('*')].some(
        (element) => ['d', 'x', 'y', 'width', 'height', 'cx', 'cy'].some(
          (attribute) => /NaN|Infinity/.test(element.getAttribute(attribute) || ''),
        ),
      ));
      expect(invalid, `${tile.id} has finite chart geometry`).toBe(false);
    }
  }
  expect(errors).toEqual([]);
});

test('TanStack preserves palette identity in dark mode and fits a mobile iframe', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.setViewportSize({ width: 390, height: 844 });
  const frame = page.frameLocator('#frame');
  await expect(frame.locator('[data-tile="backlog_weekly"] .swatch').first()).toHaveCSS('background-color', 'rgb(57, 135, 229)');
  await expect(frame.locator('.chart svg')).toHaveCount(7);
  const widths = await frame.locator('body').evaluate((body) => ({
    viewport: window.innerWidth, content: body.scrollWidth,
  }));
  expect(widths.content).toBeLessThanOrEqual(widths.viewport + 1);
  await page.emulateMedia({ colorScheme: 'light' });
  await expect(frame.locator('[data-tile="backlog_weekly"] .swatch').first()).toHaveCSS('background-color', 'rgb(42, 120, 214)');
  await expect(frame.locator('.chart svg')).toHaveCount(7);
});
