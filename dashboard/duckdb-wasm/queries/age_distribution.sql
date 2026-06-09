SELECT
    age_bucket,
    issue_category,
    issue_count
FROM fusion_issues.main.age_distribution
ORDER BY bucket_sort_order
