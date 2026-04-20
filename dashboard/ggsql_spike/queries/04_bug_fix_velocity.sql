-- title: Bug-fix velocity
-- blurb: Weekly bugs closed with median hours-to-close.
SELECT
    week_closed,
    bugs_closed,
    median_hours_to_close
FROM bug_fix_velocity
ORDER BY week_closed
VISUALISE week_closed AS x, bugs_closed AS y, median_hours_to_close AS fill
DRAW bar
SCALE BINNED fill
LABEL title => 'Bugs closed per week (fill = median hours to close)'
