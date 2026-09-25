{#
  Q: Are new issues getting a timely first response?
  Per week of creation: share of new issues that got a non-author reply
  within 48h. Unanswered issues count as misses, and only weeks whose every
  issue has had 48h to be answered are included.
#}

with a as (select as_of_date from {{ ref('as_of') }}),

weeks as (
    select (date_trunc('week', a.as_of_date) - to_days((t.i * 7)::integer))::timestamp as week
    from a cross join generate_series(0::bigint, 26::bigint) as t(i)
),

issues as (
    select created_at, hours_to_first_response
    from {{ ref('fct_issues') }}
    where issue_category != 'epic'
)

select
    strftime(w.week, '%Y-%m-%d') as week,
    count(i.created_at) as issues_opened,
    count(*) filter (where i.hours_to_first_response <= 48) as responded_48h,
    round(100.0 * count(*) filter (where i.hours_to_first_response <= 48)
        / nullif(count(i.created_at), 0), 0) as pct_responded_48h,
    round(median(i.hours_to_first_response), 1) as median_hours_to_first_response
from weeks w
cross join a
left join issues i
    on i.created_at >= w.week and i.created_at < w.week + interval 7 day
where w.week + interval 9 day <= a.as_of_date::timestamp  -- week complete + 48h grace
group by 1
order by 1
