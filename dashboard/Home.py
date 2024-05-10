"""Generate and display forecast data for a specific location."""

from datetime import datetime
from os import environ as ENV

import altair as alt
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection
import pydeck as pdk
import streamlit as st

SUN_URL = """https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Weather-clear.svg/2048px-Weat
her-clear.svg.png"""
SUN_CLOUD_URL = """https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/Antu_com.librehat.yahoo
weather.svg/2048px-Antu_com.librehat.yahooweather.svg.png"""
CLOUD_URL = """https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Antu_weather-many-clouds.sv
g/768px-Antu_weather-many-clouds.svg.png"""
FOG_URL = """https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Breeze-weather-mist-48.svg/20
48px-Breeze-weather-mist-48.svg.png"""
DRIZZLE_URL = """https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Faenza-weather-showers-sc
attered-symbolic.svg/2048px-Faenza-weather-showers-scattered-symbolic.svg.png"""
RAIN_URL = """https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Breeze-weather-showers-scatt
ered-48.svg/2048px-Breeze-weather-showers-scattered-48.svg.png"""
FREEZE_RAIN_URL = """https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Antu_weather-freezing
-rain.svg/2048px-Antu_weather-freezing-rain.svg.png"""
SNOW_URL = """https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Antu_weather-snow-scattered.
svg/2048px-Antu_weather-snow-scattered.svg.png"""
THUNDER_URL = """https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Antu_weather-storm-day.sv
g/2048px-Antu_weather-storm-day.svg.png"""


def icon_data(weather_code: int) -> dict:
    """Get the relevant url data for a given weather code."""
    if weather_code in range(0, 2):
        url = SUN_URL
    if weather_code == 2:
        url = SUN_CLOUD_URL
    if weather_code == 3:
        url = CLOUD_URL
    if weather_code in range(45, 49):
        url = FOG_URL
    if weather_code in range(51, 58):
        url = DRIZZLE_URL
    if weather_code in range(61, 66) or weather_code in range(80, 83):
        url = RAIN_URL
    if weather_code in range(67, 59):
        url = FREEZE_RAIN_URL
    if weather_code in range(71, 78) or weather_code in range(85, 87):
        url = SNOW_URL
    if weather_code in range(95, 100):
        url = THUNDER_URL
    return {
        "url": url,
        "width": 242,
        "height": 242,
        "anchorY": 242,
    }


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


def time_rounder(timestamp: datetime, get_fifteen: bool = True) -> datetime:
    """Obtains the most recent 15 min time, or the most recent hour"""
    if get_fifteen:
        return timestamp.replace(second=0, microsecond=0, minute=timestamp.minute // 15 * 15)
    return timestamp.replace(second=0, microsecond=0, minute=0)


def get_locations(_conn: connection) -> pd.DataFrame:
    """Get a list of all locations that are associated with forecast data."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SELECT loc_name, latitude, longitude
                    FROM location
                    WHERE loc_id IN
                    (SELECT loc_id FROM weather_report)""")
        locations = cur.fetchall()
    return pd.DataFrame(locations)


def get_weather_alerts(_conn: connection, location: str) -> pd.DataFrame:
    """Get all weather alerts for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT AL.name AS "Alert type", SL.severity_level AS "Severity",
                    MIN(F.forecast_timestamp) AS min_time, MAX(F.forecast_timestamp) AS max_time
                    FROM weather_alert AS WA
                    JOIN forecast AS F ON (WA.forecast_id = F.forecast_id)
                    JOIN severity_level AS SL ON (WA.severity_level_id = SL.severity_level_id)
                    JOIN alert_type AS AL ON (WA.alert_type_id = AL.alert_type_id)
                    JOIN weather_report AS WR ON (F.weather_report_id = WR.weather_report_id)
                    JOIN location AS L ON (WR.loc_id = L.loc_id)
                    WHERE SL.severity_level_id < 4
                    AND F.forecast_timestamp > NOW()
                    AND L.loc_name = '{location}'
                    GROUP BY L.loc_id, "Alert type", "Severity", SL.severity_level_id
                    ORDER BY SL.severity_level_id ASC
                    """)

        rows = cur.fetchall()
        weather_data = pd.DataFrame(rows).drop_duplicates()
    return weather_data


