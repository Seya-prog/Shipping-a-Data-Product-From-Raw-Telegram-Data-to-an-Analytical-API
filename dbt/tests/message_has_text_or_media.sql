-- Ensure each message has text or media (at least one)

with invalid as (
    select *
    from {{ ref('stg_telegram_messages') }}
    where coalesce(message_text, '') = ''
      and media is false
)

select * from invalid
