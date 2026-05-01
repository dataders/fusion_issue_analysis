-- title: Time to First Response (hours)
-- blurb: Weekly p25/p50/p75 of hours from issue creation to first team response.
SELECT week, 'p25' AS percentile, p25 AS hours
FROM response_pctiles
UNION ALL
SELECT week, 'p50' AS percentile, p50 AS hours
FROM response_pctiles
UNION ALL
SELECT week, 'p75' AS percentile, p75 AS hours
FROM response_pctiles
ORDER BY week
VISUALISE week AS x, hours AS y, percentile AS color
DRAW line
SCALE x VIA date
LABEL title => 'Time to First Response (hours)'
