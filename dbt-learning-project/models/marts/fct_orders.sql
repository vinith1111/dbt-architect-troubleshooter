with orders as (
    select * from {{ ref('stg_orders') }}
),
payments as (
    select
        order_id,
        sum(amount) as payment_amount
    from {{ ref('stg_payments') }}
    group by order_id
)
select
    orders.order_id,
    orders.customer_id,
    orders.order_date,
    orders.status,
    coalesce(payments.payment_amount, 0)::number(10, 2) as payment_amount,
    case when orders.status = 'completed' then true else false end as is_completed
from orders
left join payments using (order_id)
