select
    payment_id::number as payment_id,
    order_id::number as order_id,
    lower(trim(payment_method)) as payment_method,
    amount::number(10, 2) as amount,
    paid_at::date as paid_date
from {{ ref('payments') }}
