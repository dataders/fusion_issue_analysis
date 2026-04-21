select
    count(*) as total_open,
    round(count(case when is_labeled then 1 end)::float / count(*) * 100, 0) as pct_labeled,
    round(count(case when is_assigned then 1 end)::float / count(*) * 100, 0) as pct_assigned,
    round(count(case when has_milestone then 1 end)::float / count(*) * 100, 0) as pct_milestoned,
    round(count(case when issue_category != 'other' then 1 end)::float / count(*) * 100, 0) as pct_typed,
    count(case when not is_labeled then 1 end) as unlabeled_count,
    count(case when not is_assigned then 1 end) as unassigned_count
from {{ ref('fct_issues') }}
where state = 'OPEN' and issue_category != 'epic'
