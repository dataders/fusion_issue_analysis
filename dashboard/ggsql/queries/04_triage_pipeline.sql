-- tile: triage_pipeline
-- order: y
-- Age buckets are prefixed with age_bucket_order so ggsql stacks them young
-- to old; RENAMING restores the labels.
SELECT
    status_label,
    age_bucket_order || ' ' || age_bucket AS age,
    issue_count
FROM triage_pipeline
ORDER BY status_order, age_bucket_order
VISUALISE issue_count AS x, status_label AS y, age AS fill
DRAW bar
SCALE DISCRETE fill FROM ['1 0-7d', '2 8-30d', '3 31-90d', '4 91-180d', '5 180d+']
    TO ['#b7d3f6', '#86b6ef', '#5598e7', '#256abf', '#104281']
    RENAMING '1 0-7d' => '0-7d', '2 8-30d' => '8-30d', '3 31-90d' => '31-90d',
             '4 91-180d' => '91-180d', '5 180d+' => '180d+'
LABEL x => 'Open issues', y => null, fill => 'Age'
