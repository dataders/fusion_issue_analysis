// dct renders real, fixed SVG layouts. Pick a native layout at shared bakeoff
// breakpoints, instead of shrinking the entire 1200px desktop board into a pane.
(() => {
  const params = new URLSearchParams(location.search);
  const system = matchMedia('(prefers-color-scheme: dark)');
  let comparison = params.get('comparison') === '1';
  let appearance = params.get('appearance') || 'system';
  let timer;
  const anchors = () => [...document.querySelectorAll('[data-chart-id]')];
  const key = `bakeoff-dct-position:${window.name || 'dashboard'}`;

  function update() {
    const theme = appearance === 'dark' || (appearance !== 'light' && system.matches) ? 'dark' : 'light';
    const layout = innerWidth < 420 ? 'mobile' : innerWidth < 760 ? 'narrow' : 'wide';
    const filename = `fusion-issue-health-${theme}${comparison ? `-${layout}` : ''}.html`;
    if (location.pathname.endsWith(`/${filename}`)) return false;
    const chart = anchors().find(node => node.getBoundingClientRect().bottom > 0);
    try {
      sessionStorage.setItem(key, JSON.stringify(chart ? {
        id: chart.dataset.chartId,
        offset: chart.getBoundingClientRect().top / Math.max(chart.getBoundingClientRect().height, 1),
      } : { top: scrollY }));
    } catch (_) { /* Storage may be disabled; layout still changes. */ }
    params.set('appearance', appearance);
    if (comparison) params.set('comparison', '1');
    else params.delete('comparison');
    location.replace(`${filename}?${params}${location.hash}`);
    return true;
  }

  addEventListener('message', event => {
    if (event.source !== parent || event.origin !== location.origin || event.data?.type !== 'bakeoff:appearance') return;
    if (!['light', 'dark', 'system'].includes(event.data.appearance)) return;
    appearance = event.data.appearance;
    comparison = event.data.comparison === true;
    update();
  });
  addEventListener('resize', () => { clearTimeout(timer); timer = setTimeout(update, 120); });
  system.addEventListener('change', update);
  if (!update()) requestAnimationFrame(() => {
    try {
      const position = JSON.parse(sessionStorage.getItem(key) || 'null');
      sessionStorage.removeItem(key);
      if (!position) return;
      const chart = anchors().find(node => node.dataset.chartId === position.id);
      scrollTo(0, chart ? chart.getBoundingClientRect().top + scrollY - position.offset * chart.getBoundingClientRect().height : position.top || 0);
    } catch (_) { /* Malformed or unavailable saved position is harmless. */ }
  });
})();