def get_flood_alerts(_conn: connection, location: str) -> pd.DataFrame:
    """Get all flood alerts for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT SL.severity_level AS "Severity", C.name AS "County",
                    FW.time_raised AS "Time raised"
                    FROM flood_warnings AS FW
                    JOIN severity_level AS SL ON (FW.severity_level_id = SL.severity_level_id)
                    JOIN location AS L ON (FW.loc_id = L.loc_id)
                    JOIN county AS C ON (L.county_id = C.county_id)
                    WHERE L.loc_name = '{location}'
                    AND SL.severity_level_id < 4
                    AND FW.time_raised > NOW() - interval '12 hours'
                    ORDER BY SL.severity_level_id ASC""")

        rows = cur.fetchall()
        flood_data = pd.DataFrame(rows).drop_duplicates()
    return flood_data


def get_air_quality_alerts(_conn: connection, location: str) -> pd.DataFrame:
    """Get all air quality alerts for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT SL.severity_level AS "Severity",
                    MIN(WR.report_time) AS min_time, MAX(WR.report_time) AS max_time
                    FROM air_quality AS AQ
                    JOIN weather_report AS WR ON (WR.weather_report_id = AQ.weather_report_id)
                    JOIN severity_level AS SL ON (AQ.severity_level_id = SL.severity_level_id)
                    JOIN location AS L ON (WR.loc_id = L.loc_id)
                    WHERE L.loc_name = '{location}'
                    AND SL.severity_level_id < 4
                    GROUP BY "Severity", SL.severity_level_id
                    ORDER BY SL.severity_level_id ASC""")

        rows = cur.fetchall()
    if rows:
        air_q_data = pd.DataFrame(rows).drop_duplicates()
        air_q_data.loc[:, "Alert type"] = pd.Series(
            ["Air Quality" for _ in range(len(air_q_data))])
        air_q_data.loc[:, 'min_time'] = air_q_data.loc[:, 'min_time'].apply(
            time_rounder)
        air_q_data.loc[:, 'max_time'] = air_q_data.loc[:, 'max_time'].apply(
            time_rounder)
        air_q_data = air_q_data.loc[air_q_data.loc[:, 'max_time']
                                    >= time_rounder(datetime.now()), :]
        return air_q_data
    return pd.DataFrame()


