-- Milestone burndown: cumulative open vs closed issues per milestone over time
with milestone_issues as (
    select
        f.milestone_title,
        m.milestone_due_on,
        f.issue_number,
        f.state,
        f.created_at,
        f.closed_at
    from {{ ref('fct_issues') }} f
    left join {{ ref('dim_milestones') }} m
        on f.milestone_number = m.milestone_number
    where f.milestone_title is not null
),

-- Generate a date spine from the earliest issue to today
date_spine as (
    select unnest(generate_series(
        (select min(created_at::date) from milestone_issues),
        current_date,
        interval '1 day'
    )) as date_day
),

milestones as (
    select distinct milestone_title, milestone_due_on from milestone_issues
),

burndown as (
    select
        d.date_day,
        ms.milestone_title,
        ms.milestone_due_on,
        count(case when mi.created_at::date <= d.date_day then 1 end) as cumulative_opened,
        count(case when mi.closed_at::date <= d.date_day then 1 end) as cumulative_closed,
        count(case when mi.created_at::date <= d.date_day then 1 end)
            - count(case when mi.closed_at::date <= d.date_day then 1 end) as open_at_date
    from date_spine d
    cross join milestones ms
    left join milestone_issues mi
        on mi.milestone_title = ms.milestone_title
    group by d.date_day, ms.milestone_title, ms.milestone_due_on
)

select * from burndown
where cumulative_opened > 0
order by milestone_title, date_day
