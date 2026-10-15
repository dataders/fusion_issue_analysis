# BoardBench rule index

Rubric 2.8.0 · 47 rules · [Searchable rule browser](rules.html) · [Results](results.md)

**Defect:** a yes subtracts the stated points. **Excellence:** a yes contributes raw points that are scaled into the 0–40 bonus. **Gate:** a failure sets the whole score to zero; its raw points are excluded from the bonus. ‘Triggered’ means a defect found, excellence earned, or gate failed in the captured views.

| Rule | Category | Kind | Weight | Checked by | Triggered views | Question |
|---|---|---|---:|---|---:|---|
| [DEL-01](rules.html#rule-DEL-01) | delivery | Gate | Pass/fail | program | 0 | Did the artifact's own run instructions produce a page with content? |
| [DEL-02](rules.html#rule-DEL-02) | delivery | Defect | −4 | program | 21 | Did the browser console report errors while the page loaded? |
| [DEL-03](rules.html#rule-DEL-03) | delivery | Defect | −15 | program | 0 | Does the visible text contain NaN, undefined, null, Invalid Date, or a traceback? |
| [COR-01](rules.html#rule-COR-01) | correctness | Defect | −15 | program | 0 | What share of the brief's reference numbers are missing from the page? (scored proportionally) |
| [BRF-01](rules.html#rule-BRF-01) | answers brief | Defect | −15 | judge | 8 | Is there a question in the brief that no element on the page answers? |
| [BRF-02](rules.html#rule-BRF-02) | answers brief | Defect | −5 | judge | 1 | Do elements the brief did not ask for take up more of the page than the elements it did ask for? |
| [WRK-01](rules.html#rule-WRK-01) | working | Gate | Pass/fail | judge | 0 | Is the page a crash or error screen, or a shell where most panels show no data (error messages, spinners, blank cards, "failed to load"), instead of a working dashboard? |
| [WRK-02](rules.html#rule-WRK-02) | working | Defect | −15 | judge | 1 | Is any chart or table panel blank, an error message, a loading spinner, or a placeholder where data should be? |
| [HON-01](rules.html#rule-HON-01) | honesty | Defect | −20 | judge | 0 | Does a bar or area chart whose bar length shows an amount have a value axis that starts above zero, so small differences look large? |
| [HON-02](rules.html#rule-HON-02) | honesty | Defect | −20 | judge | 0 | Does a chart or number promise a rate or share in its title or label ("rate", "share", "%") while its values are plainly counts or amounts? |
| [HON-03](rules.html#rule-HON-03) | honesty | Defect | −12 | judge | 1 | Does the same category appear in different colors in different charts? |
| [HON-04](rules.html#rule-HON-04) | honesty | Defect | −12 | judge | 0 | Does a chart put two measures on two independent value axes with nothing telling the reader which series reads against which axis? |
| [HON-05](rules.html#rule-HON-05) | honesty | Defect | −8 | judge | 0 | Are side-by-side charts or small multiples of the same measure drawn on different scales with nothing saying so, so equal heights mean different amounts? |
| [HON-06](rules.html#rule-HON-06) | honesty | Defect | −8 | judge | 0 | Does a line connect categories that have no order (products, regions, channels), implying a trend between them? |
| [FRM-01](rules.html#rule-FRM-01) | form | Defect | −8 | judge | 0 | Does any chart use a form that hides its main comparison — a pie or donut whose slices are too many or too similar to compare, a 3D chart, a trend shown as a table or pie, or a ranking shown as a line? |
| [FRM-02](rules.html#rule-FRM-02) | form | Defect | −8 | judge | 0 | Do two or more charts on the page hide their main comparison through their form? |
| [FRM-03](rules.html#rule-FRM-03) | form | Defect | −8 | judge | 0 | In any chart with several series or categories, can some not be told apart — similar colors with no labels, or more series than distinct colors? |
| [FRM-04](rules.html#rule-FRM-04) | form | Defect | −3 | judge | 1 | Are the categories of a ranked comparison in an arbitrary or alphabetical order when the point is which is largest? |
| [FRM-05](rules.html#rule-FRM-05) | form | Defect | −3 | judge | 0 | Is a single number drawn as a chart (a gauge, a one-bar chart) where the number alone would do? |
| [FRM-07](rules.html#rule-FRM-07) | form | Defect | −3 | judge | 0 | Do two charts show the same data in the same form, so one adds nothing? |
| [FRM-08](rules.html#rule-FRM-08) | form | Defect | −8 | judge | 20 | Is a chart's point destroyed by its scale or ordering — one outlier flattening everything else, two measures of very different size sharing one axis so one is a flat line, or histogram or time bins sorted out of their natural order? |
| [FRM-06](rules.html#rule-FRM-06) | form | Defect | −4 | judge | 0 | Does a time series start or end with a sudden drop or spike that comes from an incomplete period (a week or month still in progress, a partial first period), with nothing on the page saying the period is partial? |
| [LEG-01](rules.html#rule-LEG-01) | legibility | Defect | −6 | judge | 2 | Does any text overlap other text or cover the mark it labels (tick labels running together, data labels on top of each other, a title over a chart)? |
| [LEG-02](rules.html#rule-LEG-02) | legibility | Defect | −8 | judge | 2 | Do three or more charts on the page have overlapping text? |
| [LEG-03](rules.html#rule-LEG-03) | legibility | Defect | −4 | judge | 9 | Is any title, label, or table column cut off, ended with an ellipsis that hides words, or pushed outside its card? |
| [LEG-04](rules.html#rule-LEG-04) | legibility | Defect | −5 | judge | 1 | Is any text too small or too faint to read at the page's normal size — tiny tick labels, pale gray titles or values? |
| [LEG-05](rules.html#rule-LEG-05) | legibility | Defect | −8 | judge | 0 | Are charts squeezed into cards too small for them, so their bars, lines, or cells cannot be told apart at the size drawn? |
| [LBL-01](rules.html#rule-LBL-01) | labeling | Defect | −6 | judge | 0 | Is there a number on the page whose unit (currency, percent, count, duration) cannot be found anywhere near it — not in the value, its axis, its title, subtitle, or column? |
| [LBL-02](rules.html#rule-LBL-02) | labeling | Defect | −4 | judge | 4 | Does any title, axis title, legend, or column header show a raw field name, code, or placeholder ("sum_amount", "fct_orders.region", "Untitled", "Chart 1")? |
| [LBL-03](rules.html#rule-LBL-03) | labeling | Defect | −6 | judge | 1 | Does the page fail to say what it covers, or is there no period (dates, month, year, "last 30 days") anywhere on it? |
| [LBL-04](rules.html#rule-LBL-04) | labeling | Defect | −4 | judge | 4 | Is there a headline number whose period cannot be found — not on its tile and not stated for the page? |
| [LBL-05](rules.html#rule-LBL-05) | labeling | Defect | −4 | judge | 0 | Is there a chart or table with no title or label saying what it shows? |
| [LBL-07](rules.html#rule-LBL-07) | labeling | Defect | −3 | judge | 7 | Is there a percentage a reader could reasonably read against two different bases, with nothing saying which? |
| [LBL-08](rules.html#rule-LBL-08) | labeling | Defect | −10 | judge | 0 | Does a label contradict what is plotted — a unit that does not fit the measure ($ ticks on a count), an axis or title naming a measure the chart does not show, or a stated finding the chart itself contradicts? |
| [LBL-09](rules.html#rule-LBL-09) | labeling | Defect | −10 | judge | 2 | Do numbers or statements on the page contradict each other — a headline that disagrees with the table or chart it summarizes, parts that cannot add up to their total, two different as-of dates, or a note that points at content that is not there ("shown at right", "see tooltip" on a static page)? |
| [LAY-01](rules.html#rule-LAY-01) | layout | Defect | −5 | judge | 6 | Is there a large empty region the content does not need — a hole beside a tall chart, a half-empty row, a band of blank page? |
| [LAY-02](rules.html#rule-LAY-02) | layout | Defect | −5 | judge | 1 | Are cards visibly misaligned — edges that nearly line up but miss, ragged bottoms within one row, uneven gaps between cards? |
| [LAY-04](rules.html#rule-LAY-04) | layout | Defect | −5 | judge | 6 | Does detail outrank the summary — a raw table, a filter bar, or a minor chart placed above the page's main numbers or charts, or given far more space than them? |
| [LAY-05](rules.html#rule-LAY-05) | layout | Defect | −4 | judge | 3 | Do borders, fills, colored headers, shadows, icons, or decoration carry more visual weight than the data? |
| [LAY-06](rules.html#rule-LAY-06) | layout | Defect | −4 | judge | 0 | Is color used in a way that encodes nothing or misleads — bars of a single series cycling through a palette, a rainbow color scale for a quantity, colored or sized marks with no legend saying what color or size means? |
| [LAY-07](rules.html#rule-LAY-07) | layout | Defect | −4 | judge | 5 | Is there leftover scaffolding the author left in — placeholder or starter content, debug text, "lorem ipsum", stray test elements? |
| [EXC-01](rules.html#rule-EXC-01) | excellence | Excellence | +10 | judge | 1 | Does the page state its main finding in words — a title or sentence that says what happened ("Churn doubled in March"), not just what is shown ("Churn by month") — and do the charts bear it out? |
| [EXC-03](rules.html#rule-EXC-03) | excellence | Excellence | +3 | judge | 20 | Do the headline numbers carry a comparison — a change vs a prior period, a target, or a peer? |
| [EXC-04](rules.html#rule-EXC-04) | excellence | Excellence | +6 | judge | 0 | Is a key point marked on a chart where it happens — an annotated spike or dip, a target line, a highlighted series or bar with the rest muted? |
| [EXC-06](rules.html#rule-EXC-06) | excellence | Excellence | +5 | judge | 0 | Is most of the data drawn in a neutral gray, with one accent color reserved for the subject — the series, bar, or period the page is about? |
| [EXC-07](rules.html#rule-EXC-07) | excellence | Excellence | +4 | judge | 1 | Are a chart's series or pie slices labeled directly (at line ends, on the slices) instead of through a legend the reader has to look back at? |
| [EXC-08](rules.html#rule-EXC-08) | excellence | Excellence | +5 | judge | 23 | Does the page explain its numbers where they are shown — how a measure is defined, a filter or exclusion applied, a method note, or the sample size behind a rate? |

The trigger counts describe only the 23 views captured on 14 October 2026. A rule marked N/A or unclear does not count as triggered. [Read how the final score is calculated](results.md).
