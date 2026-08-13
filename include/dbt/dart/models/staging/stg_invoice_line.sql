with source as (
        select * from {{ source('chinook', 'invoice_line') }}
  ),
  renamed as (
      select
          invoice_line_id,
          invoice_id,
          track_id,
          unit_price,
          quantity

      from source
  )
  select * from renamed
    