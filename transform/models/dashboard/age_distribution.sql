with aged as (
    select
        issue_category,
        case
            when datediff('day', created_at, current_date) <= 7 then 1
            when datediff('day', created_at, current_date) <= 30 then 2
            when datediff('day', created_at, current_date) <= 90 then 3
            when datediff('day', created_at, current_date) <= 180 then 4
            else 5
        end as bucket_sort_order
    from {{ ref('fct_issues') }}
    where state = 'OPEN' and issue_category != 'epic'
)
select
    issue_category,
    case bucket_sort_order
        when 1 then '0-7d' when 2 then '8-30d' when 3 then '31-90d' when 4 then '91-180d' else '180d+'
    end as age_bucket,
    bucket_sort_order,
    count(*) as issue_count
from aged
group by 1, 2, 3
