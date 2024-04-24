




SELECT *
FROM weather_report AS WR
JOIN location AS L ON (WR.loc_id = L.loc_id)
JOIN flood_warnings AS FW ON (L.loc_id = FW.loc_id)
JOIN severity_level AS SL ON (FW.severity_level_id = SL.severity_level_id)
WHERE WR.weather_report_id == 1;