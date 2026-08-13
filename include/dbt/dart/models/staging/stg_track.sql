with source as (
        select * from {{ source('chinook', 'track') }}
  ),
  renamed as (
      select
          track_id,
          "name" as track_name,
          album_id,
          media_type_id,
          genre_id,
          composer
          -- 안쓰는 컬럼들은 버리기
        --   date_trunc('second', (milliseconds || ' ms')::interval) as minutes,
        --   bytes,
        --   unit_price

      from source
  )
  select * from renamed
    