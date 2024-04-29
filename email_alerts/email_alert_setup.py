"""Sets up the data for emailing out weather, air quality and flood alerts."""

from os import environ as ENV

from psycopg2 import connect
from psycopg2.extensions import connection
from dotenv import load_dotenv


def get_db_connection(config: dict):
    """Connect to the database."""
    return connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def select_email_list(conn: connection) -> list:
    """Gets the list of emails that should all be receiving an alert."""

    sql_query = """
    SELECT UD.email 
    FROM location AS L
    LEFT JOIN flood_warnings AS FW ON (L.loc_id = FW.loc_id)
    LEFT JOIN user_location_assignment AS ULA ON (L.loc_id = ULA.loc_id)
    JOIN user_details AS UD ON (ULA.user_id = UD.user_id)
    LEFT JOIN weather_report AS WR ON (L.loc_id = WR.loc_id)
    LEFT JOIN forecast AS F ON (WR.weather_report_id = F.weather_report_id)
    LEFT JOIN weather_alert AS WA ON (F.forecast_id = WA.forecast_id)
    LEFT JOIN air_quality AS AQ ON (WR.weather_report_id = AQ.weather_report_id)
    WHERE (FW.notified = FALSE or WA.notified = FALSE or AQ.notified = FALSE) 
    and ULA.alert_opt_in = TRUE;"""

    rows = []

    with conn.cursor() as cur:
        cur.execute(sql_query)
        conn.commit()
        rows = cur.fetchall()

    return [row[0] for row in rows]


def select_flood_warnings(conn: connection) -> list[list]:
    """Selects data from the database relating to flood alerts per user.
    The data is returned as a list of lists."""

    sql_query = """SELECT FW.flood_id, SL.severity_level,
    L.loc_name, C.name, FW.time_raised, UD.email
    FROM flood_warnings AS FW
    JOIN severity_level AS SL ON (FW.severity_level_id = SL.severity_level_id)
    JOIN location AS L ON (FW.loc_id = L.loc_id)
    JOIN county AS C ON (L.county_id = C.county_id)
    LEFT JOIN user_location_assignment AS ULA ON (L.loc_id = ULA.loc_id)
    JOIN user_details AS UD ON (ULA.user_id = UD.user_id)
    WHERE FW.notified = FALSE;"""

    rows = []
    with conn.cursor() as cur:
        cur.execute(sql_query)
        conn.commit()
        rows = cur.fetchall()

    return [list(row) for row in rows]


def select_weather_warnings(conn: connection) -> list[list]:
    """Selects data from the database relating to weather alerts per user.
    The data is returned as a list of lists."""

    sql_query = """SELECT WA.alert_id, SL.severity_level, L.loc_name, C.name, AL.name,
    F.forecast_timestamp, WC.description, WR.report_time, 
    F.temperature, F.apparent_temp, F.wind_speed, F.wind_gusts, 
    F.lightning_potential, F.snowfall, F.visibility, F.uv_index, F.rainfall, UD.email
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
    WHERE WA.notified = FALSE"""

    rows = []
    with conn.cursor() as cur:
        cur.execute(sql_query)
        conn.commit()
        rows = cur.fetchall()

    return [list(row) for row in rows]


def select_air_warnings(conn: connection) -> list[list]:
    """Selects data from the database relating to air quality alerts per user.
    The data is returned as a list of lists."""

    sql_query = """SELECT AQ.air_quality_id,
    SL.severity_level, L.loc_name, C.name,
    AQ.o3_concentration, UD.email
    FROM air_quality AS AQ
    JOIN severity_level AS SL ON (AQ.severity_level_id = SL.severity_level_id)
    JOIN weather_report AS WR ON (AQ.weather_report_id = WR.weather_report_id)
    JOIN location AS L ON (WR.loc_id = L.loc_id)
    JOIN county AS C ON (L.county_id = C.county_id)
    LEFT JOIN user_location_assignment AS ULA ON (L.loc_id = ULA.loc_id)
    JOIN user_details AS UD ON (ULA.user_id = UD.user_id)
    WHERE AQ.notified = FALSE and NOT AQ.severity_level_id = 4;"""

    rows = []
    with conn.cursor() as cur:
        cur.execute(sql_query)
        conn.commit()
        rows = cur.fetchall()

    return [list(row) for row in rows]


def emails_to_dict(emails: list[str]) -> dict:
    """Converts the list of emails to dictionaries with an empty list."""

    email_dict = {}
    for email in emails:
        email_dict[email] = []

    return email_dict


def remove_unnecessary_weather_data(warning: list[str]) -> list[str]:
    """Remove the unnecessary data from the alerts such as emails.
    The weather conditions are kept depending on the weather alert type."""

    if warning[0] != 'weather_alert':
        return warning[:-1]

    alert_type = warning[5]
    data = warning[:9]
    if alert_type == 'Wind':
        data += warning[11:13] + ['&#x1F32C;']
    if alert_type in ['Heat', 'Ice']:
        data += warning[9:11] + ['&#x1F321;']
    if alert_type == 'Lightning':
        data += [warning[13]] + ['&#x26A1;']
    if alert_type == 'Snowfall':
        data += [warning[14]] + ['&#x1F328;']
    if alert_type == 'Visibility':
        data += [warning[15]] + ['&#x1F32B;']
    if alert_type == 'UV-index':
        data += [warning[16]] + ['&#x1F506;']
    if alert_type == 'Rain':
        data += [warning[17]] + ['&#x1F327;']
    return data


def sort_warnings_to_email(emails: list[str], warnings: list[list[str]]) -> dict:
    """Creates a dictionary of the emails and all the alerts associated with each."""

    emails = emails_to_dict(emails)
    for warning in warnings:
        email = warning[-1]
        if email not in emails:
            continue

        emails[email] += [remove_unnecessary_weather_data(warning)]

    return emails


def set_up_email_data(config: dict, tables: list[str]) -> dict:
    """Returns a dictionary of all the email recipients and their respective alerts."""
    with get_db_connection(config) as conn:
        emails = select_email_list(conn)
        floods = select_flood_warnings(conn)
        weather = select_weather_warnings(conn)
        air = select_air_warnings(conn)
        warnings = [[tables[-1]] + f for f in floods]
        warnings += [[tables[0]] + w for w in weather]
        warnings += [[tables[1]] + a for a in air]
    conn.close()
    return sort_warnings_to_email(emails, warnings)


if __name__ == '__main__':
    load_dotenv()
    print(set_up_email_data(ENV))
