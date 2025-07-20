{{ config(materialized='table', schema='marts') }}

with bounds as (
    select
        min(date)::date as min_date,
        max(date)::date as max_date
    from {{ ref('stg_telegram_messages') }}
),

date_spine as (
    select generate_series(min_date, max_date, interval '1 day')::date as date_day
    from bounds
),

dim as (
    select
        date_day                                       as date_id,
        extract(year  from date_day)::int             as year,
        extract(month from date_day)::int             as month,
        extract(day   from date_day)::int             as day,
        to_char(date_day, 'YYYYMMDD')::int           as yyyymmdd,
        to_char(date_day, 'Day')                     as day_name,
        extract(dow from date_day)::int               as day_of_week,
        to_char(date_day, 'Month')                   as month_name,
        date_trunc('week',   date_day)::date          as week_start,
        date_trunc('month',  date_day)::date          as month_start,
        date_trunc('quarter',date_day)::date          as quarter_start,
        date_trunc('year',   date_day)::date          as year_start,
        current_timestamp                              as created_at,
        current_timestamp                              as updated_at
    from date_spine
)

select * from dim
