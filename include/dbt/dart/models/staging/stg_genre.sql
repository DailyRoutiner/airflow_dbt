with source as (
        select * from {{ source('chinook', 'genre') }}
  ),
  renamed as (
      select
          genre_id,
          "name" as genre_name

      from source
  )
  select * from renamed
    