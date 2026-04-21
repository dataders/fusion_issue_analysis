select
    round(count(case when is_labeled then 1 end)*100.0/count(*),0) as pct_labeled,
    round(count(case when is_assigned then 1 end)*100.0/count(*),0) as pct_assigned,
    round(count(case when has_milestone then 1 end)*100.0/count(*),0) as pct_milestoned
from fct_issues where state='OPEN' and issue_category!='epic'
