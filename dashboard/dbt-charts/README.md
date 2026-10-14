# dbt Charts preview

`scripts/render_dbt_charts.sh` renders the canonical board and its light/dark
comparison layouts using the installed dbt Charts renderer. No metrics are
recomputed in this adapter.

Comparison panes use the same layout breakpoints as the bakeoff: below 760px,
charts stack and KPIs use two columns; below 420px, KPIs also stack. Three native
SVG layouts (1000px, 600px, 360px) are generated for each theme. `comparison.js`
selects the layout on resize and responds to the shell's `bakeoff:appearance`
message. Theme and comparison state persist in the document URL. The current
chart's position is restored after changing layouts or themes.

These are native **layout variants**, not continuous browser rendering. dbt
Charts 0.9.1 still exports a fixed SVG: it scales within each width tier, and
wide data tables remain constrained by the native renderer. Text and chart
geometry therefore cannot match a browser-native renderer at every width.
