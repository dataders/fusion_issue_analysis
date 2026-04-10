-- Overall issue summary metrics
select
    count(*) as total_issues,
    count(case when state = 'OPEN' then 1 end) as open_issues,
    count(case when state = 'CLOSED' then 1 end) as closed_issues,
    round(avg(case when hours_to_close is not null then hours_to_close end), 1) as avg_hours_to_close,
    round(median(case when hours_to_close is not null then hours_to_close end), 1) as median_hours_to_close,
    round(avg(case when hours_to_first_response is not null then hours_to_first_response end), 1) as avg_hours_to_first_response,
    round(median(case when hours_to_first_response is not null then hours_to_first_response end), 1) as median_hours_to_first_response,
    min(created_at) as earliest_issue,
    max(created_at) as latest_issue
from {{ ref('fct_issues') }}
