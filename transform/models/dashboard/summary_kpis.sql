with recent_window as (
    select
        count(case when created_at >= current_date - interval '28 days' then 1 end) as opened_4w,
        count(case when closed_at >= current_date - interval '28 days' then 1 end) as closed_4w,
        count(case when state = 'OPEN' then 1 end) as open_issues,
        count(*) as total_issues
    from {{ ref('fct_issues') }} where issue_category != 'epic'
),
rolling_close as (
    select round(median(hours_to_close) / 24, 1) as rolling_median_close_days
    from {{ ref('fct_issues') }}
    where closed_at >= current_date - interval '28 days' and issue_category != 'epic'
),
sla as (
    select
        round(
            count(case when hours_to_first_response <= 48 then 1 end)::float
            / nullif(count(case when hours_to_first_response is not null then 1 end), 0)
            * 100, 0
        ) as pct_responded_48h
    from {{ ref('fct_issues') }}
    where created_at >= current_date - interval '28 days' and issue_category != 'epic'
),
stale as (
    select count(*) as stale_count
    from {{ ref('fct_issues') }}
    where state = 'OPEN' and updated_at < current_date - interval '30 days' and issue_category != 'epic'
)
select * from recent_window cross join rolling_close cross join sla cross join stale
