with track as (
    select * from {{ ref('stg_track') }}
),
album as (
    select * from {{ ref('stg_album') }}
),
artist as (
    select * from {{ ref('stg_artist') }}
),
genre as (
    select * from {{ ref('stg_genre') }}
)
select track_id, track_name, composer, unit_price,
    album_title,
    artist_name,
    genre_name
from track 
    left join album using (album_id)
    left join artist using (artist_id)
    left join genre using (genre_id)
