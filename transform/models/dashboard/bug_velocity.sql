select week, median_days from {{ ref('velocity') }} where issue_category = 'bug' order by week
