with customers as (
    select * from {{ ref('stg_customers') }}
),
orders as (
    select
        customer_id,
        count(*) as total_orders,
        sum(case when status = 'completed' then 1 else 0 end) as completed_orders
    from {{ ref('stg_orders') }}
    group by customer_id
)
select
    customers.customer_id,
    customers.first_name,
    customers.last_name,
    customers.first_name || ' ' || customers.last_name as full_name,
    customers.email,
    customers.signup_date,
    customers.country,
    coalesce(orders.total_orders, 0) as total_orders,
    coalesce(orders.completed_orders, 0) as completed_orders
from customers
left join orders using (customer_id)
