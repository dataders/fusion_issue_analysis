const { test, expect } = require('@playwright/test');

// Exercise the shell independently of generated dashboards and network data.
// Tall same-origin fixtures make linked scrolling deterministic.
test.beforeEach(async ({ page }) => {
  await page.route('**/*', async route => {
    const request = route.request();
    if (request.isNavigationRequest() && request.frame().parentFrame()) {
      return route.fulfill({ contentType: 'text/html', headers: { 'Cross-Origin-Embedder-Policy': 'credentialless' }, body: '<!doctype html><html><body style="margin:0;height:4000px"><h1>Dashboard fixture</h1><input aria-label="Dashboard filter"></body></html>' });
    }
    if (new URL(request.url()).hostname !== '127.0.0.1') return route.abort();
    return route.continue();
  });
});

test('picker searches, supports keyboard selection, and retains legacy links', async ({ page }) => {
  await page.goto('/index.html?tab=prefab-windows-2000');
  await expect(page.locator('#frame')).toHaveAttribute('src', 'prefab/app_windows_2000.html');
  await page.getByRole('button', { name: 'Choose dashboard framework' }).click();
  await page.getByRole('searchbox').fill('no such framework');
  await expect(page.getByText('No frameworks found.')).toBeVisible();
  await page.getByRole('searchbox').fill('tanstack');
  await page.keyboard.press('ArrowDown');
  await expect(page.getByRole('button', { name: 'TanStack Charts', exact: true })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.locator('#frame')).toHaveAttribute('src', 'tanstack/dist/');
  await expect(page.locator('#framework-picker')).toBeHidden();
  await expect(page.locator('#picker-toggle')).toBeFocused();
  await expect(page).not.toHaveURL(/theme=/);
  await page.locator('#picker-toggle').click();
  await page.keyboard.press('Escape');
  await expect(page.locator('#picker-toggle')).toHaveAttribute('aria-expanded', 'false');
});

test('comparison keeps independent dashboards, shares state, and supports three panes', async ({ page }) => {
  await page.goto('/index.html?tab=prefab&theme=myspace');
  await page.getByRole('button', { name: 'Compare frameworks' }).click();
  await expect(page.locator('#panes iframe')).toHaveCount(2);
  await page.getByLabel('Framework 2').selectOption('chartjs');
  await page.frameLocator('#frame').getByLabel('Dashboard filter').fill('keep my filter');
  await page.getByRole('button', { name: '+ Add third' }).click();
  await page.getByLabel('Framework 3').selectOption('tanstack');
  await expect(page.frameLocator('#frame').getByLabel('Dashboard filter')).toHaveValue('keep my filter');
  await expect(page.locator('#panes iframe')).toHaveCount(3);
  await expect(page.getByRole('button', { name: '+ Add third' })).toBeHidden();
  await page.getByLabel('Layout').selectOption('stacked');
  await page.getByLabel('Link scroll').check();
  await expect(page).toHaveURL(/compare=chartjs%2Ctanstack/);
  await expect(page).toHaveURL(/layout=stacked/);
  await expect(page).toHaveURL(/scroll=linked/);
  await page.reload();
  await expect(page.locator('#panes iframe')).toHaveCount(3);
  await expect(page.locator('#frame')).toHaveAttribute('src', 'prefab/app_myspace.html');
  await expect(page.getByLabel('Framework 2')).toHaveValue('chartjs');
  await expect(page.getByLabel('Framework 3')).toHaveValue('tanstack');
  await expect(page.getByLabel('Link scroll')).toBeChecked();
  await page.getByRole('button', { name: 'Remove comparison 2' }).click();
  await expect(page.getByLabel('Framework 2')).toHaveValue('tanstack');
  await page.locator('.comparison-pane .view-only').click();
  await expect(page.locator('#panes iframe')).toHaveCount(1);
  await expect(page.locator('#frame')).toHaveAttribute('src', 'tanstack/dist/');
  await expect(page).not.toHaveURL(/compare=|layout=|scroll=|theme=/);
});

test('normalizes invalid comparison URLs and avoids duplicate frameworks when switching', async ({ page }) => {
  await page.goto('/index.html?tab=chartjs&compare=unknown,about,chartjs,tanstack,tanstack');
  await expect(page.locator('#panes iframe')).toHaveCount(2);
  await page.locator('#picker-toggle').click();
  await page.getByRole('button', { name: 'TanStack Charts', exact: true }).click();
  await expect(page.locator('#frame')).toHaveAttribute('src', 'tanstack/dist/');
  await expect(page.getByLabel('Framework 2')).toHaveValue('chartjs');
  await page.getByRole('button', { name: 'Exit comparison' }).click();
  await expect(page.locator('#panes iframe')).toHaveCount(1);
  await expect(page).not.toHaveURL(/compare=/);
});

test('linked scrolling follows relative position and can be turned off', async ({ page }) => {
  await page.goto('/index.html?tab=chartjs&compare=tanstack&scroll=linked');
  await expect(page.frameLocator('.comparison-pane iframe').getByRole('heading')).toBeVisible();
  await page.locator('#frame').evaluate(frame => { frame.contentDocument.scrollingElement.scrollTop = 1200; });
  await expect.poll(() => page.locator('#panes iframe').evaluateAll(frames => {
    const ratios = frames.map(frame => {
      const root = frame.contentDocument.scrollingElement;
      return root.scrollTop / (root.scrollHeight - root.clientHeight);
    });
    return Math.abs(ratios[0] - ratios[1]);
  })).toBeLessThan(0.001);
  const previousTop = await page.locator('.comparison-pane iframe').evaluate(frame => frame.contentDocument.scrollingElement.scrollTop);
  await page.getByLabel('Link scroll').uncheck();
  await page.locator('#frame').evaluate(frame => { frame.contentDocument.scrollingElement.scrollTop = 2000; });
  // Wait for the source scroll event, then assert independent position.
  await expect.poll(() => page.locator('#frame').evaluate(frame => frame.contentDocument.scrollingElement.scrollTop)).toBe(2000);
  await expect.poll(() => page.locator('.comparison-pane iframe').evaluate(frame => frame.contentDocument.scrollingElement.scrollTop)).toBe(previousTop);
});

test('mobile comparisons stack without overflowing and picker fits the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/index.html?tab=chartjs&compare=tanstack');
  await expect(page.locator('#panes')).toHaveCSS('flex-direction', 'column');
  await page.locator('#picker-toggle').click();
  const metrics = await page.evaluate(() => ({
    width: document.documentElement.scrollWidth,
    viewport: innerWidth,
    right: document.getElementById('framework-picker').getBoundingClientRect().right,
  }));
  expect(metrics.width).toBeLessThanOrEqual(metrics.viewport);
  expect(metrics.right).toBeLessThanOrEqual(metrics.viewport);
});

test('copy comparison link offers a usable fallback when clipboard is unavailable', async ({ page }) => {
  await page.goto('/index.html?tab=chartjs&compare=tanstack');
  await page.evaluate(() => { Object.defineProperty(navigator, 'clipboard', { value: undefined }); });
  await page.getByRole('button', { name: 'Copy comparison link' }).click();
  await expect(page.getByRole('textbox', { name: 'Comparison link', exact: true })).toHaveValue(page.url());
  await expect(page.getByRole('status')).toHaveText('Copy the selected link');
});
