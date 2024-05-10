"""A streamlit page allowing the user to explore the climate across the whole of the UK."""

from datetime import datetime
from os import environ as ENV

import altair as alt
import pandas as pd
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection
from dotenv import load_dotenv
import streamlit as st
import pydeck as pdk

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
        return (timestamp.replace(second=0, microsecond=0, minute=timestamp.minute // 15 * 15))
    return timestamp.replace(second=0, microsecond=0, minute=0)


def get_locations(_conn: connection) -> list[str]:
    """Get a list of all locations that are associated with forecast data."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SELECT L.loc_name as "Location", C.name as "County", CO.name as "Country"
                    FROM location AS L
                    JOIN county AS C
                    ON (C.county_id = L.county_id)
                    JOIN country AS CO
                    ON (CO.country_id = C.country_id)
                    WHERE L.loc_id IN
                    (SELECT loc_id FROM weather_report)""")
        locations = cur.fetchall()
    return locations


def get_forecast_data(_conn: connection) -> list[pd.DataFrame]:
    """Get basic current weather for all locations."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT l.latitude, l.longitude, l.loc_name as "Location",
                    C.name as "County", CO.name as "Country",wc.description as "Weather",
                    f.weather_code_id AS "Weather code"
                    FROM location AS l
                    JOIN county as c
                    ON (l.county_id=c.county_id)
                    JOIN country as co
                    ON (c.country_id=co.country_id)
                    JOIN weather_report as w
                    ON (l.loc_id=w.loc_id)
                    JOIN forecast as f
                    ON (f.weather_report_id=w.weather_report_id)
                    JOIN weather_code as wc
                    ON (f.weather_code_id=wc.weather_code_id)
                    WHERE F.forecast_timestamp = '{time_rounder(datetime.now())}'
                    GROUP BY l.latitude, l.longitude, "Location", "County", "Country", "Weather",
                    f.forecast_timestamp, f.weather_code_id
                    ORDER BY f.forecast_timestamp DESC
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows).drop_duplicates()
    data_f.loc[:, "icon_data"] = data_f.loc[:, "Weather code"].apply(icon_data)
    return [d for _, d in data_f.groupby(['Weather code'])]


def get_location_data(_conn: connection, location: str, location_type: str) -> pd.DataFrame:
    """Get basic current weather for all locations."""
    if location_type == "Country":
        where = f"CO.name = '{location}'"
    elif location_type == "County":
        where = f"C.name = '{location}'"
    elif location_type == "Location":
        where = f"L.loc_name = '{location}'"
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT l.latitude, l.longitude, wc.description as "Weather",
                    f.weather_code_id AS "Weather code"
                    FROM location AS l
                    JOIN county as c
                    ON (l.county_id=c.county_id)
                    JOIN country as co
                    ON (c.country_id=co.country_id)
                    JOIN weather_report as w
                    ON (l.loc_id=w.loc_id)
                    JOIN forecast as f
                    ON (f.weather_report_id=w.weather_report_id)
                    JOIN weather_code as wc
                    ON (f.weather_code_id=wc.weather_code_id)
                    WHERE f.forecast_timestamp < NOW()
                    AND f.forecast_timestamp > NOW() - interval '15 minutes'
                    AND {where}
                    GROUP BY l.latitude, l.longitude, "Weather", f.forecast_timestamp,
                    f.weather_code_id
                    ORDER BY f.forecast_timestamp DESC
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows).drop_duplicates()
    return data_f


def get_current_weather_metric_loc(_conn: connection, variable: str, metric: str) -> pd.DataFrame:
    """Extract analytics about current weather for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""SELECT l.loc_name as "Location", f.{variable}
                    FROM location AS l
                    JOIN weather_report as w
                    ON (l.loc_id=w.loc_id)
                    JOIN forecast as f
                    ON (f.weather_report_id=w.weather_report_id)
                    WHERE F.forecast_timestamp = '{time_rounder(datetime.now())}'
                    AND f.{variable} IN (
                    SELECT {metric}(f.{variable}) from forecast as f
                    WHERE F.forecast_timestamp = '{time_rounder(datetime.now())}'
                    )
                    GROUP BY F.forecast_timestamp, l.loc_id, f.forecast_id
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)
    return data_f


def get_air_qualities(_conn: connection):
    """Get air quality for top 5 locations."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SELECT AQ.o3_concentration AS "O3 concentration", WR.report_time AS "Report time",
                    L.loc_name AS "Location", L.loc_id, AQ.severity_level_id AS "Severity"
                    FROM air_quality AS AQ
                    JOIN weather_report as WR
                    ON (AQ.weather_report_id = WR.weather_report_id)
                    JOIN location AS L ON (WR.loc_id = L.loc_id)
                    WHERE L.loc_id < 11
                    AND WR.report_time > NOW() - interval '1 day'
                    GROUP BY WR.report_time, AQ.o3_concentration, L.loc_name, L.loc_id, AQ.severity_level_id
                    ORDER BY report_time""")
        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)
        data_f.loc[:, 'Report time'] = data_f.loc[:,
                                                  'Report time'].apply(time_rounder)
        data_f = data_f.groupby(['Location'])
        locations = pd.DataFrame()
        for _, data_frame in data_f:
            loc_dup_group = data_frame.sort_values(
                ['loc_id']).groupby(['loc_id'])
            locations = pd.concat([locations,
                                   [data_frame for _, data_frame in loc_dup_group][0].drop_duplicates()])
    return locations


