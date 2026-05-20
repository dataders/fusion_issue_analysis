-- Fails when audit_epics_without_milestone rowcount disagrees with
-- fct_epics.is_orphan_epic, which means the audit and mart drifted.
with audit_n as (
    select count(*) as n from {{ ref('audit_epics_without_milestone') }}
),
fact_n as (
    select count(*) as n from {{ ref('fct_epics') }} where is_orphan_epic
)
select 'mismatch' as failure, audit_n.n as audit_rowcount, fact_n.n as fact_rowcount
from audit_n cross join fact_n
where audit_n.n != fact_n.n
