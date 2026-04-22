select
    l.label_name,
    round(median(f.hours_to_close) / 24, 1) as median_days_to_close,
    count(*) as closed_count
from fct_issues f
inner join fct_issue_labels l on f.issue_dlt_id = l.issue_dlt_id
where f.closed_at is not null and f.issue_category != 'epic'
group by l.label_name
having count(*) >= 10
order by median_days_to_close desc
limit 15
