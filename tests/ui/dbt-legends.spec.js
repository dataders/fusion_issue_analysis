const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
test.use({ serviceWorkers: 'block' });

const colors = {
  '0-7d': '#b7d3f6', '8-30d': '#86b6ef', '31-90d': '#5598e7',
  '91-180d': '#256abf', '180d+': '#104281',
};

for (const theme of ['light', 'dark']) {
  for (const [layout, width] of [['wide', 1000], ['narrow', 600], ['mobile', 360]]) {
    test(`dbt ${theme} ${layout} legends flow horizontally and preserve age colors`, async ({ page }, testInfo) => {
      const file = `fusion-issue-health-${theme}-${layout}.html`;
      test.skip(!fs.existsSync(path.resolve('dashboard/dbt-charts', file)), 'Build dbt Charts layouts first');
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(`/dbt-charts/${file}?appearance=${theme}&comparison=1`);
      const triage = page.locator('[data-chart-id="triage_pipeline_chart"]');
      await expect(triage).toBeAttached();
      const legends = await page.locator('[data-chart-id] .role-legend').evaluateAll(nodes => nodes.map(node => {
        const chart = node.closest('[data-chart-id]');
        const matrix = chart.getScreenCTM();
        const left = new DOMPoint(0, 0).matrixTransform(matrix).x;
        const right = left + Number(chart.dataset.chartWidth) * matrix.a;
        const box = node.getBoundingClientRect();
        return {
          chart: chart.dataset.chartId,
          overflow: Math.max(0, left - box.left, box.right - right),
          labels: [...node.querySelectorAll('.role-legend-label text')].map(label => ({
            text: label.textContent,
            x: label.getBoundingClientRect().x,
            y: label.getBoundingClientRect().y,
            color: label.parentElement.parentElement.querySelector('.role-legend-symbol path').getAttribute('fill'),
          })),
        };
      }));
      for (const legend of legends) {
        expect(legend.overflow, `${legend.chart} legend fits its chart`).toBeLessThan(2);
        if (legend.labels.length > 1) {
          expect(legend.labels.some((label, i) => legend.labels.some((other, j) => i !== j && Math.abs(label.y - other.y) < 1)), `${legend.chart} has multiple entries per row`).toBe(true);
        }
      }
      const age = legends.find(legend => legend.chart === 'triage_pipeline_chart');
      expect(Object.fromEntries(age.labels.map(label => [label.text, label.color]))).toEqual(colors);
      const ageRows = new Set(age.labels.map(label => Math.round(label.y)));
      if (layout === 'mobile') expect(ageRows.size, 'wrap the legend on small cards').toBeGreaterThan(1);
      else expect(ageRows.size, 'keep fitting entries on one row').toBe(1);
      await triage.scrollIntoViewIfNeeded();
      await triage.screenshot({ path: testInfo.outputPath('triage-legend.png') });
    });
  }
}
