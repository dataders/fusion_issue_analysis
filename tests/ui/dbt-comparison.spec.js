const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
test.use({ serviceWorkers: 'block' });

test('dbt Charts and TanStack follow the shell appearance and pane width together', async ({ page }) => {
  test.skip(!fs.existsSync(path.join(__dirname, '../../dashboard/dbt-charts/fusion-issue-health-light-narrow.html')), 'Build dbt Charts layouts first');
  await page.emulateMedia({ colorScheme: 'light' });
  await page.setViewportSize({ width: 1200, height: 1000 });
  await page.goto('/index.html?tab=dbt-charts&compare=tanstack&appearance=dark&scroll=linked');
  const native = page.frameLocator('#frame');
  const tanstack = page.frameLocator('.comparison-pane iframe');
  await expect(native.locator('[data-chart-id]')).toHaveCount(17);
  await expect.poll(() => page.locator('#frame').evaluate(el => el.contentWindow.location.pathname)).toContain('dark-narrow.html');
  await expect(tanstack.locator('.tile').first()).toHaveCSS('background-color', 'rgb(28, 35, 45)');
  await expect.poll(() => tanstack.locator('.tiles').first().evaluate(el => getComputedStyle(el).gridTemplateColumns.split(' ').length)).toBe(1);
  await native.locator('[data-chart-id="backlog_weekly_chart"]').evaluate(el => window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 24));
  await expect.poll(() => tanstack.getByRole('heading', { name: 'Open issues over time', exact: true }).evaluate(el => Math.abs(el.getBoundingClientRect().top - 24))).toBeLessThan(2);
  await page.getByLabel('Appearance').selectOption('light');
  await expect.poll(() => page.locator('#frame').evaluate(el => el.contentWindow.location.pathname)).toContain('light-narrow.html');
  await expect(tanstack.locator('.tile').first()).toHaveCSS('background-color', 'rgb(255, 255, 255)');
  await page.setViewportSize({ width: 2000, height: 1000 });
  await expect.poll(() => page.locator('#frame').evaluate(el => el.contentWindow.location.pathname)).toContain('light-wide.html');
  await expect.poll(() => tanstack.locator('.tiles').first().evaluate(el => getComputedStyle(el).gridTemplateColumns.split(' ').length)).toBe(2);
});

test('dbt Charts changes native layout at comparison breakpoints and follows shared theme', async ({ page }) => {
  test.skip(!fs.existsSync(path.join(__dirname, '../../dashboard/dbt-charts/fusion-issue-health-light-narrow.html')), 'Build dbt Charts layouts first');
  await page.setViewportSize({ width: 600, height: 900 });
  await page.goto('/dbt-charts/fusion-issue-health.html?comparison=1&appearance=light');
  await expect(page).toHaveURL(/light-narrow\.html/);
  const charts = page.locator('[data-chart-id]');
  await expect(charts).toHaveCount(17);
  const box = id => page.locator(`[data-chart-id="${id}"]`).boundingBox();
  const backlog = await box('backlog_weekly_chart');
  const flow = await box('weekly_flow_chart');
  expect(flow.y).toBeGreaterThan(backlog.y + backlog.height - 1);
  const first = await box('kpi_open_issues');
  const second = await box('kpi_opened_closed');
  const third = await box('kpi_awaiting_triage');
  expect(Math.abs(first.y - second.y)).toBeLessThan(1);
  expect(third.y).toBeGreaterThan(first.y);

  await page.setViewportSize({ width: 1000, height: 900 });
  await expect(page).toHaveURL(/light-wide\.html/);
  await expect.poll(async () => Math.abs((await box('backlog_weekly_chart')).y - (await box('weekly_flow_chart')).y)).toBeLessThan(1);

  await page.setViewportSize({ width: 380, height: 900 });
  await expect(page).toHaveURL(/light-mobile\.html/);
  expect((await box('kpi_opened_closed')).y).toBeGreaterThan((await box('kpi_open_issues')).y);
  await page.evaluate(() => window.postMessage({ type: 'bakeoff:appearance', appearance: 'dark', comparison: true }, location.origin));
  await expect(page).toHaveURL(/dark-mobile\.html/);
  await expect(page.locator('meta[name="color-scheme"]')).toHaveAttribute('content', 'only dark');
});
