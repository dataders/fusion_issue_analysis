{# Resolves raw source tables: parquet in dev, MotherDuck in prod #}
{% macro raw_source(table_name) %}
    {% if target.name == 'prod' %}
        raw_github.{{ table_name }}
    {% else %}
        read_parquet('../data/raw/fusion_issues/{{ table_name }}/*.parquet')
    {% endif %}
{% endmacro %}
