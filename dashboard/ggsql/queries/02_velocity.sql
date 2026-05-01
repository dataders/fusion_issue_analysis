-- title: Median Days to Close: Bugs vs Enhancements
-- blurb: Weekly median close time by issue type. Tracks resolution velocity trends.
SELECT week, issue_category, median_days
FROM velocity
ORDER BY week
VISUALISE week AS x, median_days AS y, issue_category AS color
DRAW line
SCALE x VIA date
LABEL title => 'Median Days to Close: Bugs vs Enhancements'
