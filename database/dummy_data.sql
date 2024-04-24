


INSERT INTO user_details (
    email, name 
) VALUES (
    'mellonmail@gmail.com', 'Melanie'
);

INSERT INTO user_location_assignment(
    user_id, loc_id, report_opt_in, alert_opt_in
) VALUES (
    1, 12, True, True
);

INSERT INTO weather_report(
    report_time, loc_id
) VALUES (
    '2024/04/24 13:00', 12
);

INSERT INTO forecast(
    forecast_timestamp, air_quality, visibility, humidity, precipitation, precipitation_prob, rainfall, snowfall, wind_speed, wind_direction, wind_gusts, lightning_potential, uv_index, cloud_cover, temperature, apparent_temp, weather_report_id, weather_code_id
)
VALUES(
    '2024/04/24 14:00', 1, 1000, 30, 10, 100, 10.0, 0, 40.0, 180, 50.0, 0, 0, 100, 10.0, 8.0, 1, 82
);

INSERT INTO flood_warnings(
    severity_level_id, time_raised, loc_id
) VALUES(
    1, '2024/04/24 13:00', 1
);

INSERT INTO weather_alert(
    alert_type_id, forecast_id, severity_level_id
) VALUES(
    2, 1, 1
);