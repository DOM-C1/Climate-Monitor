
from os import environ as ENV

import altair as alt
import pandas as pd
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import streamlit as st
from vega_datasets import data
import pydeck as pdk


def connect_to_db(config):
    """Returns a live database connection."""
    return connect(
        host=config["DB_HOST"],
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        database=config["DB_NAME"],
        port=config["DB_PORT"]
    )


def get_location_forecast_data(conn) -> pd.DataFrame:
    """Returns location data as DataFrame from database."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SET timezone='Europe/London'""")
        cur.execute(f"""SELECT l.latitude, l.longitude, l.loc_name as Location, c.name as County, co.name as Country,
                    f.forecast_timestamp as forecast_time, wc.description as weather
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
                    WHERE f.forecast_timestamp > NOW()
                    GROUP BY forecast_time, l.loc_id, County, Country, weather
                    """)

        rows = cur.fetchall()
        data_f = pd.DataFrame.from_dict(rows)

    return data_f


def uk_map(loc_data, lat, lon, tooltips):
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
        center=[-2, 54],                     # [lon, lat]
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


def get_map(loc_data, lat, lon):
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
                'HexagonLayer',
                data=loc_data,
                get_position="[latitude, longitude]",
                radius=200,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
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
        tooltip={'html': '<b>Weather:</b> {weather}\
                 <b>Location:</b> {location}',
                 'style': {"backgroundColor": "navyblue", 'color': '#87CEEB', 'font-size': '100%'}}))


if __name__ == "__main__":
    load_dotenv()
    with connect_to_db(ENV) as conn:
        forecast_d = get_location_forecast_data(conn)
        location = st.selectbox('Locations',
                                ['Select a location...'] + list(forecast_d['location'].sort_values().unique()))
        time_forecast = st.selectbox('Time',
                                     ['Select a time...'] + list(forecast_d['forecast_time'].sort_values().unique()))
        if location != 'Select a location...' and time_forecast != 'Select a time...':
            lat, lon, county = forecast_d[forecast_d['location'] == location][[
                'latitude', 'longitude', 'county']].values[0]
            forecast_d = forecast_d[forecast_d['county'] ==
                                    county][forecast_d['forecast_time'] == time_forecast]
            w_map = get_map(forecast_d, lat, lon)
        elif time_forecast != 'Select a time...':
            st.warning('No location selected!')
        elif location != 'Select a location...':
            st.warning('No location selected!')
        else:
            st.warning('Please pick a location and time!')
