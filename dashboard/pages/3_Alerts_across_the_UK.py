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
        cur.execute(f"""SELECT AL.name as "Alert type", SL.severity_level as "Severity",
                    L.loc_name as "Location", L.loc_id, MIN(F.forecast_timestamp) as min_time, MAX(F.forecast_timestamp) as max_time
                    FROM weather_alert AS WA
                    JOIN forecast AS F ON (WA.forecast_id = F.forecast_id)
                    JOIN severity_level AS SL ON (WA.severity_level_id = SL.severity_level_id)
                    JOIN alert_type AS AL ON (WA.alert_type_id = AL.alert_type_id)
                    JOIN weather_report AS WR ON (F.weather_report_id = WR.weather_report_id)
                    JOIN location AS L ON (WR.loc_id = L.loc_id)
                    WHERE SL.severity_level_id < 4

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

    data_f["Time raised"] = data_f["Time raised"].apply(
        lambda x: x.replace(second=0))
    return data_f.drop_duplicates().groupby(["County"])


def get_air_quality_alerts(_conn):
    """Get all air quality alerts for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT SL.severity_level AS "Severity", L.loc_name as "Location", L.loc_id,
                    MIN(WR.report_time) as min_time, MAX(WR.report_time) as max_time
                    FROM air_quality AS AQ
                    JOIN weather_report as WR ON (WR.weather_report_id = AQ.weather_report_id)
                    JOIN severity_level AS SL ON (AQ.severity_level_id = SL.severity_level_id)
                    JOIN location AS L ON (WR.loc_id = L.loc_id)
                    WHERE SL.severity_level_id < 4
                    GROUP BY "Severity", SL.severity_level_id, L.loc_id, "Location"
                    ORDER BY SL.severity_level_id ASC""")

        rows = cur.fetchall()
    if rows:
        data_f = pd.DataFrame(rows).drop_duplicates()
        data_f["Alert type"] = None
        data_f['min_time'] = data_f['min_time'].apply(time_rounder)
        data_f['max_time'] = data_f['max_time'].apply(time_rounder)
        data_f = data_f[data_f['max_time'] >= time_rounder(datetime.now())]

        for i in data_f.index:
            data_f["Alert type"][i] = 'Air Quality'
        print(data_f)
        return data_f.drop_duplicates()

    return pd.DataFrame()


def format_time_list(times):
    if len(times) == 1:
        return '**' + str(times[0]) + '**'
    time_str = ''
    times = sorted(times)
    for time in times[:-2]:
        time_str += '**' + str(time) + '**' + ', '
    time_str += '**' + str(times[-2]) + '**' + \
        ' and ' + '**' + str(times[-1]) + '**'
    return time_str


def write_floods(floods: pd.DataFrame) -> tuple[list[tuple[str]]]:
    """Write streamlit warnings for flood alerts."""
    severes = []
    warnings = []
    alerts = []
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
                severes.append(
                    f'🚨 **{county}** had a **Severe Flood Warning** raised {date_val} at {times}.')
            elif severity == "Warning":
                warnings.append(
                    f'⚠️ **{county}** had a **Flood Warning** raised {date_val} at {times}.')
            elif severity == "Alert":
                alerts.append(
                    f'❗ **{county}** had a **Flood Alert** raised {date_val} at {times}.')
    return severes, warnings, alerts


def write_alerts(w_alerts: pd.DataFrame):
    print(w_alerts)
    severes = []
    warnings = []
    alerts = []
    location = w_alerts["Location"].values[0]
    w_alerts = w_alerts.groupby(["Alert type"])
    for _, w_alert_a in w_alerts:
        alert_type = w_alert_a["Alert type"].values[0]
        for _, w_alert in w_alert_a.sort_values(['min_time']).iterrows():
            severity = w_alert["Severity"]
            datetime_min = w_alert['min_time']
            date_min = datetime_min.date()
            time_min = datetime_min.time()
            datetime_max = w_alert['max_time']
            date_max = datetime_max.date()
            time_max = datetime_max.time()
            if date_min == datetime.today().date():
                date_min = '**Today**'
            if date_max == datetime.today().date():
                date_max = '**Today**'
            if w_alert["Alert type"] == "Air Quality":
                key_words = 'had an'
            else:
                key_words = 'has a'

            if date_min != date_max:
                if severity == "Severe Warning":
                    severes.append(
                        f'🚨 **{location}** {key_words} **Severe {alert_type} Warning** raised from **{date_min}** at **{time_min}** to **{date_max}** at **{time_max}**.')
                elif severity == "Warning":
                    warnings.append(
                        f'⚠️ **{location}** {key_words} **{alert_type} Warning** raised from **{date_min}** at **{time_min}** to **{date_max}** at **{time_max}**.')
                elif severity == "Alert":
                    alerts.append(
                        f'❗ **{location}** {key_words} **{alert_type} Alert** raised from **{date_min}** at **{time_min}** to **{date_max}** at **{time_max}**.')
            else:
                if time_min != time_max:
                    if severity == "Severe Warning":
                        severes.append(
                            f'🚨 **{location}** {key_words} **Severe {alert_type} Warning** raised **{date_min}** from **{time_min}** to **{time_max}**.')
                    elif severity == "Warning":
                        warnings.append(
                            f'⚠️ **{location}** {key_words} **{alert_type} Warning** raised **{date_min}** from **{time_min}** to **{time_max}**.')
                    elif severity == "Alert":
                        alerts.append(
                            f'❗ **{location}** {key_words} **{alert_type} Alert** raised **{date_min}** from **{time_min}** to **{time_max}**.')
                else:
                    if severity == "Severe Warning":
                        severes.append(
                            f'🚨 **{location}** {key_words} **Severe {alert_type} Warning** raised **{date_min}** at **{time_min}**.')
                    elif severity == "Warning":
                        warnings.append(
                            f'⚠️ **{location}** {key_words} **{alert_type} Warning** raised **{date_min}** at **{time_min}**.')
                    elif severity == "Alert":
                        alerts.append(
                            f'❗ **{location}** {key_words} **{alert_type} Alert** raised **{date_min}** at **{time_min}**.')
    return severes, warnings, alerts


...


if __name__ == "__main__":
    load_dotenv()
    st.title("Weather alerts across the UK")
    conn = connect_to_db(dict(ENV))
    w_alerts = get_locations_with_alerts(conn)
    air_alerts = get_air_quality_alerts(conn)
    floods = get_flood_alerts(conn)

    if floods:
        severes = []
        warnings = []
        alerts = []
        st.markdown("### Flood warnings")
        for _, location in floods:
            flood_alerts = write_floods(location)
            severes += flood_alerts[0]
            warnings += flood_alerts[1]
            alerts += flood_alerts[2]
        for severe in severes:
            st.markdown(
                f"""<span style="background-color:rgb(128,0,128,0.2);color:	#5c005c;font-size:1.35em;border-radius:5px;padding:10px;">{severe}</span>""", unsafe_allow_html=True)
        for warning in warnings:
            st.markdown(
                f"""<span style="background-color:rgb(240,128,128,0.2);color:#670000;font-size:1.35em;border-radius:5px;padding:10px;">{warning}</span>""", unsafe_allow_html=True)
        with st.expander('Mild flood alerts'):
            for alert in alerts:
                st.markdown(
                    f"""<span style="background-color:rgb(255,205,0,0.2);color:#423d01;font-size:1.2em;border-radius:5px;padding:8px;">{alert}</span>""", unsafe_allow_html=True)

    if not w_alerts.empty:
        severes = []
        warnings = []
        alerts = []
        st.markdown("### Weather warnings")
        for _, location in w_alerts.groupby("Location"):
            weather_alerts = write_alerts(location)
            severes += weather_alerts[0]
            warnings += weather_alerts[1]
            alerts += weather_alerts[2]
        for severe in severes:
            st.markdown(
                f"""<span style="background-color:rgb(128,0,128,0.2);color:	#5c005c;font-size:1.35em;border-radius:5px;padding:10px;">{severe}</span>""", unsafe_allow_html=True)
        for warning in warnings:
            st.markdown(
                f"""<span style="background-color:rgb(240,128,128,0.2);color:#670000;font-size:1.35em;border-radius:5px;padding:10px;">{warning}</span>""", unsafe_allow_html=True)
        for alert in alerts:
            st.markdown(
                f"""<span style="background-color:rgb(255,205,0,0.2);color:#423d01;font-size:1.2em;border-radius:5px;padding:8px;">{alert}</span>""", unsafe_allow_html=True)
    if not air_alerts.empty:
        severes = []
        warnings = []
        alerts = []
        st.markdown("### Air quality warnings")
        for _, location in air_alerts.groupby("Location"):
            air_quality_alerts = write_alerts(location)
            severes += air_quality_alerts[0]
            warnings += air_quality_alerts[1]
            alerts += air_quality_alerts[2]
        for severe in severes:
            st.markdown(
                f"""<span style="background-color:rgb(128,0,128,0.2);color:	#5c005c;font-size:1.35em;border-radius:5px;padding:10px;">{severe}</span>""", unsafe_allow_html=True)
        for warning in warnings:
            st.markdown(
                f"""<span style="background-color:rgb(240,128,128,0.2);color:#670000;font-size:1.35em;border-radius:5px;padding:10px;">{warning}</span>""", unsafe_allow_html=True)
        for alert in alerts:
            st.markdown(
                f"""<span style="background-color:rgb(255,205,0,0.2);color:#423d01;font-size:1.2em;border-radius:5px;padding:8px;">{alert}</span>""", unsafe_allow_html=True)
