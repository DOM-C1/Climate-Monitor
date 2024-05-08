"""Create a streamlit page displaying weather and flood alerts across the UK."""

from datetime import datetime
from os import environ as ENV

from dotenv import load_dotenv
import pandas as pd
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection
import streamlit as st


@st.cache_resource
def connect_to_db(config: dict) -> connection:
    """Returns a live database connection."""
    return connect(
        host=config["DB_HOST"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
        port=config["DB_PORT"]
    )


def time_rounder(timestamp: datetime) -> datetime:
    """Obtains the most recent 15 min time."""
    return timestamp.replace(second=0, microsecond=0,
                             minute=timestamp.minute // 15 * 15)


def get_locations_with_alerts(_conn: connection) -> pd.DataFrame:
    """Get the weather alert information from the database"""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute("""SELECT AL.name as "Alert type", SL.severity_level as "Severity",
                    L.loc_name as "Location", MIN(F.forecast_timestamp) as min_time,
                    MAX(F.forecast_timestamp) as max_time, L.loc_id
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
        if rows:
            data_f = pd.DataFrame.from_dict(
                rows).drop_duplicates()

            data_f = data_f.groupby(['Location'])
            locations = []
            for _, data_frame in data_f:
                loc_dup_group = data_frame.sort_values(
                    ['loc_id']).groupby(['loc_id'])
                locations.append(
                    [data_frame for _, data_frame in loc_dup_group][0].drop_duplicates())
            return locations
    return pd.DataFrame()


def get_flood_alerts(_conn: connection) -> pd.DataFrame:
    """Get all flood alerts for all locations."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute("""SELECT SL.severity_level AS "Severity", C.name AS "County",
                    FW.time_raised AS "Time raised"
                    FROM flood_warnings AS FW
                    JOIN severity_level AS SL ON (FW.severity_level_id = SL.severity_level_id)
                    JOIN location AS L ON (FW.loc_id = L.loc_id)
                    JOIN county AS C ON (L.county_id = C.county_id)
                    WHERE SL.severity_level_id < 4
                    AND FW.time_raised > NOW() - interval '12 hours'
                    ORDER BY SL.severity_level_id ASC""")

        rows = cur.fetchall()
        data_f = pd.DataFrame(rows)

    data_f.loc[:, "Time raised"] = data_f.loc[:, "Time raised"].apply(
        lambda x: x.replace(second=0))
    return data_f.drop_duplicates().groupby(["County"])


def get_air_quality_alerts(_conn: connection) -> pd.DataFrame:
    """Get all air quality alerts for all locations."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute("""SELECT SL.severity_level AS "Severity", L.loc_name as "Location", L.loc_id,
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
        data_f.loc[:, "Alert type"] = None
        data_f.loc[:, 'min_time'] = data_f.loc[:,
                                               'min_time'].apply(time_rounder)
        data_f.loc[:, 'max_time'] = data_f.loc[:,
                                               'max_time'].apply(time_rounder)
        data_f = data_f.loc[data_f.loc[:, 'max_time']
                            >= time_rounder(datetime.now()), :]

        for i in data_f.index:
            data_f.loc[:, "Alert type"][i] = 'Air Quality'
        return data_f.drop_duplicates()

    return pd.DataFrame()


def format_time_list(times: list) -> str:
    """Format times for appropiate time ranges in markdown."""
    if len(times) == 1:
        return '**' + str(times[0]) + '**'
    time_str = ''
    times = sorted(times)
    for time in times[:-2]:
        time_str += '**' + str(time) + '**' + ', '
    time_str += '**' + str(times[-2]) + '**' + \
        ' and ' + '**' + str(times[-1]) + '**'
    return time_str


def write_floods(flood_alerts: pd.DataFrame) -> tuple[list[tuple[str]]]:
    """Create and format warnings for flood alerts."""
    severes = []
    warnings = []
    alerts = []
    county = flood_alerts.loc[:, "County"].values[0]
    flood_alerts.loc[:, "Dates"] = flood_alerts.loc[:,
                                                    "Time raised"].dt.date.values
    flood_alerts = flood_alerts.groupby(["Severity"])
    for _, flood_s in flood_alerts:
        flood_d = flood_s.groupby(["Dates"])
        for _, flood in flood_d:
            times = flood.loc[:, "Time raised"].apply(
                time_rounder).dt.time.values
            times = format_time_list(times)
            severity = flood.loc[:, "Severity"].unique()[0]
            date_val = flood.loc[:, "Dates"].values[0]
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


def get_min_max_dates_times(w_alert: pd.Series) -> tuple[str]:
    """Extract forecast dates and times from a weather alert."""
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
    return time_min, time_max, date_min, date_max


def write_alert(w_alert, location):
    """Write strings for """
    alert_type = w_alert["Alert type"]
    time_min, time_max, date_min, date_max = get_min_max_dates_times(
        w_alert)
    if w_alert["Alert type"] == "Air Quality":
        key_words = 'had an'
    else:
        key_words = 'has a'

    if date_min != date_max:
        return [f'**{location} ** {key_words} **', alert_type, f'** raised from **{date_min}** at \
                **{time_min}** to **{date_max}** at **{time_max}**.']
    if time_min != time_max:
        return [f'**{location}** {key_words} **', alert_type, f'** raised \
                        **{date_min}** from **{time_min}** to **{time_max}**.']
    return [f'**{location}** {key_words} **', alert_type, f'** raised \
                        **{date_min}** at **{time_min}**.']


def write_alerts(weather_alerts: pd.DataFrame) -> list[str]:
    """Create weather alert strings for various severities at a specfic location."""
    severes = []
    warnings = []
    alerts = []
    location = w_alerts.loc[:, "Location"].values[0]
    weather_alerts = weather_alerts.groupby(["Severity"])
    for _, w_alert_a in weather_alerts:
        severity = w_alert_a.loc[:, "Severity"].values[0]
        for _, w_alert in w_alert_a.sort_values(['min_time']).iterrows():
            first_line, alert_type, second_line = write_alert(
                w_alert, location)
            if severity == 'Severe Warning':
                severes.append('🚨 ' + first_line + 'Severe' +
                               alert_type + 'Warning' + second_line)
            if severity == 'Warning':
                warnings.append('⚠️ ' + first_line +
                                alert_type + 'Warning' + second_line)
            if severity == 'Alert':
                alerts.append('❗ ' + first_line + alert_type +
                              'Alert' + second_line)
    return severes, warnings, alerts


if __name__ == "__main__":
    load_dotenv()
    st.title("Weather alerts across the UK")
    conn = connect_to_db(dict(ENV))
    w_alerts = get_locations_with_alerts(conn)
    air_alerts = get_air_quality_alerts(conn)
    floods = get_flood_alerts(conn)
    st.markdown("### Flood warnings")
    if floods:
        f_severes = []
        f_warnings = []
        f_alerts = []
        for _, loc in floods:
            flood_alert_lists = write_floods(loc)
            f_severes += flood_alert_lists[0]
            f_warnings += flood_alert_lists[1]
            f_alerts += flood_alert_lists[2]
        for severe in f_severes:
            st.markdown(
                f"""<span style="background-color:rgb(128,0,128,0.2);color:	#5c005c;
                font-size:1.35em;border-radius:5px;padding:10px;">{severe}</span>""",
                unsafe_allow_html=True)
        for warning in f_warnings:
            st.markdown(
                f"""<span style="background-color:rgb(240,128,128,0.2);color:#670000;
                font-size:1.35em;border-radius:5px;padding:10px;">{warning}</span>""",
                unsafe_allow_html=True)
        with st.expander('Mild flood alerts'):
            for alert in f_alerts:
                st.markdown(
                    f"""<span style="background-color:rgb(255,205,0,0.2);color:#423d01;
                    font-size:1.2em;border-radius:5px;padding:8px;">{alert}</span>""",
                    unsafe_allow_html=True)
    else:
        st.markdown("""No flood alerts to show!""")
    st.markdown("### Weather warnings")
    if not w_alerts.empty:
        w_severes = []
        w_warnings = []
        w_alerts = []
        for _, loc in w_alerts.groupby("Location"):
            weather_alert_list = write_alerts(loc)
            w_severes += weather_alert_list[0]
            w_warnings += weather_alert_list[1]
            w_alerts += weather_alert_list[2]
        for severe in w_severes:
            st.markdown(
                f"""<span style="background-color:rgb(128,0,128,0.2);color:	#5c005c;
                font-size:1.35em;border-radius:5px;padding:10px;">{severe}</span>""",
                unsafe_allow_html=True)
        for warning in w_warnings:
            st.markdown(
                f"""<span style="background-color:rgb(240,128,128,0.2);color:#670000;
                font-size:1.35em;border-radius:5px;padding:10px;">{warning}</span>""",
                unsafe_allow_html=True)
        for alert in w_alerts:
            st.markdown(
                f"""<span style="background-color:rgb(255,205,0,0.2);color:#423d01;
                font-size:1.2em;border-radius:5px;padding:8px;">{alert}</span>""",
                unsafe_allow_html=True)
    else:
        st.markdown("""No weather alerts to show!""")
    st.markdown("### Air quality warnings")
    if not air_alerts.empty:
        a_severes = []
        a_warnings = []
        a_alerts = []
        for _, loc in air_alerts.groupby("Location"):
            air_quality_alerts = write_alerts(loc)
            a_severes += air_quality_alerts[0]
            a_warnings += air_quality_alerts[1]
            a_alerts += air_quality_alerts[2]
        for severe in a_severes:
            st.markdown(
                f"""<span style="background-color:rgb(128,0,128,0.2);color:	#5c005c;
                font-size:1.35em;border-radius:5px;padding:10px;">{severe}</span>""",
                unsafe_allow_html=True)
        for warning in a_warnings:
            st.markdown(
                f"""<span style="background-color:rgb(240,128,128,0.2);color:#670000;
                font-size:1.35em;border-radius:5px;padding:10px;">{warning}</span>""",
                unsafe_allow_html=True)
        for alert in a_alerts:
            st.markdown(
                f"""<span style="background-color:rgb(255,205,0,0.2);color:#423d01;
                font-size:1.2em;border-radius:5px;padding:8px;">{alert}</span>""",
                unsafe_allow_html=True)
    else:
        st.markdown("""No air quality alerts to show!""")
