{% snapshot customer_country_snapshot %}
{{
    config(
        target_schema='dbt_learning_snapshots',
        unique_key='customer_id',
        strategy='check',
        check_cols=['country']
    )
}}

select
    customer_id,
    country
from {{ ref('stg_customers') }}

{% endsnapshot %}
