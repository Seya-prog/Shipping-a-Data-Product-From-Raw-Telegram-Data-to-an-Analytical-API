{{ config(materialized='view', schema='staging') }}

with source as (
    select
        id,
        date,
        message,
        from_id,
        chat_id,
        media,
        channel,
        file_path,
        loaded_at
    from raw.telegram_messages
),

clean as (
    select
        id,
        date,
        message as message_text,
        from_id,
        chat_id,
        media,
        channel,
        file_path,
        loaded_at,
        coalesce(message, '')                                          as message_text_clean,
        (coalesce(message, '') ilike '%http%')                          as has_url,
        (coalesce(message, '') ilike '%#%')                             as has_hashtag,
        (coalesce(message, '') ilike '%@%')                             as has_mention
    from source
)

select *
from clean
where not (coalesce(message_text, '') = '' and coalesce(media, false) = false)
