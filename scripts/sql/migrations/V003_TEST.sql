SELECT 
            current_timestamp() as execution_time,
            current_user() as user,
            'Query ejecutada con token temporal' as mensaje