SELECT WA.alert_id, SL.severity_level, L.loc_name, C.name, AL.name,
    MIN(F.forecast_timestamp) AS min_time, MAX(F.forecast_timestamp) AS max_time, WC.description, UD.email
    FROM weather_alert AS WA
    JOIN severity_level AS SL ON (WA.severity_level_id = SL.severity_level_id)
    JOIN forecast AS F ON (WA.forecast_id = F.forecast_id)
    JOIN alert_type AS AL ON (WA.alert_type_id = AL.alert_type_id)
    JOIN weather_code AS WC ON (F.weather_code_id = WC.weather_code_id)
    JOIN weather_report AS WR ON (F.weather_report_id = WR.weather_report_id)
    JOIN location AS L ON (WR.loc_id = L.loc_id)
    JOIN county AS C ON (L.county_id = C.county_id)
    JOIN user_location_assignment AS ULA ON (L.loc_id = ULA.loc_id)
    JOIN user_details AS UD ON (ULA.user_id = UD.user_id)
    WHERE WA.notified = FALSE
    GROUP BY WA.alert_id, SL.severity_level, L.loc_name, C.name, AL.name,
    F.forecast_timestamp, WC.description, UD.email, SL.severity_level_id
    ORDER BY SL.severity_level_id DESC, L.loc_name ASC;

SELECT WA.alert_id, AL.name as "Alert type", SL.severity_level as "Severity", 
L.loc_name as "Location", L.loc_id, MIN(F.forecast_timestamp) AS min_time, MAX(F.forecast_timestamp) AS max_time
    FROM weather_alert AS WA
    JOIN forecast AS F ON (WA.forecast_id = F.forecast_id)
    JOIN severity_level AS SL ON (WA.severity_level_id = SL.severity_level_id)
    JOIN alert_type AS AL ON (WA.alert_type_id = AL.alert_type_id)
    JOIN weather_report AS WR ON (F.weather_report_id = WR.weather_report_id)
    JOIN location AS L ON (WR.loc_id = L.loc_id)
    WHERE SL.severity_level_id != 4
    GROUP BY WA.alert_id, L.loc_id, "Alert type", "Severity", SL.severity_level_id 
    ORDER BY SL.severity_level_id DESC, L.loc_id ASC;



SELECT * FROM weather_report ORDER BY weather_code_id DESC;

INSERT INTO weather_report (
    report_time, loc_id
) VALUES ('2024-04-29 17:00:41', 5);

INSERT INTO forecast (
    forecast_timestamp, visibility, humidity, precipitation, precipitation_prob, rainfall, snowfall, wind_speed, wind_direction, wind_gusts, lightning_potential, uv_index, cloud_cover, temperature, apparent_temp, weather_report_id, weather_code_id
)
VALUES (
'2024-04-30 11:00:00', 24140,74, 100, 14,100,0,17,148,32,0,4.4,100,15,13, 2576,82
), (
'2024-04-30 12:00:00', 24140,74, 100, 14,100,0,17,148,32,0,4.4,100,15,13, 2576,82
),
(
'2024-04-30 13:00:00', 24140,74, 100, 14,100,0,17,148,32,0,4.4,100,15,13, 2576,82
);

INSERT INTO weather_alert (
    alert_type_id,forecast_id,severity_level_id
) VALUES 
(8, 401813, 1),(8, 401814, 1),(8, 401815, 1);