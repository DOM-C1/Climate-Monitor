from datetime import datetime, timedelta
from os import environ as ENV

import altair as alt
import pandas as pd
import numpy as np
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import streamlit as st
from vega_datasets import data
import pydeck as pdk

ICON_URL = "https://upload.wikimedia.org/wikipedia/commons/f/f7/Light_Rain_Cloud.png"

icon_data = {
    # Icon from Wikimedia, used the Creative Commons Attribution-Share Alike 3.0
    # Unported, 2.5 Generic, 2.0 Generic and 1.0 Generic licenses
    "url": ICON_URL,
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
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""SELECT loc_name
                    FROM location
                    WHERE loc_id IN
                    (SELECT loc_id FROM weather_report)""")
        locations = cur.fetchall()
    return locations


def get_weather_alerts(_conn, location):
    """Get the loc_id and alert type if they exist in database"""
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
                    AND L.loc_name = {location}
                    GROUP BY L.loc_id, "Alert type", "Severity", SL.severity_level_id
                    ORDER BY SL.severity_level_id ASC
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame(rows)
    data_f["icon_data"] = None

    for i in data_f.index:
        data_f["icon_data"][i] = icon_data
    return data_f


def get_flood_alerts(_conn, location):
    """Get the loc_id and alert type if they exist in database"""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT SL.severity_level AS "Severity", C.name AS "County", FW.time_raised AS "Time raised"
                        FROM flood_warnings AS FW
                        JOIN severity_level AS SL ON (FW.severity_level_id = SL.severity_level_id)
                        JOIN location AS L ON (FW.loc_id = L.loc_id)
                        JOIN county AS C ON (L.county_id = C.county_id)
                        WHERE L.location = {location}
                        AND SL.severity_level_id < 4
                        ORDER BY SL.severity_level_id ASC""")

        rows = cur.fetchall()
        data_f = pd.DataFrame(rows)
    data_f["icon_data"] = None

    for i in data_f.index:
        data_f["icon_data"][i] = icon_data
    return data_f


