const { test, expect } = require('@playwright/test');
test.use({ serviceWorkers: 'block' });

// Exercise the shell independently of generated dashboards and network data.
// Tall same-origin fixtures make linked scrolling deterministic.
test.beforeEach(async ({ page }) => {
  await page.route('**/*', async route => {
    const request = route.request();
    if (/\/comparison-(core|adapters)\.js$/.test(new URL(request.url()).pathname)) return route.fulfill({ contentType: 'text/javascript', body: '' });
    if (request.isNavigationRequest() && request.frame().parentFrame()) {
      return route.fulfill({ contentType: 'text/html', headers: { 'Cross-Origin-Embedder-Policy': 'credentialless' }, body: `<!doctype html><html><style>#scheme-probe {color:black} html[data-appearance="dark"] #scheme-probe{color:white}</style><body style="margin:0;height:${request.url().includes('tanstack') ? 6000 : 4000}px"><h1 id="scheme-probe">Dashboard fixture</h1><input aria-label="Dashboard filter"><script>addEventListener("message", e => {if(e.data?.type === "bakeoff:appearance") document.documentElement.dataset.appearance=e.data.appearance;});</script></body></html>` });
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

test('comparison appearance overrides system for every pane without resetting filters', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/index.html?tab=chartjs&compare=tanstack&appearance=dark');
  await expect(page.getByLabel('Appearance')).toHaveValue('dark');
  await expect(page.frameLocator('#frame').locator('#scheme-probe')).toHaveCSS('color', 'rgb(255, 255, 255)');
  await expect(page.frameLocator('.comparison-pane iframe').locator('#scheme-probe')).toHaveCSS('color', 'rgb(255, 255, 255)');
  await page.frameLocator('#frame').getByLabel('Dashboard filter').fill('retain this');
  await page.getByLabel('Appearance').selectOption('light');
  await expect(page.frameLocator('#frame').locator('#scheme-probe')).toHaveCSS('color', 'rgb(0, 0, 0)');
  await expect(page.frameLocator('.comparison-pane iframe').locator('#scheme-probe')).toHaveCSS('color', 'rgb(0, 0, 0)');
  await expect(page.frameLocator('#frame').getByLabel('Dashboard filter')).toHaveValue('retain this');
  await expect(page).toHaveURL(/appearance=light/);
  await page.reload();
  await expect(page.getByLabel('Appearance')).toHaveValue('light');
  await page.getByLabel('Appearance').selectOption('system');
  await page.emulateMedia({ colorScheme: 'dark' });
  await expect(page.frameLocator('#frame').locator('#scheme-probe')).toHaveCSS('color', 'rgb(255, 255, 255)');
  await page.getByRole('button', { name: '+ Add third' }).click();
  await expect(page.frameLocator('.comparison-pane iframe').last().locator('#scheme-probe')).toHaveCSS('color', 'rgb(255, 255, 255)');
  await page.getByRole('button', { name: 'Exit comparison' }).click();
  await expect(page.getByLabel('Appearance')).toBeHidden();
  await expect(page).not.toHaveURL(/appearance=/);
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

// Unequal KPI and chart heights mirror the Prefab/mviz comparison. Prefab uses
// card-title divs, mviz uses headings; case and punctuation are presentation.
async function semanticFixtures(page, { nested = false } = {}) {
  await page.route('**/*', async route => {
    if (!route.request().isNavigationRequest() || !route.request().frame().parentFrame()) return route.fallback();
    const index = route.request().url().includes('chartjs') ? 0 : route.request().url().includes('tanstack') ? 1 : 2;
    const positions = [[1100, 1700, 2700], [350, 950, 1900], [650, 1200, 2200]][index];
    const html = `<style>html,body{margin:0}${nested ? 'body{overflow:hidden}main{height:100vh;overflow:auto;position:relative}' : ''}
      .content{height:5000px;position:relative}h2,[data-slot]{position:absolute;margin:0;font-size:20px}</style>
      <main><div class="content"><h2 style="top:40px">Where do things stand?</h2>
      <h2 id="backlog" style="top:${positions[0]}px">${index ? 'IS THE BACKLOG SHRINKING?' : 'Is the backlog shrinking?'}</h2>
      <${index ? 'h2' : 'div data-slot="card-title"'} id="chart" style="top:${positions[1]}px">Open issues over time</${index ? 'h2' : 'div'}>
      <h2 id="triage" style="top:${positions[2]}px">Are we keeping up with triage?</h2>
      <div id="table" style="position:absolute;top:3000px;height:100px;overflow:auto"><div style="height:900px">Independent table rows</div></div>
      </div></main>`;
    await route.fulfill({ contentType: 'text/html', headers: { 'Cross-Origin-Embedder-Policy': 'credentialless' }, body: html });
  });
}

async function scrollAnchor(frame, id, offset = 24, nested = false) {
  await frame.evaluate((iframe, { id, offset, nested }) => {
    const doc = iframe.contentDocument;
    const root = nested ? doc.querySelector('main') : doc.scrollingElement;
    root.scrollTop = doc.getElementById(id).offsetTop - offset;
  }, { id, offset, nested });
}

async function expectAligned(page, id, offset = 24) {
  await expect.poll(() => page.locator('#panes iframe').evaluateAll((frames, { id, offset }) =>
    Math.max(...frames.map(frame => Math.abs(frame.contentDocument.getElementById(id).getBoundingClientRect().top - offset))),
  { id, offset })).toBeLessThan(2);
}

test('linked scroll aligns real-style section and chart titles in both directions across three panes', async ({ page }) => {
  await semanticFixtures(page);
  await page.goto('/index.html?tab=chartjs&compare=tanstack,mviz&scroll=linked');
  await expect(page.frameLocator('#frame').locator('#backlog')).toBeAttached();
  await expect(page.locator('#panes iframe')).toHaveCount(3);
  await expect(page.frameLocator('.comparison-pane iframe').first().locator('#backlog')).toBeAttached();
  await scrollAnchor(page.locator('#frame'), 'backlog');
  await expectAligned(page, 'backlog');
  // Halfway between matching titles stays halfway despite different spacing.
  await page.locator('#frame').evaluate(frame => { frame.contentDocument.scrollingElement.scrollTop = 1376; });
  await expect.poll(() => page.locator('.comparison-pane iframe').first().evaluate(frame => frame.contentDocument.scrollingElement.scrollTop)).toBe(626);
  await expect.poll(() => page.locator('.comparison-pane iframe').last().evaluate(frame => frame.contentDocument.scrollingElement.scrollTop)).toBe(901);
  await scrollAnchor(page.locator('#frame'), 'chart');
  await expectAligned(page, 'chart');
  // A follower can immediately become the driver, without a timeout or bounce.
  await scrollAnchor(page.locator('.comparison-pane iframe').last(), 'triage');
  await expectAligned(page, 'triage');
  await page.waitForTimeout(200);
  await expectAligned(page, 'triage');
  // Re-measure after a responsive/content height change.
  await page.locator('#frame').evaluate(frame => { frame.contentDocument.getElementById('chart').style.top = '1900px'; });
  await scrollAnchor(page.locator('#frame'), 'chart');
  await expectAligned(page, 'chart');
});

test('linked scroll supports a main scrolling panel and leaves nested tables independent', async ({ page }) => {
  await semanticFixtures(page, { nested: true });
  await page.goto('/index.html?tab=chartjs&compare=tanstack&scroll=linked');
  await expect(page.frameLocator('.comparison-pane iframe').locator('#backlog')).toBeAttached();
  await scrollAnchor(page.locator('#frame'), 'backlog', 24, true);
  await expectAligned(page, 'backlog');
  await page.locator('#frame').evaluate(frame => { frame.contentDocument.getElementById('table').scrollTop = 200; });
  await page.waitForTimeout(100);
  await expectAligned(page, 'backlog');
  await expect.poll(() => page.locator('.comparison-pane iframe').evaluate(frame => frame.contentDocument.getElementById('table').scrollTop)).toBe(0);
});

test('enabling linked scroll immediately aligns the current chart', async ({ page }) => {
  await semanticFixtures(page);
  await page.goto('/index.html?tab=chartjs&compare=tanstack');
  await expect(page.frameLocator('.comparison-pane iframe').locator('#chart')).toBeAttached();
  await scrollAnchor(page.locator('#frame'), 'chart');
  await page.getByLabel('Link scroll').check();
  await expectAligned(page, 'chart');
});


test('stacked source charts can align with charts sharing one row in the other framework', async ({ page }) => {
  await semanticFixtures(page);
  await page.goto('/index.html?tab=chartjs&compare=tanstack&scroll=linked');
  await expect(page.frameLocator('.comparison-pane iframe').locator('#chart')).toBeAttached();
  await page.locator('.comparison-pane iframe').evaluate(frame => {
    const doc = frame.contentDocument;
    doc.getElementById('chart').style.top = doc.getElementById('backlog').style.top;
  });
  await scrollAnchor(page.locator('#frame'), 'chart');
  await expectAligned(page, 'chart');
});
