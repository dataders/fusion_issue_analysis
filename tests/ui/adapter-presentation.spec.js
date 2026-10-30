const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const dashboards = [
  ['chartjs', 'chartjs/index.html', '.grid'],
  ['graphene', 'graphene/index.html', '.dashboardLayout > div:has(> .echarts)'],
  ['ggsql', 'ggsql/index.html', 'section.question'],
  ['glyf', 'glyf/build/site/dashboards/fusion_issue_health.html', '.glyf-chart-grid:not(:has(.glyf-kpi-card))'],
  ['mdv', 'mdv/index.html', '.mdv-doc'],
  ['observable', 'observable/dist/index.html', '#observablehq-main > .grid.grid-cols-2'],
  ['quarto', 'quarto/index.html', 'section.level2:has(> section.level3)'],
];

for (const [framework, src, grid] of dashboards) {
  test(`${framework} comparison reflows native content and restores standalone styling`, async ({ page }) => {
    test.skip(!fs.existsSync(path.resolve('dashboard', src)), 'Build the framework export first');
    await page.route('**/adapter-test.html', route => route.fulfill({
      contentType:'text/html', body:'<!doctype html><script src="comparison-adapters.js"></script><iframe style="width:620px;height:800px"></iframe>',
    }));
    await page.goto('/adapter-test.html');
    await page.locator('iframe').evaluate((iframe, {framework,src}) => {
      iframe.dataset.framework = framework; iframe.src = src;
    }, {framework,src});
    const frame = page.frameLocator('iframe');
    await expect(frame.locator(grid).first()).toBeVisible();
    await page.evaluate(() => applyComparisonAdapter(document.querySelector('iframe'),{comparison:true,appearance:'dark'}));
    const columns = () => frame.locator(grid).first().evaluate(el => getComputedStyle(el).gridTemplateColumns.split(' ').length);
    await expect.poll(columns).toBe(1);
    await expect.poll(() => frame.locator('html').evaluate(el => el.scrollWidth <= innerWidth + 4)).toBe(true);
    if (framework === 'chartjs') {
      await expect.poll(() => frame.locator('body').evaluate(() => Object.values(window.Chart.instances)[0]?.options.scales.x.ticks.color)).toBe('#e4ebf2');
    }
    await page.locator('iframe').evaluate(el => {el.style.width='1100px';});
    await expect.poll(columns).toBe(2);
    await page.evaluate(() => applyComparisonAdapter(document.querySelector('iframe'),{comparison:true,appearance:'light'}));
    if (framework === 'glyf') await expect(frame.locator('html')).toHaveAttribute('data-theme','light');
    else await expect.poll(() => frame.locator('body').evaluate(el => getComputedStyle(el).color)).toBe('rgb(24, 35, 47)');
    await page.evaluate(() => applyComparisonAdapter(document.querySelector('iframe'),{comparison:false,appearance:'light'}));
    await expect(frame.locator('#comparison-adapter')).toHaveCount(0);
    await expect(frame.locator('.comparison-mdv-tile')).toHaveCount(0);
  });
}

test('DAC comparison uses two KPI columns and one chart per row in a narrow pane', async ({page}) => {
  test.skip(!fs.existsSync(path.resolve('dashboard/dac/build/index.html')), 'Build DAC first');
  await page.route('**/adapter-test.html', route => route.fulfill({contentType:'text/html',body:'<!doctype html><script src="comparison-adapters.js"></script><iframe data-framework="dac" src="dac/build/" style="width:620px;height:800px"></iframe>'}));
  await page.goto('/adapter-test.html');
  const frame=page.frameLocator('iframe');
  await expect(frame.locator('.dac-root')).toBeVisible();
  await page.evaluate(()=>applyComparisonAdapter(document.querySelector('iframe'),{comparison:true,appearance:'dark'}));
  await expect(frame.locator('.grid > :has(.dac-metric-border)').first()).toHaveCSS('grid-column','span 6');
  await expect(frame.locator('.grid > :has(.recharts-responsive-container)').first()).toHaveCSS('grid-column','1 / -1');
  await expect(frame.locator('.dac-root')).toHaveCSS('color','rgb(228, 235, 242)');
});

