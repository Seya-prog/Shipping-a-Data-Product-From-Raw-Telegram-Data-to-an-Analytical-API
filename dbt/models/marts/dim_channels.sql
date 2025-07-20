{{ config(materialized='table', schema='marts') }}

with distinct_channels as (
    select distinct channel, chat_id
    from {{ ref('stg_telegram_messages') }}
)

select
    row_number() over (order by channel) as channel_id,
    channel,
    chat_id,
    current_timestamp as created_at,
    current_timestamp as updated_at
from distinct_channels