def get_location_forecast_day(_conn: connection, location: str) -> pd.DataFrame:
    """Returns forecast data for the upcoming day for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SET TIMEZONE TO 'Europe/London'")
        cur.execute(f"""SELECT L.loc_id, L.loc_name, L.latitude, L.longitude,
                    f.forecast_timestamp AS "Forecast time", wc.description AS "Weather", f.temperature AS "Temperature",
                    f.apparent_temp AS "Feels like", f.precipitation_prob AS "Precipitation probability", f.rainfall AS "Rainfall",
                    f.precipitation AS "Precipitation", f.snowfall AS "Snowfall", f.visibility AS "Visibility", f.humidity AS "Humidity",
                    f.lightning_potential AS "Lightning potential", f.wind_speed AS "Wind speed", f.cloud_cover AS "Cloud cover"
                    FROM location AS l
                    JOIN county AS c
                    ON (l.county_id=c.county_id)
                    JOIN country AS co
                    ON (c.country_id=co.country_id)
                    JOIN weather_report AS w
                    ON (l.loc_id=w.loc_id)
                    JOIN forecast AS f
                    ON (f.weather_report_id=w.weather_report_id)
                    JOIN weather_code AS wc
                    ON (F.weather_code_id=wc.weather_code_id)
                    WHERE F.forecast_timestamp < NOW() + interval '8 hours'
                    AND F.forecast_timestamp > NOW() - interval '15 minutes'
                    AND L.loc_name = '{location}'
                    GROUP BY L.loc_id, L.loc_name, L.latitude, L.longitude, "Forecast time", "Weather", "Temperature", "Feels like","Precipitation", "Humidity",
                    "Precipitation probability", "Rainfall", "Snowfall", "Visibility", "Lightning potential", "Wind speed", "Cloud cover"
                    ORDER BY f.forecast_timestamp
                    """)

        rows = cur.fetchall()
        forecast_data = pd.DataFrame.from_dict(
            rows).drop_duplicates().groupby(['loc_id'])
        location_dupes = [data_frame for _, data_frame in forecast_data]
    return location_dupes[0].sort_values(['Forecast time'])


def get_location_forecast_week(_conn: connection, location: str) -> pd.DataFrame:
    """Returns forecast data for the upcoming week for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SET TIMEZONE TO 'Europe/London'")
        cur.execute(f"""SELECT L.loc_id, f.forecast_timestamp AS "Forecast time",
                    wc.description AS "Weather", f.temperature AS "Temperature", f.apparent_temp AS "Feels like",
                    f.precipitation_prob AS "Precipitation probability", f.rainfall AS "Rainfall",
                    f.precipitation AS "Precipitation", f.snowfall AS "Snowfall", f.visibility AS "Visibility",
                    f.humidity AS "Humidity", f.lightning_potential AS "Lightning potential", f.wind_speed AS "Wind speed",
                    f.cloud_cover AS "Cloud cover"
                    FROM location AS l
                    JOIN county AS c
                    ON (l.county_id=c.county_id)
                    JOIN country AS co
                    ON (c.country_id=co.country_id)
                    JOIN weather_report AS w
                    ON (l.loc_id=w.loc_id)
                    JOIN forecast AS f
                    ON (f.weather_report_id=w.weather_report_id)
                    JOIN weather_code AS wc
                    ON (F.weather_code_id=wc.weather_code_id)
                    WHERE F.forecast_timestamp > NOW()
                    AND l.loc_name = '{location}'
                    GROUP BY L.loc_id, "Forecast time", "Weather", "Temperature", "Feels like", "Precipitation", "Humidity",
                    "Precipitation probability", "Rainfall", "Snowfall", "Visibility", "Lightning potential", "Wind speed", "Cloud cover"
                    ORDER BY f.forecast_timestamp
                    """)

        rows = cur.fetchall()
        forecast_data = pd.DataFrame.from_dict(
            rows).drop_duplicates().sort_values(['loc_id']).groupby(['loc_id'])
        location_dupes = [data_frame for _, data_frame in forecast_data]

    return location_dupes[0].sort_values(['Forecast time'])


def get_air_quality(_conn: connection, location: str) -> pd.DataFrame:
    """Returns air quality data for the past day for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""SELECT aq.o3_concentration AS "O3 concentration",
                    aq.severity_level_id AS "Severity level", wr.report_time AS "Report time",
                    sl.severity_level AS "Severity"
                    FROM
                    air_quality AS aq
                    JOIN
                    weather_report AS wr
                    ON (aq.weather_report_id = wr.weather_report_id)
                    JOIN
                    severity_level AS sl
                    ON (sl.severity_level_id = aq.severity_level_id)
                    JOIN
                    location AS l
                    ON (l.loc_id = wr.loc_id)
                    WHERE l.loc_name = '{location}'
                    """)

        rows = cur.fetchall()
        air_q_data = pd.DataFrame.from_dict(rows)

    return air_q_data


