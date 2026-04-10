-- Time to first response: weekly trend of how quickly issues get a non-author response
with weekly as (
    select
        date_trunc('week', created_at) as week_created,
        count(*) as issues_opened,
        count(case when hours_to_first_response is not null then 1 end) as issues_with_response,
        round(avg(hours_to_first_response), 1) as avg_hours_to_first_response,
        round(median(hours_to_first_response), 1) as median_hours_to_first_response,
        round(quantile_cont(hours_to_first_response, 0.9), 1) as p90_hours_to_first_response
    from {{ ref('fct_issues') }}
    group by date_trunc('week', created_at)
)

select
    *,
    round(issues_with_response::float / nullif(issues_opened, 0) * 100, 1) as pct_responded
from weekly
order by week_created
