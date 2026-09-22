with source as (
        select * from {{ source('chinook', 'album') }}
  ),
  renamed as (
      select
        album_id,
        title as album_title,
        artist_id
      from source
  )
  select * from renamed
    