def get_current_weather(_conn: connection, location: str) -> pd.DataFrame:
    """Extract analytics about current weather for a specific location"""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""SELECT f.forecast_timestamp AS "Forecast time", wc.description AS "Weather",
                    f.*
                    FROM location AS l
                    JOIN county AS c
                    ON (l.county_id=c.county_id)
                    JOIN country AS co
                    ON (c.country_id=co.country_id)
                    JOIN weather_report AS w
                    ON (l.loc_id=w.loc_id)
                    JOIN forecast AS f
                    ON (f.weather_report_id=w.weather_report_id)
                    JOIN weather_code AS wc
                    ON (f.weather_code_id=wc.weather_code_id)
                    WHERE F.forecast_timestamp = '{time_rounder(datetime.now())}'
                    AND l.loc_name = '{location}'
                    GROUP BY "Forecast time", l.loc_id, f.forecast_id, "Weather"
                    """)

        rows = cur.fetchall()
        weather_data = pd.DataFrame.from_dict(rows)

    return weather_data


def get_forecast_data(_conn: connection) -> pd.DataFrame:
    """Get basic current weather for all locations."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT l.latitude, l.longitude, l.loc_name AS "Location",
                    wc.description AS "Weather",
                    f.weather_code_id AS "Weather code"
                    FROM location AS l
                    JOIN county AS c
                    ON (l.county_id=c.county_id)
                    JOIN country AS co
                    ON (c.country_id=co.country_id)
                    JOIN weather_report AS w
                    ON (l.loc_id=w.loc_id)
                    JOIN forecast AS f
                    ON (f.weather_report_id=w.weather_report_id)
                    JOIN weather_code AS wc
                    ON (f.weather_code_id=wc.weather_code_id)
                    WHERE F.forecast_timestamp = '{time_rounder(datetime.now())}'
                    GROUP BY l.latitude, l.longitude, "Location", "Weather", f.forecast_timestamp, f.weather_code_id
                    ORDER BY f.forecast_timestamp DESC
                    """)

        rows = cur.fetchall()
        forecast_data = pd.DataFrame.from_dict(rows).drop_duplicates()
    forecast_data.loc[:, "icon_data"] = forecast_data.loc[:,
                                                          "Weather code"].apply(icon_data)
    return [d for _, d in forecast_data.groupby(['Weather code'])]


def get_map(loc_data: pd.DataFrame, lon: float, lat: float) -> pdk.Deck:
    """Generate a pydeck map, zoomed in on a specific location."""
    return pdk.Deck(
        map_style='dark',
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=12,
            pitch=30,
            max_zoom=12,
            min_zoom=10
        ),
        layers=[
            pdk.Layer(
                'IconLayer',
                data=data_frame,
                get_icon="icon_data",
                opacity=500,
                get_size=20,
                size_scale=2,
                get_position="[longitude, latitude]",
                get_text="location",
                pickable=True
            ) for data_frame in loc_data
        ],
        tooltip={'html': '<b>Weather:</b> {Weather}\
                 <b>Location:</b> {Location}',
                 'style': {"backgroundColor": "navyblue", 'color': '#87CEEB', 'font-size': '100%'}})


def make_compass(wind_direction: int) -> alt.LayerChart:
    """Create a compass display."""
    compass_star = """https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Compass_Rose_en_smal
l_N.svg/2835px-Compass_Rose_en_small_N.svg.png"""
    nautical_rose = """https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Compass_Rose-Black.
