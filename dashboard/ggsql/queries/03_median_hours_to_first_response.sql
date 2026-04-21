-- title: Median hours to first response (weekly)
-- blurb: Responsiveness trend from response_time_trends mart.
SELECT
    week_created,
    median_hours_to_first_response AS median_hours
FROM response_time_trends
WHERE median_hours_to_first_response IS NOT NULL
ORDER BY week_created
VISUALISE week_created AS x, median_hours AS y
DRAW line
LABEL title => 'Median hours to first response, by week'
