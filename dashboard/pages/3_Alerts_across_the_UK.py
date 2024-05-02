from datetime import datetime
from os import environ as ENV

import altair as alt
import pandas as pd
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import streamlit as st
import pydeck as pdk


@st.cache_resource
def connect_to_db(config):
    """Returns a live database connection."""
    return connect(
        host=config["DB_HOST"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
        port=config["DB_PORT"]
    )


def time_rounder(timestamp: datetime) -> datetime:
    """Obtains the most recent 15 min time, or the most recent hour"""
    return (timestamp.replace(second=0, microsecond=0, minute=(timestamp.minute // 15 * 15)))


def get_locations_with_alerts(_conn):
    """Get the loc_id and alert type if they exist in database"""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute("""SELECT AL.name as "Alert type", SL.severity_level as "Severity",
                    L.loc_name as "Location", L.loc_id, MIN(F.forecast_timestamp) as min_time, MAX(F.forecast_timestamp) as max_time
                    FROM weather_alert AS WA
                    JOIN forecast AS F ON (WA.forecast_id = F.forecast_id)
                    JOIN severity_level AS SL ON (WA.severity_level_id = SL.severity_level_id)
                    JOIN alert_type AS AL ON (WA.alert_type_id = AL.alert_type_id)
                    JOIN weather_report AS WR ON (F.weather_report_id = WR.weather_report_id)
                    JOIN location AS L ON (WR.loc_id = L.loc_id)
                    WHERE SL.severity_level_id < 4
                    AND F.forecast_timestamp > NOW()
                    GROUP BY L.loc_id, "Alert type", "Severity", SL.severity_level_id
                    ORDER BY SL.severity_level_id DESC, L.loc_id ASC
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame(rows)
    return data_f


def get_flood_alerts(_conn):
    """Get all flood alerts for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT SL.severity_level AS "Severity", C.name AS "County", FW.time_raised AS "Time raised"
                        FROM flood_warnings AS FW
                        JOIN severity_level AS SL ON (FW.severity_level_id = SL.severity_level_id)
                        JOIN location AS L ON (FW.loc_id = L.loc_id)
                        JOIN county AS C ON (L.county_id = C.county_id)
                        WHERE SL.severity_level_id < 4
                        AND FW.time_raised > NOW() - interval '12 hours'
                        ORDER BY SL.severity_level_id ASC""")

        rows = cur.fetchall()
        data_f = pd.DataFrame(rows)
        print(data_f)
    data_f["Time raised"] = data_f["Time raised"].apply(
        lambda x: x.replace(second=0))
    return data_f.drop_duplicates().groupby(["County"])


def get_air_quality_alerts(_conn, location):
    """Get all air quality alerts for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT SL.severity_level AS "Severity",
                    MIN(WR.report_time) as min_time, MAX(WR.report_time) as max_time
                    FROM air_quality AS AQ
                    JOIN weather_report as WR ON (WR.weather_report_id = AQ.weather_report_id)
                    JOIN severity_level AS SL ON (AQ.severity_level_id = SL.severity_level_id)
                    JOIN location AS L ON (WR.loc_id = L.loc_id)
                    WHERE L.loc_name = '{location}'
                    AND SL.severity_level_id < 4
                    GROUP BY "Severity", SL.severity_level_id
                    ORDER BY SL.severity_level_id ASC""")

        rows = cur.fetchall()
    if rows:
        data_f = pd.DataFrame(rows).drop_duplicates()
        data_f["Alert type"] = None
        data_f['min_time'] = data_f['min_time'].apply(time_rounder)
        data_f['max_time'] = data_f['max_time'].apply(time_rounder)

        for i in data_f.index:
            data_f["Alert type"][i] = 'Air Quality'
        return data_f
    return pd.DataFrame()


def format_time_list(times):
    if len(times) == 1:
        return str(times[0])
    time_str = ''
    times = sorted(times)
    for time in times[:-2]:
        time_str += '**' + str(time) + '**' + ', '
    time_str += '**' + str(times[-2]) + '**' + \
        ' and ' + '**' + str(times[-1]) + '**'
    return time_str


def write_floods(floods: pd.DataFrame) -> tuple[list[tuple[str]]]:
    """Write streamlit warnings for flood alerts."""
    errors = []
    warnings = []
    county = floods["County"].values[0]
    floods["Dates"] = floods["Time raised"].dt.date.values
    floods = floods.groupby(["Severity"])
    for _, flood_s in floods:
        flood_d = flood_s.groupby(["Dates"])
        for _, flood in flood_d:
            times = flood["Time raised"].dt.time.values
            times = format_time_list(times)
            severity = flood["Severity"].unique()[0]
            date_val = flood["Dates"].values[0]
            if date_val == datetime.today().date():
                date_val = '**Today**'
            else:
                date_val = f'on **{date_val}**'
            if severity == "Severe Warning":
                errors.append((
                    f'**{county}** had a **Severe Flood Warning** raised {date_val} at {times}.', "🚨"))
            elif severity == "Warning":
                errors.append((
                    f'**{county}** had a **Flood Warning** raised {date_val} at {times}.', "⚠️"))

            elif severity == "Alert":
                warnings.append((
                    f'**{county}** had a **Flood Alert** raised {date_val} at {times}.', "❕"))
    return errors, warnings


if __name__ == "__main__":
    load_dotenv()
    st.title("Weather alerts across the UK")
    conn = connect_to_db(dict(ENV))
    alerts = get_locations_with_alerts(conn)
    floods = get_flood_alerts(conn)

    if floods:
        errors = []
        warnings = []
        st.markdown("### Flood warnings")
        for _, location in floods:
            flood_alerts = write_floods(location)
            errors += flood_alerts[0]
            warnings += flood_alerts[1]
        for error in errors:
            st.error(error[0], icon=error[1])

        with st.expander('Mild flood alerts'):
            for warning in warnings:
                st.warning(warning[0], icon=warning[1])

    if not alerts.empty:
        st.markdown("### Weather warnings")
        for _, alert in alerts.iterrows():
            if alert["Severity"] == "Alert":
                icon = "❕"
            elif alert["Severity"] == "Warning":
                icon = "⚠️"
            elif alert["Severity"] == "Severe Warning":
                icon = "🚨"
            if alert["Alert type"] == "Air Quality":
                key_words = 'had an'
            else:
                key_words = 'has a'
            if alert["min_time"] != alert["max_time"]:
                st.warning(
                    f'**{alert["Location"]}** {key_words} **{alert["Alert type"]} {alert["Severity"]}** from **{alert["min_time"]}** to **{alert["max_time"]}**.', icon=icon)
            else:
                st.warning(
                    f'**{alert["Location"]}** {key_words} **{alert["Alert type"]} {alert["Severity"]}** at **{alert["min_time"]}**.', icon=icon)