svg/2048px-Compass_Rose-Black.svg.png"""
    plot_points = {'x': [0], 'y': [0], 'img': [compass_star], 'rose': [nautical_rose],
                   'arr_x': [0.75*np.cos((wind_direction-90)/180*np.pi)],
                   'arr_y': [-0.75*np.sin((wind_direction-90)/180*np.pi)]}
    corners = {'c_x': [-1.2, 1.2, -1.2, 1.2], 'c_y': [-1.2, -1.2, 1.2, 1.2]}

    plots_df = pd.DataFrame(plot_points)
    corners_df = pd.DataFrame(corners)

    star = alt.Chart(plots_df).mark_image(width=230, height=230).encode(
        x=alt.X('x', axis=alt.Axis(ticks=False,
                                   domain=False, labels=False, title=None)),
        y=alt.Y('y', axis=alt.Axis(ticks=False,
                                   domain=False, labels=False, title=None)),
        url='img',
        tooltip=alt.value(None))
    nautical = alt.Chart(plots_df).mark_image(width=195, height=195).encode(
        x=alt.X('x', axis=alt.Axis(ticks=False,
                                   domain=False, labels=False, title=None)),
        y=alt.Y('y', axis=alt.Axis(ticks=False,
                                   domain=False, labels=False, title=None)),
        url='rose',
        tooltip=alt.value(None))

    points = alt.Chart(corners_df).mark_point(size=0).encode(
        x=alt.X('c_x', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        y=alt.Y('c_y', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        tooltip=alt.value(None)
    ).properties(
        width=260,
        height=260
    )
    dot = alt.Chart(plots_df).mark_point(size=700, color="gold", opacity=1).encode(
        x=alt.X('arr_x', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        y=alt.Y('arr_y', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        tooltip=alt.value(str(wind_direction) + "°"),
        strokeWidth=alt.value(10)).properties(
        width=260,
        height=260
    )
    dot_border = alt.Chart(plots_df).mark_point(size=750,
                                                color="black",
                                                align="center",
                                                baseline="middle",
                                                opacity=1).encode(
        x=alt.X('arr_x', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        y=alt.Y('arr_y', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        tooltip=alt.value(str(wind_direction) + "°"),
        strokeWidth=alt.value(16)).properties(
        width=260,
        height=260
    )

    circle = alt.Chart(plots_df).mark_arc(color="#ADD8E6").encode(
        theta=alt.value(20),
        radius=alt.value(118),
        x=alt.X('x', axis=alt.Axis(ticks=False,
                                   domain=False, labels=False, title=None)),
        y=alt.Y('y', axis=alt.Axis(ticks=False,
                                   domain=False, labels=False, title=None)),
        tooltip=alt.value(None)).properties(
        width=260,
        height=260
    )
    border = alt.Chart(plots_df).mark_arc(color="black").encode(
        theta=alt.value(20),
        radius=alt.value(122),
        x=alt.X('x', axis=alt.Axis(ticks=False,
                                   domain=False, labels=False, title=None)),
        y=alt.Y('y', axis=alt.Axis(ticks=False,
                                   domain=False, labels=False, title=None)),
        tooltip=alt.value(None)
    ).properties(
        width=260,
        height=260
    )

    compass = alt.layer(points, border, circle, nautical, star, dot_border, dot,
                        title=alt.Title(' ', fontSize=0.5)).configure_view(
        strokeWidth=0).configure_axis(grid=False).properties(
        width=260,
        height=260
    )
    return compass


def sort_data_by_time(data: pd.DataFrame, time_code: str) -> pd.DataFrame:
    """Group data by a particular time step."""
    data["Temperature"] = data[
        "Temperature"].resample(time_code).mean().round(1)
    data["Feels like"] = data[
        "Feels like"].resample(time_code).mean().round(1)
    data["Precipitation probability"] = data[
        "Temperature"].resample(time_code).mean().round()
    data["Cloud cover"] = data[
        "Temperature"].resample(time_code).mean().round()
    data["Snowfall"] = data[
        "Snowfall"].resample(time_code).sum()
    data["Lightning potential"] = data[
        "Lightning potential"].resample(time_code).sum().round(1)
    data["Humidity"] = data[
        "Humidity"].resample(time_code).mean().round()
    data = data.dropna(how="any")
    data = data.loc[:, (data != 0).any(axis=0)]
    data = data.reset_index(level=['Forecast time']).drop_duplicates()
    return data


def format_data_types(data: pd.DataFrame, time_format: str) -> pd.DataFrame:
    """Format data in a database to strings, displaying appropiate units."""
    data['Forecast time'] = data['Forecast time'].dt.strftime(
        time_format)
    data["Temperature"] = data["Temperature"].apply(
        lambda x: str(x) + '°C')
    data["Feels like"] = data["Feels like"].apply(
        lambda x: str(x) + '°C')
    if "Precipitation probability" in data.columns:
        data["Precipitation probability"] = data["Precipitation probability"].apply(
            lambda x: str(int(x)) + '%')
    if "Lightning potential" in data.columns:
        data["Lightning potential"] = data["Lightning potential"].apply(
            lambda x: str(x) + 'J/kg')
    if "Cloud cover" in data.columns:
        data["Cloud cover"] = data["Cloud cover"].apply(
            lambda x: str(int(x)) + '%')
    if "Rainfall" in data.columns:
        data["Rainfall"] = data["Rainfall"].apply(
            lambda x: str(x) + 'mm')
    if "Humidity" in data.columns:
        data["Humidity"] = data["Humidity"].apply(
            lambda x: str(int(x)) + '%')
    return data


def create_location_selection_box(_conn) -> str:
    """Create a selection box for all locations."""
    location_data = get_locations(_conn)
    locations = location_data['loc_name'].drop_duplicates(
    ).sort_values().to_list()
    location = st.selectbox('Locations',
                            ['Select a location...'] + locations)
    if location != 'Select a location...':
        location_data = location_data[location_data['loc_name'] == location]
        lat = location_data['latitude'].values[0]
        lon = location_data['longitude'].values[0]
    else:
        lat, lon = (0, 0)
    return location, lat, lon


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


def write_alerts(weather_alerts: pd.DataFrame, location: str) -> list[str]:
    """Create weather alert strings for various severities at a specfic location."""
    severes = []
    warnings = []
    alerts = []
    weather_alerts = weather_alerts.groupby(["Severity"])
    for _, w_alert_a in weather_alerts:
        severity = w_alert_a.loc[:, "Severity"].values[0]
        for _, w_alert in w_alert_a.sort_values(['min_time']).iterrows():
            first_line, alert_type, second_line = write_alert(
                w_alert, location)
            if severity == 'Severe Warning':
                severes.append('🚨 ' + first_line + 'Severe ' +
                               alert_type + ' Warning' + second_line)
            if severity == 'Warning':
                warnings.append('⚠️ ' + first_line +
                                alert_type + ' Warning' + second_line)
            if severity == 'Alert':
                alerts.append('❗ ' + first_line + alert_type +
                              ' Alert' + second_line)
    return severes, warnings, alerts


def get_current_metrics(current_weather: pd.DataFrame) -> None:
    """Display streamlit metrics for weather."""
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("Weather", current_weather['Weather'].values[0])
    with col2:
        st.metric("Temperature",
                  f"{current_weather['temperature'].values[0]}°C")
    with col3:
        st.metric("Feels like",
                  f"{current_weather['apparent_temp'].values[0]}°C")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("Cloud cover",
                  f"{current_weather['cloud_cover'].values[0]}%")
        st.metric("Precipitation probability",
                  f"{current_weather['precipitation_prob'].values[0]}%")
        st.metric("Wind speed",
                  f"{current_weather['wind_speed'].values[0]} km/h")
        st.metric("Wind gusts",
                  f"{current_weather['wind_gusts'].values[0]} km/h")
    with col2:
        st.write("Wind direction")

        st.altair_chart(
            make_compass(current_weather['wind_direction'].values[0]), theme=None)
        st.markdown("# ")


def write_table(data: pd.DataFrame) -> None:
    """Write and format a forecast table."""
    main_cols = [
        {'selector': 'th', 'props': 'background-color: #000042; color:  #ffffff'}]
    st.markdown(data.T.style.hide(axis="columns").map(
        lambda x: "background-color:#000042;color:#ffffff"
        if isinstance(x, str) and (':' in x or ('/' in x and len(x) == 5))
        else "background-color:#82a6f4").set_table_styles(main_cols, axis=1).to_html(),
        unsafe_allow_html=True)


def create_precipitation_graph(data: pd.DataFrame) -> None:
    """Create and display in streamlit an altair chart regarding rainfall and precipitation."""
    prec_col, rain_col = st.columns(2)
    with prec_col:
        precipitation_graph = alt.Chart(data).mark_area(color="navyblue").encode(
            x=alt.X('Forecast time:T', axis=alt.Axis(
                grid=True)).scale(zero=False).title('Time'),
            y=alt.Y("Precipitation:Q", axis=alt.Axis(grid=True)).scale(
                zero=False).title("Precipitation (mm)")
        )
        precipitation_prob_graph = alt.Chart(data).mark_line(color="gold").encode(
            x=alt.X('Forecast time:T').scale(zero=False).title('Time'),
            y=alt.Y("Precipitation probability:Q", axis=alt.Axis(grid=True)).scale(
                zero=False).title("Precipitation probability (%)")
        )
        prec_graph = alt.layer(
            precipitation_graph, precipitation_prob_graph).resolve_scale(y="independent")
        st.altair_chart(prec_graph.configure_axisLeft(
            labelColor='black',
            titleColor='black'
        ).configure_axisRight(
            labelColor='black',
            titleColor='black'
        ).configure_axisBottom(
            labelColor='black',
            titleColor='black'
        ), use_container_width=True)
    with rain_col:
        rainfall_graph = alt.Chart(data).mark_area(color="blue").encode(
            x=alt.X('Forecast time:T', axis=alt.Axis(
                grid=True)).scale(zero=False).title('Time'),
            y=alt.Y("Rainfall:Q", axis=alt.Axis(grid=True)).scale(
                zero=False).title("Rainfall (mm)")
        )
        st.altair_chart(rainfall_graph.configure_axisLeft(
            labelColor='black',
            titleColor='black'
        ).configure_axisBottom(
            labelColor='black',
            titleColor='black'
        ), use_container_width=True)


def create_air_quality_graph(location: str) -> alt.LayerChart:
    """Create a graph displaying air quality, with lines to mark air quality thresholds."""
    air_quality = get_air_quality(conn, location)
    air_quality["Report time"] = air_quality["Report time"].apply(
        time_rounder)
    air_quality["level1"] = air_quality["Report time"].apply(
        lambda x: 160)
    air_quality["level2"] = air_quality["Report time"].apply(
        lambda x: 140)
    air_quality["level3"] = air_quality["Report time"].apply(
        lambda x: 100)
    air_base = alt.Chart(air_quality).encode(
        x=alt.X("Report time:T", axis=alt.Axis(grid=True)))
    aq_chart = air_base.mark_line(color="black").encode(
        y=alt.Y("O3 concentration", axis=alt.Axis(
            grid=True)).scale(zero=False),
        tooltip=["Report time", "O3 concentration"]
    )
    aq_chart1 = air_base.mark_line(color="red").encode(
        y=alt.Y("level1").title("O3 concentration")
    )
    aq_chart2 = air_base.mark_line(color="gold").encode(
        y=alt.Y("level2").title("O3 concentration")
    )
    aq_chart3 = air_base.mark_line(color="green").encode(
        y=alt.Y("level3").title("O3 concentration")
    )
    return alt.layer(aq_chart + aq_chart1 + aq_chart2 +
                     aq_chart3)


def create_temperature_graph(data: pd.DataFrame) -> alt.Chart:
    """Create a graph for displaying temperature and apparent temperature."""
    return alt.Chart(data).mark_line().transform_fold(
        fold=['Temperature', 'Feels like'],
        as_=['variable', 'value']
    ).encode(
        x=alt.X('Forecast time:T', axis=alt.Axis(
            grid=True)).scale(zero=False).title('Time'),
        y=alt.Y('max(value):Q', axis=alt.Axis(grid=True)).scale(
            zero=False).title('Temperature (°C)'),
        color=alt.Color('variable:N').title("Temperature type")
    ).configure_range(
        category={'scheme': 'category10'}
    )


def create_weather_graph(data: pd.DataFrame, variable: str, title: str, colour: str) -> alt.Chart:
    """Create an altair line graph for various weather or airquality."""
    return alt.Chart(data).mark_line(color=colour).encode(
        x=alt.X('Forecast time:T', axis=alt.Axis(
            grid=True)).scale(zero=False).title('Time'),
        y=alt.Y(f"{variable}:Q", axis=alt.Axis(grid=True)).scale(
            zero=False).title(title)
    )


def create_not_precipitation_graph(graph_type_day: str, forecast_d_loc: pd.DataFrame,
                                   location: str) -> None:
    """Create and format a graph displaying weather or air quality."""
    if graph_type_day == "Air quality":
        weather_today_graph = create_air_quality_graph(location)
    elif graph_type_day == "Temperature":
        weather_today_graph = create_temperature_graph(forecast_d_loc)
    elif graph_type_day == "Cloud cover":
        weather_today_graph = create_weather_graph(
            forecast_d_loc, "Cloud cover", "Cloud cover (%)", "blue")
    elif graph_type_day == "Snowfall":
        weather_today_graph = create_weather_graph(
            forecast_d_loc, "Snowfall", "Snowfall (cm)", "red")
    elif graph_type_day == "Lightning":
        weather_today_graph = create_weather_graph(
            forecast_d_loc, "Lightning potential", "Lightning potential (J/kg)", "gold")
    elif graph_type_day == "Visibility":
        weather_today_graph = create_weather_graph(
            forecast_d_loc, "Visibility", "Visibility (m)", "green")
    elif graph_type_day == "Humidity":
        weather_today_graph = create_weather_graph(
            forecast_d_loc, "Humidity", "Humidity (%)", "orange")
    st.altair_chart(weather_today_graph.configure_legend(
        labelColor='black',
        titleColor='black'
    ).configure_axisLeft(
        labelColor='black',
        titleColor='black'
    ).configure_axisBottom(
        labelColor='black',
        titleColor='black'
    ), use_container_width=True)


def today_forecast(_conn: connection, location: str) -> None:
    """Get the forecast for the upcoming day and display tables and graphs."""
    forecast_d_loc = get_location_forecast_day(_conn, location)

    forecast_hourly = forecast_d_loc[[
        "Forecast time", "Weather", "Temperature", "Feels like", "Humidity",
        "Precipitation probability", "Rainfall", "Snowfall", "Lightning potential",
        "Cloud cover"]].copy().set_index("Forecast time")
    forecast_hourly = sort_data_by_time(forecast_hourly, 'h')
    forecast_hourly = format_data_types(forecast_hourly, '%H:%M')
    write_table(forecast_hourly)

    graph_type_day = st.selectbox('Daily data', [
        "Temperature", "Visibility", "Air quality", "Precipitation", "Snowfall", "Lightning",
        "Cloud cover", "Humidity",])
    if graph_type_day == "Precipitation":
        create_precipitation_graph(forecast_d_loc)
    else:
        create_not_precipitation_graph(
            graph_type_day, forecast_d_loc, location)


def week_forecast(_conn: connection, location: str) -> None:
    """Get the forecast for the upcoming week and display tables and graphs."""
    forecast_week_fix = get_location_forecast_week(_conn, location)
    forecast_week = forecast_week_fix[[
        "Forecast time", "Weather", "Temperature", "Feels like", "Humidity",
        "Precipitation probability", "Snowfall", "Lightning potential",
        "Cloud cover"]].copy().set_index("Forecast time")
    forecast_week = sort_data_by_time(forecast_week, 'd')
    forecast_week = format_data_types(forecast_week, '%d/%m')

    write_table(forecast_week)
    st.markdown('#')

    graph_type_week = st.selectbox('Weekly data', [
        "Temperature", "Visibility", "Air quality", "Precipitation", "Snowfall", "Lightning",
        "Cloud cover", "Humidity",])

    if graph_type_week == "Precipitation":
        create_precipitation_graph(forecast_week_fix)
    else:
        create_not_precipitation_graph(
            graph_type_week, forecast_week_fix, location)


def format_time_list(times: list[pd.Timestamp]):
    """Write out times and time ranges formatted for markdown."""
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
    """Create warnings for flood alerts."""
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
                    f'**{county}** had a **Severe Flood Warning** raised {date_val} at {times}.',
                    "🚨"))
            elif severity == "Warning":
                errors.append((
                    f'**{county}** had a **Flood Warning** raised {date_val} at {times}.',
                    "⚠️"))

            elif severity == "Alert":
                warnings.append((
                    f'**{county}** had a **Flood Alert** raised {date_val} at {times}.',
                    "❕"))
    return errors, warnings


if __name__ == "__main__":
    load_dotenv()
    st.set_page_config(layout="wide")
    st.title('Quick Search')
    conn = connect_to_db(dict(ENV))
    loc, latitude, longitude = create_location_selection_box(conn)
    if loc != 'Select a location...':
        # floods = get_flood_alerts(conn, loc)
        alerts_data = pd.concat([get_air_quality_alerts(conn, loc),
                                 get_weather_alerts(conn, loc)])
        if not alerts_data.empty:
            w_severes, w_warnings, w_alerts = write_alerts(alerts_data, loc)
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

        st.markdown("# Current weather")
        current_weather_data = get_current_weather(conn, loc)
        get_current_metrics(current_weather_data)

        st.markdown("## Today's forecast")
        today_forecast(conn, loc)

        st.markdown("## This week's forecast")
        week_forecast(conn, loc)

        st.pydeck_chart(get_map(get_forecast_data(conn), longitude, latitude))
    else:
        st.write('Please pick a location!')
