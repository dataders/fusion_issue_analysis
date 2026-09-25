-- tile: weekly_flow
-- week stays a string so dodged bars get a band per week (on a temporal
-- axis they render as hairlines).
SELECT week, 'opened' AS series, opened AS issues FROM weekly_flow
UNION ALL
SELECT week, 'closed' AS series, closed AS issues FROM weekly_flow
ORDER BY week, series DESC
VISUALISE week AS x, issues AS y, series AS fill
DRAW bar
    SETTING position => 'dodge'
SCALE DISCRETE fill FROM ['opened', 'closed'] TO ['#eb6834', '#2a78d6']
    RENAMING 'opened' => 'Opened', 'closed' => 'Closed'
LABEL x => 'Week', y => 'Issues', fill => null
