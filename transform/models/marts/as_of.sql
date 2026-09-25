{#
  Single-row anchor for every time window on the dashboards. Windows are
  measured back from the latest activity in the data, not from current_date,
  so a stalled extract shows stale-but-correct numbers (and a visible
  "data as of" date) instead of silently decaying to zero.
#}
select
    max(updated_at)::date as as_of_date,
    max(updated_at) as latest_activity_at,
    count(*) as issue_count
from {{ ref('stg_issues') }}
