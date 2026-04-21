select
    issue_category,
    count(*) as count
from {{ ref('fct_issues') }}
where state = 'OPEN' and issue_category != 'epic'
group by issue_category
order by count desc
