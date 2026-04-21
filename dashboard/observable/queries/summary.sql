select
    count(case when state='OPEN' and issue_category!='epic' then 1 end) as open_issues,
    count(case when closed_at >= current_date - interval '28 days' and issue_category!='epic' then 1 end) as closed_4w,
    count(case when created_at >= current_date - interval '28 days' and issue_category!='epic' then 1 end) as opened_4w,
    count(case when state='OPEN' and updated_at < current_date - interval '30 days' and issue_category!='epic' then 1 end) as stale_count,
    round(median(case when closed_at >= current_date-interval '28 days' then hours_to_close end)/24.0, 1) as median_close_days
from fct_issues
