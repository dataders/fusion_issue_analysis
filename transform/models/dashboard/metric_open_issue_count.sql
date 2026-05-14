-- MetricFlow metric: open_issue_count, sliced by issue_category and milestone_title
select
    issue_category,
    coalesce(milestone_title, 'No milestone') as milestone_title,
    count(*) as open_issue_count
from {{ ref('fct_issues') }}
where state = 'OPEN'
  and issue_category != 'epic'
group by 1, 2
order by 3 desc
