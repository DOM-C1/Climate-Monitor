
SELECT FW.flood_id, FW.time_raised, SL.severity_level, 
L.loc_name, C.name, UD.email
FROM flood_warnings AS FW
JOIN severity_level AS SL ON (FW.severity_level_id = SL.severity_level_id)
JOIN location AS L ON (FW.loc_id = L.loc_id)
JOIN county AS C ON (L.county_id = C.county_id)
LEFT JOIN user_location_assignment AS ULA ON (L.loc_id = ULA.loc_id)
JOIN user_details AS UD ON (ULA.user_id = UD.user_id)
WHERE FW.notified = FALSE;


SELECT WA.alert_id, SL.severity_level, AL.name, 
F.forecast_timestamp, WC.description, WR.report_time, 
L.loc_name, C.name, UD.email
FROM weather_alert AS WA
JOIN severity_level AS SL ON (WA.severity_level_id = SL.severity_level_id)
JOIN forecast AS F ON (WA.forecast_id = F.forecast_id)
JOIN alert_type AS AL ON (WA.alert_type_id = AL.alert_type_id)
JOIN weather_code AS WC ON (F.weather_code_id = WC.weather_code_id)
JOIN weather_report AS WR ON (F.weather_report_id = WR.weather_report_id)
JOIN location AS L ON (WR.loc_id = L.loc_id)
JOIN county AS C ON (L.county_id = C.county_id)
LEFT JOIN user_location_assignment AS ULA ON (L.loc_id = ULA.loc_id)
JOIN user_details AS UD ON (ULA.user_id = UD.user_id)
WHERE WA.notified = FALSE;



SELECT UD.email 
FROM location AS L
LEFT JOIN flood_warnings AS FW ON (L.loc_id = FW.loc_id)
LEFT JOIN user_location_assignment AS ULA ON (L.loc_id = ULA.loc_id)
JOIN user_details AS UD ON (ULA.user_id = UD.user_id)
LEFT JOIN weather_report AS WR ON (L.loc_id = WR.loc_id)
LEFT JOIN forecast AS F ON (WR.weather_report_id = F.weather_report_id)
LEFT JOIN weather_alert AS WA ON (F.forecast_id = WA.forecast_id)
LEFT JOIN air_quality AS AQ ON (WR.weather_report_id = AQ.weather_report_id)
WHERE FW.notified = FALSE or WA.notified = FALSE or AQ.notified = FALSE;


SELECT AQ.air_quality_id, SL.severity_level, 
AQ.o3_concentration, 
L.loc_name, C.name, UD.email
FROM air_quality AS AQ
JOIN severity_level AS SL ON (AQ.severity_level_id = SL.severity_level_id)
JOIN weather_report AS WR ON (AQ.weather_report_id = WR.weather_report_id)
JOIN location AS L ON (WR.loc_id = L.loc_id)
JOIN county AS C ON (L.county_id = C.county_id)
LEFT JOIN user_location_assignment AS ULA ON (L.loc_id = ULA.loc_id)
JOIN user_details AS UD ON (ULA.user_id = UD.user_id)
WHERE AQ.notified = FALSE;



SELECT WA.alert_id, SL.severity_level, L.loc_name, C.name, AL.name, 
    F.forecast_timestamp, WC.description, WR.report_time, 
    F.temperature, UD.email
    FROM weather_alert AS WA
    JOIN severity_level AS SL ON (WA.severity_level_id = SL.severity_level_id)
    JOIN forecast AS F ON (WA.forecast_id = F.forecast_id)
    JOIN alert_type AS AL ON (WA.alert_type_id = AL.alert_type_id)
    JOIN weather_code AS WC ON (F.weather_code_id = WC.weather_code_id)
    JOIN weather_report AS WR ON (F.weather_report_id = WR.weather_report_id)
    JOIN location AS L ON (WR.loc_id = L.loc_id)
    JOIN county AS C ON (L.county_id = C.county_id)
    LEFT JOIN user_location_assignment AS ULA ON (L.loc_id = ULA.loc_id)
    JOIN user_details AS UD ON (ULA.user_id = UD.user_id)
    WHERE WA.notified = FALSE;