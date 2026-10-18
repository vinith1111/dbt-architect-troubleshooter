select
    customer_id::number as customer_id,
    trim(first_name) as first_name,
    trim(last_name) as last_name,
    lower(trim(email)) as email,
    signup_date::date as signup_date,
    upper(trim(country)) as country
from {{ ref('customers') }}
