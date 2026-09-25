{#
  Q: Which adapters carry the most open work?
  Open non-epic issues per `adapter:*` label, by type. An issue with two
  adapters counts in both; '(none)' = adapter-agnostic.
#}

with open_issues as (
    select issue_dlt_id, issue_category
    from {{ ref('fct_issues') }}
    where state = 'OPEN' and issue_category != 'epic'
),

tagged as (
    select distinct issue_dlt_id, label_value as adapter
    from {{ ref('stg_issue_labels') }}
    where label_dimension = 'adapter'
),

counted as (
    select
        coalesce(t.adapter, '(none)') as adapter,
        o.issue_category,
        count(*) as issue_count
    from open_issues o
    left join tagged t using (issue_dlt_id)
    group by all
)

select
    adapter,
    issue_category,
    issue_count,
    sum(issue_count) over (partition by adapter) as adapter_total
from counted
order by adapter_total desc, adapter, issue_category
