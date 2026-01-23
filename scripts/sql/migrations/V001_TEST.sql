SELECT
    current_timestamp() AS execution_time,
    current_user() AS usuario,
    'attributes' AS categoria,
    'Query ejecutada con token temporal' AS mensaje
