SELECT
    current_timestamp() AS execution_time,
    current_user() AS usuario,
    'Query ejecutada con token temporal' AS mensaje
