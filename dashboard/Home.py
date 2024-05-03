"""Generate and display forecast data for a specific location."""

from datetime import datetime
from os import environ as ENV

import altair as alt
import pandas as pd
import numpy as np
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import streamlit as st
import pydeck as pdk

SUN_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Weather-clear.svg/2048px-Weather-clear.svg.png"
SUN_CLOUD_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/Antu_com.librehat.yahooweather.svg/2048px-Antu_com.librehat.yahooweather.svg.png"
CLOUD_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Antu_weather-many-clouds.svg/768px-Antu_weather-many-clouds.svg.png"
FOG_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Breeze-weather-mist-48.svg/2048px-Breeze-weather-mist-48.svg.png"
DRIZZLE_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Faenza-weather-showers-scattered-symbolic.svg/2048px-Faenza-weather-showers-scattered-symbolic.svg.png"
RAIN_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Breeze-weather-showers-scattered-48.svg/2048px-Breeze-weather-showers-scattered-48.svg.png"
FREEZE_RAIN_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Antu_weather-freezing-rain.svg/2048px-Antu_weather-freezing-rain.svg.png"
SNOW_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Antu_weather-snow-scattered.svg/2048px-Antu_weather-snow-scattered.svg.png"
THUNDER_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Antu_weather-storm-day.svg/2048px-Antu_weather-storm-day.svg.png"


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
        cur.execute(f"""SELECT loc_name, latitude, longitude
                    FROM location
                    WHERE loc_id IN
                    (SELECT loc_id FROM weather_report)""")
        locations = cur.fetchall()
    return pd.DataFrame(locations)


