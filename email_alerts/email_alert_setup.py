"""Sets up the data for emailing out weather, air quality and flood alerts."""

from os import environ as ENV

from psycopg2 import connect
from psycopg2.extensions import connection
from dotenv import load_dotenv

ALERT_TYPE_NAME_POS = 4
ALERT_TYPE_POS = 0


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

    sql_query = """SELECT C.name, SL.severity_level, L.loc_name, AL.name,
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
    GROUP BY SL.severity_level, L.loc_name, C.name, AL.name, WC.description, UD.email, SL.severity_level_id
    ORDER BY min_time DESC, SL.severity_level_id ASC"""

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


def add_unicode_symbols_weather(warning: list[str]) -> list[str]:
    """Remove the unnecessary data from the alerts such as emails.
    The weather conditions are kept depending on the weather alert type."""

    data = warning[:-1]
    if warning[ALERT_TYPE_POS] != 'weather_alert':
        return data

    alert_type = warning[ALERT_TYPE_NAME_POS]
    if alert_type == 'Wind':
        data += ['&#x1F32C;']
    if alert_type in ['Heat', 'Ice']:
        data += ['&#x1F321;']
    if alert_type == 'Lightning':
        data += ['&#x26A1;']
    if alert_type == 'Snowfall':
        data += ['&#x1F328;']
    if alert_type == 'Visibility':
        data += ['&#x1F32B;']
    if alert_type == 'UV-index':
        data += ['&#x1F506;']
    if alert_type == 'Rain':
        data += ['&#x1F327;']
    return data


def sort_warnings_to_email(emails: list[str], warnings: list[list[str]]) -> dict:
    """Creates a dictionary of the emails and all the alerts associated with each."""

    emails = emails_to_dict(emails)
    for warning in warnings:
        email = warning[-1]
        if email not in emails:
            continue

        emails[email] += [add_unicode_symbols_weather(warning)]

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
