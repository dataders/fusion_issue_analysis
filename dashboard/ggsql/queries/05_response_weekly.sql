-- tile: response_weekly
SELECT week::DATE AS week, pct_responded_48h
FROM response_weekly
ORDER BY week
VISUALISE week AS x, pct_responded_48h AS y
DRAW line
    SETTING colour => '#2a78d6'
DRAW point
    SETTING colour => '#2a78d6'
SCALE x VIA date
SCALE CONTINUOUS y FROM [0, 100]
LABEL x => 'Week opened', y => '% answered within 48h'
