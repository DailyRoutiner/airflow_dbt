with customers as (
    select * from {{ ref('int_customers_enriched') }}
)
select 
    customer_id,
    customer_name,
    company,
    customer_email,
    customer_phone,
    customer_city,
    customer_state,
    customer_postal_code,
    country,
    region,
    continent,
    support_rep_id,
    support_rep_name,
    support_rep_title,
    support_rep_email
from customers