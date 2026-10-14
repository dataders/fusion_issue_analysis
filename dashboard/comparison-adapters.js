/* Presentation adapters for same-origin static exports. Data and series colours
   stay with each framework; this coordinates only layout and surrounding ink. */
(() => {
  const states = new WeakMap();
  const supported = new Set(['chartjs', 'graphene', 'ggsql', 'glyf', 'mdv', 'observable', 'observable-live', 'marimo', 'quarto', 'dac', 'shaper', 'duckdb-wasm', 'metricflow', 'mosaic', 'semiotic']);
  const grids = {
    chartjs: ['.grid', '.kpis'],
    graphene: ['.dashboardLayout > div:has(> .echarts)', '.dashboardLayout > div:has(> .big-value)'],
    ggsql: ['section.question', '.kpi-row'],
    glyf: ['.glyf-chart-grid:not(:has(.glyf-kpi-card))', '.glyf-chart-grid:has(.glyf-kpi-card)'],
    mdv: ['.mdv-doc', '.mdv-stat-grid'],
    observable: ['#observablehq-main > .grid.grid-cols-2', '.tiles-kpis'],
    'observable-live': ['#observablehq-main > .grid.grid-cols-2', '.tiles-kpis'],
    marimo: ['div:has(> .marimo-cell)', 'div:has(> marimo-stat)'],
    quarto: ['section.level2:has(> section.level3)', '.kpi-row'],
    'duckdb-wasm': ['.tiles:not(.one)', '.kpis'],
    metricflow: ['.tiles:not(.one)', '.kpis'],
    mosaic: ['.row:has(> .tile)', '.kpi-row'],
    semiotic: ['.row:has(> .tile)', '.kpi-row'],
  };

  function layoutCSS(key) {
    const [charts, kpis] = grids[key] || [];
    let css = charts ? `${charts}{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:16px!important} ${charts} > *{min-width:0!important;max-width:100%}` : '';
    if (kpis) css += `${kpis}{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:12px!important} ${kpis} > *{min-width:0!important;grid-column:auto!important}`;
    if (charts) css += `@media(max-width:759px){${charts}{grid-template-columns:minmax(0,1fr)!important}}`;
    if (kpis) css += `@media(max-width:759px){${kpis}{grid-template-columns:repeat(2,minmax(0,1fr))!important}}@media(max-width:419px){${kpis}{grid-template-columns:minmax(0,1fr)!important}}`;
    if (key === 'ggsql') css += 'section.question > h2,section.question > .tile:has(.kpi-row),section.question > .tile:has(table){grid-column:1/-1}.source code{overflow-wrap:anywhere}';
    if (key === 'glyf') css += '.glyf-chart-grid > *{grid-column:auto!important}.glyf-chart-grid > :has(table){grid-column:1/-1!important}.glyf-main,.glyf-content{min-width:0!important}.glyf-source-drawer{display:none!important}';
    if (key === 'graphene') css += '.dashboardLayout{width:auto!important;max-width:1200px!important;padding:24px!important}.dashboardLayout > div > .echarts{width:100%!important;min-width:0!important}.big-value{flex:initial!important}.table-component,.table-container,.scrollbox{min-width:0;max-width:100%;overflow-x:auto!important}';
    if (key === 'mdv') css += '.mdv-doc > :not(.comparison-mdv-tile),.mdv-doc > .comparison-full{grid-column:1/-1}.mdv-doc{margin:0 auto!important;padding:24px!important;box-sizing:border-box;max-width:1200px}.mdv-chart{margin:12px 0!important}.mdv-chart svg{width:100%;height:auto}.comparison-mdv-tile{overflow:auto}';
    if (key.startsWith('observable')) css += '#observablehq-main .grid > .card{min-width:0!important;max-width:100%}.tiles-table{overflow:auto;max-width:100%}';
    if (key === 'quarto') css += 'section.level2 > h2,section.level2 > .cell,section.level3:has(table){grid-column:1/-1}#quarto-content{display:block!important}#quarto-margin-sidebar{display:none!important}main.content{min-width:0!important}';
    if (key === 'marimo') css += 'div:has(> .marimo-cell) > .marimo-cell:not(:has(marimo-plotly)){grid-column:1/-1}.marimo-cell:empty{display:none!important}.marimo-cell,.output-area,.output{min-width:0!important;max-width:100%!important}.mathjax_ignore > div{padding:24px!important}.mathjax_ignore > div > div:has(> div > .marimo-cell){max-width:1200px!important;min-width:0!important}.marimo-cell:has(#open-issues-by-assignee){grid-column:1/-1}marimo-stat{display:block!important;width:100%;min-width:0}marimo-plotly{min-width:0}';
    if (key === 'dac') css += '.dac-layout .grid{grid-template-columns:repeat(12,minmax(0,1fr))!important}.dac-layout .grid > :has(.dac-metric-border){grid-column:span 4!important}@media(max-width:759px){.dac-layout .grid > :has(.recharts-responsive-container){grid-column:1/-1!important}.dac-layout .grid > :has(.dac-metric-border){grid-column:span 6!important}}@media(max-width:419px){.dac-layout .grid > :has(.dac-metric-border){grid-column:1/-1!important}}';
    return css;
  }

  function paletteCSS(key, dark) {
    const bg = dark ? '#141a21' : '#ffffff';
    const card = dark ? '#1c2530' : '#f7f9fc';
    const ink = dark ? '#e4ebf2' : '#18232f';
    const muted = dark ? '#adbac9' : '#536273';
    const line = dark ? '#394958' : '#d5dee7';
    // Use framework tokens when available. These do not touch mark/data colours.
    let css = `:root{color-scheme:${dark ? 'dark' : 'light'};--comparison-bg:${bg};--comparison-card:${card};--comparison-ink:${ink};--comparison-muted:${muted};--comparison-line:${line};--color-bg:${bg};--color-body:${ink};--color-surface:${card};--color-muted:${muted};--color-border:${line};--color-border-strong:${line};--color-hover:${card};--theme-background:${bg};--theme-background-alt:${card};--theme-foreground:${ink};--theme-foreground-alt:${ink};--theme-foreground-muted:${muted};--theme-foreground-faint:${muted};--theme-foreground-fainter:${line};--theme-foreground-faintest:${card};--bs-body-bg:${bg};--bs-body-color:${ink};--bs-secondary-color:${muted};--bs-border-color:${line}}`;
    if (['graphene','ggsql','mdv','quarto','shaper'].includes(key)) css += `body{background:${bg}!important;color:${ink}!important} h1,h2,h3,h4,.big-value__value,.big-value__title,.table-title__headline,.mdv-stat-value{color:${ink}!important}.subtitle,.source,.blurb,.label,.context,.tile-subtitle,.static-note{color:${muted}!important}.mdv-doc,.table-container,.table-component,.scrollbox{background:${bg}!important;color:${ink}!important}.kpi,.mdv-stat-card,table th,.header-row{background:${card}!important;color:${ink}!important;border-color:${line}!important}td,th{color:${ink}!important;border-color:${line}!important}.mdv-style-note{background:${card}!important;color:${ink}!important;border-color:${line}!important}a{color:${dark ? '#84b8f5' : '#245fac'}!important}`;
    if (key === 'graphene' || key === 'mdv') css += `.echarts svg text,.mdv-chart svg text{fill:${ink}!important}.echarts svg [stroke="#ccc"],.mdv-chart svg [stroke="#e5e5e5"]{stroke:${line}!important}.echarts svg > rect[fill="white"],.mdv-chart svg > rect[fill="white"],.mdv-chart svg > rect[fill="#fff"]{fill:${bg}!important}`;
    if (['chartjs','duckdb-wasm','metricflow','mosaic','semiotic'].includes(key)) css += `:root{--bg:${bg}!important;--card:${card}!important;--text:${ink}!important;--muted:${muted}!important;--faint:${muted}!important;--line:${line}!important;--border:${line}!important;--track:${line}!important}`;
    if (['duckdb-wasm','metricflow','mosaic','semiotic'].includes(key)) css += `.tile svg{color:${ink}!important}.tile svg text{fill:${ink}!important}`;
    if (key === 'shaper') css += `.panel,.metric,.actions a,code,pre{background:${card}!important;color:${ink}!important;border-color:${line}!important}p,ul,.metric span,.eyebrow{color:${muted}!important}`;
    if (key === 'dac') css += `.dac-root{--dac-background:${bg}!important;--dac-surface:${card}!important;--dac-surface-hover:${card}!important;--dac-text-primary:${ink}!important;--dac-text-secondary:${muted}!important;--dac-text-muted:${muted}!important;--dac-border:${line}!important}.recharts-cartesian-axis text{fill:${muted}!important}.recharts-cartesian-grid line{stroke:${line}!important}`;
    return css;
  }

  function prepareMDV(state) {
    const article = state.doc.querySelector('.mdv-doc');
    if (!article || article.querySelector('.comparison-mdv-tile')) return;
    for (const heading of [...article.querySelectorAll(':scope > h3')]) {
      const wrapper = state.doc.createElement('section');
      wrapper.className = 'comparison-mdv-tile';
      article.insertBefore(wrapper, heading);
      let node = heading;
      while (node && (node === heading || !/^H[123]$/.test(node.tagName))) {
        const next = node.nextSibling;
        wrapper.appendChild(node);
        node = next;
      }
      if (wrapper.querySelector('table')) wrapper.classList.add('comparison-full');
      state.cleanup.push(() => wrapper.replaceWith(...wrapper.childNodes));
    }
  }

  // The ggsql and Quarto builders embed JSON literals in vegaEmbed calls. Read
  // those literals without eval; keep their original data, transforms and marks.
  function embeddedSpecs(doc) {
    const results = [];
    for (const script of doc.querySelectorAll('script:not([src])')) {
      const text = script.textContent;
      const re = /vegaEmbed\(\s*['"]([^'"]+)['"]\s*,\s*(?=\{)/g;
      for (const match of text.matchAll(re)) {
        const start = match.index + match[0].length;
        let depth = 0, quoted = false, escaped = false;
        for (let i = start; i < text.length; i++) {
          const c = text[i];
          if (quoted) { if (escaped) escaped = false; else if (c === '\\') escaped = true; else if (c === '"') quoted = false; }
          else if (c === '"') quoted = true;
          else if (c === '{') depth++;
          else if (c === '}' && --depth === 0) {
            try { results.push({selector: match[1], spec: JSON.parse(text.slice(start, i + 1))}); } catch (_) { /* non-JSON embeds stay native */ }
            break;
          }
        }
      }
    }
    return results;
  }

  function syncVega(state) {
    if (!['ggsql','quarto','glyf'].includes(state.key) || typeof state.win.vegaEmbed !== 'function') return;
    const dark = state.appearance === 'dark';
    let specs = state.specs;
    if (!specs) {
      specs = state.key === 'glyf' ? [...state.doc.querySelectorAll('[data-vega-chart]')].map(el => ({el, spec: JSON.parse(state.doc.getElementById(el.dataset.vegaChart).textContent)})) : embeddedSpecs(state.doc);
      if (!specs.length) return;
      state.specs = specs;
    }
    if (state.vegaAppearance === state.appearance) return;
    state.vegaAppearance = state.appearance;
    for (const item of specs) {
      const el = item.el || state.doc.querySelector(item.selector);
      if (!el) continue;
      const spec = JSON.parse(JSON.stringify(item.spec));
      const ink = dark ? '#e4ebf2' : '#18232f', line = dark ? '#394958' : '#d5dee7';
      spec.background = 'transparent';
      spec.width = 'container';
      spec.autosize = {type:'fit', contains:'padding', resize:true};
      spec.config ||= {};
      for (const [key, values] of Object.entries({axis:{labelColor:ink,titleColor:ink,domainColor:line,tickColor:line,gridColor:line},legend:{labelColor:ink,titleColor:ink},title:{color:ink,subtitleColor:ink},view:{stroke:line}})) spec.config[key] = {...spec.config[key],...values};
      // Serialize renders per container: a slow old theme cannot overwrite the
      // most recently selected appearance or finalize its replacement view.
      const appearance = state.appearance;
      const job = (state.vegaJobs.get(el) || Promise.resolve()).catch(() => {}).then(async () => {
        if (!state.active || state.appearance !== appearance) return;
        state.views.get(el)?.finalize();
        state.views.delete(el);
        const result = await state.win.vegaEmbed(el,spec,{actions:false,renderer:'svg'});
        if (!state.active) result.finalize();
        else state.views.set(el,result);
      }).catch(() => { /* keep the framework's own error display */ });
      state.vegaJobs.set(el,job);
    }
  }


  function syncChartJS(state) {
    if (state.key !== 'chartjs' || !state.win.Chart?.instances) return;
    const ink = state.appearance === 'dark' ? '#e4ebf2' : '#18232f';
    const line = state.appearance === 'dark' ? '#394958' : '#d5dee7';
    for (const chart of Object.values(state.win.Chart.instances)) {
      if (state.chartAppearances.get(chart) === state.appearance) continue;
      state.chartAppearances.set(chart,state.appearance);
      if (!state.chartOptions.has(chart)) {
        const original = chart.config.options;
        state.chartOptions.set(chart, original);
        state.cleanup.push(() => { if (chart.ctx) { chart.config.options = original; chart.update('none'); } });
      }
      const original = state.chartOptions.get(chart);
      chart.config.options = {...original, color:ink,
        plugins:{...original.plugins,legend:{...original.plugins?.legend,labels:{...original.plugins?.legend?.labels,color:ink}}},
        scales:Object.fromEntries(Object.entries(original.scales || {}).map(([id,scale]) => [id,{...scale,ticks:{...scale.ticks,color:ink},title:{...scale.title,color:ink},grid:{...scale.grid,color:line},border:{...scale.border,color:line}}]))};
      chart.update('none');
    }
  }


  function syncMarimo(state) {
    if (state.key !== 'marimo') return;
    const dark = state.appearance === 'dark';
    state.doc.body.classList.toggle('dark',dark);
    state.doc.body.classList.toggle('dark-theme',dark);
    state.doc.body.classList.toggle('light',!dark);
    state.doc.body.classList.toggle('light-theme',!dark);
    state.doc.body.setAttribute('data-theme',state.appearance);
    for (const host of state.doc.querySelectorAll('marimo-stat,marimo-plotly,marimo-table')) {
      const root = host.shadowRoot;
      if (!root) continue;
      if (!state.shadows.has(root)) {
        state.shadows.set(root,true);
        state.observer.observe(root,{childList:true,subtree:true});
        const style = state.doc.createElement('style');
        style.textContent = ':host{min-width:0!important;max-width:100%}.min-w-48{min-width:0!important}.js-plotly-plot{width:100%!important}';
        root.appendChild(style);
        state.cleanup.push(() => style.remove());
      }
      const themeRoot = root.querySelector('.contents.light,.contents.dark');
      if (themeRoot && !state.shadows.has(themeRoot)) {
        const original = themeRoot.className;
        state.shadows.set(themeRoot,true);
        state.cleanup.push(() => {themeRoot.className=original;});
      }
      themeRoot?.classList.toggle('dark',dark);
      themeRoot?.classList.toggle('light',!dark);
      const graph = root.querySelector('.js-plotly-plot');
      if (!graph?.layout || !state.win.Plotly) continue;
      if (!state.plotlyLayouts.has(graph)) {
        const original = JSON.parse(JSON.stringify(graph.layout));
        state.plotlyLayouts.set(graph,original);
        state.cleanup.push(() => {
          (state.plotlyJobs.get(graph) || Promise.resolve()).catch(() => {}).then(() => {
            if (!states.has(state.frame) && state.frame.contentDocument === state.doc && graph.isConnected) return state.win.Plotly.relayout(graph,original);
          }).catch(() => {});
        });
        const resize = new state.win.ResizeObserver(() => {
          if (state.active && graph.isConnected) state.win.Plotly.Plots.resize(graph);
        });
        resize.observe(graph);
        state.disposers.push(() => resize.disconnect());
      }
      if (state.plotlyAppearances.get(graph) === state.appearance) continue;
      state.plotlyAppearances.set(graph,state.appearance);
      const ink = dark ? '#e4ebf2' : '#18232f', line = dark ? '#394958' : '#d5dee7';
      const layout = {paper_bgcolor:dark?'#141a21':'#ffffff',plot_bgcolor:dark?'#141a21':'#ffffff','font.color':ink,autosize:true,width:null,'legend.font.color':ink};
      for (const axis of Object.keys(graph.layout).filter(key => /^[xy]axis[0-9]*$/.test(key))) {
        for (const [part,value] of Object.entries({'color':ink,'tickfont.color':ink,'title.font.color':ink,'gridcolor':line,'zerolinecolor':line})) layout[`${axis}.${part}`]=value;
      }
      const appearance = state.appearance;
      const job = (state.plotlyJobs.get(graph) || Promise.resolve()).catch(() => {}).then(() => {
        if (state.active && state.appearance === appearance && graph.isConnected) return state.win.Plotly.relayout(graph,layout);
      }).catch(() => {});
      state.plotlyJobs.set(graph,job);
    }
  }

  window.applyComparisonAdapter = function(iframe, options) {
    const key = iframe.dataset.framework;
    let doc, win;
    try { doc = iframe.contentDocument; win = iframe.contentWindow; if (!doc?.body) return null; } catch (_) { return {theme:false,layout:false,note:'This external dashboard controls its own appearance.'}; }
    let state = states.get(iframe);
    if (state && (state.doc !== doc || state.key !== key || !options.comparison)) {
      state.active = false;
      state.observer?.disconnect(); state.resize?.disconnect();
      for (const dispose of state.disposers) dispose();
      state.style.remove();
      if (state.doc === doc) {
        for (const cleanup of state.cleanup.reverse()) cleanup();
        if (state.originalTheme === null) state.doc.documentElement.removeAttribute('data-theme');
        else state.doc.documentElement.setAttribute('data-theme',state.originalTheme);
        const previousState = state;
        Promise.allSettled([...state.vegaJobs.values()]).then(() => {
          // Leaving comparison may be followed immediately by another selection.
          if (states.has(iframe) || iframe.contentDocument !== previousState.doc) return;
          for (const item of previousState.specs || []) {
            const el = item.el || previousState.doc.querySelector(item.selector);
            let originalSpec = item.spec;
            if (previousState.key === 'glyf' && previousState.win.glyfVegaTheme) originalSpec = previousState.win.glyfVegaTheme(JSON.parse(JSON.stringify(item.spec)),previousState.originalTheme === 'dark');
            if (el && previousState.win.vegaEmbed) previousState.win.vegaEmbed(el,originalSpec,{actions:false,renderer:'svg'}).catch(() => {});
          }
        });
      }
      states.delete(iframe); state = null;
    }
    if (!options.comparison || !supported.has(key)) return null;
    if (!state) {
      const style = doc.createElement('style'); style.id = 'comparison-adapter'; doc.head.appendChild(style);
      state = {doc,win,key,style,frame:iframe,active:true,cleanup:[],disposers:[],views:new Map(),chartOptions:new Map(),chartAppearances:new Map(),vegaJobs:new Map(),shadows:new Map(),plotlyLayouts:new Map(),plotlyAppearances:new Map(),plotlyJobs:new Map(),originalTheme:doc.documentElement.getAttribute('data-theme')};
      states.set(iframe,state);
      const update = () => {
        if (!state.active) return;
        if (key === 'mdv') prepareMDV(state);
        syncVega(state);
        syncChartJS(state);
        syncMarimo(state);
      };
      let queued = false;
      state.observer = new win.MutationObserver(() => {
        if (queued) return; queued = true;
        win.requestAnimationFrame(() => {queued=false;update();});
      });
      state.observer.observe(doc.body,{childList:true,subtree:true});
      state.resize = new win.ResizeObserver(() => {
        for (const [el,result] of state.views) {
          const width = Math.max(180,el.parentElement.clientWidth - 24);
          if (result.view.width() !== width) result.view.width(width).resize().runAsync();
        }
      });
      state.resize.observe(doc.documentElement);
      const media = win.matchMedia('(prefers-color-scheme: dark)');
      media.addEventListener('change',update);
      state.disposers.push(() => media.removeEventListener('change',update));
      if (key === 'marimo') {
        const themeClass = doc.body.className;
        const themeAttr = doc.body.getAttribute('data-theme');
        state.cleanup.push(() => {doc.body.className=themeClass; if(themeAttr===null) doc.body.removeAttribute('data-theme'); else doc.body.setAttribute('data-theme',themeAttr);});
      }
    }
    state.appearance = options.appearance === 'dark' ? 'dark' : 'light';
    state.style.textContent = layoutCSS(key) + paletteCSS(key,state.appearance === 'dark');
    if (key === 'glyf') doc.documentElement.setAttribute('data-theme',state.appearance);
    if (key === 'mdv') prepareMDV(state);
    syncVega(state);
    syncChartJS(state);
    syncMarimo(state);
    return key === 'shaper' ? {theme:true,layout:false,note:'Source preview — no charts to reflow.'} : {theme:true,layout:true};
  };
})();
