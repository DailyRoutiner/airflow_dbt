with invoice_lines as (
    select * from {{ ref('stg_invoice_line')}}
),
invoices as (
    select * from {{ ref('stg_invoice')}}
), 
joined as (
select *,
    quantity * unit_price as line_amount
from invoice_lines 
   left join invoices using (invoice_id)
)
select 
    invoice_line_id,
    invoice_id,
    customer_id,
    track_id,
    invoice_date,
    quantity,
    unit_price,
    line_amount
from joined