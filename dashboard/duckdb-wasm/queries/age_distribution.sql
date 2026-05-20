SELECT
    age_bucket,
    issue_category,
    issue_count
FROM fusion_issues.main.age_distribution
ORDER BY
    CASE age_bucket
        WHEN '0-7d'    THEN 1
        WHEN '8-30d'   THEN 2
        WHEN '31-90d'  THEN 3
        WHEN '91-180d' THEN 4
        ELSE 5
    END