def get_air_quality_alerts(_conn, location):
    """Get the loc_id and alert type if they exist in database"""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT SL.severity_level AS "Severity Level", 
                    MIN(WR.report_time) as min_time, MAX(WR.report_time) as max_time
                    FROM air_quality AS AQ
                    JOIN weather_report as WR ON (WR.weather_report_id = AQ.weather_report_id)
                    JOIN severity_level AS SL ON (FW.severity_level_id = SL.severity_level_id)
                    JOIN location AS L ON (FW.loc_id = L.loc_id)
                    WHERE L.location = {location}
                    AND SL.severity_level_id < 4
                    ORDER BY SL.severity_level_id ASC""")

        rows = cur.fetchall()
        data_f = pd.DataFrame(rows)
    data_f["icon_data"] = None
    data_f["Alert type"] = None

    for i in data_f.index:
        data_f["icon_data"][i] = icon_data
        data_f["icon_data"][i] = 'Air quality'
    return data_f


def get_location_forecast_day(_conn, location) -> pd.DataFrame:
    """Returns location data as DataFrame from database."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SET TIMEZONE TO 'Europe/London'")
        cur.execute(f"""SELECT L.latitude, L.longitude, f.forecast_timestamp as "Forecast time", wc.description as "Weather", f.temperature as "Temperature",
                    f.apparent_temp as "Feels like", f.precipitation_prob as "Precipitation probability", f.rainfall as "Rainfall",
                    f.precipitation as "Precipitation", f.snowfall as "Snowfall", f.visibility as "Visibility", 
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
                    AND L.loc_name = {location}
                    GROUP BY L.latitude, L.longitude, "Forecast time", "Weather", "Temperature", "Feels like","Precipitation",
                    "Precipitation probability", "Rainfall", "Snowfall", "Visibility", "Lightning potential", "Wind speed", "Cloud cover"
                    ORDER BY f.forecast_timestamp
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


def get_location_forecast_week(_conn, location) -> pd.DataFrame:
    """Returns location data as DataFrame from database."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SET TIMEZONE TO 'Europe/London'")
        cur.execute(f"""SELECT f.forecast_timestamp as "Forecast time", wc.description as "Weather", f.temperature as "Temperature",
                    f.apparent_temp as "Feels like", f.precipitation_prob as "Precipitation probability", f.rainfall as "Rainfall",
                    f.precipitation as "Precipitation", f.snowfall as "Snowfall", f.visibility as "Visibility", 
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
                    AND EXTRACT(hours FROM F.forecast_timestamp) % 4 = 0
                    AND EXTRACT(minutes FROM F.forecast_timestamp) = 0
                    AND l.loc_name = '{location}'
                    GROUP BY "Forecast time", "Weather", "Temperature", "Feels like", "Precipitation",
                    "Precipitation probability", "Rainfall", "Snowfall", "Visibility", "Lightning potential", "Wind speed", "Cloud cover"
                    ORDER BY f.forecast_timestamp
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


def get_air_quality(_conn, location) -> pd.DataFrame:
    """Extract analytics about current weather for a specific location"""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""SELECT aq.o3_concentration AS "O3 concentration", aq.severity_level_id AS "Severity level", 
                    wr.report_time AS "Report time", sl.severity_level AS "Severity"
                    FROM
                    air_quality AS aq
                    JOIN
                    weather_report AS wr
                    ON
                    (aq.weather_report_id = wr.weather_report_id)
                    JOIN
                    severity_level as sl
                    ON
                    (sl.severity_level_id = aq.severity_level_id)
                    JOIN
                    location AS l
                    ON
                    (l.loc_id = wr.loc_id)
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
                    WHERE F.forecast_timestamp <= '{time_rounder(datetime.now())}'
                    AND l.loc_name = '{location}'
                    GROUP BY "Forecast time", l.loc_id, f.forecast_id, "Weather"
                    ORDER BY f.forecast_timestamp DESC
                    LIMIT 1
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


def uk_map(loc_data, lon=-2, lat=54, tooltips=[]):
    """Generates a uk map of where the locations."""
    # Load GeoJSON data
    countries = alt.topo_feature(data.world_110m.url, 'countries')

    background = alt.Chart(countries).mark_geoshape(
        fill='lightgray',
        stroke='white',
        tooltip=None
    ).project(
        type='mercator',
        scale=1500,                          # Magnify
        center=[lon, lat],                     # [lon, lat]
        clipExtent=[[0, 0], [500, 500]],    # [[left, top], [right, bottom]]
    ).properties(
        width=500,
        height=500
    )
    points = alt.Chart(loc_data).mark_circle(color='red').encode(
        latitude='latitude:Q',
        longitude='longitude:Q',
        size=alt.value(20),
        tooltip=tooltips
    ).project(
        type='mercator',
        scale=1500,                          # Magnify
        center=[-2, 54],                     # [lon, lat]
        clipExtent=[[0, 0], [500, 500]],    # [[left, top], [right, bottom]]
    ).properties(
        width=500,
        height=500
    )
    return alt.layer(background, points).properties(title='Location map')


def get_map(loc_data, lon, lat):
    st.pydeck_chart(pdk.Deck(
        map_style='dark',
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=12,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=loc_data,
                get_position="[longitude, latitude]",
                get_color='[200, 30, 0, 160]',
                get_text="location",
                get_radius=200,
                pickable=True
            ),
        ],
        tooltip={'html': '<b>Weather:</b> {Weather}\
                 <b>Location:</b> {Location}',
                 'style': {"backgroundColor": "navyblue", 'color': '#87CEEB', 'font-size': '100%'}}))


def compass(wind_direction):
    compass_star = "https://upload.wikimedia.org/wikipedia/commons/b/bb/Windrose.svg"
    a = {'x': [0], 'y': [0], 'img': [compass_star],
         'arr_x': [0.95*np.cos((wind_direction-90)/180*np.pi)], 'arr_y': [-0.95*np.sin((wind_direction-90)/180*np.pi)]}
    c = {'c_x': [-1.2, 1.2, -1.2, 1.2], 'c_y': [-1.2, -1.2, 1.2, 1.2]}
    df = pd.DataFrame(a)
    corners = pd.DataFrame(c)

    star = alt.Chart(df).mark_image(width=220, height=220).encode(
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
    dot = alt.Chart(df).mark_point(size=800, color="gold", opacity=1).encode(
        x=alt.X('arr_x', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        y=alt.Y('arr_y', axis=alt.Axis(
            ticks=False, domain=False, labels=False, title=None)),
        tooltip=alt.value(str(wind_direction) + "°"),
        strokeWidth=alt.value(10)).properties(
        width=260,
        height=260
    )
    dot_border = alt.Chart(df).mark_point(size=850, color="black", align="center", baseline="middle", opacity=1).encode(
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
        radius=alt.value(120),
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
        radius=alt.value(130),
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


def sort_data_by_hour(data):
    data["Temperature"] = data[
        "Temperature"].resample('h').mean().round(1)
    data["Feels like"] = data[
        "Feels like"].resample('h').mean().round(1)
    data["Precipitation probability"] = data[
        "Temperature"].resample('h').mean().round()
    data["Cloud cover"] = data[
        "Temperature"].resample('h').mean().round()
    data["Rainfall"] = data[
        "Rainfall"].resample('h').sum().round(2)
    data["Snowfall"] = data[
        "Snowfall"].resample('h').sum()
    data["Lightning potential"] = data[
        "Lightning potential"].resample('h').mean().round(1)
    data = data.dropna(how="any")  # drop nans
    data = data.loc[:, (data != 0).any(axis=0)]  # drop columns with zeros
    data = data.reset_index(level=['Forecast time']).drop_duplicates()
    return data


def format_data_types(data):
    data['Forecast time'] = data['Forecast time'].dt.strftime(
        '%H:%M')
    data["Temperature"] = data["Temperature"].apply(
        lambda x: str(x) + '°C')
    data["Feels like"] = data["Feels like"].apply(
        lambda x: str(x) + '°C')
    if "Precipitation probability" in data.columns:
        data["Precipitation probability"] = data["Precipitation probability"].apply(
            lambda x: str(x) + '%')
    if "Lightning potential" in data.columns:
        data["Lightning potential"] = data["Lightning potential"].apply(
            lambda x: str(x) + 'J/kg')
    if "Cloud cover" in data.columns:
        data["Cloud cover"] = data["Cloud cover"].apply(
            lambda x: str(x) + '%')
    if "Rainfall" in data.columns:
        data["Rainfall"] = data["Rainfall"].apply(
            lambda x: str(x) + 'mm')
    return data


def style_table(cell):
    if '%' in cell:
        cell = float(cell[:-1])
        if cell <= 30:
            return "background-color: green"
        if 30 < cell < 70:
            return "background-color: yellow"
        return "background-color: red"
    if '°C' in cell:
        cell = float(cell[:-2])
        if cell <= 10:
            return "background-color: blue"
        if 10 < cell < 20:
            return "background-color: green"
        return "background-color: red"


def create_location_selection_box(_conn) -> str:
    locations = get_locations(_conn)
    return st.selectbox('Locations',
                        ['Select a location...'] + list(set(locations)))


def write_alerts(alerts):
    for _, alert in alerts.iterrows():
        if alert["Severity"] == "Alert":
            icon = "❕"
        elif alert["Severity"] == "Warning":
            icon = "⚠️"
        elif alert["Severity"] == "Severe Warning":
            icon = "🚨"
        if alert["min_time"] != alert["max_time"]:
            st.warning(
                f'**{alert["Location"]}** has a **{alert["Alert type"]} {alert["Severity"]}** from **{alert["min_time"]}** to **{alert["max_time"]}**.', icon=icon)
        else:
            st.warning(
                f'**{alert["Location"]}** has a **{alert["Alert type"]} {alert["Severity"]}** at **{alert["min_time"]}**.', icon=icon)


def write_floods(floods):
    for _, flood in floods.iterrows():
        if flood["Severity"] == "Alert":
            icon = "❕"
        elif flood["Severity"] == "Warning":
            icon = "⚠️"
        elif flood["Severity"] == "Severe Warning":
            icon = "🚨"
        st.warning(
            f'**{flood["County"]}** had a flood {flood["Severity"]}** raised at **{flood["Time raised"]}**.', icon=icon)


def get_current_metrics(current_weather):
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
    main_cols = [
        {'selector': 'th', 'props': 'background-color: #000042; color:  #ffffff'}]
    st.markdown(data.T.style.hide(axis="columns").map(lambda x: "background-color:#000042;color:#ffffff" if isinstance(x, str) and ':' in x else "background-color:#82a6f4").set_table_styles(main_cols, axis=1).to_html(),
                unsafe_allow_html=True)


def create_graph_selection_box() -> str:
    return st.selectbox('Variable_day', [
        "Temperature", "Visibility", "Air quality", "Precipitation", "Snowfall", "Lightning", "Cloud cover"])


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


if __name__ == "__main__":
    load_dotenv()
    st.set_page_config(layout="wide")
    st.title('Quick Search')
    conn = connect_to_db(dict(ENV))
    location = create_location_selection_box(conn)
    if location != 'Select a location...':
        floods = get_flood_alerts(conn)
        alerts = pd.concat(get_air_quality_alerts(conn),
                           get_weather_alerts(conn))
        write_floods(floods)
        write_alerts(alerts)

        st.markdown("# Current weather")
        current_weather = get_current_weather(conn, location)
        get_current_metrics(current_weather)

        st.markdown("## Today's forecast")
        forecast_d_loc = get_location_forecast_day(conn, location)

        forecast_hourly = forecast_d_loc[[
            "Forecast time", "Weather", "Temperature", "Feels like", "Visibility",
            "Precipitation probability", "Rainfall", "Snowfall", "Lightning potential", "Cloud cover"]].copy().set_index("Forecast time")
        forecast_hourly = sort_data_by_hour(forecast_hourly)
        forecast_hourly = format_data_types(forecast_hourly)
        write_table(forecast_hourly)

        graph_type_day = create_graph_selection_box()
        if graph_type_day == "Precipitation":
            create_precipitation_graph(forecast_d_loc)
        else:
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


#########################################

        st.markdown("## This week's forecast")
        forecast_week_fix = get_location_forecast_week(conn, location)
        forecast_week = forecast_week_fix[[
            "Forecast time", "Weather", "Temperature", "Feels like",
            "Precipitation probability", "Rainfall", "Snowfall", "Lightning potential", "Cloud cover"]].copy().set_index("Forecast time")
        forecast_week = sort_data_by_hour(forecast_week)
        forecast_week = format_data_types(forecast_week)

        main_cols = [
            {'selector': 'th', 'props': 'background-color: #000042; color:  #ffffff'}]
        sub_cols = [{'selector': 'th', 'props': 'background-color: grey'}]
        st.markdown(forecast_week.T.style.hide(axis="columns").map(lambda x: "background-color:#000042;color:#ffffff" if isinstance(x, str) and ':' in x else "background-color:#82a6f4").set_table_styles(main_cols, axis=1).to_html(),
                    unsafe_allow_html=True)
        st.markdown('#')

        graph_type_week = st.selectbox('Variable_week', [
            "Temperature", "Visibility", "Air quality", "Precipitation", "Snowfall", "Lightning", "Cloud cover"])
        if graph_type_week == "Precipitation":
            """rainfall, prec, prec prob"""
            prec_col, rain_col = st.columns(2)
            with prec_col:

                precipitation_graph = alt.Chart(forecast_week_fix).mark_area(color="navyblue").encode(
                    x=alt.X('Forecast time:T', axis=alt.Axis(
                        grid=True)).scale(zero=False).title('Time'),
                    y=alt.Y("Precipitation:Q", axis=alt.Axis(grid=True)).scale(
                        zero=False).title("Precipitation (mm)")
                )
                precipitation_prob_graph = alt.Chart(forecast_week_fix).mark_line(color="gold").encode(
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
                rainfall_graph = alt.Chart(forecast_week_fix).mark_area(color="blue").encode(
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
        else:
            if graph_type_week == "Air quality":
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
                    y=alt.Y("level1").title("03 concentration")
                )
                aq_chart2 = air_base.mark_line(color="gold").encode(
                    y=alt.Y("level2").title("03 concentration")
                )
                aq_chart3 = air_base.mark_line(color="green").encode(
                    y=alt.Y("level3").title("03 concentration")
                )
                weather_today_graph = alt.layer(aq_chart + aq_chart1 + aq_chart2 +
                                                aq_chart3)
            elif graph_type_week == "Temperature":
                weather_today_graph = alt.Chart(forecast_week_fix).mark_line().transform_fold(
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
            elif graph_type_week == "Cloud cover":
                weather_today_graph = alt.Chart(forecast_week_fix).mark_line(color="blue").encode(
                    x=alt.X('Forecast time:T', axis=alt.Axis(
                        grid=True)).scale(zero=False).title('Time'),
                    y=alt.Y("Cloud cover:Q", axis=alt.Axis(grid=True)).scale(
                        zero=False).title("Cloud cover (%)")
                )
            elif graph_type_week == "Snowfall":
                weather_today_graph = alt.Chart(forecast_week_fix).mark_line(color="red").encode(
                    x=alt.X('Forecast time:T', axis=alt.Axis(
                        grid=True)).scale(zero=False).title('Time'),
                    y=alt.Y("Snowfall:Q", axis=alt.Axis(grid=True)).scale(
                        zero=False).title("Snowfall (cm)")
                )
            elif graph_type_week == "Lightning":
                weather_today_graph = alt.Chart(forecast_week_fix).mark_line(color="gold").encode(
                    x=alt.X('Forecast time:T', axis=alt.Axis(
                        grid=True)).scale(zero=False).title('Time'),
                    y=alt.Y("Lightning potential", axis=alt.Axis(grid=True)).scale(
                        zero=False).title(f"Lightning potential (J/kg)")
                )
            elif graph_type_week == "Visibility":
                weather_today_graph = alt.Chart(forecast_week_fix).mark_line(color="green").encode(
                    x=alt.X('Forecast time:T', axis=alt.Axis(
                        grid=True)).scale(zero=False).title('Time'),
                    y=alt.Y("Visibility", axis=alt.Axis(grid=True)).scale(
                        zero=False).title(f"Visibility (m)")
                )

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
        lat, lon = forecast_d_loc[['latitude', 'longitude']].values[0]
        get_map(forecast_d_loc, lon, lat)
    else:
        st.write('Please pick a location!')