def get_map(loc_data: pd.DataFrame, lat: float, lon: float, location_type: str) -> pdk.Deck:
    """Create a pydeck map, optionally zoomed into particular locations."""
    if location_type == 'Location':
        zoom = 11
        get_size = 30
    elif location_type == 'County':
        zoom = 10
        get_size = 35
    elif location_type == 'Country':
        zoom = 6.5
        get_size = 30
    elif location_type == 'UK':
        zoom = 4.3
        get_size = 20
    return pdk.Deck(
        map_style='dark',
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=zoom,
            pitch=30,
            max_zoom=zoom + 10,
            min_zoom=zoom
        ),
        layers=[
            pdk.Layer(
                'IconLayer',
                data=df,
                get_icon="icon_data",
                opacity=500,
                get_size=get_size,
                size_scale=1,
                get_position="[longitude, latitude]",
                get_text="location",
                pickable=True
            ) for df in loc_data
        ],
        tooltip={'html': '<b>Weather:</b> {Weather}\
                 <b>Location:</b> {Location}',
                 'style': {"backgroundColor": "navyblue", 'color': '#87CEEB', 'font-size': '100%'}})


def write_floods(floods: pd.DataFrame) -> None:
    """Write streamlit warnings for flood alerts."""
    for _, flood in floods.iterrows():
        if flood["Severity"] == "Alert":
            icon = "❕"
        elif flood["Severity"] == "Warning":
            icon = "⚠️"
        elif flood["Severity"] == "Severe Warning":
            icon = "🚨"
        st.warning(
            f'**{flood["County"]}** had a **Flood {flood["Severity"]}** raised at \
                **{flood["Time raised"]}**.', icon=icon)


def get_global_metric(_conn: connection, variable: str, metric: str,
                      title: str, unit: str) -> st.metric:
    """Get a streamlit metric as a location for a particular weather condition."""
    if metric in {'Most', 'Highest'}:
        info = get_current_weather_metric_loc(_conn, variable, 'max')
        location = info['Location'].values[0]
        if variable == 'precipitation_prob' and info[variable].values[0] == 0:
            variable = 'uv_index'
            metric = 'Highest'
            title = ' UV-index '
            unit = ''
            info = get_current_weather_metric_loc(_conn, variable, 'max')
            location = info['Location'].values[0]
            value = str(info[variable].values[0])
    elif metric in {'Least', 'Lowest'}:
        info = get_current_weather_metric_loc(_conn, variable, 'min')
        location = info['Location'].values[0]
    value = str(info[variable].values[0]) + ' ' + unit
    return st.metric(f'{metric} {title}', f'{location}: {value}')


def top_five_air_quality():
    pass


def bottom_five_air_quality():
    pass


if __name__ == "__main__":
    load_dotenv()
    st.title('Explore')
    conn = connect_to_db(dict(ENV))
    forecast_d = get_forecast_data(conn)
    st.markdown('## Map')
    st.pydeck_chart(get_map(forecast_d, 54.536, -2.5341, 'UK'))
    st.markdown('## Metrics')
    st.markdown("""
                    <style>
                    [data-testid="stMetricValue"] {
                        font-size: 20px;
                    }
                    </style>
                    """,
                unsafe_allow_html=True,
                )

    col1, col2, col3 = st.columns(3)
    with col1:
        get_global_metric(conn, 'temperature',
                          'Highest', 'temperature', '°C')
        get_global_metric(conn, 'cloud_cover', 'Least', 'cloud cover', '%')
    with col2:
        get_global_metric(conn, 'temperature',
                          'Lowest', 'temperature', '°C')
        get_global_metric(conn, 'humidity', 'Most', 'humidity', '%')
    with col3:
        get_global_metric(conn, 'wind_speed',
                          'Highest', 'wind speeds', 'km/h')
        get_global_metric(conn, 'precipitation_prob',
                          'Most', 'chance of rain', '%')

    st.markdown('## Air quality')
    st.altair_chart(alt.Chart(get_air_qualities(conn)).mark_line().encode(
        x=alt.X('Report time:T'),
        y=alt.Y('O3 concentration:Q').scale(zero=False),
        color='Location',
        tooltip=['O3 concentration', 'Severity', 'Location']
    ), use_container_width=True)
