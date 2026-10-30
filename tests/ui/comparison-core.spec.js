const {test,expect} = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname,'../..');
test.use({colorScheme:'light'});
const cases = [
  ['prefab','prefab/app.html','[data-bakeoff-grid="charts"]','[data-bakeoff-grid="kpis"]'],
  ['evidence','evidence/build/index.html','article.markdown','article.markdown > .grid'],
  ['mviz','mviz/index.html','.dashboard-section:has([id^="chart_"])','.dashboard-section:has(.textarea-item)'],
  ['tanstack','tanstack/dist/index.html','.tiles','.kpis'],
];
for (const [name,file,chartGrid,kpiGrid] of cases) {
  test(`${name} comparison uses native themes and common reflow breakpoints`,async({page})=>{
    test.skip(!fs.existsSync(path.join(root,'dashboard',file)),`${name} preview not built`);
    await page.setViewportSize({width:1640,height:1000});
    await page.goto(`/index.html?tab=${name}&compare=${name==='tanstack'?'prefab':'tanstack'}&appearance=dark`);
    const frame=page.frameLocator('#frame');
    await expect(frame.locator('html')).toHaveAttribute('data-bakeoff-core',name);
    const columns=async(selector)=>frame.locator(selector).first().evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length);
    await expect.poll(()=>columns(chartGrid)).toBe(2);
    await expect.poll(()=>columns(kpiGrid)).toBe(3);
    if(name==='evidence') await expect(frame.locator('html')).toHaveAttribute('data-theme','dark');
    if(name==='mviz') await expect(frame.locator('body')).toHaveClass(/theme-dark/);
    if(name==='prefab') await expect(frame.locator('html')).toHaveClass(/dark/);
    if(name==='tanstack') {
      await expect(frame.locator('.tile').first()).toHaveCSS('background-color','rgb(28, 35, 45)');
      await expect(frame.locator('.swatch').first()).toHaveCSS('background-color','rgb(57, 135, 229)');
      await expect(frame.locator('svg text').first()).toHaveCSS('fill','rgb(229, 234, 241)');
    }
    await page.setViewportSize({width:1200,height:1000});
    await expect.poll(()=>columns(chartGrid)).toBe(1);
    await expect.poll(()=>columns(kpiGrid)).toBe(2);
    if(name==='tanstack') await frame.locator('h2').nth(1).evaluate(el=>window.scrollTo(0,el.getBoundingClientRect().top+window.scrollY));
    await page.emulateMedia({colorScheme:'dark'});
    await page.selectOption('#appearance','light');
    await expect(frame.locator('body')).toHaveCSS('background-color','rgb(247, 248, 250)');
    if(name==='evidence') await expect(frame.locator('html')).toHaveAttribute('data-theme','light');
    if(name==='mviz') await expect(frame.locator('body')).toHaveClass(/theme-light/);
    if(name==='prefab') await expect(frame.locator('html')).not.toHaveClass(/dark/);
    if(name==='tanstack') {
      await expect.poll(()=>frame.locator('html').evaluate(()=>window.scrollY)).toBeGreaterThan(100);
      await expect(frame.locator('.tile').first()).toHaveCSS('background-color','rgb(255, 255, 255)');
      await expect(frame.locator('.swatch').first()).toHaveCSS('background-color','rgb(42, 120, 214)');
      await expect(frame.locator('svg text').first()).toHaveCSS('fill','rgb(32, 39, 52)');
    }
    await page.setViewportSize({width:390,height:900});
    await expect.poll(()=>columns(kpiGrid)).toBe(1);
    await page.getByRole('button',{name:'Exit comparison',exact:true}).click();
    await expect(frame.locator('html')).not.toHaveAttribute('data-bakeoff-core');
  });
}

test('Prefab decorative and reactive variants retain readable comparison surfaces',async({page})=>{
  for(const theme of ['reactive','myspace','windows-2000']) {
    const file=theme==='windows-2000'?'windows_2000':theme;
    test.skip(!fs.existsSync(path.join(root,'dashboard/prefab',`app_${file}.html`)),'Prefab variants not built');
    await page.setViewportSize({width:1640,height:1000});
    await page.goto(`/index.html?tab=prefab&theme=${theme}&compare=tanstack&appearance=dark`);
    const frame=page.frameLocator('#frame');
    await expect(frame.locator('[data-slot="card"]').first()).toHaveCSS('background-color','rgb(28, 35, 45)');
    const grid=theme==='myspace'?'.pf-app-root':'[data-bakeoff-grid="charts"]';
    await expect.poll(()=>frame.locator(grid).first().evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length)).toBe(2);
    await page.setViewportSize({width:1200,height:1000});
    await expect.poll(()=>frame.locator(grid).first().evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length)).toBe(1);
    await page.selectOption('#appearance','light');
    await expect(frame.locator('[data-slot="card"]').first()).toHaveCSS('background-color','rgb(255, 255, 255)');
    await expect(frame.locator('.recharts-cartesian-axis-tick-labels text').first()).toHaveCSS('fill','rgb(89, 101, 117)');
  }
});
