with source as (
        select * from {{ source('chinook', 'invoice') }}
  ),
  renamed as (
      select
          invoice_id,
          customer_id,
          invoice_date,
          billing_address,
          billing_city,
          billing_state,
          billing_country,
          billing_postal_code,
          total

      from source
  )
  select * from renamed
    