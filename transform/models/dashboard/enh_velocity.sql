select week, median_days from {{ ref('velocity') }} where issue_category = 'enhancement' order by week
