select
    age_bucket,
    bucket_sort_order,
    sum(case when issue_category = 'bug' then issue_count else 0 end) as bug,
    sum(case when issue_category = 'enhancement' then issue_count else 0 end) as enhancement,
    sum(case when issue_category = 'task' then issue_count else 0 end) as task,
    sum(case when issue_category = 'other' then issue_count else 0 end) as other
from {{ ref('age_distribution') }}
group by 1, 2
order by bucket_sort_order