test('Marimo comparison reflows native Plotly cells and stat cards with the selected theme', async ({page}) => {
  test.skip(!fs.existsSync(path.resolve('dashboard/marimo.html')), 'Build Marimo first');
  await page.route('**/adapter-test.html', route => route.fulfill({contentType:'text/html',body:'<!doctype html><script src="comparison-adapters.js"></script><iframe data-framework="marimo" src="marimo.html" style="width:620px;height:800px"></iframe>'}));
  await page.goto('/adapter-test.html');
  const frame=page.frameLocator('iframe');
  await expect(frame.locator('marimo-stat')).toHaveCount(6);
  await expect(frame.locator('marimo-plotly .js-plotly-plot')).toHaveCount(7);
  await page.evaluate(()=>applyComparisonAdapter(document.querySelector('iframe'),{comparison:true,appearance:'dark'}));
  const columns=selector=>frame.locator(selector).first().evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length);
  await expect.poll(()=>columns('div:has(> .marimo-cell)')).toBe(1);
  await expect.poll(()=>columns('div:has(> marimo-stat)')).toBe(2);
  const plot=frame.locator('marimo-plotly .js-plotly-plot').first();
  await expect.poll(()=>plot.evaluate(el=>el.layout.paper_bgcolor)).toBe('#141a21');
  // marimo re-renders plots with their original figure (e.g. after a resize); the theme must survive it.
  await plot.evaluate(el=>el.ownerDocument.defaultView.Plotly.react(el,el.data,{...el.layout,paper_bgcolor:undefined,plot_bgcolor:undefined}));
  await expect.poll(()=>plot.evaluate(el=>el.layout.paper_bgcolor)).toBe('#141a21');
  await expect(frame.locator('body')).toHaveClass(/dark-theme/);
  await page.locator('iframe').evaluate(el=>{el.style.width='1100px';});
  await expect.poll(()=>columns('div:has(> .marimo-cell)')).toBe(2);
  await expect.poll(()=>columns('div:has(> marimo-stat)')).toBe(3);
  await expect.poll(()=>plot.evaluate(el=>el._fullLayout.width < 600)).toBe(true);
  await page.evaluate(()=>{for(const appearance of ['light','dark','light']) applyComparisonAdapter(document.querySelector('iframe'),{comparison:true,appearance});});
  await expect.poll(()=>plot.evaluate(el=>el.layout.paper_bgcolor)).toBe('#ffffff');
  await page.evaluate(()=>applyComparisonAdapter(document.querySelector('iframe'),{comparison:false,appearance:'light'}));
  await expect(frame.locator('#comparison-adapter')).toHaveCount(0);
  await expect(frame.locator('body')).toHaveClass(/light-theme/);
});

for (const framework of ['duckdb-wasm','mosaic','semiotic']) {
  test(`${framework} selected palette overrides the opposite system theme`, async ({page}) => {
    await page.emulateMedia({colorScheme:'light'});
    await page.route('**/adapter-test.html',route=>route.fulfill({contentType:'text/html',body:`<!doctype html><script src="comparison-adapters.js"></script><iframe data-framework="${framework}" src="${framework}/index.html" style="width:620px;height:800px"></iframe>`}));
    await page.goto('/adapter-test.html');
    const body=page.frameLocator('iframe').locator('body');
    await expect(body).toBeVisible();
    await page.evaluate(()=>applyComparisonAdapter(document.querySelector('iframe'),{comparison:true,appearance:'dark'}));
    await expect(body).toHaveCSS('background-color','rgb(20, 26, 33)');
    await page.emulateMedia({colorScheme:'dark'});
    await page.evaluate(()=>applyComparisonAdapter(document.querySelector('iframe'),{comparison:true,appearance:'light'}));
    await expect(body).toHaveCSS('background-color','rgb(255, 255, 255)');
    await expect(body).toHaveCSS('color','rgb(24, 35, 47)');
  });
}

test('rapid Vega appearance changes finish on the last selected theme',async({page})=>{
  test.skip(!fs.existsSync(path.resolve('dashboard/ggsql/index.html')),'Build ggsql first');
  await page.route('**/adapter-test.html',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><script src="comparison-adapters.js"></script><iframe data-framework="ggsql" src="ggsql/index.html" style="width:620px;height:800px"></iframe>'}));
  await page.goto('/adapter-test.html');
  const frame=page.frameLocator('iframe');
  await expect(frame.locator('section.question').first()).toBeVisible();
  await page.evaluate(()=>{for(const appearance of ['dark','light','dark','light','dark']) applyComparisonAdapter(document.querySelector('iframe'),{comparison:true,appearance});});
  await expect(frame.locator('.role-axis-label text').first()).toHaveAttribute('fill','#e4ebf2');
});
