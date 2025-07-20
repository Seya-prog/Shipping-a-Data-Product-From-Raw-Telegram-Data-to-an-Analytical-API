{{ config(materialized='table', schema='marts') }}

with base as (
    select
        id                                 as message_id,
        chat_id,
        channel,
        date::date                         as message_date,
        media,
        message_text,
        has_url,
        has_hashtag,
        has_mention
    from {{ ref('stg_telegram_messages') }}
),

joined as (
    select
        b.message_id,
        c.channel_id,
        d.date_id,
        b.message_text,
        b.media,
        b.has_url,
        b.has_hashtag,
        b.has_mention,
        b.message_date,
        current_timestamp                  as created_at,
        current_timestamp                  as updated_at
    from base b
    left join {{ ref('dim_channels') }} c
        on b.chat_id = c.chat_id and b.channel = c.channel
    left join {{ ref('dim_dates') }} d
        on b.message_date = d.date_id
)

select * from joined
