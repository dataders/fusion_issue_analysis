{#
  Q: Which parts of the product carry the most open work?
  Open non-epic issues per `area:*` label, by type. An issue with two areas
  counts in both; '(none)' = no area label.
#}

with open_issues as (
    select issue_dlt_id, issue_category
    from {{ ref('fct_issues') }}
    where state = 'OPEN' and issue_category != 'epic'
),

tagged as (
    select distinct issue_dlt_id, label_value as area
    from {{ ref('stg_issue_labels') }}
    where label_dimension = 'area'
),

counted as (
    select
        coalesce(t.area, '(none)') as area,
        o.issue_category,
        count(*) as issue_count
    from open_issues o
    left join tagged t using (issue_dlt_id)
    group by all
)

select
    area,
    issue_category,
    issue_count,
    sum(issue_count) over (partition by area) as area_total
from counted
order by area_total desc, area, issue_category