def get_weather_alerts(_conn, location):
    """Get all weather alerts for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT AL.name as "Alert type", SL.severity_level as "Severity",
                    MIN(F.forecast_timestamp) as min_time, MAX(F.forecast_timestamp) as max_time
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
        data_f = pd.DataFrame(rows).drop_duplicates()
    return data_f


def get_flood_alerts(_conn, location):
    """Get all flood alerts for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT SL.severity_level AS "Severity", C.name AS "County", FW.time_raised AS "Time raised"
                        FROM flood_warnings AS FW
                        JOIN severity_level AS SL ON (FW.severity_level_id = SL.severity_level_id)
                        JOIN location AS L ON (FW.loc_id = L.loc_id)
                        JOIN county AS C ON (L.county_id = C.county_id)
                        WHERE L.loc_name = '{location}'
                        AND SL.severity_level_id < 4
                        AND FW.time_raised > NOW() - interval '12 hours'
                        ORDER BY SL.severity_level_id ASC""")

        rows = cur.fetchall()
        data_f = pd.DataFrame(rows).drop_duplicates()
    return data_f


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


def get_location_forecast_day(_conn, location) -> pd.DataFrame:
    """Returns forecast data for the upcoming day for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SET TIMEZONE TO 'Europe/London'")
        cur.execute(f"""SELECT L.loc_id, L.latitude, L.longitude, f.forecast_timestamp as "Forecast time", wc.description as "Weather", f.temperature as "Temperature",
                    f.apparent_temp as "Feels like", f.precipitation_prob as "Precipitation probability", f.rainfall as "Rainfall",
                    f.precipitation as "Precipitation", f.snowfall as "Snowfall", f.visibility as "Visibility", f.humidity as "Humidity",
                    f.lightning_potential as "Lightning potential", f.wind_speed as "Wind speed", f.cloud_cover as "Cloud cover"
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
                    ON (F.weather_code_id=wc.weather_code_id)
                    WHERE F.forecast_timestamp < NOW() + interval '8 hours'
                    AND F.forecast_timestamp > NOW() - interval '15 minutes'
                    AND L.loc_name = '{location}'
                    GROUP BY L.loc_id, L.latitude, L.longitude, "Forecast time", "Weather", "Temperature", "Feels like","Precipitation", "Humidity",
                    "Precipitation probability", "Rainfall", "Snowfall", "Visibility", "Lightning potential", "Wind speed", "Cloud cover"
                    ORDER BY f.forecast_timestamp
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows).drop_duplicates().sort_values(['loc_id']).groupby([
            'loc_id'])
        location_dupes = [df for _, df in data_f]
    return location_dupes[0].sort_values(['Forecast time'])


def get_location_forecast_week(_conn, location) -> pd.DataFrame:
    """Returns forecast data for the upcoming week for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SET TIMEZONE TO 'Europe/London'")
        cur.execute(f"""SELECT L.loc_id, f.forecast_timestamp as "Forecast time", wc.description as "Weather", f.temperature as "Temperature",
                    f.apparent_temp as "Feels like", f.precipitation_prob as "Precipitation probability", f.rainfall as "Rainfall",
                    f.precipitation as "Precipitation", f.snowfall as "Snowfall", f.visibility as "Visibility", f.humidity as "Humidity",
                    f.lightning_potential as "Lightning potential", f.wind_speed as "Wind speed", f.cloud_cover as "Cloud cover"
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
                    ON (F.weather_code_id=wc.weather_code_id)
                    WHERE F.forecast_timestamp > NOW()
                    AND l.loc_name = '{location}'
                    GROUP BY L.loc_id, "Forecast time", "Weather", "Temperature", "Feels like", "Precipitation", "Humidity",
                    "Precipitation probability", "Rainfall", "Snowfall", "Visibility", "Lightning potential", "Wind speed", "Cloud cover"
                    ORDER BY f.forecast_timestamp
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)
        data_f = pd.DataFrame.from_dict(rows).drop_duplicates().sort_values(['loc_id']).groupby([
            'loc_id'])
        location_dupes = [df for _, df in data_f]

    return location_dupes[0].sort_values(['Forecast time'])


def get_air_quality(_conn, location) -> pd.DataFrame:
    """Returns air quality data for the past day for a specific location."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""SELECT aq.o3_concentration AS "O3 concentration", aq.severity_level_id AS "Severity level",
                    wr.report_time AS "Report time", sl.severity_level AS "Severity"
                    FROM
                    air_quality AS aq
                    JOIN
                    weather_report AS wr
                    ON (aq.weather_report_id = wr.weather_report_id)
                    JOIN
                    severity_level as sl
                    ON (sl.severity_level_id = aq.severity_level_id)
                    JOIN
                    location AS l
                    ON (l.loc_id = wr.loc_id)
                    WHERE l.loc_name = '{location}'
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


def get_current_weather(_conn, location) -> pd.DataFrame:
    """Extract analytics about current weather for a specific location"""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""SELECT f.forecast_timestamp as "Forecast time", wc.description as "Weather", f.*
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
                    AND l.loc_name = '{location}'
                    GROUP BY "Forecast time", l.loc_id, f.forecast_id, "Weather"
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


def get_forecast_data(_conn) -> pd.DataFrame:
    """Get basic current weather for all locations."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT l.latitude, l.longitude, l.loc_name as "Location", wc.description as "Weather",
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
                    GROUP BY l.latitude, l.longitude, "Location", "Weather", f.forecast_timestamp, f.weather_code_id
                    ORDER BY f.forecast_timestamp DESC
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows).drop_duplicates()
    data_f["icon_data"] = data_f["Weather code"].apply(icon_data)
    return [d for _, d in data_f.groupby(['Weather code'])]


def get_map(loc_data, lon, lat):
    """Generate a pydeck map, zoomed in on a specific location."""
    print(loc_data)
    st.pydeck_chart(pdk.Deck(
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
                data=df,
                get_icon="icon_data",
                opacity=500,
                get_size=20,
                size_scale=2,
                get_position="[longitude, latitude]",
                get_text="location",
                pickable=True
            ) for df in loc_data
        ],
        tooltip={'html': '<b>Weather:</b> {Weather}\
                 <b>Location:</b> {Location}',
                 'style': {"backgroundColor": "navyblue", 'color': '#87CEEB', 'font-size': '100%'}}))


def compass(wind_direction):
    """Create a compass display."""
    compass_star = "https://upload.wikimedia.org/wikipedia/commons/b/bb/Windrose.svg"
    a = {'x': [0], 'y': [0], 'img': [compass_star],
         'arr_x': [0.75*np.cos((wind_direction-90)/180*np.pi)], 'arr_y': [-0.75*np.sin((wind_direction-90)/180*np.pi)]}
    c = {'c_x': [-1.2, 1.2, -1.2, 1.2], 'c_y': [-1.2, -1.2, 1.2, 1.2]}
    df = pd.DataFrame(a)
    corners = pd.DataFrame(c)

    star = alt.Chart(df).mark_image(width=200, height=200).encode(
        x=alt.X('x', axis=alt.Axis(ticks=False,
                                   domain=False, labels=False, title=None)),
        y=alt.Y('y', axis=alt.Axis(ticks=False,
                                   domain=False, labels=False, title=None)),
        url='img',
        tooltip=alt.value(None))

    points = alt.Chart(corners).mark_point(size=0).encode(
        x=alt.X('c_x', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        y=alt.Y('c_y', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        tooltip=alt.value(None)
    ).properties(
        width=260,
        height=260
    )
    dot = alt.Chart(df).mark_point(size=700, color="gold", opacity=1).encode(
        x=alt.X('arr_x', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        y=alt.Y('arr_y', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        tooltip=alt.value(str(wind_direction) + "°"),
        strokeWidth=alt.value(10)).properties(
        width=260,
        height=260
    )
    dot_border = alt.Chart(df).mark_point(size=750, color="black", align="center", baseline="middle", opacity=1).encode(
        x=alt.X('arr_x', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        y=alt.Y('arr_y', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        tooltip=alt.value(str(wind_direction) + "°"),
        strokeWidth=alt.value(16)).properties(
        width=260,
        height=260
    )

    circle = alt.Chart(df).mark_arc(color="#ADD8E6").encode(
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
    border = alt.Chart(df).mark_arc(color="black").encode(
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

    compass = alt.layer(points, border, circle, star, dot_border, dot, title=alt.Title(' ', fontSize=0.5)).configure_view(
        strokeWidth=0).configure_axis(grid=False).properties(
        width=260,
        height=260
    )
    return compass


def sort_data_by_time(data, time_code):
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
    data = data.dropna(how="any")  # drop nans
    data = data.loc[:, (data != 0).any(axis=0)]  # drop columns with zeros
    data = data.reset_index(level=['Forecast time']).drop_duplicates()
    return data


def format_data_types(data, time_format):
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
    locations = location_data['loc_name'].to_list()
    location = st.selectbox('Locations',
                            ['Select a location...'] + locations)
    if location != 'Select a location...':
        location_data = location_data[location_data['loc_name'] == location]
        lat = location_data['latitude'].values[0]
        lon = location_data['longitude'].values[0]
    else:
        lat, lon = (0, 0)
    return location, lat, lon


def write_alerts(alerts, location):
    """Write streamlit warnings for weather alerts."""
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
                f'**{location}** {key_words} **{alert["Alert type"]} {alert["Severity"]}** from **{alert["min_time"]}** to **{alert["max_time"]}**.', icon=icon)
        else:
            st.warning(
                f'**{location}** {key_words} **{alert["Alert type"]} {alert["Severity"]}** at **{alert["min_time"]}**.', icon=icon)


def write_floods(floods):
    """Write streamlit warnings for flood alerts."""
    for _, flood in floods.iterrows():
        if flood["Severity"] == "Alert":
            icon = "❕"
        elif flood["Severity"] == "Warning":
            icon = "⚠️"
        elif flood["Severity"] == "Severe Warning":
            icon = "🚨"
        st.warning(
            f'**{flood["County"]}** had a **Flood {flood["Severity"]}** raised at **{flood["Time raised"]}**.', icon=icon)


def get_current_metrics(current_weather):
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
            compass(current_weather['wind_direction'].values[0]), theme=None)
        st.markdown("# ")


def write_table(data):
    """Write and format a forecast table."""
    main_cols = [
        {'selector': 'th', 'props': 'background-color: #000042; color:  #ffffff'}]
    st.markdown(data.T.style.hide(axis="columns").map(lambda x: "background-color:#000042;color:#ffffff" if isinstance(x, str) and (':' in x or ('/' in x and len(x) == 5)) else "background-color:#82a6f4").set_table_styles(main_cols, axis=1).to_html(),
                unsafe_allow_html=True)


def create_precipitation_graph(data):
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


def create_air_quality_graph(location) -> alt.Chart:
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


def create_temperature_graph(data):
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


def create_weather_graph(data, variable, title, colour):
    return alt.Chart(data).mark_line(color=colour).encode(
        x=alt.X('Forecast time:T', axis=alt.Axis(
            grid=True)).scale(zero=False).title('Time'),
        y=alt.Y(f"{variable}:Q", axis=alt.Axis(grid=True)).scale(
            zero=False).title(title)
    )


def create_not_precipitation_graph(graph_type_day, forecast_d_loc, location):
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


def today_forecast(_conn, location):
    forecast_d_loc = get_location_forecast_day(_conn, location)

    forecast_hourly = forecast_d_loc[[
        "Forecast time", "Weather", "Temperature", "Feels like", "Humidity",
        "Precipitation probability", "Rainfall", "Snowfall", "Lightning potential", "Cloud cover"]].copy().set_index("Forecast time")
    forecast_hourly = sort_data_by_time(forecast_hourly, 'h')
    forecast_hourly = format_data_types(forecast_hourly, '%H:%M')
    write_table(forecast_hourly)

    graph_type_day = st.selectbox('Daily data', [
        "Temperature", "Visibility", "Air quality", "Precipitation", "Snowfall", "Lightning", "Cloud cover", "Humidity",])
    if graph_type_day == "Precipitation":
        create_precipitation_graph(forecast_d_loc)
    else:
        create_not_precipitation_graph(
            graph_type_day, forecast_d_loc, location)


def week_forecast(_conn, location):
    forecast_week_fix = get_location_forecast_week(_conn, location)
    forecast_week = forecast_week_fix[[
        "Forecast time", "Weather", "Temperature", "Feels like", "Humidity",
        "Precipitation probability", "Snowfall", "Lightning potential", "Cloud cover"]].copy().set_index("Forecast time")
    forecast_week = sort_data_by_time(forecast_week, 'd')
    forecast_week = format_data_types(forecast_week, '%d/%m')

    write_table(forecast_week)
    st.markdown('#')

    graph_type_week = st.selectbox('Weekly data', [
        "Temperature", "Visibility", "Air quality", "Precipitation", "Snowfall", "Lightning", "Cloud cover", "Humidity",])

    if graph_type_week == "Precipitation":
        create_precipitation_graph(forecast_week_fix)
    else:
        create_not_precipitation_graph(
            graph_type_week, forecast_week_fix, location)


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
    st.set_page_config(layout="wide")
    st.title('Quick Search')
    conn = connect_to_db(dict(ENV))
    location, lat, lon = create_location_selection_box(conn)
    if location != 'Select a location...':
        # floods = get_flood_alerts(conn, location)
        alerts = pd.concat([get_air_quality_alerts(conn, location),
                           get_weather_alerts(conn, location)])
        # if not floods.empty:
        #     errors, warnings = write_floods(floods)
        #     for error in errors:
        #         st.error(error[0], icon=error[1])

        #     for warning in warnings:
        #         st.warning(warning[0], icon=warning[1])
        write_alerts(alerts, location)

        st.markdown("# Current weather")
        current_weather = get_current_weather(conn, location)
        get_current_metrics(current_weather)

        st.markdown("## Today's forecast")
        today_forecast(conn, location)

        st.markdown("## This week's forecast")
        week_forecast(conn, location)

        get_map(get_forecast_data(conn), lon, lat)
    else:
        st.write('Please pick a location!')
