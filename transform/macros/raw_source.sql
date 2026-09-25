{# Resolves raw source tables: parquet in dev, MotherDuck in prod.
   Both point at the dbt-core `engine:v2` extract (see extract/run.py). #}
{% macro raw_source(table_name) %}
    {% if target.name == 'prod' %}
        raw_github_core.{{ table_name }}
    {% else %}
        read_parquet('../data/raw/fusion_issues_core/{{ table_name }}/*.parquet', union_by_name=true)
    {% endif %}
{% endmacro %}
