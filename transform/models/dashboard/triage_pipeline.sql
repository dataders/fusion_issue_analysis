{#
  Q: How much is waiting on triage, and how long has it waited?
  Open non-epic issues by triage status x age. Long format; render as a
  horizontal stacked bar (one bar per status, segments = age bucket).
#}

with a as (select as_of_date from {{ ref('as_of') }}),

open_issues as (
    select
        f.triage_status,
        date_diff('day', f.created_at, a.as_of_date) as age_days
    from {{ ref('fct_issues') }} f cross join a
    where f.state = 'OPEN' and f.issue_category != 'epic'
),

statuses as (
    select * from (values
        ('awaiting_triage', 'Awaiting triage', 1),
        ('needs_repro', 'Needs repro', 2),
        ('has_repro', 'Has repro', 3),
        ('awaiting_release', 'Fixed, awaiting release', 4),
        ('triaged', 'Triaged backlog', 5)
    ) as s(triage_status, status_label, status_order)
),

buckets as (
    select * from (values
        ('0-7d', 1), ('8-30d', 2), ('31-90d', 3), ('91-180d', 4), ('180d+', 5)
    ) as b(age_bucket, age_bucket_order)
),

bucketed as (
    select
        triage_status,
        case
            when age_days <= 7 then '0-7d'
            when age_days <= 30 then '8-30d'
            when age_days <= 90 then '31-90d'
            when age_days <= 180 then '91-180d'
            else '180d+'
        end as age_bucket
    from open_issues
)

select
    s.triage_status,
    s.status_label,
    s.status_order,
    b.age_bucket,
    b.age_bucket_order,
    count(x.triage_status) as issue_count
from statuses s
cross join buckets b
left join bucketed x
    on x.triage_status = s.triage_status and x.age_bucket = b.age_bucket
group by all
order by s.status_order, b.age_bucket_order
