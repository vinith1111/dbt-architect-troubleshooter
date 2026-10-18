select
    order_id::number as order_id,
    customer_id::number as customer_id,
    order_date::date as order_date,
    lower(trim(status)) as status
from {{ ref('orders') }}
