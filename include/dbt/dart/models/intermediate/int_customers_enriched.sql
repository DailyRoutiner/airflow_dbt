with 
customer as (
    select * from {{ ref('stg_customer') }}
),
region as (
    select * from {{ ref('country_region') }}
),
employee as (
    select * from {{ ref('stg_employee') }}
),
joined as (
    select 
        customer.customer_id,
        customer.full_name      as customer_name,
        customer.company,
        customer.email          as customer_email,
        customer.phone          as customer_phone,
        customer.city           as customer_city,
        customer.state          as customer_state,
        customer.postal_code    as customer_postal_code,

        customer.country,
        region.region,
        region.continent,

        customer.employee_id             as support_rep_id,
        employee.first_name || ' ' || employee.last_name as support_rep_name,
        employee.job_title      as support_rep_title,
        employee.email          as support_rep_email
    from customer
        left join region using (country)
        left join employee using (employee_id)
)
select * from joined