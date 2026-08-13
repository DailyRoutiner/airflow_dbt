with source as (
        select * from {{ source('chinook', 'artist') }}
  ),
  renamed as (
      select
      
          artist_id,
          "name" as artist_name

      from source
  )
  select * from renamed
    