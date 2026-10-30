/* Native theme bridges and shared comparison breakpoints for the core adapters.
 * All layout rules are scoped; leaving comparison restores the original page.
 */
(() => {
  const states = new WeakMap();
  const css = `
    html[data-bakeoff-core] { --comparison-bg:#f7f8fa; --comparison-surface:#fff; --comparison-text:#202734; --comparison-muted:#596575; --comparison-border:#dce1e8; }
    html[data-bakeoff-core][data-bakeoff-appearance="dark"] { --comparison-bg:#141920; --comparison-surface:#1c232d; --comparison-text:#e5eaf1; --comparison-muted:#acb8c8; --comparison-border:#354151; }
    html[data-bakeoff-core] body { background:var(--comparison-bg)!important; color:var(--comparison-text)!important; }
    html[data-bakeoff-core="tanstack"] .tiles { grid-template-columns:repeat(2,minmax(0,1fr)); }
    html[data-bakeoff-core="tanstack"] .kpis { grid-template-columns:repeat(3,minmax(0,1fr)); }
    html[data-bakeoff-core="prefab"] { --background:var(--comparison-bg); --foreground:var(--comparison-text); --card:var(--comparison-surface); --card-foreground:var(--comparison-text); --muted:var(--comparison-bg); --muted-foreground:var(--comparison-muted); --border:var(--comparison-border); --popover:var(--comparison-surface); --popover-foreground:var(--comparison-text); }
    html[data-bakeoff-core="prefab"] #root { max-width:1440px!important; padding:16px!important; color:var(--comparison-text)!important; }
    html[data-bakeoff-core="prefab"] .pf-app-root { max-width:none!important; padding:0!important; }
    html[data-bakeoff-core="prefab"] [data-slot="card"], html[data-bakeoff-core="prefab"] .pf-card, html[data-bakeoff-core="prefab"] .group-box, html[data-bakeoff-core="prefab"] .window-body, html[data-bakeoff-core="prefab"] .kpi-card { background:var(--comparison-surface)!important; color:var(--comparison-text)!important; min-width:0!important; }
    html[data-bakeoff-core="prefab"] [data-slot="card-title"], html[data-bakeoff-core="prefab"] td, html[data-bakeoff-core="prefab"] th, html[data-bakeoff-core="prefab"] .kpi-value, html[data-bakeoff-core="prefab"] .group-caption { color:var(--comparison-text)!important; }
    html[data-bakeoff-core="prefab"] .win-window, html[data-bakeoff-core="prefab"] .win-panel, html[data-bakeoff-core="prefab"] .win-inset, html[data-bakeoff-core="prefab"] .workspace, html[data-bakeoff-core="prefab"] .menu-bar, html[data-bakeoff-core="prefab"] .status-bar, html[data-bakeoff-core="prefab"] .msgbox { background:var(--comparison-surface)!important; }
    html[data-bakeoff-core="prefab"] p, html[data-bakeoff-core="prefab"] span, html[data-bakeoff-core="prefab"] label, html[data-bakeoff-core="prefab"] .recharts-legend-wrapper div { color:var(--comparison-text)!important; }
    html[data-bakeoff-core="prefab"] .title-bar span { color:#fff!important; }
    html[data-bakeoff-core="prefab"] .kpi-label, html[data-bakeoff-core="prefab"] .kpi-detail, html[data-bakeoff-core="prefab"] .status-mini { color:var(--comparison-muted)!important; }
    html[data-bakeoff-core="prefab"] th, html[data-bakeoff-core="prefab"] td { background:var(--comparison-surface)!important; }
    html[data-bakeoff-core="prefab"] .recharts-cartesian-axis-tick text, html[data-bakeoff-core="prefab"] .recharts-cartesian-axis-tick-labels text { fill:var(--comparison-muted)!important; }
    html[data-bakeoff-core="prefab"] .pf-app-root:has(> .neon-card) { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; }
    html[data-bakeoff-core="prefab"] .pf-app-root:has(> .neon-card) > * { grid-column:1/-1; min-width:0; }
    html[data-bakeoff-core="prefab"] .pf-app-root:has(> .neon-card) > [data-slot="card"]:has(.recharts-wrapper) { grid-column:auto; }
    html[data-bakeoff-core="prefab"] [data-bakeoff-grid="charts"] { display:grid!important; grid-template-columns:repeat(2,minmax(0,1fr))!important; width:100%!important; }
    html[data-bakeoff-core="prefab"] [data-bakeoff-grid="kpis"] { display:grid!important; grid-template-columns:repeat(3,minmax(0,1fr))!important; width:100%!important; }
    html[data-bakeoff-core="evidence"] aside, html[data-bakeoff-core="evidence"] body header { display:none!important; }
    html[data-bakeoff-core="evidence"] main { margin-top:16px!important; padding:0!important; min-width:0; }
    html[data-bakeoff-core="evidence"] div:has(>main) { padding:0 16px!important; width:100%; }
    html[data-bakeoff-core="evidence"] article.markdown { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:0 20px; }
    html[data-bakeoff-core="evidence"] article.markdown > * { min-width:0; grid-column:1/-1; }
    html[data-bakeoff-core="evidence"] article.markdown > .chart-container { grid-column:auto; }
    html[data-bakeoff-core="evidence"] article.markdown > .grid { grid-template-columns:repeat(3,minmax(0,1fr))!important; }
    html[data-bakeoff-core="mviz"] .dashboard { max-width:1440px; }
    html[data-bakeoff-core="mviz"] .theme-toggle { display:none; }
    html[data-bakeoff-core="mviz"] .dashboard-section { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; }
    html[data-bakeoff-core="mviz"] .dashboard-section > h2 { grid-column:1/-1; }
    html[data-bakeoff-core="mviz"] .row { display:contents; }
    html[data-bakeoff-core="mviz"] .grid-item { grid-column:auto!important; min-width:0; }
    html[data-bakeoff-core="mviz"] .grid-item[style*="--col-span: 16"] { grid-column:1/-1!important; }
    html[data-bakeoff-core="mviz"] .dashboard-section:has(.textarea-item) { grid-template-columns:repeat(3,minmax(0,1fr)); }
    html[data-bakeoff-core="mviz"] .grid-item [id^="chart_"] { height:300px!important; }
    @media(max-width:759.98px) {
      html[data-bakeoff-core="prefab"] .pf-app-root:has(> .neon-card), html[data-bakeoff-core="tanstack"] .tiles, html[data-bakeoff-core="prefab"] [data-bakeoff-grid="charts"], html[data-bakeoff-core="evidence"] article.markdown, html[data-bakeoff-core="mviz"] .dashboard-section { grid-template-columns:minmax(0,1fr)!important; }
      html[data-bakeoff-core="tanstack"] .kpis, html[data-bakeoff-core="prefab"] [data-bakeoff-grid="kpis"], html[data-bakeoff-core="evidence"] article.markdown > .grid, html[data-bakeoff-core="mviz"] .dashboard-section:has(.textarea-item) { grid-template-columns:repeat(2,minmax(0,1fr))!important; }
    }
    @media(max-width:419.98px) {
      html[data-bakeoff-core="tanstack"] .kpis, html[data-bakeoff-core="prefab"] [data-bakeoff-grid="kpis"], html[data-bakeoff-core="evidence"] article.markdown > .grid, html[data-bakeoff-core="mviz"] .dashboard-section:has(.textarea-item) { grid-template-columns:minmax(0,1fr)!important; }
    }
  `;
  function classifyPrefab(doc) {
    // Select the actual card groups, never the grid inside an individual card.
    for (const node of doc.querySelectorAll('.pf-app-root .grid, .pf-app-root .flex-row')) {
      const cards = [...node.children].filter(child => child.matches('[data-slot="card"], .pf-card'));
      if (cards.length < 2 || cards.length !== node.children.length) continue;
      node.dataset.bakeoffGrid = cards.some(card => card.querySelector('.recharts-wrapper')) ? 'charts' : 'kpis';
    }
  }
  function combineMviz(doc, state) {
    if (state.moves.length) return;
    for (const row of doc.querySelectorAll('.row')) {
      const captions = [...row.children];
      const charts = [...(row.nextElementSibling?.children || [])];
      if (!captions.length || captions.length !== charts.length || !captions.every(x => x.querySelector(':scope > .text-content')) || !charts.every(x => x.querySelector('[id^="chart_"]'))) continue;
      captions.forEach((caption, index) => {
        const placeholder = doc.createComment('comparison subtitle');
        caption.before(placeholder);
        charts[index].querySelector('.chart-title')?.after(caption);
        state.moves.push({caption, placeholder});
      });
    }
  }
  window.applyCoreComparisonAdapter = (iframe, {appearance, comparison}) => {
    const framework = iframe.dataset.framework;
    if (!['prefab', 'evidence', 'tanstack', 'mviz'].includes(framework)) return null;
    let doc, win;
    try { doc = iframe.contentDocument; win = iframe.contentWindow; if (!doc?.body) return null; } catch { return null; }
    let state = states.get(doc);
    if (!state) {
      state = {dark:doc.documentElement.classList.contains('dark'), theme:doc.documentElement.getAttribute('data-theme'), mvizDark:doc.body.classList.contains('theme-dark'), moves:[], appearance};
      if (framework === 'evidence') { try { state.savedPreference=win.localStorage.getItem('evidence-theme'); } catch {} }
      states.set(doc,state);
    }
    state.observer?.disconnect();
    state.comparison=comparison;
    const root = doc.documentElement;
    if (!comparison) {
      root.removeAttribute('data-bakeoff-core'); root.removeAttribute('data-bakeoff-appearance');
      if (framework === 'prefab') root.classList.toggle('dark',state.dark);
      if (framework === 'evidence' && state.theme) {
        root.setAttribute('data-theme',state.theme);
        // The native store persists attribute changes on its next microtask.
        // Restore the user's preference after that update has completed.
        win.requestAnimationFrame(() => {
          if (state.comparison) return;
          try { if (state.savedPreference == null) win.localStorage.removeItem('evidence-theme'); else win.localStorage.setItem('evidence-theme',state.savedPreference); } catch {}
        });
      }
      if (framework === 'mviz' && doc.body.classList.contains('theme-dark') !== state.mvizDark) win.toggleTheme?.();
      for (const {caption,placeholder} of state.moves) placeholder.replaceWith(caption);
      state.moves = [];
      win.dispatchEvent(new win.Event('resize'));
      return {theme:true,layout:true};
    }
    if (!doc.getElementById('bakeoff-core-style')) {
      const style = doc.createElement('style'); style.id='bakeoff-core-style'; style.textContent=css; doc.head.append(style);
    }
    root.dataset.bakeoffCore=framework; root.dataset.bakeoffAppearance=appearance;
    const apply = () => {
      if (framework === 'prefab') {
        root.classList.toggle('dark', appearance === 'dark');
        classifyPrefab(doc);
      }
      if (framework === 'evidence' && root.getAttribute('data-theme') !== appearance) {
        root.setAttribute('data-theme',appearance);
        // Evidence persists its native theme store. A comparison setting must
        // not become a new standalone preference if this pane is removed.
        win.requestAnimationFrame(() => {
          try { if (state.savedPreference == null) win.localStorage.removeItem('evidence-theme'); else win.localStorage.setItem('evidence-theme',state.savedPreference); } catch {}
        });
      }
      if (framework === 'mviz') {
        if (doc.body.classList.contains('theme-dark') !== (appearance === 'dark')) win.toggleTheme?.();
        combineMviz(doc,state);
      }
    };
    apply();
    // Prefab and Evidence hydrate after iframe load. Observe only structure and
    // native theme attributes, not chart animation style changes.
    state.observer = new win.MutationObserver(apply);
    state.observer.observe(root,{subtree:true,childList:true,attributes:framework==='evidence',attributeFilter:framework==='evidence'?['data-theme']:undefined});
    win.dispatchEvent(new win.Event('resize'));
    return {theme:true,layout:true};
  };
})();
