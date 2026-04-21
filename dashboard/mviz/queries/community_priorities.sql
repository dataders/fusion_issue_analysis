select
    issue_number,
    title,
    issue_category,
    reactions_total_count as reactions,
    comments_total_count as comments,
    round(datediff('day', created_at, current_date), 0) as age_days
from fct_issues
where state = 'OPEN' and reactions_total_count > 0 and issue_category != 'epic'
order by reactions_total_count desc
limit 10
