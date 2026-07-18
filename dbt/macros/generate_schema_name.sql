{#
    dbt's default behavior prefixes a model's custom schema with the target
    schema (e.g. "main_marts" instead of "marts"). Override it so the schema
    is exactly what's configured in dbt_project.yml -- matches the docs/README,
    which reference `marts.mart_cx_kpi_rollup` and `staging.stg_*` directly.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
