with
source as(
    select * from {{ source('dart', 'raw_stores')}}
)
select * from source