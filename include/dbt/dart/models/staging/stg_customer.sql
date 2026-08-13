with source as (
        select * from {{ source('chinook', 'customer') }}
  ),
  renamed as (
      select
          
          customer_id,
          first_name,
          last_name,
          concat(first_name, ' ',  last_name ) as full_name,
          company,
          address,
          city,
          state,
          country,
          postal_code,
          phone,
          fax,
          email,
          support_rep_id as employee_id

      from source
  )
  select * from renamed
    