from datetime import datetime
from os import environ as ENV

import altair as alt
import pandas as pd
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import streamlit as st
import pydeck as pdk
from streamlit_extras.chart_container import chart_container

SUN_URL = "https://commons.wikimedia.org/wiki/Category:Sun_icons#/media/File:Draw_sunny.png"
SUN_CLOUD_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/Antu_com.librehat.yahooweather.svg/2048px-Antu_com.librehat.yahooweather.svg.png"
CLOUD_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Antu_weather-many-clouds.svg/768px-Antu_weather-many-clouds.svg.png"
FOG_URL = "https://commons.wikimedia.org/wiki/Category:Fog_icons#/media/File:Breeze-weather-mist-48.svg.png"
DRIZZLE_URL = "https://commons.wikimedia.org/wiki/Category:Rain_icons#/media/File:Faenza-weather-showers-scattered-symbolic.svg.png"
RAIN_URL = "https://commons.wikimedia.org/wiki/Category:Rain_icons#/media/File:Faenza-weather-showers-symbolic.svg.png"
FREEZE_RAIN_URL = "https://commons.wikimedia.org/wiki/Category:Rain_icons#/media/File:Antu_weather-freezing-rain.svg.png"
SNOW_URL = "https://commons.wikimedia.org/wiki/File:Antu_weather-snow-scattered.svg#/media/File:Antu_weather-snow-scattered.svg.png"
THUNDER_URL = "https://commons.wikimedia.org/wiki/Category:SVG_cloud_icons#/media/File:Antu_weather-storm-day.svg.png"


def icon_data(weather_code):
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
def connect_to_db(config):
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
        return (timestamp.replace(second=0, microsecond=0, minute=(timestamp.minute // 15 * 15)))
    return (timestamp.replace(second=0, microsecond=0, minute=0))


def get_locations(_conn):
    """Get a list of all locations that are associated with forecast data."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""SELECT L.loc_name as "Location", C.name as "County", CO.name as "Country"
                    FROM location AS L
                    JOIN county AS C
                    ON (C.county_id = L.county_id)
                    JOIN country AS CO
                    ON (CO.country_id = C.country_id)
                    WHERE L.loc_id IN
                    (SELECT loc_id FROM weather_report)""")
        locations = cur.fetchall()
    return locations


def get_forecast_data(_conn) -> pd.DataFrame:
    """Get basic current weather for all locations."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT l.latitude, l.longitude, l.loc_name as "Location", C.name as "County", CO.name as "Country",wc.description as "Weather",
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
                    GROUP BY l.latitude, l.longitude, "Location", "County", "Country", "Weather", f.forecast_timestamp, f.weather_code_id
                    ORDER BY f.forecast_timestamp DESC
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows).drop_duplicates()
    data_f["icon_data"] = data_f["Weather code"].apply(icon_data)
    return [d for _, d in data_f.groupby(['Weather code'])]


def get_location_data(_conn, location, location_type) -> pd.DataFrame:
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
                    GROUP BY l.latitude, l.longitude, "Weather", f.forecast_timestamp, f.weather_code_id
                    ORDER BY f.forecast_timestamp DESC
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows).drop_duplicates()
    return data_f


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
    data_f["icon_data"] = None

    for i in data_f.index:
        data_f["icon_data"][i] = icon_data
    return data_f


def get_map(loc_data, lat, lon, location_type):
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
        zoom = 5.2
        get_size = 30
    st.pydeck_chart(pdk.Deck(
        map_style='dark',
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=zoom,
            pitch=30,
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
                 'style': {"backgroundColor": "navyblue", 'color': '#87CEEB', 'font-size': '100%'}}))


if __name__ == "__main__":
    load_dotenv()
    st.title('Explore')
    conn = connect_to_db(dict(ENV))
    forecast_d = get_forecast_data(conn)
    with st.sidebar:
        by_loc = st.checkbox("Search by location")
        if by_loc:
            loc_type = st.selectbox('Search by:',
                                    ['Location', 'County', 'Country'])
            locations = get_locations(conn)

            if loc_type == 'Location':
                location = st.selectbox('Locations',
                                        {l['Location'] for l in locations})
            elif loc_type == 'County':
                location = st.selectbox('Counties',
                                        {l['County'] for l in locations})
            elif loc_type == 'Country':
                location = st.selectbox('Locations',
                                        {l['Country'] for l in locations})

    if by_loc:
        forecast_loc = get_location_data(conn, location, loc_type)
        lat, lon = forecast_loc[['latitude', 'longitude']].values[0]
        print(lat, lon)
        w_map = get_map(forecast_d, lat, lon, loc_type)
    else:
        alerts = get_locations_with_alerts(conn)
        print(alerts)
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
        w_map = get_map(forecast_d, 52.536, -2.5341, 'UK')
        with chart_container(forecast_d):

            st.write("Here's a cool chart")
            forecast_d["Forecast time"] = pd.to_datetime(
                forecast_d['Forecast time'])
            graph_hourly = forecast_d.sort_values(by='Forecast time')
            st.area_chart(
                graph_hourly[["Temperature", "Feels like"]])
