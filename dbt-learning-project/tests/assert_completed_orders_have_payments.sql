-- A singular test passes when this query returns zero rows.
select
    order_id
from {{ ref('fct_orders') }}
where status = 'completed'
  and payment_amount <= 0
