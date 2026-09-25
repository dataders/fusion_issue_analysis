{# One row: what the dashboard's data covers and how fresh it is. Render a
   warning when days_stale is large — the extract has probably stopped. #}
select
    a.as_of_date,
    a.latest_activity_at,
    a.issue_count,
    date_diff('day', a.as_of_date, current_date) as days_stale,
    'dbt-labs/dbt-core' as source_repo,
    'engine:v2' as source_label
from {{ ref('as_of') }} a
