with source as (
        select * from {{ source('chinook', 'employee') }}
  ),
  renamed as (
      select
          employee_id,
          last_name,
          first_name,
          title as job_title,
          reports_to as manager_id,
          birth_date,
          hire_date,
          address,
          city,
          state,
          country,
          postal_code,
          phone,
          fax,
          email

      from source
  )
  select * from renamed
    