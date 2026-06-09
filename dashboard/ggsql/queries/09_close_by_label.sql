-- title: Median Days to Close by Label
-- blurb: Which labels correlate with longer or shorter resolution times.
SELECT label_name, median_days_to_close, closed_count
FROM close_by_label
ORDER BY median_days_to_close DESC
LIMIT 15
VISUALISE label_name AS y, median_days_to_close AS x
DRAW bar
LABEL title => 'Median Days to Close by Label'
