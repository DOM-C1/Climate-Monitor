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
import streamlit.components.v1 as components


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


def get_location_forecast_data(_conn) -> pd.DataFrame:
    """Returns location data as DataFrame from database."""
    with _conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""SELECT l.latitude, l.longitude, l.loc_name as "Location", c.name as "County", co.name as "Country",
                    f.forecast_timestamp as "Forecast time", wc.description as "Weather"
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
                    WHERE F.forecast_timestamp < NOW() + interval '12 hours'
                    AND F.forecast_timestamp > NOW() - interval '15 minutes'
                    GROUP BY "Forecast time", l.loc_id, "County", "Country", "Weather"
                    ORDER BY f.forecast_timestamp
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
        map_style=None,
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


if __name__ == "__main__":
    load_dotenv()
    st.title('Quick Search')
    conn = connect_to_db(dict(ENV))
    forecast_d = get_location_forecast_data(conn)
    location = st.selectbox('Locations',
                            ['Select a location...'] + list(forecast_d['Location'].sort_values().unique()))
    if location != 'Select a location...':
        lat, lon = forecast_d[forecast_d['Location'] ==
                              location][['latitude', 'longitude']].values[0]
        forecast_d_loc = forecast_d[forecast_d['Location'] == location]
        lat, lon = forecast_d_loc[['latitude', 'longitude']].values[0]

        st.markdown("# Current weather")
        current_weather = forecast_d_loc[forecast_d_loc["Forecast time"] == time_rounder(
            datetime.now())]
        current_weather = get_current_weather(conn, location)

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
            st.metric("Chance of rain",
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

        st.markdown("#")

        # st.altair_chart(alt.Chart(current_weather).mark_bar().encode(
        #     x = "Weather",
        #     y = "temperature"

        # ) + alt.Chart(current_weather).mark_point().encode(
        #     x = 'humidity',
        #     y = 'precipitation',
        #     color = "temperature"))

        st.markdown("## Today's forecast")
        st.write("average temp, modal weather code, etc.")
        st.table(forecast_d_loc)
        st.markdown("## This week's forecast")
        st.write(forecast_d_loc)
        get_map(forecast_d, lon, lat)
    else:
        st.write('Please pick a location!')
