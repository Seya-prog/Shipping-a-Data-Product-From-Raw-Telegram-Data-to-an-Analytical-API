{{ config(materialized='table', schema='marts') }}

-- Fact table linking object detections to core message and dimension keys

with detections as (
    select
        message_id,
        object_class,
        confidence
    from raw.image_detections
),

joined as (
    select
        d.message_id,
        fm.channel_id,
        fm.date_id,
        d.object_class,
        d.confidence,
        current_timestamp as created_at,
        current_timestamp as updated_at
    from detections d
    left join {{ ref('fct_messages') }} fm on fm.message_id = d.message_id
)

select * from joined
